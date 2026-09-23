#!/usr/bin/env python3
"""Build lifecycle/fillability/order-type bridge evidence for compressed package sleeves."""

from __future__ import annotations

import json
import subprocess
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
ACCEPTANCE_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_final_package_acceptance_compression_2026_06_19"
FILLABILITY_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19"
ORDER_TYPE_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_f_order_type_fillability_join_exhaustion_2026_06_19"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_text(path: Path) -> str:
    last_error: OSError | None = None
    for _ in range(5):
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            last_error = exc
            time.sleep(0.05)
    rel = path.relative_to(ROOT)
    try:
        return subprocess.check_output(["git", "show", f"HEAD:{rel}"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError):
        if last_error:
            raise last_error
        raise


def read_json(path: Path) -> Any:
    return json.loads(read_text(path))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in read_text(path).splitlines() if line.strip()]


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


def pair_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("symbol") or "UNKNOWN"), str(row.get("side") or "UNKNOWN")


def infer_order_type(row: dict[str, Any]) -> str:
    if row.get("pending_lifecycle_v4_state_group") in {"active_pending", "nofill_terminal", "filled_terminal", "retry_active"}:
        return "internal_pending_limit_or_retry_lifecycle"
    if row.get("order_send_attempted") is True:
        return "order_send_attempt_lifecycle"
    return "unknown_order_type"


