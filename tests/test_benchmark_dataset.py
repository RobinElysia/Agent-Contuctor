from pathlib import Path

import pytest

from agentconductor import (
    BenchmarkDatasetFormat,
    BenchmarkInvocationMode,
    DifficultyLevel,
    load_benchmark_dataset,
    load_canonical_benchmark_dataset,
)


def test_load_benchmark_dataset_rejects_missing_required_apps_fields(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "invalid_apps.jsonl"
    dataset_path.write_text(
        '{"problem_id":"missing-question","split":"train"}\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="question"):
        load_benchmark_dataset(dataset_path)


def test_load_benchmark_dataset_normalizes_apps_records(tmp_path: Path) -> None:
    dataset_path = tmp_path / "apps.jsonl"
    dataset_path.write_text(
        (
            '{"problem_id":"7","question":"Solve it.\\r\\nExplain.  \\r\\n",'
            '"difficulty":"Interview","split":"TRAIN","language":"Python"}\n'
        ),
        encoding="utf-8",
    )

    dataset = load_benchmark_dataset(dataset_path)
    problem = dataset.problems[0]

    assert dataset.source.format is BenchmarkDatasetFormat.APPS_JSONL
    assert problem.identifier == "apps/train/7"
    assert problem.source_problem_id == "7"
    assert problem.split_name == "train"
    assert problem.language == "python"
    assert problem.prompt == "Solve it.\nExplain."
    assert problem.difficulty is DifficultyLevel.MEDIUM
    assert "introductory->easy" in dataset.normalization_notes[1]
    assert dataset.records[0].execution_settings.invocation_mode is BenchmarkInvocationMode.FUNCTION
    assert dataset.records[0].test_cases == ()


def test_load_canonical_benchmark_dataset_reads_fixture_path() -> None:
    fixture_path = (
        Path(__file__).parent / "fixtures" / "benchmark" / "apps_fixture.jsonl"
    )

    dataset = load_canonical_benchmark_dataset(
        str(fixture_path),
        source_format=BenchmarkDatasetFormat.APPS_JSONL,
    )

    assert len(dataset.problems) == 3
    assert dataset.problems[0].identifier == "apps/train/42"
    assert dataset.problems[0].difficulty is DifficultyLevel.EASY
    assert dataset.records[0].execution_settings.invocation_mode is BenchmarkInvocationMode.FUNCTION
    assert dataset.records[0].execution_settings.entrypoint == "solve"
    assert len(dataset.records[0].test_cases) == 2
    assert dataset.records[0].test_cases[0].arguments == (1, 2)
    assert dataset.problems[1].identifier == "apps/test/314"
    assert dataset.problems[1].difficulty is DifficultyLevel.HARD
    assert dataset.records[1].execution_settings.invocation_mode is BenchmarkInvocationMode.STDIN
    assert dataset.records[1].test_cases[0].stdin_text == "3\n1 5 2\n"
    assert dataset.records[1].test_cases[0].expected_stdout == "5\n"
    assert dataset.problems[2].identifier == "apps/test/2718"
    assert dataset.problems[2].language == "javascript"
    assert dataset.problems[2].difficulty is DifficultyLevel.MEDIUM
    assert dataset.records[2].execution_settings.invocation_mode is BenchmarkInvocationMode.FUNCTION
    assert dataset.records[2].execution_settings.entrypoint == "solve"
    assert dataset.records[2].test_cases[0].arguments == (2, 3)
