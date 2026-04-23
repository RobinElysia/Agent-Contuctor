# AgentConductor

AgentConductor 是一个面向后端的 Python 项目，目标是把论文 `2602.17100v1.pdf` 中的方法整理成可复用、可测试、可持续迭代的软件系统。

当前仓库已经提供：

- 基于 `uv` 管理的 `src/` 布局 Python 包
- 论文方法对应的 typed domain contracts
- 有界多轮 `solve_problem(...)` API
- `TopologyPlan <-> YAML` 的稳定传输契约
- deterministic planner、learned orchestrator boundary、checkpoint-backed frozen inference
- benchmark dataset ingestion、benchmark adapter seam、SFT checkpoint、RL checkpoint update、benchmark-aligned evaluation
- Python / JavaScript 本地 benchmark harness
- phase-aware benchmark contract，用来显式表示 compile / run 两个阶段
- vendor-native benchmark runtime boundary，用来显式表示 submission / polling / terminal verdict / artifact provenance

当前状态仍然不是论文级完整 runtime。仓库更适合做方法复现、接口接线、artifact 审计和可重复评测，而不是直接宣称严格 leaderboard reproduction。

## 当前进度

已完成的关键任务包括：

- `TOP-02`：YAML-native topology serialization / parsing
- `ORCH-02`：model-backed YAML orchestrator boundary
- `TRAIN-02`：checkpoint-producing supervised training path
- `ORCH-03`：checkpoint-backed frozen inference 接入在线 solve loop
- `RL-02`：从 source checkpoint 出发的 RL checkpoint update path
- `EVAL-02`：benchmark-aligned frozen-inference evaluation，产出 per-attempt artifacts 与 `pass@1` / `pass@k`
- `BENCH-01` 到 `BENCH-04`：canonical benchmark dataset + Python / JavaScript 本地 benchmark harness
- `BENCH-05`：compiled-language compile / run phase contract
- `BENCH-07`：vendor-native benchmark runtime boundary

仍未完成的重点：

- `BENCH-06`：第一个本地 compiled-language harness
- 真正的外部 vendor-native benchmark service 接入
- 真实模型权重加载与生产级 frozen inference
- 论文规模训练与严格 leaderboard 复现

## 根目录文档

- [README.md](/D:/code/PaperCreate/AgentConductor/README.md)：英文总览
- [API.md](/D:/code/PaperCreate/AgentConductor/API.md)：公开 API 与 public types
- [use.md](/D:/code/PaperCreate/AgentConductor/use.md)：常见使用方式与工作流
- [docs/tasks.md](/D:/code/PaperCreate/AgentConductor/docs/tasks.md)：任务卡与状态
- [docs/Paper.md](/D:/code/PaperCreate/AgentConductor/docs/Paper.md)：论文实现导向总结

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

## Benchmark 能力边界

当前 benchmark 相关能力分成两类：

- repository-local harness
  现在默认支持 Python / JavaScript 本地执行
- vendor-native runtime boundary
  现在已经有 typed submission / polling / result lifecycle，但仓库内置验证仍然是 fixture-driven stub，而不是 live external service

当前 benchmark contract 已经支持：

- `BenchmarkExecutionSettings.phase_settings`
- compile phase 与 run phase 的显式配置
- source layout、command template、executable target、phase-specific resource limits
- `BenchmarkPhaseResult` 与 `BenchmarkPhaseArtifactIdentifiers`
- `BenchmarkVendorSubmissionReceipt` 与 `BenchmarkVendorPollSnapshot`

这意味着 compile failure、run-time failure、adapter error、vendor poll lifecycle 现在都能被结构化记录，而不是再被压平成一个 generic runtime error。

## 评测路径

当前评测路径会：

- 读取 canonical benchmark dataset
- 用 frozen orchestrator checkpoint 跑 solve
- 将 candidate 再送入 benchmark adapter 复判
- 输出 per-attempt artifacts 与 aggregate metrics

artifact 会显式记录：

- `dataset_version`
- `harness_version`
- `runtime_mode`
- `checkpoint_id`
- `pass@1`
- `pass@k`

默认评测 runtime 仍然是 repository-local benchmark harness，因此这些结果应被视为 benchmark-aligned metrics。只有当调用方明确切换到真实 vendor-native adapter，并且外部 benchmark 约束满足时，才更接近论文级 reproduction。

## 下一步建议

如果继续沿主链推进，优先顺序通常是：

1. 完成 `BENCH-06`，补上第一个本地 compiled-language harness
2. 用真实外部服务替换当前 fixture-driven vendor-native stub
3. 用真实模型加载替换当前 mock checkpoint runtime
