"""Single-turn execution for validated topology plans."""

from __future__ import annotations

from collections.abc import Callable

from agentconductor.domain.execution import (
    AgentExecutionResult,
    ExecutionStatus,
    ResolvedAgentOutput,
    StepExecutionResult,
    TestingOutcome,
    TopologyExecutionError,
    TopologyExecutionResult,
)
from agentconductor.domain.models import ProblemInstance
from agentconductor.domain.topology import AgentInvocation, AgentReference, AgentRole, TopologyPlan

RoleHandler = Callable[
    [ProblemInstance, AgentInvocation, int, tuple[ResolvedAgentOutput, ...]],
    AgentExecutionResult,
]


def execute_topology(
    problem: ProblemInstance,
    topology: TopologyPlan,
    *,
    registry: dict[AgentRole, RoleHandler] | None = None,
) -> TopologyExecutionResult:
    """Execute a single-turn topology plan layer by layer."""
    topology.validate()
    active_registry = registry or build_default_role_registry()

    results_by_agent: dict[tuple[int, str], AgentExecutionResult] = {}
    step_results: list[StepExecutionResult] = []

    for step in topology.steps:
        agent_results: list[AgentExecutionResult] = []
        for agent in step.agents:
            handler = active_registry.get(agent.role)
            if handler is None:
                raise TopologyExecutionError(
                    f"no role handler registered for role '{agent.role.value}'"
                )

            consumed_outputs = _resolve_references(agent.refs, results_by_agent)
            result = handler(problem, agent, step.index, consumed_outputs)
            agent_results.append(result)
            results_by_agent[(step.index, agent.name)] = result

        step_results.append(
            StepExecutionResult(step_index=step.index, agent_results=tuple(agent_results))
        )

    all_results = tuple(
        result for step_result in step_results for result in step_result.agent_results
    )
    final_candidate_code = _select_final_candidate_code(all_results)
    final_testing_result = _select_final_testing_result(all_results)

    diagnostics = final_testing_result.diagnostics if final_testing_result else ()
    testing_outcome = (
        final_testing_result.testing_outcome if final_testing_result else None
    )

    return TopologyExecutionResult(
        problem=problem,
        difficulty=topology.difficulty,
        status=ExecutionStatus.COMPLETED,
        step_results=tuple(step_results),
        final_candidate_code=final_candidate_code,
        testing_outcome=testing_outcome,
        diagnostics=diagnostics,
    )


def build_default_role_registry() -> dict[AgentRole, RoleHandler]:
    """Return the deterministic role registry used by the initial executor."""
    return {
        AgentRole.RETRIEVAL: _run_retrieval_role,
        AgentRole.PLANNING: _run_planning_role,
        AgentRole.ALGORITHMIC: _run_algorithmic_role,
        AgentRole.CODING: _run_coding_role,
        AgentRole.DEBUGGING: _run_debugging_role,
        AgentRole.TESTING: _run_testing_role,
    }


def _resolve_references(
    refs: tuple[AgentReference, ...],
    results_by_agent: dict[tuple[int, str], AgentExecutionResult],
) -> tuple[ResolvedAgentOutput, ...]:
    resolved: list[ResolvedAgentOutput] = []
    for ref in refs:
        upstream = results_by_agent.get((ref.step_index, ref.agent_name))
        if upstream is None:
            raise TopologyExecutionError(
                f"could not resolve reference to step {ref.step_index} agent "
                f"'{ref.agent_name}' during execution"
            )
        resolved.append(
            ResolvedAgentOutput(
                step_index=upstream.step_index,
                agent_name=upstream.agent_name,
                role=upstream.role,
                summary=upstream.summary,
                candidate_code=upstream.candidate_code,
            )
        )
    return tuple(resolved)


def _select_final_candidate_code(
    results: tuple[AgentExecutionResult, ...],
) -> str | None:
    for result in reversed(results):
        if result.candidate_code:
            return result.candidate_code
    return None


def _select_final_testing_result(
    results: tuple[AgentExecutionResult, ...],
) -> AgentExecutionResult | None:
    for result in reversed(results):
        if result.role is AgentRole.TESTING:
            return result
    return None


def _run_retrieval_role(
    problem: ProblemInstance,
    agent: AgentInvocation,
    step_index: int,
    consumed_outputs: tuple[ResolvedAgentOutput, ...],
) -> AgentExecutionResult:
    del consumed_outputs
    focus = _extract_focus(problem.prompt)
    summary = f"Retrieved deterministic context focused on {focus}."
    return AgentExecutionResult(
        step_index=step_index,
        agent_name=agent.name,
        role=agent.role,
        summary=summary,
        references=agent.refs,
    )


