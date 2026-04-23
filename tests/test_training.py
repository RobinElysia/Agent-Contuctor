import json
from pathlib import Path

import pytest

from agentconductor import (
    DifficultyLevel,
    SftTrainingConfig,
    TopologyPlan,
    generate_sft_dataset_entrypoint,
    run_sft_baseline_entrypoint,
)
from agentconductor.application.training import load_sft_dataset


def test_generate_sft_dataset_and_load_schema(tmp_path: Path) -> None:
    dataset_path = tmp_path / "sft.jsonl"

    samples = generate_sft_dataset_entrypoint(dataset_path)

    assert len(samples) == 3
    loaded_samples = load_sft_dataset(dataset_path)
    assert len(loaded_samples) == 3
    assert loaded_samples[0].target_topology["difficulty"] == "easy"
    assert loaded_samples[0].target_topology == TopologyPlan.from_mapping(
        loaded_samples[0].target_topology
    ).to_mapping()
    assert loaded_samples[2].difficulty == DifficultyLevel.HARD.value


def test_sft_training_config_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="epochs"):
        SftTrainingConfig(epochs=0)


def test_run_sft_baseline_entrypoint_writes_artifact(tmp_path: Path) -> None:
    dataset_path = tmp_path / "sft.jsonl"
    artifact_path = tmp_path / "artifacts" / "sft.json"
    generate_sft_dataset_entrypoint(dataset_path)

    artifact = run_sft_baseline_entrypoint(
        dataset_path,
        artifact_path,
        epochs=2,
        learning_rate=5e-4,
        seed=7,
    )

    assert artifact.sample_count == 3
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["epochs"] == 2
