from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"

STATE_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE}.jsonl"
CONFIG_PATH = REPO_ROOT / "config/agent_config.yaml"
STAGE08_MAP = ROUTE_DIR / f"VNEXT_REPLACEMENT_MARKET_SOURCE_ACTIVATION_MAP_{DATE}.json"

OUTPUT_DOSSIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_PRODUCTION_ACTIVATION_DOSSIER_{DATE}.md"
OUTPUT_OVERLAY = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONFIG_OVERLAY_DIFF_{DATE}.yaml"
OUTPUT_ROLLBACK = ROUTE_DIR / f"VNEXT_REPLACEMENT_ROLLBACK_RUNBOOK_{DATE}.md"
OUTPUT_DEMO = ROUTE_DIR / f"VNEXT_REPLACEMENT_DEMO_SHADOW_ACTIVATION_RUNBOOK_{DATE}.md"
OUTPUT_MONITORING = ROUTE_DIR / f"VNEXT_REPLACEMENT_MONITORING_CHECKLIST_{DATE}.md"
OUTPUT_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_ACTIVATION_DOSSIER_VERIFIER_{DATE}.json"

REQUIRED_MONITORING_SURFACES = [
    "vnext_apply_status",
    "router_decisions",
    "label_effects",
    "avoid_mixed_legacy_distribution_and_execution_effect",
    "dynamic_exit_transitions",
    "ltf_pending_monitor_health",
    "prop_budget_projection",
    "source_capture_completeness",
    "old_live_fallback_leakage",
    "malformed_ai_responses",
]

