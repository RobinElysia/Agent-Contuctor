"""Application services for the first stable callable API."""

from pathlib import Path

from agentconductor.application.bootstrap import bootstrap_overview
from agentconductor.application.execution import execute_topology
from agentconductor.application.history import (
    append_turn_result,
    build_revision_input,
    initialize_solve_state,
)
from agentconductor.application.orchestrator import (
    plan_topology_for_problem,
    plan_topology_with_policy,
    resolve_orchestrator_runtime,
    revise_topology_for_feedback,
    revise_topology_with_policy,
)
from agentconductor.domain.execution import TestingOutcome
from agentconductor.domain.orchestration import TopologyOrchestratorPolicy
from agentconductor.domain.models import (
    DifficultyLevel,
    ProblemInstance,
    SolveRequest,
    SolveResult,
    SolveStatus,
)


def solve_request(
    request: SolveRequest,
    *,
    orchestrator_policy: TopologyOrchestratorPolicy | None = None,
    orchestrator_checkpoint: str | Path | None = None,
    orchestrator_checkpoint_id: str | None = None,
    orchestrator_device: str = "cpu",
    orchestrator_max_attempts: int = 1,
) -> SolveResult:
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
    orchestrator_mode, resolved_policy, checkpoint_metadata = resolve_orchestrator_runtime(
        orchestrator_policy=orchestrator_policy,
        orchestrator_checkpoint=orchestrator_checkpoint,
        orchestrator_checkpoint_id=orchestrator_checkpoint_id,
        orchestrator_device=orchestrator_device,
    )
    if resolved_policy is None:
        topology = plan_topology_for_problem(problem)
    else:
        topology = plan_topology_with_policy(
            problem,
            policy=resolved_policy,
            max_attempts=orchestrator_max_attempts,
        ).topology
    execution = execute_topology(problem, topology)
    solve_state = append_turn_result(solve_state, topology=topology, execution=execution)

    while (
        execution.testing_outcome is not TestingOutcome.PASSED
        and solve_state.can_continue
    ):
        revision_input = build_revision_input(solve_state)
        if resolved_policy is None:
            topology = revise_topology_for_feedback(revision_input)
        else:
            topology = revise_topology_with_policy(
                revision_input,
                policy=resolved_policy,
                max_attempts=orchestrator_max_attempts,
            ).topology
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
            "This API performs bounded multi-turn execution over an explicit orchestrator boundary.",
            f"Topology planning mode: {orchestrator_mode.value}.",
            (
                "Checkpoint-backed frozen inference is not configured."
                if checkpoint_metadata is None
                else "Checkpoint-backed frozen inference uses "
                f"{checkpoint_metadata.checkpoint_id} on device "
                f"'{orchestrator_device}'."
            ),
            "Later turns consume typed testing feedback through a local revision-input contract.",
            "Testing outcomes now come from a repository-local Python subprocess judge adapter.",
        ),
    )
