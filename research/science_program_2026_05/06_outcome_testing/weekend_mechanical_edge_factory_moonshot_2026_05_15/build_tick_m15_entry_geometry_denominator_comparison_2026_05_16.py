#!/usr/bin/env python3
"""Compare residual path geometry against each residual denominator.

The prior path-geometry packet described flagged residual rows only. This
builder computes the same direction-family path geometry for every denominator
row in each residual descriptor and compares flagged geometry against its
own denominator. No fill, R/PnL, validation, live-readiness, or promotion is
claimed.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

PRIMITIVE_EVENT_LEDGER = ROUTE_DIR / f"TICK_M15_PRIMITIVE_EVENT_LEDGER_{SOURCE_STAMP}.jsonl"
ROW_RECONSTRUCTION_LEDGER = ROUTE_DIR / f"TICK_M15_RESIDUAL_ROW_RECONSTRUCTION_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"TICK_M15_ENTRY_GEOMETRY_DENOMINATOR_COMPARISON_RESULT_{STAMP}.json"
DENOMINATOR_GEOMETRY_ROW_LEDGER = ROUTE_DIR / f"TICK_M15_ENTRY_GEOMETRY_DENOMINATOR_ROW_LEDGER_{STAMP}.jsonl"
COMPARISON_LEDGER = ROUTE_DIR / f"TICK_M15_ENTRY_GEOMETRY_DENOMINATOR_COMPARISON_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"TICK_M15_ENTRY_GEOMETRY_DENOMINATOR_BUCKET_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"TICK_M15_ENTRY_GEOMETRY_DENOMINATOR_COMPARISON_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Route C entry geometry denominator comparison only; no fill simulation, "
    "validation, trade outcome, R/PnL, expectancy, live-readiness, or promotion"
)

HORIZON_BARS = {"h4": 4, "h16": 16, "h32": 32}


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


def safe_float(value: Any) -> float | None:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if value != value or value in (float("inf"), float("-inf")):
        return None
    return value


def mean(values: list[float]) -> float | None:
    numeric = [value for value in values if safe_float(value) is not None]
    return safe_float(sum(numeric) / len(numeric)) if numeric else None


def median(values: list[float]) -> float | None:
    numeric = sorted(value for value in values if safe_float(value) is not None)
    if not numeric:
        return None
    mid = len(numeric) // 2
    if len(numeric) % 2:
        return safe_float(numeric[mid])
    return safe_float((numeric[mid - 1] + numeric[mid]) / 2)


def rate(values: list[bool]) -> float | None:
    return safe_float(sum(1 for value in values if value) / len(values)) if values else None


def parse_utc(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def sign_from_value(value: Any) -> int:
    numeric = safe_float(value)
    if numeric is None:
        return 0
    if numeric > 0:
        return 1
    if numeric < 0:
        return -1
    return 0


def direction_specs(row: dict[str, Any]) -> list[tuple[str, int]]:
    specs: list[tuple[str, int]] = []
    delta_sign = int(row.get("delta_sign") or 0)
    price_sign = sign_from_value(row.get("source_fields", {}).get("price_change"))
    if delta_sign:
        specs.append(("delta_follow", delta_sign))
        specs.append(("delta_inverse", -delta_sign))
    if price_sign:
        specs.append(("price_follow", price_sign))
        specs.append(("price_inverse", -price_sign))
    return specs


def first_touch_order(path_rows: list[dict[str, Any]], entry_mid: float, direction: int, threshold: float) -> str:
    favorable_first = None
    adverse_first = None
    for offset, row in enumerate(path_rows, 1):
        high = safe_float(row.get("mid_high"))
        low = safe_float(row.get("mid_low"))
        if high is None or low is None:
            continue
        favorable = high - entry_mid if direction > 0 else entry_mid - low
        adverse = entry_mid - low if direction > 0 else high - entry_mid
        if favorable_first is None and favorable >= threshold:
            favorable_first = offset
        if adverse_first is None and adverse >= threshold:
            adverse_first = offset
        if favorable_first is not None and adverse_first is not None:
            break
    if favorable_first is None and adverse_first is None:
        return "neither_touched"
    if favorable_first is not None and adverse_first is None:
        return "favorable_only"
    if favorable_first is None and adverse_first is not None:
        return "adverse_only"
    if favorable_first < adverse_first:
        return "favorable_first"
    if adverse_first < favorable_first:
        return "adverse_first"
    return "same_bar_touch_ambiguous"


def path_metrics(current: dict[str, Any], path_rows: list[dict[str, Any]], direction: int) -> dict[str, Any]:
    entry_mid = safe_float(current.get("mid_close"))
    spread_max = safe_float(current.get("spread_max"))
    current_range = safe_float(current.get("price_range"))
    future_mid = safe_float(path_rows[-1].get("mid_close")) if path_rows else None
    if entry_mid is None or spread_max is None or spread_max <= 0 or not path_rows:
        return {"path_status": "missing_entry_spread_or_path"}
    highs = [safe_float(row.get("mid_high")) for row in path_rows if safe_float(row.get("mid_high")) is not None]
    lows = [safe_float(row.get("mid_low")) for row in path_rows if safe_float(row.get("mid_low")) is not None]
    if not highs or not lows:
        return {"path_status": "missing_high_low"}
    if direction > 0:
        mfe = max(0.0, max(highs) - entry_mid)
        mae = max(0.0, entry_mid - min(lows))
    else:
        mfe = max(0.0, entry_mid - min(lows))
        mae = max(0.0, max(highs) - entry_mid)
    final_change = direction * (future_mid - entry_mid) if future_mid is not None else None
    one_spread = first_touch_order(path_rows, entry_mid, direction, spread_max)
    two_spread = first_touch_order(path_rows, entry_mid, direction, spread_max * 2.0)
    one_range = (
        first_touch_order(path_rows, entry_mid, direction, current_range)
        if current_range is not None and current_range > 0 else "threshold_unavailable"
    )
    return {
        "path_status": "ok",
        "mfe_to_spread_max": safe_float(mfe / spread_max),
        "mae_to_spread_max": safe_float(mae / spread_max),
        "final_to_spread_max": safe_float(final_change / spread_max) if final_change is not None else None,
        "final_directional_change": safe_float(final_change),
        "one_spread_touch_order": one_spread,
        "two_spread_touch_order": two_spread,
        "one_range_touch_order": one_range,
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ok = [row for row in rows if row["path_status"] == "ok"]
    one_counts = Counter(row["one_spread_touch_order"] for row in ok)
    two_counts = Counter(row["two_spread_touch_order"] for row in ok)
    return {
        "n": len(rows),
        "ok_n": len(ok),
        "median_mfe_to_spread_max": median([row["mfe_to_spread_max"] for row in ok if row.get("mfe_to_spread_max") is not None]),
        "median_mae_to_spread_max": median([row["mae_to_spread_max"] for row in ok if row.get("mae_to_spread_max") is not None]),
        "mean_final_to_spread_max": mean([row["final_to_spread_max"] for row in ok if row.get("final_to_spread_max") is not None]),
        "final_positive_share": rate([row["final_directional_change"] > 0 for row in ok if row.get("final_directional_change") is not None]),
        "one_spread_touch_order_counts": dict(one_counts),
        "one_spread_favorable_first_or_only_share": safe_float((one_counts.get("favorable_first", 0) + one_counts.get("favorable_only", 0)) / sum(one_counts.values())) if one_counts else None,
        "two_spread_touch_order_counts": dict(two_counts),
        "two_spread_favorable_first_or_only_share": safe_float((two_counts.get("favorable_first", 0) + two_counts.get("favorable_only", 0)) / sum(two_counts.values())) if two_counts else None,
    }


def bucket(flagged: dict[str, Any], denominator: dict[str, Any]) -> str:
    if flagged["ok_n"] < 20:
        return "GEOMETRY_UNDERPOWERED"
    flagged_mfe = flagged["median_mfe_to_spread_max"]
    denom_mfe = denominator["median_mfe_to_spread_max"]
    flagged_mae = flagged["median_mae_to_spread_max"]
    denom_mae = denominator["median_mae_to_spread_max"]
    flagged_final = flagged["final_positive_share"]
    denom_final = denominator["final_positive_share"]
    if flagged_mfe is None or denom_mfe is None:
        return "GEOMETRY_NOT_NUMERIC"
    beats_mfe = flagged_mfe > denom_mfe
    beats_mae = flagged_mae is not None and denom_mae is not None and flagged_mae <= denom_mae
    beats_final = flagged_final is not None and denom_final is not None and flagged_final >= denom_final
    if beats_mfe and beats_mae and beats_final:
        return "GEOMETRY_FLAGGED_BEATS_DENOMINATOR_DIAGNOSTIC"
    if beats_mfe:
        return "GEOMETRY_FLAGGED_HAS_MORE_EXCURSION_BUT_MORE_RISK_OR_WEAK_FINAL"
    return "GEOMETRY_DENOMINATOR_EXPLAINS_OR_WEAKENS"


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "tick_m15_entry_geometry_denominator_comparison_builder", "created"),
        (RESULT_PATH, "tick_m15_entry_geometry_denominator_comparison_result", "created"),
        (DENOMINATOR_GEOMETRY_ROW_LEDGER, "tick_m15_entry_geometry_denominator_row_ledger", "created"),
        (COMPARISON_LEDGER, "tick_m15_entry_geometry_denominator_comparison_ledger", "created"),
        (BUCKET_LEDGER, "tick_m15_entry_geometry_denominator_bucket_ledger", "created"),
        (SUMMARY_PATH, "tick_m15_entry_geometry_denominator_comparison_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], bucket_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "tick_m15_entry_geometry_denominator_comparison",
        "status": "done",
        "route": "tick_sierra_orderflow_route_c",
        "details": (
            "Compared residual flagged path geometry against every same residual denominator row and direction family. "
            "This repairs selected-row-only geometry diagnostics without creating fill/R/PnL claims."
        ),
        "counts": counts,
        "bucket_counts": bucket_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(DENOMINATOR_GEOMETRY_ROW_LEDGER),
            relative(COMPARISON_LEDGER),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def main() -> int:
    generated_utc = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    primitive_rows = read_jsonl(PRIMITIVE_EVENT_LEDGER)
    reconstruction_rows = read_jsonl(ROW_RECONSTRUCTION_LEDGER)

    primitive_by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in primitive_rows:
        primitive_by_symbol[row["symbol"]].append(row)
    for rows in primitive_by_symbol.values():
        rows.sort(key=lambda row: row["bar_open_utc"])
    primitive_by_symbol_bar = {f"{row['symbol']}|{row['bar_open_utc']}": row for row in primitive_rows}
    index_by_symbol_bar = {
        f"{row['symbol']}|{row['bar_open_utc']}": idx
        for symbol, rows in primitive_by_symbol.items()
        for idx, row in enumerate(rows)
    }

    geometry_rows: list[dict[str, Any]] = []
    for row in reconstruction_rows:
        current = primitive_by_symbol_bar.get(row["row_id"])
        current_idx = index_by_symbol_bar.get(row["row_id"])
        horizon_bars = HORIZON_BARS[row["horizon_id"]]
        if current is None or current_idx is None:
            path = []
            path_status = "current_source_missing"
        else:
            symbol_rows = primitive_by_symbol[row["symbol"]]
            path = symbol_rows[current_idx + 1:current_idx + horizon_bars + 1]
            expected = parse_utc(row["bar_open_utc"]) + timedelta(minutes=15 * horizon_bars)
            actual = parse_utc(path[-1]["bar_open_utc"]) if path else None
            path_status = "ok" if len(path) == horizon_bars and actual == expected else "future_path_not_contiguous"
        for direction_family, direction in direction_specs(row):
            metrics = (
                path_metrics(current, path, direction)
                if path_status == "ok" and current is not None
                else {"path_status": path_status}
            )
            geometry_rows.append({
                "queue_id": row["queue_id"],
                "route_id": ROUTE_ID,
                "row_id": row["row_id"],
                "is_flagged": row["is_flagged"],
                "symbol": row["symbol"],
                "session_bucket": row["session_bucket"],
                "horizon_id": row["horizon_id"],
                "primitive_flag": row["primitive_flag"],
                "bar_open_utc": row["bar_open_utc"],
                "direction_family": direction_family,
                "direction_sign": direction,
                **metrics,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            })

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in geometry_rows:
        grouped[(row["queue_id"], row["direction_family"])].append(row)

    comparison_rows: list[dict[str, Any]] = []
    for (queue_id, direction_family), rows in sorted(grouped.items()):
        flagged = [row for row in rows if row["is_flagged"]]
        denominator = rows
        flagged_stats = aggregate(flagged)
        denominator_stats = aggregate(denominator)
        first = rows[0]
        comparison_rows.append({
            "queue_id": queue_id,
            "route_id": ROUTE_ID,
            "symbol": first["symbol"],
            "session_bucket": first["session_bucket"],
            "horizon_id": first["horizon_id"],
            "primitive_flag": first["primitive_flag"],
            "direction_family": direction_family,
            "flagged_geometry": flagged_stats,
            "denominator_geometry": denominator_stats,
            "geometry_comparison_bucket": bucket(flagged_stats, denominator_stats),
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        })

    bucket_counts = Counter(row["geometry_comparison_bucket"] for row in comparison_rows)
    bucket_rows = [
        {
            "route_id": ROUTE_ID,
            "geometry_comparison_bucket": bucket_name,
            "row_count": count,
            "evidence_boundary": "bucket count only; no validation or promotion",
            "safe_flags": SAFE_FLAGS,
        }
        for bucket_name, count in sorted(bucket_counts.items())
    ]

    write_jsonl(DENOMINATOR_GEOMETRY_ROW_LEDGER, geometry_rows)
    write_jsonl(COMPARISON_LEDGER, comparison_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)

    counts = {
        "denominator_geometry_row_rows": len(geometry_rows),
        "comparison_rows": len(comparison_rows),
        "bucket_rows": len(bucket_rows),
    }
    result = {
        "schema": "tick_m15_entry_geometry_denominator_comparison_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "ROUTE_C_ENTRY_GEOMETRY_DENOMINATOR_COMPARISON_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "bucket_counts": dict(bucket_counts),
        "next_same_resource_work": [
            "keep only geometry families that beat denominator as branch-local challenger inputs",
            "turn weakened geometry families into avoid/inverse tests",
            "deduplicate overlapping bars before any future comparison",
        ],
        "not_completion": "This repairs selected-row-only geometry but does not complete the 60-hour objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = [
        "# Tick M15 Entry Geometry Denominator Comparison",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: denominator path-geometry diagnostics only. No fill simulation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        summary.append(f"- `{key}`: `{value}`")
    summary.extend(["", "## Buckets", ""])
    for bucket_name, count in sorted(bucket_counts.items()):
        summary.append(f"- `{bucket_name}`: `{count}`")
    summary.extend([
        "",
        "## Boundary",
        "",
        "- Every row is still a path diagnostic from M15 high/low bars, not an executable fill.",
        "- This comparison decides whether selected residual geometry is special versus its denominator, not whether it is tradable.",
        "",
    ])
    SUMMARY_PATH.write_text("\n".join(summary), encoding="utf-8")

    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, dict(bucket_counts))
    print(json.dumps({"ok": True, "counts": counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
