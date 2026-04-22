"""Public entrypoints for benchmark evaluation and dataset ingestion."""

from __future__ import annotations

from pathlib import Path

from agentconductor.application.benchmark import (
    evaluate_candidate_with_benchmark,
    load_benchmark_dataset_entrypoint,
)
from agentconductor.domain.benchmark import (
    BenchmarkAdapter,
    BenchmarkDatasetFormat,
    CanonicalBenchmarkDataset,
    BenchmarkEvaluationResult,
    BenchmarkExecutionSettings,
    BenchmarkProblemDefinition,
)
from agentconductor.domain.execution import CodeCandidate


def evaluate_candidate_against_benchmark(
    problem: BenchmarkProblemDefinition,
    candidate: CodeCandidate,
    settings: BenchmarkExecutionSettings,
    *,
    adapter: BenchmarkAdapter,
) -> BenchmarkEvaluationResult:
    """Evaluate one candidate through the benchmark adapter boundary."""
    return evaluate_candidate_with_benchmark(
        problem,
        candidate,
        settings,
        adapter=adapter,
    )


def load_canonical_benchmark_dataset(
    dataset_path: str | Path,
    *,
    source_format: BenchmarkDatasetFormat = BenchmarkDatasetFormat.APPS_JSONL,
) -> CanonicalBenchmarkDataset:
    """Load one supported external benchmark dataset into canonical records."""
    return load_benchmark_dataset_entrypoint(
        dataset_path,
        source_format=source_format,
    )
