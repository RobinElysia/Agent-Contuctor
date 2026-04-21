import time

from agentconductor import (
    AgentRole,
    CodeCandidate,
    DistributedEvaluationConfig,
    DistributedEvaluationStatus,
    DistributedEvaluationTask,
    JudgeResourceLimits,
    JudgeTestCase,
    ProblemInstance,
    SandboxExecutionResult,
    SandboxTestSpec,
    TestingOutcome,
    evaluate_candidate_batch,
)
from agentconductor.infrastructure.distributed import (
    LocalDistributedEvaluationOrchestrator,
)


def test_distributed_evaluation_batch_collects_parallel_successes() -> None:
    tasks = (
        DistributedEvaluationTask(
            task_id="candidate-1",
            problem=ProblemInstance(identifier="dist-pass-1", prompt="Return the sum."),
            candidate=CodeCandidate(
                step_index=1,
                agent_name="coder_1",
                role=AgentRole.CODING,
                source_code="def solve(a, b):\n    return a + b\n",
            ),
            spec=SandboxTestSpec(
                entrypoint="solve",
                test_cases=(JudgeTestCase(name="sample", arguments=(1, 2), expected_output=3),),
                resource_limits=JudgeResourceLimits(cpu_time_seconds=1.0),
            ),
        ),
        DistributedEvaluationTask(
            task_id="candidate-2",
            problem=ProblemInstance(identifier="dist-pass-2", prompt="Return the sum."),
            candidate=CodeCandidate(
                step_index=1,
                agent_name="coder_2",
                role=AgentRole.CODING,
                source_code="def solve(a, b):\n    return a + b\n",
            ),
            spec=SandboxTestSpec(
                entrypoint="solve",
                test_cases=(JudgeTestCase(name="sample", arguments=(3, 4), expected_output=7),),
                resource_limits=JudgeResourceLimits(cpu_time_seconds=1.0),
            ),
        ),
    )

    batch = evaluate_candidate_batch(
        tasks,
        config=DistributedEvaluationConfig(max_workers=2, max_retries=0),
    )

    assert batch.completed_count == 2
    assert batch.failed_count == 0
    assert batch.timed_out_count == 0
    assert tuple(result.task_id for result in batch.results) == ("candidate-1", "candidate-2")
    assert all(result.status is DistributedEvaluationStatus.COMPLETED for result in batch.results)
    assert all(
        result.sandbox_result is not None
        and result.sandbox_result.outcome is TestingOutcome.PASSED
        for result in batch.results
    )


def test_distributed_evaluation_batch_reports_collection_timeout() -> None:
    class SlowOrchestrator(LocalDistributedEvaluationOrchestrator):
        def _run_task(self, *, task, config):
            del task, config
            time.sleep(0.2)
            return super()._run_task  # pragma: no cover

    task = DistributedEvaluationTask(
        task_id="timeout",
        problem=ProblemInstance(identifier="dist-timeout", prompt="Any prompt."),
        candidate=CodeCandidate(
            step_index=1,
            agent_name="coder_timeout",
            role=AgentRole.CODING,
            source_code="def solve():\n    return 1\n",
        ),
        spec=SandboxTestSpec(
            entrypoint="solve",
            test_cases=(JudgeTestCase(name="sample", expected_output=1),),
            resource_limits=JudgeResourceLimits(cpu_time_seconds=1.0),
        ),
    )

    orchestrator = LocalDistributedEvaluationOrchestrator(
        sandbox_factory=lambda: _NeverReachedSandbox()
    )
    orchestrator._run_task = SlowOrchestrator()._run_task  # type: ignore[method-assign]

    batch = evaluate_candidate_batch(
        (task,),
        config=DistributedEvaluationConfig(
            max_workers=1,
            max_retries=0,
            collection_timeout_seconds=0.05,
        ),
        orchestrator=orchestrator,
    )

    assert batch.completed_count == 0
    assert batch.timed_out_count == 1
    assert batch.results[0].status is DistributedEvaluationStatus.TIMED_OUT


def test_distributed_evaluation_batch_retries_worker_failures() -> None:
    attempts = {"count": 0}

    class FlakySandbox:
        def evaluate(self, problem, candidate, spec) -> SandboxExecutionResult:
            del problem, candidate, spec
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise RuntimeError("transient worker crash")
            return SandboxExecutionResult(
                outcome=TestingOutcome.PASSED,
                diagnostics=("Recovered on retry.",),
            )

    task = DistributedEvaluationTask(
        task_id="retry",
        problem=ProblemInstance(identifier="dist-retry", prompt="Any prompt."),
        candidate=CodeCandidate(
            step_index=1,
            agent_name="coder_retry",
            role=AgentRole.CODING,
            source_code="def solve():\n    return 1\n",
        ),
        spec=SandboxTestSpec(
            entrypoint="solve",
            test_cases=(JudgeTestCase(name="sample", expected_output=1),),
            resource_limits=JudgeResourceLimits(cpu_time_seconds=1.0),
        ),
    )

    batch = evaluate_candidate_batch(
        (task,),
        config=DistributedEvaluationConfig(max_workers=1, max_retries=1),
        orchestrator=LocalDistributedEvaluationOrchestrator(
            sandbox_factory=lambda: FlakySandbox()
        ),
    )

    assert attempts["count"] == 2
    assert batch.results[0].status is DistributedEvaluationStatus.COMPLETED
    assert batch.results[0].attempt_count == 2


class _NeverReachedSandbox:
    def evaluate(self, problem, candidate, spec) -> SandboxExecutionResult:
        del problem, candidate, spec
        raise AssertionError("sandbox should not be reached before the collection timeout")
