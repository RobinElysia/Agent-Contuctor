"""Infrastructure helpers for external benchmark adapter boundaries."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
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
    BenchmarkInvocationMode,
    BenchmarkProblemDefinition,
    BenchmarkTestCase,
    BenchmarkVerdictMapping,
)
from agentconductor.domain.execution import (
    CodeCandidate,
    JudgeCaseResult,
    JudgeResourceLimits,
    JudgeTestCase,
    SandboxExecutionResult,
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


@dataclass(frozen=True, slots=True)
class _CompletedCommandProcess:
    stdout: str
    stderr: str
    returncode: int | None
    timed_out: bool


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
    """Concrete Python benchmark path with function and script execution modes."""

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
        if _normalize_benchmark_language(settings.language) != "python":
            return BenchmarkEvaluationResult(
                adapter_name=self._adapter_name,
                status=BenchmarkEvaluationStatus.ADAPTER_ERROR,
                problem=problem,
                diagnostics=(
                    f"Python benchmark harness only supports settings.language='python', received '{settings.language}'.",
                ),
            )
        if _normalize_benchmark_language(candidate.language) != "python":
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

        if settings.invocation_mode is BenchmarkInvocationMode.FUNCTION:
            sandbox_result = self._judge.evaluate(
                problem.to_problem_instance(),
                candidate,
                _build_sandbox_spec(settings=settings, test_cases=test_cases),
            )
        else:
            sandbox_result = _evaluate_script_cases(
                command_builder=lambda candidate_path: [sys.executable, candidate_path.name],
                problem=problem,
                candidate=candidate,
                settings=settings,
                test_cases=test_cases,
                candidate_filename="candidate.py",
                invocation_diagnostic=(
                    "STDIN benchmark execution ran the candidate as a standalone Python script rather than calling a repository-owned solve() wrapper."
                ),
            )

        return _build_benchmark_result(
            adapter_name=self._adapter_name,
            artifact_root=self._artifact_root,
            problem=problem,
            candidate=candidate,
            settings=settings,
            sandbox_result=sandbox_result,
        )


class NodeJsBenchmarkJudgeAdapter(BenchmarkAdapter):
    """Concrete Node.js benchmark path for JavaScript benchmark records."""

    def __init__(
        self,
        *,
        node_command: str = "node",
        artifact_root: Path | None = None,
        adapter_name: str = "nodejs-benchmark-harness",
    ) -> None:
        if not adapter_name:
            raise ValueError("adapter_name must be a non-empty string")
        self._node_command = node_command
        self._artifact_root = artifact_root
        self._adapter_name = adapter_name

    def evaluate(
        self,
        problem: BenchmarkProblemDefinition,
        candidate: CodeCandidate,
        settings: BenchmarkExecutionSettings,
        test_cases: tuple[BenchmarkTestCase, ...] = (),
    ) -> BenchmarkEvaluationResult:
        if _normalize_benchmark_language(settings.language) != "javascript":
            return BenchmarkEvaluationResult(
                adapter_name=self._adapter_name,
                status=BenchmarkEvaluationStatus.ADAPTER_ERROR,
                problem=problem,
                diagnostics=(
                    f"Node.js benchmark harness only supports JavaScript settings, received '{settings.language}'.",
                ),
            )
        if _normalize_benchmark_language(candidate.language) != "javascript":
            return BenchmarkEvaluationResult(
                adapter_name=self._adapter_name,
                status=BenchmarkEvaluationStatus.ADAPTER_ERROR,
                problem=problem,
                diagnostics=(
                    f"Node.js benchmark harness only supports JavaScript candidates, received '{candidate.language}'.",
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
        if shutil.which(self._node_command) is None:
            return BenchmarkEvaluationResult(
                adapter_name=self._adapter_name,
                status=BenchmarkEvaluationStatus.ADAPTER_ERROR,
                problem=problem,
                diagnostics=(
                    f"Node.js runtime '{self._node_command}' was not available on PATH.",
                ),
            )

        if settings.invocation_mode is BenchmarkInvocationMode.FUNCTION:
            sandbox_result = self._evaluate_function_cases(
                candidate=candidate,
                settings=settings,
                test_cases=test_cases,
            )
        else:
            sandbox_result = _evaluate_script_cases(
                command_builder=lambda candidate_path: [self._node_command, candidate_path.name],
                problem=problem,
                candidate=candidate,
                settings=settings,
                test_cases=test_cases,
                candidate_filename="candidate.js",
                invocation_diagnostic=(
                    "STDIN benchmark execution ran the candidate as a standalone Node.js script with benchmark-owned stdin payloads."
                ),
            )

        return _build_benchmark_result(
            adapter_name=self._adapter_name,
            artifact_root=self._artifact_root,
            problem=problem,
            candidate=candidate,
            settings=settings,
            sandbox_result=sandbox_result,
        )

    def _evaluate_function_cases(
        self,
        *,
        candidate: CodeCandidate,
        settings: BenchmarkExecutionSettings,
        test_cases: tuple[BenchmarkTestCase, ...],
    ) -> SandboxExecutionResult:
        with tempfile.TemporaryDirectory(prefix="agentconductor-node-benchmark-") as temp_dir:
            sandbox_root = Path(temp_dir)
            candidate_path = sandbox_root / "candidate.js"
            harness_path = sandbox_root / "harness.js"

            candidate_path.write_text(
                candidate.source_code + "\n" + _node_function_export_epilogue(),
                encoding="utf-8",
            )
            harness_path.write_text(
                _build_node_function_harness(settings=settings, test_cases=test_cases),
                encoding="utf-8",
            )

            case_results: list[JudgeCaseResult] = []
            last_stdout = ""
            last_stderr = ""
            last_exit_code: int | None = None

            for case_index, test_case in enumerate(test_cases):
                result_path = sandbox_root / f"result-{case_index}.json"
                completed = _run_command(
                    command=[
                        self._node_command,
                        harness_path.name,
                        "--case-index",
                        str(case_index),
                        "--result-path",
                        result_path.name,
                    ],
                    cwd=sandbox_root,
                    timeout_seconds=settings.time_limit_seconds or 1.0,
                )
                last_stdout = completed.stdout
                last_stderr = completed.stderr
                last_exit_code = completed.returncode

                if completed.timed_out:
                    diagnostics = (
                        f"Case '{test_case.name}' exceeded the hard wall-clock limit of {(settings.time_limit_seconds or 1.0):.1f}s.",
                    )
                    case_results.append(
                        JudgeCaseResult(
                            name=test_case.name,
                            outcome=TestingOutcome.TIME_LIMIT_EXCEEDED,
                            diagnostics=diagnostics,
                        )
                    )
                    return SandboxExecutionResult(
                        outcome=TestingOutcome.TIME_LIMIT_EXCEEDED,
                        diagnostics=diagnostics,
                        case_results=tuple(case_results),
                        stdout=completed.stdout,
                        stderr=completed.stderr,
                        exit_code=completed.returncode,
                    )

                if not result_path.exists():
                    outcome, diagnostics = _classify_script_process_failure(
                        test_case=test_case,
                        completed=completed,
                    )
                    case_results.append(
                        JudgeCaseResult(
                            name=test_case.name,
                            outcome=outcome,
                            diagnostics=diagnostics,
                            actual_stdout=completed.stdout,
                            expected_stdout=test_case.expected_stdout,
                            expected_output=test_case.expected_output,
                        )
                    )
                    return SandboxExecutionResult(
                        outcome=outcome,
                        diagnostics=diagnostics,
                        case_results=tuple(case_results),
                        stdout=completed.stdout,
                        stderr=completed.stderr,
                        exit_code=completed.returncode,
                    )

                payload = json.loads(result_path.read_text(encoding="utf-8"))
                case_payload = payload["case_results"][0]
                current_case_result = JudgeCaseResult(
                    name=case_payload["name"],
                    outcome=TestingOutcome(case_payload["outcome"]),
                    diagnostics=tuple(case_payload.get("diagnostics", ())),
                    actual_output=case_payload.get("actual_output"),
                    expected_output=case_payload.get("expected_output"),
                    actual_stdout=case_payload.get("actual_stdout"),
                    expected_stdout=case_payload.get("expected_stdout"),
                )
                case_results.append(current_case_result)
                if current_case_result.outcome is not TestingOutcome.PASSED:
                    return SandboxExecutionResult(
                        outcome=current_case_result.outcome,
                        diagnostics=current_case_result.diagnostics,
                        case_results=tuple(case_results),
                        stdout=payload.get("stdout", completed.stdout),
                        stderr=payload.get("stderr", completed.stderr),
                        exit_code=completed.returncode,
                    )

            return SandboxExecutionResult(
                outcome=TestingOutcome.PASSED,
                diagnostics=(
                    f"Judge accepted the candidate across {len(test_cases)} case(s).",
                ),
                case_results=tuple(case_results),
                stdout=last_stdout,
                stderr=last_stderr,
                exit_code=last_exit_code,
            )


class MultiLanguageBenchmarkJudgeAdapter(BenchmarkAdapter):
    """Dispatch benchmark execution to the configured language-specific harness."""

    def __init__(
        self,
        *,
        python_adapter: PythonBenchmarkJudgeAdapter | None = None,
        nodejs_adapter: NodeJsBenchmarkJudgeAdapter | None = None,
    ) -> None:
        self._python_adapter = python_adapter or PythonBenchmarkJudgeAdapter()
        self._nodejs_adapter = nodejs_adapter or NodeJsBenchmarkJudgeAdapter()

    def evaluate(
        self,
        problem: BenchmarkProblemDefinition,
        candidate: CodeCandidate,
        settings: BenchmarkExecutionSettings,
        test_cases: tuple[BenchmarkTestCase, ...] = (),
    ) -> BenchmarkEvaluationResult:
        language = _normalize_benchmark_language(settings.language)
        if language == "python":
            return self._python_adapter.evaluate(
                problem,
                candidate,
                settings,
                test_cases,
            )
        if language == "javascript":
            return self._nodejs_adapter.evaluate(
                problem,
                candidate,
                settings,
                test_cases,
            )
        return BenchmarkEvaluationResult(
            adapter_name="multi-language-benchmark-harness",
            status=BenchmarkEvaluationStatus.ADAPTER_ERROR,
            problem=problem,
            diagnostics=(
                f"No benchmark harness is configured for language '{settings.language}'.",
            ),
        )


def _build_benchmark_result(
    *,
    adapter_name: str,
    artifact_root: Path | None,
    problem: BenchmarkProblemDefinition,
    candidate: CodeCandidate,
    settings: BenchmarkExecutionSettings,
    sandbox_result: SandboxExecutionResult,
) -> BenchmarkEvaluationResult:
    artifact_identifiers = _write_artifacts(
        artifact_root=artifact_root,
        problem=problem,
        candidate=candidate,
        settings=settings,
        sandbox_result=sandbox_result,
    )
    native_verdict = _map_outcome_to_native_verdict(sandbox_result.outcome)
    repository_outcome = _default_verdict_map()[native_verdict]
    diagnostics = (
        f"Evaluation ran through the external benchmark path '{adapter_name}' rather than the repository-default testing role.",
        f"Invocation mode: {settings.invocation_mode.value}.",
        f"Language runtime: {_normalize_benchmark_language(settings.language)}.",
    ) + sandbox_result.diagnostics

    return BenchmarkEvaluationResult(
        adapter_name=adapter_name,
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
    *,
    artifact_root: Path | None,
    problem: BenchmarkProblemDefinition,
    candidate: CodeCandidate,
    settings: BenchmarkExecutionSettings,
    sandbox_result: SandboxExecutionResult,
) -> BenchmarkArtifactIdentifiers:
    safe_problem_id = problem.identifier.replace("/", "_").replace("\\", "_")
    run_id = f"{safe_problem_id}-{uuid.uuid4().hex[:8]}"
    resolved_root = artifact_root or Path(
        tempfile.mkdtemp(prefix="agentconductor-benchmark-run-")
    )
    resolved_root.mkdir(parents=True, exist_ok=True)

    result_path = resolved_root / f"{run_id}.result.json"
    log_path = resolved_root / f"{run_id}.log.json"
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


def _evaluate_script_cases(
    *,
    command_builder,
    problem: BenchmarkProblemDefinition,
    candidate: CodeCandidate,
    settings: BenchmarkExecutionSettings,
    test_cases: tuple[BenchmarkTestCase, ...],
    candidate_filename: str,
    invocation_diagnostic: str,
) -> SandboxExecutionResult:
    del problem
    with tempfile.TemporaryDirectory(prefix="agentconductor-script-benchmark-") as temp_dir:
        sandbox_root = Path(temp_dir)
        candidate_path = sandbox_root / candidate_filename
        candidate_path.write_text(candidate.source_code, encoding="utf-8")

        case_results: list[JudgeCaseResult] = []
        last_stdout = ""
        last_stderr = ""
        last_exit_code: int | None = None
        timeout_seconds = settings.time_limit_seconds or 1.0

        for test_case in test_cases:
            completed = _run_command(
                command=command_builder(candidate_path),
                cwd=sandbox_root,
                timeout_seconds=timeout_seconds,
                stdin_text=test_case.stdin_text,
            )
            last_stdout = completed.stdout
            last_stderr = completed.stderr
            last_exit_code = completed.returncode

            if completed.timed_out:
                diagnostics = (
                    f"Case '{test_case.name}' exceeded the hard wall-clock limit of {timeout_seconds:.1f}s.",
                    invocation_diagnostic,
                )
                case_results.append(
                    JudgeCaseResult(
                        name=test_case.name,
                        outcome=TestingOutcome.TIME_LIMIT_EXCEEDED,
                        diagnostics=diagnostics,
                        expected_stdout=test_case.expected_stdout,
                        expected_output=test_case.expected_output,
                    )
                )
                return SandboxExecutionResult(
                    outcome=TestingOutcome.TIME_LIMIT_EXCEEDED,
                    diagnostics=diagnostics,
                    case_results=tuple(case_results),
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                    exit_code=completed.returncode,
                )

            if completed.returncode not in (0, None):
                outcome, diagnostics = _classify_script_process_failure(
                    test_case=test_case,
                    completed=completed,
                )
                diagnostics = diagnostics + (invocation_diagnostic,)
                case_results.append(
                    JudgeCaseResult(
                        name=test_case.name,
                        outcome=outcome,
                        diagnostics=diagnostics,
                        actual_stdout=completed.stdout,
                        expected_stdout=test_case.expected_stdout,
                        expected_output=test_case.expected_output,
                    )
                )
                return SandboxExecutionResult(
                    outcome=outcome,
                    diagnostics=diagnostics,
                    case_results=tuple(case_results),
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                    exit_code=completed.returncode,
                )

            actual_stdout = completed.stdout
            expected_stdout = _expected_stdout_for_script_case(test_case)
            if _normalize_text(actual_stdout) != _normalize_text(expected_stdout):
                diagnostics = (
                    f"Case '{test_case.name}' printed {actual_stdout.strip()!r}; expected {expected_stdout!r}.",
                    invocation_diagnostic,
                )
                case_results.append(
                    JudgeCaseResult(
                        name=test_case.name,
                        outcome=TestingOutcome.WRONG_ANSWER,
                        diagnostics=diagnostics,
                        actual_stdout=actual_stdout,
                        expected_stdout=expected_stdout,
                        expected_output=test_case.expected_output,
                    )
                )
                return SandboxExecutionResult(
                    outcome=TestingOutcome.WRONG_ANSWER,
                    diagnostics=diagnostics,
                    case_results=tuple(case_results),
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                    exit_code=completed.returncode,
                )

            case_results.append(
                JudgeCaseResult(
                    name=test_case.name,
                    outcome=TestingOutcome.PASSED,
                    diagnostics=(invocation_diagnostic,),
                    actual_stdout=actual_stdout,
                    expected_stdout=expected_stdout,
                    expected_output=test_case.expected_output,
                )
            )

        return SandboxExecutionResult(
            outcome=TestingOutcome.PASSED,
            diagnostics=(
                f"Judge accepted the candidate across {len(test_cases)} case(s).",
                invocation_diagnostic,
            ),
            case_results=tuple(case_results),
            stdout=last_stdout,
            stderr=last_stderr,
            exit_code=last_exit_code,
        )


def _run_command(
    *,
    command: list[str],
    cwd: Path,
    timeout_seconds: float,
    stdin_text: str | None = None,
) -> _CompletedCommandProcess:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        stdout, stderr = process.communicate(
            input=stdin_text,
            timeout=timeout_seconds,
        )
        return _CompletedCommandProcess(
            stdout=stdout,
            stderr=stderr,
            returncode=process.returncode,
            timed_out=False,
        )
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        return _CompletedCommandProcess(
            stdout=stdout,
            stderr=stderr,
            returncode=process.returncode,
            timed_out=True,
        )


def _classify_script_process_failure(
    *,
    test_case: BenchmarkTestCase,
    completed: _CompletedCommandProcess,
) -> tuple[TestingOutcome, tuple[str, ...]]:
    stderr = completed.stderr.strip()
    if "SyntaxError" in stderr:
        return (
            TestingOutcome.COMPILATION_ERROR,
            (
                f"Case '{test_case.name}' failed before execution with a syntax error.",
                stderr or "SyntaxError",
            ),
        )
    return (
        TestingOutcome.RUNTIME_ERROR,
        (
            f"Case '{test_case.name}' exited with return code {completed.returncode}.",
            stderr or "The runtime did not emit stderr diagnostics.",
        ),
    )


def _expected_stdout_for_script_case(test_case: BenchmarkTestCase) -> str:
    if test_case.expected_stdout is not None:
        return test_case.expected_stdout
    if test_case.expected_output is not None:
        return str(test_case.expected_output)
    raise ValueError("script benchmark cases must define expected_stdout or expected_output")


def _normalize_text(value: str) -> str:
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    trimmed_lines = [line.rstrip(" \t") for line in lines]
    while trimmed_lines and trimmed_lines[-1] == "":
        trimmed_lines.pop()
    return "\n".join(trimmed_lines)


def _normalize_benchmark_language(value: str) -> str:
    normalized = value.strip().lower()
    aliases = {
        "python": "python",
        "py": "python",
        "javascript": "javascript",
        "js": "javascript",
        "node": "javascript",
        "nodejs": "javascript",
    }
    return aliases.get(normalized, normalized)


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


def _node_function_export_epilogue() -> str:
    return (
        "if (typeof module !== 'undefined' && module.exports && "
        "typeof solve === 'function' && typeof module.exports.solve !== 'function') {\n"
        "  module.exports.solve = solve;\n"
        "}\n"
    )


def _build_node_function_harness(
    *,
    settings: BenchmarkExecutionSettings,
    test_cases: tuple[BenchmarkTestCase, ...],
) -> str:
    payload = {
        "entrypoint": settings.entrypoint,
        "test_cases": [
            {
                "name": test_case.name,
                "arguments": list(test_case.arguments),
                "keyword_arguments": dict(test_case.keyword_arguments),
                "expected_output": test_case.expected_output,
                "expected_stdout": test_case.expected_stdout,
            }
            for test_case in test_cases
        ],
    }
    payload_json = json.dumps(payload)
    return f"""const fs = require("fs");
