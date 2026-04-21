"""Typed contracts for the repository-local RL baseline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RewardBreakdown:
    """Inspectable reward components for one rollout sample."""

    yaml_reward: float
    execution_reward: float
    density_reward: float
    total_reward: float


@dataclass(frozen=True, slots=True)
class RlTrainingConfig:
    """Configuration for the repository-local RL baseline."""

    rollouts: int = 1
    seed: int = 0

    def __post_init__(self) -> None:
        if self.rollouts < 1:
            raise ValueError("rollouts must be at least 1")


@dataclass(frozen=True, slots=True)
class RlTrainingArtifact:
    """Inspectable artifact written by the RL baseline entrypoint."""

    rollout_count: int
    average_reward: float
