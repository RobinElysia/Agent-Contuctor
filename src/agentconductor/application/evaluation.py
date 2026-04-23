"""Benchmark-aligned evaluation pipeline over frozen orchestrator inference."""

from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
import hashlib
from importlib import metadata as importlib_metadata
import json
from pathlib import Path
import time

from agentconductor.application.benchmark import (
    evaluate_candidate_with_benchmark_record,
    load_benchmark_dataset,
)
from agentconductor.domain.benchmark import (
    BenchmarkAdapter,
    BenchmarkDatasetFormat,
    BenchmarkEvaluationResult,
    BenchmarkEvaluationStatus,
    CanonicalBenchmarkDataset,
    CanonicalBenchmarkRecord,
)
from agentconductor.domain.evaluation import (
    EvaluationProblemDefinition,
    EvaluationProblemResult,
    EvaluationRunArtifact,
    EvaluationRunMetadata,
    EvaluationSummary,
)
from agentconductor.domain.execution import CodeCandidate
from agentconductor.domain.models import SolveResult
from agentconductor.infrastructure.benchmark import (
    MultiLanguageBenchmarkJudgeAdapter,
    NodeJsBenchmarkJudgeAdapter,
    PythonBenchmarkJudgeAdapter,
)
from agentconductor.infrastructure.training_checkpoint import (
    resolve_orchestrator_checkpoint_metadata,
)
from agentconductor.interfaces.api import solve_problem


def load_evaluation_dataset(
    dataset_path: Path,
    *,
    source_format: BenchmarkDatasetFormat = BenchmarkDatasetFormat.APPS_JSONL,
) -> CanonicalBenchmarkDataset:
    """Load and validate one canonical benchmark dataset for evaluation."""
    return load_benchmark_dataset(dataset_path, source_format=source_format)


