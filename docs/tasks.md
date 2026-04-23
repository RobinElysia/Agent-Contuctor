# Task Cards

## Purpose
This document translates project goals into executable work units. Each task should be narrow enough for an agent to complete without guessing scope, but concrete enough to be reviewed and verified.

## Task Card Format

Every task card should include:

- `Task ID`
- `Status`
- `Depends on`
- `Scope`
- `Files`
- `Implementation notes`
- `Acceptance criteria`
- `Out of scope`

Statuses should use one of:

- `todo`
- `in_progress`
- `blocked`
- `done`

## Global Task Rules

- An agent should work on the smallest complete task that advances the repository.
- If a task requires files outside the stated scope, the agent should report the dependency instead of silently broadening the task.
- If code and documentation drift is discovered, report it before implementation.
- Acceptance criteria must be behavior-based and verifiable.

## Active Task Cards

### Task ID: DOC-01
Status: done
Depends on: none
Scope: establish the repository documentation hierarchy and baseline agent constraints
Files:
- `AGENTS.md`
- `docs/Codex.md`
- `docs/ClaudeCode.md`
- `docs/requirements.md`
- `docs/tech.md`
- `docs/tasks.md`
Implementation notes:
- define document priority
- define backend-oriented architecture constraints
- define agent execution and verification expectations
Acceptance criteria:
- repository-level guidance exists
- document roles are clearly separated
- the docs are written in English
Out of scope:
- paper interpretation
- runtime implementation

### Task ID: RES-01
Status: done
Depends on: DOC-01
Scope: read `2602.17100v1.pdf` and distill the method into implementation-oriented notes
Files:
- `2602.17100v1.pdf`
- `docs/Paper.md`
Implementation notes:
- separate direct facts from implementation inferences
- document the method pipeline, inputs, outputs, and key abstractions
- identify unresolved ambiguities that will affect implementation
Acceptance criteria:
- `docs/Paper.md` exists
- the paper summary is implementation-oriented rather than purely academic
- open questions are explicitly listed
Out of scope:
- full code implementation
- API framework selection

### Task ID: BOOT-01
Status: done
Depends on: RES-01
Scope: replace placeholder project bootstrap files with a reproducible Python package baseline
Files:
- `pyproject.toml`
- `main.py`
- `src/agentconductor/`
- `tests/`
Implementation notes:
- remove placeholder project metadata
- define initial dependency set from `docs/Paper.md`
- move reusable logic into package modules
Acceptance criteria:
- project metadata is no longer placeholder text
- package structure exists
- at least one basic test path exists
Out of scope:
- full paper implementation
- external service deployment

### Task ID: API-01
Status: done
Depends on: BOOT-01
Scope: expose the first stable callable API around the paper method
Files:
- package modules under `src/agentconductor/`
- API adapter files if introduced
- tests covering the API boundary
Implementation notes:
- keep API contracts explicit
- separate orchestration from transport details
- avoid locking the project into a heavyweight framework unless justified
Acceptance criteria:
- external callers have a documented entrypoint
- API inputs and outputs are typed or clearly structured
- basic verification covers the API boundary
Out of scope:
- production deployment hardening
- unrelated convenience endpoints

### Task ID: TOP-01
Status: done
Depends on: API-01
Scope: define the executable topology schema and validation rules for a single-turn plan
Files:
- `src/agentconductor/domain/`
- `src/agentconductor/infrastructure/` if schema parsing adapters are introduced
- `tests/`
- `API.md`
Implementation notes:
- define typed models for topology plan, step, agent invocation, and references
- encode the paper's structural constraints for layered DAG execution
- validate first-layer empty references, final-layer testing agent presence, and difficulty-aware node budgets
- document any inferred schema rules that are not explicit in the paper
Acceptance criteria:
- callers can construct or parse a single-turn topology plan into typed objects
- invalid topology structures are rejected with explicit validation errors
- tests cover at least one valid topology and multiple invalid topology cases
- public API documentation reflects the new topology contract if exposed
Out of scope:
- orchestrator policy generation
- graph execution
- multi-turn history management

### Task ID: ORCH-01
Status: done
Depends on: TOP-01
Scope: implement a deterministic rule-based orchestrator that emits valid single-turn topology plans
Files:
- `src/agentconductor/application/`
- `src/agentconductor/domain/`
- `src/agentconductor/interfaces/`
- `tests/`
- `API.md`
Implementation notes:
- keep the orchestrator deterministic and local; do not introduce model-serving dependencies
- map difficulty and problem shape to a small set of topology templates
- emit only schema-valid topologies compatible with the current role pool
- make rule choices explicit so they can later be replaced by a learned orchestrator
Acceptance criteria:
- the orchestrator returns a valid topology plan for each supported difficulty tier
- generated plans satisfy topology schema validation
- tests verify stable topology generation for representative problem inputs
- external callers have a documented way to invoke topology planning
Out of scope:
- learned orchestration
- multi-turn topology revision
- reward optimization

### Task ID: EXEC-01
Status: done
Depends on: TOP-01
Scope: implement single-turn graph execution for a validated layered topology
Files:
- `src/agentconductor/application/`
- `src/agentconductor/domain/`
- `src/agentconductor/infrastructure/` if role adapters are introduced
- `tests/`
Implementation notes:
- execute layers in order and resolve references only from prior layers
- introduce a role registry or equivalent dispatch boundary for worker behavior
- use deterministic mock or rule-based role implementations for retrieval, planning, algorithmic, coding, debugging, and testing roles
- capture structured per-agent outputs needed by later API integration
Acceptance criteria:
- a validated single-turn topology can be executed end to end
- role outputs are available to downstream steps through explicit references
- tests cover successful layer execution and invalid reference handling
- execution results are returned in typed structures rather than raw strings only
Out of scope:
- sandboxed code execution against external judges
- multi-turn retries
- RL reward calculation

