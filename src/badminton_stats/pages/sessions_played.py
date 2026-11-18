import altair as alt
import pandas as pd
import streamlit as st

from badminton_stats.filter_state import (
    render_date_range_inputs,
    render_searchable_multiselect,
)
from badminton_stats.pages.trend_utils import (
    SELECT_ALL,
    filter_date_range,
    multiselect,
    style_trend_chart,
)


MONTH_FILTER_KEY = "sessions_played_months"
GAME_TYPE_FILTER_KEY = "sessions_played_game_types"
PLAYER_FILTER_KEY = "sessions_played_players"
DATE_RANGE_KEY = "sessions_played_date_range"
FILTER_SIGNATURE_KEY = "sessions_played_filter_signature"
LEADERBOARD_KEY = "sessions_played_leaderboard"
DETAIL_PLAYER_KEY = "sessions_played_detail_player"


st.title("Session Leaderboard")

games = st.session_state["games"].copy()
if games.empty:
    st.info("No games are available.")
    st.stop()

games["Month Year"] = games["DateTime"].dt.strftime("%Y-%m")
available_months = sorted(
    games["Month Year"].dropna().unique().tolist(),
    reverse=True,
)
available_game_types = sorted(
    games["GameType"].dropna().astype(str).unique().tolist()
)
min_date = games["DateTime"].min().date()
max_date = games["DateTime"].max().date()

with st.sidebar:
    if st.button("Clear all filters", width="stretch"):
        st.session_state[MONTH_FILTER_KEY] = [SELECT_ALL]
        st.session_state[f"{MONTH_FILTER_KEY}_select_all_active"] = True
        st.session_state[GAME_TYPE_FILTER_KEY] = [SELECT_ALL]
        st.session_state[f"{GAME_TYPE_FILTER_KEY}_select_all_active"] = True
        st.session_state[PLAYER_FILTER_KEY] = [SELECT_ALL]
        st.session_state[f"{PLAYER_FILTER_KEY}_all"] = True
        st.session_state[f"{PLAYER_FILTER_KEY}_search"] = ""
        st.session_state[DATE_RANGE_KEY] = (min_date, max_date)
        st.session_state.pop(DETAIL_PLAYER_KEY, None)
        st.session_state.pop(LEADERBOARD_KEY, None)

    selected_game_types = multiselect(
        "Game Type",
        available_game_types,
        key=GAME_TYPE_FILTER_KEY,
    )
    selected_months = multiselect(
        "Month Year",
        available_months,
        key=MONTH_FILTER_KEY,
    )
    selected_date_range = render_date_range_inputs(
        DATE_RANGE_KEY,
        DATE_RANGE_KEY,
        (min_date, max_date),
        min_date,
        max_date,
    )
    filtered_games = games[
        games["GameType"].isin(selected_game_types)
        & games["Month Year"].isin(selected_months)
    ]
    filtered_games = filter_date_range(
        filtered_games,
        selected_date_range,
    )
    player_names = sorted(
        pd.concat(
            [filtered_games["Player1"], filtered_games["Player2"]],
            ignore_index=True,
        )
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )
    selected_players = render_searchable_multiselect(
        "Player",
        player_names,
        PLAYER_FILTER_KEY,
        SELECT_ALL,
    )

filter_signature = repr(
    (
        tuple(selected_game_types),
        tuple(selected_months),
        selected_date_range,
        tuple(selected_players),
    )
)
if st.session_state.get(FILTER_SIGNATURE_KEY) != filter_signature:
    st.session_state.pop(DETAIL_PLAYER_KEY, None)
    st.session_state.pop(LEADERBOARD_KEY, None)
    st.session_state[FILTER_SIGNATURE_KEY] = filter_signature

player_games = pd.concat(
    [
        filtered_games.assign(Player=filtered_games["Player1"]),
        filtered_games.assign(Player=filtered_games["Player2"]),
    ],
    ignore_index=True,
)
player_games = player_games.dropna(subset=["Player"]).drop_duplicates(
    subset=["Player", "DateTime"],
)
player_games = player_games[player_games["Player"].isin(selected_players)]

