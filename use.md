# AgentConductor Usage

This document is the task-oriented root usage guide for the current repository.
It complements [README.md](/D:/code/PaperCreate/AgentConductor/README.md) and
[API.md](/D:/code/PaperCreate/AgentConductor/API.md).

## Environment

Sync the workspace:

```powershell
uv sync
```

Run the bootstrap entrypoint:

```powershell
uv run python main.py
```

Expected output:

```text
agentconductor: roles=6, max_turns=2
```

## Common Python Calls

### Solve One Problem

```python
from agentconductor import DifficultyLevel, ProblemInstance, solve_problem

result = solve_problem(
    ProblemInstance(
        identifier="apps-two-sum",
        prompt="Write a function that returns two indices adding up to a target.",
        difficulty=DifficultyLevel.EASY,
    ),
    max_turns=2,
)

print(result.status)
print(result.testing_outcome)
print(result.candidate_solution)
print(result.solve_state.completed_turns)
```

Use this when you want the repository to plan and execute a bounded solve loop.

### Solve Through a Trained Checkpoint Boundary

```python
from agentconductor import DifficultyLevel, ProblemInstance, solve_problem

result = solve_problem(
    ProblemInstance(
        identifier="apps-checkpoint",
        prompt="Fix the failing implementation.",
        difficulty=DifficultyLevel.EASY,
    ),
    max_turns=2,
    orchestrator_checkpoint="artifacts/sft-run.json",
)

print(result.notes[1])
print(result.notes[2])
```

Use this when you want online frozen inference to resolve a trained checkpoint
artifact instead of using the deterministic planner directly.
The current checkpoint runtime loads a repository-local
`orchestrator-runtime.json` bundle and supports `orchestrator_device="cpu"`
only.

### Solve With an Explicit Worker Runtime

```python
from agentconductor import (
    DifficultyLevel,
    ProblemInstance,
    RepositoryWorkerModelRuntime,
    solve_problem,
)

result = solve_problem(
    ProblemInstance(
        identifier="apps-workers",
        prompt="Implement a correct solution.",
        difficulty=DifficultyLevel.EASY,
    ),
    worker_runtime=RepositoryWorkerModelRuntime(),
)

first_agent = result.execution.step_results[0].agent_results[0]
print(first_agent.worker_runtime)
print(first_agent.worker_model)
```

Use this when you want to swap or inspect the non-testing worker runtime
explicitly. The testing role still runs through the judge boundary.

### Plan a Typed Topology

```python
from agentconductor import DifficultyLevel, ProblemInstance, plan_problem_topology

topology = plan_problem_topology(
    ProblemInstance(
        identifier="apps-graph",
        prompt="Solve a graph shortest path problem under tight constraints.",
        difficulty=DifficultyLevel.MEDIUM,
    )
)

print(topology.steps)
print(topology.node_count)
```

Without an explicit policy, this uses the deterministic planner.
You can also pass `orchestrator_checkpoint=...` to resolve the learned path
from checkpoint metadata.

### Generate a YAML Candidate Through a Learned Policy Boundary

```python
from agentconductor import (
    DifficultyLevel,
    ProblemInstance,
    TopologyOrchestratorPolicy,
    plan_problem_topology_candidate,
)


class StubPolicy:
    def generate_topology_candidate(self, *, prompt: str, request) -> str:
        return """difficulty: easy
steps:
  - index: 0
    agents:
      - name: planner_0
        role: planning
        refs: []
  - index: 1
    agents:
      - name: coder_1
        role: coding
        refs:
          - step_index: 0
            agent_name: planner_0
  - index: 2
    agents:
      - name: tester_2
        role: testing
        refs:
          - step_index: 1
            agent_name: coder_1
"""


candidate = plan_problem_topology_candidate(
    ProblemInstance(
        identifier="apps-policy",
        prompt="Fix the failing implementation.",
        difficulty=DifficultyLevel.EASY,
    ),
    orchestrator_policy=StubPolicy(),
)

print(candidate.topology_yaml)
print(candidate.topology)
print(candidate.attempt_count)
```

Use this when you need the raw YAML plus the parsed `TopologyPlan`.
The same entrypoint also accepts `orchestrator_checkpoint=...` when you want
the candidate to come from a checkpoint-backed frozen policy.

### Serialize and Parse Topology YAML

```python
from agentconductor import (
    DifficultyLevel,
    ProblemInstance,
    parse_topology_plan_yaml,
    plan_problem_topology,
    serialize_topology_plan_to_yaml,
)

topology = plan_problem_topology(
    ProblemInstance(
        identifier="apps-roundtrip",
        prompt="Implement a correct solution.",
        difficulty=DifficultyLevel.EASY,
    )
)

yaml_text = serialize_topology_plan_to_yaml(topology)
parsed = parse_topology_plan_yaml(yaml_text)

print(yaml_text)
print(parsed == topology)
```

