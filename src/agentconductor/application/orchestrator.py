"""Deterministic rule-based topology planning."""

from __future__ import annotations

from enum import StrEnum

from agentconductor.domain.models import DifficultyLevel, ProblemInstance
from agentconductor.domain.topology import (
    AgentInvocation,
    AgentReference,
    AgentRole,
    TopologyPlan,
    TopologyStep,
)


class ProblemShape(StrEnum):
    """Coarse local problem categories used by the rule-based orchestrator."""

    GENERAL = "general"
    KNOWLEDGE_INTENSIVE = "knowledge_intensive"
    DEBUGGING = "debugging"


KNOWLEDGE_KEYWORDS = (
    "graph",
    "tree",
    "dynamic programming",
    "dp",
    "constraint",
    "geometry",
    "combin",
)
DEBUGGING_KEYWORDS = (
    "debug",
    "bug",
    "fix",
    "error",
    "failing",
    "incorrect",
    "broken",
)


def infer_problem_shape(problem: ProblemInstance) -> ProblemShape:
    """Infer a coarse problem shape from the prompt text.

    Inference:
    The paper does not define an explicit runtime taxonomy for prompt shape.
    This repository uses a small deterministic keyword heuristic so the initial
    orchestrator remains local, inspectable, and replaceable.
    """
    prompt = problem.prompt.lower()
    if any(keyword in prompt for keyword in DEBUGGING_KEYWORDS):
        return ProblemShape.DEBUGGING
    if any(keyword in prompt for keyword in KNOWLEDGE_KEYWORDS):
        return ProblemShape.KNOWLEDGE_INTENSIVE
    return ProblemShape.GENERAL


def plan_topology_for_problem(problem: ProblemInstance) -> TopologyPlan:
    """Return a deterministic single-turn topology plan for a problem."""
    difficulty = problem.difficulty or DifficultyLevel.MEDIUM
    shape = infer_problem_shape(problem)

    if difficulty is DifficultyLevel.EASY:
        return _easy_topology()
    if difficulty is DifficultyLevel.HARD:
        return _hard_topology(shape)
    return _medium_topology(shape)


def _easy_topology() -> TopologyPlan:
    return TopologyPlan(
        difficulty=DifficultyLevel.EASY,
        steps=(
            TopologyStep(
                index=0,
                agents=(
                    AgentInvocation(name="planner_0", role=AgentRole.PLANNING),
                ),
            ),
            TopologyStep(
                index=1,
                agents=(
                    AgentInvocation(
                        name="coder_1",
                        role=AgentRole.CODING,
                        refs=(AgentReference(step_index=0, agent_name="planner_0"),),
                    ),
                ),
            ),
            TopologyStep(
                index=2,
                agents=(
                    AgentInvocation(
                        name="tester_2",
                        role=AgentRole.TESTING,
                        refs=(
                            AgentReference(step_index=0, agent_name="planner_0"),
                            AgentReference(step_index=1, agent_name="coder_1"),
                        ),
                    ),
                ),
            ),
        ),
    )


def _medium_topology(shape: ProblemShape) -> TopologyPlan:
    if shape is ProblemShape.DEBUGGING:
        return TopologyPlan(
            difficulty=DifficultyLevel.MEDIUM,
            steps=(
                TopologyStep(
                    index=0,
                    agents=(
                        AgentInvocation(name="planner_0", role=AgentRole.PLANNING),
                    ),
                ),
                TopologyStep(
                    index=1,
                    agents=(
                        AgentInvocation(
                            name="debugger_1",
                            role=AgentRole.DEBUGGING,
                            refs=(AgentReference(step_index=0, agent_name="planner_0"),),
                        ),
                        AgentInvocation(
                            name="coder_1",
                            role=AgentRole.CODING,
                            refs=(AgentReference(step_index=0, agent_name="planner_0"),),
                        ),
                    ),
                ),
                TopologyStep(
                    index=2,
                    agents=(
                        AgentInvocation(
                            name="tester_2",
                            role=AgentRole.TESTING,
                            refs=(
                                AgentReference(step_index=1, agent_name="debugger_1"),
                                AgentReference(step_index=1, agent_name="coder_1"),
                            ),
                        ),
                    ),
                ),
            ),
        )

    step_zero_agents = [
        AgentInvocation(name="planner_0", role=AgentRole.PLANNING),
    ]
    if shape is ProblemShape.KNOWLEDGE_INTENSIVE:
        step_zero_agents.insert(
            0, AgentInvocation(name="retrieval_0", role=AgentRole.RETRIEVAL)
        )

    step_one_refs = [AgentReference(step_index=0, agent_name="planner_0")]
    if shape is ProblemShape.KNOWLEDGE_INTENSIVE:
        step_one_refs.insert(0, AgentReference(step_index=0, agent_name="retrieval_0"))

    return TopologyPlan(
        difficulty=DifficultyLevel.MEDIUM,
        steps=(
            TopologyStep(index=0, agents=tuple(step_zero_agents)),
            TopologyStep(
                index=1,
                agents=(
                    AgentInvocation(
                        name="algorithmic_1",
                        role=AgentRole.ALGORITHMIC,
                        refs=tuple(step_one_refs),
                    ),
                    AgentInvocation(
                        name="coder_1",
                        role=AgentRole.CODING,
                        refs=tuple(step_one_refs),
                    ),
                ),
            ),
            TopologyStep(
                index=2,
                agents=(
                    AgentInvocation(
                        name="tester_2",
                        role=AgentRole.TESTING,
                        refs=(
                            AgentReference(step_index=1, agent_name="algorithmic_1"),
                            AgentReference(step_index=1, agent_name="coder_1"),
                        ),
                    ),
                ),
            ),
        ),
    )


def _hard_topology(shape: ProblemShape) -> TopologyPlan:
    step_zero_agents = [
        AgentInvocation(name="retrieval_0", role=AgentRole.RETRIEVAL),
        AgentInvocation(name="planner_0", role=AgentRole.PLANNING),
    ]
    if shape is ProblemShape.DEBUGGING:
        step_zero_agents = [
            AgentInvocation(name="planner_0", role=AgentRole.PLANNING),
            AgentInvocation(name="debugger_0", role=AgentRole.DEBUGGING),
        ]

    common_refs = tuple(
        AgentReference(step_index=0, agent_name=agent.name) for agent in step_zero_agents
    )

    step_one_agents = [
        AgentInvocation(
            name="algorithmic_1",
            role=AgentRole.ALGORITHMIC,
            refs=common_refs,
        ),
        AgentInvocation(
            name="coder_1",
            role=AgentRole.CODING,
            refs=common_refs,
        ),
    ]
    if shape is not ProblemShape.DEBUGGING:
        step_one_agents.append(
            AgentInvocation(
                name="debugger_1",
                role=AgentRole.DEBUGGING,
                refs=common_refs,
            )
        )

    test_refs = tuple(
        AgentReference(step_index=1, agent_name=agent.name) for agent in step_one_agents
    )

    return TopologyPlan(
        difficulty=DifficultyLevel.HARD,
        steps=(
            TopologyStep(index=0, agents=tuple(step_zero_agents)),
            TopologyStep(index=1, agents=tuple(step_one_agents)),
            TopologyStep(
                index=2,
                agents=(
                    AgentInvocation(
                        name="tester_2",
                        role=AgentRole.TESTING,
                        refs=test_refs,
                    ),
                ),
            ),
        ),
    )
