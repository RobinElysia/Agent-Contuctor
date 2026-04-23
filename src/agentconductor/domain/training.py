"""Typed contracts for supervised orchestrator training."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SftDatasetConfig:
    """Configuration for paper-oriented synthetic YAML-topology dataset creation."""

    sample_count: int = 4500
    seed: int = 0
    prompt_template_version: str = "orchestrator-sft-v2"
    source_recipe_name: str = "paper-oriented-synthetic-yaml-v1"
    paper_target_sample_count: int = 4500

    def __post_init__(self) -> None:
        if self.sample_count < 1:
            raise ValueError("sample_count must be at least 1")
        if self.paper_target_sample_count < 1:
            raise ValueError("paper_target_sample_count must be at least 1")
        if not self.prompt_template_version.strip():
            raise ValueError("prompt_template_version must be a non-empty string")
        if not self.source_recipe_name.strip():
            raise ValueError("source_recipe_name must be a non-empty string")


@dataclass(frozen=True, slots=True)
class SyntheticTopologySample:
    """One schema-valid SFT training sample for the orchestrator."""

    problem_id: str
    prompt: str
    difficulty: str
    source_template_id: str
    prompt_variant: int
    target_topology: dict
    target_topology_yaml: str


@dataclass(frozen=True, slots=True)
class SftDatasetMetadata:
    """Inspectable metadata for one prepared synthetic topology corpus."""

    dataset_path: str
    metadata_path: str
    sample_count: int
    paper_target_sample_count: int
    uses_reduced_paper_subset: bool
    source_recipe_name: str
    prompt_template_version: str
    seed: int
    difficulty_breakdown: dict[str, int]
    topology_source: str = "deterministic_orchestrator"
    fidelity_label: str = "paper-oriented-approximation"


@dataclass(frozen=True, slots=True)
class SftTrainingConfig:
    """Configuration for repository-local supervised orchestrator training."""

    epochs: int = 1
    learning_rate: float = 1e-4
    seed: int = 0
    backbone_name: str = "Qwen2.5-3B-Instruct"
    tokenizer_name: str = "Qwen2.5-3B-Instruct"
    prompt_template_version: str = "orchestrator-sft-v2"
    optimizer_name: str = "adamw"

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
        if not self.optimizer_name.strip():
            raise ValueError("optimizer_name must be a non-empty string")


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
    source_dataset_metadata_path: str | None = None
    source_recipe_name: str = "paper-oriented-synthetic-yaml-v1"
    paper_target_sample_count: int = 4500
    uses_reduced_paper_subset: bool = True
    scale_label: str = "reduced-scale-approximate"
    training_stage: str = "sft"
    parent_checkpoint_id: str | None = None
    optimizer_name: str | None = "adamw"
    optimizer_steps: int = 0
    average_reward: float | None = None
    runtime_kind: str = "repository_frozen_bundle"
    runtime_artifact_path: str | None = None
    weights_path: str | None = None


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
    source_dataset_metadata_path: str | None = None
    source_recipe_name: str = "paper-oriented-synthetic-yaml-v1"
    paper_target_sample_count: int = 4500
    uses_reduced_paper_subset: bool = True
    scale_label: str = "reduced-scale-approximate"
    optimizer_name: str = "adamw"
    runtime_kind: str = "repository_frozen_bundle"
    runtime_artifact_path: str | None = None
