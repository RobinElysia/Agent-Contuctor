"""Typed domain models derived from the paper distillation."""

from dataclasses import dataclass
from enum import StrEnum


class DifficultyLevel(StrEnum):
    """Difficulty tiers used by the paper's topology budget."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass(frozen=True, slots=True)
class ProblemInstance:
    """Minimal task contract for future orchestration entrypoints."""

    identifier: str
    prompt: str
    difficulty: DifficultyLevel | None = None


@dataclass(frozen=True, slots=True)
class ProjectOverview:
    """Stable package-level summary for bootstrap verification."""

    package_name: str
    supported_roles: tuple[str, ...]
    max_nodes_by_difficulty: dict[DifficultyLevel, int]
    max_interaction_turns: int


class SolveStatus(StrEnum):
    """Current high-level state of an API solve attempt."""

    PLANNED = "planned"


@dataclass(frozen=True, slots=True)
class SolveRequest:
    """Typed input for the first stable callable API boundary."""

    problem: ProblemInstance
    max_turns: int | None = None


@dataclass(frozen=True, slots=True)
class SolveResult:
    """Structured output returned by the package API."""

    problem_id: str
    status: SolveStatus
    selected_difficulty: DifficultyLevel
    planned_turns: int
    max_nodes: int
    available_roles: tuple[str, ...]
    notes: tuple[str, ...]
