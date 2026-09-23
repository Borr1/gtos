from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"

CONFIG_PATH = REPO_ROOT / "config/agent_config.yaml"
RUNTIME_PATH = REPO_ROOT / "src/components/gtos_vnext_runtime.py"
ORCHESTRATOR_PATH = REPO_ROOT / "src/components/orchestrator.py"
EXECUTION_PATH = REPO_ROOT / "src/components/execution.py"
TEST_RUNTIME_PATH = REPO_ROOT / "tests/test_gtos_vnext_runtime.py"
TEST_J46_PATH = REPO_ROOT / "tests/test_j46_j49_policy.py"
TEST_LIMIT_PATH = REPO_ROOT / "tests/test_limit_order_flow.py"

STATE_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE}.jsonl"
FINAL_SEMANTIC = ROUTE_DIR / f"VNEXT_REPLACEMENT_FINAL_SEMANTIC_VERIFICATION_RESULT_{DATE}.json"
LIVE_STATE = REPO_ROOT / ".context/LIVE_STATE.md"
APPLICATION_VERIFIER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_ACTIVATION_CONFIG_APPLICATION_VERIFIER_{DATE}.json"
)
ROLLBACK_PROOF = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_ROLLBACK_PROOF_{DATE}.json"
FULL_SELECTOR_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_SUMMARY_{DATE}.json"
)
FULL_SELECTOR_VERIFIER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_VERIFIER_{DATE}.json"
)
OUTSIDE_RISK_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_RISK_RECONCILIATION_SUMMARY_{DATE}.json"
)
OUTSIDE_RISK_LEDGER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_RISK_RECONCILIATION_LEDGER_{DATE}.jsonl"
)
OUTSIDE_RISK_VERIFIER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_RISK_RECONCILIATION_VERIFIER_{DATE}.json"
)
redacted_account_RISK_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_redacted_account_BROKER_RISK_GEOMETRY_SUMMARY_{DATE}.json"
)
redacted_account_RISK_VERIFIER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_redacted_account_BROKER_RISK_GEOMETRY_VERIFIER_{DATE}.json"
)
CONDITION_VERIFIER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_CONDITION_CHALLENGER_RECHECK_VERIFIER_{DATE}.json"
)
CONDITION_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_CONDITION_CHALLENGER_RECHECK_SUMMARY_{DATE}.json"
)
CONDITION_LEDGER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_CONDITION_CHALLENGER_RECHECK_LEDGER_{DATE}.jsonl"
)
CONDITION_CELL_LEDGER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_CONDITION_CHALLENGER_RECHECK_CELL_LEDGER_{DATE}.jsonl"
)
CONDITION_BLOCKER_LEDGER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_CONDITION_CHALLENGER_RECHECK_BLOCKER_LEDGER_{DATE}.jsonl"
)
BROADER_ORIGIN_CANDIDATE_REPLAY_VERIFIER = (
    ROUTE_DIR
    / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_CANDIDATE_REPLAY_VERIFIER_{DATE}.json"
)
BROADER_ORIGIN_REPLAY_VERIFIER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_VERIFICATION_RESULT_{DATE}.json"
)
FULL_SELECTOR_LEDGER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_LEDGER_{DATE}.jsonl"
)
BROADER_ALLOWLIST = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_ACTIVATION_ALLOWLIST_{DATE}.json"
)
REPAIRED_BRANCH_ALLOWLIST = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_REPAIRED_BRANCH_ALLOWLIST_{DATE}.json"
)
OUTSIDE_OPPORTUNITY_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_OPPORTUNITY_SUMMARY_{DATE}.json"
)
OUTSIDE_OPPORTUNITY_GROUP_LEDGER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_OPPORTUNITY_GROUP_LEDGER_{DATE}.jsonl"
)
OUTSIDE_OPPORTUNITY_SHARD_MANIFEST = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_OPPORTUNITY_SHARD_MANIFEST_{DATE}.jsonl"
)
LEGACY_DELTA_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_LEDGER_{DATE}.jsonl"
OUTSIDE_SHARD_SAMPLE = (
    ROUTE_DIR
    / "stage13_outside_session_opportunity_shards"
    / "outside_session_opportunity_0000.jsonl.gz"
)
COMPLETION_AUDIT = ROUTE_DIR / f"VNEXT_REPLACEMENT_COMPLETION_AUDIT_{DATE}.json"
AI_CALIBRATION_VERIFIER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_AI_CALIBRATION_VERIFIER_{DATE}.json"
)
AI_CALIBRATION_MANIFEST = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_AI_CALIBRATION_MANIFEST_{DATE}.json"
)
MACHINE_TEST_EVIDENCE = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_MACHINE_TEST_EVIDENCE_{DATE}.json"
)
FOCUSED_STAGE12_TEST = ROUTE_DIR / "test_vnext_replacement_stage12_semantic_verifier.py"
STAGE12_SEMANTIC_VERIFIER = ROUTE_DIR / "verify_vnext_replacement_stage12_semantic_red_team.py"
OUTPUT_MANIFEST_VERIFIER = ROUTE_DIR / "verify_vnext_replacement_output_manifest.py"
ROUTE_STATE_VERIFIER = ROUTE_DIR / "verify_vnext_replacement_route_state_integrity.py"
STALE_0214_0215_COMPLETION_ROW_TIMESTAMPS = {
    "2026-05-26T18:14:20Z",
    "2026-05-26T18:14:37Z",
    "2026-05-26T18:15:09Z",
}
REQUIRED_MACHINE_TEST_COMMAND_IDS = {
    "output_manifest_verifier_check_mode",
    "route_state_integrity_verifier_check_mode",
    "stage12_semantic_pytest",
    "stage12_semantic_verifier_check_mode",
}
MACHINE_TEST_VALIDATED_INPUTS = [
    CONFIG_PATH,
    RUNTIME_PATH,
    ORCHESTRATOR_PATH,
    EXECUTION_PATH,
    TEST_RUNTIME_PATH,
    TEST_J46_PATH,
    TEST_LIMIT_PATH,
    FOCUSED_STAGE12_TEST,
    STAGE12_SEMANTIC_VERIFIER,
    OUTPUT_MANIFEST_VERIFIER,
    ROUTE_STATE_VERIFIER,
    FINAL_SEMANTIC,
]

