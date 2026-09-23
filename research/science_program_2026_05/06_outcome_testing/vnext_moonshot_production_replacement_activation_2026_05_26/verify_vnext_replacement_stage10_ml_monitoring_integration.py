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
RUNTIME_PATH = REPO_ROOT / "src/components/gtos_vnext_runtime.py"
ORCHESTRATOR_PATH = REPO_ROOT / "src/components/orchestrator.py"
TEST_PATH = REPO_ROOT / "tests/test_gtos_vnext_runtime.py"

OUTPUT_MAP = ROUTE_DIR / f"VNEXT_REPLACEMENT_ML_MONITORING_INTEGRATION_MAP_{DATE}.json"
OUTPUT_SCHEMA = ROUTE_DIR / f"VNEXT_REPLACEMENT_MONITORING_LOG_SCHEMA_{DATE}.json"
OUTPUT_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_ML_MONITORING_VERIFIER_{DATE}.json"

REQUIRED_ML_ROLES = [
    "ai_call_reducer",
    "source_confidence_scorer",
    "partition_robustness_scorer",
    "timeout_ambiguous_monitor",
    "drift_detector",
]

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

REQUIRED_SNAPSHOT_FIELDS = [
    "schema_version",
    "phase",
    "symbol",
    "kill_zone",
    "candle_time_utc",
    "vnext_apply_status",
    "router_decision",
    "label_effects",
    "execution_effects",
    "dynamic_exit_transition",
    "ltf_pending_monitor_health",
    "prop_budget_projection",
    "source_capture_completeness",
    "old_live_fallback_leakage",
    "ai_malformed_monitoring",
    "ml_assistant_roles",
    "warnings",
]

RUNTIME_NEEDLES = [
    "GTOSVNextReplacementMonitoringSnapshot",
    "build_vnext_replacement_monitoring_snapshot",
    "record_vnext_replacement_monitoring_snapshot",
    "attach_vnext_replacement_monitoring_to_record",
    "old_live_fallback_leakage",
    "malformed_response_summary",
    "ml_assistant_roles",
]

ORCHESTRATOR_NEEDLES = [
    "_record_gtos_vnext_replacement_monitoring",
    "post_l2_replacement_candidate",
    "post_l2_replacement_block",
]

TEST_NEEDLES = [
    "test_vnext_replacement_monitoring_snapshot_records_stage10_surfaces",
    "test_vnext_replacement_monitoring_flags_old_live_fallback_leakage",
    "replacement_monitoring_log_path",
]


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


def _source_presence(path: Path, needles: list[str]) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {needle: needle in text for needle in needles}


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


def _missing_true(presence: dict[str, bool]) -> list[str]:
    return sorted(key for key, present in presence.items() if not present)


