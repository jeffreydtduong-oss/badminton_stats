from typing import Optional

import pandas as pd
import streamlit as st


SELECT_ALL = "__leaderboard_select_all__"
FILTER_KEYS = {
    "players": "leaderboard_players",
    "sessions": "leaderboard_sessions",
    "months": "leaderboard_months",
}
DATE_RANGE_KEY = "leaderboard_date_range"


def _unique_names(values: pd.Series) -> list[str]:
    return sorted(values.dropna().astype(str).unique().tolist())


def _on_multiselect_change(key: str) -> None:
    previous_key = f"{key}_select_all_active"
    selected = st.session_state[key]
    had_select_all = st.session_state.get(previous_key, False)

    if SELECT_ALL in selected and len(selected) > 1:
        selected = (
            [value for value in selected if value != SELECT_ALL]
            if had_select_all
            else [SELECT_ALL]
        )
        st.session_state[key] = selected

    st.session_state[previous_key] = SELECT_ALL in selected


def _multiselect(
    label: str,
    options: list[str],
    key: str,
    default_values: Optional[list[str]] = None,
    placeholder: Optional[str] = None,
) -> list[str]:
    state_key = FILTER_KEYS[key]
    previous_key = f"{state_key}_select_all_active"
    valid_options = set(options)

    if state_key not in st.session_state:
        st.session_state[state_key] = (
            [SELECT_ALL] if default_values is None else default_values
        )
        st.session_state[previous_key] = default_values is None
    else:
        current = st.session_state[state_key]
        if SELECT_ALL not in current:
            st.session_state[state_key] = [
                value for value in current if value in valid_options
            ]

    selected = st.multiselect(
        label,
        options=[SELECT_ALL, *options],
        key=state_key,
        format_func=lambda value: "Select all" if value == SELECT_ALL else value,
        on_change=_on_multiselect_change,
        args=(state_key,),
        placeholder=placeholder,
    )
    st.session_state[previous_key] = SELECT_ALL in selected
    if not selected or SELECT_ALL in selected:
        return options
    return [value for value in selected if value in valid_options]


def _player_rows(games: pd.DataFrame, game_type: str) -> pd.DataFrame:
    type_games = games[games["GameType"].eq(game_type)].copy()
    if game_type == "Doubles":
        player_rows = pd.concat(
            [
                type_games.assign(Player=type_games[column])
                for column in ("Player1", "Player2")
            ],
            ignore_index=True,
        )
    else:
        player_rows = type_games.assign(Player=type_games["Player1"])

    return player_rows.dropna(subset=["Player"]).drop_duplicates(
        subset=["GameKey", "Player"],
        keep="first",
    )


