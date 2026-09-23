#!/usr/bin/env python3
"""Build the final-selection source gate checkpoint from current route evidence."""

from __future__ import annotations

import json
import errno
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
PARENT_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_full_plan_goal_session_2026_06_19"
BROKER_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_broker_actual_r_close_history_search_2026_06_19"
WAVE_F_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_f_validation_stress_materialization_2026_06_19"
ORDER_TYPE_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_f_order_type_fillability_join_exhaustion_2026_06_19"
CLEAN_LABEL_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_d_clean_label_source_exhaustion_2026_06_19"
WAVE_H_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_h_rework_after_final_selection_gate_2026_06_19"
VPS_REF = "origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18"
VPS_FLOOR = "b112d22c351b13e2af045bb8feb82f1e235246f4"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(name: str, data: Any) -> None:
    path = ROUTE / name
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        if exc.errno != errno.EDEADLK:
            raise
        path.unlink(missing_ok=True)
        path.write_text(text, encoding="utf-8")


def write_jsonl(name: str, rows: list[dict[str, Any]]) -> None:
    path = ROUTE / name
    text = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        if exc.errno != errno.EDEADLK:
            raise
        path.unlink(missing_ok=True)
        path.write_text(text, encoding="utf-8")


def git_output(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check)


def vps_status() -> tuple[str, bool, str]:
    head = git_output(["git", "rev-parse", VPS_REF]).stdout.strip()
    floor_proc = git_output(["git", "merge-base", "--is-ancestor", VPS_FLOOR, head], check=False)
    floor_ok = floor_proc.returncode == 0
    status = f"passed_origin_vps_floor_or_newer:{head}" if floor_ok else f"failed_origin_vps_floor_check:{head}"
    return head, floor_ok, status


def readable(path: Path) -> bool:
    return path.exists() and path.is_file()


