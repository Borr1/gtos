"""A closed bar whose sleeve did not fire still has a unit Choice.

The stop is that bar's range on the chosen side. An empty answer, a tie,
or a zero range does not invent a direction.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.judgment.book_engine_choices import QUESTIONS, limit_unit_spec, unit_question_text


def test_long_stop_is_the_bar_low() -> None:
    row = limit_unit_spec("unit_long", close=2350.5, high=2352.0, low=2348.0)
    assert row is not None
    assert row["direction"] == 1
    assert row["entry_price"] == 2350.5
    assert row["stop_dist"] == 2350.5 - 2348.0
    assert "target_dist" not in row


def test_short_stop_is_the_bar_high() -> None:
    row = limit_unit_spec("unit_short", close=31.2, high=31.8, low=31.0)
    assert row is not None
    assert row["direction"] == -1
    assert row["entry_price"] == 31.2
    assert row["stop_dist"] == 31.8 - 31.2


def test_unset_does_not_invent() -> None:
    assert limit_unit_spec(None, close=10, high=11, low=9) is None
    assert limit_unit_spec("sleeve_stays_out", close=10, high=11, low=9) is None
    assert limit_unit_spec("unit_long", close=10, high=11, low=10) is None
    assert limit_unit_spec("unit_short", close=10, high=10, low=9) is None
    assert limit_unit_spec("unit_long", close=None, high=11, low=9) is None


def test_question_names_the_three_sides() -> None:
    spec = QUESTIONS["unit"]
    assert spec["id"] == "be_unit"
    assert tuple(spec["criteria"]) == ("unit_long", "unit_short", "sleeve_stays_out")
    text = spec["instructions"]
    assert "empty answer or a tie" in text
    assert "does not invent a direction" in text
    assert "bid" in text and "ask" in text


def test_question_text_carries_the_closed_bar() -> None:
    text = unit_question_text(
        {
            "symbol": "XAUUSD",
            "sleeve": "metals_softband",
            "open": 2350.0,
            "high": 2352.0,
            "low": 2348.0,
            "close": 2350.5,
            "range_to_low": 2.5,
            "range_to_high": 1.5,
            "direction": None,
            "bid": 2350.4,
            "ask": 2350.6,
            "last_bar_choice": "closed_bar_reaches",
        }
    )
    for piece in (
        "Symbol XAUUSD",
        "Sleeve metals_softband",
        "Open 2350",
        "High 2352",
        "Low 2348",
        "Close 2350.5",
        "Range to the low 2.5",
        "Range to the high 1.5",
        "Direction absent",
        "Bid 2350.4",
        "Ask 2350.6",
        "Last bar closed_bar_reaches",
        "does not invent a direction",
    ):
        assert piece in text, piece
    assert "Jev" not in text
    assert "System One" not in text


def test_empty_card_does_not_invent_a_side() -> None:
    text = unit_question_text({})
    assert "Direction absent" in text
    assert "Last bar absent" in text
    assert "Open absent" in text
    assert "does not invent a direction" in text


def test_engine_asks_before_unit_unset() -> None:
    engine = (ROOT / "src" / "components" / "ultimate_book" / "book_engine.py").read_text(
        encoding="utf-8"
    )
    call = engine.find("intent = self._limit_unit_from_closed_bar")
    unset = engine.find('status = "unit_unset"')
    assert call > 0
    assert unset > call
    body = engine[engine.find("def _limit_unit_from_closed_bar") : call]
    for piece in (
        'facts["open"]',
        'facts["range_to_low"]',
        'facts["range_to_high"]',
        'facts["bid"]',
        'facts["ask"]',
        'facts["direction"]',
        "_direction_if_any",
    ):
        assert piece in body, piece


if __name__ == "__main__":
    test_long_stop_is_the_bar_low()
    test_short_stop_is_the_bar_high()
    test_unset_does_not_invent()
    test_question_names_the_three_sides()
    test_question_text_carries_the_closed_bar()
    test_empty_card_does_not_invent_a_side()
    test_engine_asks_before_unit_unset()
    print("ok")
