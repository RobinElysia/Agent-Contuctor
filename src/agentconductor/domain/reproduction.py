"""Typed fidelity-audit contracts for strict paper reproduction claims."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ReproductionStatus(StrEnum):
    """Repository status of one paper-facing fidelity item."""

    EXACT = "exact"
    APPROXIMATE = "approximate"
    BLOCKED = "blocked"


class ReproductionClaim(StrEnum):
    """Overall claim the repository can currently support."""

    EXACT = "exact"
    APPROXIMATE = "approximate"


@dataclass(frozen=True, slots=True)
class ReproductionChecklistItem:
    """One line item in the paper-to-repository fidelity checklist."""

    item_id: str
    title: str
    paper_requirement: str
    repository_status: ReproductionStatus
    repository_state: str
    evidence: tuple[str, ...]
    blocking_reason: str | None = None
    upstream_dependencies: tuple[str, ...] = ()
    external_constraints: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ReproductionAudit:
    """Structured audit of strict paper-reproduction readiness."""

    paper_id: str
    paper_title: str
    audited_on: str
    overall_claim: ReproductionClaim
    exact_reproduction_ready: bool
    checklist_items: tuple[ReproductionChecklistItem, ...]
    blocking_gap_ids: tuple[str, ...]
    summary_notes: tuple[str, ...] = ()
