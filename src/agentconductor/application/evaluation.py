"""Batch evaluation pipeline built on the current solve and judge stack."""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

from agentconductor.domain.evaluation import (
    EvaluationProblemDefinition,
    EvaluationProblemResult,
    EvaluationRunArtifact,
    EvaluationSummary,
)
from agentconductor.domain.models import DifficultyLevel, ProblemInstance
from agentconductor.interfaces.api import solve_problem


def load_evaluation_dataset(dataset_path: Path) -> tuple[EvaluationProblemDefinition, ...]:
    """Load and validate a JSON dataset for batch evaluation."""
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    raw_problems = payload.get("problems")
    if not isinstance(raw_problems, list) or not raw_problems:
        raise ValueError("Evaluation dataset must contain a non-empty 'problems' list.")

    definitions: list[EvaluationProblemDefinition] = []
    for index, raw_problem in enumerate(raw_problems):
        if not isinstance(raw_problem, dict):
            raise ValueError(f"Problem at index {index} must be an object.")
        identifier = raw_problem.get("identifier")
        prompt = raw_problem.get("prompt")
        difficulty_value = raw_problem.get("difficulty")
        if not isinstance(identifier, str) or not identifier:
            raise ValueError(f"Problem at index {index} must define a non-empty string identifier.")
        if not isinstance(prompt, str) or not prompt:
            raise ValueError(f"Problem '{identifier}' must define a non-empty string prompt.")
        difficulty = None
        if difficulty_value is not None:
            try:
                difficulty = DifficultyLevel(difficulty_value)
            except ValueError as exc:
                raise ValueError(
                    f"Problem '{identifier}' has unsupported difficulty '{difficulty_value}'."
                ) from exc
        definitions.append(
            EvaluationProblemDefinition(
                identifier=identifier,
                prompt=prompt,
                difficulty=difficulty,
            )
        )
    return tuple(definitions)


def run_batch_evaluation(
    dataset_path: Path,
    output_path: Path,
    *,
    max_workers: int = 1,
) -> EvaluationRunArtifact:
    """Run the current solve stack over a dataset and write JSON artifacts."""
    if max_workers < 1:
        raise ValueError("max_workers must be at least 1")

    problems = load_evaluation_dataset(dataset_path)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = tuple(executor.map(_evaluate_problem, problems))

    summary = EvaluationSummary(
        problem_count=len(results),
        completed_count=sum(1 for result in results if result.status.value == "completed"),
        failed_count=sum(1 for result in results if result.status.value == "failed"),
        passed_count=sum(1 for result in results if result.testing_outcome == "passed"),
        average_latency_seconds=(
            sum(result.latency_seconds for result in results) / len(results)
            if results
            else 0.0
        ),
    )
    artifact = EvaluationRunArtifact(
        problems=problems,
        results=results,
        summary=summary,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_payload = {
        "problems": [asdict(problem) for problem in problems],
        "results": [asdict(result) for result in results],
        "summary": asdict(summary),
    }
    output_path.write_text(json.dumps(output_payload, indent=2), encoding="utf-8")
    return artifact


def run_batch_evaluation_entrypoint(
    dataset_path: str | Path,
    output_path: str | Path,
    *,
    max_workers: int = 1,
) -> EvaluationRunArtifact:
    """Public wrapper that normalizes entrypoint paths."""
    return run_batch_evaluation(
        Path(dataset_path),
        Path(output_path),
        max_workers=max_workers,
    )


def _evaluate_problem(problem: EvaluationProblemDefinition) -> EvaluationProblemResult:
    started_at = time.perf_counter()
    solve_result = solve_problem(
        ProblemInstance(
            identifier=problem.identifier,
            prompt=problem.prompt,
            difficulty=problem.difficulty,
        )
    )
    latency_seconds = time.perf_counter() - started_at
    diagnostics = tuple(solve_result.execution.diagnostics)
    return EvaluationProblemResult(
        identifier=problem.identifier,
        status=solve_result.status,
        testing_outcome=(
            solve_result.testing_outcome.value
            if solve_result.testing_outcome is not None
            else None
        ),
        latency_seconds=latency_seconds,
        completed_turns=solve_result.solve_state.completed_turns,
        topology_steps=len(solve_result.topology.steps),
        topology_agents=sum(len(step.agents) for step in solve_result.topology.steps),
        diagnostics=diagnostics,
    )