### Task ID: API-02
Status: done
Depends on: ORCH-01, EXEC-01
Scope: upgrade `solve_problem()` from returning a static plan to returning a candidate solution and structured execution result
Files:
- `src/agentconductor/application/`
- `src/agentconductor/domain/`
- `src/agentconductor/interfaces/`
- `tests/`
- `API.md`
- `README.md`
Implementation notes:
- keep the public API callable from Python without requiring CLI or HTTP transport
- integrate rule-based orchestration and single-turn execution behind the existing API boundary
- return structured candidate code, role trace, and testing outcome in the solve result
- preserve explicit typing for API inputs and outputs
Acceptance criteria:
- `solve_problem()` performs planning plus single-turn execution instead of returning bootstrap metadata only
- the returned result includes candidate solution content and a structured execution summary
- tests cover at least one end-to-end solve path and one failure path
- caller-facing documentation is updated to match the new API behavior
Out of scope:
- multi-turn topology evolution
- external sandbox infrastructure
- production-grade model integration

### Task ID: TURN-01
Status: done
Depends on: API-02
Scope: define multi-turn solve state, history, and topology-revision contracts
Files:
- `src/agentconductor/domain/`
- `src/agentconductor/application/`
- `tests/`
- `API.md`
Implementation notes:
- introduce typed history objects for turn-level topology, role trace, and testing feedback
- model early-stop conditions and revision inputs explicitly rather than passing raw strings
- keep the contracts compatible with the current single-turn executor so later loops can compose them
- label any inferred history semantics that are not fully specified in the paper
Acceptance criteria:
- callers can construct and inspect a typed multi-turn solve state
- turn history preserves topology, execution result, and testing outcome per turn
- tests cover at least one successful history append and one invalid state transition
- API documentation reflects the new multi-turn state contract if exposed
Out of scope:
- executing more than one turn
- sandbox-backed code execution
- training infrastructure

### Task ID: TURN-02
Status: done
Depends on: TURN-01
Scope: implement multi-turn topology revision and stopping logic for solve requests
Files:
- `src/agentconductor/application/`
- `src/agentconductor/interfaces/`
- `src/agentconductor/domain/`
- `tests/`
- `API.md`
- `README.md`
Implementation notes:
- extend the orchestrator boundary so a later turn can consume prior testing feedback and history
- run plan -> execute -> evaluate in a bounded loop up to the current turn budget
- stop early on pass and otherwise emit a revised topology for the next turn
- keep the initial implementation deterministic and local until learned orchestration exists
Acceptance criteria:
- solve requests can execute more than one turn when testing fails
- later turns consume explicit prior-turn feedback rather than recomputing from scratch only
- tests cover early stop on pass and a two-turn revision path
- caller-facing documentation describes the updated multi-turn behavior
Out of scope:
- real sandbox integration
- RL reward optimization
- production model serving

### Task ID: SBX-01
Status: done
Depends on: TURN-01
Scope: implement real code extraction and sandbox-backed testing integration
Files:
- `src/agentconductor/infrastructure/`
- `src/agentconductor/application/`
- `src/agentconductor/domain/`
- `tests/`
- `docs/tech.md`
- `API.md`
Implementation notes:
- define a narrow sandbox adapter interface instead of coupling execution logic to one runtime
- extract candidate code from role outputs with an explicit contract
- return structured execution outcomes aligned with the paper's testing-agent result categories
- keep deterministic local fallbacks only where needed for tests
Acceptance criteria:
- testing agents can evaluate extracted candidate code through a concrete sandbox adapter
- sandbox outcomes are mapped into typed execution results and diagnostics
- tests cover at least one passing run and one failing run through the sandbox boundary
- technical docs describe the sandbox interface and assumptions
Out of scope:
- distributed sandbox orchestration
- multi-turn policy learning
- benchmark-scale evaluation pipelines

### Task ID: JUDGE-01
Status: done
Depends on: SBX-01
Scope: replace the repository-local Python sandbox harness with a benchmark-grade judge boundary
Files:
- `src/agentconductor/infrastructure/`
- `src/agentconductor/application/`
- `src/agentconductor/domain/`
- `tests/`
- `docs/tech.md`
- `API.md`
- `README.md`
Implementation notes:
- keep the existing sandbox adapter boundary and extend it instead of coupling execution logic to one judge runtime
- support richer judge inputs such as test cases, expected outputs, and resource limits
- preserve typed mapping from judge-native outcomes into repository execution results
- document which parts remain repository approximations if exact benchmark semantics are still unavailable
Acceptance criteria:
- the repository can evaluate candidate code through a judge interface richer than the current substring-based local harness
- judge outcomes are mapped into typed testing results with explicit diagnostics
- tests cover at least one passing run and one failing run through the new judge boundary
- caller-facing docs explain the new judge contract and its current fidelity limits
Out of scope:
- distributed scheduling across multiple sandbox workers
- benchmark-scale batch orchestration
- training or RL policy updates

