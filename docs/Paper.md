# Paper Distillation: AgentConductor

## Scope
This document distills `2602.17100v1.pdf` into implementation-oriented notes for the AgentConductor repository. It is not a literature review. Its purpose is to capture the paper's method in a form that a future agent can use to design modules, data contracts, and execution flows.

## Paper Identity

- Title: `AgentConductor: Topology Evolution for Multi-Agent Competition-Level Code Generation`
- Core problem: dynamic multi-agent coordination for competition-level code generation
- Core idea: train an orchestrator model to generate and iteratively refine multi-agent interaction topologies, conditioned on problem difficulty and execution feedback

## Direct Facts from the Paper

### High-Level Method

The paper proposes a multi-agent system centered on an orchestrator agent. The orchestrator does not directly solve the coding task. Instead, it generates a YAML description of a multi-agent interaction topology for each turn.

The topology is:

- task-specific
- difficulty-aware
- represented as a layered directed acyclic graph
- updated across turns based on execution feedback

The paper claims two main technical ideas:

1. a topology-density function that links graph structure to communication cost
2. a difficulty-aware mechanism that bounds topology complexity by difficulty level

### Three-Stage Pipeline

The full method has three stages.

1. Data collection and SFT
   The authors synthesize valid topology examples and use them to teach the orchestrator structural priors.
2. Multi-turn RL with GRPO
   The orchestrator is optimized to generate better topologies using rewards derived from YAML validity, code execution outcome, and topology density.
3. Frozen inference
   At inference time, the orchestrator is frozen and generates topologies online for new problems. It can revise the topology over multiple turns using sandbox feedback.

### Online Inference Workflow

For a coding problem `x`, the orchestrator repeatedly performs the following process:

1. infer difficulty and appropriate agent roles
2. generate a YAML token sequence that encodes the topology for the current turn
3. decode the YAML into a layered DAG
4. execute agents layer by layer, with agents inside the same layer running in parallel
5. collect role outputs and run generated code in a sandbox via a testing agent
6. stop early if the code passes
7. otherwise append feedback to history and generate a revised topology for the next turn

The paper's appendix gives the workflow as an online topology-generation algorithm with:

- global history `H_k`
- per-agent local memory
- early stop on `PASSED`
- invalid-YAML handling before graph execution

### Topology Representation

The topology is represented in YAML. Each step corresponds to one layer. Each agent entry contains:

- an `agent` role token such as `<planner>`
- a `ref` list that points to outputs of earlier agents

The topology supports:

- within-layer parallelism
- cross-layer references
- multi-turn evolution across repeated attempts

The first step must contain only empty `ref` fields. The final step must contain a testing agent.

### Agent Role Pool

The paper defines six role types.

1. Retrieval agent
   Retrieves semantically relevant material using an E5-based retriever. It may use prior agent outputs as context.
2. Planning agent
   Produces or refines a step-by-step coding plan.
3. Algorithmic agent
   Produces algorithmic decomposition or solution steps.
4. Coding agent
   Writes candidate code using the problem, plans, and retrieved references.
5. Debugging agent
   Revises code after failures using prior errors and interaction history.
6. Testing agent
   Executes validation and returns pass/fail plus graded error diagnostics.

### Graph Complexity / Density Signal

The paper models interaction cost through graph properties. The main components are:

- number of nodes `|V|`
- edge-related interaction term derived from references
- depth proxy based on the number of steps/layers `s`

The paper motivates a basic unnormalized structural score of the form:

- node count contribution
- edge density contribution
- depth contribution

It then normalizes the score with difficulty-aware bounds and converts it with an exponential form into a complexity signal used by the reward.

The paper explicitly uses difficulty-specific node limits:

- easy: `Nmax = 4`
- medium: `Nmax = 7`
- hard: `Nmax = 10`

The RL reward penalizes topologies that exceed the allowed node budget for the inferred difficulty level.

### Reward Structure

The immediate reward is composed of two main parts:

1. execution-related reward
2. graph-density reward

Execution-related reward includes:

- YAML-format failure penalties
- code execution outcome rewards or penalties

The paper lists YAML failure modes such as:

- no YAML found
- YAML parse error
- YAML schema invalid
- YAML logic invalid

It also lists code-execution outcomes such as:

- passed
- wrong answer
- time limit exceeded
- memory limit exceeded
- runtime error
- compilation error

The graph-density reward depends on whether the topology stays within the difficulty-aware bound and how sparse/complex the topology is.

### Training Setup

The orchestrator backbone is `Qwen2.5-3B-Instruct`.

The paper states:

- SFT uses 4,500 synthetic samples
- RL uses GRPO
- group size is 8
- maximum number of interaction turns is 2
- individual worker agents are executed with `gpt-4o-mini`
- code is checked in a sandbox

### Datasets and Results

The paper evaluates on:

- contest-level: APPS, LiveCodeBench v4, CodeContests
- basic code generation: HumanEval, MBPP

The paper reports that AgentConductor improves pass@1 over strong baselines while reducing topology density and token cost. For implementation purposes, the most important takeaway is not the exact leaderboard, but that the method depends on:

- real execution feedback
- difficulty-aware topology scaling
- multi-turn topology revision

Current repository ingestion status:

