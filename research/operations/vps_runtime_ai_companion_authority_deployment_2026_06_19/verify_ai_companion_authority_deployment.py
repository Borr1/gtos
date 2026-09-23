#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
VERIFICATION_RESULT = ROUTE / "VERIFICATION_RESULT.json"
OUTPUT_MANIFEST = ROUTE / "OUTPUT_MANIFEST.json"
CONTROL_SNAPSHOT = ROUTE / "AI_COMPANION_ACTIVE_CONTROL_STATE_SNAPSHOT.json"
DIGEST_SNAPSHOT = ROUTE / "AI_COMPANION_ACTIVE_DIGEST_SNAPSHOT.json"
SNAPSHOT_METADATA = ROUTE / "AI_COMPANION_ACTIVE_SNAPSHOT_METADATA.json"
PRE_RELOAD_SNAPSHOT = ROUTE / "PRE_RELOAD_PROCESS_SNAPSHOT.json"
POST_RELOAD_SNAPSHOT = ROUTE / "POST_RELOAD_PROCESS_SNAPSHOT.json"
RELOAD_RECOVERY_AUDIT = ROUTE / "RELOAD_RECOVERY_AUDIT.json"

EXPECTED_BOUNDARY = (
    "bounded_protective_runtime_controls_only_no_order_placement_no_risk_increase_"
    "no_hard_gate_override_no_broker_account_order_deal_position_or_credential_mutation"
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def copy_json(src: Path, dst: Path) -> dict[str, Any]:
    data = read_json(src)
    dst.write_text(json.dumps(data, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return data if isinstance(data, dict) else {}


def run_cmd(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True)
    return {
        "args": args,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout.splitlines()[-20:],
        "stderr_tail": proc.stderr.splitlines()[-20:],
    }


def main() -> int:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from src.components.ai_companion.control_state import (
        AI_COMPANION_CONTROL_SCHEMA,
        RUNTIME_EFFECT_BOUNDARY,
        validate_control_state,
    )

    issues: list[dict[str, Any]] = []
    required_paths = [
        REPO_ROOT / "src/components/ai_companion/control_state.py",
        REPO_ROOT / "src/components/ai_companion/supervisor.py",
        REPO_ROOT / "scripts/run_ai_companion_supervisor.py",
        REPO_ROOT / "src/components/ultimate_book/book_owner.py",
        REPO_ROOT / "src/components/ultimate_book/launcher.py",
        REPO_ROOT / "scripts/run_book_supervisor.ps1",
        REPO_ROOT / "config/agent_config.yaml",
        REPO_ROOT / "pipeline_state/ai_companion/control_state.json",
        REPO_ROOT / "pipeline_state/ai_companion/cycle_digest.json",
        REPO_ROOT / "pipeline_state/ai_companion/heartbeat.json",
        PRE_RELOAD_SNAPSHOT,
        POST_RELOAD_SNAPSHOT,
        RELOAD_RECOVERY_AUDIT,
    ]
    for path in required_paths:
        if not path.exists():
            issues.append({"id": "missing_required_path", "path": str(path.relative_to(REPO_ROOT))})

    cfg = yaml.safe_load((REPO_ROOT / "config/agent_config.yaml").read_text(encoding="utf-8")) or {}
    rt = cfg.get("gtos_vnext_runtime") if isinstance(cfg, dict) else {}
    companion = rt.get("ai_companion") if isinstance(rt, dict) else {}
    if not isinstance(companion, dict):
        companion = {}
    expected_config = {
        "enabled": True,
        "authority_level": "protective",
        "control_state_path": "pipeline_state/ai_companion/control_state.json",
        "decision_log_path": "shadow_logs/ai_companion_decisions.jsonl",
    }
    for key, expected in expected_config.items():
        if companion.get(key) != expected:
            issues.append({"id": "config_mismatch", "key": key, "expected": expected, "actual": companion.get(key)})
    if companion.get("runtime_effect_boundary") != EXPECTED_BOUNDARY:
        issues.append({"id": "config_runtime_boundary_mismatch", "actual": companion.get("runtime_effect_boundary")})
    if RUNTIME_EFFECT_BOUNDARY != EXPECTED_BOUNDARY:
        issues.append({"id": "code_runtime_boundary_mismatch", "actual": RUNTIME_EFFECT_BOUNDARY})

    code_checks = {
        "book_owner_gate_import": (REPO_ROOT / "src/components/ultimate_book/book_owner.py", "AICompanionRuntimeGate"),
        "book_owner_pause": (REPO_ROOT / "src/components/ultimate_book/book_owner.py", "ai_companion_pause_new_entries"),
        "book_owner_cooldown": (REPO_ROOT / "src/components/ultimate_book/book_owner.py", "ai_companion_cooldown"),
        "book_owner_risk": (REPO_ROOT / "src/components/ultimate_book/book_owner.py", "ai_companion_risk_adjustments"),
        "launcher_log_state": (REPO_ROOT / "src/components/ultimate_book/launcher.py", "\"ai_companion\""),
        "supervisor_restart": (REPO_ROOT / "scripts/run_book_supervisor.ps1", "run_ai_companion_supervisor.py"),
    }
    for check_id, (path, needle) in code_checks.items():
        if path.exists() and needle not in read_text(path):
            issues.append({"id": check_id, "needle": needle, "path": str(path.relative_to(REPO_ROOT))})

    control_state = {}
    digest = {}
    if (REPO_ROOT / "pipeline_state/ai_companion/control_state.json").exists():
        control_state = copy_json(REPO_ROOT / "pipeline_state/ai_companion/control_state.json", CONTROL_SNAPSHOT)
        if control_state.get("schema") != AI_COMPANION_CONTROL_SCHEMA:
            issues.append({"id": "control_schema_mismatch", "actual": control_state.get("schema")})
        if control_state.get("runtime_effect_boundary") != EXPECTED_BOUNDARY:
            issues.append({"id": "control_boundary_mismatch", "actual": control_state.get("runtime_effect_boundary")})
        for namespace in ("operator_profile", "redacted_account_live_bee34003"):
            ok, summary = validate_control_state(control_state, namespace=namespace)
            if not ok:
                issues.append({"id": "control_validation_failed", "namespace": namespace, "summary": summary})
            if summary.get("issues"):
                issues.append({"id": "control_validation_issues", "namespace": namespace, "issues": summary.get("issues")})
            for control in summary.get("accepted_controls") or []:
                if control.get("type") == "risk_multiplier" and float(control.get("multiplier", 1.0)) > 1.0:
                    issues.append({"id": "risk_multiplier_above_one", "namespace": namespace, "control": control})
    if (REPO_ROOT / "pipeline_state/ai_companion/cycle_digest.json").exists():
        digest = copy_json(REPO_ROOT / "pipeline_state/ai_companion/cycle_digest.json", DIGEST_SNAPSHOT)
        if digest.get("runtime_effect_boundary") != EXPECTED_BOUNDARY:
            issues.append({"id": "digest_boundary_mismatch", "actual": digest.get("runtime_effect_boundary")})
        if not bool(digest.get("ok")):
            issues.append({"id": "digest_not_ok", "issue_counts": digest.get("issue_counts")})
    snapshot_metadata = {
        "schema": "gtos.ai_companion.active_snapshot_metadata.v1",
        "snapshot_generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_effect_boundary": EXPECTED_BOUNDARY,
        "control_snapshot_path": str(CONTROL_SNAPSHOT.relative_to(ROUTE)),
        "digest_snapshot_path": str(DIGEST_SNAPSHOT.relative_to(ROUTE)),
        "source_control_state_path": "pipeline_state/ai_companion/control_state.json",
        "source_digest_path": "pipeline_state/ai_companion/cycle_digest.json",
        "control_generated_at_utc": control_state.get("generated_at_utc"),
        "digest_generated_at_utc": digest.get("generated_at_utc"),
        "snapshot_interpretation": "point_in_time_copy_verify_live_pipeline_state_for_current_runtime_truth",
    }
    SNAPSHOT_METADATA.write_text(
        json.dumps(snapshot_metadata, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    post_reload = read_json(POST_RELOAD_SNAPSHOT) if POST_RELOAD_SNAPSHOT.exists() else {}
    processes = post_reload.get("processes") if isinstance(post_reload.get("processes"), list) else []
    command_lines = [str(row.get("CommandLine") or row.get("commandLine") or "") for row in processes if isinstance(row, dict)]
    required_process_needles = {
        "ftmo_terminal": "C:\\MT5\\FTMO\\terminal64.exe",
        "redacted_account_terminal": "C:\\MT5\\redacted_account\\terminal64.exe",
        "book_supervisor": "run_book_supervisor.ps1",
        "ftmo_book": "--namespace operator_profile",
        "redacted_account_book": "--namespace redacted_account_live_bee34003",
        "monitor_books": "monitor_books.py",
        "ai_companion_supervisor": "run_ai_companion_supervisor.py",
    }
    for check_id, needle in required_process_needles.items():
        if not any(needle in line for line in command_lines):
            issues.append({"id": "post_reload_missing_process", "check": check_id, "needle": needle})
    ai_hb = post_reload.get("ai_companion_heartbeat") if isinstance(post_reload.get("ai_companion_heartbeat"), dict) else {}
    if ai_hb.get("ok") is not True:
        issues.append({"id": "post_reload_ai_companion_heartbeat_not_ok", "heartbeat": ai_hb})
    active_control_state = (
        post_reload.get("active_control_state") if isinstance(post_reload.get("active_control_state"), dict) else {}
    )
    summary = active_control_state.get("summary") if isinstance(active_control_state.get("summary"), dict) else {}
    if summary.get("active_control_count") not in (0, None):
        issues.append({"id": "post_reload_unexpected_active_controls", "summary": summary})

    syntax = run_cmd([
        sys.executable,
        "-m",
        "py_compile",
        "src/components/ai_companion/__init__.py",
        "src/components/ai_companion/control_state.py",
        "src/components/ai_companion/supervisor.py",
        "src/components/ultimate_book/book_owner.py",
        "src/components/ultimate_book/launcher.py",
        "scripts/run_ai_companion_supervisor.py",
    ])
    if syntax["returncode"] != 0:
        issues.append({"id": "py_compile_failed", "result": syntax})

    manifest = {
        "schema": "gtos.ai_companion_authority_deployment.output_manifest.v1",
        "artifacts": [
            "AI_COMPANION_AUTHORITY_DEPLOYMENT.md",
            "AI_COMPANION_ACTIVE_CONTROL_STATE_SNAPSHOT.json",
            "AI_COMPANION_ACTIVE_DIGEST_SNAPSHOT.json",
            "COMPLETION_AUDIT.json",
            "DECISION_LEDGER.json",
            "FOCUSED_TEST_RESULT.json",
            "PRE_RELOAD_PROCESS_SNAPSHOT.json",
            "POST_RELOAD_PROCESS_SNAPSHOT.json",
            "RELOAD_RECOVERY_AUDIT.json",
            "VERIFICATION_RESULT.json",
            "OUTPUT_MANIFEST.json",
            "AI_COMPANION_ACTIVE_SNAPSHOT_METADATA.json",
            "verify_ai_companion_authority_deployment.py",
        ],
        "runtime_effect_boundary": EXPECTED_BOUNDARY,
    }
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "gtos.ai_companion_authority_deployment.verification_result.v1",
        "ok": not issues,
        "issues": issues,
        "runtime_effect_boundary": EXPECTED_BOUNDARY,
        "config": {
            "enabled": companion.get("enabled"),
            "authority_level": companion.get("authority_level"),
            "control_state_path": companion.get("control_state_path"),
        },
        "active_control_summary": control_state.get("summary"),
        "digest_issue_counts": digest.get("issue_counts"),
        "digest_ok": digest.get("ok"),
        "active_snapshot_metadata": snapshot_metadata,
        "syntax": syntax,
        "output_manifest": manifest,
    }
    VERIFICATION_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