## Command-Line Workflows

### Run Focused Tests

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1 tests\test_api.py
```

Repository-wide preferred command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1
```

### Run Benchmark-Aligned Evaluation

```powershell
uv run python -m agentconductor.interfaces.evaluation --dataset .\tests\fixtures\benchmark\apps_fixture.jsonl --output .\artifacts\eval-results.json --checkpoint .\artifacts\sft-run.json --samples-per-problem 1
```

This path:

- resolves one frozen orchestrator checkpoint explicitly
- loads a canonical benchmark dataset artifact such as APPS JSONL
- runs solve attempts, then re-judges emitted candidates through the benchmark adapter boundary
- writes per-attempt records plus aggregate `pass@1` or `pass@k`
- records dataset version, harness version, runtime mode, checkpoint id,
  reproduction claim, and exact-reproduction readiness in the output artifact

The default evaluation adapter is still the repository-local Python or
JavaScript harness. The benchmark seam now also supports:

- explicit compile or run phase contracts in `BenchmarkExecutionSettings` for
  future compiled-language records
- a Java-first local compiled-language harness for stdin-style benchmark
  records when `javac` and `java` are available
- a separate vendor-native runtime boundary when a benchmark must be evaluated
  through submission plus polling rather than local execution

### Generate SFT Data

```powershell
uv run python -m agentconductor.interfaces.training --dataset .\artifacts\sft-dataset.jsonl --artifact .\artifacts\sft-run.json --sample-count 4500
```

This writes:

- a JSONL dataset with both `target_topology` and `target_topology_yaml`
- a dataset sidecar metadata file with sample count, difficulty breakdown,
  source recipe, prompt-template version, and reduced-scale status
- a training manifest file for YAML-target supervision
- a lightweight checkpoint directory with loadable metadata

### Inspect a Generated SFT Checkpoint

```powershell
uv run python -m agentconductor.interfaces.training --dataset .\artifacts\sft-dataset.jsonl --load-checkpoint .\artifacts\sft-run-checkpoint
```

### Run RL Checkpoint Optimization

```powershell
uv run python -m agentconductor.interfaces.rl --dataset .\artifacts\sft-dataset.jsonl --artifact .\artifacts\rl-run.json --checkpoint .\artifacts\sft-run.json --rollout-count 8 --group-size 8
```

This path:

- resolves one source orchestrator checkpoint from explicit metadata
- collects grouped rollouts through the current bounded solve loop
- writes a rollout manifest, a grouped-update artifact, and an updated checkpoint directory

## Planning Modes

The repository currently supports two topology-planning modes.

- `deterministic`
  Uses repository-local heuristics and template topologies.
- `learned`
  Calls a `TopologyOrchestratorPolicy`, extracts YAML, parses it, validates it,
  and returns explicit failures instead of silently falling back.

Checkpoint-backed frozen inference is an explicit learned sub-mode.

- It accepts a checkpoint directory, checkpoint metadata file, or SFT artifact
  JSON as `orchestrator_checkpoint`.
- If the source directory contains multiple checkpoints, you must also set
  `orchestrator_checkpoint_id`.
- The current repository-local frozen runtime supports `orchestrator_device="cpu"`
  only and loads serialized checkpoint runtime state from
  `orchestrator-runtime.json` rather than relying on metadata-only mock logic.

### Write the Current Reproduction Audit

```powershell
uv run python -m agentconductor.interfaces.reproduction --output .\artifacts\reproduction-audit.json
```

Use this when you need one repository-owned artifact that lists the current
exact-reproduction blockers and the active `approximate` vs `exact` claim.

## Failure Boundaries

Topology and orchestrator failures are intentionally explicit.

- Missing YAML in a policy response raises `TopologyCandidateExtractionError`.
- Malformed YAML raises the parse-layer transport error.
- Schema-invalid topology payloads raise `TopologySchemaError`.
- Logic-invalid topologies raise `TopologyLogicError`.

Benchmark runtime failures are also explicit.

- Compile-phase failures and run-phase failures stay separated in typed
  `BenchmarkPhaseResult` records.
- Missing local compiled-language toolchains surface as explicit adapter errors
  instead of silent skips.
- Vendor-native adapters preserve submission ids, poll history, and terminal
  verdict mapping instead of flattening everything into one local harness log.

## When To Read Which Doc

- Read [README.md](/D:/code/PaperCreate/AgentConductor/README.md) for repository status and scope.
- Read [README_ZH.md](/D:/code/PaperCreate/AgentConductor/README_ZH.md) for the Chinese summary.
- Read [API.md](/D:/code/PaperCreate/AgentConductor/API.md) for the full callable contract.
