from __future__ import annotations

import pytest

from src.research_infra.forward_capture import AMBIGUITY_STATES, classify_ltf_ambiguity


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"lower_tf_available": False}, "no_ltf_data"),
        ({"lower_tf_available": True, "fill_happened": False}, "no_fill"),
        (
            {"lower_tf_available": True, "fill_before_invalidation": True},
            "fill_before_invalidation",
        ),
        (
            {"lower_tf_available": True, "invalidation_before_fill": True},
            "invalidation_before_fill",
        ),
        (
            {
                "lower_tf_available": True,
                "tp_hit": True,
                "sl_hit": True,
                "tp_time_utc": "2026-05-04T13:31:00+00:00",
                "sl_time_utc": "2026-05-04T13:31:00+00:00",
            },
            "same_bar_tp_sl_ambiguity",
        ),
        (
            {
                "lower_tf_available": True,
                "tp_hit": True,
                "sl_hit": True,
                "tp_time_utc": "2026-05-04T13:31:00+00:00",
                "sl_time_utc": "2026-05-04T13:32:00+00:00",
            },
            "tp_before_sl",
        ),
        (
            {
                "lower_tf_available": True,
                "tp_hit": True,
                "sl_hit": True,
                "tp_time_utc": "2026-05-04T13:33:00+00:00",
                "sl_time_utc": "2026-05-04T13:32:00+00:00",
            },
            "sl_before_tp",
        ),
        ({"lower_tf_available": True, "unresolved": True}, "unresolved"),
    ],
)
def test_classify_ltf_ambiguity_states(kwargs, expected):
    assert classify_ltf_ambiguity(**kwargs) == expected


def test_classifier_output_set_is_registered():
    observed = {
        "no_ltf_data",
        "same_bar_tp_sl_ambiguity",
        "no_fill",
        "fill_before_invalidation",
        "invalidation_before_fill",
        "tp_before_sl",
        "sl_before_tp",
        "unresolved",
    }
    assert observed == AMBIGUITY_STATES
