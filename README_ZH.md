# AgentConductor

AgentConductor 是一个面向后端的 Python 项目，目标是把论文 `2602.17100v1.pdf` 中的方法整理成可复用的软件系统。

当前仓库已经提供：

- 基于 `uv` 管理的 `src/` 布局 Python 包
- 从论文方法抽象出来的 typed domain models
- 有界多轮 `solve_problem(...)` Python API
- `TopologyPlan <-> YAML` 的稳定传输契约
- deterministic planner、learned policy boundary、checkpoint-backed frozen inference 三条规划路径
- 本地 judge、benchmark adapter、SFT checkpoint、RL checkpoint update、benchmark-aligned evaluation 的基础边界

当前实现仍然不是论文级完整 runtime。仓库现在更适合做方法复现、接口接线、checkpoint 管理和可审计评测，而不是直接宣称精确 leaderboard reproduction。

## 当前状态

已完成的关键任务包括：

- `TOP-02`：YAML-native topology serialization / parsing
- `ORCH-02`：model-backed YAML orchestrator boundary
- `TRAIN-02`：checkpoint-producing supervised training path
- `ORCH-03`：checkpoint-backed frozen inference 接入在线 solve loop
- `RL-02`：从 source checkpoint 出发的 RL checkpoint update path
- `EVAL-02`：benchmark-aligned frozen-inference evaluation，产出 per-attempt artifacts 与 `pass@1` / `pass@k`
- `BENCH-01` 到 `BENCH-04`：canonical benchmark dataset 与 Python / JavaScript 本地 benchmark harness

仍未完成的重点包括：

- compiled-language benchmark runtime
- vendor-native benchmark runtime
- 真实模型权重加载与生产级 frozen inference
- 论文规模训练与严格 leaderboard 复现

## 根目录文档

- [README.md](/D:/code/PaperCreate/AgentConductor/README.md)：英文总览
- [API.md](/D:/code/PaperCreate/AgentConductor/API.md)：公开 API 与 public types
- [use.md](/D:/code/PaperCreate/AgentConductor/use.md)：常见调用方式与工作流
- [docs/tasks.md](/D:/code/PaperCreate/AgentConductor/docs/tasks.md)：任务卡与状态
- [docs/Paper.md](/D:/code/PaperCreate/AgentConductor/docs/Paper.md)：论文实现导向总结

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
- `run_benchmark_evaluation_entrypoint(...)`
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

## 评测路径

当前评测路径会：

- 读取 canonical benchmark dataset
- 用 frozen orchestrator checkpoint 跑 solve
- 将 candidate 再送进 benchmark adapter 复判
- 写出 per-attempt artifacts 与 aggregate metrics

当前 artifact 会显式记录：

- `dataset_version`
- `harness_version`
- `runtime_mode`
- `checkpoint_id`
- `pass@1`
- `pass@k`

当前默认 runtime 仍然是 repository-local benchmark harness，而不是 vendor-native benchmark service。因此这些结果应被视为 benchmark-aligned metrics，不应直接表述为严格论文级 leaderboard claim。

## Checkpoint Runtime 约束

- 当前仓库只支持 `orchestrator_device="cpu"`
- 如果一个目录下有多个 checkpoint，必须额外传 `orchestrator_checkpoint_id`
- 当前 frozen inference 仍然是 repository-local mock policy，不是生产级 model serving

## 文档同步要求

每完成一张任务卡，仓库要求同步检查并更新：

- `README.md`
- `README_ZH.md`
- `API.md`
- `use.md`

## 下一步建议

如果继续沿主线推进，通常优先做：

1. 补上 vendor-native benchmark runtime
2. 扩展 compiled-language benchmark execution
3. 用真实模型加载替换当前 mock checkpoint runtime
