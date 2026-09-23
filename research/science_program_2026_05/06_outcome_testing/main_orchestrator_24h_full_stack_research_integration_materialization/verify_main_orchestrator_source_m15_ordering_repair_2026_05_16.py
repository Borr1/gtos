"""Verify SOURCE M15-ordering repair materialization."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_M15_ORDERING_REPAIR_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_M15_ORDERING_REPAIR_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_M15_ORDERING_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
RESULT = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_M15_ORDERING_REPAIR_VERIFICATION_RESULT_{DATE}.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def close_enough(a: float | None, b: float, tol: float = 1e-9) -> bool:
    return a is not None and abs(a - b) <= tol


def main() -> None:
    issues: list[str] = []
    if not LEDGER.exists():
        issues.append(f"missing ledger: {LEDGER}")
    if not SUMMARY.exists():
        issues.append(f"missing summary: {SUMMARY}")
    if not MANIFEST.exists():
        issues.append(f"missing manifest: {MANIFEST}")
    if issues:
        payload = {"ok": False, "issues": issues}
        RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(payload))
        raise SystemExit(1)

    rows = read_jsonl(LEDGER)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)
    affected = [row for row in rows if row.get("m15_ordering_repair_status") == "REPAIRED_WITH_BOUNDED_ORDERING_PROXY"]
    checks = {
        "row_count_138": len(rows) == 138,
        "affected_count_30": len(affected) == 30,
        "summary_rows": summary.get("rows") == 138,
        "summary_affected": summary.get("m15_ordering_repaired_rows") == 30,
        "remaining_blockers_zero": summary.get("m15_ordering_remaining_blocker_rows") == 0,
        "after_proxy_rows_30": summary.get("after_row_level_ordering_proxy_rows") == 30,
        "exact_r_zero": summary.get("exact_r_rows") == 0,
        "exact_chronology_zero": summary.get("exact_chronology_true_rows") == 0,
        "midpoint_sum": close_enough(float(summary.get("ordering_proxy_midpoint_sum")), 3.302239),
        "lower_sum": close_enough(float(summary.get("ordering_proxy_lower_sum")), 1.278912),
        "upper_sum": close_enough(float(summary.get("ordering_proxy_upper_sum")), 5.32557),
        "manifest_hash_ledger": manifest["outputs"][LEDGER.name]["sha256"] == sha256_file(LEDGER),
        "manifest_hash_summary": manifest["outputs"][SUMMARY.name]["sha256"] == sha256_file(SUMMARY),
        "safe_flags_closed": all(
            row.get("safe_flags") == {
                "NO_PROMOTION_VERDICT": True,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            }
            for row in rows
        ),
    }
    expected_after = {
        "KEEP_SOURCE_ACCEPTED_AFTER_M15_ORDERING_POSITIVE_PROXY": 20,
        "KILL_SOURCE_REPAIR_UPGRADED_CHALLENGER_AFTER_ORDERING_NEGATIVE_PROXY": 3,
        "PRESERVE_SOURCE_REPAIR_UPGRADED_INTERVAL_BOUND_NO_CHALLENGER": 4,
        "KEEP_SOURCE_REPAIR_WITH_M15_ORDERING_INTERVAL_BOUND": 3,
    }
    checks["after_decision_counts"] = Counter(row.get("after_branch_decision") for row in affected) == expected_after
    checks["all_affected_have_proxy_midpoint"] = all(row.get("ordering_proxy_midpoint_r") is not None for row in affected)
    checks["no_exact_chronology_claims"] = not any(row.get("exact_chronology_claim") for row in affected)
    for name, passed in checks.items():
        if not passed:
            issues.append(f"check failed: {name}")

    payload = {
        "ok": not issues,
        "issues": issues,
        "checks": checks,
        "row_count": len(rows),
        "affected_rows": len(affected),
        "after_branch_decision_counts": dict(Counter(row.get("after_branch_decision") for row in affected)),
        "ordering_evidence_source_counts": dict(Counter(row.get("ordering_evidence_source") for row in affected)),
    }
    RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
