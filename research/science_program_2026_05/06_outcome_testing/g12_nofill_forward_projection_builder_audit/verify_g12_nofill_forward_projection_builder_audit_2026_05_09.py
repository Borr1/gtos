#!/usr/bin/env python3
"""Verify the independent G12 NOFILL forward projection-builder audit."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
ROUTE_ID = "G12_NOFILL_FORWARD_PROJECTION_BUILDER_AUDIT"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]

REQUIRED_FILES = [
    f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_CONTEXT_ANCHOR_{DATE}.md",
    f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_ADVERSARIAL_ISSUE_LEDGER_{DATE}.md",
    f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_ADVERSARIAL_ISSUE_LEDGER_{DATE}.json",
    f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_RECOMPUTATION_LEDGER_{DATE}.json",
    f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_DENOMINATOR_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_DENOMINATOR_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_LOCAL_HEAVY_SEARCH_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_DECISION_LEDGER_{DATE}.md",
    f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_DECISION_LEDGER_{DATE}.json",
    f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_NEXT_ROUTE_LEDGER_{DATE}.md",
    f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_NEXT_ROUTE_LEDGER_{DATE}.json",
    f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.md",
    f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.json",
    f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_COMPLETION_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_COMPLETION_AUDIT_{DATE}.json",
    "build_g12_nofill_forward_projection_builder_audit_2026_05_09.py",
    "verify_g12_nofill_forward_projection_builder_audit_2026_05_09.py",
    "test_g12_nofill_forward_projection_builder_audit_2026_05_09.py",
]

FORBIDDEN_LIVE_PREFIXES = (
    "src/components/",
    "src/safety/",
    "prompts/",
    "config/",
    "run_agent.py",
    "start_all.bat",
)

ALLOWED_DIR_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_projection_builder_audit/",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)


def load_json(name: str) -> Any:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def git_changed_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip() or line.startswith("warning:"):
            continue
        paths.append(line[3:].replace("\\", "/"))
    return paths


def git_head_commit_paths() -> list[str]:
    result = subprocess.run(
        ["git", "show", "--name-only", "--pretty=format:", "HEAD"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def control_flags_ok(data: dict[str, Any], file_name: str, failures: list[dict[str, Any]]) -> None:
    if data.get("promotion_verdict") != PROMOTION_VERDICT:
        failures.append({"check": "promotion_verdict", "file": file_name, "value": data.get("promotion_verdict")})
    for flag in ("validation_safe", "outcome_review_opened", "live_effect"):
        if data.get(flag) is not False:
            failures.append({"check": "closed_flag", "file": file_name, "flag": flag, "value": data.get(flag)})
    for flag in (
        "opens_result_scoring",
        "opens_live_wiring",
        "opens_paid_api_or_databento_route",
        "opens_registry_edit",
        "changes_live_trading_behavior",
    ):
        if flag in data and data.get(flag) is not False:
            failures.append({"check": "closed_route", "file": file_name, "flag": flag, "value": data.get(flag)})


def main() -> int:
    failures: list[dict[str, Any]] = []

    missing = [name for name in REQUIRED_FILES if not (OUT_DIR / name).exists()]
    if missing:
        failures.append({"check": "required_files", "missing": missing})

    parsed: dict[str, Any] = {}
    for name in REQUIRED_FILES:
        if not name.endswith(".json") or not (OUT_DIR / name).exists():
            continue
        try:
            parsed[name] = load_json(name)
        except json.JSONDecodeError as exc:
            failures.append({"check": "json_parse", "file": name, "error": str(exc)})

    for name, data in parsed.items():
        if isinstance(data, dict):
            control_flags_ok(data, name, failures)

    for name in REQUIRED_FILES:
        if not name.endswith(".md") or not (OUT_DIR / name).exists():
            continue
        text = (OUT_DIR / name).read_text(encoding="utf-8", errors="replace")
        for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
            if token not in text:
                failures.append({"check": "md_control_token", "file": name, "missing": token})

    completion = parsed.get(f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_COMPLETION_AUDIT_{DATE}.json", {})
    decision = parsed.get(f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_DECISION_LEDGER_{DATE}.json", {})
    issues = parsed.get(f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_ADVERSARIAL_ISSUE_LEDGER_{DATE}.json", {})
    denominator = parsed.get(f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_DENOMINATOR_AUDIT_{DATE}.json", {})
    noleak = parsed.get(f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json", {})
    local_heavy = parsed.get(f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_LOCAL_HEAVY_SEARCH_AUDIT_{DATE}.json", {})
    coverage = parsed.get(f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.json", {})

    if completion.get("terminal_verdict") != "BLOCK_ACCEPTANCE_PENDING_EXACT_REPAIR":
        failures.append({"check": "terminal_verdict", "value": completion.get("terminal_verdict")})
    if completion.get("can_accept_projection_builder_as_g12_source_control_evidence") is not False:
        failures.append({"check": "acceptance_flag", "value": completion.get("can_accept_projection_builder_as_g12_source_control_evidence")})
    expected_blockers = {"G12-PROJ-BLOCKER-001", "G12-PROJ-BLOCKER-002"}
    if set(completion.get("blocking_issue_ids") or []) != expected_blockers:
        failures.append({"check": "blocking_issue_ids", "value": completion.get("blocking_issue_ids")})
    if decision.get("can_mark_goal_complete_after_verification_and_commit") is not True:
        failures.append({"check": "decision_completion_flag", "value": decision.get("can_mark_goal_complete_after_verification_and_commit")})
    if issues.get("blocking_issue_count") != 2:
        failures.append({"check": "blocking_issue_count", "value": issues.get("blocking_issue_count")})
    if denominator.get("status") != "PASS" or denominator.get("projection_row_count") != 298:
        failures.append({"check": "denominator_status", "status": denominator.get("status"), "rows": denominator.get("projection_row_count")})
    if denominator.get("accepted_row_level_denominator") != 225:
        failures.append({"check": "row_level_denominator", "value": denominator.get("accepted_row_level_denominator")})
    if denominator.get("primary_duplicate_key_denominator") != 182:
        failures.append({"check": "primary_denominator", "value": denominator.get("primary_duplicate_key_denominator")})
    if denominator.get("secondary_duplicate_group_denominator") != 139:
        failures.append({"check": "secondary_denominator", "value": denominator.get("secondary_duplicate_group_denominator")})
    if noleak.get("hash_recompute", {}).get("status") != "PASS":
        failures.append({"check": "hash_recompute", "value": noleak.get("hash_recompute")})
    if noleak.get("forbidden_projection_key_hits") or noleak.get("forbidden_projection_value_token_hits"):
        failures.append({"check": "projection_no_leak", "keys": noleak.get("forbidden_projection_key_hits"), "values": noleak.get("forbidden_projection_value_token_hits")})
    if noleak.get("unsafe_fields_outside_declared_allowlist"):
        failures.append({"check": "unsafe_allowlist_extras", "value": noleak.get("unsafe_fields_outside_declared_allowlist")})
    if local_heavy.get("status") != "PASS" or local_heavy.get("prior_worktree_extra_needed_matches"):
        failures.append({"check": "local_heavy", "status": local_heavy.get("status"), "matches": local_heavy.get("prior_worktree_extra_needed_matches")})
    if coverage.get("status") != "FAIL":
        failures.append({"check": "coverage_expected_fail", "status": coverage.get("status")})

    changed_paths = git_changed_paths()
    forbidden_dirty = [path for path in changed_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)]
    outside_scope_dirty = [path for path in changed_paths if not path.startswith(ALLOWED_DIR_PREFIXES)]
    if forbidden_dirty:
        failures.append({"check": "forbidden_live_surface_dirty", "paths": forbidden_dirty})
    if outside_scope_dirty:
        failures.append({"check": "outside_scope_dirty", "paths": outside_scope_dirty})

    head_paths = git_head_commit_paths()
    forbidden_head_paths = [path for path in head_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)]
    if forbidden_head_paths:
        failures.append({"check": "committed_diff_live_surface", "paths": forbidden_head_paths})

    result = {
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "terminal_verdict": completion.get("terminal_verdict"),
        "blocking_issue_ids": completion.get("blocking_issue_ids"),
        "failures": failures,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
