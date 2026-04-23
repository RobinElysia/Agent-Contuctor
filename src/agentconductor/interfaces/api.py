"""Public Python API entrypoints for external callers.

External callers should treat ``solve_problem`` as the stable entrypoint for
problem-oriented execution requests during the current milestone.
"""

from pathlib import Path

from agentconductor.application.api import solve_request
from agentconductor.application.bootstrap import bootstrap_overview
from agentconductor.domain.history import TopologyRevisionInput
from agentconductor.domain.orchestration import LearnedTopologyPlan, TopologyOrchestratorPolicy
from agentconductor.domain.models import ProblemInstance, SolveRequest, SolveResult
from agentconductor.domain.topology import TopologyPlan
from agentconductor.infrastructure.topology_yaml import (
    dump_topology_yaml_mapping,
    parse_topology_plan_yaml as parse_topology_plan_yaml_text,
)
from agentconductor.interfaces.planning import (
    plan_topology,
    plan_topology_candidate,
    revise_topology_candidate,
)


def solve_problem(
    problem: ProblemInstance,
    *,
    max_turns: int | None = None,
    orchestrator_policy: TopologyOrchestratorPolicy | None = None,
    orchestrator_checkpoint: str | Path | None = None,
    orchestrator_checkpoint_id: str | None = None,
    orchestrator_device: str = "cpu",
    orchestrator_max_attempts: int = 1,
) -> SolveResult:
    """Return a structured solve result for a problem instance."""
    return solve_request(
        SolveRequest(problem=problem, max_turns=max_turns),
        orchestrator_policy=orchestrator_policy,
        orchestrator_checkpoint=orchestrator_checkpoint,
        orchestrator_checkpoint_id=orchestrator_checkpoint_id,
        orchestrator_device=orchestrator_device,
        orchestrator_max_attempts=orchestrator_max_attempts,
    )


def plan_problem_topology(
    problem: ProblemInstance,
    *,
    orchestrator_policy: TopologyOrchestratorPolicy | None = None,
    orchestrator_checkpoint: str | Path | None = None,
    orchestrator_checkpoint_id: str | None = None,
    orchestrator_device: str = "cpu",
    orchestrator_max_attempts: int = 1,
) -> TopologyPlan:
    """Return a validated topology plan for a problem instance."""
    return plan_topology(
        problem,
        orchestrator_policy=orchestrator_policy,
        orchestrator_checkpoint=orchestrator_checkpoint,
        orchestrator_checkpoint_id=orchestrator_checkpoint_id,
        orchestrator_device=orchestrator_device,
        orchestrator_max_attempts=orchestrator_max_attempts,
    )


def plan_problem_topology_candidate(
    problem: ProblemInstance,
    *,
    orchestrator_policy: TopologyOrchestratorPolicy | None = None,
    orchestrator_checkpoint: str | Path | None = None,
    orchestrator_checkpoint_id: str | None = None,
    orchestrator_device: str = "cpu",
    orchestrator_max_attempts: int = 1,
) -> LearnedTopologyPlan:
    """Return the learned-policy YAML candidate plus the parsed topology."""
    return plan_topology_candidate(
        problem,
        orchestrator_policy=orchestrator_policy,
        orchestrator_checkpoint=orchestrator_checkpoint,
        orchestrator_checkpoint_id=orchestrator_checkpoint_id,
        orchestrator_device=orchestrator_device,
        orchestrator_max_attempts=orchestrator_max_attempts,
    )


def revise_problem_topology_candidate(
    revision: TopologyRevisionInput,
    *,
    orchestrator_policy: TopologyOrchestratorPolicy | None = None,
    orchestrator_checkpoint: str | Path | None = None,
    orchestrator_checkpoint_id: str | None = None,
    orchestrator_device: str = "cpu",
    orchestrator_max_attempts: int = 1,
) -> LearnedTopologyPlan:
    """Return the learned-policy revised YAML candidate plus the parsed topology."""
    return revise_topology_candidate(
        revision,
        orchestrator_policy=orchestrator_policy,
        orchestrator_checkpoint=orchestrator_checkpoint,
        orchestrator_checkpoint_id=orchestrator_checkpoint_id,
        orchestrator_device=orchestrator_device,
        orchestrator_max_attempts=orchestrator_max_attempts,
    )


def serialize_topology_plan_to_yaml(topology: TopologyPlan) -> str:
    """Serialize a validated topology plan into repository YAML text."""
    topology.validate()
    return dump_topology_yaml_mapping(topology.to_mapping())


def parse_topology_plan_yaml(yaml_text: str) -> TopologyPlan:
    """Parse repository YAML text into a validated typed topology plan."""
    return parse_topology_plan_yaml_text(yaml_text)
