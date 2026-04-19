from agentconductor import (
    CodeCandidate,
    AgentRole,
    ProblemInstance,
    PythonSubprocessSandboxAdapter,
    SandboxTestSpec,
    TestingOutcome,
)


def test_python_subprocess_sandbox_adapter_accepts_valid_candidate() -> None:
    adapter = PythonSubprocessSandboxAdapter(timeout_seconds=1.0)
    result = adapter.evaluate(
        ProblemInstance(identifier="demo-pass", prompt="Write a correct solution."),
        CodeCandidate(
            step_index=1,
            agent_name="coder_1",
            role=AgentRole.CODING,
            source_code="def solve():\n    return 'write solved in sandbox'\n",
        ),
        SandboxTestSpec(entrypoint="solve", required_substrings=("write",)),
    )

    assert result.outcome is TestingOutcome.PASSED
    assert result.diagnostics == ("Local sandbox accepted the candidate code.",)
    assert "write solved in sandbox" in result.stdout


def test_python_subprocess_sandbox_adapter_reports_wrong_answer() -> None:
    adapter = PythonSubprocessSandboxAdapter(timeout_seconds=1.0)
    result = adapter.evaluate(
        ProblemInstance(identifier="demo-fail", prompt="Write a correct solution."),
        CodeCandidate(
            step_index=1,
            agent_name="coder_1",
            role=AgentRole.CODING,
            source_code="def solve():\n    return 'incorrect'\n",
        ),
        SandboxTestSpec(entrypoint="solve", required_substrings=("write",)),
    )

    assert result.outcome is TestingOutcome.WRONG_ANSWER
    assert result.diagnostics == (
        "Returned value missed required token(s): write.",
    )
    assert result.stdout == "incorrect"
