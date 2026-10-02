# Badminton Stats

A Streamlit app for exploring badminton game history.

## Run the app

From the project root, run:

```powershell
uv run streamlit run src\badminton_stats\main.py
```

The app opens in your browser. Its **Data folder** field defaults to
`E:\Desktop\Badminton apps backup\Stats`; change it if your CSVs are stored
somewhere else.

## Game history data

The app loads every CSV in the selected folder whose filename contains
`game_history`, including timestamped `*_game_history.csv` exports and the
`unioned_game_history_*.csv` file. The files must have the same columns. Their
rows are combined into one dataset, and exact duplicate rows are removed
before display.