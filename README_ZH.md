# AgentConductor

AgentConductor 是一个面向后端的 Python 项目，旨在将论文 `2602.17100v1.pdf` 中的方法复现为可复用的软件系统。

该仓库目前提供：

- 使用 `uv` 管理的 `src/` 布局 Python 包
- 基于论文提炼的带类型领域模型
- 第一个稳定的、面向问题调用的 Python API 边界
- 面向 benchmark 元数据、verdict 映射和运行产物的带类型 adapter seam
- APPS 风格 JSONL benchmark 数据集的 canonical ingestion
- 面向 Python 和 JavaScript canonical benchmark record 的多语言执行路径
- 针对引导层和 API 层的聚焦测试

该仓库尚未实现完整的论文运行时。当前 API 返回的是符合论文约束的结构化解题计划，而非完整的拓扑执行结果。

## 当前状态

已完成的里程碑：

- `DOC-01`：仓库指引和持久化项目文档
- `RES-01`：在 `docs/Paper.md` 中面向实现的论文提炼
- `BOOT-01`：包引导、入口点和测试
- `API-01`：第一个带类型的可调用 API 边界
- `BENCH-01`：外部 benchmark adapter 的带类型契约边界
- `BENCH-02`：APPS 风格 benchmark 数据集 ingestion 与 canonical normalization
- `BENCH-03`：基于 canonical benchmark record 的 Python 执行路径
- `BENCH-04`：Python/JavaScript 多语言 benchmark dispatch，以及更严格的 stdin 脚本执行语义

尚未实现：

- 拓扑 YAML 生成
- 超出当前 Python/JavaScript 本地 harness 的 benchmark 执行
- 精确到论文规模的 checkpoint 训练或 benchmark leaderboard 复现

## 项目布局

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

关键位置：

- `docs/requirements.md`：产品和交付约束
- `docs/tech.md`：架构和验证规则
- `docs/tasks.md`：任务卡片和当前任务状态
- `docs/Paper.md`：面向实现的论文提炼
- `src/agentconductor/domain/`：带类型的核心契约
- `src/agentconductor/application/`：应用服务
- `src/agentconductor/interfaces/`：公共入口点
- `API.md`：面向调用方的 API 文档

## 要求

- Python `>=3.11`
- 使用 `uv` 进行环境和依赖管理

## 快速开始

创建或同步环境：

```powershell
uv sync
```

运行当前 CLI 入口点：

```powershell
uv run python main.py
```

或使用包脚本：

```powershell
uv run agentconductor
```

预期输出：

```text
agentconductor: roles=6, max_turns=2
```

## Python API

稳定的包入口点是 `solve_problem(...)`。

```python
from agentconductor import DifficultyLevel, ProblemInstance, solve_problem

result = solve_problem(
    ProblemInstance(
        identifier="apps-two-sum",
        prompt="编写一个函数，返回两个相加等于目标值的下标。",
        difficulty=DifficultyLevel.EASY,
    )
)

print(result.status)
print(result.max_nodes)
```

当前 API 返回一个描述基线计划的带类型 `SolveResult`：

- 选定的难度
- 允许的轮数预算
- 与难度相关的节点预算
- 当前可用的角色集
- 关于尚未实现内容的实现备注

完整的接口契约请参见 [API.md](/D:/code/PaperCreate/AgentConductor/API.md)。

## 测试

运行聚焦的测试套件：

```powershell
uv run pytest tests/test_bootstrap.py tests/test_api.py
```

## 设计说明

- 该包将论文方法逻辑、应用编排和接口分离。
- 第一个 API 有意保持窄范围。它是一个稳定的 Python 边界，而不是 HTTP 服务。
- benchmark 集成现在有独立的带类型边界，用于承载 benchmark 问题元数据、执行设置、verdict 映射和运行产物标识。
- 当前 benchmark runtime 支持 Python 和 JavaScript。function-style record 走语言感知的调用边界，stdin-style record 则按独立脚本执行，更接近真实 benchmark 语义。
- JavaScript function 路径支持 CommonJS export，同时对顶层 `solve(...)` 定义加了一层窄兼容 shim；这一点属于实现推断，不是 benchmark 原生规则。
- 当行为是推断而非论文明确说明时，仓库会显式记录这一点。

## 接下来的可能步骤

- 将 benchmark dataset normalization 扩展到 APPS 之外的数据源
- 将 benchmark execution 扩展到当前 Python/JavaScript 本地 harness 之外，尤其是编译型语言和 vendor-native runtime
- 继续推进 checkpoint 训练与 frozen-inference orchestration 路径
