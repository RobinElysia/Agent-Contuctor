import json
from pathlib import Path

from agentconductor import (
    ReproductionClaim,
    ReproductionStatus,
    build_reproduction_audit,
    write_reproduction_audit_entrypoint,
)


def test_build_reproduction_audit_reports_blocking_gaps() -> None:
    audit = build_reproduction_audit()

    assert audit.paper_id == "2602.17100v1"
    assert audit.overall_claim is ReproductionClaim.APPROXIMATE
    assert audit.exact_reproduction_ready is False
    assert "frozen-inference" in audit.blocking_gap_ids
    assert "benchmark-runtime" in audit.blocking_gap_ids
    assert any(
        item.item_id == "worker-agents"
        and item.repository_status is ReproductionStatus.BLOCKED
        for item in audit.checklist_items
    )
    assert any(
        item.item_id == "topology-yaml"
        and item.repository_status is ReproductionStatus.APPROXIMATE
        for item in audit.checklist_items
    )


def test_write_reproduction_audit_entrypoint_writes_json(tmp_path: Path) -> None:
    output_path = tmp_path / "artifacts" / "reproduction-audit.json"

    audit = write_reproduction_audit_entrypoint(output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["overall_claim"] == "approximate"
    assert payload["exact_reproduction_ready"] is False
    assert payload["blocking_gap_ids"] == list(audit.blocking_gap_ids)
    assert payload["checklist_items"][0]["item_id"] == audit.checklist_items[0].item_id
