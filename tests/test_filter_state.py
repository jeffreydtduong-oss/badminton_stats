import hashlib
import unittest
from datetime import date

from streamlit.testing.v1 import AppTest

from badminton_stats.filter_state import filter_multiselect_options


class FilterMultiselectOptionsTests(unittest.TestCase):
    def test_date_range_inputs_update_shared_range_and_keep_endpoints_ordered(
        self,
    ) -> None:
        app = AppTest.from_string(
            """
import streamlit as st
from datetime import date
from badminton_stats.filter_state import render_date_range_inputs

selected = render_date_range_inputs(
    "date_filter",
    "shared_date_filter",
    (date(2025, 11, 1), date(2026, 10, 1)),
    date(2025, 11, 1),
    date(2026, 10, 1),
)
st.write(selected)
"""
        ).run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.date_input), 2)
        self.assertEqual(
            app.session_state["shared_date_filter"],
            (date(2025, 11, 1), date(2026, 10, 1)),
        )

        app.date_input(key="date_filter_start").set_value(
            date(2026, 1, 1)
        ).run()
        self.assertFalse(app.exception)
        self.assertEqual(
            app.session_state["shared_date_filter"],
            (date(2026, 1, 1), date(2026, 10, 1)),
        )
        app.date_input(key="date_filter_end").set_value(
            date(2026, 5, 31)
        ).run()
        self.assertFalse(app.exception)
        self.assertEqual(
            app.session_state["shared_date_filter"],
            (date(2026, 1, 1), date(2026, 5, 31)),
        )

        app.date_input(key="date_filter_start").set_value(
            date(2026, 6, 1)
        ).run()
        self.assertFalse(app.exception)
        self.assertEqual(
            app.session_state["shared_date_filter"],
            (date(2026, 6, 1), date(2026, 6, 1)),
        )

    def test_searchable_picker_preserves_selection_across_searches(self) -> None:
        app = AppTest.from_string(
            """
import streamlit as st
from badminton_stats.filter_state import render_searchable_multiselect

selected = render_searchable_multiselect(
    "Player", ["Alice", "Bob", "Charlie"], "picker", "__all__"
)
st.write("Selected:", selected)
"""
        ).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["picker"], ["__all__"])

        app.checkbox(key="picker_all").uncheck().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["picker"], [])

        app.text_input(key="picker_search").set_value("ali").run()
        self.assertFalse(app.exception)
        self.assertEqual(
            [checkbox.label for checkbox in app.checkbox],
            ["Select all", "Alice"],
        )

        alice_key = (
            "picker_option_" + hashlib.sha256(b"Alice").hexdigest()
        )
        app.checkbox(key=alice_key).check().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["picker"], ["Alice"])

        app.text_input(key="picker_search").set_value("Bob").run()
        self.assertFalse(app.exception)
        self.assertEqual(
            {checkbox.label for checkbox in app.checkbox},
            {"Select all", "Alice", "Bob"},
        )
        self.assertEqual(app.session_state["picker"], ["Alice"])

    def test_filters_options_case_insensitively(self) -> None:
        self.assertEqual(
            filter_multiselect_options(
                ["Alice", "Bob", "Charlie"],
                "ALI",
                [],
            ),
            ["Alice"],
        )

    def test_keeps_selected_options_visible_outside_search(self) -> None:
        self.assertEqual(
            filter_multiselect_options(
                ["Alice", "Bob", "Charlie"],
                "ali",
                ["Charlie", "Unknown"],
            ),
            ["Alice", "Charlie"],
        )

    def test_blank_query_returns_all_options(self) -> None:
        self.assertEqual(
            filter_multiselect_options(
                ["Alice", "Bob"],
                " ",
                [],
            ),
            ["Alice", "Bob"],
        )


if __name__ == "__main__":
    unittest.main()
