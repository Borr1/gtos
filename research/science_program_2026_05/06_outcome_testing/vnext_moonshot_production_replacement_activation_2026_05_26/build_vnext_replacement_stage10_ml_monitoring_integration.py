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

STAGE03_CONTRACT = ROUTE_DIR / f"VNEXT_REPLACEMENT_PRODUCTION_CANDIDATE_CONTRACT_{DATE}.json"
STAGE05_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SUMMARY_{DATE}.json"
STAGE05_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_VERIFIER_{DATE}.json"
STAGE06_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_VERIFIER_{DATE}.json"
STAGE08_CAPTURE = ROUTE_DIR / f"VNEXT_REPLACEMENT_SOURCE_CAPTURE_REQUIREMENTS_{DATE}.jsonl"
STAGE09_MANIFEST = ROUTE_DIR / f"VNEXT_REPLACEMENT_AI_CALIBRATION_MANIFEST_{DATE}.json"
ML_RESULTS = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26/"
    / f"VNEXT_ACTIVATION_ML_CHALLENGER_RESULTS_{DATE}.json"
)

OUTPUT_MAP = ROUTE_DIR / f"VNEXT_REPLACEMENT_ML_MONITORING_INTEGRATION_MAP_{DATE}.json"
OUTPUT_SCHEMA = ROUTE_DIR / f"VNEXT_REPLACEMENT_MONITORING_LOG_SCHEMA_{DATE}.json"

REQUIRED_ML_ROLES = [
    "ai_call_reducer",
    "source_confidence_scorer",
    "partition_robustness_scorer",
    "timeout_ambiguous_monitor",
    "drift_detector",
]

