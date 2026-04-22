# AgentConductor API

This document describes the current stable Python API exposed by the repository root package.

The API is still in an early milestone. It currently provides:

- a typed solve entrypoint with deterministic planning and bounded multi-turn execution
- a typed multi-turn solve-state contract that records per-turn history
- a deterministic topology-planning entrypoint
- a single-turn topology-execution entrypoint backed by a local subprocess judge adapter
- typed topology schema objects for single-turn plans
- validation rules for topology structure before execution

The repository now supports a local bounded multi-turn solve loop, but it still
does not implement the paper's full benchmark-grade inference runtime.

## Public Entry Points

Stable callable API:

- `agentconductor.solve_problem`
- `agentconductor.plan_problem_topology`
- `agentconductor.execute_topology_plan`
- `agentconductor.evaluate_candidate_against_benchmark`
- `agentconductor.evaluate_candidate_against_benchmark_record`
- `agentconductor.load_canonical_benchmark_dataset`
- `agentconductor.evaluate_candidate_batch`
- `agentconductor.run_batch_evaluation_entrypoint`
- `agentconductor.generate_sft_dataset_entrypoint`
- `agentconductor.run_sft_baseline_entrypoint`
- `agentconductor.compute_reward_breakdown_entrypoint`
- `agentconductor.run_rl_baseline_entrypoint`

Stable public topology contract:

- `agentconductor.TopologyPlan`
- `agentconductor.TopologyStep`
- `agentconductor.AgentInvocation`
- `agentconductor.AgentReference`
- `agentconductor.AgentRole`
- `agentconductor.TopologyValidationError`

Other public types:

- `agentconductor.AgentExecutionResult`
- `agentconductor.StepExecutionResult`
- `agentconductor.TopologyExecutionResult`
- `agentconductor.BenchmarkAdapter`
- `agentconductor.BenchmarkArtifactIdentifiers`
- `agentconductor.BenchmarkDatasetFormat`
- `agentconductor.BenchmarkDatasetSource`
- `agentconductor.BenchmarkEvaluationResult`
- `agentconductor.BenchmarkEvaluationStatus`
- `agentconductor.BenchmarkExecutionSettings`
- `agentconductor.BenchmarkInvocationMode`
- `agentconductor.BenchmarkProblemDefinition`
- `agentconductor.BenchmarkTestCase`
- `agentconductor.BenchmarkVerdictMapping`
- `agentconductor.CanonicalBenchmarkDataset`
- `agentconductor.CanonicalBenchmarkRecord`
- `agentconductor.DistributedEvaluationBatch`
- `agentconductor.DistributedEvaluationConfig`
- `agentconductor.DistributedEvaluationResult`
- `agentconductor.DistributedEvaluationStatus`
- `agentconductor.DistributedEvaluationTask`
- `agentconductor.EvaluationProblemDefinition`
- `agentconductor.EvaluationProblemResult`
- `agentconductor.EvaluationRunArtifact`
- `agentconductor.EvaluationSummary`
- `agentconductor.ExecutionStatus`
- `agentconductor.RewardBreakdown`
- `agentconductor.TestingOutcome`
- `agentconductor.CodeCandidate`
- `agentconductor.JudgeTestCase`
- `agentconductor.JudgeCaseResult`
- `agentconductor.JudgeResourceLimits`
- `agentconductor.SandboxCapabilityState`
- `agentconductor.SandboxBindingState`
- `agentconductor.SandboxTestSpec`
- `agentconductor.SandboxExecutionResult`
- `agentconductor.SandboxRuntimeCapabilities`
- `agentconductor.PythonSubprocessJudgeAdapter`
- `agentconductor.PythonSubprocessSandboxAdapter`
- `agentconductor.PythonBenchmarkJudgeAdapter`
- `agentconductor.StubBenchmarkAdapter`
- `agentconductor.StubBenchmarkSubmission`
- `agentconductor.TopologyExecutionError`
- `agentconductor.SolveState`
- `agentconductor.SolveTurnRecord`
- `agentconductor.TestingFeedback`
- `agentconductor.TopologyRevisionInput`
- `agentconductor.StopReason`
- `agentconductor.SolveStateTransitionError`
- `agentconductor.ProblemInstance`
- `agentconductor.DifficultyLevel`
- `agentconductor.SolveRequest`
- `agentconductor.SolveResult`
- `agentconductor.SolveStatus`
- `agentconductor.SftTrainingArtifact`
- `agentconductor.SftTrainingConfig`
- `agentconductor.SyntheticTopologySample`
- `agentconductor.RlTrainingArtifact`
- `agentconductor.RlTrainingConfig`