### Task ID: JUDGE-02
Status: done
Depends on: JUDGE-01
Scope: close the fidelity gap between the repository-local judge and the target benchmark judge semantics
Files:
- `src/agentconductor/infrastructure/`
- `src/agentconductor/application/`
- `src/agentconductor/domain/`
- `tests/`
- `docs/tech.md`
- `docs/Paper.md`
- `API.md`
- `README.md`
Implementation notes:
- identify which benchmark judge behaviors are still approximated locally and document them explicitly
- add adapter contracts for benchmark-facing execution semantics without leaking judge-specific details into application services
- support benchmark-relevant behaviors that are currently missing, such as stricter entrypoint expectations, result normalization rules, or richer per-case verdict mapping
- label every remaining repository-level inference so downstream evaluation tasks know the current fidelity boundary
Acceptance criteria:
- the repository documents a concrete gap list between the local judge and the target benchmark semantics
- at least one currently approximated judge behavior is upgraded to a stricter benchmark-aligned implementation
- tests cover the upgraded semantics and verify typed outcome mapping remains stable
- caller-facing docs explain what is now benchmark-aligned and what still remains approximate
Out of scope:
- distributed worker orchestration
- benchmark-scale batch scheduling
- RL or SFT training changes

### Task ID: SBX-02
Status: done
Depends on: JUDGE-01
Scope: replace soft in-process resource checks with stronger sandbox-enforced execution limits
Files:
- `src/agentconductor/infrastructure/`
- `src/agentconductor/domain/`
- `tests/`
- `docs/tech.md`
- `API.md`
- `README.md`
Implementation notes:
- move resource enforcement toward subprocess- or OS-level controls instead of relying only on Python-level approximation
- keep the sandbox adapter boundary narrow so application services continue to consume typed execution results only
- make CPU, wall-clock, and memory limits explicit and separately configurable where the runtime supports them
- document platform-specific behavior and any fallback path used when hard limits are unavailable
Acceptance criteria:
- the judge path enforces at least one resource limit through a stronger mechanism than `tracemalloc`
- typed outcomes distinguish hard limit violations from generic runtime failures
- tests cover at least one limit-exceeded path under the stronger enforcement strategy
- docs describe enforcement guarantees and known platform gaps
Out of scope:
- distributed orchestration
- external benchmark dataset pipelines
- training changes

### Task ID: SBX-03
Status: done
Depends on: SBX-02
Scope: add Windows Job Object-backed resource enforcement for sandbox judge workers
Files:
- `src/agentconductor/infrastructure/`
- `src/agentconductor/domain/`
- `tests/`
- `docs/tech.md`
- `API.md`
- `README.md`
Implementation notes:
- implement a Windows-specific sandbox enforcement path using Job Objects so judge worker processes run inside an OS-managed resource container
- keep the existing sandbox adapter boundary narrow and preserve the current typed `TestingOutcome` mapping for limit violations
- prefer standard-library integration such as `ctypes` unless a Windows dependency is justified by a concrete maintenance or correctness benefit
- document exactly which limits are hard-enforced on Windows through Job Objects and how that differs from the current POSIX `resource` path
- break the implementation into these substeps:
  1. introduce a Windows-only infrastructure helper responsible for Job Object lifecycle, limit configuration, process assignment, and teardown
  2. add a narrow internal adapter seam in the judge runner so per-case subprocess launch can delegate platform-specific resource binding without changing application-layer contracts
  3. map the current `JudgeResourceLimits` contract onto Windows primitives, with explicit documentation of which fields are hard-enforced and which remain approximations
  4. detect and classify worker termination paths where the operating system kills the process before the harness emits a structured result
  5. add platform-gated tests for Windows behavior and keep non-Windows tests stable
- use an internal interface sketch close to:
  - `class ProcessLimitBinder(Protocol): bind(process_handle, resource_limits) -> BoundProcessContext`
  - `class WindowsJobObjectBinder: create_job(); configure_limits(resource_limits); assign_process(process_handle); close()`
  - `@dataclass(frozen=True) class BoundProcessContext: platform: str; hard_memory_limit: bool; hard_cpu_limit: bool; hard_wall_time_limit: bool`
  - the judge adapter should keep returning `SandboxExecutionResult` only; Job Object details stay inside infrastructure
- map resource limits on Windows with these expectations:
  - `memory_limit_bytes`: primary target for hard Job Object enforcement
  - `wall_time_seconds`: remains enforced by the existing per-case subprocess timeout owned by the parent judge process
  - `cpu_time_seconds`: treat as provisional on Windows until the repository chooses a stable Job Object CPU accounting strategy; do not claim parity with POSIX `RLIMIT_CPU` without verification
- use a result-mapping plan close to:
  - if the harness writes a structured result first, keep trusting the emitted typed outcome
  - if the worker exits without a result file and Windows termination evidence indicates a Job Object memory kill, map to `TestingOutcome.MEMORY_LIMIT_EXCEEDED`
  - if the worker exits without a result file and the parent timeout expires, map to `TestingOutcome.TIME_LIMIT_EXCEEDED`
  - if the worker exits without a result file and the termination cause cannot be classified, keep mapping to `TestingOutcome.RUNTIME_ERROR` with platform-specific diagnostics
- the implementation should make the Windows classification evidence explicit, for example by checking exit codes, Job Object completion state, or a narrow side-channel owned by the launcher rather than inferring from generic stderr text only
Acceptance criteria:
- on Windows, the judge can place worker processes into a Job Object with at least one hard OS-enforced resource limit
- limit-triggered worker termination is mapped back into typed sandbox outcomes instead of surfacing only as a generic runtime failure
- tests cover at least one Windows-specific limit-exceeded path or, if direct runtime coverage is not portable, isolate and verify the Windows adapter logic behind a platform-gated test seam
- caller-facing docs describe the Windows enforcement guarantees, configuration limits, and remaining gaps
Out of scope:
- distributed worker orchestration
- non-Windows sandbox redesign
- benchmark dataset integration

