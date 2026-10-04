import unittest
from typing import Optional
from unittest.mock import patch

import pandas as pd

from badminton_stats.google_sheets import (
    append_new_game_history,
    load_game_history_from_sheet,
)
from badminton_stats.data import normalize_game_history


class FakeWorksheet:
    def __init__(self, values: list[list[str]]) -> None:
        self.values = values
        self.update_range: Optional[str] = None
        self.update_option: Optional[str] = None
        self.append_option: Optional[str] = None

    def get_all_values(self) -> list[list[str]]:
        return self.values

    def update(
        self,
        values: list[list[str]],
        range_name: str,
        value_input_option: str,
    ) -> None:
        self.update_range = range_name
        self.update_option = value_input_option
        self.values = values

    def append_rows(
        self,
        values: list[list[str]],
        value_input_option: str,
    ) -> None:
        self.append_option = value_input_option
        self.values.extend(values)


class GoogleSheetsTests(unittest.TestCase):
    def test_upload_appends_only_unseen_datetimes(self) -> None:
        worksheet = FakeWorksheet([])
        games = pd.DataFrame(
            {
                "DateTime": [
                    "2026-01-01 10:00:00",
                    "2026-01-01 10:00:00",
                    "2026-01-02 10:00:00",
                ],
                "Team1Score": [21, 21, 18],
            }
        )

        with patch(
            "badminton_stats.google_sheets._open_worksheet",
            return_value=worksheet,
        ):
            first_upload = append_new_game_history("sheet", {}, games)
            second_upload = append_new_game_history("sheet", {}, games)

        self.assertEqual(first_upload, (2, 1))
        self.assertEqual(second_upload, (0, 1))
        self.assertEqual(
            worksheet.values,
            [
                ["DateTime", "Team1Score"],
                ["2026-01-01 10:00:00", "21"],
                ["2026-01-02 10:00:00", "18"],
            ],
        )
        self.assertEqual(worksheet.update_range, "A1")
        self.assertEqual(worksheet.update_option, "RAW")
        self.assertEqual(worksheet.append_option, "RAW")

    def test_upload_rejects_mismatched_sheet_headers(self) -> None:
        worksheet = FakeWorksheet([["DateTime", "Other"]])
        games = pd.DataFrame(
            {"DateTime": ["2026-01-01 10:00:00"], "Team1Score": [21]}
        )

        with patch(
            "badminton_stats.google_sheets._open_worksheet",
            return_value=worksheet,
        ):
            with self.assertRaisesRegex(ValueError, "header does not match"):
                append_new_game_history("sheet", {}, games)

    def test_sheet_loader_converts_empty_cells_to_missing_values(self) -> None:
        worksheet = FakeWorksheet(
            [
                ["DateTime", "Team1Score", "OptionalPlayer"],
                ["2026-01-01 10:00:00", "21", ""],
            ]
        )

        with patch(
            "badminton_stats.google_sheets._open_worksheet",
            return_value=worksheet,
        ):
            games = load_game_history_from_sheet("sheet", {})

        self.assertEqual(games.loc[0, "Team1Score"], "21")
        self.assertTrue(pd.isna(games.loc[0, "OptionalPlayer"]))

    def test_sheet_rows_normalize_for_the_reporting_pages(self) -> None:
        worksheet = FakeWorksheet(
            [
                [
                    "Timestamp",
                    "DateTime",
                    "GameType",
                    "Team1Player1",
                    "Team1Player2",
                    "Team2Player1",
                    "Team2Player2",
                    "Team1Score",
                    "Team2Score",
                    "Winner",
                    "WinningTeam",
                    "GameDurationSeconds",
                    "WinningPoints",
                    "ScoreDifference",
                ],
                [
                    "2026-01-01T10:00:00",
                    "2026-01-01T10:00:00",
                    "Doubles",
                    "Alex",
                    "Bea",
                    "Chris",
                    "Dee",
                    "21",
                    "18",
                    "Alex/Bea",
                    "Team1",
                    "600",
                    "21",
                    "3",
                ],
            ]
        )

        with patch(
            "badminton_stats.google_sheets._open_worksheet",
            return_value=worksheet,
        ):
            source_games = load_game_history_from_sheet("sheet", {})

        normalized = normalize_game_history(source_games)
        self.assertEqual(len(normalized), 2)
        self.assertEqual(
            set(normalized["TeamCanonical"]),
            {"Alex/Bea", "Chris/Dee"},
        )


if __name__ == "__main__":
    unittest.main()
