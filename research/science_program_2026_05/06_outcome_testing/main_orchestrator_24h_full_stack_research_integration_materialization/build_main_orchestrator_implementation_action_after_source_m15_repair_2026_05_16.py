"""Build implementation action queue after SOURCE M15-ordering repair.

This versioned follow-up plate consumes the latest SOURCE M15-ordering repair
ledger instead of the earlier SOURCE implication ledger. It preserves the same
3,426-row implementation/action denominator while converting the 30 stale
M15-ordering repair actions into bounded keep/kill/preserve decisions.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-16"
ROUTE_DIR = Path(__file__).resolve().parent

FVG_STRUCT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_FVG_STRUCTURAL_SCORER_CANDIDATE_RECOMPUTE_LEDGER_{DATE}.jsonl"
ENTRY_TICK_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_REDESIGN_TICK_OFFSET_RECOMPUTE_LEDGER_{DATE}.jsonl"
PENDING_DERIVATION_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_DERIVATION_RECOMPUTE_LEDGER_{DATE}.jsonl"
SOURCE_M15_REPAIR_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_M15_ORDERING_REPAIR_LEDGER_{DATE}.jsonl"
PREVIOUS_ACTION_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_RECOMPUTE_BRANCH_ACTION_SUMMARY_{DATE}.json"
SOURCE_M15_REPAIR_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_M15_ORDERING_REPAIR_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_ACTION_AFTER_SOURCE_M15_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_ACTION_AFTER_SOURCE_M15_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_ACTION_AFTER_SOURCE_M15_REPAIR_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            row = json.loads(stripped)
            row["_source_line_no"] = line_no
            rows.append(row)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def classify_implementation_decision(decision: str) -> str:
    if decision.startswith("IMPLEMENT_DEFAULT_OFF"):
        return "IMPLEMENT_DEFAULT_OFF"
    if decision.startswith("KILL"):
        return "KILL"
    if decision.startswith("REDESIGN"):
        return "REDESIGN"
    if decision.startswith("SOURCE_CAPTURE_REQUIRED") or decision.startswith("SOURCE_REPAIR_REQUIRED"):
        return "SOURCE_REPAIR"
    if decision.startswith("KEEP"):
        return "KEEP"
    if decision.startswith("PRESERVE"):
        return "PRESERVE_REQUIREMENT"
    if decision.startswith("DOWNGRADE"):
        return "DOWNGRADE_OR_REPAIR"
    if decision.startswith("UPGRADE"):
        return "UPGRADE_CHALLENGER_REVIEW"
    return "REVIEW_REQUIRED"


def source_after_action_class(bucket: str) -> str:
    return {
        "keep_confirmed_source": "KEEP",
        "keep_confirmed_source_after_ordering_repair": "KEEP",
        "degrade_avoid_or_repair": "DOWNGRADE_OR_REPAIR",
        "repair_or_avoid": "KEEP_REPAIR_OR_AVOID",
        "keep_repair_with_interval_bound": "KEEP_REPAIR_OR_AVOID",
        "source_requirement_only": "PRESERVE_REQUIREMENT",
        "preserve_interval_bound_no_challenger": "PRESERVE_REQUIREMENT",
        "upgraded_challenger_review": "UPGRADE_CHALLENGER_REVIEW",
        "kill_upgraded_challenger_after_ordering_repair": "KILL",
    }.get(bucket, "REVIEW_REQUIRED")


def coverage_status(action_class: str) -> str:
    return {
        "IMPLEMENT_DEFAULT_OFF": "OBSERVABLE_CANDIDATE_READY_DEFAULT_OFF",
        "KILL": "KILLED_WITH_CURRENT_PROXY_EVIDENCE",
        "REDESIGN": "QUEUED_FOR_REDESIGN",
        "SOURCE_REPAIR": "PRESERVED_WITH_EXACT_SOURCE_REQUIREMENT",
        "KEEP": "KEPT_WITH_CURRENT_EVIDENCE",
        "KEEP_WITH_SOURCE_DERIVATION": "KEPT_WITH_PARTIAL_SOURCE_DERIVATION",
        "PRESERVE_REQUIREMENT": "PRESERVED_SOURCE_REQUIREMENT_ONLY",
        "DOWNGRADE_OR_REPAIR": "DOWNGRADED_OR_AVOID_UNTIL_REPAIR",
        "UPGRADE_CHALLENGER_REVIEW": "QUEUED_DEFAULT_OFF_CHALLENGER_REVIEW",
        "KEEP_REPAIR_OR_AVOID": "KEPT_AS_REPAIR_OR_AVOID_BRANCH",
    }.get(action_class, "REVIEW_REQUIRED")


def primitive_family(source_plate: str, source_capture_surface: str | None, decision: str) -> str:
    surface = source_capture_surface or ""
    if source_plate == "entry_redesign_tick_offset_recompute":
        return "entry_geometry_fillability_tick_path_ordering"
    if source_plate == "pending_lifecycle_source_derivation_recompute":
        return "pending_lifecycle_fill_cancel_expiry_source_capture"
    if source_plate == "source_m15_ordering_repair":
        return "source_cost_spread_bar_proxy_implication"
    if "standalone_fvg" in surface:
        return "fvg_entry_geometry_and_lock_metadata"
    if "swing_protected" in surface:
        return "structural_swing_protected_stop_geometry"
    if "structural_lock" in surface:
        return "structural_lock_reentry_cost_metadata"
    if "fvg_ob_confluence" in surface:
        return "fvg_ob_confluence_shared_path_scorer"
    if "prefill" in surface or "PREFILL" in decision:
        return "prefill_delivery_adverse_reversal_path"
    if "pending" in surface:
        return "pending_lifecycle_fill_cancel_expiry_source_capture"
    return "scorer_source_capture_and_branch_decision"


def entry_selected_shift(row: dict[str, Any]) -> tuple[str | None, dict[str, Any] | None, float | None, str]:
    decision = str(row.get("implementation_decision") or "")
    outcomes = row.get("offset_shift_outcomes") or {}
    if decision == "REDESIGN_FAR_MISS_RETEST_WITH_050R_OFFSET_CONTROL":
        selected = outcomes.get("0.5")
        return "0.5", selected, safe_float((selected or {}).get("proxy_r_delta_vs_original_no_fill")), "050R_REDESIGN_CHALLENGER"
    if decision == "KILL_025R_OFFSET_AS_FILL_PROXY_REDESIGN_TO_SPREAD_AWARE_050R_CHALLENGER":
        selected = outcomes.get("0.25")
        alternative = outcomes.get("0.5")
        return "0.25", selected, safe_float((alternative or {}).get("proxy_r_delta_vs_original_no_fill")), "025R_KILLED_050R_ALTERNATIVE_DELTA_REPORTED"
    if decision.startswith("KILL_025R"):
        selected = outcomes.get("0.25")
        return "0.25", selected, safe_float((selected or {}).get("proxy_r_delta_vs_original_no_fill")), "025R_KILLED"
    return None, None, None, "NO_SELECTED_OFFSET_ACTION"


def scorer_proxy_delta(row: dict[str, Any]) -> float | None:
    recorded = safe_float(row.get("proxy_r_delta"))
    if recorded is not None:
        return recorded
    if row.get("before_proxy_r") is None and safe_float(row.get("after_proxy_r")) is not None:
        return safe_float(row.get("after_proxy_r"))
    return None


def make_action_row(
    *,
    row_id: str,
    source_plate: str,
    source_artifact: Path,
    source_row: dict[str, Any],
    action_class: str,
    branch_decision: str,
    implementation_decision: str,
    current_action: str,
    exact_r: Any,
    before_proxy_r: Any,
    after_proxy_r: Any,
    proxy_r_delta: Any,
    selected_shift_r: str | None = None,
    selected_shift_status: str | None = None,
    selected_shift_proxy_r: Any = None,
    data_requirement_state: str | None = None,
    source_capture_surface: str | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "row_id": row_id,
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "source_plate": source_plate,
        "source_artifact": source_artifact.name,
        "source_row_id": source_row.get("row_id"),
        "source_line_no": source_row.get("_source_line_no"),
        "candidate_id": source_row.get("candidate_id") or source_row.get("route_candidate_id"),
        "symbol": source_row.get("symbol"),
        "side": source_row.get("side"),
        "strategy_id": source_row.get("strategy_id"),
        "source_capture_surface": source_capture_surface,
        "primitive_family": primitive_family(source_plate, source_capture_surface, implementation_decision),
        "coverage_status": coverage_status(action_class),
        "action_class": action_class,
        "branch_decision": branch_decision,
        "implementation_decision": implementation_decision,
        "current_action": current_action,
        "next_action": current_action,
        "exact_r": exact_r,
        "before_proxy_r": before_proxy_r,
        "after_proxy_r": after_proxy_r,
        "proxy_r_delta": proxy_r_delta,
        "selected_shift_r": selected_shift_r,
        "selected_shift_status": selected_shift_status,
        "selected_shift_proxy_r": selected_shift_proxy_r,
        "data_requirement_state": data_requirement_state,
        "safe_flags": SAFE_FLAGS,
        "no_live_behavior": True,
        "no_shadow_log_append": True,
        "no_promotion": True,
    }
    if extra_fields:
        row.update(extra_fields)
    return row


def build_rows() -> list[dict[str, Any]]:
    generated_rows: list[dict[str, Any]] = []
    seq = 0

    for row in read_jsonl(FVG_STRUCT_LEDGER):
        seq += 1
        decision = str(row.get("implementation_decision") or "")
        generated_rows.append(
            make_action_row(
                row_id=f"MAIN-ORCH24-ACTION-SRCM15-{seq:05d}",
                source_plate="fvg_structural_scorer_candidate_recompute",
                source_artifact=FVG_STRUCT_LEDGER,
                source_row=row,
                action_class=classify_implementation_decision(decision),
                branch_decision=str(row.get("after_branch_decision") or decision),
                implementation_decision=decision,
                current_action=str(row.get("after_implementation_candidate") or row.get("after_strategy_status") or decision),
                exact_r=row.get("exact_r"),
                before_proxy_r=row.get("before_proxy_r"),
                after_proxy_r=row.get("after_proxy_r"),
                proxy_r_delta=scorer_proxy_delta(row),
                data_requirement_state=row.get("after_score_status"),
                source_capture_surface=row.get("source_capture_surface"),
            )
        )

    for row in read_jsonl(ENTRY_TICK_LEDGER):
        seq += 1
        decision = str(row.get("implementation_decision") or "")
        shift, selected, selected_delta, basis = entry_selected_shift(row)
        generated_rows.append(
            make_action_row(
                row_id=f"MAIN-ORCH24-ACTION-SRCM15-{seq:05d}",
                source_plate="entry_redesign_tick_offset_recompute",
                source_artifact=ENTRY_TICK_LEDGER,
                source_row=row,
                action_class=classify_implementation_decision(decision),
                branch_decision=decision,
                implementation_decision=decision,
                current_action=basis,
                exact_r=row.get("exact_r"),
                before_proxy_r=0.0 if row.get("entry_retest_redesign_bucket") != "NOT_A_NO_FILL_TP1_ENTRY_REDESIGN_ROW" else None,
                after_proxy_r=(selected or {}).get("proxy_r"),
                proxy_r_delta=selected_delta,
                selected_shift_r=shift,
                selected_shift_status=(selected or {}).get("outcome_status"),
                selected_shift_proxy_r=(selected or {}).get("proxy_r"),
                data_requirement_state=row.get("tick_source_status"),
                source_capture_surface="entry_redesign_tick_offset",
            )
        )

    for row in read_jsonl(PENDING_DERIVATION_LEDGER):
        seq += 1
        decision = str(row.get("implementation_decision") or "")
        action_class = "KEEP_WITH_SOURCE_DERIVATION" if "DERIVED_SOURCE_FIELDS" in decision else classify_implementation_decision(decision)
        generated_rows.append(
            make_action_row(
                row_id=f"MAIN-ORCH24-ACTION-SRCM15-{seq:05d}",
                source_plate="pending_lifecycle_source_derivation_recompute",
                source_artifact=PENDING_DERIVATION_LEDGER,
                source_row=row,
                action_class=action_class,
                branch_decision=decision,
                implementation_decision=decision,
                current_action=str(row.get("after_source_capture_complete")),
                exact_r=row.get("exact_r"),
                before_proxy_r=row.get("before_proxy_r"),
                after_proxy_r=row.get("after_proxy_r"),
                proxy_r_delta=row.get("proxy_r_delta"),
                data_requirement_state=row.get("after_score_status"),
                source_capture_surface="pending_limit_lifecycle_source_derivation",
            )
        )

    for row in read_jsonl(SOURCE_M15_REPAIR_LEDGER):
        seq += 1
        bucket = str(row.get("after_implementation_bucket") or "")
        action_class = source_after_action_class(bucket)
        midpoint = safe_float(row.get("ordering_proxy_midpoint_r"))
        generated_rows.append(
            make_action_row(
                row_id=f"MAIN-ORCH24-ACTION-SRCM15-{seq:05d}",
                source_plate="source_m15_ordering_repair",
                source_artifact=SOURCE_M15_REPAIR_LEDGER,
                source_row=row,
                action_class=action_class,
                branch_decision=str(row.get("after_branch_decision") or ""),
                implementation_decision=str(row.get("after_branch_decision") or ""),
                current_action=bucket,
                exact_r=row.get("exact_r"),
                before_proxy_r=None,
                after_proxy_r=midpoint,
                proxy_r_delta=midpoint,
                data_requirement_state=row.get("ordering_score_status"),
                source_capture_surface="source_m15_ordering_repair",
                extra_fields={
                    "source_branch_queue_id": row.get("source_branch_queue_id"),
                    "target_stop_contract_id": row.get("target_stop_contract_id"),
                    "m15_ordering_repair_status": row.get("m15_ordering_repair_status"),
                    "ordering_evidence_source": row.get("ordering_evidence_source"),
                    "ordering_proxy_lower_r": row.get("ordering_proxy_lower_r"),
                    "ordering_proxy_midpoint_r": row.get("ordering_proxy_midpoint_r"),
                    "ordering_proxy_upper_r": row.get("ordering_proxy_upper_r"),
                    "interval_sign_class": row.get("interval_sign_class"),
                    "exact_chronology_claim": row.get("exact_chronology_claim"),
                },
            )
        )

    return generated_rows


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(str(row.get(field) or "") for row in rows))


def proxy_delta_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_plate: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        value = safe_float(row.get("proxy_r_delta"))
        if value is not None:
            by_plate[str(row.get("source_plate"))].append(value)
    return {
        plate: {
            "numeric_proxy_delta_rows": len(values),
            "proxy_r_delta_sum": round(sum(values), 8),
            "proxy_r_delta_mean": round(sum(values) / len(values), 8) if values else None,
        }
        for plate, values in sorted(by_plate.items())
    }


def source_m15_bounds(rows: list[dict[str, Any]]) -> dict[str, Any]:
    affected = [row for row in rows if row.get("source_plate") == "source_m15_ordering_repair" and row.get("m15_ordering_repair_status") == "REPAIRED_WITH_BOUNDED_ORDERING_PROXY"]
    lower = [safe_float(row.get("ordering_proxy_lower_r")) for row in affected]
    mid = [safe_float(row.get("ordering_proxy_midpoint_r")) for row in affected]
    upper = [safe_float(row.get("ordering_proxy_upper_r")) for row in affected]
    return {
        "rows": len(affected),
        "lower_sum": round(sum(v for v in lower if v is not None), 6),
        "midpoint_sum": round(sum(v for v in mid if v is not None), 6),
        "upper_sum": round(sum(v for v in upper if v is not None), 6),
        "exact_chronology_true_rows": sum(1 for row in affected if row.get("exact_chronology_claim") is True),
    }


def action_count_delta(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
    keys = sorted(set(before) | set(after))
    return {key: int(after.get(key, 0)) - int(before.get(key, 0)) for key in keys if int(after.get(key, 0)) != int(before.get(key, 0))}


def build_manifest(paths: list[Path]) -> dict[str, Any]:
    inputs = [
        FVG_STRUCT_LEDGER,
        ENTRY_TICK_LEDGER,
        PENDING_DERIVATION_LEDGER,
        SOURCE_M15_REPAIR_LEDGER,
        PREVIOUS_ACTION_SUMMARY,
        SOURCE_M15_REPAIR_SUMMARY,
    ]
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "input_artifacts": {
            path.name: {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in inputs
        },
        "output_artifacts": {
            path.name: {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in paths
        },
        "safe_flags": SAFE_FLAGS,
    }


def main() -> None:
    rows = build_rows()
    previous_summary = read_json(PREVIOUS_ACTION_SUMMARY)
    source_summary = read_json(SOURCE_M15_REPAIR_SUMMARY)
    action_counts = counter(rows, "action_class")
    coverage_counts = counter(rows, "coverage_status")
    branch_counts = counter(rows, "branch_decision")
    proxy_summary = proxy_delta_summary(rows)
    bounds = source_m15_bounds(rows)

    write_jsonl(OUTPUT_LEDGER, rows)
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_IMPLEMENTATION_ACTION_AFTER_SOURCE_M15_REPAIR",
        "claim_boundary": (
            "Versioned implementation/action queue after SOURCE M15-ordering repair. "
            "It converts stale M15-ordering repair actions into bounded keep/kill/preserve "
            "decisions only; no live behavior, broker R, promotion, validation-safe, or "
            "execution change."
        ),
        "action_rows": len(rows),
        "source_plate_counts": counter(rows, "source_plate"),
        "action_class_counts": action_counts,
        "coverage_status_counts": coverage_counts,
        "primitive_family_counts": counter(rows, "primitive_family"),
        "branch_decision_counts": branch_counts,
        "implementation_decision_counts": counter(rows, "implementation_decision"),
        "proxy_delta_summary_by_plate": proxy_summary,
        "before_action_class_counts": previous_summary.get("action_class_counts"),
        "action_class_delta_vs_previous": action_count_delta(previous_summary.get("action_class_counts", {}), action_counts),
        "before_coverage_status_counts": previous_summary.get("coverage_status_counts"),
        "coverage_status_delta_vs_previous": action_count_delta(previous_summary.get("coverage_status_counts", {}), coverage_counts),
        "m15_ordering_repair_actions_before": previous_summary.get("action_class_counts", {}).get("M15_ORDERING_REPAIR", 0),
        "m15_ordering_repair_actions_after": action_counts.get("M15_ORDERING_REPAIR", 0),
        "source_m15_ordering_repair_rows": source_summary.get("m15_ordering_repaired_rows"),
        "source_m15_ordering_proxy_bounds": bounds,
        "source_m15_after_branch_decision_counts": source_summary.get("after_branch_decision_counts"),
        "source_m15_ordering_evidence_source_counts": source_summary.get("ordering_evidence_source_counts"),
        "plate_decision": "IMPLEMENTATION_ACTION_QUEUE_CONSUMES_SOURCE_M15_ORDERING_REPAIR",
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(json.dumps({"rows_written": len(rows), "summary": str(OUTPUT_SUMMARY)}, sort_keys=True))


if __name__ == "__main__":
    main()