def _run_planning_role(
    problem: ProblemInstance,
    agent: AgentInvocation,
    step_index: int,
    consumed_outputs: tuple[ResolvedAgentOutput, ...],
) -> AgentExecutionResult:
    planning_steps = (
        "analyze the problem statement",
        "choose a candidate algorithm",
        "prepare a testable implementation",
    )
    if consumed_outputs:
        planning_steps = planning_steps + ("integrate referenced context",)
    summary = "Plan: " + "; ".join(planning_steps) + "."
    return AgentExecutionResult(
        step_index=step_index,
        agent_name=agent.name,
        role=agent.role,
        summary=summary,
        references=agent.refs,
        consumed_outputs=consumed_outputs,
    )


def _run_algorithmic_role(
    problem: ProblemInstance,
    agent: AgentInvocation,
    step_index: int,
    consumed_outputs: tuple[ResolvedAgentOutput, ...],
) -> AgentExecutionResult:
    del problem
    ref_summary = _format_reference_names(consumed_outputs)
    summary = f"Algorithmic decomposition prepared from {ref_summary}."
    return AgentExecutionResult(
        step_index=step_index,
        agent_name=agent.name,
        role=agent.role,
        summary=summary,
        references=agent.refs,
        consumed_outputs=consumed_outputs,
    )


def _run_coding_role(
    problem: ProblemInstance,
    agent: AgentInvocation,
    step_index: int,
    consumed_outputs: tuple[ResolvedAgentOutput, ...],
) -> AgentExecutionResult:
    focus = _extract_focus(problem.prompt)
    ref_summary = _format_reference_names(consumed_outputs)
    candidate_code = (
        f"def solve() -> str:\n"
        f"    \"\"\"Deterministic candidate for {problem.identifier}.\"\"\"\n"
        f"    return \"{focus} solved using {ref_summary}\"\n"
    )
    return AgentExecutionResult(
        step_index=step_index,
        agent_name=agent.name,
        role=agent.role,
        summary=f"Candidate code drafted from {ref_summary}.",
        references=agent.refs,
        consumed_outputs=consumed_outputs,
        candidate_code=candidate_code,
    )


def _run_debugging_role(
    problem: ProblemInstance,
    agent: AgentInvocation,
    step_index: int,
    consumed_outputs: tuple[ResolvedAgentOutput, ...],
) -> AgentExecutionResult:
    del problem
    referenced_code = next(
        (output.candidate_code for output in reversed(consumed_outputs) if output.candidate_code),
        None,
    )
    diagnostics = ("Checked edge cases and failure modes.",)
    candidate_code = None
    if referenced_code is not None:
        candidate_code = referenced_code + "    # Debugger review: deterministic sanity checks applied.\n"
        diagnostics = diagnostics + ("Revised the referenced candidate code.",)

    return AgentExecutionResult(
        step_index=step_index,
        agent_name=agent.name,
        role=agent.role,
        summary="Debugging review completed.",
        references=agent.refs,
        consumed_outputs=consumed_outputs,
        candidate_code=candidate_code,
        diagnostics=diagnostics,
    )


def _run_testing_role(
    problem: ProblemInstance,
    agent: AgentInvocation,
    step_index: int,
    consumed_outputs: tuple[ResolvedAgentOutput, ...],
) -> AgentExecutionResult:
    del problem
    candidate_code = next(
        (output.candidate_code for output in reversed(consumed_outputs) if output.candidate_code),
        None,
    )
    if candidate_code is None:
        outcome = TestingOutcome.FAILED
        diagnostics = ("No candidate code was available to test.",)
        summary = "Testing failed because no candidate code reached the final layer."
    else:
        outcome = TestingOutcome.PASSED
        diagnostics = ("Deterministic testing accepted the candidate code.",)
        summary = "Testing completed successfully for the referenced candidate code."

    return AgentExecutionResult(
        step_index=step_index,
        agent_name=agent.name,
        role=agent.role,
        summary=summary,
        references=agent.refs,
        consumed_outputs=consumed_outputs,
        candidate_code=candidate_code,
        diagnostics=diagnostics,
        testing_outcome=outcome,
    )


def _extract_focus(prompt: str) -> str:
    prompt_tokens = [token.strip(".,:;()[]{}") for token in prompt.lower().split()]
    meaningful_tokens = [
        token for token in prompt_tokens if token and token not in {"the", "a", "an", "and", "or", "to"}
    ]
    return meaningful_tokens[0] if meaningful_tokens else "problem"


def _format_reference_names(consumed_outputs: tuple[ResolvedAgentOutput, ...]) -> str:
    if not consumed_outputs:
        return "local reasoning only"
    return ", ".join(output.agent_name for output in consumed_outputs)
