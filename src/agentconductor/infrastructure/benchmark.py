"""Infrastructure helpers for external benchmark adapter boundaries."""

from __future__ import annotations

import json
import tempfile
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from agentconductor.domain.benchmark import (
    BenchmarkAdapter,
    BenchmarkArtifactIdentifiers,
    BenchmarkEvaluationResult,
    BenchmarkEvaluationStatus,
    BenchmarkExecutionSettings,
    BenchmarkProblemDefinition,
    BenchmarkTestCase,
    BenchmarkVerdictMapping,
)
from agentconductor.domain.execution import (
    CodeCandidate,
    JudgeResourceLimits,
    JudgeTestCase,
    SandboxTestSpec,
    TestingOutcome,
)
from agentconductor.infrastructure.sandbox import PythonSubprocessJudgeAdapter


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
        test_cases: tuple[BenchmarkTestCase, ...] = (),
    ) -> BenchmarkEvaluationResult:
        del settings, test_cases
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
                artifact_identifiers=_build_artifacts(submission),
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
                artifact_identifiers=_build_artifacts(submission),
                diagnostics=(
                    f"Native benchmark verdict '{submission.native_verdict}' has no repository mapping.",
                )
                + submission.diagnostics,
            )

        return BenchmarkEvaluationResult(
            adapter_name=self._adapter_name,
            status=BenchmarkEvaluationStatus.COMPLETED,
            problem=problem,
            artifact_identifiers=_build_artifacts(submission),
            verdict_mapping=BenchmarkVerdictMapping(
                native_verdict=submission.native_verdict,
                repository_outcome=repository_outcome,
                diagnostics=submission.diagnostics,
            ),
            diagnostics=submission.diagnostics,
        )


