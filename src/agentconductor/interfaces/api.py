"""Public Python API entrypoints for external callers.

External callers should treat ``solve_problem`` as the stable entrypoint for
problem-oriented execution requests during the current milestone.
"""

from agentconductor.application.api import solve_request
from agentconductor.application.bootstrap import bootstrap_overview
from agentconductor.domain.models import ProblemInstance, SolveRequest, SolveResult
from agentconductor.domain.topology import TopologyPlan
from agentconductor.interfaces.planning import plan_topology


def solve_problem(problem: ProblemInstance, *, max_turns: int | None = None) -> SolveResult:
    """Return a structured solve result for a problem instance."""
    return solve_request(SolveRequest(problem=problem, max_turns=max_turns))


def plan_problem_topology(problem: ProblemInstance) -> TopologyPlan:
    """Return a deterministic topology plan for a problem instance."""
    return plan_topology(problem)
