"""Deterministic rule-based topology planning."""

from __future__ import annotations

from dataclasses import replace
from enum import StrEnum
from pathlib import Path
import re

from agentconductor.domain.execution import ExecutionStatus
from agentconductor.domain.history import TopologyRevisionInput
from agentconductor.domain.orchestration import (
    LearnedTopologyPlan,
    OrchestratorCheckpointLoadError,
    OrchestratorMode,
    OrchestratorPromptRequest,
    TopologyCandidateExtractionError,
    TopologyOrchestratorPolicy,
    TopologyPromptKind,
)
from agentconductor.domain.models import DifficultyLevel, ProblemInstance
from agentconductor.domain.topology import (
    AgentInvocation,
    AgentReference,
    AgentRole,
    TopologyLogicError,
    TopologyPlan,
    TopologyStep,
)
from agentconductor.domain.training import OrchestratorCheckpointMetadata
from agentconductor.infrastructure.training_checkpoint import (
    resolve_orchestrator_checkpoint_metadata,
)
from agentconductor.infrastructure.topology_yaml import (
    dump_topology_yaml_mapping,
    parse_topology_plan_yaml,
)


class ProblemShape(StrEnum):
    """Coarse local problem categories used by the rule-based orchestrator."""

    GENERAL = "general"
    KNOWLEDGE_INTENSIVE = "knowledge_intensive"
    DEBUGGING = "debugging"


KNOWLEDGE_KEYWORDS = (
    "graph",
    "tree",
    "dynamic programming",
    "dp",
    "constraint",
    "geometry",
    "combin",
)
DEBUGGING_KEYWORDS = (
    "debug",
    "bug",
    "fix",
    "error",
    "failing",
    "incorrect",
    "broken",
)
YAML_FENCE_PATTERN = re.compile(
    r"```(?:yaml|yml)?\s*(.*?)```",
    re.IGNORECASE | re.DOTALL,
)
SUPPORTED_FROZEN_PROMPT_TEMPLATE = "orchestrator-sft-v1"
SUPPORTED_FROZEN_DEVICE = "cpu"


class CheckpointTopologyPolicy:
    """Repository-local checkpoint-backed frozen-inference policy."""

    def __init__(
        self,
        metadata: OrchestratorCheckpointMetadata,
        *,
        device: str = SUPPORTED_FROZEN_DEVICE,
    ) -> None:
        if device != SUPPORTED_FROZEN_DEVICE:
            raise OrchestratorCheckpointLoadError(
                "repository-local frozen inference currently supports only "
                f"device='{SUPPORTED_FROZEN_DEVICE}'"
            )
        if metadata.target_format != "yaml":
            raise OrchestratorCheckpointLoadError(
                "checkpoint metadata must target YAML frozen inference"
            )
        if metadata.prompt_template_version != SUPPORTED_FROZEN_PROMPT_TEMPLATE:
            raise OrchestratorCheckpointLoadError(
                "checkpoint prompt template version "
                f"'{metadata.prompt_template_version}' is not supported; expected "
                f"'{SUPPORTED_FROZEN_PROMPT_TEMPLATE}'"
            )
        checkpoint_dir = Path(metadata.checkpoint_path)
        weights_stub_path = checkpoint_dir / "weights.stub"
        if not weights_stub_path.exists():
            raise OrchestratorCheckpointLoadError(
                f"checkpoint weights artifact is missing: {weights_stub_path}"
            )
        self.metadata = metadata
        self.device = device

    def generate_topology_candidate(
        self,
        *,
        prompt: str,
        request: OrchestratorPromptRequest,
    ) -> str:
        del prompt
        if request.kind is TopologyPromptKind.INITIAL:
            topology = plan_topology_for_problem(request.problem)
        else:
            if request.testing_feedback is None:
                raise OrchestratorCheckpointLoadError(
                    "revision inference requires testing feedback"
                )
            if request.prior_topology is None:
                raise OrchestratorCheckpointLoadError(
                    "revision inference requires a prior topology"
                )
            if request.remaining_turns is None:
                raise OrchestratorCheckpointLoadError(
                    "revision inference requires remaining_turns"
                )
            topology = revise_topology_for_feedback(
                TopologyRevisionInput(
                    problem=request.problem,
                    selected_difficulty=request.selected_difficulty,
                    turn_index=request.turn_index,
                    prior_topology=request.prior_topology,
                    prior_execution_status=ExecutionStatus.COMPLETED,
                    testing_feedback=request.testing_feedback,
                    remaining_turns=request.remaining_turns,
                )
            )
        return dump_topology_yaml_mapping(topology.to_mapping())


