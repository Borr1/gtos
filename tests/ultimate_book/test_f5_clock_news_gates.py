"""F5 writer NEW-risk clocks: dead window, named HIGH, Friday weekend cutoff."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from src.components.ultimate_book.minimal_size import (
    F5_NAMESPACE,
    f5_compose_official_high_spine,
    f5_event_is_warsh_class,
    f5_event_scheduled_utc,
    f5_friday_weekend_cutoff_reason,
    f5_in_dead_window,
    f5_load_live_calendar_events,
    f5_named_high_window_reason,
    f5_new_risk_clock_block_reason,
    minutes_to_nearest_high_impact_event,
)

WARSH = {
    "name": "Fed Chair Kevin Warsh Jackson Hole remarks",
    "impact": "high",
    "official_high": True,
    "time_utc": "2026-08-28T14:00:00Z",
    "tickets": ["US30", "EURUSD", "GER40"],
}


def test_dead_window_2100_to_0000_utc():
    assert f5_in_dead_window(datetime(2026, 8, 28, 21, 0, tzinfo=timezone.utc))
    assert f5_in_dead_window(datetime(2026, 8, 28, 23, 59, tzinfo=timezone.utc))
    assert not f5_in_dead_window(datetime(2026, 8, 29, 0, 0, tzinfo=timezone.utc))
    assert not f5_in_dead_window(datetime(2026, 8, 28, 20, 59, tzinfo=timezone.utc))
    assert f5_new_risk_clock_block_reason(
        "EURUSD", datetime(2026, 8, 28, 21, 5, tzinfo=timezone.utc), events=(),
    ) == "f5_dead_window"


def test_friday_1600_cutoff_crypto_exempt():
    fri1600 = datetime(2026, 8, 28, 16, 0, tzinfo=timezone.utc)
    assert f5_friday_weekend_cutoff_reason("EURUSD", fri1600) == "f5_friday_weekend_cutoff"
    assert f5_friday_weekend_cutoff_reason("BTCUSD", fri1600) is None
    assert f5_friday_weekend_cutoff_reason(
        "EURUSD", datetime(2026, 8, 28, 15, 59, tzinfo=timezone.utc),
    ) is None
    # Thursday 17:00 leftover is not this gate.
    assert f5_friday_weekend_cutoff_reason(
        "US30", datetime(2026, 8, 27, 17, 0, tzinfo=timezone.utc),
    ) is None


def test_warsh_class_and_not_gdp_or_agenda():
    assert f5_event_is_warsh_class(WARSH)
    assert not f5_event_is_warsh_class({
        "name": "Jackson Hole agenda published (symposium Day 1 already open)",
        "impact": "high_context",
        "official_high": True,
        "time_utc": "2026-08-28T00:00:00Z",
    })
    assert not f5_event_is_warsh_class({
        "name": "US GDP Q2 2nd estimate + Core PCE Jul",
        "impact": "high",
        "official_high": False,
        "event_type": "gdp",
        "scheduled_utc": "2026-08-26T12:30:00Z",
    })
    assert f5_event_is_warsh_class({
        "event": "US CPI",
        "impact": "HIGH",
        "event_type": "cpi",
        "currency": "USD",
        "scheduled_utc": "2026-09-10T12:30:00Z",
    })
    assert f5_event_is_warsh_class({
        "what": "NFP / Employment Situation",
        "next": "2026-09-04T12:30:00Z (Friday 4 Sep 08:30 ET)",
    })


def test_named_high_tminus15_tplus60_by_symbol_not_occupancy():
    t_minus_15 = datetime(2026, 8, 28, 13, 45, tzinfo=timezone.utc)
    t_minus_16 = datetime(2026, 8, 28, 13, 44, tzinfo=timezone.utc)
    t_plus_60 = datetime(2026, 8, 28, 15, 0, tzinfo=timezone.utc)
    t_plus_61 = datetime(2026, 8, 28, 15, 1, tzinfo=timezone.utc)
    events = [WARSH]
    # USD-leg + listed tickets. Occupancy of other names is irrelevant.
    for sym in ("EURUSD", "GBPUSD", "US30", "GER40", "XAUUSD"):
        assert f5_named_high_window_reason(sym, t_minus_15, events) == "f5_named_high_window"
        assert f5_named_high_window_reason(sym, t_plus_60, events) == "f5_named_high_window"
    assert f5_named_high_window_reason("EURUSD", t_minus_16, events) is None
    assert f5_named_high_window_reason("EURUSD", t_plus_61, events) is None
    # EURGBP has no USD leg and is not on the ticket list.
    assert f5_named_high_window_reason("EURGBP", t_minus_15, events) is None


def test_minutes_to_parses_news_calendar_hhmm():
    when = datetime(2026, 8, 12, 12, 32, tzinfo=timezone.utc)
    rows = [
        {"impact": "HIGH", "date": "2026-08-12", "time_utc": "12:30"},
        {"impact": "HIGH", "scheduled_utc": "2026-08-12T18:00:00Z"},
    ]
    assert minutes_to_nearest_high_impact_event(when, rows) == 2.0
    assert f5_event_scheduled_utc(rows[0]) == datetime(2026, 8, 12, 12, 30, tzinfo=timezone.utc)


def test_production_namespace_is_inert(monkeypatch):

    monkeypatch.setattr(
        "src.components.ultimate_book.minimal_size.fear_withholds",
        lambda *a, **k: a[0],
    )
    from src.components.ultimate_book.minimal_size import f5_clock_hold_reason
    now = datetime(2026, 8, 28, 21, 5, tzinfo=timezone.utc)
    assert f5_clock_hold_reason("operator_profile", "EURUSD", now=now) is None
    assert f5_clock_hold_reason(F5_NAMESPACE, "EURUSD", now=now) == "f5_dead_window"


def test_owner_new_risk_block_is_namespace_gated(tmp_path):
    from types import SimpleNamespace
    from src.components.ultimate_book.book_owner import UltimateBookOwner
    from src.components.ultimate_book.minimal_size import MinimalSizeConfig

    cfg = {
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "gtos_vnext_runtime": {
            "ultimate_book_enabled": True,
            "ultimate_book_apply_to_execution": True,
            "ultimate_book_live_activation_allowed": True,
            "ultimate_book_live_broker_authority": True,
            "ultimate_book_disable_broad_selector": True,
            "ultimate_book_profile": "clean3_w7_measured_nom1p25",
            "ultimate_book_include_clean3": True,
            "ultimate_book_derisk_mode": "band",
            "ultimate_book_include_candidate_book": False,
            "ultimate_book_include_market_expansion_book": False,
            "ultimate_book_stress_derisk": False,
            "ultimate_book_kelly_lite": True,
            "ultimate_book_kelly_conservative": True,
            "ultimate_book_drop_w7_symbols": True,
            "selector_v4_enabled": True,
            "selector_v4_apply_to_execution": False,
        },
    }

    class _MT5:
        def get_tick(self, _symbol):
            return SimpleNamespace(bid=1.0, ask=1.0001, time=datetime.now(timezone.utc))
        def get_account_balance(self):
            return 100_000.0
        def get_account_equity(self):
            return 100_000.0

    f5 = UltimateBookOwner(
        cfg, _MT5(), str(tmp_path), namespace="operator",
        engine_factory=lambda _s: SimpleNamespace(active_trade=None),
        minimal_size=MinimalSizeConfig(
            enabled=True, target_risk_usd=75.0, notional_initial_usd=100_000.0,
        ),
    )
    prod = UltimateBookOwner(
        cfg, _MT5(), str(tmp_path / "prod"), namespace="operator_profile",
        engine_factory=lambda _s: SimpleNamespace(active_trade=None),
    )
    dead = datetime(2026, 8, 28, 21, 30, tzinfo=timezone.utc)
    assert f5._f5_new_risk_block("EURUSD", dead) == "f5_dead_window"
    assert prod._f5_new_risk_block("EURUSD", dead) is None


def test_compose_spine_includes_warsh_from_brief(tmp_path):
    brief = {
        "schema": "gtos.live.news_brief.v1",
        "as_of_utc": "2026-08-26T23:51:00Z",
        "events": [WARSH],
        "absent_next_48h": [
            {
                "what": "NFP / Employment Situation",
                "next": "2026-09-04T12:30:00Z (Friday 4 Sep 08:30 ET)",
            }
        ],
    }
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "news_brief.json").write_text(json.dumps(brief), encoding="utf-8")
    (tmp_path / "data" / "news_calendar.json").write_text(json.dumps({
        "events": [{
            "date": "2026-09-16",
            "time_utc": "18:00",
            "event": "FOMC Rate Decision",
            "impact": "HIGH",
            "currency": "USD",
            "event_type": "fomc_decision",
            "scheduled_utc": "2026-09-16T18:00:00Z",
        }]
    }), encoding="utf-8")
    spine = f5_compose_official_high_spine(
        tmp_path, now=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
    )
    names = [e["name"] for e in spine["events"]]
    assert any("Warsh" in n for n in names)
    assert any("NFP" in n or "Employment" in n for n in names)
    assert any("FOMC" in n for n in names)
    loaded = f5_load_live_calendar_events(tmp_path)
    assert f5_named_high_window_reason(
        "EURUSD", datetime(2026, 8, 28, 14, 5, tzinfo=timezone.utc), loaded,
    ) == "f5_named_high_window"
