# AgentConductor 使用指南

本文档是当前仓库面向任务的根本使用指南。
它是对 [README.md](/D:/code/PaperCreate/AgentConductor/README.md) 和
[API.md](/D:/code/PaperCreate/AgentConductor/API.md) 的补充。

## 环境配置

同步工作区：

```powershell
uv sync
```

运行引导入口点：

```powershell
uv run python main.py
```

预期输出：

```text
agentconductor: roles=6, max_turns=2
```

## 常用 Python 调用

### 求解单个问题

```python
from agentconductor import DifficultyLevel, ProblemInstance, solve_problem

result = solve_problem(
    ProblemInstance(
        identifier="apps-two-sum",
        prompt="编写一个函数，返回两数之和等于目标值的两个索引。",
        difficulty=DifficultyLevel.EASY,
    ),
    max_turns=2,
)

print(result.status)
print(result.testing_outcome)
print(result.candidate_solution)
print(result.solve_state.completed_turns)
```

当你希望仓库规划并执行一个有界的求解循环时，使用此方法。

### 通过训练好的检查点边界求解

```python
from agentconductor import DifficultyLevel, ProblemInstance, solve_problem

result = solve_problem(
    ProblemInstance(
        identifier="apps-checkpoint",
        prompt="修复失败的实现。",
        difficulty=DifficultyLevel.EASY,
    ),
    max_turns=2,
    orchestrator_checkpoint="artifacts/sft-run.json",
)

print(result.notes[1])
print(result.notes[2])
```

当你希望在线冻结推理来解析训练好的检查点工件，而不是直接使用确定性规划器时，使用此方法。
当前检查点运行时加载仓库本地的 `orchestrator-runtime.json` 捆绑包，并且仅支持 `orchestrator_device="cpu"`。

### 使用显式的工作器运行时求解

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
        prompt="实现一个正确的解决方案。",
        difficulty=DifficultyLevel.EASY,
    ),
    worker_runtime=RepositoryWorkerModelRuntime(),
)

first_agent = result.execution.step_results[0].agent_results[0]
print(first_agent.worker_runtime)
print(first_agent.worker_model)
```

当你希望显式地替换或检查非测试类工作器运行时时，使用此方法。测试角色仍然通过评判边界运行。

### 规划带类型的拓扑

```python
from agentconductor import DifficultyLevel, ProblemInstance, plan_problem_topology

topology = plan_problem_topology(
    ProblemInstance(
        identifier="apps-graph",
        prompt="在严格约束下解决一个图的最短路径问题。",
        difficulty=DifficultyLevel.MEDIUM,
    )
)

print(topology.steps)
print(topology.node_count)
```

在没有显式策略的情况下，这将使用确定性规划器。
你也可以传入 `orchestrator_checkpoint=...` 来从检查点元数据中解析学习到的路径。

### 通过学习到的策略边界生成 YAML 候选方案

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
        prompt="修复失败的实现。",
        difficulty=DifficultyLevel.EASY,
    ),
    orchestrator_policy=StubPolicy(),
)

print(candidate.topology_yaml)
print(candidate.topology)
print(candidate.attempt_count)
```

当你需要原始 YAML 加上解析后的 `TopologyPlan` 时，使用此方法。
当你希望候选方案来自检查点支持的冻结策略时，相同的入口点也接受 `orchestrator_checkpoint=...`。

### 序列化和解析拓扑 YAML

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
        prompt="实现一个正确的解决方案。",
        difficulty=DifficultyLevel.EASY,
    )
)

yaml_text = serialize_topology_plan_to_yaml(topology)
parsed = parse_topology_plan_yaml(yaml_text)

print(yaml_text)
print(parsed == topology)
```

## 命令行工作流

### 运行针对性测试

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1 tests\test_api.py
```