## Installation and Import

From the repository root:

```powershell
uv sync
```

Then import from Python:

```python
from agentconductor import (
    ProblemInstance,
    TopologyPlan,
    execute_topology_plan,
    plan_problem_topology,
    solve_problem,
)
```

## Solve API

### `solve_problem(problem, *, max_turns=None) -> SolveResult`

Plan and execute a structured bounded multi-turn solve for a problem instance.

Parameters:

- `problem: ProblemInstance`
- `max_turns: int | None = None`

Behavior:

- uses the explicit difficulty from `problem` when present
- defaults missing difficulty to `DifficultyLevel.MEDIUM`
- validates the turn budget against the current baseline limit
- generates a deterministic first-turn topology
- executes plan -> evaluate in a bounded loop up to the current turn budget
- consumes typed prior-turn testing feedback when planning a later turn
- returns the final candidate code, role trace, and final testing outcome

Returned `SolveResult` fields:

- `status`
- `selected_difficulty`
- `planned_turns`
- `max_nodes`
- `available_roles`
- `topology`
- `execution`
- `candidate_solution`
- `testing_outcome`
- `solve_state`
- `notes`

Implementation inference:

- the medium-difficulty fallback is an engineering inference until the repository implements the paper's real difficulty inference mechanism
- later-turn revision remains deterministic and repository-local until a learned orchestrator exists

## Multi-Turn Solve-State Contract

The repository now exposes a typed solve-state object so later multi-turn logic
can compose around the current single-turn executor without changing earlier
execution contracts.

### `SolveState`

```python
SolveState(
    problem: ProblemInstance,
    selected_difficulty: DifficultyLevel,
    max_turns: int,
    max_nodes: int,
    available_roles: tuple[str, ...],
    turns: tuple[SolveTurnRecord, ...] = (),
    stop_reason: StopReason | None = None,
)
```

Properties:

- `completed_turns`
- `remaining_turns`
- `can_continue`
- `latest_turn`

### `SolveTurnRecord`

```python
SolveTurnRecord(
    turn_index: int,
    topology: TopologyPlan,
    execution: TopologyExecutionResult,
    testing_feedback: TestingFeedback,
)
```

### `TestingFeedback`

```python
TestingFeedback(
    outcome: TestingOutcome | None,
    diagnostics: tuple[str, ...],
    candidate_code: str | None,
)
```

### `TopologyRevisionInput`

```python
TopologyRevisionInput(
    problem: ProblemInstance,
    selected_difficulty: DifficultyLevel,
    turn_index: int,
    prior_topology: TopologyPlan,
    prior_execution_status: ExecutionStatus,
    testing_feedback: TestingFeedback,
    remaining_turns: int,
)
```

### `StopReason`

Enum values:

- `solved`
- `turn_budget_exhausted`

Implementation inference:

- the paper describes global history and testing feedback, but not a repository-level typed state object
- `TopologyRevisionInput` is a repository-local contract so later revision logic can consume structured prior-turn artifacts instead of raw strings only

## Topology Execution API

### `execute_topology_plan(problem, topology) -> TopologyExecutionResult`

Execute a validated single-turn topology plan layer by layer.

