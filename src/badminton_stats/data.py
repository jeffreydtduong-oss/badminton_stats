from pathlib import Path
from typing import Optional

import pandas as pd


def load_game_history(
    directory: Path,
) -> tuple[pd.DataFrame, list[Path], int]:
    files = sorted(directory.glob("*game_history*.csv"))
    if not files:
        raise FileNotFoundError(
            f"No CSV files matching '*game_history*.csv' in {directory}"
        )

    frames: list[pd.DataFrame] = []
    columns: Optional[list[str]] = None

    for file in files:
        frame = pd.read_csv(file)
        if columns is None:
            columns = list(frame.columns)
        elif set(frame.columns) != set(columns):
            missing = sorted(set(columns) - set(frame.columns))
            unexpected = sorted(set(frame.columns) - set(columns))
            raise ValueError(
                f"Incompatible columns in {file.name}; "
                f"missing: {missing}, unexpected: {unexpected}"
            )
        frames.append(frame.reindex(columns=columns))

    combined = pd.concat(frames, ignore_index=True)
    duplicates_removed = int(combined.duplicated().sum())
    combined = combined.drop_duplicates(ignore_index=True)
    return combined, files, duplicates_removed
