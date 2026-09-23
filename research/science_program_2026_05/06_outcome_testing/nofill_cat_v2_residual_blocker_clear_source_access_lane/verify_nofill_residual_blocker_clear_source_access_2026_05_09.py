#!/usr/bin/env python3
"""Verify the NOFILL CAT V2 residual blocker source-access packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

DATE = "2026-05-09"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
LANE_ID = "NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE"
LANE_DIR = Path(__file__).resolve().parent
ROOT = LANE_DIR.parents[3]

REQUIRED_FILES = [
    f"NOFILL_RESIDUAL_BLOCKER_CONTEXT_ANCHOR_{DATE}.md",
    f"NOFILL_RESIDUAL_BLOCKER_SOURCE_SEARCH_LEDGER_{DATE}.md",
    f"NOFILL_RESIDUAL_BLOCKER_SOURCE_SEARCH_LEDGER_{DATE}.json",
    f"NOFILL_RESIDUAL_BLOCKER_ROW_DECISION_LEDGER_{DATE}.jsonl",
    f"NOFILL_RESIDUAL_BLOCKER_CLEARANCE_PACKET_{DATE}.json",
    f"NOFILL_RESIDUAL_BLOCKER_BLOCKED_OR_IMPOSSIBLE_LEDGER_{DATE}.md",
    f"NOFILL_RESIDUAL_BLOCKER_BLOCKED_OR_IMPOSSIBLE_LEDGER_{DATE}.json",
    f"NOFILL_RESIDUAL_BLOCKER_NOLEAK_DUPLICATE_AUDIT_{DATE}.md",
    f"NOFILL_RESIDUAL_BLOCKER_NOLEAK_DUPLICATE_AUDIT_{DATE}.json",
    f"NOFILL_RESIDUAL_BLOCKER_NEXT_PROMPT_PACK_{DATE}.md",
    f"NOFILL_RESIDUAL_BLOCKER_COMPLETION_AUDIT_{DATE}.md",
    f"NOFILL_RESIDUAL_BLOCKER_COMPLETION_AUDIT_{DATE}.json",
    "build_nofill_residual_blocker_clear_source_access_2026_05_09.py",
    "verify_nofill_residual_blocker_clear_source_access_2026_05_09.py",
    "test_nofill_residual_blocker_clear_source_access_2026_05_09.py",
]

ALLOWED_STATUSES = {
    "SOURCE_CONTROL_CLEARED_INPUT_ONLY",
    "STILL_BLOCKED_WITH_EXACT_NEXT_SOURCE",
    "SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES",
    "REJECTED_SCOPE_VIOLATION",
}

FORBIDDEN_DIFF_PREFIXES = (
    "src/",
    "src\\",
    "prompts/",
    "prompts\\",
    "config/",
    "config\\",
    "scripts/canary",
    "scripts\\canary",
)

FORBIDDEN_FIELD_NAMES = {
    "broker_actual_r",
    "account_history",
    "order_history",
    "deal_history",
    "hidden_label",
    "win_rate",
    "expectancy",
    "r_multiple",
    "dsr_p",
    "pbo",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(name: str) -> Any:
    return json.loads((LANE_DIR / name).read_text(encoding="utf-8"))


def load_jsonl(name: str) -> list[dict[str, Any]]:
    rows = []
    with (LANE_DIR / name).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def walk_keys(value: Any, path: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_lower = str(key).lower()
            if key_lower in FORBIDDEN_FIELD_NAMES:
                hits.append(f"{path}.{key}" if path else str(key))
            hits.extend(walk_keys(child, f"{path}.{key}" if path else str(key)))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            hits.extend(walk_keys(child, f"{path}[{idx}]"))
    return hits


def unsafe_true_flags(value: Any) -> list[str]:
    bad: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {
                "validation_safe",
                "outcome_review_opened",
                "live_effect",
                "opens_result_scoring",
                "opens_registry_edit",
                "opens_selector_logic",
                "changes_live_trading_behavior",
            } and child is True:
                bad.append(key)
            bad.extend(unsafe_true_flags(child))
    elif isinstance(value, list):
        for child in value:
            bad.extend(unsafe_true_flags(child))
    return bad


def git_output_paths(args: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return [f"GIT_ERROR: {result.stderr.strip()}"]
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def git_status_paths() -> list[str]:
    status = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if status.returncode != 0:
        return [f"GIT_ERROR: {status.stderr.strip()}"]
    paths = []
    for line in status.stdout.splitlines():
        if len(line) > 3:
            paths.append(line[3:].strip())
    return sorted(set(paths))


def git_diff_paths() -> dict[str, object]:
    working_paths = git_output_paths(["diff", "--name-only", "HEAD", "--"])
    staged_paths = git_output_paths(["diff", "--cached", "--name-only"])
    status_paths = git_status_paths()
    two_commit = git_output_paths(["diff", "--name-only", "HEAD~2..HEAD"])
    one_commit = git_output_paths(["diff", "--name-only", "HEAD~1..HEAD"])
    committed_paths = (
        two_commit
        if two_commit and not any(path.startswith("GIT_ERROR:") for path in two_commit)
        else one_commit
    )
    # Main often has unrelated live-monitoring/runtime dirt. Verify this lane
    # by the committed source-access diff while preserving workspace dirt as
    # informational context.
    if committed_paths and not any(path.startswith("GIT_ERROR:") for path in committed_paths):
        checked_paths = sorted(set(staged_paths + committed_paths))
        checked_scope = "committed_lane_diff"
    else:
        checked_paths = sorted(set(working_paths + staged_paths + status_paths + committed_paths))
        checked_scope = "workspace_and_commit_diff"
    return {
        "working_paths": working_paths,
        "staged_paths": staged_paths,
        "status_paths": status_paths,
        "committed_range_paths": committed_paths,
        "checked_paths": checked_paths,
        "checked_scope": checked_scope,
        "workspace_paths_informational_only": checked_scope == "committed_lane_diff",
    }


def forbidden_live_surface_changes(paths: list[str]) -> list[str]:
    hits = []
    for path in paths:
        normalized = path.replace("\\", "/")
        if normalized.startswith("research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_residual_blocker_clear_source_access_lane/"):
            continue
        if normalized in {".context/LIVE_STATE.md", ".context/00_core/research_current_state.md"}:
            continue
        if any(normalized.startswith(prefix.replace("\\", "/")) for prefix in FORBIDDEN_DIFF_PREFIXES):
            hits.append(path)
    return hits


def verify() -> dict[str, Any]:
    issues: list[str] = []
    missing = [name for name in REQUIRED_FILES if not (LANE_DIR / name).exists()]
    if missing:
        issues.append(f"missing required files: {missing}")

    clearance = load_json(f"NOFILL_RESIDUAL_BLOCKER_CLEARANCE_PACKET_{DATE}.json")
    search = load_json(f"NOFILL_RESIDUAL_BLOCKER_SOURCE_SEARCH_LEDGER_{DATE}.json")
    blocked = load_json(f"NOFILL_RESIDUAL_BLOCKER_BLOCKED_OR_IMPOSSIBLE_LEDGER_{DATE}.json")
    noleak = load_json(f"NOFILL_RESIDUAL_BLOCKER_NOLEAK_DUPLICATE_AUDIT_{DATE}.json")
    completion = load_json(f"NOFILL_RESIDUAL_BLOCKER_COMPLETION_AUDIT_{DATE}.json")
    rows = load_jsonl(f"NOFILL_RESIDUAL_BLOCKER_ROW_DECISION_LEDGER_{DATE}.jsonl")

    json_objects = [clearance, search, blocked, noleak, completion] + rows

    if len(rows) != 8:
        issues.append(f"row decision count expected 8, got {len(rows)}")
    statuses = {row.get("terminal_source_control_status") for row in rows}
    if not statuses <= ALLOWED_STATUSES:
        issues.append(f"unexpected terminal statuses: {sorted(statuses - ALLOWED_STATUSES)}")
    if clearance.get("targeted_blocker_count") != 8:
        issues.append("clearance packet targeted_blocker_count != 8")
    if clearance.get("reject_total_preserved_outside_labels_denominators") != 65:
        issues.append("reject total not preserved at 65")
    if noleak.get("reject_total_preserved_outside_labels_denominators") != 65:
        issues.append("noleak reject total not preserved at 65")
    if noleak.get("result_labels_assigned") != 0:
        issues.append("result labels assigned")
    if noleak.get("violations"):
        issues.append(f"noleak violations: {noleak.get('violations')}")
    if any(row.get("cleared_into_accepted_denominator") for row in rows):
        issues.append("a row was moved into accepted denominator")
    if any(row.get("categorical_lifecycle_label") is not None for row in rows):
        issues.append("a row has a lifecycle label")

    families = {
        "OTI4_G6_OPENING_DRIVE": 3,
        "OTI2_RISKBANK": 1,
        "OTI3_G3_GEOMETRY": 4,
    }
    for family, expected in families.items():
        actual = sum(1 for row in rows if row.get("source_lane") == family)
        if actual != expected:
            issues.append(f"{family} expected {expected}, got {actual}")

    searched_families = {record.get("family") for record in search.get("source_records", [])}
    for family in {"oti4_may3_opening_range", "oti2_xauusd_active_window", "oti3_same_tick_event_order"}:
        if family not in searched_families:
            issues.append(f"missing searched source family {family}")

    for obj in json_objects:
        if obj.get("promotion_verdict") not in {PROMOTION_VERDICT, None}:
            issues.append("promotion verdict changed")
        issues.extend([f"unsafe true flag: {hit}" for hit in unsafe_true_flags(obj)])
        issues.extend([f"forbidden field key: {hit}" for hit in walk_keys(obj)])

    hash_mismatches = []
    hash_records = clearance.get("source_hash_manifest", [])
    for record in hash_records:
        if not record.get("exists"):
            continue
        resolved = Path(record["resolved_path"])
        if not resolved.exists():
            hash_mismatches.append({"path": str(resolved), "reason": "missing_on_recompute"})
            continue
        actual = sha256_file(resolved)
        if actual != record.get("sha256"):
            hash_mismatches.append(
                {"path": str(resolved), "expected": record.get("sha256"), "actual": actual}
            )
    if hash_mismatches:
        issues.append(f"hash mismatches: {hash_mismatches[:3]}")

    diff_context = git_diff_paths()
    live_hits = forbidden_live_surface_changes(diff_context["checked_paths"])
    if live_hits:
        issues.append(f"forbidden live-surface diff paths: {live_hits}")

    status = "PASS" if not issues else "FAIL"
    return {
        "artifact_family": "NOFILL_RESIDUAL_BLOCKER_VERIFICATION",
        "route_id": LANE_ID,
        "status": status,
        "issues": issues,
        "can_mark_goal_complete": status == "PASS",
        "required_file_count": len(REQUIRED_FILES),
        "row_decision_count": len(rows),
        "terminal_status_counts": clearance.get("terminal_status_counts"),
        "source_hash_records_recomputed": len(hash_records),
        "git_diff_paths_checked": diff_context["checked_paths"],
        "git_diff_context": diff_context,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