REQUIRED_DOC_PHRASES = {
    OUTPUT_DOSSIER: [
        "Stage 11 does not apply the production overlay",
        "activated_default_source_bound_primary",
        "What Replaces Old GTOS",
        "External Surface Handoff Fields",
        "Stage12 semantic verifier",
        "stale legacy deployment list",
    ],
    OUTPUT_ROLLBACK: [
        "Restore the current GTOS shadow/default-off behavior",
        "moonshot_dynamic_execution_router_apply_to_execution=false",
        "replacement_ml_apply_to_execution=false",
    ],
    OUTPUT_DEMO: [
        "demo-shadow only",
        "does not start `run_agent.py`",
        "External Handoff Required Before Runtime Startup",
    ],
    OUTPUT_MONITORING: [
        "Required Surfaces",
        "old_live_fallback_leakage",
        "source_capture_completeness",
        "Rollback Criteria",
    ],
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rel(path: Path | str) -> str:
    if isinstance(path, str):
        path = Path(path)
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _upsert_manifest_output(manifest: dict[str, Any], entry: dict[str, Any]) -> None:
    outputs = manifest.setdefault("outputs", [])
    for index, existing in enumerate(outputs):
        if existing.get("path") == entry["path"]:
            outputs[index] = {**existing, **entry}
            return
    outputs.append(entry)


def _append_control(row: dict[str, Any]) -> None:
    with CONTROL_LEDGER.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _append_test_result(state: dict[str, Any], command: str, result: str, timestamp: str) -> None:
    tests = state.setdefault("tests_verifiers_run", [])
    tests[:] = [row for row in tests if row.get("command") != command]
    tests.append({"command": command, "result": result, "timestamp_utc": timestamp})


def _nested_get(mapping: dict[str, Any], path: list[str]) -> Any:
    cursor: Any = mapping
    for part in path:
        if not isinstance(cursor, dict):
            return None
        cursor = cursor.get(part)
    return cursor


def _expect_flag(
    failures: list[str],
    mapping: dict[str, Any],
    path: list[str],
    expected: Any,
    label: str,
) -> None:
    actual = _nested_get(mapping, path)
    if actual != expected:
        failures.append(f"{label}={actual!r}, expected {expected!r}")


def main() -> int:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    failures: list[str] = []
    warnings: list[str] = []

    required_outputs = [
        OUTPUT_DOSSIER,
        OUTPUT_OVERLAY,
        OUTPUT_ROLLBACK,
        OUTPUT_DEMO,
        OUTPUT_MONITORING,
    ]
    for path in required_outputs:
        if not path.exists():
            failures.append(f"missing Stage11 output: {_rel(path)}")

    if failures:
        overlay: dict[str, Any] = {}
    else:
        overlay = yaml.safe_load(OUTPUT_OVERLAY.read_text(encoding="utf-8")) or {}

    state = _read_json(STATE_PATH)
    manifest = _read_json(MANIFEST_PATH)
    stage08 = _read_json(STAGE08_MAP)
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    runtime_cfg = config.get("gtos_vnext_runtime", {})

    if overlay.get("schema_version") != "vnext_replacement_stage11_config_overlay_diff_v2":
        failures.append("overlay schema_version mismatch")
    if overlay.get("repo_config_changed_by_stage11") is not False:
        failures.append("Stage11 overlay says repo config was changed")
    if overlay.get("application_state", {}).get("production_activation_overlay_applied_now") is not False:
        failures.append("Stage11 claims production activation overlay was applied")
    if overlay.get("application_state", {}).get("required_gate_before_application") != (
        "stage_12_final_semantic_verifier_status_passed"
    ):
        failures.append("Stage11 overlay missing Stage12 semantic gate")

    guardrails = overlay.get("input_guardrails", {})
    if int(guardrails.get("candidate_rows", 0)) != 253234:
        failures.append("overlay does not preserve 253,234 candidate rows")
    if int(guardrails.get("dynamic_policy_replay_rows", 0)) != 214536:
        failures.append("overlay does not preserve 214,536 dynamic policy rows")
    if float(guardrails.get("activated_default_source_bound_primary_expectancy_r", 0.0)) >= 0.0:
        failures.append("negative source-bound primary guard is not negative")
    if guardrails.get("activated_default_source_bound_primary_blocks_production_overlay") is not True:
        failures.append("negative source-bound primary guard does not block production overlay")
    if int(guardrails.get("stage09_paid_calls_made", -1)) != 0:
        failures.append("Stage11 overlay records paid AI/vendor calls")
    if guardrails.get("stage09_route_state_budget_cap_usd") is not None:
        failures.append("Stage11 overlay has non-null route budget cap")

    selected = overlay.get("selected_replacement", {})
    expected_selected = {
        "dynamic_execution_policy": "be_after_trigger",
        "primary_framework": "fvg_fill",
        "replaces": "live_current_j46_j49",
        "prop_policy_reference": "ACCOUNT_ABANDON_OR_RESTART",
        "prop_default_retained_over_condition_challenger": True,
    }
    for key, expected in expected_selected.items():
        if selected.get(key) != expected:
            failures.append(f"selected replacement {key}={selected.get(key)!r}, expected {expected!r}")

    _expect_flag(
        failures,
        overlay,
        ["demo_shadow_overlay", "config", "gtos_vnext_runtime", "apply_to_execution"],
        False,
        "demo shadow global apply",
    )
    _expect_flag(
        failures,
        overlay,
        [
            "demo_shadow_overlay",
            "config",
            "gtos_vnext_runtime",
            "moonshot_dynamic_execution_router_enabled",
        ],
        True,
        "demo shadow dynamic router enabled",
    )
    _expect_flag(
        failures,
        overlay,
        [
            "demo_shadow_overlay",
            "config",
            "gtos_vnext_runtime",
            "moonshot_dynamic_execution_router_apply_to_execution",
        ],
        False,
        "demo shadow dynamic apply",
    )

    prod_cfg = overlay.get("semantic_gated_production_activation_overlay_candidate", {}).get(
        "config", {}
    )
    for key in (
        "apply_to_execution",
        "pre_ai_apply_to_ai_call",
        "ai_policy_follow_no_ai_enabled",
        "ltf_path_execution_apply_to_execution",
        "prop_safe_selector_apply_to_execution",
        "moonshot_dynamic_execution_router_enabled",
        "moonshot_dynamic_execution_router_apply_to_execution",
    ):
        _expect_flag(
            failures,
            prod_cfg,
            ["gtos_vnext_runtime", key],
            True,
            f"production candidate {key}",
        )
    for key in (
        "ai_policy_apply_to_ai_call",
        "moonshot_dynamic_execution_router_condition_challenger_enabled",
        "replacement_ml_apply_to_execution",
        "exit_management_residue_apply_to_execution",
        "ready8_failure_control_residue_apply_to_execution",
    ):
        _expect_flag(
            failures,
            prod_cfg,
            ["gtos_vnext_runtime", key],
            False,
            f"production candidate {key}",
        )
    if (
        overlay.get("semantic_gated_production_activation_overlay_candidate", {})
        .get("deployment_phase_change")
        != "none_in_this_route_without_owner_account_runtime_start_approval"
    ):
        failures.append("production overlay must not change deployment phase inside Stage11")

    rollback_cfg = overlay.get("rollback_overlay", {}).get("config", {})
    for key in (
        "apply_to_execution",
        "pre_ai_apply_to_ai_call",
        "ai_policy_apply_to_ai_call",
        "ai_policy_follow_no_ai_enabled",
        "ltf_path_execution_apply_to_execution",
        "prop_safe_selector_apply_to_execution",
        "moonshot_dynamic_execution_router_enabled",
        "moonshot_dynamic_execution_router_apply_to_execution",
        "moonshot_dynamic_execution_router_condition_challenger_enabled",
        "replacement_ml_apply_to_execution",
    ):
        _expect_flag(failures, rollback_cfg, ["gtos_vnext_runtime", key], False, f"rollback {key}")
    _expect_flag(
        failures,
        rollback_cfg,
        ["gtos_vnext_runtime", "replacement_monitoring_enabled"],
        True,
        "rollback monitoring enabled",
    )

    current_expected_false = {
        "apply_to_execution": runtime_cfg.get("apply_to_execution"),
        "moonshot_dynamic_execution_router_enabled": runtime_cfg.get(
            "moonshot_dynamic_execution_router_enabled"
        ),
        "moonshot_dynamic_execution_router_apply_to_execution": runtime_cfg.get(
            "moonshot_dynamic_execution_router_apply_to_execution"
        ),
        "ltf_path_execution_apply_to_execution": runtime_cfg.get(
            "ltf_path_execution_apply_to_execution"
        ),
        "prop_safe_selector_apply_to_execution": runtime_cfg.get(
            "prop_safe_selector_apply_to_execution"
        ),
        "replacement_ml_apply_to_execution": runtime_cfg.get("replacement_ml_apply_to_execution"),
    }
    for key, actual in current_expected_false.items():
        if actual is not False:
            failures.append(f"repo config Stage11 should not apply {key}, actual={actual!r}")
    if runtime_cfg.get("replacement_monitoring_enabled") is not True:
        failures.append("repo config should keep replacement monitoring enabled")

    phase_rules = overlay.get("market_activation_phase_rules", {})
    stage08_eligible = stage08.get("broker_native_activation_eligible_symbols", [])
    stage08_pending = stage08.get("broker_native_pending_not_excluded_symbols", [])
    stage08_exact_excluded = stage08.get("broker_native_exact_excluded_symbols", [])
    if phase_rules.get("broker_native_live_feed_symbols", []) != stage08_eligible:
        failures.append("overlay broker-native live symbols do not match Stage08 onboarding eligibility")
    if phase_rules.get("broker_native_activation_eligible_symbols", []) != stage08_eligible:
        failures.append("overlay broker-native activation eligible symbols do not match Stage08")
    if phase_rules.get("broker_contract_verification_pending_not_excluded_symbols", []) != stage08_pending:
        failures.append("overlay pending-not-excluded symbols do not match Stage08")
    if phase_rules.get("broker_exact_excluded_symbols", []) != stage08_exact_excluded:
        failures.append("overlay exact broker exclusions do not match Stage08")
    if phase_rules.get("legacy_live_deployment_symbols_not_activation_ceiling", []) != stage08.get(
        "legacy_live_deployment_symbols_not_activation_ceiling", []
    ):
        failures.append("overlay legacy deployment non-ceiling list does not match Stage08")
    if int(phase_rules.get("excluded_until_broker_source_exists_count", -1)) != int(
        stage08["activation_status_counts"].get("excluded_until_broker_source_exists", 0)
    ):
        failures.append("overlay stale excluded_until_broker_source_exists count does not match Stage08")
    if int(phase_rules.get("proxy_context_excluded_count", -1)) != int(
        stage08["activation_status_counts"].get("proxy_context_excluded_from_broker_execution", 0)
    ):
        failures.append("overlay proxy-context excluded count does not match Stage08")
    if int(phase_rules.get("forward_capture_requirement_rows", 0)) != int(stage08["capture_requirement_rows"]):
        failures.append("overlay forward capture requirement rows does not match Stage08")
    if "broker-native MT5/redacted_account contract verification decides eligibility" not in str(
        phase_rules.get("market_source_invariant", "")
    ):
        failures.append("overlay missing market-source activation invariant")

    monitoring = overlay.get("monitoring", {})
    surfaces = monitoring.get("surfaces", [])
    if surfaces != REQUIRED_MONITORING_SURFACES:
        failures.append(f"overlay monitoring surfaces mismatch: {surfaces}")
    if monitoring.get("log_path") != "shadow_logs/gtos_vnext_replacement_monitoring.jsonl":
        failures.append("overlay monitoring log path mismatch")
    if monitoring.get("ml_apply_to_execution") is not False:
        failures.append("overlay monitoring allows ML execution effect")

    for path, phrases in REQUIRED_DOC_PHRASES.items():
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
            for phrase in phrases:
                if phrase not in text:
                    failures.append(f"{path.name} missing phrase: {phrase}")
    if OUTPUT_DOSSIER.exists():
        dossier_text = OUTPUT_DOSSIER.read_text(encoding="utf-8", errors="replace")
        for symbol in phase_rules.get("broker_native_live_feed_symbols", []):
            if f"| {symbol} |" not in dossier_text:
                failures.append(f"dossier market table missing broker symbol {symbol}")
    if OUTPUT_MONITORING.exists():
        monitoring_text = OUTPUT_MONITORING.read_text(encoding="utf-8", errors="replace")
        for surface in REQUIRED_MONITORING_SURFACES:
            if surface not in monitoring_text:
                failures.append(f"monitoring checklist missing surface {surface}")

    output_paths = {row.get("path"): row for row in manifest.get("outputs", [])}
    for path in required_outputs:
        entry = output_paths.get(path.name)
        if not entry:
            failures.append(f"manifest missing Stage11 output {path.name}")
        elif entry.get("status") != "created":
            failures.append(f"manifest Stage11 output {path.name} status={entry.get('status')!r}")

    if state.get("current_stage") == "stage_11_activation_dossier_and_config_overlay":
        failures.append("route state was reset to Stage11")
    if state.get("first_incomplete_invariant") == "stage_11_activation_dossier_and_config_overlay_pending":
        failures.append("route first incomplete invariant was reset to Stage11")
    if state.get("stage_status", {}).get("stage_11_activation_dossier_and_config_overlay") != (
        "completed_activation_package_written_overlay_not_applied_pending_semantic_verifier"
    ):
        failures.append("route state Stage11 status is not completed")
    if state.get("config_overlay_state", {}).get("production_activation_overlay_applied") is not False:
        failures.append("route state says production overlay was applied")

    evidence = state.get("evidence_rows_scanned", {})
    expected_evidence = {
        "stage11_activation_docs_written": 5,
        "stage11_overlay_sections": 5,
        "stage11_live_broker_symbols": len(stage08_eligible),
        "stage11_broker_pending_not_excluded_symbols": len(stage08_pending),
        "stage11_broker_exact_excluded_symbols": len(stage08_exact_excluded),
        "stage11_market_rows_consumed": 24,
        "stage11_activation_exclusion_rows_consumed": int(stage08["exclusion_rows"]),
        "stage11_monitoring_surfaces_consumed": 10,
        "stage11_ai_prompt_rows_consumed": 32,
    }
    for key, expected in expected_evidence.items():
        if evidence.get(key) != expected:
            failures.append(f"state evidence {key}={evidence.get(key)!r}, expected {expected!r}")

    if not failures:
        warnings.append(
            "production_overlay_remains_unapplied_until_stage12_semantic_verifier_passes"
        )
        warnings.append(
            "negative_default_source_bound_primary_guard_must_block_unrepaired_application"
        )

    status = "passed" if not failures else "failed"
    verifier = {
        "external_surface_state": {
            "broker_account_order_deal_position_history_mutation": "not_used",
            "live_trading": "not_used",
            "paid_api_or_vendor_model_calls": "not_used",
            "remote_push": "not_used",
        },
        "failures": failures,
        "generated_at_utc": generated_at,
        "input_hashes": {
            path.name: _sha256(path) for path in required_outputs if path.exists()
        },
        "negative_default_source_bound_primary_expectancy_r": guardrails.get(
            "activated_default_source_bound_primary_expectancy_r"
        ),
        "production_activation_overlay_applied": False,
        "route_id": ROUTE_ID,
        "schema_version": "vnext_replacement_stage11_activation_dossier_verifier_v2",
        "stage_id": "stage_11_activation_dossier_and_config_overlay",
        "status": status,
        "warnings": warnings,
    }
    _write_json(OUTPUT_VERIFIER, verifier)

    _upsert_manifest_output(
        manifest,
        {"path": OUTPUT_VERIFIER.name, "result": status, "stage": "stage_11", "status": "created"},
    )
    manifest["last_updated_utc"] = generated_at
    _write_json(MANIFEST_PATH, manifest)

    evidence = state.setdefault("evidence_rows_scanned", {})
    evidence["stage11_verifier_docs_scanned"] = len(required_outputs)
    evidence["stage11_verifier_monitoring_surfaces_scanned"] = len(REQUIRED_MONITORING_SURFACES)
    _append_test_result(state, _rel(Path(__file__)), status, generated_at)
    state["last_updated_utc"] = generated_at
    _write_json(STATE_PATH, state)

    _append_control(
        {
            "event": "stage_11_activation_dossier_verifier_completed",
            "generated_at_utc": generated_at,
            "production_activation_overlay_applied": False,
            "result": status,
            "route_id": ROUTE_ID,
            "stage_id": "stage_11_activation_dossier_and_config_overlay",
            "warnings": warnings,
        }
    )

    print(
        json.dumps(
            {
                "docs": len(required_outputs),
                "production_overlay_applied": False,
                "status": status,
                "warnings": warnings,
            },
            sort_keys=True,
        )
    )
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
