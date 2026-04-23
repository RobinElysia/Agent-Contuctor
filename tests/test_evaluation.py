import json
from pathlib import Path

import pytest

import agentconductor.application.evaluation as evaluation_module
from agentconductor import (
    AgentExecutionResult,
    AgentInvocation,
    AgentRole,
    DifficultyLevel,
    EvaluationSummary,
    ExecutionStatus,
    ProblemInstance,
    SolveResult,
    SolveState,
    SolveStatus,
    SolveTurnRecord,
    StopReason,
    StepExecutionResult,
    TestingFeedback,
    TestingOutcome,
    TopologyExecutionResult,
    TopologyPlan,
    TopologyStep,
    generate_sft_dataset_entrypoint,
    run_benchmark_evaluation_entrypoint,
    run_sft_baseline_entrypoint,
)
from agentconductor.application.evaluation import load_evaluation_dataset


def test_load_evaluation_dataset_rejects_invalid_schema(tmp_path: Path) -> None:
    dataset_path = tmp_path / "invalid.jsonl"
    dataset_path.write_text(
        '{"problem_id":"missing-question","split":"train"}\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="question"):
        load_evaluation_dataset(dataset_path)


def test_run_benchmark_evaluation_entrypoint_writes_summary_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset_path = tmp_path / "apps.jsonl"
    output_path = tmp_path / "artifacts" / "results.json"
    sft_dataset_path = tmp_path / "sft.jsonl"
    sft_artifact_path = tmp_path / "artifacts" / "sft-run.json"
    dataset_path.write_text(
        json.dumps(
            {
                "problem_id": "42",
                "question": "Return the sum of two integers.",
                "difficulty": "introductory",
                "split": "test",
                "language": "python",
                "input_output": {
                    "fn_name": "solve",
                    "inputs": [[1, 2], [3, 4]],
                    "outputs": [3, 7],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    generate_sft_dataset_entrypoint(sft_dataset_path, sample_count=9)
    sft_artifact = run_sft_baseline_entrypoint(
        sft_dataset_path,
        sft_artifact_path,
        seed=7,
    )

    solve_calls = {"count": 0}

    def fake_solve_problem(
        problem: ProblemInstance,
        *,
        max_turns: int | None = None,
        orchestrator_policy=None,
        orchestrator_checkpoint=None,
        orchestrator_checkpoint_id=None,
        orchestrator_device: str = "cpu",
        orchestrator_max_attempts: int = 1,
    ) -> SolveResult:
        del orchestrator_policy, orchestrator_max_attempts
        assert max_turns == 2
        assert orchestrator_checkpoint == str(
            Path(sft_artifact.checkpoint_path) / "checkpoint.json"
        )
        assert orchestrator_checkpoint_id == sft_artifact.checkpoint_id
        assert orchestrator_device == "cpu"

        solve_calls["count"] += 1
        candidate_code = (
            "def solve(a, b):\n    return a - b\n"
            if solve_calls["count"] == 1
            else "def solve(a, b):\n    return a + b\n"
        )
        outcome = (
            TestingOutcome.WRONG_ANSWER
            if solve_calls["count"] == 1
            else TestingOutcome.PASSED
        )
        return _build_stub_solve_result(
            problem=problem,
            candidate_code=candidate_code,
            outcome=outcome,
        )

    monkeypatch.setattr(evaluation_module, "solve_problem", fake_solve_problem)

    artifact = run_benchmark_evaluation_entrypoint(
        dataset_path,
        output_path,
        checkpoint_source=sft_artifact_path,
        samples_per_problem=2,
        pass_k=2,
        max_workers=1,
        max_turns=2,
    )

    assert artifact.metadata.checkpoint_id == sft_artifact.checkpoint_id
    assert artifact.metadata.dataset_version.startswith("sha256:")
    assert artifact.metadata.runtime_mode == "local_harness"
    assert artifact.metadata.reproduction_claim == "approximate"
    assert artifact.metadata.exact_reproduction_ready is False
    assert "benchmark-runtime" in artifact.metadata.blocking_gap_ids
    assert artifact.summary.problem_count == 1
    assert artifact.summary.attempt_count == 2
    assert artifact.summary.benchmark_completed_count == 2
    assert artifact.summary.pass_at_1 == 0.0
    assert artifact.summary.pass_at_k == 1.0
    assert artifact.summary.pass_k == 2
    assert artifact.results[0].benchmark_testing_outcome == "wrong_answer"
    assert artifact.results[1].benchmark_testing_outcome == "passed"
    assert artifact.results[1].candidate_language == "python"
    assert Path(artifact.results[1].result_artifact_uri).exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["metadata"]["checkpoint_id"] == sft_artifact.checkpoint_id
    assert payload["metadata"]["reproduction_claim"] == "approximate"
    assert payload["summary"]["pass_at_1"] == 0.0
    assert payload["summary"]["pass_at_k"] == 1.0


def test_evaluation_summary_can_compute_pass_at_k() -> None:
    summary = evaluation_module._summarize_results(
        results=(
            evaluation_module.EvaluationProblemResult(
                identifier="apps/test/1",
                source_problem_id="1",
                attempt_index=0,
                solve_status=SolveStatus.FAILED,
                benchmark_status=evaluation_module.BenchmarkEvaluationStatus.COMPLETED,
                solve_testing_outcome="wrong_answer",
                benchmark_testing_outcome="wrong_answer",
                benchmark_native_verdict="wrong_answer",
                latency_seconds=0.2,
                completed_turns=2,
                topology_steps=3,
                topology_agents=3,
                candidate_language="python",
                checkpoint_id="ckpt-a",
            ),
            evaluation_module.EvaluationProblemResult(
                identifier="apps/test/1",
                source_problem_id="1",
                attempt_index=1,
                solve_status=SolveStatus.COMPLETED,
                benchmark_status=evaluation_module.BenchmarkEvaluationStatus.COMPLETED,
                solve_testing_outcome="passed",
                benchmark_testing_outcome="passed",
                benchmark_native_verdict="accepted",
                latency_seconds=0.1,
                completed_turns=1,
                topology_steps=3,
                topology_agents=3,
                candidate_language="python",
                checkpoint_id="ckpt-a",
            ),
        ),
        problem_count=1,
        pass_k=2,
    )

    assert isinstance(summary, EvaluationSummary)
    assert summary.pass_at_1 == 0.0
    assert summary.pass_at_k == 1.0
    assert summary.average_latency_seconds == pytest.approx(0.15)


def _build_stub_solve_result(
    *,
    problem: ProblemInstance,
    candidate_code: str,
    outcome: TestingOutcome,
) -> SolveResult:
    difficulty = problem.difficulty or DifficultyLevel.MEDIUM
    topology = TopologyPlan(
        difficulty=difficulty,
        steps=(
            TopologyStep(
                index=0,
                agents=(AgentInvocation(name="planner_0", role=AgentRole.PLANNING),),
            ),
            TopologyStep(
                index=1,
                agents=(AgentInvocation(name="tester_1", role=AgentRole.TESTING),),
            ),
        ),
    )
    diagnostics = (
        "Accepted benchmark-aligned candidate."
        if outcome is TestingOutcome.PASSED
        else "Benchmark-aligned candidate failed."
    )
    execution = TopologyExecutionResult(
        problem=problem,
        difficulty=difficulty,
        status=ExecutionStatus.COMPLETED,
        step_results=(
            StepExecutionResult(
                step_index=1,
                agent_results=(
                    AgentExecutionResult(
                        step_index=1,
                        agent_name="tester_1",
                        role=AgentRole.TESTING,
                        summary="Stub evaluation candidate.",
                        references=(),
                        candidate_code=candidate_code,
                        diagnostics=(diagnostics,),
                        testing_outcome=outcome,
                    ),
                ),
            ),
        ),
        final_candidate_code=candidate_code,
        testing_outcome=outcome,
        diagnostics=(diagnostics,),
    )
    feedback = TestingFeedback(
        outcome=outcome,
        diagnostics=(diagnostics,),
        candidate_code=candidate_code,
    )
    solve_state = SolveState(
        problem=problem,
        selected_difficulty=difficulty,
        max_turns=2,
        max_nodes=4,
        available_roles=("planning", "coding", "testing"),
        turns=(
            SolveTurnRecord(
                turn_index=0,
                topology=topology,
                execution=execution,
                testing_feedback=feedback,
            ),
        ),
        stop_reason=(
            StopReason.SOLVED
            if outcome is TestingOutcome.PASSED
            else StopReason.TURN_BUDGET_EXHAUSTED
        ),
    )
    return SolveResult(
        problem_id=problem.identifier,
        status=SolveStatus.COMPLETED if outcome is TestingOutcome.PASSED else SolveStatus.FAILED,
        selected_difficulty=difficulty,
        planned_turns=2,
        max_nodes=4,
        available_roles=("planning", "coding", "testing"),
        topology=topology,
        execution=execution,
        candidate_solution=candidate_code,
        testing_outcome=outcome,
        solve_state=solve_state,
        notes=("Stub benchmark-aligned solve result.",),
    )
