"""Infrastructure helpers for external benchmark adapter boundaries."""

from __future__ import annotations

from dataclasses import dataclass

from agentconductor.domain.benchmark import (
    BenchmarkAdapter,
    BenchmarkArtifactIdentifiers,
    BenchmarkEvaluationResult,
    BenchmarkEvaluationStatus,
    BenchmarkExecutionSettings,
    BenchmarkProblemDefinition,
    BenchmarkVerdictMapping,
)
from agentconductor.domain.execution import CodeCandidate, TestingOutcome


@dataclass(frozen=True, slots=True)
class StubBenchmarkSubmission:
    """Fixture-friendly benchmark-native response used for contract tests."""

    native_verdict: str
    run_id: str
    submission_id: str | None = None
    result_artifact_uri: str | None = None
    log_artifact_uri: str | None = None
    diagnostics: tuple[str, ...] = ()


class StubBenchmarkAdapter(BenchmarkAdapter):
    """Deterministic benchmark adapter used for boundary verification."""

    def __init__(
        self,
        *,
        submissions: dict[str, StubBenchmarkSubmission],
        verdict_map: dict[str, TestingOutcome] | None = None,
        adapter_name: str = "stub-benchmark",
    ) -> None:
        if not adapter_name:
            raise ValueError("adapter_name must be a non-empty string")
        self._submissions = dict(submissions)
        self._verdict_map = dict(verdict_map or _default_verdict_map())
        self._adapter_name = adapter_name

    def evaluate(
        self,
        problem: BenchmarkProblemDefinition,
        candidate: CodeCandidate,
        settings: BenchmarkExecutionSettings,
    ) -> BenchmarkEvaluationResult:
        del settings
        submission = self._submissions.get(problem.source_problem_id)
        if submission is None:
            return BenchmarkEvaluationResult(
                adapter_name=self._adapter_name,
                status=BenchmarkEvaluationStatus.ADAPTER_ERROR,
                problem=problem,
                diagnostics=(
                    f"No stub benchmark submission was configured for '{problem.source_problem_id}'.",
                ),
            )

        if candidate.language != problem.language:
            return BenchmarkEvaluationResult(
                adapter_name=self._adapter_name,
                status=BenchmarkEvaluationStatus.ADAPTER_ERROR,
                problem=problem,
                artifact_identifiers=BenchmarkArtifactIdentifiers(
                    run_id=submission.run_id,
                    submission_id=submission.submission_id,
                    result_artifact_uri=submission.result_artifact_uri,
                    log_artifact_uri=submission.log_artifact_uri,
                ),
                diagnostics=(
                    f"Candidate language '{candidate.language}' does not match benchmark problem language '{problem.language}'.",
                ),
            )

        repository_outcome = self._verdict_map.get(submission.native_verdict)
        if repository_outcome is None:
            return BenchmarkEvaluationResult(
                adapter_name=self._adapter_name,
                status=BenchmarkEvaluationStatus.ADAPTER_ERROR,
                problem=problem,
                artifact_identifiers=BenchmarkArtifactIdentifiers(
                    run_id=submission.run_id,
                    submission_id=submission.submission_id,
                    result_artifact_uri=submission.result_artifact_uri,
                    log_artifact_uri=submission.log_artifact_uri,
                ),
                diagnostics=(
                    f"Native benchmark verdict '{submission.native_verdict}' has no repository mapping.",
                )
                + submission.diagnostics,
            )

        return BenchmarkEvaluationResult(
            adapter_name=self._adapter_name,
            status=BenchmarkEvaluationStatus.COMPLETED,
            problem=problem,
            artifact_identifiers=BenchmarkArtifactIdentifiers(
                run_id=submission.run_id,
                submission_id=submission.submission_id,
                result_artifact_uri=submission.result_artifact_uri,
                log_artifact_uri=submission.log_artifact_uri,
            ),
            verdict_mapping=BenchmarkVerdictMapping(
                native_verdict=submission.native_verdict,
                repository_outcome=repository_outcome,
                diagnostics=submission.diagnostics,
            ),
            diagnostics=submission.diagnostics,
        )


def _default_verdict_map() -> dict[str, TestingOutcome]:
    return {
        "accepted": TestingOutcome.PASSED,
        "wrong_answer": TestingOutcome.WRONG_ANSWER,
        "time_limit_exceeded": TestingOutcome.TIME_LIMIT_EXCEEDED,
        "memory_limit_exceeded": TestingOutcome.MEMORY_LIMIT_EXCEEDED,
        "runtime_error": TestingOutcome.RUNTIME_ERROR,
        "compilation_error": TestingOutcome.COMPILATION_ERROR,
    }
