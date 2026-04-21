"""Typed contracts for batch evaluation datasets and artifacts."""

from __future__ import annotations

from dataclasses import dataclass

from agentconductor.domain.models import DifficultyLevel, SolveStatus


@dataclass(frozen=True, slots=True)
class EvaluationProblemDefinition:
    """One problem loaded from a batch-evaluation dataset."""

    identifier: str
    prompt: str
    difficulty: DifficultyLevel | None = None


@dataclass(frozen=True, slots=True)
class EvaluationProblemResult:
    """Per-problem output recorded by the batch-evaluation pipeline."""

    identifier: str
    status: SolveStatus
    testing_outcome: str | None
    latency_seconds: float
    completed_turns: int
    topology_steps: int
    topology_agents: int
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EvaluationSummary:
    """Aggregate summary over one batch-evaluation run."""

    problem_count: int
    completed_count: int
    failed_count: int
    passed_count: int
    average_latency_seconds: float


@dataclass(frozen=True, slots=True)
class EvaluationRunArtifact:
    """Structured in-memory view of one batch-evaluation artifact."""

    problems: tuple[EvaluationProblemDefinition, ...]
    results: tuple[EvaluationProblemResult, ...]
    summary: EvaluationSummary
