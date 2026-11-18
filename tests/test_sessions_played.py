import json
import unittest
from datetime import date
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from badminton_stats.data import normalize_game_history
from badminton_stats.pages.trend_utils import SELECT_ALL


PLAYER_FILTER_KEY = "sessions_played_players"
GAME_TYPE_FILTER_KEY = "sessions_played_game_types"


class SessionsPlayedTests(unittest.TestCase):
    def setUp(self) -> None:
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
                {
                    "Timestamp": "game-3",
                    "DateTime": "2026-01-02 19:00:00",
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
                    "Timestamp": "game-4",
                    "DateTime": "2026-02-03 10:00:00",
                    "GameType": "Doubles",
                    "Team1Player1": "A",
                    "Team1Player2": "E",
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
                    "Timestamp": "game-5",
                    "DateTime": "2026-03-04 11:00:00",
                    "GameType": "Singles",
                    "Team1Player1": "A",
                    "Team1Player2": None,
                    "Team2Player1": "F",
                    "Team2Player2": None,
                    "Team1Score": 21,
                    "Team2Score": 18,
                    "Winner": "A",
                    "WinningTeam": "Team1",
                    "GameDurationSeconds": 600,
                    "WinningPoints": 21,
                    "ScoreDifference": 3,
                },
            ]
        )
        self.games = normalize_game_history(source)
        self.page_path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "badminton_stats"
            / "pages"
            / "sessions_played.py"
        )

    def test_leaderboard_filters_and_player_session_drilldown(self) -> None:
        app = AppTest.from_file(str(self.page_path))
        app.session_state["games"] = self.games

        app.run()

        self.assertFalse(app.exception)
        leaderboard = app.dataframe[0].value
        self.assertEqual(
            leaderboard.columns.tolist(),
            ["Player", "Sessions Played", "Games Played"],
        )
        self.assertEqual(leaderboard.iloc[0].to_dict(), {
            "Player": "A",
            "Sessions Played": 4,
            "Games Played": 5,
        })
        self.assertEqual(
            leaderboard["Sessions Played"].tolist(),
            [4, 3, 3, 2, 1, 1],
        )
        self.assertTrue(
            any(
                item.key == f"{PLAYER_FILTER_KEY}_search"
                for item in app.text_input
            )
        )

        app.text_input(
            key=f"{PLAYER_FILTER_KEY}_search"
        ).set_value("A").run()

        self.assertFalse(app.exception)
        checkbox_labels = [item.label for item in app.checkbox]
        self.assertIn("A", checkbox_labels)
        self.assertNotIn("B", checkbox_labels)

        app.multiselect(key=GAME_TYPE_FILTER_KEY).set_value(
            ["Singles"]
        ).run()

        self.assertFalse(app.exception)
        singles_leaderboard = app.dataframe[0].value.set_index("Player")
        self.assertEqual(set(singles_leaderboard.index), {"A", "F"})
        self.assertEqual(
            singles_leaderboard["Games Played"].tolist(),
            [1, 1],
        )

        app.multiselect(key=GAME_TYPE_FILTER_KEY).set_value(
            [SELECT_ALL]
        ).run()

        app.session_state[PLAYER_FILTER_KEY] = ["A"]
        app.text_input(key=f"{PLAYER_FILTER_KEY}_search").set_value("").run()

        self.assertFalse(app.exception)
        self.assertEqual(
            app.dataframe[0].value["Player"].tolist(),
            ["A"],
        )

        app.session_state[PLAYER_FILTER_KEY] = [SELECT_ALL]
        app.run()

        app.multiselect(key="sessions_played_months").set_value(
            ["2026-01"]
        ).run()

        self.assertFalse(app.exception)
        january_leaderboard = app.dataframe[0].value.set_index("Player")
        self.assertEqual(
            january_leaderboard.loc["A", "Sessions Played"],
            2,
        )
        self.assertEqual(january_leaderboard.loc["A", "Games Played"], 3)
        self.assertNotIn("E", january_leaderboard.index)

        app.date_input(key="sessions_played_date_range_end").set_value(
            date(2026, 1, 1)
        ).run()

        self.assertFalse(app.exception)
        filtered_leaderboard = app.dataframe[0].value
        self.assertEqual(filtered_leaderboard.iloc[0]["Player"], "A")
        self.assertEqual(filtered_leaderboard.iloc[0]["Sessions Played"], 1)
        self.assertEqual(filtered_leaderboard.iloc[0]["Games Played"], 2)

        app.session_state["sessions_played_leaderboard"] = {
            "selection": {"rows": [0], "columns": []}
        }
        app.run()

        self.assertFalse(app.exception)
        session_table = app.dataframe[0].value
        self.assertEqual(
            session_table.columns.tolist(),
            ["Session Key", "Games Played"],
        )
        self.assertEqual(session_table["Games Played"].tolist(), [2])
        self.assertEqual(
            [metric.value for metric in app.metric],
            ["1", "2"],
        )
        monthly_chart = app.get("vega_lite_chart")[0]
        chart_spec = json.loads(monthly_chart.proto.spec)
        line_layer = chart_spec["layer"][0]
        self.assertEqual(
            line_layer["mark"]["type"],
            "line",
        )
        self.assertEqual(
            line_layer["encoding"]["x"]["title"],
            "Month Year",
        )
        self.assertEqual(
            line_layer["encoding"]["y"]["title"],
            "Sessions Played",
        )
        self.assertIn(
            "Games Played",
            [
                tooltip["title"]
                for tooltip in line_layer["encoding"]["tooltip"]
            ],
        )

        next(
            button
            for button in app.button
            if button.label == "Back to leaderboard"
        ).click().run()

        self.assertFalse(app.exception)
        self.assertEqual(
            app.dataframe[0].value.columns.tolist(),
            ["Player", "Sessions Played", "Games Played"],
        )

        next(
            button
            for button in app.button
            if button.label == "Clear all filters"
        ).click().run()

        self.assertFalse(app.exception)
        self.assertEqual(app.dataframe[0].value.iloc[0]["Games Played"], 5)

        app.session_state["sessions_played_leaderboard"] = {
            "selection": {"rows": [0], "columns": []}
        }
        app.run()

        self.assertFalse(app.exception)
        chart_spec = json.loads(app.get("vega_lite_chart")[0].proto.spec)
        self.assertEqual(
            chart_spec["layer"][0]["encoding"]["x"]["sort"],
            ["2026-01", "2026-02", "2026-03"],
        )


if __name__ == "__main__":
    unittest.main()
