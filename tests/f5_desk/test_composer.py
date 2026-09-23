"""Composer against the REAL stream formats (trimmed 2026-08-24 harvest rows)."""
from __future__ import annotations

import json
from datetime import timedelta

from scripts.f5_desk import common, composer

from .conftest import ADOPTED_TICKET, CLOSED_TICKET, FIXED_NOW, OPEN_TICKET


def _slate(desk_cfg, now=FIXED_NOW, persist=True):
    slate, path = composer.build_slate(desk_cfg, now_utc=now, persist=persist)
    return slate, path


def _by_id_fragment(slate, fragment):
    for cand in slate["candidates"]:
        if fragment in cand["candidate_id"] or any(fragment in a for a in cand.get("alias_ids", [])):
            return cand
    return None


# ---------------------------------------------------------------------------
# candidates
# ---------------------------------------------------------------------------
def test_candidate_extraction_from_intents_and_placed(desk_cfg):
    slate, path = _slate(desk_cfg)
    assert slate["schema"] == "gtos.judgment.slate.v2"
    assert slate["namespace"] == "operator"
    assert path is not None and path.is_file()
    # sha pinned in the filename
    assert slate["slate_id"] in path.name

    # standing intent (never placed): XAUUSD sleeve from the f5_slate row
    xau = _by_id_fragment(slate, "dsp_walked_high_accepted_through")
    assert xau is not None
    assert xau["status"] == "intent"
    assert xau["candidate_id"] == "LAUNCHER::XAUUSD::dsp_walked_high_accepted_through::2026-08-24"

    # placed candidate from the launcher cycle row, engine candidate_id verbatim + geometry
    flush = _by_id_fragment(slate, "dsp_climax_flush_to_96low_then_snap")
    assert flush is not None
    assert flush["status"] == "placed"
    assert flush["candidate_id"] == (
        "W7_BOOK::dsp_c_flush::EURUSD::2026-08-24::LONG::dsp_climax_flush_to_96low_then_snap"
    )
    assert "LAUNCHER::EURUSD::dsp_climax_flush_to_96low_then_snap::2026-08-24" in flush["alias_ids"]
    assert flush["geometry"] == {"entry": 1.16651, "stop": 1.16601, "target": 1.17051}
    assert flush["direction"] == "LONG"
    assert flush["cluster"] == "dsp_c_flush"

    # the filled intent is marked filled and carries the engine id from the fill event
    filled = _by_id_fragment(slate, "dsp_small_bar_sit_on_20high_rejects")
    assert filled is not None
    assert filled["status"] == "filled"
    assert filled["candidate_id"].startswith("W7_BOOK::dsp_c_smallsit::EURUSD::2026-08-24::LONG")


def test_skips_and_refusals_carried(desk_cfg):
    slate, _ = _slate(desk_cfg)
    assert slate["skips"]["counts_today"], "skip reasons from the launcher cycle row expected"
    assert any(r.get("refusal_reasons") for r in slate["refusals"])


# ---------------------------------------------------------------------------
# open positions: fills minus closes, enriched by stop moves, seeded by adopted
# ---------------------------------------------------------------------------
def test_open_position_reconstruction(desk_cfg):
    slate, _ = _slate(desk_cfg)
    tickets = {p["ticket"] for p in slate["open_positions"]}
    assert OPEN_TICKET in tickets
    # 178058089 was adopted at 07:45Z, never enriched by a stop_move, and its
    # close was lost by the packet stream — the phantom class the 2026-08-25
    # liveness filter exists to hide. It must NOT reach the judge, and the
    # counter must own up to hiding it.
    assert ADOPTED_TICKET not in tickets, "stale adopted-only row must be hidden"
    assert slate["counters"]["stale_open_rows_hidden"] >= 1
    assert CLOSED_TICKET not in tickets, "a closed ticket must never appear open"

    pos = next(p for p in slate["open_positions"] if p["ticket"] == OPEN_TICKET)
    assert pos["entry_price"] == 1.16657
    assert pos["stop_now"] == 1.16605
    assert abs(pos["take_profit_1"] - 1.16969) < 1e-6
    assert pos["locked_r"] == -1.0
    assert pos["direction"] == "LONG"
    # age from the fill timestamp (23:18:21Z) to FIXED_NOW (23:45Z) ~ 26.6 min
    assert 20.0 < pos["age_minutes"] < 30.0


