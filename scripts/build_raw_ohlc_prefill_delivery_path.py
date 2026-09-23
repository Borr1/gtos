#!/usr/bin/env python3
"""Build research-only pre-fill delivery-path coverage rows.

This harness reconstructs the path from an M15 setup decision close to the
first pending-entry touch or pending expiry using existing local OHLC data. It
does not score a delivery-leg strategy and does not infer broker lifecycle
states that are not present in the source logs.
"""

from __future__ import annotations

import argparse
import bisect
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_historical_opportunity_dataset import (  # noqa: E402
    DEFAULT_MECHANICAL_MAX_HOLD_BARS,
    _find_ohlcv_path,
    _load_outcome_rows,
)

DEFAULT_EVENT_LOG = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "raw_ohlc_prequential_replay/path_scaling_v2_structural_levels/"
    "raw_ohlc_path_scaling_v2_structural_levels_events_20260501T213225Z.jsonl"
)
DEFAULT_DATA_ROOTS = [
    "data/mt5_research_exports/phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1",
    "data/mt5_research_exports/phase3_m15_2022_2026_fn_chunked_v1",
    "data/historical_2026",
    "data/historical_2022_2023",
    "data",
]
DEFAULT_OUTPUT_JSON = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PREFILL_DELIVERY_PATH_COVERAGE_2026-05-03.json"
)
DEFAULT_OUTPUT_JSONL = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PREFILL_DELIVERY_PATH_SAMPLE_2026-05-03.jsonl"
)
DEFAULT_OUTPUT_MD = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PREFILL_DELIVERY_PATH_COVERAGE_2026-05-03.md"
)
DEFAULT_JSONL_SAMPLE_LIMIT = 200
PATH_TIMEFRAMES = ("M1", "M5", "M15")
LOWER_TIMEFRAMES = ("M1", "M5")
M15_MINUTES = 15
J46_VARIANT = "J46_J49_ONLY"


@dataclass
class PathIndex:
    symbol: str
    timeframe: str
    rows: list[dict[str, Any]]
    source_path: str | None = None

    def __post_init__(self) -> None:
        self.rows.sort(key=lambda row: row["time"])
        self.times = [row["time"] for row in self.rows]

    def between(self, start_exclusive: datetime, end_inclusive: datetime) -> list[dict[str, Any]]:
        left = bisect.bisect_right(self.times, start_exclusive)
        right = bisect.bisect_right(self.times, end_inclusive)
        return self.rows[left:right]


def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso(dt: datetime | None) -> str | None:
    return dt.astimezone(timezone.utc).isoformat() if isinstance(dt, datetime) else None


def parse_cohort(raw_cohort_key: str | None) -> dict[str, str | None]:
    parts = str(raw_cohort_key or "").split("|")
    return {
        "cohort_symbol": parts[0] if len(parts) > 0 and parts[0] else None,
        "cohort_session": parts[1] if len(parts) > 1 and parts[1] else None,
        "cohort_bias": parts[2] if len(parts) > 2 and parts[2] else None,
        "regime": parts[3] if len(parts) > 3 and parts[3] else None,
    }


