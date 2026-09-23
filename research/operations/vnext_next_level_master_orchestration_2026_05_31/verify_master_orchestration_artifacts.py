from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = ROOT / "research" / "operations" / "vnext_next_level_master_orchestration_2026_05_31"

REQUIRED = [
    "MASTER_ROUTE_REGISTRY.json",
    "MASTER_LANE_DEPENDENCY_GRAPH.json",
    "MASTER_TERMINAL_ACCEPTANCE_LEDGER.jsonl",
    "MASTER_EXTERNAL_DEPENDENCY_LEDGER.jsonl",
    "MASTER_SHARED_FILE_OWNERSHIP_LEDGER.jsonl",
    "MASTER_SCOPED_MERGE_STAGING_LEDGER.jsonl",
    "MASTER_SCOPED_MERGE_STAGING_PLAN.json",
    "MASTER_MERGE_READINESS_MATRIX.json",
    "MASTER_CROSS_LANE_BLOCKER_LEDGER.jsonl",
    "MASTER_CROSS_LANE_RESULT_MATERIALIZATION_LEDGER.jsonl",
    "MASTER_MARKET_COVERAGE_SEED_LEDGER.jsonl",
    "MASTER_EVIDENCE_INSPECTION_LEDGER.jsonl",
    "MASTER_SUBAGENT_AUDIT_LEDGER.jsonl",
    "MASTER_PROMPT_HARDENING_VERIFICATION.json",
    "MASTER_ORCHESTRATION_OUTPUT_MANIFEST.json",
    "MASTER_ORCHESTRATION_COMPLETION_AUDIT.json",
    "MASTER_ORCHESTRATION_FINAL_REPORT.md",
]


def count_jsonl(path: Path) -> int:
    return sum(1 for line in path.open("r", encoding="utf-8") if line.strip())


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    issues = []
    for name in REQUIRED:
        path = ROUTE_DIR / name
        if not path.exists() or path.stat().st_size <= 0:
            issues.append({"code": "missing_required_output", "path": str(path)})
    registry_path = ROUTE_DIR / "MASTER_ROUTE_REGISTRY.json"
    if registry_path.exists():
        registry = load_json(registry_path)
        if len(registry.get("lanes", [])) != 9:
            issues.append({"code": "registry_lane_count_mismatch", "actual": len(registry.get("lanes", []))})
        for lane in registry.get("lanes", []):
            if not lane.get("prompt_path") or not lane.get("starter_path") or not lane.get("route_path"):
                issues.append({"code": "lane_missing_required_path", "lane_id": lane.get("lane_id")})
    market_path = ROUTE_DIR / "MASTER_MARKET_COVERAGE_SEED_LEDGER.jsonl"
    if market_path.exists() and count_jsonl(market_path) != 24:
        issues.append({"code": "market_seed_not_24_symbols", "actual": count_jsonl(market_path)})
    acceptance_path = ROUTE_DIR / "MASTER_TERMINAL_ACCEPTANCE_LEDGER.jsonl"
    if acceptance_path.exists() and count_jsonl(acceptance_path) != 9:
        issues.append({"code": "terminal_acceptance_lane_count_mismatch", "actual": count_jsonl(acceptance_path)})
    shared_path = ROUTE_DIR / "MASTER_SHARED_FILE_OWNERSHIP_LEDGER.jsonl"
    if shared_path.exists() and count_jsonl(shared_path) < 10:
        issues.append({"code": "shared_file_ownership_ledger_too_narrow", "actual": count_jsonl(shared_path)})
    staging_path = ROUTE_DIR / "MASTER_SCOPED_MERGE_STAGING_LEDGER.jsonl"
    if staging_path.exists() and count_jsonl(staging_path) <= 0:
        issues.append({"code": "scoped_staging_ledger_empty"})
    staging_plan_path = ROUTE_DIR / "MASTER_SCOPED_MERGE_STAGING_PLAN.json"
    if staging_plan_path.exists():
        staging_plan = load_json(staging_plan_path)
        if not staging_plan.get("scoped_staging_review_complete"):
            issues.append({"code": "scoped_staging_review_not_complete"})
        staged_paths = set(staging_plan.get("staged_paths") or [])
        include_paths = set(staging_plan.get("include_candidate_paths") or [])
        unexpected_staged = sorted(staged_paths - include_paths)
        if unexpected_staged:
            issues.append({"code": "scoped_staging_contains_unapproved_paths", "paths": unexpected_staged})
        if staging_plan.get("include_candidate_count", 0) <= 0:
            issues.append({"code": "scoped_staging_has_no_include_candidates"})
        if not staged_paths and not staging_plan.get("scoped_commit_performed"):
            issues.append({"code": "scoped_package_not_staged_or_committed"})
        unstaged_candidates = staging_plan.get("unstaged_include_candidate_paths") or []
        if unstaged_candidates and not staging_plan.get("scoped_commit_performed"):
            issues.append({"code": "scoped_include_candidates_unstaged", "paths": unstaged_candidates[:50], "count": len(unstaged_candidates)})
        if staging_plan.get("scoped_commit_performed") and not staging_plan.get("scoped_commit_sha"):
            issues.append({"code": "scoped_commit_missing_sha"})
        if staging_plan.get("scoped_commit_forbidden_path_count"):
            issues.append({"code": "scoped_commit_contains_forbidden_paths", "count": staging_plan.get("scoped_commit_forbidden_path_count")})
    matrix_path = ROUTE_DIR / "MASTER_MERGE_READINESS_MATRIX.json"
    if matrix_path.exists():
        matrix = load_json(matrix_path)
        lane_rows = matrix.get("lane_rows", [])
        if len(lane_rows) != 9:
            issues.append({"code": "merge_readiness_lane_count_mismatch", "actual": len(lane_rows)})
        lane02 = next((row for row in lane_rows if row.get("lane_id") == "02"), {})
        lane09 = next((row for row in lane_rows if row.get("lane_id") == "09"), {})
        lane09_terminal = bool(lane09.get("master_terminal_accepted"))
        if lane02.get("master_terminal_accepted") and not lane09_terminal:
            issues.append({"code": "lane02_wrongly_master_terminal_accepted"})
        if not lane02.get("master_terminal_accepted") and "02" not in matrix.get("external_session_owned_lanes", []):
            issues.append({"code": "lane02_external_session_not_tracked"})
        held = {row.get("lane_id") for row in matrix.get("external_dependency_pending_lanes", [])}
        if not lane09_terminal and not {"03", "08"}.issubset(held):
            issues.append({"code": "lane03_lane08_external_dependency_hold_missing", "actual": sorted(held)})
        if lane09_terminal and (matrix.get("external_session_owned_lanes") or matrix.get("external_dependency_pending_lanes")):
            issues.append({"code": "lane09_terminal_but_external_dependency_not_cleared"})
        if matrix.get("completion_ready"):
            issues.append({"code": "merge_readiness_claimed_too_early"})
    completion_ready = False
    audit_path = ROUTE_DIR / "MASTER_ORCHESTRATION_COMPLETION_AUDIT.json"
    if audit_path.exists():
        completion_ready = bool(load_json(audit_path).get("completion_ready"))
    result = {
        "completion_ready": completion_ready,
        "issue_count": len(issues),
        "issues": issues,
        "ok": not issues,
        "route_dir": str(ROUTE_DIR.relative_to(ROOT)).replace("\\", "/"),
        "schema_version": "vnext_next_level_master_route_verification_v1",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
