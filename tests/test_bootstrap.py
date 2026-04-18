from agentconductor import DifficultyLevel, bootstrap_overview
from agentconductor.interfaces.cli import main


def test_bootstrap_overview_matches_paper_constraints() -> None:
    overview = bootstrap_overview()

    assert overview.package_name == "agentconductor"
    assert overview.supported_roles == (
        "retrieval",
        "planning",
        "algorithmic",
        "coding",
        "debugging",
        "testing",
    )
    assert overview.max_nodes_by_difficulty == {
        DifficultyLevel.EASY: 4,
        DifficultyLevel.MEDIUM: 7,
        DifficultyLevel.HARD: 10,
    }
    assert overview.max_interaction_turns == 2


def test_cli_main_prints_bootstrap_summary(capsys) -> None:
    main()

    captured = capsys.readouterr()
    assert captured.out.strip() == "agentconductor: roles=6, max_turns=2"