def infer_problem_shape(problem: ProblemInstance) -> ProblemShape:
    """Infer a coarse problem shape from the prompt text.

    Inference:
    The paper does not define an explicit runtime taxonomy for prompt shape.
    This repository uses a small deterministic keyword heuristic so the initial
    orchestrator remains local, inspectable, and replaceable.
    """
    prompt = problem.prompt.lower()
    if any(keyword in prompt for keyword in DEBUGGING_KEYWORDS):
        return ProblemShape.DEBUGGING
    if any(keyword in prompt for keyword in KNOWLEDGE_KEYWORDS):
        return ProblemShape.KNOWLEDGE_INTENSIVE
    return ProblemShape.GENERAL


def resolve_orchestrator_runtime(
    *,
    orchestrator_policy: TopologyOrchestratorPolicy | None = None,
    orchestrator_checkpoint: str | Path | None = None,
    orchestrator_checkpoint_id: str | None = None,
    orchestrator_device: str = SUPPORTED_FROZEN_DEVICE,
) -> tuple[OrchestratorMode, TopologyOrchestratorPolicy | None, OrchestratorCheckpointMetadata | None]:
    """Resolve the orchestrator path for deterministic, direct-policy, or checkpoint modes."""
    if orchestrator_policy is not None and orchestrator_checkpoint is not None:
        raise ValueError(
            "orchestrator_policy and orchestrator_checkpoint are mutually exclusive"
        )
    if orchestrator_policy is not None:
        return OrchestratorMode.LEARNED, orchestrator_policy, None
    if orchestrator_checkpoint is None:
        return OrchestratorMode.DETERMINISTIC, None, None
    metadata = resolve_orchestrator_checkpoint_metadata(
        orchestrator_checkpoint,
        checkpoint_id=orchestrator_checkpoint_id,
    )
    return (
        OrchestratorMode.LEARNED,
        CheckpointTopologyPolicy(metadata, device=orchestrator_device),
        metadata,
    )


def plan_topology_for_problem(problem: ProblemInstance) -> TopologyPlan:
    """Return a deterministic single-turn topology plan for a problem."""
    difficulty = problem.difficulty or DifficultyLevel.MEDIUM
    shape = infer_problem_shape(problem)

    if difficulty is DifficultyLevel.EASY:
        return _easy_topology()
    if difficulty is DifficultyLevel.HARD:
        return _hard_topology(shape)
    return _medium_topology(shape)


def plan_topology_with_policy(
    problem: ProblemInstance,
    *,
    policy: TopologyOrchestratorPolicy,
    max_attempts: int = 1,
) -> LearnedTopologyPlan:
    """Return a parsed topology candidate from a learned-policy boundary."""
    difficulty = problem.difficulty or DifficultyLevel.MEDIUM
    request = OrchestratorPromptRequest(
        kind=TopologyPromptKind.INITIAL,
        problem=ProblemInstance(
            identifier=problem.identifier,
            prompt=problem.prompt,
            difficulty=difficulty,
        ),
        selected_difficulty=difficulty,
        turn_index=0,
    )
    return _generate_topology_with_policy(
        request=request,
        policy=policy,
        max_attempts=max_attempts,
    )


