import hashlib
import html
import math
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
TABLE_VIEW_KEY = "game_history_table_view"
MARGIN_HELP = "0 = close game; 1 = blowout."
OVERALL_STATS_TABLE_KEY_PREFIX = "game_history_overall_stats"


def _unique_values(frame: pd.DataFrame, column: str) -> list[str]:
    return sorted(frame[column].dropna().astype(str).unique().tolist())


def _change_table_page(delta: int) -> None:
    st.session_state[TABLE_PAGE_KEY] += delta


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
    placeholder: Optional[str] = None,
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
        placeholder=placeholder,
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


def _format_session_duration(seconds: int) -> str:
    hours, remaining_seconds = divmod(seconds, 3600)
    minutes = remaining_seconds // 60
    parts = []
    if hours:
        parts.append(f"{hours} {'hour' if hours == 1 else 'hours'}")
    if minutes or not hours:
        parts.append(f"{minutes} {'min' if minutes == 1 else 'mins'}")
    return " ".join(parts)


def _calculate_margin(frame: pd.DataFrame) -> pd.Series:
    denominator = frame["WinningPoints"] - 2
    return (
        (frame["PointDifferential"].abs() - 2) / denominator
    ).where(denominator.ne(0))


def _donut_chart_html(good_side_wins: int, bad_side_wins: int) -> str:
    total_wins = good_side_wins + bad_side_wins
    good_side_rate = good_side_wins / total_wins
    bad_side_rate = bad_side_wins / total_wins
    label_radius = 69
    good_mid_angle = -90 + 180 * good_side_rate
    bad_mid_angle = -90 + 360 * good_side_rate + 180 * bad_side_rate

    def percentage_label(rate: float, midpoint: float) -> str:
        if rate < 0.12:
            return ""
        angle = math.radians(midpoint)
        left = 85 + label_radius * math.cos(angle)
        top = 85 + label_radius * math.sin(angle)
        return (
            f'<span style="position:absolute;left:{left:.1f}px;'
            f'top:{top:.1f}px;transform:translate(-50%,-50%);'
            'color:#000000;font-size:12px;font-weight:700;'
            'text-shadow:0 1px 2px rgba(255,255,255,0.6);">'
            f"{rate:.0%}</span>"
        )

    arc_labels = (
        percentage_label(good_side_rate, good_mid_angle)
        + percentage_label(bad_side_rate, bad_mid_angle)
    )
    return f"""
        <div style="display:flex;align-items:center;justify-content:center;
                    gap:1.25rem;flex-wrap:wrap;">
          <div role="img"
               aria-label="Good side wins {good_side_rate:.1%};
                           Bad side wins {bad_side_rate:.1%}"
               style="position:relative;width:170px;height:170px;
                      border-radius:50%;
                      background:
                        radial-gradient(circle, #ffffff 0 54%, transparent 55%),
                        conic-gradient(
                          #2563eb 0 {good_side_rate:.4%},
                          #f97316 {good_side_rate:.4%} 100%);
                      display:grid;place-items:center;">
            {arc_labels}
          </div>
          <div style="display:grid;gap:0.5rem;font-size:0.875rem;">
            <div><span style="color:#2563eb">●</span>
                 Good side wins: {good_side_wins} ({good_side_rate:.1%})</div>
            <div><span style="color:#f97316">●</span>
                 Bad side wins: {bad_side_wins} ({bad_side_rate:.1%})</div>
          </div>
        </div>
    """


def _aggregate_stats(
    frame: pd.DataFrame, group_columns: list[str]
) -> pd.DataFrame:
    columns = [
        *group_columns,
        "Wins",
        "Losses",
        "Win Rate",
        "Wins Margin",
        "Losses Margin",
        "Total Margin",
        "Point +/- per game",
    ]
    if frame.empty:
        return pd.DataFrame(
            {
                column: pd.Series(
                    dtype=(
                        "string"
                        if column in group_columns
                        else "int64"
                        if column in {"Wins", "Losses"}
                        else "float64"
                    )
                )
                for column in columns
            }
        )

    games_with_margin = frame.assign(Margin=_calculate_margin(frame))
    grouped = games_with_margin.groupby(
        group_columns,
        dropna=False,
        sort=True,
    )
    stats = grouped.agg(
        TotalGames=("DateTime", "size"),
        **{
            "Total Margin": ("Margin", "mean"),
            "Point +/- per game": ("PointDifferential", "mean"),
        },
    )
    for result, count_column, margin_column in (
        ("Won", "Wins", "Wins Margin"),
        ("Lost", "Losses", "Losses Margin"),
    ):
        result_stats = (
            games_with_margin[games_with_margin["Result"].eq(result)]
            .groupby(group_columns, dropna=False, sort=True)
            .agg(
                **{
                    count_column: ("Result", "size"),
                    margin_column: ("Margin", "mean"),
                }
            )
        )
        stats = stats.join(result_stats)

    stats[["Wins", "Losses"]] = stats[["Wins", "Losses"]].fillna(0).astype(
        "int64"
    )
    stats["Win Rate"] = stats["Wins"] / stats["TotalGames"]
    return stats.reset_index().drop(columns="TotalGames")[columns]


