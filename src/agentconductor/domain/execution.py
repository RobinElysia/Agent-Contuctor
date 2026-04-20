"""Typed execution contracts for topology runs and judge-backed evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol

from agentconductor.domain.models import DifficultyLevel, ProblemInstance
from agentconductor.domain.topology import AgentReference, AgentRole


class ExecutionStatus(StrEnum):
    """High-level status of a topology execution attempt."""

    COMPLETED = "completed"
    FAILED = "failed"


class TestingOutcome(StrEnum):
    """Outcome categories reported by the testing role.

    The paper enumerates pass/fail categories such as wrong answer, runtime
    error, compilation error, and resource-limit failures. This repository
    keeps those categories and also preserves narrow local fallbacks for
    missing code and pre-sandbox failures.
    """

    PASSED = "passed"
    FAILED = "failed"
    WRONG_ANSWER = "wrong_answer"
    TIME_LIMIT_EXCEEDED = "time_limit_exceeded"
    MEMORY_LIMIT_EXCEEDED = "memory_limit_exceeded"
    RUNTIME_ERROR = "runtime_error"
    COMPILATION_ERROR = "compilation_error"
    NO_CANDIDATE = "no_candidate"


TestingOutcome.__test__ = False


@dataclass(frozen=True, slots=True)
class JudgeCaseResult:
    """Structured verdict for one executed judge case."""

    name: str
    outcome: TestingOutcome
    diagnostics: tuple[str, ...] = ()
    actual_output: Any | None = None
    expected_output: Any | None = None
    actual_stdout: str | None = None
    expected_stdout: str | None = None


@dataclass(frozen=True, slots=True)
class CodeCandidate:
    """Extracted candidate code passed into a judge adapter."""

    step_index: int
    agent_name: str
    role: AgentRole
    source_code: str
    language: str = "python"


@dataclass(frozen=True, slots=True)
class JudgeTestCase:
    """Single judge test case for one candidate invocation."""

    name: str
    arguments: tuple[Any, ...] = ()
    keyword_arguments: tuple[tuple[str, Any], ...] = ()
    stdin_text: str | None = None
    expected_output: Any = None
    expected_stdout: str | None = None


@dataclass(frozen=True, slots=True)
class JudgeResourceLimits:
    """Soft resource limits attached to a judge evaluation request."""

    cpu_time_seconds: float = 1.0
    memory_limit_bytes: int | None = None


@dataclass(frozen=True, slots=True)
class SandboxTestSpec:
    """Judge-oriented executable spec for a candidate solution."""

    entrypoint: str
    test_cases: tuple[JudgeTestCase, ...] = ()
    resource_limits: JudgeResourceLimits = field(default_factory=JudgeResourceLimits)


@dataclass(frozen=True, slots=True)
class SandboxExecutionResult:
    """Structured outcome returned by a sandbox or judge adapter."""

    outcome: TestingOutcome
    diagnostics: tuple[str, ...]
    case_results: tuple[JudgeCaseResult, ...] = ()
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None


class SandboxAdapter(Protocol):
    """Narrow boundary for runtime-specific candidate evaluation."""

    def evaluate(
        self,
        problem: ProblemInstance,
        candidate: CodeCandidate,
        spec: SandboxTestSpec,
    ) -> SandboxExecutionResult:
        """Run judge-backed evaluation for one code candidate."""


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
    sandbox_result: SandboxExecutionResult | None = None


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
    sandbox_result: SandboxExecutionResult | None = None

    @property
    def executed_steps(self) -> int:
        return len(self.step_results)

    @property
    def executed_agents(self) -> int:
        return sum(len(step.agent_results) for step in self.step_results)


class TopologyExecutionError(ValueError):
    """Raised when a topology cannot be executed under the current runtime."""
