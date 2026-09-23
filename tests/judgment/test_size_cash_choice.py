"""Size cash and persist weight decide by unique highest probability.

A missing or tied answer does not fill printed 150 or printed 0.00 in as
the decision. A bare label is not a probability. No broker send.
"""

from __future__ import annotations

import pytest

from src.judgment.size_exit import (
    PRINTED_PERSIST,
    PRINTED_UNIT_USD,
    choose_size_and_persist,
)


_STATE = {
    "equity": 93678.44,
    "balance": 93670.92,
    "namespace": "operator",
    "open_ticket": 294215389,
}


@pytest.fixture
def noted(monkeypatch: pytest.MonkeyPatch):
    seen: list = []
    monkeypatch.setattr(
        "src.judgment.size_exit._note_persist",
        lambda weight: seen.append(weight),
    )
    return seen


def _choose(answers: dict) -> dict:
    return choose_size_and_persist(_STATE, answers=answers)


def test_unique_highest_names_cash_and_ignores_printed_150(noted) -> None:
    row = _choose(
        {
            "size_cash": {
                "choice": "usd_150",
                "probabilities": {
                    "usd_200": 0.00,
                    "usd_150": 0.16,
                    "usd_100": 0.44,
                    "usd_75": 0.38,
                    "not_this_spot": 0.02,
                },
            },
            "persist_weight": {
                "choice": "w_0_20",
                "probabilities": {"w_0_20": 0.05, "w_0_10": 0.15, "w_0_00": 0.80},
            },
        }
    )
    assert row["size_alternative"] == "usd_100"
    assert row["cash_usd"] == 100.0
    assert row["cash_usd"] != PRINTED_UNIT_USD
    assert row["size_decided"] is True
    assert row["persist_alternative"] == "w_0_00"
    assert row["persist_decided"] is True
    assert row["persist_weight"] == 0.0
    assert row["facts"]["printed_unit_usd"] == PRINTED_UNIT_USD
    assert row["facts"]["open_ticket"] == 294215389
    assert noted == [0.0]


def test_unique_not_this_spot_is_a_decision_with_no_cash(noted) -> None:
    row = _choose(
        {
            "size_cash": {
                "probabilities": {
                    "usd_200": 0.02,
                    "usd_150": 0.04,
                    "usd_100": 0.06,
                    "usd_75": 0.08,
                    "not_this_spot": 0.80,
                }
            },
            "persist_weight": {
                "probabilities": {"w_0_20": 0.70, "w_0_10": 0.20, "w_0_00": 0.10}
            },
        }
    )
    assert row["size_alternative"] == "not_this_spot"
    assert row["size_decided"] is True
    assert row["cash_usd"] is None
    assert row["persist_alternative"] == "w_0_20"
    assert row["persist_weight"] == 0.20
    assert noted == [0.20]


def test_empty_answer_does_not_restore_150_or_zero_persist(noted) -> None:
    row = _choose(
        {
            "size_cash": {"choice": "usd_150", "probabilities": {}},
            "persist_weight": {"choice": "w_0_00", "probabilities": {}},
        }
    )
    assert row["size_decided"] is False
    assert row["persist_decided"] is False
    assert row["size_alternative"] is None
    assert row["persist_alternative"] is None
    assert row["cash_usd"] is None
    assert row["persist_weight"] is None
    assert row["facts"]["printed_unit_usd"] == 150.0
    assert row["facts"]["printed_persist_weight"] == PRINTED_PERSIST
    assert noted == [None]


def test_missing_blocks_do_not_restore_printed_defaults(noted) -> None:
    row = _choose({})
    assert row["cash_usd"] is None
    assert row["persist_weight"] is None
    assert row["size_decided"] is False
    assert row["persist_decided"] is False
    assert noted == [None]


def test_tie_does_not_pick_first_name_or_printed_150(noted) -> None:
    row = _choose(
        {
            "size_cash": {
                "choice": "usd_150",
                "probabilities": {
                    "usd_200": 0.30,
                    "usd_150": 0.30,
                    "usd_100": 0.20,
                    "usd_75": 0.10,
                    "not_this_spot": 0.10,
                },
            },
            "persist_weight": {
                "choice": "w_0_00",
                "probabilities": {"w_0_20": 0.50, "w_0_10": 0.0, "w_0_00": 0.50},
            },
        }
    )
    assert row["size_alternative"] is None
    assert row["cash_usd"] is None
    assert row["size_decided"] is False
    assert row["persist_alternative"] is None
    assert row["persist_weight"] is None
    assert row["persist_decided"] is False
    assert noted == [None]


def test_bare_label_is_not_a_decision(noted) -> None:
    row = _choose(
        {
            "size_cash": {"choice": "usd_150"},
            "persist_weight": {"choice": "w_0_00"},
        }
    )
    assert row["cash_usd"] is None
    assert row["persist_weight"] is None
    assert row["size_decided"] is False
    assert row["persist_decided"] is False
    assert noted == [None]
