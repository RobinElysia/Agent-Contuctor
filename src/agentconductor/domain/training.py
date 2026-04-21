"""Typed contracts for the repository-local SFT baseline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SyntheticTopologySample:
    """One schema-valid SFT training sample for the orchestrator."""

    problem_id: str
    prompt: str
    difficulty: str
    target_topology: dict


@dataclass(frozen=True, slots=True)
class SftTrainingConfig:
    """Configuration for the repository-local supervised baseline."""

    epochs: int = 1
    learning_rate: float = 1e-4
    seed: int = 0

    def __post_init__(self) -> None:
        if self.epochs < 1:
            raise ValueError("epochs must be at least 1")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be > 0")


@dataclass(frozen=True, slots=True)
class SftTrainingArtifact:
    """Inspectable artifact written by the SFT baseline entrypoint."""

    sample_count: int
    epochs: int
    learning_rate: float
    seed: int
