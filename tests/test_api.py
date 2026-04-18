import pytest

from agentconductor import DifficultyLevel, ProblemInstance, SolveStatus, solve_problem


def test_solve_problem_returns_typed_boundary_result() -> None:
    result = solve_problem(
        ProblemInstance(
            identifier="apps-two-sum",
            prompt="Write a function that returns two indices adding up to a target.",
            difficulty=DifficultyLevel.EASY,
        )
    )

    assert result.problem_id == "apps-two-sum"
    assert result.status is SolveStatus.PLANNED
    assert result.selected_difficulty is DifficultyLevel.EASY
    assert result.planned_turns == 2
    assert result.max_nodes == 4
    assert result.available_roles == (
        "retrieval",
        "planning",
        "algorithmic",
        "coding",
        "debugging",
        "testing",
    )


def test_solve_problem_uses_inferred_baseline_defaults() -> None:
    result = solve_problem(
        ProblemInstance(
            identifier="apps-unknown",
            prompt="Solve the problem with a correct implementation.",
        ),
        max_turns=1,
    )

    assert result.selected_difficulty is DifficultyLevel.MEDIUM
    assert result.planned_turns == 1
    assert result.max_nodes == 7


def test_solve_problem_rejects_invalid_turn_budget() -> None:
    with pytest.raises(ValueError, match="max_turns must be <= 2"):
        solve_problem(
            ProblemInstance(identifier="bad-turns", prompt="Any prompt"),
            max_turns=3,
        )
