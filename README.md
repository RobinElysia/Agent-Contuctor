# AgentConductor

AgentConductor is a backend-oriented Python project that aims to reproduce the method from `2602.17100v1.pdf` as a reusable software system.

The repository currently provides:

- a `src/`-layout Python package managed with `uv`
- typed domain models derived from the paper distillation
- a stable Python solve API for bounded multi-turn execution over deterministic or learned orchestrator paths
- a typed multi-turn solve-state contract for turn history and later revision
- a deterministic topology planner that emits validated single-turn plans
- a learned-orchestrator policy boundary that produces topology YAML candidates and parses them into validated typed plans
- a single-turn graph executor whose testing role runs through a local subprocess judge adapter
- a typed external benchmark adapter seam for benchmark metadata, verdict normalization, and run artifact identifiers
- canonical benchmark dataset ingestion for APPS-style JSONL records
- a multi-language benchmark execution path for Python and JavaScript canonical benchmark records
- focused tests for the bootstrap and API layers

The repository does not yet implement the full paper runtime. The current API can run up to the configured turn budget with deterministic topology revision and local judge-backed evaluation, but the judge remains a repository-local approximation rather than an exact benchmark integration.

## Current Status

Completed milestones:

- `DOC-01`: repository guidance and durable project docs
- `RES-01`: implementation-oriented paper distillation in `docs/Paper.md`
- `BOOT-01`: package bootstrap, entrypoint, and tests
- `API-01`: first typed callable API boundary
- `TOP-01`: single-turn topology schema and validation
- `TOP-02`: YAML-native topology serialization and parsing around the typed topology contract
- `ORCH-01`: deterministic rule-based topology planning
- `ORCH-02`: model-backed YAML orchestration boundary for frozen inference and later-turn revision
- `EXEC-01`: deterministic single-turn topology execution
- `JUDGE-01`: richer subprocess judge boundary with explicit test cases and soft resource limits
- `JUDGE-02`: stricter judge normalization and typed per-case verdict reporting
- `SBX-02`: stronger per-case subprocess enforcement for wall-clock limits, with platform-aware CPU and memory controls
- `SBX-03`: Windows Job Object-backed worker binding for hard memory limits where the host runtime permits dedicated job assignment
- `DEVX-01`: repository-local `uv` verification path for restricted cache environments
- `SBX-04`: explicit Windows breakaway-launch and downgrade reporting for host runtimes that forbid dedicated Job attachment
- `SBX-05`: typed Windows CPU-limit capability reporting that marks CPU enforcement unsupported until a verified strategy exists
- `DIST-01`: local distributed evaluation boundary for parallel candidate judging with explicit concurrency, retry, and collection-timeout controls
- `EVAL-01`: JSON-backed batch evaluation pipeline that records per-problem outcomes and aggregate summaries
- `TRAIN-01`: synthetic topology dataset generation plus a reproducible SFT baseline artifact path
- `RL-01`: repository-local reward breakdown and RL-style rollout artifact generation
- `BENCH-01`: typed external benchmark adapter seam for execution metadata and verdict mapping
- `BENCH-02`: canonical benchmark dataset ingestion and normalization for APPS-style JSONL artifacts
- `BENCH-03`: concrete Python benchmark execution path over canonical benchmark records
- `BENCH-04`: multi-language benchmark execution dispatch for Python and JavaScript records, plus stricter stdin script fidelity

Not yet implemented:

- benchmark execution beyond the current Python and JavaScript local harnesses
- exact paper-scale checkpoint training or benchmark leaderboard reproduction

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
- `use.md`: root-level usage guide for common repository workflows
- `README_ZH.md`: Chinese overview of the current repository state
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

The stable package entrypoints are `solve_problem(...)`, `plan_problem_topology(...)`, `plan_problem_topology_candidate(...)`, `revise_problem_topology_candidate(...)`, `execute_topology_plan(...)`, `serialize_topology_plan_to_yaml(...)`, and `parse_topology_plan_yaml(...)`.

