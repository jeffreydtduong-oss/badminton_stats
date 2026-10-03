#TO DO: donut chart still not updating numbers based on filters.. sometimes it works
#TO DO: margin tooltip is too crowded, also doesn't show up on field name only the records in column
#TO DO: add cross filter..

from typing import Optional

import pandas as pd
import streamlit as st


SELECT_ALL = "__select_all__"
SELECT_ALL_LABEL = "Select all"
FILTER_KEYS = {
    "game_types": "game_history_game_types",
    "sessions": "game_history_sessions",
    "months": "game_history_months",
    "players": "game_history_players",
    "opponents": "game_history_opponents",
}
DATE_RANGE_KEY = "game_history_date_range"
REMOVE_DOUBLE_COUNTING_KEY = "game_history_remove_double_counting"
TABLE_PAGE_KEY = "game_history_table_page"
TABLE_PAGE_SIZE = 100
MARGIN_HELP = (
    "Margin of 0 indicates close games (e.g., 21-19, 15-13). "
    "Margin of 1 indicates blowout scores (e.g., 21-0, 15-0)."
)


def _unique_values(frame: pd.DataFrame, column: str) -> list[str]:
    return sorted(frame[column].dropna().astype(str).unique().tolist())


def _on_multiselect_change(key: str) -> None:
    previous_key = f"{key}_select_all_active"
    choices = st.session_state[key]
    had_select_all = st.session_state.get(previous_key, False)

    if SELECT_ALL in choices and len(choices) > 1:
        if had_select_all:
            choices = [choice for choice in choices if choice != SELECT_ALL]
        else:
            choices = [SELECT_ALL]
        st.session_state[key] = choices

    st.session_state[previous_key] = SELECT_ALL in choices


def _multiselect(
    label: str,
    options: list[str],
    key: str,
    default_all: bool = True,
    default_values: Optional[list[str]] = None,
) -> list[str]:
    state_key = FILTER_KEYS[key]
    previous_key = f"{state_key}_select_all_active"
    valid_options = set(options)

    if state_key not in st.session_state:
        if default_all:
            st.session_state[state_key] = [SELECT_ALL]
        else:
            st.session_state[state_key] = default_values or []
        st.session_state[previous_key] = default_all
    else:
        current = st.session_state[state_key]
        if SELECT_ALL not in current:
            current = [value for value in current if value in valid_options]
            st.session_state[state_key] = current

    selected = st.multiselect(
        label,
        options=[SELECT_ALL, *options],
        key=state_key,
        format_func=lambda value: SELECT_ALL_LABEL if value == SELECT_ALL else value,
        on_change=_on_multiselect_change,
        args=(state_key,),
    )
    st.session_state[previous_key] = SELECT_ALL in selected

    if not selected or SELECT_ALL in selected:
        return options
    return [value for value in selected if value in valid_options]


def _format_duration(seconds: object) -> str:
    if pd.isna(seconds):
        return "—"
    minutes, remaining_seconds = divmod(int(seconds), 60)
    return f"{minutes} mins and {remaining_seconds} secs"


st.title("Game History")

games = st.session_state["games"].copy()
if games.empty:
    st.info("No games are available.")
    st.stop()

games["Month Year"] = games["DateTime"].dt.strftime("%Y-%m")
available_months = sorted(
    games["Month Year"].dropna().unique().tolist(), reverse=True
)
available_game_types = _unique_values(games, "GameType")
available_sessions = sorted(_unique_values(games, "Session Key"), reverse=True)
min_date = games["DateTime"].min().date()
max_date = games["DateTime"].max().date()