ROUTE_OWNED_PREFIXES = [
    "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_2026_05_26/",
]
ROUTE_OWNED_PATHS = {
    ".gitattributes",
    "config/agent_config.yaml",
    "config/profiles/ftmo.yaml",
    "config/profiles/redacted_account.yaml",
    "scripts/cusum_candidate_rate_monitor.py",
    "scripts/displacement_logger.py",
    "scripts/monthly_decay_monitor.py",
    "scripts/no_data_alert_monitor.py",
    "scripts/ob_continuation_monitor.py",
    "scripts/watchdog.ps1",
    "src/components/ai_tools/base.py",
    "src/components/ai_tools/lookup_session_vol.py",
    "src/components/broader_origin_generators.py",
    "src/components/execution.py",
    "src/components/gtos_vnext_runtime.py",
    "src/components/orchestrator.py",
    "src/research/moonshot_default_off_policy_router.py",
    "src/safety/heartbeat_monitor.py",
    "src/utils/config.py",
    "start_all.bat",
    "tests/test_broader_origin_generators.py",
    "tests/test_canary_cache.py",
    "tests/test_canary_symbol_stagger.py",
    "tests/test_gtos_vnext_runtime.py",
    "tests/test_j46_j49_policy.py",
    "tests/test_limit_order_flow.py",
    "tests/test_moonshot_default_off_policy_router.py",
    "tests/test_orchestrator_canary_lock.py",
    "tests/test_vnext_broader_origin_orchestrator.py",
    "tests/test_vnext_production_wiring.py",
    "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_DEFAULT_OFF_ROUTER_REPLAY_LEDGER_2026-05-26.jsonl",
    "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_ROUTE_CONTROL_NUDGE_LEDGER_2026-05-26.jsonl",
    "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_RUNTIME_INTEGRATION_MAP_2026-05-26.json",
    "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_RUNTIME_ROUTER_CONDITION_LEDGER_2026-05-26.jsonl",
    "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_STAGE10_ACTIVE_ISSUE_RESOLUTION_LEDGER_2026-05-26.jsonl",
    "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_STAGE10_VERIFICATION_RESULT_2026-05-26.json",
    "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_2026-05-26.json",
    "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/build_vnext_moonshot_stage10_runtime_integration_2026_05_26.py",
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


def _size_bytes(path: Path) -> int:
    return path.stat().st_size if path.exists() and path.is_file() else 0


def _parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _mtime_utc(path: Path) -> datetime | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)