```python
from agentconductor import (
    DifficultyLevel,
    ProblemInstance,
    execute_topology_plan,
    parse_topology_plan_yaml,
    plan_problem_topology,
    plan_problem_topology_candidate,
    serialize_topology_plan_to_yaml,
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

candidate = plan_problem_topology_candidate(
    ProblemInstance(
        identifier="apps-policy",
        prompt="Fix the failing implementation.",
        difficulty=DifficultyLevel.EASY,
    ),
    orchestrator_policy=my_policy,  # implements TopologyOrchestratorPolicy
)

execution = execute_topology_plan(
    ProblemInstance(
        identifier="apps-two-sum",
        prompt="Write a function that returns two indices adding up to a target.",
        difficulty=DifficultyLevel.EASY,
    ),
    topology,
)

topology_yaml = serialize_topology_plan_to_yaml(topology)
parsed_topology = parse_topology_plan_yaml(topology_yaml)

print(topology.steps)
print(topology_yaml)
print(parsed_topology == topology)
print(result.status)
print(result.candidate_solution)
print(result.testing_outcome)
print(result.solve_state.completed_turns)
print(execution.testing_outcome)
print(candidate.topology_yaml)
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

When no `orchestrator_policy` is passed, planning stays on deterministic
repository-local templates. When a policy is passed, `solve_problem(...)` and
`plan_problem_topology(...)` route through the learned YAML path, while
`plan_problem_topology_candidate(...)` and
`revise_problem_topology_candidate(...)` expose the raw YAML candidate plus the
parsed `TopologyPlan`.

The execution API can return a typed `TopologyExecutionResult` with:

- per-step and per-agent structured outputs
- resolved upstream references for each agent
- final candidate code
- judge outcome and diagnostics

The YAML transport helpers can:

- serialize a validated `TopologyPlan` into the repository's stable YAML shape
- parse repository YAML text back into the same typed `TopologyPlan` contract
- preserve explicit parse, schema, and logic failure boundaries

The learned orchestrator path preserves explicit failure boundaries as well:

- missing YAML in a policy response raises `TopologyCandidateExtractionError`
- malformed YAML raises the existing parse-layer transport error
- schema-invalid or logic-invalid topologies raise the existing validation errors

See [API.md](/D:/code/PaperCreate/AgentConductor/API.md) for the full interface contract.
See [use.md](/D:/code/PaperCreate/AgentConductor/use.md) for task-oriented usage examples.

## Testing

Run the focused test suite:

```powershell
uv run pytest
```

For restricted environments where `uv` cannot use a user-global cache, prefer
the repository-local verification wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1
```

That wrapper defaults `UV_CACHE_DIR` to `.\.uv-cache` inside the repository.
If you need a different cache location, set `UV_CACHE_DIR` explicitly before
running either command.

Preferred verification commands:

- `powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1`
- `uv run pytest` when the current environment already has usable cache permissions

Fallback verification commands:

- `$env:UV_CACHE_DIR = ".uv-cache"; uv run pytest`
- `uv sync --locked` before the test command if the environment is not yet synced

Run a small batch evaluation artifact:

```powershell
uv run python -m agentconductor.interfaces.evaluation --dataset .\examples\eval-dataset.json --output .\artifacts\eval-results.json
```

The dataset JSON must contain a `problems` list with `identifier`, `prompt`,
and optional `difficulty` fields.

Generate synthetic SFT data and run the baseline artifact path:

```powershell
uv run python -m agentconductor.interfaces.training --dataset .\artifacts\sft-dataset.jsonl --artifact .\artifacts\sft-run.json
```

Run the repository-local RL baseline over that dataset:

```powershell
uv run python -m agentconductor.interfaces.rl --dataset .\artifacts\sft-dataset.jsonl --artifact .\artifacts\rl-run.json --rollouts 2
```

## Design Notes

- The package keeps paper-method logic, application orchestration, and interfaces separated.
- The first API is intentionally narrow. It is a stable Python boundary, not an HTTP service.
- The executor remains deterministic for planning and worker-role behavior, but
  its testing role now evaluates candidate code through a local subprocess judge adapter.
