#!/usr/bin/env python3
"""Build cross-horizon and cross-session transfer diagnostics for Route C.

This expands beyond the 18 selected residual rows by reopening all 420 neutral
target movement flag-control rows. The goal is to decide whether residual
descriptors are isolated slice artifacts, horizon-specific, session-specific,
or part of a broader mechanically expressible market-behavior family.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

FLAG_CONTROL_LEDGER = ROUTE_DIR / f"TICK_M15_TARGET_MOVEMENT_FLAG_CONTROL_LEDGER_{SOURCE_STAMP}.jsonl"
TRIAGE_LEDGER = ROUTE_DIR / f"TICK_M15_TARGET_CONTROL_TRIAGE_LEDGER_{SOURCE_STAMP}.jsonl"
PLACEBO_LEDGER = ROUTE_DIR / f"TICK_M15_NEIGHBOR_PLACEBO_CONTROL_LEDGER_{SOURCE_STAMP}.jsonl"
FULL_CONTROL_LEDGER = ROUTE_DIR / f"TICK_M15_FULL_PERMUTATION_CONCENTRATION_LEDGER_{STAMP}.jsonl"
BLOCK_CONTROL_LEDGER = ROUTE_DIR / f"TICK_M15_RESIDUAL_BLOCK_AWARE_CONTROL_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"TICK_M15_CROSS_HORIZON_SESSION_TRANSFER_RESULT_{STAMP}.json"
BASE_ROW_LEDGER = ROUTE_DIR / f"TICK_M15_CROSS_TRANSFER_BASE_ROW_LEDGER_{STAMP}.jsonl"
HORIZON_MATRIX_LEDGER = ROUTE_DIR / f"TICK_M15_CROSS_HORIZON_TRANSFER_MATRIX_{STAMP}.jsonl"
SESSION_MATRIX_LEDGER = ROUTE_DIR / f"TICK_M15_CROSS_SESSION_TRANSFER_MATRIX_{STAMP}.jsonl"
RESIDUAL_TRANSFER_LEDGER = ROUTE_DIR / f"TICK_M15_RESIDUAL_TRANSFER_DIAGNOSIS_LEDGER_{STAMP}.jsonl"
HYPOTHESIS_MUTATION_LEDGER = ROUTE_DIR / f"TICK_M15_TRANSFER_HYPOTHESIS_MUTATION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"TICK_M15_CROSS_HORIZON_SESSION_TRANSFER_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Route C cross-horizon/session transfer diagnostics only; not validation, "
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


def key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (row["symbol"], row["session_bucket"], row["primitive_flag"], row["horizon_id"])


def movement_status(row: dict[str, Any]) -> str:
    flagged_n = int(row.get("flagged_n") or 0)
    delta_abs = safe_float(row.get("delta_mean_abs_future_change"))
    delta_alignment = safe_float(row.get("delta_alignment_rate"))
    if flagged_n < 20:
        return "SMALL_N_LT20"
    if delta_abs is None:
        return "NOT_NUMERIC"
    if delta_abs > 0 and (delta_alignment is None or delta_alignment >= 0):
        return "POSITIVE_ABS_AND_NONNEGATIVE_ALIGNMENT_DELTA"
    if delta_abs > 0 and delta_alignment is not None and delta_alignment < 0:
        return "POSITIVE_ABS_NEGATIVE_ALIGNMENT_DELTA"
    return "FLAT_OR_NEGATIVE_ABS_DELTA"


def support_strength(status: str) -> int:
    if status == "POSITIVE_ABS_AND_NONNEGATIVE_ALIGNMENT_DELTA":
        return 2
    if status == "POSITIVE_ABS_NEGATIVE_ALIGNMENT_DELTA":
        return 1
    return 0


def pattern_from_statuses(statuses: list[str]) -> str:
    material = [status for status in statuses if status != "SMALL_N_LT20"]
    if not material:
        return "ALL_SMALL_N"
    positive = sum(1 for status in material if support_strength(status) > 0)
    strong = sum(1 for status in material if support_strength(status) == 2)
    if positive == len(material) and strong == len(material):
        return "BROAD_POSITIVE_ABS_NONNEGATIVE_ALIGNMENT"
    if positive == len(material):
        return "BROAD_POSITIVE_ABS_MIXED_ALIGNMENT"
    if positive == 0:
        return "NO_POSITIVE_ABS_TRANSFER"
    if positive == 1:
        return "SINGLE_SLICE_ONLY"
    return "PARTIAL_TRANSFER_MIXED"


def compact_cell(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "flagged_n": row["flagged_n"],
        "control_n": row["control_n"],
        "delta_mean_abs_future_change": row["delta_mean_abs_future_change"],
        "delta_alignment_rate": row.get("delta_alignment_rate"),
        "movement_status": row["movement_status"],
        "triage_bucket": row.get("triage_bucket"),
        "placebo_bucket": row.get("placebo_bucket"),
        "full_control_bucket": row.get("full_control_bucket"),
        "block_low_tail_scheme_count": row.get("block_low_tail_scheme_count", 0),
        "block_weak_scheme_count": row.get("block_weak_scheme_count", 0),
    }


def residual_transfer_class(
    row: dict[str, Any],
    horizon_group_rows: list[dict[str, Any]],
    session_group_rows: list[dict[str, Any]],
) -> str:
    current_support = support_strength(row["movement_status"])
    horizon_support = sum(1 for peer in horizon_group_rows if support_strength(peer["movement_status"]) > 0)
    session_support = sum(1 for peer in session_group_rows if support_strength(peer["movement_status"]) > 0)
    block_low_tail = int(row.get("block_low_tail_scheme_count", 0))
    if current_support == 0:
        return "RESIDUAL_WEAK_ON_BASE_MOVEMENT_STATUS"
    if block_low_tail == 0:
        return "RESIDUAL_CONTROL_OR_BLOCK_WEAKENED"
    if horizon_support >= 2 and session_support >= 2:
        return "BROAD_HORIZON_AND_SESSION_TRANSFER_BUT_STILL_DEVELOPMENT_ONLY"
    if horizon_support >= 2:
        return "SAME_SESSION_MULTI_HORIZON_TRANSFER"
    if session_support >= 2:
        return "SAME_HORIZON_MULTI_SESSION_TRANSFER"
    return "ISOLATED_SELECTED_SLICE_REQUIRES_DEEPER_MUTATION"


def mutation_rows_for(residual: dict[str, Any], transfer_class: str) -> list[dict[str, Any]]:
    base = {
        "queue_id": residual["queue_id"],
        "route_id": ROUTE_ID,
        "symbol": residual["symbol"],
        "session_bucket": residual["session_bucket"],
        "horizon_id": residual["horizon_id"],
        "primitive_flag": residual["primitive_flag"],
        "transfer_class": transfer_class,
        "safe_flags": SAFE_FLAGS,
    }
    actions_by_class = {
        "RESIDUAL_CONTROL_OR_BLOCK_WEAKENED": [
            ("avoid_filter_mutation", "Test whether this descriptor identifies generic volatility/noise regimes to avoid rather than entries."),
            ("source_proxy_mutation", "Check if Sierra/venue proxy data explains why MT5 aggressor proxy was misleading."),
            ("cost_filter_mutation", "Join spread/tick velocity to see whether high movement coincides with expensive execution states."),
        ],
        "ISOLATED_SELECTED_SLICE_REQUIRES_DEEPER_MUTATION": [
            ("split_by_clock_mutation", "Split by UTC hour and contiguous event cluster before treating it as a primitive family."),
            ("inverse_window_mutation", "Test if neighboring or opposite-session windows carry inverse/avoid information."),
            ("horizon_target_mutation", "Try target-family/horizon-specific selector rather than a universal primitive."),
        ],
        "SAME_SESSION_MULTI_HORIZON_TRANSFER": [
            ("horizon_router_mutation", "Build a mechanical horizon selector for this symbol/session/primitive family."),
            ("entry_geometry_mutation", "Define executable entry/stop/target geometry for the multi-horizon movement state."),
            ("deconcentration_mutation", "Require future/sealed deconcentration before challenger status."),
        ],
        "SAME_HORIZON_MULTI_SESSION_TRANSFER": [
            ("session_router_mutation", "Build a session-transfer router that separates core/off-core behavior."),
            ("session_cost_mutation", "Check whether the sessions with transfer have similar spread and tick velocity."),
            ("deconcentration_mutation", "Require future/sealed deconcentration before challenger status."),
        ],
        "BROAD_HORIZON_AND_SESSION_TRANSFER_BUT_STILL_DEVELOPMENT_ONLY": [
            ("broad_family_challenger_mutation", "Create a branch-local challenger spec after entry/cost/fill geometry is defined."),
            ("robustness_mutation", "Stress across dates, months, hours, and source files before any validation lane."),
            ("risk_router_mutation", "If later validated, consider volatility/risk routing rather than raw entry use."),
        ],
        "RESIDUAL_WEAK_ON_BASE_MOVEMENT_STATUS": [
            ("kill_entry_claim_preserve_failure", "Kill entry-signal language and preserve as failure intelligence."),
            ("avoid_or_inverse_mutation", "Check whether the weak movement status predicts no-trade or inverse movement."),
            ("source_gap_mutation", "Search whether source completeness or duplicate ticks explain the weak status."),
        ],
    }
    rows: list[dict[str, Any]] = []
    for idx, (mutation_type, action) in enumerate(actions_by_class.get(transfer_class, []), 1):
        row = dict(base)
        row.update({
            "mutation_id": f"{residual['queue_id']}-MUT-{idx:02d}",
            "mutation_type": mutation_type,
            "action": action,
            "status": "open_same_resource_or_next_packet",
            "evidence_boundary": EVIDENCE_BOUNDARY,
        })
        rows.append(row)
    return rows


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "tick_m15_cross_horizon_session_transfer_builder", "created"),
        (RESULT_PATH, "tick_m15_cross_horizon_session_transfer_result", "created"),
        (BASE_ROW_LEDGER, "tick_m15_cross_transfer_base_row_ledger", "created"),
        (HORIZON_MATRIX_LEDGER, "tick_m15_cross_horizon_transfer_matrix", "created"),
        (SESSION_MATRIX_LEDGER, "tick_m15_cross_session_transfer_matrix", "created"),
        (RESIDUAL_TRANSFER_LEDGER, "tick_m15_residual_transfer_diagnosis", "created"),
        (HYPOTHESIS_MUTATION_LEDGER, "tick_m15_transfer_hypothesis_mutation", "created"),
        (SUMMARY_PATH, "tick_m15_cross_horizon_session_transfer_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], transfer_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "tick_m15_cross_horizon_session_transfer",
        "status": "done",
        "route": "tick_sierra_orderflow_route_c",
        "details": (
            "Reopened all 420 Route C flag-control rows to build cross-horizon, cross-session, residual transfer, "
            "and mutation ledgers. This expands the residual packet instead of stopping at selected rows."
        ),
        "counts": counts,
        "residual_transfer_counts": transfer_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(BASE_ROW_LEDGER),
            relative(HORIZON_MATRIX_LEDGER),
            relative(SESSION_MATRIX_LEDGER),
            relative(RESIDUAL_TRANSFER_LEDGER),
            relative(HYPOTHESIS_MUTATION_LEDGER),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def main() -> int:
    generated_utc = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    flag_rows = read_jsonl(FLAG_CONTROL_LEDGER)
    triage_rows = read_jsonl(TRIAGE_LEDGER)
    placebo_rows = read_jsonl(PLACEBO_LEDGER)
    full_control_rows = read_jsonl(FULL_CONTROL_LEDGER)
    block_rows = read_jsonl(BLOCK_CONTROL_LEDGER)

    triage_by_key = {key(row): row for row in triage_rows}
    placebo_by_key = {key(row): row for row in placebo_rows}
    full_by_key = {key(row): row for row in full_control_rows}
    block_counts_by_key: dict[tuple[str, str, str, str], Counter[str]] = defaultdict(Counter)
    for row in block_rows:
        block_counts_by_key[key(row)][row["block_control_bucket"]] += 1

    base_rows: list[dict[str, Any]] = []
    for row in flag_rows:
        row_key = key(row)
        triage = triage_by_key.get(row_key, {})
        placebo = placebo_by_key.get(row_key, {})
        full = full_by_key.get(row_key, {})
        block_counts = block_counts_by_key.get(row_key, Counter())
        movement = movement_status(triage or row)
        base_rows.append({
            "route_id": ROUTE_ID,
            "symbol": row["symbol"],
            "session_bucket": row["session_bucket"],
            "primitive_flag": row["primitive_flag"],
            "horizon_id": row["horizon_id"],
            "flagged_n": row["flagged_n"],
            "control_n": row["control_n"],
            "flagged_mean_abs_future_change": row["flagged_mean_abs_future_change"],
            "control_mean_abs_future_change": row["control_mean_abs_future_change"],
            "delta_mean_abs_future_change": row["delta_mean_abs_future_change"],
            "flagged_delta_alignment_rate": row["flagged_delta_alignment_rate"],
            "control_delta_alignment_rate": row["control_delta_alignment_rate"],
            "delta_alignment_rate": triage.get("delta_alignment_rate"),
            "movement_status": movement,
            "triage_bucket": triage.get("triage_bucket"),
            "placebo_bucket": placebo.get("placebo_bucket"),
            "full_control_bucket": full.get("control_bucket"),
            "block_low_tail_scheme_count": block_counts.get("BLOCK_CONTROL_RESIDUAL_LOW_TAIL", 0),
            "block_weak_scheme_count": block_counts.get("BLOCK_CONTROL_WEAKENED", 0),
            "is_route_c_residual": bool(full),
            "queue_id": full.get("queue_id"),
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        })

    by_horizon_group: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    by_session_group: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in base_rows:
        by_horizon_group[(row["symbol"], row["session_bucket"], row["primitive_flag"])].append(row)
        by_session_group[(row["symbol"], row["primitive_flag"], row["horizon_id"])].append(row)

    horizon_rows: list[dict[str, Any]] = []
    for group_key, rows in sorted(by_horizon_group.items()):
        cells = {row["horizon_id"]: row for row in rows}
        statuses = [row["movement_status"] for row in rows]
        horizon_rows.append({
            "route_id": ROUTE_ID,
            "symbol": group_key[0],
            "session_bucket": group_key[1],
            "primitive_flag": group_key[2],
            "horizon_count": len(rows),
            "h4": compact_cell(cells.get("h4")),
            "h16": compact_cell(cells.get("h16")),
            "h32": compact_cell(cells.get("h32")),
            "status_counts": dict(Counter(statuses)),
            "transfer_pattern": pattern_from_statuses(statuses),
            "residual_queue_ids": sorted(row["queue_id"] for row in rows if row.get("queue_id")),
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        })

    session_rows: list[dict[str, Any]] = []
    for group_key, rows in sorted(by_session_group.items()):
        statuses = [row["movement_status"] for row in rows]
        session_rows.append({
            "route_id": ROUTE_ID,
            "symbol": group_key[0],
            "primitive_flag": group_key[1],
            "horizon_id": group_key[2],
            "session_count": len(rows),
            "sessions": {
                row["session_bucket"]: compact_cell(row)
                for row in sorted(rows, key=lambda item: item["session_bucket"])
            },
            "status_counts": dict(Counter(statuses)),
            "transfer_pattern": pattern_from_statuses(statuses),
            "residual_queue_ids": sorted(row["queue_id"] for row in rows if row.get("queue_id")),
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        })

    residual_rows: list[dict[str, Any]] = []
    mutation_rows: list[dict[str, Any]] = []
    for row in sorted((row for row in base_rows if row["is_route_c_residual"]), key=lambda item: item["queue_id"]):
        horizon_peers = by_horizon_group[(row["symbol"], row["session_bucket"], row["primitive_flag"])]
        session_peers = by_session_group[(row["symbol"], row["primitive_flag"], row["horizon_id"])]
        transfer_class = residual_transfer_class(row, horizon_peers, session_peers)
        residual = {
            "queue_id": row["queue_id"],
            "route_id": ROUTE_ID,
            "symbol": row["symbol"],
            "session_bucket": row["session_bucket"],
            "primitive_flag": row["primitive_flag"],
            "horizon_id": row["horizon_id"],
            "movement_status": row["movement_status"],
            "triage_bucket": row["triage_bucket"],
            "placebo_bucket": row["placebo_bucket"],
            "full_control_bucket": row["full_control_bucket"],
            "block_low_tail_scheme_count": row["block_low_tail_scheme_count"],
            "block_weak_scheme_count": row["block_weak_scheme_count"],
            "same_session_horizon_status_counts": dict(Counter(peer["movement_status"] for peer in horizon_peers)),
            "same_horizon_session_status_counts": dict(Counter(peer["movement_status"] for peer in session_peers)),
            "same_session_horizon_transfer_pattern": pattern_from_statuses([peer["movement_status"] for peer in horizon_peers]),
            "same_horizon_session_transfer_pattern": pattern_from_statuses([peer["movement_status"] for peer in session_peers]),
            "residual_transfer_class": transfer_class,
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        }
        residual_rows.append(residual)
        mutation_rows.extend(mutation_rows_for(residual, transfer_class))

    write_jsonl(BASE_ROW_LEDGER, base_rows)
    write_jsonl(HORIZON_MATRIX_LEDGER, horizon_rows)
    write_jsonl(SESSION_MATRIX_LEDGER, session_rows)
    write_jsonl(RESIDUAL_TRANSFER_LEDGER, residual_rows)
    write_jsonl(HYPOTHESIS_MUTATION_LEDGER, mutation_rows)

    transfer_counts = Counter(row["residual_transfer_class"] for row in residual_rows)
    counts = {
        "base_flag_control_rows": len(base_rows),
        "cross_horizon_matrix_rows": len(horizon_rows),
        "cross_session_matrix_rows": len(session_rows),
        "residual_transfer_rows": len(residual_rows),
        "hypothesis_mutation_rows": len(mutation_rows),
    }
    result = {
        "schema": "tick_m15_cross_horizon_session_transfer_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "ROUTE_C_CROSS_HORIZON_SESSION_TRANSFER_DIAGNOSTIC_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "movement_status_counts": dict(Counter(row["movement_status"] for row in base_rows)),
        "horizon_transfer_pattern_counts": dict(Counter(row["transfer_pattern"] for row in horizon_rows)),
        "session_transfer_pattern_counts": dict(Counter(row["transfer_pattern"] for row in session_rows)),
        "residual_transfer_counts": dict(transfer_counts),
        "next_same_resource_work": [
            "run mutation rows that stay inside current data resources",
            "build entry geometry and cost packet for residuals not fully weakened",
            "expand source acquisition for symbols/sessions absent from the 2026-04-28_to_2026-05-15 tick window",
        ],
        "not_completion": "This transfer packet expands Route C and opens mutation rows; it does not complete the 60-hour objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = [
        "# Tick M15 Cross-Horizon / Cross-Session Transfer",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: transfer diagnostics only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key_name, value in counts.items():
        summary.append(f"- `{key_name}`: `{value}`")
    summary.extend(["", "## Residual Transfer Classes", ""])
    for key_name, value in sorted(transfer_counts.items()):
        summary.append(f"- `{key_name}`: `{value}`")
    summary.extend([
        "",
        "## Boundary",
        "",
        "- This reopens all 420 flag-control rows so the 18 residuals are not treated as isolated winners.",
        "- Mutation rows are work generators, not claims.",
        "",
    ])
    SUMMARY_PATH.write_text("\n".join(summary), encoding="utf-8")

    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, dict(transfer_counts))
    print(json.dumps({"ok": True, "counts": counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
