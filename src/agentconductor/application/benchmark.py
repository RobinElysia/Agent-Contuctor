"""Application services for external benchmark adapter boundaries."""

from __future__ import annotations

from pathlib import Path

from agentconductor.domain.benchmark import (
    BenchmarkAdapter,
    BenchmarkDatasetFormat,
    BenchmarkDatasetSource,
    BenchmarkEvaluationResult,
    BenchmarkExecutionSettings,
    BenchmarkProblemDefinition,
    CanonicalBenchmarkDataset,
)
from agentconductor.domain.execution import CodeCandidate
from agentconductor.domain.models import DifficultyLevel
from agentconductor.infrastructure.benchmark_dataset import read_jsonl_objects


def evaluate_candidate_with_benchmark(
    problem: BenchmarkProblemDefinition,
    candidate: CodeCandidate,
    settings: BenchmarkExecutionSettings,
    *,
    adapter: BenchmarkAdapter,
) -> BenchmarkEvaluationResult:
    """Evaluate one candidate through the configured benchmark adapter."""
    if candidate.language != settings.language:
        raise ValueError(
            "candidate language must match benchmark execution settings language"
        )
    return adapter.evaluate(problem, candidate, settings)


def load_benchmark_dataset(
    dataset_path: Path,
    *,
    source_format: BenchmarkDatasetFormat = BenchmarkDatasetFormat.APPS_JSONL,
) -> CanonicalBenchmarkDataset:
    """Load one external benchmark dataset artifact into canonical problem records."""
    if source_format is BenchmarkDatasetFormat.APPS_JSONL:
        raw_records = read_jsonl_objects(dataset_path)
        return _normalize_apps_jsonl_dataset(dataset_path, raw_records)
    raise ValueError(f"Unsupported benchmark dataset format '{source_format}'.")


def load_benchmark_dataset_entrypoint(
    dataset_path: str | Path,
    *,
    source_format: BenchmarkDatasetFormat = BenchmarkDatasetFormat.APPS_JSONL,
) -> CanonicalBenchmarkDataset:
    """Public wrapper that normalizes benchmark dataset paths."""
    return load_benchmark_dataset(
        Path(dataset_path),
        source_format=source_format,
    )


def _normalize_apps_jsonl_dataset(
    dataset_path: Path,
    raw_records: tuple[dict[str, object], ...],
) -> CanonicalBenchmarkDataset:
    problems: list[BenchmarkProblemDefinition] = []
    seen_identifiers: set[str] = set()
    for index, raw_record in enumerate(raw_records):
        source_problem_id = _require_string(
            raw_record,
            "problem_id",
            record_index=index,
        )
        prompt = _normalize_multiline_text(
            _require_string(
                raw_record,
                "question",
                record_index=index,
            )
        )
        split_name = _normalize_split_name(
            _require_string(
                raw_record,
                "split",
                record_index=index,
            ),
            record_index=index,
        )
        language = _normalize_language(raw_record.get("language"), record_index=index)
        difficulty = _normalize_apps_difficulty(
            raw_record.get("difficulty"),
            record_index=index,
        )
        identifier = f"apps/{split_name}/{source_problem_id}"
        if identifier in seen_identifiers:
            raise ValueError(
                f"Benchmark dataset produced a duplicate canonical identifier '{identifier}'."
            )
        seen_identifiers.add(identifier)
        problems.append(
            BenchmarkProblemDefinition(
                identifier=identifier,
                prompt=prompt,
                benchmark_name="apps",
                dataset_name="APPS",
                source_problem_id=source_problem_id,
                language=language,
                split_name=split_name,
                difficulty=difficulty,
            )
        )

    return CanonicalBenchmarkDataset(
        source=BenchmarkDatasetSource(
            benchmark_name="apps",
            dataset_name="APPS",
            format=BenchmarkDatasetFormat.APPS_JSONL,
            source_uri=str(dataset_path),
        ),
        problems=tuple(problems),
        normalization_notes=(
            "APPS JSONL records are normalized into canonical identifiers of the form 'apps/<split>/<problem_id>'.",
            "APPS difficulty labels are mapped into repository difficulty tiers as an inference: introductory->easy, interview->medium, competition->hard.",
            "Prompt normalization preserves content while converting CRLF or CR line endings to LF and trimming trailing whitespace at line boundaries.",
        ),
    )


def _require_string(
    record: dict[str, object],
    field_name: str,
    *,
    record_index: int,
) -> str:
    value = record.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"Benchmark dataset record {record_index} must define a non-empty string '{field_name}'."
        )
    return value.strip()


def _normalize_multiline_text(value: str) -> str:
    lines = value.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    normalized_lines = [line.rstrip(" \t") for line in lines]
    while normalized_lines and normalized_lines[-1] == "":
        normalized_lines.pop()
    normalized = "\n".join(normalized_lines).strip()
    if not normalized:
        raise ValueError("Benchmark dataset prompt normalization produced an empty prompt.")
    return normalized


def _normalize_split_name(value: str, *, record_index: int) -> str:
    normalized = value.strip().lower()
    if normalized not in {"train", "test"}:
        raise ValueError(
            f"Benchmark dataset record {record_index} has unsupported split '{value}'."
        )
    return normalized


def _normalize_language(value: object, *, record_index: int) -> str:
    if value is None:
        return "python"
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"Benchmark dataset record {record_index} must define 'language' as a non-empty string when provided."
        )
    return value.strip().lower()


def _normalize_apps_difficulty(
    value: object,
    *,
    record_index: int,
) -> DifficultyLevel | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"Benchmark dataset record {record_index} must define 'difficulty' as a non-empty string when provided."
        )
    normalized = value.strip().lower()
    difficulty_map = {
        "introductory": DifficultyLevel.EASY,
        "easy": DifficultyLevel.EASY,
        "interview": DifficultyLevel.MEDIUM,
        "medium": DifficultyLevel.MEDIUM,
        "competition": DifficultyLevel.HARD,
        "hard": DifficultyLevel.HARD,
    }
    difficulty = difficulty_map.get(normalized)
    if difficulty is None:
        raise ValueError(
            f"Benchmark dataset record {record_index} has unsupported difficulty '{value}'."
        )
    return difficulty