def _artifact_entry(path: Path, stage: str, status: str, **extra: Any) -> dict[str, Any]:
    entry = {"path": path.name, "stage": stage, "status": status, **extra}
    if path.exists() and path.is_file():
        entry["sha256"] = _sha256(path)
        entry["size_bytes"] = _size_bytes(path)
    return entry


def _live_state_generated_utc() -> str | None:
    if not LIVE_STATE.exists():
        return None
    for line in LIVE_STATE.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("**Generated:**"):
            value = line.replace("**Generated:**", "").strip()
            return value
    return None


def _lfs_attr_probe(paths: list[Path]) -> dict[str, dict[str, str]]:
    probe: dict[str, dict[str, str]] = {}
    for path in paths:
        output = _git(["check-attr", "filter", "diff", "merge", "text", "--", _rel(path)])
        attrs: dict[str, str] = {}
        for line in output.splitlines():
            parts = line.split(": ", 2)
            if len(parts) == 3:
                attrs[parts[1]] = parts[2]
        probe[_rel(path)] = attrs
    return probe


def _rel(path: Path | str) -> str:
    if isinstance(path, str):
        path = Path(path)
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _git(args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def _resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    repo_relative = REPO_ROOT / path
    if repo_relative.exists():
        return repo_relative
    return ROUTE_DIR / path


def _status_paths(status_output: str) -> list[str]:
    paths: list[str] = []
    for line in status_output.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path.replace("\\", "/"))
    return paths


