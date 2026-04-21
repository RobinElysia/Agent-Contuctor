import json
from pathlib import Path

import pytest

from agentconductor import run_batch_evaluation_entrypoint
from agentconductor.application.evaluation import load_evaluation_dataset


def test_load_evaluation_dataset_rejects_invalid_schema(tmp_path: Path) -> None:
    dataset_path = tmp_path / "invalid.json"
    dataset_path.write_text(json.dumps({"problems": [{}]}), encoding="utf-8")

    with pytest.raises(ValueError, match="identifier"):
        load_evaluation_dataset(dataset_path)


def test_run_batch_evaluation_entrypoint_writes_summary_artifact(tmp_path: Path) -> None:
    dataset_path = tmp_path / "dataset.json"
    output_path = tmp_path / "artifacts" / "results.json"
    dataset_path.write_text(
        json.dumps(
            {
                "problems": [
                    {
                        "identifier": "eval-sum",
                        "prompt": "Write a function that returns two values added together.",
                        "difficulty": "easy",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    artifact = run_batch_evaluation_entrypoint(
        dataset_path,
        output_path,
        max_workers=1,
    )

    assert artifact.summary.problem_count == 1
    assert artifact.summary.passed_count == 1
    assert artifact.results[0].identifier == "eval-sum"
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["summary"]["problem_count"] == 1
    assert payload["results"][0]["identifier"] == "eval-sum"
