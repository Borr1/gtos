from __future__ import annotations

import ast
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_FVG_OB_SOURCE_BUCKET_SCORER_DECISION_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_FVG_OB_SOURCE_BUCKET_SCORER_DECISION_SUMMARY_{DATE}.json"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_KILL_SCOPE_PRESERVATION_AUDIT_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_KILL_SCOPE_PRESERVATION_AUDIT_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_KILL_SCOPE_PRESERVATION_AUDIT_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH24_KILL_SCOPE_PRESERVATION_AUDIT_VERIFICATION_RESULT_{DATE}.json"

EXPECTED_ACTION_COUNTS = {
    "IMPLEMENT_DEFAULT_OFF": 518,
    "KEEP": 942,
    "KILL": 1098,
    "PRESERVE_REQUIREMENT": 22,
    "REDESIGN": 846,
}
EXPECTED_KILL_BRANCH_COUNTS = {
    "KILL_FAR_MISS_050R_OFFSET_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL": 84,
    "KILL_OR_AVOID_ACCEPTED_SOURCE_BRANCH_UNTIL_EXACT_SOURCE_REPAIR": 47,
    "KILL_PREFILL_050R_OFFSET_NO_FILL_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL": 84,
    "KILL_ROW_NOT_FVG_OB_CONFLUENCE": 273,
    "KILL_ROW_NOT_STANDALONE_FVG_POI": 518,
    "KILL_ROW_NOT_SWING_PROTECTED_STOP": 89,
    "KILL_SOURCE_REPAIR_UPGRADED_CHALLENGER_AFTER_ORDERING_NEGATIVE_PROXY": 3,
}
EXPECTED_STATUS_COUNTS = {
    "KILL_SCOPE_AUDIT_ALREADY_PRESENT": 791,
    "KILL_SCOPE_AUDIT_REPAIRED_FROM_BRANCH_DECISION": 307,
    "NOT_KILL_ROW": 2328,
}


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            row = json.loads(stripped)
            row["_line_no"] = line_no
            rows.append(row)
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter("" if row.get(field) is None else str(row.get(field)) for row in rows))


def check(name: str, ok: bool, detail: Any = None) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {"numeric_proxy_rows": len(values), "proxy_r_sum": round(sum(values), 8)}


def has_metadata_gap(row: dict[str, Any]) -> bool:
    return (
        row.get("decision_evidence") in (None, "")
        or row.get("scoring_boundary") in (None, "")
        or row.get("implementation_candidate") in (None, "")
        or str(row.get("current_action")) in {"None", "False", ""}
        or str(row.get("next_action")) in {"None", "False", ""}
    )


def kill_audit_present(row: dict[str, Any]) -> bool:
    audit = row.get("missed_opportunity_audit")
    return (
        row.get("claim_decision_scope")
        == "CURRENT_STRATEGY_CLAIM_ONLY_UNDERLYING_INTELLIGENCE_PRESERVED"
        and row.get("underlying_intelligence_preserved") is True
        and isinstance(audit, dict)
        and audit.get("kill_scope") == "CURRENT_CLAIM_ONLY"
        and bool(audit.get("what_was_tried"))
        and bool(audit.get("what_could_make_it_work"))
        and bool(audit.get("preserve_as"))
        and bool(audit.get("next_route"))
    )


def ast_parse_ok(path: Path) -> tuple[bool, str | None]:
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return False, str(exc)
    return True, None