### Task ID: DEVX-01
Status: done
Depends on: JUDGE-01
Scope: make repository verification commands reproducible under restricted local environments
Files:
- `pyproject.toml`
- `README.md`
- `docs/tech.md`
- `tests/` if helper coverage is added
- repository-level helper scripts if introduced
Implementation notes:
- keep `uv` as the package and environment manager, but remove assumptions that verification always has access to a user-global cache path
- provide a repository-local or explicitly configurable verification path for test execution in sandboxed environments
- document the supported verification commands and any required environment variables
- avoid introducing heavyweight tooling solely for test invocation
Acceptance criteria:
- the repository documents and supports at least one `uv`-based test command that works with restricted cache permissions
- verification instructions no longer rely on undeclared machine-specific state
- if helper configuration is added, tests or smoke verification cover the supported invocation path
- docs clearly distinguish preferred verification commands from fallback commands
Out of scope:
- CI service deployment
- external package mirror management
- non-Python toolchain setup

### Task ID: SBX-04
Status: done
Depends on: SBX-03
Scope: improve Windows hard-memory enforcement reliability when the host runtime already runs inside an outer Job
Files:
- `src/agentconductor/infrastructure/`
- `tests/`
- `docs/tech.md`
- `API.md`
- `README.md`
Implementation notes:
- detect whether the current host runtime prevents rebinding child processes into a dedicated Job Object
- introduce an explicit launcher strategy for Windows workers so breakaway-capable child creation is attempted before plain subprocess fallback
- preserve the narrow sandbox adapter boundary; keep Win32 and launcher details inside infrastructure
- make the downgrade path explicit and inspectable so callers can distinguish "hard memory enforcement attached" from "host runtime forbids attachment"
- prefer classification evidence from process creation flags, bind results, and host-job diagnostics rather than generic stderr heuristics
- document which Windows runtime environments are expected to allow hard memory enforcement and which are expected to degrade
Acceptance criteria:
- the judge can explicitly report whether Windows hard memory enforcement was attached or downgraded
- tests cover at least one downgraded host-runtime path and one successful binder-path seam
- caller-facing docs describe the Windows reliability boundary instead of treating hard memory enforcement as uniformly available
Out of scope:
- CPU quota enforcement
- non-Windows sandbox changes
- distributed orchestration

### Task ID: SBX-05
Status: done
Depends on: SBX-03
Scope: add a verified Windows CPU-limit enforcement strategy or explicitly codify its absence behind a typed capability boundary
Files:
- `src/agentconductor/infrastructure/`
- `src/agentconductor/domain/`
- `tests/`
- `docs/tech.md`
- `API.md`
- `README.md`
Implementation notes:
- evaluate whether Windows Job Objects should use CPU rate control, per-job user time accounting, or remain unsupported
- do not claim parity with POSIX `RLIMIT_CPU` unless the chosen Windows mechanism can be verified with stable tests
- if no stable strategy is found, add an explicit capability model so Windows CPU enforcement is reported as unsupported rather than implicitly approximated
- keep `wall_time_seconds` as the only guaranteed hard timing control until Windows CPU semantics are proven
- document the semantic difference between throttling, accounting, and hard time-limit termination
Acceptance criteria:
- the repository either implements a verified Windows CPU-limit path or exposes an explicit typed unsupported/provisional capability
- tests cover the chosen behavior or the unsupported-capability contract
- docs clearly separate hard wall-clock guarantees from Windows CPU-limit semantics
Out of scope:
- benchmark integration
- training or evaluation pipeline work
- Linux or POSIX CPU-limit redesign

### Task ID: DIST-01
Status: done
Depends on: JUDGE-01
Scope: add distributed sandbox orchestration for parallel candidate evaluation
Files:
- `src/agentconductor/infrastructure/`
- `src/agentconductor/application/`
- `src/agentconductor/domain/`
- `tests/`
- `docs/tech.md`
- `README.md`
Implementation notes:
- separate job submission, worker execution, and result collection from judge semantics
- keep the single-node path available for local verification and fallback
- make concurrency, retries, and timeout handling explicit and inspectable
- avoid introducing deployment-specific infrastructure assumptions unless the task requires them
Acceptance criteria:
- the repository can dispatch sandbox evaluation work through a distributed orchestration boundary
- execution results remain typed and equivalent to the single-node judge path
- tests or verification cover successful distributed submission and at least one failure or timeout path
- technical docs describe worker orchestration assumptions and fallback behavior
Out of scope:
- benchmark-scale metrics aggregation
- RL training integration
- production cloud deployment hardening

### Task ID: EVAL-01
Status: done
Depends on: JUDGE-01
Scope: build a benchmark-scale evaluation pipeline around the current solve and judge stack
Files:
- `src/agentconductor/`
- `scripts/` if introduced
- `tests/`
- `docs/tech.md`
- `README.md`
Implementation notes:
- keep batch-evaluation code outside the online solve path
- define a reproducible input/output format for benchmark problems, runs, and aggregated results
- record per-problem judge outcomes, latency, and topology metadata so later training analysis can reuse them
- document which benchmark adapters are fully implemented and which remain placeholders
Acceptance criteria:
- the repository contains a runnable batch evaluation entrypoint over a dataset of problems
- evaluation artifacts include per-problem outcomes and an aggregate summary
- tests or verification cover dataset schema validation and one small end-to-end batch run
- docs explain how to run and interpret the evaluation pipeline
Out of scope:
- distributed worker orchestration
- RL optimization
- exact paper leaderboard reproduction