st.title("Game History & Matchups")

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
remove_double_counting = st.session_state.get(
    REMOVE_DOUBLE_COUNTING_KEY, False
)

with st.sidebar:
    if st.button("Clear all filters", use_container_width=True):
        for state_key in FILTER_KEYS.values():
            st.session_state[state_key] = [SELECT_ALL]
            st.session_state[f"{state_key}_select_all_active"] = True
        st.session_state[DATE_RANGE_KEY] = (min_date, max_date)
        st.session_state[REMOVE_DOUBLE_COUNTING_KEY] = False
        st.session_state[TABLE_PAGE_KEY] = 1

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
        placeholder="Search players...",
    )
    opponent_context = player_context[
        player_context["TeamCanonical"].isin(selected_players)
    ]
    selected_opponents = _multiselect(
        "Opponent(s)",
        _unique_values(opponent_context, "OpponentCanonical"),
        "opponents",
        placeholder="Search opponents...",
    )
    remove_double_counting = st.checkbox(
        "Remove Double Counting",
        key=REMOVE_DOUBLE_COUNTING_KEY,
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

games_played_column, session_duration_column = st.columns(2)
with games_played_column:
    st.metric("Games Played", f"{filtered['DateTime'].nunique():,}")

session_selection = st.session_state[FILTER_KEYS["sessions"]]
session_duration = ""
if len(session_selection) == 1 and session_selection[0] != SELECT_ALL:
    session_games = games[
        games["Session Key"].eq(session_selection[0])
    ].sort_values("DateTime", kind="stable")
    if not session_games.empty:
        first_game = session_games.iloc[0]
        if pd.notna(first_game["GameDurationSeconds"]):
            session_seconds = int(
                (
                    session_games["DateTime"].iloc[-1]
                    - first_game["DateTime"]
                ).total_seconds()
                + first_game["GameDurationSeconds"]
            )
            session_duration = _format_session_duration(session_seconds)
with session_duration_column:
    st.metric("Session Duration", session_duration)

overall_stats = _aggregate_stats(filtered, ["TeamCanonical"]).rename(
    columns={"TeamCanonical": "Player(s)"}
)
overall_stats["_Games Played"] = overall_stats["Player(s)"].map(
    filtered["TeamCanonical"].value_counts()
)
overall_stats = overall_stats.sort_values(
    "_Games Played",
    ascending=False,
    kind="stable",
).drop(columns="_Games Played")
filter_signature = repr(
    (
        tuple(selected_game_types),
        tuple(selected_sessions),
        tuple(selected_months),
        tuple(selected_players),
        tuple(selected_opponents),
        selected_date_range,
        remove_double_counting,
    )
)
overall_stats_key = (
    f"{OVERALL_STATS_TABLE_KEY_PREFIX}_"
    f"{hashlib.sha256(filter_signature.encode()).hexdigest()[:12]}"
)

st.subheader("Overall Stats")
st.caption(
    "Select a row to quickly cross filter Head to Head Stats and Game History"
)
overall_selection = st.dataframe(
    overall_stats,
    column_config={
        "Player(s)": st.column_config.TextColumn(pinned=True),
        "Win Rate": st.column_config.NumberColumn(format="percent"),
        "Wins Margin": st.column_config.NumberColumn(format="%.2f"),
        "Losses Margin": st.column_config.NumberColumn(format="%.2f"),
        "Total Margin": st.column_config.NumberColumn(format="%.2f"),
        "Point +/- per game": st.column_config.NumberColumn(format="%.1f"),
    },
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    key=overall_stats_key,
)
if isinstance(overall_selection, dict):
    selected_rows = overall_selection.get("selection", {}).get("rows", [])
else:
    selected_rows = overall_selection.selection.rows
selected_player = (
    str(overall_stats.iloc[selected_rows[0]]["Player(s)"])
    if selected_rows and 0 <= selected_rows[0] < len(overall_stats)
    else None
)

head_to_head_games = filtered
if selected_player is not None:
    head_to_head_games = head_to_head_games[
        head_to_head_games["TeamCanonical"].eq(selected_player)
    ]
head_to_head_stats = _aggregate_stats(
    head_to_head_games,
    ["TeamCanonical", "OpponentCanonical"],
).rename(
    columns={
        "TeamCanonical": "Player(s)",
        "OpponentCanonical": "Opponent(s)",
        "Wins": "H2H Wins",
        "Losses": "H2H Losses",
        "Win Rate": "H2H Win Rate",
        "Wins Margin": "H2H Wins Margin",
        "Losses Margin": "H2H Losses Margin",
        "Total Margin": "H2H Total Margin",
    }
)

st.subheader("Head to Head Stats")
st.dataframe(
    head_to_head_stats,
    column_config={
        "Player(s)": st.column_config.TextColumn(pinned=True),
        "Opponent(s)": st.column_config.TextColumn(pinned=True),
        "H2H Win Rate": st.column_config.NumberColumn(format="percent"),
        "H2H Wins Margin": st.column_config.NumberColumn(format="%.2f"),
        "H2H Losses Margin": st.column_config.NumberColumn(format="%.2f"),
        "H2H Total Margin": st.column_config.NumberColumn(format="%.2f"),
        "Point +/- per game": st.column_config.NumberColumn(format="%.1f"),
    },
    hide_index=True,
    width="stretch",
)

if selected_player is not None:
    filtered = filtered[filtered["TeamCanonical"].eq(selected_player)]

player_filter_active = (
    selected_player is not None
    or SELECT_ALL not in st.session_state[FILTER_KEYS["players"]]
)
if player_filter_active:
    player_wins = filtered[filtered["Result"].eq("Won")]
    good_side_wins = int(player_wins["IsIndexEven"].eq(0).sum())
    bad_side_wins = int(player_wins["IsIndexEven"].eq(1).sum())
else:
    unique_games = filtered[filtered["IsIndexEven"].eq(0)]
    good_side_wins = int(
        unique_games["TeamCanonical"].eq(unique_games["Winner Canonical"]).sum()
    )
    bad_side_wins = int(
        unique_games["OpponentCanonical"].eq(unique_games["Winner Canonical"]).sum()
    )
total_side_wins = good_side_wins + bad_side_wins

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

table_view = st.radio(
    "Game History display",
    ["Table", "Compact cards"],
    horizontal=True,
    key=TABLE_VIEW_KEY,
)
previous_column, page_column, next_column = st.columns([1, 2, 1])
with previous_column:
    st.button(
        "Previous",
        disabled=page_number <= 1,
        on_click=_change_table_page,
        args=(-1,),
    )
with page_column:
    st.number_input(
        f"Page {page_number} of {total_pages}",
        min_value=1,
        max_value=total_pages,
        step=1,
        key=TABLE_PAGE_KEY,
    )
with next_column:
    st.button(
        "Next",
        disabled=page_number >= total_pages,
        on_click=_change_table_page,
        args=(1,),
    )

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
table.index.name = "Game Number"

winning_style = (
    "background-color: #dbeafe; color: #1d4ed8; font-weight: 600"
)
cell_styles = pd.DataFrame("", index=table.index, columns=table.columns)
team_won = page_games["Result"].eq("Won").to_numpy()
cell_styles.loc[team_won, "TeamCanonical"] = winning_style
cell_styles.loc[~team_won, "OpponentCanonical"] = winning_style


styled_table = (
    table.style.apply(lambda _: cell_styles, axis=None)
    .format({"Margin": "{:.2f}"})
    .set_properties(**{"text-align": "center"})
    .set_table_styles(
        [{"selector": "th", "props": [("text-align", "center")]}]
    )
)

st.subheader("Game History")
if table_view == "Table":
    st.dataframe(
        styled_table,
        column_config={
            "Margin": st.column_config.NumberColumn(
                help=MARGIN_HELP,
                format="%.2f",
            )
        },
        hide_index=False,
        width="stretch",
        height=min(700, 36 * (len(table) + 1) + 8),
    )
else:
    for row_position, (game_number, row) in enumerate(table.iterrows()):
        with st.container(border=True):
            st.markdown(
                f"**Game {game_number} · {row['Time Completed']}**"
            )
            team = html.escape(str(row["TeamCanonical"]))
            opponent = html.escape(str(row["OpponentCanonical"]))
            score = html.escape(str(row["Final Score"]))
            if team_won[row_position]:
                team = (
                    '<span style="color:#1d4ed8;font-weight:600">'
                    f"{team}</span>"
                )
            else:
                opponent = (
                    f'<span style="color:#1d4ed8;font-weight:600">'
                    f"{opponent}</span>"
                )
            st.html(f"{team} &nbsp; {score} &nbsp; {opponent}")
            st.caption(
                f"{row['GameType']} · {row['Winning Points']} winning points"
                f" · {row['Duration']} · Margin {row['Margin']:.2f}"
            )

st.subheader("Win Rate by Sides")
if total_side_wins:
    chart_column = st.columns([1, 2, 1])[1]
    with chart_column:
        st.html(
            _donut_chart_html(
                good_side_wins,
                bad_side_wins,
            )
        )
else:
    st.info("No wins are available for the selected filters.")
