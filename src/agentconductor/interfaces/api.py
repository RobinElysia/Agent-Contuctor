"""Public Python API entrypoints for external callers.

External callers should treat ``solve_problem`` as the stable entrypoint for
problem-oriented execution requests during the current milestone.
"""

from agentconductor.application.api import solve_request
from agentconductor.application.bootstrap import bootstrap_overview
from agentconductor.domain.models import ProblemInstance, SolveRequest, SolveResult


def solve_problem(problem: ProblemInstance, *, max_turns: int | None = None) -> SolveResult:
    """Return a structured solve plan for a problem instance."""
    return solve_request(SolveRequest(problem=problem, max_turns=max_turns))