with st.sidebar:
    if st.button("Clear all filters", use_container_width=True):
        for state_key in FILTER_KEYS.values():
            st.session_state[state_key] = [SELECT_ALL]
            st.session_state[f"{state_key}_select_all_active"] = True
        st.session_state[DATE_RANGE_KEY] = (min_date, max_date)
        st.session_state[REMOVE_DOUBLE_COUNTING_KEY] = False
        st.session_state[TABLE_PAGE_KEY] = 1

    remove_double_counting = st.checkbox(
        "Remove Double Counting",
        key=REMOVE_DOUBLE_COUNTING_KEY,
    )

    selected_game_types = _multiselect(
        "GameType",
        available_game_types,
        "game_types",
    )
    selected_sessions = _multiselect(
        "Session Key",
        available_sessions,
        "sessions",
        default_all=False,
        default_values=available_sessions[:1],
    )
    selected_months = _multiselect(
        "Month Year",
        available_months,
        "months",
    )
    selected_date_range = st.date_input(
        "DateTime",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        format="YYYY-MM-DD",
        key=DATE_RANGE_KEY,
    )

    player_context = games[
        games["GameType"].isin(selected_game_types)
        & games["Session Key"].isin(selected_sessions)
        & games["Month Year"].isin(selected_months)
    ]
    if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
        player_context = player_context[
            player_context["DateTime"].dt.date.between(start_date, end_date)
        ]
    if remove_double_counting:
        player_context = player_context[player_context["IsIndexEven"].eq(0)]

    selected_players = _multiselect(
        "Player(s)",
        _unique_values(player_context, "TeamCanonical"),
        "players",
    )
    opponent_context = player_context[
        player_context["TeamCanonical"].isin(selected_players)
    ]
    selected_opponents = _multiselect(
        "Opponent(s)",
        _unique_values(opponent_context, "OpponentCanonical"),
        "opponents",
    )

filtered = games[
    games["GameType"].isin(selected_game_types)
    & games["Session Key"].isin(selected_sessions)
    & games["Month Year"].isin(selected_months)
]
if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
    start_date, end_date = selected_date_range
    filtered = filtered[filtered["DateTime"].dt.date.between(start_date, end_date)]
if selected_players:
    filtered = filtered[filtered["TeamCanonical"].isin(selected_players)]
if selected_opponents:
    filtered = filtered[filtered["OpponentCanonical"].isin(selected_opponents)]
if remove_double_counting:
    filtered = filtered[filtered["IsIndexEven"].eq(0)]

st.metric("Games Played", f"{filtered['DateTime'].nunique():,}")

unique_games = filtered[filtered["IsIndexEven"].eq(0)]
good_side_wins = int(
    unique_games["TeamCanonical"].eq(unique_games["Winner Canonical"]).sum()
)
bad_side_wins = int(
    unique_games["OpponentCanonical"].eq(unique_games["Winner Canonical"]).sum()
)
total_side_wins = good_side_wins + bad_side_wins

st.subheader("Win Rate by Sides")
if total_side_wins:
    chart_data = pd.DataFrame(
        {
            "Side": ["Good side wins", "Bad side wins"],
            "Wins": [good_side_wins, bad_side_wins],
            "Win rate": [
                good_side_wins / total_side_wins,
                bad_side_wins / total_side_wins,
            ],
        }
    )
    donut_chart = {
        "width": 190,
        "height": 170,
        "layer": [
            {
                "mark": {"type": "arc", "innerRadius": 42, "outerRadius": 68},
                "encoding": {
                    "theta": {
                        "field": "Wins",
                        "type": "quantitative",
                        "stack": "normalize",
                    },
                    "order": {
                        "field": "Side",
                        "sort": ["Good side wins", "Bad side wins"],
                    },
                    "color": {
                        "field": "Side",
                        "type": "nominal",
                        "scale": {
                            "domain": ["Good side wins", "Bad side wins"],
                            "range": ["#2563eb", "#f97316"],
                        },
                        "legend": {
                            "title": None,
                            "orient": "bottom",
                            "direction": "horizontal",
                        },
                    },
                    "tooltip": [
                        {"field": "Side", "type": "nominal"},
                        {"field": "Wins", "type": "quantitative"},
                        {
                            "field": "Win rate",
                            "type": "quantitative",
                            "format": ".1%",
                        },
                    ],
                },
            },
            {
                "mark": {
                    "type": "text",
                    "radius": 54,
                    "fontSize": 11,
                    "fontWeight": "bold",
                },
                "encoding": {
                    "theta": {
                        "field": "Wins",
                        "type": "quantitative",
                        "stack": "normalize",
                    },
                    "order": {
                        "field": "Side",
                        "sort": ["Good side wins", "Bad side wins"],
                    },
                    "text": {
                        "field": "Win rate",
                        "type": "quantitative",
                        "format": ".1%",
                    },
                },
            },
        ],
        "view": {"stroke": None},
    }
    chart_column = st.columns([1, 2, 1])[1]
    with chart_column:
        st.vega_lite_chart(
            chart_data,
            spec=donut_chart,
            key="win_rate_by_sides",
            width=250,
            height=210,
        )