def load_setup_rows(event_log_path: str | Path, *, variant_id: str = J46_VARIANT) -> list[dict[str, Any]]:
    rows = []
    with Path(event_log_path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("variant_id") != variant_id:
                continue
            if row.get("mechanical_entry") is None:
                continue
            rows.append(row)
    return rows


def load_path_indexes(symbols: Iterable[str], roots: Sequence[Path]) -> dict[tuple[str, str], PathIndex]:
    cache: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    indexes: dict[tuple[str, str], PathIndex] = {}
    for symbol in sorted(set(symbols)):
        for timeframe in PATH_TIMEFRAMES:
            rows = _load_outcome_rows(roots=roots, symbol=symbol, timeframe=timeframe, cache=cache)
            source = _find_ohlcv_path(roots, symbol, timeframe)
            indexes[(symbol, timeframe)] = PathIndex(
                symbol=symbol,
                timeframe=timeframe,
                rows=list(rows),
                source_path=str(source) if source else None,
            )
    return indexes


def high_low_close(row: Mapping[str, Any]) -> tuple[float | None, float | None, float | None]:
    try:
        return float(row["high"]), float(row["low"]), float(row["close"])
    except (KeyError, TypeError, ValueError):
        return None, None, None


def fill_hit(*, side: str, entry: float, high: float, low: float) -> bool:
    return low <= entry if side.upper() == "LONG" else high >= entry


def m15_bars_between(start: datetime, end: datetime) -> int:
    seconds = max(0.0, (end - start).total_seconds())
    return int(max(1, (seconds + (M15_MINUTES * 60) - 1) // (M15_MINUTES * 60)))


def row_snapshot(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "time": iso(row.get("time")),
        "open": row.get("open"),
        "high": row.get("high"),
        "low": row.get("low"),
        "close": row.get("close"),
    }


def select_prefill_window(
    *,
    symbol: str,
    setup_close: datetime,
    indexes: Mapping[tuple[str, str], PathIndex],
    pending_expiry_bars: int,
) -> dict[str, Any]:
    expiry = setup_close + timedelta(minutes=M15_MINUTES * int(pending_expiry_bars))
    windows = {
        timeframe: indexes.get((symbol, timeframe), PathIndex(symbol, timeframe, [])).between(setup_close, expiry)
        for timeframe in PATH_TIMEFRAMES
    }
    selected = "M15"
    fallback_reason = "M1_M5_UNAVAILABLE_IN_POST_DECISION_WINDOW"
    for timeframe in LOWER_TIMEFRAMES:
        if windows[timeframe]:
            selected = timeframe
            fallback_reason = None if timeframe == "M1" else "M1_UNAVAILABLE_IN_POST_DECISION_WINDOW"
            break
    return {
        "expiry_utc": expiry,
        "selected_timeframe": selected,
        "selected_rows": windows[selected],
        "fallback_reason": fallback_reason,
        "row_counts": {timeframe: len(rows) for timeframe, rows in windows.items()},
        "first_close": {timeframe: iso(rows[0]["time"]) if rows else None for timeframe, rows in windows.items()},
        "last_close": {timeframe: iso(rows[-1]["time"]) if rows else None for timeframe, rows in windows.items()},
    }


def detect_fill_state(
    *,
    setup: Mapping[str, Any],
    selected_rows: Sequence[Mapping[str, Any]],
    setup_close: datetime,
    expiry: datetime,
) -> dict[str, Any]:
    side = str(setup.get("mechanical_side") or "").upper()
    entry = float(setup["mechanical_entry"])
    rows_seen: list[Mapping[str, Any]] = []
    for row in selected_rows:
        high, low, _close = high_low_close(row)
        bar_time = row.get("time")
        if high is None or low is None or not isinstance(bar_time, datetime):
            continue
        rows_seen.append(row)
        if fill_hit(side=side, entry=entry, high=high, low=low):
            return {
                "state": "FILLED_RECONSTRUCTED_PATH_TOUCH",
                "fill_time_utc": iso(bar_time),
                "expiry_utc": iso(expiry),
                "pre_fill_path_rows": len(rows_seen),
                "bars_to_fill_m15_units": m15_bars_between(setup_close, bar_time),
                "rows_before_fill": list(rows_seen[:-1]),
                "rows_until_state": list(rows_seen),
                "fill_row": row,
            }
    last_time = selected_rows[-1].get("time") if selected_rows else None
    if not selected_rows:
        state = "NO_PATH_ROWS"
    elif isinstance(last_time, datetime) and last_time < expiry:
        state = "UNRESOLVED_PATH_ENDS_BEFORE_EXPIRY"
    else:
        state = "NOT_FILLED_BEFORE_EXPIRY_ON_SELECTED_PATH"
    return {
        "state": state,
        "fill_time_utc": None,
        "expiry_utc": iso(expiry),
        "pre_fill_path_rows": len(selected_rows),
        "bars_to_fill_m15_units": None,
        "rows_before_fill": list(selected_rows),
        "rows_until_state": list(selected_rows),
        "fill_row": None,
    }


def max_run(values: list[bool]) -> int:
    best = cur = 0
    for value in values:
        cur = cur + 1 if value else 0
        best = max(best, cur)
    return best


def delivery_structure_flags(
    *,
    side: str,
    entry: float,
    rows_before_fill: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if not rows_before_fill:
        return {
            "schema": "primitive_ohlc_delivery_proxy_v1",
            "rows_used": 0,
            "status": "INSUFFICIENT_PREFILL_ROWS",
        }
    closes = [float(row["close"]) for row in rows_before_fill if row.get("close") is not None]
    opens = [float(row["open"]) for row in rows_before_fill if row.get("open") is not None]
    highs = [float(row["high"]) for row in rows_before_fill if row.get("high") is not None]
    lows = [float(row["low"]) for row in rows_before_fill if row.get("low") is not None]
    side_up = side.upper()
    toward_entry_moves = []
    for prev, cur in zip(closes, closes[1:]):
        toward_entry_moves.append(cur < prev if side_up == "LONG" else cur > prev)
    body_toward = [
        close < open_ if side_up == "LONG" else close > open_
        for open_, close in zip(opens, closes)
    ]
    if side_up == "LONG":
        structure_progressions = [cur < prev for prev, cur in zip(lows, lows[1:])]
        closest_distance = min((abs(low - entry) for low in lows), default=None)
    else:
        structure_progressions = [cur > prev for prev, cur in zip(highs, highs[1:])]
        closest_distance = min((abs(high - entry) for high in highs), default=None)
    return {
        "schema": "primitive_ohlc_delivery_proxy_v1",
        "rows_used": len(rows_before_fill),
        "status": "STRUCTURE_PROXY_ONLY_NOT_VALIDATION",
        "toward_entry_close_move_share": round(sum(toward_entry_moves) / len(toward_entry_moves), 6)
        if toward_entry_moves
        else None,
        "toward_entry_body_share": round(sum(body_toward) / len(body_toward), 6) if body_toward else None,
        "max_consecutive_toward_entry_closes": max_run(toward_entry_moves),
        "delivery_extreme_progression_share": round(sum(structure_progressions) / len(structure_progressions), 6)
        if structure_progressions
        else None,
        "max_consecutive_delivery_extremes": max_run(structure_progressions),
        "closest_prefill_extreme_distance_to_entry_price": round(closest_distance, 6)
        if closest_distance is not None
        else None,
        "first_close": closes[0] if closes else None,
        "last_prefill_close": closes[-1] if closes else None,
    }


def ambiguity_flags(
    *,
    fill_state: str,
    lower_tf_available: bool,
    selected_timeframe: str,
    fallback_reason: str | None,
) -> list[str]:
    flags = [
        "PENDING_LIMIT_CREATED_UTC_ASSUMED_EQUAL_SETUP_DECISION_CLOSE",
        "ORIGINAL_POI_TYPE_AND_BOUNDS_MISSING_IN_V2_EVENT_LOG",
        "BROKER_PENDING_LIFECYCLE_STATE_MISSING",
    ]
    if not lower_tf_available:
        flags.append("LOWER_TF_UNAVAILABLE_SELECTED_M15")
    if fallback_reason:
        flags.append(fallback_reason)
    if fill_state == "FILLED_RECONSTRUCTED_PATH_TOUCH":
        flags.append(f"{selected_timeframe}_FILL_ROW_INTRABAR_ORDER_AMBIGUOUS")
    if fill_state == "UNRESOLVED_PATH_ENDS_BEFORE_EXPIRY":
        flags.append("PATH_SOURCE_ENDS_BEFORE_PENDING_EXPIRY")
    if fill_state == "NO_PATH_ROWS":
        flags.append("NO_POST_DECISION_PATH_ROWS")
    return flags


def capture_setup(
    setup: Mapping[str, Any],
    *,
    indexes: Mapping[tuple[str, str], PathIndex],
    pending_expiry_bars: int = DEFAULT_MECHANICAL_MAX_HOLD_BARS,
) -> dict[str, Any]:
    setup_close = parse_utc(setup.get("candle_close_utc"))
    if setup_close is None:
        raise ValueError(f"missing/invalid candle_close_utc for {setup.get('event_key')}")
    symbol = str(setup.get("symbol") or "")
    side = str(setup.get("mechanical_side") or "").upper()
    entry = float(setup["mechanical_entry"])
    window = select_prefill_window(
        symbol=symbol,
        setup_close=setup_close,
        indexes=indexes,
        pending_expiry_bars=pending_expiry_bars,
    )
    fill = detect_fill_state(
        setup=setup,
        selected_rows=window["selected_rows"],
        setup_close=setup_close,
        expiry=window["expiry_utc"],
    )
    lower_tf_available = bool(window["row_counts"].get("M1") or window["row_counts"].get("M5"))
    flags = ambiguity_flags(
        fill_state=fill["state"],
        lower_tf_available=lower_tf_available,
        selected_timeframe=window["selected_timeframe"],
        fallback_reason=window["fallback_reason"],
    )
    rows_until_state = fill["rows_until_state"]
    return {
        "schema_version": "raw_ohlc_prefill_delivery_path_capture_v1",
        "setup_id": setup.get("event_key"),
        "symbol": symbol,
        "session": setup.get("session"),
        "side": side,
        "role": setup.get("role"),
        "raw_cohort_key": setup.get("raw_cohort_key"),
        **parse_cohort(setup.get("raw_cohort_key")),
        "setup_decision_close_utc": iso(setup_close),
        "pending_limit_created_utc": iso(setup_close),
        "pending_limit_created_utc_source": "ASSUMED_DECISION_CLOSE_RAW_REPLAY_NO_BROKER_LIFECYCLE",
        "entry_price": entry,
        "initial_sl": setup.get("mechanical_sl"),
        "initial_tp": setup.get("mechanical_tp"),
        "original_poi_type_and_bounds": {
            "available": False,
            "poi_type": None,
            "bounds": None,
            "missing_reason": "V2 event log retains mechanical entry/SL/TP but not original POI type/bounds.",
        },
        "pre_fill_path_timeframe": window["selected_timeframe"],
        "pre_fill_path_rows": fill["pre_fill_path_rows"],
        "pre_fill_path_first_close_utc": iso(rows_until_state[0].get("time")) if rows_until_state else None,
        "pre_fill_path_last_close_utc": iso(rows_until_state[-1].get("time")) if rows_until_state else None,
        "pre_fill_path_row_counts_by_timeframe": window["row_counts"],
        "path_first_close_by_timeframe": window["first_close"],
        "path_last_close_by_timeframe": window["last_close"],
        "fill_or_expiry_state": fill["state"],
        "fill_time_utc": fill["fill_time_utc"],
        "pending_expiry_utc": fill["expiry_utc"],
        "bars_to_fill_m15_units": fill["bars_to_fill_m15_units"],
        "lower_tf_available": lower_tf_available,
        "as_of_delivery_structure_flags": delivery_structure_flags(
            side=side,
            entry=entry,
            rows_before_fill=fill["rows_before_fill"],
        ),
        "path_sample": {
            "first_rows": [row_snapshot(row) for row in rows_until_state[:3]],
            "last_rows": [row_snapshot(row) for row in rows_until_state[-3:]],
        },
        "source_event_outcome": setup.get("outcome"),
        "source_event_bars_to_fill": setup.get("bars_to_fill"),
        "source_event_path_rows_to_fill": setup.get("path_rows_to_fill"),
        "source_event_selected_timeframe": setup.get("selected_timeframe"),
        "ambiguity_flags": flags,
    }


def source_inventory(indexes: Mapping[tuple[str, str], PathIndex]) -> list[dict[str, Any]]:
    rows = []
    for (symbol, timeframe), index in sorted(indexes.items()):
        rows.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "source_path": index.source_path,
                "rows": len(index.rows),
                "first_close_utc": iso(index.rows[0]["time"]) if index.rows else None,
                "last_close_utc": iso(index.rows[-1]["time"]) if index.rows else None,
            }
        )
    return rows


def summarize(records: list[dict[str, Any]], *, setup_rows_seen: int, event_log_path: str, data_roots: Sequence[Path]) -> dict[str, Any]:
    by_symbol = defaultdict(list)
    for record in records:
        by_symbol[record["symbol"]].append(record)
    def pct(count: int, denom: int) -> float | None:
        return round(count / denom, 6) if denom else None
    summary = {
        "schema_version": "raw_ohlc_prefill_delivery_path_coverage_summary_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "discovery_label": "COVERAGE_ONLY_NOT_STRATEGY_SCORE",
        "registered_question_before_outputs": (
            "Can existing local OHLC rows reconstruct setup-close-to-fill/expiry pre-fill paths "
            "and expose as-of delivery proxies without using post-fill outcome information?"
        ),
        "inputs": {
            "event_log_path": event_log_path,
            "variant_id": J46_VARIANT,
            "data_roots": [str(path) for path in data_roots],
            "pending_expiry_bars": DEFAULT_MECHANICAL_MAX_HOLD_BARS,
        },
        "coverage": {
            "setup_rows_seen": setup_rows_seen,
            "captured_setup_rows": len(records),
            "lower_tf_available_rows": sum(bool(record["lower_tf_available"]) for record in records),
            "lower_tf_available_rate": pct(sum(bool(record["lower_tf_available"]) for record in records), len(records)),
            "selected_timeframes": dict(Counter(record["pre_fill_path_timeframe"] for record in records)),
            "fill_or_expiry_states": dict(Counter(record["fill_or_expiry_state"] for record in records)),
            "rows_with_original_poi_bounds": sum(
                bool((record["original_poi_type_and_bounds"] or {}).get("available")) for record in records
            ),
            "rows_with_broker_lifecycle_state": 0,
            "rows_with_structure_proxy": sum(
                record["as_of_delivery_structure_flags"].get("status") == "STRUCTURE_PROXY_ONLY_NOT_VALIDATION"
                for record in records
            ),
        },
        "by_symbol": {},
        "ambiguity_flag_counts": dict(Counter(flag for record in records for flag in record["ambiguity_flags"])),
        "missing_fields": [
            "original_poi_type_and_bounds",
            "broker_pending_lifecycle_state",
            "true_pending_limit_created_utc",
            "intrabar_order_inside_fill_row",
        ],
        "explicit_non_claims": [
            "No delivery-leg strategy is scored.",
            "Reconstructed fill touch is an OHLC path touch, not a broker-confirmed fill.",
            "As-of delivery structure flags are primitive OHLC proxies, not validated market-structure labels.",
            "Post-fill rows are not used to define pre-fill structure flags.",
        ],
    }
    for symbol, rows in sorted(by_symbol.items()):
        summary["by_symbol"][symbol] = {
            "n": len(rows),
            "lower_tf_available_rate": pct(sum(bool(row["lower_tf_available"]) for row in rows), len(rows)),
            "selected_timeframes": dict(Counter(row["pre_fill_path_timeframe"] for row in rows)),
            "fill_or_expiry_states": dict(Counter(row["fill_or_expiry_state"] for row in rows)),
        }
    return summary


def write_json(payload: dict[str, Any], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(records: Iterable[dict[str, Any]], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value).replace("|", r"\|")


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(value) for value in row) + " |")
    return lines


def write_markdown(payload: dict[str, Any], path: str | Path) -> None:
    summary = payload["summary"]
    coverage = summary["coverage"]
    lines = [
        "# Raw OHLC Pre-Fill Delivery Path Coverage",
        "",
        "Date: 2026-05-03",
        "Scope: research/tooling only",
        f"Promotion verdict: `{summary['promotion_verdict']}`",
        f"Discovery label: `{summary['discovery_label']}`",
        "",
        "## Registered Question Before Outputs",
        "",
        summary["registered_question_before_outputs"],
        "",
        "## Bottom Line",
        "",
        "Existing local OHLC rows can reconstruct a pre-fill path coverage ledger for setup-ok V2/J46 rows, but the result is coverage/tooling only. It still lacks original POI bounds, true broker pending-limit lifecycle state, and intrabar ordering inside the fill row.",
        "",
        "## Coverage",
        "",
        *table(
            ["metric", "value"],
            [
                ["setup rows seen", coverage["setup_rows_seen"]],
                ["captured setup rows", coverage["captured_setup_rows"]],
                ["lower-TF available rows", coverage["lower_tf_available_rows"]],
                ["lower-TF available rate", coverage["lower_tf_available_rate"]],
                ["selected timeframes", coverage["selected_timeframes"]],
                ["fill/expiry states", coverage["fill_or_expiry_states"]],
                ["rows with original POI bounds", coverage["rows_with_original_poi_bounds"]],
                ["rows with broker lifecycle state", coverage["rows_with_broker_lifecycle_state"]],
                ["rows with structure proxy", coverage["rows_with_structure_proxy"]],
            ],
        ),
        "",
        "## By Symbol",
        "",
        *table(
            ["symbol", "n", "lower-TF rate", "selected timeframes", "fill/expiry states"],
            [
                [
                    symbol,
                    row["n"],
                    row["lower_tf_available_rate"],
                    row["selected_timeframes"],
                    row["fill_or_expiry_states"],
                ]
                for symbol, row in summary["by_symbol"].items()
            ],
        ),
        "",
        "## Source Inventory",
        "",
        *table(
            ["symbol", "tf", "rows", "first close", "last close", "source"],
            [
                [
                    row["symbol"],
                    row["timeframe"],
                    row["rows"],
                    row["first_close_utc"],
                    row["last_close_utc"],
                    row["source_path"],
                ]
                for row in payload["source_inventory"]
            ],
        ),
        "",
        "## Outputs",
        "",
        *table(
            ["artifact", "value"],
            [
                ["summary json", (summary.get("outputs") or {}).get("json")],
                ["sample jsonl", (summary.get("outputs") or {}).get("jsonl")],
                ["markdown", (summary.get("outputs") or {}).get("markdown")],
                ["jsonl sample rows", (summary.get("outputs") or {}).get("jsonl_sample_rows")],
                ["full captured records counted", (summary.get("outputs") or {}).get("full_captured_records_counted")],
            ],
        ),
        "",
        "## Captured Row Schema",
        "",
        "Each JSONL row includes:",
        "",
        *[
            f"- `{field}`"
            for field in [
                "setup_id",
                "symbol",
                "side",
                "setup_decision_close_utc",
                "pending_limit_created_utc",
                "entry_price",
                "original_poi_type_and_bounds",
                "pre_fill_path_timeframe",
                "pre_fill_path_rows",
                "fill_or_expiry_state",
                "lower_tf_available",
                "as_of_delivery_structure_flags",
                "ambiguity_flags",
            ]
        ],
        "",
        "## Ambiguity Flag Counts",
        "",
        *table(
            ["flag", "count"],
            [[flag, count] for flag, count in sorted(summary["ambiguity_flag_counts"].items())],
        ),
        "",
        "## Missing Fields",
        "",
        *[f"- `{field}`" for field in summary["missing_fields"]],
        "",
        "## Explicit Non-Claims",
        "",
        *[f"- {item}" for item in summary["explicit_non_claims"]],
        "",
        "## Next Steps",
        "",
        "1. Add true pending-limit lifecycle telemetry before treating reconstructed touches as broker fills.",
        "2. Add original POI type/bounds to future path-scaling event logs.",
        "3. Use this coverage ledger as an input to V3/design forensics only after risk-bank tests exist.",
        "4. Keep any delivery-leg plus reversal-leg scoring in a separate pre-registered discovery task.",
        "",
    ]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_payload(
    *,
    event_log_path: str | Path = DEFAULT_EVENT_LOG,
    data_roots: Sequence[str | Path] = DEFAULT_DATA_ROOTS,
    pending_expiry_bars: int = DEFAULT_MECHANICAL_MAX_HOLD_BARS,
) -> dict[str, Any]:
    roots = [Path(path) for path in data_roots]
    setup_rows = load_setup_rows(event_log_path)
    indexes = load_path_indexes((row["symbol"] for row in setup_rows), roots)
    records = [
        capture_setup(row, indexes=indexes, pending_expiry_bars=pending_expiry_bars)
        for row in setup_rows
    ]
    return {
        "summary": summarize(
            records,
            setup_rows_seen=len(setup_rows),
            event_log_path=str(event_log_path),
            data_roots=roots,
        ),
        "source_inventory": source_inventory(indexes),
        "records": records,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-log", default=DEFAULT_EVENT_LOG)
    parser.add_argument("--data-root", action="append", default=None)
    parser.add_argument("--pending-expiry-bars", type=int, default=DEFAULT_MECHANICAL_MAX_HOLD_BARS)
    parser.add_argument("--jsonl-sample-limit", type=int, default=DEFAULT_JSONL_SAMPLE_LIMIT)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(
        event_log_path=args.event_log,
        data_roots=args.data_root or DEFAULT_DATA_ROOTS,
        pending_expiry_bars=args.pending_expiry_bars,
    )
    records = payload.pop("records")
    sample_records = records[: max(0, int(args.jsonl_sample_limit))]
    payload["summary"]["outputs"] = {
        "json": args.output_json,
        "jsonl": args.output_jsonl,
        "markdown": args.output_md,
        "jsonl_sample_limit": int(args.jsonl_sample_limit),
        "jsonl_sample_rows": len(sample_records),
        "full_captured_records_counted": len(records),
    }
    write_json(payload, args.output_json)
    write_jsonl(sample_records, args.output_jsonl)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_jsonl}")
    print(f"wrote {args.output_md}")
    coverage = payload["summary"]["coverage"]
    print(
        f"captured={coverage['captured_setup_rows']} "
        f"lower_tf_rate={coverage['lower_tf_available_rate']} "
        f"promotion={payload['summary']['promotion_verdict']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
