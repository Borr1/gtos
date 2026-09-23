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

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_DECISION_SPREAD_REPAIR_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_DECISION_SPREAD_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_NOFILL_FORWARD_SPREAD_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_NOFILL_FORWARD_SPREAD_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / (
    f"MAIN_ORCH24_PENDING_LIFECYCLE_NOFILL_FORWARD_SPREAD_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
)
VERIFY_RESULT = ROUTE_DIR / (
    f"MAIN_ORCH24_PENDING_LIFECYCLE_NOFILL_FORWARD_SPREAD_REPAIR_VERIFICATION_RESULT_{DATE}.json"
)

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}
EXPECTED_ACTION_COUNTS = {
    "IMPLEMENT_DEFAULT_OFF": 518,
    "KEEP": 942,
    "KILL": 1098,
    "PRESERVE_REQUIREMENT": 22,
    "REDESIGN": 846,
}
EXPECTED_STATUS_COUNTS = {
    "NOT_PENDING_LIFECYCLE_ROW": 3152,
    "PENDING_LIFECYCLE_DECISION_SPREAD_REPAIRED_FROM_NOFILL_FORWARD_CAPTURE": 28,
    "PENDING_LIFECYCLE_LEGACY_SPREAD_REPAIR_PRESERVED": 3,
    "PENDING_LIFECYCLE_RECOMPUTE_APPLIED_NO_DECISION_SPREAD_REPAIR": 8,
    "PENDING_LIFECYCLE_RECOMPUTE_APPLIED_NO_INTERNAL_LIFECYCLE": 235,
}
EXPECTED_BEFORE_BRANCH_COUNTS = {
    "KEEP_PENDING_LIFECYCLE_HYPOTHETICAL_PATH_SCORER": 235,
    "KEEP_PENDING_LIFECYCLE_SCORER_WITH_DERIVED_SOURCE_FIELDS_CURRENT_ROWS_PARTIAL": 34,
    "KEEP_PENDING_LIFECYCLE_SCORER_WITH_RECONSTRUCTED_SOURCE_FIELDS_COMPLETE": 5,
}
EXPECTED_AFTER_BRANCH_COUNTS = {
    "KEEP_PENDING_LIFECYCLE_HYPOTHETICAL_PATH_SCORER": 235,
    "KEEP_PENDING_LIFECYCLE_SCORER_WITH_DERIVED_SOURCE_FIELDS_CURRENT_ROWS_PARTIAL": 8,
    "KEEP_PENDING_LIFECYCLE_SCORER_WITH_RECONSTRUCTED_SOURCE_FIELDS_COMPLETE": 31,
}
EXPECTED_BEFORE_STATUS_COUNTS = {
    "DERIVED_FROM_PENDING_LIFECYCLE_LEGACY_SPREAD_AS_DECISION_SPREAD_PROXY": 5,
    "NO_PENDING_LIFECYCLE_STATUS_MAP": 235,
    "SOURCE_NOT_CAPTURED_IN_CURRENT_ROW": 34,
}
EXPECTED_AFTER_STATUS_COUNTS = {
    "DERIVED_FROM_NOFILL_FORWARD_SOURCE_CAPTURE_DECISION_SPREAD": 28,
    "DERIVED_FROM_PENDING_LIFECYCLE_LEGACY_SPREAD_AS_DECISION_SPREAD_PROXY": 3,
    "NO_PENDING_LIFECYCLE_STATUS_MAP": 235,
    "SOURCE_NOT_CAPTURED_IN_CURRENT_ROW": 8,
}
EXPECTED_BEFORE_COMPLETE_COUNTS = {"": 235, "False": 34, "True": 5}
EXPECTED_AFTER_COMPLETE_COUNTS = {"": 235, "False": 8, "True": 31}
EXPECTED_NOFILL_CANDIDATES = [
    "GBPJPY_2026-05-11T07:30:00+00:00",
    "GBPJPY_2026-05-13T14:30:00+00:00",
    "NAS100_2026-05-11T09:15:00+00:00",
    "NAS100_2026-05-12T07:15:00+00:00",
    "NAS100_2026-05-13T07:15:00+00:00",
    "NAS100_2026-05-13T09:45:00+00:00",
    "NAS100_2026-05-13T10:30:00+00:00",
    "NAS100_2026-05-13T17:00:00+00:00",
    "NAS100_2026-05-14T14:15:00+00:00",
    "US30_cash_2026-05-11T08:15:00+00:00",
    "US30_cash_2026-05-12T09:30:00+00:00",
    "US30_cash_2026-05-14T10:00:00+00:00",
    "XAGUSD_2026-05-12T09:00:00+00:00",
    "XAGUSD_2026-05-13T07:15:00+00:00",
    "XAGUSD_2026-05-13T10:30:00+00:00",
    "XAGUSD_2026-05-13T13:15:00+00:00",
    "XAGUSD_2026-05-13T13:45:00+00:00",
    "XAGUSD_2026-05-13T14:15:00+00:00",
    "XAGUSD_2026-05-13T14:45:00+00:00",
    "XAGUSD_2026-05-13T15:15:00+00:00",
    "XAGUSD_2026-05-13T15:45:00+00:00",
    "XAGUSD_2026-05-13T16:15:00+00:00",
    "XAGUSD_2026-05-13T16:45:00+00:00",
    "XAGUSD_2026-05-14T09:00:00+00:00",
    "XAGUSD_2026-05-14T09:30:00+00:00",
    "XAGUSD_2026-05-14T10:00:00+00:00",
    "XAGUSD_2026-05-14T10:30:00+00:00",
    "XAGUSD_2026-05-14T13:15:00+00:00",
]


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


