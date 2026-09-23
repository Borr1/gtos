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

CONFIG_PATH = REPO_ROOT / "config/agent_config.yaml"
STATE_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE}.jsonl"
FINAL_SEMANTIC = ROUTE_DIR / f"VNEXT_REPLACEMENT_FINAL_SEMANTIC_VERIFICATION_RESULT_{DATE}.json"
OVERLAY_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONFIG_OVERLAY_DIFF_{DATE}.yaml"
FULL_SELECTOR_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_SUMMARY_{DATE}.json"
)
FULL_SELECTOR_VERIFIER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_VERIFIER_{DATE}.json"
)

OUTPUT_VERIFIER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_ACTIVATION_CONFIG_APPLICATION_VERIFIER_{DATE}.json"
)
OUTPUT_ROLLBACK_PROOF = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_ROLLBACK_PROOF_{DATE}.json"
)

FULL_SELECTOR_ID = "full_moonshot_old_three_plus_broader_origin_positive_native_be_after_trigger"
APPLIED_TRUE_FLAGS = {
    "enabled": True,
    "apply_to_execution": True,
    "pre_ai_apply_to_ai_call": True,
    "ai_policy_follow_no_ai_enabled": True,
    "ltf_path_execution_apply_to_execution": True,
    "prop_safe_selector_apply_to_execution": True,
    "moonshot_dynamic_execution_router_enabled": True,
    "moonshot_dynamic_execution_router_apply_to_execution": True,
    "replacement_monitoring_enabled": True,
    "replacement_monitoring_log_enabled": True,
}
APPLIED_FALSE_FLAGS = {
    "ai_policy_apply_to_ai_call": False,
    "moonshot_dynamic_execution_router_condition_challenger_enabled": False,
    "replacement_ml_apply_to_execution": False,
    "avoid_blocks_execution": False,
}
ROLLBACK_REQUIRED_FALSE_FLAGS = {
    "apply_to_execution": False,
    "pre_ai_apply_to_ai_call": False,
    "ai_policy_apply_to_ai_call": False,
    "ai_policy_follow_no_ai_enabled": False,
    "ltf_path_execution_apply_to_execution": False,
    "prop_safe_selector_apply_to_execution": False,
    "moonshot_dynamic_execution_router_enabled": False,
    "moonshot_dynamic_execution_router_apply_to_execution": False,
    "moonshot_dynamic_execution_router_condition_challenger_enabled": False,
    "replacement_ml_apply_to_execution": False,
    "exit_management_residue_apply_to_execution": False,
    "ready8_failure_control_residue_apply_to_execution": False,
}
ROLLBACK_OBSERVED_KEYS = sorted(
    set(APPLIED_TRUE_FLAGS)
    | set(APPLIED_FALSE_FLAGS)
    | set(ROLLBACK_REQUIRED_FALSE_FLAGS)
    | {
        "mode",
        "moonshot_dynamic_execution_router_policy",
        "moonshot_dynamic_execution_router_repaired_overlay_selector",
        "moonshot_dynamic_execution_router_stage13_repair_summary_path",
        "moonshot_dynamic_execution_router_repaired_branch_allowlist_path",
        "moonshot_dynamic_execution_router_broader_origin_allowlist_path",
        "replacement_monitoring_log_path",
    }
)


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


def _append_control(row: dict[str, Any]) -> None:
    with CONTROL_LEDGER.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _append_test_result(state: dict[str, Any], command: str, result: str, timestamp: str) -> None:
    tests = state.setdefault("tests_verifiers_run", [])
    tests[:] = [row for row in tests if row.get("command") != command]
    tests.append({"command": command, "result": result, "timestamp_utc": timestamp})


def _upsert_manifest_output(manifest: dict[str, Any], entry: dict[str, Any]) -> None:
    outputs = manifest.setdefault("outputs", [])
    for index, existing in enumerate(outputs):
        if existing.get("path") == entry["path"]:
            outputs[index] = {**existing, **entry}
            return
    outputs.append(entry)


