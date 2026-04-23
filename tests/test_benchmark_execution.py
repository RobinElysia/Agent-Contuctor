from pathlib import Path
import shutil

import pytest

from agentconductor import (
    BenchmarkDatasetFormat,
    BenchmarkExecutionSettings,
    BenchmarkInvocationMode,
    BenchmarkPhaseExecutionSettings,
    BenchmarkPhaseResourceLimits,
    BenchmarkExecutionPhase,
    BenchmarkEvaluationStatus,
    BenchmarkProblemDefinition,
    CppBenchmarkJudgeAdapter,
    CodeCandidate,
    JavaBenchmarkJudgeAdapter,
    MultiLanguageBenchmarkJudgeAdapter,
    NodeJsBenchmarkJudgeAdapter,
    PythonBenchmarkJudgeAdapter,
    BenchmarkTestCase,
    CanonicalBenchmarkRecord,
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
    assert result.phase_results[0].phase is BenchmarkExecutionPhase.RUN
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
    assert result.phase_results[0].phase is BenchmarkExecutionPhase.RUN
    assert Path(result.artifact_identifiers.result_artifact_uri).exists()


@pytest.mark.skipif(
    shutil.which("javac") is None or shutil.which("java") is None,
    reason="Java toolchain is unavailable.",
)
def test_java_benchmark_judge_adapter_executes_compiled_record(
    tmp_path: Path,
) -> None:
    problem = BenchmarkProblemDefinition(
        identifier="apps/test/java-sum",
        prompt="Read two integers from stdin and print their sum.",
        benchmark_name="apps",
        dataset_name="APPS",
        source_problem_id="java/1",
        language="java",
        split_name="test",
    )
    settings = BenchmarkExecutionSettings(
        language="java",
        invocation_mode=BenchmarkInvocationMode.STDIN,
        entrypoint=None,
        phase_settings=(
            BenchmarkPhaseExecutionSettings(
                phase=BenchmarkExecutionPhase.COMPILE,
                source_layout=("Main.java",),
                command=("javac", "Main.java"),
                executable_target="Main",
                resource_limits=BenchmarkPhaseResourceLimits(time_limit_seconds=5.0),
            ),
            BenchmarkPhaseExecutionSettings(
                phase=BenchmarkExecutionPhase.RUN,
                source_layout=("Main.class",),
                command=("java", "Main"),
                executable_target="Main",
                resource_limits=BenchmarkPhaseResourceLimits(time_limit_seconds=5.0),
            ),
        ),
        time_limit_seconds=5.0,
    )
    candidate = CodeCandidate(
        step_index=1,
        agent_name="coder_java",
        role=AgentRole.CODING,
        source_code=(
            "import java.io.*;\n"
            "import java.util.*;\n"
            "public class Main {\n"
            "  public static void main(String[] args) throws Exception {\n"
            "    Scanner scanner = new Scanner(System.in);\n"
            "    int a = scanner.nextInt();\n"
            "    int b = scanner.nextInt();\n"
            "    System.out.println(a + b);\n"
            "  }\n"
            "}\n"
        ),
        language="java",
    )
    adapter = JavaBenchmarkJudgeAdapter(artifact_root=tmp_path)
    record = CanonicalBenchmarkRecord(
        problem=problem,
        execution_settings=settings,
        test_cases=(
            BenchmarkTestCase(
                name="case-0",
                stdin_text="2 5\n",
                expected_stdout="7\n",
            ),
        ),
    )

    result = evaluate_candidate_against_benchmark_record(
        record,
        candidate,
        adapter=adapter,
    )

    assert result.status is BenchmarkEvaluationStatus.COMPLETED
    assert result.testing_outcome is TestingOutcome.PASSED
    assert [phase.phase for phase in result.phase_results] == [
        BenchmarkExecutionPhase.COMPILE,
        BenchmarkExecutionPhase.RUN,
    ]
    assert result.phase_results[0].status.value == "completed"
    assert result.phase_results[1].repository_outcome is TestingOutcome.PASSED
    assert Path(result.artifact_identifiers.result_artifact_uri).exists()
    assert len(result.artifact_identifiers.phase_artifacts) == 2


@pytest.mark.skipif(
    shutil.which("javac") is None or shutil.which("java") is None,
    reason="Java toolchain is unavailable.",
)
def test_java_benchmark_judge_adapter_reports_compile_phase_failure(
    tmp_path: Path,
) -> None:
    problem = BenchmarkProblemDefinition(
        identifier="apps/test/java-bad",
        prompt="Read two integers from stdin and print their sum.",
        benchmark_name="apps",
        dataset_name="APPS",
        source_problem_id="java/2",
        language="java",
        split_name="test",
    )
    settings = BenchmarkExecutionSettings(
        language="java",
        invocation_mode=BenchmarkInvocationMode.STDIN,
        entrypoint=None,
        phase_settings=(
            BenchmarkPhaseExecutionSettings(
                phase=BenchmarkExecutionPhase.COMPILE,
                source_layout=("Main.java",),
                command=("javac", "Main.java"),
                executable_target="Main",
            ),
            BenchmarkPhaseExecutionSettings(
                phase=BenchmarkExecutionPhase.RUN,
                source_layout=("Main.class",),
                command=("java", "Main"),
                executable_target="Main",
            ),
        ),
        time_limit_seconds=5.0,
    )
    candidate = CodeCandidate(
        step_index=1,
        agent_name="coder_java",
        role=AgentRole.CODING,
        source_code=(
            "public class Main {\n"
            "  public static void main(String[] args) {\n"
            "    System.out.println(1 + );\n"
            "  }\n"
            "}\n"
        ),
        language="java",
    )
    adapter = JavaBenchmarkJudgeAdapter(artifact_root=tmp_path)
    record = CanonicalBenchmarkRecord(
        problem=problem,
        execution_settings=settings,
        test_cases=(
            BenchmarkTestCase(
                name="case-0",
                stdin_text="2 5\n",
                expected_stdout="7\n",
            ),
        ),
    )

    result = evaluate_candidate_against_benchmark_record(
        record,
        candidate,
        adapter=adapter,
    )

    assert result.status is BenchmarkEvaluationStatus.COMPLETED
    assert result.testing_outcome is TestingOutcome.COMPILATION_ERROR
    assert len(result.phase_results) == 1
    assert result.phase_results[0].phase is BenchmarkExecutionPhase.COMPILE
    assert result.phase_results[0].repository_outcome is TestingOutcome.COMPILATION_ERROR
    assert Path(result.artifact_identifiers.result_artifact_uri).exists()


def test_cpp_benchmark_judge_adapter_reports_missing_toolchain(
    tmp_path: Path,
) -> None:
    problem = BenchmarkProblemDefinition(
        identifier="apps/test/cpp-sum",
        prompt="Read two integers from stdin and print their sum.",
        benchmark_name="apps",
        dataset_name="APPS",
        source_problem_id="cpp/1",
        language="cpp",
        split_name="test",
    )
    settings = BenchmarkExecutionSettings(
        language="cpp",
        invocation_mode=BenchmarkInvocationMode.STDIN,
        entrypoint=None,
        phase_settings=(
            BenchmarkPhaseExecutionSettings(
                phase=BenchmarkExecutionPhase.COMPILE,
                source_layout=("main.cpp",),
                command=("missing-gpp", "main.cpp", "-o", "main.exe"),
                executable_target="main.exe",
            ),
            BenchmarkPhaseExecutionSettings(
                phase=BenchmarkExecutionPhase.RUN,
                source_layout=("main.exe",),
                command=("{executable}",),
                executable_target="main.exe",
            ),
        ),
    )
    candidate = CodeCandidate(
        step_index=1,
        agent_name="coder_cpp",
        role=AgentRole.CODING,
        source_code="#include <iostream>\nint main(){ std::cout << 3 << std::endl; }\n",
        language="cpp",
    )
    adapter = CppBenchmarkJudgeAdapter(
        artifact_root=tmp_path,
        compiler_command="missing-gpp",
    )
    record = CanonicalBenchmarkRecord(
        problem=problem,
        execution_settings=settings,
        test_cases=(
            BenchmarkTestCase(
                name="case-0",
                stdin_text="2 5\n",
                expected_stdout="7\n",
            ),
        ),
    )

    result = evaluate_candidate_against_benchmark_record(
        record,
        candidate,
        adapter=adapter,
    )

    assert result.status is BenchmarkEvaluationStatus.ADAPTER_ERROR
    assert result.testing_outcome is None
    assert "missing-gpp" in result.diagnostics[0]


def _load_fixture_dataset():
    fixture_path = Path(__file__).parent / "fixtures" / "benchmark" / "apps_fixture.jsonl"
    return load_canonical_benchmark_dataset(
        fixture_path,
        source_format=BenchmarkDatasetFormat.APPS_JSONL,
    )
