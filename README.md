# AgentConductor

AgentConductor is a backend-oriented Python project that aims to reproduce the method from `2602.17100v1.pdf` as a reusable software system.

The repository currently provides:

- a `src/`-layout Python package managed with `uv`
- typed domain models derived from the paper distillation
- a stable Python solve API for bounded multi-turn execution over deterministic or learned orchestrator paths
- a typed multi-turn solve-state contract for turn history and later revision
- a deterministic topology planner that emits validated single-turn plans
- a learned-orchestrator policy boundary that produces topology YAML candidates and parses them into validated typed plans
- a checkpoint-backed frozen orchestrator runtime that loads a repository-local runtime bundle instead of relying on metadata plus `weights.stub` alone
- a single-turn graph executor whose non-testing worker roles now run through an explicit model-backed runtime seam and whose testing role runs through a local subprocess judge adapter
- a typed external benchmark adapter seam for benchmark metadata, verdict normalization, and run artifact identifiers
- canonical benchmark dataset ingestion for APPS-style JSONL records
- a multi-language benchmark execution path for Python and JavaScript canonical benchmark records
- phase-aware benchmark execution contracts that now model compile and run phases explicitly
- a local compiled-language benchmark path for Java plus explicit C++ toolchain-error reporting
- a typed vendor-native benchmark runtime boundary with fixture-driven submission and polling lifecycle coverage
- focused tests for the bootstrap and API layers

The repository does not yet implement the full paper runtime. The current API can run up to the configured turn budget with deterministic or checkpoint-backed topology revision, and the repository now emits benchmark-aligned evaluation artifacts. Local evaluation still defaults to repository-local harness adapters, while the vendor-native runtime boundary is currently verified through fixture-driven stubs rather than a live external service.

Current strict-reproduction claim: `approximate reproduction`

See [docs/reproduction.md](/D:/code/PaperCreate/AgentConductor/docs/reproduction.md) for the line-item fidelity checklist and the current blockers to an exact paper-level claim.

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
- `TRAIN-02`: checkpoint-producing supervised training path with YAML targets and loadable checkpoint metadata
- `TRAIN-03`: paper-oriented synthetic YAML-topology SFT corpus expansion with dataset sidecar metadata, auditable optimizer or tokenizer provenance, and explicit reduced-scale labeling
- `ORCH-03`: checkpoint-backed frozen inference wiring for the online solve loop and learned planning entrypoints
- `ORCH-04`: repository-local checkpoint bundle loading for frozen orchestrator inference with explicit runtime-artifact validation
- `EXEC-02`: model-backed non-testing worker runtime seam with per-agent runtime or model provenance
- `RL-01`: repository-local reward breakdown and RL-style rollout artifact generation
- `RL-02`: checkpoint-updating RL path with grouped rollout artifacts, lightweight GRPO-style update summaries, and loadable updated checkpoint metadata
- `RL-03`: paper-oriented grouped-rollout RL path with group-normalized advantages, grouped update artifacts, and RL lineage written into checkpoint runtime provenance
- `EVAL-02`: benchmark-aligned frozen-inference evaluation with structured per-attempt artifacts, dataset or harness provenance, and pass@1 or pass@k aggregates
- `BENCH-01`: typed external benchmark adapter seam for execution metadata and verdict mapping
- `BENCH-02`: canonical benchmark dataset ingestion and normalization for APPS-style JSONL artifacts
- `BENCH-03`: concrete Python benchmark execution path over canonical benchmark records
- `BENCH-04`: multi-language benchmark execution dispatch for Python and JavaScript records, plus stricter stdin script fidelity
- `BENCH-05`: phase-aware benchmark execution contracts for compiled-language compile or run settings and diagnostics
- `BENCH-06`: local compiled-language benchmark harness with Java compile-then-run execution and explicit C++ toolchain diagnostics
- `BENCH-07`: typed vendor-native benchmark runtime boundary with submission receipt, poll history, and artifact provenance

Not yet implemented:

- a repository-bundled C++ toolchain path in environments where `g++` is unavailable
- exact paper-scale checkpoint training or benchmark leaderboard reproduction