Behavior:

- validates the topology before execution
- executes steps in index order
- resolves references only from prior executed steps
- dispatches each agent through a deterministic role registry
- extracts the last referenced candidate code through an explicit code-candidate contract
- evaluates candidate code through a concrete judge adapter
- returns structured per-agent outputs, final candidate code, judge diagnostics, and final testing outcome

Implementation inference:

- the current role registry uses deterministic non-testing worker handlers, while
  the testing role delegates to a repository-local Python subprocess judge
- the local judge validates a Python `solve()` entrypoint against explicit test
  cases, expected outputs, and explicit resource limits until a fuller benchmark
  integration exists

### Judge Contract

The current judge-facing types are:

- `JudgeTestCase`
  Carries one named invocation, optional positional or keyword arguments, optional stdin text, and expected output or stdout.
- `JudgeCaseResult`
  Carries the typed verdict for one executed case, including pass/fail outcome, diagnostics, and captured actual versus expected outputs.
- `JudgeResourceLimits`
  Carries per-evaluation CPU, wall-clock, and memory limits.
- `SandboxTestSpec`
  Bundles the target entrypoint, concrete test cases, and resource limits into the adapter request.
- `SandboxRuntimeCapabilities`
  Reports the active worker platform, launcher strategy, and typed wall-clock, CPU, and memory enforcement status for the evaluation.

Current benchmark-aligned semantics:

- the judge now returns structured per-case verdicts instead of only a single aggregate outcome
- string comparison normalizes line endings and ignores trailing whitespace at line boundaries, which is closer to common benchmark judge behavior than the earlier full `strip()` comparison
- aggregate outcomes still map into the repository's typed `TestingOutcome` contract
- wall-clock limits are enforced per case at the subprocess boundary instead of only within one long-lived in-process harness
- on Windows, the judge now routes worker launch through a Job Object binding seam and targets hard process-memory limits through `memory_limit_bytes` when the host runtime permits dedicated job assignment
- the sandbox result now carries typed runtime-capability metadata so callers can inspect whether memory binding was attached, downgraded, skipped, or not applicable
- Windows CPU enforcement is now reported explicitly as unsupported until the repository has a verified Job Object CPU strategy

Current fidelity limits:

- the repository judge is still local and Python-only
- entrypoint and invocation semantics are still repository-defined rather than imported from a real benchmark harness
- wall-clock handling is enforced by the subprocess boundary
- POSIX CPU and memory limits use OS-level `resource` controls only on supported platforms
- Windows hard memory enforcement depends on whether the host runtime allows the worker to be rebound into a dedicated Job Object
- when Windows Job Object binding is unavailable, the judge keeps hard wall-clock enforcement and returns explicit platform diagnostics instead of claiming hard memory isolation
- Windows worker launch first attempts `CREATE_BREAKAWAY_FROM_JOB` and falls back to plain subprocess creation only when that strategy is unavailable
- Windows CPU limits are not claimed to be hard-enforced; wall-clock timeout remains the only guaranteed timing control on Windows
- on runtimes without usable OS-level memory controls, memory limits fall back to traced Python allocations and remain approximate
- output normalization is still a repository-level inference rather than a benchmark-specific ruleset
- exact benchmark-specific semantics, datasets, and multi-language support are still out of scope for this milestone

## Benchmark Adapter API

### `evaluate_candidate_against_benchmark(problem, candidate, settings, *, adapter) -> BenchmarkEvaluationResult`

Evaluate one extracted candidate through a typed external benchmark boundary.

Parameters:

- `problem: BenchmarkProblemDefinition`
- `candidate: CodeCandidate`
- `settings: BenchmarkExecutionSettings`
- `adapter: BenchmarkAdapter`

Behavior:

