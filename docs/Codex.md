# Codex Execution Constraints

## Purpose
This document defines how Codex should operate inside AgentConductor. Codex is expected to execute with strong repository discipline, not with generic backend assumptions.

## Required Reading Order

Before substantial work, Codex should read in this order:

1. the current user instruction
2. `AGENTS.md`
3. `docs/tasks.md`
4. `docs/tech.md`
5. `docs/requirements.md`
6. task-relevant code or source material

Codex should not treat default model intuition as authoritative when repository documents already define the boundary.

## Primary Responsibilities

Codex should:

- identify the smallest complete change that advances the current task
- keep implementation aligned with the layered document model
- preserve user changes and existing repository intent
- turn durable findings into repository documentation

## Mandatory Pre-Edit Check

Before editing, Codex should be able to state:

- the hard constraints relevant to the task
- the exact scope boundary
- the files it expects to change
- the verification it expects to run

If document/code drift is found, Codex should report it before building new work on top of the drift.

## Backend-Specific Engineering Rules

- Keep paper-method logic inside package modules, not root scripts.
- Keep transport adapters thin; the API boundary should call reusable application logic.
- Prefer explicit schemas, typed interfaces, and deterministic behavior where possible.
- Do not add heavyweight frameworks without a concrete need.
- Do not blend domain logic, orchestration, and I/O into the same module.

## Safety Rules

- Never revert or delete user work unless explicitly asked.
- Avoid destructive git operations.
- Prefer local repository evidence over memory.
- Ask for clarification only when the risk of a wrong assumption is material.

## Entropy Control

Codex should reduce entropy by:

- replacing placeholders with concrete project intent
- avoiding duplicate guidance across files
- keeping naming aligned across docs and code
- documenting inferences instead of hiding them in implementation

## Verification Expectations

- Run focused verification for the changed scope when possible.
- Expand to broader verification only when justified by the change.
- If verification is skipped or blocked, say so explicitly.

## Final Output

Codex should report:

- what changed
- what was verified
- what remains open or risky