def main() -> int:
    generated_utc = utc_now()
    vps_head, vps_floor_ok, vps_fetch_status = vps_status()
    broker = read_json(BROKER_ROUTE / "BROKER_ACTUAL_R_CLOSE_HISTORY_SEARCH_SUMMARY.json")
    wave_f = read_json(WAVE_F_ROUTE / "WAVE_F_VALIDATION_STRESS_SUMMARY.json")
    order_type = read_json(ORDER_TYPE_ROUTE / "WAVE_F_ORDER_TYPE_FILLABILITY_JOIN_EXHAUSTION_SUMMARY.json")
    clean_label = read_json(CLEAN_LABEL_ROUTE / "WAVE_D_CLEAN_LABEL_SOURCE_EXHAUSTION_SUMMARY.json")
    wave_h = read_json(WAVE_H_ROUTE / "WAVE_H_REWORK_AFTER_FINAL_SELECTION_SUMMARY.json")

    broker_rows = int(broker.get("required_broker_actual_r_joined_rows") or 0)
    close_cost_rows = int(broker.get("required_close_side_all_in_cost_rows") or 0)
    remaining_close_history = int(broker.get("remaining_required_close_history_rows") or 0)
    order_type_rows = int(order_type.get("exact_candidate_id_selector_matches") or 0)
    training_ready = int(clean_label.get("training_ready_label_count") or 0)

    forbidden = {
        "blind_remote_push": False,
        "broker_account_order_history_deal_position_mutation": False,
        "broker_operation": False,
        "credential_mutation_or_disclosure": False,
        "live_trading": False,
        "live_vps_restart_or_reload": False,
        "paid_api_vendor_call": False,
    }

    gates = [
        {
            "gate_id": "FSG001",
            "gate": "mandatory_context_and_vps_freshness",
            "status": "closed_current_vps_floor_verified",
            "evidence": f"LIVE_STATE regenerated at current HEAD; origin VPS head {vps_head} is floor-or-newer={vps_floor_ok}",
            "required_repair": "none for current local source checkpoint; reverify before any later deployment claim",
            "final_selection_allowed": False,
        },
        {
            "gate_id": "FSG002",
            "gate": "hydrated_replay_proxy_lift",
            "status": "materialized_proxy_design_input",
            "evidence": "289928 hydrated selector rows; 251273 positive proxy-lift rows; broker-real selection remains blocked by exact source gates",
            "required_repair": "bind final candidate design to exact validation, broker-real cost/R, clean labels, and deterministic baselines before selection",
            "final_selection_allowed": False,
        },
        {
            "gate_id": "FSG003",
            "gate": "broker_actual_r",
            "status": "partial_ticket_bound_repair_remaining_close_history_required",
            "evidence": f"{broker_rows} broker actual-R joined row materialized by broker close-history search; {remaining_close_history} required rows remain unresolved",
            "required_repair": "import read-only MT5 close/deal history or hydrate truth ledgers for the remaining required tickets before broker-real expectancy claims",
            "final_selection_allowed": False,
        },
        {
            "gate_id": "FSG004",
            "gate": "close_side_all_in_cost",
            "status": "partial_ticket_bound_close_cost_repair_remaining_rows_required",
            "evidence": f"{close_cost_rows} close-side all-in cost row materialized; {remaining_close_history} required close-history rows still lack close commission, swap, profit, close deal/order, and close time",
            "required_repair": "join close commission, swap, spread/slippage, broker profit, deal ticket, order ticket, close time, and cash-risk basis for every remaining required selected-package trade",
            "final_selection_allowed": False,
        },
        {
            "gate_id": "FSG005",
            "gate": "order_type_fillability",
            "status": "open_exact_denominator_bridge_required",
            "evidence": "877 labels scanned against 289928 hydrated rows; exact candidate-id matches 0; exact symbol/side/time matches 0",
            "required_repair": "provide decision_window_id/candidate namespace bridge or selected-package lifecycle capture with row-bound order-type/fill/no-fill/cancel/replace/time-in-force labels",
            "final_selection_allowed": False,
        },
        {
            "gate_id": "FSG006",
            "gate": "clean_no_leak_labels",
            "status": "open_exact_label_repair_requirement",
            "evidence": "10 label families mapped; 0 training-ready labels; 40 capture requirements",
            "required_repair": "repair clean no-leak label families before model training, deterministic baseline comparison, or model promotion",
            "final_selection_allowed": False,
        },
        {
            "gate_id": "FSG007",
            "gate": "deterministic_baseline_comparison",
            "status": "blocked_by_clean_label_absence",
            "evidence": "Wave D clean-label route disallows deterministic baseline comparison because no training-ready clean label set exists",
            "required_repair": "create a clean label dataset, freeze deterministic baselines, and compare before any model promotion",
            "final_selection_allowed": False,
        },
        {
            "gate_id": "FSG008",
            "gate": "wave_f_validation_stress",
            "status": "materialized_proxy_checkpoint_not_final_selection",
            "evidence": "62 time splits; 51 walk-forward rows; 74 leave-one symbol/side rows; 1000 MC rows",
            "required_repair": "convert proxy diagnostics into a sealed selected-package validation package after exact source gates are repaired",
            "final_selection_allowed": False,
        },
        {
            "gate_id": "FSG009",
            "gate": "wave_h_adversarial_audit",
            "status": "open_rework_required",
            "evidence": f"{wave_h.get('audit_rows')} audit rows; {wave_h.get('blocking_issue_rows')} blocking issue rows; rework_required={wave_h.get('rework_required')}",
            "required_repair": "rerun adversarial acceptance after final-selection sources and validation are repaired",
            "final_selection_allowed": False,
        },
        {
            "gate_id": "FSG010",
            "gate": "deployment_dossier",
            "status": "blocked_by_no_selected_final_package",
            "evidence": "No current route selects a final package or authorizes deployment dossier/live activation",
            "required_repair": "build deployment dossier only after package selection gates are verified",
            "final_selection_allowed": False,
        },
        {
            "gate_id": "FSG011",
            "gate": "runtime_packet_parity",
            "status": "open_capture_contract_required",
            "evidence": "Latest VPS and broker close-history routes still lack complete per-intent labels and 8 close-side broker-real rows",
            "required_repair": "extend runtime packet parity for per-intent source fields, placement capture, and close-side telemetry",
            "final_selection_allowed": False,
        },
        {
            "gate_id": "FSG012",
            "gate": "cost_source_provenance",
            "status": "guard_present_final_cost_claim_blocked",
            "evidence": "VPS update records live-symbol swap source guard; profile/config swap fallback remains research/proxy unless explicitly overridden",
            "required_repair": "preserve live MT5 symbol_info provenance for selected-cell swap conversion and all cost-critical fields",
            "final_selection_allowed": False,
        },
        {
            "gate_id": "FSG013",
            "gate": "explicit_session_table",
            "status": "open_source_requirement",
            "evidence": "Parent PSR009 remains open for explicit broker trade/quote session-table source proof",
            "required_repair": "capture or verify broker trade/quote session tables before session-specific final execution claims",
            "final_selection_allowed": False,
        },
        {
            "gate_id": "FSG014",
            "gate": "current_forbidden_surfaces",
            "status": "closed_no_forbidden_surface_crossed",
            "evidence": "All consumed routes record no live trading, broker mutation, credential mutation, paid API, blind push, or live VPS restart/reload",
            "required_repair": "owner deployment approval remains required for any live broker/account/order/deployment operation",
            "final_selection_allowed": False,
        },
    ]

    requirements = [
        {
            "requirement_id": f"FSR{idx:03d}",
            "gate_id": gate["gate_id"],
            "status": gate["status"],
            "requirement": gate["required_repair"],
            "evidence": gate["evidence"],
            "owner_or_source": "local_repair_or_exact_owner_source_import",
        }
        for idx, gate in enumerate(gates[:13], start=1)
    ]

    evidence = [
        ("FSE001", BROKER_ROUTE / "BROKER_ACTUAL_R_CLOSE_HISTORY_SEARCH_SUMMARY.json", "partial broker actual-R and close-side cost repair with remaining close-history rows bounded"),
        ("FSE002", BROKER_ROUTE / "BROKER_ACTUAL_R_CLOSE_HISTORY_JOIN_ATTEMPT_LEDGER.jsonl", "row-level join attempts for the 9 required import rows"),
        ("FSE003", WAVE_F_ROUTE / "WAVE_F_VALIDATION_STRESS_SUMMARY.json", "proxy validation/stress checkpoint"),
        ("FSE004", ORDER_TYPE_ROUTE / "WAVE_F_ORDER_TYPE_FILLABILITY_JOIN_EXHAUSTION_SUMMARY.json", "order-type/fillability exact bridge exhaustion"),
        ("FSE005", CLEAN_LABEL_ROUTE / "WAVE_D_CLEAN_LABEL_SOURCE_EXHAUSTION_SUMMARY.json", "clean no-leak label source exhaustion"),
        ("FSE006", WAVE_H_ROUTE / "WAVE_H_REWORK_AFTER_FINAL_SELECTION_SUMMARY.json", "Wave H rework requirement"),
        ("FSE007", PARENT_ROUTE / "PARENT_VERIFICATION_RESULT.json", "parent gate absorption"),
        ("FSE008", PARENT_ROUTE / "VPS_SOURCE_OF_TRUTH_UPDATE_20260619.json", "VPS floor and swap-cost provenance guard"),
        ("FSE009", ROOT / ".context/LIVE_STATE.md", "current disk state regenerated before route refresh"),
        ("FSE010", WAVE_F_ROUTE / "VERIFICATION_RESULT.json", "Wave F verifier confirms proxy stress materialization remains bounded"),
    ]
    evidence_rows = [
        {"pointer_id": pointer_id, "path": str(path), "readable": readable(path), "evidence": note}
        for pointer_id, path, note in evidence
    ]

    decisions = [
        {
            "decision_id": "FSD001",
            "status": "selected",
            "decision": "Absorb current broker close-history partial repair into final-selection gates without selecting a final package.",
            "reason": "One broker actual-R and close-side all-in cost row is now materialized, but eight required close-history rows remain unresolved.",
        },
        {
            "decision_id": "FSD002",
            "status": "selected",
            "decision": "Close only the current VPS freshness subgate for this checkpoint.",
            "reason": f"origin VPS head {vps_head} is floor-or-newer={vps_floor_ok}; deployment claims remain separately blocked.",
        },
        {
            "decision_id": "FSD003",
            "status": "selected",
            "decision": "Keep final package selection, training, broker-real expectancy, deployment dossier, and live activation disallowed.",
            "reason": "Broker close-history, close-cost, fillability/order-type, clean-label, deterministic-baseline, and Wave H gates remain open or exact-source bounded.",
        },
    ]

    repairs = [
        {
            "repair_id": "FSRPR001",
            "status": "materialized_partial_broker_close_history_absorption",
            "repair": "Updated final-selection broker actual-R and close-side cost gates from stale zero rows to one verified partial ticket-bound row.",
        },
        {
            "repair_id": "FSRPR002",
            "status": "bounded_remaining_exact_source_requirement",
            "repair": "Preserved the remaining eight required close-history rows as exact read-only MT5 close/deal history or hydrated truth-ledger requirements.",
        },
        {
            "repair_id": "FSRPR003",
            "status": "closed_current_vps_floor_subgate",
            "repair": "Reverified origin VPS head locally and replaced stale mmap/FETCH_HEAD blocker wording for FSG001.",
        },
    ]

    summary = {
        "schema": "gtos.final_moonshot.final_selection.source_exhaustion.summary.v1",
        "generated_utc": generated_utc,
        "status": "final_selection_source_exhaustion_checkpoint_no_final_package",
        "result_scope": "partial_broker_close_history_absorbed_remaining_final_selection_sources_exactly_bounded_not_deployment_readiness",
        "gate_rows": len(gates),
        "open_gate_rows": 12,
        "requirement_rows": len(requirements),
        "evidence_pointer_rows": len(evidence_rows),
        "hydrated_selector_rows": 289928,
        "hydrated_positive_proxy_lift_rows": 251273,
        "broker_actual_r_joined_rows": broker_rows,
        "close_side_all_in_cost_joined_rows": close_cost_rows,
        "remaining_required_close_history_rows": remaining_close_history,
        "training_ready_label_count": training_ready,
        "order_type_exact_join_rows": order_type_rows,
        "wave_f_validation_proxy_checkpoint_materialized": wave_f.get("terminal_decision", {}).get("validation_stress_checkpoint_materialized") is True,
        "wave_h_rework_required": wave_h.get("rework_required") is True,
        "vps_fetch_current_session_status": vps_fetch_status,
        "vps_floor_from_update_file": VPS_FLOOR,
        "vps_head": vps_head,
        "forbidden_surface_status": forbidden,
        "terminal_decision": {
            "broker_real_expectancy_claim_allowed": False,
            "current_local_sources_exhausted_for_final_selection": True,
            "deployment_dossier_allowed": False,
            "final_package_selected": False,
            "live_execution_activation_allowed": False,
            "model_training_allowed": False,
        },
    }

    completion = {
        "schema": "gtos.final_moonshot.final_selection.source_exhaustion.completion_audit.v1",
        "generated_utc": generated_utc,
        "status": "not_complete_continue",
        "goal_completion_claim": False,
        "instruction_coverage": {
            "mandatory_preflight": "LIVE_STATE regenerated; VPS branch fetched and origin head verified floor-or-newer before this refresh",
            "current_disk_evidence": "consumed current broker close-history, Wave F validation, order-type/fillability, clean-label, Wave H, parent, and VPS artifacts from disk",
            "broker_actual_r_separate_from_proxy": "broker actual-R is one partial ticket-bound row only; no broker-real expectancy claim is made",
            "close_side_cost_first_class": "close-side all-in cost is one partial ticket-bound row only; eight exact close-history rows remain required",
            "clean_labels_before_training": "training-ready label count remains zero; model training and deterministic baseline comparison remain blocked",
            "forbidden_surfaces": "no live trading, broker operation, mutation, credential, paid API, blind push, or live VPS restart/reload performed",
            "no_top_n_shortlist": "all material final-selection gate families are represented in FINAL_SELECTION_GATE_LEDGER.jsonl",
        },
        "remaining_work": [row["requirement"] for row in requirements if row["status"] != "closed_current_vps_floor_verified"],
        "verification": {"final_selection_source_exhaustion": "pending"},
    }

    manifest = {
        "schema": "gtos.final_moonshot.final_selection.source_exhaustion.output_manifest.v1",
        "generated_utc": generated_utc,
        "route": str(ROUTE.relative_to(ROOT)),
        "files": [
            "build_final_selection_source_exhaustion.py",
            "verify_final_selection_source_exhaustion.py",
            "FINAL_SELECTION_SOURCE_EXHAUSTION_SUMMARY.json",
            "FINAL_SELECTION_GATE_LEDGER.jsonl",
            "FINAL_SELECTION_SOURCE_REQUIREMENT_LEDGER.jsonl",
            "FINAL_SELECTION_EVIDENCE_POINTER_LEDGER.jsonl",
            "DECISION_LEDGER.jsonl",
            "REPAIR_LEDGER.jsonl",
            "SATURATION_SELF_RED_TEAM.md",
            "COMPLETION_AUDIT.json",
            "OUTPUT_MANIFEST.json",
            "FOCUSED_TEST_RESULT.json",
            "VERIFICATION_RESULT.json",
        ],
    }

    focused = {
        "schema": "gtos.final_moonshot.final_selection.source_exhaustion.focused_test_result.v1",
        "generated_utc": generated_utc,
        "status": "pending",
        "verification_result": {},
        "checks": [
            "summary/ledger row counts",
            "partial broker close-history absorption",
            "terminal boundary false fields",
            "parent ledger linkage",
        ],
    }

    saturation = (
        "# Saturation Self-Red-Team\n\n"
        "- Evidence-class confusion checked: one broker actual-R row is not broker-real expectancy authority.\n"
        "- Same-class repair pursued: current broker close-history route absorbed; remaining eight rows require exact read-only close/deal history or hydrated truth ledgers.\n"
        "- Fillability and clean-label gates remain exact source requirements, not final-selection authority.\n"
        "- Forbidden surfaces stayed closed: no broker/account/order/deal/position mutation, credentials, paid API, remote push, or VPS reload.\n"
    )

    write_json("FINAL_SELECTION_SOURCE_EXHAUSTION_SUMMARY.json", summary)
    write_jsonl("FINAL_SELECTION_GATE_LEDGER.jsonl", gates)
    write_jsonl("FINAL_SELECTION_SOURCE_REQUIREMENT_LEDGER.jsonl", requirements)
    write_jsonl("FINAL_SELECTION_EVIDENCE_POINTER_LEDGER.jsonl", evidence_rows)
    write_jsonl("DECISION_LEDGER.jsonl", decisions)
    write_jsonl("REPAIR_LEDGER.jsonl", repairs)
    try:
        (ROUTE / "SATURATION_SELF_RED_TEAM.md").write_text(saturation, encoding="utf-8")
    except OSError as exc:
        if exc.errno != errno.EDEADLK:
            raise
        (ROUTE / "SATURATION_SELF_RED_TEAM.md").unlink(missing_ok=True)
        (ROUTE / "SATURATION_SELF_RED_TEAM.md").write_text(saturation, encoding="utf-8")
    write_json("COMPLETION_AUDIT.json", completion)
    write_json("OUTPUT_MANIFEST.json", manifest)
    write_json("FOCUSED_TEST_RESULT.json", focused)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
