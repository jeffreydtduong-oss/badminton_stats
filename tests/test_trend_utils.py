import unittest

import pandas as pd

from badminton_stats.pages.trend_utils import aggregate_trend_data


class TrendAggregationTests(unittest.TestCase):
    def test_aggregates_win_rates_counts_and_dynasties(self) -> None:
        games = pd.DataFrame(
            [
                {
                    "Player": "A",
                    "Period": "2026-01",
                    "Result": "Won",
                    "IsDynasty": True,
                    "GameKey": "game-1",
                    "WinningPoints": 21,
                    "PointDifferential": 5,
                    "IsIndexEven": 0,
                },
                {
                    "Player": "A",
                    "Period": "2026-01",
                    "Result": "Lost",
                    "IsDynasty": False,
                    "GameKey": "game-2",
                    "WinningPoints": 21,
                    "PointDifferential": -3,
                    "IsIndexEven": 1,
                },
                {
                    "Player": "B",
                    "Period": "2026-01",
                    "Result": "Won",
                    "IsDynasty": True,
                    "GameKey": "game-1",
                    "WinningPoints": 21,
                    "PointDifferential": 5,
                    "IsIndexEven": 0,
                },
                {
                    "Player": "C",
                    "Period": "2026-01",
                    "Result": "Lost",
                    "IsDynasty": False,
                    "GameKey": "game-3",
                    "WinningPoints": 21,
                    "PointDifferential": -4,
                    "IsIndexEven": 1,
                },
            ]
        )

        stats = aggregate_trend_data(games, "Player").set_index("Series")

        self.assertEqual(stats.loc["A", "WinRate"], 0.5)
        self.assertEqual(stats.loc["A", "Wins"], 1)
        self.assertEqual(stats.loc["A", "Losses"], 1)
        self.assertEqual(stats.loc["A", "Dynasties"], 1)
        self.assertEqual(stats.loc["A", "Games"], 2)
        self.assertAlmostEqual(stats.loc["A", "WinsMargin"], 3 / 19)
        self.assertAlmostEqual(stats.loc["A", "LossesMargin"], 1 / 19)
        self.assertAlmostEqual(stats.loc["A", "TotalMargin"], 2 / 19)
        self.assertEqual(stats.loc["A", "PointDifference"], 1)
        self.assertEqual(stats.loc["A", "WinPercentGoodSide"], 1)
        self.assertEqual(stats.loc["A", "WinPercentBadSide"], 0)
        self.assertEqual(stats.loc["B", "Dynasties"], 1)
        self.assertEqual(stats.loc["B", "WinPercentBadSide"], 0)
        self.assertEqual(stats.loc["C", "WinRate"], 0)
        self.assertTrue(pd.isna(stats.loc["C", "WinPercentGoodSide"]))
        self.assertTrue(pd.isna(stats.loc["C", "WinPercentBadSide"]))


if __name__ == "__main__":
    unittest.main()
