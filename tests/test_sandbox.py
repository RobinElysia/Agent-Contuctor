import subprocess
import sys

import pytest

from agentconductor import (
    CodeCandidate,
    AgentRole,
    JudgeResourceLimits,
    JudgeTestCase,
    ProblemInstance,
    PythonSubprocessJudgeAdapter,
    SandboxTestSpec,
    TestingOutcome,
)
from agentconductor.infrastructure.windows_job import (
    BoundProcessContext,
    WindowsJobObjectBinder,
    build_process_limit_binder,
)


def test_python_subprocess_judge_adapter_accepts_valid_candidate() -> None:
    adapter = PythonSubprocessJudgeAdapter(timeout_seconds=1.0)
    result = adapter.evaluate(
        ProblemInstance(identifier="demo-pass", prompt="Write a correct solution."),
        CodeCandidate(
            step_index=1,
            agent_name="coder_1",
            role=AgentRole.CODING,
            source_code="def solve(a, b):\n    return a + b\n",
        ),
        SandboxTestSpec(
            entrypoint="solve",
            test_cases=(
                JudgeTestCase(name="sample-1", arguments=(1, 2), expected_output=3),
                JudgeTestCase(name="sample-2", arguments=(5, 7), expected_output=12),
            ),
            resource_limits=JudgeResourceLimits(cpu_time_seconds=1.0),
        ),
    )

    assert result.outcome is TestingOutcome.PASSED
    assert result.diagnostics == ("Judge accepted the candidate across 2 case(s).",)
    assert result.stdout == ""
    assert tuple(case.outcome for case in result.case_results) == (
        TestingOutcome.PASSED,
        TestingOutcome.PASSED,
    )
    assert tuple(case.name for case in result.case_results) == ("sample-1", "sample-2")


def test_python_subprocess_judge_adapter_reports_wrong_answer() -> None:
    adapter = PythonSubprocessJudgeAdapter(timeout_seconds=1.0)
    result = adapter.evaluate(
        ProblemInstance(identifier="demo-fail", prompt="Write a correct solution."),
        CodeCandidate(
            step_index=1,
            agent_name="coder_1",
            role=AgentRole.CODING,
            source_code="def solve(value):\n    return value * 2\n",
        ),
        SandboxTestSpec(
            entrypoint="solve",
            test_cases=(
                JudgeTestCase(name="sample-1", arguments=(4,), expected_output=5),
            ),
            resource_limits=JudgeResourceLimits(cpu_time_seconds=1.0),
        ),
    )

    assert result.outcome is TestingOutcome.WRONG_ANSWER
    assert result.diagnostics == (
        "Case 'sample-1' returned 8; expected 5.",
    )
    assert result.stdout == ""
    assert len(result.case_results) == 1
    assert result.case_results[0].name == "sample-1"
    assert result.case_results[0].outcome is TestingOutcome.WRONG_ANSWER
    assert result.case_results[0].actual_output == 8
    assert result.case_results[0].expected_output == 5


def test_python_subprocess_judge_adapter_normalizes_line_endings_and_trailing_spaces() -> None:
    adapter = PythonSubprocessJudgeAdapter(timeout_seconds=1.0)
    result = adapter.evaluate(
        ProblemInstance(identifier="demo-stdout", prompt="Print a normalized answer."),
        CodeCandidate(
            step_index=1,
            agent_name="coder_1",
            role=AgentRole.CODING,
            source_code='def solve():\n    print("alpha  \\r\\n beta\\t")\n',
        ),
        SandboxTestSpec(
            entrypoint="solve",
            test_cases=(
                JudgeTestCase(
                    name="stdout-normalization",
                    expected_stdout="alpha\n beta",
                ),
            ),
            resource_limits=JudgeResourceLimits(cpu_time_seconds=1.0),
        ),
    )

    assert result.outcome is TestingOutcome.PASSED
    assert len(result.case_results) == 1
    assert result.case_results[0].outcome is TestingOutcome.PASSED
    assert result.case_results[0].actual_stdout == "alpha  \r\n beta\t\n"


def test_python_subprocess_judge_adapter_enforces_hard_wall_clock_limit() -> None:
    adapter = PythonSubprocessJudgeAdapter(timeout_seconds=0.05)
    result = adapter.evaluate(
        ProblemInstance(identifier="demo-timeout", prompt="Loop forever."),
        CodeCandidate(
            step_index=1,
            agent_name="coder_1",
            role=AgentRole.CODING,
            source_code=(
                "def solve():\n"
                "    while True:\n"
                "        pass\n"
            ),
        ),
        SandboxTestSpec(
            entrypoint="solve",
            test_cases=(
                JudgeTestCase(name="infinite-loop"),
            ),
            resource_limits=JudgeResourceLimits(
                cpu_time_seconds=1.0,
                wall_time_seconds=0.05,
            ),
        ),
    )

    assert result.outcome is TestingOutcome.TIME_LIMIT_EXCEEDED
    assert result.diagnostics == (
        "Case 'infinite-loop' exceeded the hard wall-clock limit of 0.1s.",
    )
    assert len(result.case_results) == 1
    assert result.case_results[0].name == "infinite-loop"
    assert result.case_results[0].outcome is TestingOutcome.TIME_LIMIT_EXCEEDED


def test_windows_job_object_classification_maps_missing_result_to_memory_limit() -> None:
    context = BoundProcessContext(
        platform="win32",
        hard_memory_limit=True,
        hard_cpu_limit=False,
        hard_wall_time_limit=False,
        assigned_to_job=True,
        memory_limit_bytes=1024,
        peak_process_memory_used=1024,
    )

    outcome, diagnostics = context.classify_missing_result(return_code=1)

    assert outcome is TestingOutcome.MEMORY_LIMIT_EXCEEDED
    assert diagnostics == (
        "Windows Job Object enforcement stopped the worker near the configured process memory limit before the harness emitted a result.",
    )


@pytest.mark.skipif(sys.platform != "win32", reason="Windows Job Objects are only available on Windows.")
def test_windows_job_object_binder_assigns_worker_to_job() -> None:
    binder = build_process_limit_binder()
    assert isinstance(binder, WindowsJobObjectBinder)

    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import time; time.sleep(0.05)",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0),
    )
    context = None
    try:
        context = binder.bind(
            process_pid=process.pid,
            resource_limits=JudgeResourceLimits(memory_limit_bytes=64 * 1024 * 1024),
        )
        process.communicate(timeout=1.0)
        context.observe_process_exit()
        assert context.platform == "win32"
        assert context.memory_limit_bytes == 64 * 1024 * 1024
        if context.assigned_to_job:
            assert context.hard_memory_limit is True
            assert context.binding_diagnostics == (
                "Windows Job Object enforced a per-process memory limit.",
            )
        else:
            assert context.hard_memory_limit is False
            assert context.binding_diagnostics == (
                "Windows Job Object binding was unavailable in this host runtime; wall-clock enforcement remains active but hard memory enforcement could not be attached.",
            )
    finally:
        if context is not None:
            context.close()
        if process.poll() is None:
            process.kill()
        process.communicate()
