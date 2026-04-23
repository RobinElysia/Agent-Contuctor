"""Synthetic-topology data generation and SFT baseline entrypoints."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from agentconductor.application.orchestrator import plan_topology_for_problem
from agentconductor.domain.models import DifficultyLevel, ProblemInstance
from agentconductor.domain.topology import TopologyPlan
from agentconductor.domain.training import (
    OrchestratorCheckpointMetadata,
    SftTrainingArtifact,
    SftTrainingConfig,
    SyntheticTopologySample,
)
from agentconductor.infrastructure.topology_yaml import dump_topology_yaml_mapping, parse_topology_plan_yaml
from agentconductor.infrastructure.training_checkpoint import (
    load_orchestrator_checkpoint_metadata,
    write_orchestrator_checkpoint_metadata,
)

_SYNTHETIC_PROBLEMS = (
    (
        DifficultyLevel.EASY,
        "sft-easy-sum",
        "Write a function that returns two values added together.",
    ),
    (
        DifficultyLevel.MEDIUM,
        "sft-medium-graph",
        "Solve a graph shortest path problem under tight constraints.",
    ),
    (
        DifficultyLevel.HARD,
        "sft-hard-debug",
        "Debug a failing dynamic programming solution with incorrect edge-case handling.",
    ),
)


def generate_sft_dataset(dataset_path: Path) -> tuple[SyntheticTopologySample, ...]:
    """Generate a deterministic schema-valid SFT dataset and write JSONL."""
    samples = tuple(
        _build_synthetic_sample(difficulty=difficulty, problem_id=problem_id, prompt=prompt)
        for difficulty, problem_id, prompt in _SYNTHETIC_PROBLEMS
    )
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    dataset_path.write_text(
        "".join(json.dumps(asdict(sample)) + "\n" for sample in samples),
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
    training_manifest_path = artifact_path.with_name(f"{artifact_path.stem}.train.jsonl")
    checkpoint_dir = artifact_path.with_name(f"{artifact_path.stem}-checkpoint")
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
    )
    metadata_path = write_orchestrator_checkpoint_metadata(checkpoint_dir, metadata)
    (checkpoint_dir / "weights.stub").write_text(
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
    )
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(asdict(artifact), indent=2), encoding="utf-8")
    return artifact


def load_sft_checkpoint(checkpoint_path: Path) -> OrchestratorCheckpointMetadata:
    """Load repository-local orchestrator checkpoint metadata."""
    return load_orchestrator_checkpoint_metadata(checkpoint_path)


def generate_sft_dataset_entrypoint(dataset_path: str | Path):
    """Public wrapper that normalizes the dataset path."""
    return generate_sft_dataset(Path(dataset_path))


def run_sft_baseline_entrypoint(
    dataset_path: str | Path,
    artifact_path: str | Path,
    *,
    epochs: int = 1,
    learning_rate: float = 1e-4,
    seed: int = 0,
    backbone_name: str = "Qwen2.5-3B-Instruct",
    tokenizer_name: str = "Qwen2.5-3B-Instruct",
    prompt_template_version: str = "orchestrator-sft-v1",
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
