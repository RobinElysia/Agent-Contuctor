"""Application services for the first stable callable API."""

from agentconductor.application.bootstrap import bootstrap_overview
from agentconductor.domain.models import (
    DifficultyLevel,
    SolveRequest,
    SolveResult,
    SolveStatus,
)


def solve_request(request: SolveRequest) -> SolveResult:
    """Prepare a typed solve plan for external callers.

    Inference:
    Until the repository implements the paper's difficulty inference logic,
    missing difficulty values default to ``medium``.
    """
    overview = bootstrap_overview()
    planned_turns = request.max_turns or overview.max_interaction_turns
    if planned_turns < 1:
        raise ValueError("max_turns must be at least 1")
    if planned_turns > overview.max_interaction_turns:
        raise ValueError(
            f"max_turns must be <= {overview.max_interaction_turns} for the current baseline"
        )

    selected_difficulty = request.problem.difficulty or DifficultyLevel.MEDIUM

    return SolveResult(
        problem_id=request.problem.identifier,
        status=SolveStatus.PLANNED,
        selected_difficulty=selected_difficulty,
        planned_turns=planned_turns,
        max_nodes=overview.max_nodes_by_difficulty[selected_difficulty],
        available_roles=overview.supported_roles,
        notes=(
            "This API currently prepares a paper-aligned solve plan.",
            "Topology generation and execution remain future implementation work.",
        ),
    )