else:
    st.info("No wins are available for the selected filters.")

filtered = filtered.sort_values(
    "DateTime",
    ascending=False,
    kind="stable",
).reset_index(drop=True)
total_pages = max(1, (len(filtered) + TABLE_PAGE_SIZE - 1) // TABLE_PAGE_SIZE)
if TABLE_PAGE_KEY not in st.session_state:
    st.session_state[TABLE_PAGE_KEY] = 1
st.session_state[TABLE_PAGE_KEY] = min(
    max(1, st.session_state[TABLE_PAGE_KEY]),
    total_pages,
)
page_number = st.session_state[TABLE_PAGE_KEY]
page_start = (page_number - 1) * TABLE_PAGE_SIZE
page_games = filtered.iloc[page_start : page_start + TABLE_PAGE_SIZE]

previous_column, page_column, next_column = st.columns([1, 2, 1])
with previous_column:
    if st.button("Previous", disabled=page_number <= 1):
        st.session_state[TABLE_PAGE_KEY] = page_number - 1
        st.rerun()
with page_column:
    st.markdown(
        f"<div style='text-align: center'>Page {page_number} of {total_pages}</div>",
        unsafe_allow_html=True,
    )
with next_column:
    if st.button("Next", disabled=page_number >= total_pages):
        st.session_state[TABLE_PAGE_KEY] = page_number + 1
        st.rerun()

duration = page_games["GameDurationSeconds"].map(_format_duration)
denominator = page_games["WinningPoints"] - 2
margin = (
    (page_games["PointDifferential"].abs() - 2) / denominator
).where(denominator.ne(0))
table = pd.DataFrame(
    {
        "Time Completed": page_games["DateTime"].dt.strftime(
            "%a, %d %b %Y %I:%M:%S %p"
        ),
        "GameType": page_games["GameType"],
        "Winning Points": page_games["WinningPoints"],
        "TeamCanonical": page_games["TeamCanonical"],
        "Final Score": page_games["Final Score"],
        "OpponentCanonical": page_games["OpponentCanonical"],
        "Duration": duration,
        "Margin": margin,
    }
)
table.index = pd.RangeIndex(
    len(filtered) - page_start,
    len(filtered) - page_start - len(table),
    -1,
)
table = table.rename(columns={"Margin": "Margin ⓘ"})

winning_style = (
    "background-color: #dbeafe; color: #1d4ed8; font-weight: 600"
)
cell_styles = pd.DataFrame("", index=table.index, columns=table.columns)
team_won = page_games["Result"].eq("Won").to_numpy()
cell_styles.loc[team_won, "TeamCanonical"] = winning_style
cell_styles.loc[~team_won, "OpponentCanonical"] = winning_style


styled_table = (
    table.style.apply(lambda _: cell_styles, axis=None)
    .format({"Margin ⓘ": "{:.2f}"})
    .set_properties(**{"text-align": "center"})
    .set_table_styles(
        [{"selector": "th", "props": [("text-align", "center")]}]
    )
    .set_tooltips(
        pd.DataFrame("", index=table.index, columns=table.columns).assign(
            **{"Margin ⓘ": [MARGIN_HELP] * len(table)}
        )
    )
)

st.table(styled_table)
