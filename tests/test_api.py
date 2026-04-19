import pytest

import agentconductor.application.api as api_module
from agentconductor import (
    AgentExecutionResult,
    AgentInvocation,
    AgentRole,
    AgentReference,
    DifficultyLevel,
    ExecutionStatus,
    ProblemInstance,
    SolveStatus,
    StopReason,
    StepExecutionResult,
    TestingOutcome,
    TopologyExecutionResult,
    TopologyPlan,
    TopologyStep,
    solve_problem,
)


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
    assert result.solve_state.completed_turns == 2
    assert result.solve_state.stop_reason is StopReason.TURN_BUDGET_EXHAUSTED
    assert result.execution.diagnostics == (
        "Synthetic failure for API-path verification.",
    )


def test_solve_problem_runs_second_turn_after_failure_and_stops_on_pass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executions: list[TopologyExecutionResult] = []
    planned_topologies: list[TopologyPlan] = []

    def fake_plan(problem: ProblemInstance) -> TopologyPlan:
        del problem
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
        planned_topologies.append(topology)
        return topology

    def fake_revise(revision_input):
        assert revision_input.turn_index == 1
        assert revision_input.testing_feedback.outcome is TestingOutcome.FAILED
        assert revision_input.testing_feedback.diagnostics == ("Wrong answer on sample.",)
        topology = TopologyPlan(
            difficulty=DifficultyLevel.EASY,
            steps=(
                TopologyStep(
                    index=0,
                    agents=(AgentInvocation(name="planner_t1_0", role=AgentRole.PLANNING),),
                ),
                TopologyStep(
                    index=1,
                    agents=(
                        AgentInvocation(
                            name="coder_t1_1",
                            role=AgentRole.CODING,
                            refs=(AgentReference(step_index=0, agent_name="planner_t1_0"),),
                        ),
                    ),
                ),
                TopologyStep(
                    index=2,
                    agents=(
                        AgentInvocation(
                            name="debugger_t1_2",
                            role=AgentRole.DEBUGGING,
                            refs=(AgentReference(step_index=1, agent_name="coder_t1_1"),),
                        ),
                    ),
                ),
                TopologyStep(
                    index=3,
                    agents=(
                        AgentInvocation(
                            name="tester_t1_3",
                            role=AgentRole.TESTING,
                            refs=(AgentReference(step_index=2, agent_name="debugger_t1_2"),),
                        ),
                    ),
                ),
            ),
        )
        planned_topologies.append(topology)
        return topology

    def fake_execute(problem: ProblemInstance, topology: TopologyPlan) -> TopologyExecutionResult:
        attempt_index = len(executions)
        if attempt_index == 0:
            result = TopologyExecutionResult(
                problem=problem,
                difficulty=DifficultyLevel.EASY,
                status=ExecutionStatus.COMPLETED,
                step_results=(
                    StepExecutionResult(
                        step_index=2,
                        agent_results=(
                            AgentExecutionResult(
                                step_index=2,
                                agent_name="tester_2",
                                role=AgentRole.TESTING,
                                summary="First attempt failed.",
                                references=(),
                                candidate_code="def solve():\n    return 'wrong'\n",
                                diagnostics=("Wrong answer on sample.",),
                                testing_outcome=TestingOutcome.FAILED,
                            ),
                        ),
                    ),
                ),
                final_candidate_code="def solve():\n    return 'wrong'\n",
                testing_outcome=TestingOutcome.FAILED,
                diagnostics=("Wrong answer on sample.",),
            )
        else:
            result = TopologyExecutionResult(
                problem=problem,
                difficulty=DifficultyLevel.EASY,
                status=ExecutionStatus.COMPLETED,
                step_results=(
                    StepExecutionResult(
                        step_index=3,
                        agent_results=(
                            AgentExecutionResult(
                                step_index=3,
                                agent_name="tester_t1_3",
                                role=AgentRole.TESTING,
                                summary="Second attempt passed.",
                                references=(),
                                candidate_code="def solve():\n    return 'fixed'\n",
                                diagnostics=("Accepted after revision.",),
                                testing_outcome=TestingOutcome.PASSED,
                            ),
                        ),
                    ),
                ),
                final_candidate_code="def solve():\n    return 'fixed'\n",
                testing_outcome=TestingOutcome.PASSED,
                diagnostics=("Accepted after revision.",),
            )
        executions.append(result)
        return result

    monkeypatch.setattr(api_module, "plan_topology_for_problem", fake_plan)
    monkeypatch.setattr(api_module, "revise_topology_for_feedback", fake_revise)
    monkeypatch.setattr(api_module, "execute_topology", fake_execute)

    result = solve_problem(
        ProblemInstance(
            identifier="apps-retry",
            prompt="Fix the failing implementation.",
            difficulty=DifficultyLevel.EASY,
        ),
        max_turns=2,
    )

    assert result.status is SolveStatus.COMPLETED
    assert len(planned_topologies) == 2
    assert len(executions) == 2
    assert result.topology is planned_topologies[-1]
    assert result.execution is executions[-1]
    assert result.solve_state.completed_turns == 2
    assert result.solve_state.stop_reason is StopReason.SOLVED
    assert result.solve_state.turns[0].testing_feedback.outcome is TestingOutcome.FAILED
    assert result.solve_state.turns[1].testing_feedback.outcome is TestingOutcome.PASSED
    assert result.candidate_solution == "def solve():\n    return 'fixed'\n"
