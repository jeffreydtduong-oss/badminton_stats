import unittest
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from badminton_stats.data import normalize_game_history


class MarginOverTimeTests(unittest.TestCase):
    def test_numeric_input_sets_last_data_points_without_slider(self) -> None:
        source = pd.DataFrame(
            [
                {
                    "Timestamp": str(index),
                    "DateTime": f"{day} 10:00:00",
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
                }
                for index, day in enumerate(
                    ["2026-01-01", "2026-01-02", "2026-01-03"]
                )
            ]
        )
        app = AppTest.from_file(
            str(
                Path(__file__).resolve().parents[1]
                / "src"
                / "badminton_stats"
                / "pages"
                / "margin_over_time.py"
            )
        )
        app.session_state["games"] = normalize_game_history(source)
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.slider), 0)
        self.assertEqual(
            app.number_input(key="margin_over_time_data_points").value,
            3,
        )

        app.number_input(
            key="margin_over_time_data_points"
        ).set_value(2).run()
        self.assertFalse(app.exception)
        self.assertEqual(
            app.number_input(key="margin_over_time_data_points").value,
            2,
        )


if __name__ == "__main__":
    unittest.main()
