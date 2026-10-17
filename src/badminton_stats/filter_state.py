from datetime import date
import hashlib
from typing import Optional

import streamlit as st


SHARED_FILTER_KEYS = {
    "sessions": "shared_filter_sessions",
    "months": "shared_filter_months",
    "date_range": "shared_filter_date_range",
}


def prepare_multiselect_state(
    widget_key: str,
    shared_key: str,
    options: list[str],
    select_all: str,
    default_values: Optional[list[str]],
) -> None:
    if shared_key not in st.session_state:
        if widget_key in st.session_state:
            current = st.session_state[widget_key]
            if not current or select_all in current:
                st.session_state[shared_key] = None
            else:
                st.session_state[shared_key] = [
                    value for value in current if value in options
                ]
        else:
            st.session_state[shared_key] = (
                None
                if default_values is None
                else [value for value in default_values if value in options]
            )

    shared_values = st.session_state[shared_key]
    if shared_values is None:
        st.session_state[widget_key] = [select_all]
        return

    selected = [value for value in shared_values if value in options]
    if not selected:
        st.session_state[shared_key] = None
        st.session_state[widget_key] = [select_all]
    elif len(selected) == len(options) and set(selected) == set(options):
        st.session_state[shared_key] = None
        st.session_state[widget_key] = [select_all]
    else:
        st.session_state[shared_key] = selected
        st.session_state[widget_key] = selected


def sync_multiselect_state(
    widget_key: str,
    shared_key: str,
    options: list[str],
    select_all: str,
) -> None:
    previous_key = f"{widget_key}_select_all_active"
    selected = st.session_state[widget_key]
    had_select_all = st.session_state.get(previous_key, False)

    if select_all in selected and len(selected) > 1:
        selected = (
            [value for value in selected if value != select_all]
            if had_select_all
            else [select_all]
        )
        st.session_state[widget_key] = selected

    has_select_all = select_all in selected
    st.session_state[previous_key] = has_select_all
    if has_select_all or not selected or set(selected) == set(options):
        st.session_state[shared_key] = None
    else:
        st.session_state[shared_key] = [
            value for value in selected if value in options
        ]


def filter_multiselect_options(
    options: list[str], query: str, selected: list[str]
) -> list[str]:
    normalized_query = query.strip().casefold()
    selected_options = set(selected)
    return [
        option
        for option in options
        if option in selected_options or normalized_query in option.casefold()
    ]


def _set_all_multiselect_options(widget_key: str, select_all: str) -> None:
    st.session_state[widget_key] = (
        [select_all] if st.session_state[f"{widget_key}_all"] else []
    )


def _toggle_multiselect_option(
    widget_key: str,
    option_key: str,
    option: str,
    options: list[str],
    select_all: str,
) -> None:
    current = st.session_state[widget_key]
    selected = set(options if select_all in current else current)
    if st.session_state[option_key]:
        selected.add(option)
    else:
        selected.discard(option)

    st.session_state[widget_key] = (
        [select_all]
        if selected == set(options)
        else [value for value in options if value in selected]
    )


def render_searchable_multiselect(
    label: str,
    options: list[str],
    widget_key: str,
    select_all: str,
    default_values: Optional[list[str]] = None,
) -> list[str]:
    search_key = f"{widget_key}_search"
    all_key = f"{widget_key}_all"
    if widget_key not in st.session_state:
        st.session_state[widget_key] = (
            [select_all] if default_values is None else default_values
        )

    current = st.session_state[widget_key]
    all_selected = select_all in current
    selected = (
        options
        if all_selected
        else [value for value in current if value in options]
    )
    if current and not all_selected and not selected:
        all_selected = True
        st.session_state[widget_key] = [select_all]
    elif not all_selected and selected != current:
        st.session_state[widget_key] = selected
    st.session_state[all_key] = all_selected

    selection_summary = (
        f"All {len(options)}"
        if all_selected
        else f"{len(selected)} selected"
    )
    with st.popover(f"{label} ({selection_summary})"):
        st.checkbox(
            "Select all",
            key=all_key,
            on_change=_set_all_multiselect_options,
            args=(widget_key, select_all),
        )
        query = st.text_input(
            "Search options",
            placeholder=f"Search {label.lower()}...",
            label_visibility="collapsed",
            key=search_key,
            type="search",
            live=True,
        )
        if query.strip():
            visible_options = filter_multiselect_options(
                options,
                query,
                [] if all_selected else selected,
            )
        else:
            visible_options = [] if all_selected else selected

        if query.strip() and not visible_options:
            st.caption("No matching options.")
        elif not query.strip() and all_selected:
            st.caption("Search to find an option to deselect.")
        elif not query.strip() and not selected:
            st.caption("Search to find options to select.")

        for option in visible_options:
            option_key = (
                f"{widget_key}_option_"
                f"{hashlib.sha256(option.encode('utf-8')).hexdigest()}"
            )
            st.session_state[option_key] = option in selected
            st.checkbox(
                option,
                key=option_key,
                on_change=_toggle_multiselect_option,
                args=(widget_key, option_key, option, options, select_all),
            )

    current = st.session_state[widget_key]
    if select_all in current:
        return options
    return [value for value in current if value in options]


def _clamp_date(value: date, min_date: date, max_date: date) -> date:
    return min(max(value, min_date), max_date)


def _sync_date_range_inputs(
    start_key: str,
    end_key: str,
    shared_key: str,
    changed_key: str,
) -> None:
    start_date = st.session_state[start_key]
    end_date = st.session_state[end_key]
    if start_date > end_date:
        if changed_key == start_key:
            end_date = start_date
            st.session_state[end_key] = end_date
        else:
            start_date = end_date
            st.session_state[start_key] = start_date
    st.session_state[shared_key] = (start_date, end_date)


def render_date_range_inputs(
    widget_key: str,
    shared_key: str,
    default_range: tuple[date, date],
    min_date: date,
    max_date: date,
) -> tuple[date, date]:
    if shared_key not in st.session_state:
        st.session_state[shared_key] = st.session_state.get(
            widget_key,
            default_range,
        )

    value = st.session_state[shared_key]
    if isinstance(value, tuple):
        if len(value) == 2:
            start_date = _clamp_date(value[0], min_date, max_date)
            end_date = _clamp_date(value[1], min_date, max_date)
        elif len(value) == 1:
            start_date = _clamp_date(value[0], min_date, max_date)
            end_date = _clamp_date(default_range[1], min_date, max_date)
        else:
            start_date, end_date = default_range
    elif isinstance(value, date):
        start_date = _clamp_date(value, min_date, max_date)
        end_date = _clamp_date(default_range[1], min_date, max_date)
    else:
        start_date, end_date = default_range

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    st.session_state[shared_key] = (start_date, end_date)
    start_key = f"{widget_key}_start"
    end_key = f"{widget_key}_end"
    st.session_state[start_key] = start_date
    st.session_state[end_key] = end_date

    start_column, end_column = st.columns(2)
    with start_column:
        selected_start = st.date_input(
            "Start date",
            min_value=min_date,
            max_value=max_date,
            format="YYYY-MM-DD",
            key=start_key,
            on_change=_sync_date_range_inputs,
            args=(start_key, end_key, shared_key, start_key),
        )
    with end_column:
        selected_end = st.date_input(
            "End date",
            min_value=min_date,
            max_value=max_date,
            format="YYYY-MM-DD",
            key=end_key,
            on_change=_sync_date_range_inputs,
            args=(start_key, end_key, shared_key, end_key),
        )
    return selected_start, selected_end
