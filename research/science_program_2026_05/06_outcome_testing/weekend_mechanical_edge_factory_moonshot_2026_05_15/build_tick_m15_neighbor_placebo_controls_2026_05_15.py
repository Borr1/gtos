#!/usr/bin/env python3
"""Apply neighbor and deterministic rotated-placebo controls to tick rows.

Consumes every row in TICK_M15_PLACEBO_READY_QUEUE. Controls are development
diagnostics only; this does not validate edge, trade outcome, R/PnL,
live-readiness, or promotion.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
STAMP = "2026-05-15"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

TARGET_EVENT_LEDGER = ROUTE_DIR / f"TICK_M15_TARGET_MOVEMENT_EVENT_LEDGER_{STAMP}.jsonl"
PLACEBO_READY_QUEUE = ROUTE_DIR / f"TICK_M15_PLACEBO_READY_QUEUE_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"TICK_M15_NEIGHBOR_PLACEBO_CONTROL_RESULT_{STAMP}.json"
CONTROL_LEDGER = ROUTE_DIR / f"TICK_M15_NEIGHBOR_PLACEBO_CONTROL_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"TICK_M15_NEIGHBOR_PLACEBO_BUCKET_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"TICK_M15_NEIGHBOR_PLACEBO_CONTROL_SUMMARY_{STAMP}.md"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
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


def parse_utc(ts: str):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def fmt_utc(ts) -> str:
    return ts.isoformat().replace("+00:00", "Z")


def safe_float(value: Any) -> float | None:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if value != value or value in (float("inf"), float("-inf")):
        return None
    return value


def mean(values: list[float]) -> float | None:
    return safe_float(sum(values) / len(values)) if values else None


def rate(values: list[bool]) -> float | None:
    return safe_float(sum(1 for v in values if v) / len(values)) if values else None


def stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    changes = [row["future_change"] for row in rows if row.get("future_change") is not None]
    abs_changes = [row["future_abs_change"] for row in rows if row.get("future_abs_change") is not None]
    align = [
        row["delta_aligned_with_future"]
        for row in rows
        if row.get("delta_sign", 0) != 0 and row.get("future_sign", 0) != 0
    ]
    return {
        "n": len(rows),
        "mean_future_change": mean(changes),
        "mean_abs_future_change": mean(abs_changes),
        "delta_alignment_n": len(align),
        "delta_alignment_rate": rate(align),
    }


def delta(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return safe_float(a - b)


def bucket_for(flagged: dict[str, Any], neighbor: dict[str, Any], rotated: dict[str, Any]) -> str:
    if neighbor["n"] < 20 or rotated["n"] < 20:
        return "PLACEBO_UNDERPOWERED"
    flagged_abs = flagged["mean_abs_future_change"]
    neighbor_abs = neighbor["mean_abs_future_change"]
    rotated_abs = rotated["mean_abs_future_change"]
    if flagged_abs is None or neighbor_abs is None or rotated_abs is None:
        return "PLACEBO_NOT_NUMERIC"
    beats_neighbor = flagged_abs > neighbor_abs
    beats_rotated = flagged_abs > rotated_abs
    flagged_align = flagged["delta_alignment_rate"]
    neighbor_align = neighbor["delta_alignment_rate"]
    rotated_align = rotated["delta_alignment_rate"]
    align_not_worse = (
        flagged_align is None
        or neighbor_align is None
        or rotated_align is None
        or (flagged_align >= neighbor_align and flagged_align >= rotated_align)
    )
    if beats_neighbor and beats_rotated and align_not_worse:
        return "DESCRIPTIVE_RESIDUAL_AFTER_NEIGHBOR_AND_ROTATED_PLACEBO"
    if not beats_neighbor and not beats_rotated:
        return "EXPLAINED_OR_WEAKENED_BY_PLACEBO"
    return "MIXED_AFTER_PLACEBO"


def main() -> int:
    generated_utc = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    target_rows = read_jsonl(TARGET_EVENT_LEDGER)
    queue_rows = read_jsonl(PLACEBO_READY_QUEUE)

    target_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    denominator_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in target_rows:
        target_by_key[(row["symbol"], row["horizon_id"], row["bar_open_utc"])] = row
        denom_key = (row["symbol"], row["session_bucket"], row["horizon_id"])
        denominator_by_key.setdefault(denom_key, []).append(row)
    for rows in denominator_by_key.values():
        rows.sort(key=lambda r: r["bar_open_utc"])

    out_rows: list[dict[str, Any]] = []
    for queue in queue_rows:
        symbol = queue["symbol"]
        session = queue["session_bucket"]
        horizon = queue["horizon_id"]
        primitive_flag = queue["primitive_flag"]
        denom_rows = denominator_by_key.get((symbol, session, horizon), [])
        flagged_rows = [
            row for row in denom_rows
            if primitive_flag in row.get("primitive_flags", [])
        ]

        neighbor_map: dict[tuple[str, str, str], dict[str, Any]] = {}
        for row in flagged_rows:
            current_dt = parse_utc(row["bar_open_utc"])
            for offset in (-15, 15):
                neighbor_dt = fmt_utc(current_dt + timedelta(minutes=offset))
                neighbor = target_by_key.get((symbol, horizon, neighbor_dt))
                if neighbor and neighbor["session_bucket"] == session:
                    neighbor_map[(neighbor["symbol"], neighbor["horizon_id"], neighbor["bar_open_utc"])] = neighbor
        neighbor_rows = list(neighbor_map.values())

        index_by_bar = {row["bar_open_utc"]: idx for idx, row in enumerate(denom_rows)}
        rotated_map: dict[tuple[str, str, str], dict[str, Any]] = {}
        if denom_rows:
            rotation = max(1, len(denom_rows) // 3)
            for row in flagged_rows:
                idx = index_by_bar[row["bar_open_utc"]]
                rotated = denom_rows[(idx + rotation) % len(denom_rows)]
                rotated_map[(rotated["symbol"], rotated["horizon_id"], rotated["bar_open_utc"])] = rotated
        rotated_rows = list(rotated_map.values())

        flagged_stats = stats(flagged_rows)
        neighbor_stats = stats(neighbor_rows)
        rotated_stats = stats(rotated_rows)
        bucket = bucket_for(flagged_stats, neighbor_stats, rotated_stats)
        out_rows.append({
            "route_id": ROUTE_ID,
            "symbol": symbol,
            "session_bucket": session,
            "primitive_flag": primitive_flag,
            "horizon_id": horizon,
            "flagged_n": flagged_stats["n"],
            "neighbor_n": neighbor_stats["n"],
            "rotated_placebo_n": rotated_stats["n"],
            "flagged_mean_abs_future_change": flagged_stats["mean_abs_future_change"],
            "neighbor_mean_abs_future_change": neighbor_stats["mean_abs_future_change"],
            "rotated_placebo_mean_abs_future_change": rotated_stats["mean_abs_future_change"],
            "flagged_minus_neighbor_abs_change": delta(flagged_stats["mean_abs_future_change"], neighbor_stats["mean_abs_future_change"]),
            "flagged_minus_rotated_placebo_abs_change": delta(flagged_stats["mean_abs_future_change"], rotated_stats["mean_abs_future_change"]),
            "flagged_delta_alignment_rate": flagged_stats["delta_alignment_rate"],
            "neighbor_delta_alignment_rate": neighbor_stats["delta_alignment_rate"],
            "rotated_placebo_delta_alignment_rate": rotated_stats["delta_alignment_rate"],
            "flagged_minus_neighbor_alignment_rate": delta(flagged_stats["delta_alignment_rate"], neighbor_stats["delta_alignment_rate"]),
            "flagged_minus_rotated_alignment_rate": delta(flagged_stats["delta_alignment_rate"], rotated_stats["delta_alignment_rate"]),
            "placebo_bucket": bucket,
            "control_scope": "adjacent_same_session_neighbors_and_deterministic_same_denominator_rotation",
            "evidence_boundary": "development placebo diagnostic only; no validation, trade outcome, R/PnL, live-readiness, or promotion",
            "safe_flags": SAFE_FLAGS,
        })

    bucket_counts: dict[str, int] = {}
    for row in out_rows:
        bucket_counts[row["placebo_bucket"]] = bucket_counts.get(row["placebo_bucket"], 0) + 1
    bucket_rows = [
        {
            "route_id": ROUTE_ID,
            "placebo_bucket": bucket,
            "row_count": count,
            "evidence_boundary": "bucket count only; no validation or promotion",
            "safe_flags": SAFE_FLAGS,
        }
        for bucket, count in sorted(bucket_counts.items())
    ]

    write_jsonl(CONTROL_LEDGER, out_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)

    result = {
        "schema": "tick_m15_neighbor_placebo_control_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "DEVELOPMENT_NEIGHBOR_AND_ROTATED_PLACEBO_CONTROL_ONLY",
        "claim_boundary": "Neighbor/rotated placebo diagnostics only. No validation, trade outcome, R/PnL, expectancy, live-readiness, or promotion claim.",
        "counts": {
            "input_placebo_ready_rows": len(queue_rows),
            "placebo_control_rows": len(out_rows),
            "bucket_rows": len(bucket_rows),
        },
        "bucket_counts": bucket_counts,
        "open_blockers": [
            "development sample only",
            "no sealed/future confirmation",
            "rotated placebo is deterministic diagnostic, not a full permutation test",
            "target movement is not trade outcome or fillable R",
            "no candidate ranking or promotion from this packet",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = [
        "# Tick M15 Neighbor/Placebo Controls",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: development neighbor/rotated placebo diagnostics only. No validation, R/PnL, live-readiness, or promotion verdict.",
        "",
        "## Counts",
        "",
        f"- Input placebo-ready rows: `{len(queue_rows)}`",
        f"- Placebo control rows: `{len(out_rows)}`",
        f"- Bucket rows: `{len(bucket_rows)}`",
        "",
        "## Buckets",
        "",
    ]
    for bucket, count in sorted(bucket_counts.items()):
        summary.append(f"- `{bucket}`: `{count}`")
    summary.extend([
        "",
        "## Boundary",
        "",
        "- Adjacent controls are same-session M15 neighbors.",
        "- Rotated controls use deterministic within-denominator rotation.",
        "- This is not a full permutation test and not sealed validation.",
        "",
    ])
    SUMMARY_PATH.write_text("\n".join(summary), encoding="utf-8")

    print(json.dumps({"ok": True, "placebo_control_rows": len(out_rows), "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
