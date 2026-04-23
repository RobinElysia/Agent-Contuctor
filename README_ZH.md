# AgentConductor

AgentConductor 是一个面向后端的 Python 项目，目标是把论文 `2602.17100v1.pdf` 中的方法复现为可复用的软件系统。

当前仓库已经提供：

- 基于 `uv` 管理的 `src/` 布局 Python 包
- 从论文抽取出的 typed domain models
- 支持 bounded multi-turn execution 的稳定 Python API
- deterministic planner 与 learned-orchestrator policy 两条拓扑规划路径
- `TopologyPlan <-> YAML` 的稳定传输契约
- 面向后续修订回合的 typed solve-state / revision-input 契约
- 单轮 topology 执行与本地 judge 适配器
- benchmark dataset / adapter / local execution 的基础边界

当前仓库仍未完整复现论文的全部运行时。现在的实现更适合做方法复现、接口对接和后续训练/推理接线，而不是直接宣称达到论文级 benchmark 结果。

## 当前状态

已完成的关键里程碑：

- `TOP-02`: YAML-native topology serialization / parsing
- `ORCH-01`: deterministic rule-based topology planning
- `ORCH-02`: model-backed YAML orchestrator boundary
- `EXEC-01`: deterministic single-turn topology execution
- `TRAIN-01`: synthetic topology dataset + reproducible SFT baseline artifact path
- `RL-01`: repository-local reward breakdown + rollout artifact path
- `BENCH-01` 到 `BENCH-04`: benchmark adapter、canonical dataset ingestion、Python/JavaScript local execution

尚未完成的重点：

- 默认内置真实 checkpoint-backed orchestrator
- benchmark-exact frozen inference runtime
- 论文规模的 checkpoint 训练与 leaderboard 复现

## 根目录文档

- [README.md](/D:/code/PaperCreate/AgentConductor/README.md)：英文总览
- [API.md](/D:/code/PaperCreate/AgentConductor/API.md)：API 契约与 public types
- [use.md](/D:/code/PaperCreate/AgentConductor/use.md)：常见调用方式与工作流示例
- [docs/tasks.md](/D:/code/PaperCreate/AgentConductor/docs/tasks.md)：任务卡和状态
- [docs/Paper.md](/D:/code/PaperCreate/AgentConductor/docs/Paper.md)：论文方法蒸馏

## 快速开始

同步环境：

```powershell
uv sync
```

运行当前 CLI 入口：

```powershell
uv run python main.py
```

或者：

```powershell
uv run agentconductor
```

预期输出：

```text
agentconductor: roles=6, max_turns=2
```

## Python API 概览

当前稳定入口包括：

- `solve_problem(...)`
- `plan_problem_topology(...)`
- `plan_problem_topology_candidate(...)`
- `revise_problem_topology_candidate(...)`
- `execute_topology_plan(...)`
- `serialize_topology_plan_to_yaml(...)`
- `parse_topology_plan_yaml(...)`

示例：

```python
from agentconductor import (
    DifficultyLevel,
    ProblemInstance,
    plan_problem_topology,
    plan_problem_topology_candidate,
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
    orchestrator_policy=my_policy,
)
```

默认情况下，如果不传 `orchestrator_policy`，仓库会走 deterministic planner。  
如果传入实现了 `TopologyOrchestratorPolicy` 的 policy，就会走 learned YAML path，并显式经历 prompt construction、YAML extraction、parse、validation 和 retry。

## 文档同步约束

仓库现在明确要求：每次完成一张任务卡时，都要同步检查并更新这些文档：

- `README.md`
- `README_ZH.md`
- `API.md`
- `docs/use.md`

如果某份文档不需要改，也应该先确认而不是默认跳过。

## 后续建议

如果继续推进当前主线，最合理的下一步通常是：

1. 把 learned orchestrator boundary 接到真实 checkpoint 或 mock serving path。
2. 让训练路径从 transport-ready artifacts 升级到 checkpoint-producing workflow。
3. 把 frozen inference 与 benchmark evaluation 进一步对齐。
