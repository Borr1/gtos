"""Verify pending hypothetical shared-path proxy redesign materialization."""

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

from build_main_orchestrator_pending_hypothetical_merge_2026_05_17 import (  # noqa: E402
    NEW_BRANCH,
    TARGET_BRANCH,
    TARGET_PRIMITIVE,
    sha256_file,
    write_json,
)


OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_HYPOTHETICAL_MERGE_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_HYPOTHETICAL_MERGE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_HYPOTHETICAL_MERGE_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_HYPOTHETICAL_MERGE_VERIFICATION_RESULT_{DATE}.json"

EXPECTED_ACTION_COUNTS = {
    "IMPLEMENT_DEFAULT_OFF": 642,
    "KEEP": 432,
    "KILL": 967,
    "PRESERVE_REQUIREMENT": 63,
    "REDESIGN": 1322,
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> None:
    checks: list[dict[str, Any]] = []
    rows = read_jsonl(OUTPUT_LEDGER)
    summary = read_json(OUTPUT_SUMMARY)
    manifest = read_json(OUTPUT_MANIFEST)
    action_counts = dict(Counter(str(row.get("action_class") or "") for row in rows))
    canonical = [
        row
        for row in rows
        if row.get("pending_hypothetical_merge_status") == "CANONICAL_SHARED_PATH_PROXY_EXCLUDED_REDESIGN"
    ]
    duplicate = [
        row
        for row in rows
        if row.get("pending_hypothetical_merge_status") == "DUPLICATE_SHARED_PATH_PROXY_REFERENCE_REDESIGN"
    ]
    stale_target = [
        row
        for row in rows
        if row.get("primitive_family") == TARGET_PRIMITIVE and row.get("branch_decision") == TARGET_BRANCH
    ]
    new_branch_rows = [
        row
        for row in rows
        if row.get("primitive_family") == TARGET_PRIMITIVE and row.get("branch_decision") == NEW_BRANCH
    ]
    canonical_values = [
        value for row in canonical if (value := safe_float(row.get("pending_hypothetical_proxy_reference_r"))) is not None
    ]
    duplicate_values = [
        value for row in duplicate if (value := safe_float(row.get("pending_hypothetical_proxy_reference_r"))) is not None
    ]

    append_check(checks, "row_count", len(rows) == 3426, len(rows))
    append_check(checks, "summary_row_count", summary.get("rows") == len(rows), summary.get("rows"))
    append_check(checks, "action_counts", action_counts == EXPECTED_ACTION_COUNTS, action_counts)
    append_check(checks, "canonical_redesign_count", len(canonical) == 235, len(canonical))
    append_check(checks, "duplicate_redesign_count", len(duplicate) == 235, len(duplicate))
    append_check(checks, "new_branch_count", len(new_branch_rows) == 470, len(new_branch_rows))
    append_check(checks, "stale_target_zero", len(stale_target) == 0, len(stale_target))
    append_check(checks, "canonical_numeric_reference_rows", len(canonical_values) == 160, len(canonical_values))
    append_check(checks, "canonical_proxy_reference_sum", round(sum(canonical_values), 8) == 50.0, round(sum(canonical_values), 8))
    append_check(checks, "duplicate_numeric_reference_rows", len(duplicate_values) == 160, len(duplicate_values))
    append_check(checks, "duplicate_proxy_reference_sum", round(sum(duplicate_values), 8) == 50.0, round(sum(duplicate_values), 8))
    append_check(checks, "canonical_after_proxy_none", all(row.get("after_proxy_r") is None for row in canonical))
    append_check(checks, "duplicate_after_proxy_none", all(row.get("after_proxy_r") is None for row in duplicate))
    append_check(
        checks,
        "redesign_rows_shape",
        all(
            row.get("action_class") == "REDESIGN"
            and row.get("coverage_status") == "REDESIGN_REQUIRED_SHARED_PATH_PROXY_NOT_DISTINCT"
            and row.get("underlying_intelligence_preserved") is True
            and str(row.get("implementation_candidate") or "").startswith("REDESIGN_PENDING_LIMIT_ENTRY_MODEL")
            for row in canonical + duplicate
        ),
    )
    append_check(checks, "numeric_proxy_rows_after", summary.get("numeric_proxy_rows_after") == 551)
    append_check(checks, "proxy_sum_after", summary.get("proxy_r_sum_after") == 134.47201587)
    append_check(checks, "proxy_rows_delta", summary.get("numeric_proxy_rows_delta") == -160)
    append_check(checks, "proxy_sum_delta", summary.get("proxy_r_sum_delta") == -50.0)
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
        "schema_version": "main_orch24_pending_hypothetical_merge_verifier_v1",
        "verified": verified,
        "decision": "PENDING_HYPOTHETICAL_MERGE_VERIFIED" if verified else "PENDING_HYPOTHETICAL_MERGE_REJECTED",
        "checks": checks,
        "summary": {
            "rows": len(rows),
            "canonical_redesign_rows": len(canonical),
            "duplicate_redesign_rows": len(duplicate),
            "numeric_proxy_rows_after": summary.get("numeric_proxy_rows_after"),
            "proxy_r_sum_after": summary.get("proxy_r_sum_after"),
            "action_counts": action_counts,
        },
    }
    write_json(VERIFY_RESULT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not verified:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