def revise_topology_for_feedback(revision: TopologyRevisionInput) -> TopologyPlan:
    """Return a deterministic revised topology for a failed prior turn.

    Inference:
    The paper states that later turns consume prior feedback and history, but it
    does not define a concrete repository-local revision policy. This function
    implements an inspectable fallback policy that increases debugging focus and
    preserves explicit dependency on the prior testing diagnostics.
    """
    shape = infer_problem_shape(revision.problem)
    diagnostics = " ".join(revision.testing_feedback.diagnostics).lower()
    requires_retrieval = shape is ProblemShape.KNOWLEDGE_INTENSIVE or any(
        keyword in diagnostics
        for keyword in ("constraint", "graph", "path", "dp", "dynamic programming")
    )

    if revision.selected_difficulty is DifficultyLevel.EASY:
        return _easy_revision_topology(revision.turn_index)
    if revision.selected_difficulty is DifficultyLevel.HARD:
        return _hard_revision_topology(revision.turn_index, requires_retrieval)
    return _medium_revision_topology(revision.turn_index, requires_retrieval)


def revise_topology_with_policy(
    revision: TopologyRevisionInput,
    *,
    policy: TopologyOrchestratorPolicy,
    max_attempts: int = 1,
) -> LearnedTopologyPlan:
    """Return a parsed revised topology candidate from a learned policy."""
    request = OrchestratorPromptRequest(
        kind=TopologyPromptKind.REVISION,
        problem=revision.problem,
        selected_difficulty=revision.selected_difficulty,
        turn_index=revision.turn_index,
        prior_topology=revision.prior_topology,
        testing_feedback=revision.testing_feedback,
        remaining_turns=revision.remaining_turns,
    )
    return _generate_topology_with_policy(
        request=request,
        policy=policy,
        max_attempts=max_attempts,
    )


def build_orchestrator_prompt(request: OrchestratorPromptRequest) -> str:
    """Build the explicit prompt sent to a learned topology policy."""
    sections = [
        "You are the AgentConductor orchestrator.",
        "Return exactly one topology YAML document for the current turn.",
        "Use the repository YAML contract:",
        "difficulty: <easy|medium|hard>",
        "steps:",
        "  - index: <int>",
        "    agents:",
        "      - name: <string>",
        "        role: <retrieval|planning|algorithmic|coding|debugging|testing>",
        "        refs:",
        "          - step_index: <int>",
        "            agent_name: <string>",
        "",
        f"Planning kind: {request.kind.value}",
        f"Problem id: {request.problem.identifier}",
        f"Difficulty: {request.selected_difficulty.value}",
        "Problem prompt:",
        request.problem.prompt,
    ]

    if request.kind is TopologyPromptKind.REVISION:
        sections.extend(
            [
                "",
                f"Revision turn index: {request.turn_index}",
                f"Remaining turns after this one: {request.remaining_turns}",
                "Prior testing outcome:",
                request.testing_feedback.outcome.value
                if request.testing_feedback is not None
                and request.testing_feedback.outcome is not None
                else "(none)",
                "Prior diagnostics:",
                "\n".join(request.testing_feedback.diagnostics)
                if request.testing_feedback and request.testing_feedback.diagnostics
                else "(none)",
                "Prior topology YAML:",
                dump_topology_yaml_mapping(request.prior_topology.to_mapping())
                if request.prior_topology is not None
                else "(none)",
            ]
        )

    if request.last_error:
        sections.extend(
            [
                "",
                "The previous candidate was rejected.",
                f"Error: {request.last_error}",
                "Repair the topology and return only corrected YAML.",
            ]
        )

    return "\n".join(sections)


def extract_topology_yaml_candidate(raw_response: str) -> str:
    """Extract a YAML document from a raw policy response."""
    stripped_response = raw_response.strip()
    if stripped_response.startswith("difficulty:"):
        return stripped_response

    for match in YAML_FENCE_PATTERN.finditer(stripped_response):
        candidate = match.group(1).strip()
        if candidate:
            return candidate

    raise TopologyCandidateExtractionError(
        "policy response did not contain a repository topology YAML block"
    )