leaderboard = (
    player_games.groupby("Player", sort=False)
    .agg(
        **{
            "Sessions Played": ("Session Key", "nunique"),
            "Games Played": ("DateTime", "nunique"),
        }
    )
    .reset_index()
    .sort_values(
        ["Sessions Played", "Games Played", "Player"],
        ascending=[False, False, True],
        kind="stable",
    )
    .reset_index(drop=True)
)

if leaderboard.empty:
    st.info("No games match the selected filters.")
    st.stop()

selected_player = st.session_state.get(DETAIL_PLAYER_KEY)
if selected_player is not None:
    if st.button("Back to leaderboard"):
        st.session_state.pop(DETAIL_PLAYER_KEY, None)
        st.session_state.pop(LEADERBOARD_KEY, None)
        st.rerun()
    st.subheader(f"Sessions for {selected_player}")
    selected_games = player_games[player_games["Player"].eq(selected_player)]
    session_summary = (
        selected_games.groupby("Session Key", sort=False)
        .agg(
            **{
                "Session ID": ("Session ID", "first"),
                "Games Played": ("DateTime", "nunique"),
            }
        )
        .sort_values("Session ID", ascending=False, kind="stable")
        .reset_index()
    )
    sessions_column, games_column = st.columns(2)
    with sessions_column:
        st.metric(
            "Sessions Played",
            f"{session_summary['Session Key'].nunique():,}",
        )
    with games_column:
        st.metric(
            "Games Played",
            f"{session_summary['Games Played'].sum():,}",
        )
    st.dataframe(
        session_summary[["Session Key", "Games Played"]],
        hide_index=True,
        width="stretch",
    )
    session_summary["Month Year"] = pd.to_datetime(
        session_summary["Session Key"].str.slice(0, 10)
    ).dt.strftime("%Y-%m")
    monthly_summary = (
        session_summary.groupby("Month Year", sort=True)
        .agg(
            **{
                "Sessions Played": ("Session Key", "nunique"),
                "Games Played": ("Games Played", "sum"),
            }
        )
        .reset_index()
    )
    with st.expander("Sessions by month"):
        st.caption(
            "Each session is assigned to the month shown in its Session Key. "
            "Hover over a point to see its games played."
        )
        month_order = monthly_summary["Month Year"].tolist()
        chart_base = alt.Chart(monthly_summary).encode(
            x=alt.X(
                "Month Year:N",
                sort=month_order,
                title="Month Year",
                axis=alt.Axis(labelAngle=-35),
            ),
            y=alt.Y(
                "Sessions Played:Q",
                title="Sessions Played",
                axis=alt.Axis(format=",.0f"),
            ),
        )
        chart = style_trend_chart(
            alt.layer(
                chart_base.mark_line(
                    color="#174C3C",
                    interpolate="monotone",
                    point=True,
                ).encode(
                    tooltip=[
                        alt.Tooltip("Month Year:N", title="Month Year"),
                        alt.Tooltip(
                            "Sessions Played:Q",
                            title="Sessions Played",
                            format=",.0f",
                        ),
                        alt.Tooltip(
                            "Games Played:Q",
                            title="Games Played",
                            format=",.0f",
                        ),
                    ],
                ),
                chart_base.mark_text(
                    color="#31483C",
                    dy=-12,
                    fontSize=11,
                ).encode(
                    text=alt.Text(
                        "Sessions Played:Q",
                        format=",.0f",
                    ),
                ),
            ).properties(height=300)
        )
        st.altair_chart(
            chart,
            width="stretch",
            key="sessions_played_monthly_chart",
        )
    st.stop()

st.caption("Select a player row to see their sessions and games played.")
selection = st.dataframe(
    leaderboard,
    hide_index=True,
    width="stretch",
    on_select="rerun",
    selection_mode="single-row",
    key=LEADERBOARD_KEY,
)
if isinstance(selection, dict):
    selected_rows = selection.get("selection", {}).get("rows", [])
else:
    selected_rows = selection.selection.rows
if selected_rows:
    st.session_state[DETAIL_PLAYER_KEY] = str(
        leaderboard.iloc[selected_rows[0]]["Player"]
    )
    st.rerun()