# ---------------------------------------------------------------------------
# ex-post exclusion — structural, not editorial
# ---------------------------------------------------------------------------
def test_expost_exclusion_everywhere(desk_cfg):
    slate, _ = _slate(desk_cfg)
    serialized = json.dumps(
        {k: slate[k] for k in ("candidates", "open_positions", "refusals", "skips", "governor")}
    )
    for forbidden in ("broker_net_pnl_usd", "realised_r", "notional_pnl_usd",
                      "real_pnl_usd_cumulative", "notional_equity_after",
                      "realized_today_pct", '"equity"', '"pnl"'):
        assert forbidden not in serialized, f"ex-post key {forbidden} leaked into the slate"
    # the fixture's closed trade IS the forensic exhibit: LTCUSD 178351323,
    # broker_net_pnl_usd -307.53 (-4.10R on the $75 unit). That number exists in
    # the stream and must not exist anywhere in the slate
    full = json.dumps(slate)
    close_row = None
    for line in open(desk_cfg.events_path, encoding="utf-8"):
        obj = json.loads(line)
        if obj.get("event") == "f5_trade_closed":
            close_row = obj
    assert close_row is not None
    assert str(close_row["broker_net_pnl_usd"]) not in full
    # open positions are whitelist-built
    for pos in slate["open_positions"]:
        assert set(pos) <= set(composer.OPEN_POSITION_FIELDS) | {"cluster"}


# ---------------------------------------------------------------------------
# calendar window
# ---------------------------------------------------------------------------
def test_calendar_folds_warsh_from_news_brief(desk_cfg, desk_repo):
    """Composer must fold live brief speakers, not only frozen news_calendar.json."""
    brief = {
        "schema": "gtos.live.news_brief.v1",
        "events": [{
            "name": "Fed Chair Kevin Warsh Jackson Hole remarks",
            "impact": "high",
            "official_high": True,
            "time_utc": "2026-08-25T01:15:00Z",
            "tickets": ["US30", "EURUSD", "GER40"],
        }],
    }
    path = desk_repo / "data" / "news_brief.json"
    path.write_text(json.dumps(brief), encoding="utf-8")
    desk_cfg.news_brief_path = path
    slate, _ = _slate(desk_cfg)
    events = {e["event"]: e for e in slate["calendar"]}
    assert "Fed Chair Kevin Warsh Jackson Hole remarks" in events
    warsh = events["Fed Chair Kevin Warsh Jackson Hole remarks"]
    assert warsh["impact"] == "HIGH"
    assert "EURUSD" in warsh["touches_symbols"]


def test_calendar_window_and_relevance(desk_cfg):
    slate, _ = _slate(desk_cfg)
    events = {e["event"]: e for e in slate["calendar"]}
    assert "US FOMC Member Speech (fixture)" in events, "+2h15m HIGH USD is inside the window"
    assert "ECB Rate Decision (fixture)" not in events, "+14h15m is outside +/-12h"
    assert "WM/Refinitiv 16:00 London Fix" in events, "currency ALL inside the window"

    fomc = events["US FOMC Member Speech (fixture)"]
    assert abs(fomc["minutes_from_now"] - 135.0) < 0.51
    # USD touches both the crypto candidate's symbol and EURUSD
    assert "EURUSD" in fomc["touches_symbols"]
    assert "LTCUSD" in fomc["touches_symbols"]
    # JPY event touches none of the slate symbols
    jpy = events.get("JPY Household Spending (fixture)")
    assert jpy is not None and jpy["touches_symbols"] == []

    # per-candidate proximity to the nearest HIGH event of a relevant currency
    xau = _by_id_fragment(slate, "dsp_walked_high_accepted_through")
    assert xau["minutes_to_nearest_high_impact"] == 135.0


def test_frozen_21aug_news_calendar_is_not_live_high(desk_cfg, desk_repo):
    """21 Aug dump cannot fold as live HIGH even if a HIGH print sits in the window."""
    frozen = {
        "updated_at": "2026-08-21T12:25:00Z",
        "kind": "full_history_plus_scheduled",
        "events": [{
            "event": "US Non-Farm Payrolls (frozen dump)",
            "impact": "HIGH",
            "currency": "USD",
            "scheduled_utc": "2026-08-25T01:00:00Z",
        }],
    }
    path = desk_repo / "data" / "news_calendar.json"
    path.write_text(json.dumps(frozen), encoding="utf-8")
    desk_cfg.calendar_path = path
    slate, _ = _slate(desk_cfg)
    names = {e["event"] for e in slate["calendar"]}
    assert "US Non-Farm Payrolls (frozen dump)" not in names
    skip = slate.get("calendar_fold") or {}
    reasons = " ".join(str(s.get("reason") or "") for s in skip.get("skipped") or [])
    assert "stamp_stale" in reasons or "valid_until" in reasons or "live_false" in reasons


