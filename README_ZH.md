# AgentConductor

AgentConductor 是一个面向后端的 Python 项目，旨在将 `2602.17100v1.pdf` 中的方法复现为一个可复用的软件系统。

该仓库目前提供：

- 一个使用 `uv` 管理的 `src/` 布局的 Python 包
- 从论文提炼中衍生出的类型化领域模型
- 一个稳定的 Python 求解 API，用于在确定性或学习型编排器路径上执行有界多轮执行
- 一个类型化的多轮求解状态契约，用于记录轮次历史及后续修订
- 一个确定性拓扑规划器，能生成经过验证的单轮计划
- 一个学习型编排器策略边界，能生成拓扑 YAML 候选方案并将其解析为经过验证的类型化计划
- 一个由检查点支持的冻结编排器运行时，加载仓库本地的运行时捆绑包，而不是仅依赖元数据和 `weights.stub`
- 一个单轮图执行器，其非测试类工作器角色现在通过显式的模型支持的运行时接缝运行，其测试角色通过本地子进程评判适配器运行
- 一个用于基准元数据、裁决规范化和运行工件标识符的类型化外部基准适配器接缝
- 对 APPS 风格 JSONL 记录的规范基准数据集摄取
- 针对 Python 和 JavaScript 规范基准记录的多语言基准执行路径
- 现在显式地分别建模编译和运行阶段的、具有阶段感知能力的基准执行契约
- 针对 Java 的本地编译语言基准路径，以及显式的 C++ 工具链错误报告
- 一个类型化的供应商原生基准运行时边界，具有由夹具驱动的提交和轮询生命周期覆盖
- 针对引导层和 API 层的针对性测试

该仓库尚未完全实现论文的运行时。当前的 API 可以在配置的轮次预算内，通过确定性或由检查点支持的拓扑修订来运行，并且仓库现在能生成与基准对齐的评估工件。本地评估仍然默认使用仓库本地的工具链适配器，而供应商原生的运行时边界目前通过由夹具驱动的桩进行验证，而非实时外部服务。

当前的严格复现声明：`近似复现（approximate reproduction）`

## 当前状态

已完成的里程碑：

- `DOC-01`: 仓库指南和持久的项目文档
- `RES-01`: 在 `docs/Paper.md` 中的面向实现的论文提炼
- `BOOT-01`: 包引导、入口点和测试
- `API-01`: 第一个类型化的可调用 API 边界
- `TOP-01`: 单轮拓扑模式（Schema）和验证
- `TOP-02`: 围绕类型化拓扑契约的 YAML 原生拓扑序列化和解析
- `ORCH-01`: 确定性的基于规则的拓扑规划
- `ORCH-02`: 用于冻结推理和后续轮次修订的、模型支持的 YAML 编排边界
- `EXEC-01`: 确定性的单轮拓扑执行
- `JUDGE-01`: 更丰富的子进程评判边界，具有显式的测试用例和软性资源限制
- `JUDGE-02`: 更严格的评判规范化和类型化的逐用例裁决报告
- `SBX-02`: 对挂钟时间限制更强的逐用例子进程强制执行，并具有平台感知的 CPU 和内存控制
- `SBX-03`: 在主机运行时允许专用作业分配的情况下，基于 Windows 作业对象的工作器绑定，用于强制内存限制
- `DEVX-01`: 针对受限缓存环境的仓库本地 `uv` 验证路径
- `SBX-04`: 针对禁止专用作业附着的主机运行时，提供显式的 Windows 脱离式启动和降级报告
- `SBX-05`: 类型化的 Windows CPU 限制能力报告，标记 CPU 强制在已验证的策略存在之前不受支持
- `DIST-01`: 用于并行候选评判的本地分布式评估边界，具有显式的并发、重试和收集超时控制
- `EVAL-01`: 基于 JSON 的批量评估流水线，记录每个问题的结果和聚合摘要
- `TRAIN-01`: 合成拓扑数据集生成，加上一个可复现的 SFT 基线工件路径
- `TRAIN-02`: 以 YAML 为目标并具有可加载检查点元数据的、生成检查点的监督训练路径
- `TRAIN-03`: 面向论文的合成 YAML 拓扑 SFT 语料库扩展，带有数据集附属元数据、可审计的优化器或分词器来源，以及显式的缩减规模标签
- `ORCH-03`: 为在线求解循环和学习型规划入口点接线的、由检查点支持的冻结推理
- `ORCH-04`: 用于冻结编排器推理的仓库本地检查点捆绑包加载，并具有显式的运行时工件验证
- `EXEC-02`: 具有每个代理的运行时或模型来源的、模型支持的非测试类工作器运行时接缝
- `RL-01`: 仓库本地的奖励分解和 RL 风格的展开工件生成
- `RL-02`: 具有分组展开工件、轻量级 GRPO 风格更新摘要和可加载的更新后检查点元数据的、更新检查点的 RL 路径
- `RL-03`: 面向论文的分组展开 RL 路径，具有组归一化优势、分组更新工件和写入检查点运行时来源的 RL 谱系
- `EVAL-02`: 具有结构化逐次尝试工件、数据集或工具链来源以及 `pass@1` 或 `pass@k` 聚合指标的、与基准对齐的冻结推理评估
- `BENCH-01`: 用于执行元数据和裁决映射的类型化外部基准适配器接缝
- `BENCH-02`: 针对 APPS 风格 JSONL 工件的规范基准数据集摄取和规范化
- `BENCH-03`: 基于规范基准记录的具体 Python 基准执行路径
- `BENCH-04`: 针对 Python 和 JavaScript 记录的多语言基准执行分派，以及对标准输入（stdin）脚本更严格的保真度
- `BENCH-05`: 针对编译语言的编译或运行设置及诊断的、具有阶段感知能力的基准执行契约
- `BENCH-06`: 具有"先编译后运行"（compile-then-run）执行方式的 Java，以及显式 C++ 工具链诊断的本地编译语言基准工具链
- `BENCH-07`: 具有提交回执、轮询历史和工件来源的类型化供应商原生基准运行时边界

