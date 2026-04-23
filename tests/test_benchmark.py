import pytest

from agentconductor import (
    BenchmarkEvaluationStatus,
    BenchmarkExecutionPhase,
    BenchmarkExecutionSettings,
    BenchmarkInvocationMode,
    BenchmarkPhaseExecutionSettings,
    BenchmarkPhaseResult,
    BenchmarkPhaseStatus,
    BenchmarkProblemDefinition,
    BenchmarkRuntimeMode,
    CodeCandidate,
    StubBenchmarkAdapter,
    StubBenchmarkSubmission,
    StubVendorNativeBenchmarkAdapter,
    StubVendorSubmissionScenario,
    TestingOutcome,
    evaluate_candidate_against_benchmark,
)
from agentconductor.domain.topology import AgentRole


def test_benchmark_problem_definition_rejects_empty_metadata() -> None:
    with pytest.raises(ValueError, match="benchmark_name"):
        BenchmarkProblemDefinition(
            identifier="apps-1",
            prompt="Return the sum of two values.",
            benchmark_name="",
            dataset_name="APPS",
            source_problem_id="train/1",
        )


def test_benchmark_execution_settings_validate_limits() -> None:
    with pytest.raises(ValueError, match="time_limit_seconds"):
        BenchmarkExecutionSettings(time_limit_seconds=0.0)

    with pytest.raises(ValueError, match="entrypoint"):
        BenchmarkExecutionSettings(
            invocation_mode=BenchmarkInvocationMode.FUNCTION,
            entrypoint=None,
        )

    with pytest.raises(ValueError, match="compile phase settings require"):
        BenchmarkPhaseExecutionSettings(phase=BenchmarkExecutionPhase.COMPILE)


def test_benchmark_execution_settings_support_compiled_language_phase_contract() -> None:
    settings = BenchmarkExecutionSettings(
        language="cpp",
        invocation_mode=BenchmarkInvocationMode.STDIN,
        entrypoint=None,
        phase_settings=(
            BenchmarkPhaseExecutionSettings(
                phase=BenchmarkExecutionPhase.COMPILE,
                source_layout=("main.cpp",),
                command=("g++", "main.cpp", "-O2", "-o", "main"),
                executable_target="main",
            ),
            BenchmarkPhaseExecutionSettings(
                phase=BenchmarkExecutionPhase.RUN,
                source_layout=("main.cpp",),
                command=("./main",),
                executable_target="main",
            ),
        ),
    )

    assert settings.requires_compilation is True
    assert settings.compile_phase is not None
    assert settings.run_phase is not None
    assert settings.compile_phase.executable_target == "main"
    assert settings.run_phase.command == ("./main",)


def test_stub_benchmark_adapter_maps_native_verdict_to_repository_types(
    tmp_path,
) -> None:
    problem = BenchmarkProblemDefinition(
        identifier="apps-sum",
        prompt="Return the sum of two values.",
        benchmark_name="apps",
        dataset_name="APPS",
        source_problem_id="train/42",
        split_name="train",
        language="python",
    )
    candidate = CodeCandidate(
        step_index=1,
        agent_name="coder_1",
        role=AgentRole.CODING,
        source_code="def solve():\n    return 3\n",
        language="python",
    )
    settings = BenchmarkExecutionSettings(
        language="python",
        invocation_mode=BenchmarkInvocationMode.FUNCTION,
        entrypoint="solve",
        time_limit_seconds=2.0,
        memory_limit_bytes=256 * 1024 * 1024,
    )
    adapter = StubBenchmarkAdapter(
        submissions={
            "train/42": StubBenchmarkSubmission(
                native_verdict="accepted",
                run_id="run-001",
                submission_id="submission-001",
                result_artifact_uri=str(tmp_path / "result.json"),
                log_artifact_uri=str(tmp_path / "judge.log"),
                diagnostics=("stub benchmark accepted the submission",),
                phase_results=(
                    BenchmarkPhaseResult(
                        phase=BenchmarkExecutionPhase.RUN,
                        status=BenchmarkPhaseStatus.COMPLETED,
                        repository_outcome=TestingOutcome.PASSED,
                        diagnostics=("stub run completed",),
                    ),
                ),
            )
        }
    )

    result = evaluate_candidate_against_benchmark(
        problem,
        candidate,
        settings,
        adapter=adapter,
    )

    assert result.status is BenchmarkEvaluationStatus.COMPLETED
    assert result.testing_outcome is TestingOutcome.PASSED
    assert result.verdict_mapping is not None
    assert result.verdict_mapping.native_verdict == "accepted"
    assert result.artifact_identifiers is not None
    assert result.artifact_identifiers.run_id == "run-001"
    assert result.artifact_identifiers.submission_id == "submission-001"
    assert result.runtime_mode is BenchmarkRuntimeMode.VENDOR_STUB
    assert result.phase_results[0].phase is BenchmarkExecutionPhase.RUN


def test_stub_benchmark_adapter_reports_unmapped_native_verdict() -> None:
    problem = BenchmarkProblemDefinition(
        identifier="apps-sum",
        prompt="Return the sum of two values.",
        benchmark_name="apps",
        dataset_name="APPS",
        source_problem_id="train/99",
    )
    candidate = CodeCandidate(
        step_index=1,
        agent_name="coder_1",
        role=AgentRole.CODING,
        source_code="def solve():\n    return 3\n",
    )
    settings = BenchmarkExecutionSettings()
    adapter = StubBenchmarkAdapter(
        submissions={
            "train/99": StubBenchmarkSubmission(
                native_verdict="presentation_error",
                run_id="run-002",
            )
        }
    )

    result = evaluate_candidate_against_benchmark(
        problem,
        candidate,
        settings,
        adapter=adapter,
    )

    assert result.status is BenchmarkEvaluationStatus.ADAPTER_ERROR
    assert result.testing_outcome is None
    assert "presentation_error" in result.diagnostics[0]


