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
Status: todo
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
Status: todo
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
Status: todo
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
