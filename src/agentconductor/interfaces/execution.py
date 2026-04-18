"""Public topology execution entrypoints."""

from agentconductor.application.execution import execute_topology
from agentconductor.domain.execution import TopologyExecutionResult
from agentconductor.domain.models import ProblemInstance
from agentconductor.domain.topology import TopologyPlan


def execute_topology_plan(
    problem: ProblemInstance,
    topology: TopologyPlan,
) -> TopologyExecutionResult:
    """Execute a validated single-turn topology plan."""
    return execute_topology(problem, topology)
