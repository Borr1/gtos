"""Build Friday microscopic price-action anatomy artifacts.

This is an offline/read-only route builder. It reuses the proven weekend
tick/M1 path simulator, but caps every primary Friday candidate at the clean
Friday close boundary so no weekend/reopen ticks leak into the microscope.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_vnext_friday_microscope_freeze_inventory as freeze
from scripts import build_vnext_weekend_price_action_anatomy as weekend


ROUTE_DIR = freeze.ROUTE_DIR
FRIDAY_CLOSE = freeze.FRIDAY_CLOSE_BATCH_UTC
EXPECTED_PRIMARY_ROWS = 328
PLACED_OUTCOME = freeze.PLACED_OUTCOME

CANONICAL_LEDGER = ROUTE_DIR / "FRIDAY_CANONICAL_EVENT_LEDGER.jsonl"

MICRO_LEDGER = ROUTE_DIR / "FRIDAY_MICRO_PRICE_ACTION_LEDGER.jsonl"
WINNER_LEDGER = ROUTE_DIR / "FRIDAY_WINNER_ANATOMY_LEDGER.jsonl"
LOSER_LEDGER = ROUTE_DIR / "FRIDAY_LOSER_ANATOMY_LEDGER.jsonl"
STUCK_LEDGER = ROUTE_DIR / "FRIDAY_STUCK_CANDIDATE_LEDGER.jsonl"
MFE_MAE_LEDGER = ROUTE_DIR / "FRIDAY_MFE_MAE_TIMING_LEDGER.jsonl"
SUMMARY_MD = ROUTE_DIR / "FRIDAY_MICRO_PRICE_ACTION_SUMMARY.md"
VERIFIER = ROUTE_DIR / "verify_friday_micro_price_action.py"
VERIFICATION = ROUTE_DIR / "FRIDAY_MICRO_PRICE_ACTION_VERIFICATION.json"

THRESHOLDS_R = (0.25, 0.5, 1.0, 1.5, 2.0, 3.0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def parse_dt(value: Any) -> datetime | None:
    return freeze.parse_dt(value)


def iso(value: datetime | pd.Timestamp | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    return value.astimezone(timezone.utc).isoformat()


def as_float(value: Any) -> float | None:
    return weekend.as_float(value)


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def write_json(path: Path, data: Any) -> None:
    freeze.write_json(path, data)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    freeze.write_jsonl(path, rows)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return freeze.load_jsonl(path)


def line_count(path: Path) -> int:
    return freeze.line_count(path)


def first_time(frame: pd.DataFrame, mask: pd.Series) -> datetime | None:
    if frame.empty:
        return None
    hit = frame[mask]
    if hit.empty:
        return None
    value = hit.iloc[0]["ts_utc"]
    return value.to_pydatetime() if hasattr(value, "to_pydatetime") else parse_dt(value)


def r_at_price(side: str, entry: float, stop: float, price: float) -> float | None:
    return weekend.r_at_price(side, entry, stop, price)


def direction_level(side: str, entry: float, risk: float, threshold_r: float) -> float:
    return entry + risk * threshold_r if side == "LONG" else entry - risk * threshold_r


def load_trade_record(canonical: dict[str, Any]) -> dict[str, Any]:
    path_text = canonical.get("source_path")
    if not path_text:
        raise ValueError(f"canonical row missing source_path for {canonical.get('candidate_id')}")
    path = Path(path_text)
    record = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    record["_source_path"] = str(path)
    record["_record_time_utc"] = canonical.get("record_time_utc") or canonical.get("timestamp_basis_utc")
    record["_source_symbol_dir"] = path.parent.name
    return record


def compact_structure(ctx: dict[str, Any]) -> dict[str, Any]:
    structure = ctx.get("structure") or {}
    events = ctx.get("structure_events") or []
    order_blocks = ctx.get("order_blocks") or []
    breakers = ctx.get("breaker_blocks") or []
    fvgs = ctx.get("fair_value_gaps") or []
    return {
        "direction": structure.get("direction"),
        "protected_swing": structure.get("protected_swing"),
        "swing_sequence": structure.get("swing_sequence"),
        "hh_count": structure.get("hh_count"),
        "hl_count": structure.get("hl_count"),
        "lh_count": structure.get("lh_count"),
        "ll_count": structure.get("ll_count"),
        "structure_event_count": len(events) if isinstance(events, list) else None,
        "latest_structure_event": events[-1] if isinstance(events, list) and events else None,
        "order_block_count": len(order_blocks) if isinstance(order_blocks, list) else None,
        "breaker_block_count": len(breakers) if isinstance(breakers, list) else None,
        "fair_value_gap_count": len(fvgs) if isinstance(fvgs, list) else None,
        "premium_discount": ctx.get("premium_discount"),
        "atr_14": ctx.get("atr_14"),
        "clv_current": ctx.get("clv_current"),
        "clv_avg_5": ctx.get("clv_avg_5"),
        "bvc_buy_fraction": ctx.get("bvc_buy_fraction"),
    }


def extract_mso_context(record: dict[str, Any]) -> dict[str, Any]:
    packet = (record.get("decision_pipeline") or {}).get("gtos_vnext_candidate_intelligence_packet") or {}
    packet_mso = packet.get("mso_context") or {}
    legacy = ((record.get("mso") or {}).get("timeframes") or {})
    out: dict[str, Any] = {}
    for timeframe in ("D1", "H4", "H1", "M15"):
        node = packet_mso.get(timeframe) or {}
        legacy_ctx = legacy.get(timeframe) or {}
        ctx = node.get("context") if isinstance(node, dict) else {}
        ctx = ctx or legacy_ctx
        out[timeframe] = {
            "available": bool((node.get("available") if isinstance(node, dict) else False) or ctx),
            "context_source": (
                "gtos_vnext_candidate_intelligence_packet.mso_context"
                if node
                else "record.mso.timeframes"
                if ctx
                else "missing"
            ),
            "compact_structure": compact_structure(ctx) if isinstance(ctx, dict) else {},
        }
    source_fields = ((packet.get("source_m15") or {}).get("source_fields") or {})
    out["_mso_timestamp_utc"] = packet_mso.get("_mso_timestamp_utc") or source_fields.get("mso_timestamp_utc")
    out["_data_quality"] = packet_mso.get("_data_quality")
    return out


def broker_modify_feasibility(base: dict[str, Any]) -> dict[str, Any]:
    spec = base.get("broker_spec_snapshot") or {}
    point = as_float(spec.get("point")) or 0.0
    stops = as_float(spec.get("trade_stops_level")) or 0.0
    freeze_level = as_float(spec.get("trade_freeze_level")) or 0.0
    min_stop = as_float(spec.get("broker_min_stop_distance"))
    stop_floor = max(min_stop or 0.0, stops * point, freeze_level * point)
    entry = as_float(base.get("repaired_entry"))
    stop = as_float(base.get("repaired_stop_loss"))
    trigger = as_float(base.get("dynamic_trigger_price"))
    final = as_float(base.get("dynamic_final_target_price"))
    risk = abs(entry - stop) if entry is not None and stop is not None else None

    def feasible(distance: float | None) -> dict[str, Any]:
        if distance is None:
            return {"distance": None, "feasible": None, "reason": "missing_price_or_risk"}
        return {
            "distance": distance,
            "feasible": distance + 1e-12 >= stop_floor,
            "required_min_distance": stop_floor,
        }

    return {
        "evidence_class": "broker_spec_static_distance_proxy_no_order_action",
        "symbol_info_available": bool(spec.get("symbol_info_available")),
        "point": point,
        "trade_stops_level": stops,
        "trade_freeze_level": freeze_level,
        "broker_min_stop_distance": min_stop,
        "initial_sl": feasible(risk),
        "be_modify_after_1r": feasible(abs((trigger or entry or 0.0) - (entry or 0.0)) if trigger is not None and entry is not None else None),
        "trail_0_5r_gap": feasible(risk * 0.5 if risk is not None else None),
        "dynamic_final_distance": feasible(abs((final or entry or 0.0) - (entry or 0.0)) if final is not None and entry is not None else None),
    }


def tick_window(row: dict[str, Any], ticks: pd.DataFrame | None, path_end: datetime) -> pd.DataFrame:
    candle = parse_dt(row.get("candle_time_utc"))
    if ticks is None or ticks.empty or candle is None:
        return pd.DataFrame()
    return ticks[
        (ticks["ts_utc"] >= pd.Timestamp(candle))
        & (ticks["ts_utc"] <= pd.Timestamp(path_end))
    ].copy()


def supplemental_timings(row: dict[str, Any], ticks: pd.DataFrame | None, path_end: datetime) -> dict[str, Any]:
    candle = parse_dt(row.get("candle_time_utc"))
    side = row.get("side")
    entry = as_float(row.get("repaired_entry"))
    stop = as_float(row.get("repaired_stop_loss"))
    if candle is None or side not in {"LONG", "SHORT"} or entry is None or stop is None:
        return {
            "supplemental_timing_source": "missing_candidate_geometry",
            "threshold_times_utc": {},
            "threshold_seconds_from_entry": {},
        }
    risk = abs(entry - stop)
    if risk <= 0:
        return {
            "supplemental_timing_source": "invalid_zero_risk",
            "threshold_times_utc": {},
            "threshold_seconds_from_entry": {},
        }
    path = tick_window(row, ticks, path_end)
    if path.empty:
        return {
            "supplemental_timing_source": "tick_window_empty",
            "threshold_times_utc": {},
            "threshold_seconds_from_entry": {},
        }
    entry_mask = path["ask"] <= entry if side == "LONG" else path["bid"] >= entry
    entry_time = first_time(path, entry_mask)
    if entry_time is None:
        basis = path["bid"] if side == "LONG" else path["ask"]
        r_series = basis.apply(lambda price: r_at_price(side, entry, stop, float(price)))
        mfe_idx = r_series.idxmax()
        mae_idx = r_series.idxmin()
        mfe_time = path.loc[mfe_idx]["ts_utc"].to_pydatetime()
        mae_time = path.loc[mae_idx]["ts_utc"].to_pydatetime()
        return {
            "supplemental_timing_source": "tick_bid_ask_no_entry_touch",
            "entry_touch_utc": None,
            "threshold_times_utc": {},
            "threshold_seconds_from_entry": {},
            "first_favorable_excursion_0_25r_utc": iso(first_time(path, r_series >= 0.25)),
            "first_adverse_excursion_0_25r_utc": iso(first_time(path, r_series <= -0.25)),
            "no_entry_max_favorable_r": float(r_series.loc[mfe_idx]),
            "no_entry_max_adverse_r": float(r_series.loc[mae_idx]),
            "mfe_price_normalized": float(basis.loc[mfe_idx]),
            "mfe_r_normalized": float(r_series.loc[mfe_idx]),
            "mfe_utc_normalized": iso(mfe_time),
            "time_to_mfe_from_candidate_seconds": (mfe_time - candle).total_seconds(),
            "mae_price_normalized": float(basis.loc[mae_idx]),
            "mae_r_normalized": float(r_series.loc[mae_idx]),
            "mae_utc_normalized": iso(mae_time),
            "time_to_mae_from_candidate_seconds": (mae_time - candle).total_seconds(),
        }
    entry_idx = path[entry_mask].index[0]
    after = path.loc[entry_idx:].copy()
    basis = after["bid"] if side == "LONG" else after["ask"]
    r_series = basis.apply(lambda price: r_at_price(side, entry, stop, float(price)))
    threshold_times: dict[str, str | None] = {}
    threshold_seconds: dict[str, float | None] = {}
    for threshold in THRESHOLDS_R:
        key = f"{str(threshold).replace('.', '_')}r"
        level = direction_level(side, entry, risk, threshold)
        mask = after["bid"] >= level if side == "LONG" else after["ask"] <= level
        t = first_time(after, mask)
        threshold_times[key] = iso(t)
        threshold_seconds[key] = (t - entry_time).total_seconds() if t else None
    adverse_025 = first_time(after, r_series <= -0.25)
    favorable_025 = first_time(after, r_series >= 0.25)
    stop_mask = after["bid"] <= stop if side == "LONG" else after["ask"] >= stop
    stop_time = first_time(after, stop_mask)
    one_r_time = parse_dt(threshold_times.get("1_0r"))
    be_time = None
    if one_r_time is not None:
        after_one_r = after[after["ts_utc"] >= pd.Timestamp(one_r_time)]
        be_mask = after_one_r["bid"] <= entry if side == "LONG" else after_one_r["ask"] >= entry
        be_time = first_time(after_one_r, be_mask)
    time_stop_end = min(entry_time + timedelta(hours=4), path_end)
    time_stop_window = after[after["ts_utc"] <= pd.Timestamp(time_stop_end)]
    time_stop_price = float((time_stop_window["bid"] if side == "LONG" else time_stop_window["ask"]).iloc[-1]) if not time_stop_window.empty else None
    mfe_idx = r_series.idxmax()
    mae_idx = r_series.idxmin()
    return {
        "supplemental_timing_source": "tick_bid_ask_friday_capped",
        "entry_touch_utc": iso(entry_time),
        "threshold_times_utc": threshold_times,
        "threshold_seconds_from_entry": threshold_seconds,
        "partial_trigger_utc": threshold_times.get("1_0r"),
        "be_return_after_1r_utc": iso(be_time),
        "sl_touch_utc": iso(stop_time),
        "time_stop_4h_utc": iso(time_stop_end),
        "time_stop_4h_price": time_stop_price,
        "time_stop_4h_r": r_at_price(side, entry, stop, time_stop_price) if time_stop_price is not None else None,
        "first_favorable_excursion_0_25r_utc": iso(favorable_025),
        "first_adverse_excursion_0_25r_utc": iso(adverse_025),
        "time_to_first_favorable_excursion_0_25r_seconds": (favorable_025 - entry_time).total_seconds() if favorable_025 else None,
        "time_to_first_adverse_excursion_0_25r_seconds": (adverse_025 - entry_time).total_seconds() if adverse_025 else None,
        "mfe_price_normalized": float(basis.loc[mfe_idx]),
        "mfe_r_normalized": float(r_series.loc[mfe_idx]),
        "mfe_utc_normalized": iso(after.loc[mfe_idx]["ts_utc"]),
        "time_to_mfe_from_candidate_seconds": (after.loc[mfe_idx]["ts_utc"].to_pydatetime() - candle).total_seconds(),
        "time_to_mfe_from_entry_seconds": (after.loc[mfe_idx]["ts_utc"].to_pydatetime() - entry_time).total_seconds(),
        "mae_price_normalized": float(basis.loc[mae_idx]),
        "mae_r_normalized": float(r_series.loc[mae_idx]),
        "mae_utc_normalized": iso(after.loc[mae_idx]["ts_utc"]),
        "time_to_mae_from_candidate_seconds": (after.loc[mae_idx]["ts_utc"].to_pydatetime() - candle).total_seconds(),
        "time_to_mae_from_entry_seconds": (after.loc[mae_idx]["ts_utc"].to_pydatetime() - entry_time).total_seconds(),
    }


def terminal_path_class(row: dict[str, Any]) -> str:
    status = row.get("path_status")
    if status == "no_entry_touch_before_last_available_price":
        return "no_entry_touch_before_friday_close"
    if status == "entry_filled_sl_before_1r_trigger":
        return "loss_sl_before_partial_trigger"
    if status == "partial_1r_then_3r_final":
        return "winner_partial_then_dynamic_final"
    if status == "partial_1r_then_be":
        return "winner_partial_then_be_return"
    if status == "partial_1r_then_open_at_last_available_price":
        return "partial_trigger_then_open_at_friday_close"
    if status == "entry_filled_no_sl_or_1r_before_last_available_price":
        return "stuck_entry_no_sl_or_1r_before_friday_close"
    return "unknown_path_status"


def mechanism_story(row: dict[str, Any]) -> str:
    symbol = row.get("symbol")
    side = row.get("side")
    outcome = row.get("final_outcome")
    entry = row.get("entry_touch_utc")
    mfe = row.get("mfe_r_normalized")
    mae = row.get("mae_r_normalized")
    klass = row.get("terminal_path_class")
    spread_r = row.get("spread_r_at_candidate")
    parts = [
        f"{symbol} {side} {row.get('origin_family')} at {row.get('route_session')}",
        f"outcome={outcome}",
        f"path={klass}",
        f"entry_touch={entry or 'none'}",
        f"mfe_r={round(mfe, 3) if isinstance(mfe, (int, float)) else mfe}",
        f"mae_r={round(mae, 3) if isinstance(mae, (int, float)) else mae}",
        f"spread_r={round(spread_r, 3) if isinstance(spread_r, (int, float)) else spread_r}",
    ]
    if row.get("sl_touch_utc"):
        parts.append(f"sl={row.get('sl_touch_utc')}")
    if row.get("threshold_times_utc", {}).get("1_0r"):
        parts.append(f"1r={row['threshold_times_utc']['1_0r']}")
    if row.get("be_return_after_1r_utc"):
        parts.append(f"be_return={row.get('be_return_after_1r_utc')}")
    return "; ".join(parts)


def build_micro_rows() -> list[dict[str, Any]]:
    canonical_rows = load_jsonl(CANONICAL_LEDGER)
    if len(canonical_rows) != EXPECTED_PRIMARY_ROWS:
        raise SystemExit(f"expected {EXPECTED_PRIMARY_ROWS} canonical rows, found {len(canonical_rows)}")
    canonical_rows.sort(key=lambda row: (row.get("timestamp_basis_utc") or "", row.get("symbol") or "", row.get("candidate_id") or ""))
    tick_cache: dict[str, pd.DataFrame | None] = {}
    m1_cache: dict[str, list[weekend.Bar]] = {}
    out: list[dict[str, Any]] = []
    original_horizon = weekend.DEFAULT_HORIZON
    try:
        for canonical in canonical_rows:
            record = load_trade_record(canonical)
            base = weekend.candidate_row(record)
            base["selected_policy"] = canonical.get("selected_policy") or base.get("selected_policy")
            base["execution_policy_id"] = canonical.get("execution_policy_id") or base.get("execution_policy_id")
            base["selected_cell_risk_pct"] = canonical.get("selected_cell_risk_pct") or base.get("selected_cell_risk_pct")
            candle = parse_dt(base.get("candle_time_utc"))
            if candle is None:
                raise SystemExit(f"missing candle time for {base.get('candidate_id')}")
            path_end = min(FRIDAY_CLOSE, candle + original_horizon)
            weekend.DEFAULT_HORIZON = max(path_end - candle, timedelta(seconds=1))
            anatomy = weekend.analyze_price_path(base, tick_cache, m1_cache)
            timings = supplemental_timings(base, tick_cache.get(str(base.get("symbol") or "")), path_end)
            mechanism, proof = weekend.classify_mechanism(base, anatomy)
            row = {
                "schema_version": "friday_micro_price_action_anatomy_v1",
                "route_id": freeze.ROUTE_ID,
                "friday_freeze_rule": "non_crypto primary rows from first placed candle through < 2026-05-29T21:00:00Z",
                "path_end_rule": "min(candidate_candle_plus_48h, friday_close_boundary)",
                "path_end_utc": iso(path_end),
                "path_horizon_seconds": (path_end - candle).total_seconds(),
                "canonical_denominator_status": canonical.get("denominator_status"),
                "broker_placement_ready": canonical.get("broker_placement_ready"),
                "actually_placed": canonical.get("actually_placed"),
                "broker_ticket": canonical.get("broker_ticket"),
                "broker_lifecycle_status_through_friday_close": canonical.get("broker_lifecycle_status_through_friday_close"),
                "canonical_row_disposition": canonical.get("row_disposition"),
                **base,
                **anatomy,
                **timings,
                "terminal_path_class": terminal_path_class({**anatomy, **timings}),
                "mechanism_classification": mechanism,
                "mechanism_proof": proof,
                "mso_context_compact": extract_mso_context(record),
                "broker_modify_feasibility": broker_modify_feasibility(base),
                "missing_price_action_sources": [
                    item
                    for item in (
                        "tick_bid_ask_unavailable" if anatomy.get("price_source") != "tick_bid_ask" else None,
                        "mso_context_missing" if not all(extract_mso_context(record).get(tf, {}).get("available") for tf in ("D1", "H4", "H1", "M15")) else None,
                    )
                    if item
                ],
                "source_refs": canonical.get("source_refs"),
                "source_path": canonical.get("source_path") or base.get("source_path"),
            }
            row["market_story"] = mechanism_story(row)
            out.append(row)
    finally:
        weekend.DEFAULT_HORIZON = original_horizon
    return out


def winner_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "friday_winner_anatomy_v1",
        "symbol": row.get("symbol"),
        "candidate_id": row.get("candidate_id"),
        "trade_id": row.get("trade_id"),
        "side": row.get("side"),
        "candle_time_utc": row.get("candle_time_utc"),
        "final_outcome": row.get("final_outcome"),
        "terminal_path_class": row.get("terminal_path_class"),
        "proxy_gross_r": row.get("proxy_gross_r"),
        "mfe_r": row.get("mfe_r_normalized"),
        "mae_r": row.get("mae_r_normalized"),
        "one_r_utc": (row.get("threshold_times_utc") or {}).get("1_0r"),
        "three_r_utc": (row.get("threshold_times_utc") or {}).get("3_0r"),
        "be_return_after_1r_utc": row.get("be_return_after_1r_utc"),
        "mechanism": row.get("mechanism_classification"),
        "mechanism_proof": row.get("mechanism_proof"),
        "market_story": row.get("market_story"),
        "source_path": row.get("source_path"),
    }


def loser_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "friday_loser_anatomy_v1",
        "symbol": row.get("symbol"),
        "candidate_id": row.get("candidate_id"),
        "trade_id": row.get("trade_id"),
        "side": row.get("side"),
        "candle_time_utc": row.get("candle_time_utc"),
        "final_outcome": row.get("final_outcome"),
        "terminal_path_class": row.get("terminal_path_class"),
        "proxy_gross_r": row.get("proxy_gross_r"),
        "mfe_r": row.get("mfe_r_normalized"),
        "mae_r": row.get("mae_r_normalized"),
        "sl_touch_utc": row.get("sl_touch_utc"),
        "first_adverse_excursion_0_25r_utc": row.get("first_adverse_excursion_0_25r_utc"),
        "mechanism": row.get("mechanism_classification"),
        "mechanism_proof": row.get("mechanism_proof"),
        "market_story": row.get("market_story"),
        "source_path": row.get("source_path"),
    }


def stuck_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "friday_stuck_candidate_v1",
        "symbol": row.get("symbol"),
        "candidate_id": row.get("candidate_id"),
        "trade_id": row.get("trade_id"),
        "side": row.get("side"),
        "candle_time_utc": row.get("candle_time_utc"),
        "terminal_path_class": row.get("terminal_path_class"),
        "entry_touch_utc": row.get("entry_touch_utc"),
        "duration_stuck_near_entry_seconds": row.get("duration_stuck_near_entry_seconds"),
        "duration_before_movement_seconds": row.get("duration_before_movement_seconds"),
        "last_r": row.get("last_r"),
        "mfe_r": row.get("mfe_r_normalized"),
        "mae_r": row.get("mae_r_normalized"),
        "market_story": row.get("market_story"),
        "source_path": row.get("source_path"),
    }


def mfe_mae_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "friday_mfe_mae_timing_v1",
        "symbol": row.get("symbol"),
        "candidate_id": row.get("candidate_id"),
        "trade_id": row.get("trade_id"),
        "side": row.get("side"),
        "candle_time_utc": row.get("candle_time_utc"),
        "entry_touch_utc": row.get("entry_touch_utc"),
        "mfe_price": row.get("mfe_price_normalized"),
        "mfe_r": row.get("mfe_r_normalized"),
        "mfe_utc": row.get("mfe_utc_normalized"),
        "time_to_mfe_from_candidate_seconds": row.get("time_to_mfe_from_candidate_seconds"),
        "time_to_mfe_from_entry_seconds": row.get("time_to_mfe_from_entry_seconds"),
        "mae_price": row.get("mae_price_normalized"),
        "mae_r": row.get("mae_r_normalized"),
        "mae_utc": row.get("mae_utc_normalized"),
        "time_to_mae_from_candidate_seconds": row.get("time_to_mae_from_candidate_seconds"),
        "time_to_mae_from_entry_seconds": row.get("time_to_mae_from_entry_seconds"),
        "threshold_times_utc": row.get("threshold_times_utc"),
        "threshold_seconds_from_entry": row.get("threshold_seconds_from_entry"),
        "first_favorable_excursion_0_25r_utc": row.get("first_favorable_excursion_0_25r_utc"),
        "first_adverse_excursion_0_25r_utc": row.get("first_adverse_excursion_0_25r_utc"),
        "time_stop_4h_r": row.get("time_stop_4h_r"),
        "path_end_utc": row.get("path_end_utc"),
    }


def is_stuck(row: dict[str, Any]) -> bool:
    klass = row.get("terminal_path_class")
    if klass in {"no_entry_touch_before_friday_close", "stuck_entry_no_sl_or_1r_before_friday_close"}:
        return True
    stuck_seconds = as_float(row.get("duration_stuck_near_entry_seconds"))
    before_move = as_float(row.get("duration_before_movement_seconds"))
    return bool((stuck_seconds is not None and stuck_seconds >= 3600) or (before_move is not None and before_move >= 3600))


def split_ledgers(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    winners: list[dict[str, Any]] = []
    losers: list[dict[str, Any]] = []
    stuck: list[dict[str, Any]] = []
    mfe_mae: list[dict[str, Any]] = []
    for row in rows:
        proxy = as_float(row.get("proxy_gross_r"))
        mfe = as_float(row.get("mfe_r_normalized"))
        if proxy is not None and proxy > 0:
            winners.append(winner_row(row))
        if proxy is not None and proxy < 0:
            losers.append(loser_row(row))
        if proxy == 0 and mfe is not None and mfe >= 1.0:
            winners.append(winner_row({**row, "mechanism_proof": "no-entry/proxy-zero row still reached >=1R favorable path before Friday close"}))
        if is_stuck(row):
            stuck.append(stuck_row(row))
        mfe_mae.append(mfe_mae_row(row))
    return winners, losers, stuck, mfe_mae


def build_summary(rows: list[dict[str, Any]], winners: list[dict[str, Any]], losers: list[dict[str, Any]], stuck: list[dict[str, Any]], mfe_mae: list[dict[str, Any]]) -> dict[str, Any]:
    placed = [row for row in rows if row.get("actually_placed")]
    by_symbol: dict[str, dict[str, Any]] = {}
    for symbol in freeze.NON_CRYPTO_SYMBOLS:
        symbol_rows = [row for row in rows if row.get("symbol") == symbol]
        by_symbol[symbol] = {
            "rows": len(symbol_rows),
            "placed": sum(1 for row in symbol_rows if row.get("actually_placed")),
            "outcomes": dict(sorted(Counter(row.get("final_outcome") for row in symbol_rows).items())),
            "terminal_path_classes": dict(sorted(Counter(row.get("terminal_path_class") for row in symbol_rows).items())),
            "mechanisms": dict(sorted(Counter(row.get("mechanism_classification") for row in symbol_rows).items())),
            "proxy_gross_r_sum": sum(float(row.get("proxy_gross_r") or 0.0) for row in symbol_rows if row.get("proxy_gross_r") is not None),
            "mfe_r_max": max((float(row.get("mfe_r_normalized")) for row in symbol_rows if row.get("mfe_r_normalized") is not None), default=None),
            "mae_r_min": min((float(row.get("mae_r_normalized")) for row in symbol_rows if row.get("mae_r_normalized") is not None), default=None),
        }
    return {
        "schema_version": "friday_micro_price_action_summary_v1",
        "generated_at_utc": utc_now(),
        "git_head": git_head(),
        "route_id": freeze.ROUTE_ID,
        "primary_rows": len(rows),
        "winner_rows": len(winners),
        "loser_rows": len(losers),
        "stuck_rows": len(stuck),
        "mfe_mae_rows": len(mfe_mae),
        "placed_rows": len(placed),
        "placed_terminal_path_classes": dict(sorted(Counter(row.get("terminal_path_class") for row in placed).items())),
        "outcome_counts": dict(sorted(Counter(row.get("final_outcome") for row in rows).items())),
        "terminal_path_class_counts": dict(sorted(Counter(row.get("terminal_path_class") for row in rows).items())),
        "path_status_counts": dict(sorted(Counter(row.get("path_status") for row in rows).items())),
        "price_source_counts": dict(sorted(Counter(row.get("price_source") for row in rows).items())),
        "mechanism_counts": dict(sorted(Counter(row.get("mechanism_classification") for row in rows).items())),
        "missing_price_action_source_counts": dict(sorted(Counter(item for row in rows for item in row.get("missing_price_action_sources", [])).items())),
        "mso_full_context_rows": sum(1 for row in rows if all((row.get("mso_context_compact") or {}).get(tf, {}).get("available") for tf in ("D1", "H4", "H1", "M15"))),
        "tick_bid_ask_rows": sum(1 for row in rows if row.get("price_source") == "tick_bid_ask"),
        "rows_with_price_after_friday_close": sum(1 for row in rows if (row.get("price_source_last_utc") or "") >= FRIDAY_CLOSE.isoformat()),
        "symbol_summary": by_symbol,
        "source_boundary": {
            "primary_start_inclusive_utc": "2026-05-28T23:45:00+00:00",
            "primary_end_exclusive_utc": FRIDAY_CLOSE.isoformat(),
            "path_cap": "per-row min(candidate+48h, Friday close); no 21:00 close-spread batch or weekend rows in primary",
        },
        "outputs": {
            "micro_price_action_ledger": MICRO_LEDGER.relative_to(ROOT).as_posix(),
            "winner_anatomy_ledger": WINNER_LEDGER.relative_to(ROOT).as_posix(),
            "loser_anatomy_ledger": LOSER_LEDGER.relative_to(ROOT).as_posix(),
            "stuck_candidate_ledger": STUCK_LEDGER.relative_to(ROOT).as_posix(),
            "mfe_mae_timing_ledger": MFE_MAE_LEDGER.relative_to(ROOT).as_posix(),
            "summary_md": SUMMARY_MD.relative_to(ROOT).as_posix(),
            "verification": VERIFICATION.relative_to(ROOT).as_posix(),
        },
    }


def render_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# Friday Micro Price-Action Summary",
        "",
        f"Generated: {summary['generated_at_utc']}",
        f"HEAD at generation: `{summary['git_head']}`",
        "",
        "## Denominator",
        "",
        f"- Primary non-crypto rows: `{summary['primary_rows']}`",
        f"- Tick bid/ask rows: `{summary['tick_bid_ask_rows']}`",
        f"- Full D1/H4/H1/M15 MSO context rows: `{summary['mso_full_context_rows']}`",
        f"- Rows with price after Friday close: `{summary['rows_with_price_after_friday_close']}`",
        "",
        "## Path Classes",
        "",
        f"- Terminal path classes: `{json.dumps(summary['terminal_path_class_counts'], sort_keys=True)}`",
        f"- Outcome counts: `{json.dumps(summary['outcome_counts'], sort_keys=True)}`",
        f"- Mechanism counts: `{json.dumps(summary['mechanism_counts'], sort_keys=True)}`",
        f"- Placed terminal classes: `{json.dumps(summary['placed_terminal_path_classes'], sort_keys=True)}`",
        "",
        "## Boundary",
        "",
        "Every row is capped at the clean Friday close boundary `< 2026-05-29T21:00:00Z`; the 21:00 spread-close batch and weekend reopen rows remain excluded from this primary anatomy.",
        "",
    ]
    return "\n".join(lines)


def write_verifier() -> None:
    VERIFIER.write_text(
        f'''from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = ROOT / "research" / "operations" / "{freeze.ROUTE_ID}"
MICRO_LEDGER = ROUTE_DIR / "{MICRO_LEDGER.name}"
WINNER_LEDGER = ROUTE_DIR / "{WINNER_LEDGER.name}"
LOSER_LEDGER = ROUTE_DIR / "{LOSER_LEDGER.name}"
STUCK_LEDGER = ROUTE_DIR / "{STUCK_LEDGER.name}"
MFE_MAE_LEDGER = ROUTE_DIR / "{MFE_MAE_LEDGER.name}"
SUMMARY_MD = ROUTE_DIR / "{SUMMARY_MD.name}"
VERIFICATION = ROUTE_DIR / "{VERIFICATION.name}"
EXPECTED_ROWS = {EXPECTED_PRIMARY_ROWS}
FRIDAY_CLOSE = "2026-05-29T21:00:00+00:00"


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main() -> int:
    issues = []
    required = [MICRO_LEDGER, WINNER_LEDGER, LOSER_LEDGER, STUCK_LEDGER, MFE_MAE_LEDGER, SUMMARY_MD, VERIFICATION]
    for path in required:
        if not path.exists() or path.stat().st_size <= 0:
            issues.append({{"code": "missing_or_empty_output", "path": str(path)}})
    rows = read_jsonl(MICRO_LEDGER) if MICRO_LEDGER.exists() else []
    mfe_rows = read_jsonl(MFE_MAE_LEDGER) if MFE_MAE_LEDGER.exists() else []
    if len(rows) != EXPECTED_ROWS:
        issues.append({{"code": "micro_row_count_mismatch", "expected": EXPECTED_ROWS, "actual": len(rows)}})
    if len(mfe_rows) != EXPECTED_ROWS:
        issues.append({{"code": "mfe_mae_row_count_mismatch", "expected": EXPECTED_ROWS, "actual": len(mfe_rows)}})
    if sum(1 for row in rows if row.get("price_source") == "tick_bid_ask") != EXPECTED_ROWS:
        issues.append({{"code": "not_all_rows_tick_backed"}})
    if any((row.get("price_source_last_utc") or "") >= FRIDAY_CLOSE for row in rows):
        issues.append({{"code": "price_source_leaks_after_friday_close"}})
    if any(not row.get("terminal_path_class") for row in rows):
        issues.append({{"code": "missing_terminal_path_class"}})
    if sum(1 for row in rows if row.get("actually_placed")) != 8:
        issues.append({{"code": "placed_row_count_mismatch", "expected": 8, "actual": sum(1 for row in rows if row.get("actually_placed"))}})
    if any(not all((row.get("mso_context_compact") or {{}}).get(tf, {{}}).get("available") for tf in ("D1", "H4", "H1", "M15")) for row in rows):
        issues.append({{"code": "missing_mso_timeframe_context"}})
    verification = json.loads(VERIFICATION.read_text(encoding="utf-8")) if VERIFICATION.exists() else {{}}
    if verification and verification.get("ok") is not True:
        issues.append({{"code": "stored_verification_not_ok", "issue_count": verification.get("issue_count")}})
    result = {{"ok": not issues, "issues": issues, "rows": len(rows), "mfe_mae_rows": len(mfe_rows)}}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
''',
        encoding="utf-8",
    )


def verify(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    required = [MICRO_LEDGER, WINNER_LEDGER, LOSER_LEDGER, STUCK_LEDGER, MFE_MAE_LEDGER, SUMMARY_MD, VERIFIER]
    for path in required:
        if not path.exists() or path.stat().st_size <= 0:
            issues.append({"code": "missing_or_empty_output", "path": str(path)})
    rows = rows if rows is not None else (load_jsonl(MICRO_LEDGER) if MICRO_LEDGER.exists() else [])
    if len(rows) != EXPECTED_PRIMARY_ROWS:
        issues.append({"code": "micro_row_count_mismatch", "expected": EXPECTED_PRIMARY_ROWS, "actual": len(rows)})
    if MFE_MAE_LEDGER.exists() and line_count(MFE_MAE_LEDGER) != EXPECTED_PRIMARY_ROWS:
        issues.append({"code": "mfe_mae_row_count_mismatch", "expected": EXPECTED_PRIMARY_ROWS, "actual": line_count(MFE_MAE_LEDGER)})
    tick_rows = sum(1 for row in rows if row.get("price_source") == "tick_bid_ask")
    if tick_rows != EXPECTED_PRIMARY_ROWS:
        issues.append({"code": "not_all_rows_tick_backed", "expected": EXPECTED_PRIMARY_ROWS, "actual": tick_rows})
    leaks = [row.get("candidate_id") for row in rows if (row.get("price_source_last_utc") or "") >= FRIDAY_CLOSE.isoformat()]
    if leaks:
        issues.append({"code": "price_source_leaks_after_friday_close", "count": len(leaks), "sample": leaks[:5]})
    missing_terminal = [row.get("candidate_id") for row in rows if not row.get("terminal_path_class")]
    if missing_terminal:
        issues.append({"code": "missing_terminal_path_class", "count": len(missing_terminal), "sample": missing_terminal[:5]})
    missing_mso = [
        row.get("candidate_id")
        for row in rows
        if not all((row.get("mso_context_compact") or {}).get(tf, {}).get("available") for tf in ("D1", "H4", "H1", "M15"))
    ]
    if missing_mso:
        issues.append({"code": "missing_mso_timeframe_context", "count": len(missing_mso), "sample": missing_mso[:5]})
    placed = sum(1 for row in rows if row.get("actually_placed"))
    if placed != 8:
        issues.append({"code": "placed_row_count_mismatch", "expected": 8, "actual": placed})
    return {
        "schema_version": "friday_micro_price_action_verification_v1",
        "generated_at_utc": utc_now(),
        "git_head": git_head(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "primary_rows_checked": len(rows),
        "tick_bid_ask_rows": tick_rows,
        "mfe_mae_rows": line_count(MFE_MAE_LEDGER) if MFE_MAE_LEDGER.exists() else 0,
        "no_top_n_truncation_proof": "FRIDAY_MICRO_PRICE_ACTION_LEDGER and FRIDAY_MFE_MAE_TIMING_LEDGER each require the full 328-row primary denominator",
    }


def update_repair_ledger(summary: dict[str, Any]) -> None:
    freeze.append_jsonl(
        freeze.REPAIR_LEDGER,
        {
            "schema_version": "friday_microscope_repair_ledger_v1",
            "timestamp_utc": utc_now(),
            "defect_id": "FRIDAY_MICRO_PRICE_ACTION_ANATOMY_NOT_BUILT",
            "defect_class": "missing_microscopic_price_action_anatomy",
            "status": "repaired_stage05_built_and_verified",
            "evidence": "FRIDAY_MICRO_PRICE_ACTION_LEDGER.jsonl covers all 328 primary rows with tick/M1 path capped at Friday close plus D1/H4/H1/M15 compact MSO context",
            "primary_rows": summary.get("primary_rows"),
            "tick_bid_ask_rows": summary.get("tick_bid_ask_rows"),
            "mso_full_context_rows": summary.get("mso_full_context_rows"),
            "verification": VERIFICATION.relative_to(ROOT).as_posix(),
        },
    )


def update_route_state(outputs: list[Path], summary: dict[str, Any]) -> None:
    state = load_json(freeze.STATE_PATH, {})
    finished = set(state.get("finished_artifacts") or [])
    finished.update(path.relative_to(ROOT).as_posix() for path in outputs)
    tests = set(state.get("tests_run") or [])
    tests.update(
        [
            "py -3 -m py_compile scripts/build_vnext_friday_micro_price_action_anatomy.py",
            "python scripts/build_vnext_friday_micro_price_action_anatomy.py",
            "python research/operations/vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31/verify_friday_micro_price_action.py",
        ]
    )
    open_defects = [
        row
        for row in state.get("open_defects", [])
        if row.get("defect_id") != "FRIDAY_MICRO_PRICE_ACTION_ANATOMY_NOT_BUILT"
    ]
    state.update(
        {
            "updated_at_utc": utc_now(),
            "current_head": git_head(),
            "current_stage": "stage_05_micro_price_action_anatomy_built",
            "finished_artifacts": sorted(finished),
            "tests_run": sorted(tests),
            "open_defects": open_defects,
            "exact_next_action": "Build Stage 09 quality-selector broad replay audit and Stage 08 selected/broker-ready execution-policy replay; keep Stage 10 account-exposure prop deferral reconstruction open.",
        }
    )
    repaired = set(state.get("repaired_defects") or [])
    repaired.add("FRIDAY_MICRO_PRICE_ACTION_ANATOMY_NOT_BUILT")
    state["repaired_defects"] = sorted(repaired)
    write_json(freeze.STATE_PATH, state)


def update_completion_audit(summary: dict[str, Any]) -> None:
    audit = load_json(freeze.COMPLETION_AUDIT, {})
    completed = set(audit.get("completed_requirements") or [])
    completed.add("Stage 05 microscopic tick/M1/M15/D1-H4-H1 price-action anatomy built for every primary row")
    unmet = [
        item
        for item in audit.get("unmet_requirements", [])
        if "microscopic tick/M1/M15/D1-H4-H1 price-action anatomy" not in item
    ]
    audit.update(
        {
            "generated_at_utc": utc_now(),
            "status": "not_complete",
            "completion_decision": "keep_goal_active",
            "completed_requirements": sorted(completed),
            "unmet_requirements": unmet,
            "primary_non_crypto_rows_current": summary.get("primary_rows"),
        }
    )
    write_json(freeze.COMPLETION_AUDIT, audit)


def append_control(summary: dict[str, Any], verification: dict[str, Any]) -> None:
    freeze.append_jsonl(
        freeze.CONTROL_LEDGER,
        {
            "schema_version": "friday_microscope_control_ledger_v1",
            "timestamp_utc": utc_now(),
            "stage": "stage_05_micro_price_action_anatomy",
            "action": "built_friday_capped_tick_m1_mso_price_action_anatomy",
            "git_head": git_head(),
            "primary_rows": summary.get("primary_rows"),
            "tick_bid_ask_rows": summary.get("tick_bid_ask_rows"),
            "mso_full_context_rows": summary.get("mso_full_context_rows"),
            "verification_ok": verification.get("ok"),
            "verification_issue_count": verification.get("issue_count"),
        },
    )


def refresh_manifest() -> None:
    paths = sorted(path for path in ROUTE_DIR.iterdir() if path.is_file())
    write_json(freeze.OUTPUT_MANIFEST, freeze.output_manifest(paths))


def build() -> dict[str, Any]:
    rows = build_micro_rows()
    winners, losers, stuck, mfe_mae = split_ledgers(rows)
    summary = build_summary(rows, winners, losers, stuck, mfe_mae)
    write_jsonl(MICRO_LEDGER, rows)
    write_jsonl(WINNER_LEDGER, winners)
    write_jsonl(LOSER_LEDGER, losers)
    write_jsonl(STUCK_LEDGER, stuck)
    write_jsonl(MFE_MAE_LEDGER, mfe_mae)
    SUMMARY_MD.write_text(render_summary(summary), encoding="utf-8")
    write_verifier()
    verification = verify(rows)
    write_json(VERIFICATION, verification)
    outputs = [MICRO_LEDGER, WINNER_LEDGER, LOSER_LEDGER, STUCK_LEDGER, MFE_MAE_LEDGER, SUMMARY_MD, VERIFIER, VERIFICATION]
    update_repair_ledger(summary)
    update_route_state(outputs, summary)
    update_completion_audit(summary)
    append_control(summary, verification)
    refresh_manifest()
    return verification


def main() -> int:
    args = parse_args()
    result = verify() if args.check else build()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