def _generate_topology_with_policy(
    *,
    request: OrchestratorPromptRequest,
    policy: TopologyOrchestratorPolicy,
    max_attempts: int,
) -> LearnedTopologyPlan:
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    last_error: Exception | None = None
    for attempt_count in range(1, max_attempts + 1):
        attempted_request = replace(
            request,
            last_error=None
            if last_error is None
            else f"{type(last_error).__name__}: {last_error}",
        )
        prompt = build_orchestrator_prompt(attempted_request)
        raw_response = policy.generate_topology_candidate(
            prompt=prompt,
            request=attempted_request,
        )
        try:
            topology_yaml = extract_topology_yaml_candidate(raw_response)
            topology = parse_topology_plan_yaml(topology_yaml)
            if topology.difficulty is not request.selected_difficulty:
                raise TopologyLogicError(
                    "learned orchestrator returned topology difficulty "
                    f"'{topology.difficulty.value}' but expected "
                    f"'{request.selected_difficulty.value}'"
                )
        except (TopologyCandidateExtractionError, ValueError) as exc:
            last_error = exc
            continue

        return LearnedTopologyPlan(
            topology=topology,
            topology_yaml=topology_yaml,
            prompt=prompt,
            raw_response=raw_response,
            attempt_count=attempt_count,
            kind=request.kind,
        )

    assert last_error is not None
    raise last_error


def _easy_topology() -> TopologyPlan:
    return TopologyPlan(
        difficulty=DifficultyLevel.EASY,
        steps=(
            TopologyStep(
                index=0,
                agents=(
                    AgentInvocation(name="planner_0", role=AgentRole.PLANNING),
                ),
            ),
            TopologyStep(
                index=1,
                agents=(
                    AgentInvocation(
                        name="coder_1",
                        role=AgentRole.CODING,
                        refs=(AgentReference(step_index=0, agent_name="planner_0"),),
                    ),
                ),
            ),
            TopologyStep(
                index=2,
                agents=(
                    AgentInvocation(
                        name="tester_2",
                        role=AgentRole.TESTING,
                        refs=(
                            AgentReference(step_index=0, agent_name="planner_0"),
                            AgentReference(step_index=1, agent_name="coder_1"),
                        ),
                    ),
                ),
            ),
        ),
    )


def _medium_topology(shape: ProblemShape) -> TopologyPlan:
    if shape is ProblemShape.DEBUGGING:
        return TopologyPlan(
            difficulty=DifficultyLevel.MEDIUM,
            steps=(
                TopologyStep(
                    index=0,
                    agents=(
                        AgentInvocation(name="planner_0", role=AgentRole.PLANNING),
                    ),
                ),
                TopologyStep(
                    index=1,
                    agents=(
                        AgentInvocation(
                            name="debugger_1",
                            role=AgentRole.DEBUGGING,
                            refs=(AgentReference(step_index=0, agent_name="planner_0"),),
                        ),
                        AgentInvocation(
                            name="coder_1",
                            role=AgentRole.CODING,
                            refs=(AgentReference(step_index=0, agent_name="planner_0"),),
                        ),
                    ),
                ),
                TopologyStep(
                    index=2,
                    agents=(
                        AgentInvocation(
                            name="tester_2",
                            role=AgentRole.TESTING,
                            refs=(
                                AgentReference(step_index=1, agent_name="debugger_1"),
                                AgentReference(step_index=1, agent_name="coder_1"),
                            ),
                        ),
                    ),
                ),
            ),
        )

    step_zero_agents = [
        AgentInvocation(name="planner_0", role=AgentRole.PLANNING),
    ]
    if shape is ProblemShape.KNOWLEDGE_INTENSIVE:
        step_zero_agents.insert(
            0, AgentInvocation(name="retrieval_0", role=AgentRole.RETRIEVAL)
        )

    step_one_refs = [AgentReference(step_index=0, agent_name="planner_0")]
    if shape is ProblemShape.KNOWLEDGE_INTENSIVE:
        step_one_refs.insert(0, AgentReference(step_index=0, agent_name="retrieval_0"))

    return TopologyPlan(
        difficulty=DifficultyLevel.MEDIUM,
        steps=(
            TopologyStep(index=0, agents=tuple(step_zero_agents)),
            TopologyStep(
                index=1,
                agents=(
                    AgentInvocation(
                        name="algorithmic_1",
                        role=AgentRole.ALGORITHMIC,
                        refs=tuple(step_one_refs),
                    ),
                    AgentInvocation(
                        name="coder_1",
                        role=AgentRole.CODING,
                        refs=tuple(step_one_refs),
                    ),
                ),
            ),
            TopologyStep(
                index=2,
                agents=(
                    AgentInvocation(
                        name="tester_2",
                        role=AgentRole.TESTING,
                        refs=(
                            AgentReference(step_index=1, agent_name="algorithmic_1"),
                            AgentReference(step_index=1, agent_name="coder_1"),
                        ),
                    ),
                ),
            ),
        ),
    )


