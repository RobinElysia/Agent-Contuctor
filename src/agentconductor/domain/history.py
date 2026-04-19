"""Typed multi-turn solve-state contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from agentconductor.domain.execution import ExecutionStatus, TestingOutcome, TopologyExecutionResult
from agentconductor.domain.models import DifficultyLevel, ProblemInstance
from agentconductor.domain.topology import TopologyPlan


class StopReason(StrEnum):
    """Terminal conditions for a solve-state lifecycle."""

    SOLVED = "solved"
    TURN_BUDGET_EXHAUSTED = "turn_budget_exhausted"


@dataclass(frozen=True, slots=True)
class TestingFeedback:
    """Structured testing feedback carried across turns.

    Inference:
    The paper describes testing outcomes and diagnostics but does not define a
    standalone serialized feedback object. This repository uses a narrow typed
    contract so later topology revision does not pass raw strings only.
    """

    outcome: TestingOutcome | None
    diagnostics: tuple[str, ...]
    candidate_code: str | None


TestingFeedback.__test__ = False


@dataclass(frozen=True, slots=True)
class SolveTurnRecord:
    """One completed solve turn and its revision-relevant artifacts."""

    turn_index: int
    topology: TopologyPlan
    execution: TopologyExecutionResult
    testing_feedback: TestingFeedback


@dataclass(frozen=True, slots=True)
class TopologyRevisionInput:
    """Explicit input for a later-turn topology revision step."""

    problem: ProblemInstance
    selected_difficulty: DifficultyLevel
    turn_index: int
    prior_topology: TopologyPlan
    prior_execution_status: ExecutionStatus
    testing_feedback: TestingFeedback
    remaining_turns: int


@dataclass(frozen=True, slots=True)
class SolveState:
    """Typed multi-turn solve state compatible with the current executor."""

    problem: ProblemInstance
    selected_difficulty: DifficultyLevel
    max_turns: int
    max_nodes: int
    available_roles: tuple[str, ...]
    turns: tuple[SolveTurnRecord, ...] = ()
    stop_reason: StopReason | None = None

    @property
    def completed_turns(self) -> int:
        return len(self.turns)

    @property
    def remaining_turns(self) -> int:
        return max(self.max_turns - self.completed_turns, 0)

    @property
    def can_continue(self) -> bool:
        return self.stop_reason is None and self.remaining_turns > 0

    @property
    def latest_turn(self) -> SolveTurnRecord | None:
        if not self.turns:
            return None
        return self.turns[-1]


class SolveStateTransitionError(ValueError):
    """Raised when a solve-state transition violates repository contracts."""
