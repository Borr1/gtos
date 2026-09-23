"""Verify the G12 NOFILL forward projection repair reaudit artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
ROUTE_ID = "G12_NOFILL_FORWARD_PROJECTION_REPAIR_REAUDIT"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_ACCEPT = "ACCEPT_AS_SOURCE_CONTROL_PROJECTION_EVIDENCE_ONLY"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
PROJECTION_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/nofill_forward_source_safe_projection_builder"

REQUIRED_FILES = [
    f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_CONTEXT_ANCHOR_{DATE}.md",
    f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_DECISION_LEDGER_{DATE}.md",
    f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_DECISION_LEDGER_{DATE}.json",
    f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_RECOMPUTATION_LEDGER_{DATE}.json",
    f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_BLOCKER_CLOSURE_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_BLOCKER_CLOSURE_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_SOURCE_HASH_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_ALLOWLIST_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_MISSING_STATUS_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_MISSING_STATUS_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_NO_LEAK_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_NO_LEAK_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_DENOMINATOR_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_SEARCH_LEDGER_{DATE}.json",
    f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_LIVE_SURFACE_SCOPE_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_HOSTILE_EDGE_REVIEW_{DATE}.md",
    f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_HOSTILE_EDGE_REVIEW_{DATE}.json",
    f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_NEXT_PROMPT_PACK_{DATE}.md",
    f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_COMPLETION_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_COMPLETION_AUDIT_{DATE}.json",
    "build_g12_nofill_forward_projection_repair_reaudit_2026_05_09.py",
    "verify_g12_nofill_forward_projection_repair_reaudit_2026_05_09.py",
    "test_g12_nofill_forward_projection_repair_reaudit_2026_05_09.py",
]

FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/start",
    "run_agent.py",
)
ALLOWED_DIR_PREFIXES = (
    str(OUT_DIR.relative_to(REPO_ROOT)).replace("\\", "/"),
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
)


def load_json(name: str) -> Any:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise AssertionError(f"{path}:{line_no}: {exc}") from exc
    return rows


def git_lines(args: list[str]) -> list[str]:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def status_paths() -> list[str]:
    paths = []
    for line in git_lines(["status", "--short"]):
        path = line[3:] if len(line) > 3 else line
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path.replace("\\", "/").strip())
    return paths


def head_commit_paths() -> list[str]:
    return [line.replace("\\", "/") for line in git_lines(["show", "--name-only", "--format=", "HEAD"])]


def control_flags_ok(payload: dict[str, Any], file_name: str, failures: list[dict[str, Any]]) -> None:
    expected = {
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_result_scoring": False,
        "opens_live_wiring": False,
        "opens_paid_api_or_databento_route": False,
        "opens_registry_edit": False,
        "changes_live_trading_behavior": False,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            failures.append({"check": "control_flag", "file": file_name, "key": key, "actual": payload.get(key)})


def forbidden_paths(paths: list[str]) -> list[str]:
    return [
        path
        for path in paths
        if path.startswith(FORBIDDEN_LIVE_PREFIXES) and not path.startswith(ALLOWED_DIR_PREFIXES)
    ]


def upstream_core_survived(upstream: dict[str, Any]) -> bool:
    parsed = upstream.get("parsed_stdout") or {}
    if upstream.get("returncode") == 0 and parsed.get("ok") is True:
        return True
    failures = parsed.get("failures") or []
    audit_dir = str(OUT_DIR.relative_to(REPO_ROOT)).replace("\\", "/") + "/"
    dirty_only = bool(failures) and all(
        failure.get("check") == "outside_scope_dirty" and failure.get("paths") == [audit_dir]
        for failure in failures
    )
    return (
        dirty_only
        and parsed.get("projection_row_count") == 298
        and parsed.get("family_counts") == {"accepted": 225, "reject": 65, "source_control": 4, "source_impossible": 4}
        and parsed.get("source_hash_records") == 56
        and parsed.get("parser_hash_records") == 3
        and not upstream.get("stderr_tail")
    )


def main() -> int:
    failures: list[dict[str, Any]] = []
    missing = [name for name in REQUIRED_FILES if not (OUT_DIR / name).exists()]
    if missing:
        failures.append({"check": "required_files", "missing": missing})

    parsed: dict[str, Any] = {}
    for name in REQUIRED_FILES:
        if name.endswith(".json") and (OUT_DIR / name).exists():
            try:
                parsed[name] = load_json(name)
            except json.JSONDecodeError as exc:
                failures.append({"check": "json_parse", "file": name, "error": str(exc)})

    try:
        rows = load_jsonl(PROJECTION_DIR / f"NOFILL_FORWARD_SOURCE_SAFE_PROJECTION_ROWS_{DATE}.jsonl")
    except Exception as exc:  # pragma: no cover - verifier output path
        rows = []
        failures.append({"check": "projection_jsonl_parse", "error": str(exc)})
    if len(rows) != 298:
        failures.append({"check": "projection_jsonl_row_count", "actual": len(rows)})

    for name, payload in parsed.items():
        if isinstance(payload, dict) and payload.get("route_id") == ROUTE_ID:
            control_flags_ok(payload, name, failures)

    decision = parsed.get(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_DECISION_LEDGER_{DATE}.json", {})
    if decision.get("terminal_decision") != TERMINAL_ACCEPT:
        failures.append({"check": "terminal_decision", "actual": decision.get("terminal_decision")})
    if decision.get("can_accept_as_source_control_projection_evidence_only") is not True:
        failures.append({"check": "acceptance_scope_flag", "actual": decision.get("can_accept_as_source_control_projection_evidence_only")})
    if decision.get("blocking_failures"):
        failures.append({"check": "blocking_failures", "actual": decision.get("blocking_failures")})
    closure = {item.get("issue_id"): item.get("reaudit_status") for item in decision.get("blocker_closure", [])}
    for issue_id in ("G12-PROJ-BLOCKER-001", "G12-PROJ-BLOCKER-002", "G12-PROJ-WARN-001"):
        if closure.get(issue_id) != "CLOSED":
            failures.append({"check": "blocker_closure", "issue_id": issue_id, "actual": closure.get(issue_id)})

    recomputation = parsed.get(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_RECOMPUTATION_LEDGER_{DATE}.json", {})
    upstream = recomputation.get("upstream_verifier_after_live_state_regeneration", {})
    if not upstream_core_survived(upstream):
        failures.append({"check": "upstream_verifier_after_live_state", "value": upstream})

    denominator = parsed.get(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_DENOMINATOR_AUDIT_{DATE}.json", {})
    if denominator.get("status") != "PASS":
        failures.append({"check": "denominator_status", "value": denominator.get("status"), "issues": denominator.get("issues")})
    expected_family = {"accepted": 225, "reject": 65, "source_control": 4, "source_impossible": 4}
    if denominator.get("family_counts") != expected_family:
        failures.append({"check": "family_counts", "value": denominator.get("family_counts")})
    if (
        denominator.get("accepted_row_level_denominator"),
        denominator.get("primary_duplicate_key_denominator"),
        denominator.get("secondary_duplicate_group_denominator"),
    ) != (225, 182, 139):
        failures.append({"check": "denominator_values", "value": denominator})
    if denominator.get("reject_overlap_rows_recomputed_by_key") != 47:
        failures.append({"check": "reject_overlap_rows", "value": denominator.get("reject_overlap_rows_recomputed_by_key")})

    source_hash = parsed.get(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_SOURCE_HASH_AUDIT_{DATE}.json", {})
    if source_hash.get("status") != "PASS" or source_hash.get("hash_recompute", {}).get("status") != "PASS":
        failures.append({"check": "source_hash_status", "value": source_hash.get("hash_recompute")})

    allowlist = parsed.get(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_ALLOWLIST_AUDIT_{DATE}.json", {})
    if allowlist.get("status") != "PASS" or allowlist.get("allowed_fields_equal_emitted_keys") is not True:
        failures.append({"check": "allowlist_status", "value": allowlist})
    if allowlist.get("fields_outside_exhaustive_allowlist") or allowlist.get("unused_exhaustive_allowlist_fields"):
        failures.append({"check": "allowlist_exactness", "value": allowlist})

    missing_status = parsed.get(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_MISSING_STATUS_AUDIT_{DATE}.json", {})
    if missing_status.get("status") != "PASS" or missing_status.get("collapsed_to_source_field_missing_rows") != 0:
        failures.append({"check": "missing_status_semantics", "value": missing_status})
    if missing_status.get("touch_not_observed_value_not_applicable_rows") != 113:
        failures.append({"check": "touch_not_observed_count", "value": missing_status})

    no_leak = parsed.get(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_NO_LEAK_AUDIT_{DATE}.json", {})
    if no_leak.get("status") != "PASS":
        failures.append({"check": "no_leak_status", "value": no_leak})
    for key in ("forbidden_projection_key_hits", "forbidden_projection_value_token_hits", "closed_control_flag_issues", "spread_source_issues"):
        if no_leak.get(key):
            failures.append({"check": key, "value": no_leak.get(key)})

    local_heavy = parsed.get(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_SEARCH_LEDGER_{DATE}.json", {})
    if local_heavy.get("status") != "PASS" or local_heavy.get("prior_worktree_extra_needed_matches"):
        failures.append({"check": "local_heavy_search", "value": local_heavy})

    live_surface = parsed.get(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_LIVE_SURFACE_SCOPE_AUDIT_{DATE}.json", {})
    if live_surface.get("status") != "PASS" or live_surface.get("forbidden_live_surface_paths"):
        failures.append({"check": "live_surface_artifact", "value": live_surface})

    completion = parsed.get(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_COMPLETION_AUDIT_{DATE}.json", {})
    if completion.get("status") != "PASS" or completion.get("can_mark_goal_complete_after_verification_and_commit") is not True:
        failures.append({"check": "completion_audit", "value": completion})

    dirty_forbidden = forbidden_paths(status_paths())
    if dirty_forbidden:
        failures.append({"check": "dirty_forbidden_live_surface_paths", "paths": dirty_forbidden})
    head_forbidden = forbidden_paths(head_commit_paths())
    if head_forbidden:
        failures.append({"check": "head_commit_forbidden_live_surface_paths", "paths": head_forbidden})

    result = {
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "failures": failures,
        "route_id": ROUTE_ID,
        "terminal_decision": decision.get("terminal_decision"),
        "projection_row_count": len(rows),
        "family_counts": denominator.get("family_counts"),
        "source_hash_records": source_hash.get("hash_recompute", {}).get("source_hash_records"),
        "parser_hash_records": source_hash.get("hash_recompute", {}).get("parser_hash_records"),
        "required_file_count": len(REQUIRED_FILES),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
