"""Typed contracts for supervised orchestrator training."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SyntheticTopologySample:
    """One schema-valid SFT training sample for the orchestrator."""

    problem_id: str
    prompt: str
    difficulty: str
    target_topology: dict
    target_topology_yaml: str


@dataclass(frozen=True, slots=True)
class SftTrainingConfig:
    """Configuration for repository-local supervised orchestrator training."""

    epochs: int = 1
    learning_rate: float = 1e-4
    seed: int = 0
    backbone_name: str = "Qwen2.5-3B-Instruct"
    tokenizer_name: str = "Qwen2.5-3B-Instruct"
    prompt_template_version: str = "orchestrator-sft-v1"

    def __post_init__(self) -> None:
        if self.epochs < 1:
            raise ValueError("epochs must be at least 1")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be > 0")
        if not self.backbone_name.strip():
            raise ValueError("backbone_name must be a non-empty string")
        if not self.tokenizer_name.strip():
            raise ValueError("tokenizer_name must be a non-empty string")
        if not self.prompt_template_version.strip():
            raise ValueError("prompt_template_version must be a non-empty string")


@dataclass(frozen=True, slots=True)
class OrchestratorCheckpointMetadata:
    """Loadable metadata for one repository-local orchestrator checkpoint."""

    checkpoint_id: str
    checkpoint_path: str
    metadata_path: str
    dataset_path: str
    training_manifest_path: str
    sample_count: int
    target_format: str
    backbone_name: str
    tokenizer_name: str
    prompt_template_version: str
    epochs: int
    learning_rate: float
    seed: int
    training_stage: str = "sft"
    parent_checkpoint_id: str | None = None
    optimizer_name: str | None = None
    optimizer_steps: int = 0
    average_reward: float | None = None


@dataclass(frozen=True, slots=True)
class SftTrainingArtifact:
    """Inspectable artifact written by the SFT training entrypoint."""

    dataset_path: str
    training_manifest_path: str
    checkpoint_id: str
    checkpoint_path: str
    checkpoint_metadata_path: str
    sample_count: int
    target_format: str
    backbone_name: str
    tokenizer_name: str
    prompt_template_version: str
    epochs: int
    learning_rate: float
    seed: int
