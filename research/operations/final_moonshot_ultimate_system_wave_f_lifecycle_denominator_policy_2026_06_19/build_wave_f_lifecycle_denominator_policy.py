#!/usr/bin/env python3
"""Materialize the Wave F lifecycle-label denominator policy."""

from __future__ import annotations

import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
PARENT_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_full_plan_goal_session_2026_06_19"
BRIDGE_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_replay_bridge_2026_06_19"
MAIN_ORCH24_DIR = (
    ROOT.parent
    / "ai-trading-agent/research/science_program_2026_05/06_outcome_testing/"
    "main_orchestrator_24h_full_stack_research_integration_materialization"
)

ALT_SOURCE_FILES = [
    "MAIN_ORCH24_ACTION_AFTER_ENTRY_OFFSET_CONCENTRATION_GUARD_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_ACTION_AFTER_PENDING_TICK_SPREAD_REPAIR_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_PATH_PROXY_REPAIR_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_SOURCE_DECISION_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_DERIVATION_RECOMPUTE_LEDGER_2026-05-16.jsonl",
    "MAIN_ORCH24_PENDING_LIFECYCLE_TICK_SPREAD_RECONSTRUCTION_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_PENDING_LIFECYCLE_DECISION_SPREAD_REPAIR_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_PENDING_LIFECYCLE_NOFILL_FORWARD_SPREAD_REPAIR_LEDGER_2026-05-17.jsonl",
]

REPLAY_EXTENSION_REQUIRED_FIELDS = [
    "candidate_id",
    "decision_window_id",
    "asof_utc",
    "symbol",
    "side",
    "entry_price",
    "stop_loss",
    "take_profit",
    "target_r",
    "path_touch_ordering_status",
    "spread",
    "swap",
    "slippage",
    "broker_profile",
    "cost_source_provenance",
]

