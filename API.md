# AgentConductor API

This document describes the current stable Python API exposed by the repository root package.

The API is still in an early milestone. It currently provides:

- a typed solve entrypoint with bounded multi-turn execution over explicit orchestrator modes
- a typed multi-turn solve-state contract that records per-turn history
- deterministic and learned-policy topology-planning entrypoints
- a single-turn topology-execution entrypoint whose non-testing worker roles can run through a model-backed runtime seam and whose testing role is backed by a local subprocess judge adapter
- typed topology schema objects for single-turn plans
- validation rules for topology structure before execution

The repository now supports a local bounded multi-turn solve loop, but it still
does not implement the paper's full benchmark-grade inference runtime.

## Public Entry Points

Stable callable API:

- `agentconductor.solve_problem`
- `agentconductor.plan_problem_topology`
- `agentconductor.plan_problem_topology_candidate`
- `agentconductor.revise_problem_topology_candidate`
- `agentconductor.execute_topology_plan`
- `agentconductor.serialize_topology_plan_to_yaml`
- `agentconductor.parse_topology_plan_yaml`
- `agentconductor.evaluate_candidate_against_benchmark`
- `agentconductor.evaluate_candidate_against_benchmark_record`
- `agentconductor.load_canonical_benchmark_dataset`
- `agentconductor.evaluate_candidate_batch`
- `agentconductor.run_benchmark_evaluation_entrypoint`
- `agentconductor.run_batch_evaluation_entrypoint`
- `agentconductor.build_reproduction_audit`
- `agentconductor.write_reproduction_audit`
- `agentconductor.write_reproduction_audit_entrypoint`
- `agentconductor.generate_sft_dataset_entrypoint`
- `agentconductor.load_sft_checkpoint_entrypoint`
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
- `agentconductor.TopologySchemaError`
- `agentconductor.TopologyLogicError`

Other public types:

- `agentconductor.AgentExecutionResult`
- `agentconductor.StepExecutionResult`
- `agentconductor.TopologyExecutionResult`
- `agentconductor.BenchmarkAdapter`
- `agentconductor.BenchmarkArtifactIdentifiers`
- `agentconductor.BenchmarkDatasetFormat`
- `agentconductor.BenchmarkDatasetSource`
- `agentconductor.BenchmarkExecutionPhase`
- `agentconductor.BenchmarkEvaluationResult`
- `agentconductor.BenchmarkEvaluationStatus`
- `agentconductor.BenchmarkExecutionSettings`
- `agentconductor.BenchmarkInvocationMode`
- `agentconductor.BenchmarkPhaseArtifactIdentifiers`
- `agentconductor.BenchmarkPhaseExecutionSettings`
- `agentconductor.BenchmarkPhaseResourceLimits`
- `agentconductor.BenchmarkPhaseResult`
- `agentconductor.BenchmarkPhaseStatus`
- `agentconductor.BenchmarkProblemDefinition`
- `agentconductor.BenchmarkRuntimeMode`
- `agentconductor.BenchmarkTestCase`
- `agentconductor.BenchmarkVerdictMapping`
- `agentconductor.BenchmarkVendorPollSnapshot`
- `agentconductor.BenchmarkVendorSubmissionReceipt`
- `agentconductor.BenchmarkVendorSubmissionState`
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
- `agentconductor.EvaluationRunMetadata`
- `agentconductor.EvaluationSummary`
- `agentconductor.ReproductionAudit`
- `agentconductor.ReproductionChecklistItem`
- `agentconductor.ReproductionClaim`
- `agentconductor.ReproductionStatus`
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
- `agentconductor.NodeJsBenchmarkJudgeAdapter`
- `agentconductor.CppBenchmarkJudgeAdapter`
- `agentconductor.JavaBenchmarkJudgeAdapter`
- `agentconductor.PythonBenchmarkJudgeAdapter`
- `agentconductor.MultiLanguageBenchmarkJudgeAdapter`
- `agentconductor.StubBenchmarkAdapter`
- `agentconductor.StubBenchmarkSubmission`
- `agentconductor.StubVendorNativeBenchmarkAdapter`
- `agentconductor.StubVendorSubmissionScenario`
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
- `agentconductor.LearnedTopologyPlan`
- `agentconductor.OrchestratorCheckpointMetadata`
- `agentconductor.OrchestratorCheckpointError`
- `agentconductor.OrchestratorCheckpointSelectionError`
- `agentconductor.OrchestratorCheckpointLoadError`
- `agentconductor.OrchestratorMode`
- `agentconductor.OrchestratorPromptRequest`
- `agentconductor.TopologyOrchestratorPolicy`
- `agentconductor.TopologyPromptKind`
- `agentconductor.TopologyCandidateExtractionError`
- `agentconductor.SftTrainingArtifact`
- `agentconductor.SftTrainingConfig`
- `agentconductor.SyntheticTopologySample`
- `agentconductor.RlTrainingArtifact`
- `agentconductor.RlTrainingConfig`
- `agentconductor.RepositoryFrozenOrchestratorBundle`
- `agentconductor.RepositoryFrozenOrchestratorRuntime`
- `agentconductor.RepositoryWorkerModelRuntime`
- `agentconductor.WorkerGenerationRequest`
- `agentconductor.WorkerGenerationResult`
- `agentconductor.WorkerRoleRuntime`
- `agentconductor.WorkerRuntimeError`

