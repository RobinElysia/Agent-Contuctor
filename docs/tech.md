# Technical Strategy

## Purpose
This document defines how AgentConductor should be built. It exists to convert product intent into engineering constraints that are concrete enough for agents to execute without inventing architecture.

## Instruction Priority

When making technical decisions, use this order:

1. current user instruction
2. `AGENTS.md`
3. `docs/tasks.md`
4. `docs/tech.md`
5. `docs/requirements.md`
6. current codebase state
7. default model assumptions

If code and documents drift apart, agents must report the drift before expanding the implementation on top of it.

## Architecture Principles

The repository should evolve toward a layered backend architecture:

- `domain`
  Core paper concepts, algorithms, and typed entities.
- `application`
  Use cases, orchestration, and workflow composition.
- `infrastructure`
  File I/O, external integrations, persistence, or runtime adapters.
- `interfaces`
  CLI, API, or other entrypoints that call application services.

The exact folder names may evolve, but the separation of responsibilities must remain clear.

## Code Organization Rules

- Prefer a `src/` layout for production code.
- Keep the package importable without depending on scripts in the repository root.
- Keep command-line entrypoints thin; paper logic must live in package modules.
- Isolate parsing, configuration loading, and transport concerns from method logic.
- Use absolute package imports once the package layout exists.

## Dependency Policy

- Prefer the standard library unless a dependency clearly reduces complexity or risk.
- Do not add a new dependency without a concrete implementation need.
- Record the purpose of important dependencies in code comments, docs, or commit context.
- Avoid overlapping libraries that solve the same problem.

## Typing and Data Contracts

- Public functions should use explicit type hints.
- Structured inputs and outputs should use clear schema objects when plain primitives are no longer sufficient.
- Configuration should be explicit and validated.
- Error handling should be narrow and intentional rather than broad `except Exception` fallbacks.

## Testing Strategy

- Core paper logic should have direct unit tests.
- Integration tests should cover boundary wiring only where it adds confidence.
- Tests should focus on behavior, invariants, and edge cases derived from the paper.
- If the method relies on stochastic behavior, document how determinism or tolerance is handled in tests.

## Verification Rules

For code changes, agents should run the smallest relevant verification set first, then broader checks if available. Typical verification should include:

- focused tests for changed modules
- a repository-level test command when available
- basic import or entrypoint verification for new package boundaries

If verification cannot be run, the agent must say so explicitly and explain why.

## Documentation Drift Control

Agents must perform a drift check before substantial implementation work:

- compare the current codebase with `AGENTS.md`, `docs/requirements.md`, and `docs/tasks.md`
- list important mismatches
- avoid silently treating current code as the only source of truth

## Anti-Patterns

Do not:

- mix research notes, implementation notes, and task tracking in the same file
- put paper-method logic directly in root scripts
- create large utility modules with unrelated responsibilities
- introduce hidden global state to coordinate workflows
- expand API surfaces before the underlying method boundary is stable