Current exact-reproduction blockers recorded in `docs/reproduction.md`:

- paper-fidelity worker agents and retriever fidelity
- paper-scale SFT and RL training fidelity
- benchmark-grade checkpoint-backed frozen inference instead of the current repository-local bundle runtime
- full paper benchmark dataset coverage
- live vendor-native benchmark runtime fidelity
- stable compiled-language coverage across hosts

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
- `docs/reproduction.md`: exact-vs-approximate reproduction checklist and blockers
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

The stable package entrypoints are `solve_problem(...)`, `plan_problem_topology(...)`, `plan_problem_topology_candidate(...)`, `revise_problem_topology_candidate(...)`, `execute_topology_plan(...)`, `serialize_topology_plan_to_yaml(...)`, `parse_topology_plan_yaml(...)`, and `load_sft_checkpoint_entrypoint(...)`.

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

checkpoint_result = solve_problem(
    ProblemInstance(
        identifier="apps-checkpoint",
        prompt="Fix the failing implementation.",
        difficulty=DifficultyLevel.EASY,
    ),
    max_turns=2,
    orchestrator_checkpoint="artifacts/sft-run.json",
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
print(checkpoint_result.notes[2])
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
When `orchestrator_checkpoint` is passed instead, the same learned path is
loaded from explicit checkpoint metadata plus a checkpoint-owned runtime
artifact. The current repository runtime is still a local substitute rather
than benchmark-grade Qwen serving, but it now loads serialized frozen-inference
state instead of falling back to metadata-only mock behavior.

The execution API can return a typed `TopologyExecutionResult` with:

- per-step and per-agent structured outputs
- resolved upstream references for each agent
- per-agent worker runtime and model identifiers for non-testing roles
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

Run a small benchmark-aligned evaluation artifact:

```powershell
uv run python -m agentconductor.interfaces.evaluation --dataset .\tests\fixtures\benchmark\apps_fixture.jsonl --output .\artifacts\eval-results.json --checkpoint .\artifacts\sft-run.json --samples-per-problem 1
```

The evaluation dataset must be a supported canonical benchmark source such as
APPS-style JSONL. The generated artifact records dataset version, harness
version, runtime mode, checkpoint id, reproduction claim, exact-reproduction
readiness, per-attempt outcomes, and aggregate metrics including `pass@1` and
`pass@k`.

Write the current reproduction audit artifact:

```powershell
uv run python -m agentconductor.interfaces.reproduction --output .\artifacts\reproduction-audit.json
```

Generate synthetic SFT data and run the checkpoint-producing SFT path:

```powershell
uv run python -m agentconductor.interfaces.training --dataset .\artifacts\sft-dataset.jsonl --artifact .\artifacts\sft-run.json --sample-count 4500
```

Inspect the generated checkpoint metadata:

```powershell
uv run python -m agentconductor.interfaces.training --dataset .\artifacts\sft-dataset.jsonl --load-checkpoint .\artifacts\sft-run-checkpoint
```

Run a solve request through checkpoint-backed frozen inference:

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
```

Run the repository-local RL checkpoint-optimization path over that dataset:

```powershell
uv run python -m agentconductor.interfaces.rl --dataset .\artifacts\sft-dataset.jsonl --artifact .\artifacts\rl-run.json --checkpoint .\artifacts\sft-run.json --rollout-count 8 --group-size 8
```

## Design Notes

- The package keeps paper-method logic, application orchestration, and interfaces separated.
- The first API is intentionally narrow. It is a stable Python boundary, not an HTTP service.
- The executor now routes non-testing worker roles through an explicit
  model-backed runtime seam. The default runtime is repository-local and uses
  `gpt-4o-mini-compatible-stub` model identifiers as a paper-facing placeholder
  rather than claiming real provider execution.
- The testing role still evaluates candidate code through a local subprocess
  judge adapter instead of letting worker models self-grade.
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
- The current benchmark runtime supports Python, JavaScript, and Java locally.
  Function-style records execute through language-aware call boundaries for
  Python and JavaScript, while stdin-style records run as standalone scripts
  or local compile-then-run harnesses with benchmark-owned stdin payloads.
- Benchmark execution settings can now also carry explicit compile and run
  phase contracts for compiled-language records, including source layout,
  command templates, executable targets, and per-phase resource limits.
- Benchmark result artifacts now preserve typed per-phase diagnostics and
  artifact identifiers so compile failures and run-time failures stay
  distinguishable in later evaluation or vendor-runtime reporting.
- The first compiled-language local harness is Java. It expects a host-local
  `javac` plus `java` toolchain and currently supports stdin-style records.
- The C++ local adapter is also wired into the benchmark seam, but if `g++`
  is unavailable on the host it returns an explicit adapter error rather than
  silently skipping execution.
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
- Benchmark-aligned evaluation artifacts now record per-attempt solve
  outcomes, benchmark verdicts, latency, dataset version, harness version,
  runtime mode, reproduction claim, exact-reproduction readiness, and
  aggregate pass metrics so later comparisons do not depend on ad hoc log
  parsing.
- The current evaluation path computes repository-observed `pass@k` from
  structured repeated attempts over canonical benchmark records.
- The SFT path now writes both canonical mapping targets and YAML topology
  targets, plus explicit source-dataset sidecar metadata, a training-manifest
  file, and loadable checkpoint metadata.
- The default SFT dataset generator now prepares a paper-oriented synthetic
  YAML corpus of 4,500 samples and records difficulty breakdown, source recipe,
  prompt-template version, and reduced-scale status in a sidecar metadata file.
- The generated checkpoint artifact is repository-local and lightweight. It
  now makes sample count, source dataset metadata path, source recipe,
  optimizer name, prompt-template version, backbone name, tokenizer name,
  seed, and checkpoint location explicit, but it still does not claim exact
  paper-scale fine-tuning fidelity by itself.
- Checkpoint-backed frozen inference now resolves one checkpoint explicitly from
  a checkpoint directory, metadata file, or training artifact. If a directory
  contains multiple candidates, callers must pass `orchestrator_checkpoint_id`
  instead of relying on filesystem order.
- The current checkpoint-backed runtime now loads a repository-local
  `orchestrator-runtime.json` bundle from checkpoint metadata. It supports
  `device="cpu"` only and keeps explicit checks for runtime-artifact presence,
  prompt-template compatibility, and supported-device selection.
- The RL path now consumes an explicit source checkpoint, collects rollout
  records through the bounded solve loop, computes group-normalized advantages,
  writes a dedicated grouped-update artifact, and materializes an updated
  checkpoint plus rollout manifest artifacts.
- The current RL path now matches the paper more closely on explicit group-size
  configuration, grouped rollout semantics, and separated reward or advantage
  stages. It still remains a repository-local reduced-scale approximation
  rather than a paper-scale distributed GRPO implementation.
- The repository now also exposes a vendor-native benchmark runtime boundary
  with typed submission receipt, poll history, terminal verdict mapping, and
  artifact provenance. The current verification path is fixture-driven rather
  than backed by a live external service.
- The default benchmark evaluation runtime still uses repository-local Python
  and JavaScript harness adapters. Reported metrics should therefore be treated
  as benchmark-aligned rather than exact leaderboard claims unless callers
  intentionally route through a configured vendor-native adapter.
- The repository now also exposes a dedicated reproduction-audit artifact path
  so future agents have one stable place to inspect the remaining exact
  reproduction blockers.
- When behavior is inferred rather than stated by the paper, the repository documents that explicitly.

## Next Likely Steps

- extend benchmark dataset normalization beyond APPS-style JSONL sources
- extend the compiled-language local harness beyond the current Java-first path, especially for C++ on hosts with an available toolchain
- replace the repository-local checkpoint bundle runtime with benchmark-grade model inference
- replace the lightweight GRPO-style stub updater with a fuller paper-aligned RL optimizer
- replace the fixture-driven vendor-native benchmark stub with a real external runtime integration where licensing and authentication permit it