- keeps benchmark problem metadata, execution settings, verdict mapping, and artifact identifiers in explicit typed contracts
- keeps the external benchmark seam distinct from the repository-local subprocess judge
- validates candidate language against the requested benchmark execution language before dispatch
- returns a normalized repository `TestingOutcome` only through `BenchmarkVerdictMapping`, so core services do not consume benchmark-native payloads directly

Key benchmark-facing types:

- `BenchmarkProblemDefinition`
  Canonical benchmark metadata including `benchmark_name`, `dataset_name`, `source_problem_id`, optional `split_name`, repository-facing `identifier`, `prompt`, and `language`.
- `BenchmarkExecutionSettings`
  External-harness execution settings such as `language`, invocation mode, entrypoint, and benchmark-owned resource limits.
- `BenchmarkTestCase`
  Benchmark-owned cases expressed independently from the repository-local judge payload types.
- `BenchmarkVerdictMapping`
  Normalized mapping from a benchmark-native verdict string into repository `TestingOutcome`.
- `BenchmarkArtifactIdentifiers`
  Typed identifiers for benchmark-side run artifacts such as `run_id`, `submission_id`, and optional result or log URIs.
- `BenchmarkEvaluationResult`
  Adapter result containing adapter status, normalized verdict mapping, typed diagnostics, and optional artifact identifiers.

Current scope and limits:

- the repository now exposes a typed benchmark adapter seam plus one canonical dataset-ingestion path for APPS-style JSONL artifacts
- the included `StubBenchmarkAdapter` is only for contract verification and fixture-driven tests
- the local subprocess judge remains the explicit development fallback for current solve execution
- the repository now includes a concrete Python-first benchmark execution adapter, but it still remains a local harness rather than a remote benchmark service

### `load_canonical_benchmark_dataset(dataset_path, *, source_format=BenchmarkDatasetFormat.APPS_JSONL) -> CanonicalBenchmarkDataset`

Load one supported external benchmark dataset artifact into canonical problem records.

Parameters:

- `dataset_path: str | Path`
- `source_format: BenchmarkDatasetFormat = BenchmarkDatasetFormat.APPS_JSONL`

Behavior:

- keeps source-layout parsing behind a typed dataset format selector instead of leaking vendor-specific keys into solve services
- normalizes supported source records into canonical `BenchmarkProblemDefinition` objects
- normalizes benchmark execution payloads into `CanonicalBenchmarkRecord` entries with explicit `BenchmarkExecutionSettings` and benchmark-owned `BenchmarkTestCase` values when the source row contains executable metadata
- preserves repository-facing `identifier`, source `problem_id`, benchmark `split_name`, prompt text, language, and optional difficulty
- returns dataset-level provenance through `BenchmarkDatasetSource`
- records normalization assumptions through `CanonicalBenchmarkDataset.normalization_notes`

Current supported dataset format:

- `BenchmarkDatasetFormat.APPS_JSONL`
  Expects one JSON object per line with `problem_id`, `question`, and `split`.
  Optional fields: `difficulty`, `language`.

Current normalization rules:

- canonical identifiers are built as `apps/<split>/<problem_id>`
- split names are normalized to lowercase `train` or `test`
- prompt text converts CRLF or CR line endings to LF and trims trailing whitespace at line boundaries
- when `input_output` metadata is present, APPS `fn_name` selects function invocation and otherwise the loader normalizes the record as stdin-style execution
- APPS difficulty labels are mapped into repository tiers as an implementation inference:
  `introductory -> easy`, `interview -> medium`, `competition -> hard`

Current scope and limits:

- only APPS-style JSONL ingestion is wired in this milestone
- the repository does not bundle benchmark payloads and assumes the caller has legitimate local access to the source artifact
- some APPS rows may still load as metadata-only records when they do not include executable `input_output` payloads
- benchmark-specific leaderboard reporting and non-Python runtime support remain later milestones

### `evaluate_candidate_against_benchmark_record(record, candidate, *, adapter) -> BenchmarkEvaluationResult`

