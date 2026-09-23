"""Verify structural duplicate merge materialization."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = find_repo_root(ROUTE_DIR)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from build_main_orchestrator_structural_duplicate_merge_2026_05_17 import (  # noqa: E402
    CANONICAL_STRATEGY_ID,
    MERGE_BRANCH,
    STRUCTURAL_PRIMITIVE,
    sha256_file,
    write_json,
)


OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_DUPLICATE_MERGE_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_DUPLICATE_MERGE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_DUPLICATE_MERGE_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_DUPLICATE_MERGE_VERIFICATION_RESULT_{DATE}.json"

EXPECTED_ACTION_COUNTS = {
    "IMPLEMENT_DEFAULT_OFF": 518,
    "KEEP": 1026,
    "KILL": 967,
    "PRESERVE_REQUIREMENT": 63,
    "REDESIGN": 852,
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_line_no"] = line_no
            rows.append(row)
    return rows


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def append_check(checks: list[dict[str, Any]], name: str, ok: bool, detail: Any = None) -> None:
    checks.append({"name": name, "ok": bool(ok), "detail": detail})


def verify_manifest(manifest: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    for section in ("input_artifacts", "output_artifacts"):
        for raw_path, expected in manifest.get(section, {}).items():
            path = REPO_ROOT / raw_path if section == "input_artifacts" else ROUTE_DIR / raw_path
            append_check(checks, f"{section}:{raw_path}:exists", path.exists())
            if not path.exists():
                continue
            append_check(checks, f"{section}:{raw_path}:sha256", sha256_file(path) == expected.get("sha256"))
            append_check(checks, f"{section}:{raw_path}:size", path.stat().st_size == expected.get("size_bytes"))


def repaired_audit_present(row: dict[str, Any]) -> bool:
    audit = row.get("missed_opportunity_audit")
    return (
        row.get("structural_duplicate_merge_status")
        == "MERGED_DUPLICATE_SHARED_PATH_PROXY_INTO_CANONICAL_SCORER"
        and row.get("branch_decision") == MERGE_BRANCH
        and row.get("after_proxy_r") is None
        and row.get("current_claim_proxy_counted") is False
        and row.get("canonical_strategy_id") == CANONICAL_STRATEGY_ID
        and isinstance(audit, dict)
        and audit.get("kill_scope") == "NOT_KILLED_MERGED_DUPLICATE_POSITIVE_PROXY_EVIDENCE"
        and bool(audit.get("what_was_tried"))
        and bool(audit.get("what_could_make_it_work"))
        and bool(audit.get("preserve_as"))
        and bool(audit.get("next_route"))
    )


def main() -> None:
    checks: list[dict[str, Any]] = []
    rows = read_jsonl(OUTPUT_LEDGER)
    summary = read_json(OUTPUT_SUMMARY)
    manifest = read_json(OUTPUT_MANIFEST)
    action_counts = dict(Counter(str(row.get("action_class") or "") for row in rows))
    structural = [row for row in rows if row.get("primitive_family") == STRUCTURAL_PRIMITIVE]
    canonical = [
        row
        for row in rows
        if row.get("structural_duplicate_merge_status") == "CANONICAL_STRUCTURAL_LOCK_PROXY_COUNTED"
    ]
    merged = [
        row
        for row in rows
        if row.get("structural_duplicate_merge_status")
        == "MERGED_DUPLICATE_SHARED_PATH_PROXY_INTO_CANONICAL_SCORER"
    ]
    merged_values = [safe_float(row.get("merged_duplicate_proxy_reference_r")) for row in merged]
    merged_numeric = [value for value in merged_values if value is not None]
    canonical_values = [safe_float(row.get("after_proxy_r")) for row in canonical]
    canonical_numeric = [value for value in canonical_values if value is not None]
    by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in structural:
        by_candidate[str(row.get("candidate_id") or "")].append(row)

    append_check(checks, "row_count", len(rows) == 3426, len(rows))
    append_check(checks, "summary_row_count", summary.get("rows") == len(rows), summary.get("rows"))
    append_check(checks, "action_counts_unchanged", action_counts == EXPECTED_ACTION_COUNTS, action_counts)
    append_check(checks, "structural_row_count", len(structural) == 1096, len(structural))
    append_check(checks, "canonical_count", len(canonical) == 274, len(canonical))
    append_check(checks, "merged_count", len(merged) == 822, len(merged))
    append_check(checks, "candidate_group_count", len(by_candidate) == 274, len(by_candidate))
    append_check(checks, "candidate_group_sizes", all(len(group) == 4 for group in by_candidate.values()))
    append_check(checks, "merged_audits_present", all(repaired_audit_present(row) for row in merged))
    append_check(checks, "canonical_proxy_rows", len(canonical_numeric) == 188, len(canonical_numeric))
    append_check(checks, "canonical_proxy_sum", round(sum(canonical_numeric), 8) == 59.0, sum(canonical_numeric))
    append_check(checks, "merged_numeric_reference_rows", len(merged_numeric) == 564, len(merged_numeric))
    append_check(checks, "merged_proxy_reference_sum", round(sum(merged_numeric), 8) == 177.0, sum(merged_numeric))
    append_check(checks, "numeric_proxy_rows_after", summary.get("numeric_proxy_rows_after") == 911)
    append_check(checks, "proxy_sum_after", summary.get("proxy_r_sum_after") == 231.47201587)
    append_check(checks, "proxy_rows_delta", summary.get("numeric_proxy_rows_delta") == -564)
    append_check(checks, "proxy_sum_delta", summary.get("proxy_r_sum_delta") == -177.0)
    append_check(checks, "exact_r_zero", summary.get("exact_r_rows") == 0)
    append_check(
        checks,
        "safe_flags_closed",
        summary.get("safe_flags")
        == {
            "NO_PROMOTION_VERDICT": True,
            "live_effect": False,
            "outcome_review_opened": False,
            "validation_safe": False,
        },
    )
    verify_manifest(manifest, checks)

    verified = all(check["ok"] for check in checks)
    result = {
        "schema_version": "main_orch24_structural_duplicate_merge_verifier_v1",
        "verified": verified,
        "decision": (
            "STRUCTURAL_DUPLICATE_MERGE_VERIFIED"
            if verified
            else "STRUCTURAL_DUPLICATE_MERGE_REJECTED"
        ),
        "checks": checks,
        "summary": {
            "rows": len(rows),
            "structural_rows": len(structural),
            "canonical_rows": len(canonical),
            "merged_duplicate_rows": len(merged),
            "numeric_proxy_rows_after": summary.get("numeric_proxy_rows_after"),
            "proxy_r_sum_after": summary.get("proxy_r_sum_after"),
            "proxy_r_sum_delta": summary.get("proxy_r_sum_delta"),
        },
    }
    write_json(VERIFY_RESULT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not verified:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
