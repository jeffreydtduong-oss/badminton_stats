import os
from pathlib import Path
from typing import Any

import gspread
import streamlit as st
from google.auth.exceptions import GoogleAuthError
from streamlit.errors import StreamlitSecretNotFoundError

from badminton_stats.data import (
    DEFAULT_DATA_DIRECTORY,
    load_game_history,
    normalize_game_history,
)
from badminton_stats.google_sheets import load_game_history_from_sheet


@st.cache_data(show_spinner=False)
def get_normalized_games(directory: str):
    source_games, _, _ = load_game_history(Path(directory))
    return normalize_game_history(source_games)


@st.cache_data(ttl=300, show_spinner=False)
def get_normalized_sheet_games(
    spreadsheet_id: str,
    credentials_info: dict[str, Any],
):
    source_games = load_game_history_from_sheet(
        spreadsheet_id,
        credentials_info,
    )
    return normalize_game_history(source_games)


st.set_page_config(page_title="Badminton Stats", layout="wide")

try:
    try:
        secrets = st.secrets.to_dict()
    except StreamlitSecretNotFoundError:
        secrets = {}

    has_sheet_secrets = "google_sheets" in secrets
    has_credentials_secrets = "gcp_service_account" in secrets
    if has_sheet_secrets or has_credentials_secrets:
        if not has_sheet_secrets or not has_credentials_secrets:
            raise ValueError(
                "Configure both [google_sheets] and [gcp_service_account] "
                "in Streamlit secrets."
            )
        spreadsheet_id = secrets["google_sheets"].get("spreadsheet_id")
        if not spreadsheet_id:
            raise ValueError(
                "Streamlit secrets [google_sheets] must define spreadsheet_id."
            )
        credentials_info = dict(secrets["gcp_service_account"])
    else:
        spreadsheet_id = os.environ.get("BADMINTON_STATS_SPREADSHEET_ID")
        credentials_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if spreadsheet_id or credentials_file:
            if not spreadsheet_id or not credentials_file:
                raise ValueError(
                    "Set both BADMINTON_STATS_SPREADSHEET_ID and "
                    "GOOGLE_APPLICATION_CREDENTIALS to use Google Sheets."
                )
            import json

            with Path(credentials_file).open(encoding="utf-8") as file:
                credentials_info = json.load(file)
        else:
            spreadsheet_id = ""
            credentials_info = {}

    if spreadsheet_id:
        if not isinstance(credentials_info, dict) or not credentials_info:
            raise ValueError(
                "Google Sheets is configured, but service-account credentials "
                "are missing. Configure Streamlit secrets or "
                "GOOGLE_APPLICATION_CREDENTIALS."
            )
        games = get_normalized_sheet_games(spreadsheet_id, credentials_info)
    else:
        games = get_normalized_games(str(DEFAULT_DATA_DIRECTORY))
except (
    OSError,
    ValueError,
    GoogleAuthError,
    gspread.exceptions.GSpreadException,
) as error:
    st.error(f"Could not load game history: {error}")
    st.stop()

if st.sidebar.button("Refresh game data"):
    st.cache_data.clear()
    st.rerun()

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
