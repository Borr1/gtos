"""Skip Choices resolve by unique highest probability.

When the old predicate is true, an empty answer or a tie does not restore
that skip. The first criterion is not a default. No order send, no install.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from src.judgment import skip_choices as sc


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
    sc._CACHE.clear()
    monkeypatch.setattr(sc, "_append_receipt", lambda row: None)
    monkeypatch.setattr("src.judgment.jev_client.calls_enabled", lambda: True)
    monkeypatch.setattr("src.judgment.jev_client._consume_call", lambda: True)
    monkeypatch.setattr(
        "src.judgment.jev_client.resolve_key",
        lambda: ("unit-test-not-a-credential", "unit-test"),
    )
    box: dict = {"payload": {}}
    seen = {"n": 0}

    def _urlopen(req, timeout=0):
        del req, timeout
        seen["n"] += 1
        return _Resp(box["payload"])

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)
    yield box, seen
    sc._CACHE.clear()


def _body(skip: str, probabilities: dict, label: str) -> dict:
    return {
        "model": "jev-1.13.0",
        "answers": {
            skip: {
                "probabilities": probabilities,
                "choice": label,
                "confidence": 0.4,
            }
        },
    }


def _probs(skip: str, winner: str | None, *, tie: bool = False, empty: bool = False) -> dict:
    order = sc.SPECS[skip]["order"]
    if empty:
        return {}
    if tie:
        return {name: 0.5 for name in order}
    return {name: (0.82 if name == winner else 0.18 / max(len(order) - 1, 1)) for name in order}


def _decide(box: dict, seen: dict, skip: str, probabilities: dict, label: str) -> dict:
    before = seen["n"]
    box["payload"] = _body(skip, probabilities, label)
    row = sc.decide(
        skip,
        {"symbol": "EURUSD", "sleeve": "dsp_x", "namespace": "operator"},
        cache_key=f"unit|{skip}|{label}|{sorted(probabilities.items())}|{before}",
    )
    assert seen["n"] == before + 1
    assert row["flatten"] is False
    assert row["do_not_close_ticket"] == "294215389"
    assert row["persist"] == 0.0
    assert row["unit_usd"] == 150.0
    return row


@pytest.mark.parametrize("skip", list(sc.SPECS))
def test_unique_highest_skip_blocks(skip, _no_live_post) -> None:
    box, seen = _no_live_post
    withhold = sc.SPECS[skip]["skip"]
    row = _decide(box, seen, skip, _probs(skip, withhold), "not-the-probability")
    assert row["alternative"] == withhold
    assert row["blocks"] is True
    assert row["unanswered"] is False
    assert row["error"] is None


@pytest.mark.parametrize("skip", list(sc.SPECS))
def test_unique_other_does_not_restore_skip(skip, _no_live_post) -> None:
    box, seen = _no_live_post
    order = sc.SPECS[skip]["order"]
    withhold = sc.SPECS[skip]["skip"]
    other = next(name for name in order if name != withhold)
    row = _decide(box, seen, skip, _probs(skip, other), withhold)
    assert row["alternative"] == other
    assert row["blocks"] is False
    assert row["unanswered"] is False


@pytest.mark.parametrize("skip", list(sc.SPECS))
def test_empty_answer_does_not_restore_skip(skip, _no_live_post) -> None:
    box, seen = _no_live_post
    withhold = sc.SPECS[skip]["skip"]
    row = _decide(box, seen, skip, {}, withhold)
    assert row["alternative"] is None
    assert row["blocks"] is False
    assert row["unanswered"] is True
    assert row["error"] == "probabilities_missing"


@pytest.mark.parametrize("skip", list(sc.SPECS))
def test_tie_does_not_restore_first_name(skip, _no_live_post) -> None:
    box, seen = _no_live_post
    withhold = sc.SPECS[skip]["skip"]
    first = sc.SPECS[skip]["order"][0]
    row = _decide(box, seen, skip, _probs(skip, None, tie=True), withhold)
    assert row["alternative"] is None
    assert row["alternative"] != first
    assert row["blocks"] is False
    assert row["unanswered"] is True
    assert row["error"] == "tie"


def _owner():
    return SimpleNamespace(_namespace="operator")


def test_already_placed_today_empty_does_not_restore_true(_no_live_post) -> None:
    box, seen = _no_live_post
    box["payload"] = _body("already_placed_today", {}, "one_fill_is_enough")
    wrapped = sc._wrap_today(lambda *args, **kwargs: True)

    def invoke(self):
        return wrapped(self, "dsp_x", "EURUSD", "2026-09-21")

    assert invoke(_owner()) is False
    assert seen["n"] == 1


def test_already_placed_today_unique_skip_stays_true(_no_live_post) -> None:
    box, _seen = _no_live_post
    box["payload"] = _body(
        "already_placed_today",
        _probs("already_placed_today", "one_fill_is_enough"),
        "later_bar_is_the_fire",
    )
    wrapped = sc._wrap_today(lambda *args, **kwargs: True)

    def invoke(self):
        return wrapped(self, "dsp_y", "GBPUSD", "2026-09-21")

    assert invoke(_owner()) is True


def test_late_entry_tie_does_not_restore_true(_no_live_post) -> None:
    box, seen = _no_live_post
    box["payload"] = _body(
        "stale_late_entry_after_restart",
        _probs("stale_late_entry_after_restart", None, tie=True),
        "restart_chase",
    )
    wrapped = sc._wrap_late(lambda *args, **kwargs: True)
    now = datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc)

    def invoke(self):
        assert self._namespace == "operator"
        return wrapped(now, "2026-09-21T11:45:00+00:00", "M15", 0.25)

    assert invoke(_owner()) is False
    assert seen["n"] == 1


def test_judgment_hold_empty_does_not_restore_held(_no_live_post) -> None:
    box, seen = _no_live_post
    box["payload"] = _body("judgment_hold", {}, "hold_stands")
    decision = {"reason": "flow", "action": "hold"}
    wrapped = sc._wrap_hold(lambda self, *args, **kwargs: (True, decision))
    intent = SimpleNamespace(symbol="EURUSD", sleeve="dsp_x")
    held, stamped = wrapped(_owner(), intent)
    assert held is False
    assert stamped["skip_unanswered"] is True
    assert seen["n"] == 1


def test_open_exposure_tie_does_not_restore_the_block(_no_live_post) -> None:
    box, seen = _no_live_post
    skip = "same_broker_symbol_open_position_lifecycle_guard"
    box["payload"] = _body(skip, _probs(skip, None, tie=True), "keep_open_ticket")
    position = SimpleNamespace(ticket=111, symbol="EURUSD", comment="unit")
    wrapped = sc._wrap_exposures(lambda self, symbol, open_positions_snapshot=None: [position])
    assert wrapped(_owner(), "EURUSD") == []
    assert seen["n"] == 1


def test_cycle_keys_empty_does_not_restore_the_placed_set(_no_live_post) -> None:
    box, seen = _no_live_post
    skip = "same_broker_symbol_already_placed_this_cycle"
    box["payload"] = _body(skip, {}, "cycle_already_sent")
    keys = {"EURUSD"}
    assert sc.cycle_target_keys(keys, {"EURUSD"}, symbol="EURUSD", sleeve="dsp_x") == set()
    assert keys == {"EURUSD"}
    assert seen["n"] == 1


def test_cycle_keys_unique_skip_keeps_real_keys(_no_live_post) -> None:
    box, _seen = _no_live_post
    skip = "same_broker_symbol_already_placed_this_cycle"
    box["payload"] = _body(skip, _probs(skip, "cycle_already_sent"), "sibling_is_a_new_send")
    keys = {"GBPUSD"}
    assert sc.cycle_target_keys(keys, {"GBPUSD"}, symbol="GBPUSD", sleeve="dsp_y") == keys


def test_fx_drop_wrap_empty_does_not_restore_reason(_no_live_post) -> None:
    box, seen = _no_live_post
    box["payload"] = _body("fx_dsp_dropped_j6", {}, "pattern_absent")
    wrapped = sc._wrap_fx(lambda *args, **kwargs: "fx_dsp_dropped_j6")
    assert (
        wrapped(
            "operator",
            "EURUSD",
            family="dsp_descending_lows_accepted",
            stop_dist=1.5,
        )
        is None
    )
    assert seen["n"] == 1
