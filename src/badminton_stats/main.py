from pathlib import Path

import streamlit as st

from badminton_stats.data import load_game_history, normalize_game_history


DEFAULT_DATA_DIRECTORY = Path(r"E:\Desktop\Badminton apps backup\Stats")


@st.cache_data(show_spinner=False)
def get_normalized_games(directory: str):
    source_games, _, _ = load_game_history(Path(directory))
    return normalize_game_history(source_games)


st.set_page_config(page_title="Badminton Stats", layout="wide")

try:
    games = get_normalized_games(str(DEFAULT_DATA_DIRECTORY))
except (OSError, ValueError) as error:
    st.error(f"Could not load game history: {error}")
    st.stop()

st.session_state["games"] = games

page = st.navigation(
    {
        "Matches": [
            st.Page(
                "pages/game_history.py",
                title="Game History & Matchups",
                default=True,
            ),
            st.Page("pages/leaderboard.py", title="Leaderboard"),
        ],
        "Trends": [
            st.Page("pages/win_rates.py", title="Win Rates over Time"),
            st.Page(
                "pages/partnership_win_rates.py",
                title="Partnership Win Rates over Time",
            ),
            st.Page("pages/margin_over_time.py", title="Margin over Time"),
        ],
    }
)
page.run()