MONITORING_SURFACES = [
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

SNAPSHOT_REQUIRED_FIELDS = [
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


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl_count(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


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


def _source_presence(path: Path, needles: list[str]) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {needle: needle in text for needle in needles}


def main() -> int:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    runtime_cfg = config["gtos_vnext_runtime"]
    stage03 = _read_json(STAGE03_CONTRACT)
    stage05 = _read_json(STAGE05_SUMMARY)
    stage05_verifier = _read_json(STAGE05_VERIFIER)
    stage06_verifier = _read_json(STAGE06_VERIFIER)
    stage09 = _read_json(STAGE09_MANIFEST)
    ml_results = _read_json(ML_RESULTS)
    source_capture_rows = _read_jsonl_count(STAGE08_CAPTURE)
    state = _read_json(STATE_PATH)
    manifest = _read_json(MANIFEST_PATH)

    configured_roles = list(runtime_cfg.get("replacement_ml_role_keys", []))
    if configured_roles != REQUIRED_ML_ROLES:
        raise RuntimeError(f"replacement ML role keys mismatch: {configured_roles}")

    schema = {
        "route_id": ROUTE_ID,
        "schema_version": "vnext_replacement_stage10_monitoring_log_schema_v1",
        "generated_at_utc": generated_at,
        "log_path": runtime_cfg["replacement_monitoring_log_path"],
        "top_level_required_fields": ["schema_version", "timestamp_utc", "snapshot"],
        "snapshot_required_fields": SNAPSHOT_REQUIRED_FIELDS,
        "surface_to_snapshot_field": {
            "vnext_apply_status": "vnext_apply_status",
            "router_decisions": "router_decision",
            "label_effects": "label_effects",
            "avoid_mixed_legacy_distribution_and_execution_effect": "label_effects",
            "dynamic_exit_transitions": "dynamic_exit_transition",
            "ltf_pending_monitor_health": "ltf_pending_monitor_health",
            "prop_budget_projection": "prop_budget_projection",
            "source_capture_completeness": "source_capture_completeness",
            "old_live_fallback_leakage": "old_live_fallback_leakage",
            "malformed_ai_responses": "ai_malformed_monitoring",
        },
        "no_execution_effect": True,
    }
    _write_json(OUTPUT_SCHEMA, schema)

    ml_role_modules = []
    upstream_roles = {
        str(row.get("role")): row
        for row in ml_results.get("model_role_results", [])
        if isinstance(row, dict)
    }
    role_to_upstream_name = {
        "ai_call_reducer": "ML AI-call reducer",
        "source_confidence_scorer": "ML source-confidence scorer",
        "partition_robustness_scorer": "ML partition robustness scorer",
        "timeout_ambiguous_monitor": "ML timeout/ambiguous monitor",
        "drift_detector": "ML drift detector",
    }
    for role_key in REQUIRED_ML_ROLES:
        upstream = upstream_roles.get(role_to_upstream_name[role_key], {})
        ml_role_modules.append(
            {
                "role_key": role_key,
                "runtime_config_enabled_key": f"replacement_ml_{role_key}_enabled",
                "enabled": bool(runtime_cfg[f"replacement_ml_{role_key}_enabled"]),
                "apply_to_execution": bool(runtime_cfg["replacement_ml_apply_to_execution"]),
                "runtime_effect": "monitor_only",
                "activation_rule": "sealed_validation_and_no_leak_tests_required_before_control",
                "upstream_role": role_to_upstream_name[role_key],
                "upstream_target": upstream.get("target"),
                "upstream_disposition": upstream.get("disposition"),
                "upstream_train_status": upstream.get("train_status"),
            }
        )

    runtime_presence = _source_presence(
        RUNTIME_PATH,
        [
            "GTOSVNextReplacementMonitoringSnapshot",
            "build_vnext_replacement_monitoring_snapshot",
            "record_vnext_replacement_monitoring_snapshot",
            "attach_vnext_replacement_monitoring_to_record",
            "old_live_fallback_leakage",
            "malformed_response_summary",
            "ml_assistant_roles",
        ],
    )
    orchestrator_presence = _source_presence(
        ORCHESTRATOR_PATH,
        [
            "_record_gtos_vnext_replacement_monitoring",
            "post_l2_replacement_candidate",
            "post_l2_replacement_block",
        ],
    )
    test_presence = _source_presence(
        TEST_PATH,
        [
            "test_vnext_replacement_monitoring_snapshot_records_stage10_surfaces",
            "test_vnext_replacement_monitoring_flags_old_live_fallback_leakage",
            "replacement_monitoring_log_path",
        ],
    )

    default_projection = stage06_verifier["overall_scenario_metrics"][
        "activated_default_source_bound_primary"
    ]
    integration_map = {
        "route_id": ROUTE_ID,
        "stage_id": "stage_10_ml_and_monitoring_integration",
        "generated_at_utc": generated_at,
        "no_live_trading_or_broker_mutation": True,
        "paid_api_or_vendor_calls_made": 0,
        "input_artifacts": {
            "stage03_contract": {"path": _rel(STAGE03_CONTRACT), "sha256": _sha256(STAGE03_CONTRACT)},
            "stage05_summary": {"path": _rel(STAGE05_SUMMARY), "sha256": _sha256(STAGE05_SUMMARY)},
            "stage05_verifier": {"path": _rel(STAGE05_VERIFIER), "sha256": _sha256(STAGE05_VERIFIER)},
            "stage06_verifier": {"path": _rel(STAGE06_VERIFIER), "sha256": _sha256(STAGE06_VERIFIER)},
            "stage08_source_capture": {"path": _rel(STAGE08_CAPTURE), "rows": source_capture_rows},
            "stage09_ai_manifest": {"path": _rel(STAGE09_MANIFEST), "sha256": _sha256(STAGE09_MANIFEST)},
            "ml_results": {"path": _rel(ML_RESULTS), "sha256": _sha256(ML_RESULTS)},
        },
        "runtime_config": {
            "replacement_monitoring_enabled": runtime_cfg["replacement_monitoring_enabled"],
            "replacement_monitoring_log_enabled": runtime_cfg["replacement_monitoring_log_enabled"],
            "replacement_monitoring_log_path": runtime_cfg["replacement_monitoring_log_path"],
            "replacement_ml_apply_to_execution": runtime_cfg["replacement_ml_apply_to_execution"],
            "replacement_ml_role_keys": configured_roles,
            "moonshot_dynamic_execution_router_apply_to_execution": runtime_cfg[
                "moonshot_dynamic_execution_router_apply_to_execution"
            ],
            "gtos_vnext_apply_to_execution": runtime_cfg["apply_to_execution"],
        },
        "ml_role_modules": ml_role_modules,
        "monitoring_surfaces": [
            {
                "surface": surface,
                "schema_field": schema["surface_to_snapshot_field"][surface],
                "runtime_effect": "log_only",
            }
            for surface in MONITORING_SURFACES
        ],
        "monitoring_log_schema": {
            "path": _rel(OUTPUT_SCHEMA),
            "sha256": _sha256(OUTPUT_SCHEMA),
            "snapshot_required_fields": SNAPSHOT_REQUIRED_FIELDS,
        },
        "runtime_presence": {
            "src/components/gtos_vnext_runtime.py": runtime_presence,
            "src/components/orchestrator.py": orchestrator_presence,
            "tests/test_gtos_vnext_runtime.py": test_presence,
        },
        "replay_guardrails": {
            "candidate_rows": stage05["coverage"]["candidate_rows"],
            "dynamic_policy_replay_rows": stage05["coverage"]["dynamic_policy_replay_rows"],
            "stage05_warnings": stage05_verifier.get("warnings", []),
            "negative_default_source_bound_primary_expectancy_r": float(
                default_projection["expectancy_r"]
            ),
            "negative_default_source_bound_primary_blocks_overlay": (
                float(default_projection["expectancy_r"]) < 0.0
            ),
            "stage09_ai_prompt_rows": stage09["prompt_pack"]["packet_rows"],
            "paid_ai_or_vendor_calls_made": stage09["ai_call_execution_state"][
                "paid_api_or_vendor_calls_made"
            ],
        },
        "stage03_ml_contract_rows": len(stage03.get("ml_contract", {}).get("ml_roles", [])),
        "semantic_controls": {
            "old_live_fallback_leakage_is_explicit_field": True,
            "source_missing_rows_require_capture_or_exclusion": True,
            "ml_live_control_blocked_until_sealed_validation": True,
            "malformed_ai_responses_are_supervised_not_silent": True,
            "monitoring_does_not_override_safety_gates": True,
        },
        "focused_tests": [
            "tests/test_gtos_vnext_runtime.py::test_vnext_replacement_monitoring_snapshot_records_stage10_surfaces",
            "tests/test_gtos_vnext_runtime.py::test_vnext_replacement_monitoring_flags_old_live_fallback_leakage",
            "tests/test_gtos_vnext_runtime.py::test_agent_config_wires_vnext_runtime_shadow_execution_path",
        ],
        "schema_version": "vnext_replacement_stage10_ml_monitoring_integration_map_v1",
    }
    _write_json(OUTPUT_MAP, integration_map)

    _upsert_manifest_output(
        manifest,
        {
            "path": OUTPUT_MAP.name,
            "stage": "stage_10",
            "status": "created",
            "ml_role_rows": len(ml_role_modules),
            "monitoring_surfaces": len(MONITORING_SURFACES),
        },
    )
    _upsert_manifest_output(
        manifest,
        {
            "path": OUTPUT_SCHEMA.name,
            "stage": "stage_10",
            "status": "created",
            "required_snapshot_fields": len(SNAPSHOT_REQUIRED_FIELDS),
        },
    )
    _upsert_manifest_output(
        manifest,
        {
            "path": Path(__file__).name,
            "stage": "stage_10",
            "status": "created_and_ready_for_py_compile",
        },
    )
    manifest["last_updated_utc"] = generated_at
    _write_json(MANIFEST_PATH, manifest)

    evidence = state.setdefault("evidence_rows_scanned", {})
    evidence["stage10_ml_role_rows"] = len(ml_role_modules)
    evidence["stage10_monitoring_surfaces"] = len(MONITORING_SURFACES)
    evidence["stage10_source_capture_rows_consumed"] = source_capture_rows
    evidence["stage10_ai_prompt_rows_consumed"] = int(stage09["prompt_pack"]["packet_rows"])
    evidence["stage10_log_schema_required_fields"] = len(SNAPSHOT_REQUIRED_FIELDS)
    state["current_stage"] = "stage_11_activation_dossier_and_config_overlay"
    state["first_incomplete_invariant"] = "stage_11_activation_dossier_and_config_overlay_pending"
    state["exact_next_action"] = "Build activation dossier, config overlay diff, rollback runbook, demo/shadow activation runbook, and monitoring checklist."
    state.setdefault("stage_status", {})[
        "stage_10_ml_and_monitoring_integration"
    ] = "completed_ml_monitoring_map_runtime_schema_and_tests_written"
    state.setdefault("stage_status", {})[
        "stage_11_activation_dossier_and_config_overlay"
    ] = "pending"
    _append_test_result(
        state,
        _rel(Path(__file__)),
        "passed; wrote Stage10 ML monitoring integration map and monitoring log schema",
        generated_at,
    )
    state["last_updated_utc"] = generated_at
    _write_json(STATE_PATH, state)

    _append_control(
        {
            "event": "stage_10_ml_monitoring_integration_completed",
            "generated_at_utc": generated_at,
            "ml_role_rows": len(ml_role_modules),
            "monitoring_surfaces": len(MONITORING_SURFACES),
            "route_id": ROUTE_ID,
            "stage_id": "stage_10_ml_and_monitoring_integration",
        }
    )

    print(
        json.dumps(
            {
                "ml_roles": len(ml_role_modules),
                "monitoring_surfaces": len(MONITORING_SURFACES),
                "next": state["first_incomplete_invariant"],
                "stage": "stage_10_ml_and_monitoring_integration",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
