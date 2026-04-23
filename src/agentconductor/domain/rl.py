"""Typed contracts for repository-local RL checkpoint optimization."""

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
class RlRolloutRecord:
    """One rollout record used by the repository-local RL stage."""

    rollout_index: int
    group_index: int
    problem_id: str
    difficulty: str
    source_checkpoint_id: str
    resulting_checkpoint_id: str
    topology_node_count: int
    topology_yaml: str
    execution_outcome: str
    turn_count: int
    reward_breakdown: RewardBreakdown


@dataclass(frozen=True, slots=True)
class RlAdvantageRecord:
    """One inspectable grouped-advantage record for a rollout."""

    rollout_index: int
    group_index: int
    total_reward: float
    group_mean_reward: float
    group_reward_stddev: float
    normalized_advantage: float


@dataclass(frozen=True, slots=True)
class RlRolloutGroupSummary:
    """Inspectable grouped-rollout statistics used by the policy update."""

    group_index: int
    rollout_indices: tuple[int, ...]
    mean_reward: float
    reward_stddev: float
    min_reward: float
    max_reward: float


@dataclass(frozen=True, slots=True)
class RlPolicyUpdateSummary:
    """Inspectable summary of one paper-oriented GRPO-style policy update."""

    optimizer_name: str
    source_checkpoint_id: str
    resulting_checkpoint_id: str
    rollout_count: int
    group_size: int
    group_count: int
    turn_budget: int
    advantage_estimator: str
    normalization_epsilon: float
    average_reward: float
    average_advantage: float
    average_group_reward: float
    max_abs_advantage: float
    applied_update_scale: float
    optimizer_steps: int


@dataclass(frozen=True, slots=True)
class RlTrainingConfig:
    """Configuration for repository-local RL checkpoint optimization."""

    rollout_count: int = 8
    group_size: int = 8
    turn_budget: int = 2
    seed: int = 0
    optimizer_learning_rate: float = 1e-5
    optimizer_name: str = "grpo-paper-oriented"
    advantage_epsilon: float = 1e-6
    checkpoint_device: str = "cpu"

    def __post_init__(self) -> None:
        if self.rollout_count < 1:
            raise ValueError("rollout_count must be at least 1")
        if self.group_size < 1:
            raise ValueError("group_size must be at least 1")
        if self.rollout_count % self.group_size != 0:
            raise ValueError("rollout_count must be divisible by group_size")
        if self.turn_budget < 1:
            raise ValueError("turn_budget must be at least 1")
        if self.optimizer_learning_rate <= 0:
            raise ValueError("optimizer_learning_rate must be > 0")
        if self.advantage_epsilon <= 0:
            raise ValueError("advantage_epsilon must be > 0")
        if not self.optimizer_name.strip():
            raise ValueError("optimizer_name must be a non-empty string")
        if not self.checkpoint_device.strip():
            raise ValueError("checkpoint_device must be a non-empty string")


@dataclass(frozen=True, slots=True)
class RlTrainingArtifact:
    """Inspectable artifact written by the RL training entrypoint."""

    dataset_path: str
    source_checkpoint_id: str
    source_checkpoint_path: str
    rollout_manifest_path: str
    grouped_update_path: str
    checkpoint_id: str
    checkpoint_path: str
    checkpoint_metadata_path: str
    rollout_count: int
    group_size: int
    turn_budget: int
    optimizer_name: str
    optimizer_learning_rate: float
    advantage_estimator: str
    average_reward: float
    average_advantage: float
    seed: int
