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

For runtime evaluation, candidate testing must stay behind a narrow adapter
boundary. Application services may request candidate evaluation, but they
should not embed subprocess orchestration or judge-specific details directly.
External benchmark integrations should follow the same pattern: keep benchmark
wire formats, artifact identifiers, and native verdict payloads inside a typed
adapter seam instead of leaking them into solve or training services.
Benchmark dataset ingestion should also normalize source-specific layouts into
canonical repository records before training or evaluation services consume the
problems, so split metadata and source identifiers stay reproducible without
coupling the rest of the codebase to one vendor schema.
When benchmark datasets also carry executable metadata, that metadata should be
normalized into typed benchmark-owned invocation settings and test cases before
any local subprocess judge or runtime adapter consumes it.
Current repository benchmark execution supports Python and JavaScript as
explicit runtime selections. Language dispatch should stay inside
infrastructure adapters rather than leaking language-specific branching into
application services.
For stdin-style benchmark records, adapters should prefer standalone script
execution over repository-owned `solve()` wrappers so the remaining fidelity
gaps stay narrow and documented.

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
- Judge-backed tests should exercise the adapter boundary with concrete passing
  and failing candidate code, while keeping local fidelity limits explicit.
- When the repository approximates benchmark semantics, tests and docs should
  state the exact approximation boundary, such as output normalization rules or
  whether per-case verdicts are preserved.
- When sandbox resource limits are platform-dependent, docs must distinguish
  hard subprocess or OS-enforced guarantees from repository-local fallback
  approximations such as traced-memory checks.
- Windows-specific sandbox paths should keep Job Object details inside
  infrastructure helpers and document when host-level job constraints force an
  explicit downgrade back to wall-clock-only hard enforcement.
- Windows CPU-limit semantics must remain explicitly separated from wall-clock
  enforcement. Until a stable Job Object CPU strategy is verified, the runtime
  should report CPU enforcement as unsupported or provisional rather than
  implying POSIX-equivalent hard limits.

## Verification Rules

For code changes, agents should run the smallest relevant verification set first, then broader checks if available. Typical verification should include:

- focused tests for changed modules
- a repository-level test command when available
- basic import or entrypoint verification for new package boundaries

If verification cannot be run, the agent must say so explicitly and explain why.

Repository verification commands should remain reproducible under restricted
local environments:

- prefer `powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1` as the
  repository-level test command on Windows because it defaults `UV_CACHE_DIR`
  to the repository-local `.uv-cache` directory
- keep `uv run pytest` documented as the simpler path when cache permissions are
  already available
- when wrappers are not available, document the explicit environment variables
  needed to keep `uv` away from undeclared user-global cache paths

For batch or distributed evaluation work:

- keep job submission, worker execution, and result collection as explicit
  orchestration concerns rather than embedding them inside judge adapters
- preserve a single-worker path for local fallback and focused verification
- make worker count, retry count, and collection timeout explicit and inspectable

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
