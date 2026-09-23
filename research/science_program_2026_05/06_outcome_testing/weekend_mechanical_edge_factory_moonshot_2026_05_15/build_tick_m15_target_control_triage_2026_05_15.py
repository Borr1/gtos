#!/usr/bin/env python3
"""Triage tick M15 target-control rows for placebo-ready follow-up.

All control rows are preserved. Rows with flagged_n >= 20 are routed to the
placebo-ready queue because the project does not claim significance at n < 20.
This is still development triage only, not validation or promotion.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
STAMP = "2026-05-15"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

CONTROL_LEDGER = ROUTE_DIR / f"TICK_M15_TARGET_MOVEMENT_FLAG_CONTROL_LEDGER_{STAMP}.jsonl"
RESULT_PATH = ROUTE_DIR / f"TICK_M15_TARGET_CONTROL_TRIAGE_RESULT_{STAMP}.json"
TRIAGE_LEDGER = ROUTE_DIR / f"TICK_M15_TARGET_CONTROL_TRIAGE_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"TICK_M15_TARGET_CONTROL_TRIAGE_BUCKET_LEDGER_{STAMP}.jsonl"
PLACEBO_READY_QUEUE = ROUTE_DIR / f"TICK_M15_PLACEBO_READY_QUEUE_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"TICK_M15_TARGET_CONTROL_TRIAGE_SUMMARY_{STAMP}.md"

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


def safe_float(value: Any) -> float | None:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if value != value or value in (float("inf"), float("-inf")):
        return None
    return value


def triage_bucket(row: dict[str, Any]) -> str:
    flagged_n = int(row.get("flagged_n") or 0)
    control_n = int(row.get("control_n") or 0)
    delta_abs = safe_float(row.get("delta_mean_abs_future_change"))
    delta_align = None
    flagged_align = safe_float(row.get("flagged_delta_alignment_rate"))
    control_align = safe_float(row.get("control_delta_alignment_rate"))
    if flagged_align is not None and control_align is not None:
        delta_align = flagged_align - control_align
    if flagged_n < 20:
        return "SMALL_N_LT20_NO_SIGNIFICANCE_CLAIM"
    if control_n < 20:
        return "CONTROL_N_LT20_NO_SIGNIFICANCE_CLAIM"
    if delta_abs is not None and delta_abs > 0 and (delta_align is None or delta_align >= 0):
        return "PLACEBO_READY_N_GE20_POSITIVE_ABS_AND_NONNEGATIVE_ALIGNMENT_DELTA"
    if delta_abs is not None and delta_abs > 0:
        return "PLACEBO_READY_N_GE20_POSITIVE_ABS_NEGATIVE_ALIGNMENT_DELTA"
    return "PLACEBO_READY_N_GE20_FLAT_OR_NEGATIVE_ABS_DELTA"


def main() -> int:
    generated_utc = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    control_rows = read_jsonl(CONTROL_LEDGER)

    triage_rows: list[dict[str, Any]] = []
    placebo_ready_rows: list[dict[str, Any]] = []
    bucket_counts: dict[str, int] = {}
    for row in control_rows:
        bucket = triage_bucket(row)
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
        flagged_align = safe_float(row.get("flagged_delta_alignment_rate"))
        control_align = safe_float(row.get("control_delta_alignment_rate"))
        delta_alignment_rate = None
        if flagged_align is not None and control_align is not None:
            delta_alignment_rate = flagged_align - control_align
        out = {
            "route_id": ROUTE_ID,
            "symbol": row["symbol"],
            "session_bucket": row["session_bucket"],
            "primitive_flag": row["primitive_flag"],
            "horizon_id": row["horizon_id"],
            "flagged_n": row["flagged_n"],
            "control_n": row["control_n"],
            "triage_bucket": bucket,
            "delta_mean_abs_future_change": row.get("delta_mean_abs_future_change"),
            "delta_alignment_rate": safe_float(delta_alignment_rate),
            "flagged_mean_abs_future_change": row.get("flagged_mean_abs_future_change"),
            "control_mean_abs_future_change": row.get("control_mean_abs_future_change"),
            "flagged_delta_alignment_rate": row.get("flagged_delta_alignment_rate"),
            "control_delta_alignment_rate": row.get("control_delta_alignment_rate"),
            "next_gate": "neighbor_placebo_and_shuffle_required_before_candidate_ranking" if row["flagged_n"] >= 20 else "collect_more_rows_or_ignore_for_claims",
            "evidence_boundary": "triage only; no validation, trade outcome, R/PnL, live-readiness, or promotion",
            "safe_flags": SAFE_FLAGS,
        }
        triage_rows.append(out)
        if int(row.get("flagged_n") or 0) >= 20:
            placebo_ready_rows.append(out)

    bucket_rows = [
        {
            "route_id": ROUTE_ID,
            "triage_bucket": bucket,
            "row_count": count,
            "evidence_boundary": "bucket count only; no validation or promotion",
            "safe_flags": SAFE_FLAGS,
        }
        for bucket, count in sorted(bucket_counts.items())
    ]

    write_jsonl(TRIAGE_LEDGER, triage_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(PLACEBO_READY_QUEUE, placebo_ready_rows)

    result = {
        "schema": "tick_m15_target_control_triage_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "DEVELOPMENT_TARGET_CONTROL_TRIAGE_ONLY",
        "claim_boundary": "Triage and placebo queue only. No validation, trade outcome, R/PnL, expectancy, live-readiness, or promotion claim.",
        "counts": {
            "input_control_rows": len(control_rows),
            "triage_rows": len(triage_rows),
            "bucket_rows": len(bucket_rows),
            "placebo_ready_rows": len(placebo_ready_rows),
        },
        "bucket_counts": bucket_counts,
        "open_blockers": [
            "neighbor/placebo/shuffle controls not yet applied",
            "development sample only",
            "target movement is not trade outcome or fillable R",
            "no candidate ranking or promotion from this packet",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = [
        "# Tick M15 Target Control Triage",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: development triage only. No validation, R/PnL, live-readiness, or promotion verdict.",
        "",
        "## Counts",
        "",
        f"- Input control rows: `{len(control_rows)}`",
        f"- Triage rows: `{len(triage_rows)}`",
        f"- Bucket rows: `{len(bucket_rows)}`",
        f"- Placebo-ready rows (all flagged_n >= 20): `{len(placebo_ready_rows)}`",
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
        "- `flagged_n >= 20` is only the minimum descriptive threshold for follow-up.",
        "- Every input control row is preserved in the triage ledger.",
        "- No row is promoted or ranked.",
        "",
    ])
    SUMMARY_PATH.write_text("\n".join(summary), encoding="utf-8")

    print(json.dumps({"ok": True, "triage_rows": len(triage_rows), "placebo_ready_rows": len(placebo_ready_rows), "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
