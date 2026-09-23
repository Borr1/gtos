#!/usr/bin/env python3
"""Append real-time path-follow snapshots for live CANDIDATE rows.

This is a read-only live-monitoring helper. It reads
``shadow_logs/strategy_follow_candidates.jsonl``, pulls current MT5 M15 bars for
today's candidate windows, and appends one row per candidate/latest-candle to
``shadow_logs/candidate_path_follow.jsonl``.

It does not call AI APIs, does not place/cancel orders, and does not alter live
trading decisions. The rows are post-decision forward observation, not
decision-time features.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.forward_capture import external_confluence_snapshot
from src.research_infra.trade_record_candidate_backfill import sync_trade_record_candidates
from src.components.mt5_daemon_runtime import detect_broker_offset_seconds
from src.components.gtos_vnext_event_fields import enrich_cp281_event_contract_fields

SCHEMA_VERSION = "candidate_path_follow_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

DEFAULT_SOURCE = Path("shadow_logs/strategy_follow_candidates.jsonl")
DEFAULT_OUTPUT = Path("shadow_logs/candidate_path_follow.jsonl")
DEFAULT_MECHANICAL_OUTPUT = Path("shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl")
DEFAULT_OBSERVER_TICK_SYMBOLS = {"EURUSD"}


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    except Exception:
        return None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def existing_rows_by_key(path: Path) -> dict[tuple[str, str | None], dict[str, Any]]:
    rows_by_key: dict[tuple[str, str | None], dict[str, Any]] = {}
    for row in read_jsonl(path):
        candidate_id = str(row.get("candidate_id") or "")
        asof = row.get("asof_latest_candle_utc")
        if candidate_id and asof:
            rows_by_key[(candidate_id, str(asof))] = row
    return rows_by_key


def existing_keys(path: Path) -> set[tuple[str, str | None]]:
    return set(existing_rows_by_key(path))


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _rate_has_field(item: Any, field: str) -> bool:
    if isinstance(item, dict):
        return field in item
    dtype = getattr(item, "dtype", None)
    return field in (getattr(dtype, "names", None) or ())


def _numeric_bar_summary(bars: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = [value for bar in bars if (value := _safe_float(bar.get(field))) is not None]
    if not values:
        return {
            "available": False,
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
        }
    return {
        "available": True,
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
    }


def _first_touch_time(bars: list[dict[str, Any]], predicate) -> str | None:
    for bar in bars:
        try:
            if predicate(bar):
                return str(bar["time_utc"]) if bar.get("time_utc") else None
        except Exception:
            continue
    return None


def _source_ohlc_range(bars: list[dict[str, Any]], min_low: float | None, max_high: float | None) -> dict[str, Any]:
    return {
        "source_timeframe": "M15",
        "bar_count": len(bars),
        "first_bar_utc": bars[0].get("time_utc") if bars else None,
        "last_bar_utc": bars[-1].get("time_utc") if bars else None,
        "min_low": min_low,
        "max_high": max_high,
    }


def _path_ambiguity_status(label: str) -> str:
    if label == "entry_touched_tp_and_sl_m15_ambiguous":
        return "M15_TP1_SL_ORDER_AMBIGUOUS_NO_TICK_ORDER_CLAIM"
    if label == "continued_without_entry_touch_to_tp_area":
        return "NO_ENTRY_TOUCH_TP_AREA_NOT_A_FILL"
    if label in {"no_m15_bars_available", "missing_trade_parameters_or_prices"}:
        return "PATH_SOURCE_INCOMPLETE"
    return "M15_OHLC_PATH_LABEL_ONLY"


def classify_path(
    *,
    side: str | None,
    entry: float | None,
    stop_loss: float | None,
    take_profit_1: float | None,
    bars: list[dict[str, Any]],
) -> dict[str, Any]:
    if not bars:
        return {
            "path_label": "no_m15_bars_available",
            "touched_entry": None,
            "hit_sl": None,
            "hit_tp1": None,
            "entry_first_touch_utc": None,
            "tp1_first_touch_utc": None,
            "sl_first_touch_utc": None,
            "path_ambiguity_status": "PATH_SOURCE_INCOMPLETE",
            "tick_order_claim_status": "NO_TICK_ORDER_CLAIM_NO_M15_BARS",
            "source_ohlc_range": _source_ohlc_range([], None, None),
        }
    highs = [_safe_float(bar.get("high")) for bar in bars]
    lows = [_safe_float(bar.get("low")) for bar in bars]
    closes = [_safe_float(bar.get("close")) for bar in bars]
    highs_f = [value for value in highs if value is not None]
    lows_f = [value for value in lows if value is not None]
    if entry is None or stop_loss is None or take_profit_1 is None or not highs_f or not lows_f:
        return {
            "path_label": "missing_trade_parameters_or_prices",
            "touched_entry": None,
            "hit_sl": None,
            "hit_tp1": None,
            "min_low": min(lows_f) if lows_f else None,
            "max_high": max(highs_f) if highs_f else None,
            "entry_first_touch_utc": None,
            "tp1_first_touch_utc": None,
            "sl_first_touch_utc": None,
            "path_ambiguity_status": "PATH_SOURCE_INCOMPLETE",
            "tick_order_claim_status": "NO_TICK_ORDER_CLAIM_M15_OHLC_ONLY",
            "source_ohlc_range": _source_ohlc_range(bars, min(lows_f) if lows_f else None, max(highs_f) if highs_f else None),
        }

    side_u = str(side or "").upper()
    max_high = max(highs_f)
    min_low = min(lows_f)
    last_close = next((value for value in reversed(closes) if value is not None), None)
    base_r = abs(entry - stop_loss) if entry is not None and stop_loss is not None else None
    if side_u == "LONG":
        touched_entry = min_low <= entry
        hit_sl = min_low <= stop_loss
        hit_tp1 = max_high >= take_profit_1
        nearest_distance_to_entry = min((low - entry for low in lows_f), key=abs)
        entry_first_touch_utc = _first_touch_time(bars, lambda bar: (_safe_float(bar.get("low")) or float("inf")) <= entry)
        sl_first_touch_utc = _first_touch_time(bars, lambda bar: (_safe_float(bar.get("low")) or float("inf")) <= stop_loss)
        tp1_first_touch_utc = _first_touch_time(bars, lambda bar: (_safe_float(bar.get("high")) or float("-inf")) >= take_profit_1)
        if not touched_entry and hit_tp1:
            label = "continued_without_entry_touch_to_tp_area"
        elif not touched_entry:
            label = "no_touch_stayed_above_entry"
        elif hit_sl and hit_tp1:
            label = "entry_touched_tp_and_sl_m15_ambiguous"
        elif hit_sl:
            label = "went_through_entry_and_continued_to_sl"
        elif hit_tp1:
            label = "entry_touched_then_reached_tp1"
        else:
            label = "entry_touched_unresolved"
    elif side_u == "SHORT":
        touched_entry = max_high >= entry
        hit_sl = max_high >= stop_loss
        hit_tp1 = min_low <= take_profit_1
        nearest_distance_to_entry = min((entry - high for high in highs_f), key=abs)
        entry_first_touch_utc = _first_touch_time(bars, lambda bar: (_safe_float(bar.get("high")) or float("-inf")) >= entry)
        sl_first_touch_utc = _first_touch_time(bars, lambda bar: (_safe_float(bar.get("high")) or float("-inf")) >= stop_loss)
        tp1_first_touch_utc = _first_touch_time(bars, lambda bar: (_safe_float(bar.get("low")) or float("inf")) <= take_profit_1)
        if not touched_entry and hit_tp1:
            label = "continued_without_entry_touch_to_tp_area"
        elif not touched_entry:
            label = "no_touch_stayed_below_entry"
        elif hit_sl and hit_tp1:
            label = "entry_touched_tp_and_sl_m15_ambiguous"
        elif hit_sl:
            label = "went_through_entry_and_continued_to_sl"
        elif hit_tp1:
            label = "entry_touched_then_reached_tp1"
        else:
            label = "entry_touched_unresolved"
    else:
        touched_entry = None
        hit_sl = None
        hit_tp1 = None
        nearest_distance_to_entry = None
        entry_first_touch_utc = None
        sl_first_touch_utc = None
        tp1_first_touch_utc = None
        label = "unknown_side"
    nearest_abs_distance_to_entry = abs(nearest_distance_to_entry) if nearest_distance_to_entry is not None else None
    nearest_distance_to_entry_r = (
        nearest_abs_distance_to_entry / base_r
        if nearest_abs_distance_to_entry is not None and base_r and base_r > 0
        else None
    )
    if touched_entry is True:
        entry_touch_distance_status = "ENTRY_TOUCHED"
    elif nearest_distance_to_entry_r is None:
        entry_touch_distance_status = "ENTRY_DISTANCE_UNKNOWN"
    elif nearest_distance_to_entry_r <= 0.25:
        entry_touch_distance_status = "NEAR_MISS_LE_0_25R"
    else:
        entry_touch_distance_status = "FAR_MISS_GT_0_25R"

    return {
        "path_label": label,
        "touched_entry": touched_entry,
        "hit_sl": hit_sl,
        "hit_tp1": hit_tp1,
        "entry_first_touch_utc": entry_first_touch_utc,
        "tp1_first_touch_utc": tp1_first_touch_utc,
        "sl_first_touch_utc": sl_first_touch_utc,
        "path_ambiguity_status": _path_ambiguity_status(label),
        "tick_order_claim_status": "NO_TICK_ORDER_CLAIM_M15_OHLC_ONLY",
        "source_ohlc_range": _source_ohlc_range(bars, min_low, max_high),
        "min_low": min_low,
        "max_high": max_high,
        "last_close": last_close,
        "nearest_distance_to_entry": nearest_distance_to_entry,
        "nearest_abs_distance_to_entry": nearest_abs_distance_to_entry,
        "nearest_distance_to_entry_r": nearest_distance_to_entry_r,
        "entry_touch_distance_status": entry_touch_distance_status,
    }


def _rates_to_bars(rates: Any, *, broker_offset_seconds: int = 0) -> list[dict[str, Any]]:
    if rates is None:
        return []
    bars: list[dict[str, Any]] = []
    for row in rates:
        try:
            # MT5 bar epochs are broker-server-localized. Convert them back
            # to true UTC before writing shadow labels keyed by UTC candles.
            ts = datetime.fromtimestamp(int(row["time"]) - broker_offset_seconds, tz=timezone.utc)
            bars.append(
                {
                    "time_utc": ts.isoformat(),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "spread": _safe_float(row["spread"]) if _rate_has_field(row, "spread") else None,
                    "tick_volume": _safe_float(row["tick_volume"]) if _rate_has_field(row, "tick_volume") else None,
                    "real_volume": _safe_float(row["real_volume"]) if _rate_has_field(row, "real_volume") else None,
                }
            )
        except Exception:
            continue
    return bars


def pull_m15_bars(symbol: str, start: datetime, end: datetime) -> tuple[list[dict[str, Any]], str | None]:
    try:
        import MetaTrader5 as mt5  # type: ignore

        if not mt5.initialize():
            return [], "mt5_initialize_failed"
        try:
            broker_offset_seconds = detect_broker_offset_seconds(mt5, symbols=(symbol,))
            # Raw MT5 range queries compare against broker-localized candle
            # epochs. Shift the true-UTC window into broker time for the query,
            # then convert returned epochs back to UTC in _rates_to_bars.
            query_start = start + timedelta(seconds=broker_offset_seconds)
            query_end = end + timedelta(seconds=broker_offset_seconds)
            rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M15, query_start, query_end)
            return _rates_to_bars(rates, broker_offset_seconds=broker_offset_seconds), None
        finally:
            mt5.shutdown()
    except Exception as exc:  # noqa: BLE001
        return [], f"mt5_read_failed:{exc}"


def build_follow_row(
    candidate: dict[str, Any],
    *,
    now: datetime,
    max_hours: float,
) -> tuple[dict[str, Any], str | None]:
    decision_time = parse_utc(candidate.get("decision_time_utc"))
    candidate_id = str(candidate.get("candidate_id") or "")
    if decision_time is None:
        return {}, "missing_decision_time"
    if now - decision_time > timedelta(hours=max_hours):
        return {}, "outside_max_hours"

    symbol = str(candidate.get("broker_symbol") or candidate.get("symbol") or "")
    bars, error = pull_m15_bars(symbol, decision_time, now)
    if not bars:
        if error:
            return {}, f"path_source_incomplete:{error}"
        return {}, "path_source_incomplete:no_m15_bars_available"
    trade_params = candidate.get("trade_parameters") or {}
    path = classify_path(
        side=candidate.get("side") or trade_params.get("direction"),
        entry=_safe_float(trade_params.get("entry_price")),
        stop_loss=_safe_float(trade_params.get("stop_loss")),
        take_profit_1=_safe_float(trade_params.get("take_profit_1")),
        bars=bars,
    )
    if path.get("path_ambiguity_status") == "PATH_SOURCE_INCOMPLETE":
        return {}, f"path_source_incomplete:{path.get('path_label') or 'unknown'}"
    latest_bar = bars[-1] if bars else {}
    route_session = (
        candidate.get("route_session")
        or candidate.get("session")
        or candidate.get("session_tag")
        or candidate.get("kill_zone")
    )
    spread_summary = _numeric_bar_summary(bars, "spread")
    tick_volume_summary = _numeric_bar_summary(bars, "tick_volume")
    real_volume_summary = _numeric_bar_summary(bars, "real_volume")
    external_confluence = candidate.get("external_confluence")
    if not isinstance(external_confluence, dict) or not external_confluence:
        external_confluence = external_confluence_snapshot(
            {
                **candidate,
                "analysis_decision": candidate.get("analysis_decision"),
                "final_outcome": candidate.get("final_outcome_at_log"),
            }
        )
    row = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": utc_now_iso(),
        "promotion_verdict": PROMOTION_VERDICT,
        "evidence_class": "FORWARD_SHADOW_PATH_FOLLOW",
        "candidate_id": candidate_id,
        "trade_id": candidate.get("trade_id"),
        "symbol": candidate.get("symbol"),
        "broker_symbol": symbol,
        "route_session": route_session,
        "side": candidate.get("side") or trade_params.get("direction"),
        "framework": candidate.get("framework"),
        "final_outcome_at_candidate_log": candidate.get("final_outcome_at_log"),
        "decision_time_utc": candidate.get("decision_time_utc"),
        "asof_latest_candle_utc": latest_bar.get("time_utc"),
        "bars_elapsed": len(bars),
        "trade_parameters": trade_params,
        "mt5_read_error": error,
        "no_leak_status": "POST_DECISION_FORWARD_OBSERVATION_NOT_DECISION_FEATURE",
        "external_confluence": external_confluence,
        "m15_spread_source_status": "SPREAD_CAPTURED" if spread_summary["available"] else "SPREAD_NOT_AVAILABLE",
        "m15_spread_count": spread_summary["count"],
        "m15_spread_min": spread_summary["min"],
        "m15_spread_max": spread_summary["max"],
        "m15_spread_mean": spread_summary["mean"],
        "m15_tick_volume_source_status": (
            "TICK_VOLUME_CAPTURED" if tick_volume_summary["available"] else "TICK_VOLUME_NOT_AVAILABLE"
        ),
        "m15_tick_volume_count": tick_volume_summary["count"],
        "m15_tick_volume_min": tick_volume_summary["min"],
        "m15_tick_volume_max": tick_volume_summary["max"],
        "m15_tick_volume_mean": tick_volume_summary["mean"],
        "m15_real_volume_source_status": (
            "REAL_VOLUME_CAPTURED" if real_volume_summary["available"] else "REAL_VOLUME_NOT_AVAILABLE"
        ),
        "m15_real_volume_count": real_volume_summary["count"],
        "m15_real_volume_min": real_volume_summary["min"],
        "m15_real_volume_max": real_volume_summary["max"],
        "m15_real_volume_mean": real_volume_summary["mean"],
        **path,
    }
    return enrich_cp281_event_contract_fields(row, source_path=DEFAULT_OUTPUT), None


PATH_CHANGE_FIELDS = (
    "path_label",
    "touched_entry",
    "hit_sl",
    "hit_tp1",
    "entry_first_touch_utc",
    "tp1_first_touch_utc",
    "sl_first_touch_utc",
    "path_ambiguity_status",
    "nearest_abs_distance_to_entry",
    "nearest_distance_to_entry_r",
    "entry_touch_distance_status",
    "m15_spread_source_status",
    "m15_spread_count",
    "m15_spread_min",
    "m15_spread_max",
    "m15_spread_mean",
    "m15_tick_volume_source_status",
    "m15_tick_volume_count",
    "m15_tick_volume_min",
    "m15_tick_volume_max",
    "m15_tick_volume_mean",
    "m15_real_volume_source_status",
    "m15_real_volume_count",
    "m15_real_volume_min",
    "m15_real_volume_max",
    "m15_real_volume_mean",
)


def path_changed(existing: dict[str, Any], new: dict[str, Any]) -> bool:
    return any(existing.get(field) != new.get(field) for field in PATH_CHANGE_FIELDS)


def run(
    source: Path,
    output: Path,
    *,
    max_hours: float,
    observer_tick_symbols: set[str] | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    trade_record_backfill = sync_trade_record_candidates(
        candidates_path=source,
        max_hours=max_hours,
        now=now,
    )
    rows = read_jsonl(source)
    existing_rows = existing_rows_by_key(output)
    written = 0
    skipped: dict[str, int] = {}
    for candidate in rows:
        row, skip = build_follow_row(candidate, now=now, max_hours=max_hours)
        if skip:
            skipped[skip] = skipped.get(skip, 0) + 1
            continue
        key = (str(row.get("candidate_id") or ""), row.get("asof_latest_candle_utc"))
        existing = existing_rows.get(key)
        if existing:
            if not path_changed(existing, row):
                skipped["duplicate_candidate_asof"] = skipped.get("duplicate_candidate_asof", 0) + 1
                continue
            row["correction_of_created_at_utc"] = existing.get("created_at_utc")
            row["correction_reason"] = "same_candidate_asof_path_recomputed_changed"
            row["manual_backfill_status"] = "CORRECTED_CANDIDATE_PATH_RECOMPUTED_FOR_SAME_ASOF"
        append_jsonl(output, row)
        existing_rows[key] = row
        written += 1
    summary = {
        "source": str(source),
        "output": str(output),
        "candidates_seen": len(rows),
        "rows_written": written,
        "skipped": dict(sorted(skipped.items())),
        "trade_record_candidate_backfill": trade_record_backfill,
    }
    try:
        from src.research_infra.live_shadow_gap_closure import refresh_ltf_rows

        summary["ltf_path_order_refresh"] = refresh_ltf_rows(max_hours=max_hours)
    except Exception as exc:  # noqa: BLE001
        summary["ltf_path_order_refresh"] = {
            "status": "FAILED_NON_BLOCKING",
            "error": str(exc),
        }
    try:
        from src.research_infra.live_mechanical_shadow import run as run_mechanical_shadow

        summary["mechanical_shadow"] = run_mechanical_shadow(
            candidates_path=source,
            paths_path=output,
            output_path=DEFAULT_MECHANICAL_OUTPUT,
        )
    except Exception as exc:  # noqa: BLE001
        summary["mechanical_shadow"] = {
            "status": "FAILED_NON_BLOCKING",
            "error": str(exc),
        }
    try:
        from src.research_infra.live_shadow_gap_closure import close_gaps

        summary["gap_closure"] = close_gaps(max_hours=max_hours, refresh_ltf=False)
    except Exception as exc:  # noqa: BLE001
        summary["gap_closure"] = {
            "status": "FAILED_NON_BLOCKING",
            "error": str(exc),
        }
    if observer_tick_symbols is None:
        observer_tick_symbols = set(DEFAULT_OBSERVER_TICK_SYMBOLS)
    if observer_tick_symbols:
        try:
            from src.research_infra.shadow_observer_tick_enrichment import run as run_observer_tick_enrichment

            summary["observer_tick_enrichment"] = run_observer_tick_enrichment(
                symbol_filter=observer_tick_symbols,
            )
        except Exception as exc:  # noqa: BLE001
            summary["observer_tick_enrichment"] = {
                "status": "FAILED_NON_BLOCKING",
                "error": str(exc),
                "symbols": sorted(observer_tick_symbols),
            }
    else:
        summary["observer_tick_enrichment"] = {
            "status": "SKIPPED_DISABLED",
            "symbols": [],
        }
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--max-hours", type=float, default=8.0)
    parser.add_argument(
        "--observer-tick-symbols",
        default=",".join(sorted(DEFAULT_OBSERVER_TICK_SYMBOLS)),
        help=(
            "Comma-separated shadow-observer symbols to enrich from MT5 ticks. "
            "Use an empty string to skip this duplicate-protected maintenance lane."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    observer_tick_symbols = {
        item.strip()
        for item in str(args.observer_tick_symbols or "").split(",")
        if item.strip()
    }
    summary = run(
        Path(args.source),
        Path(args.output),
        max_hours=args.max_hours,
        observer_tick_symbols=observer_tick_symbols,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