### Task ID: TRAIN-01
Status: done
Depends on: TOP-01, ORCH-01
Scope: build the synthetic-topology data and supervised-finetuning baseline for the orchestrator
Files:
- `src/agentconductor/`
- `scripts/` if introduced
- `tests/`
- `docs/Paper.md`
- `README.md`
Implementation notes:
- generate or materialize schema-valid training examples that teach structural priors
- define a reproducible data format for problem input, difficulty, and target topology output
- keep training code separate from runtime inference modules
- document which parts are faithful to the paper and which parts are repository-level approximations
Acceptance criteria:
- the repository can produce or load SFT-ready topology training data
- a documented training entrypoint exists for the supervised baseline
- tests or verification cover dataset schema integrity and basic training-config validation
- docs explain how the SFT stage maps to the paper
Out of scope:
- RL optimization
- full benchmark reproduction
- deployment of trained checkpoints

### Task ID: RL-01
Status: done
Depends on: TURN-02, SBX-01, TRAIN-01
Scope: reproduce the paper's reward-driven RL stage for topology optimization
Files:
- `src/agentconductor/`
- `scripts/` if introduced
- `tests/`
- `docs/Paper.md`
- `README.md`
Implementation notes:
- implement reward calculation components for YAML validity, execution outcome, and topology density
- define the training loop boundary so the orchestrator policy can be optimized independently of worker agents
- preserve reproducibility with explicit configs, seeds, and artifact layout
- document where the repository necessarily approximates paper details that remain underspecified
Acceptance criteria:
- the repository contains a runnable RL training path wired to the current reward components
- reward breakdowns are inspectable per sample or rollout
- tests cover reward calculation invariants and basic training-loop configuration validation
- docs describe the RL stage, its assumptions, and its current fidelity limits
Out of scope:
- exact leaderboard reproduction
- large-scale cluster orchestration
- serving fine-tuned policies in production

### Task ID: TOP-02
Status: done
Depends on: TOP-01, ORCH-01
Scope: add YAML-native topology serialization and parsing so the repository can exchange plans in the paper's primary representation
Files:
- `src/agentconductor/domain/`
- `src/agentconductor/infrastructure/`
- `src/agentconductor/interfaces/`
- `tests/`
- `API.md`
- `docs/Paper.md`
- `README.md`
Implementation notes:
- keep the typed `TopologyPlan` contract as the source of truth and treat YAML as a transport and persistence format around it
- introduce explicit YAML encode and decode boundaries instead of leaking raw dictionaries into application services
- preserve current validation semantics for layered DAG structure, node budgets, and testing-agent requirements after YAML round-trips
- document any YAML schema choices that remain repository-level inferences rather than paper-stated facts
Acceptance criteria:
- callers can serialize a valid `TopologyPlan` into a stable YAML representation and parse it back into typed objects
- invalid YAML syntax, schema violations, and logical topology violations are rejected with explicit diagnostics
- tests cover at least one valid round-trip plus malformed, schema-invalid, and logic-invalid YAML inputs
- caller-facing docs explain the YAML contract and how it relates to the existing typed topology API
Suggested implementation slices:
1. Define the YAML transport contract around the existing typed topology model.
   Scope:
   - choose one stable repository YAML shape for `difficulty`, `steps`, `agents`, and `refs`
   - document which field names are repository-level inference rather than paper-stated facts
   Deliverables:
   - update `docs/Paper.md` and `API.md` with the YAML shape and inference notes
   - keep `TopologyPlan` as the source of truth rather than introducing a parallel YAML-owned domain model
2. Add typed topology serialization helpers that emit a stable mapping before YAML encoding.
   Scope:
   - move the current ad hoc topology-to-dict logic out of training-specific code
   - expose one canonical `TopologyPlan -> mapping` path shared by training and later orchestrator integration
   Deliverables:
   - shared serialization helpers under `src/agentconductor/domain/` or a narrow adjacent seam
   - focused tests for stable mapping output on representative plans
3. Add an infrastructure YAML adapter for encode and decode boundaries.
   Scope:
   - parse YAML text into raw mappings
   - encode canonical mappings into stable YAML text
   - keep YAML-library details out of application services
   Deliverables:
   - dedicated YAML adapter module under `src/agentconductor/infrastructure/`
   - explicit error translation for malformed YAML syntax
4. Parse YAML through the existing typed validation path.
   Scope:
   - decode YAML into a mapping and then into `TopologyPlan`
   - preserve current logical validation semantics for node budgets, prior-step refs, and final testing-agent presence
   Deliverables:
   - one public or internal entrypoint that returns `TopologyPlan` from YAML text
   - explicit distinction between YAML syntax failure, schema-invalid payloads, and logic-invalid topologies
5. Expose caller-facing topology YAML entrypoints without breaking existing typed APIs.
   Scope:
   - add narrow interface functions for topology YAML serialization and parsing
   - keep `plan_problem_topology()` returning `TopologyPlan` for backward compatibility
   Deliverables:
   - interface-level entrypoints and package exports if justified
   - API documentation showing how YAML transport relates to the typed topology contract
6. Rewire existing training and future-planning prep to use the canonical topology transport helpers.
   Scope:
   - replace `_serialize_topology()` in the SFT path with the shared serialization contract
   - keep JSONL dataset structure stable unless a documented YAML field is intentionally introduced
   Deliverables:
   - training code updated to consume the shared topology serialization path
   - regression tests proving the SFT baseline still validates generated targets
7. Add end-to-end verification for YAML round-trips and failure modes.
   Scope:
   - cover valid round-trip, malformed YAML, schema-invalid YAML, and logic-invalid YAML
   - verify diagnostics stay explicit and behavior-based
   Deliverables:
   - tests under `tests/` covering both adapter and typed validation paths
   - repository docs updated to reflect the new YAML-native contract
Out of scope:
- learned orchestrator generation
- benchmark harness integration
- checkpoint training

