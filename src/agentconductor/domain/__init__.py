"""Domain models for AgentConductor."""

from agentconductor.domain.execution import (
    AgentExecutionResult,
    CodeCandidate,
    ExecutionStatus,
    ResolvedAgentOutput,
    SandboxAdapter,
    SandboxExecutionResult,
    SandboxTestSpec,
    StepExecutionResult,
    TestingOutcome,
    TopologyExecutionError,
    TopologyExecutionResult,
)
from agentconductor.domain.history import (
    SolveState,
    SolveStateTransitionError,
    SolveTurnRecord,
    StopReason,
    TestingFeedback,
    TopologyRevisionInput,
)
from agentconductor.domain.topology import (
    AgentInvocation,
    AgentReference,
    AgentRole,
    TopologyPlan,
    TopologyStep,
    TopologyValidationError,
)

__all__ = [
    "AgentExecutionResult",
    "AgentInvocation",
    "AgentReference",
    "AgentRole",
    "CodeCandidate",
    "ExecutionStatus",
    "ResolvedAgentOutput",
    "SandboxAdapter",
    "SandboxExecutionResult",
    "SandboxTestSpec",
    "SolveState",
    "SolveStateTransitionError",
    "SolveTurnRecord",
    "StepExecutionResult",
    "StopReason",
    "TestingOutcome",
    "TestingFeedback",
    "TopologyPlan",
    "TopologyExecutionError",
    "TopologyExecutionResult",
    "TopologyRevisionInput",
    "TopologyStep",
    "TopologyValidationError",
]
