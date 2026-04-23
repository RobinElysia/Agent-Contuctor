"""Public entrypoints for SFT dataset generation and baseline training."""

from __future__ import annotations

import argparse

from agentconductor.application.training import (
    generate_sft_dataset_entrypoint,
    load_sft_checkpoint_entrypoint,
    run_sft_baseline_entrypoint,
)


def main() -> None:
    """CLI entrypoint for SFT dataset generation and baseline training."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="Path to the SFT dataset JSONL file.")
    parser.add_argument("--artifact", help="Path to the SFT artifact JSON file.")
    parser.add_argument("--generate-only", action="store_true", help="Only generate the dataset.")
    parser.add_argument("--load-checkpoint", help="Load and print checkpoint metadata from this path.")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--backbone-name", default="Qwen2.5-3B-Instruct")
    parser.add_argument("--tokenizer-name", default="Qwen2.5-3B-Instruct")
    parser.add_argument("--prompt-template-version", default="orchestrator-sft-v1")
    args = parser.parse_args()

    if args.load_checkpoint:
        print(load_sft_checkpoint_entrypoint(args.load_checkpoint))
        return
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
        backbone_name=args.backbone_name,
        tokenizer_name=args.tokenizer_name,
        prompt_template_version=args.prompt_template_version,
    )