仓库范围内的首选命令：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1
```

### 运行基准测试对齐的评估

```powershell
uv run python -m agentconductor.interfaces.evaluation --dataset .\tests\fixtures\benchmark\apps_fixture.jsonl --output .\artifacts\eval-results.json --checkpoint .\artifacts\sft-run.json --samples-per-problem 1
```

此路径：

- 显式解析一个冻结的编排器检查点
- 加载一个规范的基准数据集工件，如 APPS JSONL
- 运行求解尝试，然后通过基准适配器边界重新评判发出的候选方案
- 写入每次尝试的记录以及聚合的 `pass@1` 或 `pass@k`
- 在输出工件中记录数据集版本、工具链版本、运行时模式、检查点 ID、
  可复现声明以及精确复现就绪状态

默认的评估适配器仍然是仓库本地的 Python 或 JavaScript 工具链。基准接缝现在也支持：

- 在 `BenchmarkExecutionSettings` 中使用显式的编译或运行阶段契约，用于未来的编译语言记录
- 当 `javac` 和 `java` 可用时，为基于标准输入（stdin）风格的基准记录提供一个 Java 优先的本地编译语言工具链
- 一个独立的供应商原生运行时边界，当基准测试必须通过提交加轮询而非本地执行来评估时使用

### 生成 SFT 数据

```powershell
uv run python -m agentconductor.interfaces.training --dataset .\artifacts\sft-dataset.jsonl --artifact .\artifacts\sft-run.json --sample-count 4500
```

这将写入：

- 一个包含 `target_topology` 和 `target_topology_yaml` 的 JSONL 数据集
- 一个数据集附属元数据文件，包含样本数量、难度分布、来源配方、提示词模板版本和缩减规模状态
- 一个用于 YAML 目标监督的训练清单文件
- 一个包含可加载元数据的轻量级检查点目录

### 检查生成的 SFT 检查点

```powershell
uv run python -m agentconductor.interfaces.training --dataset .\artifacts\sft-dataset.jsonl --load-checkpoint .\artifacts\sft-run-checkpoint
```

### 运行 RL 检查点优化

```powershell
uv run python -m agentconductor.interfaces.rl --dataset .\artifacts\sft-dataset.jsonl --artifact .\artifacts\rl-run.json --checkpoint .\artifacts\sft-run.json --rollout-count 8 --group-size 8
```

此路径：

- 从显式元数据中解析一个源编排器检查点
- 通过当前有界求解循环收集分组的展开结果
- 写入一个展开清单、一个分组更新工件和一个更新后的检查点目录

## 规划模式

仓库目前支持两种拓扑规划模式。

- `deterministic`（确定性）
  使用仓库本地的启发式方法和模板拓扑。
- `learned`（学习型）
  调用 `TopologyOrchestratorPolicy`，提取 YAML，解析它，验证它，
  并返回显式的失败信息，而不是静默回退。

检查点支持的冻结推理是一种显式的学习型子模式。

- 它接受检查点目录、检查点元数据文件或 SFT 工件 JSON 作为 `orchestrator_checkpoint`。
- 如果源目录包含多个检查点，你还必须设置 `orchestrator_checkpoint_id`。
- 当前的仓库本地冻结运行时仅支持 `orchestrator_device="cpu"`，并从 `orchestrator-runtime.json` 加载序列化的检查点运行时状态，而不是依赖仅含元数据的模拟逻辑。

### 写入当前可复现性审计

```powershell
uv run python -m agentconductor.interfaces.reproduction --output .\artifacts\reproduction-audit.json
```

当你需要一个仓库自有的工件来列出当前的精确复现阻碍因素以及活跃的 `approximate`（近似）与 `exact`（精确）声明时，使用此命令。

## 失败边界

拓扑和编排器的失败是有意设计为显式的。

- 策略响应中缺少 YAML 会引发 `TopologyCandidateExtractionError`。
- 格式错误的 YAML 会引发解析层传输错误。
- 模式无效的拓扑负载会引发 `TopologySchemaError`。
- 逻辑无效的拓扑会引发 `TopologyLogicError`。

基准运行时失败也是显式的。

- 编译阶段失败和运行阶段失败在带类型的 `BenchmarkPhaseResult` 记录中保持分离。
- 缺少本地编译语言工具链会显示为显式的适配器错误，而不是静默跳过。
- 供应商原生适配器保留提交 ID、轮询历史和终端裁决映射，而不是将所有内容扁平化到单个本地工具链日志中。

## 何时阅读哪份文档

- 阅读 [README.md](/D:/code/PaperCreate/AgentConductor/README.md) 获取仓库状态和范围。
- 阅读 [README_ZH.md](/D:/code/PaperCreate/AgentConductor/README_ZH.md) 获取中文摘要。
- 阅读 [API.md](/D:/code/PaperCreate/AgentConductor/API.md) 获取完整的可调用契约。