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
Status: todo
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

### Task ID: DEVX-01
Status: todo
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

### Task ID: DIST-01
Status: todo
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
Status: todo
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
Status: todo
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
Status: todo
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
