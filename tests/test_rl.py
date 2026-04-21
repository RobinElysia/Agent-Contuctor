import json
from pathlib import Path

import pytest

from agentconductor import (
    RlTrainingConfig,
    compute_reward_breakdown_entrypoint,
    generate_sft_dataset_entrypoint,
    run_rl_baseline_entrypoint,
)


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


def test_rl_training_config_rejects_invalid_rollout_count() -> None:
    with pytest.raises(ValueError, match="rollouts"):
        RlTrainingConfig(rollouts=0)


def test_run_rl_baseline_entrypoint_writes_reward_breakdowns(tmp_path: Path) -> None:
    dataset_path = tmp_path / "sft.jsonl"
    artifact_path = tmp_path / "artifacts" / "rl.json"
    generate_sft_dataset_entrypoint(dataset_path)

    artifact = run_rl_baseline_entrypoint(
        dataset_path,
        artifact_path,
        rollouts=2,
        seed=3,
    )

    assert artifact.rollout_count == 2
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert len(payload["reward_breakdowns"]) == 2
