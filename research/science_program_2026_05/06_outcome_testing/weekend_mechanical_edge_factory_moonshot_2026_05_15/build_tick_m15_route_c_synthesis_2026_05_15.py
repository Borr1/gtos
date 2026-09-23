#!/usr/bin/env python3
"""Synthesize Route C tick M15 residual descriptor queue and blockers."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
STAMP = "2026-05-15"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

SOURCE_RESULT = ROUTE_DIR / f"TICK_SIERRA_SOURCE_CONTRACT_RESULT_{STAMP}.json"
PRIMITIVE_RESULT = ROUTE_DIR / f"TICK_M15_PRIMITIVE_FACTORY_RESULT_{STAMP}.json"
TARGET_RESULT = ROUTE_DIR / f"TICK_M15_TARGET_MOVEMENT_PACKET_RESULT_{STAMP}.json"
TRIAGE_RESULT = ROUTE_DIR / f"TICK_M15_TARGET_CONTROL_TRIAGE_RESULT_{STAMP}.json"
PLACEBO_RESULT = ROUTE_DIR / f"TICK_M15_NEIGHBOR_PLACEBO_CONTROL_RESULT_{STAMP}.json"
PLACEBO_LEDGER = ROUTE_DIR / f"TICK_M15_NEIGHBOR_PLACEBO_CONTROL_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"TICK_M15_ROUTE_C_SYNTHESIS_RESULT_{STAMP}.json"
RESIDUAL_QUEUE = ROUTE_DIR / f"TICK_M15_ROUTE_C_RESIDUAL_DESCRIPTOR_QUEUE_{STAMP}.jsonl"
BLOCKER_LEDGER = ROUTE_DIR / f"TICK_M15_ROUTE_C_RESIDUAL_BLOCKER_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"TICK_M15_ROUTE_C_SYNTHESIS_SUMMARY_{STAMP}.md"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

RESIDUAL_BUCKET = "DESCRIPTIVE_RESIDUAL_AFTER_NEIGHBOR_AND_ROTATED_PLACEBO"

BLOCKERS = [
    "full_permutation_or_shuffle_control_required",
    "sealed_or_future_holdout_required",
    "entry_geometry_and_fillability_not_defined",
    "spread_slippage_commission_not_applied",
    "mt5_aggressor_proxy_only_on_current_broker",
    "sample_concentration_audit_required",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def main() -> int:
    generated_utc = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    source = read_json(SOURCE_RESULT)
    primitive = read_json(PRIMITIVE_RESULT)
    target = read_json(TARGET_RESULT)
    triage = read_json(TRIAGE_RESULT)
    placebo = read_json(PLACEBO_RESULT)
    placebo_rows = read_jsonl(PLACEBO_LEDGER)

    residual_rows: list[dict[str, Any]] = []
    blocker_rows: list[dict[str, Any]] = []
    for idx, row in enumerate(placebo_rows, 1):
        if row["placebo_bucket"] != RESIDUAL_BUCKET:
            continue
        queue_id = f"ROUTE-C-RESIDUAL-{idx:04d}"
        out = {
            "queue_id": queue_id,
            "route_id": ROUTE_ID,
            "symbol": row["symbol"],
            "session_bucket": row["session_bucket"],
            "primitive_flag": row["primitive_flag"],
            "horizon_id": row["horizon_id"],
            "placebo_bucket": row["placebo_bucket"],
            "flagged_n": row["flagged_n"],
            "neighbor_n": row["neighbor_n"],
            "rotated_placebo_n": row["rotated_placebo_n"],
            "flagged_mean_abs_future_change": row.get("flagged_mean_abs_future_change"),
            "neighbor_mean_abs_future_change": row.get("neighbor_mean_abs_future_change"),
            "rotated_placebo_mean_abs_future_change": row.get("rotated_placebo_mean_abs_future_change"),
            "flagged_minus_neighbor_abs_change": row.get("flagged_minus_neighbor_abs_change"),
            "flagged_minus_rotated_placebo_abs_change": row.get("flagged_minus_rotated_placebo_abs_change"),
            "flagged_delta_alignment_rate": row.get("flagged_delta_alignment_rate"),
            "neighbor_delta_alignment_rate": row.get("neighbor_delta_alignment_rate"),
            "rotated_placebo_delta_alignment_rate": row.get("rotated_placebo_delta_alignment_rate"),
            "next_gate": "full_permutation_concentration_and_sealed_forward_packet_required",
            "evidence_boundary": "residual descriptor queue only; not validation, trade outcome, R/PnL, live-readiness, or promotion",
            "safe_flags": SAFE_FLAGS,
        }
        residual_rows.append(out)
        for blocker in BLOCKERS:
            blocker_rows.append({
                "queue_id": queue_id,
                "route_id": ROUTE_ID,
                "symbol": row["symbol"],
                "session_bucket": row["session_bucket"],
                "primitive_flag": row["primitive_flag"],
                "horizon_id": row["horizon_id"],
                "blocker": blocker,
                "status": "open",
                "safe_flags": SAFE_FLAGS,
            })

    write_jsonl(RESIDUAL_QUEUE, residual_rows)
    write_jsonl(BLOCKER_LEDGER, blocker_rows)

    result = {
        "schema": "tick_m15_route_c_synthesis_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "ROUTE_C_DEVELOPMENT_SYNTHESIS_ONLY",
        "claim_boundary": "Route C synthesis and residual descriptor queue only. No validation, trade outcome, R/PnL, expectancy, live-readiness, or promotion claim.",
        "counts": {
            "tick_parquet_files": source["counts"]["tick_parquet_files"],
            "tick_rows_total": source["counts"]["tick_rows_total"],
            "primitive_event_rows": primitive["counts"]["tick_event_rows"],
            "target_event_rows": target["counts"]["target_event_rows"],
            "triage_rows": triage["counts"]["triage_rows"],
            "placebo_control_rows": placebo["counts"]["placebo_control_rows"],
            "residual_descriptor_rows": len(residual_rows),
            "residual_blocker_rows": len(blocker_rows),
        },
        "placebo_bucket_counts": placebo["bucket_counts"],
        "next_required_gate": "full_permutation_concentration_and_sealed_forward_packet_required",
        "open_blockers": BLOCKERS,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = [
        "# Tick M15 Route C Synthesis",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: Route C development synthesis only. No validation, R/PnL, live-readiness, or promotion verdict.",
        "",
        "## Counts",
        "",
        f"- Tick parquet files: `{source['counts']['tick_parquet_files']}`",
        f"- Tick rows from parquet metadata: `{source['counts']['tick_rows_total']}`",
        f"- M15 primitive event rows: `{primitive['counts']['tick_event_rows']}`",
        f"- Target event-horizon rows: `{target['counts']['target_event_rows']}`",
        f"- Placebo control rows: `{placebo['counts']['placebo_control_rows']}`",
        f"- Residual descriptor rows: `{len(residual_rows)}`",
        f"- Residual blocker rows: `{len(blocker_rows)}`",
        "",
        "## Placebo Buckets",
        "",
    ]
    for bucket, count in sorted(placebo["bucket_counts"].items()):
        summary.append(f"- `{bucket}`: `{count}`")
    summary.extend([
        "",
        "## Boundary",
        "",
        "- Residual rows are follow-up descriptors, not ranked candidates.",
        "- Every residual row has open blockers for permutation, concentration, sealed/future, entry geometry, cost, and broker-proxy limitations.",
        "",
    ])
    SUMMARY_PATH.write_text("\n".join(summary), encoding="utf-8")

    print(json.dumps({"ok": True, "residual_rows": len(residual_rows), "blocker_rows": len(blocker_rows), "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
