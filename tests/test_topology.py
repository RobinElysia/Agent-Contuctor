import pytest

from agentconductor import DifficultyLevel, TopologyPlan, TopologyValidationError
from agentconductor.domain.topology import (
    AgentRole,
    TopologyLogicError,
    TopologySchemaError,
)


def test_topology_plan_from_mapping_parses_valid_single_turn_plan() -> None:
    plan = TopologyPlan.from_mapping(
        {
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
                            "name": "coder_1",
                            "role": "coding",
                            "refs": [{"step_index": 0, "agent_name": "planner_0"}],
                        },
                        {
                            "name": "tester_1",
                            "role": "testing",
                            "refs": [{"step_index": 0, "agent_name": "planner_0"}],
                        },
                    ],
                },
            ],
        }
    )

    assert plan.difficulty is DifficultyLevel.EASY
    assert plan.node_count == 3
    assert plan.max_nodes == 4
    assert plan.steps[1].agents[0].role is AgentRole.CODING


def test_topology_plan_to_mapping_returns_canonical_transport_shape() -> None:
    plan = TopologyPlan.from_mapping(
        {
            "difficulty": "medium",
            "steps": [
                {
                    "index": 0,
                    "agents": [
                        {"name": "retrieval_0", "role": "retrieval", "refs": []},
                        {"name": "planner_0", "role": "planning", "refs": []},
                    ],
                },
                {
                    "index": 1,
                    "agents": [
                        {
                            "name": "coder_1",
                            "role": "coding",
                            "refs": [
                                {"step_index": 0, "agent_name": "retrieval_0"},
                                {"step_index": 0, "agent_name": "planner_0"},
                            ],
                        },
                    ],
                },
                {
                    "index": 2,
                    "agents": [
                        {
                            "name": "tester_2",
                            "role": "testing",
                            "refs": [{"step_index": 1, "agent_name": "coder_1"}],
                        },
                    ],
                },
            ],
        }
    )

    assert plan.to_mapping() == {
        "difficulty": "medium",
        "steps": [
            {
                "index": 0,
                "agents": [
                    {"name": "retrieval_0", "role": "retrieval", "refs": []},
                    {"name": "planner_0", "role": "planning", "refs": []},
                ],
            },
            {
                "index": 1,
                "agents": [
                    {
                        "name": "coder_1",
                        "role": "coding",
                        "refs": [
                            {"step_index": 0, "agent_name": "retrieval_0"},
                            {"step_index": 0, "agent_name": "planner_0"},
                        ],
                    }
                ],
            },
            {
                "index": 2,
                "agents": [
                    {
                        "name": "tester_2",
                        "role": "testing",
                        "refs": [{"step_index": 1, "agent_name": "coder_1"}],
                    }
                ],
            },
        ],
    }


def test_topology_plan_from_mapping_rejects_schema_invalid_payload() -> None:
    with pytest.raises(
        TopologySchemaError,
        match="topology plan steps must be a list",
    ):
        TopologyPlan.from_mapping({"difficulty": "easy", "steps": "invalid"})


def test_topology_plan_rejects_first_step_references() -> None:
    with pytest.raises(
        TopologyLogicError,
        match="first step must not reference prior outputs",
    ):
        TopologyPlan.from_mapping(
            {
                "difficulty": "easy",
                "steps": [
                    {
                        "index": 0,
                        "agents": [
                            {
                                "name": "planner_0",
                                "role": "planning",
                                "refs": [{"step_index": 0, "agent_name": "planner_0"}],
                            }
                        ],
                    },
                    {
                        "index": 1,
                        "agents": [{"name": "tester_1", "role": "testing"}],
                    },
                ],
            }
        )


def test_topology_plan_rejects_missing_final_testing_agent() -> None:
    with pytest.raises(
        TopologyLogicError,
        match="final step must contain a testing agent",
    ):
        TopologyPlan.from_mapping(
            {
                "difficulty": "easy",
                "steps": [
                    {
                        "index": 0,
                        "agents": [{"name": "planner_0", "role": "planning"}],
                    },
                    {
                        "index": 1,
                        "agents": [
                            {
                                "name": "coder_1",
                                "role": "coding",
                                "refs": [{"step_index": 0, "agent_name": "planner_0"}],
                            }
                        ],
                    },
                ],
            }
        )


def test_topology_plan_rejects_unknown_or_future_references() -> None:
    with pytest.raises(
        TopologyLogicError,
        match="references must target earlier steps only",
    ):
        TopologyPlan.from_mapping(
            {
                "difficulty": "medium",
                "steps": [
                    {
                        "index": 0,
                        "agents": [{"name": "planner_0", "role": "planning"}],
                    },
                    {
                        "index": 1,
                        "agents": [
                            {
                                "name": "tester_1",
                                "role": "testing",
                                "refs": [{"step_index": 1, "agent_name": "planner_0"}],
                            }
                        ],
                    },
                ],
            }
        )


def test_topology_plan_rejects_node_budget_overflow() -> None:
    with pytest.raises(
        TopologyLogicError,
        match="topology plan exceeds node budget for easy: 5 > 4",
    ):
        TopologyPlan.from_mapping(
            {
                "difficulty": "easy",
                "steps": [
                    {
                        "index": 0,
                        "agents": [
                            {"name": "planner_0", "role": "planning"},
                            {"name": "retrieval_0", "role": "retrieval"},
                        ],
                    },
                    {
                        "index": 1,
                        "agents": [
                            {
                                "name": "algorithmic_1",
                                "role": "algorithmic",
                                "refs": [{"step_index": 0, "agent_name": "planner_0"}],
                            },
                            {
                                "name": "coding_1",
                                "role": "coding",
                                "refs": [{"step_index": 0, "agent_name": "planner_0"}],
                            },
                            {
                                "name": "testing_1",
                                "role": "testing",
                                "refs": [{"step_index": 0, "agent_name": "planner_0"}],
                            },
                        ],
                    },
                ],
            }
        )


def test_topology_schema_and_logic_errors_remain_topology_validation_errors() -> None:
    assert issubclass(TopologySchemaError, TopologyValidationError)
    assert issubclass(TopologyLogicError, TopologyValidationError)
