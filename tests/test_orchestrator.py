from agentconductor import (
    DifficultyLevel,
    ProblemInstance,
    generate_sft_dataset_entrypoint,
    TopologyCandidateExtractionError,
    TopologyLogicError,
    plan_problem_topology,
    plan_problem_topology_candidate,
    revise_problem_topology_candidate,
    run_sft_baseline_entrypoint,
)
from agentconductor.application.orchestrator import (
    ProblemShape,
    build_orchestrator_prompt,
    extract_topology_yaml_candidate,
    infer_problem_shape,
    revise_topology_for_feedback,
)
from agentconductor.domain.execution import ExecutionStatus, TestingOutcome
from agentconductor.domain.history import TestingFeedback, TopologyRevisionInput
from agentconductor.domain.orchestration import OrchestratorPromptRequest, TopologyPromptKind
from agentconductor.domain.topology import AgentRole
import pytest


class StubTopologyPolicy:
    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self.prompts: list[str] = []
        self.requests: list[OrchestratorPromptRequest] = []

    def generate_topology_candidate(
        self,
        *,
        prompt: str,
        request: OrchestratorPromptRequest,
    ) -> str:
        self.prompts.append(prompt)
        self.requests.append(request)
        return self._responses[len(self.prompts) - 1]


def test_plan_problem_topology_returns_easy_template() -> None:
    plan = plan_problem_topology(
        ProblemInstance(
            identifier="easy-sum",
            prompt="Return the sum of two integers.",
            difficulty=DifficultyLevel.EASY,
        )
    )

    assert plan.difficulty is DifficultyLevel.EASY
    assert len(plan.steps) == 3
    assert plan.steps[0].agents[0].role is AgentRole.PLANNING
    assert plan.steps[1].agents[0].role is AgentRole.CODING
    assert plan.steps[2].agents[0].role is AgentRole.TESTING


def test_plan_problem_topology_uses_knowledge_intensive_medium_template() -> None:
    plan = plan_problem_topology(
        ProblemInstance(
            identifier="medium-graph",
            prompt="Solve a graph shortest path problem under tight constraints.",
            difficulty=DifficultyLevel.MEDIUM,
        )
    )

    assert plan.difficulty is DifficultyLevel.MEDIUM
    assert infer_problem_shape(
        ProblemInstance(identifier="shape-check", prompt="graph shortest path")
    ) is ProblemShape.KNOWLEDGE_INTENSIVE
    assert plan.steps[0].agents[0].role is AgentRole.RETRIEVAL
    assert plan.steps[0].agents[1].role is AgentRole.PLANNING
    assert plan.steps[1].agents[0].role is AgentRole.ALGORITHMIC
    assert plan.steps[2].agents[0].role is AgentRole.TESTING


def test_plan_problem_topology_uses_debugging_shape_when_keywords_match() -> None:
    plan = plan_problem_topology(
        ProblemInstance(
            identifier="medium-debug",
            prompt="Fix the failing implementation and debug the incorrect output.",
            difficulty=DifficultyLevel.MEDIUM,
        )
    )

    assert infer_problem_shape(
        ProblemInstance(identifier="shape-debug", prompt="debug this broken code")
    ) is ProblemShape.DEBUGGING
    assert plan.steps[1].agents[0].role is AgentRole.DEBUGGING
    assert plan.steps[1].agents[1].role is AgentRole.CODING
    assert plan.steps[2].agents[0].role is AgentRole.TESTING


def test_plan_problem_topology_returns_valid_hard_template() -> None:
    plan = plan_problem_topology(
        ProblemInstance(
            identifier="hard-dp",
            prompt="Solve a dynamic programming problem with multiple constraints.",
            difficulty=DifficultyLevel.HARD,
        )
    )

    assert plan.difficulty is DifficultyLevel.HARD
    assert len(plan.steps) == 3
    assert plan.node_count <= plan.max_nodes
    assert plan.steps[0].agents[0].role is AgentRole.RETRIEVAL
    assert plan.steps[1].agents[0].role is AgentRole.ALGORITHMIC
    assert plan.steps[1].agents[1].role is AgentRole.CODING
    assert plan.steps[2].agents[0].role is AgentRole.TESTING


def test_plan_problem_topology_defaults_missing_difficulty_to_medium() -> None:
    plan = plan_problem_topology(
        ProblemInstance(
            identifier="default-medium",
            prompt="Implement a correct solution for this problem.",
        )
    )

    assert plan.difficulty is DifficultyLevel.MEDIUM


def test_revise_topology_for_feedback_adds_debugging_turn_for_failed_medium_problem() -> None:
    problem = ProblemInstance(
        identifier="medium-revise",
        prompt="Solve a graph shortest path problem under tight constraints.",
        difficulty=DifficultyLevel.MEDIUM,
    )

    revised = revise_topology_for_feedback(
        TopologyRevisionInput(
            problem=problem,
            selected_difficulty=DifficultyLevel.MEDIUM,
            turn_index=1,
            prior_topology=plan_problem_topology(problem),
            prior_execution_status=ExecutionStatus.COMPLETED,
            testing_feedback=TestingFeedback(
                outcome=TestingOutcome.FAILED,
                diagnostics=("Wrong answer on graph constraint edge case.",),
                candidate_code="def solve():\n    pass\n",
            ),
            remaining_turns=1,
        )
    )

    assert revised.difficulty is DifficultyLevel.MEDIUM
    assert len(revised.steps) == 4
    assert revised.steps[0].agents[0].role is AgentRole.RETRIEVAL
    assert revised.steps[2].agents[0].role is AgentRole.DEBUGGING
    assert revised.steps[3].agents[0].role is AgentRole.TESTING
    assert revised.steps[3].agents[0].refs[-1].agent_name == "debugger_t1_2"


