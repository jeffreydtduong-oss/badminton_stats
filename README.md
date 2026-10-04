# Badminton Stats

A Streamlit app for exploring badminton game history.

## Run the app

From the project root, run:

```powershell
uv run streamlit run src\badminton_stats\main.py
```

The app opens in your browser. It loads CSV files from
`E:\Desktop\Badminton apps backup\Stats`, configured in
`src\badminton_stats\main.py`.

Use the sidebar to navigate between **Game History & Matchups**, **Leaderboard**,
**Win Rates over Time**, **Partnership Win Rates over Time**, and
**Margin over Time**. The game history, leaderboard, and trends pages are
available.

## Game history data

The app loads every CSV in the configured folder whose filename contains
`game_history`, including timestamped `*_game_history.csv` exports and the
`unioned_game_history_*.csv` file. The files must have the same columns. Their
rows are combined into one dataset, and exact duplicate rows are removed.

Before display, the game history is normalized into one row per team
perspective: each match appears once for each team, with team and opponent
columns, canonical team names, result, score differential, match key, and
session fields. Rows with duplicate `DateTime` values are reduced to the first
row before the two perspectives are created.

The **Game History** page includes filters for game type, session, month, date
range, team, and opponent. The Games Played summary counts distinct matches.
**Remove Double Counting** shows only one team perspective for each match;
clear all filters restores the full date range and selections. The **Win Rate
by Sides** donut chart shows each side's share of wins for the filtered matches.
The Session Duration card shows the elapsed time for a session only when one
session is explicitly selected. The game table is paginated to keep rendering
responsive; its reverse **Game Number** index continues across pages and
reflects the current filters.

The **Overall Stats** table summarizes wins, losses, win rate, average margin,
and point differential per player/team for the filtered games. Selecting a
row filters the **Head to Head Stats** and game history tables to that player
or team. The head-to-head table reports the filtered record against each
opponent; clearing the selected row restores all players and matchups.

The **Leaderboard** page has separate Doubles and Singles tables with shared
player, session, month, and date filters. Doubles results count each player
individually, including across different partner combinations. Both tables
include win/loss, margin, point differential, and good-/bad-side win rates.

The **Win Rates over Time** page plots individual players' win rates by month
or session, with player, opponent, game type, and date filters. The
**Partnership Win Rates over Time** page plots doubles-pair win rates by month
or session, with pair, opponent, and date filters. Both trend charts show a
percentage label at each point and use smooth lines. The opponent filters have
an explicit **Exclude selected opponents** option; all other filters use
**Select all** only to include every option.

The **Margin over Time** page plots average game margin by session or month,
with filters for game type and the number of most recent data points to show.
It defaults to Doubles, By Session, and the latest 10 sessions.