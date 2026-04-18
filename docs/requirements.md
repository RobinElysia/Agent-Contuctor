# Project Requirements

## Purpose
AgentConductor is a backend-oriented Python project that aims to reproduce the method described in `2602.17100v1.pdf` as a reusable software system. The repository should not stop at a one-off experiment. It should converge on a maintainable package, a callable API surface, and durable implementation documentation.

## Requirement Hierarchy

This repository uses a layered documentation model:

1. `AGENTS.md`
   Repository-wide collaboration rules and engineering discipline.
2. `docs/requirements.md`
   Product scope, target outcomes, and domain-level constraints.
3. `docs/tech.md`
   Technical implementation strategy and architectural boundaries.
4. `docs/tasks.md`
   Executable work units with scope, files, and acceptance criteria.
5. `docs/Codex.md` and `docs/ClaudeCode.md`
   Agent-specific execution constraints.

If these documents conflict, the higher item in the list wins unless the user explicitly overrides it.

## End Goal

The end goal is to build a Python package that:

- reproduces the paper's method in an engineering-ready form
- exposes the method through stable internal interfaces
- provides an API that can be called by other projects
- remains reproducible, inspectable, and testable

## Phase Goals

The project should advance through the following phases:

1. Constraint and documentation setup
   Deliver project rules, agent rules, and a stable document hierarchy.
2. Paper distillation
   Read `2602.17100v1.pdf` and convert the method into `docs/Paper.md`.
3. Project bootstrap
   Replace placeholder metadata, define dependencies, and establish package structure.
4. Method implementation
   Implement the paper method as typed Python modules with tests.
5. API exposure
   Provide a clean programmatic API and, if needed later, a transport layer such as CLI or HTTP.

## Functional Requirements

- The repository must preserve a clear mapping between paper concepts and implementation modules.
- Core logic must be callable without requiring a command-line workflow.
- The system must support reuse by external callers through a documented API boundary.
- Important assumptions that are not explicitly stated in the paper must be documented as inferences.

## Non-Functional Requirements

- Python version: `>=3.11`
- Dependency management: `uv`
- Code quality: typed, testable, and modular
- Reproducibility: explicit configuration and deterministic behavior where feasible
- Documentation quality: durable, implementation-oriented, and written in English

## Out of Scope for Early Phases

- speculative feature additions not justified by the paper
- broad framework adoption without a concrete need
- production deployment infrastructure
- premature optimization before the method is correctly reproduced

## Deliverable Expectations

Each substantial milestone should leave behind:

- code or documentation updates in the repository
- explicit verification evidence appropriate to the change
- enough written context for a future agent to continue without relying on chat history
- synchronized task tracking: when work completes a task card in `docs/tasks.md`, the task status must be updated in the same change
