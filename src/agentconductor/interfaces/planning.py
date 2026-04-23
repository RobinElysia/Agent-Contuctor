"""Public topology planning entrypoints."""

from pathlib import Path

from agentconductor.application.orchestrator import (
    plan_topology_for_problem,
    plan_topology_with_policy,
    resolve_orchestrator_runtime,
    revise_topology_with_policy,
)
from agentconductor.domain.history import TopologyRevisionInput
from agentconductor.domain.orchestration import LearnedTopologyPlan, TopologyOrchestratorPolicy
from agentconductor.domain.models import ProblemInstance
from agentconductor.domain.topology import TopologyPlan


def plan_topology(
    problem: ProblemInstance,
    *,
    orchestrator_policy: TopologyOrchestratorPolicy | None = None,
    orchestrator_checkpoint: str | Path | None = None,
    orchestrator_checkpoint_id: str | None = None,
    orchestrator_device: str = "cpu",
    orchestrator_max_attempts: int = 1,
) -> TopologyPlan:
    """Return a validated topology plan for a problem."""
    _, resolved_policy, _ = resolve_orchestrator_runtime(
        orchestrator_policy=orchestrator_policy,
        orchestrator_checkpoint=orchestrator_checkpoint,
        orchestrator_checkpoint_id=orchestrator_checkpoint_id,
        orchestrator_device=orchestrator_device,
    )
    if resolved_policy is None:
        plan = plan_topology_for_problem(problem)
    else:
        plan = plan_topology_with_policy(
            problem,
            policy=resolved_policy,
            max_attempts=orchestrator_max_attempts,
        ).topology
    plan.validate()
    return plan


def plan_topology_candidate(
    problem: ProblemInstance,
    *,
    orchestrator_policy: TopologyOrchestratorPolicy | None = None,
    orchestrator_checkpoint: str | Path | None = None,
    orchestrator_checkpoint_id: str | None = None,
    orchestrator_device: str = "cpu",
    orchestrator_max_attempts: int = 1,
) -> LearnedTopologyPlan:
    """Return the learned-policy YAML candidate and parsed topology."""
    _, resolved_policy, _ = resolve_orchestrator_runtime(
        orchestrator_policy=orchestrator_policy,
        orchestrator_checkpoint=orchestrator_checkpoint,
        orchestrator_checkpoint_id=orchestrator_checkpoint_id,
        orchestrator_device=orchestrator_device,
    )
    if resolved_policy is None:
        raise ValueError(
            "plan_topology_candidate requires orchestrator_policy or orchestrator_checkpoint"
        )
    return plan_topology_with_policy(
        problem,
        policy=resolved_policy,
        max_attempts=orchestrator_max_attempts,
    )


def revise_topology_candidate(
    revision: TopologyRevisionInput,
    *,
    orchestrator_policy: TopologyOrchestratorPolicy | None = None,
    orchestrator_checkpoint: str | Path | None = None,
    orchestrator_checkpoint_id: str | None = None,
    orchestrator_device: str = "cpu",
    orchestrator_max_attempts: int = 1,
) -> LearnedTopologyPlan:
    """Return the learned-policy revised YAML candidate and parsed topology."""
    _, resolved_policy, _ = resolve_orchestrator_runtime(
        orchestrator_policy=orchestrator_policy,
        orchestrator_checkpoint=orchestrator_checkpoint,
        orchestrator_checkpoint_id=orchestrator_checkpoint_id,
        orchestrator_device=orchestrator_device,
    )
    if resolved_policy is None:
        raise ValueError(
            "revise_topology_candidate requires orchestrator_policy or orchestrator_checkpoint"
        )
    return revise_topology_with_policy(
        revision,
        policy=resolved_policy,
        max_attempts=orchestrator_max_attempts,
    )
