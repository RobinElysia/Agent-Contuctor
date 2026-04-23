import json
from pathlib import Path

import pytest

import agentconductor.application.rl as rl_module
from agentconductor import (
    AgentExecutionResult,
    AgentInvocation,
    AgentRole,
    DifficultyLevel,
    ExecutionStatus,
    RlTrainingConfig,
    StepExecutionResult,
    TestingOutcome,
    TopologyExecutionResult,
    TopologyPlan,
    TopologyStep,
    compute_reward_breakdown_entrypoint,
    generate_sft_dataset_entrypoint,
    load_sft_checkpoint_entrypoint,
    run_rl_baseline_entrypoint,
    run_sft_baseline_entrypoint,
)
from agentconductor.domain.models import ProblemInstance


def test_compute_reward_breakdown_prefers_valid_passing_topology() -> None:
    reward = compute_reward_breakdown_entrypoint(
        {
            "difficulty": "easy",
            "steps": [
                {
                    "index": 0,
                    "agents": [{"name": "planner_0", "role": "planning", "refs": []}],
                },
                {
                    "index": 1,
                    "agents": [
                        {
                            "name": "tester_1",
                            "role": "testing",
                            "refs": [{"step_index": 0, "agent_name": "planner_0"}],
                        }
                    ],
                },
            ],
        },
        yaml_valid=True,
        execution_outcome="passed",
    )

    assert reward.yaml_reward == 0.0
    assert reward.execution_reward == 1.0
    assert reward.total_reward > 0


def test_rl_training_config_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="rollout_count"):
        RlTrainingConfig(rollout_count=0)
    with pytest.raises(ValueError, match="divisible"):
        RlTrainingConfig(rollout_count=3, group_size=2)
    with pytest.raises(ValueError, match="optimizer_learning_rate"):
        RlTrainingConfig(optimizer_learning_rate=0)


def test_run_rl_baseline_entrypoint_writes_updated_checkpoint_artifact(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "sft.jsonl"
    sft_artifact_path = tmp_path / "artifacts" / "sft.json"
    rl_artifact_path = tmp_path / "artifacts" / "rl.json"
    generate_sft_dataset_entrypoint(dataset_path, sample_count=9)
    sft_artifact = run_sft_baseline_entrypoint(dataset_path, sft_artifact_path, seed=7)

    def fake_solve_problem(
        problem: ProblemInstance,
        *,
        max_turns: int | None = None,
        orchestrator_policy=None,
        orchestrator_checkpoint=None,
        orchestrator_checkpoint_id=None,
        orchestrator_device: str = "cpu",
        orchestrator_max_attempts: int = 1,
    ):
        del (
            orchestrator_policy,
            orchestrator_checkpoint,
            orchestrator_max_attempts,
        )
        assert max_turns == 2
        assert orchestrator_checkpoint_id == sft_artifact.checkpoint_id
        assert orchestrator_device == "cpu"
        topology = TopologyPlan(
            difficulty=problem.difficulty or DifficultyLevel.EASY,
            steps=(
                TopologyStep(
                    index=0,
                    agents=(AgentInvocation(name="planner_0", role=AgentRole.PLANNING),),
                ),
                TopologyStep(
                    index=1,
                    agents=(AgentInvocation(name="coder_1", role=AgentRole.CODING),),
                ),
                TopologyStep(
                    index=2,
                    agents=(AgentInvocation(name="tester_2", role=AgentRole.TESTING),),
                ),
            ),
        )
        execution = TopologyExecutionResult(
            problem=problem,
            difficulty=problem.difficulty or DifficultyLevel.EASY,
            status=ExecutionStatus.COMPLETED,
            step_results=(
                StepExecutionResult(
                    step_index=2,
                    agent_results=(
                        AgentExecutionResult(
                            step_index=2,
                            agent_name="tester_2",
                            role=AgentRole.TESTING,
                            summary="RL rollout passed.",
                            references=(),
                            candidate_code="def solve():\n    return 'ok'\n",
                            diagnostics=("Accepted.",),
                            testing_outcome=TestingOutcome.PASSED,
                        ),
                    ),
                ),
            ),
            final_candidate_code="def solve():\n    return 'ok'\n",
            testing_outcome=TestingOutcome.PASSED,
            diagnostics=("Accepted.",),
        )

        class StubSolveResult:
            def __init__(self):
                self.topology = topology
                self.testing_outcome = TestingOutcome.PASSED
                self.execution = execution

        return StubSolveResult()

    monkeypatch.setattr(rl_module, "solve_problem", fake_solve_problem)

    artifact = run_rl_baseline_entrypoint(
        dataset_path,
        rl_artifact_path,
        checkpoint_source=sft_artifact_path,
        rollout_count=4,
        group_size=2,
        turn_budget=2,
        seed=3,
    )

    assert artifact.rollout_count == 4
    assert artifact.group_size == 2
    payload = json.loads(rl_artifact_path.read_text(encoding="utf-8"))
    assert len(payload["rollout_records"]) == 4
    assert payload["rollout_records"][0]["execution_outcome"] == "passed"
    assert payload["rollout_records"][0]["resulting_checkpoint_id"] == artifact.checkpoint_id
    assert payload["policy_update"]["optimizer_name"] == "grpo-stub"

    updated_checkpoint = load_sft_checkpoint_entrypoint(artifact.checkpoint_path)
    assert updated_checkpoint.training_stage == "rl"
    assert updated_checkpoint.parent_checkpoint_id == sft_artifact.checkpoint_id
    assert updated_checkpoint.average_reward == artifact.average_reward
    assert updated_checkpoint.optimizer_name == "grpo-stub"
    assert updated_checkpoint.runtime_artifact_path is not None
    assert Path(updated_checkpoint.runtime_artifact_path).exists()
    assert Path(artifact.rollout_manifest_path).exists()