- APPS-style JSONL dataset ingestion is wired into canonical repository problem records
- APPS rows with `input_output` payloads are also normalized into canonical benchmark execution records with invocation settings and benchmark-owned test cases
- the current repository benchmark harness can execute Python and JavaScript canonical records through typed language-specific adapter boundaries
- the repository normalizes APPS difficulty labels into `easy`, `medium`, and `hard` as an implementation inference for later topology-budget and reporting paths
- LiveCodeBench v4, CodeContests, HumanEval, and MBPP dataset loaders are still pending

## Implementation-Oriented Interpretation

### Minimum Runtime Components

A practical reproduction will likely need these runtime components:

1. Orchestrator policy
   Generates YAML topology plans from problem input and prior history.
2. Topology parser and validator
   Parses YAML, checks schema rules, and converts the plan into an executable graph.
3. Role registry
   Maps role identifiers to executable agent implementations.
4. Graph executor
   Executes one topology turn layer by layer, with parallel execution inside a layer.
5. Memory/history manager
   Stores turn history, agent outputs, and execution feedback.
6. Code extraction and sandbox evaluation
   Extracts generated code and returns structured execution results.
7. Reward calculator
   Computes YAML-validity reward, execution reward, and graph-density reward.

### Likely Data Contracts

The paper implies the need for structured objects similar to:

- `ProblemInstance`
- `DifficultyLevel`
- `TopologyPlan`
- `TopologyStep`
- `AgentInvocation`
- `ExecutionHistory`
- `AgentOutput`
- `CodeExecutionResult`
- `TurnResult`
- `RewardBreakdown`

These names are implementation suggestions, not paper terminology.

Current repository-level training inference:

- the SFT stage can be approximated locally by materializing deterministic,
  schema-valid topology targets from the current rule-based orchestrator so the
  data format and validation path exist before large-model fine-tuning is added
- the RL stage can be approximated locally by making YAML-validity,
  execution-outcome, and topology-density rewards explicit and inspectable even
  before full GRPO policy optimization is implemented

### Likely Module Boundaries

To align with this repository's backend architecture, the method naturally separates into:

- `domain`
  topology model, role model, density calculation, reward rules
- `application`
  orchestration loop, turn execution, stopping policy
- `infrastructure`
  YAML parsing, retriever integration, sandbox execution, model calls
- `interfaces`
  callable API or CLI adapters

### Minimal Reproduction Path

A minimal but credible reproduction does not require full training on day one. A staged implementation path could be:

1. implement the topology schema and executor
2. implement deterministic or mock role agents to validate control flow
3. implement sandbox result handling and reward calculation
4. plug in an orchestrator prompt-based baseline before reproducing SFT/RL
5. add training pipelines only after the runtime semantics are stable

This is an implementation inference, not a claim from the paper.

## Facts vs. Inferences

### Facts

- The method uses a YAML-encoded layered DAG.
- The orchestrator generates topologies, not final code directly.
- The system runs in multiple turns and uses execution feedback.
- The role pool has six role types.
- The reward combines execution correctness and graph-density signals.
- Difficulty-specific node caps are 4, 7, and 10.
- The reported orchestrator backbone is Qwen2.5-3B-Instruct.
- The reported maximum interaction turns during training is 2.

### Inferences

- A clean software reproduction should treat topology parsing, execution, and reward calculation as separate modules.
- A repository-first implementation should build the runtime loop before attempting RL training.
- The first stable API should probably expose topology generation, single-turn execution, and multi-turn solve as separate entrypoints.
- Some paper details are sufficient for reproduction of control flow, but not yet sufficient for faithful training reproduction without additional implementation choices.

## Open Questions for Implementation

The following points remain unclear or underspecified from the paper text and will affect implementation quality:

1. Difficulty inference mechanism
   The paper says the orchestrator infers difficulty, but the exact inference procedure and prompt/runtime contract are not fully specified in the main method description.
2. YAML schema details
   The paper describes the structure conceptually, but a complete formal schema is not provided in the main body.
3. Agent I/O formats
   The exact serialized format for role outputs, references, and memory passing is not fully specified.
4. Local memory semantics
   The appendix mentions per-agent local memory, but the persistence policy and memory contents are not fully defined.
5. Code extraction rule
   The paper says code is extracted from role outputs, but the extraction contract is not precisely defined.
6. Sandbox interface
   The execution environment is described functionally, but not as a concrete API.
7. Retriever corpus construction for advanced tasks
   The retrieval setup is partially described, but the exact document construction and storage interface for a reproduction remain open.
8. RL reproducibility details
   The paper gives high-level hyperparameters, but not enough end-to-end implementation detail to reproduce training exactly without further design choices.

## Recommended Engineering Priorities

Based on the paper and this repository's goals, the next engineering steps should be:

1. define the YAML schema and validation rules in code
2. define typed models for topology, history, and execution results
3. implement a graph executor that respects layered parallelism and references
4. define reward-calculation interfaces independently from training infrastructure
5. only then decide how much of SFT and RL training will be reproduced in the first milestone

## Practical Summary

AgentConductor should be understood as a topology-generation system rather than just a multi-agent prompt chain. The paper's real novelty lies in treating agent interaction structure as a generated, difficulty-aware, feedback-refined object. For this repository, that means the core engineering challenge is not only agent prompting, but building:

- a topology language
- a topology validator
- a layered graph executor
- a feedback loop
- a reward model that can later support training
