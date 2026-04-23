"""Single-turn execution for validated topology plans."""

from __future__ import annotations

from collections.abc import Callable

from agentconductor.domain.execution import (
    AgentExecutionResult,
    CodeCandidate,
    ExecutionStatus,
    JudgeResourceLimits,
    JudgeTestCase,
    ResolvedAgentOutput,
    SandboxAdapter,
    SandboxExecutionResult,
    SandboxTestSpec,
    StepExecutionResult,
    TestingOutcome,
    TopologyExecutionError,
    TopologyExecutionResult,
)
from agentconductor.domain.models import ProblemInstance
from agentconductor.domain.topology import AgentInvocation, AgentReference, AgentRole, TopologyPlan
from agentconductor.domain.worker_runtime import (
    WorkerGenerationRequest,
    WorkerRoleRuntime,
)
from agentconductor.infrastructure.sandbox import PythonSubprocessJudgeAdapter
from agentconductor.infrastructure.worker_runtime import RepositoryWorkerModelRuntime

RoleHandler = Callable[
    [ProblemInstance, AgentInvocation, int, tuple[ResolvedAgentOutput, ...]],
    AgentExecutionResult,
]


def execute_topology(
    problem: ProblemInstance,
    topology: TopologyPlan,
    *,
    registry: dict[AgentRole, RoleHandler] | None = None,
    sandbox: SandboxAdapter | None = None,
    worker_runtime: WorkerRoleRuntime | None = None,
) -> TopologyExecutionResult:
    """Execute a single-turn topology plan layer by layer."""
    topology.validate()
    active_registry = registry or build_default_role_registry(
        sandbox=sandbox,
        worker_runtime=worker_runtime,
    )

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
    sandbox_result = final_testing_result.sandbox_result if final_testing_result else None

    return TopologyExecutionResult(
        problem=problem,
        difficulty=topology.difficulty,
        status=ExecutionStatus.COMPLETED,
        step_results=tuple(step_results),
        final_candidate_code=final_candidate_code,
        testing_outcome=testing_outcome,
        diagnostics=diagnostics,
        sandbox_result=sandbox_result,
    )


def build_default_role_registry(
    *,
    sandbox: SandboxAdapter | None = None,
    worker_runtime: WorkerRoleRuntime | None = None,
) -> dict[AgentRole, RoleHandler]:
    """Return the default execution registry for model-backed worker roles."""
    active_sandbox = sandbox or PythonSubprocessJudgeAdapter()
    active_worker_runtime = worker_runtime or RepositoryWorkerModelRuntime()
    return {
        AgentRole.RETRIEVAL: lambda problem, agent, step_index, consumed_outputs: _run_model_backed_role(
            problem,
            agent,
            step_index,
            consumed_outputs,
            worker_runtime=active_worker_runtime,
        ),
        AgentRole.PLANNING: lambda problem, agent, step_index, consumed_outputs: _run_model_backed_role(
            problem,
            agent,
            step_index,
            consumed_outputs,
            worker_runtime=active_worker_runtime,
        ),
        AgentRole.ALGORITHMIC: lambda problem, agent, step_index, consumed_outputs: _run_model_backed_role(
            problem,
            agent,
            step_index,
            consumed_outputs,
            worker_runtime=active_worker_runtime,
        ),
        AgentRole.CODING: lambda problem, agent, step_index, consumed_outputs: _run_model_backed_role(
            problem,
            agent,
            step_index,
            consumed_outputs,
            worker_runtime=active_worker_runtime,
        ),
        AgentRole.DEBUGGING: lambda problem, agent, step_index, consumed_outputs: _run_model_backed_role(
            problem,
            agent,
            step_index,
            consumed_outputs,
            worker_runtime=active_worker_runtime,
        ),
        AgentRole.TESTING: lambda problem, agent, step_index, consumed_outputs: _run_testing_role(
            problem,
            agent,
            step_index,
            consumed_outputs,
            sandbox=active_sandbox,
        ),
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


def _run_model_backed_role(
    problem: ProblemInstance,
    agent: AgentInvocation,
    step_index: int,
    consumed_outputs: tuple[ResolvedAgentOutput, ...],
    *,
    worker_runtime: WorkerRoleRuntime,
) -> AgentExecutionResult:
    prompt = build_worker_prompt(
        problem,
        agent,
        step_index,
        consumed_outputs,
    )
    response = worker_runtime.generate_role_output(
        WorkerGenerationRequest(
            problem=problem,
            agent=agent,
            step_index=step_index,
            consumed_outputs=consumed_outputs,
            prompt=prompt,
        )
    )
    return AgentExecutionResult(
        step_index=step_index,
        agent_name=agent.name,
        role=agent.role,
        summary=response.summary,
        references=agent.refs,
        consumed_outputs=consumed_outputs,
        candidate_code=response.candidate_code,
        diagnostics=response.diagnostics,
        worker_runtime=response.runtime_name,
        worker_model=response.model_name,
    )


def _run_testing_role(
    problem: ProblemInstance,
    agent: AgentInvocation,
    step_index: int,
    consumed_outputs: tuple[ResolvedAgentOutput, ...],
    *,
    sandbox: SandboxAdapter,
) -> AgentExecutionResult:
    extracted_candidate = extract_code_candidate(consumed_outputs)
    if extracted_candidate is None:
        outcome = TestingOutcome.NO_CANDIDATE
        diagnostics = ("No candidate code was available to test.",)
        summary = "Testing failed because no candidate code reached the final layer."
        candidate_code = None
        sandbox_result = SandboxExecutionResult(
            outcome=outcome,
            diagnostics=diagnostics,
        )
    else:
        candidate_code = extracted_candidate.source_code
        sandbox_result = sandbox.evaluate(
            problem,
            extracted_candidate,
            build_judge_test_spec(problem),
        )
        outcome = sandbox_result.outcome
        diagnostics = sandbox_result.diagnostics
        summary = _summarize_testing_outcome(outcome)

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
        sandbox_result=sandbox_result,
    )