### Task ID: ORCH-02
Status: done
Depends on: TOP-02, TURN-02
Scope: add a model-backed orchestrator interface that generates topology YAML for online frozen inference
Files:
- `src/agentconductor/application/`
- `src/agentconductor/domain/`
- `src/agentconductor/infrastructure/`
- `src/agentconductor/interfaces/`
- `tests/`
- `API.md`
- `docs/tech.md`
- `README.md`
Implementation notes:
- keep learned orchestration behind a narrow policy boundary so deterministic planning remains available for tests and fallback
- make prompt construction, YAML extraction, parsing, and retry behavior explicit rather than embedding them in the solve loop
- consume the existing typed revision and feedback contracts so later turns can request revised YAML topologies instead of only rule-based plans
- support repository-local mock policies for verification when a real checkpoint is unavailable
Acceptance criteria:
- the repository exposes a learned-orchestrator boundary that can return YAML topology candidates for first-turn and later-turn planning
- invalid model output is surfaced through explicit parse or validation failures rather than silent fallback
- tests cover one successful YAML-planning path and one invalid-output handling path through the new policy boundary
- docs describe how frozen inference chooses between deterministic and learned orchestrator paths
Out of scope:
- exact benchmark judge semantics
- checkpoint fine-tuning
- leaderboard reproduction

### Task ID: BENCH-01
Status: done
Depends on: JUDGE-02, EVAL-01
Scope: define an external benchmark adapter boundary for judge semantics, dataset metadata, and run artifacts
Files:
- `src/agentconductor/domain/`
- `src/agentconductor/application/`
- `src/agentconductor/infrastructure/`
- `tests/`
- `API.md`
- `docs/tech.md`
- `README.md`
Implementation notes:
- separate benchmark-facing concerns from the current repository-local judge so application services do not learn benchmark-specific wire formats
- define typed contracts for benchmark problem metadata, execution settings, verdict mapping, and artifact identifiers
- preserve the current local judge path as an explicit fallback for development and focused testing
- document which semantics must come from the external benchmark and which remain repository-owned
Acceptance criteria:
- the repository exposes a typed benchmark adapter seam distinct from the local subprocess judge
- benchmark problem definitions and verdict mappings can be represented without leaking benchmark-native payloads into core solve services
- tests cover contract validation and at least one adapter stub path that maps benchmark-native results into repository types
- technical docs explain the boundary between local judge behavior and external benchmark integration
Out of scope:
- full benchmark execution against real datasets
- multi-language runtime support
- leaderboard reporting

### Task ID: BENCH-02
Status: done
Depends on: BENCH-01
Scope: add benchmark dataset ingestion and normalization for the paper's target evaluation sets
Files:
- `src/agentconductor/application/`
- `src/agentconductor/infrastructure/`
- `src/agentconductor/domain/`
- `tests/`
- `docs/Paper.md`
- `README.md`
Implementation notes:
- support explicit dataset loaders for benchmark problem statements, identifiers, difficulty metadata, and evaluation splits
- keep dataset normalization reproducible and documented so later training and leaderboard tasks can consume the same canonical problem records
- avoid coupling dataset storage format to one benchmark vendor layout when a typed canonical record can isolate the differences
- document any unavailable dataset fields or licensing constraints that block exact reproduction
Acceptance criteria:
- the repository can load and validate canonical benchmark problem records from at least one external dataset source
- normalized dataset artifacts preserve source identifiers and split metadata needed for later evaluation reporting
- tests cover dataset schema validation, source-to-canonical normalization, and one small fixture-based load path
- docs explain which benchmark datasets are wired, which are pending, and any known access constraints
Out of scope:
- executing benchmark submissions
- multi-language compile and run support
- model training

### Task ID: BENCH-03
Status: done
Depends on: BENCH-01, BENCH-02, DIST-01
Scope: integrate a benchmark-backed execution path for Python problems with stricter benchmark-aligned invocation semantics
Files:
- `src/agentconductor/infrastructure/`
- `src/agentconductor/application/`
- `src/agentconductor/domain/`
- `tests/`
- `API.md`
- `docs/tech.md`
- `README.md`
Implementation notes:
- wire the benchmark adapter boundary to a concrete Python-first harness before expanding to more languages
- align entrypoint, stdin or function invocation, per-case verdict mapping, and artifact capture with benchmark expectations instead of repository-local defaults
- make it explicit when evaluation is running through the external benchmark path versus the local subprocess fallback
- preserve inspectable diagnostics so later leaderboard analysis can distinguish harness failures from candidate failures
Acceptance criteria:
- the repository can execute Python benchmark problems through a concrete benchmark-backed path rather than only the local judge
- benchmark-native verdicts and diagnostics are mapped into typed repository results without losing pass or fail categories needed by later analysis
- tests or smoke verification cover one end-to-end Python benchmark execution path and one benchmark-specific failure path
- docs describe the Python benchmark execution contract and any remaining fidelity gaps
Out of scope:
- non-Python language support
- checkpoint training
- exact leaderboard aggregation

### Task ID: BENCH-04
Status: done
Depends on: BENCH-03
Scope: extend benchmark execution to the paper-relevant multi-language runtime surface
Files:
- `src/agentconductor/infrastructure/`
- `src/agentconductor/application/`
- `src/agentconductor/domain/`
- `tests/`
- `API.md`
- `docs/tech.md`
- `README.md`
Implementation notes:
- add typed language metadata, build or run commands, and verdict mapping without hard-coding language-specific behavior into application services
- start from the languages required by the target benchmarks and document any benchmark-language combinations that remain unsupported
- keep resource-limit semantics explicit per language runtime because compile, run, and memory behavior may differ from Python
- preserve the local Python-only path for developer verification when full multi-language infrastructure is unavailable
Acceptance criteria:
- the benchmark execution path supports more than one language with explicit language-aware configuration
- tests or smoke verification cover at least one compiled-language or non-Python execution path plus one language-specific failure mode
- docs enumerate the supported benchmark languages and the remaining unsupported combinations
- caller-facing contracts expose language selection without requiring benchmark-specific payload handling in user code
Out of scope:
- distributed cluster scheduling beyond the current orchestration boundary
- model training
- leaderboard result publication