class PythonBenchmarkJudgeAdapter(BenchmarkAdapter):
    """Concrete Python-first benchmark path backed by benchmark-owned test cases."""

    def __init__(
        self,
        *,
        judge: PythonSubprocessJudgeAdapter | None = None,
        artifact_root: Path | None = None,
        adapter_name: str = "python-benchmark-harness",
    ) -> None:
        if not adapter_name:
            raise ValueError("adapter_name must be a non-empty string")
        self._judge = judge or PythonSubprocessJudgeAdapter()
        self._artifact_root = artifact_root
        self._adapter_name = adapter_name

    def evaluate(
        self,
        problem: BenchmarkProblemDefinition,
        candidate: CodeCandidate,
        settings: BenchmarkExecutionSettings,
        test_cases: tuple[BenchmarkTestCase, ...] = (),
    ) -> BenchmarkEvaluationResult:
        if settings.language != "python":
            return BenchmarkEvaluationResult(
                adapter_name=self._adapter_name,
                status=BenchmarkEvaluationStatus.ADAPTER_ERROR,
                problem=problem,
                diagnostics=(
                    f"Python benchmark harness only supports settings.language='python', received '{settings.language}'.",
                ),
            )
        if candidate.language != "python":
            return BenchmarkEvaluationResult(
                adapter_name=self._adapter_name,
                status=BenchmarkEvaluationStatus.ADAPTER_ERROR,
                problem=problem,
                diagnostics=(
                    f"Python benchmark harness only supports candidate.language='python', received '{candidate.language}'.",
                ),
            )
        if not test_cases:
            return BenchmarkEvaluationResult(
                adapter_name=self._adapter_name,
                status=BenchmarkEvaluationStatus.ADAPTER_ERROR,
                problem=problem,
                diagnostics=(
                    "Benchmark execution requires at least one benchmark-owned test case; the canonical dataset record only contained metadata.",
                ),
            )

        sandbox_result = self._judge.evaluate(
            problem.to_problem_instance(),
            candidate,
            _build_sandbox_spec(settings=settings, test_cases=test_cases),
        )
        artifact_identifiers = self._write_artifacts(
            problem=problem,
            candidate=candidate,
            settings=settings,
            sandbox_result=sandbox_result,
        )
        native_verdict = _map_outcome_to_native_verdict(sandbox_result.outcome)
        repository_outcome = _default_verdict_map()[native_verdict]
        diagnostics = (
            f"Evaluation ran through the external benchmark path '{self._adapter_name}' rather than the repository-default testing role.",
            f"Invocation mode: {settings.invocation_mode.value}.",
        ) + sandbox_result.diagnostics

        return BenchmarkEvaluationResult(
            adapter_name=self._adapter_name,
            status=BenchmarkEvaluationStatus.COMPLETED,
            problem=problem,
            artifact_identifiers=artifact_identifiers,
            verdict_mapping=BenchmarkVerdictMapping(
                native_verdict=native_verdict,
                repository_outcome=repository_outcome,
                diagnostics=sandbox_result.diagnostics,
            ),
            diagnostics=diagnostics,
        )

    def _write_artifacts(
        self,
        *,
        problem: BenchmarkProblemDefinition,
        candidate: CodeCandidate,
        settings: BenchmarkExecutionSettings,
        sandbox_result,
    ) -> BenchmarkArtifactIdentifiers:
        safe_problem_id = problem.identifier.replace("/", "_").replace("\\", "_")
        run_id = f"{safe_problem_id}-{uuid.uuid4().hex[:8]}"
        artifact_root = self._artifact_root or Path(
            tempfile.mkdtemp(prefix="agentconductor-benchmark-run-")
        )
        artifact_root.mkdir(parents=True, exist_ok=True)

        result_path = artifact_root / f"{run_id}.result.json"
        log_path = artifact_root / f"{run_id}.log.json"
        result_path.write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "problem_id": problem.identifier,
                    "source_problem_id": problem.source_problem_id,
                    "invocation_mode": settings.invocation_mode.value,
                    "entrypoint": settings.entrypoint,
                    "candidate_language": candidate.language,
                    "outcome": sandbox_result.outcome.value,
                    "diagnostics": list(sandbox_result.diagnostics),
                    "case_results": [asdict(case_result) for case_result in sandbox_result.case_results],
                    "runtime_capabilities": (
                        asdict(sandbox_result.runtime_capabilities)
                        if sandbox_result.runtime_capabilities is not None
                        else None
                    ),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        log_path.write_text(
            json.dumps(
                {
                    "stdout": sandbox_result.stdout,
                    "stderr": sandbox_result.stderr,
                    "exit_code": sandbox_result.exit_code,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return BenchmarkArtifactIdentifiers(
            run_id=run_id,
            submission_id=run_id,
            result_artifact_uri=str(result_path),
            log_artifact_uri=str(log_path),
        )


def _build_artifacts(submission: StubBenchmarkSubmission) -> BenchmarkArtifactIdentifiers:
    return BenchmarkArtifactIdentifiers(
        run_id=submission.run_id,
        submission_id=submission.submission_id,
        result_artifact_uri=submission.result_artifact_uri,
        log_artifact_uri=submission.log_artifact_uri,
    )


def _build_sandbox_spec(
    *,
    settings: BenchmarkExecutionSettings,
    test_cases: tuple[BenchmarkTestCase, ...],
) -> SandboxTestSpec:
    return SandboxTestSpec(
        entrypoint=settings.entrypoint or "solve",
        test_cases=tuple(
            JudgeTestCase(
                name=test_case.name,
                arguments=test_case.arguments,
                keyword_arguments=test_case.keyword_arguments,
                stdin_text=test_case.stdin_text,
                expected_output=test_case.expected_output,
                expected_stdout=test_case.expected_stdout,
            )
            for test_case in test_cases
        ),
        resource_limits=JudgeResourceLimits(
            cpu_time_seconds=settings.time_limit_seconds or 1.0,
            wall_time_seconds=settings.time_limit_seconds or 1.0,
            memory_limit_bytes=settings.memory_limit_bytes,
        ),
    )


def _map_outcome_to_native_verdict(outcome: TestingOutcome) -> str:
    if outcome is TestingOutcome.PASSED:
        return "accepted"
    if outcome is TestingOutcome.WRONG_ANSWER:
        return "wrong_answer"
    if outcome is TestingOutcome.TIME_LIMIT_EXCEEDED:
        return "time_limit_exceeded"
    if outcome is TestingOutcome.MEMORY_LIMIT_EXCEEDED:
        return "memory_limit_exceeded"
    if outcome is TestingOutcome.RUNTIME_ERROR:
        return "runtime_error"
    if outcome is TestingOutcome.COMPILATION_ERROR:
        return "compilation_error"
    return "runtime_error"


def _default_verdict_map() -> dict[str, TestingOutcome]:
    return {
        "accepted": TestingOutcome.PASSED,
        "wrong_answer": TestingOutcome.WRONG_ANSWER,
        "time_limit_exceeded": TestingOutcome.TIME_LIMIT_EXCEEDED,
        "memory_limit_exceeded": TestingOutcome.MEMORY_LIMIT_EXCEEDED,
        "runtime_error": TestingOutcome.RUNTIME_ERROR,
        "compilation_error": TestingOutcome.COMPILATION_ERROR,
    }