尚未实现：

- 在 `g++` 不可用环境中的仓库内置 C++ 工具链路径
- 精确的论文规模检查点训练或基准排行榜复现

当前记录在 `docs/reproduction.md` 中的精确复现阻碍因素：

- 论文保真度的工作器代理和检索器保真度
- 论文规模的 SFT 和 RL 训练保真度
- 基准级的检查点支持的冻结推理（而非当前的仓库本地捆绑包运行时）
- 完整的论文基准数据集覆盖
- 实时供应商原生基准运行时保真度
- 跨主机的稳定编译语言覆盖

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

- `docs/requirements.md`: 产品和交付约束
- `docs/tech.md`: 架构和验证规则
- `docs/tasks.md`: 任务卡片和当前任务状态
- `docs/Paper.md`: 面向实现的论文提炼
- `docs/reproduction.md`: 精确 vs 近似复现检查清单和阻碍因素
- `use.md`: 根级别使用指南，涵盖常见仓库工作流
- `README_ZH.md`: 当前仓库状态的中文概述
- `src/agentconductor/domain/`: 类型化核心契约
- `src/agentconductor/application/`: 应用服务
- `src/agentconductor/interfaces/`: 公共入口点
- `API.md`: 面向调用者的 API 文档

## 环境要求

- Python `>=3.11`
- `uv` 用于环境和依赖管理

## 快速开始

创建或同步环境：

```powershell
uv sync
```

运行当前的 CLI 入口点：

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

稳定的包入口点是 `solve_problem(...)`, `plan_problem_topology(...)`, `plan_problem_topology_candidate(...)`, `revise_problem_topology_candidate(...)`, `execute_topology_plan(...)`, `serialize_topology_plan_to_yaml(...)`, `parse_topology_plan_yaml(...)`, 和 `load_sft_checkpoint_entrypoint(...)`。

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
        prompt="在严格约束下解决一个图的最短路径问题。",
        difficulty=DifficultyLevel.MEDIUM,
    )
)

result = solve_problem(
    ProblemInstance(
        identifier="apps-two-sum",
        prompt="编写一个函数，返回两数之和等于目标值的两个索引。",
        difficulty=DifficultyLevel.EASY,
    )
)

candidate = plan_problem_topology_candidate(
    ProblemInstance(
        identifier="apps-policy",
        prompt="修复失败的实现。",
        difficulty=DifficultyLevel.EASY,
    ),
    orchestrator_policy=my_policy,  # 实现了 TopologyOrchestratorPolicy
)

