"""Application services for external benchmark adapter boundaries."""

from __future__ import annotations

import json
from pathlib import Path

from agentconductor.domain.benchmark import (
    BenchmarkAdapter,
    BenchmarkDatasetFormat,
    BenchmarkDatasetSource,
    BenchmarkEvaluationResult,
    BenchmarkExecutionSettings,
    BenchmarkInvocationMode,
    BenchmarkProblemDefinition,
    BenchmarkTestCase,
    CanonicalBenchmarkDataset,
    CanonicalBenchmarkRecord,
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


def evaluate_candidate_with_benchmark_record(
    record: CanonicalBenchmarkRecord,
    candidate: CodeCandidate,
    *,
    adapter: BenchmarkAdapter,
) -> BenchmarkEvaluationResult:
    """Evaluate one candidate against a canonical benchmark dataset record."""
    if candidate.language != record.execution_settings.language:
        raise ValueError(
            "candidate language must match benchmark execution settings language"
        )
    return adapter.evaluate(
        record.problem,
        candidate,
        record.execution_settings,
        record.test_cases,
    )


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
    records: list[CanonicalBenchmarkRecord] = []
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
        execution_settings, test_cases, record_notes = _normalize_apps_harness(
            raw_record,
            language=language,
            record_index=index,
        )
        records.append(
            CanonicalBenchmarkRecord(
                problem=BenchmarkProblemDefinition(
                    identifier=identifier,
                    prompt=prompt,
                    benchmark_name="apps",
                    dataset_name="APPS",
                    source_problem_id=source_problem_id,
                    language=language,
                    split_name=split_name,
                    difficulty=difficulty,
                ),
                execution_settings=execution_settings,
                test_cases=test_cases,
                normalization_notes=record_notes,
            )
        )

    return CanonicalBenchmarkDataset(
        source=BenchmarkDatasetSource(
            benchmark_name="apps",
            dataset_name="APPS",
            format=BenchmarkDatasetFormat.APPS_JSONL,
            source_uri=str(dataset_path),
        ),
        records=tuple(records),
        normalization_notes=(
            "APPS JSONL records are normalized into canonical identifiers of the form 'apps/<split>/<problem_id>'.",
            "APPS difficulty labels are mapped into repository difficulty tiers as an inference: introductory->easy, interview->medium, competition->hard.",
            "Prompt normalization preserves content while converting CRLF or CR line endings to LF and trimming trailing whitespace at line boundaries.",
            "When APPS input_output metadata is present, the repository infers function invocation from 'fn_name' and otherwise falls back to stdin-style invocation.",
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


def _normalize_apps_harness(
    record: dict[str, object],
    *,
    language: str,
    record_index: int,
) -> tuple[BenchmarkExecutionSettings, tuple[BenchmarkTestCase, ...], tuple[str, ...]]:
    input_output = record.get("input_output")
    if input_output is None:
        return (
            BenchmarkExecutionSettings(language=language),
            (),
            ("No benchmark execution payload was present in the source row.",),
        )

    if isinstance(input_output, str):
        try:
            payload = json.loads(input_output)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Benchmark dataset record {record_index} has invalid JSON in 'input_output'."
            ) from exc
    elif isinstance(input_output, dict):
        payload = input_output
    else:
        raise ValueError(
            f"Benchmark dataset record {record_index} must encode 'input_output' as an object or JSON string."
        )

    inputs = payload.get("inputs")
    outputs = payload.get("outputs")
    if not isinstance(inputs, list) or not inputs:
        raise ValueError(
            f"Benchmark dataset record {record_index} must provide a non-empty 'inputs' list in 'input_output'."
        )
    if not isinstance(outputs, list) or len(outputs) != len(inputs):
        raise ValueError(
            f"Benchmark dataset record {record_index} must provide an 'outputs' list with the same length as 'inputs'."
        )

    fn_name = payload.get("fn_name")
    if fn_name is not None:
        if not isinstance(fn_name, str) or not fn_name.strip():
            raise ValueError(
                f"Benchmark dataset record {record_index} must define 'fn_name' as a non-empty string when provided."
            )
        test_cases = tuple(
            _build_function_case(
                raw_input=raw_input,
                raw_output=raw_output,
                index=index,
                record_index=record_index,
            )
            for index, (raw_input, raw_output) in enumerate(zip(inputs, outputs))
        )
        return (
            BenchmarkExecutionSettings(
                language=language,
                invocation_mode=BenchmarkInvocationMode.FUNCTION,
                entrypoint=fn_name.strip(),
            ),
            test_cases,
            (
                "Execution payload was normalized as function invocation from APPS 'fn_name'.",
            ),
        )

    test_cases = tuple(
        _build_stdin_case(
            raw_input=raw_input,
            raw_output=raw_output,
            index=index,
            record_index=record_index,
        )
        for index, (raw_input, raw_output) in enumerate(zip(inputs, outputs))
    )
    return (
        BenchmarkExecutionSettings(
            language=language,
            invocation_mode=BenchmarkInvocationMode.STDIN,
            entrypoint=None,
        ),
        test_cases,
        (
            "Execution payload was normalized as stdin invocation because APPS 'fn_name' was absent.",
        ),
    )


def _build_function_case(
    *,
    raw_input: object,
    raw_output: object,
    index: int,
    record_index: int,
) -> BenchmarkTestCase:
    normalized_input = _normalize_apps_function_value(
        raw_input,
        record_index=record_index,
        field_name="inputs",
        case_index=index,
    )
    arguments = normalized_input if isinstance(normalized_input, tuple) else (normalized_input,)
    expected_output = _normalize_apps_function_value(
        raw_output,
        record_index=record_index,
        field_name="outputs",
        case_index=index,
    )
    return BenchmarkTestCase(
        name=f"case-{index}",
        arguments=arguments,
        expected_output=expected_output,
    )


def _build_stdin_case(
    *,
    raw_input: object,
    raw_output: object,
    index: int,
    record_index: int,
) -> BenchmarkTestCase:
    stdin_text = _normalize_apps_text_value(
        raw_input,
        record_index=record_index,
        field_name="inputs",
        case_index=index,
    )
    expected_stdout = _normalize_apps_text_value(
        raw_output,
        record_index=record_index,
        field_name="outputs",
        case_index=index,
    )
    return BenchmarkTestCase(
        name=f"case-{index}",
        stdin_text=stdin_text,
        expected_stdout=expected_stdout,
    )


def _normalize_apps_function_value(
    value: object,
    *,
    record_index: int,
    field_name: str,
    case_index: int,
) -> object:
    if isinstance(value, str):
        stripped = value.strip()
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return stripped
        if isinstance(parsed, list):
            return tuple(parsed)
        return parsed
    if isinstance(value, list):
        return tuple(value)
    if value is None:
        raise ValueError(
            f"Benchmark dataset record {record_index} has null in '{field_name}' for case {case_index}."
        )
    return value


def _normalize_apps_text_value(
    value: object,
    *,
    record_index: int,
    field_name: str,
    case_index: int,
) -> str:
    if not isinstance(value, str):
        raise ValueError(
            f"Benchmark dataset record {record_index} must encode '{field_name}' case {case_index} as a string for stdin-style execution."
        )
    return value
