# AgentConductor

AgentConductor 是一个面向后端的 Python 项目，目标是把论文 `2602.17100v1.pdf` 中的方法整理为可复用的软件系统。

当前仓库已经提供：

- 基于 `uv` 管理的 `src/` 布局 Python 包
- 从论文方法提炼出的 typed domain models
- 有界多轮 `solve_problem(...)` Python API
- `deterministic planner`、`direct learned policy`、`checkpoint-backed frozen inference` 三条拓扑规划路径
- 稳定的 `TopologyPlan <-> YAML` 传输契约
- 面向后续修订回合的 typed solve-state / revision-input 契约
- 本地 judge、benchmark adapter、SFT checkpoint artifact、RL checkpoint update 的基础边界

当前实现仍然不是论文级完整 runtime。仓库现在更适合做方法复现、接口接线、训练产物管理和后续评测扩展。

## 当前状态

已完成的关键任务包括：

- `TOP-02`：YAML-native topology serialization / parsing
- `ORCH-01`：deterministic rule-based topology planning
- `ORCH-02`：model-backed YAML orchestrator boundary
- `TRAIN-02`：产生 checkpoint metadata 的 supervised training path
- `ORCH-03`：把 checkpoint-backed frozen inference 接入在线 solve loop
- `RL-02`：从 source checkpoint 出发，收集 grouped rollouts，并生成更新后的 RL checkpoint
- `EXEC-01`、`RL-01`、`BENCH-01` 到 `BENCH-04`：执行、奖励、benchmark 本地边界

仍未完成的重点包括：

- 真实模型权重加载与生产级 frozen inference runtime
- 更完整的 benchmark 数据与语言支持
- 论文规模的 checkpoint 训练与 leaderboard 复现

## 根目录文档

- [README.md](/D:/code/PaperCreate/AgentConductor/README.md)：英文总览
- [API.md](/D:/code/PaperCreate/AgentConductor/API.md)：公开 API 与 public types
- [use.md](/D:/code/PaperCreate/AgentConductor/use.md)：常见调用方式与工作流
- [docs/tasks.md](/D:/code/PaperCreate/AgentConductor/docs/tasks.md)：任务卡与状态
- [docs/Paper.md](/D:/code/PaperCreate/AgentConductor/docs/Paper.md)：论文方法蒸馏

## 快速开始

```powershell
uv sync
uv run python main.py
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
- `load_sft_checkpoint_entrypoint(...)`
- `run_rl_baseline_entrypoint(...)`

示例：

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

print(result.status)
print(result.notes[1])
print(result.notes[2])
```

说明：

- 不传 `orchestrator_policy` 或 `orchestrator_checkpoint` 时，默认走 deterministic planner
- 传 `orchestrator_policy` 时，走 direct learned YAML boundary
- 传 `orchestrator_checkpoint` 时，仓库会从 checkpoint 目录、metadata 文件或 training artifact 中显式解析 checkpoint，再走 checkpoint-backed frozen inference

## RL 训练路径

当前 RL 路径已经不再只是写 rollout summary，而是会：

- 从显式 source checkpoint 开始
- 通过当前 bounded solve loop 收集 grouped rollouts
- 记录每个 rollout 的 execution outcome、reward breakdown、topology YAML 和 resulting checkpoint id
- 产出更新后的 checkpoint metadata 与 `weights.stub`

当前优化器仍然是 repository-local 的 GRPO-shaped stub，不宣称与论文中的大规模 RL 训练完全等价。

## 当前 checkpoint runtime 约束

- 当前仓库只支持 `orchestrator_device="cpu"`
- 如果一个目录下有多个 checkpoint，必须额外传 `orchestrator_checkpoint_id`
- 当前 frozen inference 仍是 repository-local mock policy，不是生产级模型 serving

## 文档同步要求

每完成一张任务卡，仓库要求同步检查并更新：

- `README.md`
- `README_ZH.md`
- `API.md`
- `use.md`

## 下一步建议

如果继续沿主线推进，最合理的下一步通常是：

1. 用真实模型加载替换当前 mock checkpoint runtime
2. 把 RL 产物继续接到更完整的 checkpoint 更新与在线推理
3. 在 benchmark-aligned evaluation 上验证 frozen inference
