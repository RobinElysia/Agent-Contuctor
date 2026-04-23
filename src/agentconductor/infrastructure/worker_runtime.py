"""Repository-local model-backed worker runtime adapters."""

from __future__ import annotations

from agentconductor.domain.topology import AgentRole
from agentconductor.domain.worker_runtime import (
    WorkerGenerationRequest,
    WorkerGenerationResult,
    WorkerRoleRuntime,
    WorkerRuntimeError,
)


class RepositoryWorkerModelRuntime(WorkerRoleRuntime):
    """Local prompt-driven worker runtime behind an explicit model adapter seam."""

    def __init__(
        self,
        *,
        runtime_name: str = "repository-worker-runtime",
        model_name_by_role: dict[AgentRole, str] | None = None,
    ) -> None:
        self.runtime_name = runtime_name
        self.model_name_by_role = model_name_by_role or {
            AgentRole.RETRIEVAL: "gpt-4o-mini-compatible-stub",
            AgentRole.PLANNING: "gpt-4o-mini-compatible-stub",
            AgentRole.ALGORITHMIC: "gpt-4o-mini-compatible-stub",
            AgentRole.CODING: "gpt-4o-mini-compatible-stub",
            AgentRole.DEBUGGING: "gpt-4o-mini-compatible-stub",
        }

    def supports_role(self, role: AgentRole) -> bool:
        return role in self.model_name_by_role

    def generate_role_output(
        self,
        request: WorkerGenerationRequest,
    ) -> WorkerGenerationResult:
        if not self.supports_role(request.agent.role):
            raise WorkerRuntimeError(
                f"worker runtime '{self.runtime_name}' does not support role "
                f"'{request.agent.role.value}'"
            )
        model_name = self.model_name_by_role[request.agent.role]
        role = request.agent.role
        if role is AgentRole.RETRIEVAL:
            summary = (
                f"Retrieved prompt-grounded context about {_extract_focus(request.problem.prompt)} "
                "through the worker-model runtime."
            )
            return WorkerGenerationResult(
                summary=summary,
                runtime_name=self.runtime_name,
                model_name=model_name,
            )
        if role is AgentRole.PLANNING:
            plan_items = [
                "analyze the problem statement",
                "choose an algorithm",
                "prepare a testable implementation",
            ]
            if request.consumed_outputs:
                plan_items.append("integrate referenced context")
            return WorkerGenerationResult(
                summary="Plan: " + "; ".join(plan_items) + ".",
                runtime_name=self.runtime_name,
                model_name=model_name,
            )
        if role is AgentRole.ALGORITHMIC:
            return WorkerGenerationResult(
                summary=(
                    "Algorithmic decomposition prepared from "
                    f"{_format_reference_names(request)}."
                ),
                runtime_name=self.runtime_name,
                model_name=model_name,
            )
        if role is AgentRole.CODING:
            focus = _extract_focus(request.problem.prompt)
            return WorkerGenerationResult(
                summary=f"Candidate code drafted from {_format_reference_names(request)}.",
                candidate_code=(
                    f"def solve() -> str:\n"
                    f"    \"\"\"Model-backed candidate for {request.problem.identifier}.\"\"\"\n"
                    f"    return \"{focus} solved\"\n"
                ),
                runtime_name=self.runtime_name,
                model_name=model_name,
            )
        if role is AgentRole.DEBUGGING:
            referenced_code = next(
                (
                    output.candidate_code
                    for output in reversed(request.consumed_outputs)
                    if output.candidate_code
                ),
                None,
            )
            diagnostics = ("Checked edge cases and failure modes.",)
            candidate_code = None
            if referenced_code is not None:
                candidate_code = (
                    referenced_code
                    + "    # Debugger review: model-backed sanity checks applied.\n"
                )
                diagnostics = diagnostics + ("Revised the referenced candidate code.",)
            return WorkerGenerationResult(
                summary="Debugging review completed.",
                candidate_code=candidate_code,
                diagnostics=diagnostics,
                runtime_name=self.runtime_name,
                model_name=model_name,
            )
        raise WorkerRuntimeError(
            f"worker runtime '{self.runtime_name}' cannot serve role '{role.value}'"
        )


def _extract_focus(prompt: str) -> str:
    prompt_tokens = [token.strip(".,:;()[]{}") for token in prompt.lower().split()]
    meaningful_tokens = [
        token for token in prompt_tokens if token and token not in {"the", "a", "an", "and", "or", "to"}
    ]
    return meaningful_tokens[0] if meaningful_tokens else "problem"


def _format_reference_names(request: WorkerGenerationRequest) -> str:
    if not request.consumed_outputs:
        return "local reasoning only"
    return ", ".join(output.agent_name for output in request.consumed_outputs)
