"""Remaining size-path decisions are two-sided Choices.

The unique highest probability wins. An empty answer or a tie does not
restore the old boolean. There is no absent side. No broker send.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from src.components.ultimate_book import minimal_size as ms


_NOW = datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc)


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


def _answer(question: str, probabilities: dict[str, float]) -> dict:
    return {
        "model": "jev-1.13.0",
        "answers": {
            question: {
                "probabilities": probabilities,
                "confidence": 0.4,
            }
        },
    }


def _install(monkeypatch: pytest.MonkeyPatch, payload: dict) -> dict:
    seen = {"n": 0, "criteria": None}

    def _urlopen(req, timeout=0):
        del timeout
        body = json.loads(req.data.decode("utf-8"))
        questions = body["questions"]
        assert "jev_absent" not in json.dumps(questions)
        for block in questions.values():
            assert set(block["criteria"]) != {"jev_absent"}
            assert len(block["criteria"]) == 2
            seen["criteria"] = list(block["criteria"])
        seen["n"] += 1
        return _Resp(payload)

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)
    return seen


def test_usdjpy_unique_highest_withholds(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _install(
        monkeypatch,
        _answer(
            "usdjpy_verification_hold",
            {"standing_list_is_a_fact": 0.21, "usdjpy_hold": 0.79},
        ),
    )
    reason = ms.f5_standing_hold_reason(
        ms.F5_NAMESPACE,
        "USDJPY",
        direction="SHORT",
        family="dsp_isolated_spike_high",
        now=_NOW,
    )
    assert seen["n"] == 1
    assert len(seen["criteria"]) == 2
    assert reason == "usdjpy_verification_hold_5pip_dsp_stop"


def test_usdjpy_empty_and_tie_do_not_restore(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, _answer("usdjpy_verification_hold", {}))
    assert (
        ms.f5_standing_hold_reason(
            ms.F5_NAMESPACE, "USDJPY", direction="SHORT", family="dsp_isolated_spike_high", now=_NOW,
        )
        is None
    )
    ms._FEAR_CACHE.clear()
    _install(
        monkeypatch,
        _answer(
            "usdjpy_verification_hold",
            {"standing_list_is_a_fact": 0.5, "usdjpy_hold": 0.5},
        ),
    )
    assert (
        ms.f5_standing_hold_reason(
            ms.F5_NAMESPACE, "USDJPY", direction="SHORT", family="dsp_isolated_spike_high", now=_NOW,
        )
        is None
    )
    assert ms.fear_withholds.last["alternative"] is None


def test_idxrev_other_side_does_not_block(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(
        monkeypatch,
        _answer(
            "idxrev_j5_off",
            {"symbol_is_the_fire": 0.81, "idxrev_off_stands": 0.19},
        ),
    )
    assert ms.f5_idxrev_symbol_off_reason(ms.F5_NAMESPACE, "GER40", family="idxrev") is None
    assert ms.fear_withholds.last["alternative"] == "symbol_is_the_fire"


def test_stop_ticks_unique_highest_withholds(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(
        monkeypatch,
        _answer(
            "f5_stop_ticks_le_8",
            {"stop_is_the_plan": 0.11, "eight_tick_cliff": 0.89},
        ),
    )
    assert ms.f5_lots_or_ticks_refuse_reason(lots=1.0, stop_dist=8.0, tick_size=1.0) == (
        "f5_stop_ticks_le_8"
    )


def test_stop_ticks_empty_does_not_restore(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, _answer("f5_stop_ticks_le_8", {}))
    assert ms.f5_lots_or_ticks_refuse_reason(lots=1.0, stop_dist=8.0, tick_size=1.0) is None


def test_sibling_window_unique_highest(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    path = tmp_path / "closed.json"
    closed = (_NOW - timedelta(minutes=5)).isoformat()
    path.write_text(
        json.dumps({"closed": [{"symbol": "XAUUSD", "closed_utc": closed, "close_action": "stop_loss"}]}),
        encoding="utf-8",
    )
    _install(
        monkeypatch,
        _answer(
            "just_closed_sibling",
            {"close_is_a_fact": 0.2, "sibling_window_stands": 0.8},
        ),
    )
    assert ms.f5_just_closed_sibling_reason("XAUUSD", now=_NOW, path=path) == "just_closed_sibling"


def test_clock_hold_does_not_restore_dead_window(monkeypatch: pytest.MonkeyPatch) -> None:
    dead = datetime(2026, 9, 21, 22, 30, tzinfo=timezone.utc)
    assert ms.f5_in_dead_window(dead) is True
    _install(monkeypatch, _answer("f5_dead_window", {}))
    assert ms.f5_clock_hold_reason(ms.F5_NAMESPACE, "EURUSD", now=dead) is None


def test_two_stop_count_stays_integer_choice_decides(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    path = tmp_path / "closed.json"
    rows = []
    for ticket in (1, 2):
        rows.append({
            "symbol": "EURUSD",
            "sleeve": "idxrev",
            "ticket": ticket,
            "closed_utc": _NOW.isoformat(),
            "close_action": "orig_stop",
            "exit_class": "orig_stop",
        })
    path.write_text(json.dumps({"closed": rows}), encoding="utf-8")
    assert ms.f5_same_sleeve_orig_stop_count_session_day(
        "EURUSD", sleeve="idxrev", now=_NOW, path=path,
    ) == 2
    _install(monkeypatch, _answer("same_sleeve_two_orig_stops_session_day", {}))
    assert ms.f5_same_sleeve_two_stop_refuse_reason(
        "EURUSD", sleeve="idxrev", now=_NOW, path=path, namespace=ms.F5_NAMESPACE,
    ) is None
