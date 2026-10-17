import unittest
from datetime import date
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from badminton_stats.data import normalize_game_history


class TrendDateFilterOptionsTests(unittest.TestCase):
    def setUp(self) -> None:
        source = pd.DataFrame(
            [
                {
                    "Timestamp": "jan-game",
                    "DateTime": "2026-01-15 10:00:00",
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
                    "Timestamp": "may-game",
                    "DateTime": "2026-05-15 10:00:00",
                    "GameType": "Doubles",
                    "Team1Player1": "E",
                    "Team1Player2": "F",
                    "Team2Player1": "G",
                    "Team2Player2": "H",
                    "Team1Score": 21,
                    "Team2Score": 18,
                    "Winner": "E",
                    "WinningTeam": "Team1",
                    "GameDurationSeconds": 600,
                    "WinningPoints": 21,
                    "ScoreDifference": 3,
                },
            ]
        )
        self.games = normalize_game_history(source)
        self.pages_directory = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "badminton_stats"
            / "pages"
        )

    def test_win_rates_options_follow_date_filter(self) -> None:
        app = AppTest.from_file(str(self.pages_directory / "win_rates.py"))
        app.session_state["games"] = self.games
        app.run()

        app.date_input(key="win_rates_date_range_end").set_value(
            date(2026, 1, 15)
        ).run()

        self.assertFalse(app.exception)
        player_filter = next(
            item for item in app.multiselect if item.label == "Player(s)"
        )
        opponent_filter = next(
            item
            for item in app.multiselect
            if item.label == "Opponent(s)"
        )
        self.assertEqual(player_filter.options, ["A", "B", "C", "D"])
        self.assertEqual(opponent_filter.options, ["A", "B", "C", "D"])

    def test_partnership_options_follow_date_filter(self) -> None:
        app = AppTest.from_file(
            str(self.pages_directory / "partnership_win_rates.py")
        )
        app.session_state["games"] = self.games
        app.run()

        app.date_input(
            key="partnership_win_rates_date_range_end"
        ).set_value(date(2026, 1, 15)).run()

        self.assertFalse(app.exception)
        pair_filter = next(
            item for item in app.multiselect if item.label == "Doubles Pair"
        )
        opponent_filter = next(
            item
            for item in app.multiselect
            if item.label == "Opponent(s)"
        )
        self.assertEqual(pair_filter.options, ["A/B", "C/D"])
        self.assertEqual(opponent_filter.options, ["A/B", "C/D"])


if __name__ == "__main__":
    unittest.main()
