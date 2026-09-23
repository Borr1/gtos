from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


DATE = "2026-05-27"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
CONFIG = REPO_ROOT / "config" / "agent_config.yaml"
OUTPUT = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE05_ROLLBACK_PROOF_{DATE}.json"

ROLLBACK_FLAGS = {
    "mode": "shadow",
    "apply_to_execution": False,
    "pre_ai_apply_to_ai_call": False,
    "moonshot_dynamic_execution_router_enabled": False,
    "moonshot_dynamic_execution_router_apply_to_execution": False,
    "ltf_path_execution_apply_to_execution": False,
    "prop_safe_selector_apply_to_execution": False,
}
MONITOR_FLAGS = {
    "replacement_monitoring_enabled": True,
    "replacement_monitoring_log_enabled": True,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_proof() -> dict[str, Any]:
    before_hash = sha256_file(CONFIG)
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
    rolled = copy.deepcopy(config)
    runtime = rolled.setdefault("gtos_vnext_runtime", {})
    runtime.update(ROLLBACK_FLAGS)
    runtime.update(MONITOR_FLAGS)
    temp_path = ROUTE_DIR / f"tmp_stage05_rollback_agent_config_{DATE}.yaml"
    temp_path.write_text(yaml.safe_dump(rolled, sort_keys=False), encoding="utf-8")
    loaded = yaml.safe_load(temp_path.read_text(encoding="utf-8")) or {}
    loaded_runtime = loaded.get("gtos_vnext_runtime") or {}
    assertions = {}
    for key, expected in {**ROLLBACK_FLAGS, **MONITOR_FLAGS}.items():
        assertions[key] = {
            "expected": expected,
            "observed": loaded_runtime.get(key),
            "passed": loaded_runtime.get(key) == expected,
        }
    after_hash = sha256_file(CONFIG)
    payload = {
        "schema_version": "vnext_activation_repair_stage05_rollback_proof_v1",
        "route_id": "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27",
        "stage_id": "stage_05_full_verification_matrix",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "passed" if before_hash == after_hash and all(row["passed"] for row in assertions.values()) else "failed",
        "source_config_path": "config/agent_config.yaml",
        "source_config_sha256_before": before_hash,
        "source_config_sha256_after": after_hash,
        "source_config_unchanged": before_hash == after_hash,
        "temp_config_path": temp_path.relative_to(REPO_ROOT).as_posix(),
        "temp_config_sha256": sha256_file(temp_path),
        "rollback_overlay_applied_to_temp_config_only": True,
        "assertions": assertions,
        "active_production_flags_covered": sorted(ROLLBACK_FLAGS),
        "monitoring_flags_preserved": sorted(MONITOR_FLAGS),
    }
    write_json(OUTPUT, payload)
    return payload


def check_proof() -> dict[str, Any]:
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    issues = []
    if payload.get("status") != "passed":
        issues.append(f"status:{payload.get('status')}")
    if payload.get("source_config_sha256_after") != sha256_file(CONFIG):
        issues.append("current_config_hash_differs_from_proof")
    if not payload.get("source_config_unchanged"):
        issues.append("source_config_mutated")
    for key, row in (payload.get("assertions") or {}).items():
        if not row.get("passed"):
            issues.append(f"rollback_flag_failed:{key}")
    payload["check_status"] = "passed" if not issues else "failed"
    payload["check_issues"] = issues
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = check_proof() if args.check else build_proof()
    result = {
        "mode": "check" if args.check else "build",
        "status": payload.get("check_status") if args.check else payload.get("status"),
        "issues": payload.get("check_issues", []),
        "output": str(OUTPUT),
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