const path = require("path");

const SPEC = JSON.parse({payload_json!r});
const ENTRYPOINT = SPEC.entrypoint;
const TEST_CASES = SPEC.test_cases;

function normalizeText(value) {{
  return String(value)
    .replace(/\\r\\n/g, "\\n")
    .replace(/\\r/g, "\\n")
    .split("\\n")
    .map((line) => line.replace(/[ \\t]+$/g, ""))
    .filter((line, index, lines) => !(index >= lines.length - 1 && line === ""))
    .join("\\n");
}}

function normalizeValue(value) {{
  if (typeof value === "string") {{
    return normalizeText(value);
  }}
  return JSON.stringify(value);
}}

function writeResult(resultPath, payload) {{
  fs.writeFileSync(resultPath, JSON.stringify(payload), "utf8");
}}

const args = process.argv.slice(2);
const caseIndex = Number(args[args.indexOf("--case-index") + 1]);
const resultPath = path.resolve(args[args.indexOf("--result-path") + 1]);
const testCase = TEST_CASES[caseIndex];
const caseResults = [];

let candidateModule;
try {{
  candidateModule = require("./candidate.js");
}} catch (error) {{
  const outcome = error && error.name === "SyntaxError" ? "compilation_error" : "runtime_error";
  const diagnostics = [
    error && error.name === "SyntaxError"
      ? `Compilation failed: ${{error.message}}`
      : `Module import failed: ${{error.name}}: ${{error.message}}`,
  ];
  writeResult(resultPath, {{
    outcome,
    diagnostics,
    case_results: [{{
      name: testCase.name,
      outcome,
      diagnostics,
    }}],
  }});
  process.exit(0);
}}

