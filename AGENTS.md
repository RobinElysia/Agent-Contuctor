# AGENTS.md

## Mission
AgentConductor is a Python project that aims to reproduce the methods from `2602.17100v1.pdf` as a reusable software system. The repository should evolve toward:

- a clear implementation of the paper's method
- a stable Python package managed with `uv`
- an API layer that other projects can call
- documentation that allows future agents to continue work with minimal ambiguity

## Working Principles

1. Read local documentation before changing code.
2. Prefer small, composable modules over large scripts.
3. Keep code aligned with the paper's method, not with speculative features.
4. Preserve reproducibility: deterministic configuration, explicit dependencies, and testable interfaces.
5. Update documentation when architecture or assumptions change.

## Source of Truth

Use the following priority when making decisions:

1. User instructions in the current session
2. This `AGENTS.md`
3. Files in `docs/`, especially `docs/requirements.md`, `docs/tech.md`, `docs/tasks.md`, and `docs/Paper.md`
4. Existing code and tests
5. Temporary assumptions made by the current agent

If these sources conflict, follow the higher-priority source and document the deviation.

## Repository Expectations

The repository should gradually converge on this structure:

- `docs/requirements.md`: product and delivery requirements
- `docs/Paper.md`: structured understanding of the target paper
- `docs/tech.md`: technical strategy and architecture constraints
- `docs/tasks.md`: executable task cards
- `docs/Codex.md`: Codex-oriented execution constraints
- `docs/ClaudeCode.md`: Claude Code-oriented execution constraints
- `src/agentconductor/`: main package implementation
- `tests/`: automated tests

Current repository state may lag behind this target. Agents may create missing files when needed.

## Implementation Constraints

- Use Python `>=3.11`.
- Use `uv` for dependency and environment management.
- Prefer a `src/` layout once implementation begins.
- Favor typed Python, dataclasses or pydantic-style schemas where appropriate, and explicit interfaces.
- Keep I/O boundaries isolated from core paper logic.
- Separate paper-method logic, orchestration logic, and API adapters.

## Documentation Constraints

- Write durable documentation in English unless the user asks for another language.
- Keep requirement, architecture, and research notes separate.
- When a design decision is inferred rather than stated in the paper, label it explicitly as an inference.
- Avoid copying long passages from the paper; summarize and transform them into implementation guidance.

## Context Management

To reduce drift across agent sessions:

- restate the active goal before major edits
- inspect existing files before changing them
- record durable conclusions in docs instead of relying on chat history
- prefer incremental edits over broad rewrites
- surface blockers early when the paper or requirements are ambiguous

## Entropy Management

Agents should actively reduce project entropy:

- remove placeholder descriptions when real intent is known
- avoid duplicate definitions of architecture or workflow
- keep filenames and module names stable and descriptive
- do not introduce optional frameworks without a concrete need
- convert implicit assumptions into documented constraints

## Definition of Progress

A task is considered complete only when applicable changes include:

- implementation or document updates
- consistency with existing repository structure
- basic verification appropriate to the change
- a short explanation of what changed and what remains open

## Near-Term Priorities

1. Establish agent guidance documents.
2. Read and distill `2602.17100v1.pdf` into `docs/Paper.md`.
3. Replace placeholder project metadata and dependencies in `pyproject.toml`.
4. Create initial package structure and tests.
