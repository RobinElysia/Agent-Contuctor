import pytest

from agentconductor.domain.topology import TopologyLogicError, TopologySchemaError
from agentconductor.infrastructure.topology_yaml import (
    TopologyYamlParseError,
    TopologyYamlSchemaError,
    dump_topology_yaml_mapping,
    load_topology_yaml_mapping,
    parse_topology_plan_yaml,
)


def test_dump_topology_yaml_mapping_renders_stable_yaml_text() -> None:
    raw_plan = {
        "difficulty": "easy",
        "steps": [
            {
                "index": 0,
                "agents": [
                    {"name": "planner_0", "role": "planning", "refs": []},
                ],
            },
            {
                "index": 1,
                "agents": [
                    {
                        "name": "tester_1",
                        "role": "testing",
                        "refs": [{"step_index": 0, "agent_name": "planner_0"}],
                    }
                ],
            },
        ],
    }

    assert dump_topology_yaml_mapping(raw_plan) == (
        "difficulty: easy\n"
        "steps:\n"
        "- index: 0\n"
        "  agents:\n"
        "  - name: planner_0\n"
        "    role: planning\n"
        "    refs: []\n"
        "- index: 1\n"
        "  agents:\n"
        "  - name: tester_1\n"
        "    role: testing\n"
        "    refs:\n"
        "    - step_index: 0\n"
        "      agent_name: planner_0\n"
    )


def test_load_topology_yaml_mapping_parses_valid_yaml_mapping() -> None:
    yaml_text = """
difficulty: medium
steps:
  - index: 0
    agents:
      - name: planner_0
        role: planning
        refs: []
"""

    assert load_topology_yaml_mapping(yaml_text) == {
        "difficulty": "medium",
        "steps": [
            {
                "index": 0,
                "agents": [
                    {"name": "planner_0", "role": "planning", "refs": []},
                ],
            }
        ],
    }


def test_load_topology_yaml_mapping_rejects_malformed_yaml_text() -> None:
    with pytest.raises(
        TopologyYamlParseError,
        match="failed to parse topology YAML text",
    ):
        load_topology_yaml_mapping("difficulty: [easy")


def test_load_topology_yaml_mapping_rejects_non_mapping_top_level_yaml() -> None:
    with pytest.raises(
        TopologyYamlSchemaError,
        match="topology YAML must decode to a mapping",
    ):
        load_topology_yaml_mapping("- difficulty: easy")


def test_parse_topology_plan_yaml_returns_valid_typed_topology() -> None:
    plan = parse_topology_plan_yaml(
        """
difficulty: easy
steps:
  - index: 0
    agents:
      - name: planner_0
        role: planning
        refs: []
  - index: 1
    agents:
      - name: tester_1
        role: testing
        refs:
          - step_index: 0
            agent_name: planner_0
"""
    )

    assert plan.difficulty.value == "easy"
    assert plan.steps[1].agents[0].name == "tester_1"


def test_parse_topology_plan_yaml_rejects_schema_invalid_payload() -> None:
    with pytest.raises(
        TopologySchemaError,
        match="topology step agents must be a list",
    ):
        parse_topology_plan_yaml(
            """
difficulty: easy
steps:
  - index: 0
    agents: invalid
"""
        )


def test_parse_topology_plan_yaml_rejects_logic_invalid_payload() -> None:
    with pytest.raises(
        TopologyLogicError,
        match="final step must contain a testing agent",
    ):
        parse_topology_plan_yaml(
            """
difficulty: easy
steps:
  - index: 0
    agents:
      - name: planner_0
        role: planning
        refs: []
  - index: 1
    agents:
      - name: coder_1
        role: coding
        refs:
          - step_index: 0
            agent_name: planner_0
"""
        )
