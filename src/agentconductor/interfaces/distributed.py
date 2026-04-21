"""Public entrypoint for distributed candidate evaluation."""

from __future__ import annotations

from agentconductor.application.distributed import evaluate_candidates_distributed
from agentconductor.domain.distributed import (
    DistributedEvaluationBatch,
    DistributedEvaluationConfig,
    DistributedEvaluationTask,
)
from agentconductor.infrastructure.distributed import LocalDistributedEvaluationOrchestrator


def evaluate_candidate_batch(
    tasks: tuple[DistributedEvaluationTask, ...],
    *,
    config: DistributedEvaluationConfig | None = None,
    orchestrator: LocalDistributedEvaluationOrchestrator | None = None,
) -> DistributedEvaluationBatch:
    """Evaluate a batch of candidate solutions through the distributed boundary."""
    return evaluate_candidates_distributed(
        tasks,
        config=config,
        orchestrator=orchestrator,
    )
