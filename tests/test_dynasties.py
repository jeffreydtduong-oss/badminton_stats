import unittest

import pandas as pd

from badminton_stats.data import normalize_game_history


def _normalized_games(
    games: list[tuple[str, str, str]],
) -> pd.DataFrame:
    rows = []
    for index, (date_time, game_type, winning_team) in enumerate(games):
        is_doubles = game_type == "Doubles"
        rows.append(
            {
                "Timestamp": f"{date_time}-{index}",
                "DateTime": date_time,
                "GameType": game_type,
                "Team1Player1": "A1",
                "Team1Player2": "A2" if is_doubles else None,
                "Team2Player1": "B1",
                "Team2Player2": "B2" if is_doubles else None,
                "Team1Score": 21 if winning_team == "Team1" else 18,
                "Team2Score": 18 if winning_team == "Team1" else 21,
                "Winner": "A1" if winning_team == "Team1" else "B1",
                "WinningTeam": winning_team,
                "GameDurationSeconds": 600,
                "WinningPoints": 21,
                "ScoreDifference": 3,
            }
        )
    return normalize_game_history(pd.DataFrame(rows))


class DynastyTests(unittest.TestCase):
    def test_four_consecutive_doubles_wins_count_as_one_dynasty(self) -> None:
        games = _normalized_games(
            [
                ("2026-01-01 10:00:00", "Doubles", "Team1"),
                ("2026-01-01 10:30:00", "Doubles", "Team1"),
                ("2026-01-01 11:00:00", "Doubles", "Team1"),
                ("2026-01-01 11:30:00", "Doubles", "Team1"),
            ]
        )

        dynasty_rows = games[games["IsDynasty"]]
        self.assertEqual(len(dynasty_rows), 1)
        self.assertEqual(
            dynasty_rows.iloc[0]["DateTime"],
            pd.Timestamp("2026-01-01 11:00:00"),
        )
        self.assertEqual(dynasty_rows.iloc[0]["TeamCanonical"], "A1/A2")

    def test_dynasty_is_credited_when_winner_is_isindexeven_one(self) -> None:
        games = _normalized_games(
            [
                ("2026-01-01 10:00:00", "Doubles", "Team2"),
                ("2026-01-01 10:30:00", "Doubles", "Team2"),
                ("2026-01-01 11:00:00", "Doubles", "Team2"),
            ]
        )

        dynasty_rows = games[games["IsDynasty"]]
        self.assertEqual(len(dynasty_rows), 1)
        self.assertEqual(dynasty_rows.iloc[0]["TeamCanonical"], "B1/B2")
        self.assertEqual(dynasty_rows.iloc[0]["Result"], "Won")
        self.assertEqual(dynasty_rows.iloc[0]["IsIndexEven"], 1)

    def test_wins_across_sessions_do_not_form_a_dynasty(self) -> None:
        games = _normalized_games(
            [
                ("2026-01-01 10:00:00", "Doubles", "Team1"),
                ("2026-01-01 10:30:00", "Doubles", "Team1"),
                ("2026-01-02 10:00:00", "Doubles", "Team1"),
            ]
        )

        self.assertFalse(games["IsDynasty"].any())

    def test_singles_game_breaks_a_doubles_streak(self) -> None:
        games = _normalized_games(
            [
                ("2026-01-01 10:00:00", "Doubles", "Team1"),
                ("2026-01-01 10:30:00", "Doubles", "Team1"),
                ("2026-01-01 11:00:00", "Singles", "Team1"),
                ("2026-01-01 11:30:00", "Doubles", "Team1"),
            ]
        )

        self.assertFalse(games["IsDynasty"].any())


if __name__ == "__main__":
    unittest.main()
