import pandas as pd
import streamlit as st

from badminton_stats.pages.trend_utils import (
    SELECT_ALL,
    expand_individual_players,
    filter_date_range,
    multiselect,
    render_win_rate_chart,
    selected_values,
    unique_values,
)


FILTER_KEYS = {
    "players": "win_rates_players",
    "opponents": "win_rates_opponents",
    "game_types": "win_rates_game_types",
}
DATE_RANGE_KEY = "win_rates_date_range"
TIME_PERIOD_KEY = "win_rates_time_period"
EXCLUDE_OPPONENTS_KEY = "win_rates_exclude_opponents"


st.title("Win Rates over Time")

games = st.session_state["games"].copy()
if games.empty:
    st.info("No games are available.")
    st.stop()

available_game_types = unique_values(games, "GameType")
min_date = games["DateTime"].min().date()
max_date = games["DateTime"].max().date()
available_player_rows = expand_individual_players(games)

with st.sidebar:
    if st.button("Clear all filters", use_container_width=True):
        for state_key in FILTER_KEYS.values():
            st.session_state[state_key] = [SELECT_ALL]
            st.session_state[f"{state_key}_select_all_active"] = True
        for state_key in (FILTER_KEYS["players"], FILTER_KEYS["opponents"]):
            st.session_state[state_key] = []
            st.session_state[f"{state_key}_select_all_active"] = False
        st.session_state[EXCLUDE_OPPONENTS_KEY] = False
        st.session_state[DATE_RANGE_KEY] = (min_date, max_date)
        st.session_state[TIME_PERIOD_KEY] = "Monthly"

    selected_players = multiselect(
        "Player(s)",
        unique_values(available_player_rows, "Player"),
        FILTER_KEYS["players"],
        placeholder="Search players...",
        include_select_all=False,
    )
    opponent_context = available_player_rows[
        available_player_rows["Player"].isin(selected_players)
    ]
    opponent_names = unique_values(
        pd.concat(
            [opponent_context["Opponent1"], opponent_context["Opponent2"]],
            ignore_index=True,
        ).to_frame(name="Opponent"),
        "Opponent",
    )
    exclude_opponents = st.checkbox(
        "Exclude selected opponents",
        key=EXCLUDE_OPPONENTS_KEY,
    )
    selected_opponents = multiselect(
        "Opponent(s) to exclude" if exclude_opponents else "Opponent(s)",
        opponent_names,
        FILTER_KEYS["opponents"],
        placeholder="Search opponents...",
        include_select_all=False,
    )
    selected_game_types = multiselect(
        "GameType",
        available_game_types,
        FILTER_KEYS["game_types"],
    )
    time_period = st.selectbox(
        "Time Period",
        ["Monthly", "By Session"],
        key=TIME_PERIOD_KEY,
    )
    selected_date_range = st.date_input(
        "DateTime",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        format="YYYY-MM-DD",
        key=DATE_RANGE_KEY,
    )

filtered = games[games["GameType"].isin(selected_game_types)]
filtered = filter_date_range(filtered, selected_date_range)
player_games = expand_individual_players(filtered)
player_games = player_games[player_games["Player"].isin(selected_players)]
if exclude_opponents:
    excluded_opponents = selected_values(FILTER_KEYS["opponents"])
    opponent_mask = ~player_games["Opponent1"].isin(
        excluded_opponents
    ) & ~player_games["Opponent2"].isin(excluded_opponents)
else:
    opponent_mask = player_games["Opponent1"].isin(
        selected_opponents
    ) | player_games["Opponent2"].isin(selected_opponents)
player_games = player_games[opponent_mask]

render_win_rate_chart(
    player_games,
    series_column="Player",
    series_title="Player",
    time_period=time_period,
    key="win_rates_line_chart",
)
