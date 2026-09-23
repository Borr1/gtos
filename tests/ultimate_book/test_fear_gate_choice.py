"""Fear gates decide by unique highest probability.

An empty answer or a tie does not restore the old boolean, even when the
clock, sleeve, or drop-set fact that used to block is true. No broker send.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from src.components.ultimate_book import minimal_size as ms


_DEAD = datetime(2026, 9, 21, 22, 30, tzinfo=timezone.utc)
_FRIDAY = datetime(2026, 9, 18, 17, 0, tzinfo=timezone.utc)


class _Resp:
    def __init__(self, payload: dict) -> None:
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> "_Resp":
        return self

    def __exit__(self, *exc: object) -> bool:
        return False


@pytest.fixture(autouse=True)
def _no_live_post(monkeypatch: pytest.MonkeyPatch):
    ms._FEAR_CACHE.clear()
    monkeypatch.setattr(ms, "_fear_receipt", lambda row: None)
    monkeypatch.setattr("src.judgment.jev_client.calls_enabled", lambda: True)
    monkeypatch.setattr("src.judgment.jev_client._consume_call", lambda: True)
    monkeypatch.setattr(
        "src.judgment.jev_client.resolve_key",
        lambda: ("unit-test-not-a-credential", "unit-test"),
    )
    yield
    ms._FEAR_CACHE.clear()


def _answer(question: str, probabilities: dict[str, float], label: str) -> dict:
    return {
        "model": "jev-1.13.0",
        "answers": {
            question: {
                "probabilities": probabilities,
                "choice": label,
                "confidence": 0.4,
            }
        },
    }


def _install_body(monkeypatch: pytest.MonkeyPatch, payload: dict) -> dict:
    seen = {"n": 0}

    def _urlopen(req, timeout=0):
        del req, timeout
        seen["n"] += 1
        return _Resp(payload)

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)
    return seen


def test_dead_window_unique_highest_withholds(monkeypatch: pytest.MonkeyPatch) -> None:
    assert ms.f5_in_dead_window(_DEAD) is True
    seen = _install_body(
        monkeypatch,
        _answer(
            "f5_dead_window",
            {"hour_is_a_fact": 0.06, "dead_hour_mute": 0.94},
            "hour_is_a_fact",
        ),
    )
    reason = ms.f5_new_risk_clock_block_reason("EURUSD", _DEAD, events=())
    assert seen["n"] == 1
    assert reason == "f5_dead_window"
    assert ms.fear_withholds.last["blocks"] is True
    assert ms.fear_withholds.last["alternative"] == "dead_hour_mute"
    assert ms.fear_withholds.last["unanswered"] is False


def test_dead_window_empty_does_not_restore_boolean(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _install_body(
        monkeypatch,
        _answer("f5_dead_window", {}, "dead_hour_mute"),
    )
    reason = ms.f5_new_risk_clock_block_reason("EURUSD", _DEAD, events=())
    assert seen["n"] == 1
    assert reason is None
    assert ms.fear_withholds.last["blocks"] is False
    assert ms.fear_withholds.last["alternative"] is None
    assert ms.fear_withholds.last["unanswered"] is True
    assert ms.fear_withholds.last["error"] == "probabilities_missing"


def test_dead_window_tie_does_not_restore_boolean(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _install_body(
        monkeypatch,
        _answer(
            "f5_dead_window",
            {"hour_is_a_fact": 0.5, "dead_hour_mute": 0.5},
            "dead_hour_mute",
        ),
    )
    reason = ms.f5_new_risk_clock_block_reason("EURUSD", _DEAD, events=())
    assert seen["n"] == 1
    assert reason is None
    assert ms.fear_withholds.last["blocks"] is False
    assert ms.fear_withholds.last["alternative"] is None
    assert ms.fear_withholds.last["error"] == "tie"


def test_dead_window_other_alternative_does_not_block(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _install_body(
        monkeypatch,
        _answer(
            "f5_dead_window",
            {"hour_is_a_fact": 0.91, "dead_hour_mute": 0.09},
            "dead_hour_mute",
        ),
    )
    reason = ms.f5_new_risk_clock_block_reason("EURUSD", _DEAD, events=())
    assert seen["n"] == 1
    assert reason is None
    assert ms.fear_withholds.last["alternative"] == "hour_is_a_fact"
    assert ms.fear_withholds.last["blocks"] is False


def test_friday_cutoff_empty_and_tie_do_not_restore(monkeypatch: pytest.MonkeyPatch) -> None:
    assert ms.f5_friday_weekend_cutoff_reason("EURUSD", _FRIDAY) == "f5_friday_weekend_cutoff"
    seen = _install_body(
        monkeypatch,
        _answer("f5_friday_weekend_cutoff", {}, "weekend_cutoff_mute"),
    )
    assert ms.f5_new_risk_clock_block_reason("EURUSD", _FRIDAY, events=()) is None
    assert seen["n"] == 1
    ms._FEAR_CACHE.clear()
    _install_body(
        monkeypatch,
        _answer(
            "f5_friday_weekend_cutoff",
            {"friday_is_a_fact": 0.5, "weekend_cutoff_mute": 0.5},
            "weekend_cutoff_mute",
        ),
    )
    assert ms.f5_new_risk_clock_block_reason("EURUSD", _FRIDAY, events=()) is None
    assert ms.fear_withholds.last["alternative"] is None


def test_friday_cutoff_unique_highest_withholds(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_body(
        monkeypatch,
        _answer(
            "f5_friday_weekend_cutoff",
            {"friday_is_a_fact": 0.12, "weekend_cutoff_mute": 0.88},
            "friday_is_a_fact",
        ),
    )
    assert ms.f5_new_risk_clock_block_reason("EURUSD", _FRIDAY, events=()) == "f5_friday_weekend_cutoff"


def test_hard_off_unique_highest_withholds(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_body(
        monkeypatch,
        _answer(
            "f5_hard_off_sleeve",
            {"sleeve_is_the_fire": 0.08, "hard_off_stands": 0.92},
            "sleeve_is_the_fire",
        ),
    )
    assert ms.f5_hard_off_sleeve_reason("idxrev", "operator") == "hard_off_sleeve"


def test_hard_off_empty_and_tie_do_not_restore(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_body(
        monkeypatch,
        _answer("f5_hard_off_sleeve", {}, "hard_off_stands"),
    )
    assert ms.f5_hard_off_sleeve_reason("idxrev", "operator") is None
    ms._FEAR_CACHE.clear()
    _install_body(
        monkeypatch,
        _answer(
            "f5_hard_off_sleeve",
            {"sleeve_is_the_fire": 0.5, "hard_off_stands": 0.5},
            "hard_off_stands",
        ),
    )
    assert ms.f5_hard_off_sleeve_reason("idxrev", "operator") is None


def test_hard_off_other_alternative_does_not_block(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_body(
        monkeypatch,
        _answer(
            "f5_hard_off_sleeve",
            {"sleeve_is_the_fire": 0.77, "hard_off_stands": 0.23},
            "hard_off_stands",
        ),
    )
    assert ms.f5_hard_off_sleeve_reason("idxrev", "operator") is None
    assert ms.fear_withholds.last["alternative"] == "sleeve_is_the_fire"


def test_fx_drop_set_empty_and_tie_do_not_restore(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_body(
        monkeypatch,
        _answer("fx_dsp_dropped_j6", {}, "pattern_absent"),
    )
    assert (
        ms.f5_fx_dsp_tight_stop_reason(
            "operator",
            "EURUSD",
            family="dsp_descending_lows_accepted",
            stop_dist=1.5,
        )
        is None
    )
    ms._FEAR_CACHE.clear()
    _install_body(
        monkeypatch,
        _answer(
            "fx_dsp_dropped_j6",
            {"pattern_is_the_fire": 0.5, "pattern_absent": 0.5},
            "pattern_absent",
        ),
    )
    assert (
        ms.f5_fx_dsp_tight_stop_reason(
            "operator",
            "GBPUSD",
            family="dsp_descending_lows_accepted",
            stop_dist=1.5,
        )
        is None
    )


def test_fx_drop_set_unique_highest_withholds(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_body(
        monkeypatch,
        _answer(
            "fx_dsp_dropped_j6",
            {"pattern_is_the_fire": 0.18, "pattern_absent": 0.82},
            "pattern_is_the_fire",
        ),
    )
    assert (
        ms.f5_fx_dsp_tight_stop_reason(
            "operator",
            "USDJPY",
            family="dsp_descending_lows_accepted",
            stop_dist=1.5,
        )
        == "fx_dsp_dropped_j6"
    )


def test_fear_withholds_ignores_first_name_on_a_tie(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_body(
        monkeypatch,
        _answer(
            "f5_named_high_window",
            {"send_through_the_window": 0.5, "named_high_inside_window": 0.5},
            "named_high_inside_window",
        ),
    )
    got = ms.fear_withholds(
        "f5_named_high_window",
        {"symbol": "EURUSD", "named_high_inside_window": True},
        {
            "send_through_the_window": "still the fire",
            "named_high_inside_window": "window withholds",
        },
        "named_high_inside_window",
        "unit-test-named-high-tie",
        "named high window",
    )
    assert got is None
    assert ms.fear_withholds.last["alternative"] is None
