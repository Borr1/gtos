#!/usr/bin/env python3
"""Compress the final-package shortlist into executable sleeve candidates without selecting a package."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
SYNTHESIS_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_final_package_synthesis_2026_06_19"

SLEEVE_TYPES = {
    "promote_default_off_package_candidate": "promote_default_off_signal_sleeve",
    "merge_with_scheduler_lifecycle_controls": "scheduler_lifecycle_merge_sleeve",
    "redesign_or_source_repair_candidate": "redesign_repair_sleeve",
    "avoid_or_preserve_as_failure_feature": "avoid_failure_feature_sleeve",
    "source_required_before_package_disposition": "source_required_hold_sleeve",
}
SLEEVE_ORDER = {
    "promote_default_off_signal_sleeve": 0,
    "scheduler_lifecycle_merge_sleeve": 1,
    "redesign_repair_sleeve": 2,
    "source_required_hold_sleeve": 3,
    "avoid_failure_feature_sleeve": 4,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(name: str, data: Any) -> None:
    (ROUTE / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(name: str, rows: list[dict[str, Any]]) -> None:
    (ROUTE / name).write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def fnum(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if number == number else 0.0


def sleeve_type(disposition: str) -> str:
    return SLEEVE_TYPES.get(disposition, "source_required_hold_sleeve")


def sleeve_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        sleeve_type(str(row.get("disposition") or "")),
        str(row.get("framework") or "unknown_framework"),
        str(row.get("origin_family") or "unknown_origin_family"),
        str(row.get("side") or "ALL"),
    )


def sleeve_id(key: tuple[str, str, str, str]) -> str:
    raw = "__".join(part.replace(" ", "_").replace("/", "_") for part in key)
    return "fpsc_" + raw.lower()


def new_sleeve_stats() -> dict[str, Any]:
    return {
        "member_rows": 0,
        "symbols": Counter(),
        "sessions": Counter(),
        "selector_rows": 0,
        "selector_positive_lift_rows": 0,
        "selector_zero_lift_rows": 0,
        "selector_lift_sum": 0.0,
        "candidate_level_rows": 0,
        "candidate_level_source_bound_r_sum": 0.0,
        "scheduler_rows": 0,
        "scheduler_result_r_sum": 0.0,
        "scheduler_missed_result_r_sum": 0.0,
        "combined_source_bound_signal_r": 0.0,
        "scheduler_action_class_counts": Counter(),
        "selector_branch_decision_counts": Counter(),
        "source_gap_family_counts": Counter(),
    }


def control_status(row: dict[str, Any], stats: dict[str, Any]) -> tuple[str, str]:
    key_type = row["sleeve_type"]
    action_counts = stats["scheduler_action_class_counts"]
    adverse = action_counts.get("conflict_net", 0) + action_counts.get("reject", 0) + action_counts.get("require_source", 0)
    lifecycle = (
        action_counts.get("queue", 0)
        + action_counts.get("delay", 0)
        + action_counts.get("admit_reduced_risk", 0)
        + action_counts.get("replace", 0)
    )
    if key_type == "promote_default_off_signal_sleeve":
        return (
            "candidate_default_off_acceptance_pending_residual_gates",
            "Keep default-off; require residual gates before any final package or live execution authority.",
        )
    if key_type == "scheduler_lifecycle_merge_sleeve":
        return (
            "merge_with_queue_delay_reduce_replace_controls",
            "Use scheduler lifecycle controls as mandatory sleeve constraints before package acceptance.",
        )
    if key_type == "redesign_repair_sleeve":
        return (
            "redesign_before_acceptance",
            "Preserve edge source, but redesign entry/lifecycle/source requirements before promotion.",
        )
    if key_type == "source_required_hold_sleeve":
        return (
            "hold_until_exact_source_repair",
            "Do not execute or promote until exact source/capture requirements close.",
        )
    if adverse > lifecycle:
        return (
            "avoid_or_convert_to_failure_feature",
            "Use as avoid/veto/failure feature; do not admit as positive sleeve without new evidence.",
        )
    return (
        "avoid_feature_with_lifecycle_watch",
        "Preserve as failure intelligence and concentration watch, not as an executable positive sleeve.",
    )


def build_sleeves(shortlist_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    stats_by_key: defaultdict[tuple[str, str, str, str], dict[str, Any]] = defaultdict(new_sleeve_stats)
    member_rows: list[dict[str, Any]] = []
    for index, row in enumerate(shortlist_rows, 1):
        key = sleeve_key(row)
        sid = sleeve_id(key)
        stats = stats_by_key[key]
        stats["member_rows"] += 1
        stats["symbols"][str(row.get("symbol") or "ALL")] += 1
        stats["sessions"][str(row.get("session_bucket") or "ALL")] += 1
        for field in [
            "selector_rows",
            "selector_positive_lift_rows",
            "selector_zero_lift_rows",
            "candidate_level_rows",
            "scheduler_rows",
        ]:
            stats[field] += int(row.get(field) or 0)
        for field in [
            "selector_lift_sum",
            "candidate_level_source_bound_r_sum",
            "scheduler_result_r_sum",
            "scheduler_missed_result_r_sum",
            "combined_source_bound_signal_r",
        ]:
            stats[field] += fnum(row.get(field))
        stats["scheduler_action_class_counts"].update(row.get("scheduler_action_class_counts") or {})
        stats["selector_branch_decision_counts"].update(row.get("selector_branch_decision_counts") or {})
        stats["source_gap_family_counts"].update(row.get("source_gap_family_counts") or {})
        member_rows.append(
            {
                "schema_version": "gtos.final_moonshot.final_package_acceptance_compression.member_row.v1",
                "source_axis_row_index": index,
                "sleeve_id": sid,
                "sleeve_type": key[0],
                "framework": row.get("framework"),
                "origin_family": row.get("origin_family"),
                "symbol": row.get("symbol"),
                "session_bucket": row.get("session_bucket"),
                "side": row.get("side"),
                "source_disposition": row.get("disposition"),
                "combined_source_bound_signal_r": row.get("combined_source_bound_signal_r"),
                "selector_lift_sum": row.get("selector_lift_sum"),
                "candidate_level_source_bound_r_sum": row.get("candidate_level_source_bound_r_sum"),
                "scheduler_result_r_sum": row.get("scheduler_result_r_sum"),
                "final_package_selection_allowed": False,
                "broker_actual_r_role": "calibration_only_not_edge_source",
            }
        )

    sleeve_rows: list[dict[str, Any]] = []
    for key, stats in stats_by_key.items():
        row = {
            "schema_version": "gtos.final_moonshot.final_package_acceptance_compression.sleeve_row.v1",
            "sleeve_id": sleeve_id(key),
            "sleeve_type": key[0],
            "framework": key[1],
            "origin_family": key[2],
            "side": key[3],
            "member_rows": stats["member_rows"],
            "symbol_count": len(stats["symbols"]),
            "session_bucket_count": len(stats["sessions"]),
            "symbols": sorted(stats["symbols"]),
            "session_buckets": sorted(stats["sessions"]),
            "selector_rows": stats["selector_rows"],
            "selector_positive_lift_rows": stats["selector_positive_lift_rows"],
            "selector_zero_lift_rows": stats["selector_zero_lift_rows"],
            "selector_lift_sum": round(stats["selector_lift_sum"], 9),
            "candidate_level_rows": stats["candidate_level_rows"],
            "candidate_level_source_bound_r_sum": round(stats["candidate_level_source_bound_r_sum"], 9),
            "scheduler_rows": stats["scheduler_rows"],
            "scheduler_result_r_sum": round(stats["scheduler_result_r_sum"], 9),
            "scheduler_missed_result_r_sum": round(stats["scheduler_missed_result_r_sum"], 9),
            "combined_source_bound_signal_r": round(stats["combined_source_bound_signal_r"], 9),
            "scheduler_action_class_counts": dict(stats["scheduler_action_class_counts"]),
            "selector_branch_decision_counts": dict(stats["selector_branch_decision_counts"]),
            "source_gap_family_counts": dict(stats["source_gap_family_counts"].most_common()),
            "final_package_selection_allowed": False,
            "broker_actual_r_role": "calibration_only_not_edge_source",
        }
        row["acceptance_status"], row["next_action"] = control_status(row, stats)
        sleeve_rows.append(row)

    sleeve_rows.sort(
        key=lambda row: (
            SLEEVE_ORDER.get(row["sleeve_type"], 99),
            -row["combined_source_bound_signal_r"],
            row["framework"],
            row["origin_family"],
            row["side"],
        )
    )
    member_rows.sort(key=lambda row: (row["sleeve_id"], row["source_axis_row_index"]))
    return sleeve_rows, member_rows


def build_overlap_rows(member_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: defaultdict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in member_rows:
        grouped[(str(row["symbol"]), str(row["session_bucket"]), str(row["side"]))].append(row)
    out: list[dict[str, Any]] = []
    for key, rows in grouped.items():
        sleeve_counts = Counter(row["sleeve_id"] for row in rows)
        disposition_counts = Counter(row["source_disposition"] for row in rows)
        combined_signal = round(sum(fnum(row["combined_source_bound_signal_r"]) for row in rows), 9)
        if combined_signal <= 0:
            status = "avoid_or_redesign_cell"
        elif len(sleeve_counts) > 1:
            status = "dedup_or_merge_required_before_execution"
        else:
            status = "single_sleeve_cell"
        out.append(
            {
                "schema_version": "gtos.final_moonshot.final_package_acceptance_compression.overlap_row.v1",
                "symbol": key[0],
                "session_bucket": key[1],
                "side": key[2],
                "member_rows": len(rows),
                "participating_sleeve_count": len(sleeve_counts),
                "participating_sleeve_ids": sorted(sleeve_counts),
                "source_disposition_counts": dict(disposition_counts),
                "combined_source_bound_signal_r": combined_signal,
                "control_status": status,
                "final_package_selection_allowed": False,
            }
        )
    out.sort(key=lambda row: (row["symbol"], row["session_bucket"], row["side"]))
    return out


def build_scheduler_controls(sleeve_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in sleeve_rows:
        actions = row.get("scheduler_action_class_counts") or {}
        lifecycle_rows = sum(actions.get(key, 0) for key in ["queue", "delay", "admit_reduced_risk", "replace"])
        block_rows = sum(actions.get(key, 0) for key in ["conflict_net", "reject", "require_source"])
        if row["sleeve_type"] == "scheduler_lifecycle_merge_sleeve":
            control = "mandatory_scheduler_lifecycle_controls"
        elif block_rows > lifecycle_rows:
            control = "block_or_repair_before_positive_use"
        else:
            control = "preserve_controls_for_acceptance_review"
        out.append(
            {
                "schema_version": "gtos.final_moonshot.final_package_acceptance_compression.scheduler_control_row.v1",
                "sleeve_id": row["sleeve_id"],
                "sleeve_type": row["sleeve_type"],
                "member_rows": row["member_rows"],
                "scheduler_rows": row["scheduler_rows"],
                "lifecycle_control_rows": lifecycle_rows,
                "block_or_conflict_rows": block_rows,
                "scheduler_action_class_counts": actions,
                "control_status": control,
                "final_package_selection_allowed": False,
            }
        )
    return out


def affected_sleeves_for_stress(row: dict[str, Any], sleeve_rows: list[dict[str, Any]]) -> list[str]:
    axis = row.get("axis")
    value = row.get("value")
    if axis == "framework":
        return sorted(r["sleeve_id"] for r in sleeve_rows if r["framework"] == value)
    if axis == "side":
        return sorted(r["sleeve_id"] for r in sleeve_rows if r["side"] == value)
    if axis in {"symbol", "held_out_symbol"}:
        return sorted(r["sleeve_id"] for r in sleeve_rows if value in (r.get("symbols") or []))
    if axis == "session":
        return sorted(r["sleeve_id"] for r in sleeve_rows if value in (r.get("session_buckets") or []))
    if axis == "validation_stress_materialization":
        return sorted(r["sleeve_id"] for r in sleeve_rows)
    return sorted(r["sleeve_id"] for r in sleeve_rows if row.get("disposition") != "avoid_or_redesign_axis")


def build_stress_rows(split_rows: list[dict[str, Any]], sleeve_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in split_rows:
        affected = affected_sleeves_for_stress(row, sleeve_rows)
        out.append(
            {
                "schema_version": "gtos.final_moonshot.final_package_acceptance_compression.stress_row.v1",
                "source": row.get("source"),
                "axis": row.get("axis"),
                "value": row.get("value"),
                "rows": row.get("rows"),
                "r_sum": row.get("r_sum"),
                "expectancy_r": row.get("expectancy_r"),
                "positive_rows": row.get("positive_rows"),
                "negative_rows": row.get("negative_rows"),
                "source_disposition": row.get("disposition"),
                "affected_sleeve_count": len(affected),
                "affected_sleeve_ids": affected,
                "final_package_selection_allowed": False,
            }
        )
    return out


def build_concentration_rows(rows: list[dict[str, Any]], sleeve_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_framework_symbol = defaultdict(list)
    for sleeve in sleeve_rows:
        by_framework_symbol[(sleeve["framework"], sleeve.get("side"))].append(sleeve["sleeve_id"])
        by_framework_symbol[(sleeve["framework"], "ALL")].append(sleeve["sleeve_id"])
    out: list[dict[str, Any]] = []
    for row in rows:
        affected = sorted(set(by_framework_symbol.get((row.get("framework"), "ALL"), [])))
        out.append(
            {
                "schema_version": "gtos.final_moonshot.final_package_acceptance_compression.concentration_row.v1",
                "framework": row.get("framework"),
                "symbol": row.get("symbol"),
                "session_bucket": row.get("session_bucket"),
                "rows": row.get("rows"),
                "r_sum": row.get("r_sum"),
                "expectancy_r": row.get("expectancy_r"),
                "source_disposition": row.get("disposition"),
                "affected_sleeve_count": len(affected),
                "affected_sleeve_ids": affected,
                "control_status": row.get("disposition"),
                "final_package_selection_allowed": False,
            }
        )
    return out


def main() -> int:
    generated_utc = utc_now()
    synthesis_summary = read_json(SYNTHESIS_ROUTE / "FINAL_PACKAGE_SYNTHESIS_SUMMARY.json")
    shortlist_rows = read_jsonl(SYNTHESIS_ROUTE / "FINAL_PACKAGE_CANDIDATE_SHORTLIST_LEDGER.jsonl")
    split_rows = read_jsonl(SYNTHESIS_ROUTE / "FINAL_PACKAGE_SPLIT_STRESS_LEDGER.jsonl")
    concentration_source_rows = read_jsonl(SYNTHESIS_ROUTE / "FINAL_PACKAGE_CONCENTRATION_CONTROL_LEDGER.jsonl")
    successor_rows = read_jsonl(SYNTHESIS_ROUTE / "FINAL_PACKAGE_SUCCESSOR_PRIMITIVE_LEDGER.jsonl")
    residual_rows = read_jsonl(SYNTHESIS_ROUTE / "FINAL_PACKAGE_RESIDUAL_GATE_LEDGER.jsonl")

    sleeve_rows, member_rows = build_sleeves(shortlist_rows)
    overlap_rows = build_overlap_rows(member_rows)
    scheduler_rows = build_scheduler_controls(sleeve_rows)
    stress_rows = build_stress_rows(split_rows, sleeve_rows)
    concentration_rows = build_concentration_rows(concentration_source_rows, sleeve_rows)
    acceptance_counts = Counter(row["acceptance_status"] for row in sleeve_rows)
    sleeve_type_counts = Counter(row["sleeve_type"] for row in sleeve_rows)
    member_sleeve_type_counts = Counter(row["sleeve_type"] for row in member_rows)
    residual_status_counts = Counter(row["status"] for row in residual_rows)

    total_combined_signal = round(sum(fnum(row["combined_source_bound_signal_r"]) for row in member_rows), 9)
    total_selector_lift = round(sum(fnum(row["selector_lift_sum"]) for row in member_rows), 9)
    total_candidate_r = round(sum(fnum(row["candidate_level_source_bound_r_sum"]) for row in member_rows), 9)
    total_scheduler_r = round(sum(fnum(row["scheduler_result_r_sum"]) for row in member_rows), 9)

    summary = {
        "schema": "gtos.final_moonshot.final_package_acceptance_compression.summary.v1",
        "generated_utc": generated_utc,
        "status": "final_package_acceptance_compression_checkpoint_not_final_selection",
        "result_scope": "candidate_sleeve_compression_from_full_1101_row_shortlist_not_deployment_readiness",
        "source_route": str(SYNTHESIS_ROUTE.relative_to(ROOT)),
        "input_shortlist_rows": len(shortlist_rows),
        "input_axis_rows": synthesis_summary.get("axis_score_rows"),
        "input_selector_candidate_rows": synthesis_summary.get("selector_candidate_rows"),
        "input_selector_positive_lift_rows": synthesis_summary.get("selector_positive_lift_rows"),
        "input_candidate_level_rows": synthesis_summary.get("candidate_level_rows"),
        "input_candidate_level_source_bound_r_sum": synthesis_summary.get("candidate_level_source_bound_r_sum"),
        "input_scheduler_rows": synthesis_summary.get("scheduler_rows"),
        "input_scheduler_result_r_sum": synthesis_summary.get("scheduler_result_r_sum"),
        "package_sleeve_rows": len(sleeve_rows),
        "sleeve_member_rows": len(member_rows),
        "overlap_dedup_rows": len(overlap_rows),
        "concentration_control_rows": len(concentration_rows),
        "scheduler_lifecycle_control_rows": len(scheduler_rows),
        "split_stress_leave_one_symbol_rows": len(stress_rows),
        "successor_primitive_rows": len(successor_rows),
        "residual_gate_rows": len(residual_rows),
        "sleeve_type_counts": dict(sleeve_type_counts),
        "member_sleeve_type_counts": dict(member_sleeve_type_counts),
        "acceptance_status_counts": dict(acceptance_counts),
        "residual_gate_status_counts": dict(residual_status_counts),
        "compressed_combined_source_bound_signal_r": total_combined_signal,
        "compressed_selector_lift_sum": total_selector_lift,
        "compressed_candidate_level_source_bound_r_sum": total_candidate_r,
        "compressed_scheduler_result_r_sum": total_scheduler_r,
        "forbidden_surface_status": {
            "live_trading": False,
            "broker_operation": False,
            "broker_account_order_history_deal_position_mutation": False,
            "credential_mutation_or_disclosure": False,
            "paid_api_vendor_call": False,
            "blind_remote_push": False,
            "live_vps_restart_or_reload": False,
            "execution_admission_or_sizing_change": False,
        },
        "terminal_decision": {
            "broker_actual_r_claim_allowed": False,
            "broker_actual_r_is_edge_source": False,
            "candidate_package_sleeves_materialized": True,
            "deployment_dossier_allowed": False,
            "final_package_selected": False,
            "live_execution_activation_allowed": False,
            "model_training_allowed": False,
        },
    }

    source_rows = [
        {
            "source_id": "synthesis_shortlist",
            "path": str((SYNTHESIS_ROUTE / "FINAL_PACKAGE_CANDIDATE_SHORTLIST_LEDGER.jsonl").relative_to(ROOT)),
            "rows": len(shortlist_rows),
            "status": "read_full_shortlist_no_top_n",
            "r_sum": total_combined_signal,
        },
        {
            "source_id": "synthesis_split_stress_leave_one_symbol",
            "path": str((SYNTHESIS_ROUTE / "FINAL_PACKAGE_SPLIT_STRESS_LEDGER.jsonl").relative_to(ROOT)),
            "rows": len(split_rows),
            "status": "read_full_split_stress_and_leave_one_symbol",
        },
        {
            "source_id": "synthesis_concentration_controls",
            "path": str((SYNTHESIS_ROUTE / "FINAL_PACKAGE_CONCENTRATION_CONTROL_LEDGER.jsonl").relative_to(ROOT)),
            "rows": len(concentration_source_rows),
            "status": "read_full_concentration_control_ledger",
        },
        {
            "source_id": "synthesis_residual_gates",
            "path": str((SYNTHESIS_ROUTE / "FINAL_PACKAGE_RESIDUAL_GATE_LEDGER.jsonl").relative_to(ROOT)),
            "rows": len(residual_rows),
            "status": "carried_exact_residual_gates",
        },
    ]
    decisions = [
        {
            "decision_id": "FPACD001",
            "status": "selected",
            "decision": "Compress all 1101 shortlist axes into deterministic sleeve candidates without dropping rows.",
            "reason": "Sleeve key is disposition plus framework, origin family, and side; symbol/session rows remain in member and dedup ledgers.",
        },
        {
            "decision_id": "FPACD002",
            "status": "selected",
            "decision": "Treat scheduler lifecycle rows as executable constraints, not proof of final package readiness.",
            "reason": "Queue, delay, reduced-risk, replacement, conflict, reject, and require-source counts are carried into sleeve controls.",
        },
        {
            "decision_id": "FPACD003",
            "status": "selected",
            "decision": "Keep broker actual-R and close-cost as calibration-only residual gates.",
            "reason": "The broad edge is preserved from replay/proxy/source-bound discovery evidence; broker-real claims remain closed.",
        },
        {
            "decision_id": "FPACD004",
            "status": "selected",
            "decision": "Keep final_package_selected=false.",
            "reason": "Acceptance/compression creates candidate sleeves, but residual source, lifecycle, clean-label, and final acceptance gates remain open.",
        },
    ]
    completion = {
        "schema": "gtos.final_moonshot.final_package_acceptance_compression.completion_audit.v1",
        "generated_utc": generated_utc,
        "status": "not_complete_continue",
        "goal_completion_claim": False,
        "instruction_coverage": {
            "full_shortlist_used": "all 1101 candidate shortlist rows mapped to member ledger rows",
            "no_arbitrary_top_n": "82 sleeves are deterministic compression groups, not a rank cap",
            "big_discovery_edge_preserved": "selector lift, candidate-level source-bound R, scheduler result R, and combined signal sums are conserved",
            "broker_r_cost_role": "broker actual-R and close-cost remain calibration-only residual gates",
            "forbidden_surfaces": "no live trading, broker operation, mutation, credential, paid API, blind push, execution sizing, or VPS reload performed",
        },
        "remaining_work": [
            "Repair selected-package lifecycle/fillability/order-type labels before final package selection.",
            "Create clean no-leak labels and deterministic baselines before model training or model promotion.",
            "Import read-only close history or hydrated truth ledgers for broker-real calibration claims.",
            "Run final acceptance after residual gates close; final_package_selected remains false now.",
        ],
        "verification": {"final_package_acceptance_compression": "pending"},
    }
    manifest = {
        "schema": "gtos.final_moonshot.final_package_acceptance_compression.output_manifest.v1",
        "generated_utc": generated_utc,
        "route": str(ROUTE.relative_to(ROOT)),
        "files": [
            "build_final_package_acceptance_compression.py",
            "verify_final_package_acceptance_compression.py",
            "FINAL_PACKAGE_ACCEPTANCE_COMPRESSION_SUMMARY.json",
            "FINAL_PACKAGE_ACCEPTANCE_SOURCE_LEDGER.jsonl",
            "FINAL_PACKAGE_SLEEVE_CANDIDATE_LEDGER.jsonl",
            "FINAL_PACKAGE_SLEEVE_MEMBER_LEDGER.jsonl",
            "FINAL_PACKAGE_OVERLAP_DEDUP_CONCENTRATION_LEDGER.jsonl",
            "FINAL_PACKAGE_SCHEDULER_LIFECYCLE_CONTROL_LEDGER.jsonl",
            "FINAL_PACKAGE_SPLIT_STRESS_ACCEPTANCE_LEDGER.jsonl",
            "FINAL_PACKAGE_CONCENTRATION_ACCEPTANCE_LEDGER.jsonl",
            "FINAL_PACKAGE_SUCCESSOR_PRIMITIVE_ACCEPTANCE_LEDGER.jsonl",
            "FINAL_PACKAGE_ACCEPTANCE_RESIDUAL_GATE_LEDGER.jsonl",
            "DECISION_LEDGER.jsonl",
            "COMPLETION_AUDIT.json",
            "OUTPUT_MANIFEST.json",
            "FOCUSED_TEST_RESULT.json",
            "SATURATION_SELF_RED_TEAM.md",
            "VERIFICATION_RESULT.json",
        ],
    }
    focused = {
        "schema": "gtos.final_moonshot.final_package_acceptance_compression.focused_test_result.v1",
        "generated_utc": generated_utc,
        "status": "pending_verifier",
        "commands": [
            "python3 -m py_compile build_final_package_acceptance_compression.py verify_final_package_acceptance_compression.py",
            "python3 build_final_package_acceptance_compression.py",
            "python3 verify_final_package_acceptance_compression.py",
        ],
    }
    red_team = "\n".join(
        [
            "# Saturation Self Red Team",
            "",
            "- This route compresses a shortlist into sleeves; it does not prove final package selection.",
            "- No top-N cap is used: all 1101 source rows are present in the member ledger.",
            "- Broker actual-R and close-cost remain calibration-only residual gates.",
            "- Sleeve execution is default-off and blocked by residual source, label, lifecycle, and final acceptance gates.",
            "",
        ]
    )

    write_json("FINAL_PACKAGE_ACCEPTANCE_COMPRESSION_SUMMARY.json", summary)
    write_jsonl("FINAL_PACKAGE_ACCEPTANCE_SOURCE_LEDGER.jsonl", source_rows)
    write_jsonl("FINAL_PACKAGE_SLEEVE_CANDIDATE_LEDGER.jsonl", sleeve_rows)
    write_jsonl("FINAL_PACKAGE_SLEEVE_MEMBER_LEDGER.jsonl", member_rows)
    write_jsonl("FINAL_PACKAGE_OVERLAP_DEDUP_CONCENTRATION_LEDGER.jsonl", overlap_rows)
    write_jsonl("FINAL_PACKAGE_SCHEDULER_LIFECYCLE_CONTROL_LEDGER.jsonl", scheduler_rows)
    write_jsonl("FINAL_PACKAGE_SPLIT_STRESS_ACCEPTANCE_LEDGER.jsonl", stress_rows)
    write_jsonl("FINAL_PACKAGE_CONCENTRATION_ACCEPTANCE_LEDGER.jsonl", concentration_rows)
    write_jsonl("FINAL_PACKAGE_SUCCESSOR_PRIMITIVE_ACCEPTANCE_LEDGER.jsonl", successor_rows)
    write_jsonl("FINAL_PACKAGE_ACCEPTANCE_RESIDUAL_GATE_LEDGER.jsonl", residual_rows)
    write_jsonl("DECISION_LEDGER.jsonl", decisions)
    write_json("COMPLETION_AUDIT.json", completion)
    write_json("OUTPUT_MANIFEST.json", manifest)
    write_json("FOCUSED_TEST_RESULT.json", focused)
    (ROUTE / "SATURATION_SELF_RED_TEAM.md").write_text(red_team, encoding="utf-8")
    write_json(
        "VERIFICATION_RESULT.json",
        {
            "schema": "gtos.final_moonshot.final_package_acceptance_compression.verification_result.v1",
            "verified_utc": generated_utc,
            "ok": False,
            "issue_count": 1,
            "issues": ["verifier_not_run_after_build"],
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