def nested_status_counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        statuses = row.get("pending_lifecycle_source_capture_statuses")
        if isinstance(statuses, dict):
            counts[str(statuses.get(field))] += 1
        else:
            counts["NO_PENDING_LIFECYCLE_STATUS_MAP"] += 1
    return dict(counts)


def proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {"numeric_proxy_rows": len(values), "proxy_r_sum": round(sum(values), 8)}


def pending_proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pending = [row for row in rows if row.get("strategy_id") == "PENDING_LIMIT_LIFECYCLE"]
    values = [value for row in pending if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {
        "pending_rows": len(pending),
        "pending_numeric_proxy_rows": len(values),
        "pending_proxy_r_sum": round(sum(values), 8),
    }


def check(name: str, ok: bool, detail: Any = None) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


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
    build_script = (
        ROUTE_DIR / "build_main_orchestrator_pending_lifecycle_nofill_forward_spread_repair_2026_05_17.py"
    )
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
    input_pending = [row for row in input_rows if row.get("strategy_id") == "PENDING_LIMIT_LIFECYCLE"]
    output_pending = [row for row in output_rows if row.get("strategy_id") == "PENDING_LIMIT_LIFECYCLE"]
    nofill_rows = [
        row
        for row in output_pending
        if row.get("pending_lifecycle_nofill_forward_spread_repair_status")
        == "PENDING_LIFECYCLE_DECISION_SPREAD_REPAIRED_FROM_NOFILL_FORWARD_CAPTURE"
    ]
    kill_rows = [row for row in output_rows if row.get("action_class") == "KILL"]

    checks.append(check("route_id_matches", summary.get("route_id") == ROUTE_ID and manifest.get("route_id") == ROUTE_ID))
    checks.append(check("safe_flags_closed", summary.get("safe_flags") == SAFE_FLAGS and manifest.get("safe_flags") == SAFE_FLAGS))
    checks.append(check("row_count_preserved", len(input_rows) == len(output_rows) == summary.get("rows") == 3426))
    checks.append(check("previous_summary_matches_input", input_summary.get("rows") == len(input_rows)))
    checks.append(check("pending_rows_expected", len(output_pending) == summary.get("pending_rows") == 274))
    checks.append(check("action_counts_preserved", summary.get("after_action_class_counts") == EXPECTED_ACTION_COUNTS and counter(output_rows, "action_class") == EXPECTED_ACTION_COUNTS))
    checks.append(check("status_counts_expected", summary.get("status_counts") == EXPECTED_STATUS_COUNTS and counter(output_rows, "pending_lifecycle_nofill_forward_spread_repair_status") == EXPECTED_STATUS_COUNTS))
    checks.append(check("branch_counts_expected", summary.get("before_pending_branch_counts") == EXPECTED_BEFORE_BRANCH_COUNTS and summary.get("after_pending_branch_counts") == EXPECTED_AFTER_BRANCH_COUNTS and counter(output_pending, "branch_decision") == EXPECTED_AFTER_BRANCH_COUNTS))
    checks.append(check("decision_spread_status_counts_expected", summary.get("before_pending_decision_spread_status_counts") == EXPECTED_BEFORE_STATUS_COUNTS and summary.get("after_pending_decision_spread_status_counts") == EXPECTED_AFTER_STATUS_COUNTS and nested_status_counter(output_pending, "decision_spread_value_source_safe") == EXPECTED_AFTER_STATUS_COUNTS))
    checks.append(check("source_complete_counts_expected", summary.get("before_pending_source_complete_counts") == EXPECTED_BEFORE_COMPLETE_COUNTS and summary.get("after_pending_source_complete_counts") == EXPECTED_AFTER_COMPLETE_COUNTS and counter(output_pending, "pending_lifecycle_source_capture_complete") == EXPECTED_AFTER_COMPLETE_COUNTS))
    checks.append(check("nofill_candidates_expected", summary.get("nofill_forward_decision_spread_rows") == len(nofill_rows) == 28 and summary.get("nofill_forward_decision_spread_candidates") == EXPECTED_NOFILL_CANDIDATES))
    checks.append(check("remaining_gap_expected", summary.get("remaining_pending_decision_spread_gaps") == 8 and summary.get("legacy_decision_spread_rows_after") == 3))
    checks.append(check("repair_stats_expected", summary.get("decision_repair_stats", {}).get("branch_changed") == 26 and summary.get("decision_repair_stats", {}).get("source_capture_complete_changed") == 26 and summary.get("decision_repair_stats", {}).get("proxy_changed", 0) == 0))
    checks.append(check("proxy_r_preserved", proxy_summary(input_rows) == proxy_summary(output_rows) == {"numeric_proxy_rows": 1416, "proxy_r_sum": 396.47201587} and summary.get("proxy_r_sum_delta") == 0.0))
    checks.append(check("pending_proxy_r_preserved", pending_proxy_summary(input_rows) == pending_proxy_summary(output_rows) == {"pending_rows": 274, "pending_numeric_proxy_rows": 197, "pending_proxy_r_sum": 50.0} and summary.get("pending_proxy_r_sum_delta") == 0.0))
    checks.append(check("exact_r_rows_zero", summary.get("exact_r_rows") == 0 and all(row.get("exact_r") is None for row in output_rows)))
    checks.append(check("no_metadata_gaps", summary.get("all_metadata_gaps_after") == 0 and sum(1 for row in output_rows if has_metadata_gap(row)) == 0))
    checks.append(check("kill_audits_preserved", summary.get("kill_scope_audited_rows_after") == 1098 and len([row for row in kill_rows if kill_audit_present(row)]) == 1098))

    nofill_errors: list[dict[str, Any]] = []
    for row in nofill_rows:
        statuses = row.get("pending_lifecycle_source_capture_statuses") or {}
        if row.get("pending_lifecycle_decision_spread_reconstruction_source") != "nofill_forward_source_capture":
            nofill_errors.append({"row_id": row.get("row_id"), "error": "source_not_nofill_forward"})
        if statuses.get("decision_spread_value_source_safe") != "DERIVED_FROM_NOFILL_FORWARD_SOURCE_CAPTURE_DECISION_SPREAD":
            nofill_errors.append({"row_id": row.get("row_id"), "error": "status_not_nofill_forward"})
        if statuses.get("decision_spread_unit") != "DERIVED_FROM_NOFILL_FORWARD_SOURCE_CAPTURE_DECISION_SPREAD":
            nofill_errors.append({"row_id": row.get("row_id"), "error": "unit_status_not_nofill_forward"})
        if row.get("pending_lifecycle_source_capture_complete") is not True:
            nofill_errors.append({"row_id": row.get("row_id"), "error": "source_not_complete"})
        if safe_float(row.get("before_pending_nofill_forward_spread_repair_after_proxy_r")) != safe_float(row.get("after_proxy_r")):
            nofill_errors.append({"row_id": row.get("row_id"), "error": "proxy_changed"})
    checks.append(check("nofill_rows_have_exact_source_derivation", not nofill_errors, nofill_errors[:20]))

    row_errors: list[dict[str, Any]] = []
    input_by_row_id = {row.get("row_id"): row for row in input_rows}
    for row in output_rows:
        before = input_by_row_id.get(row.get("row_id"))
        if before is None:
            row_errors.append({"line": row["_line_no"], "error": "row_id_not_in_input", "row_id": row.get("row_id")})
            continue
        for field in ("candidate_id", "strategy_id", "action_class", "exact_r"):
            if row.get(field) != before.get(field):
                row_errors.append({"line": row["_line_no"], "error": f"{field}_changed", "row_id": row.get("row_id")})
                break
        if safe_float(row.get("after_proxy_r")) != safe_float(before.get("after_proxy_r")):
            row_errors.append({"line": row["_line_no"], "error": "after_proxy_r_changed", "row_id": row.get("row_id")})
        if row.get("safe_flags") != before.get("safe_flags") or row.get("no_live_behavior") is not True or row.get("no_promotion") is not True:
            row_errors.append({"line": row["_line_no"], "error": "safe_flag_or_no_effect_mismatch", "row_id": row.get("row_id")})
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

    for path in [build_script, verify_script, source_file, test_file]:
        ok, detail = ast_parse_ok(path)
        checks.append(check(f"{path.name}_ast_parse_ok", ok, detail))

    ok = all(item["ok"] for item in checks)
    result = {
        "route_id": ROUTE_ID,
        "verified": ok,
        "checks": checks,
        "plate_decision": (
            "PENDING_LIFECYCLE_NOFILL_FORWARD_SPREAD_REPAIR_VERIFIED"
            if ok
            else "PENDING_LIFECYCLE_NOFILL_FORWARD_SPREAD_REPAIR_REJECTED"
        ),
        "summary_path": str(OUTPUT_SUMMARY.relative_to(repo_root)),
        "ledger_path": str(OUTPUT_LEDGER.relative_to(repo_root)),
        "safe_flags": SAFE_FLAGS,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
