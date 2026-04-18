# AgentConductor API

This document describes the current stable Python API exposed by the repository root package.

The API is still in an early milestone. It currently provides:

- a typed solve-planning entrypoint
- typed topology schema objects for single-turn plans
- validation rules for topology structure before execution

The repository does not yet execute the full AgentConductor method.

## Public Entry Points

Stable callable API:

- `agentconductor.solve_problem`

Stable public topology contract:

- `agentconductor.TopologyPlan`
- `agentconductor.TopologyStep`
- `agentconductor.AgentInvocation`
- `agentconductor.AgentReference`
- `agentconductor.AgentRole`
- `agentconductor.TopologyValidationError`

Other public types:

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

Then import from Python:

```python
from agentconductor import ProblemInstance, TopologyPlan, solve_problem
```

## Solve API

### `solve_problem(problem, *, max_turns=None) -> SolveResult`

Prepare a structured solve plan for a problem instance.

Parameters:

- `problem: ProblemInstance`
- `max_turns: int | None = None`

Behavior:

- uses the explicit difficulty from `problem` when present
- defaults missing difficulty to `DifficultyLevel.MEDIUM`
- validates the turn budget against the current baseline limit

Implementation inference:

- the medium-difficulty fallback is an engineering inference until the repository implements the paper's real difficulty inference mechanism

## Topology Schema

### `TopologyPlan`

```python
TopologyPlan(
    difficulty: DifficultyLevel,
    steps: tuple[TopologyStep, ...],
)
```

Current scope:

- single-turn topology only
- layered DAG structure
- dependency-free parsing from plain mappings via `TopologyPlan.from_mapping(...)`

Properties:

- `node_count`
- `max_nodes`

Methods:

- `validate() -> None`
- `from_mapping(raw_plan: Mapping[str, Any]) -> TopologyPlan`

### `TopologyStep`

```python
TopologyStep(
    index: int,
    agents: tuple[AgentInvocation, ...],
)
```

### `AgentInvocation`

```python
AgentInvocation(
    name: str,
    role: AgentRole,
    refs: tuple[AgentReference, ...] = (),
)
```

### `AgentReference`

```python
AgentReference(
    step_index: int,
    agent_name: str,
)
```

### `AgentRole`

Enum values:

- `retrieval`
- `planning`
- `algorithmic`
- `coding`
- `debugging`
- `testing`

## Validation Rules

The current topology validator enforces these constraints:

- the plan must contain at least one step
- step indices must be contiguous and zero-based
- every step must contain at least one agent
- agent names must be unique across the full topology
- the first step must not contain references
- references may target earlier steps only
- references must point to known prior agent names
- the final step must contain a testing agent
- the total node count must stay within the paper-derived difficulty budget

Difficulty-specific node budgets:

- `easy`: `4`
- `medium`: `7`
- `hard`: `10`

Implementation inference:

- the paper does not define a full concrete schema; `from_mapping(...)` is a repository-local parsing contract used until a YAML adapter is added

## Topology Parsing Example

```python
from agentconductor import TopologyPlan

plan = TopologyPlan.from_mapping(
    {
        "difficulty": "easy",
        "steps": [
            {
                "index": 0,
                "agents": [
                    {"name": "planner_0", "role": "planning", "refs": []},
                ],
            },
            {
                "index": 1,
                "agents": [
                    {
                        "name": "coder_1",
                        "role": "coding",
                        "refs": [{"step_index": 0, "agent_name": "planner_0"}],
                    },
                    {
                        "name": "tester_1",
                        "role": "testing",
                        "refs": [{"step_index": 0, "agent_name": "planner_0"}],
                    },
                ],
            },
        ],
    }
)
```

## Current Limits

The repository currently does not:

- generate topology YAML from an orchestrator
- execute the graph
- run code in a sandbox
- revise topology over multiple turns
- return candidate code from `solve_problem(...)`

It currently does:

- expose typed topology contracts
- parse single-turn topologies from plain mappings
- validate paper-aligned topology structure
- expose a narrow typed planning API for callers

## Source References

Implementation files:

- [src/agentconductor/domain/topology.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/domain/topology.py)
- [src/agentconductor/interfaces/api.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/interfaces/api.py)
- [src/agentconductor/application/api.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/application/api.py)
- [src/agentconductor/domain/models.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/domain/models.py)
