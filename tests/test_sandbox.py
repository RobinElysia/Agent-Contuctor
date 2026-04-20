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