Evaluate one candidate against a canonical benchmark dataset record that already
contains benchmark-owned invocation settings and test cases.

Parameters:

- `record: CanonicalBenchmarkRecord`
- `candidate: CodeCandidate`
- `adapter: BenchmarkAdapter`

Behavior:

- dispatches through the benchmark adapter boundary using the record's own `BenchmarkExecutionSettings`
- preserves the distinction between metadata-only canonical records and executable records with benchmark-owned test cases
- allows benchmark execution to consume the canonical dataset layer directly instead of rebuilding ad hoc test specs outside the adapter seam

Current concrete Python path:

- `PythonBenchmarkJudgeAdapter`
  Uses the repository's subprocess sandbox as the worker runtime, but evaluates
  through benchmark-owned `BenchmarkTestCase` values and emits benchmark-style
  verdict strings such as `accepted` and `wrong_answer`.

Current fidelity limits:

- function-style invocation is closest to benchmark semantics when `fn_name` is available
- stdin-style execution still calls a repository-owned `solve()` function that reads from `stdin` instead of executing an unrestricted script entrypoint
- artifact capture is local and file-based rather than vendor-native

## Topology Planning API

### `plan_problem_topology(problem) -> TopologyPlan`

Return a deterministic topology plan for a problem instance.

Behavior:

- uses the explicit problem difficulty when present
- defaults missing difficulty to `DifficultyLevel.MEDIUM`
- infers a coarse local problem shape from prompt keywords
- selects one of a small set of topology templates
- returns a validated single-turn `TopologyPlan`

Implementation inference:

- prompt-shape inference is a repository-local heuristic, not a paper-defined mechanism
- the current orchestrator is deterministic and local so it can later be replaced by a learned policy

## Distributed Evaluation API

### `evaluate_candidate_batch(tasks, *, config=None, orchestrator=None) -> DistributedEvaluationBatch`

Evaluate multiple candidate solutions through an orchestration boundary that
keeps submission, worker execution, and collection separate from judge logic.

Behavior:

- preserves task ordering in the collected batch result
- supports explicit `max_workers`, `max_retries`, and `collection_timeout_seconds`
- keeps `max_workers=1` as the local single-worker fallback path
- returns typed per-task statuses plus the underlying `SandboxExecutionResult` when available

## Batch Evaluation API

### `run_batch_evaluation_entrypoint(dataset_path, output_path, *, max_workers=1) -> EvaluationRunArtifact`

Run the current solve-and-judge stack over a JSON dataset and write a JSON
artifact containing per-problem outcomes and an aggregate summary.

Dataset format:

- top-level object with a non-empty `problems` list
- each problem must define `identifier` and `prompt`
- `difficulty` is optional and must be `easy`, `medium`, or `hard` when present

## SFT Baseline API

### `generate_sft_dataset_entrypoint(dataset_path) -> tuple[SyntheticTopologySample, ...]`

Generate a deterministic JSONL dataset of schema-valid topology targets derived
from the current rule-based orchestrator.

### `run_sft_baseline_entrypoint(dataset_path, artifact_path, *, epochs=1, learning_rate=1e-4, seed=0) -> SftTrainingArtifact`

Validate the generated dataset and write a reproducible baseline artifact for
the repository-local SFT stage.

Implementation inference:

- this stage materializes structured training data and configuration artifacts
  but does not fine-tune the paper's full orchestrator backbone

## RL Baseline API

### `compute_reward_breakdown_entrypoint(topology, *, yaml_valid, execution_outcome) -> RewardBreakdown`

Compute a repository-local reward breakdown from YAML validity, execution
outcome, and topology-density signals.

### `run_rl_baseline_entrypoint(dataset_path, artifact_path, *, rollouts=1, seed=0) -> RlTrainingArtifact`

Run a deterministic rollout loop over the SFT dataset and write per-rollout
reward breakdowns plus an aggregate artifact.

