"""Verify GBPJPY LONG adverse-cluster redesign reclassification."""

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

from build_main_orchestrator_gbpjpy_long_adverse_reclass_2026_05_17 import (  # noqa: E402
    NEW_BRANCH,
    TARGET_BRANCHES,
    sha256_file,
    write_json,
)


OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_GBPJPY_LONG_ADVERSE_RECLASS_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_GBPJPY_LONG_ADVERSE_RECLASS_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_GBPJPY_LONG_ADVERSE_RECLASS_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_GBPJPY_LONG_ADVERSE_RECLASS_VERIFICATION_RESULT_{DATE}.json"

EXPECTED_ACTION_COUNTS = {
    "IMPLEMENT_DEFAULT_OFF": 579,
    "KEEP": 432,
    "KILL": 967,
    "PRESERVE_REQUIREMENT": 64,
    "REDESIGN": 1384,
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
    reclassified = [
        row
        for row in rows
        if row.get("gbpjpy_long_adverse_reclass_status")
        == "RECLASSIFIED_IMPLEMENT_TO_REDESIGN_AVOID_FILTER_CANDIDATE"
    ]
    stale_target = [
        row
        for row in rows
        if row.get("action_class") == "IMPLEMENT_DEFAULT_OFF"
        and row.get("symbol") == "GBPJPY"
        and row.get("side") == "LONG"
        and row.get("branch_decision") in TARGET_BRANCHES
    ]
    numeric_values = [value for row in reclassified if (value := safe_float(row.get("after_proxy_r"))) is not None]

    append_check(checks, "row_count", len(rows) == 3426, len(rows))
    append_check(checks, "summary_row_count", summary.get("rows") == len(rows), summary.get("rows"))
    append_check(checks, "action_counts", action_counts == EXPECTED_ACTION_COUNTS, action_counts)
    append_check(checks, "reclassified_count", len(reclassified) == 62, len(reclassified))
    append_check(checks, "stale_target_zero", len(stale_target) == 0, len(stale_target))
    append_check(checks, "new_branch_count", sum(1 for row in rows if row.get("branch_decision") == NEW_BRANCH) == 62)
    append_check(checks, "numeric_rows_reclassified", len(numeric_values) == 22, len(numeric_values))
    append_check(checks, "numeric_sum_reclassified", round(sum(numeric_values), 8) == -22.0, round(sum(numeric_values), 8))
    append_check(
        checks,
        "reclassified_all_gbpjpy_long",
        all(row.get("symbol") == "GBPJPY" and row.get("side") == "LONG" for row in reclassified),
    )
    append_check(
        checks,
        "reclassified_shape",
        all(
            row.get("action_class") == "REDESIGN"
            and row.get("coverage_status") == "REDESIGN_REQUIRED_GBPJPY_LONG_ADVERSE_CLUSTER"
            and row.get("underlying_intelligence_preserved") is True
            and row.get("missed_opportunity_audit", {}).get("kill_scope")
            == "NOT_KILLED_REDESIGN_ADVERSE_CLUSTER"
            for row in reclassified
        ),
    )
    append_check(
        checks,
        "primitive_counts",
        Counter(row.get("primitive_family") for row in reclassified)
        == {
            "structural_lock_reentry_cost_metadata": 23,
            "fvg_ob_confluence_shared_path_scorer": 17,
            "structural_swing_protected_stop_geometry": 16,
            "tick_derived_structural_source_repair": 6,
        },
        dict(Counter(row.get("primitive_family") for row in reclassified)),
    )
    append_check(checks, "numeric_proxy_rows_after", summary.get("numeric_proxy_rows_after") == 550)
    append_check(checks, "proxy_sum_after", summary.get("proxy_r_sum_after") == 135.47201587)
    append_check(checks, "proxy_delta_zero", summary.get("proxy_r_sum_delta") == 0.0)
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
        "schema_version": "main_orch24_gbpjpy_long_adverse_reclass_verifier_v1",
        "verified": verified,
        "decision": "GBPJPY_LONG_ADVERSE_RECLASS_VERIFIED"
        if verified
        else "GBPJPY_LONG_ADVERSE_RECLASS_REJECTED",
        "checks": checks,
        "summary": {
            "rows": len(rows),
            "reclassified_rows": len(reclassified),
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