### Task ID: BENCH-05
Status: done
Depends on: BENCH-04
Scope: extend the benchmark execution contracts to represent compiled-language build and run phases explicitly
Files:
- `src/agentconductor/domain/`
- `src/agentconductor/application/`
- `src/agentconductor/infrastructure/`
- `tests/`
- `API.md`
- `docs/tech.md`
- `README.md`
Implementation notes:
- add typed benchmark-owned fields for compiled-language source layout, compile commands or templates, executable targets, and phase-specific resource limits without leaking vendor wire formats into application services
- keep the existing Python and JavaScript script-first path intact while making compile and run phases inspectable in artifacts and diagnostics
- define how compile-time failures, run-time failures, and harness failures map into repository `TestingOutcome` values without collapsing them into one generic runtime error
- document which pieces remain repository-local inferences versus official benchmark semantics
Acceptance criteria:
- the benchmark contracts can describe both interpreted and compiled-language execution without forcing caller code to construct benchmark-vendor payloads
- compile and run phases have explicit typed diagnostics and artifact identifiers
- tests cover schema validation for compiled-language settings and one adapter-stub path that emits compile-phase versus run-phase failures distinctly
- docs explain the new compile or run contract and the remaining unsupported benchmark-language combinations
Out of scope:
- full C++ or Java execution
- remote vendor-native submission services
- leaderboard aggregation

### Task ID: BENCH-06
Status: todo
Depends on: BENCH-05
Scope: add a local compiled-language benchmark harness for the first paper-relevant C++ and Java execution paths
Files:
- `src/agentconductor/infrastructure/`
- `src/agentconductor/application/`
- `src/agentconductor/domain/`
- `tests/`
- `API.md`
- `docs/tech.md`
- `README.md`
Implementation notes:
- implement explicit compile then run handling for at least C++ and Java, including temporary workspace layout, executable or class discovery, and per-phase diagnostics
- keep language-specific command construction in infrastructure adapters so the benchmark application services continue to dispatch on typed language metadata only
- make toolchain availability explicit and inspectable so unsupported host environments fail as adapter errors rather than silent skips
- preserve the existing Python and JavaScript local harnesses as the low-friction developer path when compiled-language toolchains are unavailable
Acceptance criteria:
- the repository can execute at least one compiled-language benchmark record end to end through a local benchmark harness
- tests or smoke verification cover one successful compiled-language path and one compile-phase failure path
- docs enumerate which compiled languages are supported locally, which toolchains are required, and which benchmark-language combinations remain unsupported
- caller-facing benchmark APIs stay unchanged apart from the expanded typed execution settings introduced earlier
Out of scope:
- remote benchmark vendor submission
- distributed compile farms or cluster scheduling
- exact leaderboard reproduction

### Task ID: BENCH-07
Status: done
Depends on: BENCH-05, BENCH-06
Scope: add a vendor-native benchmark runtime boundary for benchmarks that cannot be faithfully reproduced through only local harness execution
Files:
- `src/agentconductor/domain/`
- `src/agentconductor/application/`
- `src/agentconductor/infrastructure/`
- `src/agentconductor/interfaces/`
- `tests/`
- `API.md`
- `docs/Paper.md`
- `docs/tech.md`
- `README.md`
Implementation notes:
- model submission, polling, result download, and vendor-side artifact provenance as typed contracts rather than overloading the local harness result path
- keep local harness execution and vendor-native execution as separate infrastructure adapters behind the same benchmark seam so later evaluation can choose intentionally
- document authentication, licensing, dataset access, or benchmark-policy constraints that may block exact repository-local reproduction
- make it explicit which benchmark-language combinations now use vendor-native execution and which still use repository-local harnesses
Acceptance criteria:
- the repository exposes a typed vendor-native benchmark runtime path distinct from the local harness adapters
- vendor-native results preserve submission identifiers, terminal verdict mapping, and artifact provenance needed for later evaluation reporting
- tests cover at least one fixture-driven vendor submission lifecycle path, including submission, terminal result collection, and adapter-error handling
- docs explain when callers should use vendor-native runtime versus the local harness path and what external constraints apply
Out of scope:
- public leaderboard submission automation
- production secrets management beyond explicit configuration boundaries
- paper-level result claims by itself

### Task ID: TRAIN-02
Status: done
Depends on: TOP-02, ORCH-02, BENCH-02, TRAIN-01
Scope: replace the repository-local SFT artifact baseline with checkpoint-producing supervised training for the orchestrator
Files:
- `src/agentconductor/application/`
- `src/agentconductor/infrastructure/`
- `src/agentconductor/domain/`
- `scripts/` if introduced
- `tests/`
- `docs/Paper.md`
- `docs/tech.md`
- `README.md`
Implementation notes:
- train against YAML-topology targets rather than only structured JSON surrogates so the checkpoint learns the paper's primary output format
- make backbone selection, tokenizer or prompt formatting, optimizer settings, seeds, checkpoint naming, and artifact layout explicit and reproducible
- separate dataset preparation from actual fine-tuning execution so benchmark and synthetic data sources can be mixed intentionally
- document every deviation from the paper's reported setup, including reduced scale, substitute backbone, or unavailable data
Acceptance criteria:
- the repository contains a documented SFT training path that can produce a loadable orchestrator checkpoint artifact
- training configuration, dataset provenance, and output checkpoint locations are explicit and reproducible
- tests or smoke verification cover config validation and checkpoint-loading metadata even if full training is too heavy for routine test runs
- docs explain how the implemented SFT path differs from the earlier repository-local artifact baseline
Out of scope:
- RL optimization
- exact leaderboard reproduction
- production deployment of trained checkpoints

