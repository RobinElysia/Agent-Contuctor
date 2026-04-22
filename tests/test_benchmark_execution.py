from pathlib import Path
import shutil

import pytest

from agentconductor import (
    BenchmarkDatasetFormat,
    BenchmarkEvaluationStatus,
    CodeCandidate,
    MultiLanguageBenchmarkJudgeAdapter,
    NodeJsBenchmarkJudgeAdapter,
    PythonBenchmarkJudgeAdapter,
    TestingOutcome,
    evaluate_candidate_against_benchmark_record,
    load_canonical_benchmark_dataset,
)
from agentconductor.domain.topology import AgentRole


def test_python_benchmark_judge_adapter_executes_function_record(
    tmp_path: Path,
) -> None:
    dataset = _load_fixture_dataset()
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
    assert Path(result.artifact_identifiers.result_artifact_uri).exists()
    assert Path(result.artifact_identifiers.log_artifact_uri).exists()


def test_python_benchmark_judge_adapter_runs_stdin_record_as_script(
    tmp_path: Path,
) -> None:
    dataset = _load_fixture_dataset()
    record = dataset.records[1]
    candidate = CodeCandidate(
        step_index=1,
        agent_name="coder_1",
        role=AgentRole.CODING,
        source_code=(
            "import sys\n"
            "data = sys.stdin.read().strip().split()\n"
            "values = [int(value) for value in data[1:]]\n"
            "print(min(values))\n"
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
    assert "standalone Python script" in " ".join(result.diagnostics)
    assert Path(result.artifact_identifiers.result_artifact_uri).exists()


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js runtime is unavailable.")
def test_multilanguage_benchmark_judge_adapter_executes_javascript_record(
    tmp_path: Path,
) -> None:
    dataset = _load_fixture_dataset()
    record = dataset.records[2]
    candidate = CodeCandidate(
        step_index=1,
        agent_name="coder_js",
        role=AgentRole.CODING,
        source_code="function solve(a, b) {\n  return a + b;\n}\n",
        language="javascript",
    )
    adapter = MultiLanguageBenchmarkJudgeAdapter(
        python_adapter=PythonBenchmarkJudgeAdapter(artifact_root=tmp_path),
        nodejs_adapter=NodeJsBenchmarkJudgeAdapter(artifact_root=tmp_path),
    )

    result = evaluate_candidate_against_benchmark_record(
        record,
        candidate,
        adapter=adapter,
    )

    assert result.status is BenchmarkEvaluationStatus.COMPLETED
    assert result.testing_outcome is TestingOutcome.PASSED
    assert result.verdict_mapping is not None
    assert result.verdict_mapping.native_verdict == "accepted"
    assert "Language runtime: javascript." in result.diagnostics
    assert Path(result.artifact_identifiers.result_artifact_uri).exists()


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js runtime is unavailable.")
def test_nodejs_benchmark_judge_adapter_reports_compilation_error(
    tmp_path: Path,
) -> None:
    dataset = _load_fixture_dataset()
    record = dataset.records[2]
    candidate = CodeCandidate(
        step_index=1,
        agent_name="coder_js",
        role=AgentRole.CODING,
        source_code="function solve(a, b) { return a + ; }\n",
        language="javascript",
    )
    adapter = NodeJsBenchmarkJudgeAdapter(artifact_root=tmp_path)

    result = evaluate_candidate_against_benchmark_record(
        record,
        candidate,
        adapter=adapter,
    )

    assert result.status is BenchmarkEvaluationStatus.COMPLETED
    assert result.testing_outcome is TestingOutcome.COMPILATION_ERROR
    assert result.verdict_mapping is not None
    assert result.verdict_mapping.native_verdict == "compilation_error"
    assert Path(result.artifact_identifiers.result_artifact_uri).exists()


def _load_fixture_dataset():
    fixture_path = Path(__file__).parent / "fixtures" / "benchmark" / "apps_fixture.jsonl"
    return load_canonical_benchmark_dataset(
        fixture_path,
        source_format=BenchmarkDatasetFormat.APPS_JSONL,
    )
