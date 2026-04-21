"""Reward-driven RL baseline built on the current topology contracts."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from agentconductor.application.training import load_sft_dataset
from agentconductor.domain.rl import RewardBreakdown, RlTrainingArtifact, RlTrainingConfig
from agentconductor.domain.topology import MAX_NODES_BY_DIFFICULTY, TopologyPlan


def compute_reward_breakdown(
    *,
    topology: TopologyPlan,
    yaml_valid: bool,
    execution_outcome: str,
) -> RewardBreakdown:
    """Compute the repository-local reward components for one topology."""
    yaml_reward = 0.0 if yaml_valid else -1.0
    execution_reward = {
        "passed": 1.0,
        "wrong_answer": -0.3,
        "time_limit_exceeded": -0.5,
        "memory_limit_exceeded": -0.5,
        "runtime_error": -0.7,
        "compilation_error": -0.8,
        "failed": -0.6,
    }.get(execution_outcome, -0.6)

    edge_count = sum(len(agent.refs) for step in topology.steps for agent in step.agents)
    depth = len(topology.steps)
    max_nodes = MAX_NODES_BY_DIFFICULTY[topology.difficulty]
    node_budget_ratio = topology.node_count / max_nodes
    density_penalty = min(
        1.0,
        node_budget_ratio + (edge_count / max(1, topology.node_count)) * 0.25,
    )
    depth_penalty = depth / max(1, max_nodes)
    density_reward = 1.0 - density_penalty - depth_penalty

    total_reward = yaml_reward + execution_reward + density_reward
    return RewardBreakdown(
        yaml_reward=yaml_reward,
        execution_reward=execution_reward,
        density_reward=density_reward,
        total_reward=total_reward,
    )


def run_rl_baseline(
    dataset_path: Path,
    artifact_path: Path,
    *,
    config: RlTrainingConfig | None = None,
) -> RlTrainingArtifact:
    """Run a deterministic RL-style rollout loop over the SFT dataset."""
    active_config = config or RlTrainingConfig()
    samples = load_sft_dataset(dataset_path)
    rewards: list[RewardBreakdown] = []
    for rollout_index in range(active_config.rollouts):
        sample = samples[rollout_index % len(samples)]
        topology = TopologyPlan.from_mapping(sample.target_topology)
        rewards.append(
            compute_reward_breakdown(
                topology=topology,
                yaml_valid=True,
                execution_outcome=(
                    "passed" if topology.node_count <= topology.max_nodes else "failed"
                ),
            )
        )

    artifact = RlTrainingArtifact(
        rollout_count=len(rewards),
        average_reward=sum(reward.total_reward for reward in rewards) / len(rewards),
    )
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        json.dumps(
            {
                "artifact": asdict(artifact),
                "reward_breakdowns": [asdict(reward) for reward in rewards],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return artifact


def run_rl_baseline_entrypoint(
    dataset_path: str | Path,
    artifact_path: str | Path,
    *,
    rollouts: int = 1,
    seed: int = 0,
) -> RlTrainingArtifact:
    """Public wrapper that normalizes paths and config values."""
    return run_rl_baseline(
        Path(dataset_path),
        Path(artifact_path),
        config=RlTrainingConfig(rollouts=rollouts, seed=seed),
    )


def compute_reward_breakdown_entrypoint(
    topology: dict,
    *,
    yaml_valid: bool,
    execution_outcome: str,
) -> RewardBreakdown:
    """Public wrapper that accepts serialized topology input."""
    return compute_reward_breakdown(
        topology=TopologyPlan.from_mapping(topology),
        yaml_valid=yaml_valid,
        execution_outcome=execution_outcome,
    )
