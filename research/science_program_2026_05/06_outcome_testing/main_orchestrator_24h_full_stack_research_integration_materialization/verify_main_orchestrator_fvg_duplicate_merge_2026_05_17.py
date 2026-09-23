"""Verify standalone-FVG duplicate merge materialization."""

from __future__ import annotations

import json
import sys
from collections import Counter
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

from build_main_orchestrator_fvg_duplicate_merge_2026_05_17 import (  # noqa: E402
    CANONICAL_FVG_STRATEGY_ID,
    MERGE_BRANCH,
    sha256_file,
    write_json,
)


OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_DUPLICATE_MERGE_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_DUPLICATE_MERGE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_DUPLICATE_MERGE_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_DUPLICATE_MERGE_VERIFICATION_RESULT_{DATE}.json"

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
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def merge_audit_present(row: dict[str, Any]) -> bool:
    audit = row.get("missed_opportunity_audit")
    return (
        row.get("fvg_duplicate_merge_status") == "MERGED_DUPLICATE_FVG_SHARED_PATH_PROXY_INTO_CANONICAL_SCORER"
        and row.get("branch_decision") == MERGE_BRANCH
        and row.get("after_proxy_r") is None
        and row.get("current_claim_proxy_counted") is False
        and row.get("canonical_strategy_id") == CANONICAL_FVG_STRATEGY_ID
        and isinstance(audit, dict)
        and audit.get("kill_scope") == "NOT_KILLED_MERGED_DUPLICATE_FVG_REDESIGN_EVIDENCE"
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
    canonical = [
        row
        for row in rows
        if row.get("fvg_duplicate_merge_status") == "CANONICAL_STANDALONE_FVG_REDESIGN_PROXY_COUNTED"
    ]
    merged = [
        row
        for row in rows
        if row.get("fvg_duplicate_merge_status") == "MERGED_DUPLICATE_FVG_SHARED_PATH_PROXY_INTO_CANONICAL_SCORER"
    ]
    canonical_values = [value for row in canonical if (value := safe_float(row.get("after_proxy_r"))) is not None]
    merged_values = [
        value for row in merged if (value := safe_float(row.get("merged_duplicate_proxy_reference_r"))) is not None
    ]

    append_check(checks, "row_count", len(rows) == 3426, len(rows))
    append_check(checks, "summary_row_count", summary.get("rows") == len(rows), summary.get("rows"))
    append_check(checks, "action_counts_unchanged", action_counts == EXPECTED_ACTION_COUNTS, action_counts)
    append_check(checks, "canonical_count", len(canonical) == 12, len(canonical))
    append_check(checks, "merged_count", len(merged) == 12, len(merged))
    append_check(checks, "merged_audits_present", all(merge_audit_present(row) for row in merged))
    append_check(checks, "canonical_numeric_proxy_rows", len(canonical_values) == 3, len(canonical_values))
    append_check(checks, "canonical_proxy_sum", round(sum(canonical_values), 8) == -3.0, sum(canonical_values))
    append_check(checks, "merged_numeric_reference_rows", len(merged_values) == 3, len(merged_values))
    append_check(checks, "merged_proxy_reference_sum", round(sum(merged_values), 8) == -3.0, sum(merged_values))
    append_check(checks, "numeric_proxy_rows_after", summary.get("numeric_proxy_rows_after") == 908)
    append_check(checks, "proxy_sum_after", summary.get("proxy_r_sum_after") == 234.47201587)
    append_check(checks, "proxy_rows_delta", summary.get("numeric_proxy_rows_delta") == -3)
    append_check(checks, "proxy_sum_delta", summary.get("proxy_r_sum_delta") == 3.0)
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
        "schema_version": "main_orch24_fvg_duplicate_merge_verifier_v1",
        "verified": verified,
        "decision": "FVG_DUPLICATE_MERGE_VERIFIED" if verified else "FVG_DUPLICATE_MERGE_REJECTED",
        "checks": checks,
        "summary": {
            "rows": len(rows),
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
