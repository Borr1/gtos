"""Verify pending lifecycle tick-spread reconstruction materialization."""

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
    sha256_file,
    write_json,
)


SOURCE_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_TICK_SPREAD_RECONSTRUCTION_SOURCE_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_TICK_SPREAD_RECONSTRUCTION_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_TICK_SPREAD_RECONSTRUCTION_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / (
    f"MAIN_ORCH24_PENDING_LIFECYCLE_TICK_SPREAD_RECONSTRUCTION_OUTPUT_MANIFEST_{DATE}.json"
)
VERIFY_RESULT = ROUTE_DIR / (
    f"MAIN_ORCH24_PENDING_LIFECYCLE_TICK_SPREAD_RECONSTRUCTION_VERIFICATION_RESULT_{DATE}.json"
)

SUCCESS_STATUS = "TICK_PARQUET_AT_OR_BEFORE_DECISION_WITHIN_2S_SOURCE_SAFE"
UNSAFE_STATUS = "TICK_PARQUET_NO_PRIOR_TICK_WITHIN_2S_SOURCE_UNSAFE"
TICK_DERIVATION = "DERIVED_FROM_TICK_PARQUET_AT_OR_BEFORE_DECISION_SPREAD"
NOFILL_DERIVATION = "DERIVED_FROM_NOFILL_FORWARD_SOURCE_CAPTURE_DECISION_SPREAD"
MISSING_STATUS = "SOURCE_NOT_CAPTURED_IN_CURRENT_ROW"
UNSAFE_CANDIDATE = "NAS100_2026-05-03T16:15:00+00:00"

EXPECTED_ACTION_COUNTS = {
    "IMPLEMENT_DEFAULT_OFF": 518,
    "KEEP": 942,
    "KILL": 1098,
    "PRESERVE_REQUIREMENT": 22,
    "REDESIGN": 846,
}
EXPECTED_BRANCH_COUNTS = {
    "KEEP_PENDING_LIFECYCLE_HYPOTHETICAL_PATH_SCORER": 235,
    "KEEP_PENDING_LIFECYCLE_SCORER_WITH_DERIVED_SOURCE_FIELDS_CURRENT_ROWS_PARTIAL": 1,
    "KEEP_PENDING_LIFECYCLE_SCORER_WITH_RECONSTRUCTED_SOURCE_FIELDS_COMPLETE": 38,
}
EXPECTED_DECISION_SPREAD_COUNTS = {
    NOFILL_DERIVATION: 28,
    TICK_DERIVATION: 10,
    "NO_PENDING_LIFECYCLE_STATUS_MAP": 235,
    MISSING_STATUS: 1,
}
EXPECTED_REPAIR_STATUS_COUNTS = {
    "NOT_PENDING_LIFECYCLE_ROW": 3152,
    "PENDING_LIFECYCLE_DECISION_SPREAD_REPAIRED_FROM_TICK_PARQUET": 7,
    "PENDING_LIFECYCLE_DECISION_SPREAD_UPGRADED_FROM_LEGACY_TO_TICK_PARQUET": 3,
    "PENDING_LIFECYCLE_NOFILL_FORWARD_SOURCE_PRESERVED": 28,
    "PENDING_LIFECYCLE_RECOMPUTE_APPLIED_NO_INTERNAL_LIFECYCLE": 235,
    "PENDING_LIFECYCLE_TICK_PARQUET_NOT_SOURCE_SAFE_DECISION_SPREAD_GAP_REMAINS": 1,
}
EXPECTED_ATTEMPT_COUNTS = {
    SUCCESS_STATUS: 10,
    UNSAFE_STATUS: 1,
}


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


def nested_decision_spread_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        statuses = row.get("pending_lifecycle_source_capture_statuses")
        if not isinstance(statuses, dict):
            counts["NO_PENDING_LIFECYCLE_STATUS_MAP"] += 1
            continue
        counts[str(statuses.get("decision_spread_value_source_safe") or "")] += 1
    return dict(sorted(counts.items()))


def append_check(checks: list[dict[str, Any]], name: str, ok: bool, detail: Any = None) -> None:
    checks.append({"name": name, "ok": bool(ok), "detail": detail})


