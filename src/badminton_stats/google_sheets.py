from typing import Any, Mapping

import gspread
import pandas as pd


WORKSHEET_NAME = "Game History"
REQUIRED_UPLOAD_COLUMNS = {"DateTime"}


def _open_worksheet(
    spreadsheet_id: str,
    credentials_info: Mapping[str, Any],
    worksheet_name: str = WORKSHEET_NAME,
) -> gspread.Worksheet:
    client = gspread.service_account_from_dict(dict(credentials_info))
    spreadsheet = client.open_by_key(spreadsheet_id)
    try:
        return spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(
            title=worksheet_name,
            rows=1000,
            cols=26,
        )


def load_game_history_from_sheet(
    spreadsheet_id: str,
    credentials_info: Mapping[str, Any],
) -> pd.DataFrame:
    worksheet = _open_worksheet(spreadsheet_id, credentials_info)
    values = worksheet.get_all_values()
    if not values:
        raise ValueError(
            f"The '{WORKSHEET_NAME}' worksheet is empty; upload game history "
            "CSV files first."
        )
    if len(values) < 2:
        raise ValueError(
            f"The '{WORKSHEET_NAME}' worksheet has a header but no game rows."
        )

    columns = values[0]
    if not columns or len(columns) != len(set(columns)):
        raise ValueError(
            f"The '{WORKSHEET_NAME}' worksheet must have unique column names."
        )
    records = [
        row[: len(columns)] + [""] * max(0, len(columns) - len(row))
        for row in values[1:]
    ]
    frame = pd.DataFrame(records, columns=columns).replace("", pd.NA)
    return frame


def append_new_game_history(
    spreadsheet_id: str,
    credentials_info: Mapping[str, Any],
    games: pd.DataFrame,
) -> tuple[int, int]:
    if games.empty:
        return 0, 0

    missing = sorted(REQUIRED_UPLOAD_COLUMNS - set(games.columns))
    if missing:
        raise ValueError(f"Game history is missing required columns: {missing}")

    incoming = games.copy()
    incoming["_DateTimeKey"] = _datetime_keys(incoming["DateTime"])
    duplicate_mask = incoming.duplicated(subset=["_DateTimeKey"], keep="first")
    duplicates_within_upload = int(duplicate_mask.sum())
    incoming = incoming.loc[~duplicate_mask].copy()

    worksheet = _open_worksheet(spreadsheet_id, credentials_info)
    values = worksheet.get_all_values()
    columns = games.columns.tolist()
    if not values:
        worksheet.update(
            values=[columns],
            range_name="A1",
            value_input_option="RAW",
        )
        existing_keys: set[str] = set()
    else:
        if values[0] != columns:
            raise ValueError(
                f"The '{WORKSHEET_NAME}' worksheet header does not match "
                "the CSV columns. Keep the same columns and column order."
            )
        if "DateTime" not in values[0]:
            raise ValueError(
                f"The '{WORKSHEET_NAME}' worksheet must include DateTime."
            )
        date_time_index = values[0].index("DateTime")
        existing_values = [
            row[date_time_index]
            for row in values[1:]
            if len(row) > date_time_index and row[date_time_index]
        ]
        existing_keys = set(_datetime_keys(pd.Series(existing_values)))

    new_games = incoming.loc[
        ~incoming["_DateTimeKey"].isin(existing_keys), columns
    ]
    if not new_games.empty:
        rows = [
            ["" if pd.isna(value) else str(value) for value in row]
            for row in new_games.itertuples(index=False, name=None)
        ]
        worksheet.append_rows(rows, value_input_option="RAW")

    return len(new_games), duplicates_within_upload


def _datetime_keys(values: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(values, errors="raise")
    if parsed.isna().any():
        raise ValueError("Game history contains missing DateTime values.")
    return parsed.map(lambda value: pd.Timestamp(value).isoformat())
