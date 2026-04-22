from pathlib import Path

from agentconductor import (
    BenchmarkDatasetFormat,
    BenchmarkEvaluationStatus,
    CodeCandidate,
    PythonBenchmarkJudgeAdapter,
    TestingOutcome,
    evaluate_candidate_against_benchmark_record,
    load_canonical_benchmark_dataset,
)
from agentconductor.domain.topology import AgentRole


def test_python_benchmark_judge_adapter_executes_function_record(
    tmp_path: Path,
) -> None:
    fixture_path = (
        Path(__file__).parent / "fixtures" / "benchmark" / "apps_fixture.jsonl"
    )
    dataset = load_canonical_benchmark_dataset(
        fixture_path,
        source_format=BenchmarkDatasetFormat.APPS_JSONL,
    )
    record = dataset.records[0]
    candidate = CodeCandidate(
        step_index=1,
        agent_name="coder_1",
        role=AgentRole.CODING,
        source_code="def solve(a, b):\n    return a + b\n",
        language="python",
    )
    adapter = PythonBenchmarkJudgeAdapter(artifact_root=tmp_path)

    result = evaluate_candidate_against_benchmark_record(
        record,
        candidate,
        adapter=adapter,
    )

    assert result.status is BenchmarkEvaluationStatus.COMPLETED
    assert result.testing_outcome is TestingOutcome.PASSED
    assert result.verdict_mapping is not None
    assert result.verdict_mapping.native_verdict == "accepted"
    assert "external benchmark path" in result.diagnostics[0]
    assert result.artifact_identifiers is not None
    assert Path(result.artifact_identifiers.result_artifact_uri).exists()
    assert Path(result.artifact_identifiers.log_artifact_uri).exists()


def test_python_benchmark_judge_adapter_reports_wrong_answer_for_stdin_record(
    tmp_path: Path,
) -> None:
    fixture_path = (
        Path(__file__).parent / "fixtures" / "benchmark" / "apps_fixture.jsonl"
    )
    dataset = load_canonical_benchmark_dataset(
        fixture_path,
        source_format=BenchmarkDatasetFormat.APPS_JSONL,
    )
    record = dataset.records[1]
    candidate = CodeCandidate(
        step_index=1,
        agent_name="coder_1",
        role=AgentRole.CODING,
        source_code=(
            "def solve():\n"
            "    import sys\n"
            "    data = sys.stdin.read().strip().split()\n"
            "    print(min(int(value) for value in data[1:]))\n"
        ),
        language="python",
    )
    adapter = PythonBenchmarkJudgeAdapter(artifact_root=tmp_path)

    result = evaluate_candidate_against_benchmark_record(
        record,
        candidate,
        adapter=adapter,
    )

    assert result.status is BenchmarkEvaluationStatus.COMPLETED
    assert result.testing_outcome is TestingOutcome.WRONG_ANSWER
    assert result.verdict_mapping is not None
    assert result.verdict_mapping.native_verdict == "wrong_answer"
    assert result.artifact_identifiers is not None
    assert Path(result.artifact_identifiers.result_artifact_uri).exists()
