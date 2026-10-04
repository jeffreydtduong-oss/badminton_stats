from typing import Optional

import altair as alt
import pandas as pd
import streamlit as st


SELECT_ALL = "__trend_select_all__"


def unique_values(frame: pd.DataFrame, column: str) -> list[str]:
    return sorted(frame[column].dropna().astype(str).unique().tolist())


def multiselect(
    label: str,
    options: list[str],
    key: str,
    placeholder: Optional[str] = None,
    include_select_all: bool = True,
) -> list[str]:
    previous_key = f"{key}_select_all_active"
    valid_options = set(options)

    if key not in st.session_state:
        st.session_state[key] = [SELECT_ALL] if include_select_all else []
        st.session_state[previous_key] = include_select_all
    else:
        current = st.session_state[key]
        st.session_state[key] = [
            value
            for value in current
            if (include_select_all and value == SELECT_ALL)
            or value in valid_options
        ]

    def on_change() -> None:
        selected = st.session_state[key]
        had_select_all = st.session_state.get(previous_key, False)
        if include_select_all and SELECT_ALL in selected and len(selected) > 1:
            if had_select_all:
                selected = [value for value in selected if value != SELECT_ALL]
            else:
                selected = [SELECT_ALL]
            st.session_state[key] = selected
        st.session_state[previous_key] = SELECT_ALL in selected

    selected = st.multiselect(
        label,
        options=[SELECT_ALL, *options] if include_select_all else options,
        key=key,
        format_func=lambda value: (
            "Select all"
            if include_select_all and value == SELECT_ALL
            else value
        ),
        on_change=on_change,
        placeholder=placeholder,
    )
    st.session_state[previous_key] = SELECT_ALL in selected
    if not selected:
        return options
    if include_select_all and SELECT_ALL in selected:
        return options
    return [value for value in selected if value in valid_options]


def filter_date_range(
    frame: pd.DataFrame, date_range: object
) -> pd.DataFrame:
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        return frame[
            frame["DateTime"].dt.date.between(start_date, end_date)
        ]
    return frame


def expand_individual_players(games: pd.DataFrame) -> pd.DataFrame:
    player_rows = pd.concat(
        [
            games.assign(Player=games[column])
            for column in ("Player1", "Player2")
        ],
        ignore_index=True,
    )
    return player_rows.dropna(subset=["Player"]).drop_duplicates(
        subset=["GameKey", "Player"],
        keep="first",
    )


def render_win_rate_chart(
    games: pd.DataFrame,
    series_column: str,
    series_title: str,
    time_period: str,
    key: str,
) -> None:
    if games.empty:
        st.info("No games are available for the selected filters.")
        return

    plot_games = games.copy()
    if time_period == "Monthly":
        plot_games["Period"] = plot_games["DateTime"].dt.strftime("%Y-%m")
        period_order = sorted(plot_games["Period"].unique().tolist())
        x_title = "Month Year"
    else:
        period_order = (
            plot_games.groupby("Session Key")["DateTime"]
            .min()
            .sort_values(kind="stable")
            .index.tolist()
        )
        plot_games["Period"] = plot_games["Session Key"]
        x_title = "Session Key"

    plot_games["IsWin"] = plot_games["Result"].eq("Won")
    chart_data = (
        plot_games.groupby([series_column, "Period"], sort=False)
        .agg(
            WinRate=("IsWin", "mean"),
            Games=("GameKey", "nunique"),
        )
        .reset_index()
        .rename(columns={series_column: "Series"})
    )

    base = alt.Chart(chart_data).encode(
        x=alt.X(
            "Period:N",
            sort=period_order,
            title=x_title,
            axis=alt.Axis(labelAngle=-35),
        ),
        y=alt.Y(
            "WinRate:Q",
            title="Win Rate",
            scale=alt.Scale(domain=[0, 1]),
            axis=alt.Axis(format="%"),
        ),
        color=alt.Color("Series:N", title=series_title),
    )
    chart = alt.layer(
        base.mark_line(interpolate="monotone", point=True).encode(
            tooltip=[
                alt.Tooltip("Series:N", title=series_title),
                alt.Tooltip("Period:N", title=x_title),
                alt.Tooltip("WinRate:Q", title="Win Rate", format=".1%"),
                alt.Tooltip("Games:Q", title="Games"),
            ],
        ),
        base.mark_text(dy=-12, fontSize=11).encode(
            text=alt.Text("WinRate:Q", format=".0%"),
        ),
    ).properties(height=380)
    st.altair_chart(chart, use_container_width=True, key=key)


def selected_values(key: str) -> list[str]:
    selected = st.session_state.get(key, [])
    return [value for value in selected if value != SELECT_ALL]
