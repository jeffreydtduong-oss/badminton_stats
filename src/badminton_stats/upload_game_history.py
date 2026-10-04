import argparse
import json
import os
from pathlib import Path
from typing import Any

from badminton_stats.data import DEFAULT_DATA_DIRECTORY, load_game_history
from badminton_stats.google_sheets import append_new_game_history


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Append new game-history CSV records to Google Sheets."
    )
    parser.add_argument(
        "--directory",
        type=Path,
        default=DEFAULT_DATA_DIRECTORY,
        help="Folder containing game_history CSV exports.",
    )
    parser.add_argument(
        "--spreadsheet-id",
        default=os.environ.get("BADMINTON_STATS_SPREADSHEET_ID"),
        help="Google spreadsheet ID (or BADMINTON_STATS_SPREADSHEET_ID).",
    )
    parser.add_argument(
        "--credentials-file",
        type=Path,
        default=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
        help="Service-account JSON file path (or GOOGLE_APPLICATION_CREDENTIALS).",
    )
    args = parser.parse_args()

    if not args.spreadsheet_id:
        parser.error(
            "Set BADMINTON_STATS_SPREADSHEET_ID or pass --spreadsheet-id."
        )
    if not args.credentials_file:
        parser.error(
            "Set GOOGLE_APPLICATION_CREDENTIALS or pass --credentials-file."
        )

    with args.credentials_file.open(encoding="utf-8") as credentials_file:
        credentials_info: Any = json.load(credentials_file)
    if not isinstance(credentials_info, dict):
        parser.error("The service-account credentials file must contain a JSON object.")

    source_games, files, _ = load_game_history(args.directory)
    source_games = source_games.drop(columns=["Source File Name"])
    added, duplicate_uploads = append_new_game_history(
        args.spreadsheet_id,
        credentials_info,
        source_games,
    )
    print(
        f"Read {len(files)} CSV file(s) and {len(source_games)} game(s); "
        f"appended {added} new game(s)."
    )
    if duplicate_uploads:
        print(
            f"Skipped {duplicate_uploads} duplicate DateTime record(s) "
            "within the uploaded files."
        )
    already_uploaded = len(source_games) - added - duplicate_uploads
    if already_uploaded:
        print(f"Skipped {already_uploaded} game(s) already present in the sheet.")


if __name__ == "__main__":
    main()
