"""Public entrypoint for batch evaluation."""

from __future__ import annotations

import argparse

from agentconductor.application.evaluation import run_batch_evaluation_entrypoint


def main() -> None:
    """CLI entrypoint for JSON-backed batch evaluation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="Path to the evaluation dataset JSON file.")
    parser.add_argument("--output", required=True, help="Path to the output artifact JSON file.")
    parser.add_argument("--max-workers", type=int, default=1, help="Number of concurrent solve workers.")
    args = parser.parse_args()

    artifact = run_batch_evaluation_entrypoint(
        args.dataset,
        args.output,
        max_workers=args.max_workers,
    )
    print(
        "agentconductor-eval:",
        f"problems={artifact.summary.problem_count}",
        f"passed={artifact.summary.passed_count}",
        f"failed={artifact.summary.failed_count}",
    )
