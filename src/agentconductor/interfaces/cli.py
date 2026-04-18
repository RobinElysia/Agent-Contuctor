"""Thin CLI wrapper around package services."""

from agentconductor.interfaces.api import bootstrap_overview


def main() -> None:
    """Print a human-readable bootstrap summary."""
    overview = bootstrap_overview()
    print(
        f"{overview.package_name}: roles={len(overview.supported_roles)}, "
        f"max_turns={overview.max_interaction_turns}"
    )
