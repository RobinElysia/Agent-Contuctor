"""Application services for the first stable callable API."""

from agentconductor.application.bootstrap import bootstrap_overview
from agentconductor.application.execution import execute_topology
from agentconductor.application.history import append_turn_result, initialize_solve_state
from agentconductor.application.orchestrator import plan_topology_for_problem
from agentconductor.domain.execution import TestingOutcome
from agentconductor.domain.models import (
    DifficultyLevel,
    ProblemInstance,
    SolveRequest,
    SolveResult,
    SolveStatus,
)


def solve_request(request: SolveRequest) -> SolveResult:
    """Prepare and execute a typed single-turn solve request.

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
    problem = ProblemInstance(
        identifier=request.problem.identifier,
        prompt=request.problem.prompt,
        difficulty=selected_difficulty,
    )
    max_nodes = overview.max_nodes_by_difficulty[selected_difficulty]
    solve_state = initialize_solve_state(
        problem=problem,
        max_turns=planned_turns,
        max_nodes=max_nodes,
        available_roles=overview.supported_roles,
    )
    topology = plan_topology_for_problem(problem)
    execution = execute_topology(problem, topology)
    solve_state = append_turn_result(solve_state, topology=topology, execution=execution)
    status = (
        SolveStatus.COMPLETED
        if execution.testing_outcome is TestingOutcome.PASSED
        else SolveStatus.FAILED
    )

    return SolveResult(
        problem_id=request.problem.identifier,
        status=status,
        selected_difficulty=selected_difficulty,
        planned_turns=planned_turns,
        max_nodes=max_nodes,
        available_roles=overview.supported_roles,
        topology=topology,
        execution=execution,
        candidate_solution=execution.final_candidate_code,
        testing_outcome=execution.testing_outcome,
        solve_state=solve_state,
        notes=(
            "This API performs deterministic topology planning plus single-turn execution.",
            "A typed solve-state contract now preserves turn history for later revision logic.",
            "Testing outcomes remain repository-local heuristics until sandbox integration exists.",
        ),
    )
