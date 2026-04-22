"""Typed contracts for external benchmark integration boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol

from agentconductor.domain.execution import CodeCandidate, TestingOutcome
from agentconductor.domain.models import DifficultyLevel, ProblemInstance


class BenchmarkInvocationMode(StrEnum):
    """How the benchmark expects the candidate to be invoked."""

    FUNCTION = "function"
    STDIN = "stdin"


class BenchmarkEvaluationStatus(StrEnum):
    """High-level status returned by a benchmark adapter."""

    COMPLETED = "completed"
    ADAPTER_ERROR = "adapter_error"


class BenchmarkDatasetFormat(StrEnum):
    """External dataset layouts that can be normalized into canonical records."""

    APPS_JSONL = "apps_jsonl"


@dataclass(frozen=True, slots=True)
class BenchmarkProblemDefinition:
    """Canonical benchmark problem metadata used by repository services."""

    identifier: str
    prompt: str
    benchmark_name: str
    dataset_name: str
    source_problem_id: str
    language: str = "python"
    split_name: str | None = None
    difficulty: DifficultyLevel | None = None

    def __post_init__(self) -> None:
        if not self.identifier:
            raise ValueError("identifier must be a non-empty string")
        if not self.prompt:
            raise ValueError("prompt must be a non-empty string")
        if not self.benchmark_name:
            raise ValueError("benchmark_name must be a non-empty string")
        if not self.dataset_name:
            raise ValueError("dataset_name must be a non-empty string")
        if not self.source_problem_id:
            raise ValueError("source_problem_id must be a non-empty string")
        if not self.language:
            raise ValueError("language must be a non-empty string")
        if self.split_name == "":
            raise ValueError("split_name must be omitted or a non-empty string")

    def to_problem_instance(self) -> ProblemInstance:
        """Project benchmark metadata onto the repository solve contract."""
        return ProblemInstance(
            identifier=self.identifier,
            prompt=self.prompt,
            difficulty=self.difficulty,
        )


@dataclass(frozen=True, slots=True)
class BenchmarkExecutionSettings:
    """Benchmark-owned execution settings kept separate from local judge specs."""

    language: str = "python"
    invocation_mode: BenchmarkInvocationMode = BenchmarkInvocationMode.FUNCTION
    entrypoint: str | None = "solve"
    time_limit_seconds: float | None = None
    memory_limit_bytes: int | None = None

    def __post_init__(self) -> None:
        if not self.language:
            raise ValueError("language must be a non-empty string")
        if self.invocation_mode is BenchmarkInvocationMode.FUNCTION and not self.entrypoint:
            raise ValueError("function invocation requires a non-empty entrypoint")
        if self.invocation_mode is BenchmarkInvocationMode.STDIN and self.entrypoint == "":
            raise ValueError("entrypoint must be omitted or non-empty for stdin invocation")
        if self.time_limit_seconds is not None and self.time_limit_seconds <= 0:
            raise ValueError("time_limit_seconds must be > 0 when provided")
        if self.memory_limit_bytes is not None and self.memory_limit_bytes <= 0:
            raise ValueError("memory_limit_bytes must be > 0 when provided")


@dataclass(frozen=True, slots=True)
class BenchmarkTestCase:
    """One benchmark-owned test case kept separate from local judge payloads."""

    name: str
    arguments: tuple[Any, ...] = ()
    keyword_arguments: tuple[tuple[str, Any], ...] = ()
    stdin_text: str | None = None
    expected_output: Any = None
    expected_stdout: str | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name must be a non-empty string")
        if self.expected_output is None and self.expected_stdout is None:
            raise ValueError(
                "benchmark test cases must define expected_output or expected_stdout"
            )


@dataclass(frozen=True, slots=True)
class BenchmarkVerdictMapping:
    """Typed mapping from a benchmark-native verdict into repository semantics."""

    native_verdict: str
    repository_outcome: TestingOutcome
    terminal: bool = True
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.native_verdict:
            raise ValueError("native_verdict must be a non-empty string")


@dataclass(frozen=True, slots=True)
class BenchmarkArtifactIdentifiers:
    """Inspectable identifiers for benchmark-side run artifacts."""

    run_id: str
    submission_id: str | None = None
    result_artifact_uri: str | None = None
    log_artifact_uri: str | None = None

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id must be a non-empty string")
        if self.submission_id == "":
            raise ValueError("submission_id must be omitted or a non-empty string")
        if self.result_artifact_uri == "":
            raise ValueError("result_artifact_uri must be omitted or a non-empty string")
        if self.log_artifact_uri == "":
            raise ValueError("log_artifact_uri must be omitted or a non-empty string")


@dataclass(frozen=True, slots=True)
class BenchmarkEvaluationResult:
    """Typed benchmark adapter result consumed by repository services."""

    adapter_name: str
    status: BenchmarkEvaluationStatus
    problem: BenchmarkProblemDefinition
    artifact_identifiers: BenchmarkArtifactIdentifiers | None = None
    verdict_mapping: BenchmarkVerdictMapping | None = None
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.adapter_name:
            raise ValueError("adapter_name must be a non-empty string")
        if (
            self.status is BenchmarkEvaluationStatus.COMPLETED
            and self.verdict_mapping is None
        ):
            raise ValueError("completed benchmark results must include verdict_mapping")

    @property
    def testing_outcome(self) -> TestingOutcome | None:
        """Return the normalized repository outcome when available."""
        if self.verdict_mapping is None:
            return None
        return self.verdict_mapping.repository_outcome


class BenchmarkAdapter(Protocol):
    """Typed seam for external benchmark execution backends."""

    def evaluate(
        self,
        problem: BenchmarkProblemDefinition,
        candidate: CodeCandidate,
        settings: BenchmarkExecutionSettings,
        test_cases: tuple[BenchmarkTestCase, ...] = (),
    ) -> BenchmarkEvaluationResult:
        """Run one candidate through an external benchmark boundary."""


@dataclass(frozen=True, slots=True)
class BenchmarkDatasetSource:
    """Location and source-format metadata for one benchmark dataset artifact."""

    benchmark_name: str
    dataset_name: str
    format: BenchmarkDatasetFormat
    source_uri: str

    def __post_init__(self) -> None:
        if not self.benchmark_name:
            raise ValueError("benchmark_name must be a non-empty string")
        if not self.dataset_name:
            raise ValueError("dataset_name must be a non-empty string")
        if not self.source_uri:
            raise ValueError("source_uri must be a non-empty string")


@dataclass(frozen=True, slots=True)
class CanonicalBenchmarkRecord:
    """Canonical benchmark execution record derived from one dataset row."""

    problem: BenchmarkProblemDefinition
    execution_settings: BenchmarkExecutionSettings = field(
        default_factory=BenchmarkExecutionSettings
    )
    test_cases: tuple[BenchmarkTestCase, ...] = ()
    normalization_notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CanonicalBenchmarkDataset:
    """Canonical benchmark records produced from one external source artifact."""

    source: BenchmarkDatasetSource
    records: tuple[CanonicalBenchmarkRecord, ...]
    normalization_notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.records:
            raise ValueError("canonical benchmark dataset must contain at least one problem")

    @property
    def problems(self) -> tuple[BenchmarkProblemDefinition, ...]:
        """Return canonical problem metadata for compatibility with earlier callers."""
        return tuple(record.problem for record in self.records)
