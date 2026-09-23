#!/usr/bin/env python3
"""Build residual entry/path geometry diagnostics from M15 tick bars.

This computes path excursions after every residual flagged reference using the
source primitive M15 high/low path, for follow and inverse versions of delta
and price direction proxies. It creates executable-geometry questions without
claiming fills, R/PnL, validation, live-readiness, or promotion.
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
FRICTION_RESIDUAL_LEDGER = ROUTE_DIR / f"TICK_M15_EXECUTION_FRICTION_RESIDUAL_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"TICK_M15_ENTRY_PATH_GEOMETRY_RESULT_{STAMP}.json"
ROW_LEDGER = ROUTE_DIR / f"TICK_M15_ENTRY_PATH_GEOMETRY_ROW_LEDGER_{STAMP}.jsonl"
RESIDUAL_DIRECTION_LEDGER = ROUTE_DIR / f"TICK_M15_ENTRY_PATH_GEOMETRY_RESIDUAL_DIRECTION_LEDGER_{STAMP}.jsonl"
CHALLENGER_SPEC_LEDGER = ROUTE_DIR / f"TICK_M15_ENTRY_PATH_GEOMETRY_CHALLENGER_SPEC_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"TICK_M15_ENTRY_PATH_GEOMETRY_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"TICK_M15_ENTRY_PATH_GEOMETRY_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Route C entry/path geometry diagnostics only; no fill simulation, validation, "
    "trade outcome, R/PnL, expectancy, live-readiness, or promotion"
)

HORIZON_BARS = {"h4": 4, "h16": 16, "h32": 32}
THRESHOLDS = [
    ("one_spread_max", "spread_max", 1.0),
    ("two_spread_max", "spread_max", 2.0),
    ("one_current_range", "price_range", 1.0),
]


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


def sign_label(sign: int) -> str:
    if sign > 0:
        return "long"
    if sign < 0:
        return "short"
    return "flat"


def direction_specs(row: dict[str, Any]) -> list[tuple[str, int]]:
    specs: list[tuple[str, int]] = []
    delta_sign = int(row.get("delta_sign") or 0)
    price_sign = int(row.get("source_fields", {}).get("price_change") and (1 if row["source_fields"]["price_change"] > 0 else -1 if row["source_fields"]["price_change"] < 0 else 0) or 0)
    if delta_sign:
        specs.append(("delta_follow", delta_sign))
        specs.append(("delta_inverse", -delta_sign))
    if price_sign:
        specs.append(("price_follow", price_sign))
        specs.append(("price_inverse", -price_sign))
    return specs


def first_touch(
    path_rows: list[dict[str, Any]],
    entry_mid: float,
    direction: int,
    threshold: float,
) -> dict[str, Any]:
    first_favorable = None
    first_adverse = None
    for offset, row in enumerate(path_rows, 1):
        high = safe_float(row.get("mid_high"))
        low = safe_float(row.get("mid_low"))
        if high is None or low is None:
            continue
        favorable = high - entry_mid if direction > 0 else entry_mid - low
        adverse = entry_mid - low if direction > 0 else high - entry_mid
        if first_favorable is None and favorable >= threshold:
            first_favorable = offset
        if first_adverse is None and adverse >= threshold:
            first_adverse = offset
        if first_favorable is not None and first_adverse is not None:
            break
    if first_favorable is None and first_adverse is None:
        order = "neither_touched"
    elif first_favorable is not None and first_adverse is None:
        order = "favorable_only"
    elif first_favorable is None and first_adverse is not None:
        order = "adverse_only"
    elif first_favorable < first_adverse:
        order = "favorable_first"
    elif first_adverse < first_favorable:
        order = "adverse_first"
    else:
        order = "same_bar_touch_ambiguous"
    return {
        "first_favorable_bar_offset": first_favorable,
        "first_adverse_bar_offset": first_adverse,
        "touch_order": order,
    }


def path_metrics(
    current: dict[str, Any],
    path_rows: list[dict[str, Any]],
    direction_family: str,
    direction: int,
) -> dict[str, Any]:
    entry_mid = safe_float(current.get("mid_close"))
    future_mid = safe_float(path_rows[-1].get("mid_close")) if path_rows else None
    spread_max = safe_float(current.get("spread_max"))
    current_range = safe_float(current.get("price_range"))
    if entry_mid is None or not path_rows:
        return {"path_status": "missing_entry_or_path"}
    highs = [safe_float(row.get("mid_high")) for row in path_rows if safe_float(row.get("mid_high")) is not None]
    lows = [safe_float(row.get("mid_low")) for row in path_rows if safe_float(row.get("mid_low")) is not None]
    if not highs or not lows:
        return {"path_status": "missing_path_high_low"}
    if direction > 0:
        mfe = max(0.0, max(highs) - entry_mid)
        mae = max(0.0, entry_mid - min(lows))
    else:
        mfe = max(0.0, entry_mid - min(lows))
        mae = max(0.0, max(highs) - entry_mid)
    final_directional_change = direction * (future_mid - entry_mid) if future_mid is not None else None
    threshold_results: dict[str, Any] = {}
    for threshold_id, source_field, multiplier in THRESHOLDS:
        source_value = spread_max if source_field == "spread_max" else current_range
        if source_value is None or source_value <= 0:
            threshold_results[threshold_id] = {"threshold": None, "touch_order": "threshold_unavailable"}
            continue
        threshold = source_value * multiplier
        touch = first_touch(path_rows, entry_mid, direction, threshold)
        threshold_results[threshold_id] = {"threshold": safe_float(threshold), **touch}
    return {
        "path_status": "ok",
        "direction_family": direction_family,
        "direction_sign": direction,
        "direction_label": sign_label(direction),
        "entry_mid_close_proxy": entry_mid,
        "future_mid_close": future_mid,
        "final_directional_change": safe_float(final_directional_change),
        "max_favorable_excursion": safe_float(mfe),
        "max_adverse_excursion": safe_float(mae),
        "mfe_to_spread_max": safe_float(mfe / spread_max) if spread_max else None,
        "mae_to_spread_max": safe_float(mae / spread_max) if spread_max else None,
        "final_to_spread_max": safe_float(final_directional_change / spread_max) if spread_max and final_directional_change is not None else None,
        "mfe_to_current_range": safe_float(mfe / current_range) if current_range else None,
        "mae_to_current_range": safe_float(mae / current_range) if current_range else None,
        "threshold_results": threshold_results,
    }


def direction_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ok_rows = [row for row in rows if row["path_metrics"].get("path_status") == "ok"]
    touch_ids = [threshold_id for threshold_id, _, _ in THRESHOLDS]
    stats = {
        "n": len(rows),
        "ok_n": len(ok_rows),
        "median_mfe_to_spread_max": median([
            row["path_metrics"].get("mfe_to_spread_max") for row in ok_rows
            if row["path_metrics"].get("mfe_to_spread_max") is not None
        ]),
        "median_mae_to_spread_max": median([
            row["path_metrics"].get("mae_to_spread_max") for row in ok_rows
            if row["path_metrics"].get("mae_to_spread_max") is not None
        ]),
        "mean_final_to_spread_max": mean([
            row["path_metrics"].get("final_to_spread_max") for row in ok_rows
            if row["path_metrics"].get("final_to_spread_max") is not None
        ]),
        "final_positive_share": rate([
            row["path_metrics"].get("final_directional_change", 0) > 0 for row in ok_rows
            if row["path_metrics"].get("final_directional_change") is not None
        ]),
    }
    for threshold_id in touch_ids:
        orders = [
            row["path_metrics"].get("threshold_results", {}).get(threshold_id, {}).get("touch_order")
            for row in ok_rows
        ]
        counts = Counter(order for order in orders if order)
        denom = sum(counts.values())
        stats[f"{threshold_id}_touch_order_counts"] = dict(counts)
        stats[f"{threshold_id}_favorable_first_or_only_share"] = (
            safe_float((counts.get("favorable_first", 0) + counts.get("favorable_only", 0)) / denom)
            if denom else None
        )
        stats[f"{threshold_id}_adverse_first_or_only_share"] = (
            safe_float((counts.get("adverse_first", 0) + counts.get("adverse_only", 0)) / denom)
            if denom else None
        )
    return stats


def geometry_bucket(stats: dict[str, Any]) -> str:
    if stats["ok_n"] < 20:
        return "PATH_GEOMETRY_UNDERPOWERED"
    one_spread_fav = stats.get("one_spread_max_favorable_first_or_only_share")
    two_spread_fav = stats.get("two_spread_max_favorable_first_or_only_share")
    final_positive = stats.get("final_positive_share")
    median_mfe = stats.get("median_mfe_to_spread_max")
    median_mae = stats.get("median_mae_to_spread_max")
    if (
        one_spread_fav is not None and one_spread_fav >= 0.60
        and two_spread_fav is not None and two_spread_fav >= 0.45
        and final_positive is not None and final_positive >= 0.50
    ):
        return "PATH_GEOMETRY_FAVORABLE_BEFORE_ADVERSE_DIAGNOSTIC"
    if median_mfe is not None and median_mae is not None and median_mfe > median_mae:
        return "PATH_GEOMETRY_EXCURSION_SKEW_FAVORABLE"
    return "PATH_GEOMETRY_ADVERSE_OR_CHOP_DIAGNOSTIC"


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "tick_m15_entry_path_geometry_builder", "created"),
        (RESULT_PATH, "tick_m15_entry_path_geometry_result", "created"),
        (ROW_LEDGER, "tick_m15_entry_path_geometry_row_ledger", "created"),
        (RESIDUAL_DIRECTION_LEDGER, "tick_m15_entry_path_geometry_residual_direction_ledger", "created"),
        (CHALLENGER_SPEC_LEDGER, "tick_m15_entry_path_geometry_challenger_spec_ledger", "created"),
        (QUESTION_LEDGER, "tick_m15_entry_path_geometry_question_ledger", "created"),
        (SUMMARY_PATH, "tick_m15_entry_path_geometry_summary", "created"),
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
        "event_type": "tick_m15_entry_path_geometry",
        "status": "done",
        "route": "tick_sierra_orderflow_route_c",
        "details": (
            "Computed future M15 path excursions for every residual flagged reference using delta/price follow "
            "and inverse direction proxies. This defines geometry diagnostics only, not fills or R/PnL."
        ),
        "counts": counts,
        "geometry_bucket_counts": bucket_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(ROW_LEDGER),
            relative(RESIDUAL_DIRECTION_LEDGER),
            relative(CHALLENGER_SPEC_LEDGER),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def main() -> int:
    generated_utc = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    primitive_rows = read_jsonl(PRIMITIVE_EVENT_LEDGER)
    residual_rows = [row for row in read_jsonl(ROW_RECONSTRUCTION_LEDGER) if row["is_flagged"]]
    friction_by_queue = {row["queue_id"]: row for row in read_jsonl(FRICTION_RESIDUAL_LEDGER)}

    primitive_by_symbol_bar = {
        f"{row['symbol']}|{row['bar_open_utc']}": row
        for row in primitive_rows
    }
    primitive_by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in primitive_rows:
        primitive_by_symbol[row["symbol"]].append(row)
    for rows in primitive_by_symbol.values():
        rows.sort(key=lambda row: row["bar_open_utc"])
    index_by_symbol_bar = {
        f"{row['symbol']}|{row['bar_open_utc']}": idx
        for symbol, rows in primitive_by_symbol.items()
        for idx, row in enumerate(rows)
    }

    path_rows: list[dict[str, Any]] = []
    for residual in residual_rows:
        current = primitive_by_symbol_bar.get(f"{residual['symbol']}|{residual['bar_open_utc']}")
        current_idx = index_by_symbol_bar.get(f"{residual['symbol']}|{residual['bar_open_utc']}")
        horizon_bars = HORIZON_BARS[residual["horizon_id"]]
        symbol_rows = primitive_by_symbol[residual["symbol"]]
        if current is None or current_idx is None:
            future_path = []
            path_status = "current_source_row_missing"
        else:
            future_path = symbol_rows[current_idx + 1: current_idx + horizon_bars + 1]
            expected_last = parse_utc(residual["bar_open_utc"]) + timedelta(minutes=15 * horizon_bars)
            actual_last = parse_utc(future_path[-1]["bar_open_utc"]) if future_path else None
            path_status = "ok" if len(future_path) == horizon_bars and actual_last == expected_last else "future_path_not_contiguous"
        for direction_family, direction in direction_specs(residual):
            metrics = (
                path_metrics(current, future_path, direction_family, direction)
                if path_status == "ok" and current is not None
                else {"path_status": path_status, "direction_family": direction_family, "direction_sign": direction, "direction_label": sign_label(direction)}
            )
            path_rows.append({
                "queue_id": residual["queue_id"],
                "route_id": ROUTE_ID,
                "symbol": residual["symbol"],
                "session_bucket": residual["session_bucket"],
                "horizon_id": residual["horizon_id"],
                "horizon_bars": horizon_bars,
                "primitive_flag": residual["primitive_flag"],
                "bar_open_utc": residual["bar_open_utc"],
                "direction_family": direction_family,
                "direction_sign": direction,
                "direction_label": sign_label(direction),
                "path_metrics": metrics,
                "source_fields": residual["source_fields"],
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            })

    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in path_rows:
        groups[(row["queue_id"], row["direction_family"])].append(row)

    direction_rows: list[dict[str, Any]] = []
    challenger_rows: list[dict[str, Any]] = []
    question_rows: list[dict[str, Any]] = []
    for (queue_id, direction_family), rows in sorted(groups.items()):
        stats = direction_stats(rows)
        bucket = geometry_bucket(stats)
        first = rows[0]
        friction = friction_by_queue.get(queue_id, {})
        out = {
            "queue_id": queue_id,
            "route_id": ROUTE_ID,
            "symbol": first["symbol"],
            "session_bucket": first["session_bucket"],
            "horizon_id": first["horizon_id"],
            "primitive_flag": first["primitive_flag"],
            "direction_family": direction_family,
            "direction_label": first["direction_label"],
            "friction_bucket": friction.get("friction_bucket"),
            "geometry_stats": stats,
            "geometry_bucket": bucket,
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        }
        direction_rows.append(out)
        challenger_rows.append({
            "spec_id": f"{queue_id}-{direction_family}-GEOMETRY-SPEC",
            "queue_id": queue_id,
            "route_id": ROUTE_ID,
            "symbol": first["symbol"],
            "session_bucket": first["session_bucket"],
            "horizon_id": first["horizon_id"],
            "primitive_flag": first["primitive_flag"],
            "direction_family": direction_family,
            "geometry_bucket": bucket,
            "mechanical_rule_sketch": (
                f"When {first['primitive_flag']} fires on {first['symbol']} {first['session_bucket']}, "
                f"evaluate {direction_family} path geometry over {first['horizon_id']} before any live candidate use."
            ),
            "required_before_challenger_status": [
                "deduplicate overlapping descriptor references",
                "entry price and fill timing definition",
                "stop/target family definition",
                "spread/slippage/commission model",
                "sealed or future deconcentration",
                "Sierra/proxy repair where relevant",
            ],
            "live_effect": False,
            "evidence_boundary": "branch-local challenger spec sketch only; not production code or promotion",
            "safe_flags": SAFE_FLAGS,
        })
        question_rows.append({
            "question_id": f"{queue_id}-{direction_family}-PATH-Q01",
            "queue_id": queue_id,
            "route_id": ROUTE_ID,
            "question": "Can this path geometry survive deduplication, cost/fill ordering, and sealed/future deconcentration?",
            "geometry_bucket": bucket,
            "status": "open_same_resource_or_next_packet",
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        })

    bucket_counts = Counter(row["geometry_bucket"] for row in direction_rows)
    write_jsonl(ROW_LEDGER, path_rows)
    write_jsonl(RESIDUAL_DIRECTION_LEDGER, direction_rows)
    write_jsonl(CHALLENGER_SPEC_LEDGER, challenger_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)

    counts = {
        "flagged_input_rows": len(residual_rows),
        "path_geometry_row_rows": len(path_rows),
        "residual_direction_rows": len(direction_rows),
        "challenger_spec_rows": len(challenger_rows),
        "question_rows": len(question_rows),
    }
    result = {
        "schema": "tick_m15_entry_path_geometry_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "ROUTE_C_ENTRY_PATH_GEOMETRY_DIAGNOSTIC_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "geometry_bucket_counts": dict(bucket_counts),
        "direction_families": ["delta_follow", "delta_inverse", "price_follow", "price_inverse"],
        "thresholds": THRESHOLDS,
        "next_same_resource_work": [
            "deduplicate geometry specs by unique bar before any system comparison",
            "define concrete stop/target families and fill-order rules",
            "compare geometry specs against denominator rows rather than selected residual rows only",
        ],
        "not_completion": "This converts entry-geometry blocker into path diagnostics and more work; it does not complete the 60-hour objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = [
        "# Tick M15 Entry Path Geometry",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: path geometry diagnostics only. No fill simulation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        summary.append(f"- `{key}`: `{value}`")
    summary.extend(["", "## Geometry Buckets", ""])
    for bucket, count in sorted(bucket_counts.items()):
        summary.append(f"- `{bucket}`: `{count}`")
    summary.extend([
        "",
        "## Boundary",
        "",
        "- Entry is current M15 close proxy only; no fill is assumed.",
        "- Direction families are mechanical proxy mutations, not trade recommendations.",
        "- Challenger specs are branch-local sketches requiring deduplication, cost/fill rules, and sealed/future evidence.",
        "",
    ])
    SUMMARY_PATH.write_text("\n".join(summary), encoding="utf-8")

    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, dict(bucket_counts))
    print(json.dumps({"ok": True, "counts": counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
