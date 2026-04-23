"""Typed contracts for learned-orchestrator planning boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from agentconductor.domain.models import DifficultyLevel, ProblemInstance

if TYPE_CHECKING:
    from agentconductor.domain.history import TestingFeedback
    from agentconductor.domain.topology import TopologyPlan


class OrchestratorMode(StrEnum):
    """Planning path used to produce a topology."""

    DETERMINISTIC = "deterministic"
    LEARNED = "learned"


class TopologyPromptKind(StrEnum):
    """High-level prompt purpose for topology generation."""

    INITIAL = "initial"
    REVISION = "revision"


@dataclass(frozen=True, slots=True)
class OrchestratorPromptRequest:
    """Structured inputs for one learned-orchestrator prompt."""

    kind: TopologyPromptKind
    problem: ProblemInstance
    selected_difficulty: DifficultyLevel
    turn_index: int
    prior_topology: TopologyPlan | None = None
    testing_feedback: TestingFeedback | None = None
    remaining_turns: int | None = None
    last_error: str | None = None


@dataclass(frozen=True, slots=True)
class LearnedTopologyPlan:
    """Parsed learned-policy candidate plus the raw YAML transport."""

    topology: TopologyPlan
    topology_yaml: str
    prompt: str
    raw_response: str
    attempt_count: int
    kind: TopologyPromptKind


class OrchestratorPolicyError(RuntimeError):
    """Base class for repository-local learned-policy boundary failures."""


class TopologyCandidateExtractionError(OrchestratorPolicyError):
    """Raised when a policy response does not contain an extractable YAML plan."""


class OrchestratorCheckpointError(RuntimeError):
    """Base class for checkpoint-backed orchestrator configuration failures."""


class OrchestratorCheckpointSelectionError(OrchestratorCheckpointError):
    """Raised when a checkpoint source cannot be resolved unambiguously."""


class OrchestratorCheckpointLoadError(OrchestratorCheckpointError):
    """Raised when a resolved checkpoint cannot support frozen inference."""


@runtime_checkable
class TopologyOrchestratorPolicy(Protocol):
    """Minimal policy contract for frozen-orchestrator planning."""

    def generate_topology_candidate(
        self,
        *,
        prompt: str,
        request: OrchestratorPromptRequest,
    ) -> str:
        """Return one raw model response containing a topology YAML candidate."""