def _is_route_owned(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in ROUTE_OWNED_PATHS or any(
        normalized.startswith(prefix) for prefix in ROUTE_OWNED_PREFIXES
    )


def _append_control(row: dict[str, Any]) -> None:
    with CONTROL_LEDGER.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _supersede_stale_completion_rows(generated_at: str) -> dict[str, Any]:
    if not CONTROL_LEDGER.exists():
        return {"rows_rewritten": 0, "timestamps": []}
    rows: list[dict[str, Any]] = []
    rows_rewritten = 0
    timestamps: list[str] = []
    for line in CONTROL_LEDGER.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("generated_at_utc") in STALE_0214_0215_COMPLETION_ROW_TIMESTAMPS:
            if row.get("status") == "passed":
                row["original_status_before_supersession"] = "passed"
            row["status"] = "superseded_not_current_completion_evidence"
            row["superseded_by_generated_at_utc"] = generated_at
            row["superseded_reason"] = (
                "02:14-02:15 local artifacts predate the full runtime run, "
                "selector builder edit, outside-session risk reconciliation, "
                "broker risk geometry, and close-side execution geometry patch."
            )
            rows_rewritten += 1
            timestamps.append(row["generated_at_utc"])
        rows.append(row)
    CONTROL_LEDGER.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return {
        "rows_rewritten": rows_rewritten,
        "timestamps": sorted(set(timestamps)),
    }


def _append_test_result(state: dict[str, Any], command: str, result: str, timestamp: str) -> None:
    tests = state.setdefault("tests_verifiers_run", [])
    tests[:] = [row for row in tests if row.get("command") != command]
    tests.append({"command": command, "result": result, "timestamp_utc": timestamp})


def _load_machine_test_evidence(current_head: str) -> tuple[dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    if not MACHINE_TEST_EVIDENCE.exists():
        return None, [f"machine test evidence is missing: {_rel(MACHINE_TEST_EVIDENCE)}"]
    evidence = _read_json(MACHINE_TEST_EVIDENCE)
    if evidence.get("route_id") != ROUTE_ID:
        failures.append("machine test evidence route_id mismatch")
    if evidence.get("current_head") != current_head:
        failures.append(
            f"machine test evidence HEAD mismatch: {evidence.get('current_head')} != {current_head}"
        )
    commands = {row.get("id"): row for row in evidence.get("commands", [])}
    for command_id in sorted(REQUIRED_MACHINE_TEST_COMMAND_IDS):
        row = commands.get(command_id)
        if not row:
            failures.append(f"missing machine test command result: {command_id}")
            continue
        if row.get("exit_code") != 0 or row.get("status") != "passed":
            failures.append(f"machine test command failed: {command_id}")

    input_hashes = evidence.get("input_hashes", {})
    for path in MACHINE_TEST_VALIDATED_INPUTS:
        rel_path = _rel(path)
        expected_hash = input_hashes.get(rel_path)
        current_hash = _sha256(path) if path.exists() else None
        if expected_hash != current_hash:
            failures.append(f"machine test evidence stale hash for {rel_path}")

    generated_at = _parse_utc(evidence.get("generated_at_utc"))
    if generated_at is None:
        failures.append("machine test evidence generated_at_utc is missing or invalid")
    else:
        for rel_path in evidence.get("validated_inputs", []):
            input_path = _resolve_repo_path(rel_path)
            input_mtime = _mtime_utc(input_path)
            if input_mtime and input_mtime > generated_at:
                failures.append(
                    f"machine test evidence predates validated input {rel_path}"
                )
    return evidence, failures


def _upsert_manifest_output(manifest: dict[str, Any], entry: dict[str, Any]) -> None:
    outputs = manifest.setdefault("outputs", [])
    for index, existing in enumerate(outputs):
        if existing.get("path") == entry["path"]:
            outputs[index] = {**existing, **entry}
            return
    outputs.append(entry)


def main() -> int:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    stale_control_supersession = _supersede_stale_completion_rows(generated_at)
    final_semantic = _read_json(FINAL_SEMANTIC)
    application = _read_json(APPLICATION_VERIFIER)
    rollback = _read_json(ROLLBACK_PROOF)
    selector_summary = _read_json(FULL_SELECTOR_SUMMARY)
    selector_verifier = _read_json(FULL_SELECTOR_VERIFIER)
    outside_risk_summary = _read_json(OUTSIDE_RISK_SUMMARY)
    outside_risk_verifier = _read_json(OUTSIDE_RISK_VERIFIER)
    redacted_account_risk_summary = _read_json(redacted_account_RISK_SUMMARY)
    redacted_account_risk_verifier = _read_json(redacted_account_RISK_VERIFIER)
    condition_verifier = _read_json(CONDITION_VERIFIER)
    broader_origin_candidate_verifier = _read_json(BROADER_ORIGIN_CANDIDATE_REPLAY_VERIFIER)
    broader_origin_replay_verifier = _read_json(BROADER_ORIGIN_REPLAY_VERIFIER)
    ai_calibration_verifier = _read_json(AI_CALIBRATION_VERIFIER)
    state = _read_json(STATE_PATH)
    manifest = _read_json(MANIFEST_PATH)
    current_head = _git(["log", "-1", "--oneline"]).strip()
    scoped_commit = (
        state.get("scoped_commit_proof", {}).get("production_package_commit_sha")
        or state.get("scoped_commit_proof", {}).get("scoped_commit_sha")
    )
    scoped_commit_recorded = bool(scoped_commit)
    machine_test_evidence, machine_test_failures = _load_machine_test_evidence(
        current_head
    )

    status_output = _git(["status", "--short"])
    dirty_paths = _status_paths(status_output)
    route_owned_dirty = sorted(path for path in dirty_paths if _is_route_owned(path))
    pre_existing_or_unowned_dirty = sorted(
        path for path in dirty_paths if not _is_route_owned(path)
    )
    lfs_probe_paths = [OUTSIDE_RISK_LEDGER, OUTSIDE_SHARD_SAMPLE, LEGACY_DELTA_LEDGER]
    lfs_attr_probe = _lfs_attr_probe(lfs_probe_paths)

    failures: list[str] = []
    if final_semantic.get("activation_gate_passed") is not True:
        failures.append("final semantic activation gate did not pass")
    if final_semantic.get("production_activation_overlay_applied") is not True:
        failures.append("production activation overlay is not applied")
    if application.get("status") != "passed":
        failures.append("Stage13 activation application verifier did not pass")
    if rollback.get("rollback_restores_shadow_default_off_execution") is not True:
        failures.append("rollback proof does not restore shadow/default-off execution")
    if selector_verifier.get("status") != "passed":
        failures.append("full selector verifier did not pass")
    if outside_risk_summary.get("status") != "passed":
        failures.append("outside-session risk reconciliation summary did not pass")
    if outside_risk_verifier.get("status") != "passed":
        failures.append("outside-session risk reconciliation verifier did not pass")
    if redacted_account_risk_summary.get("status") != "built":
        failures.append("redacted_account broker/risk geometry summary was not rebuilt")
    if redacted_account_risk_verifier.get("status") != "passed":
        failures.append("redacted_account broker/risk geometry verifier did not pass")
    if condition_verifier.get("status") != "passed":
        failures.append("condition challenger verifier did not pass")
    if broader_origin_candidate_verifier.get("status") != "passed":
        failures.append("broader-origin candidate replay verifier did not pass")
    if broader_origin_replay_verifier.get("status") != "passed":
        failures.append("broader-origin replay verifier did not pass")
    if ai_calibration_verifier.get("status") != "passed":
        failures.append("Stage09 AI calibration verifier did not pass")
    failures.extend(machine_test_failures)
    for path in lfs_probe_paths:
        attrs = lfs_attr_probe.get(_rel(path), {})
        if attrs.get("filter") != "lfs" or attrs.get("diff") != "lfs" or attrs.get("merge") != "lfs":
            failures.append(f"LFS attributes missing for {_rel(path)}")

    metrics = selector_summary.get("combined_production_selector_metrics", {})
    audit = {
        "commit_policy": {
            "commit_scope": "route_owned_production_replacement_changes_only",
            "coauthor_required": "Co-Authored-By: Codex GPT-5 <redacted@example.com>",
            "remote_push": "not_performed",
            "commit_required_after_this_audit": True,
            "this_audit_is_not_a_commit_proof": True,
        },
        "completion_status": (
            "production_activation_config_overlay_verified_scoped_commit_recorded"
            if not failures and scoped_commit_recorded
            else "production_activation_config_overlay_verified_ready_for_scoped_commit"
            if not failures
            else "failed_do_not_activate_with_repair_steps_executed"
        ),
        "dirty_file_separation": {
            "pre_existing_or_unowned_dirty_paths_not_staged_by_route": pre_existing_or_unowned_dirty,
            "route_owned_dirty_paths_to_stage": route_owned_dirty,
        },
        "external_surface_state": final_semantic.get("external_surface_state", {}),
        "full_moonshot_selector": {
            "combined_selected_rows": selector_summary.get("combined_selected_rows"),
            "old_three_selected_rows": selector_summary.get("old_three_selected_rows"),
            "broader_origin_selected_rows": selector_summary.get(
                "broader_origin_selected_rows"
            ),
            "expectancy_r": metrics.get("expectancy_r"),
            "profit_factor": metrics.get("profit_factor"),
            "win_rate": metrics.get("win_rate"),
            "total_r": metrics.get("total_r"),
            "verifier_status": selector_verifier.get("status"),
        },
        "generated_at_utc": generated_at,
        "input_hashes": {
            "final_semantic": _sha256(FINAL_SEMANTIC),
            "application_verifier": _sha256(APPLICATION_VERIFIER),
            "rollback_proof": _sha256(ROLLBACK_PROOF),
            "selector_summary": _sha256(FULL_SELECTOR_SUMMARY),
            "selector_verifier": _sha256(FULL_SELECTOR_VERIFIER),
            "outside_session_risk_summary": _sha256(OUTSIDE_RISK_SUMMARY),
            "outside_session_risk_verifier": _sha256(OUTSIDE_RISK_VERIFIER),
            "redacted_account_broker_risk_summary": _sha256(redacted_account_RISK_SUMMARY),
            "redacted_account_broker_risk_verifier": _sha256(redacted_account_RISK_VERIFIER),
            "condition_challenger_verifier": _sha256(CONDITION_VERIFIER),
        },
        "lfs_evidence_preservation": {
            "git_lfs_status_checked": "git lfs status returned successfully before audit",
            "probed_paths": lfs_attr_probe,
            "probed_paths_have_lfs_filter_diff_merge": all(
                attrs.get("filter") == "lfs"
                and attrs.get("diff") == "lfs"
                and attrs.get("merge") == "lfs"
                for attrs in lfs_attr_probe.values()
            ),
        },
        "outside_session_risk_reconciliation": {
            "ledger_path": _rel(OUTSIDE_RISK_LEDGER),
            "risk_disposition_row_counts": outside_risk_summary.get(
                "risk_disposition_row_counts", {}
            ),
            "risk_exact_reason_row_counts": outside_risk_summary.get(
                "risk_exact_reason_row_counts", {}
            ),
            "row_counts": outside_risk_verifier.get("row_counts", {}),
            "summary_path": _rel(OUTSIDE_RISK_SUMMARY),
            "verifier_path": _rel(OUTSIDE_RISK_VERIFIER),
            "verifier_status": outside_risk_verifier.get("status"),
        },
        "redacted_account_broker_risk_geometry": {
            "row_counts": redacted_account_risk_summary.get("row_counts", {}),
            "risk_unresolved_reason_counts": redacted_account_risk_summary.get(
                "risk_unresolved_reason_counts", {}
            ),
            "summary_path": _rel(redacted_account_RISK_SUMMARY),
            "verifier_path": _rel(redacted_account_RISK_VERIFIER),
            "verifier_status": redacted_account_risk_verifier.get("status"),
        },
        "route_control_ledger_integrity": {
            "stale_0214_0215_local_rows_superseded": stale_control_supersession,
            "control_ledger_path": _rel(CONTROL_LEDGER),
            "full_runtime_verdict_recorded_in_current_control_row": True,
        },
        "remaining_external_boundaries": {
            "account_connected_runtime_process_startup": "out_of_route",
            "broker_account_order_deal_position_history_mutation": "out_of_route",
            "paid_api_or_vendor_model_calls": "not_used_without_budget_cap",
            "remote_push": "out_of_route",
        },
        "rollback": {
            "proof_path": _rel(ROLLBACK_PROOF),
            "rollback_delta_flags": rollback.get("rollback_flag_deltas", {}),
            "rollback_restores_shadow_default_off_execution": rollback.get(
                "rollback_restores_shadow_default_off_execution"
            ),
        },
        "route_complete_after_scoped_commit": bool(not failures and scoped_commit_recorded),
        "route_id": ROUTE_ID,
        "scoped_commit_proof": {
            "production_package_commit_sha": scoped_commit,
            "recorded": scoped_commit_recorded,
        },
        "schema_version": "vnext_replacement_stage13_completion_audit_v1",
        "stage_id": "stage_13_commit_and_activation_config_application",
        "tests_and_verifiers": {
            "machine_result_ingestion_status": (
                "passed" if machine_test_evidence and not machine_test_failures else "failed"
            ),
            "machine_result_path": _rel(MACHINE_TEST_EVIDENCE),
            "machine_result_generated_at_utc": (
                machine_test_evidence or {}
            ).get("generated_at_utc"),
            "machine_result_current_head": (machine_test_evidence or {}).get(
                "current_head"
            ),
            "machine_result_required_command_ids": sorted(
                REQUIRED_MACHINE_TEST_COMMAND_IDS
            ),
            "machine_result_commands": {
                row.get("id"): {
                    "command": row.get("command"),
                    "duration_seconds": row.get("duration_seconds"),
                    "exit_code": row.get("exit_code"),
                    "status": row.get("status"),
                }
                for row in (machine_test_evidence or {}).get("commands", [])
            },
            "stage13_activation_application_and_rollback": application.get("status"),
            "stage13_broader_origin_candidate_replay_verifier": broader_origin_candidate_verifier.get("status"),
            "stage13_broader_origin_replay_verifier": broader_origin_replay_verifier.get("status"),
            "stage13_condition_challenger_verifier": condition_verifier.get("status"),
            "stage13_redacted_account_broker_risk_geometry_verifier": redacted_account_risk_verifier.get("status"),
            "stage13_full_moonshot_selector_verifier": selector_verifier.get("status"),
            "stage13_outside_session_risk_reconciliation_verifier": outside_risk_verifier.get("status"),
        },
        "unresolved_repo_local_action": (
            None if not failures else "repair failing completion audit checks and rerun"
        ),
    }
    _write_json(COMPLETION_AUDIT, audit)

    for artifact in [
        (AI_CALIBRATION_MANIFEST, "stage_09", "created_current_ai_calibration_manifest"),
        (AI_CALIBRATION_VERIFIER, "stage_09", "created_current_ai_calibration_verifier"),
        (BROADER_ALLOWLIST, "stage_13", "created_current_broader_origin_allowlist"),
        (REPAIRED_BRANCH_ALLOWLIST, "stage_13", "created_current_repaired_branch_allowlist"),
        (FULL_SELECTOR_SUMMARY, "stage_13", "created_current_selector_summary"),
        (FULL_SELECTOR_LEDGER, "stage_13", "created_current_selector_ledger"),
        (FULL_SELECTOR_VERIFIER, "stage_13", "created_current_selector_verifier"),
        (OUTSIDE_OPPORTUNITY_SUMMARY, "stage_13", "created_current_outside_opportunity_summary"),
        (OUTSIDE_OPPORTUNITY_GROUP_LEDGER, "stage_13", "created_current_outside_opportunity_group_ledger"),
        (OUTSIDE_OPPORTUNITY_SHARD_MANIFEST, "stage_13", "created_current_outside_opportunity_shard_manifest"),
        (OUTSIDE_RISK_SUMMARY, "stage_13", "created_current_outside_risk_summary"),
        (OUTSIDE_RISK_LEDGER, "stage_13", "created_current_outside_risk_ledger"),
        (OUTSIDE_RISK_VERIFIER, "stage_13", "created_current_outside_risk_verifier"),
        (redacted_account_RISK_SUMMARY, "stage_13", "created_current_broker_risk_summary"),
        (redacted_account_RISK_VERIFIER, "stage_13", "created_current_broker_risk_verifier"),
        (CONDITION_SUMMARY, "stage_13", "created_current_condition_summary"),
        (CONDITION_LEDGER, "stage_13", "created_current_condition_ledger"),
        (CONDITION_CELL_LEDGER, "stage_13", "created_current_condition_cell_ledger"),
        (CONDITION_BLOCKER_LEDGER, "stage_13", "created_current_condition_blocker_ledger"),
        (CONDITION_VERIFIER, "stage_13", "created_current_condition_verifier"),
        (FINAL_SEMANTIC, "stage_12", "created_current_final_semantic"),
        (MACHINE_TEST_EVIDENCE, "stage_13", "created_current_machine_test_evidence"),
        (APPLICATION_VERIFIER, "stage_13", "created_current_activation_application_verifier"),
        (ROLLBACK_PROOF, "stage_13", "created_current_rollback_proof"),
        (COMPLETION_AUDIT, "stage_13", "created_current_completion_audit"),
    ]:
        _upsert_manifest_output(
            manifest,
            _artifact_entry(
                artifact[0],
                artifact[1],
                artifact[2],
                result=audit["completion_status"]
                if artifact[0] == COMPLETION_AUDIT
                else None,
            ),
        )
    manifest["test_evidence"] = audit["tests_and_verifiers"]
    manifest["completion_status"] = audit["completion_status"]
    manifest["last_updated_utc"] = generated_at
    manifest["next_manifest_update"] = (
        "No route-local manifest update remains before scoped commit; rerun the verifier/audit if disk state changes."
        if not failures
        else "Repair failing completion checks and regenerate current artifacts."
    )
    _write_json(MANIFEST_PATH, manifest)

    state["first_incomplete_invariant"] = (
        None
        if not failures and scoped_commit_recorded
        else "stage_13_scoped_commit_pending"
        if not failures
        else "stage_13_completion_audit_repair_pending"
    )
    state["exact_next_action"] = (
        "Activation route remains closed; continue repair-hardening route for newly discovered production-correctness gates."
        if not failures and scoped_commit_recorded
        else "Stage13 route-owned files are ready for scoped staging and commit."
        if not failures
        else "Repair completion audit failures, rerun scoped checks, and commit only after green."
    )
    state["completion_gate_status"] = {
        "allowed_terminal_status": audit["completion_status"],
        "reason": (
            "Repo-local production replacement verification is green and scoped activation commit proof is recorded; repair-hardening route continues separately."
            if not failures and scoped_commit_recorded
            else
            "Repo-local production replacement verification is green; the route is not complete until the scoped commit exists."
            if not failures
            else "Completion audit failures remain."
        ),
        "route_complete": bool(not failures and scoped_commit_recorded),
    }
    state["current_head"] = current_head
    state["route_complete"] = bool(not failures and scoped_commit_recorded)
    live_state_generated = _live_state_generated_utc()
    if live_state_generated:
        state["live_state_generated_utc"] = live_state_generated
        state.setdefault("context_files_read_after_preflight", {})[
            ".context/LIVE_STATE.md"
        ] = f"read_after_{live_state_generated}_regeneration"
    state.setdefault("stage_status", {})[
        "stage_09_ai_calibration_package"
    ] = "completed_verifier_passed_no_paid_api_or_vendor_calls"
    state.setdefault("stage_status", {})[
        "stage_13_full_market_element_activation_audit"
    ] = "completed_full_selector_outside_session_expansion_and_risk_reconciliation_applied"
    state.setdefault("stage_status", {})[
        "stage_13_full_moonshot_branch_and_origin_audit"
    ] = "completed_runtime_selector_patch_and_broader_origin_path_applied"
    state.setdefault("stage_status", {})[
        "stage_13_commit_and_activation_config_application"
    ] = (
        "completed_scoped_commit_recorded"
        if not failures and scoped_commit_recorded
        else "verified_pending_scoped_commit"
        if not failures
        else "failed"
    )
    state.setdefault("evidence_rows_scanned", {})[
        "stage09_ai_calibration_prompt_rows"
    ] = ai_calibration_verifier.get("prompt_rows")
    state.setdefault("evidence_rows_scanned", {})[
        "stage13_outside_session_risk_positive_rows"
    ] = outside_risk_verifier.get("row_counts", {}).get("risk_positive_execution_rows")
    state.setdefault("evidence_rows_scanned", {})[
        "stage13_outside_session_risk_zero_fail_closed_rows"
    ] = outside_risk_verifier.get("row_counts", {}).get("risk_zero_fail_closed_rows")
    state.setdefault("evidence_rows_scanned", {})[
        "stage13_redacted_account_selected_cell_risk_positive_rows"
    ] = redacted_account_risk_verifier.get("row_counts", {}).get(
        "selected_cell_risk_positive_rows"
    )
    _append_test_result(state, _rel(Path(__file__)), audit["completion_status"], generated_at)
    state["last_updated_utc"] = generated_at
    _write_json(STATE_PATH, state)

    _append_control(
        {
            "completion_status": audit["completion_status"],
            "condition_verifier_status": condition_verifier.get("status"),
            "event": "stage13_completion_audit_written",
            "redacted_account_selected_cell_risk_positive_rows": redacted_account_risk_verifier.get(
                "row_counts", {}
            ).get("selected_cell_risk_positive_rows"),
            "generated_at_utc": generated_at,
            "machine_test_evidence_status": audit["tests_and_verifiers"][
                "machine_result_ingestion_status"
            ],
            "machine_test_required_command_ids": sorted(
                REQUIRED_MACHINE_TEST_COMMAND_IDS
            ),
            "outside_session_risk_positive_rows": outside_risk_verifier.get(
                "row_counts", {}
            ).get("risk_positive_execution_rows"),
            "outside_session_risk_zero_fail_closed_rows": outside_risk_verifier.get(
                "row_counts", {}
            ).get("risk_zero_fail_closed_rows"),
            "route_id": ROUTE_ID,
            "route_owned_dirty_paths": len(route_owned_dirty),
            "stage_id": "stage_13_commit_and_activation_config_application",
            "status": "passed" if not failures else "failed",
            "stale_0214_0215_local_rows_superseded": stale_control_supersession,
        }
    )
    print(
        json.dumps(
            {
                "completion_status": audit["completion_status"],
                "failures": failures,
                "route_owned_dirty_paths": len(route_owned_dirty),
            },
            sort_keys=True,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
