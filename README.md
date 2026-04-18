# AgentConductor

AgentConductor is a backend-oriented Python project that aims to reproduce the method from `2602.17100v1.pdf` as a reusable software system.

The repository currently provides:

- a `src/`-layout Python package managed with `uv`
- typed domain models derived from the paper distillation
- a first stable Python API boundary for problem-oriented calls
- focused tests for the bootstrap and API layers

The repository does not yet implement the full paper runtime. The current API returns a structured solve plan aligned with paper constraints, not a completed topology execution result.

## Current Status

Completed milestones:

- `DOC-01`: repository guidance and durable project docs
- `RES-01`: implementation-oriented paper distillation in `docs/Paper.md`
- `BOOT-01`: package bootstrap, entrypoint, and tests
- `API-01`: first typed callable API boundary

Not yet implemented:

- topology YAML generation
- topology validation and graph execution
- sandbox-backed code execution
- multi-turn topology refinement
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

The stable package entrypoint is `solve_problem(...)`.

```python
from agentconductor import DifficultyLevel, ProblemInstance, solve_problem

result = solve_problem(
    ProblemInstance(
        identifier="apps-two-sum",
        prompt="Write a function that returns two indices adding up to a target.",
        difficulty=DifficultyLevel.EASY,
    )
)

print(result.status)
print(result.max_nodes)
```

The current API returns a typed `SolveResult` describing the baseline plan:

- selected difficulty
- allowed turn budget
- difficulty-specific node budget
- currently available role set
- implementation notes about what remains unimplemented

See [API.md](/D:/code/PaperCreate/AgentConductor/API.md) for the full interface contract.

## Testing

Run the focused test suite:

```powershell
uv run pytest tests/test_bootstrap.py tests/test_api.py
```

## Design Notes

- The package keeps paper-method logic, application orchestration, and interfaces separated.
- The first API is intentionally narrow. It is a stable Python boundary, not an HTTP service.
- When behavior is inferred rather than stated by the paper, the repository documents that explicitly.

## Next Likely Steps

- define the topology schema and validator
- implement graph execution over layered agent steps
- connect solve requests to real topology generation
- add structured execution feedback and turn history