def test_f5_high_calendar_nfp_folds_when_dump_frozen(desk_cfg, desk_repo):
    """Live HIGH is f5_high_calendar / spine (NFP), not the 21 Aug dump."""
    frozen = {
        "updated_at": "2026-08-21T12:25:00Z",
        "events": [{
            "event": "US Non-Farm Payrolls (frozen dump)",
            "impact": "HIGH",
            "currency": "USD",
            "scheduled_utc": "2026-08-25T01:00:00Z",
        }],
    }
    dump = desk_repo / "data" / "news_calendar.json"
    dump.write_text(json.dumps(frozen), encoding="utf-8")
    live = {
        "schema": "gtos.f5.high_calendar.v1",
        "updated_utc": "2026-08-29T12:00:00Z",
        "events": [{
            "name": "US Nonfarm Payrolls (NFP)",
            "impact": "HIGH",
            "official_high": True,
            "scheduled_utc": "2026-08-25T01:15:00Z",
            "currency": "USD",
            "event_type": "nfp",
        }],
    }
    high = (
        desk_repo / "pipeline_state" / "ultimate_book" / "operator"
        / "judgment" / "state" / "f5_high_calendar.json"
    )
    high.parent.mkdir(parents=True, exist_ok=True)
    high.write_text(json.dumps(live), encoding="utf-8")
    desk_cfg.calendar_path = dump
    desk_cfg.f5_high_calendar_path = high
    slate, _ = _slate(desk_cfg)
    events = {e["event"]: e for e in slate["calendar"]}
    assert "US Non-Farm Payrolls (frozen dump)" not in events
    assert "US Nonfarm Payrolls (NFP)" in events
    assert events["US Nonfarm Payrolls (NFP)"]["impact"] == "HIGH"
    used = {u["name"] for u in (slate.get("calendar_fold") or {}).get("used") or []}
    assert "f5_high_calendar" in used
    skipped = {s["name"] for s in (slate.get("calendar_fold") or {}).get("skipped") or []}
    assert "news_calendar" in skipped


# ---------------------------------------------------------------------------
# clock/session block
# ---------------------------------------------------------------------------
def test_clock_block(desk_cfg):
    slate, _ = _slate(desk_cfg)
    clock = slate["clock"]
    assert clock["now_utc"].startswith("2026-08-24T23:45")
    assert clock["session"] == "asia"           # 23:45 UTC is inside 21:00-07:00
    assert clock["minutes_into_session"] == 165
    assert clock["day_of_week"] == "Monday"
    assert clock["is_weekend_utc"] is False
    # FTMO-Server3 on 2026-08-24 (US EDT): broker wall = UTC+3
    assert clock["broker_utc_offset_hours"] == 3.0
    assert clock["broker_wall_time"].startswith("2026-08-25T02:45")
    assert clock["minutes_to_friday_close"] > 0
    assert clock["in_friday_close_window"] is False


# ---------------------------------------------------------------------------
# cursor tailing + durable state
# ---------------------------------------------------------------------------
def test_cursor_incremental_and_close_applies(desk_cfg):
    slate1, _ = _slate(desk_cfg)
    lines_after_first = slate1["counters"]["events_lines"]
    assert OPEN_TICKET in {p["ticket"] for p in slate1["open_positions"]}

    close = {
        "event": "f5_trade_closed", "schema": "gtos.f5.minimal_size_event.v1",
        "namespace": "operator", "ticket": OPEN_TICKET,
        "symbol": "EURUSD", "sleeve": "dsp_small_bar_sit_on_20high_rejects",
        "broker_net_pnl_usd": -75.0, "realised_r": -1.0,
        "ts_utc": "2026-08-24T23:50:00+00:00",
    }
    with open(desk_cfg.events_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(close) + "\n")

    slate2, _ = _slate(desk_cfg, now=FIXED_NOW + timedelta(minutes=10))
    assert OPEN_TICKET not in {p["ticket"] for p in slate2["open_positions"]}
    # byte cursor: exactly ONE new line was read, nothing re-ingested
    assert slate2["counters"]["events_lines"] == lines_after_first + 1
    assert slate2["fingerprint"] != slate1["fingerprint"]


def test_fingerprint_ignores_clock_churn(desk_cfg):
    slate1, _ = _slate(desk_cfg)
    slate2, _ = _slate(desk_cfg, now=FIXED_NOW + timedelta(minutes=2))
    assert slate1["fingerprint"] == slate2["fingerprint"]


