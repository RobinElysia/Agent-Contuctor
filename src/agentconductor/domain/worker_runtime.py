"""Typed worker-model runtime contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from agentconductor.domain.execution import ResolvedAgentOutput
    from agentconductor.domain.models import ProblemInstance
    from agentconductor.domain.topology import AgentInvocation, AgentRole


@dataclass(frozen=True, slots=True)
class WorkerGenerationRequest:
    """Prompt-bound request for one non-testing worker role."""

    problem: ProblemInstance
    agent: AgentInvocation
    step_index: int
    consumed_outputs: tuple[ResolvedAgentOutput, ...]
    prompt: str


@dataclass(frozen=True, slots=True)
class WorkerGenerationResult:
    """Structured response from a worker-model runtime."""

    summary: str
    candidate_code: str | None = None
    diagnostics: tuple[str, ...] = ()
    runtime_name: str = "unknown"
    model_name: str = "unknown"


class WorkerRuntimeError(RuntimeError):
    """Raised when a worker-model runtime cannot serve a role request."""


class WorkerRoleRuntime(Protocol):
    """Narrow adapter contract for model-backed worker execution."""

    def generate_role_output(
        self,
        request: WorkerGenerationRequest,
    ) -> WorkerGenerationResult:
        """Return one structured role output for the provided prompt."""

    def supports_role(self, role: AgentRole) -> bool:
        """Return whether the runtime can serve the requested role."""