def _merge_runtime(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    merged.update(overlay)
    return merged


def main() -> int:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    failures: list[str] = []
    warnings: list[str] = []

    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    overlay = yaml.safe_load(OVERLAY_PATH.read_text(encoding="utf-8")) or {}
    final_semantic = _read_json(FINAL_SEMANTIC)
    selector_summary = _read_json(FULL_SELECTOR_SUMMARY)
    selector_verifier = _read_json(FULL_SELECTOR_VERIFIER)
    state = _read_json(STATE_PATH)
    manifest = _read_json(MANIFEST_PATH)

    runtime = config.get("gtos_vnext_runtime", {}) or {}
    for key, expected in APPLIED_TRUE_FLAGS.items():
        if runtime.get(key) is not expected:
            failures.append(f"current config {key}={runtime.get(key)!r}, expected {expected!r}")
    for key, expected in APPLIED_FALSE_FLAGS.items():
        if runtime.get(key) is not expected:
            failures.append(f"current config {key}={runtime.get(key)!r}, expected {expected!r}")
    if runtime.get("mode") != "production_replacement_vnext_moonshot":
        failures.append(f"current config mode={runtime.get('mode')!r}, expected production replacement")
    if runtime.get("moonshot_dynamic_execution_router_repaired_overlay_selector") != FULL_SELECTOR_ID:
        failures.append("current config selector id is not the full moonshot production selector")
    if not str(runtime.get("moonshot_dynamic_execution_router_stage13_repair_summary_path", "")).endswith(
        FULL_SELECTOR_SUMMARY.name
    ):
        failures.append("current config selector summary path does not point to final full selector")
    if not str(runtime.get("moonshot_dynamic_execution_router_broader_origin_allowlist_path", "")).endswith(
        f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_ACTIVATION_ALLOWLIST_{DATE}.json"
    ):
        failures.append("current config broader-origin allowlist path is missing")
    if final_semantic.get("production_activation_overlay_applied") is not True:
        failures.append("final semantic verifier does not mark production activation overlay applied")
    if final_semantic.get("activation_gate_passed") is not True:
        failures.append("final semantic verifier activation gate did not pass")
    if selector_verifier.get("status") != "passed":
        failures.append("full moonshot selector verifier did not pass")
    selector_metrics = selector_summary.get("combined_production_selector_metrics", {})
    if float(selector_metrics.get("expectancy_r") or 0.0) <= 0:
        failures.append("full moonshot selector expectancy is not positive")
    if float(selector_metrics.get("profit_factor") or 0.0) <= 1:
        failures.append("full moonshot selector profit factor is not above 1")

    rollback_runtime = (
        overlay.get("rollback_overlay", {}).get("config", {}).get("gtos_vnext_runtime", {})
    )
    rollback_dry_run = _merge_runtime(runtime, rollback_runtime)
    for key, expected in ROLLBACK_REQUIRED_FALSE_FLAGS.items():
        if rollback_dry_run.get(key) is not expected:
            failures.append(f"rollback dry-run {key}={rollback_dry_run.get(key)!r}, expected {expected!r}")
    if rollback_dry_run.get("mode") != "shadow":
        failures.append("rollback dry-run does not restore mode=shadow")
    if rollback_dry_run.get("enabled") is not True:
        failures.append("rollback dry-run must keep gtos_vnext_runtime.enabled=true")
    if rollback_dry_run.get("replacement_monitoring_enabled") is not True:
        failures.append("rollback dry-run must keep replacement monitoring enabled")
    if rollback_dry_run.get("replacement_monitoring_log_enabled") is not True:
        failures.append("rollback dry-run must keep replacement monitoring log enabled")

    rollback_delta = {
        key: {"applied": runtime.get(key), "rollback": rollback_dry_run.get(key)}
        for key in sorted(set(APPLIED_TRUE_FLAGS) | set(ROLLBACK_REQUIRED_FALSE_FLAGS) | {"mode"})
        if runtime.get(key) != rollback_dry_run.get(key)
    }
    if not rollback_delta:
        failures.append("rollback dry-run produced no behavioral flag deltas")

    proof = {
        "applied_config_path": _rel(CONFIG_PATH),
        "applied_selector": FULL_SELECTOR_ID,
        "applied_selector_metrics": selector_metrics,
        "current_applied_flags": {key: runtime.get(key) for key in ROLLBACK_OBSERVED_KEYS},
        "generated_at_utc": generated_at,
        "input_hashes": {
            "agent_config_yaml": _sha256(CONFIG_PATH),
            "final_semantic": _sha256(FINAL_SEMANTIC),
            "overlay": _sha256(OVERLAY_PATH),
            "selector_summary": _sha256(FULL_SELECTOR_SUMMARY),
            "selector_verifier": _sha256(FULL_SELECTOR_VERIFIER),
        },
        "rollback_dry_run_relevant_config": {
            "gtos_vnext_runtime": {key: rollback_dry_run.get(key) for key in ROLLBACK_OBSERVED_KEYS}
        },
        "rollback_flag_deltas": rollback_delta,
        "rollback_overlay_source": _rel(OVERLAY_PATH),
        "rollback_proven_without_mutating_repo_config": True,
        "rollback_restores_shadow_default_off_execution": not failures,
        "rollback_verification_commands": [
            "python -m py_compile src\\components\\gtos_vnext_runtime.py src\\components\\orchestrator.py src\\research\\moonshot_default_off_policy_router.py",
            "python -m pytest tests\\test_gtos_vnext_runtime.py::test_agent_config_wires_vnext_runtime_production_replacement_path -q",
            "python research\\science_program_2026_05\\06_outcome_testing\\vnext_moonshot_production_replacement_activation_2026_05_26\\verify_vnext_replacement_stage12_semantic_red_team.py",
        ],
        "route_id": ROUTE_ID,
        "schema_version": "vnext_replacement_stage13_rollback_proof_v1",
        "stage_id": "stage_13_activation_config_application_and_rollback",
    }
    status = "passed" if not failures else "failed"
    verifier = {
        "failures": failures,
        "generated_at_utc": generated_at,
        "production_activation_overlay_applied": not failures,
        "rollback_proof_path": _rel(OUTPUT_ROLLBACK_PROOF),
        "route_id": ROUTE_ID,
        "schema_version": "vnext_replacement_stage13_activation_application_verifier_v1",
        "stage_id": "stage_13_activation_config_application_and_rollback",
        "status": status,
        "warnings": warnings,
    }
    _write_json(OUTPUT_ROLLBACK_PROOF, proof)
    _write_json(OUTPUT_VERIFIER, verifier)

    for path in (OUTPUT_ROLLBACK_PROOF, OUTPUT_VERIFIER, Path(__file__)):
        _upsert_manifest_output(
            manifest,
            {
                "path": path.name,
                "result": status if path != Path(__file__) else "created",
                "sha256": _sha256(path),
                "stage": "stage_13",
                "status": "created",
            },
        )
    manifest["last_updated_utc"] = generated_at
    _write_json(MANIFEST_PATH, manifest)

    evidence = state.setdefault("evidence_rows_scanned", {})
    evidence["stage13_activation_application_verifier_failures"] = len(failures)
    evidence["stage13_rollback_delta_flags"] = len(rollback_delta)
    state["first_incomplete_invariant"] = "stage_13_completion_audit_dirty_split_and_commit_pending"
    state["exact_next_action"] = (
        "Run scoped tests/verifiers/diff checks, write completion audit, separate dirty files, and commit route-owned production replacement changes."
    )
    state.setdefault("stage_status", {})[
        "stage_13_activation_config_application_and_rollback"
    ] = "completed_activation_application_verified_rollback_dry_run_proven" if not failures else "failed"
    _append_test_result(state, _rel(Path(__file__)), status, generated_at)
    state["last_updated_utc"] = generated_at
    _write_json(STATE_PATH, state)

    _append_control(
        {
            "event": "stage13_activation_application_and_rollback_verifier",
            "generated_at_utc": generated_at,
            "production_activation_overlay_applied": not failures,
            "rollback_delta_flags": len(rollback_delta),
            "route_id": ROUTE_ID,
            "stage_id": "stage_13_activation_config_application_and_rollback",
            "status": status,
        }
    )
    print(json.dumps({"status": status, "failures": failures, "rollback_delta_flags": len(rollback_delta)}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
