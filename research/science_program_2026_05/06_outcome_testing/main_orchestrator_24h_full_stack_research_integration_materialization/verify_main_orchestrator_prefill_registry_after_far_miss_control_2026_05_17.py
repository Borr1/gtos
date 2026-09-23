"""Verify prefill registry metadata after far-miss control repair."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


ROOT = find_repo_root(Path(__file__).resolve())
DATE = "2026-05-17"
ROUTE_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization"
LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_REGISTRY_FAR_MISS_CONTROL_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_REGISTRY_FAR_MISS_CONTROL_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_REGISTRY_FAR_MISS_CONTROL_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_REGISTRY_FAR_MISS_CONTROL_VERIFY_RESULT_{DATE}.json"

EXPECTED_BRANCH = "PREFILL_FAR_MISS_RETEST_CONTROL_DEFAULT_OFF_WITH_CONCENTRATION_GUARD"
EXPECTED_IMPL = "KEEP_DEFAULT_OFF_PREFILL_FAR_MISS_RETEST_CONTROL_CANDIDATE_WITH_CONCENTRATION_GUARD"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def fail_if(condition: bool, failures: list[str], message: str) -> None:
    if condition:
        failures.append(message)


def main() -> None:
    failures: list[str] = []
    rows = read_jsonl(LEDGER)
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    row = rows[0] if rows else {}

    fail_if(len(rows) != 1, failures, "expected 1 registry metadata row")
    fail_if(row.get("branch_decision") != EXPECTED_BRANCH, failures, "unexpected branch decision")
    fail_if(row.get("implementation_candidate") != EXPECTED_IMPL, failures, "unexpected implementation candidate")
    fail_if(summary.get("metadata_rows_with_stale_tokens") != 0, failures, "stale token count must be 0")
    fail_if(row.get("metadata_rows_with_stale_tokens") != 0, failures, "ledger stale token count must be 0")
    fail_if(summary.get("redesign_rows_after") != 0, failures, "redesign rows after must be 0")
    fail_if(summary.get("action_class_delta_vs_previous") != {"IMPLEMENT_DEFAULT_OFF": 20, "REDESIGN": -20}, failures, "unexpected action-class delta")
    fail_if(summary.get("affected_candidate_rows") != 10, failures, "expected 10 affected candidates")
    fail_if(summary.get("affected_entry_offset_proxy_rows") != 10, failures, "expected 10 entry-offset proxy rows")
    fail_if(round(float(summary.get("affected_entry_offset_proxy_r_sum", 0.0)), 8) != 6.67275084, failures, "unexpected affected proxy-R sum")
    fail_if(summary.get("prefill_metadata_proxy_rows") != 0, failures, "prefill metadata must own 0 proxy rows")
    fail_if(summary.get("exact_r_rows") != 0, failures, "exact-R rows must remain 0")
    fail_if(summary.get("safe_flags", {}).get("live_effect") is not False, failures, "live_effect safe flag changed")
    fail_if(manifest.get("summary_counts", {}).get("metadata_rows_with_stale_tokens") != 0, failures, "manifest stale token count mismatch")

    result = {
        "ok": not failures,
        "failures": failures,
        "rows": len(rows),
        "metadata_rows_with_stale_tokens": summary.get("metadata_rows_with_stale_tokens"),
        "redesign_rows_after": summary.get("redesign_rows_after"),
        "action_class_delta_vs_previous": summary.get("action_class_delta_vs_previous"),
        "affected_candidate_rows": summary.get("affected_candidate_rows"),
        "affected_entry_offset_proxy_r_sum": summary.get("affected_entry_offset_proxy_r_sum"),
        "exact_r_rows": summary.get("exact_r_rows"),
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
