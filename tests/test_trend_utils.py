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
                },
                {
                    "Player": "A",
                    "Period": "2026-01",
                    "Result": "Lost",
                    "IsDynasty": False,
                    "GameKey": "game-2",
                },
                {
                    "Player": "B",
                    "Period": "2026-01",
                    "Result": "Won",
                    "IsDynasty": True,
                    "GameKey": "game-1",
                },
            ]
        )

        stats = aggregate_trend_data(games, "Player").set_index("Series")

        self.assertEqual(stats.loc["A", "WinRate"], 0.5)
        self.assertEqual(stats.loc["A", "Wins"], 1)
        self.assertEqual(stats.loc["A", "Losses"], 1)
        self.assertEqual(stats.loc["A", "Dynasties"], 1)
        self.assertEqual(stats.loc["A", "Games"], 2)
        self.assertEqual(stats.loc["B", "Dynasties"], 1)


if __name__ == "__main__":
    unittest.main()
