"""Public entrypoints for SFT dataset generation and baseline training."""

from __future__ import annotations

import argparse

from agentconductor.application.training import (
    generate_sft_dataset_entrypoint,
    run_sft_baseline_entrypoint,
)


def main() -> None:
    """CLI entrypoint for SFT dataset generation and baseline training."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="Path to the SFT dataset JSONL file.")
    parser.add_argument("--artifact", help="Path to the SFT artifact JSON file.")
    parser.add_argument("--generate-only", action="store_true", help="Only generate the dataset.")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    generate_sft_dataset_entrypoint(args.dataset)
    if args.generate_only:
        return
    if not args.artifact:
        raise SystemExit("--artifact is required unless --generate-only is used.")
    run_sft_baseline_entrypoint(
        args.dataset,
        args.artifact,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        seed=args.seed,
    )