def _leaderboard_stats(games: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "Player",
        "Wins",
        "Losses",
        "Win Rate",
        "Wins Margin",
        "Losses Margin",
        "Total Margin",
        "Point +/- per game",
        "Win % on Good Side",
        "Win % on Bad Side",
    ]
    if games.empty:
        return pd.DataFrame(
            {
                column: pd.Series(
                    dtype="string" if column == "Player" else "float64"
                )
                for column in columns
            }
        )

    denominator = games["WinningPoints"] - 2
    games["Margin"] = (
        (games["PointDifferential"].abs() - 2) / denominator
    ).where(denominator.ne(0))
    games["IsWin"] = games["Result"].eq("Won")
    games["WinMargin"] = games["Margin"].where(games["IsWin"])
    games["LossMargin"] = games["Margin"].where(~games["IsWin"])
    games["GoodSideGame"] = games["IsIndexEven"].eq(0)
    games["BadSideGame"] = games["IsIndexEven"].eq(1)
    games["GoodSideWin"] = games["IsWin"] & games["GoodSideGame"]
    games["BadSideWin"] = games["IsWin"] & games["BadSideGame"]

    stats = games.groupby("Player", sort=True).agg(
        Wins=("IsWin", "sum"),
        Losses=("IsWin", lambda wins: (~wins).sum()),
        WinRate=("IsWin", "mean"),
        WinsMargin=("WinMargin", "mean"),
        LossesMargin=("LossMargin", "mean"),
        TotalMargin=("Margin", "mean"),
        PointDifference=("PointDifferential", "mean"),
        GamesPlayed=("GameKey", "size"),
        GoodSideGames=("GoodSideGame", "sum"),
        GoodSideWins=("GoodSideWin", "sum"),
        BadSideGames=("BadSideGame", "sum"),
        BadSideWins=("BadSideWin", "sum"),
    )
    stats["Win % on Good Side"] = (
        stats["GoodSideWins"] / stats["Wins"]
    ).where(stats["Wins"].ne(0))
    stats["Win % on Bad Side"] = (
        stats["BadSideWins"] / stats["Wins"]
    ).where(stats["Wins"].ne(0))

    stats = stats.reset_index().sort_values(
        "WinRate",
        ascending=False,
        kind="stable",
    )
    return stats.rename(
        columns={
            "WinRate": "Win Rate",
            "WinsMargin": "Wins Margin",
            "LossesMargin": "Losses Margin",
            "TotalMargin": "Total Margin",
            "PointDifference": "Point +/- per game",
        }
    )[columns]


st.title("Leaderboard")

games = st.session_state["games"].copy()
if games.empty:
    st.info("No games are available.")
    st.stop()

games["Month Year"] = games["DateTime"].dt.strftime("%Y-%m")
available_months = sorted(
    games["Month Year"].dropna().unique().tolist(),
    reverse=True,
)
available_sessions = sorted(
    games["Session Key"].dropna().astype(str).unique().tolist(),
    reverse=True,
)
min_date = games["DateTime"].min().date()
max_date = games["DateTime"].max().date()

with st.sidebar:
    if st.button("Clear all filters", use_container_width=True):
        for state_key in FILTER_KEYS.values():
            st.session_state[state_key] = [SELECT_ALL]
            st.session_state[f"{state_key}_select_all_active"] = True
        st.session_state[DATE_RANGE_KEY] = (min_date, max_date)

    selected_sessions = _multiselect(
        "Session Key",
        available_sessions,
        "sessions",
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
        games["Session Key"].isin(selected_sessions)
        & games["Month Year"].isin(selected_months)
    ]
    if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
        player_context = player_context[
            player_context["DateTime"].dt.date.between(start_date, end_date)
        ]
    player_names = _unique_names(
        pd.concat(
            [
                player_context["Player1"],
                player_context["Player2"],
            ],
            ignore_index=True,
        )
    )
    selected_players = _multiselect(
        "Player",
        player_names,
        "players",
        placeholder="Search players...",
    )

filtered = player_context.copy()

for game_type, title in (
    ("Doubles", "Doubles Leaderboard"),
    ("Singles", "Singles Leaderboard"),
):
    player_games = _player_rows(filtered, game_type)
    if selected_players:
        player_games = player_games[player_games["Player"].isin(selected_players)]

    stats = _leaderboard_stats(player_games)
    st.subheader(title)
    st.dataframe(
        stats,
        column_config={
            "Player": st.column_config.TextColumn(pinned=True),
            "Win Rate": st.column_config.NumberColumn(format="percent"),
            "Wins Margin": st.column_config.NumberColumn(format="%.2f"),
            "Losses Margin": st.column_config.NumberColumn(format="%.2f"),
            "Total Margin": st.column_config.NumberColumn(format="%.2f"),
            "Point +/- per game": st.column_config.NumberColumn(format="%.1f"),
            "Win % on Good Side": st.column_config.NumberColumn(
                format="percent"
            ),
            "Win % on Bad Side": st.column_config.NumberColumn(
                format="percent"
            ),
        },
        hide_index=True,
        width="stretch",
    )
