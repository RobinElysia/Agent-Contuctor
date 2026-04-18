"""Bootstrap services used by the initial package baseline."""

from agentconductor.domain.models import DifficultyLevel, ProjectOverview


def bootstrap_overview() -> ProjectOverview:
    """Return stable project capabilities for early integration checks."""
    return ProjectOverview(
        package_name="agentconductor",
        supported_roles=(
            "retrieval",
            "planning",
            "algorithmic",
            "coding",
            "debugging",
            "testing",
        ),
        max_nodes_by_difficulty={
            DifficultyLevel.EASY: 4,
            DifficultyLevel.MEDIUM: 7,
            DifficultyLevel.HARD: 10,
        },
        max_interaction_turns=2,
    )
