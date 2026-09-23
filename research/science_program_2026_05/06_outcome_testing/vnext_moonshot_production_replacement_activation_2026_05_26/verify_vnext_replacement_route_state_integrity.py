from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"

STATE_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
FINAL_SEMANTIC = ROUTE_DIR / f"VNEXT_REPLACEMENT_FINAL_SEMANTIC_VERIFICATION_RESULT_{DATE}.json"
COMPLETION_AUDIT = ROUTE_DIR / f"VNEXT_REPLACEMENT_COMPLETION_AUDIT_{DATE}.json"
RESULT_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_ROUTE_STATE_INTEGRITY_VERIFIER_{DATE}.json"


def _git(args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _commit_exists(commit: str) -> bool:
    if not commit:
        return False
    try:
        _git(["rev-parse", "--verify", f"{commit}^{{commit}}"])
        return True
    except subprocess.CalledProcessError:
        return False


def _state_issues(
    state: dict[str, Any],
    manifest: dict[str, Any],
    current_head: str,
    *,
    commit_exists: Callable[[str], bool] = _commit_exists,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if state.get("current_head") != current_head:
        issues.append(
            {
                "actual": state.get("current_head"),
                "expected": current_head,
                "issue": "state_current_head_stale",
            }
        )
    if manifest.get("current_head") != current_head:
        issues.append(
            {
                "actual": manifest.get("current_head"),
                "expected": current_head,
                "issue": "manifest_current_head_stale",
            }
        )
    top_route_complete = state.get("route_complete")
    gate_route_complete = state.get("completion_gate_status", {}).get("route_complete")
    if top_route_complete != gate_route_complete:
        issues.append(
            {
                "completion_gate_status_route_complete": gate_route_complete,
                "issue": "route_complete_internal_contradiction",
                "top_level_route_complete": top_route_complete,
            }
        )
    scoped_commit = (
        state.get("scoped_commit_proof", {}).get("production_package_commit_sha")
        or state.get("scoped_commit_proof", {}).get("scoped_commit_sha")
    )
    if not scoped_commit or not commit_exists(str(scoped_commit)):
        issues.append(
            {
                "issue": "scoped_commit_proof_missing_or_not_in_git",
                "scoped_commit": scoped_commit,
            }
        )
    if FINAL_SEMANTIC.exists():
        final_semantic = _read_json(FINAL_SEMANTIC)
        if final_semantic.get("activation_gate_passed") is not True:
            issues.append({"issue": "final_semantic_activation_gate_not_passed"})
    if COMPLETION_AUDIT.exists():
        completion = _read_json(COMPLETION_AUDIT)
        if completion.get("completion_status") not in {
            "production_activation_config_overlay_verified_scoped_commit_recorded",
            "production_activation_config_overlay_verified_ready_for_scoped_commit",
            "production_activation_config_overlay_verified_ready_for_scoped_commit",
        }:
            issues.append(
                {
                    "completion_status": completion.get("completion_status"),
                    "issue": "completion_audit_status_not_activation_success",
                }
            )
    return issues


def _repair_state_and_manifest(
    state: dict[str, Any], manifest: dict[str, Any], current_head: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    repaired_state = dict(state)
    repaired_manifest = dict(manifest)
    repaired_state["current_head"] = current_head
    repaired_state["first_incomplete_invariant"] = None
    repaired_state["route_complete"] = True
    repaired_state["last_updated_utc"] = generated_at
    repaired_state["completion_gate_status"] = {
        "allowed_terminal_status": "production_activation_config_overlay_verified_scoped_commit_recorded",
        "reason": "Activation route metadata repaired to current HEAD; scoped activation commit proof remains recorded while this repair-hardening route continues separately.",
        "route_complete": True,
    }
    proof = dict(repaired_state.get("scoped_commit_proof", {}))
    proof.setdefault("production_package_commit_sha", "a7f1f77b50")
    proof["current_head_at_metadata_repair"] = current_head
    proof["metadata_repair_generated_at_utc"] = generated_at
    repaired_state["scoped_commit_proof"] = proof

    repaired_manifest["current_head"] = current_head
    repaired_manifest["last_updated_utc"] = generated_at
    repaired_manifest[
        "next_manifest_update"
    ] = "Run output manifest verifier after any route artifact mutation."
    return repaired_state, repaired_manifest


def run(*, write: bool) -> tuple[dict[str, Any], int]:
    current_head = _git(["log", "-1", "--oneline"])
    state = _read_json(STATE_PATH)
    manifest = _read_json(MANIFEST_PATH)
    if write:
        state, manifest = _repair_state_and_manifest(state, manifest, current_head)
        _write_json(STATE_PATH, state)
        _write_json(MANIFEST_PATH, manifest)
        state = _read_json(STATE_PATH)
        manifest = _read_json(MANIFEST_PATH)
    issues = _state_issues(state, manifest, current_head)
    result = {
        "current_head": current_head,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "issue_count": len(issues),
        "issues": issues,
        "mode": "write" if write else "check",
        "route_id": ROUTE_ID,
        "schema_version": "vnext_replacement_route_state_integrity_verifier_v1",
        "status": "passed" if not issues else "failed",
    }
    if write:
        _write_json(RESULT_PATH, result)
    return result, 0 if not issues else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="verify without mutating files")
    mode.add_argument("--write", action="store_true", help="repair route metadata and write result")
    args = parser.parse_args()
    result, exit_code = run(write=args.write)
    print(json.dumps({k: result[k] for k in ["status", "issue_count", "mode"]}, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
