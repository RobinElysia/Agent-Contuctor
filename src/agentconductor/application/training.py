"""Synthetic-topology data generation and SFT baseline entrypoints."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from agentconductor.application.orchestrator import (
    plan_topology_for_problem,
    revise_topology_for_feedback,
)
from agentconductor.domain.execution import ExecutionStatus, TestingOutcome
from agentconductor.domain.history import TestingFeedback, TopologyRevisionInput
from agentconductor.domain.models import DifficultyLevel, ProblemInstance
from agentconductor.domain.topology import TopologyPlan
from agentconductor.domain.training import (
    OrchestratorCheckpointMetadata,
    SftDatasetConfig,
    SftDatasetMetadata,
    SftTrainingArtifact,
    SftTrainingConfig,
    SyntheticTopologySample,
)
from agentconductor.infrastructure.topology_yaml import dump_topology_yaml_mapping, parse_topology_plan_yaml
from agentconductor.infrastructure.training_checkpoint import (
    load_orchestrator_checkpoint_metadata,
    write_orchestrator_checkpoint_metadata,
)

_DIFFICULTY_ORDER = (
    DifficultyLevel.EASY,
    DifficultyLevel.MEDIUM,
    DifficultyLevel.HARD,
)

_SUBJECTS = {
    DifficultyLevel.EASY: (
        "two integers",
        "a short list of values",
        "a pair of coordinates",
        "a string and an offset",
        "daily transaction counts",
    ),
    DifficultyLevel.MEDIUM: (
        "a weighted graph",
        "an interval scheduling table",
        "a dependency DAG",
        "a monotonic queue window",
        "a binary-search feasibility check",
    ),
    DifficultyLevel.HARD: (
        "a dynamic-programming table with broken transitions",
        "a tree rerooting implementation with state leakage",
        "a shortest-path solver with overflow on edge relaxation",
        "a segment-tree update path with inconsistent lazy propagation",
        "a search routine that fails on adversarial corner cases",
    ),
}

_CONSTRAINTS = {
    DifficultyLevel.EASY: (
        "with straightforward correctness checks",
        "while keeping the implementation minimal",
        "under a tiny edge-case set",
        "for a short interview-style prompt",
    ),
    DifficultyLevel.MEDIUM: (
        "under tight asymptotic constraints",
        "while preserving correctness on sparse and dense cases",
        "with at least one optimization step required",
        "for inputs large enough to punish naive enumeration",
    ),
    DifficultyLevel.HARD: (
        "after earlier submissions failed hidden tests",
        "with multiple interacting edge cases",
        "where naive fixes regress a previously passing case",
        "under debugging pressure from contradictory traces",
    ),
}

_PROMPT_TEMPLATES = {
    DifficultyLevel.EASY: (
        (
            "easy-direct",
            "Write a function that processes {subject} {constraint}. Return the final answer only.",
        ),
        (
            "easy-checks",
            "Implement a small utility over {subject} {constraint}. Mentioned examples must continue to pass.",
        ),
    ),
    DifficultyLevel.MEDIUM: (
        (
            "medium-optimized",
            "Solve a coding problem over {subject} {constraint}. The solution should explain the intended optimization before coding.",
        ),
        (
            "medium-graph",
            "Design and implement an algorithm for {subject} {constraint}. Watch for off-by-one and initialization mistakes.",
        ),
    ),
    DifficultyLevel.HARD: (
        (
            "hard-debug",
            "Debug and repair a failing solution around {subject} {constraint}. Provide a corrected implementation after isolating the bug.",
        ),
        (
            "hard-revision",
            "A previous attempt on {subject} is wrong {constraint}. Analyze the failure mode, revise the plan, and produce fixed code.",
        ),
    ),
}


def generate_sft_dataset(
    dataset_path: Path,
    *,
    config: SftDatasetConfig | None = None,
) -> tuple[SyntheticTopologySample, ...]:
    """Generate a deterministic schema-valid SFT dataset and write JSONL."""
    active_config = config or SftDatasetConfig()
    samples = tuple(_build_dataset_samples(active_config))
    dataset_metadata = _build_dataset_metadata(dataset_path=dataset_path, samples=samples, config=active_config)
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    dataset_path.write_text(
        "".join(json.dumps(asdict(sample)) + "\n" for sample in samples),
        encoding="utf-8",
    )
    Path(dataset_metadata.metadata_path).write_text(
        json.dumps(asdict(dataset_metadata), indent=2),
        encoding="utf-8",
    )
    return samples


def load_sft_dataset(dataset_path: Path) -> tuple[SyntheticTopologySample, ...]:
    """Load and validate the JSONL SFT dataset."""
    samples: list[SyntheticTopologySample] = []
    for line_index, raw_line in enumerate(
        dataset_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not raw_line.strip():
            continue
        payload = json.loads(raw_line)
        if not isinstance(payload, dict):
            raise ValueError(f"SFT dataset line {line_index} must be an object.")
        required_keys = {
            "problem_id",
            "prompt",
            "difficulty",
            "source_template_id",
            "prompt_variant",
            "target_topology",
            "target_topology_yaml",
        }
        if not required_keys.issubset(payload):
            raise ValueError(
                f"SFT dataset line {line_index} must define {sorted(required_keys)}."
            )
        parsed_mapping = TopologyPlan.from_mapping(payload["target_topology"]).to_mapping()
        parsed_yaml = parse_topology_plan_yaml(payload["target_topology_yaml"]).to_mapping()
        if parsed_mapping != parsed_yaml:
            raise ValueError(
                f"SFT dataset line {line_index} must keep target_topology and "
                "target_topology_yaml in sync."
            )
        samples.append(
            SyntheticTopologySample(
                problem_id=payload["problem_id"],
                prompt=payload["prompt"],
                difficulty=payload["difficulty"],
                source_template_id=payload["source_template_id"],
                prompt_variant=payload["prompt_variant"],
                target_topology=payload["target_topology"],
                target_topology_yaml=payload["target_topology_yaml"],
            )
        )
    if not samples:
        raise ValueError("SFT dataset must contain at least one sample.")
    return tuple(samples)


def run_sft_baseline(
    dataset_path: Path,
    artifact_path: Path,
    *,
    config: SftTrainingConfig | None = None,
) -> SftTrainingArtifact:
    """Validate the SFT dataset and write a reproducible checkpoint artifact."""
    active_config = config or SftTrainingConfig()
    samples = load_sft_dataset(dataset_path)
    dataset_metadata = load_sft_dataset_metadata(dataset_path)
    training_manifest_path = artifact_path.with_name(f"{artifact_path.stem}.train.jsonl")
    checkpoint_dir = artifact_path.with_name(f"{artifact_path.stem}-checkpoint")
    runtime_artifact_path = checkpoint_dir / "orchestrator-runtime.json"
    weights_path = checkpoint_dir / "weights.stub"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    training_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    _write_training_manifest(samples=samples, manifest_path=training_manifest_path)

    checkpoint_id = (
        f"sft-{_slugify(active_config.backbone_name)}"
        f"-seed{active_config.seed}"
        f"-samples{len(samples)}"
    )
    metadata = OrchestratorCheckpointMetadata(
        checkpoint_id=checkpoint_id,
        checkpoint_path=str(checkpoint_dir),
        metadata_path=str(checkpoint_dir / "checkpoint.json"),
        dataset_path=str(dataset_path),
        training_manifest_path=str(training_manifest_path),
        sample_count=len(samples),
        target_format="yaml",
        backbone_name=active_config.backbone_name,
        tokenizer_name=active_config.tokenizer_name,
        prompt_template_version=active_config.prompt_template_version,
        epochs=active_config.epochs,
        learning_rate=active_config.learning_rate,
        seed=active_config.seed,
        source_dataset_metadata_path=dataset_metadata.metadata_path,
        source_recipe_name=dataset_metadata.source_recipe_name,
        paper_target_sample_count=dataset_metadata.paper_target_sample_count,
        uses_reduced_paper_subset=dataset_metadata.uses_reduced_paper_subset,
        scale_label=_build_scale_label(
            sample_count=len(samples),
            paper_target_sample_count=dataset_metadata.paper_target_sample_count,
            backbone_name=active_config.backbone_name,
            tokenizer_name=active_config.tokenizer_name,
        ),
        optimizer_name=active_config.optimizer_name,
        runtime_kind="repository_frozen_bundle",
        runtime_artifact_path=str(runtime_artifact_path),
        weights_path=str(weights_path),
    )
    _write_orchestrator_runtime_bundle(
        samples=samples,
        runtime_artifact_path=runtime_artifact_path,
        config=active_config,
        dataset_metadata=dataset_metadata,
        scale_label=metadata.scale_label,
    )
    metadata_path = write_orchestrator_checkpoint_metadata(checkpoint_dir, metadata)
    weights_path.write_text(
        "repository-local placeholder for supervised orchestrator weights\n",
        encoding="utf-8",
    )
    artifact = SftTrainingArtifact(
        dataset_path=str(dataset_path),
        training_manifest_path=str(training_manifest_path),
        checkpoint_id=checkpoint_id,
        checkpoint_path=str(checkpoint_dir),
        checkpoint_metadata_path=str(metadata_path),
        sample_count=len(samples),
        target_format="yaml",
        backbone_name=active_config.backbone_name,
        tokenizer_name=active_config.tokenizer_name,
        prompt_template_version=active_config.prompt_template_version,
        epochs=active_config.epochs,
        learning_rate=active_config.learning_rate,
        seed=active_config.seed,
        source_dataset_metadata_path=dataset_metadata.metadata_path,
        source_recipe_name=dataset_metadata.source_recipe_name,
        paper_target_sample_count=dataset_metadata.paper_target_sample_count,
        uses_reduced_paper_subset=dataset_metadata.uses_reduced_paper_subset,
        scale_label=metadata.scale_label,
        optimizer_name=active_config.optimizer_name,
        runtime_kind=metadata.runtime_kind,
        runtime_artifact_path=str(runtime_artifact_path),
    )
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(asdict(artifact), indent=2), encoding="utf-8")
    return artifact


def load_sft_checkpoint(checkpoint_path: Path) -> OrchestratorCheckpointMetadata:
    """Load repository-local orchestrator checkpoint metadata."""
    return load_orchestrator_checkpoint_metadata(checkpoint_path)


def generate_sft_dataset_entrypoint(
    dataset_path: str | Path,
    *,
    sample_count: int = 4500,
    seed: int = 0,
    prompt_template_version: str = "orchestrator-sft-v2",
    source_recipe_name: str = "paper-oriented-synthetic-yaml-v1",
):
    """Public wrapper that normalizes the dataset path."""
    return generate_sft_dataset(
        Path(dataset_path),
        config=SftDatasetConfig(
            sample_count=sample_count,
            seed=seed,
            prompt_template_version=prompt_template_version,
            source_recipe_name=source_recipe_name,
        ),
    )


def run_sft_baseline_entrypoint(
    dataset_path: str | Path,
    artifact_path: str | Path,
    *,
    epochs: int = 1,
    learning_rate: float = 1e-4,
    seed: int = 0,
    backbone_name: str = "Qwen2.5-3B-Instruct",
    tokenizer_name: str = "Qwen2.5-3B-Instruct",
    prompt_template_version: str = "orchestrator-sft-v2",
    optimizer_name: str = "adamw",
) -> SftTrainingArtifact:
    """Public wrapper that normalizes paths and config values."""
    return run_sft_baseline(
        Path(dataset_path),
        Path(artifact_path),
        config=SftTrainingConfig(
            epochs=epochs,
            learning_rate=learning_rate,
            seed=seed,
            backbone_name=backbone_name,
            tokenizer_name=tokenizer_name,
            prompt_template_version=prompt_template_version,
            optimizer_name=optimizer_name,
        ),
    )


def load_sft_checkpoint_entrypoint(
    checkpoint_path: str | Path,
) -> OrchestratorCheckpointMetadata:
    """Public wrapper that normalizes a checkpoint path."""
    return load_sft_checkpoint(Path(checkpoint_path))


def _build_synthetic_sample(
    *,
    difficulty: DifficultyLevel,
    problem_id: str,
    prompt: str,
    source_template_id: str,
    prompt_variant: int,
) -> SyntheticTopologySample:
    topology = plan_topology_for_problem(
        ProblemInstance(
            identifier=problem_id,
            prompt=prompt,
            difficulty=difficulty,
        )
    )
    topology_mapping = topology.to_mapping()
    return SyntheticTopologySample(
        problem_id=problem_id,
        prompt=prompt,
        difficulty=difficulty.value,
        source_template_id=source_template_id,
        prompt_variant=prompt_variant,
        target_topology=topology_mapping,
        target_topology_yaml=dump_topology_yaml_mapping(topology_mapping),
    )


def _write_training_manifest(
    *,
    samples: tuple[SyntheticTopologySample, ...],
    manifest_path: Path,
) -> None:
    manifest_path.write_text(
        "".join(
            json.dumps(
                {
                    "problem_id": sample.problem_id,
                    "difficulty": sample.difficulty,
                    "source_template_id": sample.source_template_id,
                    "prompt_variant": sample.prompt_variant,
                    "input_prompt": sample.prompt,
                    "target_topology_yaml": sample.target_topology_yaml,
                }
            )
            + "\n"
            for sample in samples
        ),
        encoding="utf-8",
    )


def _slugify(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "-" for character in value).strip("-")


def _write_orchestrator_runtime_bundle(
    *,
    samples: tuple[SyntheticTopologySample, ...],
    runtime_artifact_path: Path,
    config: SftTrainingConfig,
    dataset_metadata: SftDatasetMetadata,
    scale_label: str,
) -> None:
    runtime_artifact_path.write_text(
        json.dumps(
            {
                "runtime_kind": "repository_frozen_bundle",
                "backbone_name": config.backbone_name,
                "tokenizer_name": config.tokenizer_name,
                "prompt_template_version": config.prompt_template_version,
                "optimizer_name": config.optimizer_name,
                "source_recipe_name": dataset_metadata.source_recipe_name,
                "sample_count": dataset_metadata.sample_count,
                "paper_target_sample_count": dataset_metadata.paper_target_sample_count,
                "uses_reduced_paper_subset": dataset_metadata.uses_reduced_paper_subset,
                "scale_label": scale_label,
                "supported_devices": ["cpu"],
                "initial_candidates": {
                    sample.difficulty: sample.target_topology_yaml for sample in samples
                },
                "revision_candidates": {
                    sample.difficulty: _build_revision_topology_yaml(sample)
                    for sample in samples
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _build_revision_topology_yaml(sample: SyntheticTopologySample) -> str:
    difficulty = DifficultyLevel(sample.difficulty)
    problem = ProblemInstance(
        identifier=sample.problem_id,
        prompt=sample.prompt,
        difficulty=difficulty,
    )
    revised_topology = revise_topology_for_feedback(
        TopologyRevisionInput(
            problem=problem,
            selected_difficulty=difficulty,
            turn_index=1,
            prior_topology=TopologyPlan.from_mapping(sample.target_topology),
            prior_execution_status=ExecutionStatus.COMPLETED,
            testing_feedback=TestingFeedback(
                outcome=TestingOutcome.FAILED,
                diagnostics=("Synthetic training failure for frozen-inference revision.",),
                candidate_code="def solve():\n    return 'wrong'\n",
            ),
            remaining_turns=1,
        )
    )
    return dump_topology_yaml_mapping(revised_topology.to_mapping())


def load_sft_dataset_metadata(dataset_path: Path) -> SftDatasetMetadata:
    """Load dataset metadata or infer a reduced-scale fallback for older datasets."""
    metadata_path = _dataset_metadata_path(dataset_path)
    if metadata_path.exists():
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("SFT dataset metadata must be a JSON object.")
        return SftDatasetMetadata(
            dataset_path=payload["dataset_path"],
            metadata_path=payload["metadata_path"],
            sample_count=payload["sample_count"],
            paper_target_sample_count=payload.get("paper_target_sample_count", 4500),
            uses_reduced_paper_subset=payload.get("uses_reduced_paper_subset", True),
            source_recipe_name=payload.get(
                "source_recipe_name",
                "paper-oriented-synthetic-yaml-v1",
            ),
            prompt_template_version=payload.get(
                "prompt_template_version",
                "orchestrator-sft-v2",
            ),
            seed=payload.get("seed", 0),
            difficulty_breakdown=payload.get("difficulty_breakdown", {}),
            topology_source=payload.get("topology_source", "deterministic_orchestrator"),
            fidelity_label=payload.get("fidelity_label", "paper-oriented-approximation"),
        )
    samples = load_sft_dataset(dataset_path)
    return _build_dataset_metadata(
        dataset_path=dataset_path,
        samples=samples,
        config=SftDatasetConfig(sample_count=len(samples)),
    )


def _build_dataset_samples(config: SftDatasetConfig) -> list[SyntheticTopologySample]:
    samples: list[SyntheticTopologySample] = []
    for difficulty, count in _build_difficulty_counts(config.sample_count).items():
        templates = _PROMPT_TEMPLATES[difficulty]
        subjects = _SUBJECTS[difficulty]
        constraints = _CONSTRAINTS[difficulty]
        for variant_index in range(count):
            template_index = (variant_index + config.seed) % len(templates)
            subject_index = (variant_index * 2 + config.seed) % len(subjects)
            constraint_index = (variant_index * 3 + config.seed) % len(constraints)
            template_id, prompt_template = templates[template_index]
            problem_id = f"sft-{difficulty.value}-{variant_index:04d}"
            prompt = prompt_template.format(
                subject=subjects[subject_index],
                constraint=constraints[constraint_index],
            )
            samples.append(
                _build_synthetic_sample(
                    difficulty=difficulty,
                    problem_id=problem_id,
                    prompt=prompt,
                    source_template_id=template_id,
                    prompt_variant=variant_index,
                )
            )
    return samples


def _build_dataset_metadata(
    *,
    dataset_path: Path,
    samples: tuple[SyntheticTopologySample, ...] | list[SyntheticTopologySample],
    config: SftDatasetConfig,
) -> SftDatasetMetadata:
    difficulty_breakdown = dict(Counter(sample.difficulty for sample in samples))
    return SftDatasetMetadata(
        dataset_path=str(dataset_path),
        metadata_path=str(_dataset_metadata_path(dataset_path)),
        sample_count=len(samples),
        paper_target_sample_count=config.paper_target_sample_count,
        uses_reduced_paper_subset=len(samples) < config.paper_target_sample_count,
        source_recipe_name=config.source_recipe_name,
        prompt_template_version=config.prompt_template_version,
        seed=config.seed,
        difficulty_breakdown=difficulty_breakdown,
    )


def _build_difficulty_counts(sample_count: int) -> dict[DifficultyLevel, int]:
    base_count, remainder = divmod(sample_count, len(_DIFFICULTY_ORDER))
    counts = {difficulty: base_count for difficulty in _DIFFICULTY_ORDER}
    for difficulty in _DIFFICULTY_ORDER[:remainder]:
        counts[difficulty] += 1
    return counts


def _dataset_metadata_path(dataset_path: Path) -> Path:
    return dataset_path.with_suffix(f"{dataset_path.suffix}.metadata.json")


def _build_scale_label(
    *,
    sample_count: int,
    paper_target_sample_count: int,
    backbone_name: str,
    tokenizer_name: str,
) -> str:
    if (
        sample_count >= paper_target_sample_count
        and backbone_name == "Qwen2.5-3B-Instruct"
        and tokenizer_name == "Qwen2.5-3B-Instruct"
    ):
        return "paper-target-size-approximate"
    return "reduced-scale-approximate"
