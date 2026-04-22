import pytest

from agentconductor import (
    BenchmarkEvaluationStatus,
    BenchmarkExecutionSettings,
    BenchmarkInvocationMode,
    BenchmarkProblemDefinition,
    CodeCandidate,
    StubBenchmarkAdapter,
    StubBenchmarkSubmission,
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
