"""YAML transport helpers for topology plans."""

from __future__ import annotations

from typing import Any

import yaml

from agentconductor.domain.topology import TopologyPlan


class TopologyYamlError(ValueError):
    """Base class for repository-local topology YAML transport failures."""


class TopologyYamlParseError(TopologyYamlError):
    """Raised when topology YAML text cannot be parsed."""


class TopologyYamlSchemaError(TopologyYamlError):
    """Raised when parsed YAML does not match the repository transport shape."""


def load_topology_yaml_mapping(yaml_text: str) -> dict[str, Any]:
    """Parse topology YAML text into a raw repository transport mapping."""
    try:
        loaded = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        raise TopologyYamlParseError("failed to parse topology YAML text") from exc

    if not isinstance(loaded, dict):
        raise TopologyYamlSchemaError("topology YAML must decode to a mapping")

    return loaded


def dump_topology_yaml_mapping(raw_plan: dict[str, Any]) -> str:
    """Serialize one repository transport mapping into stable YAML text."""
    rendered = yaml.safe_dump(
        raw_plan,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=False,
    )
    if not rendered.endswith("\n"):
        rendered += "\n"
    return rendered


def parse_topology_plan_yaml(yaml_text: str) -> TopologyPlan:
    """Parse topology YAML text into a validated typed topology plan."""
    return TopologyPlan.from_mapping(load_topology_yaml_mapping(yaml_text))