- The subprocess judge is concrete but still approximate. It runs Python candidates
  against explicit test cases, expected outputs, typed per-case verdicts, and
  explicit CPU, wall-clock, and memory limits.
- Wall-clock limits are now enforced as hard per-case subprocess timeouts.
- On platforms that expose `resource` limits, the judge also applies OS-level
  CPU and address-space limits inside the worker process.
- On Windows, the judge now tries to attach each worker to a dedicated Job
  Object and hard-enforce `memory_limit_bytes` at the process level.
- Some host Windows runtimes already place the current process tree inside a
  controlling Job that forbids rebinding child processes. In that case the
  repository keeps wall-clock enforcement, reports explicit diagnostics, and
  falls back to the existing approximate memory path.
- Windows worker launch now attempts `CREATE_BREAKAWAY_FROM_JOB` before plain
  subprocess fallback so the downgrade path is explicit and inspectable.
- Windows CPU-limit enforcement is now reported as unsupported rather than
  being implied by the generic `cpu_time_seconds` field. Hard wall-clock
  timeout remains the only guaranteed timing control on Windows.
- On platforms without those primitives, memory enforcement falls back to traced
  Python allocations and remains approximate.
- The judge still normalizes line endings and trailing line whitespace in a more
  benchmark-like way, but it does not yet reproduce an external benchmark's
  full runtime semantics.
- External benchmark integration now has its own typed adapter boundary for
  benchmark problem metadata, execution settings, verdict mapping, and run
  artifact identifiers.
- The bundled benchmark adapter is a deterministic stub used to verify the
  contract; it does not execute against a real benchmark service yet.
- Benchmark dataset ingestion now supports a local APPS-style JSONL source and
  normalizes it into canonical `BenchmarkProblemDefinition` records.
- The repository now also exposes canonical benchmark execution records with
  benchmark-owned invocation settings and test cases, plus a concrete
  `PythonBenchmarkJudgeAdapter`, `NodeJsBenchmarkJudgeAdapter`, and
  `MultiLanguageBenchmarkJudgeAdapter` that run those records through the
  benchmark adapter boundary.
- The current benchmark runtime supports Python and JavaScript. Function-style
  records execute through language-aware call boundaries, while stdin-style
  records now run as standalone scripts with benchmark-owned stdin payloads.
- The JavaScript function path accepts CommonJS exports and also applies a
  narrow repository compatibility shim for top-level `solve(...)` definitions;
  that shim is an implementation inference rather than a benchmark-native rule.
- The current APPS normalization maps `introductory`, `interview`, and
  `competition` difficulty labels to repository `easy`, `medium`, and `hard`
  tiers as an implementation inference rather than a paper-stated rule.
- LiveCodeBench, CodeContests, HumanEval, and MBPP dataset ingestion are still
  pending, and the repository does not bundle proprietary or license-restricted
  benchmark payloads.
- Parallel candidate evaluation now goes through an explicit orchestration
  boundary with inspectable worker count, retry count, and collection timeout.
- Batch evaluation artifacts record per-problem solve outcomes, latency, and
  topology metadata so later training analysis can reuse them.
- The SFT baseline materializes schema-valid synthetic topology data and writes
  a reproducible training artifact, but it does not fine-tune a large model.
- The synthetic `target_topology` payload now reuses the same canonical
  `TopologyPlan.to_mapping()` transport shape that backs the YAML path, so
  training fixtures do not maintain a separate topology serializer.
- The RL baseline computes inspectable reward breakdowns and rollout artifacts
  using repository-local approximations of the paper's reward terms.
- When behavior is inferred rather than stated by the paper, the repository documents that explicitly.

## Next Likely Steps

- extend benchmark dataset normalization beyond APPS-style JSONL sources
- extend benchmark execution beyond the current Python and JavaScript local harnesses, especially for compiled-language and vendor-native runtimes
- extend checkpoint-producing SFT and frozen-inference orchestration paths
