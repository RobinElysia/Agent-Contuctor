"""Application service for distributed candidate evaluation."""

from __future__ import annotations

from agentconductor.domain.distributed import (
    DistributedEvaluationBatch,
    DistributedEvaluationConfig,
    DistributedEvaluationTask,
)
from agentconductor.infrastructure.distributed import LocalDistributedEvaluationOrchestrator


def evaluate_candidates_distributed(
    tasks: tuple[DistributedEvaluationTask, ...],
    *,
    config: DistributedEvaluationConfig | None = None,
    orchestrator: LocalDistributedEvaluationOrchestrator | None = None,
) -> DistributedEvaluationBatch:
    """Submit and collect a batch of candidate evaluations."""
    active_config = config or DistributedEvaluationConfig()
    active_orchestrator = orchestrator or LocalDistributedEvaluationOrchestrator()
    return active_orchestrator.evaluate(tasks, config=active_config)