def _hard_topology(shape: ProblemShape) -> TopologyPlan:
    step_zero_agents = [
        AgentInvocation(name="retrieval_0", role=AgentRole.RETRIEVAL),
        AgentInvocation(name="planner_0", role=AgentRole.PLANNING),
    ]
    if shape is ProblemShape.DEBUGGING:
        step_zero_agents = [
            AgentInvocation(name="planner_0", role=AgentRole.PLANNING),
            AgentInvocation(name="debugger_0", role=AgentRole.DEBUGGING),
        ]

    common_refs = tuple(
        AgentReference(step_index=0, agent_name=agent.name) for agent in step_zero_agents
    )

    step_one_agents = [
        AgentInvocation(
            name="algorithmic_1",
            role=AgentRole.ALGORITHMIC,
            refs=common_refs,
        ),
        AgentInvocation(
            name="coder_1",
            role=AgentRole.CODING,
            refs=common_refs,
        ),
    ]
    if shape is not ProblemShape.DEBUGGING:
        step_one_agents.append(
            AgentInvocation(
                name="debugger_1",
                role=AgentRole.DEBUGGING,
                refs=common_refs,
            )
        )

    test_refs = tuple(
        AgentReference(step_index=1, agent_name=agent.name) for agent in step_one_agents
    )

    return TopologyPlan(
        difficulty=DifficultyLevel.HARD,
        steps=(
            TopologyStep(index=0, agents=tuple(step_zero_agents)),
            TopologyStep(index=1, agents=tuple(step_one_agents)),
            TopologyStep(
                index=2,
                agents=(
                    AgentInvocation(
                        name="tester_2",
                        role=AgentRole.TESTING,
                        refs=test_refs,
                    ),
                ),
            ),
        ),
    )


def _easy_revision_topology(turn_index: int) -> TopologyPlan:
    return TopologyPlan(
        difficulty=DifficultyLevel.EASY,
        steps=(
            TopologyStep(
                index=0,
                agents=(AgentInvocation(name=f"planner_t{turn_index}_0", role=AgentRole.PLANNING),),
            ),
            TopologyStep(
                index=1,
                agents=(
                    AgentInvocation(
                        name=f"coder_t{turn_index}_1",
                        role=AgentRole.CODING,
                        refs=(
                            AgentReference(step_index=0, agent_name=f"planner_t{turn_index}_0"),
                        ),
                    ),
                ),
            ),
            TopologyStep(
                index=2,
                agents=(
                    AgentInvocation(
                        name=f"debugger_t{turn_index}_2",
                        role=AgentRole.DEBUGGING,
                        refs=(
                            AgentReference(step_index=1, agent_name=f"coder_t{turn_index}_1"),
                        ),
                    ),
                ),
            ),
            TopologyStep(
                index=3,
                agents=(
                    AgentInvocation(
                        name=f"tester_t{turn_index}_3",
                        role=AgentRole.TESTING,
                        refs=(
                            AgentReference(step_index=0, agent_name=f"planner_t{turn_index}_0"),
                            AgentReference(step_index=2, agent_name=f"debugger_t{turn_index}_2"),
                        ),
                    ),
                ),
            ),
        ),
    )