def test_plan_problem_topology_candidate_parses_yaml_from_policy_response() -> None:
    policy = StubTopologyPolicy(
        [
            """```yaml
difficulty: medium
steps:
  - index: 0
    agents:
      - name: planner_0
        role: planning
        refs: []
  - index: 1
    agents:
      - name: coder_1
        role: coding
        refs:
          - step_index: 0
            agent_name: planner_0
  - index: 2
    agents:
      - name: tester_2
        role: testing
        refs:
          - step_index: 1
            agent_name: coder_1
```"""
        ]
    )

    candidate = plan_problem_topology_candidate(
        ProblemInstance(
            identifier="policy-medium",
            prompt="Implement a correct solution.",
            difficulty=DifficultyLevel.MEDIUM,
        ),
        orchestrator_policy=policy,
    )

    assert candidate.kind is TopologyPromptKind.INITIAL
    assert candidate.attempt_count == 1
    assert candidate.topology.difficulty is DifficultyLevel.MEDIUM
    assert candidate.topology.steps[0].agents[0].role is AgentRole.PLANNING
    assert candidate.topology_yaml.startswith("difficulty: medium\n")
    assert "Problem id: policy-medium" in policy.prompts[0]
    assert policy.requests[0].kind is TopologyPromptKind.INITIAL


def test_plan_problem_topology_candidate_can_load_checkpoint_artifact(
    tmp_path,
) -> None:
    dataset_path = tmp_path / "sft-dataset.jsonl"
    artifact_path = tmp_path / "sft-run.json"
    generate_sft_dataset_entrypoint(dataset_path)
    run_sft_baseline_entrypoint(dataset_path, artifact_path)

    candidate = plan_problem_topology_candidate(
        ProblemInstance(
            identifier="policy-checkpoint",
            prompt="Implement a correct solution.",
            difficulty=DifficultyLevel.EASY,
        ),
        orchestrator_checkpoint=artifact_path,
    )

    assert candidate.kind is TopologyPromptKind.INITIAL
    assert candidate.topology.difficulty is DifficultyLevel.EASY
    assert candidate.topology_yaml.startswith("difficulty: easy\n")


def test_revise_problem_topology_candidate_retries_and_surfaces_last_validation_error() -> None:
    problem = ProblemInstance(
        identifier="retry-medium",
        prompt="Fix the failing implementation.",
        difficulty=DifficultyLevel.MEDIUM,
    )
    revision = TopologyRevisionInput(
        problem=problem,
        selected_difficulty=DifficultyLevel.MEDIUM,
        turn_index=1,
        prior_topology=plan_problem_topology(problem),
        prior_execution_status=ExecutionStatus.COMPLETED,
        testing_feedback=TestingFeedback(
            outcome=TestingOutcome.FAILED,
            diagnostics=("Wrong answer on sample.",),
            candidate_code="def solve():\n    return 'wrong'\n",
        ),
        remaining_turns=1,
    )
    policy = StubTopologyPolicy(
        [
            "I think this should work.",
            """difficulty: medium
steps:
  - index: 0
    agents:
      - name: planner_t1_0
        role: planning
        refs: []
""",
        ]
    )

    with pytest.raises(
        TopologyLogicError,
        match="final step must contain a testing agent",
    ):
        revise_problem_topology_candidate(
            revision,
            orchestrator_policy=policy,
            orchestrator_max_attempts=2,
        )

    assert len(policy.prompts) == 2
    assert "The previous candidate was rejected." in policy.prompts[1]
    assert "TopologyCandidateExtractionError" in policy.prompts[1]
    assert policy.requests[1].kind is TopologyPromptKind.REVISION


def test_extract_topology_yaml_candidate_rejects_missing_yaml_block() -> None:
    with pytest.raises(
        TopologyCandidateExtractionError,
        match="did not contain a repository topology YAML block",
    ):
        extract_topology_yaml_candidate("No YAML here.")


def test_build_orchestrator_prompt_includes_prior_feedback_for_revision() -> None:
    revision_prompt = build_orchestrator_prompt(
        OrchestratorPromptRequest(
            kind=TopologyPromptKind.REVISION,
            problem=ProblemInstance(
                identifier="prompt-check",
                prompt="Fix the broken implementation.",
                difficulty=DifficultyLevel.EASY,
            ),
            selected_difficulty=DifficultyLevel.EASY,
            turn_index=1,
            prior_topology=plan_problem_topology(
                ProblemInstance(
                    identifier="prompt-check",
                    prompt="Fix the broken implementation.",
                    difficulty=DifficultyLevel.EASY,
                )
            ),
            testing_feedback=TestingFeedback(
                outcome=TestingOutcome.FAILED,
                diagnostics=("Wrong answer on edge case.",),
                candidate_code="def solve():\n    return 0\n",
            ),
            remaining_turns=1,
            last_error="TopologyLogicError: final step must contain a testing agent",
        )
    )

    assert "Planning kind: revision" in revision_prompt
    assert "Prior topology YAML:" in revision_prompt
    assert "Wrong answer on edge case." in revision_prompt
    assert "TopologyLogicError: final step must contain a testing agent" in revision_prompt
