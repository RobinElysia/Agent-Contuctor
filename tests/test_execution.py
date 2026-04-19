import pytest

from agentconductor import (
    AgentInvocation,
    AgentReference,
    AgentRole,
    DifficultyLevel,
    ExecutionStatus,
    ProblemInstance,
    TestingOutcome,
    TopologyPlan,
    TopologyStep,
    TopologyValidationError,
    execute_topology_plan,
    plan_problem_topology,
)


def test_execute_topology_plan_runs_valid_plan_end_to_end() -> None:
    problem = ProblemInstance(
        identifier="medium-graph",
        prompt="Solve a graph shortest path problem under tight constraints.",
        difficulty=DifficultyLevel.MEDIUM,
    )
    plan = plan_problem_topology(problem)

    result = execute_topology_plan(problem, plan)

    assert result.status is ExecutionStatus.COMPLETED
    assert result.executed_steps == 3
    assert result.executed_agents == plan.node_count
    assert result.final_candidate_code is not None
    assert result.testing_outcome is TestingOutcome.PASSED
    assert result.sandbox_result is not None
    assert result.sandbox_result.outcome is TestingOutcome.PASSED
    coder_result = result.step_results[1].agent_results[1]
    assert coder_result.agent_name == "coder_1"
    assert tuple(output.agent_name for output in coder_result.consumed_outputs) == (
        "retrieval_0",
        "planner_0",
    )


def test_execute_topology_plan_preserves_testing_diagnostics() -> None:
    problem = ProblemInstance(
        identifier="easy-sum",
        prompt="Return the sum of two integers.",
        difficulty=DifficultyLevel.EASY,
    )
    plan = plan_problem_topology(problem)

    result = execute_topology_plan(problem, plan)

    testing_result = result.step_results[-1].agent_results[-1]
    assert testing_result.role is AgentRole.TESTING
    assert testing_result.testing_outcome is TestingOutcome.PASSED
    assert testing_result.candidate_code == result.final_candidate_code
    assert testing_result.sandbox_result is not None
    assert result.diagnostics == (
        "Local sandbox accepted the candidate code.",
    )


def test_execute_topology_plan_rejects_invalid_references() -> None:
    problem = ProblemInstance(
        identifier="invalid-ref",
        prompt="Implement a correct solution.",
        difficulty=DifficultyLevel.EASY,
    )
    invalid_plan = TopologyPlan(
        difficulty=DifficultyLevel.EASY,
        steps=(
            TopologyStep(
                index=0,
                agents=(AgentInvocation(name="planner_0", role=AgentRole.PLANNING),),
            ),
            TopologyStep(
                index=1,
                agents=(
                    AgentInvocation(
                        name="tester_1",
                        role=AgentRole.TESTING,
                        refs=(AgentReference(step_index=0, agent_name="missing_0"),),
                    ),
                ),
            ),
        ),
    )

    with pytest.raises(
        TopologyValidationError,
        match="references unknown prior agent 'missing_0'",
    ):
        execute_topology_plan(problem, invalid_plan)
