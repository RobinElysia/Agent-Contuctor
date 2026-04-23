"""Public topology planning entrypoints."""

from agentconductor.application.orchestrator import (
    plan_topology_for_problem,
    plan_topology_with_policy,
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
    orchestrator_max_attempts: int = 1,
) -> TopologyPlan:
    """Return a validated topology plan for a problem."""
    if orchestrator_policy is None:
        plan = plan_topology_for_problem(problem)
    else:
        plan = plan_topology_with_policy(
            problem,
            policy=orchestrator_policy,
            max_attempts=orchestrator_max_attempts,
        ).topology
    plan.validate()
    return plan


def plan_topology_candidate(
    problem: ProblemInstance,
    *,
    orchestrator_policy: TopologyOrchestratorPolicy,
    orchestrator_max_attempts: int = 1,
) -> LearnedTopologyPlan:
    """Return the learned-policy YAML candidate and parsed topology."""
    return plan_topology_with_policy(
        problem,
        policy=orchestrator_policy,
        max_attempts=orchestrator_max_attempts,
    )


def revise_topology_candidate(
    revision: TopologyRevisionInput,
    *,
    orchestrator_policy: TopologyOrchestratorPolicy,
    orchestrator_max_attempts: int = 1,
) -> LearnedTopologyPlan:
    """Return the learned-policy revised YAML candidate and parsed topology."""
    return revise_topology_with_policy(
        revision,
        policy=orchestrator_policy,
        max_attempts=orchestrator_max_attempts,
    )
