"""Verify current action ledger after pending tick-spread repair consumption."""

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

from build_main_orchestrator_pending_lifecycle_decision_spread_repair_2026_05_17 import (  # noqa: E402
    PENDING_LIMIT_STRATEGY_ID,
    kill_audit_present,
    sha256_file,
    write_json,
)


OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_TICK_SPREAD_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_TICK_SPREAD_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_TICK_SPREAD_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_TICK_SPREAD_REPAIR_VERIFICATION_RESULT_{DATE}.json"

EXPECTED_ACTION_COUNTS = {
    "IMPLEMENT_DEFAULT_OFF": 518,
    "KEEP": 1026,
    "KILL": 1014,
    "PRESERVE_REQUIREMENT": 16,
    "REDESIGN": 852,
}
EXPECTED_PENDING_BRANCH_COUNTS = {
    "KEEP_PENDING_LIFECYCLE_HYPOTHETICAL_PATH_SCORER": 235,
    "KEEP_PENDING_LIFECYCLE_SCORER_WITH_DERIVED_SOURCE_FIELDS_CURRENT_ROWS_PARTIAL": 1,
    "KEEP_PENDING_LIFECYCLE_SCORER_WITH_RECONSTRUCTED_SOURCE_FIELDS_COMPLETE": 38,
}
EXPECTED_PENDING_SPREAD_COUNTS = {
    "DERIVED_FROM_NOFILL_FORWARD_SOURCE_CAPTURE_DECISION_SPREAD": 28,
    "DERIVED_FROM_TICK_PARQUET_AT_OR_BEFORE_DECISION_SPREAD": 10,
    "NO_PENDING_LIFECYCLE_STATUS_MAP": 235,
    "SOURCE_NOT_CAPTURED_IN_CURRENT_ROW": 1,
}
EXPECTED_STATUS_COUNTS = {
    "NOT_PENDING_LIFECYCLE_ROW": 3152,
    "PENDING_LIFECYCLE_DECISION_SPREAD_REPAIRED_FROM_TICK_PARQUET": 7,
    "PENDING_LIFECYCLE_DECISION_SPREAD_UPGRADED_FROM_LEGACY_TO_TICK_PARQUET": 3,
    "PENDING_LIFECYCLE_NOFILL_FORWARD_SOURCE_PRESERVED": 28,
    "PENDING_LIFECYCLE_RECOMPUTE_APPLIED_NO_INTERNAL_LIFECYCLE": 235,
    "PENDING_LIFECYCLE_TICK_PARQUET_NOT_SOURCE_SAFE_DECISION_SPREAD_GAP_REMAINS": 1,
}
UNSAFE_CANDIDATE = "NAS100_2026-05-03T16:15:00+00:00"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_line_no"] = line_no
            rows.append(row)
    return rows


def pending_decision_spread_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        statuses = row.get("pending_lifecycle_source_capture_statuses")
        if not isinstance(statuses, dict):
            counts["NO_PENDING_LIFECYCLE_STATUS_MAP"] += 1
        else:
            counts[str(statuses.get("decision_spread_value_source_safe") or "")] += 1
    return dict(sorted(counts.items()))


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


def main() -> None:
    checks: list[dict[str, Any]] = []
    rows = read_jsonl(OUTPUT_LEDGER)
    summary = read_json(OUTPUT_SUMMARY)
    manifest = read_json(OUTPUT_MANIFEST)
    pending = [row for row in rows if row.get("strategy_id") == PENDING_LIMIT_STRATEGY_ID]
    kill_rows = [row for row in rows if row.get("action_class") == "KILL"]
    source_requirements = summary.get("remaining_pending_tick_source_requirements") or []

    append_check(checks, "row_count", len(rows) == 3426, len(rows))
    append_check(checks, "summary_row_count", summary.get("rows") == len(rows), summary.get("rows"))
    append_check(checks, "pending_count", len(pending) == 274, len(pending))
    append_check(checks, "action_counts", dict(Counter(str(row.get("action_class") or "") for row in rows)) == EXPECTED_ACTION_COUNTS)
    append_check(checks, "pending_branch_counts", dict(Counter(str(row.get("branch_decision") or "") for row in pending)) == EXPECTED_PENDING_BRANCH_COUNTS)
    append_check(checks, "pending_spread_counts", pending_decision_spread_counts(pending) == EXPECTED_PENDING_SPREAD_COUNTS)
    append_check(
        checks,
        "status_counts",
        dict(Counter(str(row.get("action_after_pending_tick_spread_repair_status") or "") for row in rows))
        == EXPECTED_STATUS_COUNTS,
    )
    append_check(checks, "numeric_proxy_rows", summary.get("after_numeric_proxy_rows") == 1475)
    append_check(checks, "proxy_sum", summary.get("after_proxy_r_sum") == 408.47201587)
    append_check(checks, "proxy_delta_zero", summary.get("proxy_r_sum_delta") == 0.0)
    append_check(checks, "exact_r_zero", summary.get("exact_r_rows") == 0)
    append_check(checks, "metadata_gaps_zero", summary.get("all_metadata_gaps_after") == 0)
    append_check(checks, "kill_count", len(kill_rows) == 1014, len(kill_rows))
    append_check(checks, "kill_audits_present", all(kill_audit_present(row) for row in kill_rows))
    append_check(checks, "kill_audit_summary_count", summary.get("kill_scope_audited_rows_after") == 1014)
    append_check(
        checks,
        "single_pending_source_requirement",
        len(source_requirements) == 1 and source_requirements[0].get("candidate_id") == UNSAFE_CANDIDATE,
        source_requirements,
    )
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
        "schema_version": "main_orch24_action_after_pending_tick_spread_repair_verifier_v1",
        "verified": verified,
        "decision": (
            "ACTION_AFTER_PENDING_TICK_SPREAD_REPAIR_VERIFIED"
            if verified
            else "ACTION_AFTER_PENDING_TICK_SPREAD_REPAIR_REJECTED"
        ),
        "checks": checks,
        "summary": {
            "rows": len(rows),
            "pending_rows": len(pending),
            "numeric_proxy_rows": summary.get("after_numeric_proxy_rows"),
            "proxy_r_sum": summary.get("after_proxy_r_sum"),
            "kill_rows_with_audit": sum(1 for row in kill_rows if kill_audit_present(row)),
            "remaining_pending_tick_source_requirements": len(source_requirements),
        },
    }
    write_json(VERIFY_RESULT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not verified:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
