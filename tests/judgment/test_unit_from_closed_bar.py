"""The unit Choice is long, short, or no move.

The limit prices are the forming open shifted by the projected move.
An empty answer or a tie does not invent a direction.
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
        "Sleeve fired absent",
        "Forming open absent",
        "Projected move absent",
        "Long limit absent",
        "Short limit absent",
        "does not invent a direction",
        "unit_long is the long limit",
        "unit_short is the short limit",
        "sleeve_stays_out is no move",
    ):
        assert piece in text, piece
    assert "Entry is this close" not in text
    assert "produces no unit" not in text
    assert "did not fire" not in text
    assert "Jev" not in text
    assert "System One" not in text


def test_question_text_names_both_limits() -> None:
    text = unit_question_text(
        {
            "symbol": "USDJPY",
            "sleeve": "fx_jpy",
            "forming_open": 157.58,
            "projected_move": 0.05,
            "sleeve_fired": False,
        }
    )
    assert "Forming open 157.58" in text
    assert "Projected move 0.05" in text
    assert "Long limit 157.53" in text
    assert "Short limit 157.63" in text
    assert "Sleeve fired false" in text


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
    card = engine[engine.find("def _closed_bar_card") : engine.find("def _remember_last_bar")]
    for piece in (
        'facts["open"]',
        'facts["range_to_low"]',
        'facts["range_to_high"]',
        'facts["bid"]',
        'facts["ask"]',
        'facts["direction"]',
        "_direction_if_any",
        "if sleeve_fired is not None",
    ):
        assert piece in card, piece
    assert '"sleeve_fired": False' not in card
    unit = engine[engine.find("def _limit_unit_from_closed_bar") : engine.find("def _slot_generation")]
    assert "sleeve_fired=False" in unit
    assert 'facts["long_limit"]' in engine or "long_limit" in engine


if __name__ == "__main__":
    test_long_stop_is_the_bar_low()
    test_short_stop_is_the_bar_high()
    test_unset_does_not_invent()
    test_question_names_the_three_sides()
    test_question_text_carries_the_closed_bar()
    test_question_text_names_both_limits()
    test_empty_card_does_not_invent_a_side()
    test_engine_asks_before_unit_unset()
    print("ok")