def _medium_revision_topology(turn_index: int, requires_retrieval: bool) -> TopologyPlan:
    step_zero_agents = [AgentInvocation(name=f"planner_t{turn_index}_0", role=AgentRole.PLANNING)]
    if requires_retrieval:
        step_zero_agents.insert(
            0, AgentInvocation(name=f"retrieval_t{turn_index}_0", role=AgentRole.RETRIEVAL)
        )

    step_one_refs = [AgentReference(step_index=0, agent_name=f"planner_t{turn_index}_0")]
    if requires_retrieval:
        step_one_refs.insert(
            0, AgentReference(step_index=0, agent_name=f"retrieval_t{turn_index}_0")
        )

    return TopologyPlan(
        difficulty=DifficultyLevel.MEDIUM,
        steps=(
            TopologyStep(index=0, agents=tuple(step_zero_agents)),
            TopologyStep(
                index=1,
                agents=(
                    AgentInvocation(
                        name=f"algorithmic_t{turn_index}_1",
                        role=AgentRole.ALGORITHMIC,
                        refs=tuple(step_one_refs),
                    ),
                    AgentInvocation(
                        name=f"coder_t{turn_index}_1",
                        role=AgentRole.CODING,
                        refs=tuple(step_one_refs),
                    ),
                ),
            ),
            TopologyStep(
                index=2,
                agents=(
                    AgentInvocation(
                        name=f"debugger_t{turn_index}_2",
                        role=AgentRole.DEBUGGING,
                        refs=(
                            AgentReference(step_index=1, agent_name=f"algorithmic_t{turn_index}_1"),
                            AgentReference(step_index=1, agent_name=f"coder_t{turn_index}_1"),
                        ),
                    ),
                ),
            ),
            TopologyStep(
                index=3,
                agents=(
                    AgentInvocation(
                        name=f"tester_t{turn_index}_3",
                        role=AgentRole.TESTING,
                        refs=(
                            AgentReference(step_index=1, agent_name=f"coder_t{turn_index}_1"),
                            AgentReference(step_index=2, agent_name=f"debugger_t{turn_index}_2"),
                        ),
                    ),
                ),
            ),
        ),
    )


def _hard_revision_topology(turn_index: int, requires_retrieval: bool) -> TopologyPlan:
    step_zero_agents = [AgentInvocation(name=f"planner_t{turn_index}_0", role=AgentRole.PLANNING)]
    if requires_retrieval:
        step_zero_agents.insert(
            0, AgentInvocation(name=f"retrieval_t{turn_index}_0", role=AgentRole.RETRIEVAL)
        )

    step_zero_refs = tuple(
        AgentReference(step_index=0, agent_name=agent.name) for agent in step_zero_agents
    )

    return TopologyPlan(
        difficulty=DifficultyLevel.HARD,
        steps=(
            TopologyStep(index=0, agents=tuple(step_zero_agents)),
            TopologyStep(
                index=1,
                agents=(
                    AgentInvocation(
                        name=f"algorithmic_t{turn_index}_1",
                        role=AgentRole.ALGORITHMIC,
                        refs=step_zero_refs,
                    ),
                    AgentInvocation(
                        name=f"coder_t{turn_index}_1",
                        role=AgentRole.CODING,
                        refs=step_zero_refs,
                    ),
                ),
            ),
            TopologyStep(
                index=2,
                agents=(
                    AgentInvocation(
                        name=f"debugger_t{turn_index}_2",
                        role=AgentRole.DEBUGGING,
                        refs=(
                            AgentReference(step_index=1, agent_name=f"algorithmic_t{turn_index}_1"),
                            AgentReference(step_index=1, agent_name=f"coder_t{turn_index}_1"),
                        ),
                    ),
                ),
            ),
            TopologyStep(
                index=3,
                agents=(
                    AgentInvocation(
                        name=f"tester_t{turn_index}_3",
                        role=AgentRole.TESTING,
                        refs=(
                            AgentReference(step_index=1, agent_name=f"coder_t{turn_index}_1"),
                            AgentReference(step_index=2, agent_name=f"debugger_t{turn_index}_2"),
                        ),
                    ),
                ),
            ),
        ),
    )
