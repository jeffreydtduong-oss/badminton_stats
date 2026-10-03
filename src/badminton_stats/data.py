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
        if "Source File Name" in frame.columns:
            raise ValueError(
                f"Unexpected column 'Source File Name' in {file.name}"
            )
        frame = frame.reindex(columns=columns)
        frame.insert(0, "Source File Name", file.name)
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True)
    source_columns = columns or []
    duplicates_removed = int(combined.duplicated(subset=source_columns).sum())
    combined = combined.drop_duplicates(subset=source_columns, ignore_index=True)
    return combined, files, duplicates_removed


def normalize_game_history(games: pd.DataFrame) -> pd.DataFrame:
    required_columns = {
        "Timestamp",
        "DateTime",
        "GameType",
        "Team1Player1",
        "Team1Player2",
        "Team2Player1",
        "Team2Player2",
        "Team1Score",
        "Team2Score",
        "Winner",
        "WinningTeam",
        "GameDurationSeconds",
        "WinningPoints",
        "ScoreDifference",
    }
    missing = sorted(required_columns - set(games.columns))
    if missing:
        raise ValueError(f"Game history is missing required columns: {missing}")

    source = games.copy()
    if "Source File Name" not in source.columns:
        source["Source File Name"] = pd.NA

    source["DateTime"] = pd.to_datetime(source["DateTime"], errors="raise")
    if source["DateTime"].isna().any():
        raise ValueError("Game history contains missing DateTime values")
    if source["Timestamp"].isna().any():
        raise ValueError("Game history contains missing Timestamp values")
    invalid_winners = set(source["WinningTeam"].dropna().astype(str)) - {
        "Team1",
        "Team2",
    }
    if source["WinningTeam"].isna().any():
        invalid_winners.add("<missing>")
    if invalid_winners:
        raise ValueError(
            f"WinningTeam must contain only 'Team1' or 'Team2'; "
            f"found {sorted(invalid_winners)}"
        )
    source = source.drop_duplicates(subset=["DateTime"], keep="first").copy()

    for column in (
        "Team1Score",
        "Team2Score",
        "GameDurationSeconds",
        "WinningPoints",
        "ScoreDifference",
    ):
        source[column] = pd.to_numeric(source[column], errors="raise").astype(
            "Int64"
        )

    def canonical_team(
        game_type: object, player1: object, player2: object
    ) -> object:
        if game_type == "Doubles":
            players = [player for player in (player1, player2) if pd.notna(player)]
            return "/".join(sorted(str(player) for player in players))
        return player1

    source["Team1 Canonical"] = [
        canonical_team(game_type, player1, player2)
        for game_type, player1, player2 in zip(
            source["GameType"],
            source["Team1Player1"],
            source["Team1Player2"],
        )
    ]
    source["Team2 Canonical"] = [
        canonical_team(game_type, player1, player2)
        for game_type, player1, player2 in zip(
            source["GameType"],
            source["Team2Player1"],
            source["Team2Player2"],
        )
    ]
    source["Winner Canonical"] = [
        (
            team1 if winning_team == "Team1" else team2
        )
        if game_type == "Doubles"
        else winner
        for game_type, winning_team, team1, team2, winner in zip(
            source["GameType"],
            source["WinningTeam"],
            source["Team1 Canonical"],
            source["Team2 Canonical"],
            source["Winner"],
        )
    ]

    team1 = source[
        [
            "Timestamp",
            "DateTime",
            "GameType",
            "Team1Player1",
            "Team1Player2",
            "Team2Player1",
            "Team2Player2",
            "Team1Score",
            "Team2Score",
            "Winner",
            "WinningTeam",
            "GameDurationSeconds",
            "WinningPoints",
            "ScoreDifference",
            "Source File Name",
            "Team1 Canonical",
            "Team2 Canonical",
            "Winner Canonical",
        ]
    ].copy()
    team1["WinningTeam"] = team1["WinningTeam"].map(
        {"Team1": "Won", "Team2": "Lost"}
    )
    team1 = team1.rename(
        columns={
            "Team1Player1": "Player1",
            "Team1Player2": "Player2",
            "Team2Player1": "Opponent1",
            "Team2Player2": "Opponent2",
            "Team1Score": "TeamScore",
            "Team2Score": "OpponentScore",
            "WinningTeam": "Result",
            "Team1 Canonical": "TeamCanonical",
            "Team2 Canonical": "OpponentCanonical",
        }
    )

    team2 = source[
        [
            "Timestamp",
            "DateTime",
            "GameType",
            "Team2Player1",
            "Team2Player2",
            "Team1Player1",
            "Team1Player2",
            "Team2Score",
            "Team1Score",
            "Winner",
            "WinningTeam",
            "GameDurationSeconds",
            "WinningPoints",
            "ScoreDifference",
            "Source File Name",
            "Team2 Canonical",
            "Team1 Canonical",
            "Winner Canonical",
        ]
    ].copy()
    team2["WinningTeam"] = team2["WinningTeam"].map(
        {"Team1": "Lost", "Team2": "Won"}
    )
    team2 = team2.rename(
        columns={
            "Team2Player1": "Player1",
            "Team2Player2": "Player2",
            "Team1Player1": "Opponent1",
            "Team1Player2": "Opponent2",
            "Team2Score": "TeamScore",
            "Team1Score": "OpponentScore",
            "WinningTeam": "Result",
            "Team2 Canonical": "TeamCanonical",
            "Team1 Canonical": "OpponentCanonical",
        }
    )

    combined = pd.concat([team1, team2], ignore_index=True)
    combined["GameKey"] = (
        combined["Timestamp"].astype("string")
        + "-"
        + combined["Result"].astype("string")
    )
    combined["PointDifferential"] = (
        combined["TeamScore"] - combined["OpponentScore"]
    )
    combined["IsWin"] = combined["Result"].eq("Won")
    combined["Final Score"] = (
        combined["TeamScore"].astype("string")
        + "-"
        + combined["OpponentScore"].astype("string")
    )

    combined = combined.sort_values(
        "Timestamp", ascending=False, kind="stable"
    ).reset_index(drop=True)
    combined["Index"] = pd.Series(range(len(combined)), dtype="int64")
    combined["IsIndexEven"] = (combined["Index"] % 2).astype("int64")
    combined = combined.sort_values(
        "DateTime", ascending=True, kind="stable"
    ).reset_index(drop=True)
    combined["Date"] = combined["DateTime"].dt.date
    combined["Hour"] = combined["DateTime"].dt.hour.astype("int64")
    combined["Day of Week"] = combined["DateTime"].dt.dayofweek.astype("int64")

    is_early_morning = combined["Hour"] < 6
    is_evening = combined["Hour"] >= 18
    session_dates = combined["DateTime"].dt.normalize()
    session_dates = session_dates.where(
        ~is_early_morning, session_dates - pd.Timedelta(days=1)
    )
    combined["Session Key"] = (
        session_dates.dt.strftime("%Y-%m-%d")
        + " "
        + (is_evening | is_early_morning).map(
            {True: "Evening", False: "Day"}
        )
    )

    session_order = (
        combined.groupby("Session Key", sort=False)["DateTime"]
        .min()
        .sort_values(kind="stable")
        .index
    )
    session_ids = {
        session_key: index
        for index, session_key in enumerate(session_order, 1)
    }
    combined.insert(
        0,
        "Session ID",
        combined["Session Key"].map(session_ids).astype("int64"),
    )

    first_columns = ["Session ID", "Session Key"]
    other_columns = [column for column in combined if column not in first_columns]
    return combined[first_columns + other_columns]
