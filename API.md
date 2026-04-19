# AgentConductor API

This document describes the current stable Python API exposed by the repository root package.

The API is still in an early milestone. It currently provides:

- a typed solve entrypoint with deterministic planning and single-turn execution
- a typed multi-turn solve-state contract that records per-turn history
- a deterministic topology-planning entrypoint
- a deterministic single-turn topology-execution entrypoint
- typed topology schema objects for single-turn plans
- validation rules for topology structure before execution

The repository does not yet execute the full multi-turn AgentConductor method.

## Public Entry Points

Stable callable API:

- `agentconductor.solve_problem`
- `agentconductor.plan_problem_topology`
- `agentconductor.execute_topology_plan`

Stable public topology contract:

- `agentconductor.TopologyPlan`
- `agentconductor.TopologyStep`
- `agentconductor.AgentInvocation`
- `agentconductor.AgentReference`
- `agentconductor.AgentRole`
- `agentconductor.TopologyValidationError`

Other public types:

- `agentconductor.AgentExecutionResult`
- `agentconductor.StepExecutionResult`
- `agentconductor.TopologyExecutionResult`
- `agentconductor.ExecutionStatus`
- `agentconductor.TestingOutcome`
- `agentconductor.TopologyExecutionError`
- `agentconductor.SolveState`
- `agentconductor.SolveTurnRecord`
- `agentconductor.TestingFeedback`
- `agentconductor.TopologyRevisionInput`
- `agentconductor.StopReason`
- `agentconductor.SolveStateTransitionError`
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
from agentconductor import (
    ProblemInstance,
    TopologyPlan,
    execute_topology_plan,
    plan_problem_topology,
    solve_problem,
)
```

## Solve API

### `solve_problem(problem, *, max_turns=None) -> SolveResult`

Plan and execute a structured single-turn solve for a problem instance.

Parameters:

- `problem: ProblemInstance`
- `max_turns: int | None = None`

Behavior:

- uses the explicit difficulty from `problem` when present
- defaults missing difficulty to `DifficultyLevel.MEDIUM`
- validates the turn budget against the current baseline limit
- generates a deterministic single-turn topology
- executes that topology with the current local role registry
- returns candidate code, role trace, and final testing outcome

Returned `SolveResult` fields:

- `status`
- `selected_difficulty`
- `planned_turns`
- `max_nodes`
- `available_roles`
- `topology`
- `execution`
- `candidate_solution`
- `testing_outcome`
- `solve_state`
- `notes`

Implementation inference:

- the medium-difficulty fallback is an engineering inference until the repository implements the paper's real difficulty inference mechanism
- the current solve path is limited to one deterministic turn; it records turn history now, but does not yet revise topology from that history

## Multi-Turn Solve-State Contract

The repository now exposes a typed solve-state object so later multi-turn logic
can compose around the current single-turn executor without changing earlier
execution contracts.

### `SolveState`

```python
SolveState(
    problem: ProblemInstance,
    selected_difficulty: DifficultyLevel,
    max_turns: int,
    max_nodes: int,
    available_roles: tuple[str, ...],
    turns: tuple[SolveTurnRecord, ...] = (),
    stop_reason: StopReason | None = None,
)
```

Properties:

- `completed_turns`
- `remaining_turns`
- `can_continue`
- `latest_turn`

### `SolveTurnRecord`

```python
SolveTurnRecord(
    turn_index: int,
    topology: TopologyPlan,
    execution: TopologyExecutionResult,
    testing_feedback: TestingFeedback,
)
```

### `TestingFeedback`

```python
TestingFeedback(
    outcome: TestingOutcome | None,
    diagnostics: tuple[str, ...],
    candidate_code: str | None,
)
```

### `TopologyRevisionInput`

```python
TopologyRevisionInput(
    problem: ProblemInstance,
    selected_difficulty: DifficultyLevel,
    turn_index: int,
    prior_topology: TopologyPlan,
    prior_execution_status: ExecutionStatus,
    testing_feedback: TestingFeedback,
    remaining_turns: int,
)
```

### `StopReason`

Enum values:

- `solved`
- `turn_budget_exhausted`

Implementation inference:

- the paper describes global history and testing feedback, but not a repository-level typed state object
- `TopologyRevisionInput` is a repository-local contract so later revision logic can consume structured prior-turn artifacts instead of raw strings only

## Topology Execution API

### `execute_topology_plan(problem, topology) -> TopologyExecutionResult`

Execute a validated single-turn topology plan layer by layer.

Behavior:

- validates the topology before execution
- executes steps in index order
- resolves references only from prior executed steps
- dispatches each agent through a deterministic role registry
- returns structured per-agent outputs, final candidate code, and final testing outcome

Implementation inference:

- the current role registry uses deterministic rule-based role handlers so execution semantics can be verified before sandbox or model integration

## Topology Planning API

### `plan_problem_topology(problem) -> TopologyPlan`

Return a deterministic topology plan for a problem instance.

Behavior:

- uses the explicit problem difficulty when present
- defaults missing difficulty to `DifficultyLevel.MEDIUM`
- infers a coarse local problem shape from prompt keywords
- selects one of a small set of topology templates
- returns a validated single-turn `TopologyPlan`

Implementation inference:

- prompt-shape inference is a repository-local heuristic, not a paper-defined mechanism
- the current orchestrator is deterministic and local so it can later be replaced by a learned policy

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
                ],
            },
            {
                "index": 2,
                "agents": [
                    {
                        "name": "tester_2",
                        "role": "testing",
                        "refs": [
                            {"step_index": 0, "agent_name": "planner_0"},
                            {"step_index": 1, "agent_name": "coder_1"},
                        ],
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
- run code in a sandbox
- revise topology over multiple turns

It currently does:

- expose typed topology contracts
- expose typed multi-turn state and revision-input contracts
- parse single-turn topologies from plain mappings
- validate paper-aligned topology structure
- emit deterministic topology plans for supported difficulty tiers
- execute single-turn topologies with deterministic role handlers
- return candidate code and structured execution traces from `solve_problem(...)`

## Source References

Implementation files:

- [src/agentconductor/domain/topology.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/domain/topology.py)
- [src/agentconductor/application/orchestrator.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/application/orchestrator.py)
- [src/agentconductor/interfaces/planning.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/interfaces/planning.py)
- [src/agentconductor/interfaces/api.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/interfaces/api.py)
- [src/agentconductor/application/api.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/application/api.py)
- [src/agentconductor/application/history.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/application/history.py)
- [src/agentconductor/domain/history.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/domain/history.py)
- [src/agentconductor/domain/models.py](/D:/code/PaperCreate/AgentConductor/src/agentconductor/domain/models.py)
