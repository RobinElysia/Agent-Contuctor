import json
from pathlib import Path

import pytest

from agentconductor import (
    DifficultyLevel,
    SftDatasetConfig,
    SftTrainingConfig,
    TopologyPlan,
    generate_sft_dataset_entrypoint,
    load_sft_checkpoint_entrypoint,
    run_sft_baseline_entrypoint,
)
from agentconductor.application.training import load_sft_dataset


def test_generate_sft_dataset_and_load_schema(tmp_path: Path) -> None:
    dataset_path = tmp_path / "sft.jsonl"

    samples = generate_sft_dataset_entrypoint(dataset_path, sample_count=12, seed=3)

    assert len(samples) == 12
    loaded_samples = load_sft_dataset(dataset_path)
    assert len(loaded_samples) == 12
    assert loaded_samples[0].target_topology["difficulty"] == "easy"
    assert loaded_samples[0].target_topology_yaml.startswith("difficulty: easy\n")
    assert loaded_samples[0].source_template_id
    assert loaded_samples[0].prompt_variant == 0
    assert loaded_samples[0].target_topology == TopologyPlan.from_mapping(
        loaded_samples[0].target_topology
    ).to_mapping()
    assert loaded_samples[0].target_topology == TopologyPlan.from_mapping(
        load_sft_dataset(dataset_path)[0].target_topology
    ).to_mapping()
    assert {sample.difficulty for sample in loaded_samples} == {
        DifficultyLevel.EASY.value,
        DifficultyLevel.MEDIUM.value,
        DifficultyLevel.HARD.value,
    }
    metadata = json.loads(
        dataset_path.with_suffix(".jsonl.metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["sample_count"] == 12
    assert metadata["uses_reduced_paper_subset"] is True
    assert sum(metadata["difficulty_breakdown"].values()) == 12


def test_sft_training_config_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="sample_count"):
        SftDatasetConfig(sample_count=0)
    with pytest.raises(ValueError, match="epochs"):
        SftTrainingConfig(epochs=0)
    with pytest.raises(ValueError, match="backbone_name"):
        SftTrainingConfig(backbone_name=" ")


def test_run_sft_baseline_entrypoint_writes_artifact(tmp_path: Path) -> None:
    dataset_path = tmp_path / "sft.jsonl"
    artifact_path = tmp_path / "artifacts" / "sft.json"
    generate_sft_dataset_entrypoint(dataset_path, sample_count=9, seed=1)

    artifact = run_sft_baseline_entrypoint(
        dataset_path,
        artifact_path,
        epochs=2,
        learning_rate=5e-4,
        seed=7,
    )

    assert artifact.sample_count == 9
    assert artifact.target_format == "yaml"
    assert artifact.backbone_name == "Qwen2.5-3B-Instruct"
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["checkpoint_path"].endswith("sft-checkpoint")
    checkpoint = load_sft_checkpoint_entrypoint(payload["checkpoint_path"])
    assert checkpoint.sample_count == 9
    assert checkpoint.target_format == "yaml"
    assert Path(checkpoint.training_manifest_path).exists()
    assert checkpoint.runtime_kind == "repository_frozen_bundle"
    assert checkpoint.runtime_artifact_path is not None
    assert Path(checkpoint.runtime_artifact_path).exists()
    assert checkpoint.source_dataset_metadata_path is not None
    assert Path(checkpoint.source_dataset_metadata_path).exists()
    assert checkpoint.paper_target_sample_count == 4500
    assert checkpoint.uses_reduced_paper_subset is True
    assert checkpoint.scale_label == "reduced-scale-approximate"
    assert checkpoint.optimizer_name == "adamw"
    assert payload["epochs"] == 2
