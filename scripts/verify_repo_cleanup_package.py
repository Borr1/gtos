#!/usr/bin/env python3
"""Verify the vNext repo cleanup package from post-change disk."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROUTE_ID = "vnext_repo_context_cleanup_deletion_2026_05_29"
ROUTE = ROOT / "research" / "operations" / ROUTE_ID

REQUIRED_ARTIFACTS = [
    "REPO_CLEANUP_STATE.json",
    "REPO_CLEANUP_CONTROL_LEDGER.jsonl",
    "REPO_CLEANUP_OUTPUT_MANIFEST.json",
    "REPO_FILE_INVENTORY_SUMMARY.json",
    "REPO_GIT_LFS_GITHUB_FOOTPRINT_SUMMARY.json",
    "REPO_CONTEXT_STALENESS_VERIFICATION.json",
    "REPO_BLOCKED_DELETE_SECOND_PASS_LEDGER.jsonl",
    "REPO_BLOCKED_DELETE_SECOND_PASS_SUMMARY.json",
    "REPO_DELETE_LEDGER.jsonl",
    "REPO_COMPRESS_LEDGER.jsonl",
    "REPO_KEEP_LEDGER.jsonl",
    "REPO_COLD_EVIDENCE_POINTER_LEDGER.jsonl",
    "REPO_DELETION_PREIMAGE_MANIFEST.json",
    "REPO_LFS_AND_GITHUB_FOOTPRINT_DECISION_LEDGER.jsonl",
    "REPO_CREDENTIAL_ACCOUNT_ARTIFACT_REPAIR_LEDGER.jsonl",
    "REPO_RUNTIME_RETENTION_DECISION_LEDGER.jsonl",
    "REPO_MIXED_CONTEXT_EXTRACTION_DECISION_LEDGER.jsonl",
    "REPO_CONTEXT_CONSOLIDATION_DECISION_LEDGER.jsonl",
    "REPO_CURRENT_TRUTH_SUMMARY.md",
    "REPO_CONTEXT_CONSOLIDATION_SUMMARY.md",
    "REPO_CLEANUP_FINAL_SUMMARY.md",
    "REPO_CLEANUP_FINAL_DECISION_SUMMARY.json",
]

ACTIVE_DOCS = [
    "README.md",
    "CLAUDE.md",
    "AGENTS.md",
    ".context/00_READING_ORDER.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/current_vnext_system_map.md",
    ".context/00_core/current_repo_reading_order.md",
    ".context/00_core/repo_cleanup_and_staleness_policy.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/research_operating_doctrine.md",
]

REFERENCE_DOCS = ACTIVE_DOCS + [
    "research/operations/vnext_repo_context_cleanup_deletion_2026_05_29/REPO_CURRENT_TRUTH_SUMMARY.md",
    "research/operations/vnext_repo_context_cleanup_deletion_2026_05_29/REPO_CONTEXT_CONSOLIDATION_SUMMARY.md",
    "research/operations/vnext_repo_context_cleanup_deletion_2026_05_29/REPO_CLEANUP_FINAL_SUMMARY.md",
]

PATH_PREFIXES = (
    ".context/",
    "research/",
    "scripts/",
    "src/",
    "tests/",
    "config/",
    "knowledge_base/",
    "pipeline_state/",
    "shadow_logs/",
    "data/",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def line_count(path: Path) -> int:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return sum(1 for _ in handle)


def manifest_check() -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    manifest = read_json(ROUTE / "REPO_CLEANUP_OUTPUT_MANIFEST.json")
    outputs = manifest.get("outputs", [])
    output_paths = {row.get("relative_path") for row in outputs if isinstance(row, dict)}
    for name in REQUIRED_ARTIFACTS:
        path = ROUTE / name
        rel = path.relative_to(ROOT).as_posix()
        if not path.exists() or path.stat().st_size <= 0:
            failures.append(f"required artifact missing_or_empty: {rel}")
        if rel not in output_paths:
            failures.append(f"required artifact missing_from_output_manifest: {rel}")
    return failures, {"manifest_output_count": len(output_paths)}


def live_state_check() -> list[str]:
    path = ROOT / ".context" / "LIVE_STATE.md"
    text = path.read_text(encoding="utf-8", errors="replace")
    failures: list[str] = []
    required = [
        "| Status | `FRESH` |",
        "| Mandatory references ok | `True` |",
        "| Missing references | `none` |",
    ]
    for token in required:
        if token not in text:
            failures.append(f"LIVE_STATE missing expected freshness token: {token}")
    return failures


def staleness_check() -> list[str]:
    path = ROUTE / "REPO_CONTEXT_STALENESS_VERIFICATION.json"
    data = read_json(path)
    if data.get("status") != "passed" or data.get("failure_count") != 0:
        return [f"staleness verification failed: status={data.get('status')} failure_count={data.get('failure_count')}"]
    return []


def route_state_check() -> list[str]:
    data = read_json(ROUTE / "REPO_CLEANUP_STATE.json")
    failures: list[str] = []
    complete_status = data.get("status") == "cleanup_route_complete_committed"
    if not complete_status and data.get("head") != git_head():
        failures.append("cleanup state head does not match current HEAD")
    if data.get("first_incomplete_cleanup_invariant") not in {
        "final_verification_and_scoped_commit_pending",
        "none_cleanup_package_committed",
        "final_verification_and_followup_commit_pending",
        "followup_commit_pending",
        "none_cleanup_deletion_followup_committed",
        "none_deletion_execution_repaired_commit_ready",
    }:
        failures.append("cleanup route first incomplete invariant is not final verification/commit")
    if complete_status and data.get("verification_result") != "passed":
        failures.append("complete cleanup state does not preserve passed verification result")
    boundary = data.get("coordination_boundary", {})
    if not boundary.get("live_companion_route_running_in_parallel"):
        failures.append("live companion coordination boundary not recorded")
    if data.get("final_decision_summary", {}).get("deleted_confirmed_rows", 0) <= 0:
        failures.append("delete ledger did not confirm any deletion rows")
    return failures


def delete_ledger_check() -> list[str]:
    failures: list[str] = []
    old_blocked = 0
    if (ROUTE / "REPO_DELETE_LEDGER.jsonl").exists():
        with (ROUTE / "REPO_DELETE_LEDGER.jsonl").open("r", encoding="utf-8-sig") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("final_decision") == "delete_attempted_but_blocked_or_access_denied_post_change":
                    old_blocked += 1
    if old_blocked:
        failures.append(f"delete ledger still has old blocked rows: {old_blocked}")

    allowed_causes = {
        None,
        "active process handle",
        "target no longer exists and ledger must be corrected",
        "path is outside workspace and excluded",
        "reparse point/junction boundary",
        "true access denial with exact error text after attribute clearing and long-path handling",
    }
    second_pass = ROUTE / "REPO_BLOCKED_DELETE_SECOND_PASS_LEDGER.jsonl"
    if second_pass.exists():
        with second_pass.open("r", encoding="utf-8-sig") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                cause = row.get("remaining_cause")
                if cause not in allowed_causes:
                    failures.append(
                        f"second-pass target has unsupported remaining cause: {row.get('target_relative_path')} -> {cause}"
                    )
    return failures


def lfs_check() -> list[str]:
    data = read_json(ROUTE / "REPO_GIT_LFS_GITHUB_FOOTPRINT_SUMMARY.json")
    if data.get("github_hard_limit_current_head_files") != 0:
        return ["current HEAD still has GitHub hard-limit files"]
    return []


def active_doc_truth_check() -> list[str]:
    failures: list[str] = []
    required_tokens = [
        "vNext",
        "24-symbol",
        "momentum_exhaustion",
        "partial_be_runner",
    ]
    for rel in ACTIVE_DOCS:
        text = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        for token in required_tokens:
            if token not in text:
                failures.append(f"{rel} missing current truth token {token!r}")
    return failures


def extract_reference_candidates(text: str) -> set[str]:
    refs: set[str] = set()
    for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
        refs.add(match.group(1))
    for match in re.finditer(r"`([^`]+)`", text):
        refs.add(match.group(1))
    cleaned: set[str] = set()
    for ref in refs:
        ref = ref.strip().strip("<>").split("#", 1)[0]
        if not ref or " " in ref or "://" in ref or "*" in ref or "..." in ref:
            continue
        ref = ref.replace("\\", "/").rstrip(".,;:")
        if ref in {"README.md", "CLAUDE.md", "AGENTS.md"} or ref.startswith(PATH_PREFIXES):
            cleaned.add(ref)
    return cleaned


def broken_reference_scan() -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    for rel in REFERENCE_DOCS:
        path = ROOT / rel
        if not path.exists():
            findings.append({"relative_path": rel, "reference": rel, "status": "source_doc_missing"})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for ref in sorted(extract_reference_candidates(text)):
            target = ROOT / ref
            if target.exists():
                continue
            findings.append({"relative_path": rel, "reference": ref, "status": "broken_reference"})
    result = {
        "schema_version": "repo_active_doc_broken_reference_scan_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "docs_scanned": REFERENCE_DOCS,
        "finding_count": len(findings),
        "findings": findings,
        "status": "passed" if not findings else "failed",
    }
    (ROUTE / "REPO_ACTIVE_DOC_BROKEN_REFERENCE_SCAN.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def ledger_count_check() -> list[str]:
    failures: list[str] = []
    for name in REQUIRED_ARTIFACTS:
        path = ROUTE / name
        if path.suffix == ".jsonl" and path.exists() and line_count(path) <= 0:
            failures.append(f"empty ledger: {path.relative_to(ROOT).as_posix()}")
    return failures


def update_state_if_passed() -> None:
    state_path = ROUTE / "REPO_CLEANUP_STATE.json"
    state = read_json(state_path)
    state["updated_at_utc"] = utc_now()
    state["status"] = "stage04_deletion_second_pass_verification_passed_pending_followup_commit"
    state["first_incomplete_cleanup_invariant"] = "followup_commit_pending"
    state["verification_result"] = "passed"
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_matrix(result: dict[str, Any]) -> None:
    lines = [
        "# Repo Cleanup Verification Matrix",
        "",
        f"Generated at UTC: `{result['generated_at_utc']}`",
        f"Overall status: `{result['status']}`",
        "",
        "| Check | Status | Failures |",
        "|---|---:|---:|",
    ]
    for check in result["checks"]:
        lines.append(f"| {check['name']} | `{check['status']}` | `{len(check['failures'])}` |")
    lines.append("")
    if result["failures"]:
        lines.append("## Failures")
        for failure in result["failures"]:
            lines.append(f"- {failure}")
    else:
        lines.append("No verification failures recorded.")
    (ROUTE / "REPO_CLEANUP_VERIFICATION_MATRIX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def append_verifier_outputs_to_manifest() -> None:
    manifest_path = ROUTE / "REPO_CLEANUP_OUTPUT_MANIFEST.json"
    manifest = read_json(manifest_path)
    outputs = manifest.get("outputs", [])
    if not isinstance(outputs, list):
        outputs = []
    seen = {row.get("relative_path") for row in outputs if isinstance(row, dict)}
    for name in (
        "REPO_CLEANUP_ROUTE_VERIFICATION_RESULT.json",
        "REPO_ACTIVE_DOC_BROKEN_REFERENCE_SCAN.json",
        "REPO_CLEANUP_VERIFICATION_MATRIX.md",
    ):
        path = ROUTE / name
        rel = path.relative_to(ROOT).as_posix()
        if rel in seen:
            continue
        outputs.append(
            {
                "relative_path": rel,
                "size_bytes": path.stat().st_size if path.exists() else None,
                "purpose": "final_cleanup_verification_artifact",
            }
        )
        seen.add(rel)
    manifest["outputs"] = outputs
    manifest["updated_at_utc"] = utc_now()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    checks: list[dict[str, Any]] = []
    failures: list[str] = []

    manifest_failures, manifest_meta = manifest_check()
    checks.append({"name": "manifest_check", "status": "passed" if not manifest_failures else "failed", "failures": manifest_failures, "meta": manifest_meta})
    checks.append({"name": "live_state_freshness", "status": "passed" if not (f := live_state_check()) else "failed", "failures": f})
    checks.append({"name": "active_doc_staleness", "status": "passed" if not (f := staleness_check()) else "failed", "failures": f})
    checks.append({"name": "route_state", "status": "passed" if not (f := route_state_check()) else "failed", "failures": f})
    checks.append({"name": "delete_ledger_second_pass", "status": "passed" if not (f := delete_ledger_check()) else "failed", "failures": f})
    checks.append({"name": "git_lfs_github_footprint", "status": "passed" if not (f := lfs_check()) else "failed", "failures": f})
    checks.append({"name": "active_doc_current_truth_tokens", "status": "passed" if not (f := active_doc_truth_check()) else "failed", "failures": f})
    ref_result = broken_reference_scan()
    ref_failures = [f"{row['relative_path']} -> {row['reference']}" for row in ref_result["findings"]]
    checks.append({"name": "broken_reference_scan", "status": ref_result["status"], "failures": ref_failures})
    checks.append({"name": "ledger_count_check", "status": "passed" if not (f := ledger_count_check()) else "failed", "failures": f})

    for check in checks:
        failures.extend(check["failures"])

    result = {
        "schema_version": "repo_cleanup_route_verification_result_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "head": git_head(),
        "status": "passed" if not failures else "failed",
        "failure_count": len(failures),
        "failures": failures,
        "checks": checks,
    }
    (ROUTE / "REPO_CLEANUP_ROUTE_VERIFICATION_RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_matrix(result)
    append_verifier_outputs_to_manifest()
    if not failures:
        update_state_if_passed()
    print(json.dumps({"status": result["status"], "failure_count": len(failures)}, indent=2))
    return 0 if result["status"] == "passed" or not args.check else 1


if __name__ == "__main__":
    raise SystemExit(main())
