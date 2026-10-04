# Badminton Stats

A Streamlit app for exploring badminton game history.

## Run the app

From the project root, run:

```powershell
uv run streamlit run src\badminton_stats\main.py
```

The app opens in your browser. Without Google Sheets credentials, it loads CSV
files from `E:\Desktop\Badminton apps backup\Stats`. With Google Sheets
credentials configured, it reads the `Game History` worksheet instead.

Use the sidebar to navigate between **Game History & Matchups**, **Leaderboard**,
**Win Rates over Time**, **Partnership Win Rates over Time**, and
**Margin over Time**. The game history, leaderboard, and trends pages are
available.

## Game history data

The app loads every CSV in the configured folder whose filename contains
`game_history`, including timestamped `*_game_history.csv` exports and the
`unioned_game_history_*.csv` file. The files must have the same columns. Their
rows are combined into one dataset, and exact duplicate rows are removed.
For cloud deployment, the same raw columns are stored in a Google Sheet and
normalized by the app at startup; you do not upload a separate normalized
table.

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

## Google Sheets updates and Streamlit Community Cloud

1. Create a Google Cloud service account, enable the Google Sheets API, and
   download its JSON key to a private location on your computer. Create a
   Google spreadsheet and share it with the service account's
   `client_email` as an Editor. Keep the spreadsheet private; it does not need
   to be published or shared with dashboard viewers.
2. Configure the uploader with the spreadsheet ID (the part between `/d/` and
   `/edit` in its URL) and the path to the downloaded service-account JSON.
   To set these variables just for the current PowerShell terminal:

   ```powershell
   $env:BADMINTON_STATS_SPREADSHEET_ID = "your-spreadsheet-id"
   $env:GOOGLE_APPLICATION_CREDENTIALS = "C:\private\badminton-service-account.json"
   ```

   To set them once for your Windows user instead, use:

   ```powershell
   [Environment]::SetEnvironmentVariable("BADMINTON_STATS_SPREADSHEET_ID", "your-spreadsheet-id", "User")
   [Environment]::SetEnvironmentVariable("GOOGLE_APPLICATION_CREDENTIALS", "C:\private\badminton-service-account.json", "User")
   ```

   Restart PowerShell after setting user-level variables.

3. Drop new exports into the configured game-history folder and run:

   ```powershell
   uv run upload-game-history
   ```

   The uploader reads matching `game_history` CSV files, creates the
   **Game History** worksheet if needed, and appends only records whose
   `DateTime` is not already in the sheet. It expects exports with matching
   columns. It is safe to rerun after an upload; already-uploaded games are
   skipped. You can specify a different folder with
   `--directory "C:\path\to\exports"`.
4. For local development with the cloud data source, set the same two
   environment variables and run the app. The sidebar's **Refresh game data**
   button clears its cache and reloads the sheet; otherwise sheet data is
   cached for up to five minutes.
5. To deploy, push the app code to GitHub and create a Streamlit Community
   Cloud app from this repository, using `src/badminton_stats/main.py` as the
   entrypoint. In the app's **Settings > Secrets**, add the following TOML
   structure, filling in the service-account values from the JSON key:

   ```toml
   [google_sheets]
   spreadsheet_id = "your-spreadsheet-id"

   [gcp_service_account]
   type = "service_account"
   project_id = "your-project-id"
   private_key_id = "your-private-key-id"
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "your-service-account@your-project.iam.gserviceaccount.com"
   client_id = "your-client-id"
   token_uri = "https://oauth2.googleapis.com/token"
   ```

   Copy the remaining fields from the service-account JSON if present. Never
   commit the key JSON or `.streamlit/secrets.toml`; both are excluded by
   `.gitignore`. The uploader requires local credentials, while the deployed
   app uses the secrets configured in Community Cloud.