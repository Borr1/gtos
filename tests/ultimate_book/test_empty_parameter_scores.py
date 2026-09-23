"""Empty parameter scores are unasked spots, ties, or missing amounts.

A card hour by itself is not a session boundary. Two server hours on the
decision day are the question. 8 and 16 are not written in when the card
does not hold them. A choice the probability keys do not name is still that
choice. A tie stays unset. A noul that is not a bool is not a missing noul
and does not withhold.
"""
from datetime import datetime, timedelta, timezone

from src.components.ultimate_book.primitives import Bar
from src.components.ultimate_book.sleeves.spot_choice import amount_outcome
from src.components.ultimate_book.sleeves.substrate_engine import _questions
from src.judgment.nineteen import learned_score_level_cap, note_score_level_cap


def _bars(n=260):
    bars = []
    price = 100.0
    for i in range(n):
        drift = 0.3 if (i // 3) % 2 == 0 else -0.25
        bars.append(Bar(price, price + 0.8, price - 0.7, price + drift, 1.0))
        price += drift
    return bars


def _facts(bars):
    return {
        "sleeve": "sub_xvol_pullback",
        "symbol": "EURUSD",
        "decision_day": "2026-09-23",
        "i": len(bars) - 1,
        "n_bars": len(bars),
        "hour": 16,
        "close": bars[-1].c,
        "high": bars[-1].h,
        "low": bars[-1].l,
    }


def _times(n, hours):
    start = datetime(2026, 9, 23, 0, 0, tzinfo=timezone.utc)
    stamps = []
    for i in range(n):
        stamps.append(start + timedelta(hours=hours[i % len(hours)]))
    return stamps


def test_one_card_hour_is_not_asked_and_not_called_empty():
    bars = _bars()
    facts = _facts(bars)
    packed = _questions(facts, bars, len(bars) - 1, None)
    assert "session_asia_end" not in packed
    assert "session_london_end" not in packed
    anchors = _questions.anchors["session_asia_end"]
    assert len(anchors) < 2
    number, miss = amount_outcome(
        "session_asia_end", None, anchors, posted=False,
    )
    assert number is None
    assert miss == "not_asked"
    assert miss != "empty"


def test_two_server_hours_are_asked_and_not_replaced():
    from src.components.ultimate_book.sleeves.spot_choice import _server_parts
    from src.judgment import nineteen

    nineteen._LEARNED_LEVEL_CAP.clear()
    bars = _bars(6)
    facts = _facts(bars)
    times = [
        datetime(2026, 9, 23, 1, 0, tzinfo=timezone.utc),
        datetime(2026, 9, 23, 1, 0, tzinfo=timezone.utc),
        datetime(2026, 9, 23, 1, 0, tzinfo=timezone.utc),
        datetime(2026, 9, 23, 1, 0, tzinfo=timezone.utc),
        datetime(2026, 9, 23, 5, 0, tzinfo=timezone.utc),
        datetime(2026, 9, 23, 5, 0, tzinfo=timezone.utc),
    ]
    expected = sorted({float(hour) for hour, _minute, _day in (_server_parts(stamp) for stamp in times)})
    assert len(expected) == 2
    packed = _questions(facts, bars, len(bars) - 1, times)
    asia = packed["session_asia_end"]
    london = packed["session_london_end"]
    assert asia["type"] == "choice"
    assert london["type"] == "choice"
    values = sorted({value for _label, value in _questions.anchors["session_asia_end"]})
    assert values == expected
    assert sorted({value for _label, value in _questions.anchors["session_london_end"]}) == expected
    assert len(asia["criteria"]) == 2
    assert len(london["criteria"]) == 2


def test_choice_label_is_read_when_probability_keys_do_not_match():
    anchors = [("range_low", 5.0), ("swing_high_3", 12.0), ("swing_low_9", 20.0)]
    block = {
        "type": "choice",
        "choice": "range_low",
        "probabilities": {"0": 0.2, "1": 0.5, "2": 0.3},
    }
    number, miss = amount_outcome("range_bars", block, anchors, posted=True)
    assert number == 5.0
    assert miss is None


def test_tie_stays_unset_and_is_not_called_empty():
    anchors = [("range_low", 5.0), ("swing_high_3", 12.0)]
    block = {
        "type": "choice",
        "choice": "range_low",
        "probabilities": {"range_low": 0.5, "swing_high_3": 0.5},
    }
    number, miss = amount_outcome("range_bars", block, anchors, posted=True)
    assert number is None
    assert miss == "tie"


def test_wide_choice_thins_only_after_the_refusal_names_255():
    bars = _bars(260)
    facts = _facts(bars)
    from src.judgment import nineteen

    nineteen._LEARNED_LEVEL_CAP.clear()
    assert learned_score_level_cap() is None
    wide = _questions(facts, bars, 259, None)
    assert len(wide["warmup_bars"]["criteria"]) == 259
    detail = '{"detail": "Too many choices. Must have at most 255 choices."}'
    assert note_score_level_cap(detail) == 255
    thin = _questions(facts, bars, 259, None)
    kept = thin["warmup_bars"]["criteria"]
    assert len(kept) == 255
    original = set(wide["warmup_bars"]["criteria"])
    assert set(kept).issubset(original)
    nineteen._LEARNED_LEVEL_CAP.clear()


def test_generator_passes_bar_times_through(monkeypatch):
    from src.components.ultimate_book.sleeves import substrate as sleeve

    seen = {}

    def _capture(bars, i, hour, **kwargs):
        seen["bar_times"] = kwargs.get("bar_times")
        seen["i"] = i
        return None

    monkeypatch.setattr(sleeve.se, "compute_state", _capture)
    bars = _bars(8)
    times = _times(8, (0, 4))
    symbol = sleeve.XVOL_ON_SURFACE[0]
    assert sleeve.generate_sub_xvol_pullback(
        symbol, bars, "2026-09-23", bar_time=times[-1], bar_times=times,
    ) is None
    assert seen["bar_times"] is times
    assert seen["i"] == 7


def test_noul_float_is_stated_and_does_not_become_a_bool():
    from src.components.ultimate_book.book_owner import _read_jev_return, _unset_label

    block = {"type": "noul", "noul": 0.36}
    value = _read_jev_return("noul", block, {"withhold": "withhold", "allow": "allow"})
    assert value is None
    assert _unset_label("noul", block, value) == "noul_not_bool"
    assert _unset_label("noul", {}, None) == "noul_missing"
    assert _read_jev_return("noul", {"noul": True}, {}) is True
    assert _unset_label("noul", {"noul": False}, False) is None