def main() -> int:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    failures: list[str] = []
    warnings: list[str] = []

    integration_map = _read_json(OUTPUT_MAP)
    schema = _read_json(OUTPUT_SCHEMA)
    state = _read_json(STATE_PATH)
    manifest = _read_json(MANIFEST_PATH)
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    runtime_cfg = config.get("gtos_vnext_runtime", {})

    configured_roles = list(runtime_cfg.get("replacement_ml_role_keys", []))
    if configured_roles != REQUIRED_ML_ROLES:
        failures.append(f"config replacement_ml_role_keys mismatch: {configured_roles}")
    if integration_map.get("runtime_config", {}).get("replacement_ml_role_keys") != REQUIRED_ML_ROLES:
        failures.append("integration map replacement_ml_role_keys mismatch")

    expected_bool_flags = {
        "replacement_monitoring_enabled": True,
        "replacement_monitoring_log_enabled": True,
        "replacement_ml_apply_to_execution": False,
    }
    for key, expected in expected_bool_flags.items():
        actual = runtime_cfg.get(key)
        if actual is not expected:
            failures.append(f"config {key}={actual!r}, expected {expected!r}")
        map_actual = integration_map.get("runtime_config", {}).get(key)
        if map_actual is not expected:
            failures.append(f"integration map runtime_config {key}={map_actual!r}, expected {expected!r}")

    if runtime_cfg.get("replacement_monitoring_log_path") != "shadow_logs/gtos_vnext_replacement_monitoring.jsonl":
        failures.append("replacement monitoring log path changed from route schema expectation")
    if runtime_cfg.get("replacement_ml_role_source_manifest") != integration_map.get("input_artifacts", {}).get("ml_results", {}).get("path"):
        failures.append("ML role source manifest does not match integration-map ML input artifact")

    for role_key in REQUIRED_ML_ROLES:
        flag = f"replacement_ml_{role_key}_enabled"
        if runtime_cfg.get(flag) is not True:
            failures.append(f"config {flag} is not true")

    role_rows = integration_map.get("ml_role_modules", [])
    role_keys = [row.get("role_key") for row in role_rows]
    if role_keys != REQUIRED_ML_ROLES:
        failures.append(f"ML role module order/key mismatch: {role_keys}")
    for row in role_rows:
        role_key = row.get("role_key")
        if row.get("runtime_effect") != "monitor_only":
            failures.append(f"ML role {role_key} has non-monitor runtime effect")
        if row.get("apply_to_execution") is not False:
            failures.append(f"ML role {role_key} applies to execution")
        if not row.get("upstream_target"):
            failures.append(f"ML role {role_key} missing upstream target")
        if not row.get("upstream_disposition"):
            failures.append(f"ML role {role_key} missing upstream disposition")

    surfaces = [row.get("surface") for row in integration_map.get("monitoring_surfaces", [])]
    if surfaces != REQUIRED_MONITORING_SURFACES:
        failures.append(f"monitoring surface mismatch: {surfaces}")
    for row in integration_map.get("monitoring_surfaces", []):
        if row.get("runtime_effect") != "log_only":
            failures.append(f"monitoring surface {row.get('surface')} is not log_only")

    if schema.get("snapshot_required_fields") != REQUIRED_SNAPSHOT_FIELDS:
        failures.append("monitoring schema snapshot_required_fields mismatch")
    if schema.get("no_execution_effect") is not True:
        failures.append("monitoring schema must be no_execution_effect=true")
    if schema.get("log_path") != runtime_cfg.get("replacement_monitoring_log_path"):
        failures.append("monitoring schema log path does not match config")
    if integration_map.get("monitoring_log_schema", {}).get("sha256") != _sha256(OUTPUT_SCHEMA):
        failures.append("integration map schema sha256 mismatch")

    runtime_presence = _source_presence(RUNTIME_PATH, RUNTIME_NEEDLES)
    orchestrator_presence = _source_presence(ORCHESTRATOR_PATH, ORCHESTRATOR_NEEDLES)
    test_presence = _source_presence(TEST_PATH, TEST_NEEDLES)
    for label, presence in (
        ("runtime", runtime_presence),
        ("orchestrator", orchestrator_presence),
        ("tests", test_presence),
    ):
        missing = _missing_true(presence)
        if missing:
            failures.append(f"{label} missing Stage10 symbols: {missing}")

    map_presence = integration_map.get("runtime_presence", {})
    for path_key, expected_presence in (
        ("src/components/gtos_vnext_runtime.py", runtime_presence),
        ("src/components/orchestrator.py", orchestrator_presence),
        ("tests/test_gtos_vnext_runtime.py", test_presence),
    ):
        if map_presence.get(path_key) != expected_presence:
            failures.append(f"integration map source-presence mismatch for {path_key}")

    guardrails = integration_map.get("replay_guardrails", {})
    if int(guardrails.get("candidate_rows", 0)) != 253234:
        failures.append("Stage10 guardrails do not preserve the 253,234 candidate-row denominator")
    if int(guardrails.get("dynamic_policy_replay_rows", 0)) != 214536:
        failures.append("Stage10 guardrails do not preserve the 214,536 dynamic-policy replay rows")
    if float(guardrails.get("negative_default_source_bound_primary_expectancy_r", 0.0)) >= 0.0:
        failures.append("negative current default source-bound primary overlay guard is not negative")
    if guardrails.get("negative_default_source_bound_primary_blocks_overlay") is not True:
        failures.append("negative current default source-bound primary overlay is not marked as blocking")
    if int(guardrails.get("stage09_ai_prompt_rows", 0)) != 32:
        failures.append("Stage10 guardrails do not preserve Stage09 32-row AI prompt pack")
    if int(guardrails.get("paid_ai_or_vendor_calls_made", -1)) != 0:
        failures.append("Stage10 guardrails record paid AI/vendor calls")

    semantic_controls = integration_map.get("semantic_controls", {})
    for key in (
        "old_live_fallback_leakage_is_explicit_field",
        "source_missing_rows_require_capture_or_exclusion",
        "ml_live_control_blocked_until_sealed_validation",
        "malformed_ai_responses_are_supervised_not_silent",
        "monitoring_does_not_override_safety_gates",
    ):
        if semantic_controls.get(key) is not True:
            failures.append(f"semantic control {key} is not true")

    if integration_map.get("no_live_trading_or_broker_mutation") is not True:
        failures.append("Stage10 map does not assert no live/broker mutation")
    if integration_map.get("paid_api_or_vendor_calls_made") != 0:
        failures.append("Stage10 map records paid API/vendor calls")

    if state.get("current_stage") != "stage_11_activation_dossier_and_config_overlay":
        failures.append("route state did not advance to Stage11 after Stage10 builder")
    if state.get("first_incomplete_invariant") != "stage_11_activation_dossier_and_config_overlay_pending":
        failures.append("route state first incomplete invariant is not Stage11 pending")
    if state.get("stage_status", {}).get("stage_10_ml_and_monitoring_integration") != (
        "completed_ml_monitoring_map_runtime_schema_and_tests_written"
    ):
        failures.append("route state Stage10 status is not completed")
    if state.get("budget_cap_state", {}).get("route_state_budget_cap_usd") is not None:
        failures.append("route state budget cap is non-null")
    if state.get("budget_cap_state", {}).get("paid_ai_or_vendor_calls_allowed") is not False:
        failures.append("route state allows paid AI/vendor calls")

    evidence = state.get("evidence_rows_scanned", {})
    expected_evidence = {
        "stage10_ai_prompt_rows_consumed": 32,
        "stage10_log_schema_required_fields": len(REQUIRED_SNAPSHOT_FIELDS),
        "stage10_ml_role_rows": len(REQUIRED_ML_ROLES),
        "stage10_monitoring_surfaces": len(REQUIRED_MONITORING_SURFACES),
        "stage10_source_capture_rows_consumed": 33,
    }
    for key, expected in expected_evidence.items():
        if evidence.get(key) != expected:
            failures.append(f"state evidence {key}={evidence.get(key)!r}, expected {expected!r}")

    output_paths = {row.get("path") for row in manifest.get("outputs", [])}
    for required_path in (
        OUTPUT_MAP.name,
        OUTPUT_SCHEMA.name,
        "build_vnext_replacement_stage10_ml_monitoring_integration.py",
    ):
        if required_path not in output_paths:
            failures.append(f"output manifest missing {required_path}")

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
        "ledger_hashes": {
            OUTPUT_MAP.name: _sha256(OUTPUT_MAP),
            OUTPUT_SCHEMA.name: _sha256(OUTPUT_SCHEMA),
        },
        "ml_role_rows_scanned": len(role_rows),
        "monitoring_surfaces_scanned": len(surfaces),
        "required_snapshot_fields_scanned": len(REQUIRED_SNAPSHOT_FIELDS),
        "route_id": ROUTE_ID,
        "schema_version": "vnext_replacement_stage10_ml_monitoring_verifier_v1",
        "stage_id": "stage_10_ml_and_monitoring_integration",
        "status": status,
        "warnings": warnings,
    }
    _write_json(OUTPUT_VERIFIER, verifier)

    _upsert_manifest_output(
        manifest,
        {"path": OUTPUT_VERIFIER.name, "result": status, "stage": "stage_10", "status": "created"},
    )
    manifest["last_updated_utc"] = generated_at
    _write_json(MANIFEST_PATH, manifest)

    evidence["stage10_verifier_ml_role_rows_scanned"] = len(role_rows)
    evidence["stage10_verifier_monitoring_surfaces_scanned"] = len(surfaces)
    evidence["stage10_verifier_snapshot_fields_scanned"] = len(REQUIRED_SNAPSHOT_FIELDS)
    _append_test_result(state, _rel(Path(__file__)), status, generated_at)
    state["last_updated_utc"] = generated_at
    _write_json(STATE_PATH, state)

    _append_control(
        {
            "event": "stage_10_ml_monitoring_verifier_completed",
            "generated_at_utc": generated_at,
            "ml_role_rows": len(role_rows),
            "monitoring_surfaces": len(surfaces),
            "result": status,
            "route_id": ROUTE_ID,
            "stage_id": "stage_10_ml_and_monitoring_integration",
        }
    )

    print(
        json.dumps(
            {
                "ml_roles": len(role_rows),
                "monitoring_surfaces": len(surfaces),
                "status": status,
                "warnings": warnings,
            },
            sort_keys=True,
        )
    )
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
