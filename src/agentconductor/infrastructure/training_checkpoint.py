"""Checkpoint metadata helpers for repository-local SFT artifacts."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from agentconductor.domain.orchestration import (
    OrchestratorCheckpointLoadError,
    OrchestratorCheckpointSelectionError,
)
from agentconductor.domain.training import OrchestratorCheckpointMetadata


def write_orchestrator_checkpoint_metadata(
    checkpoint_dir: Path,
    metadata: OrchestratorCheckpointMetadata,
) -> Path:
    """Write one loadable checkpoint metadata file under a checkpoint directory."""
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = checkpoint_dir / "checkpoint.json"
    metadata_path.write_text(json.dumps(asdict(metadata), indent=2), encoding="utf-8")
    return metadata_path


def load_orchestrator_checkpoint_metadata(
    checkpoint_path: str | Path,
) -> OrchestratorCheckpointMetadata:
    """Load checkpoint metadata from a checkpoint directory or metadata file."""
    raw_path = Path(checkpoint_path)
    metadata_path = raw_path / "checkpoint.json" if raw_path.is_dir() else raw_path
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    return _parse_checkpoint_metadata_payload(payload)


def resolve_orchestrator_checkpoint_metadata(
    checkpoint_source: str | Path,
    *,
    checkpoint_id: str | None = None,
) -> OrchestratorCheckpointMetadata:
    """Resolve one checkpoint metadata record from a source path."""
    source_path = Path(checkpoint_source)
    if not source_path.exists():
        raise OrchestratorCheckpointSelectionError(
            f"checkpoint source does not exist: {source_path}"
        )

    if source_path.is_dir():
        direct_metadata_path = source_path / "checkpoint.json"
        if direct_metadata_path.exists():
            metadata = load_orchestrator_checkpoint_metadata(direct_metadata_path)
            _validate_checkpoint_id(metadata=metadata, checkpoint_id=checkpoint_id)
            return metadata
        return _resolve_checkpoint_from_directory(
            source_path,
            checkpoint_id=checkpoint_id,
        )

    payload = json.loads(source_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise OrchestratorCheckpointLoadError(
            "checkpoint source file must contain a JSON object"
        )

    if _is_checkpoint_metadata_payload(payload):
        metadata = _parse_checkpoint_metadata_payload(payload)
        _validate_checkpoint_id(metadata=metadata, checkpoint_id=checkpoint_id)
        return metadata

    if {"checkpoint_path", "checkpoint_id"}.issubset(payload):
        resolved_checkpoint_id = checkpoint_id or payload["checkpoint_id"]
        return resolve_orchestrator_checkpoint_metadata(
            payload["checkpoint_path"],
            checkpoint_id=resolved_checkpoint_id,
        )

    raise OrchestratorCheckpointLoadError(
        "checkpoint source file must be checkpoint metadata or a training artifact "
        "that defines checkpoint_path and checkpoint_id"
    )


def _resolve_checkpoint_from_directory(
    checkpoint_root: Path,
    *,
    checkpoint_id: str | None,
) -> OrchestratorCheckpointMetadata:
    candidate_files = sorted(
        metadata_path
        for metadata_path in checkpoint_root.glob("*-checkpoint/checkpoint.json")
        if metadata_path.is_file()
    )
    if not candidate_files:
        raise OrchestratorCheckpointSelectionError(
            "checkpoint source directory must be a checkpoint directory or contain "
            "at least one '*-checkpoint/checkpoint.json' child"
        )

    candidates = tuple(
        load_orchestrator_checkpoint_metadata(metadata_path)
        for metadata_path in candidate_files
    )
    if checkpoint_id is not None:
        for metadata in candidates:
            if metadata.checkpoint_id == checkpoint_id:
                return metadata
        raise OrchestratorCheckpointSelectionError(
            f"checkpoint source directory does not contain checkpoint_id '{checkpoint_id}'"
        )
    if len(candidates) > 1:
        raise OrchestratorCheckpointSelectionError(
            "checkpoint source directory contains multiple checkpoint candidates; "
            "set checkpoint_id explicitly"
        )
    return candidates[0]


def _validate_checkpoint_id(
    *,
    metadata: OrchestratorCheckpointMetadata,
    checkpoint_id: str | None,
) -> None:
    if checkpoint_id is not None and metadata.checkpoint_id != checkpoint_id:
        raise OrchestratorCheckpointSelectionError(
            "resolved checkpoint id "
            f"'{metadata.checkpoint_id}' does not match requested '{checkpoint_id}'"
        )


def _is_checkpoint_metadata_payload(payload: dict[str, object]) -> bool:
    return _required_checkpoint_keys().issubset(payload)


def _parse_checkpoint_metadata_payload(
    payload: object,
) -> OrchestratorCheckpointMetadata:
    if not isinstance(payload, dict):
        raise OrchestratorCheckpointLoadError("checkpoint metadata must be a JSON object")
    required_keys = _required_checkpoint_keys()
    if not required_keys.issubset(payload):
        raise OrchestratorCheckpointLoadError(
            "checkpoint metadata must define "
            f"{sorted(required_keys)}"
        )
    return OrchestratorCheckpointMetadata(
        checkpoint_id=payload["checkpoint_id"],
        checkpoint_path=payload["checkpoint_path"],
        metadata_path=payload["metadata_path"],
        dataset_path=payload["dataset_path"],
        training_manifest_path=payload["training_manifest_path"],
        sample_count=payload["sample_count"],
        target_format=payload["target_format"],
        backbone_name=payload["backbone_name"],
        tokenizer_name=payload["tokenizer_name"],
        prompt_template_version=payload["prompt_template_version"],
        epochs=payload["epochs"],
        learning_rate=payload["learning_rate"],
        seed=payload["seed"],
        training_stage=payload.get("training_stage", "sft"),
        parent_checkpoint_id=payload.get("parent_checkpoint_id"),
        optimizer_name=payload.get("optimizer_name"),
        optimizer_steps=payload.get("optimizer_steps", 0),
        average_reward=payload.get("average_reward"),
    )


def _required_checkpoint_keys() -> set[str]:
    return {
        "checkpoint_id",
        "checkpoint_path",
        "metadata_path",
        "dataset_path",
        "training_manifest_path",
        "sample_count",
        "target_format",
        "backbone_name",
        "tokenizer_name",
        "prompt_template_version",
        "epochs",
        "learning_rate",
        "seed",
    }
