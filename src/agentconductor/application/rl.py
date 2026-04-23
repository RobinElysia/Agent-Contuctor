"""Reward-driven RL checkpoint optimization built on current topology contracts."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from shutil import copyfile

from agentconductor.application.training import load_sft_dataset
from agentconductor.domain.execution import TestingOutcome
from agentconductor.domain.models import DifficultyLevel, ProblemInstance
from agentconductor.domain.rl import (
    RewardBreakdown,
    RlPolicyUpdateSummary,
    RlRolloutRecord,
    RlTrainingArtifact,
    RlTrainingConfig,
)
from agentconductor.domain.topology import MAX_NODES_BY_DIFFICULTY, TopologyPlan
from agentconductor.domain.training import OrchestratorCheckpointMetadata
from agentconductor.infrastructure.topology_yaml import dump_topology_yaml_mapping
from agentconductor.infrastructure.training_checkpoint import (
    resolve_orchestrator_checkpoint_metadata,
    write_orchestrator_checkpoint_metadata,
)
from agentconductor.interfaces.api import solve_problem


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
        "no_candidate": -0.8,
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


def collect_rl_rollouts(
    dataset_path: Path,
    *,
    checkpoint_source: str | Path,
    config: RlTrainingConfig,
    resulting_checkpoint_id: str,
) -> tuple[OrchestratorCheckpointMetadata, tuple[RlRolloutRecord, ...]]:
    """Collect inspectable rollout records through the current solve loop."""
    checkpoint_metadata = resolve_orchestrator_checkpoint_metadata(checkpoint_source)
    samples = load_sft_dataset(dataset_path)
    rollouts: list[RlRolloutRecord] = []
    for rollout_index in range(config.rollout_count):
        sample = samples[(config.seed + rollout_index) % len(samples)]
        difficulty = DifficultyLevel(sample.difficulty)
        problem = ProblemInstance(
            identifier=sample.problem_id,
            prompt=sample.prompt,
            difficulty=difficulty,
        )
        result = solve_problem(
            problem,
            max_turns=config.turn_budget,
            orchestrator_checkpoint=checkpoint_metadata.metadata_path,
            orchestrator_checkpoint_id=checkpoint_metadata.checkpoint_id,
            orchestrator_device=config.checkpoint_device,
        )
        rollout_topology = result.topology
        rollout_topology_yaml = dump_topology_yaml_mapping(rollout_topology.to_mapping())
        outcome = result.testing_outcome or TestingOutcome.FAILED
        rollouts.append(
            RlRolloutRecord(
                rollout_index=rollout_index,
                group_index=rollout_index // config.group_size,
                problem_id=sample.problem_id,
                difficulty=sample.difficulty,
                source_checkpoint_id=checkpoint_metadata.checkpoint_id,
                resulting_checkpoint_id=resulting_checkpoint_id,
                topology_node_count=rollout_topology.node_count,
                topology_yaml=rollout_topology_yaml,
                execution_outcome=outcome.value,
                reward_breakdown=compute_reward_breakdown(
                    topology=rollout_topology,
                    yaml_valid=True,
                    execution_outcome=outcome.value,
                ),
            )
        )
    return checkpoint_metadata, tuple(rollouts)


def summarize_policy_update(
    *,
    rollouts: tuple[RlRolloutRecord, ...],
    config: RlTrainingConfig,
    source_checkpoint_id: str,
    resulting_checkpoint_id: str,
) -> RlPolicyUpdateSummary:
    """Summarize one lightweight GRPO-style policy update from grouped rewards."""
    grouped_advantages: list[float] = []
    for group_start in range(0, len(rollouts), config.group_size):
        group = rollouts[group_start : group_start + config.group_size]
        group_reward = sum(item.reward_breakdown.total_reward for item in group) / len(group)
        for item in group:
            grouped_advantages.append(item.reward_breakdown.total_reward - group_reward)

    average_reward = sum(item.reward_breakdown.total_reward for item in rollouts) / len(rollouts)
    average_advantage = sum(grouped_advantages) / len(grouped_advantages)
    return RlPolicyUpdateSummary(
        optimizer_name=config.optimizer_name,
        source_checkpoint_id=source_checkpoint_id,
        resulting_checkpoint_id=resulting_checkpoint_id,
        rollout_count=len(rollouts),
        group_size=config.group_size,
        average_reward=average_reward,
        average_advantage=average_advantage,
        applied_update_scale=config.optimizer_learning_rate * average_reward,
        optimizer_steps=len(rollouts) // config.group_size,
    )


def write_rl_checkpoint(
    *,
    artifact_path: Path,
    dataset_path: Path,
    source_checkpoint: OrchestratorCheckpointMetadata,
    rollout_manifest_path: Path,
    update_summary: RlPolicyUpdateSummary,
) -> OrchestratorCheckpointMetadata:
    """Write the updated repository-local checkpoint metadata and stub weights."""
    checkpoint_dir = artifact_path.with_name(f"{artifact_path.stem}-checkpoint")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    runtime_artifact_path = checkpoint_dir / "orchestrator-runtime.json"
    source_weights = Path(source_checkpoint.checkpoint_path) / "weights.stub"
    target_weights = checkpoint_dir / "weights.stub"
    if source_weights.exists():
        copyfile(source_weights, target_weights)
        updated_weights = target_weights.read_text(encoding="utf-8")
    else:
        updated_weights = "repository-local placeholder for RL-updated orchestrator weights\n"
    target_weights.write_text(
        updated_weights
        + (
            "rl_update: "
            f"optimizer={update_summary.optimizer_name}, "
            f"source={update_summary.source_checkpoint_id}, "
            f"reward={update_summary.average_reward:.4f}, "
            f"scale={update_summary.applied_update_scale:.8f}\n"
        ),
        encoding="utf-8",
    )
    if source_checkpoint.runtime_artifact_path is not None:
        source_runtime_artifact = Path(source_checkpoint.runtime_artifact_path)
        if source_runtime_artifact.exists():
            copyfile(source_runtime_artifact, runtime_artifact_path)

    metadata = OrchestratorCheckpointMetadata(
        checkpoint_id=update_summary.resulting_checkpoint_id,
        checkpoint_path=str(checkpoint_dir),
        metadata_path=str(checkpoint_dir / "checkpoint.json"),
        dataset_path=str(dataset_path),
        training_manifest_path=str(rollout_manifest_path),
        sample_count=update_summary.rollout_count,
        target_format=source_checkpoint.target_format,
        backbone_name=source_checkpoint.backbone_name,
        tokenizer_name=source_checkpoint.tokenizer_name,
        prompt_template_version=source_checkpoint.prompt_template_version,
        epochs=source_checkpoint.epochs,
        learning_rate=update_summary.applied_update_scale,
        seed=source_checkpoint.seed,
        training_stage="rl",
        parent_checkpoint_id=source_checkpoint.checkpoint_id,
        optimizer_name=update_summary.optimizer_name,
        optimizer_steps=update_summary.optimizer_steps,
        average_reward=update_summary.average_reward,
        runtime_kind=source_checkpoint.runtime_kind,
        runtime_artifact_path=(
            str(runtime_artifact_path)
            if runtime_artifact_path.exists()
            else source_checkpoint.runtime_artifact_path
        ),
        weights_path=str(target_weights),
    )
    write_orchestrator_checkpoint_metadata(checkpoint_dir, metadata)
    return metadata


def run_rl_baseline(
    dataset_path: Path,
    artifact_path: Path,
    *,
    checkpoint_source: str | Path,
    config: RlTrainingConfig | None = None,
) -> RlTrainingArtifact:
    """Run the repository-local RL path and emit an updated checkpoint artifact."""
    active_config = config or RlTrainingConfig()
    resulting_checkpoint_id = (
        f"rl-grpo-{active_config.optimizer_name}"
        f"-seed{active_config.seed}"
        f"-rollouts{active_config.rollout_count}"
    )
    source_checkpoint, rollouts = collect_rl_rollouts(
        dataset_path,
        checkpoint_source=checkpoint_source,
        config=active_config,
        resulting_checkpoint_id=resulting_checkpoint_id,
    )
    update_summary = summarize_policy_update(
        rollouts=rollouts,
        config=active_config,
        source_checkpoint_id=source_checkpoint.checkpoint_id,
        resulting_checkpoint_id=resulting_checkpoint_id,
    )
    rollout_manifest_path = artifact_path.with_name(f"{artifact_path.stem}.rollouts.jsonl")
    _write_rollout_manifest(rollouts=rollouts, manifest_path=rollout_manifest_path)
    updated_checkpoint = write_rl_checkpoint(
        artifact_path=artifact_path,
        dataset_path=dataset_path,
        source_checkpoint=source_checkpoint,
        rollout_manifest_path=rollout_manifest_path,
        update_summary=update_summary,
    )
    artifact = RlTrainingArtifact(
        dataset_path=str(dataset_path),
        source_checkpoint_id=source_checkpoint.checkpoint_id,
        source_checkpoint_path=source_checkpoint.checkpoint_path,
        rollout_manifest_path=str(rollout_manifest_path),
        checkpoint_id=updated_checkpoint.checkpoint_id,
        checkpoint_path=updated_checkpoint.checkpoint_path,
        checkpoint_metadata_path=updated_checkpoint.metadata_path,
        rollout_count=len(rollouts),
        group_size=active_config.group_size,
        turn_budget=active_config.turn_budget,
        optimizer_name=active_config.optimizer_name,
        optimizer_learning_rate=active_config.optimizer_learning_rate,
        average_reward=update_summary.average_reward,
        average_advantage=update_summary.average_advantage,
        seed=active_config.seed,
    )
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        json.dumps(
            {
                "artifact": asdict(artifact),
                "rollout_records": [asdict(rollout) for rollout in rollouts],
                "policy_update": asdict(update_summary),
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
    checkpoint_source: str | Path,
    rollout_count: int = 4,
    group_size: int = 2,
    turn_budget: int = 2,
    seed: int = 0,
    optimizer_learning_rate: float = 1e-5,
    optimizer_name: str = "grpo-stub",
    checkpoint_device: str = "cpu",
) -> RlTrainingArtifact:
    """Public wrapper that normalizes RL checkpoint-optimization config values."""
    return run_rl_baseline(
        Path(dataset_path),
        Path(artifact_path),
        checkpoint_source=checkpoint_source,
        config=RlTrainingConfig(
            rollout_count=rollout_count,
            group_size=group_size,
            turn_budget=turn_budget,
            seed=seed,
            optimizer_learning_rate=optimizer_learning_rate,
            optimizer_name=optimizer_name,
            checkpoint_device=checkpoint_device,
        ),
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


def _write_rollout_manifest(
    *,
    rollouts: tuple[RlRolloutRecord, ...],
    manifest_path: Path,
) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        "".join(json.dumps(asdict(rollout)) + "\n" for rollout in rollouts),
        encoding="utf-8",
    )
