"""Topology schema and validation for single-turn execution plans."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping

from agentconductor.domain.models import DifficultyLevel


MAX_NODES_BY_DIFFICULTY: dict[DifficultyLevel, int] = {
    DifficultyLevel.EASY: 4,
    DifficultyLevel.MEDIUM: 7,
    DifficultyLevel.HARD: 10,
}


class AgentRole(StrEnum):
    """Agent roles described by the paper."""

    RETRIEVAL = "retrieval"
    PLANNING = "planning"
    ALGORITHMIC = "algorithmic"
    CODING = "coding"
    DEBUGGING = "debugging"
    TESTING = "testing"


@dataclass(frozen=True, slots=True)
class AgentReference:
    """Reference to a prior agent output in the topology."""

    step_index: int
    agent_name: str


@dataclass(frozen=True, slots=True)
class AgentInvocation:
    """One agent node inside a topology step."""

    name: str
    role: AgentRole
    refs: tuple[AgentReference, ...] = ()


@dataclass(frozen=True, slots=True)
class TopologyStep:
    """One execution layer in the topology."""

    index: int
    agents: tuple[AgentInvocation, ...]


class TopologyValidationError(ValueError):
    """Raised when a topology plan violates schema or logical constraints."""


class TopologySchemaError(TopologyValidationError):
    """Raised when a topology transport payload violates the field contract."""


class TopologyLogicError(TopologyValidationError):
    """Raised when a parsed topology violates graph-level execution rules."""


@dataclass(frozen=True, slots=True)
class TopologyPlan:
    """Single-turn layered topology plan."""

    difficulty: DifficultyLevel
    steps: tuple[TopologyStep, ...]

    @property
    def node_count(self) -> int:
        return sum(len(step.agents) for step in self.steps)

    @property
    def max_nodes(self) -> int:
        return MAX_NODES_BY_DIFFICULTY[self.difficulty]

    def to_mapping(self) -> dict[str, Any]:
        """Serialize the topology plan into the repository transport mapping.

        Inference:
        The repository keeps ``TopologyPlan`` as the source of truth and uses a
        stable plain-mapping representation as the canonical transport shape for
        later YAML encoding, training artifacts, and fixture-driven tests.
        """
        return {
            "difficulty": self.difficulty.value,
            "steps": [
                {
                    "index": step.index,
                    "agents": [
                        {
                            "name": agent.name,
                            "role": agent.role.value,
                            "refs": [
                                {
                                    "step_index": ref.step_index,
                                    "agent_name": ref.agent_name,
                                }
                                for ref in agent.refs
                            ],
                        }
                        for agent in step.agents
                    ],
                }
                for step in self.steps
            ],
        }

    def validate(self) -> None:
        if not self.steps:
            raise TopologyLogicError("topology plan must contain at least one step")

        expected_indices = tuple(range(len(self.steps)))
        actual_indices = tuple(step.index for step in self.steps)
        if actual_indices != expected_indices:
            raise TopologyLogicError(
                "topology steps must use contiguous zero-based indices"
            )

        if self.node_count > self.max_nodes:
            raise TopologyLogicError(
                f"topology plan exceeds node budget for {self.difficulty.value}: "
                f"{self.node_count} > {self.max_nodes}"
            )

        seen_names: set[str] = set()
        final_has_testing_agent = False

        for step in self.steps:
            if not step.agents:
                raise TopologyLogicError(
                    f"topology step {step.index} must contain at least one agent"
                )

            step_names: set[str] = set()
            for agent in step.agents:
                if agent.name in step_names or agent.name in seen_names:
                    raise TopologyLogicError(
                        f"agent name '{agent.name}' must be unique across the topology plan"
                    )
                step_names.add(agent.name)

                if step.index == 0 and agent.refs:
                    raise TopologyLogicError(
                        "agents in the first step must not reference prior outputs"
                    )

                for ref in agent.refs:
                    if ref.step_index >= step.index:
                        raise TopologyLogicError(
                            f"agent '{agent.name}' references step {ref.step_index}, "
                            "but references must target earlier steps only"
                        )
                    if ref.agent_name not in seen_names:
                        raise TopologyLogicError(
                            f"agent '{agent.name}' references unknown prior agent "
                            f"'{ref.agent_name}'"
                        )

            if step.index == len(self.steps) - 1:
                final_has_testing_agent = any(
                    agent.role is AgentRole.TESTING for agent in step.agents
                )

            seen_names.update(step_names)

        if not final_has_testing_agent:
            raise TopologyLogicError(
                "the final step must contain a testing agent"
            )

    @classmethod
    def from_mapping(cls, raw_plan: Mapping[str, Any]) -> TopologyPlan:
        """Parse a topology plan from a plain mapping.

        Inference:
        The paper does not define a complete concrete schema. This parser uses a
        repository-local mapping contract to keep the topology API dependency-free
        until a YAML adapter is introduced.
        """
        difficulty_value = raw_plan.get("difficulty")
        if not isinstance(difficulty_value, str):
            raise TopologySchemaError("topology plan difficulty must be a string")

        try:
            difficulty = DifficultyLevel(difficulty_value)
        except ValueError as exc:
            raise TopologySchemaError(
                f"unsupported difficulty level '{difficulty_value}'"
            ) from exc

        raw_steps = raw_plan.get("steps")
        if not isinstance(raw_steps, list):
            raise TopologySchemaError("topology plan steps must be a list")

        steps: list[TopologyStep] = []
        for raw_step in raw_steps:
            if not isinstance(raw_step, Mapping):
                raise TopologySchemaError("each topology step must be a mapping")

            step_index = raw_step.get("index")
            if not isinstance(step_index, int):
                raise TopologySchemaError("topology step index must be an integer")

            raw_agents = raw_step.get("agents")
            if not isinstance(raw_agents, list):
                raise TopologySchemaError("topology step agents must be a list")

            agents: list[AgentInvocation] = []
            for raw_agent in raw_agents:
                if not isinstance(raw_agent, Mapping):
                    raise TopologySchemaError(
                        "each topology agent entry must be a mapping"
                    )

                name = raw_agent.get("name")
                if not isinstance(name, str) or not name:
                    raise TopologySchemaError(
                        "topology agent name must be a non-empty string"
                    )

                role_value = raw_agent.get("role")
                if not isinstance(role_value, str):
                    raise TopologySchemaError(
                        f"agent '{name}' role must be a string"
                    )
                try:
                    role = AgentRole(role_value)
                except ValueError as exc:
                    raise TopologySchemaError(
                        f"agent '{name}' has unsupported role '{role_value}'"
                    ) from exc

                raw_refs = raw_agent.get("refs", [])
                if not isinstance(raw_refs, list):
                    raise TopologySchemaError(
                        f"agent '{name}' refs must be a list"
                    )

                refs: list[AgentReference] = []
                for raw_ref in raw_refs:
                    if not isinstance(raw_ref, Mapping):
                        raise TopologySchemaError(
                            f"agent '{name}' references must be mappings"
                        )
                    ref_step_index = raw_ref.get("step_index")
                    ref_agent_name = raw_ref.get("agent_name")
                    if not isinstance(ref_step_index, int) or not isinstance(
                        ref_agent_name, str
                    ):
                        raise TopologySchemaError(
                            f"agent '{name}' references must include integer "
                            "'step_index' and string 'agent_name'"
                        )
                    refs.append(
                        AgentReference(
                            step_index=ref_step_index,
                            agent_name=ref_agent_name,
                        )
                    )

                agents.append(AgentInvocation(name=name, role=role, refs=tuple(refs)))

            steps.append(TopologyStep(index=step_index, agents=tuple(agents)))

        plan = cls(difficulty=difficulty, steps=tuple(steps))
        plan.validate()
        return plan