def build_context_rows(
    labels_by_pair: dict[tuple[str, str], list[dict[str, Any]]],
    members_by_pair: dict[tuple[str, str], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in sorted(set(labels_by_pair) & set(members_by_pair)):
        for label in labels_by_pair[key]:
            for member in members_by_pair[key]:
                rows.append(
                    {
                        "schema_version": "gtos.final_moonshot.final_package_lifecycle_fillability_bridge.context_row.v1",
                        "bridge_status": "context_only_symbol_side_not_denominator_exact",
                        "symbol": key[0],
                        "side": key[1],
                        "sleeve_id": member.get("sleeve_id"),
                        "sleeve_type": member.get("sleeve_type"),
                        "source_axis_row_index": member.get("source_axis_row_index"),
                        "member_session_bucket": member.get("session_bucket"),
                        "member_source_disposition": member.get("source_disposition"),
                        "label_id": label.get("label_id"),
                        "label_candidate_id": label.get("candidate_id"),
                        "label_decision_time_utc": label.get("decision_time_utc"),
                        "label_fill_no_fill": label.get("fill_no_fill_label"),
                        "label_family": label.get("fillability_label_family"),
                        "label_lifecycle_state_group": label.get("pending_lifecycle_v4_state_group"),
                        "label_order_type_inference": infer_order_type(label),
                        "exact_denominator_join_allowed": False,
                        "exact_denominator_blocker": "member_rows_lack_candidate_id_decision_time_and_order_lifecycle_namespace",
                        "broker_actual_r_role": "calibration_only_not_edge_source",
                        "final_package_selection_allowed": False,
                    }
                )
    return rows


def main() -> int:
    generated_utc = utc_now()
    acceptance_summary = read_json(ACCEPTANCE_ROUTE / "FINAL_PACKAGE_ACCEPTANCE_COMPRESSION_SUMMARY.json")
    sleeve_rows = read_jsonl(ACCEPTANCE_ROUTE / "FINAL_PACKAGE_SLEEVE_CANDIDATE_LEDGER.jsonl")
    member_rows = read_jsonl(ACCEPTANCE_ROUTE / "FINAL_PACKAGE_SLEEVE_MEMBER_LEDGER.jsonl")
    labels = read_jsonl(FILLABILITY_ROUTE / "WAVE_F_ROW_BOUND_FILLABILITY_LABEL_REPAIR_LEDGER.jsonl")
    capture_requirements = read_jsonl(ORDER_TYPE_ROUTE / "WAVE_F_ORDER_TYPE_FILLABILITY_CAPTURE_REQUIREMENT_LEDGER.jsonl")

    labels_by_pair: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for label in labels:
        labels_by_pair[pair_key(label)].append(label)
    members_by_pair: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for member in member_rows:
        if member.get("side") in {"LONG", "SHORT"}:
            members_by_pair[pair_key(member)].append(member)

    context_rows = build_context_rows(labels_by_pair, members_by_pair)
    bridged_member_indexes = {row["source_axis_row_index"] for row in context_rows}
    bridged_label_ids = {row["label_id"] for row in context_rows}
    bridged_sleeves = {row["sleeve_id"] for row in context_rows}
    sleeve_context_counts = Counter(row["sleeve_id"] for row in context_rows)
    member_context_counts = Counter(row["source_axis_row_index"] for row in context_rows)

    label_bridge_rows: list[dict[str, Any]] = []
    for label in labels:
        key = pair_key(label)
        matching_members = members_by_pair.get(key, [])
        label_bridge_rows.append(
            {
                "schema_version": "gtos.final_moonshot.final_package_lifecycle_fillability_bridge.label_row.v1",
                "label_id": label.get("label_id"),
                "candidate_id": label.get("candidate_id"),
                "symbol": label.get("symbol"),
                "side": label.get("side"),
                "decision_time_utc": label.get("decision_time_utc"),
                "fill_no_fill_label": label.get("fill_no_fill_label"),
                "fillability_label_family": label.get("fillability_label_family"),
                "lifecycle_state_group": label.get("pending_lifecycle_v4_state_group"),
                "order_type_inference": infer_order_type(label),
                "context_member_rows": len(matching_members),
                "context_sleeve_rows": len({row.get("sleeve_id") for row in matching_members}),
                "bridge_status": (
                    "context_bridge_available_exact_denominator_blocked"
                    if matching_members
                    else "no_current_sleeve_symbol_side_context"
                ),
                "exact_denominator_join_allowed": False,
                "exact_denominator_blocker": "selected_sleeve_members_do_not_carry_label_candidate_id_or_decision_time",
                "training_use_allowed": False,
                "final_package_selection_allowed": False,
            }
        )

    member_bridge_rows: list[dict[str, Any]] = []
    for member in member_rows:
        if member.get("side") in {"LONG", "SHORT"}:
            matching_labels = labels_by_pair.get(pair_key(member), [])
        else:
            matching_labels = []
        member_bridge_rows.append(
            {
                "schema_version": "gtos.final_moonshot.final_package_lifecycle_fillability_bridge.member_row.v1",
                "source_axis_row_index": member.get("source_axis_row_index"),
                "sleeve_id": member.get("sleeve_id"),
                "sleeve_type": member.get("sleeve_type"),
                "symbol": member.get("symbol"),
                "side": member.get("side"),
                "session_bucket": member.get("session_bucket"),
                "source_disposition": member.get("source_disposition"),
                "combined_source_bound_signal_r": member.get("combined_source_bound_signal_r"),
                "context_label_rows": len(matching_labels),
                "context_fillability_label_families": dict(Counter(label.get("fillability_label_family") for label in matching_labels)),
                "context_fill_no_fill_labels": dict(Counter(label.get("fill_no_fill_label") for label in matching_labels)),
                "bridge_status": (
                    "context_bridge_available_exact_denominator_blocked"
                    if matching_labels
                    else "no_lifecycle_label_context_for_symbol_side"
                ),
                "exact_denominator_join_allowed": False,
                "exact_denominator_blocker": "source_axis_member_lacks_candidate_id_decision_time_pending_order_ticket_and_order_type_namespace",
                "broker_actual_r_role": "calibration_only_not_edge_source",
                "final_package_selection_allowed": False,
            }
        )

    sleeve_bridge_rows: list[dict[str, Any]] = []
    for sleeve in sleeve_rows:
        sleeve_id = sleeve["sleeve_id"]
        sleeve_members = [row for row in member_bridge_rows if row["sleeve_id"] == sleeve_id]
        context_members = [row for row in sleeve_members if row["context_label_rows"] > 0]
        label_rows_for_sleeve = sleeve_context_counts.get(sleeve_id, 0)
        status = (
            "context_bridge_available_exact_denominator_blocked"
            if label_rows_for_sleeve
            else "no_lifecycle_label_context_for_sleeve_symbols"
        )
        sleeve_bridge_rows.append(
            {
                "schema_version": "gtos.final_moonshot.final_package_lifecycle_fillability_bridge.sleeve_row.v1",
                "sleeve_id": sleeve_id,
                "sleeve_type": sleeve.get("sleeve_type"),
                "framework": sleeve.get("framework"),
                "origin_family": sleeve.get("origin_family"),
                "side": sleeve.get("side"),
                "member_rows": sleeve.get("member_rows"),
                "context_member_rows": len(context_members),
                "context_bridge_pair_rows": label_rows_for_sleeve,
                "context_symbol_count": len({row["symbol"] for row in context_members}),
                "acceptance_status": sleeve.get("acceptance_status"),
                "combined_source_bound_signal_r": sleeve.get("combined_source_bound_signal_r"),
                "bridge_status": status,
                "exact_denominator_join_allowed": False,
                "exact_denominator_blocker": "candidate_id_decision_window_and_order_lifecycle_namespace_missing_from_sleeve_members",
                "broker_actual_r_role": "calibration_only_not_edge_source",
                "final_package_selection_allowed": False,
            }
        )

    source_gap_rows = [
        {
            "gap_id": "LFOG001",
            "gap": "candidate_id_or_decision_window_namespace",
            "evidence": "1101 sleeve member rows have source_axis_row_index/symbol/side/session but no label candidate_id or decision_window_id",
            "status": "open_exact_denominator_bridge_requirement",
            "required_repair": "Carry candidate_id or stable decision_window_id from selected package replay rows into sleeve members and lifecycle labels.",
            "final_package_selection_allowed": False,
        },
        {
            "gap_id": "LFOG002",
            "gap": "order_type_lifecycle_join",
            "evidence": "877 lifecycle labels carry internal pending/fill/no-fill states but remain context-only against sleeve members",
            "status": "open_exact_order_type_lifecycle_requirement",
            "required_repair": "Join pending order ticket or explicit no-broker-order internal-intent proof plus cancel/replace/time-in-force/fillability outcomes to selected sleeve rows.",
            "final_package_selection_allowed": False,
        },
        {
            "gap_id": "LFOG003",
            "gap": "training_and_final_selection_use",
            "evidence": "context bridges are symbol/side aggregates and cannot serve as no-leak row labels",
            "status": "open_clean_label_and_acceptance_requirement",
            "required_repair": "Create exact no-leak selected-package lifecycle labels before model training or final package selection.",
            "final_package_selection_allowed": False,
        },
        {
            "gap_id": "LFOG004",
            "gap": "broker_actual_r_scope",
            "evidence": "broker actual-R is unrelated to lifecycle bridge edge source and remains calibration-only",
            "status": "calibration_only_not_edge_source",
            "required_repair": "Do not use broker actual-R or close-cost as edge source; import read-only close history only for claim calibration.",
            "final_package_selection_allowed": False,
        },
    ]
    residual_gate_rows = [
        {
            "gate_id": "FPSG002",
            "gate": "fillability_order_type_denominator",
            "previous_status": "open_exact_denominator_bridge_required",
            "bridge_evidence": f"{len(context_rows)} context bridge rows across {len(bridged_member_indexes)} sleeve members and {len(bridged_label_ids)} lifecycle labels",
            "status": "context_bridge_materialized_exact_denominator_still_open",
            "required_repair": "Add candidate_id/decision_window/order lifecycle namespace to selected-package sleeve members before final selection.",
            "final_package_selection_allowed": False,
        },
        {
            "gate_id": "FPSG001",
            "gate": "broker_actual_r_and_close_cost_claim_quality",
            "status": "calibration_gate_partial_not_edge_source",
            "required_repair": "Broker actual-R/close-cost remain calibration-only; import read-only close history before broker-real claims.",
            "final_package_selection_allowed": False,
        },
        {
            "gate_id": "FPSG003",
            "gate": "clean_labels_and_model_training",
            "status": "open_clean_label_requirement",
            "required_repair": "Create exact no-leak labels and deterministic baselines before model training.",
            "final_package_selection_allowed": False,
        },
        {
            "gate_id": "FPSG004",
            "gate": "package_selection_verifier",
            "status": "open_final_selection_not_yet_proven",
            "required_repair": "Run final acceptance only after residual gates close.",
            "final_package_selection_allowed": False,
        },
    ]

    source_rows = [
        {
            "source_id": "acceptance_sleeve_members",
            "path": str((ACCEPTANCE_ROUTE / "FINAL_PACKAGE_SLEEVE_MEMBER_LEDGER.jsonl").relative_to(ROOT)),
            "rows": len(member_rows),
            "status": "read_full_member_denominator_no_top_n",
        },
        {
            "source_id": "acceptance_sleeves",
            "path": str((ACCEPTANCE_ROUTE / "FINAL_PACKAGE_SLEEVE_CANDIDATE_LEDGER.jsonl").relative_to(ROOT)),
            "rows": len(sleeve_rows),
            "status": "read_full_sleeve_candidate_set",
        },
        {
            "source_id": "row_bound_fillability_labels",
            "path": str((FILLABILITY_ROUTE / "WAVE_F_ROW_BOUND_FILLABILITY_LABEL_REPAIR_LEDGER.jsonl").relative_to(ROOT)),
            "rows": len(labels),
            "status": "read_full_lifecycle_label_set",
        },
        {
            "source_id": "order_type_capture_requirements",
            "path": str((ORDER_TYPE_ROUTE / "WAVE_F_ORDER_TYPE_FILLABILITY_CAPTURE_REQUIREMENT_LEDGER.jsonl").relative_to(ROOT)),
            "rows": len(capture_requirements),
            "status": "read_exact_capture_requirements",
        },
    ]

    label_family_counts = Counter(row.get("fillability_label_family") for row in labels)
    fill_no_fill_counts = Counter(row.get("fill_no_fill_label") for row in labels)
    member_status_counts = Counter(row["bridge_status"] for row in member_bridge_rows)
    sleeve_status_counts = Counter(row["bridge_status"] for row in sleeve_bridge_rows)
    label_status_counts = Counter(row["bridge_status"] for row in label_bridge_rows)

    summary = {
        "schema": "gtos.final_moonshot.final_package_lifecycle_fillability_bridge.summary.v1",
        "generated_utc": generated_utc,
        "status": "final_package_lifecycle_fillability_bridge_checkpoint_exact_denominator_still_open",
        "result_scope": "lifecycle_fillability_order_type_context_bridge_for_82_sleeves_not_final_selection",
        "source_acceptance_route": str(ACCEPTANCE_ROUTE.relative_to(ROOT)),
        "input_package_sleeve_rows": len(sleeve_rows),
        "input_sleeve_member_rows": len(member_rows),
        "input_lifecycle_label_rows": len(labels),
        "input_order_type_capture_requirement_rows": len(capture_requirements),
        "context_bridge_rows": len(context_rows),
        "sleeve_bridge_rows": len(sleeve_bridge_rows),
        "member_bridge_rows": len(member_bridge_rows),
        "label_bridge_rows": len(label_bridge_rows),
        "source_gap_rows": len(source_gap_rows),
        "residual_gate_rows": len(residual_gate_rows),
        "context_bridged_sleeve_rows": len(bridged_sleeves),
        "context_bridged_member_rows": len(bridged_member_indexes),
        "context_bridged_label_rows": len(bridged_label_ids),
        "exact_denominator_join_rows": 0,
        "member_bridge_status_counts": dict(member_status_counts),
        "sleeve_bridge_status_counts": dict(sleeve_status_counts),
        "label_bridge_status_counts": dict(label_status_counts),
        "label_family_counts": dict(label_family_counts),
        "fill_no_fill_label_counts": dict(fill_no_fill_counts),
        "preserved_combined_source_bound_signal_r": acceptance_summary.get("compressed_combined_source_bound_signal_r"),
        "broker_actual_r_role": "calibration_only_not_edge_source",
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
            "candidate_lifecycle_context_bridge_materialized": True,
            "exact_lifecycle_denominator_bridge_closed": False,
            "deployment_dossier_allowed": False,
            "final_package_selected": False,
            "live_execution_activation_allowed": False,
            "model_training_allowed": False,
        },
    }
    decisions = [
        {
            "decision_id": "LFOD001",
            "status": "selected",
            "decision": "Bridge all available lifecycle labels to sleeve members by symbol/side context without using a top-N cap.",
            "reason": "The current sleeve member denominator has no candidate_id or decision_window_id, so context bridge is useful evidence but not exact denominator closure.",
        },
        {
            "decision_id": "LFOD002",
            "status": "selected",
            "decision": "Keep exact lifecycle/fillability/order-type denominator gate open.",
            "reason": "No exact row-level join can be proven without candidate_id, decision time, pending ticket, or order lifecycle namespace on selected sleeve members.",
        },
        {
            "decision_id": "LFOD003",
            "status": "selected",
            "decision": "Preserve the big discovery edge and keep broker actual-R calibration-only.",
            "reason": "Lifecycle bridge quality changes final-selection admissibility, not the source-bound replay/proxy edge itself.",
        },
    ]
    completion = {
        "schema": "gtos.final_moonshot.final_package_lifecycle_fillability_bridge.completion_audit.v1",
        "generated_utc": generated_utc,
        "status": "not_complete_continue",
        "goal_completion_claim": False,
        "instruction_coverage": {
            "current_disk_evidence": "read committed acceptance/compression sleeves and current lifecycle label repair artifacts",
            "full_ledgers": "all 82 sleeves, 1101 members, 877 labels, and 19216 context bridge rows emitted",
            "no_top_n": "no rank cap; bridge covers every available symbol/side context pair",
            "broker_r_role": "broker actual-R remains calibration-only and is not used as edge source",
            "forbidden_surfaces": "no live trading, broker mutation, VPS reload, credentials, paid API, or execution sizing performed",
        },
        "remaining_work": [
            "Carry candidate_id or decision_window_id onto selected-package sleeve member rows.",
            "Join pending order ticket or explicit no-broker-order internal-intent proof plus cancel/replace/time-in-force/fillability outcomes to selected sleeve rows.",
            "Create clean no-leak exact lifecycle labels before model training or final selection.",
        ],
        "verification": {"final_package_lifecycle_fillability_bridge": "pending"},
    }
    manifest = {
        "schema": "gtos.final_moonshot.final_package_lifecycle_fillability_bridge.output_manifest.v1",
        "generated_utc": generated_utc,
        "route": str(ROUTE.relative_to(ROOT)),
        "files": [
            "build_final_package_lifecycle_fillability_bridge.py",
            "verify_final_package_lifecycle_fillability_bridge.py",
            "FINAL_PACKAGE_LIFECYCLE_FILLABILITY_BRIDGE_SUMMARY.json",
            "FINAL_PACKAGE_LIFECYCLE_FILLABILITY_SOURCE_LEDGER.jsonl",
            "FINAL_PACKAGE_LIFECYCLE_SLEEVE_BRIDGE_LEDGER.jsonl",
            "FINAL_PACKAGE_LIFECYCLE_MEMBER_BRIDGE_LEDGER.jsonl",
            "FINAL_PACKAGE_LIFECYCLE_LABEL_BRIDGE_LEDGER.jsonl",
            "FINAL_PACKAGE_LIFECYCLE_CONTEXT_JOIN_LEDGER.jsonl",
            "FINAL_PACKAGE_LIFECYCLE_SOURCE_GAP_LEDGER.jsonl",
            "FINAL_PACKAGE_LIFECYCLE_RESIDUAL_GATE_LEDGER.jsonl",
            "DECISION_LEDGER.jsonl",
            "COMPLETION_AUDIT.json",
            "OUTPUT_MANIFEST.json",
            "FOCUSED_TEST_RESULT.json",
            "SATURATION_SELF_RED_TEAM.md",
            "VERIFICATION_RESULT.json",
        ],
    }
    focused = {
        "schema": "gtos.final_moonshot.final_package_lifecycle_fillability_bridge.focused_test_result.v1",
        "generated_utc": generated_utc,
        "status": "pending_verifier",
        "commands": [
            "python3 -m py_compile build_final_package_lifecycle_fillability_bridge.py verify_final_package_lifecycle_fillability_bridge.py",
            "python3 build_final_package_lifecycle_fillability_bridge.py",
            "python3 verify_final_package_lifecycle_fillability_bridge.py",
        ],
    }
    red_team = "\n".join(
        [
            "# Saturation Self Red Team",
            "",
            "- This route materializes context lifecycle bridges; it does not close exact denominator eligibility.",
            "- No top-N cap is used; all sleeve members and labels are processed.",
            "- Symbol/side bridge evidence cannot be used as clean training labels or final package selection proof.",
            "- Broker actual-R and close-cost remain calibration-only.",
            "",
        ]
    )

    write_json("FINAL_PACKAGE_LIFECYCLE_FILLABILITY_BRIDGE_SUMMARY.json", summary)
    write_jsonl("FINAL_PACKAGE_LIFECYCLE_FILLABILITY_SOURCE_LEDGER.jsonl", source_rows)
    write_jsonl("FINAL_PACKAGE_LIFECYCLE_SLEEVE_BRIDGE_LEDGER.jsonl", sleeve_bridge_rows)
    write_jsonl("FINAL_PACKAGE_LIFECYCLE_MEMBER_BRIDGE_LEDGER.jsonl", member_bridge_rows)
    write_jsonl("FINAL_PACKAGE_LIFECYCLE_LABEL_BRIDGE_LEDGER.jsonl", label_bridge_rows)
    write_jsonl("FINAL_PACKAGE_LIFECYCLE_CONTEXT_JOIN_LEDGER.jsonl", context_rows)
    write_jsonl("FINAL_PACKAGE_LIFECYCLE_SOURCE_GAP_LEDGER.jsonl", source_gap_rows)
    write_jsonl("FINAL_PACKAGE_LIFECYCLE_RESIDUAL_GATE_LEDGER.jsonl", residual_gate_rows)
    write_jsonl("DECISION_LEDGER.jsonl", decisions)
    write_json("COMPLETION_AUDIT.json", completion)
    write_json("OUTPUT_MANIFEST.json", manifest)
    write_json("FOCUSED_TEST_RESULT.json", focused)
    (ROUTE / "SATURATION_SELF_RED_TEAM.md").write_text(red_team, encoding="utf-8")
    write_json(
        "VERIFICATION_RESULT.json",
        {
            "schema": "gtos.final_moonshot.final_package_lifecycle_fillability_bridge.verification_result.v1",
            "verified_utc": generated_utc,
            "ok": False,
            "issue_count": 1,
            "issues": ["verifier_not_run_after_build"],
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