const entrypoint = candidateModule[ENTRYPOINT];
if (typeof entrypoint !== "function") {{
  writeResult(resultPath, {{
    outcome: "runtime_error",
    diagnostics: [`Required callable '${{ENTRYPOINT}}' was not defined as a CommonJS export.`],
    case_results: [{{
      name: testCase.name,
      outcome: "runtime_error",
      diagnostics: [`Required callable '${{ENTRYPOINT}}' was not defined as a CommonJS export.`],
    }}],
  }});
  process.exit(0);
}}

const originalLog = console.log;
const stdoutChunks = [];
console.log = (...items) => {{
  stdoutChunks.push(items.map((item) => String(item)).join(" "));
}};

let value;
try {{
  value = entrypoint(...(testCase.arguments || []));
}} catch (error) {{
  console.log = originalLog;
  const diagnostics = [`Candidate raised ${{error.name}} during case '${{testCase.name}}': ${{error.message}}.`];
  writeResult(resultPath, {{
    outcome: "runtime_error",
    diagnostics,
    case_results: [{{
      name: testCase.name,
      outcome: "runtime_error",
      diagnostics,
      actual_stdout: stdoutChunks.length ? `${{stdoutChunks.join("\\n")}}\\n` : "",
    }}],
    stdout: stdoutChunks.length ? `${{stdoutChunks.join("\\n")}}\\n` : "",
  }});
  process.exit(0);
}}
console.log = originalLog;

