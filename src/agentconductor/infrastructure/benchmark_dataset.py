"""Infrastructure readers for external benchmark dataset artifacts."""

from __future__ import annotations

import json
from pathlib import Path


def read_jsonl_objects(dataset_path: Path) -> tuple[dict[str, object], ...]:
    """Load a JSONL artifact into raw object records."""
    records: list[dict[str, object]] = []
    for line_index, line in enumerate(
        dataset_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(
                f"Benchmark dataset line {line_index} must decode to an object."
            )
        records.append(payload)

    if not records:
        raise ValueError("Benchmark dataset must contain at least one object record.")
    return tuple(records)