## Installation and Import

From the repository root:

```powershell
uv sync
```

Then import from Python:

```python
from agentconductor import (
    LearnedTopologyPlan,
    parse_topology_plan_yaml,
    ProblemInstance,
    TopologyOrchestratorPolicy,
    TopologyPlan,
    execute_topology_plan,
    plan_problem_topology,
    plan_problem_topology_candidate,
    serialize_topology_plan_to_yaml,
    solve_problem,
)
```

## Solve API

### `solve_problem(problem, *, max_turns=None, orchestrator_policy=None, orchestrator_checkpoint=None, orchestrator_checkpoint_id=None, orchestrator_device="cpu", orchestrator_max_attempts=1, worker_runtime=None) -> SolveResult`

Plan and execute a structured bounded multi-turn solve for a problem instance.

Parameters:

- `problem: ProblemInstance`
- `max_turns: int | None = None`
- `orchestrator_policy: TopologyOrchestratorPolicy | None = None`
- `orchestrator_checkpoint: str | Path | None = None`
- `orchestrator_checkpoint_id: str | None = None`
- `orchestrator_device: str = "cpu"`
- `orchestrator_max_attempts: int = 1`
- `worker_runtime: WorkerRoleRuntime | None = None`

Behavior:

- uses the explicit difficulty from `problem` when present
- defaults missing difficulty to `DifficultyLevel.MEDIUM`
- validates the turn budget against the current baseline limit
- uses deterministic planning when no orchestrator policy is provided
- uses the learned YAML planning path when `orchestrator_policy` is provided
- can also resolve the learned YAML planning path from explicit checkpoint
  metadata when `orchestrator_checkpoint` is provided
- executes plan -> evaluate in a bounded loop up to the current turn budget
- consumes typed prior-turn testing feedback when planning a later turn
- routes non-testing worker roles through the provided `worker_runtime` or the default repository-local model-backed worker runtime
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
- deterministic planning remains the repository-local fallback when no learned policy is configured
- the current checkpoint-backed frozen path loads a repository-local runtime
  bundle from checkpoint metadata, with explicit load failures for missing
  runtime artifacts, unsupported devices, or incompatible prompt templates

The `notes` field records which orchestrator mode produced the final topology
and, when relevant, which checkpoint-backed runtime was selected.

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

### `execute_topology_plan(problem, topology, *, sandbox=None, worker_runtime=None) -> TopologyExecutionResult`

Execute a validated single-turn topology plan layer by layer.

Behavior:

- validates the topology before execution
- executes steps in index order
- resolves references only from prior executed steps
- dispatches each non-testing agent through a model-backed worker runtime seam
- extracts the last referenced candidate code through an explicit code-candidate contract
- evaluates candidate code through a concrete judge adapter
- returns structured per-agent outputs, final candidate code, judge diagnostics, and final testing outcome

Implementation inference:

- the current default worker runtime is `RepositoryWorkerModelRuntime`, which
  records runtime and model identifiers per agent while remaining a
  repository-local substitute for real `gpt-4o-mini` execution
- the testing role delegates to a repository-local Python subprocess judge
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
  External-harness execution settings such as `language`, invocation mode,
  entrypoint, benchmark-owned resource limits, optional compile or run phase
  settings, and explicit runtime mode.
- `BenchmarkPhaseExecutionSettings`
  One benchmark-owned compile or run phase with explicit `source_layout`,
  `command`, optional `executable_target`, and `resource_limits`.
- `BenchmarkPhaseResourceLimits`
  Phase-specific time and memory limits for compile or run phases.
- `BenchmarkTestCase`
  Benchmark-owned cases expressed independently from the repository-local judge payload types.
