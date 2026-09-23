#!/usr/bin/env python3
"""Verify the OTI5 duplicate-conflict source identity / geometry audit."""

from __future__ import annotations

import json
import py_compile
import subprocess
import tempfile
from pathlib import Path
from typing import Any


DATE = "2026-05-08"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[3]

AUDIT_JSON = ROOT / f"OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT_{DATE}.json"
ROW_LEDGER_JSONL = ROOT / f"OTI5_DUPLICATE_CONFLICT_ROW_DECISION_LEDGER_{DATE}.jsonl"
SOURCE_SEARCH_JSON = ROOT / f"OTI5_DUPLICATE_CONFLICT_SOURCE_SEARCH_LEDGER_{DATE}.json"
COMPLETION_JSON = ROOT / f"OTI5_DUPLICATE_CONFLICT_COMPLETION_AUDIT_{DATE}.json"
BUILDER = ROOT / f"build_oti5_duplicate_conflict_source_identity_geometry_audit_2026_05_08.py"
TEST_FILE = ROOT / f"test_oti5_duplicate_conflict_source_identity_geometry_audit_2026_05_08.py"

ALLOWED_CHANGE_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def git_status_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip().replace("\\", "/")
        paths.append(path)
    return paths


def git_diff_paths_for_latest_lane_commit() -> list[str]:
    try:
        commit = subprocess.check_output(
            ["git", "log", "--format=%H", "-n", "1", "--", str(ROOT.relative_to(REPO_ROOT)).replace("\\", "/")],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if not commit:
            return []
        output = subprocess.check_output(
            ["git", "diff", "--name-only", f"{commit}^1", commit],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return []
    return [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()]


def main() -> int:
    issues: list[str] = []
    for path in [AUDIT_JSON, ROW_LEDGER_JSONL, SOURCE_SEARCH_JSON, COMPLETION_JSON, BUILDER, TEST_FILE]:
        if not path.exists():
            issues.append(f"missing artifact: {path.name}")

    if not issues:
        audit = read_json(AUDIT_JSON)
        rows = read_jsonl(ROW_LEDGER_JSONL)
        source_search = read_json(SOURCE_SEARCH_JSON)
        completion = read_json(COMPLETION_JSON)

        if audit.get("row_count") != 42 or len(rows) != 42:
            issues.append("expected exactly 42 row decisions")
        if audit.get("nofill_duplicate_key_count") != 3:
            issues.append("expected exactly 3 duplicate groups")
        if sum(1 for row in rows if row.get("is_canonical_geometry_row")) != 3:
            issues.append("expected exactly 3 canonical rows")
        if sum(1 for row in rows if not row.get("is_canonical_geometry_row")) != 39:
            issues.append("expected exactly 39 noncanonical repeated projection rows")
        for payload_name, payload in [("audit", audit), ("source_search", source_search), ("completion", completion)]:
            if payload.get("promotion_verdict") != PROMOTION_VERDICT:
                issues.append(f"{payload_name} promotion verdict changed")
            if payload.get("validation_safe") is not False:
                issues.append(f"{payload_name} validation_safe changed")
            if payload.get("outcome_review_opened") is not False:
                issues.append(f"{payload_name} outcome_review_opened changed")
            if payload.get("live_effect") is not False:
                issues.append(f"{payload_name} live_effect changed")
        if any(row.get("categorical_label_assigned_in_this_audit") is not None for row in rows):
            issues.append("row ledger assigns categorical labels")
        if source_search.get("hash_mismatches"):
            issues.append("source hash mismatches present")
        if source_search.get("missing_source_hash_paths"):
            issues.append("missing source hash paths present")
        if completion.get("can_mark_goal_complete") is not True:
            issues.append("completion audit is not complete")
        if any(item.get("status") != "PASS" for item in completion.get("checklist", [])):
            issues.append("completion checklist has non-PASS items")

    with tempfile.TemporaryDirectory(prefix="oti5_pycompile_") as pyc_dir:
        for path in [BUILDER, TEST_FILE, Path(__file__).resolve()]:
            try:
                py_compile.compile(str(path), cfile=str(Path(pyc_dir) / f"{path.name}.pyc"), doraise=True)
            except py_compile.PyCompileError as exc:
                issues.append(f"py_compile failed for {path.name}: {exc.msg}")

    committed_diff_paths = git_diff_paths_for_latest_lane_commit()
    live_surface_changes = [
        path
        for path in committed_diff_paths
        if not any(path.startswith(prefix) or path == prefix.rstrip("/") for prefix in ALLOWED_CHANGE_PREFIXES)
    ]
    if live_surface_changes:
        issues.append(f"unexpected changed paths: {live_surface_changes}")
    workspace_changed_paths = git_status_paths()

    output = {
        "can_mark_goal_complete": not issues,
        "changed_paths_checked": committed_diff_paths,
        "changed_path_check_scope": "latest committed lane diff",
        "workspace_changed_path_count": len(workspace_changed_paths),
        "workspace_changed_path_sample": workspace_changed_paths[:20],
        "issues": issues,
        "verification_status": "PASS" if not issues else "FAIL",
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
