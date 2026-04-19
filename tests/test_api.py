import pytest

import agentconductor.application.api as api_module
from agentconductor import (
    DifficultyLevel,
    ProblemInstance,
    SolveStatus,
    StopReason,
    TestingOutcome,
    solve_problem,
)
from agentconductor.domain.execution import (
    ExecutionStatus,
    StepExecutionResult,
    TopologyExecutionResult,
)
from agentconductor.domain.topology import AgentInvocation, AgentRole, TopologyPlan, TopologyStep


def test_solve_problem_returns_typed_boundary_result() -> None:
    result = solve_problem(
        ProblemInstance(
            identifier="apps-two-sum",
            prompt="Write a function that returns two indices adding up to a target.",
            difficulty=DifficultyLevel.EASY,
        )
    )

    assert result.problem_id == "apps-two-sum"
    assert result.status is SolveStatus.COMPLETED
    assert result.selected_difficulty is DifficultyLevel.EASY
    assert result.planned_turns == 2
    assert result.max_nodes == 4
    assert result.candidate_solution is not None
    assert result.testing_outcome is TestingOutcome.PASSED
    assert result.execution.status is ExecutionStatus.COMPLETED
    assert result.topology.difficulty is DifficultyLevel.EASY
    assert result.solve_state.completed_turns == 1
    assert result.solve_state.latest_turn is not None
    assert result.solve_state.latest_turn.topology is result.topology
    assert result.solve_state.stop_reason is StopReason.SOLVED
    assert result.available_roles == (
        "retrieval",
        "planning",
        "algorithmic",
        "coding",
        "debugging",
        "testing",
    )


def test_solve_problem_uses_inferred_baseline_defaults() -> None:
    result = solve_problem(
        ProblemInstance(
            identifier="apps-unknown",
            prompt="Solve the problem with a correct implementation.",
        ),
        max_turns=1,
    )

    assert result.selected_difficulty is DifficultyLevel.MEDIUM
    assert result.planned_turns == 1
    assert result.max_nodes == 7
    assert result.status is SolveStatus.COMPLETED
    assert result.execution.executed_steps >= 1
    assert result.solve_state.remaining_turns == 0
    assert result.solve_state.stop_reason is StopReason.SOLVED


def test_solve_problem_rejects_invalid_turn_budget() -> None:
    with pytest.raises(ValueError, match="max_turns must be <= 2"):
        solve_problem(
            ProblemInstance(identifier="bad-turns", prompt="Any prompt"),
            max_turns=3,
        )


def test_solve_problem_returns_failure_when_execution_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    topology = TopologyPlan(
        difficulty=DifficultyLevel.EASY,
        steps=(
            TopologyStep(
                index=0,
                agents=(AgentInvocation(name="planner_0", role=AgentRole.PLANNING),),
            ),
            TopologyStep(
                index=1,
                agents=(AgentInvocation(name="coder_1", role=AgentRole.CODING),),
            ),
            TopologyStep(
                index=2,
                agents=(AgentInvocation(name="tester_2", role=AgentRole.TESTING),),
            ),
        ),
    )
    failed_execution = TopologyExecutionResult(
        problem=ProblemInstance(
            identifier="apps-failure",
            prompt="Solve a failing problem.",
            difficulty=DifficultyLevel.EASY,
        ),
        difficulty=DifficultyLevel.EASY,
        status=ExecutionStatus.COMPLETED,
        step_results=(StepExecutionResult(step_index=0, agent_results=()),),
        final_candidate_code=None,
        testing_outcome=TestingOutcome.FAILED,
        diagnostics=("Synthetic failure for API-path verification.",),
    )

    monkeypatch.setattr(api_module, "plan_topology_for_problem", lambda problem: topology)
    monkeypatch.setattr(api_module, "execute_topology", lambda problem, topology: failed_execution)

    result = solve_problem(
        ProblemInstance(
            identifier="apps-failure",
            prompt="Solve a failing problem.",
            difficulty=DifficultyLevel.EASY,
        )
    )

    assert result.status is SolveStatus.FAILED
    assert result.candidate_solution is None
    assert result.testing_outcome is TestingOutcome.FAILED
    assert result.solve_state.completed_turns == 1
    assert result.solve_state.stop_reason is None
    assert result.execution.diagnostics == (
        "Synthetic failure for API-path verification.",
    )
