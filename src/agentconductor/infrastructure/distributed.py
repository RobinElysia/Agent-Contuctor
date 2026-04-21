"""Local distributed orchestration for parallel candidate evaluation."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass
from typing import Callable

from agentconductor.domain.distributed import (
    DistributedEvaluationBatch,
    DistributedEvaluationConfig,
    DistributedEvaluationResult,
    DistributedEvaluationStatus,
    DistributedEvaluationTask,
)
from agentconductor.domain.execution import SandboxExecutionResult
from agentconductor.infrastructure.sandbox import PythonSubprocessJudgeAdapter

SandboxFactory = Callable[[], PythonSubprocessJudgeAdapter]


@dataclass(slots=True)
class _SubmittedEvaluationBatch:
    tasks: tuple[DistributedEvaluationTask, ...]
    config: DistributedEvaluationConfig
    executor: ThreadPoolExecutor
    futures: dict[str, Future[DistributedEvaluationResult]]


class LocalDistributedEvaluationOrchestrator:
    """Evaluate multiple candidates concurrently while preserving typed results."""

    def __init__(
        self,
        *,
        sandbox_factory: SandboxFactory | None = None,
    ) -> None:
        self._sandbox_factory = sandbox_factory or PythonSubprocessJudgeAdapter

    def submit(
        self,
        tasks: tuple[DistributedEvaluationTask, ...],
        *,
        config: DistributedEvaluationConfig,
    ) -> _SubmittedEvaluationBatch:
        executor = ThreadPoolExecutor(max_workers=config.max_workers)
        futures = {
            task.task_id: executor.submit(self._run_task, task=task, config=config)
            for task in tasks
        }
        return _SubmittedEvaluationBatch(
            tasks=tasks,
            config=config,
            executor=executor,
            futures=futures,
        )

    def collect(
        self,
        submitted: _SubmittedEvaluationBatch,
    ) -> DistributedEvaluationBatch:
        ordered_results: list[DistributedEvaluationResult] = []
        try:
            for task in submitted.tasks:
                future = submitted.futures[task.task_id]
                try:
                    result = future.result(
                        timeout=submitted.config.collection_timeout_seconds
                    )
                except TimeoutError:
                    result = DistributedEvaluationResult(
                        task_id=task.task_id,
                        status=DistributedEvaluationStatus.TIMED_OUT,
                        attempt_count=submitted.config.max_retries + 1,
                        diagnostics=(
                            "Distributed collection timed out before the worker returned a result.",
                        ),
                    )
                ordered_results.append(result)
        finally:
            submitted.executor.shutdown(wait=False, cancel_futures=False)

        return DistributedEvaluationBatch(
            tasks=submitted.tasks,
            config=submitted.config,
            results=tuple(ordered_results),
        )

    def evaluate(
        self,
        tasks: tuple[DistributedEvaluationTask, ...],
        *,
        config: DistributedEvaluationConfig,
    ) -> DistributedEvaluationBatch:
        submitted = self.submit(tasks, config=config)
        return self.collect(submitted)

    def _run_task(
        self,
        *,
        task: DistributedEvaluationTask,
        config: DistributedEvaluationConfig,
    ) -> DistributedEvaluationResult:
        last_error: Exception | None = None
        for attempt_index in range(config.max_retries + 1):
            try:
                sandbox = self._sandbox_factory()
                result: SandboxExecutionResult = sandbox.evaluate(
                    task.problem,
                    task.candidate,
                    task.spec,
                )
                return DistributedEvaluationResult(
                    task_id=task.task_id,
                    status=DistributedEvaluationStatus.COMPLETED,
                    attempt_count=attempt_index + 1,
                    sandbox_result=result,
                    diagnostics=result.diagnostics,
                )
            except Exception as exc:  # pragma: no cover - guarded through tests
                last_error = exc

        assert last_error is not None
        return DistributedEvaluationResult(
            task_id=task.task_id,
            status=DistributedEvaluationStatus.FAILED,
            attempt_count=config.max_retries + 1,
            diagnostics=(
                f"Distributed worker failed: {last_error.__class__.__name__}: {last_error}.",
            ),
        )
