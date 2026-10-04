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
**Win Rates over Time**, and **Partnership Win Rates over Time**. The current
game history table is on the first page; the other three pages are scaffolded
for the Power BI report migration.

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