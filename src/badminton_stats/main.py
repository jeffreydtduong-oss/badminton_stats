from pathlib import Path

import streamlit as st

from badminton_stats.data import load_game_history


DEFAULT_DATA_DIRECTORY = Path(r"E:\Desktop\Badminton apps backup\Stats")

st.set_page_config(page_title="Badminton Stats", layout="wide")
st.title("Badminton Stats")

data_directory = Path(
    st.text_input("Data folder", value=str(DEFAULT_DATA_DIRECTORY))
).expanduser()

if not data_directory.is_dir():
    st.error(f"Data folder not found: {data_directory}")
    st.stop()

try:
    games, files, duplicates_removed = load_game_history(data_directory)
except (OSError, ValueError) as error:
    st.error(f"Could not load game history: {error}")
    st.stop()

st.caption(
    f"Loaded {len(games):,} games from {len(files)} files in "
    f"`{data_directory}`."
)
if duplicates_removed:
    st.caption(f"Removed {duplicates_removed:,} exact duplicate rows.")

with st.expander("Source files"):
    for file in files:
        st.write(file.name)

st.dataframe(games, width="stretch", hide_index=True)
