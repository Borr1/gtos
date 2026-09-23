"""Verify FVG/OB exact-bounds source requirement materialization."""

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

from build_main_orchestrator_fvg_ob_exact_bounds_requirement_2026_05_17 import (  # noqa: E402
    NEW_BRANCH,
    TARGET_BRANCH,
    sha256_file,
    write_json,
)


OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_OB_EXACT_BOUNDS_REQUIREMENT_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_OB_EXACT_BOUNDS_REQUIREMENT_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_OB_EXACT_BOUNDS_REQUIREMENT_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_OB_EXACT_BOUNDS_REQUIREMENT_VERIFICATION_RESULT_{DATE}.json"

EXPECTED_ACTION_COUNTS = {
    "IMPLEMENT_DEFAULT_OFF": 641,
    "KEEP": 432,
    "KILL": 967,
    "PRESERVE_REQUIREMENT": 64,
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
    moved = [
        row
        for row in rows
        if row.get("fvg_ob_exact_bounds_requirement_status")
        == "MOVED_DEFAULT_OFF_ROW_TO_SOURCE_REQUIREMENT_EXACT_BOUNDS_MISSING"
    ]
    stale = [row for row in rows if row.get("branch_decision") == TARGET_BRANCH]
    new_branch_rows = [row for row in rows if row.get("branch_decision") == NEW_BRANCH]
    moved_values = [
        value for row in moved if (value := safe_float(row.get("fvg_ob_exact_bounds_proxy_reference_r"))) is not None
    ]

    append_check(checks, "row_count", len(rows) == 3426, len(rows))
    append_check(checks, "summary_row_count", summary.get("rows") == len(rows), summary.get("rows"))
    append_check(checks, "action_counts", action_counts == EXPECTED_ACTION_COUNTS, action_counts)
    append_check(checks, "moved_count", len(moved) == 1, len(moved))
    append_check(checks, "new_branch_count", len(new_branch_rows) == 1, len(new_branch_rows))
    append_check(checks, "stale_target_zero", len(stale) == 0, len(stale))
    append_check(checks, "moved_proxy_reference_rows", len(moved_values) == 1, len(moved_values))
    append_check(checks, "moved_proxy_reference_sum", round(sum(moved_values), 8) == -1.0, round(sum(moved_values), 8))
    append_check(
        checks,
        "moved_shape",
        all(
            row.get("action_class") == "PRESERVE_REQUIREMENT"
            and row.get("after_proxy_r") is None
            and row.get("coverage_status") == "SOURCE_REQUIREMENT_EXACT_FVG_OB_BOUNDS_MISSING"
            and row.get("underlying_intelligence_preserved") is True
            and row.get("missed_opportunity_audit", {}).get("kill_scope") == "NOT_KILLED_SOURCE_REQUIREMENT"
            for row in moved
        ),
    )
    append_check(checks, "numeric_proxy_rows_after", summary.get("numeric_proxy_rows_after") == 550)
    append_check(checks, "proxy_sum_after", summary.get("proxy_r_sum_after") == 135.47201587)
    append_check(checks, "proxy_rows_delta", summary.get("numeric_proxy_rows_delta") == -1)
    append_check(checks, "proxy_sum_delta", summary.get("proxy_r_sum_delta") == 1.0)
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
        "schema_version": "main_orch24_fvg_ob_exact_bounds_requirement_verifier_v1",
        "verified": verified,
        "decision": "FVG_OB_EXACT_BOUNDS_REQUIREMENT_VERIFIED"
        if verified
        else "FVG_OB_EXACT_BOUNDS_REQUIREMENT_REJECTED",
        "checks": checks,
        "summary": {
            "rows": len(rows),
            "moved_rows": len(moved),
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