- `BenchmarkVerdictMapping`
  Normalized mapping from a benchmark-native verdict string into repository `TestingOutcome`.
- `BenchmarkArtifactIdentifiers`
  Typed identifiers for benchmark-side run artifacts such as `run_id`,
  `submission_id`, optional result or log URIs, and per-phase artifact ids.
- `BenchmarkPhaseArtifactIdentifiers`
  Typed artifact ids for one compile or run phase.
- `BenchmarkPhaseResult`
  Typed per-phase diagnostics that keep compile failures and run-time failures
  distinct.
- `BenchmarkVendorSubmissionReceipt`
  Typed submission metadata for vendor-native runtimes.
- `BenchmarkVendorPollSnapshot`
  One observed vendor-native poll state, including terminal verdict when known.
- `BenchmarkEvaluationResult`
  Adapter result containing adapter status, runtime mode, normalized verdict
  mapping, typed diagnostics, optional artifact identifiers, optional
  per-phase results, and optional vendor submission lifecycle metadata.

Current scope and limits:

- the repository now exposes a typed benchmark adapter seam plus one canonical dataset-ingestion path for APPS-style JSONL artifacts
- the included `StubBenchmarkAdapter` is only for contract verification and fixture-driven tests
- the local subprocess judge remains the explicit development fallback for current solve execution
- the repository now includes concrete Python, Node.js, and Java benchmark execution adapters plus a multi-language dispatch adapter, and it also exposes a separate stubbed vendor-native runtime boundary for submission-lifecycle verification

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
- the first compiled-language local harness is now Java-first and stdin-oriented; wider compiled-language coverage still depends on host toolchain availability

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

Current concrete benchmark paths:

- `PythonBenchmarkJudgeAdapter`
  Uses the repository's subprocess sandbox for function-style Python cases and a
  standalone script path for stdin-style Python cases.
- `NodeJsBenchmarkJudgeAdapter`
  Evaluates JavaScript benchmark records through local Node.js execution and
  emits benchmark-style verdict strings such as `accepted` and
  `compilation_error`.
- `JavaBenchmarkJudgeAdapter`
  Compiles and executes stdin-style Java benchmark records through local
  `javac` plus `java`, while preserving compile-phase and run-phase artifacts.
- `CppBenchmarkJudgeAdapter`
  Uses the same compile-then-run benchmark seam for C++ records and reports an
  explicit adapter error when the required compiler is unavailable.
- `MultiLanguageBenchmarkJudgeAdapter`
  Dispatches to the configured Python, Node.js, C++, or Java benchmark harness based on the
  canonical record's `BenchmarkExecutionSettings.language`.
- `StubVendorNativeBenchmarkAdapter`
  Exercises a vendor-native benchmark lifecycle through typed submission
  receipts, poll history, terminal verdict mapping, and artifact provenance
  without requiring a live external service.

Current fidelity limits:

- Python and JavaScript function-style invocation is closest to benchmark semantics when `fn_name` is available
- stdin-style Python and JavaScript execution now runs the candidate as a standalone script with benchmark-owned stdin payloads
- stdin-style Java execution now runs through a local compile-then-run harness
  when `javac` and `java` are available
- the JavaScript function path expects a CommonJS export and adds a repository-local compatibility shim for top-level `solve(...)` definitions
- local compiled-language coverage is still incomplete: Java is the first
  repository-local compiled harness, while C++ depends on host-local `g++`
  availability and currently has no bundled fallback toolchain
- local harness artifact capture is file-based and now also preserves typed
  per-phase compile or run artifact identifiers
- real vendor-native integrations still depend on external authentication,
  licensing, and service availability; the repository currently verifies that
  boundary through a fixture-driven stub
- benchmark-specific output normalization rules and compiled-language local
  harnesses remain later milestones

## Topology Planning API

### `plan_problem_topology(problem, *, orchestrator_policy=None, orchestrator_checkpoint=None, orchestrator_checkpoint_id=None, orchestrator_device="cpu", orchestrator_max_attempts=1) -> TopologyPlan`

Return a validated topology plan for a problem instance.

Behavior:

- uses the explicit problem difficulty when present
- defaults missing difficulty to `DifficultyLevel.MEDIUM`
- infers a coarse local problem shape from prompt keywords
- selects one of a small set of topology templates when no policy is provided
- otherwise routes through the learned YAML planning boundary and validates the parsed result
- can load that learned planning boundary from explicit checkpoint metadata
- returns a validated single-turn `TopologyPlan`

