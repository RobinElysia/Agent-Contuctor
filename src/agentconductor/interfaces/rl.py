"""Public entrypoints for the repository-local RL baseline."""

from __future__ import annotations

import argparse

from agentconductor.application.rl import (
    compute_reward_breakdown_entrypoint,
    run_rl_baseline_entrypoint,
)


def main() -> None:
    """CLI entrypoint for repository-local RL checkpoint optimization."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="Path to the SFT dataset JSONL file.")
    parser.add_argument("--artifact", required=True, help="Path to the RL artifact JSON file.")
    parser.add_argument(
        "--checkpoint",
        required=True,
        help="Path to the source checkpoint directory, metadata file, or training artifact.",
    )
    parser.add_argument("--rollout-count", type=int, default=4)
    parser.add_argument("--group-size", type=int, default=2)
    parser.add_argument("--turn-budget", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--optimizer-learning-rate", type=float, default=1e-5)
    parser.add_argument("--optimizer-name", default="grpo-stub")
    parser.add_argument("--checkpoint-device", default="cpu")
    args = parser.parse_args()

    run_rl_baseline_entrypoint(
        args.dataset,
        args.artifact,
        checkpoint_source=args.checkpoint,
        rollout_count=args.rollout_count,
        group_size=args.group_size,
        turn_budget=args.turn_budget,
        seed=args.seed,
        optimizer_learning_rate=args.optimizer_learning_rate,
        optimizer_name=args.optimizer_name,
        checkpoint_device=args.checkpoint_device,
    )
