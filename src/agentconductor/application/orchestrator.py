"""Deterministic rule-based topology planning."""

from __future__ import annotations

from enum import StrEnum

from agentconductor.domain.history import TopologyRevisionInput
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


def revise_topology_for_feedback(revision: TopologyRevisionInput) -> TopologyPlan:
    """Return a deterministic revised topology for a failed prior turn.

    Inference:
    The paper states that later turns consume prior feedback and history, but it
    does not define a concrete repository-local revision policy. This function
    implements an inspectable fallback policy that increases debugging focus and
    preserves explicit dependency on the prior testing diagnostics.
    """
    shape = infer_problem_shape(revision.problem)
    diagnostics = " ".join(revision.testing_feedback.diagnostics).lower()
    requires_retrieval = shape is ProblemShape.KNOWLEDGE_INTENSIVE or any(
        keyword in diagnostics
        for keyword in ("constraint", "graph", "path", "dp", "dynamic programming")
    )

    if revision.selected_difficulty is DifficultyLevel.EASY:
        return _easy_revision_topology(revision.turn_index)
    if revision.selected_difficulty is DifficultyLevel.HARD:
        return _hard_revision_topology(revision.turn_index, requires_retrieval)
    return _medium_revision_topology(revision.turn_index, requires_retrieval)


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


def _easy_revision_topology(turn_index: int) -> TopologyPlan:
    return TopologyPlan(
        difficulty=DifficultyLevel.EASY,
        steps=(
            TopologyStep(
                index=0,
                agents=(AgentInvocation(name=f"planner_t{turn_index}_0", role=AgentRole.PLANNING),),
            ),
            TopologyStep(
                index=1,
                agents=(
                    AgentInvocation(
                        name=f"coder_t{turn_index}_1",
                        role=AgentRole.CODING,
                        refs=(
                            AgentReference(step_index=0, agent_name=f"planner_t{turn_index}_0"),
                        ),
                    ),
                ),
            ),
            TopologyStep(
                index=2,
                agents=(
                    AgentInvocation(
                        name=f"debugger_t{turn_index}_2",
                        role=AgentRole.DEBUGGING,
                        refs=(
                            AgentReference(step_index=1, agent_name=f"coder_t{turn_index}_1"),
                        ),
                    ),
                ),
            ),
            TopologyStep(
                index=3,
                agents=(
                    AgentInvocation(
                        name=f"tester_t{turn_index}_3",
                        role=AgentRole.TESTING,
                        refs=(
                            AgentReference(step_index=0, agent_name=f"planner_t{turn_index}_0"),
                            AgentReference(step_index=2, agent_name=f"debugger_t{turn_index}_2"),
                        ),
                    ),
                ),
            ),
        ),
    )


def _medium_revision_topology(turn_index: int, requires_retrieval: bool) -> TopologyPlan:
    step_zero_agents = [AgentInvocation(name=f"planner_t{turn_index}_0", role=AgentRole.PLANNING)]
    if requires_retrieval:
        step_zero_agents.insert(
            0, AgentInvocation(name=f"retrieval_t{turn_index}_0", role=AgentRole.RETRIEVAL)
        )

    step_one_refs = [AgentReference(step_index=0, agent_name=f"planner_t{turn_index}_0")]
    if requires_retrieval:
        step_one_refs.insert(
            0, AgentReference(step_index=0, agent_name=f"retrieval_t{turn_index}_0")
        )

    return TopologyPlan(
        difficulty=DifficultyLevel.MEDIUM,
        steps=(
            TopologyStep(index=0, agents=tuple(step_zero_agents)),
            TopologyStep(
                index=1,
                agents=(
                    AgentInvocation(
                        name=f"algorithmic_t{turn_index}_1",
                        role=AgentRole.ALGORITHMIC,
                        refs=tuple(step_one_refs),
                    ),
                    AgentInvocation(
                        name=f"coder_t{turn_index}_1",
                        role=AgentRole.CODING,
                        refs=tuple(step_one_refs),
                    ),
                ),
            ),
            TopologyStep(
                index=2,
                agents=(
                    AgentInvocation(
                        name=f"debugger_t{turn_index}_2",
                        role=AgentRole.DEBUGGING,
                        refs=(
                            AgentReference(step_index=1, agent_name=f"algorithmic_t{turn_index}_1"),
                            AgentReference(step_index=1, agent_name=f"coder_t{turn_index}_1"),
                        ),
                    ),
                ),
            ),
            TopologyStep(
                index=3,
                agents=(
                    AgentInvocation(
                        name=f"tester_t{turn_index}_3",
                        role=AgentRole.TESTING,
                        refs=(
                            AgentReference(step_index=1, agent_name=f"coder_t{turn_index}_1"),
                            AgentReference(step_index=2, agent_name=f"debugger_t{turn_index}_2"),
                        ),
                    ),
                ),
            ),
        ),
    )


def _hard_revision_topology(turn_index: int, requires_retrieval: bool) -> TopologyPlan:
    step_zero_agents = [AgentInvocation(name=f"planner_t{turn_index}_0", role=AgentRole.PLANNING)]
    if requires_retrieval:
        step_zero_agents.insert(
            0, AgentInvocation(name=f"retrieval_t{turn_index}_0", role=AgentRole.RETRIEVAL)
        )

    step_zero_refs = tuple(
        AgentReference(step_index=0, agent_name=agent.name) for agent in step_zero_agents
    )

    return TopologyPlan(
        difficulty=DifficultyLevel.HARD,
        steps=(
            TopologyStep(index=0, agents=tuple(step_zero_agents)),
            TopologyStep(
                index=1,
                agents=(
                    AgentInvocation(
                        name=f"algorithmic_t{turn_index}_1",
                        role=AgentRole.ALGORITHMIC,
                        refs=step_zero_refs,
                    ),
                    AgentInvocation(
                        name=f"coder_t{turn_index}_1",
                        role=AgentRole.CODING,
                        refs=step_zero_refs,
                    ),
                ),
            ),
            TopologyStep(
                index=2,
                agents=(
                    AgentInvocation(
                        name=f"debugger_t{turn_index}_2",
                        role=AgentRole.DEBUGGING,
                        refs=(
                            AgentReference(step_index=1, agent_name=f"algorithmic_t{turn_index}_1"),
                            AgentReference(step_index=1, agent_name=f"coder_t{turn_index}_1"),
                        ),
                    ),
                ),
            ),
            TopologyStep(
                index=3,
                agents=(
                    AgentInvocation(
                        name=f"tester_t{turn_index}_3",
                        role=AgentRole.TESTING,
                        refs=(
                            AgentReference(step_index=1, agent_name=f"coder_t{turn_index}_1"),
                            AgentReference(step_index=2, agent_name=f"debugger_t{turn_index}_2"),
                        ),
                    ),
                ),
            ),
        ),
    )
