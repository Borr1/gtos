#!/usr/bin/env python3
"""Build development-only target-movement controls for M15 tick primitives.

This packet attaches future mid-price movement to tick descriptor rows only
when the future M15 bar is contiguous and neither row is current-day partial.
It compares primitive flags against all targetable rows in the same
symbol/session/horizon denominator.

It is not validation, trade outcome analysis, R/PnL, live-readiness, or
promotion evidence.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
STAMP = "2026-05-15"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

EVENT_LEDGER = ROUTE_DIR / f"TICK_M15_PRIMITIVE_EVENT_LEDGER_{STAMP}.jsonl"
FLAG_SUMMARY_LEDGER = ROUTE_DIR / f"TICK_M15_PRIMITIVE_FLAG_SUMMARY_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"TICK_M15_TARGET_MOVEMENT_PACKET_RESULT_{STAMP}.json"
TARGET_EVENT_LEDGER = ROUTE_DIR / f"TICK_M15_TARGET_MOVEMENT_EVENT_LEDGER_{STAMP}.jsonl"
FLAG_CONTROL_LEDGER = ROUTE_DIR / f"TICK_M15_TARGET_MOVEMENT_FLAG_CONTROL_LEDGER_{STAMP}.jsonl"
FAIL_CLOSED_LEDGER = ROUTE_DIR / f"TICK_M15_TARGET_MOVEMENT_FAIL_CLOSED_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"TICK_M15_TARGET_MOVEMENT_PACKET_SUMMARY_{STAMP}.md"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

HORIZONS = {
    "h4": 4,
    "h16": 16,
    "h32": 32,
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def parse_utc(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def safe_float(value: Any) -> float | None:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if value != value or value in (float("inf"), float("-inf")):
        return None
    return value


def sign(value: float | None) -> int:
    if value is None:
        return 0
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def mean(values: list[float]) -> float | None:
    return safe_float(sum(values) / len(values)) if values else None


def rate(values: list[bool]) -> float | None:
    return safe_float(sum(1 for v in values if v) / len(values)) if values else None


def fail_row(row: dict[str, Any], horizon_id: str, reason: str) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "symbol": row["symbol"],
        "bar_open_utc": row["bar_open_utc"],
        "session_bucket": row["session_bucket"],
        "horizon_id": horizon_id,
        "fail_reason": reason,
        "primitive_flags": row.get("primitive_flags", []),
        "evidence_boundary": "fail-closed target movement construction row; no target or strategy result",
        "safe_flags": SAFE_FLAGS,
    }


def build_target_rows(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_symbol: dict[str, list[dict[str, Any]]] = {}
    for row in events:
        by_symbol.setdefault(row["symbol"], []).append(row)
    for rows in by_symbol.values():
        rows.sort(key=lambda r: r["bar_open_utc"])

    target_rows: list[dict[str, Any]] = []
    fail_rows: list[dict[str, Any]] = []
    for symbol, rows in by_symbol.items():
        for idx, row in enumerate(rows):
            current_dt = parse_utc(row["bar_open_utc"])
            for horizon_id, horizon_bars in HORIZONS.items():
                if row.get("source_completeness") == "current_day_partial_at_generation":
                    fail_rows.append(fail_row(row, horizon_id, "current_day_partial_excluded"))
                    continue
                future_idx = idx + horizon_bars
                if future_idx >= len(rows):
                    fail_rows.append(fail_row(row, horizon_id, "future_bar_missing"))
                    continue
                future = rows[future_idx]
                future_dt = parse_utc(future["bar_open_utc"])
                expected_dt = current_dt + timedelta(minutes=15 * horizon_bars)
                if future_dt != expected_dt:
                    fail_rows.append(fail_row(row, horizon_id, "future_bar_not_contiguous"))
                    continue
                if future.get("source_completeness") == "current_day_partial_at_generation":
                    fail_rows.append(fail_row(row, horizon_id, "future_current_day_partial_excluded"))
                    continue
                current_mid = safe_float(row.get("mid_close"))
                future_mid = safe_float(future.get("mid_close"))
                if current_mid is None or future_mid is None:
                    fail_rows.append(fail_row(row, horizon_id, "missing_mid_close"))
                    continue
                future_change = future_mid - current_mid
                current_range = safe_float(row.get("price_range")) or 0.0
                range_norm_change = None
                if current_range > 0:
                    range_norm_change = future_change / current_range
                delta_sign = sign(safe_float(row.get("cumulative_delta")))
                price_sign = sign(safe_float(row.get("price_change")))
                future_sign = sign(future_change)
                target_rows.append({
                    "route_id": ROUTE_ID,
                    "symbol": symbol,
                    "bar_open_utc": row["bar_open_utc"],
                    "bar_close_utc": row["bar_close_utc"],
                    "session_bucket": row["session_bucket"],
                    "horizon_id": horizon_id,
                    "horizon_bars": horizon_bars,
                    "future_bar_open_utc": future["bar_open_utc"],
                    "current_mid_close": current_mid,
                    "future_mid_close": future_mid,
                    "future_change": safe_float(future_change),
                    "future_abs_change": abs(future_change),
                    "future_change_per_current_range": safe_float(range_norm_change),
                    "delta_sign": delta_sign,
                    "price_sign": price_sign,
                    "future_sign": future_sign,
                    "delta_aligned_with_future": (delta_sign != 0 and future_sign != 0 and delta_sign == future_sign),
                    "price_aligned_with_future": (price_sign != 0 and future_sign != 0 and price_sign == future_sign),
                    "primitive_flags": row.get("primitive_flags", []),
                    "primitive_flag_count": row.get("primitive_flag_count", 0),
                    "evidence_boundary": "development neutral target movement only; no trade outcome, R/PnL, validation, live-readiness, or promotion",
                    "safe_flags": SAFE_FLAGS,
                })
    return target_rows, fail_rows


def build_control_rows(
    target_rows: list[dict[str, Any]],
    flag_universe: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    denominator: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in target_rows:
        key = (row["symbol"], row["session_bucket"], row["horizon_id"])
        denominator.setdefault(key, []).append(row)

    control_rows: list[dict[str, Any]] = []
    seen_flag_keys: set[tuple[str, str, str]] = set()
    for flag_row in flag_universe:
        flag_key = (
            flag_row["symbol"],
            flag_row["session_bucket"],
            flag_row["primitive_flag"],
        )
        if flag_key in seen_flag_keys:
            continue
        seen_flag_keys.add(flag_key)
        symbol, session, primitive_flag = flag_key
        for horizon_id in HORIZONS:
            denom_rows = denominator.get((symbol, session, horizon_id), [])
            flagged_rows = [
                row for row in denom_rows
                if primitive_flag in row.get("primitive_flags", [])
            ]
            control_changes = [row["future_change"] for row in denom_rows if row.get("future_change") is not None]
            flagged_changes = [row["future_change"] for row in flagged_rows if row.get("future_change") is not None]
            control_abs = [row["future_abs_change"] for row in denom_rows if row.get("future_abs_change") is not None]
            flagged_abs = [row["future_abs_change"] for row in flagged_rows if row.get("future_abs_change") is not None]
            control_range_norm = [
                row["future_change_per_current_range"]
                for row in denom_rows
                if row.get("future_change_per_current_range") is not None
            ]
            flagged_range_norm = [
                row["future_change_per_current_range"]
                for row in flagged_rows
                if row.get("future_change_per_current_range") is not None
            ]
            control_delta_align = [
                row["delta_aligned_with_future"]
                for row in denom_rows
                if row.get("delta_sign", 0) != 0 and row.get("future_sign", 0) != 0
            ]
            flagged_delta_align = [
                row["delta_aligned_with_future"]
                for row in flagged_rows
                if row.get("delta_sign", 0) != 0 and row.get("future_sign", 0) != 0
            ]
            flagged_n = len(flagged_rows)
            control_n = len(denom_rows)
            flagged_abs_mean = mean(flagged_abs)
            control_abs_mean = mean(control_abs)
            delta_abs_mean = None
            if flagged_abs_mean is not None and control_abs_mean is not None:
                delta_abs_mean = flagged_abs_mean - control_abs_mean
            control_rows.append({
                "route_id": ROUTE_ID,
                "symbol": symbol,
                "session_bucket": session,
                "primitive_flag": primitive_flag,
                "horizon_id": horizon_id,
                "horizon_bars": HORIZONS[horizon_id],
                "flagged_n": flagged_n,
                "control_n": control_n,
                "sample_status": "DESCRIPTIVE_N_GE_20" if flagged_n >= 20 else "DESCRIPTIVE_SMALL_N_LT20",
                "control_scope": "all_targetable_rows_same_symbol_session_horizon_including_flagged",
                "flagged_mean_future_change": mean(flagged_changes),
                "control_mean_future_change": mean(control_changes),
                "flagged_mean_abs_future_change": flagged_abs_mean,
                "control_mean_abs_future_change": control_abs_mean,
                "delta_mean_abs_future_change": safe_float(delta_abs_mean),
                "flagged_mean_future_change_per_current_range": mean(flagged_range_norm),
                "control_mean_future_change_per_current_range": mean(control_range_norm),
                "flagged_delta_alignment_n": len(flagged_delta_align),
                "control_delta_alignment_n": len(control_delta_align),
                "flagged_delta_alignment_rate": rate(flagged_delta_align),
                "control_delta_alignment_rate": rate(control_delta_align),
                "evidence_boundary": "development neutral target movement contrast only; not validation, trade outcome, R/PnL, live-readiness, or promotion",
                "safe_flags": SAFE_FLAGS,
            })
    return control_rows


def main() -> int:
    generated_utc_s = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    events = read_jsonl(EVENT_LEDGER)
    flag_universe = read_jsonl(FLAG_SUMMARY_LEDGER)
    target_rows, fail_rows = build_target_rows(events)
    control_rows = build_control_rows(target_rows, flag_universe)

    write_jsonl(TARGET_EVENT_LEDGER, target_rows)
    write_jsonl(FLAG_CONTROL_LEDGER, control_rows)
    write_jsonl(FAIL_CLOSED_LEDGER, fail_rows)

    descriptive_ge_20 = sum(1 for row in control_rows if row["sample_status"] == "DESCRIPTIVE_N_GE_20")
    result = {
        "schema": "tick_m15_target_movement_packet_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc_s,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "DEVELOPMENT_NEUTRAL_TARGET_MOVEMENT_CONTROL_PACKET_ONLY",
        "claim_boundary": "Development target-movement controls only. No validation, trade outcome, R/PnL, expectancy, live-readiness, or promotion claim.",
        "counts": {
            "primitive_event_rows": len(events),
            "target_event_rows": len(target_rows),
            "flag_control_rows": len(control_rows),
            "fail_closed_rows": len(fail_rows),
            "flag_universe_rows": len(flag_universe),
            "descriptive_n_ge_20_control_rows": descriptive_ge_20,
        },
        "horizons": HORIZONS,
        "open_blockers": [
            "development-sample only; no sealed/future split opened",
            "target movement is not trade outcome or fillable R",
            "same-denominator control includes flagged rows and is not a promotion test",
            "current-day partial rows are fail-closed excluded",
            "neighbor/placebo/shuffle controls still required before candidate ranking",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    sample_status_counts: dict[str, int] = {}
    for row in control_rows:
        sample_status_counts[row["sample_status"]] = sample_status_counts.get(row["sample_status"], 0) + 1

    summary = [
        "# Tick M15 Target Movement Packet",
        "",
        f"Generated UTC: `{generated_utc_s}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: development neutral target-movement controls only. No validation, R/PnL, live-readiness, or promotion verdict.",
        "",
        "## Counts",
        "",
        f"- Primitive event rows: `{len(events)}`",
        f"- Target event rows: `{len(target_rows)}`",
        f"- Flag control rows: `{len(control_rows)}`",
        f"- Fail-closed rows: `{len(fail_rows)}`",
        f"- Flag universe rows: `{len(flag_universe)}`",
        f"- Control rows with flagged_n >= 20: `{descriptive_ge_20}`",
        "",
        "## Sample Status",
        "",
    ]
    for status, count in sorted(sample_status_counts.items()):
        summary.append(f"- `{status}`: `{count}`")
    summary.extend([
        "",
        "## Boundary",
        "",
        "- Current-day partial rows are excluded fail-closed.",
        "- Future bars must be contiguous.",
        "- Same-symbol/session/horizon controls are development denominators, not validation.",
        "- No neighbor/placebo/shuffle ranking has been applied yet.",
        "",
    ])
    SUMMARY_PATH.write_text("\n".join(summary), encoding="utf-8")

    print(json.dumps({"ok": True, "target_rows": len(target_rows), "control_rows": len(control_rows), "fail_closed_rows": len(fail_rows), "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
