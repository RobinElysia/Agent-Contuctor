"""Public topology planning entrypoints."""

from agentconductor.application.orchestrator import plan_topology_for_problem
from agentconductor.domain.models import ProblemInstance
from agentconductor.domain.topology import TopologyPlan


def plan_topology(problem: ProblemInstance) -> TopologyPlan:
    """Return a deterministic validated topology plan for a problem."""
    plan = plan_topology_for_problem(problem)
    plan.validate()
    return plan
