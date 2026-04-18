# AgentConductor API

This document describes the current stable Python API exposed by the repository root package.

The API in this milestone is intentionally narrow. It provides a typed entrypoint for callers who want a paper-aligned solve plan. It does not yet execute the full AgentConductor method.

## Stability

Current stable entrypoint:

- `agentconductor.solve_problem`

Supporting public types:

- `agentconductor.ProblemInstance`
- `agentconductor.DifficultyLevel`
- `agentconductor.SolveRequest`
- `agentconductor.SolveResult`
- `agentconductor.SolveStatus`

## Installation and Import

From the repository root:

```powershell
uv sync
```

Then use the package from Python:

```python
from agentconductor import DifficultyLevel, ProblemInstance, solve_problem
```

## Entry Point

### `solve_problem(problem, *, max_turns=None) -> SolveResult`

Prepare a structured solve plan for a problem instance.

Parameters:

- `problem: ProblemInstance`
  The problem descriptor supplied by the caller.
- `max_turns: int | None = None`
  Optional override for the number of planned interaction turns.

Behavior:

- If `problem.difficulty` is provided, the API uses it directly.
- If `problem.difficulty` is omitted, the current baseline defaults to `DifficultyLevel.MEDIUM`.
- If `max_turns` is omitted, the API uses the current baseline limit from project bootstrap data.
- If `max_turns < 1`, the API raises `ValueError`.
- If `max_turns` exceeds the current baseline limit, the API raises `ValueError`.

Implementation inference:

- The default difficulty fallback is an engineering inference, not a direct paper fact. The paper says difficulty is inferred by the orchestrator, but the repository does not yet implement that inference mechanism.

## Input Types

### `DifficultyLevel`

String enum values:

- `DifficultyLevel.EASY`
- `DifficultyLevel.MEDIUM`
- `DifficultyLevel.HARD`

### `ProblemInstance`

```python
ProblemInstance(
    identifier: str,
    prompt: str,
    difficulty: DifficultyLevel | None = None,
)
```

Fields:

- `identifier`
  Stable caller-defined problem id.
- `prompt`
  Natural-language problem statement or task prompt.
- `difficulty`
  Optional explicit difficulty tier.

### `SolveRequest`

```python
SolveRequest(
    problem: ProblemInstance,
    max_turns: int | None = None,
)
```

This type exists as a public contract for the application boundary, although most external callers can use `solve_problem(...)` directly.

## Output Type

### `SolveResult`

```python
SolveResult(
    problem_id: str,
    status: SolveStatus,
    selected_difficulty: DifficultyLevel,
    planned_turns: int,
    max_nodes: int,
    available_roles: tuple[str, ...],
    notes: tuple[str, ...],
)
```

Fields:

- `problem_id`
  Echoes the input problem identifier.
- `status`
  Current solve state. The present baseline only returns `SolveStatus.PLANNED`.
- `selected_difficulty`
  Effective difficulty used by the baseline.
- `planned_turns`
  Number of interaction turns allocated by the baseline.
- `max_nodes`
  Difficulty-specific topology node cap derived from the paper summary.
- `available_roles`
  Role names currently recognized by the baseline.
- `notes`
  Human-readable notes describing the current execution boundary.

### `SolveStatus`

Current enum values:

- `SolveStatus.PLANNED`

## Example

```python
from agentconductor import DifficultyLevel, ProblemInstance, solve_problem

result = solve_problem(
    ProblemInstance(
        identifier="apps-two-sum",
        prompt="Write a function that returns two indices adding up to a target.",
        difficulty=DifficultyLevel.EASY,
    ),
    max_turns=1,
)

assert result.problem_id == "apps-two-sum"
assert result.selected_difficulty == DifficultyLevel.EASY
assert result.planned_turns == 1
assert result.max_nodes == 4
assert result.status.value == "planned"
```

## Current Limits

The API currently does not:

- generate topology YAML
- execute agents
- run code in a sandbox
- revise plans across failed turns
- return candidate code

It currently does:

- expose a typed package boundary for callers
- validate turn-budget constraints
- map difficulty to node-budget constraints
- return a structured baseline planning result

## Source References

Implementation files:

- [src/agentconductor/interfaces/api.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/interfaces/api.py)
- [src/agentconductor/application/api.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/application/api.py)
- [src/agentconductor/domain/models.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/domain/models.py)
