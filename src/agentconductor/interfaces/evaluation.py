"""Public entrypoint for benchmark-aligned evaluation."""

from __future__ import annotations

import argparse

from agentconductor.application.evaluation import run_benchmark_evaluation_entrypoint
from agentconductor.domain.benchmark import BenchmarkDatasetFormat


def main() -> None:
    """CLI entrypoint for benchmark-aligned frozen-inference evaluation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="Path to the canonical benchmark dataset artifact.")
    parser.add_argument("--output", required=True, help="Path to the output evaluation artifact JSON file.")
    parser.add_argument("--checkpoint", required=True, help="Path to a checkpoint directory, checkpoint metadata file, or training artifact JSON file.")
    parser.add_argument("--checkpoint-id", help="Explicit checkpoint id when the checkpoint source resolves multiple candidates.")
    parser.add_argument(
        "--source-format",
        default=BenchmarkDatasetFormat.APPS_JSONL.value,
        choices=[format_value.value for format_value in BenchmarkDatasetFormat],
        help="Canonical loader for the input benchmark dataset artifact.",
    )
    parser.add_argument("--samples-per-problem", type=int, default=1, help="Number of solve attempts to record per benchmark problem.")
    parser.add_argument("--pass-k", type=int, help="Aggregate pass@k over the first k attempts per problem; defaults to samples-per-problem.")
    parser.add_argument("--max-workers", type=int, default=1, help="Number of concurrent solve workers.")
    parser.add_argument("--max-turns", type=int, default=2, help="Maximum solve turns per problem.")
    parser.add_argument("--orchestrator-device", default="cpu", help="Frozen-inference device for checkpoint-backed orchestration.")
    parser.add_argument("--orchestrator-max-attempts", type=int, default=1, help="Retry budget for YAML candidate extraction and parsing inside the learned orchestrator boundary.")
    args = parser.parse_args()

    artifact = run_benchmark_evaluation_entrypoint(
        args.dataset,
        args.output,
        checkpoint_source=args.checkpoint,
        checkpoint_id=args.checkpoint_id,
        source_format=BenchmarkDatasetFormat(args.source_format),
        samples_per_problem=args.samples_per_problem,
        pass_k=args.pass_k,
        max_workers=args.max_workers,
        max_turns=args.max_turns,
        orchestrator_device=args.orchestrator_device,
        orchestrator_max_attempts=args.orchestrator_max_attempts,
    )
    print(
        "agentconductor-eval:",
        f"problems={artifact.summary.problem_count}",
        f"attempts={artifact.summary.attempt_count}",
        f"pass@1={artifact.summary.pass_at_1:.3f}",
        f"pass@{artifact.summary.pass_k}={artifact.summary.pass_at_k:.3f}",
        f"checkpoint={artifact.metadata.checkpoint_id}",
    )