def main() -> None:
    repo_root = find_repo_root(ROUTE_DIR)
    build_script = ROUTE_DIR / "build_main_orchestrator_kill_scope_preservation_audit_2026_05_17.py"
    verify_script = Path(__file__).resolve()
    source_file = repo_root / "src/research_infra/live_mechanical_shadow.py"
    test_file = repo_root / "tests/test_live_mechanical_shadow.py"
    required_paths = [
        build_script,
        verify_script,
        source_file,
        test_file,
        INPUT_LEDGER,
        INPUT_SUMMARY,
        OUTPUT_LEDGER,
        OUTPUT_SUMMARY,
        OUTPUT_MANIFEST,
    ]
    checks = [check(f"{path.name}_exists", path.exists(), str(path)) for path in required_paths]

    input_rows = read_jsonl(INPUT_LEDGER)
    output_rows = read_jsonl(OUTPUT_LEDGER)
    input_summary = read_json(INPUT_SUMMARY)
    summary = read_json(OUTPUT_SUMMARY)
    manifest = read_json(OUTPUT_MANIFEST)
    input_proxy = proxy_summary(input_rows)
    output_proxy = proxy_summary(output_rows)
    kill_rows = [row for row in output_rows if row.get("action_class") == "KILL"]
    audited_kills = [row for row in kill_rows if kill_audit_present(row)]

    checks.append(check("route_id_matches", summary.get("route_id") == ROUTE_ID and manifest.get("route_id") == ROUTE_ID))
    checks.append(check("safe_flags_closed", summary.get("safe_flags") == SAFE_FLAGS and manifest.get("safe_flags") == SAFE_FLAGS))
    checks.append(check("row_count_preserved", len(input_rows) == len(output_rows) == summary.get("rows") == 3426))
    checks.append(check("previous_summary_matches_input", input_summary.get("rows") == len(input_rows)))
    checks.append(check("kill_rows_expected", len(kill_rows) == summary.get("kill_rows") == 1098))
    checks.append(check("all_kills_have_audit", len(audited_kills) == summary.get("kill_audit_rows_after") == 1098))
    checks.append(check("kill_audit_repair_counts", summary.get("kill_audit_rows_before") == 791 and summary.get("kill_audit_rows_repaired") == 307 and summary.get("kill_audit_mapping_missing") == 0))
    checks.append(check("status_counts_expected", summary.get("kill_scope_preservation_status_counts") == EXPECTED_STATUS_COUNTS and counter(output_rows, "kill_scope_preservation_audit_status") == EXPECTED_STATUS_COUNTS))
    checks.append(check("kill_branch_counts_expected", summary.get("kill_branch_counts") == EXPECTED_KILL_BRANCH_COUNTS and counter(kill_rows, "branch_decision") == EXPECTED_KILL_BRANCH_COUNTS))
    checks.append(check("action_counts_preserved", summary.get("action_class_counts_after") == EXPECTED_ACTION_COUNTS and counter(output_rows, "action_class") == EXPECTED_ACTION_COUNTS))
    checks.append(check("no_metadata_gaps", summary.get("all_metadata_gaps_after") == 0 and sum(1 for row in output_rows if has_metadata_gap(row)) == 0))
    checks.append(check("exact_r_rows_zero", summary.get("exact_r_rows") == 0 and all(row.get("exact_r") is None for row in output_rows)))
    checks.append(check("proxy_r_preserved", input_proxy == output_proxy == {"numeric_proxy_rows": 1416, "proxy_r_sum": 396.47201587} and summary.get("proxy_r_sum_delta") == 0.0))
    checks.append(check("preserved_proxy_summary_expected", summary.get("preserved_proxy_rows_from_kill_audits") == 642 and summary.get("preserved_proxy_r_sum_from_kill_audits") == 185.573329))

    row_errors: list[dict[str, Any]] = []
    input_by_row_id = {row.get("row_id"): row for row in input_rows}
    for row in output_rows:
        before = input_by_row_id.get(row.get("row_id"))
        if before is None:
            row_errors.append({"line": row["_line_no"], "error": "row_id_not_in_input", "row_id": row.get("row_id")})
            continue
        for field in ("candidate_id", "strategy_id", "action_class", "branch_decision", "after_proxy_r", "exact_r"):
            if row.get(field) != before.get(field):
                row_errors.append({"line": row["_line_no"], "error": f"{field}_changed", "row_id": row.get("row_id")})
                break
        if row.get("safe_flags") != before.get("safe_flags") or row.get("no_live_behavior") is not True or row.get("no_promotion") is not True:
            row_errors.append({"line": row["_line_no"], "error": "safe_flag_or_no_effect_mismatch", "row_id": row.get("row_id")})
        if row.get("action_class") == "KILL" and not kill_audit_present(row):
            row_errors.append({"line": row["_line_no"], "error": "kill_missing_preservation_audit", "row_id": row.get("row_id")})
    checks.append(check("rows_preserve_identity_action_r_and_safety", not row_errors, row_errors[:20]))

    manifest_input_errors = []
    for artifact_name, artifact in manifest.get("input_artifacts", {}).items():
        path = repo_root / artifact_name
        if not path.exists():
            manifest_input_errors.append({"path": artifact_name, "error": "path_missing"})
            continue
        if artifact.get("sha256") != sha256_file(path):
            manifest_input_errors.append({"path": artifact_name, "error": "sha256_mismatch"})
        if artifact.get("size_bytes") != path.stat().st_size:
            manifest_input_errors.append({"path": artifact_name, "error": "size_mismatch"})
    checks.append(check("manifest_input_hashes_match", not manifest_input_errors, manifest_input_errors))

    manifest_output_errors = []
    for path in [OUTPUT_LEDGER, OUTPUT_SUMMARY]:
        artifact = manifest.get("output_artifacts", {}).get(path.name)
        if not artifact:
            manifest_output_errors.append({"path": path.name, "error": "missing_manifest_output"})
            continue
        if artifact.get("sha256") != sha256_file(path):
            manifest_output_errors.append({"path": path.name, "error": "sha256_mismatch"})
        if artifact.get("size_bytes") != path.stat().st_size:
            manifest_output_errors.append({"path": path.name, "error": "size_mismatch"})
    checks.append(check("manifest_output_hashes_match", not manifest_output_errors, manifest_output_errors))

    for path in [source_file, test_file, build_script, verify_script]:
        ok, error = ast_parse_ok(path)
        checks.append(check(f"{path.name}_ast_parse_ok", ok, error))

    ok = all(item["ok"] for item in checks)
    result = {
        "route_id": ROUTE_ID,
        "ok": ok,
        "checks": checks,
        "counts": {
            "rows": len(output_rows),
            "kill_rows": len(kill_rows),
            "kill_audit_rows_after": len(audited_kills),
            "action_class_counts_after": counter(output_rows, "action_class"),
            "numeric_proxy_rows_after": output_proxy["numeric_proxy_rows"],
            "proxy_r_sum_after": output_proxy["proxy_r_sum"],
            "preserved_proxy_rows_from_kill_audits": summary.get("preserved_proxy_rows_from_kill_audits"),
            "preserved_proxy_r_sum_from_kill_audits": summary.get("preserved_proxy_r_sum_from_kill_audits"),
        },
        "plate_decision": "KILL_SCOPE_PRESERVATION_AUDIT_ACCEPTED_NO_PROMOTION",
        "can_mark_kill_scope_preservation_audit_complete": ok,
        "can_mark_active_24h_goal_complete": False,
        "safe_flags": SAFE_FLAGS,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "verification": str(VERIFY_RESULT)}, sort_keys=True))


if __name__ == "__main__":
    main()
