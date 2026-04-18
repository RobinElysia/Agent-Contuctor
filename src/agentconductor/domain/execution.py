"""Typed execution contracts for single-turn topology runs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from agentconductor.domain.models import DifficultyLevel, ProblemInstance
from agentconductor.domain.topology import AgentReference, AgentRole


class ExecutionStatus(StrEnum):
    """High-level status of a topology execution attempt."""

    COMPLETED = "completed"
    FAILED = "failed"


class TestingOutcome(StrEnum):
    """Outcome reported by the deterministic testing role."""

    PASSED = "passed"
    FAILED = "failed"


TestingOutcome.__test__ = False


@dataclass(frozen=True, slots=True)
class ResolvedAgentOutput:
    """Structured view of an upstream agent result used as an input."""

    step_index: int
    agent_name: str
    role: AgentRole
    summary: str
    candidate_code: str | None = None


@dataclass(frozen=True, slots=True)
class AgentExecutionResult:
    """Structured output produced by a single agent execution."""

    step_index: int
    agent_name: str
    role: AgentRole
    summary: str
    references: tuple[AgentReference, ...]
    consumed_outputs: tuple[ResolvedAgentOutput, ...] = ()
    candidate_code: str | None = None
    diagnostics: tuple[str, ...] = ()
    testing_outcome: TestingOutcome | None = None


@dataclass(frozen=True, slots=True)
class StepExecutionResult:
    """Structured outputs produced by one topology layer."""

    step_index: int
    agent_results: tuple[AgentExecutionResult, ...]


@dataclass(frozen=True, slots=True)
class TopologyExecutionResult:
    """End-to-end execution result for a validated single-turn topology."""

    problem: ProblemInstance
    difficulty: DifficultyLevel
    status: ExecutionStatus
    step_results: tuple[StepExecutionResult, ...]
    final_candidate_code: str | None
    testing_outcome: TestingOutcome | None
    diagnostics: tuple[str, ...]

    @property
    def executed_steps(self) -> int:
        return len(self.step_results)

    @property
    def executed_agents(self) -> int:
        return sum(len(step.agent_results) for step in self.step_results)


class TopologyExecutionError(ValueError):
    """Raised when a topology cannot be executed under the current runtime."""