checkpoint_result = solve_problem(
    ProblemInstance(
        identifier="apps-checkpoint",
        prompt="修复失败的实现。",
        difficulty=DifficultyLevel.EASY,
    ),
    max_turns=2,
    orchestrator_checkpoint="artifacts/sft-run.json",
)

execution = execute_topology_plan(
    ProblemInstance(
        identifier="apps-two-sum",
        prompt="编写一个函数，返回两数之和等于目标值的两个索引。",
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

规划 API 可以返回一个类型化的 `TopologyPlan`，而 `solve_problem(...)` 现在返回一个类型化的 `SolveResult`，其中包含：

- 选定的难度
- 允许的轮次预算
- 特定难度的节点预算
- 当前可用的角色集
- 规划好的拓扑
- 结构化的执行结果
- 候选解决方案内容
- 最终测试结果
- 一个类型化的求解状态，包含轮次历史和可修订的反馈

当没有传入 `orchestrator_policy` 时，规划保持在确定性的仓库本地模板上。当传入一个策略时，`solve_problem(...)` 和 `plan_problem_topology(...)` 会通过学习型 YAML 路径进行路由，而 `plan_problem_topology_candidate(...)` 和 `revise_problem_topology_candidate(...)` 则暴露原始的 YAML 候选方案和解析后的 `TopologyPlan`。
当传入 `orchestrator_checkpoint` 时，相同的学习路径会从显式的检查点元数据和检查点自有的运行时工件中加载。当前的仓库运行时仍然是一个本地替代品，而非基准级的 Qwen 服务，但它现在加载序列化的冻结推理状态，而不是回退到仅依赖元数据的模拟行为。

执行 API 可以返回一个类型化的 `TopologyExecutionResult`，其中包含：

- 每个步骤和每个代理的结构化输出
- 每个代理已解析的上游引用
- 非测试类角色的每个代理的工作器运行时和模型标识符
- 最终的候选代码
- 评判结果和诊断信息

YAML 传输工具可以：

- 将经过验证的 `TopologyPlan` 序列化为仓库的稳定 YAML 格式
- 将仓库的 YAML 文本解析回相同类型化的 `TopologyPlan` 契约
- 保留显式的解析、模式（Schema）和逻辑失败边界

学习型编排器路径同样保留显式的失败边界：

- 策略响应中缺少 YAML 会引发 `TopologyCandidateExtractionError`
- 格式错误的 YAML 会引发现有的解析层传输错误
- 模式无效或逻辑无效的拓扑会引发现有的验证错误

完整的接口契约见 [API.md](/D:/code/PaperCreate/AgentConductor/API.md)。

## 测试

运行针对性的测试套件：

```powershell
uv run pytest
```

对于 `uv` 无法使用用户全局缓存的受限环境，请优先使用仓库本地验证包装器：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1
```

该包装器默认将 `UV_CACHE_DIR` 设到仓库内的 `.\.uv-cache`。如果你需要不同的缓存位置，请在运行任一命令前显式设置 `UV_CACHE_DIR`。

首选的验证命令：

- `powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1`
- `uv run pytest`（当当前环境已具有可用的缓存权限时）

备选的验证命令：

- `$env:UV_CACHE_DIR = ".uv-cache"; uv run pytest`
- 如果环境尚未同步，在测试命令前执行 `uv sync --locked`

运行一个小的与基准对齐的评估工件：

```powershell
uv run python -m agentconductor.interfaces.evaluation --dataset .\tests\fixtures\benchmark\apps_fixture.jsonl --output .\artifacts\eval-results.json --checkpoint .\artifacts\sft-run.json --samples-per-problem 1
```

评估数据集必须是一个受支持的规范基准数据源，如 APPS 风格的 JSONL。生成的工件记录了数据集版本、工具链版本、运行时模式、检查点 ID、复现声明、精确复现就绪状态、每次尝试的结果以及包括 `pass@1` 和 `pass@k` 在内的聚合指标。

写入当前的复现审计工件：

```powershell
uv run python -m agentconductor.interfaces.reproduction --output .\artifacts\reproduction-audit.json
```

生成合成 SFT 数据并运行生成检查点的 SFT 路径：

```powershell
uv run python -m agentconductor.interfaces.training --dataset .\artifacts\sft-dataset.jsonl --artifact .\artifacts\sft-run.json --sample-count 4500
```

检查生成的检查点元数据：

```powershell
uv run python -m agentconductor.interfaces.training --dataset .\artifacts\sft-dataset.jsonl --load-checkpoint .\artifacts\sft-run-checkpoint
```

通过由检查点支持的冻结推理运行求解请求：

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
```

在该数据集上运行仓库本地的 RL 检查点优化路径：

```powershell
uv run python -m agentconductor.interfaces.rl --dataset .\artifacts\sft-dataset.jsonl --artifact .\artifacts\rl-run.json --checkpoint .\artifacts\sft-run.json --rollout-count 8 --group-size 8
```

## 设计说明

- 该包将论文方法逻辑、应用编排和接口分离。
- 第一个 API 刻意保持狭窄。它是一个稳定的 Python 边界，而非 HTTP 服务。
- 执行器现在通过显式的模型支持的运行时接缝来路由非测试类工作器角色。默认运行时是仓库本地的，并使用 `gpt-4o-mini-compatible-stub` 模型标识符作为面向论文的占位符，而非声称真正的提供商执行。
- 测试角色仍然通过本地子进程评判适配器评估候选代码，而不是让工作器模型自行评分。
- 子进程评判器是具体的，但仍是近似的。它根据显式的测试用例、预期输出、类型化的逐用例裁决以及显式的 CPU、挂钟时间和内存限制来运行 Python 候选代码。
- 挂钟时间限制现在作为强制的逐用例子进程超时来执行。
- 在暴露 `resource` 限制的平台上，评判器还在工作器进程内应用操作系统级别的 CPU 和地址空间限制。
- 在 Windows 上，评判器现在尝试将每个工作器附着到一个专用的作业对象，并在进程级别强制实施 `memory_limit_bytes`。
- 某些主机 Windows 运行时已经将当前进程树放置在一个禁止子进程重新绑定的控制作业中。在这种情况下，仓库保留挂钟时间强制，报告显式的诊断信息，并回退到现有的近似内存路径。
- Windows 工作器启动现在在回退到普通子进程之前尝试 `CREATE_BREAKAWAY_FROM_JOB`，以便降级路径是显式且可检查的。
- Windows CPU 限制强制现在被报告为不受支持，而不是通过通用的 `cpu_time_seconds` 字段暗示。硬性挂钟超时仍然是 Windows 上唯一有保证的计时控制。
- 在没有这些原语的平台上，内存强制回退到追踪 Python 分配，并保持近似状态。
- 评判器仍然以更类似基准的方式规范换行符和行尾空格，但它尚未复现外部基准的完整运行时语义。
- 外部基准集成现在拥有自己的类型化适配器边界，用于基准问题元数据、执行设置、裁决映射和运行工件标识符。
- 内置的基准适配器是一个用于验证契约的确定性桩；它尚未对真实的基准服务执行。
- 基准数据集摄取现在支持本地 APPS 风格 JSONL 源，并将其规范化为规范的 `BenchmarkProblemDefinition` 记录。
- 仓库现在还公开了带有基准自有调用设置和测试用例的规范基准执行记录，以及一个具体的 `PythonBenchmarkJudgeAdapter`、`NodeJsBenchmarkJudgeAdapter` 和 `MultiLanguageBenchmarkJudgeAdapter`，它们通过这些记录通过基准适配器边界运行。
- 当前的基准运行时在本地支持 Python、JavaScript 和 Java。对于 Python 和 JavaScript，函数风格的记录通过具有语言感知能力的调用边界执行，而标准输入（stdin）风格的记录则作为独立脚本或具有基准自有 stdin 负载的本地"先编译后运行"工具链运行。
- 基准执行设置现在还可以为编译语言记录携带显式的编译和运行阶段契约，包括源代码布局、命令模板、可执行目标以及每个阶段的资源限制。
- 基准结果工件现在保留类型化的逐阶段诊断信息和工件标识符，以便编译失败和运行时失败在后续评估或供应商运行时报告中保持可区分。
- 第一个编译语言本地工具链是 Java。它期望主机本地有 `javac` 和 `java` 工具链，目前支持标准输入（stdin）风格的记录。
- C++ 本地适配器也已接入基准接缝，但如果主机上 `g++` 不可用，它会返回一个显式的适配器错误，而不是静默跳过执行。
- JavaScript 函数路径接受 CommonJS 导出，并且还为顶层的 `solve(...)` 定义应用一个窄义的仓库兼容性填充程序（shim）；该填充程序是一个实现推断，而非基准原生的规则。
- 当前的 APPS 规范化将 `introductory`、`interview` 和 `competition` 难度标签映射到仓库的 `easy`、`medium` 和 `hard` 层级，这是一个实现推断，而非论文明确规定的规则。
- LiveCodeBench、CodeContests、HumanEval 和 MBPP 数据集的摄取仍有待完成，并且仓库不捆绑专有或受许可限制的基准负载。
- 并行候选评估现在通过一个显式的编排边界进行，该边界具有可检查的工作器数量、重试次数和收集超时。
- 与基准对齐的评估工件现在记录了每次尝试的求解结果、基准裁决、延迟、数据集版本、工具链版本、运行时模式、复现声明、精确复现就绪状态以及聚合的通过率指标，以便后续比较不依赖于临时的日志解析。
- 当前的评估路径根据对规范基准记录的结构化重复尝试计算仓库观察到的 `pass@k`。
- SFT 路径现在同时写入规范映射目标和 YAML 拓扑目标，外加显式的源数据集附属元数据、一个训练清单文件和可加载的检查点元数据。
- 默认的 SFT 数据集生成器现在准备一个面向论文的、包含 4,500 个样本的合成 YAML 语料库，并在附属元数据文件中记录难度分布、来源配方、提示词模板版本和缩减规模状态。
- 生成的检查点工件是仓库本地的、轻量级的。它现在显式地标明了样本数量、源数据集元数据路径、来源配方、优化器名称、提示词模板版本、骨干网络名称、分词器名称、随机种子和检查点位置，但它本身仍不声称达到精确的论文规模微调保真度。
- 由检查点支持的冻结推理现在从检查点目录、元数据文件或训练工件中显式解析一个检查点。如果一个目录包含多个候选项，调用者必须传入 `orchestrator_checkpoint_id`，而不是依赖文件系统顺序。
- 当前的由检查点支持的运行时现在从检查点元数据加载一个仓库本地的 `orchestrator-runtime.json` 捆绑包。它仅支持 `device="cpu"`，并对运行时工件存在性、提示词模板兼容性和支持的设备选择保持显式检查。
- RL 路径现在消费一个显式的源检查点，通过有界求解循环收集展开记录，计算组归一化优势，写入一个专用的分组更新工件，并生成一个更新后的检查点以及展开清单工件。
- 当前的 RL 路径现在在显式的组大小配置、分组展开语义以及分离的奖励或优势阶段方面与论文更加匹配。它仍然是一个仓库本地的、缩减规模的近似实现，而非论文规模的分布式 GRPO 实现。
- 仓库现在还公开了一个供应商原生的基准运行时边界，具有类型化的提交回执、轮询历史、终端裁决映射和工件来源。当前的验证路径是由夹具驱动的，而不是由实时外部服务支持的。
- 默认的基准评估运行时仍然使用仓库本地的 Python 和 JavaScript 工具链适配器。因此，报告的指标应被视为与基准对齐（benchmark-aligned），而非精确的排行榜声明，除非调用者特意通过配置好的供应商原生适配器进行路由。
- 仓库现在还公开了一个专用的复现审计工件路径，以便未来的代理有一个稳定的位置来检查剩余的精确复现阻碍因素。
- 当行为是推断而非论文明确说明时，仓库会显式地记录这一点。

## 下一步可能步骤

- 将基准数据集规范化扩展到 APPS 风格 JSONL 数据源之外
- 将本地编译语言工具链扩展到当前以 Java 为先的路径之外，尤其是在具有可用工具链的主机上支持 C++
- 用基准级的模型推理替换仓库本地的检查点捆绑包运行时
- 用更完善的、与论文对齐的 RL 优化器替换轻量级的 GRPO 风格桩更新器
- 在许可和认证允许的情况下，用真实的外部运行时集成替换由夹具驱动的供应商原生基准桩