def verify_manifest(manifest: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    for section in ("input_artifacts", "output_artifacts"):
        for raw_path, expected in manifest.get(section, {}).items():
            path = REPO_ROOT / raw_path if section == "input_artifacts" else ROUTE_DIR / raw_path
            exists = path.exists()
            append_check(checks, f"{section}:{raw_path}:exists", exists)
            if not exists:
                continue
            append_check(
                checks,
                f"{section}:{raw_path}:sha256",
                sha256_file(path) == expected.get("sha256"),
            )
            append_check(
                checks,
                f"{section}:{raw_path}:size",
                path.stat().st_size == expected.get("size_bytes"),
            )


def main() -> None:
    checks: list[dict[str, Any]] = []
    rows = read_jsonl(OUTPUT_LEDGER)
    attempts = read_jsonl(SOURCE_LEDGER)
    summary = read_json(OUTPUT_SUMMARY)
    manifest = read_json(OUTPUT_MANIFEST)

    pending = [row for row in rows if row.get("strategy_id") == PENDING_LIMIT_STRATEGY_ID]
    tick_rows = [
        row
        for row in pending
        if (row.get("pending_lifecycle_source_capture_statuses") or {}).get(
            "decision_spread_value_source_safe"
        )
        == TICK_DERIVATION
    ]
    unsafe_attempts = [row for row in attempts if row.get("decision_spread_status") == UNSAFE_STATUS]
    gap_rows = [
        row
        for row in pending
        if (row.get("pending_lifecycle_source_capture_statuses") or {}).get(
            "decision_spread_value_source_safe"
        )
        == MISSING_STATUS
    ]

    append_check(checks, "row_count", len(rows) == 3426, len(rows))
    append_check(checks, "summary_row_count", summary.get("rows") == len(rows), summary.get("rows"))
    append_check(checks, "pending_row_count", len(pending) == 274, len(pending))
    append_check(checks, "source_attempt_count", len(attempts) == 11, len(attempts))
    append_check(
        checks,
        "action_counts_preserved",
        dict(Counter(str(row.get("action_class") or "") for row in rows)) == EXPECTED_ACTION_COUNTS,
    )
    append_check(
        checks,
        "pending_branch_counts",
        dict(Counter(str(row.get("branch_decision") or "") for row in pending)) == EXPECTED_BRANCH_COUNTS,
    )
    append_check(
        checks,
        "pending_decision_spread_counts",
        nested_decision_spread_counts(pending) == EXPECTED_DECISION_SPREAD_COUNTS,
    )
    append_check(
        checks,
        "repair_status_counts",
        dict(Counter(str(row.get("pending_lifecycle_tick_spread_reconstruction_status") or "") for row in rows))
        == EXPECTED_REPAIR_STATUS_COUNTS,
    )
    append_check(
        checks,
        "attempt_status_counts",
        dict(Counter(str(row.get("decision_spread_status") or "") for row in attempts))
        == EXPECTED_ATTEMPT_COUNTS,
    )
    append_check(checks, "tick_rows_after", len(tick_rows) == 10, len(tick_rows))
    append_check(checks, "unsafe_attempt_singleton", [row.get("candidate_id") for row in unsafe_attempts] == [UNSAFE_CANDIDATE])
    append_check(checks, "gap_singleton", [row.get("candidate_id") for row in gap_rows] == [UNSAFE_CANDIDATE])
    append_check(checks, "legacy_rows_after_zero", summary.get("legacy_decision_spread_rows_after") == 0)
    append_check(checks, "remaining_gaps_one", summary.get("remaining_pending_decision_spread_gaps") == 1)
    append_check(checks, "numeric_proxy_rows_preserved", summary.get("numeric_proxy_rows_after") == 1416)
    append_check(checks, "proxy_sum_preserved", summary.get("proxy_r_sum_after") == 396.47201587)
    append_check(checks, "pending_proxy_sum_preserved", summary.get("after_pending_proxy_summary", {}).get("pending_proxy_r_sum") == 50.0)
    append_check(checks, "exact_r_rows_zero", summary.get("exact_r_rows") == 0)
    append_check(checks, "metadata_gaps_zero", summary.get("all_metadata_gaps_after") == 0)
    append_check(checks, "kill_audit_preserved", summary.get("kill_scope_audited_rows_after") == 1098)
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

    tick_source_ok = True
    for row in tick_rows:
        tick_source_ok = tick_source_ok and row.get(
            "pending_lifecycle_decision_spread_reconstruction_source"
        ) == "tick_parquet_decision_time"
        tick_source_ok = tick_source_ok and row.get(
            "pending_lifecycle_decision_spread_reconstruction_source_status"
        ) == SUCCESS_STATUS
        offset = row.get("pending_lifecycle_decision_spread_reconstruction_tick_offset_seconds")
        tick_source_ok = tick_source_ok and isinstance(offset, (int, float)) and -2.0 <= offset <= 0
        tick_source_ok = tick_source_ok and bool(
            row.get("pending_lifecycle_decision_spread_reconstruction_tick_source_sha256")
        )
    append_check(checks, "tick_row_source_fields_complete", tick_source_ok)

    unsafe_ok = len(unsafe_attempts) == 1
    if unsafe_attempts:
        unsafe = unsafe_attempts[0]
        unsafe_ok = (
            unsafe_ok
            and unsafe.get("decision_spread_value_source_safe") is None
            and unsafe.get("next_tick_offset_seconds", 0) > 2
            and bool(unsafe.get("source_requirement"))
        )
    append_check(checks, "unsafe_attempt_preserves_source_requirement", unsafe_ok)

    verify_manifest(manifest, checks)

    verified = all(check["ok"] for check in checks)
    result = {
        "schema_version": "main_orch24_pending_lifecycle_tick_spread_reconstruction_verifier_v1",
        "verified": verified,
        "decision": (
            "PENDING_LIFECYCLE_TICK_SPREAD_RECONSTRUCTION_VERIFIED"
            if verified
            else "PENDING_LIFECYCLE_TICK_SPREAD_RECONSTRUCTION_REJECTED"
        ),
        "checks": checks,
        "summary": {
            "rows": len(rows),
            "pending_rows": len(pending),
            "tick_reconstruction_success_rows": len(tick_rows),
            "remaining_pending_decision_spread_gaps": len(gap_rows),
            "proxy_r_sum_after": summary.get("proxy_r_sum_after"),
            "pending_proxy_r_sum_after": summary.get("after_pending_proxy_summary", {}).get(
                "pending_proxy_r_sum"
            ),
        },
    }
    write_json(VERIFY_RESULT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not verified:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
