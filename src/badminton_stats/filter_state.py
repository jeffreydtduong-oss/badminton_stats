from datetime import date
from typing import Optional, Union

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


def _clamp_date(value: date, min_date: date, max_date: date) -> date:
    return min(max(value, min_date), max_date)


def prepare_date_range_state(
    widget_key: str,
    shared_key: str,
    default_range: tuple[date, date],
    min_date: date,
    max_date: date,
) -> None:
    if shared_key not in st.session_state:
        st.session_state[shared_key] = default_range

    value = st.session_state[shared_key]
    if isinstance(value, tuple):
        if len(value) == 2:
            value = (
                _clamp_date(value[0], min_date, max_date),
                _clamp_date(value[1], min_date, max_date),
            )
        elif len(value) == 1:
            value = (_clamp_date(value[0], min_date, max_date),)
    elif isinstance(value, date):
        value = _clamp_date(value, min_date, max_date)

    st.session_state[shared_key] = value
    st.session_state[widget_key] = value


def sync_date_range_state(widget_key: str, shared_key: str) -> None:
    value: Union[date, tuple[date, ...]] = st.session_state[widget_key]
    st.session_state[shared_key] = value
