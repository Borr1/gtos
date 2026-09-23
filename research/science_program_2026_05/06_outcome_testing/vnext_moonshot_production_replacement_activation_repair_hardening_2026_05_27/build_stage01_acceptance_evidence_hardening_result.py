from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-27"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"
PRIOR_ROUTE_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_moonshot_production_replacement_activation_2026_05_26"
)

STAGE01_RESULT = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE01_ACCEPTANCE_HARDENING_RESULT_{DATE}.json"
SUBAGENT_FINDINGS = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_SUBAGENT_FINDINGS_{DATE}.json"
STAGE_SPINE = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE_SPINE_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_CONTROL_LEDGER_{DATE}.jsonl"


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _append_control(row: dict[str, Any]) -> None:
    with CONTROL_LEDGER.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _artifact(path_name: str) -> Path:
    return PRIOR_ROUTE_DIR / path_name


def main() -> int:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    machine_evidence = _read_json(_artifact("VNEXT_REPLACEMENT_STAGE13_MACHINE_TEST_EVIDENCE_2026-05-26.json"))
    manifest_result = _read_json(_artifact("VNEXT_REPLACEMENT_OUTPUT_MANIFEST_VERIFIER_2026-05-26.json"))
    route_state_result = _read_json(_artifact("VNEXT_REPLACEMENT_ROUTE_STATE_INTEGRITY_VERIFIER_2026-05-26.json"))
    completion_audit = _read_json(_artifact("VNEXT_REPLACEMENT_COMPLETION_AUDIT_2026-05-26.json"))
    final_semantic = _read_json(_artifact("VNEXT_REPLACEMENT_FINAL_SEMANTIC_VERIFICATION_RESULT_2026-05-26.json"))
    selector_summary = _read_json(_artifact("VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_SUMMARY_2026-05-26.json"))

    completed_gates = [
        {
            "evidence": [
                _rel(_artifact("test_vnext_replacement_stage12_semantic_verifier.py")),
                _rel(_artifact("VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_SUMMARY_2026-05-26.json")),
            ],
            "gate_id": "stage12_selected_count_truth",
            "status": "closed_artifact_derived_selector_assertion_and_negative_drift_test",
        },
        {
            "evidence": [
                _rel(_artifact("verify_vnext_replacement_stage12_semantic_red_team.py")),
                _rel(_artifact("test_vnext_replacement_stage12_semantic_verifier.py")),
            ],
            "gate_id": "stage12_semantic_exit_code",
            "status": "closed_nonzero_failure_exit_and_main_negative_path_test",
        },
        {
            "evidence": [_rel(_artifact("build_vnext_replacement_stage13_completion_audit.py"))],
            "gate_id": "stage13_completion_audit_result_ingestion",
            "status": "closed_hardcoded_pass_strings_removed_machine_result_ingestion_required",
        },
        {
            "evidence": [
                _rel(_artifact("verify_vnext_replacement_output_manifest.py")),
                _rel(_artifact("VNEXT_REPLACEMENT_OUTPUT_MANIFEST_VERIFIER_2026-05-26.json")),
            ],
            "gate_id": "manifest_hash_truth",
            "status": "closed_manifest_hashes_repaired_and_check_mode_passed",
        },
        {
            "evidence": [
                _rel(_artifact("verify_vnext_replacement_route_state_integrity.py")),
                _rel(_artifact("VNEXT_REPLACEMENT_ROUTE_STATE_INTEGRITY_VERIFIER_2026-05-26.json")),
            ],
            "gate_id": "route_state_head_integrity",
            "status": "closed_current_head_and_route_complete_contradiction_repaired",
        },
        {
            "evidence": [
                _rel(_artifact("verify_vnext_replacement_stage12_semantic_red_team.py")),
                _rel(_artifact("verify_vnext_replacement_output_manifest.py")),
            ],
            "gate_id": "non_mutating_check_mode",
            "status": "partially_closed_stage12_and_manifest_check_modes_non_mutating_remaining_verifiers_open",
        },
    ]

    open_gates_from_audits = [
        {
            "gate_id": "dynamic_pending_fill_persistence",
            "source": "subagent_execution_pending_fill_dynamic_policy_persistence",
            "status": "open_stage02_repair_required",
            "summary": "PendingLimitIntent lacks full placement-time dynamic fields; open_trade recomputes BE/target from fill-time config.",
        },
        {
            "gate_id": "execution_policy_support_matrix",
            "source": "subagent_execution_pending_fill_dynamic_policy_persistence",
            "status": "open_stage02_repair_required",
            "summary": "Unsupported challenger policies can be marked applied without live execution semantics.",
        },
        {
            "gate_id": "vnext_native_prescreen_news_parity",
            "source": "subagent_runtime_orchestrator_leakage_prescreen_news",
            "status": "open_stage02_repair_required",
            "summary": "Broader-origin path can return before old prescreen/news checks and needs vNext-native equivalents.",
        },
        {
            "gate_id": "fake_completion_dead_selector_gates",
            "source": "subagent_runtime_orchestrator_leakage_prescreen_news",
            "status": "open_stage02_repair_required",
            "summary": "Production replacement mode with disabled activation flags can fall through to old PrimaryAnalyzer/L2.",
        },
        {
            "gate_id": "canonical_frequency_executable_trade_ledger",
            "source": "subagent_frequency_prior_question_stack_consumption",
            "status": "open_stage04_build_required",
            "summary": "Current selector total recomputes as 60748 + 87814 + 125584 = 274146, but row-level membership layers are missing.",
        },
        {
            "gate_id": "prior_question_anatomy_consumption",
            "source": "subagent_frequency_prior_question_stack_consumption",
            "status": "open_stage04_build_required",
            "summary": "73001 closure rows exist as bookkeeping closure, not a production repair-intelligence ledger.",
        },
        {
            "gate_id": "broker_resolved_monitor_tick_parity",
            "source": "subagent_broker_risk_config_monitoring_alias_repair",
            "status": "open_stage03_repair_required",
            "summary": "scripts/_live_monitor_iter.py still hard-codes the old 7-symbol monitor/tick universe.",
        },
        {
            "gate_id": "broker_alias_repair_ger_oil",
            "source": "subagent_broker_risk_config_monitoring_alias_repair",
            "status": "open_stage03_repair_required",
            "summary": "GER40/UKOIL_cash/USOIL_cash exclusions remain stale until non-mutating MT5 alias verification for GER30/UKOUSD/USOUSD.",
        },
        {
            "gate_id": "redacted_account_risk_broker_geometry_current_specs",
            "source": "subagent_broker_risk_config_monitoring_alias_repair",
            "status": "open_stage03_repair_required",
            "summary": "redacted_account profile and risk geometry artifacts cover stale 21-valid/3-excluded universe.",
        },
    ]

    subagent_payload = {
        "generated_at_utc": generated_at,
        "returned_audits": [
            "acceptance_verifier_audit",
            "runtime_orchestrator_prescreen_news_leakage_audit",
            "execution_pending_fill_dynamic_policy_persistence_audit",
            "broker_risk_config_monitoring_alias_repair_audit",
            "frequency_prior_question_stack_consumption_audit",
        ],
        "still_pending_audits": [],
        "material_findings": open_gates_from_audits,
        "route_id": ROUTE_ID,
        "schema_version": "vnext_activation_repair_subagent_findings_v1",
    }
    _write_json(SUBAGENT_FINDINGS, subagent_payload)

    result = {
        "completed_gates": completed_gates,
        "completion_audit_status": completion_audit.get("completion_status"),
        "final_semantic_status": final_semantic.get("status"),
        "generated_at_utc": generated_at,
        "machine_evidence_status": machine_evidence.get("status"),
        "manifest_verifier_status": manifest_result.get("status"),
        "open_gates_from_audits": open_gates_from_audits,
        "route_id": ROUTE_ID,
        "route_state_verifier_status": route_state_result.get("status"),
        "schema_version": "vnext_activation_repair_stage01_acceptance_hardening_result_v1",
        "selector_anchor": {
            "broader_origin_selected_rows": selector_summary.get("broader_origin_selected_rows"),
            "combined_selected_rows": selector_summary.get("combined_selected_rows"),
            "old_three_selected_rows": selector_summary.get("old_three_selected_rows"),
            "total_r": selector_summary.get("combined_production_selector_metrics", {}).get("total_r"),
        },
        "status": "completed_stage01_acceptance_spine_partial_route_open",
    }
    _write_json(STAGE01_RESULT, result)

    spine = _read_json(STAGE_SPINE)
    spine["current_stage"] = "stage_02_runtime_path_hardening"
    spine["completed_gates"] = sorted(
        set(spine.get("completed_gates", []))
        | {row["gate_id"] for row in completed_gates}
    )
    still_open = [
        gate
        for gate in spine.get("open_gates", [])
        if gate not in {row["gate_id"] for row in completed_gates if not row["status"].startswith("partially")}
    ]
    for row in open_gates_from_audits:
        if row["gate_id"] not in still_open:
            still_open.append(row["gate_id"])
    spine["open_gates"] = still_open
    spine["latest_numbers"] = result["selector_anchor"]
    spine["latest_test_commands"] = machine_evidence.get("commands", [])
    spine["next_exact_action"] = (
        "Repair Stage02 runtime gates: vNext-native prescreen/news parity, no old PA/L2 fallback in production replacement mode, broader-origin zero-risk blocks, dynamic pending-fill persistence, and execution policy support matrix."
    )
    spine.setdefault("stage_status", {})[
        "stage_01_acceptance_and_evidence_hardening"
    ] = "completed_with_remaining_non_mutating_verifier_expansion"
    spine.setdefault("stage_status", {})[
        "stage_02_runtime_path_hardening"
    ] = "in_progress"
    spine["generated_at_utc"] = generated_at
    _write_json(STAGE_SPINE, spine)

    manifest = _read_json(OUTPUT_MANIFEST)
    outputs = manifest.setdefault("outputs", [])
    for path in [STAGE01_RESULT, SUBAGENT_FINDINGS, STAGE_SPINE]:
        rel_path = _rel(path)
        outputs[:] = [row for row in outputs if row.get("path") != rel_path]
        outputs.append(
            {
                "path": rel_path,
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
                "stage": "stage_01",
                "status": "created",
            }
        )
    manifest["last_updated_utc"] = generated_at
    manifest["status"] = "stage01_acceptance_hardening_recorded_route_open"
    _write_json(OUTPUT_MANIFEST, manifest)
    _append_control(
        {
            "completed_gate_count": len(completed_gates),
            "event": "stage01_acceptance_hardening_recorded",
            "generated_at_utc": generated_at,
            "open_gate_count_from_returned_audits": len(open_gates_from_audits),
            "route_id": ROUTE_ID,
            "status": result["status"],
        }
    )
    print(json.dumps({"status": result["status"], "completed_gates": len(completed_gates), "open_audit_gates": len(open_gates_from_audits)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