Implementation inference:

- prompt-shape inference is a repository-local heuristic, not a paper-defined mechanism
- deterministic planning remains the local fallback so tests and offline callers do not require a model checkpoint

### `plan_problem_topology_candidate(problem, *, orchestrator_policy=None, orchestrator_checkpoint=None, orchestrator_checkpoint_id=None, orchestrator_device="cpu", orchestrator_max_attempts=1) -> LearnedTopologyPlan`

Return the raw learned-policy YAML candidate plus its parsed topology.

Behavior:

- constructs an explicit first-turn prompt from the problem and selected difficulty
- calls the provided policy, or a checkpoint-backed loaded policy, through the
  narrow `TopologyOrchestratorPolicy` boundary
- extracts one repository YAML document from the raw response
- parses the YAML through the existing transport and topology-validation path
- retries failed extraction or validation attempts up to `orchestrator_max_attempts`

### `revise_problem_topology_candidate(revision, *, orchestrator_policy=None, orchestrator_checkpoint=None, orchestrator_checkpoint_id=None, orchestrator_device="cpu", orchestrator_max_attempts=1) -> LearnedTopologyPlan`

Return the raw learned-policy revised YAML candidate plus its parsed topology.

Behavior:

- consumes the existing `TopologyRevisionInput` contract rather than raw strings
- includes prior topology YAML and testing feedback in the explicit revision prompt
- uses the same extraction, parsing, and retry path as first-turn planning,
  including the same checkpoint-backed policy path when configured

## Learned Orchestrator Contract

### `TopologyOrchestratorPolicy`

Policies must implement:

```python
def generate_topology_candidate(
    self,
    *,
    prompt: str,
    request: OrchestratorPromptRequest,
) -> str: ...
```

Repository-local mock policies are still supported for tests, but checkpoint
loading now also supports a repository-local frozen runtime bundle that
materializes topology YAML candidates from serialized checkpoint state.

Checkpoint-backed frozen inference keeps explicit failure boundaries:

- invalid checkpoint source selection raises `OrchestratorCheckpointSelectionError`
- incompatible checkpoint metadata or missing runtime artifacts raises
  `OrchestratorCheckpointLoadError`
- there is no silent fallback to the deterministic planner after checkpoint
  selection or loading fails

### `LearnedTopologyPlan`

```python
LearnedTopologyPlan(
    topology: TopologyPlan,
    topology_yaml: str,
    prompt: str,
    raw_response: str,
    attempt_count: int,
    kind: TopologyPromptKind,
)
```

Failure behavior:

- missing extractable YAML raises `TopologyCandidateExtractionError`
- malformed YAML raises the existing parse-layer transport error
- schema-invalid or logic-invalid topologies raise the existing topology validation errors
- there is no silent fallback to deterministic planning after policy failure

## Topology YAML API

### `serialize_topology_plan_to_yaml(topology) -> str`

Serialize a validated typed topology plan into the repository YAML transport
format.

Behavior:

- validates the topology before serialization
- emits YAML from the canonical `TopologyPlan.to_mapping()` transport shape
- keeps YAML encoding details behind the repository transport helper rather than
  exposing the YAML library directly to callers

### `parse_topology_plan_yaml(yaml_text) -> TopologyPlan`

Parse repository YAML text into a validated typed topology plan.

Behavior:

- parses YAML text through the infrastructure adapter boundary
- rejects malformed YAML with a parse-layer error
- rejects schema-invalid transport payloads with `TopologySchemaError`
- rejects graph-rule violations with `TopologyLogicError`
- returns the same typed `TopologyPlan` contract used by the existing planning
  and execution APIs

## Distributed Evaluation API

### `evaluate_candidate_batch(tasks, *, config=None, orchestrator=None) -> DistributedEvaluationBatch`

Evaluate multiple candidate solutions through an orchestration boundary that
keeps submission, worker execution, and collection separate from judge logic.

Behavior:

- preserves task ordering in the collected batch result
- supports explicit `max_workers`, `max_retries`, and `collection_timeout_seconds`
- keeps `max_workers=1` as the local single-worker fallback path
- returns typed per-task statuses plus the underlying `SandboxExecutionResult` when available

## Benchmark Evaluation API

### `run_benchmark_evaluation_entrypoint(dataset_path, output_path, *, checkpoint_source, checkpoint_id=None, source_format=BenchmarkDatasetFormat.APPS_JSONL, samples_per_problem=1, pass_k=None, max_workers=1, max_turns=2, orchestrator_device="cpu", orchestrator_max_attempts=1) -> EvaluationRunArtifact`

