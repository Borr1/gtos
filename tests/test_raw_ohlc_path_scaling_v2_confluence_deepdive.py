from __future__ import annotations

import json
from pathlib import Path

from scripts import analyze_raw_ohlc_path_scaling_v2_confluence as base
from scripts import analyze_raw_ohlc_path_scaling_v2_confluence_deepdive as mod


def _lock(selector: str, confirmed_time: str, floor_r: float, index: int) -> dict:
    return {
        "selector_id": selector,
        "event_type": selector.lower(),
        "confirmed_time": confirmed_time,
        "source_time": confirmed_time,
        "confirmed_index": index,
        "source_index": index,
        "floor_r": floor_r,
        "price": 2000.0 + floor_r,
    }


def _row(
    event_key: str,
    variant: str,
    net_r: float,
    *,
    candle_close_utc: str,
    symbol: str = "XAUUSD",
    session: str = "ny",
    side: str = "LONG",
    raw_cohort_key: str = "XAUUSD|ny|bullish|D1",
    role: str = "dominance_watchlist",
    locks: list[dict] | None = None,
) -> dict:
    return {
        "event_key": event_key,
        "candle_close_utc": candle_close_utc,
        "variant_id": variant,
        "symbol": symbol,
        "session": session,
        "mechanical_side": side,
        "mechanical_entry": 2000.0,
        "mechanical_sl": 1990.0,
        "mechanical_tp": 2030.0,
        "selected_timeframe": "M15",
        "role": role,
        "raw_cohort_key": raw_cohort_key,
        "outcome": "LOCK_STOP" if locks else "SL",
        "locks_triggered": locks or [],
        "net_r_by_cost": {"0.05": net_r},
    }


def _event_rows(
    event_key: str,
    values: dict[str, float],
    *,
    candle_close_utc: str,
    fvg_lock: dict | None = None,
    ob_lock: dict | None = None,
    **kwargs,
) -> list[dict]:
    rows = []
    for variant, net_r in values.items():
        locks = []
        if variant == base.FVG and fvg_lock:
            locks = [fvg_lock]
        elif variant == base.OB and ob_lock:
            locks = [ob_lock]
        elif variant == base.COMPOSITE:
            locks = [lock for lock in (fvg_lock, ob_lock) if lock]
        rows.append(_row(event_key, variant, net_r, candle_close_utc=candle_close_utc, locks=locks, **kwargs))
    return rows


def _write(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def test_deepdive_buckets_concentration_and_sequence(tmp_path):
    event_log = tmp_path / "events.jsonl"
    rows = []
    rows.extend(
        _event_rows(
            "fvg1",
            {base.BASELINE: -1.0, base.SWING: -1.0, base.FVG: 1.0, base.OB: -1.0, base.COMPOSITE: 1.0},
            candle_close_utc="2026-01-01T13:00:00+00:00",
            fvg_lock=_lock("FVG_MIDPOINT", "2026-01-01T14:00:00+00:00", 0.3, 4),
        )
    )
    rows.extend(
        _event_rows(
            "fvg2",
            {base.BASELINE: -0.5, base.SWING: -0.5, base.FVG: 0.5, base.OB: -0.5, base.COMPOSITE: 0.5},
            candle_close_utc="2026-01-02T13:00:00+00:00",
            fvg_lock=_lock("FVG_MIDPOINT", "2026-01-02T14:00:00+00:00", 0.2, 4),
        )
    )
    rows.extend(
        _event_rows(
            "ob1",
            {base.BASELINE: -1.0, base.SWING: -1.0, base.FVG: -1.0, base.OB: 1.0, base.COMPOSITE: 1.0},
            candle_close_utc="2026-01-03T13:00:00+00:00",
            symbol="XAGUSD",
            raw_cohort_key="XAGUSD|london|bullish|H4+H1_consensus",
            session="london",
            ob_lock=_lock("OB_PROTECTIVE_BOUNDARY", "2026-01-03T14:00:00+00:00", 0.6, 7),
        )
    )
    rows.extend(
        _event_rows(
            "both1",
            {base.BASELINE: -1.0, base.SWING: 0.0, base.FVG: 0.4, base.OB: 0.8, base.COMPOSITE: 0.2},
            candle_close_utc="2025-06-01T13:00:00+00:00",
            fvg_lock=_lock("FVG_MIDPOINT", "2025-06-01T14:00:00+00:00", 0.2, 4),
            ob_lock=_lock("OB_PROTECTIVE_BOUNDARY", "2025-06-01T14:30:00+00:00", 0.6, 8),
        )
    )
    rows.extend(
        _event_rows(
            "composite",
            {base.BASELINE: -1.0, base.SWING: -1.0, base.FVG: -1.0, base.OB: -1.0, base.COMPOSITE: 0.5},
            candle_close_utc="2024-06-01T13:00:00+00:00",
            symbol="USDJPY",
            raw_cohort_key="USDJPY|tokyo|bearish|D1",
            session="tokyo",
            side="SHORT",
        )
    )
    _write(event_log, rows)

    payload = mod.build_payload(event_log_path=event_log)

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["discovery_label"] == "DISCOVERY_ONLY_NOT_REGISTERED"
    assert payload["slices"]["full_resolved"]["n"] == 5
    assert payload["bucket_deep_dives"]["fvg_only_improves_vs_j46"]["metrics"]["n"] == 2
    assert payload["bucket_deep_dives"]["ob_only_improves_vs_j46"]["metrics"]["n"] == 1
    assert payload["bucket_deep_dives"]["both_improve_vs_j46"]["metrics"]["n"] == 1

    fvg_symbol_concentration = payload["bucket_deep_dives"]["fvg_only_improves_vs_j46"]["concentration"][0]
    assert fvg_symbol_concentration["dimensions"] == ["symbol"]
    assert fvg_symbol_concentration["top_share"] == 1.0
    assert fvg_symbol_concentration["cap_exceeded"] is True

    seq_rows = payload["ob_after_fvg_tail_preservation"]["full_resolved"]["rows"]
    fvg_then_ob = [row for row in seq_rows if row["sequence"] == "fvg_then_ob"][0]
    assert fvg_then_ob["n"] == 1
    assert fvg_then_ob["ob_minus_fvg_mean_r"] == 0.4
    assert fvg_then_ob["mean_ob_floor_minus_fvg_floor_r"] == 0.4

    assert payload["composite_arbitration"]["full_resolved"]["global"]["positive_n"] == 1
    assert "actual_broker_r_if_available" in payload["forward_only_fields_for_v2b"]


def test_deepdive_writes_reports_with_required_labels(tmp_path):
    event_log = tmp_path / "events.jsonl"
    rows = _event_rows(
        "single",
        {base.BASELINE: -1.0, base.SWING: -1.0, base.FVG: 0.5, base.OB: -1.0, base.COMPOSITE: 0.5},
        candle_close_utc="2026-01-01T13:00:00+00:00",
        fvg_lock=_lock("FVG_MIDPOINT", "2026-01-01T14:00:00+00:00", 0.3, 4),
    )
    _write(event_log, rows)
    payload = mod.build_payload(event_log_path=event_log)

    out_json = tmp_path / "report.json"
    out_md = tmp_path / "report.md"
    mod.write_json(payload, out_json)
    mod.write_markdown(payload, out_md)

    assert json.loads(out_json.read_text(encoding="utf-8"))["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    md = out_md.read_text(encoding="utf-8")
    assert "NO_PROMOTION_VERDICT" in md
    assert "DISCOVERY_ONLY_NOT_REGISTERED" in md
    assert "pre_fill_delivery_path_rows" in md
