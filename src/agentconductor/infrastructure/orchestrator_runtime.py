"""Repository-local frozen orchestrator runtime helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from agentconductor.domain.orchestration import (
    OrchestratorCheckpointLoadError,
    OrchestratorPromptRequest,
    TopologyPromptKind,
)
from agentconductor.domain.training import OrchestratorCheckpointMetadata


@dataclass(frozen=True, slots=True)
class RepositoryFrozenOrchestratorBundle:
    """Loadable repository-local frozen runtime bundle."""

    runtime_kind: str
    backbone_name: str
    tokenizer_name: str
    prompt_template_version: str
    supported_devices: tuple[str, ...]
    initial_candidates: dict[str, str]
    revision_candidates: dict[str, str]


class RepositoryFrozenOrchestratorRuntime:
    """Checkpoint-backed topology generator using a serialized local bundle."""

    def __init__(
        self,
        bundle: RepositoryFrozenOrchestratorBundle,
        *,
        device: str,
    ) -> None:
        if device not in bundle.supported_devices:
            raise OrchestratorCheckpointLoadError(
                "checkpoint runtime does not support device "
                f"'{device}'; expected one of {sorted(bundle.supported_devices)}"
            )
        self.bundle = bundle
        self.device = device

    def generate(self, request: OrchestratorPromptRequest) -> str:
        difficulty = request.selected_difficulty.value
        if request.kind is TopologyPromptKind.INITIAL:
            candidate = self.bundle.initial_candidates.get(difficulty)
        else:
            candidate = self.bundle.revision_candidates.get(difficulty)
        if candidate is None:
            raise OrchestratorCheckpointLoadError(
                "checkpoint runtime bundle does not define a topology candidate for "
                f"{request.kind.value} difficulty '{difficulty}'"
            )
        return candidate


def load_repository_frozen_orchestrator_runtime(
    metadata: OrchestratorCheckpointMetadata,
    *,
    device: str,
) -> RepositoryFrozenOrchestratorRuntime:
    """Load one repository-local frozen orchestrator runtime from checkpoint metadata."""
    runtime_artifact_path = metadata.runtime_artifact_path
    if not runtime_artifact_path:
        raise OrchestratorCheckpointLoadError(
            "checkpoint metadata must define runtime_artifact_path for frozen inference"
        )
    runtime_path = Path(runtime_artifact_path)
    if not runtime_path.exists():
        raise OrchestratorCheckpointLoadError(
            f"checkpoint runtime artifact is missing: {runtime_path}"
        )

    payload = json.loads(runtime_path.read_text(encoding="utf-8"))
    bundle = _parse_runtime_bundle(payload=payload, metadata=metadata)
    return RepositoryFrozenOrchestratorRuntime(bundle, device=device)


def _parse_runtime_bundle(
    *,
    payload: object,
    metadata: OrchestratorCheckpointMetadata,
) -> RepositoryFrozenOrchestratorBundle:
    if not isinstance(payload, dict):
        raise OrchestratorCheckpointLoadError(
            "checkpoint runtime artifact must contain a JSON object"
        )
    required_keys = {
        "runtime_kind",
        "backbone_name",
        "tokenizer_name",
        "prompt_template_version",
        "supported_devices",
        "initial_candidates",
        "revision_candidates",
    }
    if not required_keys.issubset(payload):
        raise OrchestratorCheckpointLoadError(
            "checkpoint runtime artifact must define "
            f"{sorted(required_keys)}"
        )
    if payload["prompt_template_version"] != metadata.prompt_template_version:
        raise OrchestratorCheckpointLoadError(
            "checkpoint runtime artifact prompt template version "
            f"'{payload['prompt_template_version']}' does not match checkpoint "
            f"metadata '{metadata.prompt_template_version}'"
        )
    if payload["backbone_name"] != metadata.backbone_name:
        raise OrchestratorCheckpointLoadError(
            "checkpoint runtime artifact backbone "
            f"'{payload['backbone_name']}' does not match checkpoint metadata "
            f"'{metadata.backbone_name}'"
        )
    supported_devices = payload["supported_devices"]
    if not isinstance(supported_devices, list) or not all(
        isinstance(item, str) and item.strip() for item in supported_devices
    ):
        raise OrchestratorCheckpointLoadError(
            "checkpoint runtime artifact supported_devices must be a non-empty string list"
        )
    return RepositoryFrozenOrchestratorBundle(
        runtime_kind=str(payload["runtime_kind"]),
        backbone_name=str(payload["backbone_name"]),
        tokenizer_name=str(payload["tokenizer_name"]),
        prompt_template_version=str(payload["prompt_template_version"]),
        supported_devices=tuple(item.strip() for item in supported_devices),
        initial_candidates=_parse_candidate_map(
            payload["initial_candidates"],
            field_name="initial_candidates",
        ),
        revision_candidates=_parse_candidate_map(
            payload["revision_candidates"],
            field_name="revision_candidates",
        ),
    )


def _parse_candidate_map(
    payload: object,
    *,
    field_name: str,
) -> dict[str, str]:
    if not isinstance(payload, dict):
        raise OrchestratorCheckpointLoadError(
            f"checkpoint runtime artifact field '{field_name}' must be an object"
        )
    parsed: dict[str, str] = {}
    for key, value in payload.items():
        if not isinstance(key, str) or not isinstance(value, str) or not value.strip():
            raise OrchestratorCheckpointLoadError(
                f"checkpoint runtime artifact field '{field_name}' must map strings to YAML text"
            )
        parsed[key] = value
    return parsed
