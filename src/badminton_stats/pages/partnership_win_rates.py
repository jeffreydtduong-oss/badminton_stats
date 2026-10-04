import streamlit as st

from badminton_stats.pages.trend_utils import (
    filter_date_range,
    multiselect,
    render_win_rate_chart,
    selected_values,
    unique_values,
)


PAIR_KEY = "partnership_win_rates_pairs"
OPPONENT_KEY = "partnership_win_rates_opponents"
DATE_RANGE_KEY = "partnership_win_rates_date_range"
TIME_PERIOD_KEY = "partnership_win_rates_time_period"
EXCLUDE_OPPONENTS_KEY = "partnership_win_rates_exclude_opponents"


st.title("Partnership Win Rates over Time")

games = st.session_state["games"].copy()
if games.empty:
    st.info("No games are available.")
    st.stop()

doubles_games = games[games["GameType"].eq("Doubles")]
if doubles_games.empty:
    st.info("No doubles games are available.")
    st.stop()
min_date = doubles_games["DateTime"].min().date()
max_date = doubles_games["DateTime"].max().date()

with st.sidebar:
    if st.button("Clear all filters", use_container_width=True):
        st.session_state[PAIR_KEY] = []
        st.session_state[f"{PAIR_KEY}_select_all_active"] = False
        st.session_state[OPPONENT_KEY] = []
        st.session_state[f"{OPPONENT_KEY}_select_all_active"] = False
        st.session_state[EXCLUDE_OPPONENTS_KEY] = False
        st.session_state[DATE_RANGE_KEY] = (min_date, max_date)
        st.session_state[TIME_PERIOD_KEY] = "Monthly"

    selected_pairs = multiselect(
        "Doubles Pair",
        unique_values(doubles_games, "TeamCanonical"),
        PAIR_KEY,
        placeholder="Search doubles pairs...",
        include_select_all=False,
    )
    opponent_context = doubles_games[
        doubles_games["TeamCanonical"].isin(selected_pairs)
    ]
    exclude_opponents = st.checkbox(
        "Exclude selected opponents",
        key=EXCLUDE_OPPONENTS_KEY,
    )
    selected_opponents = multiselect(
        "Opponent(s) to exclude" if exclude_opponents else "Opponent(s)",
        unique_values(opponent_context, "OpponentCanonical"),
        OPPONENT_KEY,
        placeholder="Search opponents...",
        include_select_all=False,
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

filtered = filter_date_range(doubles_games, selected_date_range)
filtered = filtered[filtered["TeamCanonical"].isin(selected_pairs)]
if exclude_opponents:
    excluded_opponents = selected_values(OPPONENT_KEY)
    filtered = filtered[
        ~filtered["OpponentCanonical"].isin(excluded_opponents)
    ]
else:
    filtered = filtered[
        filtered["OpponentCanonical"].isin(selected_opponents)
    ]

render_win_rate_chart(
    filtered,
    series_column="TeamCanonical",
    series_title="Doubles Pair",
    time_period=time_period,
    key="partnership_win_rates_line_chart",
)