Run checkpoint-backed frozen inference over a canonical benchmark dataset and
write a structured evaluation artifact.

Behavior:

- loads a canonical benchmark dataset such as APPS JSONL through the benchmark dataset seam
- resolves one orchestrator checkpoint explicitly from a checkpoint directory,
  checkpoint metadata file, or training artifact JSON
- runs the current solve loop for each benchmark problem and each configured
  attempt index
- re-judges the emitted candidate through the benchmark adapter boundary rather
  than trusting repository-local solve diagnostics alone
- writes per-attempt results that preserve solve status, benchmark verdict,
  latency, topology size, benchmark artifact identifiers, and checkpoint id
- writes run metadata including dataset version, harness version, runtime mode,
  checkpoint provenance, reproduction claim, exact-reproduction readiness,
  blocking gap ids, and aggregate `pass@1` / `pass@k`

Current fidelity note:

- the default runtime still uses repository-local Python and JavaScript
  benchmark harness adapters, so the produced metrics are benchmark-aligned but
  not yet vendor-native leaderboard reproductions
- callers can now intentionally choose a vendor-native adapter boundary, but
  the bundled verification path is still the fixture-driven
  `StubVendorNativeBenchmarkAdapter` rather than a live service integration

## Reproduction Audit API

### `build_reproduction_audit() -> ReproductionAudit`

Return the repository's current strict paper-reproduction checklist as a typed
in-memory object.

Behavior:

- records the current overall claim as `exact` or `approximate`
- lists line-item fidelity items with explicit `exact`, `approximate`, or
  `blocked` status
- returns the current blocking gap ids needed for a strict paper-level claim

### `write_reproduction_audit(output_path) -> ReproductionAudit`

Write the same reproduction audit to a JSON artifact.

### `write_reproduction_audit_entrypoint(output_path) -> ReproductionAudit`

Public path-normalizing wrapper for the same audit artifact.

### `run_batch_evaluation_entrypoint(...) -> EvaluationRunArtifact`

Compatibility alias for `run_benchmark_evaluation_entrypoint(...)`.

## SFT Baseline API

### `generate_sft_dataset_entrypoint(dataset_path, *, sample_count=4500, seed=0, prompt_template_version="orchestrator-sft-v2", source_recipe_name="paper-oriented-synthetic-yaml-v1") -> tuple[SyntheticTopologySample, ...]`

Generate a deterministic JSONL dataset of schema-valid topology targets derived
from the current rule-based orchestrator.

Current transport note:

- `target_topology` remains JSON-serializable in the dataset artifact
- `target_topology_yaml` now carries the YAML-form target used by the SFT path
- the stored topology mapping now comes from the canonical
  `TopologyPlan.to_mapping()` transport shape rather than a training-local
  serializer
- the generator also writes a sidecar metadata file at
  `<dataset>.metadata.json` that records sample count, paper target size,
  difficulty breakdown, source recipe, prompt-template version, and reduced-scale
  status

### `run_sft_baseline_entrypoint(dataset_path, artifact_path, *, epochs=1, learning_rate=1e-4, seed=0, backbone_name=\"Qwen2.5-3B-Instruct\", tokenizer_name=\"Qwen2.5-3B-Instruct\", prompt_template_version=\"orchestrator-sft-v2\", optimizer_name=\"adamw\") -> SftTrainingArtifact`

Validate the generated dataset and write a reproducible checkpoint-producing
artifact for the repository-local SFT stage.

Behavior:

- validates that `target_topology` and `target_topology_yaml` stay in sync
- writes a YAML-target training manifest distinct from the source dataset
- emits a lightweight checkpoint directory with loadable metadata plus a
  repository-local `orchestrator-runtime.json` bundle for frozen inference
- records dataset provenance, source dataset metadata path, source recipe,
  sample count, reduced-scale label, optimizer name, backbone, tokenizer,
  prompt-template version, seed, and checkpoint location in the artifact

### `load_sft_checkpoint_entrypoint(checkpoint_path) -> OrchestratorCheckpointMetadata`

Load repository-local checkpoint metadata from a checkpoint directory,
metadata file, or training-artifact-derived checkpoint source.

Implementation inference:

- this stage now emits checkpoint-shaped artifacts and loadable metadata, but it
  still does not claim paper-scale supervised fine-tuning fidelity by itself

## RL Training API

### `compute_reward_breakdown_entrypoint(topology, *, yaml_valid, execution_outcome) -> RewardBreakdown`

