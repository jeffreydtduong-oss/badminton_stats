import altair as alt
import streamlit as st


TIME_PERIOD_KEY = "margin_over_time_period"
GAME_TYPE_KEY = "margin_over_time_game_type"
DATA_POINTS_KEY = "margin_over_time_data_points"


st.title("Margin over Time")

games = st.session_state["games"].copy()
if games.empty:
    st.info("No games are available.")
    st.stop()

with st.sidebar:
    time_period = st.selectbox(
        "Time",
        ["By Session", "Month Year"],
        key=TIME_PERIOD_KEY,
    )
    game_type = st.selectbox(
        "GameType",
        ["Doubles", "Singles"],
        key=GAME_TYPE_KEY,
    )

filtered_games = games[games["GameType"].eq(game_type)].drop_duplicates(
    subset=["GameKey"]
)
if time_period == "By Session":
    period_games = (
        filtered_games.groupby("Session Key", sort=False)["DateTime"]
        .min()
        .sort_values(kind="stable")
    )
    period_column = "Session Key"
    period_order = period_games.index.tolist()
    filtered_games["Period"] = filtered_games["Session Key"]
    x_title = "Session Key"
else:
    filtered_games["Period"] = filtered_games["DateTime"].dt.strftime(
        "%b %Y"
    )
    period_order = (
        filtered_games[["Period", "DateTime"]]
        .drop_duplicates()
        .sort_values("DateTime", kind="stable")["Period"]
        .drop_duplicates()
        .tolist()
    )
    period_column = "Period"
    x_title = "Month Year"

if not period_order:
    st.info(f"No {game_type.lower()} games are available.")
    st.stop()

with st.sidebar:
    max_data_points = len(period_order)
    data_points_key_value = min(
        int(st.session_state.get(DATA_POINTS_KEY, 10)),
        max_data_points,
    )
    last_data_points = st.slider(
        "Last N data points",
        min_value=1,
        max_value=max_data_points,
        value=data_points_key_value,
        key=DATA_POINTS_KEY,
    )

margin_denominator = filtered_games["WinningPoints"] - 2
filtered_games["Margin"] = (
    (filtered_games["PointDifferential"].abs() - 2) / margin_denominator
).where(margin_denominator.ne(0))
margin_by_period = (
    filtered_games.groupby(period_column, sort=False)
    .agg(
        Margin=("Margin", "mean"),
        Games=("GameKey", "nunique"),
    )
    .reindex(period_order)
    .dropna(subset=["Margin"])
    .tail(last_data_points)
    .rename_axis("Period")
    .reset_index()
)

if margin_by_period.empty:
    st.info("No valid margin values are available for the selected games.")
    st.stop()

base = alt.Chart(margin_by_period).encode(
    x=alt.X(
        "Period:N",
        sort=margin_by_period["Period"].tolist(),
        title=x_title,
        axis=alt.Axis(labelAngle=-35),
    ),
    y=alt.Y("Margin:Q", title="Margin"),
)
chart = (
    alt.layer(
        base.mark_line(point=True, interpolate="monotone").encode(
            tooltip=[
                alt.Tooltip("Period:N", title=x_title),
                alt.Tooltip("Margin:Q", title="Margin", format=".2f"),
                alt.Tooltip("Games:Q", title="Games"),
            ],
        ),
        base.mark_text(dy=-12, fontSize=11).encode(
            text=alt.Text("Margin:Q", format=".2f"),
        ),
    )
    .properties(height=380)
)
st.altair_chart(chart, use_container_width=True, key="margin_over_time_chart")