def _extract_focus(prompt: str) -> str:
    prompt_tokens = [token.strip(".,:;()[]{}") for token in prompt.lower().split()]
    meaningful_tokens = [
        token for token in prompt_tokens if token and token not in {"the", "a", "an", "and", "or", "to"}
    ]
    return meaningful_tokens[0] if meaningful_tokens else "problem"


def build_worker_prompt(
    problem: ProblemInstance,
    agent: AgentInvocation,
    step_index: int,
    consumed_outputs: tuple[ResolvedAgentOutput, ...],
) -> str:
    """Build the explicit prompt sent to one non-testing worker runtime."""
    sections = [
        "You are a worker agent in AgentConductor.",
        f"Role: {agent.role.value}",
        f"Problem id: {problem.identifier}",
        f"Step index: {step_index}",
        "Problem prompt:",
        problem.prompt,
    ]
    if consumed_outputs:
        sections.extend(
            [
                "Referenced upstream outputs:",
                "\n".join(
                    f"- {output.agent_name} ({output.role.value}): {output.summary}"
                    for output in consumed_outputs
                ),
            ]
        )
    else:
        sections.append("Referenced upstream outputs: none")
    if agent.role is AgentRole.CODING:
        sections.append("Return candidate Python code suitable for the testing role.")
    elif agent.role is AgentRole.DEBUGGING:
        sections.append("Revise any referenced candidate code when needed.")
    else:
        sections.append("Return a concise structured summary for this role.")
    return "\n".join(sections)


def build_judge_test_spec(problem: ProblemInstance) -> SandboxTestSpec:
    """Return a repository-local judge spec derived from the current problem."""
    expected_output = f"{_extract_focus(problem.prompt)} solved"
    return SandboxTestSpec(
        entrypoint="solve",
        test_cases=(
            JudgeTestCase(
                name="prompt-derived-smoke",
                expected_output=expected_output,
            ),
        ),
        resource_limits=JudgeResourceLimits(cpu_time_seconds=1.0),
    )


def extract_code_candidate(
    consumed_outputs: tuple[ResolvedAgentOutput, ...],
) -> CodeCandidate | None:
    """Extract the last referenced Python candidate from upstream outputs."""
    for output in reversed(consumed_outputs):
        if not output.candidate_code:
            continue
        source_code = _normalize_candidate_code(output.candidate_code)
        if source_code is None:
            continue
        return CodeCandidate(
            step_index=output.step_index,
            agent_name=output.agent_name,
            role=output.role,
            source_code=source_code,
        )
    return None


def _normalize_candidate_code(raw_code: str) -> str | None:
    stripped = raw_code.strip()
    if not stripped:
        return None
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if len(lines) < 3:
        return None
    if not lines[-1].startswith("```"):
        return None
    return "\n".join(lines[1:-1]).strip() or None


def _summarize_testing_outcome(outcome: TestingOutcome) -> str:
    if outcome is TestingOutcome.PASSED:
        return "Testing completed successfully for the referenced candidate code."
    if outcome is TestingOutcome.WRONG_ANSWER:
        return "Testing rejected the candidate code with a wrong-answer result."
    if outcome is TestingOutcome.COMPILATION_ERROR:
        return "Testing rejected the candidate code because it did not compile."
    if outcome is TestingOutcome.RUNTIME_ERROR:
        return "Testing rejected the candidate code because it raised at runtime."
    if outcome is TestingOutcome.TIME_LIMIT_EXCEEDED:
        return "Testing rejected the candidate code because it exceeded the timeout."
    if outcome is TestingOutcome.MEMORY_LIMIT_EXCEEDED:
        return "Testing rejected the candidate code because it exceeded memory limits."
    if outcome is TestingOutcome.NO_CANDIDATE:
        return "Testing could not start because no candidate code was available."
    return "Testing rejected the candidate code."


def _format_reference_names(consumed_outputs: tuple[ResolvedAgentOutput, ...]) -> str:
    if not consumed_outputs:
        return "local reasoning only"
    return ", ".join(output.agent_name for output in consumed_outputs)
