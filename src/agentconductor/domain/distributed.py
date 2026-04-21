"""Typed contracts for distributed candidate evaluation orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from agentconductor.domain.execution import (
    CodeCandidate,
    SandboxExecutionResult,
    SandboxTestSpec,
)
from agentconductor.domain.models import ProblemInstance


class DistributedEvaluationStatus(StrEnum):
    """High-level status for one orchestrated evaluation task."""

    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


@dataclass(frozen=True, slots=True)
class DistributedEvaluationTask:
    """One candidate-evaluation job submitted to the orchestrator."""

    task_id: str
    problem: ProblemInstance
    candidate: CodeCandidate
    spec: SandboxTestSpec


@dataclass(frozen=True, slots=True)
class DistributedEvaluationConfig:
    """Explicit concurrency, retry, and collection-timeout settings."""

    max_workers: int = 1
    max_retries: int = 0
    collection_timeout_seconds: float | None = None

    def __post_init__(self) -> None:
        if self.max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if (
            self.collection_timeout_seconds is not None
            and self.collection_timeout_seconds <= 0
        ):
            raise ValueError("collection_timeout_seconds must be > 0 when provided")


@dataclass(frozen=True, slots=True)
class DistributedEvaluationResult:
    """Collected result for one orchestrated evaluation task."""

    task_id: str
    status: DistributedEvaluationStatus
    attempt_count: int
    sandbox_result: SandboxExecutionResult | None = None
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DistributedEvaluationBatch:
    """Collected results plus the explicit config used for orchestration."""

    tasks: tuple[DistributedEvaluationTask, ...]
    config: DistributedEvaluationConfig
    results: tuple[DistributedEvaluationResult, ...]

    @property
    def completed_count(self) -> int:
        return sum(
            1
            for result in self.results
            if result.status is DistributedEvaluationStatus.COMPLETED
        )

    @property
    def failed_count(self) -> int:
        return sum(
            1
            for result in self.results
            if result.status is DistributedEvaluationStatus.FAILED
        )

    @property
    def timed_out_count(self) -> int:
        return sum(
            1
            for result in self.results
            if result.status is DistributedEvaluationStatus.TIMED_OUT
        )
