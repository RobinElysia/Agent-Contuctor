# AgentConductor

AgentConductor is a backend-oriented Python project that aims to reproduce the method from `2602.17100v1.pdf` as a reusable software system.

The repository currently provides:

- a `src/`-layout Python package managed with `uv`
- typed domain models derived from the paper distillation
- a stable Python solve API for deterministic planning plus bounded multi-turn execution
- a typed multi-turn solve-state contract for turn history and later revision
- a deterministic topology planner that emits validated single-turn plans
- a deterministic single-turn graph executor for validated plans
- focused tests for the bootstrap and API layers

The repository does not yet implement the full paper runtime. The current API can run up to the configured turn budget with deterministic topology revision, but it still does not support sandbox-backed evaluation.

## Current Status

Completed milestones:

- `DOC-01`: repository guidance and durable project docs
- `RES-01`: implementation-oriented paper distillation in `docs/Paper.md`
- `BOOT-01`: package bootstrap, entrypoint, and tests
- `API-01`: first typed callable API boundary
- `TOP-01`: single-turn topology schema and validation
- `ORCH-01`: deterministic rule-based topology planning
- `EXEC-01`: deterministic single-turn topology execution

Not yet implemented:

- topology YAML generation
- sandbox-backed code execution
- training or RL reproduction

## Project Layout

```text
.
|-- AGENTS.md
|-- API.md
|-- docs/
|-- src/agentconductor/
|   |-- application/
|   |-- domain/
|   `-- interfaces/
`-- tests/
```

Key locations:

- `docs/requirements.md`: product and delivery constraints
- `docs/tech.md`: architecture and verification rules
- `docs/tasks.md`: task cards and current task status
- `docs/Paper.md`: implementation-oriented paper distillation
- `src/agentconductor/domain/`: typed core contracts
- `src/agentconductor/application/`: application services
- `src/agentconductor/interfaces/`: public entrypoints
- `API.md`: caller-oriented API documentation

## Requirements

- Python `>=3.11`
- `uv` for environment and dependency management

## Quick Start

Create or sync the environment:

```powershell
uv sync
```

Run the current CLI entrypoint:

```powershell
uv run python main.py
```

Or use the package script:

```powershell
uv run agentconductor
```

Expected output:

```text
agentconductor: roles=6, max_turns=2
```

## Python API

The stable package entrypoints are `solve_problem(...)`, `plan_problem_topology(...)`, and `execute_topology_plan(...)`.

```python
from agentconductor import (
    DifficultyLevel,
    ProblemInstance,
    execute_topology_plan,
    plan_problem_topology,
    solve_problem,
)

topology = plan_problem_topology(
    ProblemInstance(
        identifier="apps-graph",
        prompt="Solve a graph shortest path problem under tight constraints.",
        difficulty=DifficultyLevel.MEDIUM,
    )
)

result = solve_problem(
    ProblemInstance(
        identifier="apps-two-sum",
        prompt="Write a function that returns two indices adding up to a target.",
        difficulty=DifficultyLevel.EASY,
    )
)

execution = execute_topology_plan(
    ProblemInstance(
        identifier="apps-two-sum",
        prompt="Write a function that returns two indices adding up to a target.",
        difficulty=DifficultyLevel.EASY,
    ),
    topology,
)

print(topology.steps)
print(result.status)
print(result.candidate_solution)
print(result.testing_outcome)
print(result.solve_state.completed_turns)
print(execution.testing_outcome)
```

The planning API can return a typed `TopologyPlan`, and `solve_problem(...)` now returns a typed `SolveResult` that includes:

- selected difficulty
- allowed turn budget
- difficulty-specific node budget
- currently available role set
- the planned topology
- a structured execution result
- candidate solution content
- final testing outcome
- a typed solve state with turn history and revision-ready feedback

The execution API can return a typed `TopologyExecutionResult` with:

- per-step and per-agent structured outputs
- resolved upstream references for each agent
- final candidate code
- deterministic testing outcome and diagnostics

See [API.md](/D:/code/PaperCreate/AgentConductor/API.md) for the full interface contract.

## Testing

Run the focused test suite:

```powershell
uv run pytest tests/test_bootstrap.py tests/test_api.py tests/test_topology.py tests/test_orchestrator.py tests/test_execution.py
```

## Design Notes

- The package keeps paper-method logic, application orchestration, and interfaces separated.
- The first API is intentionally narrow. It is a stable Python boundary, not an HTTP service.
- The executor is deliberately deterministic and local. It verifies control-flow semantics before sandbox integration.
- When behavior is inferred rather than stated by the paper, the repository documents that explicitly.

## Next Likely Steps

- integrate real sandbox-backed testing
- add training and RL reproduction paths
