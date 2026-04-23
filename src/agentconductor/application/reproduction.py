"""Repository-local fidelity audit for strict paper reproduction claims."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from agentconductor.domain.reproduction import (
    ReproductionAudit,
    ReproductionChecklistItem,
    ReproductionClaim,
    ReproductionStatus,
)

_AUDIT_DATE = "2026-04-23"
_PAPER_ID = "2602.17100v1"
_PAPER_TITLE = (
    "AgentConductor: Topology Evolution for Multi-Agent Competition-Level Code Generation"
)


def build_reproduction_audit() -> ReproductionAudit:
    """Build the repository's current strict-reproduction audit."""
    checklist_items = (
        ReproductionChecklistItem(
            item_id="topology-yaml",
            title="YAML topology contract and validation",
            paper_requirement="Generate, parse, and validate layered YAML topologies before execution.",
            repository_status=ReproductionStatus.APPROXIMATE,
            repository_state=(
                "The repository has a stable YAML transport plus parse, schema, and "
                "logic validation, but the exact paper schema remains an implementation inference."
            ),
            evidence=(
                "TOP-02 completed YAML serialization and parsing around TopologyPlan.",
                "docs/Paper.md records the repository YAML field names as implementation inferences.",
            ),
            blocking_reason=(
                "The paper does not publish a fully formal YAML schema, so exact field-level fidelity cannot be proven."
            ),
            external_constraints=("paper underspecification",),
        ),
        ReproductionChecklistItem(
            item_id="runtime-loop",
            title="Multi-turn solve loop and feedback-driven revision",
            paper_requirement=(
                "Run bounded online topology generation with early stop and later-turn revision from testing feedback."
            ),
            repository_status=ReproductionStatus.APPROXIMATE,
            repository_state=(
                "The bounded solve loop, revision input contract, and early-stop path are implemented, "
                "but per-agent local memory semantics remain simplified."
            ),
            evidence=(
                "ORCH-03 wires checkpoint-backed online frozen inference into solve_problem(...).",
                "docs/Paper.md still lists local memory semantics as an open question.",
            ),
            blocking_reason=(
                "The paper's per-agent local-memory behavior is described conceptually but not fully specified for exact replay."
            ),
            external_constraints=("paper underspecification",),
        ),
        ReproductionChecklistItem(
            item_id="worker-agents",
            title="Model-backed worker agents and retriever fidelity",
            paper_requirement=(
                "Execute worker agents with model-backed roles, including E5-style retrieval and gpt-4o-mini worker execution."
            ),
            repository_status=ReproductionStatus.BLOCKED,
            repository_state=(
                "Non-testing worker roles now run through a model-backed runtime seam with per-agent runtime and model provenance, "
                "but the default adapter is still a repository-local gpt-4o-mini-compatible substitute and retrieval is not yet E5-backed."
            ),
            evidence=(
                "docs/Paper.md identifies E5 retrieval and gpt-4o-mini worker execution as paper facts.",
                "EXEC-02 routes retrieval, planning, algorithmic, coding, and debugging through RepositoryWorkerModelRuntime.",
            ),
            blocking_reason=(
                "Exact reproduction still requires the paper's retriever stack plus real provider-backed gpt-4o-mini worker execution instead of the current repository-local substitute."
            ),
            external_constraints=("missing external model and retriever runtime",),
        ),
        ReproductionChecklistItem(
            item_id="sft-stage",
            title="Paper-scale SFT on synthetic topology data",
            paper_requirement=(
                "Train the orchestrator backbone on the paper's synthetic YAML-topology corpus."
            ),
            repository_status=ReproductionStatus.BLOCKED,
            repository_state=(
                "The repository writes deterministic YAML targets and checkpoint metadata, "
                "but the default SFT path trains on a tiny repository-local synthetic dataset."
            ),
            evidence=(
                "TRAIN-02 produces YAML-target manifests and checkpoint metadata.",
                "docs/Paper.md records the paper's 4,500-sample SFT setup.",
            ),
            blocking_reason=(
                "The current SFT path is a lightweight checkpoint-producing baseline rather than paper-scale supervised fine-tuning."
            ),
            upstream_dependencies=("TRAIN-02",),
        ),
        ReproductionChecklistItem(
            item_id="rl-stage",
            title="GRPO-based RL optimization fidelity",
            paper_requirement=(
                "Run the paper's multi-turn GRPO stage over execution-derived rewards and topology-density rewards."
            ),
            repository_status=ReproductionStatus.BLOCKED,
            repository_state=(
                "The repository computes explicit reward breakdowns and writes updated checkpoint lineage, "
                "but the optimizer is a local GRPO-shaped stub."
            ),
            evidence=(
                "RL-02 writes grouped rollout artifacts, reward breakdowns, and updated checkpoint metadata.",
                "README.md states that the current optimizer does not claim paper-scale distributed training fidelity.",
            ),
            blocking_reason=(
                "The repository does not yet implement the paper's full GRPO optimizer or paper-scale distributed training setup."
            ),
            upstream_dependencies=("RL-02",),
        ),
        ReproductionChecklistItem(
            item_id="frozen-inference",
            title="Real checkpoint-backed frozen orchestrator inference",
            paper_requirement=(
                "Serve a frozen orchestrator checkpoint at inference time rather than a deterministic fallback."
            ),
            repository_status=ReproductionStatus.BLOCKED,
            repository_state=(
                "Checkpoint discovery, metadata loading, and checkpoint-owned runtime bundle loading are implemented, "
                "but the loaded runtime is still a repository-local substitute rather than benchmark-grade Qwen serving."
            ),
            evidence=(
                "ORCH-04 resolves checkpoints into a repository-local orchestrator-runtime.json bundle for frozen inference.",
                "README.md states that the current checkpoint-backed runtime is a repository-local bundle runtime rather than benchmark-grade model serving.",
            ),
            blocking_reason=(
                "Exact reproduction still requires real model weights and model-serving behavior rather than the current repository-local frozen runtime bundle."
            ),
            upstream_dependencies=("ORCH-04",),
        ),
        ReproductionChecklistItem(
            item_id="benchmark-datasets",
            title="Benchmark dataset coverage",
            paper_requirement=(
                "Evaluate on APPS, LiveCodeBench v4, CodeContests, HumanEval, and MBPP."
            ),
            repository_status=ReproductionStatus.BLOCKED,
            repository_state=(
                "Only APPS-style JSONL ingestion is wired today; the other paper datasets are still absent."
            ),
            evidence=(
                "BENCH-02 completed canonical APPS ingestion.",
                "docs/Paper.md states that LiveCodeBench v4, CodeContests, HumanEval, and MBPP loaders are still pending.",
            ),
            blocking_reason=(
                "The repository cannot yet run the full paper benchmark suite because most reported datasets are not ingested."
            ),
            upstream_dependencies=("BENCH-02",),
        ),
        ReproductionChecklistItem(
            item_id="benchmark-runtime",
            title="Benchmark-native runtime and leaderboard fidelity",
            paper_requirement=(
                "Evaluate with benchmark-faithful harnesses suitable for leaderboard comparison."
            ),
            repository_status=ReproductionStatus.BLOCKED,
            repository_state=(
                "The repository has local Python, JavaScript, and Java harnesses plus a typed vendor-native seam, "
                "but vendor-native execution is only stub-verified."
            ),
            evidence=(
                "BENCH-07 added a typed vendor-native runtime boundary with fixture-driven polling coverage.",
                "EVAL-02 artifacts are documented as benchmark-aligned rather than exact leaderboard reproductions.",
            ),
            blocking_reason=(
                "Strict leaderboard claims still require a live vendor-native runtime or benchmark-owned harness, not the current stub boundary."
            ),
            upstream_dependencies=("BENCH-07", "EVAL-02"),
            external_constraints=("external authentication and licensing",),
        ),
        ReproductionChecklistItem(
            item_id="compiled-language-coverage",
            title="Compiled-language local coverage",
            paper_requirement=(
                "Support the language mix needed by the paper's benchmark suite without host-dependent silent gaps."
            ),
            repository_status=ReproductionStatus.BLOCKED,
            repository_state=(
                "Java stdin-style local harness support exists, while C++ still depends on host-local g++ availability."
            ),
            evidence=(
                "BENCH-06 completed Java compile-then-run support and explicit C++ toolchain diagnostics.",
                "README.md states that there is no bundled fallback C++ toolchain when g++ is unavailable.",
            ),
            blocking_reason=(
                "The repository cannot yet claim stable compiled-language fidelity across hosts because C++ support is still environment-dependent."
            ),
            upstream_dependencies=("BENCH-06",),
            external_constraints=("host toolchain availability",),
        ),
    )
    blocking_gap_ids = tuple(
        item.item_id
        for item in checklist_items
        if item.repository_status is ReproductionStatus.BLOCKED
    )
    return ReproductionAudit(
        paper_id=_PAPER_ID,
        paper_title=_PAPER_TITLE,
        audited_on=_AUDIT_DATE,
        overall_claim=ReproductionClaim.APPROXIMATE,
        exact_reproduction_ready=False,
        checklist_items=checklist_items,
        blocking_gap_ids=blocking_gap_ids,
        summary_notes=(
            "The repository now reproduces the paper's control-flow shape and artifact boundaries, but not the full paper-scale model, data, and benchmark stack.",
            "Reported evaluation artifacts should therefore be treated as approximate benchmark-aligned reproductions unless every blocked checklist item is closed.",
        ),
    )


def write_reproduction_audit(output_path: Path) -> ReproductionAudit:
    """Write the current reproduction audit as JSON."""
    audit = build_reproduction_audit()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(audit), indent=2), encoding="utf-8")
    return audit


def write_reproduction_audit_entrypoint(output_path: str | Path) -> ReproductionAudit:
    """Public wrapper that normalizes the audit output path."""
    return write_reproduction_audit(Path(output_path))
