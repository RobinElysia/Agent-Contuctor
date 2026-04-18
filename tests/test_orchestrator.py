from agentconductor import (
    DifficultyLevel,
    ProblemInstance,
    plan_problem_topology,
)
from agentconductor.application.orchestrator import ProblemShape, infer_problem_shape
from agentconductor.domain.topology import AgentRole


def test_plan_problem_topology_returns_easy_template() -> None:
    plan = plan_problem_topology(
        ProblemInstance(
            identifier="easy-sum",
            prompt="Return the sum of two integers.",
            difficulty=DifficultyLevel.EASY,
        )
    )

    assert plan.difficulty is DifficultyLevel.EASY
    assert len(plan.steps) == 3
    assert plan.steps[0].agents[0].role is AgentRole.PLANNING
    assert plan.steps[1].agents[0].role is AgentRole.CODING
    assert plan.steps[2].agents[0].role is AgentRole.TESTING


def test_plan_problem_topology_uses_knowledge_intensive_medium_template() -> None:
    plan = plan_problem_topology(
        ProblemInstance(
            identifier="medium-graph",
            prompt="Solve a graph shortest path problem under tight constraints.",
            difficulty=DifficultyLevel.MEDIUM,
        )
    )

    assert plan.difficulty is DifficultyLevel.MEDIUM
    assert infer_problem_shape(
        ProblemInstance(identifier="shape-check", prompt="graph shortest path")
    ) is ProblemShape.KNOWLEDGE_INTENSIVE
    assert plan.steps[0].agents[0].role is AgentRole.RETRIEVAL
    assert plan.steps[0].agents[1].role is AgentRole.PLANNING
    assert plan.steps[1].agents[0].role is AgentRole.ALGORITHMIC
    assert plan.steps[2].agents[0].role is AgentRole.TESTING


def test_plan_problem_topology_uses_debugging_shape_when_keywords_match() -> None:
    plan = plan_problem_topology(
        ProblemInstance(
            identifier="medium-debug",
            prompt="Fix the failing implementation and debug the incorrect output.",
            difficulty=DifficultyLevel.MEDIUM,
        )
    )

    assert infer_problem_shape(
        ProblemInstance(identifier="shape-debug", prompt="debug this broken code")
    ) is ProblemShape.DEBUGGING
    assert plan.steps[1].agents[0].role is AgentRole.DEBUGGING
    assert plan.steps[1].agents[1].role is AgentRole.CODING
    assert plan.steps[2].agents[0].role is AgentRole.TESTING


def test_plan_problem_topology_returns_valid_hard_template() -> None:
    plan = plan_problem_topology(
        ProblemInstance(
            identifier="hard-dp",
            prompt="Solve a dynamic programming problem with multiple constraints.",
            difficulty=DifficultyLevel.HARD,
        )
    )

    assert plan.difficulty is DifficultyLevel.HARD
    assert len(plan.steps) == 3
    assert plan.node_count <= plan.max_nodes
    assert plan.steps[0].agents[0].role is AgentRole.RETRIEVAL
    assert plan.steps[1].agents[0].role is AgentRole.ALGORITHMIC
    assert plan.steps[1].agents[1].role is AgentRole.CODING
    assert plan.steps[2].agents[0].role is AgentRole.TESTING


def test_plan_problem_topology_defaults_missing_difficulty_to_medium() -> None:
    plan = plan_problem_topology(
        ProblemInstance(
            identifier="default-medium",
            prompt="Implement a correct solution for this problem.",
        )
    )

    assert plan.difficulty is DifficultyLevel.MEDIUM
