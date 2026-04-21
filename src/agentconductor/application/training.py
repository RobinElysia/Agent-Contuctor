"""Synthetic-topology data generation and SFT baseline entrypoints."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from agentconductor.application.orchestrator import plan_topology_for_problem
from agentconductor.domain.models import DifficultyLevel, ProblemInstance
from agentconductor.domain.topology import TopologyPlan
from agentconductor.domain.training import (
    SftTrainingArtifact,
    SftTrainingConfig,
    SyntheticTopologySample,
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
        SyntheticTopologySample(
            problem_id=problem_id,
            prompt=prompt,
            difficulty=difficulty.value,
            target_topology=_serialize_topology(
                plan_topology_for_problem(
                    ProblemInstance(
                        identifier=problem_id,
                        prompt=prompt,
                        difficulty=difficulty,
                    )
                )
            ),
        )
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
        required_keys = {"problem_id", "prompt", "difficulty", "target_topology"}
        if not required_keys.issubset(payload):
            raise ValueError(
                f"SFT dataset line {line_index} must define {sorted(required_keys)}."
            )
        TopologyPlan.from_mapping(payload["target_topology"])
        samples.append(
            SyntheticTopologySample(
                problem_id=payload["problem_id"],
                prompt=payload["prompt"],
                difficulty=payload["difficulty"],
                target_topology=payload["target_topology"],
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
    """Validate the SFT dataset and write a reproducible baseline artifact."""
    active_config = config or SftTrainingConfig()
    samples = load_sft_dataset(dataset_path)
    artifact = SftTrainingArtifact(
        sample_count=len(samples),
        epochs=active_config.epochs,
        learning_rate=active_config.learning_rate,
        seed=active_config.seed,
    )
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(asdict(artifact), indent=2), encoding="utf-8")
    return artifact


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
) -> SftTrainingArtifact:
    """Public wrapper that normalizes paths and config values."""
    return run_sft_baseline(
        Path(dataset_path),
        Path(artifact_path),
        config=SftTrainingConfig(
            epochs=epochs,
            learning_rate=learning_rate,
            seed=seed,
        ),
    )


def _serialize_topology(plan: TopologyPlan) -> dict:
    return {
        "difficulty": plan.difficulty.value,
        "steps": [
            {
                "index": step.index,
                "agents": [
                    {
                        "name": agent.name,
                        "role": agent.role.value,
                        "refs": [
                            {
                                "step_index": ref.step_index,
                                "agent_name": ref.agent_name,
                            }
                            for ref in agent.refs
                        ],
                    }
                    for agent in step.agents
                ],
            }
            for step in plan.steps
        ],
    }