def test_stub_benchmark_adapter_preserves_compile_phase_failure() -> None:
    problem = BenchmarkProblemDefinition(
        identifier="apps-cpp",
        prompt="Compile a C++ program.",
        benchmark_name="apps",
        dataset_name="APPS",
        source_problem_id="train/cpp-1",
        language="cpp",
    )
    candidate = CodeCandidate(
        step_index=1,
        agent_name="coder_cpp",
        role=AgentRole.CODING,
        source_code="int main(){ return 0 }",
        language="cpp",
    )
    settings = BenchmarkExecutionSettings(
        language="cpp",
        invocation_mode=BenchmarkInvocationMode.STDIN,
        entrypoint=None,
        phase_settings=(
            BenchmarkPhaseExecutionSettings(
                phase=BenchmarkExecutionPhase.COMPILE,
                source_layout=("main.cpp",),
                command=("g++", "main.cpp", "-o", "main"),
                executable_target="main",
            ),
            BenchmarkPhaseExecutionSettings(
                phase=BenchmarkExecutionPhase.RUN,
                source_layout=("main.cpp",),
                command=("./main",),
                executable_target="main",
            ),
        ),
    )
    adapter = StubBenchmarkAdapter(
        submissions={
            "train/cpp-1": StubBenchmarkSubmission(
                native_verdict="compilation_error",
                run_id="run-cpp-001",
                phase_results=(
                    BenchmarkPhaseResult(
                        phase=BenchmarkExecutionPhase.COMPILE,
                        status=BenchmarkPhaseStatus.FAILED,
                        repository_outcome=TestingOutcome.COMPILATION_ERROR,
                        diagnostics=("g++ failed during compile phase",),
                    ),
                ),
            )
        }
    )

    result = evaluate_candidate_against_benchmark(
        problem,
        candidate,
        settings,
        adapter=adapter,
    )

    assert result.testing_outcome is TestingOutcome.COMPILATION_ERROR
    assert result.phase_results[0].phase is BenchmarkExecutionPhase.COMPILE
    assert result.phase_results[0].repository_outcome is TestingOutcome.COMPILATION_ERROR


def test_stub_vendor_native_adapter_reports_submission_lifecycle() -> None:
    problem = BenchmarkProblemDefinition(
        identifier="apps-sum",
        prompt="Return the sum of two values.",
        benchmark_name="apps",
        dataset_name="APPS",
        source_problem_id="vendor/42",
        language="python",
    )
    candidate = CodeCandidate(
        step_index=1,
        agent_name="coder_1",
        role=AgentRole.CODING,
        source_code="def solve(a, b):\n    return a + b\n",
        language="python",
    )
    settings = BenchmarkExecutionSettings(
        language="python",
        vendor_runtime_name="apps-native",
        runtime_mode=BenchmarkRuntimeMode.VENDOR_NATIVE,
    )
    adapter = StubVendorNativeBenchmarkAdapter(
        submissions={
            "vendor/42": StubVendorSubmissionScenario(
                native_verdict="accepted",
                run_id="vendor-run-001",
                submission_id="submission-001",
                polls_before_terminal=2,
                result_artifact_uri="vendor://results/001",
                log_artifact_uri="vendor://logs/001",
                diagnostics=("vendor accepted the submission",),
            )
        }
    )

    result = evaluate_candidate_against_benchmark(
        problem,
        candidate,
        settings,
        adapter=adapter,
    )

    assert result.status is BenchmarkEvaluationStatus.COMPLETED
    assert result.runtime_mode is BenchmarkRuntimeMode.VENDOR_STUB
    assert result.testing_outcome is TestingOutcome.PASSED
    assert result.vendor_submission_receipt is not None
    assert result.vendor_submission_receipt.submission_id == "submission-001"
    assert [snapshot.state.value for snapshot in result.vendor_poll_history] == [
        "submitted",
        "running",
        "running",
        "completed",
    ]
    assert result.artifact_identifiers is not None
    assert result.artifact_identifiers.result_artifact_uri == "vendor://results/001"


def test_stub_vendor_native_adapter_reports_adapter_error() -> None:
    problem = BenchmarkProblemDefinition(
        identifier="apps-sum",
        prompt="Return the sum of two values.",
        benchmark_name="apps",
        dataset_name="APPS",
        source_problem_id="vendor/error",
        language="python",
    )
    candidate = CodeCandidate(
        step_index=1,
        agent_name="coder_1",
        role=AgentRole.CODING,
        source_code="def solve(a, b):\n    return a + b\n",
        language="python",
    )
    settings = BenchmarkExecutionSettings(
        language="python",
        vendor_runtime_name="apps-native",
        runtime_mode=BenchmarkRuntimeMode.VENDOR_NATIVE,
    )
    adapter = StubVendorNativeBenchmarkAdapter(
        submissions={
            "vendor/error": StubVendorSubmissionScenario(
                native_verdict="accepted",
                run_id="vendor-run-002",
                submission_id="submission-002",
                adapter_error_message="Vendor authentication failed.",
            )
        }
    )

    result = evaluate_candidate_against_benchmark(
        problem,
        candidate,
        settings,
        adapter=adapter,
    )

    assert result.status is BenchmarkEvaluationStatus.ADAPTER_ERROR
    assert result.runtime_mode is BenchmarkRuntimeMode.VENDOR_STUB
    assert result.vendor_submission_receipt is not None
    assert result.vendor_poll_history[-1].state.value == "adapter_error"
    assert result.diagnostics == ("Vendor authentication failed.",)
