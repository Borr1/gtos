#!/usr/bin/env python3
"""Build execution/friction diagnostics for Route C residual descriptors.

This runs the cost-filter mutation opened by the transfer matrix using only
current tick primitive fields. It does not model fills or R/PnL; it measures
whether flagged movement is large or small relative to observed spread and
whether flagged rows concentrate in expensive/thin/data-quality states.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

ROW_RECONSTRUCTION_LEDGER = ROUTE_DIR / f"TICK_M15_RESIDUAL_ROW_RECONSTRUCTION_LEDGER_{STAMP}.jsonl"
RESIDUAL_TRANSFER_LEDGER = ROUTE_DIR / f"TICK_M15_RESIDUAL_TRANSFER_DIAGNOSIS_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"TICK_M15_EXECUTION_FRICTION_DIAGNOSTIC_RESULT_{STAMP}.json"
ROW_LEDGER = ROUTE_DIR / f"TICK_M15_EXECUTION_FRICTION_ROW_LEDGER_{STAMP}.jsonl"
RESIDUAL_LEDGER = ROUTE_DIR / f"TICK_M15_EXECUTION_FRICTION_RESIDUAL_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"TICK_M15_EXECUTION_FRICTION_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"TICK_M15_EXECUTION_FRICTION_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"TICK_M15_EXECUTION_FRICTION_DIAGNOSTIC_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Route C execution/friction diagnostics only; not fill simulation, validation, "
    "trade outcome, R/PnL, expectancy, live-readiness, or promotion"
)


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
    return safe_float(sum(values) / len(values)) if values else None


def median(values: list[float]) -> float | None:
    numeric = sorted(value for value in values if safe_float(value) is not None)
    if not numeric:
        return None
    mid = len(numeric) // 2
    if len(numeric) % 2:
        return safe_float(numeric[mid])
    return safe_float((numeric[mid - 1] + numeric[mid]) / 2)


def quantile(values: list[float], q: float) -> float | None:
    numeric = sorted(value for value in values if safe_float(value) is not None)
    if not numeric:
        return None
    if len(numeric) == 1:
        return safe_float(numeric[0])
    pos = (len(numeric) - 1) * q
    lower = int(pos)
    upper = min(lower + 1, len(numeric) - 1)
    weight = pos - lower
    return safe_float(numeric[lower] * (1 - weight) + numeric[upper] * weight)


def rate(values: list[bool]) -> float | None:
    return safe_float(sum(1 for value in values if value) / len(values)) if values else None


def ratio(numerator: Any, denominator: Any) -> float | None:
    num = safe_float(numerator)
    den = safe_float(denominator)
    if num is None or den is None or den == 0:
        return None
    return safe_float(num / den)


def row_metric(row: dict[str, Any]) -> dict[str, Any]:
    source = row.get("source_fields") or {}
    spread_median = safe_float(source.get("spread_median"))
    spread_max = safe_float(source.get("spread_max"))
    spread_close = safe_float(source.get("spread_close"))
    future_abs = safe_float(row.get("future_abs_change"))
    return {
        "future_abs_to_spread_median": ratio(future_abs, spread_median),
        "future_abs_to_spread_max": ratio(future_abs, spread_max),
        "future_abs_to_spread_close": ratio(future_abs, spread_close),
        "future_abs_le_one_spread_max": (
            future_abs is not None and spread_max is not None and future_abs <= spread_max
        ) if future_abs is not None and spread_max is not None else None,
        "future_abs_le_two_spread_max": (
            future_abs is not None and spread_max is not None and future_abs <= 2 * spread_max
        ) if future_abs is not None and spread_max is not None else None,
        "spread_median": spread_median,
        "spread_max": spread_max,
        "spread_close": spread_close,
        "tick_velocity_per_sec": safe_float(source.get("tick_velocity_per_sec")),
        "n_ticks": safe_float(source.get("n_ticks")),
        "duplicate_ts_msc_rows": safe_float(source.get("duplicate_ts_msc_rows")),
        "abs_cumulative_delta": safe_float(source.get("abs_cumulative_delta")),
        "price_range": safe_float(source.get("price_range")),
    }


def stat_pack(values: list[float]) -> dict[str, Any]:
    numeric = [value for value in values if safe_float(value) is not None]
    return {
        "n": len(numeric),
        "mean": mean(numeric),
        "median": median(numeric),
        "p25": quantile(numeric, 0.25),
        "p75": quantile(numeric, 0.75),
        "p90": quantile(numeric, 0.90),
    }


def population_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = [row_metric(row) for row in rows]
    return {
        "n": len(rows),
        "future_abs_to_spread_median": stat_pack([
            value["future_abs_to_spread_median"] for value in metrics
            if value["future_abs_to_spread_median"] is not None
        ]),
        "future_abs_to_spread_max": stat_pack([
            value["future_abs_to_spread_max"] for value in metrics
            if value["future_abs_to_spread_max"] is not None
        ]),
        "spread_median": stat_pack([
            value["spread_median"] for value in metrics
            if value["spread_median"] is not None
        ]),
        "spread_max": stat_pack([
            value["spread_max"] for value in metrics
            if value["spread_max"] is not None
        ]),
        "tick_velocity_per_sec": stat_pack([
            value["tick_velocity_per_sec"] for value in metrics
            if value["tick_velocity_per_sec"] is not None
        ]),
        "share_future_abs_le_one_spread_max": rate([
            value["future_abs_le_one_spread_max"] for value in metrics
            if value["future_abs_le_one_spread_max"] is not None
        ]),
        "share_future_abs_le_two_spread_max": rate([
            value["future_abs_le_two_spread_max"] for value in metrics
            if value["future_abs_le_two_spread_max"] is not None
        ]),
        "source_join_missing_share": rate([
            not row.get("source_join_found") for row in rows
        ]),
        "duplicate_timestamp_rows_share": rate([
            (value["duplicate_ts_msc_rows"] or 0) > 0 for value in metrics
        ]),
    }


def bucket_for(flagged: dict[str, Any], denominator: dict[str, Any]) -> str:
    flagged_median_move_spread = flagged["future_abs_to_spread_max"]["median"]
    denom_median_move_spread = denominator["future_abs_to_spread_max"]["median"]
    flagged_two_spread_share = flagged["share_future_abs_le_two_spread_max"]
    flagged_spread = flagged["spread_median"]["median"]
    denom_spread = denominator["spread_median"]["median"]

    if flagged["source_join_missing_share"]:
        return "FRICTION_DATA_SOURCE_JOIN_WARNING"
    if flagged_median_move_spread is None:
        return "FRICTION_NOT_NUMERIC"
    if flagged_two_spread_share is not None and flagged_two_spread_share >= 0.35:
        return "FRICTION_SPREAD_COMPETES_WITH_MOVEMENT"
    if denom_spread is not None and flagged_spread is not None and flagged_spread > denom_spread * 1.25:
        return "FRICTION_FLAGGED_ROWS_MORE_EXPENSIVE_THAN_DENOMINATOR"
    if denom_median_move_spread is not None and flagged_median_move_spread >= denom_median_move_spread:
        return "FRICTION_MOVEMENT_DOMINATES_SPREAD_DIAGNOSTIC"
    return "FRICTION_WEAKER_THAN_DENOMINATOR"


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "tick_m15_execution_friction_diagnostic_builder", "created"),
        (RESULT_PATH, "tick_m15_execution_friction_diagnostic_result", "created"),
        (ROW_LEDGER, "tick_m15_execution_friction_row_ledger", "created"),
        (RESIDUAL_LEDGER, "tick_m15_execution_friction_residual_ledger", "created"),
        (BUCKET_LEDGER, "tick_m15_execution_friction_bucket_ledger", "created"),
        (QUESTION_LEDGER, "tick_m15_execution_friction_question_ledger", "created"),
        (SUMMARY_PATH, "tick_m15_execution_friction_diagnostic_summary", "created"),
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
        "event_type": "tick_m15_execution_friction_diagnostic",
        "status": "done",
        "route": "tick_sierra_orderflow_route_c",
        "details": (
            "Executed the cost-filter mutation for Route C residuals using source-joined spread, tick velocity, "
            "and movement-to-spread diagnostics. This is friction intelligence only, not fill/R/PnL modeling."
        ),
        "counts": counts,
        "bucket_counts": bucket_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(ROW_LEDGER),
            relative(RESIDUAL_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def main() -> int:
    generated_utc = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    reconstruction_rows = read_jsonl(ROW_RECONSTRUCTION_LEDGER)
    transfer_rows = {row["queue_id"]: row for row in read_jsonl(RESIDUAL_TRANSFER_LEDGER)}

    residual_groups: dict[str, list[dict[str, Any]]] = {}
    for row in reconstruction_rows:
        residual_groups.setdefault(row["queue_id"], []).append(row)

    friction_rows: list[dict[str, Any]] = []
    residual_rows: list[dict[str, Any]] = []
    question_rows: list[dict[str, Any]] = []

    for queue_id, rows in sorted(residual_groups.items()):
        flagged = [row for row in rows if row["is_flagged"]]
        denominator = rows
        flagged_stats = population_stats(flagged)
        denominator_stats = population_stats(denominator)
        friction_bucket = bucket_for(flagged_stats, denominator_stats)
        transfer = transfer_rows.get(queue_id, {})

        residual_rows.append({
            "queue_id": queue_id,
            "route_id": ROUTE_ID,
            "symbol": transfer.get("symbol") or rows[0]["symbol"],
            "session_bucket": transfer.get("session_bucket") or rows[0]["session_bucket"],
            "horizon_id": transfer.get("horizon_id") or rows[0]["horizon_id"],
            "primitive_flag": transfer.get("primitive_flag") or rows[0]["primitive_flag"],
            "transfer_class": transfer.get("residual_transfer_class"),
            "flagged_stats": flagged_stats,
            "denominator_stats": denominator_stats,
            "friction_bucket": friction_bucket,
            "diagnostic_interpretation": "movement-to-spread and source-quality diagnostics only; no fill model or R/PnL",
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        })

        if friction_bucket in {
            "FRICTION_SPREAD_COMPETES_WITH_MOVEMENT",
            "FRICTION_FLAGGED_ROWS_MORE_EXPENSIVE_THAN_DENOMINATOR",
        }:
            question = "Can this descriptor become a spread/liquidity avoid filter instead of an entry signal?"
        elif friction_bucket == "FRICTION_MOVEMENT_DOMINATES_SPREAD_DIAGNOSTIC":
            question = "What executable entry geometry would capture movement without assuming close-to-close fills?"
        else:
            question = "Does a different target family or source proxy explain the weak friction diagnostic?"
        question_rows.append({
            "question_id": f"{queue_id}-FRICTION-Q01",
            "queue_id": queue_id,
            "route_id": ROUTE_ID,
            "question": question,
            "friction_bucket": friction_bucket,
            "status": "open_same_resource_or_entry_geometry_packet",
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        })

        for row in flagged:
            metrics = row_metric(row)
            friction_rows.append({
                "queue_id": queue_id,
                "route_id": ROUTE_ID,
                "symbol": row["symbol"],
                "session_bucket": row["session_bucket"],
                "horizon_id": row["horizon_id"],
                "primitive_flag": row["primitive_flag"],
                "bar_open_utc": row["bar_open_utc"],
                "future_bar_open_utc": row["future_bar_open_utc"],
                "future_abs_change": row["future_abs_change"],
                "metrics": metrics,
                "source_fields": row["source_fields"],
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            })

    bucket_counts = Counter(row["friction_bucket"] for row in residual_rows)
    bucket_rows = [
        {
            "route_id": ROUTE_ID,
            "friction_bucket": bucket,
            "row_count": count,
            "evidence_boundary": "bucket count only; no validation or promotion",
            "safe_flags": SAFE_FLAGS,
        }
        for bucket, count in sorted(bucket_counts.items())
    ]

    write_jsonl(ROW_LEDGER, friction_rows)
    write_jsonl(RESIDUAL_LEDGER, residual_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)

    counts = {
        "residual_rows": len(residual_rows),
        "flagged_friction_row_rows": len(friction_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
    }
    result = {
        "schema": "tick_m15_execution_friction_diagnostic_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "ROUTE_C_EXECUTION_FRICTION_DIAGNOSTIC_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "bucket_counts": dict(bucket_counts),
        "next_same_resource_work": [
            "entry_geometry packet for residuals where movement dominates spread",
            "avoid/liquidity filter mutation where spread competes with movement",
            "Sierra proxy repair for descriptors whose friction state depends on MT5 tick proxy",
        ],
        "not_completion": "This executes one mutation family and opens more same-resource work; it does not complete the 60-hour objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = [
        "# Tick M15 Execution/Friction Diagnostics",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: spread/tick-velocity diagnostics only. No fill simulation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        summary.append(f"- `{key}`: `{value}`")
    summary.extend(["", "## Buckets", ""])
    for bucket, count in sorted(bucket_counts.items()):
        summary.append(f"- `{bucket}`: `{count}`")
    summary.extend([
        "",
        "## Boundary",
        "",
        "- Movement-to-spread ratios are raw diagnostics, not trade returns.",
        "- Entry geometry and path/fill ordering remain required before any strategy claim.",
        "",
    ])
    SUMMARY_PATH.write_text("\n".join(summary), encoding="utf-8")

    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, dict(bucket_counts))
    print(json.dumps({"ok": True, "counts": counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
