import unittest
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from badminton_stats.data import normalize_game_history


class GameHistoryTotalsTests(unittest.TestCase):
    def test_overall_stats_totals_row_aggregates_filtered_team_records(self) -> None:
        source = pd.DataFrame(
            [
                {
                    "Timestamp": "game-1",
                    "DateTime": "2026-01-01 10:00:00",
                    "GameType": "Doubles",
                    "Team1Player1": "A",
                    "Team1Player2": "B",
                    "Team2Player1": "C",
                    "Team2Player2": "D",
                    "Team1Score": 21,
                    "Team2Score": 18,
                    "Winner": "A",
                    "WinningTeam": "Team1",
                    "GameDurationSeconds": 600,
                    "WinningPoints": 21,
                    "ScoreDifference": 3,
                },
                {
                    "Timestamp": "game-2",
                    "DateTime": "2026-01-01 10:30:00",
                    "GameType": "Doubles",
                    "Team1Player1": "A",
                    "Team1Player2": "B",
                    "Team2Player1": "C",
                    "Team2Player2": "D",
                    "Team1Score": 18,
                    "Team2Score": 21,
                    "Winner": "C",
                    "WinningTeam": "Team2",
                    "GameDurationSeconds": 600,
                    "WinningPoints": 21,
                    "ScoreDifference": 3,
                },
            ]
        )
        games = normalize_game_history(source)
        app = AppTest.from_file(
            str(
                Path(__file__).resolve().parents[1]
                / "src"
                / "badminton_stats"
                / "pages"
                / "game_history.py"
            )
        )
        app.session_state["games"] = games

        app.run()

        self.assertFalse(app.exception)
        overall_stats = app.dataframe[0].value
        self.assertEqual(
            overall_stats["Player(s)"].tolist(),
            ["A/B", "C/D", "Total"],
        )
        totals = overall_stats.iloc[-1]
        self.assertEqual(totals["Player(s)"], "Total")
        self.assertEqual(totals["Wins"], 2)
        self.assertEqual(totals["Losses"], 2)
        self.assertEqual(totals["Win Rate"], 0.5)
        self.assertAlmostEqual(totals["Total Margin"], 1 / 19)
        self.assertEqual(totals["Point +/- per game"], 0)


if __name__ == "__main__":
    unittest.main()