Implementation inference:

- this baseline reproduces the reward structure in a local, inspectable form
  but does not claim to implement full GRPO optimization

## Topology Schema

### `TopologyPlan`

```python
TopologyPlan(
    difficulty: DifficultyLevel,
    steps: tuple[TopologyStep, ...],
)
```

Current scope:

- single-turn topology only
- layered DAG structure
- dependency-free parsing from plain mappings via `TopologyPlan.from_mapping(...)`

Properties:

- `node_count`
- `max_nodes`

Methods:

- `validate() -> None`
- `from_mapping(raw_plan: Mapping[str, Any]) -> TopologyPlan`

### `TopologyStep`

```python
TopologyStep(
    index: int,
    agents: tuple[AgentInvocation, ...],
)
```

### `AgentInvocation`

```python
AgentInvocation(
    name: str,
    role: AgentRole,
    refs: tuple[AgentReference, ...] = (),
)
```

### `AgentReference`

```python
AgentReference(
    step_index: int,
    agent_name: str,
)
```

### `AgentRole`

Enum values:

- `retrieval`
- `planning`
- `algorithmic`
- `coding`
- `debugging`
- `testing`

## Validation Rules

The current topology validator enforces these constraints:

- the plan must contain at least one step
- step indices must be contiguous and zero-based
- every step must contain at least one agent
- agent names must be unique across the full topology
- the first step must not contain references
- references may target earlier steps only
- references must point to known prior agent names
- the final step must contain a testing agent
- the total node count must stay within the paper-derived difficulty budget

Difficulty-specific node budgets:

- `easy`: `4`
- `medium`: `7`
- `hard`: `10`

Implementation inference:

- the paper does not define a full concrete schema; `from_mapping(...)` is a repository-local parsing contract used until a YAML adapter is added

## Topology Parsing Example

```python
from agentconductor import TopologyPlan

plan = TopologyPlan.from_mapping(
    {
        "difficulty": "easy",
        "steps": [
            {
                "index": 0,
                "agents": [
                    {"name": "planner_0", "role": "planning", "refs": []},
                ],
            },
            {
                "index": 1,
                "agents": [
                    {
                        "name": "coder_1",
                        "role": "coding",
                        "refs": [{"step_index": 0, "agent_name": "planner_0"}],
                    },
                ],
            },
            {
                "index": 2,
                "agents": [
                    {
                        "name": "tester_2",
                        "role": "testing",
                        "refs": [
                            {"step_index": 0, "agent_name": "planner_0"},
                            {"step_index": 1, "agent_name": "coder_1"},
                        ],
                    },
                ],
            },
        ],
    }
)
```

## Current Limits

The repository currently does not:

- generate topology YAML from an orchestrator

It currently does:

- expose typed topology contracts
- expose typed multi-turn state and revision-input contracts
- parse single-turn topologies from plain mappings
- validate paper-aligned topology structure
- emit deterministic topology plans for supported difficulty tiers
- emit deterministic revised topologies from prior-turn feedback
- execute single-turn topologies with a local judge-backed testing role
- run a bounded multi-turn solve loop with early stop on pass
- return candidate code and structured execution traces from `solve_problem(...)`

## Source References

Implementation files:

- [src/agentconductor/domain/topology.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/domain/topology.py)
- [src/agentconductor/application/orchestrator.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/application/orchestrator.py)
- [src/agentconductor/interfaces/planning.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/interfaces/planning.py)
- [src/agentconductor/interfaces/api.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/interfaces/api.py)
- [src/agentconductor/application/api.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/application/api.py)
- [src/agentconductor/application/execution.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/application/execution.py)
- [src/agentconductor/application/history.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/application/history.py)
- [src/agentconductor/domain/history.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/domain/history.py)
- [src/agentconductor/domain/models.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/domain/models.py)
- [src/agentconductor/infrastructure/sandbox.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/infrastructure/sandbox.py)
