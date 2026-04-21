"""Public entrypoints for the repository-local RL baseline."""

from __future__ import annotations

import argparse

from agentconductor.application.rl import (
    compute_reward_breakdown_entrypoint,
    run_rl_baseline_entrypoint,
)


def main() -> None:
    """CLI entrypoint for the repository-local RL baseline."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="Path to the SFT dataset JSONL file.")
    parser.add_argument("--artifact", required=True, help="Path to the RL artifact JSON file.")
    parser.add_argument("--rollouts", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    run_rl_baseline_entrypoint(
        args.dataset,
        args.artifact,
        rollouts=args.rollouts,
        seed=args.seed,
    )