def test_partial_trailing_line_is_left_for_next_cycle(desk_cfg):
    with open(desk_cfg.events_path, "a", encoding="utf-8") as handle:
        handle.write('{"event": "f5_fill", "ticket": 999999, "symbol": "XAUUSD"')  # no newline
    slate, _ = _slate(desk_cfg)
    assert 999999 not in {p["ticket"] for p in slate["open_positions"]}
    # completing the line makes it land on the next build
    with open(desk_cfg.events_path, "a", encoding="utf-8") as handle:
        handle.write(', "sleeve": "metals_core", "ts_utc": "2026-08-24T23:50:00+00:00"}\n')
    slate2, _ = _slate(desk_cfg, now=FIXED_NOW + timedelta(minutes=5))
    assert 999999 in {p["ticket"] for p in slate2["open_positions"]}


def test_f5_slate_intent_geometry_reaches_the_candidate(desk_cfg):
    """Direction + stop on f5_slate must land on the standing intent before fill.

    Without this the resident judge abstains (PASS) and the book places unjudged.
    """
    slate1, _ = _slate(desk_cfg)
    xau = _by_id_fragment(slate1, "dsp_walked_high_accepted_through")
    assert xau is not None
    assert "direction" not in xau
    assert "geometry" not in xau

    event = {
        "event": "f5_slate",
        "namespace": "operator",
        "ts_utc": "2026-08-24T23:46:00+00:00",
        "n_intents": 1,
        "intents": [{
            "sleeve": "dsp_walked_high_accepted_through",
            "symbol": "XAUUSD",
            "decision_day": "2026-08-24",
            "direction": "SHORT",
            "entry": 3400.0,
            "stop": 3405.0,
            "target": 3380.0,
        }],
    }
    with open(desk_cfg.events_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(event) + "\n")

    slate2, _ = _slate(desk_cfg, now=FIXED_NOW + timedelta(minutes=2))
    xau2 = _by_id_fragment(slate2, "dsp_walked_high_accepted_through")
    assert xau2 is not None
    assert xau2["direction"] == "SHORT"
    assert xau2["geometry"] == {"entry": 3400.0, "stop": 3405.0, "target": 3380.0}


def test_missing_streams_build_empty_slate(tmp_path):
    cfg = composer.ComposerConfig(repo_root=tmp_path / "empty_repo")
    slate, path = composer.build_slate(cfg, now_utc=FIXED_NOW)
    assert slate["candidates"] == []
    assert slate["open_positions"] == []
    assert path is not None  # still archived; a quiet desk is visible, not absent


def test_phantom_open_rows_hidden_from_slate():
    """Rows whose close the stream never saw (nulls, ancient timestamps) must not
    reach the judge; live-observed and fresh-fill rows must."""
    from datetime import datetime, timedelta, timezone
    from scripts.f5_desk import composer

    now = datetime(2026, 8, 25, 3, 0, tzinfo=timezone.utc)
    phantom = {"ticket": 1, "symbol": "UK100", "sleeve": "idxrev"}
    phantom_old = {"ticket": 2, "symbol": "JP225", "sleeve": "idxrev",
                   "opened_utc": (now - timedelta(days=9)).isoformat()}
    real_checked = {"ticket": 3, "symbol": "BTCUSD", "stop_now": 75589.06,
                    "opened_utc": (now - timedelta(days=4)).isoformat(),
                    "last_checked_utc": (now - timedelta(hours=1)).isoformat()}
    real_restart_refresh = {"ticket": 4, "symbol": "GER40", "stop_now": 26240.32,
                            "opened_utc": (now - timedelta(hours=11)).isoformat()}
    fresh_fill_no_geometry = {"ticket": 5, "symbol": "EURUSD",
                              "opened_utc": (now - timedelta(minutes=5)).isoformat()}
    stale_checked = {"ticket": 6, "symbol": "XAUUSD", "stop_now": 4600.0,
                     "opened_utc": (now - timedelta(days=6)).isoformat(),
                     "last_checked_utc": (now - timedelta(days=3)).isoformat()}

    assert composer._open_row_is_live(phantom, now) is False
    assert composer._open_row_is_live(phantom_old, now) is False
    assert composer._open_row_is_live(real_checked, now) is True
    assert composer._open_row_is_live(real_restart_refresh, now) is True
    assert composer._open_row_is_live(fresh_fill_no_geometry, now) is True
    assert composer._open_row_is_live(stale_checked, now) is False