Compute a repository-local reward breakdown from YAML validity, execution
outcome, and topology-density signals.

### `run_rl_baseline_entrypoint(dataset_path, artifact_path, *, checkpoint_source, rollout_count=4, group_size=2, turn_budget=2, seed=0, optimizer_learning_rate=1e-5, optimizer_name="grpo-stub", checkpoint_device="cpu") -> RlTrainingArtifact`

Run the repository-local RL training path from one source checkpoint and write
rollout artifacts plus an updated checkpoint.

Behavior:

- resolves the source checkpoint from a checkpoint directory, metadata file, or
  training artifact JSON
- collects rollout records through the current bounded solve loop
- preserves per-rollout execution outcomes, YAML-derived topology artifacts,
  reward breakdowns, and the resulting checkpoint identifier
- computes grouped advantages as a lightweight GRPO-style update summary
- writes a new checkpoint directory with updated metadata, copied runtime
  bundle state when available, and a stubbed weight lineage marker
- returns a typed artifact that points to both the rollout manifest and the
  updated checkpoint

Implementation inference:

- this path is shaped like the paper's RL stage, but it still uses a
  repository-local grouped-reward stub updater instead of claiming full GRPO
  optimizer fidelity

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
- canonical plain-mapping serialization via `TopologyPlan.to_mapping()`

Properties:

- `node_count`
- `max_nodes`

Methods:

- `to_mapping() -> dict[str, Any]`
- `validate() -> None`
- `from_mapping(raw_plan: Mapping[str, Any]) -> TopologyPlan`

Current transport contract:

- `TopologyPlan` remains the source of truth
- plain mappings and YAML are transport formats around the typed contract
- the repository YAML contract uses:
  `difficulty -> steps -> index -> agents -> name/role/refs -> step_index/agent_name`
- these YAML field names are repository-level implementation inferences rather
  than paper-stated schema facts

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

- the paper does not define a full concrete schema; `from_mapping(...)` remains a repository-local parsing contract around the typed model and now coexists with the YAML adapter boundary

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

## YAML Transport Contract

The paper's primary topology representation is YAML, and the repository now
uses a stable YAML transport around the existing typed topology model.

Current repository YAML shape:

```yaml
difficulty: easy
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
          - step_index: 0
            agent_name: planner_0
          - step_index: 1
            agent_name: coder_1
```

Error categories preserved explicitly:

- YAML syntax failure:
  the text cannot be parsed as YAML
- schema failure:
  the YAML parses, but required repository fields or field types are wrong
- topology logic failure:
  the YAML parses into the repository schema, but the resulting `TopologyPlan`
  violates validation rules such as first-step references or missing final
  testing agent

Backward-compatibility rule:

- existing typed APIs such as `plan_problem_topology(...)` will keep returning
  `TopologyPlan`
- YAML entrypoints are additive transport helpers, not replacements for the
  typed topology model

Current implementation status:

- the repository now has an infrastructure-only YAML adapter boundary for
  `mapping -> YAML text` and `YAML text -> mapping`
- YAML parser failures are translated into explicit topology-YAML transport
  errors instead of leaking raw library exceptions
- the repository now also supports `YAML text -> TopologyPlan` through the
  existing typed topology parser and validator
- topology validation failures are now split into:
  `TopologySchemaError` for field-contract violations and `TopologyLogicError`
  for graph-rule violations, both under the existing
  `TopologyValidationError` base class

## Current Limits

It currently does:

- expose typed topology contracts
- serialize typed topologies into the repository YAML transport format
- parse repository YAML text back into validated typed topologies
- generate topology YAML candidates through an explicit learned-orchestrator policy boundary
- expose typed multi-turn state and revision-input contracts
- parse single-turn topologies from plain mappings
- validate paper-aligned topology structure
- emit deterministic topology plans for supported difficulty tiers
- emit deterministic revised topologies from prior-turn feedback
- emit learned-policy topology candidates for first-turn and later-turn planning
- resolve lightweight orchestrator checkpoints into the online solve loop and
  learned planning entrypoints
- execute non-testing worker roles through a typed worker-runtime adapter seam
- execute single-turn topologies with a local judge-backed testing role
- run a bounded multi-turn solve loop with early stop on pass
- produce lightweight loadable SFT checkpoint artifacts with explicit metadata
- return candidate code and structured execution traces from `solve_problem(...)`

The repository currently does not:

- load benchmark-grade model weights into a production inference runtime
- claim benchmark-exact frozen inference semantics

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