### Task ID: RL-02
Status: done
Depends on: TRAIN-02, BENCH-03, RL-01
Scope: replace the repository-local RL baseline with a checkpoint-updating policy-optimization path aligned with the paper's GRPO stage
Files:
- `src/agentconductor/application/`
- `src/agentconductor/infrastructure/`
- `src/agentconductor/domain/`
- `scripts/` if introduced
- `tests/`
- `docs/Paper.md`
- `docs/tech.md`
- `README.md`
Implementation notes:
- optimize the learned orchestrator checkpoint rather than only writing rollout summaries
- keep reward calculation, rollout collection, policy update, and checkpoint management as explicit boundaries so training failures are inspectable
- make group size, rollout count, turn budget, optimizer settings, and seed control explicit and reproducible
- document which parts match the paper's reported GRPO setup and which still rely on implementation inference
Acceptance criteria:
- the repository contains a documented RL training path that updates an orchestrator checkpoint from rollout rewards
- rollout artifacts preserve per-sample reward breakdowns, execution outcomes, and resulting checkpoint identifiers
- tests or smoke verification cover RL config validation, artifact layout, and at least one lightweight policy-update path or stubbed trainer path
- docs explain the fidelity boundary between the implemented RL trainer and the paper's reported setup
Out of scope:
- full leaderboard claims
- large-scale distributed training infrastructure
- production serving

### Task ID: ORCH-03
Status: done
Depends on: TRAIN-02, ORCH-02
Scope: load trained orchestrator checkpoints into the online solve loop for frozen multi-turn inference
Files:
- `src/agentconductor/application/`
- `src/agentconductor/infrastructure/`
- `src/agentconductor/interfaces/`
- `tests/`
- `API.md`
- `README.md`
Implementation notes:
- make checkpoint discovery, loading, version selection, and fallback behavior explicit rather than relying on implicit file conventions
- preserve deterministic fallback planning for local development while allowing solve requests to opt into trained frozen inference
- ensure later-turn revision consumes the same checkpointed orchestrator path as first-turn planning
- document runtime constraints such as device placement, memory expectations, and tokenizer compatibility
Acceptance criteria:
- callers can run solve requests with a configured trained orchestrator checkpoint instead of only the deterministic planner
- checkpoint loading failures surface as explicit configuration or runtime errors
- tests or smoke verification cover checkpoint selection and one frozen-inference solve path using a lightweight mock or fixture checkpoint
- docs explain how trained checkpoints plug into online inference and what artifacts are required
Out of scope:
- benchmark leaderboard reporting
- benchmark dataset ingestion
- production model serving infrastructure

### Task ID: EVAL-02
Status: done
Depends on: BENCH-07, ORCH-03, RL-02
Scope: run benchmark-aligned evaluation over trained frozen inference and produce leaderboard-grade aggregate metrics
Files:
- `src/agentconductor/application/`
- `src/agentconductor/interfaces/`
- `src/agentconductor/domain/`
- `scripts/` if introduced
- `tests/`
- `docs/Paper.md`
- `README.md`
Implementation notes:
- keep benchmark evaluation separate from training so reported metrics are tied to explicit checkpoint and dataset versions
- compute benchmark-facing aggregates such as pass@k or pass@1 only from normalized run artifacts rather than ad hoc logs
- preserve enough metadata to audit solver config, benchmark split, harness version, and checkpoint provenance for every reported run
- document when a reported metric is benchmark-aligned versus still approximate because of missing harness, data, or language support
Acceptance criteria:
- the repository can run a trained frozen orchestrator over benchmark-aligned datasets and emit aggregate metrics from structured artifacts
- evaluation artifacts record dataset version, harness version, checkpoint identifier, and aggregate scores needed for later comparison
- tests or smoke verification cover aggregate-metric calculation and one small benchmark-aligned evaluation run
- docs explain how to reproduce a reported evaluation artifact from dataset and checkpoint inputs
Out of scope:
- public leaderboard submission automation
- large-scale cluster orchestration beyond current repository boundaries
- paper-writing or claims generation

### Task ID: REPRO-01
Status: todo
Depends on: BENCH-07, EVAL-02
Scope: close the remaining fidelity gaps required for exact paper-style benchmark reproduction and leaderboard comparison
Files:
- `docs/Paper.md`
- `docs/tech.md`
- `docs/tasks.md`
- `README.md`
- implementation files touched by any remaining gap
- `tests/` if targeted verification is added
Implementation notes:
- audit the implemented training, inference, judge, and dataset paths against the paper's reported setup and record a concrete gap list
- identify whether exact reproduction is blocked by unavailable data, proprietary harness details, missing language support, or intentionally reduced-scale training
- only promote a reproduction claim when every blocking gap is either closed or explicitly justified with evidence
- keep this task as the final integration gate rather than a catch-all implementation bucket
Acceptance criteria:
- the repository documents a line-item fidelity checklist between the implemented system and the paper's reported benchmark setup
- any remaining blockers to exact reproduction are explicit, evidence-backed, and linked to concrete upstream tasks or external constraints
- reported benchmark results clearly distinguish exact reproduction from approximate reproduction when applicable
- docs give future agents a single place to see what still prevents a strict paper-level claim
Out of scope:
- inventing new research directions beyond the paper
- production deployment hardening
- unrelated API expansion
