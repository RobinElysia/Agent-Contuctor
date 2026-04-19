import pytest

from agentconductor import (
    AgentInvocation,
    AgentRole,
    DifficultyLevel,
    ExecutionStatus,
    ProblemInstance,
    SolveStateTransitionError,
    StopReason,
    TestingOutcome,
    TopologyPlan,
    TopologyStep,
)
from agentconductor.application.history import (
    append_turn_result,
    build_revision_input,
    initialize_solve_state,
)
from agentconductor.domain.execution import (
    AgentExecutionResult,
    StepExecutionResult,
    TopologyExecutionResult,
)


def test_append_turn_result_preserves_turn_history_and_revision_feedback() -> None:
    problem = ProblemInstance(
        identifier="apps-revise",
        prompt="Fix the implementation after a failing test.",
        difficulty=DifficultyLevel.MEDIUM,
    )
    state = initialize_solve_state(
        problem=problem,
        max_turns=2,
        max_nodes=7,
        available_roles=("planning", "coding", "testing"),
    )
    topology = TopologyPlan(
        difficulty=DifficultyLevel.MEDIUM,
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
    execution = TopologyExecutionResult(
        problem=problem,
        difficulty=DifficultyLevel.MEDIUM,
        status=ExecutionStatus.COMPLETED,
        step_results=(
            StepExecutionResult(
                step_index=2,
                agent_results=(
                    AgentExecutionResult(
                        step_index=2,
                        agent_name="tester_2",
                        role=AgentRole.TESTING,
                        summary="Testing reported a deterministic failure.",
                        references=(),
                        candidate_code="def solve():\n    return 'wrong'\n",
                        diagnostics=("Wrong answer on sample 1.",),
                        testing_outcome=TestingOutcome.FAILED,
                    ),
                ),
            ),
        ),
        final_candidate_code="def solve():\n    return 'wrong'\n",
        testing_outcome=TestingOutcome.FAILED,
        diagnostics=("Wrong answer on sample 1.",),
    )

    updated_state = append_turn_result(state, topology=topology, execution=execution)
    revision_input = build_revision_input(updated_state)

    assert updated_state.completed_turns == 1
    assert updated_state.can_continue is True
    assert updated_state.latest_turn is not None
    assert updated_state.latest_turn.topology is topology
    assert updated_state.latest_turn.execution is execution
    assert updated_state.latest_turn.testing_feedback.outcome is TestingOutcome.FAILED
    assert updated_state.latest_turn.testing_feedback.diagnostics == (
        "Wrong answer on sample 1.",
    )
    assert revision_input.turn_index == 1
    assert revision_input.prior_topology is topology
    assert revision_input.testing_feedback.candidate_code == execution.final_candidate_code
    assert revision_input.remaining_turns == 1


def test_append_turn_result_rejects_transition_after_terminal_state() -> None:
    problem = ProblemInstance(
        identifier="apps-solved",
        prompt="Return the right answer.",
        difficulty=DifficultyLevel.EASY,
    )
    state = initialize_solve_state(
        problem=problem,
        max_turns=2,
        max_nodes=4,
        available_roles=("planning", "coding", "testing"),
    )
    topology = TopologyPlan(
        difficulty=DifficultyLevel.EASY,
        steps=(
            TopologyStep(
                index=0,
                agents=(AgentInvocation(name="planner_0", role=AgentRole.PLANNING),),
            ),
            TopologyStep(
                index=1,
                agents=(AgentInvocation(name="tester_1", role=AgentRole.TESTING),),
            ),
        ),
    )
    execution = TopologyExecutionResult(
        problem=problem,
        difficulty=DifficultyLevel.EASY,
        status=ExecutionStatus.COMPLETED,
        step_results=(),
        final_candidate_code="def solve():\n    return 'ok'\n",
        testing_outcome=TestingOutcome.PASSED,
        diagnostics=("Accepted.",),
    )

    solved_state = append_turn_result(state, topology=topology, execution=execution)

    assert solved_state.stop_reason is StopReason.SOLVED
    with pytest.raises(
        SolveStateTransitionError,
        match="cannot append a turn to a terminal solve state",
    ):
        append_turn_result(solved_state, topology=topology, execution=execution)