def run_benchmark_evaluation(
    dataset_path: Path,
    output_path: Path,
    *,
    checkpoint_source: str | Path,
    checkpoint_id: str | None = None,
    source_format: BenchmarkDatasetFormat = BenchmarkDatasetFormat.APPS_JSONL,
    adapter: BenchmarkAdapter | None = None,
    samples_per_problem: int = 1,
    pass_k: int | None = None,
    max_workers: int = 1,
    max_turns: int = 2,
    orchestrator_device: str = "cpu",
    orchestrator_max_attempts: int = 1,
) -> EvaluationRunArtifact:
    """Run checkpoint-backed solve plus benchmark judging and write one artifact."""
    if samples_per_problem < 1:
        raise ValueError("samples_per_problem must be at least 1")
    if max_workers < 1:
        raise ValueError("max_workers must be at least 1")
    if max_turns < 1:
        raise ValueError("max_turns must be at least 1")

    dataset = load_evaluation_dataset(dataset_path, source_format=source_format)
    effective_pass_k = pass_k or samples_per_problem
    if effective_pass_k < 1:
        raise ValueError("pass_k must be at least 1 when provided")

    checkpoint_metadata = resolve_orchestrator_checkpoint_metadata(
        checkpoint_source,
        checkpoint_id=checkpoint_id,
    )
    active_adapter = adapter or _build_default_benchmark_adapter(output_path=output_path)
    evaluation_problems = tuple(
        EvaluationProblemDefinition(
            identifier=record.problem.identifier,
            prompt=record.problem.prompt,
            benchmark_name=record.problem.benchmark_name,
            dataset_name=record.problem.dataset_name,
            source_problem_id=record.problem.source_problem_id,
            language=record.problem.language,
            split_name=record.problem.split_name,
            difficulty=record.problem.difficulty,
        )
        for record in dataset.records
    )

    work_items = tuple(
        (record, attempt_index)
        for record in dataset.records
        for attempt_index in range(samples_per_problem)
    )
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = tuple(
            executor.map(
                lambda item: _evaluate_problem_attempt(
                    item[0],
                    attempt_index=item[1],
                    checkpoint_metadata=checkpoint_metadata,
                    adapter=active_adapter,
                    max_turns=max_turns,
                    orchestrator_device=orchestrator_device,
                    orchestrator_max_attempts=orchestrator_max_attempts,
                ),
                work_items,
            )
        )

    summary = _summarize_results(
        results=results,
        problem_count=len(dataset.records),
        pass_k=effective_pass_k,
    )
    artifact = EvaluationRunArtifact(
        metadata=_build_run_metadata(
            dataset=dataset,
            adapter=active_adapter,
            checkpoint_metadata=checkpoint_metadata,
            samples_per_problem=samples_per_problem,
            max_turns=max_turns,
            orchestrator_device=orchestrator_device,
            notes=_build_evaluation_notes(adapter=active_adapter),
        ),
        problems=evaluation_problems,
        results=results,
        summary=summary,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "metadata": asdict(artifact.metadata),
                "problems": [asdict(problem) for problem in artifact.problems],
                "results": [asdict(result) for result in artifact.results],
                "summary": asdict(artifact.summary),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return artifact


def run_benchmark_evaluation_entrypoint(
    dataset_path: str | Path,
    output_path: str | Path,
    *,
    checkpoint_source: str | Path,
    checkpoint_id: str | None = None,
    source_format: BenchmarkDatasetFormat = BenchmarkDatasetFormat.APPS_JSONL,
    samples_per_problem: int = 1,
    pass_k: int | None = None,
    max_workers: int = 1,
    max_turns: int = 2,
    orchestrator_device: str = "cpu",
    orchestrator_max_attempts: int = 1,
) -> EvaluationRunArtifact:
    """Public wrapper for benchmark-aligned evaluation."""
    return run_benchmark_evaluation(
        Path(dataset_path),
        Path(output_path),
        checkpoint_source=checkpoint_source,
        checkpoint_id=checkpoint_id,
        source_format=source_format,
        samples_per_problem=samples_per_problem,
        pass_k=pass_k,
        max_workers=max_workers,
        max_turns=max_turns,
        orchestrator_device=orchestrator_device,
        orchestrator_max_attempts=orchestrator_max_attempts,
    )


def run_batch_evaluation(
    dataset_path: Path,
    output_path: Path,
    *,
    checkpoint_source: str | Path,
    checkpoint_id: str | None = None,
    source_format: BenchmarkDatasetFormat = BenchmarkDatasetFormat.APPS_JSONL,
    samples_per_problem: int = 1,
    pass_k: int | None = None,
    max_workers: int = 1,
    max_turns: int = 2,
    orchestrator_device: str = "cpu",
    orchestrator_max_attempts: int = 1,
) -> EvaluationRunArtifact:
    """Compatibility alias for the benchmark-aligned evaluation pipeline."""
    return run_benchmark_evaluation(
        dataset_path,
        output_path,
        checkpoint_source=checkpoint_source,
        checkpoint_id=checkpoint_id,
        source_format=source_format,
        samples_per_problem=samples_per_problem,
        pass_k=pass_k,
        max_workers=max_workers,
        max_turns=max_turns,
        orchestrator_device=orchestrator_device,
        orchestrator_max_attempts=orchestrator_max_attempts,
    )


def run_batch_evaluation_entrypoint(
    dataset_path: str | Path,
    output_path: str | Path,
    *,
    checkpoint_source: str | Path,
    checkpoint_id: str | None = None,
    source_format: BenchmarkDatasetFormat = BenchmarkDatasetFormat.APPS_JSONL,
    samples_per_problem: int = 1,
    pass_k: int | None = None,
    max_workers: int = 1,
    max_turns: int = 2,
    orchestrator_device: str = "cpu",
    orchestrator_max_attempts: int = 1,
) -> EvaluationRunArtifact:
    """Compatibility alias for the benchmark-aligned evaluation entrypoint."""
    return run_benchmark_evaluation_entrypoint(
        dataset_path,
        output_path,
        checkpoint_source=checkpoint_source,
        checkpoint_id=checkpoint_id,
        source_format=source_format,
        samples_per_problem=samples_per_problem,
        pass_k=pass_k,
        max_workers=max_workers,
        max_turns=max_turns,
        orchestrator_device=orchestrator_device,
        orchestrator_max_attempts=orchestrator_max_attempts,
    )


def _evaluate_problem_attempt(
    record: CanonicalBenchmarkRecord,
    *,
    attempt_index: int,
    checkpoint_metadata,
    adapter: BenchmarkAdapter,
    max_turns: int,
    orchestrator_device: str,
    orchestrator_max_attempts: int,
) -> EvaluationProblemResult:
    started_at = time.perf_counter()
    solve_result = solve_problem(
        record.problem.to_problem_instance(),
        max_turns=max_turns,
        orchestrator_checkpoint=checkpoint_metadata.metadata_path,
        orchestrator_checkpoint_id=checkpoint_metadata.checkpoint_id,
        orchestrator_device=orchestrator_device,
        orchestrator_max_attempts=orchestrator_max_attempts,
    )
    latency_seconds = time.perf_counter() - started_at
    candidate = _extract_candidate_from_solve_result(solve_result)
    benchmark_result = (
        _build_missing_candidate_result(record=record, adapter=adapter)
        if candidate is None
        else evaluate_candidate_with_benchmark_record(
            record,
            candidate,
            adapter=adapter,
        )
    )

    return EvaluationProblemResult(
        identifier=record.problem.identifier,
        source_problem_id=record.problem.source_problem_id,
        attempt_index=attempt_index,
        solve_status=solve_result.status,
        benchmark_status=benchmark_result.status,
        solve_testing_outcome=(
            solve_result.testing_outcome.value
            if solve_result.testing_outcome is not None
            else None
        ),
        benchmark_testing_outcome=(
            benchmark_result.testing_outcome.value
            if benchmark_result.testing_outcome is not None
            else None
        ),
        benchmark_native_verdict=(
            benchmark_result.verdict_mapping.native_verdict
            if benchmark_result.verdict_mapping is not None
            else None
        ),
        latency_seconds=latency_seconds,
        completed_turns=solve_result.solve_state.completed_turns,
        topology_steps=len(solve_result.topology.steps),
        topology_agents=sum(len(step.agents) for step in solve_result.topology.steps),
        candidate_language=None if candidate is None else candidate.language,
        checkpoint_id=checkpoint_metadata.checkpoint_id,
        benchmark_run_id=(
            None
            if benchmark_result.artifact_identifiers is None
            else benchmark_result.artifact_identifiers.run_id
        ),
        result_artifact_uri=(
            None
            if benchmark_result.artifact_identifiers is None
            else benchmark_result.artifact_identifiers.result_artifact_uri
        ),
        log_artifact_uri=(
            None
            if benchmark_result.artifact_identifiers is None
            else benchmark_result.artifact_identifiers.log_artifact_uri
        ),
        diagnostics=tuple(solve_result.execution.diagnostics) + tuple(benchmark_result.diagnostics),
    )


def _build_missing_candidate_result(
    *,
    record: CanonicalBenchmarkRecord,
    adapter: BenchmarkAdapter,
) -> BenchmarkEvaluationResult:
    return BenchmarkEvaluationResult(
        adapter_name=_adapter_name(adapter),
        status=BenchmarkEvaluationStatus.ADAPTER_ERROR,
        problem=record.problem,
        diagnostics=(
            "Solve completed without a final candidate, so benchmark evaluation could not run.",
        ),
    )


def _extract_candidate_from_solve_result(solve_result: SolveResult) -> CodeCandidate | None:
    for step_result in reversed(solve_result.execution.step_results):
        for agent_result in reversed(step_result.agent_results):
            if not agent_result.candidate_code:
                continue
            source_code = agent_result.candidate_code.strip()
            if not source_code:
                continue
            return CodeCandidate(
                step_index=agent_result.step_index,
                agent_name=agent_result.agent_name,
                role=agent_result.role,
                source_code=source_code,
                language="python",
            )
    return None


def _summarize_results(
    *,
    results: tuple[EvaluationProblemResult, ...],
    problem_count: int,
    pass_k: int,
) -> EvaluationSummary:
    grouped_results: dict[str, list[EvaluationProblemResult]] = defaultdict(list)
    for result in results:
        grouped_results[result.identifier].append(result)
    ordered_groups = {
        identifier: tuple(sorted(group, key=lambda item: item.attempt_index))
        for identifier, group in grouped_results.items()
    }
    effective_pass_k = max(1, pass_k)
    pass_at_1 = (
        sum(
            1
            for group in ordered_groups.values()
            if group
            and group[0].benchmark_testing_outcome == "passed"
        )
        / problem_count
        if problem_count
        else 0.0
    )
    pass_at_k = (
        sum(
            1
            for group in ordered_groups.values()
            if any(
                result.benchmark_testing_outcome == "passed"
                for result in group[:effective_pass_k]
            )
        )
        / problem_count
        if problem_count
        else 0.0
    )
    return EvaluationSummary(
        problem_count=problem_count,
        attempt_count=len(results),
        completed_count=sum(1 for result in results if result.solve_status.value == "completed"),
        benchmark_completed_count=sum(
            1
            for result in results
            if result.benchmark_status is BenchmarkEvaluationStatus.COMPLETED
        ),
        adapter_error_count=sum(
            1
            for result in results
            if result.benchmark_status is BenchmarkEvaluationStatus.ADAPTER_ERROR
        ),
        passed_count=sum(
            1 for result in results if result.benchmark_testing_outcome == "passed"
        ),
        pass_at_1=pass_at_1,
        pass_at_k=pass_at_k,
        pass_k=effective_pass_k,
        average_latency_seconds=(
            sum(result.latency_seconds for result in results) / len(results)
            if results
            else 0.0
        ),
    )


def _build_run_metadata(
    *,
    dataset: CanonicalBenchmarkDataset,
    adapter: BenchmarkAdapter,
    checkpoint_metadata,
    samples_per_problem: int,
    max_turns: int,
    orchestrator_device: str,
    notes: tuple[str, ...],
) -> EvaluationRunMetadata:
    problem_splits = {
        record.problem.split_name for record in dataset.records if record.problem.split_name is not None
    }
    split_name = next(iter(problem_splits)) if len(problem_splits) == 1 else None
    return EvaluationRunMetadata(
        benchmark_name=dataset.source.benchmark_name,
        dataset_name=dataset.source.dataset_name,
        dataset_version=_compute_dataset_version(dataset.source.source_uri),
        dataset_source_uri=dataset.source.source_uri,
        harness_name=_adapter_name(adapter),
        harness_version=_build_harness_version(adapter),
        runtime_mode=_infer_runtime_mode(adapter),
        checkpoint_id=checkpoint_metadata.checkpoint_id,
        checkpoint_path=checkpoint_metadata.checkpoint_path,
        checkpoint_training_stage=checkpoint_metadata.training_stage,
        split_name=split_name,
        samples_per_problem=samples_per_problem,
        max_turns=max_turns,
        orchestrator_device=orchestrator_device,
        notes=notes,
    )


def _build_default_benchmark_adapter(*, output_path: Path) -> BenchmarkAdapter:
    artifact_root = output_path.parent / f"{output_path.stem}-benchmark-artifacts"
    return MultiLanguageBenchmarkJudgeAdapter(
        python_adapter=PythonBenchmarkJudgeAdapter(artifact_root=artifact_root),
        nodejs_adapter=NodeJsBenchmarkJudgeAdapter(artifact_root=artifact_root),
    )


def _compute_dataset_version(source_uri: str) -> str:
    source_path = Path(source_uri)
    digest = hashlib.sha256(source_path.read_bytes()).hexdigest()[:12]
    return f"sha256:{digest}"


def _build_harness_version(adapter: BenchmarkAdapter) -> str:
    try:
        package_version = importlib_metadata.version("agentconductor")
    except importlib_metadata.PackageNotFoundError:
        package_version = "0.1.0"
    return f"agentconductor-eval@{package_version}:{_adapter_name(adapter)}"


def _infer_runtime_mode(adapter: BenchmarkAdapter) -> str:
    adapter_name = _adapter_name(adapter)
    if "stub" in adapter_name:
        return "vendor_stub"
    return "local_harness"


def _build_evaluation_notes(*, adapter: BenchmarkAdapter) -> tuple[str, ...]:
    runtime_mode = _infer_runtime_mode(adapter)
    notes = [
        "Aggregate metrics are computed from structured per-attempt artifacts rather than ad hoc logs.",
        "Reported pass@k is repository-observed best-of-k over repeated solve attempts, not an unbiased estimator from independent stochastic sampling.",
    ]
    if runtime_mode != "vendor_stub":
        notes.append(
            "This evaluation run is benchmark-aligned through the canonical dataset plus local benchmark harness adapters; BENCH-07 vendor-native runtime fidelity is still pending."
        )
    return tuple(notes)


def _adapter_name(adapter: BenchmarkAdapter) -> str:
    return getattr(adapter, "_adapter_name", adapter.__class__.__name__)
