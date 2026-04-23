# AgentConductor

AgentConductor 是一个面向后端的 Python 项目，目标是把论文 `2602.17100v1.pdf` 的方法整理成可复用的软件系统。

当前仓库已经提供：

- 基于 `uv` 管理的 `src/` 布局 Python 包
- 面向论文方法的 typed domain contracts
- 稳定的 Python solve API，支持 bounded multi-turn 执行
- `TopologyPlan <-> YAML` 的稳定 transport contract
- deterministic planner 与 learned orchestrator boundary
- checkpoint-backed frozen orchestrator runtime
- 非 `testing` worker 的 model-backed runtime seam
- 本地 judge、benchmark ingestion、SFT/RL artifact、benchmark-aligned evaluation

当前严格复现结论仍然是 `approximate reproduction`。统一 fidelity checklist 见 [docs/reproduction.md](/D:/code/PaperCreate/AgentConductor/docs/reproduction.md)。

## 当前状态

最近完成的关键任务包括：

- `TOP-02`：Topology YAML contract 与 typed parsing
- `ORCH-02`：model-backed YAML orchestrator boundary
- `TRAIN-02`：可加载 checkpoint metadata 的 SFT 路径
- `ORCH-03`：checkpoint 接入在线 frozen inference
- `ORCH-04`：从 checkpoint runtime bundle 加载 frozen orchestrator
- `EXEC-02`：非 `testing` worker 改为显式 model-backed runtime
- `TRAIN-03`：paper-oriented synthetic YAML-topology SFT corpus 扩展，默认支持 4,500 样本 dataset preparation，并记录 dataset sidecar metadata、optimizer/tokenizer/backbone provenance 与 reduced-scale 标记
- `RL-02`：checkpoint lineage 与 grouped rollout artifact
- `EVAL-02`：checkpoint-backed benchmark-aligned evaluation

当前主线目标是 `RL + LLM` 任务编排，不再把 benchmark fidelity 或 strict reproduction 作为主阻塞项。

## 根目录文档

- [README.md](/D:/code/PaperCreate/AgentConductor/README.md)：英文总览
- [API.md](/D:/code/PaperCreate/AgentConductor/API.md)：公开 API 与类型契约
- [use.md](/D:/code/PaperCreate/AgentConductor/use.md)：常见使用方式
- [docs/tasks.md](/D:/code/PaperCreate/AgentConductor/docs/tasks.md)：任务卡与状态
- [docs/Paper.md](/D:/code/PaperCreate/AgentConductor/docs/Paper.md)：论文方法整理
- [docs/tech.md](/D:/code/PaperCreate/AgentConductor/docs/tech.md)：技术边界与架构约束
- [docs/reproduction.md](/D:/code/PaperCreate/AgentConductor/docs/reproduction.md)：严格复现缺口审计

## 现在能做什么

- 用 `plan_problem_topology(...)` 或 `plan_problem_topology_candidate(...)` 生成 topology
- 用 `solve_problem(...)` 跑 bounded multi-turn solve
- 用 `orchestrator_checkpoint=...` 从 checkpoint runtime bundle 做 frozen inference
- 用 `worker_runtime=...` 替换非 `testing` worker runtime
- 生成 paper-oriented synthetic SFT dataset，并写出 dataset sidecar metadata、training manifest、checkpoint metadata
- 运行 repository-local RL checkpoint update path，并保留 rollout artifacts

## 当前边界

- frozen orchestrator runtime 依赖 checkpoint 内的 `orchestrator-runtime.json`
- 默认只支持 `orchestrator_device="cpu"`
- 默认 worker runtime 仍是 repository-local `gpt-4o-mini-compatible-stub`
- `TRAIN-03` 已把 SFT 数据准备推进到 paper-oriented 4,500 样本规模，但训练本体仍是 repository-local approximation，不应宣称 exact paper-scale SFT
- `RL-02` 仍是轻量 GRPO-shaped path，后续真正的主线任务是 `RL-03`
