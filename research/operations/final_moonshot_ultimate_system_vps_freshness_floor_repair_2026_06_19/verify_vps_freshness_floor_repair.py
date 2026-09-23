#!/usr/bin/env python3
"""Verify VPS freshness floor repair artifacts."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
REQUIRED_FLOOR = "b112d22c351b13e2af045bb8feb82f1e235246f4"
VPS_REF = "origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def is_ancestor(ancestor: str, descendant: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=20,
    ).returncode == 0


def git_text(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8", errors="replace").strip()


def stable_verified_utc(result: dict[str, Any]) -> str:
    path = ROUTE / "VERIFICATION_RESULT.json"
    if not path.exists():
        return utc_now()
    try:
        existing = read_json(path)
    except json.JSONDecodeError:
        return utc_now()
    old = {key: value for key, value in existing.items() if key != "verified_utc"}
    new = {key: value for key, value in result.items() if key != "verified_utc"}
    if old == new:
        return existing.get("verified_utc") or utc_now()
    return utc_now()


def main() -> int:
    issues: list[str] = []
    summary = read_json(ROUTE / "VPS_FRESHNESS_FLOOR_REPAIR_SUMMARY.json")
    locks = read_jsonl(ROUTE / "VPS_FRESHNESS_GIT_LOCK_REPAIR_LEDGER.jsonl")
    gates = read_jsonl(ROUTE / "VPS_FRESHNESS_FINAL_SELECTION_GATE_IMPACT_LEDGER.jsonl")
    manifest = read_json(ROUTE / "OUTPUT_MANIFEST.json")
    completion = read_json(ROUTE / "COMPLETION_AUDIT.json")

    if summary.get("status") != "vps_freshness_floor_repaired_not_final_selection":
        issues.append("summary_status_mismatch")
    if summary.get("fetch_returncode") != 0:
        issues.append("fetch_returncode_nonzero")
    if summary.get("fetch_head") != git_text("rev-parse", "FETCH_HEAD"):
        issues.append("fetch_head_not_current")
    if summary.get("origin_vps_head") != git_text("rev-parse", VPS_REF):
        issues.append("origin_vps_head_not_current")
    if not is_ancestor(REQUIRED_FLOOR, "FETCH_HEAD"):
        issues.append("fetch_head_floor_not_ancestor")
    if not is_ancestor(REQUIRED_FLOOR, VPS_REF):
        issues.append("origin_vps_floor_not_ancestor")
    if summary.get("fetch_head_floor_or_newer") is not True:
        issues.append("summary_fetch_floor_not_true")
    if summary.get("origin_vps_floor_or_newer") is not True:
        issues.append("summary_origin_floor_not_true")
    if summary.get("live_state_regenerated_current_head") is not True:
        issues.append("live_state_not_current_head")
    if len(locks) != 4:
        issues.append("lock_row_count_mismatch")
    if any(row.get("exists_after_repair") is not False for row in locks):
        issues.append("stale_lock_still_present")
    if len(gates) != 14:
        issues.append("gate_row_count_mismatch")
    fsg001 = next((row for row in gates if row.get("gate_id") == "FSG001"), None)
    if not fsg001 or fsg001.get("status") != "completed_vps_floor_fetch_verified_live_state_regenerated":
        issues.append("fsg001_not_repaired")
    if summary.get("remaining_final_selection_open_gate_rows") != 12:
        issues.append("remaining_gate_count_mismatch")
    terminal = summary.get("terminal_decision", {})
    if terminal.get("vps_freshness_floor_repaired") is not True:
        issues.append("terminal_freshness_not_true")
    for field in ["final_package_selected", "deployment_dossier_allowed", "live_execution_activation_allowed"]:
        if terminal.get(field) is not False:
            issues.append(f"terminal_boundary_not_false:{field}")
    if any(value is not False for value in summary.get("forbidden_surface_status", {}).values()):
        issues.append("forbidden_surface_crossed")
    if completion.get("goal_completion_claim") is not False:
        issues.append("completion_claim_not_false")
    manifest_files = set(manifest.get("files") or [])
    for required in [
        "VPS_FRESHNESS_FLOOR_REPAIR_SUMMARY.json",
        "VPS_FRESHNESS_GIT_LOCK_REPAIR_LEDGER.jsonl",
        "VPS_FRESHNESS_FINAL_SELECTION_GATE_IMPACT_LEDGER.jsonl",
        "VERIFICATION_RESULT.json",
    ]:
        if required not in manifest_files:
            issues.append(f"manifest_missing:{required}")

    result = {
        "schema": "gtos.final_moonshot.ultimate_system.vps_freshness_floor_repair.verification_result.v1",
        "verified_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "fetch_head": summary.get("fetch_head"),
        "origin_vps_head": summary.get("origin_vps_head"),
        "required_vps_floor": REQUIRED_FLOOR,
        "fetch_head_floor_or_newer": summary.get("fetch_head_floor_or_newer"),
        "origin_vps_floor_or_newer": summary.get("origin_vps_floor_or_newer"),
        "live_state_regenerated_current_head": summary.get("live_state_regenerated_current_head"),
        "stale_git_locks_remaining": summary.get("stale_git_locks_remaining"),
        "remaining_final_selection_open_gate_rows": summary.get("remaining_final_selection_open_gate_rows"),
        "final_package_selected": terminal.get("final_package_selected"),
        "forbidden_surface_status": summary.get("forbidden_surface_status", {}),
    }
    result["verified_utc"] = stable_verified_utc(result)
    write_json(ROUTE / "VERIFICATION_RESULT.json", result)
    completion["verification"]["vps_freshness_floor_repair"] = "passed" if not issues else "failed"
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    focused = read_json(ROUTE / "FOCUSED_TEST_RESULT.json")
    focused["status"] = "passed" if not issues else "failed"
    focused["verification_result"] = {
        "ok": result["ok"],
        "issue_count": result["issue_count"],
        "verified_utc": result["verified_utc"],
    }
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", focused)
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