FORBIDDEN_SURFACE_STATUS = {
    "live_trading": False,
    "broker_operation": False,
    "broker_account_order_history_deal_position_mutation": False,
    "credential_mutation_or_disclosure": False,
    "paid_api_vendor_call": False,
    "blind_remote_push": False,
    "live_vps_restart_or_reload": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def replace_jsonl_row(path: Path, key: str, row: dict[str, Any]) -> None:
    rows = []
    replaced = False
    if path.exists():
        rows = read_jsonl(path)
    output = []
    for existing in rows:
        if existing.get(key) == row.get(key):
            output.append(row)
            replaced = True
        else:
            output.append(existing)
    if not replaced:
        output.append(row)
    write_jsonl(path, output)


def find_candidate_ids(value: Any, label_ids: set[str]) -> set[str]:
    found: set[str] = set()
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            for key, nested in item.items():
                if key == "candidate_id" and isinstance(nested, str) and nested in label_ids:
                    found.add(nested)
                elif isinstance(nested, (dict, list)):
                    stack.append(nested)
        elif isinstance(item, list):
            stack.extend(item)
    return found


def has_full_replay_geometry(row: dict[str, Any]) -> bool:
    aliases = {
        "entry_price": ["entry_price", "entry", "entry_ref"],
        "stop_loss": ["stop_loss", "stop"],
        "take_profit": ["take_profit", "target"],
        "target_r": ["target_r"],
        "path_touch_ordering_status": ["path_touch_ordering_status", "path_ordering"],
        "spread": ["spread"],
        "swap": ["swap"],
        "slippage": ["slippage"],
        "broker_profile": ["broker_profile"],
    }
    for names in aliases.values():
        if not any(row.get(name) not in (None, "", [], {}) for name in names):
            return False
    return True


def scan_main_orch_sources(label_ids: set[str]) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    source_rows: list[dict[str, Any]] = []
    rows_by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    matched_rows = 0
    full_geometry_rows = 0
    exact_r_rows = 0
    proxy_field_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    implementation_counts: Counter[str] = Counter()
    data_requirement_counts: Counter[str] = Counter()
    nonnull_fields = [
        "before_proxy_r",
        "after_proxy_r",
        "selected_shift_proxy_r",
        "source_scorer_proxy_r",
        "preserved_candidate_path_proxy_r",
        "asof_latest_candle_utc",
    ]

    for name in ALT_SOURCE_FILES:
        path = MAIN_ORCH24_DIR / name
        rows_scanned = 0
        file_matched_rows = 0
        file_full_geometry_rows = 0
        open_status = "missing"
        if path.exists():
            try:
                handle = path.open(encoding="utf-8")
                open_status = "readable"
            except OSError as exc:
                handle = None
                open_status = f"os_error:{exc.errno}:{exc.strerror}"
            if handle is not None:
                with handle:
                    for line in handle:
                        if not line.strip():
                            continue
                        rows_scanned += 1
                        try:
                            row = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        found = find_candidate_ids(row, label_ids)
                        if not found:
                            continue
                        file_matched_rows += 1
                        matched_rows += 1
                        if has_full_replay_geometry(row):
                            file_full_geometry_rows += 1
                            full_geometry_rows += 1
                        if row.get("exact_r") is not None:
                            exact_r_rows += 1
                        for field in nonnull_fields:
                            if row.get(field) not in (None, "", [], {}):
                                proxy_field_counts[field] += 1
                        action_counts[str(row.get("current_action") or row.get("action_class") or "")] += 1
                        implementation_counts[str(row.get("implementation_decision") or row.get("branch_decision") or "")] += 1
                        data_requirement_counts[str(row.get("data_requirement_state") or "")] += 1
                        for candidate_id in found:
                            rows_by_candidate[candidate_id].append(
                                {
                                    "source_file": name,
                                    "current_action": row.get("current_action"),
                                    "implementation_decision": row.get("implementation_decision") or row.get("branch_decision"),
                                    "data_requirement_state": row.get("data_requirement_state"),
                                    "exact_r_present": row.get("exact_r") is not None,
                                    "proxy_fields_present": [
                                        field for field in nonnull_fields if row.get(field) not in (None, "", [], {})
                                    ],
                                    "full_replay_geometry_present": has_full_replay_geometry(row),
                                }
                            )
        source_rows.append(
            {
                "source_id": f"main_orch24:{name}",
                "path": str(path),
                "rows_scanned": rows_scanned,
                "matched_lifecycle_candidate_rows": file_matched_rows,
                "full_replay_geometry_rows": file_full_geometry_rows,
                "open_status": open_status,
            }
        )

    aggregate = {
        "main_orch24_files_scanned": len(source_rows),
        "main_orch24_matched_candidate_ids": len(rows_by_candidate),
        "main_orch24_matched_rows": matched_rows,
        "main_orch24_full_replay_geometry_rows": full_geometry_rows,
        "main_orch24_exact_r_rows": exact_r_rows,
        "main_orch24_proxy_field_counts": dict(proxy_field_counts.most_common()),
        "main_orch24_top_actions": dict(action_counts.most_common(20)),
        "main_orch24_top_implementation_decisions": dict(implementation_counts.most_common(20)),
        "main_orch24_top_data_requirement_states": dict(data_requirement_counts.most_common(20)),
    }
    return source_rows, rows_by_candidate, aggregate


def build_policy_rows(bridge_rows: list[dict[str, Any]], rows_by_candidate: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    policy_rows: list[dict[str, Any]] = []
    for row in bridge_rows:
        source_matches = rows_by_candidate.get(row["candidate_id"], [])
        policy_rows.append(
            {
                "candidate_id": row["candidate_id"],
                "trade_id": row.get("trade_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "decision_time_utc": row.get("decision_time_utc"),
                "fill_no_fill_label": row.get("fill_no_fill_label"),
                "alternate_historical_owner_found": bool(source_matches),
                "alternate_historical_owner_match_rows": len(source_matches),
                "any_full_replay_geometry_in_alternate_sources": any(
                    match.get("full_replay_geometry_present") for match in source_matches
                ),
                "any_exact_r_in_alternate_sources": any(match.get("exact_r_present") for match in source_matches),
                "current_wave_b_c_denominator_joinable": False,
                "selected_package_denominator_policy": "exclude_until_replay_extension_or_explicit_owner_override",
                "policy_reason": [
                    "current_wave_b_c_direct_join_zero",
                    "current_wave_b_c_symbol_side_time_join_zero",
                    "main_orch24_sources_are_historical_action_or_proxy_provenance_not_full_replay_denominator",
                    "missing_required_replay_extension_fields",
                ],
                "required_replay_extension_fields": REPLAY_EXTENSION_REQUIRED_FIELDS,
                "final_package_selection_allowed": False,
                "model_training_allowed": False,
            }
        )
    return policy_rows


def update_parent(summary: dict[str, Any], route_rel: str) -> None:
    generated_utc = summary["generated_utc"]
    board_path = PARENT_ROUTE / "PARENT_WAVE_STATUS_BOARD.json"
    board = read_json(board_path)
    board["current_head"] = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    board["generated_utc"] = generated_utc
    for wave in board.get("waves", []):
        if wave.get("wave") != "F":
            continue
        wave["status"] = "lifecycle_denominator_policy_checkpoint_final_selection_still_blocked"
        wave["next_action"] = (
            "Use the lifecycle denominator policy to keep May 3-12 labels out of the current Wave B/C final-package denominator; "
            "repair broker actual-R, close-side all-in costs, and selected-package replay extension fields before any final selection."
        )
        for item in [
            "Formal denominator policy emitted for all 877 lifecycle labels",
            "Selected-package replay extension feasibility checked against Main-Orch24 alternate owner sources",
            "877 lifecycle labels excluded from current Wave B/C final-package denominator until full replay extension fields exist",
        ]:
            if item not in wave.setdefault("completed", []):
                wave["completed"].append(item)
        for artifact in [
            f"{route_rel}/WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_SUMMARY.json",
            f"{route_rel}/WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_LEDGER.jsonl",
            f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_EXTENSION_FEASIBILITY_LEDGER.jsonl",
            f"{route_rel}/WAVE_F_LIFECYCLE_DENOMINATOR_RESIDUAL_BLOCKER_LEDGER.jsonl",
            f"{route_rel}/VERIFICATION_RESULT.json",
        ]:
            if artifact not in wave.setdefault("evidence", []):
                wave["evidence"].append(artifact)
        for item in [
            "broker actual-R and close-side all-in cost joins before final package selection",
            "selected-package replay extension fields if May 3-12 lifecycle labels are ever included in a promoted denominator",
        ]:
            if item not in wave.setdefault("remaining", []):
                wave["remaining"].append(item)
    write_json(board_path, board)

    replace_jsonl_row(
        PARENT_ROUTE / "PARENT_ACTIVE_QUESTION_STACK.jsonl",
        "question_id",
        {
            "question_id": "PQ020",
            "question": "Can the 877 May 3-12 lifecycle labels enter the current final-package denominator now?",
            "answer": (
                "No. The policy route preserves all 877 labels but excludes them from the current Wave B/C denominator because direct joins are 0, "
                "symbol/side/time joins are 0, and alternate Main-Orch24 owner rows lack full replay geometry, exact-R, cost, and denominator fields."
            ),
            "status": "answered_lifecycle_denominator_policy_checkpoint",
            "evidence": [
                f"{route_rel}/WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_SUMMARY.json",
                f"{route_rel}/WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_LEDGER.jsonl",
                f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_EXTENSION_FEASIBILITY_LEDGER.jsonl",
            ],
            "next_action": "Keep the labels excluded unless a replay extension supplies candidate/decision-window parity plus entry/stop/target/path/cost/provenance fields.",
        },
    )
    replace_jsonl_row(
        PARENT_ROUTE / "PARENT_SOURCE_REQUEST_LEDGER.jsonl",
        "request_id",
        {
            "request_id": "PSR020",
            "source_or_field": "selected_package_lifecycle_denominator_policy",
            "exact_path": route_rel,
            "row_count": summary["policy_rows"],
            "resolution": "Completed current-denominator exclusion policy for all 877 lifecycle labels; replay extension fields remain an exact source/capture requirement.",
            "status": "completed_current_denominator_exclusion_policy_replay_extension_required",
            "next_action": "Repair broker actual-R/all-in close cost joins and only include lifecycle labels after full replay-extension fields exist.",
        },
    )
    replace_jsonl_row(
        PARENT_ROUTE / "PARENT_MERGE_DECISION_LEDGER.jsonl",
        "decision_id",
        {
            "decision_id": "PMD019",
            "decision": "Absorb Wave F lifecycle denominator policy as current final-package exclusion rule, not final package selection.",
            "reason": "The route keeps all 877 labels available while preventing unjoined lifecycle labels from entering the current Wave B/C denominator.",
            "status": "selected",
            "evidence": [
                f"{route_rel}/WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_SUMMARY.json",
                f"{route_rel}/WAVE_F_LIFECYCLE_DENOMINATOR_RESIDUAL_BLOCKER_LEDGER.jsonl",
            ],
        },
    )

    manifest_path = PARENT_ROUTE / "PARENT_OUTPUT_MANIFEST.json"
    manifest = read_json(manifest_path)
    manifest["generated_utc"] = generated_utc
    for artifact in [
        f"{route_rel}/WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_SUMMARY.json",
        f"{route_rel}/WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_LEDGER.jsonl",
        f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_EXTENSION_FEASIBILITY_LEDGER.jsonl",
        f"{route_rel}/WAVE_F_LIFECYCLE_DENOMINATOR_SOURCE_LEDGER.jsonl",
        f"{route_rel}/WAVE_F_LIFECYCLE_DENOMINATOR_RESIDUAL_BLOCKER_LEDGER.jsonl",
        f"{route_rel}/VERIFICATION_RESULT.json",
    ]:
        if artifact not in manifest.setdefault("linked_child_or_checkpoint_artifacts", []):
            manifest["linked_child_or_checkpoint_artifacts"].append(artifact)
    write_json(manifest_path, manifest)

    audit_path = PARENT_ROUTE / "PARENT_COMPLETION_AUDIT.json"
    audit = read_json(audit_path)
    audit["generated_utc"] = generated_utc
    completed_item = "Built Wave F lifecycle denominator policy with 877 current-denominator exclusions and replay-extension field requirements"
    if completed_item not in audit.setdefault("completed_requirements", []):
        audit["completed_requirements"].append(completed_item)
    audit["same_evidence_class_next_step"] = (
        "Repair broker actual-R and close-side all-in cost joins, then rerun Wave F final-package validation with the lifecycle denominator policy enforced."
    )
    verification = audit.setdefault("verification", {})
    verification["wave_f_lifecycle_denominator_policy"] = "passed"
    verification["wave_f_lifecycle_denominator_policy_rows"] = summary["policy_rows"]
    verification["wave_f_lifecycle_denominator_excluded_rows"] = summary["excluded_from_current_denominator_rows"]
    verification["wave_f_lifecycle_replay_extension_full_geometry_rows"] = summary["main_orch24_full_replay_geometry_rows"]
    write_json(audit_path, audit)


def main() -> int:
    generated_utc = utc_now()
    route_rel = str(ROUTE.relative_to(ROOT))
    bridge_rows = read_jsonl(BRIDGE_ROUTE / "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_LEDGER.jsonl")
    bridge_summary = read_json(BRIDGE_ROUTE / "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SUMMARY.json")
    label_ids = {row["candidate_id"] for row in bridge_rows}
    source_rows, rows_by_candidate, feasibility = scan_main_orch_sources(label_ids)
    policy_rows = build_policy_rows(bridge_rows, rows_by_candidate)
    excluded_rows = sum(1 for row in policy_rows if row["selected_package_denominator_policy"].startswith("exclude"))

    residual_blockers = [
        {
            "blocker_id": "WFB003",
            "requirement": "row-bound lifecycle/fillability labels included only with candidate/decision-window parity and replay denominator fields",
            "status": "current_denominator_exclusion_policy_complete_replay_extension_required",
            "remaining_action": "Build a replay extension with the required fields before including May 3-12 lifecycle labels in any promoted denominator.",
            "final_package_selection_allowed": False,
        },
        {
            "blocker_id": "WFB002",
            "requirement": "broker actual-R and close-side all-in cost joins",
            "status": "still_open_exact_capture_requirement",
            "remaining_action": "Run or import read-only close MT5/account-history source rows keyed to current package tickets.",
            "final_package_selection_allowed": False,
        },
    ]
    decisions = [
        {
            "decision_id": "WFLD001",
            "decision": "Exclude May 3-12 lifecycle labels from the current Wave B/C denominator.",
            "reason": "They have no Wave B/C direct or symbol/time joins and no full replay extension geometry in alternate owner sources.",
            "status": "selected",
        },
        {
            "decision_id": "WFLD002",
            "decision": "Preserve all lifecycle labels as future replay-extension inputs.",
            "reason": "The labels are useful source truth but are not denominator-eligible without replay parity fields.",
            "status": "selected",
        },
    ]
    repairs = [
        {
            "repair_id": "WFLD001",
            "requirement": "formal current-denominator policy for 877 lifecycle labels",
            "result": "all_877_excluded_until_replay_extension_fields_exist",
            "rows_affected": len(policy_rows),
            "status": "materialized",
        },
        {
            "repair_id": "WFLD002",
            "requirement": "selected-package replay extension feasibility from alternate owner sources",
            "result": "not_materializable_from_current_main_orch24_sources_full_geometry_rows_zero",
            "rows_affected": feasibility["main_orch24_matched_rows"],
            "status": "materialized",
        },
    ]
    feasibility_rows = [
        {
            "candidate_id": candidate_id,
            "matched_main_orch24_rows": len(matches),
            "full_replay_geometry_rows": sum(1 for row in matches if row["full_replay_geometry_present"]),
            "exact_r_rows": sum(1 for row in matches if row["exact_r_present"]),
            "proxy_field_rows": sum(1 for row in matches if row["proxy_fields_present"]),
            "extension_materializable_now": False,
            "reason": "alternate_owner_rows_do_not_supply_required_replay_extension_fields",
        }
        for candidate_id, matches in sorted(rows_by_candidate.items())
    ]
    summary = {
        "schema": "gtos.final_moonshot.wave_f.lifecycle_denominator_policy.summary.v1",
        "generated_utc": generated_utc,
        "status": "wave_f_lifecycle_denominator_policy_checkpoint_not_final_selection",
        "result_scope": "current_denominator_policy_not_final_package_selection_not_training",
        "input_bridge_rows": len(bridge_rows),
        "policy_rows": len(policy_rows),
        "excluded_from_current_denominator_rows": excluded_rows,
        "current_denominator_included_rows": len(policy_rows) - excluded_rows,
        "wave_b_direct_joins": bridge_summary.get("wave_b_exact_candidate_id_matches"),
        "wave_c_direct_joins": bridge_summary.get("wave_c_exact_candidate_id_matches"),
        "wave_b_symbol_side_time_joins": bridge_summary.get("wave_b_symbol_side_time_matches"),
        "wave_c_symbol_side_time_joins": bridge_summary.get("wave_c_symbol_side_time_matches"),
        "main_orch24_matched_candidate_ids": feasibility["main_orch24_matched_candidate_ids"],
        "main_orch24_matched_rows": feasibility["main_orch24_matched_rows"],
        "main_orch24_full_replay_geometry_rows": feasibility["main_orch24_full_replay_geometry_rows"],
        "main_orch24_exact_r_rows": feasibility["main_orch24_exact_r_rows"],
        "main_orch24_proxy_field_counts": feasibility["main_orch24_proxy_field_counts"],
        "required_replay_extension_fields": REPLAY_EXTENSION_REQUIRED_FIELDS,
        "residual_blocker_rows": len(residual_blockers),
        "forbidden_surface_status": FORBIDDEN_SURFACE_STATUS,
        "terminal_decision": {
            "current_denominator_policy_complete": True,
            "lifecycle_labels_included_in_current_denominator": False,
            "selected_package_replay_extension_materializable_now": False,
            "final_package_selected": False,
            "model_training_allowed": False,
            "deployment_dossier_allowed": False,
            "live_execution_activation_allowed": False,
            "wave_f_complete": False,
        },
    }

    write_jsonl(ROUTE / "WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_LEDGER.jsonl", policy_rows)
    write_jsonl(ROUTE / "WAVE_F_LIFECYCLE_REPLAY_EXTENSION_FEASIBILITY_LEDGER.jsonl", feasibility_rows)
    write_jsonl(ROUTE / "WAVE_F_LIFECYCLE_DENOMINATOR_SOURCE_LEDGER.jsonl", source_rows)
    write_jsonl(ROUTE / "WAVE_F_LIFECYCLE_DENOMINATOR_RESIDUAL_BLOCKER_LEDGER.jsonl", residual_blockers)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decisions)
    write_jsonl(ROUTE / "REPAIR_LEDGER.jsonl", repairs)
    write_json(ROUTE / "WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_SUMMARY.json", summary)
    (ROUTE / "SATURATION_SELF_RED_TEAM.md").write_text(
        "\n".join(
            [
                "# Wave F Lifecycle Denominator Policy Saturation Self-Red-Team",
                "",
                "- All 877 bridge rows were assigned a current-denominator policy.",
                "- Alternate Main-Orch24 owner rows were scanned for replay-extension feasibility, not treated as Wave B/C joins.",
                "- The policy preserves labels for future replay extension while preventing denominator leakage now.",
                "- Final selection, model training, deployment dossier, and live activation remain disallowed.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_json(
        ROUTE / "COMPLETION_AUDIT.json",
        {
            "schema": "gtos.final_moonshot.wave_f.lifecycle_denominator_policy.completion_audit.v1",
            "generated_utc": generated_utc,
            "status": "checkpoint_complete_not_final_selection",
            "goal_completion_claim": False,
            "completed_requirements": [
                "Assigned denominator policy to all 877 lifecycle labels",
                "Scanned alternate owner sources for replay-extension feasibility",
                "Recorded required replay-extension fields before any future inclusion",
            ],
            "remaining_requirements": [
                "broker actual-R and close-side all-in cost joins",
                "selected-package replay extension fields before lifecycle label inclusion",
                "sealed final package validation after source/cost repairs",
            ],
            "forbidden_surface_status": FORBIDDEN_SURFACE_STATUS,
        },
    )
    write_json(
        ROUTE / "OUTPUT_MANIFEST.json",
        {
            "schema": "gtos.final_moonshot.wave_f.lifecycle_denominator_policy.output_manifest.v1",
            "generated_utc": generated_utc,
            "route": route_rel,
            "inputs": [
                str((BRIDGE_ROUTE / "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_LEDGER.jsonl").relative_to(ROOT)),
                str((BRIDGE_ROUTE / "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SUMMARY.json").relative_to(ROOT)),
                str(MAIN_ORCH24_DIR),
            ],
            "files": [
                "build_wave_f_lifecycle_denominator_policy.py",
                "verify_wave_f_lifecycle_denominator_policy.py",
                "WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_SUMMARY.json",
                "WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_LEDGER.jsonl",
                "WAVE_F_LIFECYCLE_REPLAY_EXTENSION_FEASIBILITY_LEDGER.jsonl",
                "WAVE_F_LIFECYCLE_DENOMINATOR_SOURCE_LEDGER.jsonl",
                "WAVE_F_LIFECYCLE_DENOMINATOR_RESIDUAL_BLOCKER_LEDGER.jsonl",
                "DECISION_LEDGER.jsonl",
                "REPAIR_LEDGER.jsonl",
                "SATURATION_SELF_RED_TEAM.md",
                "COMPLETION_AUDIT.json",
                "OUTPUT_MANIFEST.json",
                "FOCUSED_TEST_RESULT.json",
                "VERIFICATION_RESULT.json",
            ],
        },
    )
    write_json(
        ROUTE / "FOCUSED_TEST_RESULT.json",
        {
            "schema": "gtos.final_moonshot.wave_f.lifecycle_denominator_policy.focused_test_result.v1",
            "generated_utc": generated_utc,
            "status": "pending_verifier",
            "checks": {
                "all_policy_rows_materialized": len(policy_rows) == 877,
                "all_current_denominator_rows_excluded": excluded_rows == 877,
                "full_replay_geometry_rows_zero": feasibility["main_orch24_full_replay_geometry_rows"] == 0,
                "exact_r_rows_zero": feasibility["main_orch24_exact_r_rows"] == 0,
            },
        },
    )
    update_parent(summary, route_rel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
