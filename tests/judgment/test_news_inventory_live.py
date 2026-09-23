"""G1: live A1 + haircut see host writer inventory. No NEWS_PROTOCOL."""

import json
from datetime import datetime, timezone

import pytest

from src.judgment.a1_log import maybe_observe_fluid_at_place, maybe_observe_ub_plc_017, observe
from src.judgment.apply_size import haircut_challenge_unit
from src.judgment.compose import compose_shadow
from src.judgment.host_events import (
    DEFAULT_EVENTS,
    news_inventory_at,
    news_inventory_extra,
    resolve_host_events_path,
)

AS_OF = datetime(2026, 9, 17, 7, 30, 55, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def _isolate_live_host_writer(monkeypatch):
    """Host shadow_logs / Challenge writer must not leak into live=True tests."""
    monkeypatch.delenv("GTOS_JEV_HOST_EVENTS", raising=False)
    monkeypatch.delenv("GTOS_CHALLENGE_EVENTS", raising=False)
    monkeypatch.setattr("src.judgment.host_events.LIVE_HOST_EVENT_CANDIDATES", ())


def _covering_state():
    return {
        "identity": {
            "symbol": "XAUUSD",
            "side": "short",
            "family_class": "study",
            "sleeve": "dsp_two_bar_t",
            "candidate_id": "292667008",
        },
        "completeness": {"state_sufficient_for_live": True},
        "news": {
            "spine_empty": False,
            "events": [{"event": "CPI"}],
            "challenge_axis_covering": True,
            "high_in_f5_window": False,
        },
        "cost": {"spread_r_of_stop": 0.08},
        "timeframes": {"h4": {"trend": 1}},
        "sessions": {"named": "london"},
        "clock": {"as_of_utc": "2026-09-17T07:30:55Z", "is_friday": False},
        "occupancy": {},
        "sleeve_features": {},
        "geometry": {},
    }


def _writer_row(*, status="NOT_READ", n=0, ts="2026-09-17T07:31:10Z"):
    return {
        "event": "news_t15_pending_cancel",
        "ts_utc": ts,
        "inventory_status": status,
        "n_events_in_window": n,
        "account_login": 0,
        "namespace": "operator",
        "schema": "gtos.f5.minimal_size_event.v1",
        "place": False,
        "remint": False,
    }


def _write_events(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _honest(composed):
    return composed["fluid"]["gates"]["FLUID-ADM-009"]["shadow"]


def test_news_inventory_extra_wraps_load_and_prefers_named_status(tmp_path):
    dest = tmp_path / "events.jsonl"
    _write_events(
        dest,
        [
            {
                "event": "news_t60_expiry_reeval",
                "ts_utc": "2026-09-17T07:30:51Z",
                "inventory_status": None,
                "n_events_in_window": None,
            },
            _writer_row(),
        ],
    )
    inv = news_inventory_extra(AS_OF, dest)
    assert inv == news_inventory_at(
        [
            {
                "event": "news_t60_expiry_reeval",
                "ts_utc": "2026-09-17T07:30:51Z",
                "inventory_status": None,
                "n_events_in_window": None,
            },
            _writer_row(),
        ],
        AS_OF,
    )
    assert inv["host_news_source"] == "challenge_host_news_writer"
    assert inv["host_news_inventory_status"] == "NOT_READ"
    assert inv["host_news_n_in_window"] == 0


def test_live_resolve_does_not_use_lab_tape(monkeypatch, tmp_path):
    monkeypatch.delenv("GTOS_JEV_HOST_EVENTS", raising=False)
    monkeypatch.delenv("GTOS_CHALLENGE_EVENTS", raising=False)
    assert DEFAULT_EVENTS.is_file()
    assert resolve_host_events_path(live=False) == DEFAULT_EVENTS
    assert resolve_host_events_path(live=True) is None
    lab = news_inventory_extra(AS_OF)
    assert lab["host_news_source"] == "challenge_host_news_writer"
    live = news_inventory_extra(AS_OF, live=True)
    assert live["host_news_source"] == "unassembled"
    missing = tmp_path / "absent.jsonl"
    monkeypatch.setenv("GTOS_JEV_HOST_EVENTS", str(missing))
    assert resolve_host_events_path(live=True) is None
    assert news_inventory_extra(AS_OF, live=True)["host_news_source"] == "unassembled"


def test_live_compose_writer_not_read_calendar_honest_false(monkeypatch, tmp_path):
    dest = tmp_path / "events.jsonl"
    _write_events(dest, [_writer_row()])
    monkeypatch.setenv("GTOS_JEV_HOST_EVENTS", str(dest))
    extra = news_inventory_extra(AS_OF, live=True)
    composed = compose_shadow(_covering_state(), extra=extra, ticket="292667008")
    assert extra["host_news_source"] == "challenge_host_news_writer"
    assert extra["host_news_inventory_status"] == "NOT_READ"
    assert _honest(composed) is False


def test_live_compose_no_writer_json_axis_unchanged(monkeypatch):
    monkeypatch.delenv("GTOS_JEV_HOST_EVENTS", raising=False)
    monkeypatch.delenv("GTOS_CHALLENGE_EVENTS", raising=False)
    extra = news_inventory_extra(AS_OF, live=True)
    assert extra["host_news_source"] == "unassembled"
    covering = compose_shadow(_covering_state(), extra=extra, ticket="292667008")
    baseline = compose_shadow(_covering_state(), ticket="292667008")
    assert _honest(covering) is True
    assert _honest(baseline) is True
    assert _honest(covering) == _honest(baseline)


def test_haircut_passes_live_inventory_to_compose(monkeypatch, tmp_path):
    dest = tmp_path / "events.jsonl"
    _write_events(dest, [_writer_row()])
    monkeypatch.setenv("GTOS_JEV_HOST_EVENTS", str(dest))
    captured = {}
    import src.judgment.apply_size as apply_size

    real = apply_size.compose_shadow

    def wrap(state, answers=None, **kwargs):
        captured["extra"] = kwargs.get("extra")
        return real(state, answers, **kwargs)

    monkeypatch.setattr(apply_size, "compose_shadow", wrap)
    haircut_challenge_unit(
        {"risk_pct_per_trade": 0.0015},
        state=_covering_state(),
        answers={},
        evaluate_jev=False,
        as_of_utc=AS_OF,
        ticket="292667008",
    )
    assert captured["extra"]["host_news_source"] == "challenge_host_news_writer"
    assert captured["extra"]["host_news_inventory_status"] == "NOT_READ"
    assert _honest(compose_shadow(_covering_state(), extra=captured["extra"])) is False

    monkeypatch.delenv("GTOS_JEV_HOST_EVENTS", raising=False)
    captured.clear()
    haircut_challenge_unit(
        {"risk_pct_per_trade": 0.0015},
        state=_covering_state(),
        answers={},
        evaluate_jev=False,
        as_of_utc=AS_OF,
        ticket="292667008",
    )
    assert captured["extra"]["host_news_source"] == "unassembled"
    assert _honest(compose_shadow(_covering_state(), extra=captured["extra"])) is True


def test_observe_compose_sees_writer_unread(monkeypatch, tmp_path):
    dest = tmp_path / "events.jsonl"
    _write_events(dest, [_writer_row()])
    monkeypatch.setenv("GTOS_JEV_A1_LOG", "1")
    monkeypatch.setenv("GTOS_JEV_A1_CALL", "0")
    monkeypatch.setenv("GTOS_JEV_A1_LOG_PATH", str(tmp_path / "a1.jsonl"))
    extra = news_inventory_extra(AS_OF, dest)
    row = observe("UB-PLC-017", _covering_state(), extra=extra)
    assert row.get("skipped") is None
    assert row["extra"]["host_news_inventory_status"] == "NOT_READ"
    assert _honest(row["compose"]) is False
    empty = observe("UB-PLC-017", _covering_state(), extra={})
    assert _honest(empty["compose"]) is True


def test_maybe_observe_plc_merges_live_inventory(monkeypatch, tmp_path):
    dest = tmp_path / "events.jsonl"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_events(dest, [_writer_row(ts=now)])
    monkeypatch.setenv("GTOS_JEV_HOST_EVENTS", str(dest))
    monkeypatch.setenv("GTOS_JEV_A1_LOG", "1")
    monkeypatch.setenv("GTOS_JEV_A1_CALL", "0")
    monkeypatch.setenv("GTOS_JEV_A1_LOG_PATH", str(tmp_path / "a1.jsonl"))
    captured = []
    import src.judgment.a1_log as a1_log

    real_observe = a1_log.observe
    real_fluid = a1_log.observe_fluid_inventory

    def wrap_observe(*args, **kwargs):
        captured.append(("observe", kwargs.get("extra") or {}))
        return real_observe(*args, **kwargs)

    def wrap_fluid(*args, **kwargs):
        captured.append(("fluid", kwargs.get("extra") or {}))
        return real_fluid(*args, **kwargs)

    monkeypatch.setattr(a1_log, "observe", wrap_observe)
    monkeypatch.setattr(a1_log, "observe_fluid_inventory", wrap_fluid)

    class _I:
        symbol = "XAUUSD"
        sleeve = "dsp_two_bar_t"
        stop_dist = 5.45

    class _T:
        bid = 4331.0
        ask = 4331.4

    maybe_observe_ub_plc_017(_I(), _T(), None)
    maybe_observe_fluid_at_place(_I(), _T(), None)
    assert captured
    assert any(extra.get("host_news_inventory_status") == "NOT_READ" for _, extra in captured)
    assert any(extra.get("cost_skip") is None for _, extra in captured)
    fluid = [extra for name, extra in captured if name == "fluid"]
    assert fluid and fluid[0]["host_news_source"] == "challenge_host_news_writer"
    assert fluid[0]["must_not_mutate_cost_skip"] is True
