"""Typed contracts for benchmark-aligned evaluation datasets and artifacts."""

from __future__ import annotations

from dataclasses import dataclass

from agentconductor.domain.benchmark import BenchmarkEvaluationStatus
from agentconductor.domain.models import DifficultyLevel, SolveStatus


@dataclass(frozen=True, slots=True)
class EvaluationProblemDefinition:
    """One canonical benchmark problem projected into evaluation artifacts."""

    identifier: str
    prompt: str
    benchmark_name: str
    dataset_name: str
    source_problem_id: str
    language: str = "python"
    split_name: str | None = None
    difficulty: DifficultyLevel | None = None


@dataclass(frozen=True, slots=True)
class EvaluationProblemResult:
    """Per-attempt output recorded by the benchmark evaluation pipeline."""

    identifier: str
    source_problem_id: str
    attempt_index: int
    solve_status: SolveStatus
    benchmark_status: BenchmarkEvaluationStatus
    solve_testing_outcome: str | None
    benchmark_testing_outcome: str | None
    benchmark_native_verdict: str | None
    latency_seconds: float
    completed_turns: int
    topology_steps: int
    topology_agents: int
    candidate_language: str | None
    checkpoint_id: str
    benchmark_run_id: str | None = None
    result_artifact_uri: str | None = None
    log_artifact_uri: str | None = None
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EvaluationSummary:
    """Aggregate summary over one benchmark-aligned evaluation run."""

    problem_count: int
    attempt_count: int
    completed_count: int
    benchmark_completed_count: int
    adapter_error_count: int
    passed_count: int
    pass_at_1: float
    pass_at_k: float
    pass_k: int
    average_latency_seconds: float


@dataclass(frozen=True, slots=True)
class EvaluationRunMetadata:
    """Provenance needed to reproduce or compare one evaluation artifact."""

    benchmark_name: str
    dataset_name: str
    dataset_version: str
    dataset_source_uri: str
    harness_name: str
    harness_version: str
    runtime_mode: str
    checkpoint_id: str
    checkpoint_path: str
    checkpoint_training_stage: str
    reproduction_claim: str
    exact_reproduction_ready: bool
    blocking_gap_ids: tuple[str, ...] = ()
    split_name: str | None = None
    samples_per_problem: int = 1
    max_turns: int = 1
    orchestrator_device: str = "cpu"
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EvaluationRunArtifact:
    """Structured in-memory view of one benchmark evaluation artifact."""

    metadata: EvaluationRunMetadata
    problems: tuple[EvaluationProblemDefinition, ...]
    results: tuple[EvaluationProblemResult, ...]
    summary: EvaluationSummary
