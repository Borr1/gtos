from __future__ import annotations

import json
from pathlib import Path

from scripts import analyze_raw_ohlc_path_scaling_v2_confluence as mod


def _row(
    event_key: str,
    variant: str,
    net_r: float,
    *,
    candle_close_utc: str = "2026-01-01T13:00:00+00:00",
    locks: list[dict] | None = None,
) -> dict:
    return {
        "event_key": event_key,
        "candle_close_utc": candle_close_utc,
        "variant_id": variant,
        "symbol": "XAUUSD",
        "session": "ny",
        "mechanical_side": "LONG",
        "mechanical_entry": 2000.0,
        "mechanical_sl": 1990.0,
        "mechanical_tp": 2030.0,
        "selected_timeframe": "M15",
        "role": "dominance_watchlist",
        "raw_cohort_key": "XAUUSD|ny|bullish|D1",
        "outcome": "LOCK_STOP" if locks else "SL",
        "locks_triggered": locks or [],
        "net_r_by_cost": {"0.05": net_r},
    }


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


def _write(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def test_confluence_classifies_fvg_only_ob_only_and_sequence(tmp_path):
    event_log = tmp_path / "events.jsonl"
    rows = []
    for event_key, values, fvg_lock, ob_lock in [
        (
            "both",
            {mod.BASELINE: -0.5, mod.SWING: 0.0, mod.FVG: 0.8, mod.OB: 1.1, mod.COMPOSITE: 0.8},
            _lock("FVG_MIDPOINT", "2026-01-01T14:00:00+00:00", 0.3, 4),
            _lock("OB_PROTECTIVE_BOUNDARY", "2026-01-01T14:30:00+00:00", 0.5, 6),
        ),
        (
            "fvg_only",
            {mod.BASELINE: -1.0, mod.SWING: -1.0, mod.FVG: 0.6, mod.OB: -1.0, mod.COMPOSITE: 0.6},
            _lock("FVG_MIDPOINT", "2026-01-01T15:00:00+00:00", 0.4, 8),
            None,
        ),
        (
            "ob_only",
            {mod.BASELINE: 0.2, mod.SWING: 0.2, mod.FVG: 0.2, mod.OB: 0.9, mod.COMPOSITE: 0.9},
            None,
            _lock("OB_PROTECTIVE_BOUNDARY", "2026-01-01T16:00:00+00:00", 0.7, 12),
        ),
    ]:
        for variant, net_r in values.items():
            lock = fvg_lock if variant == mod.FVG else ob_lock if variant == mod.OB else None
            if variant == mod.COMPOSITE:
                lock = fvg_lock or ob_lock
            rows.append(_row(event_key, variant, net_r, locks=[lock] if lock else []))
    _write(event_log, rows)

    payload = mod.build_payload(event_log_path=event_log)
    full = payload["slices"]["full_resolved"]

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert full["n"] == 3
    assert full["entry_consistency_violations"] == 0
    assert full["improvement_vs_j46_buckets"]["both_improve_vs_j46"]["n"] == 1
    assert full["improvement_vs_j46_buckets"]["fvg_only_improves_vs_j46"]["n"] == 1
    assert full["improvement_vs_j46_buckets"]["ob_only_improves_vs_j46"]["n"] == 1
    assert full["lock_firing_buckets"]["both_fired"]["n"] == 1
    assert full["lock_firing_buckets"]["fvg_only_fired"]["n"] == 1
    assert full["lock_firing_buckets"]["ob_only_fired"]["n"] == 1
    seq = full["sequence_when_both_fvg_and_ob_fire"]["buckets"]["fvg_then_ob"]
    assert seq["n"] == 1
    assert seq["mean_ob_floor_minus_fvg_floor_r"] == 0.2


def test_confluence_flags_composite_overlock_and_approach_gap(tmp_path):
    event_log = tmp_path / "events.jsonl"
    rows = []
    values = {
        mod.BASELINE: 0.0,
        mod.SWING: 1.4,
        mod.FVG: 1.0,
        mod.OB: 0.8,
        mod.COMPOSITE: 0.5,
    }
    for variant, net_r in values.items():
        rows.append(_row("overlock", variant, net_r))
    _write(event_log, rows)

    payload = mod.build_payload(event_log_path=event_log)
    full = payload["slices"]["full_resolved"]

    assert full["composite_vs_best_single"]["buckets"]["composite_below_best_single"]["n"] == 1
    assert full["composite_vs_best_single"]["mean"] == -0.9
    assert payload["approach_leg_assessment"]["status"] == "NOT_ANSWERABLE_FROM_CURRENT_V2_EVENT_LOG"
    assert "pre_fill_m1_or_m5_path_rows_until_fill_expiry_or_cancel" in payload["approach_leg_assessment"]["required_fields_for_future_test"]
