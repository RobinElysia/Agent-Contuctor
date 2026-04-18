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
