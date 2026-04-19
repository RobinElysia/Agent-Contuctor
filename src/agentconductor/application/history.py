"""Solve-state construction and transition helpers."""

from __future__ import annotations

from dataclasses import replace

from agentconductor.domain.execution import TestingOutcome, TopologyExecutionResult
from agentconductor.domain.history import (
    SolveState,
    SolveStateTransitionError,
    SolveTurnRecord,
    StopReason,
    TestingFeedback,
    TopologyRevisionInput,
)
from agentconductor.domain.models import ProblemInstance
from agentconductor.domain.topology import TopologyPlan


def initialize_solve_state(
    *,
    problem: ProblemInstance,
    max_turns: int,
    max_nodes: int,
    available_roles: tuple[str, ...],
) -> SolveState:
    """Create an empty solve state for a normalized problem."""
    if problem.difficulty is None:
        raise SolveStateTransitionError(
            "problem difficulty must be explicit before initializing solve state"
        )
    if max_turns < 1:
        raise SolveStateTransitionError("max_turns must be at least 1")
    if max_nodes < 1:
        raise SolveStateTransitionError("max_nodes must be at least 1")
    return SolveState(
        problem=problem,
        selected_difficulty=problem.difficulty,
        max_turns=max_turns,
        max_nodes=max_nodes,
        available_roles=available_roles,
    )


def append_turn_result(
    state: SolveState,
    *,
    topology: TopologyPlan,
    execution: TopologyExecutionResult,
) -> SolveState:
    """Append one completed turn to a solve state."""
    if state.stop_reason is not None:
        raise SolveStateTransitionError("cannot append a turn to a terminal solve state")
    if state.remaining_turns < 1:
        raise SolveStateTransitionError("cannot append a turn beyond the solve turn budget")
    if topology.difficulty is not state.selected_difficulty:
        raise SolveStateTransitionError(
            "turn topology difficulty must match the solve state's selected difficulty"
        )
    if execution.problem.identifier != state.problem.identifier:
        raise SolveStateTransitionError(
            "execution result problem id must match the solve state's problem id"
        )
    if execution.difficulty is not state.selected_difficulty:
        raise SolveStateTransitionError(
            "execution result difficulty must match the solve state's selected difficulty"
        )

    turn_record = SolveTurnRecord(
        turn_index=state.completed_turns,
        topology=topology,
        execution=execution,
        testing_feedback=TestingFeedback(
            outcome=execution.testing_outcome,
            diagnostics=execution.diagnostics,
            candidate_code=execution.final_candidate_code,
        ),
    )
    turns = state.turns + (turn_record,)

    stop_reason = None
    if execution.testing_outcome is TestingOutcome.PASSED:
        stop_reason = StopReason.SOLVED
    elif len(turns) >= state.max_turns:
        stop_reason = StopReason.TURN_BUDGET_EXHAUSTED

    return replace(state, turns=turns, stop_reason=stop_reason)


def build_revision_input(state: SolveState) -> TopologyRevisionInput:
    """Build the explicit revision input for the next turn.

    Inference:
    The paper describes feeding prior feedback and history back into the
    orchestrator, but not a concrete software contract. This repository exposes
    a typed revision-input object so `TURN-02` can consume prior-turn artifacts
    without re-deriving them from free-form text.
    """
    if state.completed_turns < 1:
        raise SolveStateTransitionError(
            "cannot build revision input before the first turn exists"
        )
    if not state.can_continue:
        raise SolveStateTransitionError(
            "cannot build revision input from a terminal or exhausted solve state"
        )

    latest_turn = state.latest_turn
    if latest_turn is None:
        raise SolveStateTransitionError("latest turn is unavailable")

    return TopologyRevisionInput(
        problem=state.problem,
        selected_difficulty=state.selected_difficulty,
        turn_index=latest_turn.turn_index + 1,
        prior_topology=latest_turn.topology,
        prior_execution_status=latest_turn.execution.status,
        testing_feedback=latest_turn.testing_feedback,
        remaining_turns=state.remaining_turns,
    )