const actualStdout = stdoutChunks.length ? `${{stdoutChunks.join("\\n")}}\\n` : "";
if (testCase.expected_output !== null && testCase.expected_output !== undefined) {{
  if (normalizeValue(value) !== normalizeValue(testCase.expected_output)) {{
    const diagnostics = [
      `Case '${{testCase.name}}' returned ${{JSON.stringify(value)}}; expected ${{JSON.stringify(testCase.expected_output)}}.`,
    ];
    writeResult(resultPath, {{
      outcome: "wrong_answer",
      diagnostics,
      case_results: [{{
        name: testCase.name,
        outcome: "wrong_answer",
        diagnostics,
        actual_output: value,
        expected_output: testCase.expected_output,
        actual_stdout: actualStdout,
        expected_stdout: testCase.expected_stdout,
      }}],
      stdout: actualStdout,
    }});
    process.exit(0);
  }}
}}

if (testCase.expected_stdout !== null && testCase.expected_stdout !== undefined) {{
  if (normalizeText(actualStdout) !== normalizeText(testCase.expected_stdout)) {{
    const diagnostics = [
      `Case '${{testCase.name}}' printed ${{JSON.stringify(actualStdout)}}; expected ${{JSON.stringify(testCase.expected_stdout)}}.`,
    ];
    writeResult(resultPath, {{
      outcome: "wrong_answer",
      diagnostics,
      case_results: [{{
        name: testCase.name,
        outcome: "wrong_answer",
        diagnostics,
        actual_output: value,
        expected_output: testCase.expected_output,
        actual_stdout: actualStdout,
        expected_stdout: testCase.expected_stdout,
      }}],
      stdout: actualStdout,
    }});
    process.exit(0);
  }}
}}

writeResult(resultPath, {{
  outcome: "passed",
  diagnostics: [`Judge accepted case '${{testCase.name}}'.`],
  case_results: [{{
    name: testCase.name,
    outcome: "passed",
    actual_output: value,
    expected_output: testCase.expected_output,
    actual_stdout: actualStdout,
    expected_stdout: testCase.expected_stdout,
  }}],
  stdout: actualStdout,
}});
process.exit(0);
"""
