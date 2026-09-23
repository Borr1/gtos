"""Verify the moonshot selected-action source-capture contract materialization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_SOURCE_CAPTURE_CONTRACT_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_SOURCE_CAPTURE_CONTRACT_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_SOURCE_CAPTURE_CONTRACT_OUTPUT_MANIFEST_{DATE}.json"
RESULT = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_SOURCE_CAPTURE_CONTRACT_VERIFICATION_RESULT_{DATE}.json"

EXPECTED_STRATEGY_IDS = {
    "MOONSHOT_DEFAULT_OFF_SCORER_APPLICATION_CONTROL",
    "MOONSHOT_MARKET_GAP_CONTROL",
    "MOONSHOT_NOFILL_FAMILY_SPLIT",
    "MOONSHOT_NOFILL_FAR_MISS_RETEST_REDESIGN",
    "MOONSHOT_NOFILL_NEAR_MISS_MARKET_ENTRY",
    "MOONSHOT_NOFILL_NEAR_MISS_OFFSET_ENTRY",
    "MOONSHOT_SOURCE_GUARD_SCOPE_CONTROL",
}
EXPECTED_SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def require(condition: bool, issues: list[str], message: str) -> None:
    if not condition:
        issues.append(message)


def complete_preservation(row: dict[str, Any]) -> bool:
    required = (
        "opportunity_preservation_status",
        "opportunity_owner_row_id",
        "opportunity_owner_source_artifact",
        "opportunity_proxy_reference_status",
        "opportunity_not_independently_countable_reason",
        "opportunity_useful_mechanism",
        "opportunity_downstream_paths",
    )
    return (
        all(row.get(field) not in (None, "", []) for field in required)
        and isinstance(row.get("missed_opportunity_audit"), dict)
        and row.get("underlying_intelligence_preserved") is True
    )


def verify() -> dict[str, Any]:
    issues: list[str] = []
    rows = read_jsonl(LEDGER)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)

    require(len(rows) == 7, issues, f"expected 7 contract rows, got {len(rows)}")
    require(set(row.get("strategy_id") for row in rows) == EXPECTED_STRATEGY_IDS, issues, "strategy ids mismatch")
    require(summary.get("strategy_rows") == 7, issues, "summary strategy row mismatch")
    require(summary.get("total_required_fields") == 24, issues, "required field count mismatch")
    require(summary.get("projection_ledger_rows") == 1918, issues, "projection row count mismatch")
    require(summary.get("projection_waiting_rows") == 1918, issues, "projection waiting count mismatch")
    require(summary.get("projection_source_ready_rows") == 0, issues, "source-ready projection rows opened")
    require(summary.get("source_capture_log_rows_seen") == 0, issues, "unexpected current source-capture log rows")
    require(summary.get("source_capture_latest_keys_seen") == 0, issues, "unexpected source-capture keys")
    require(summary.get("safe_flags") == EXPECTED_SAFE_FLAGS, issues, "safe flags mismatch")
    require(summary.get("proxy_r_rows_opened") == 0, issues, "proxy R opened")
    require(summary.get("exact_r_rows_opened") == 0, issues, "exact R opened")
    require(summary.get("counted_proxy_r_rows") == 0, issues, "counted proxy R opened")
    require(summary.get("runtime_score_allowed_rows") == 0, issues, "runtime scoring opened")
    require(summary.get("candidate_use_allowed_now_rows") == 0, issues, "candidate use opened")
    require(summary.get("live_effect_true_rows") == 0, issues, "live effect opened")
    require(summary.get("rows_with_missed_opportunity_audit") == 7, issues, "missing audits")
    require(summary.get("rows_with_underlying_intelligence_preserved") == 7, issues, "intelligence not preserved")
    require(manifest.get("counts", {}).get("strategy_rows") == 7, issues, "manifest strategy rows mismatch")
    require(manifest.get("counts", {}).get("total_required_fields") == 24, issues, "manifest field count mismatch")
    require(manifest.get("counts", {}).get("projection_waiting_rows") == 1918, issues, "manifest waiting mismatch")

    for row in rows:
        row_id = str(row.get("strategy_id") or "")
        require(row.get("schema_version") == "moonshot_selected_action_source_capture_contract_v1", issues, f"{row_id} schema mismatch")
        require(row.get("safe_flags") == EXPECTED_SAFE_FLAGS, issues, f"{row_id} safe flags mismatch")
        require(row.get("source_capture_schema_version") == "moonshot_selected_action_source_capture_v1", issues, f"{row_id} source schema mismatch")
        require(row.get("source_capture_required_field_count") == len(row.get("source_capture_required_fields") or []), issues, f"{row_id} required field count mismatch")
        require(row.get("source_capture_required_field_count", 0) > 0, issues, f"{row_id} missing required fields")
        require(row.get("source_capture_log_rows_seen") == 0, issues, f"{row_id} source rows unexpectedly present")
        require(row.get("current_projection_rows_for_strategy") == 274, issues, f"{row_id} projection rows mismatch")
        require(row.get("current_projection_waiting_rows_for_strategy") == 274, issues, f"{row_id} waiting rows mismatch")
        require(row.get("current_projection_source_ready_rows_for_strategy") == 0, issues, f"{row_id} source-ready rows mismatch")
        require(row.get("counted_exact_r") is False, issues, f"{row_id} counted exact R")
        require(row.get("counted_proxy_r") is False, issues, f"{row_id} counted proxy R")
        require(row.get("runtime_score_allowed") is False, issues, f"{row_id} runtime score allowed")
        require(row.get("candidate_use_allowed_now") is False, issues, f"{row_id} candidate use allowed")
        require(row.get("live_effect") is False, issues, f"{row_id} live effect true")
        require(complete_preservation(row), issues, f"{row_id} opportunity preservation incomplete")
        require("source requirement" in row.get("opportunity_downstream_paths", []), issues, f"{row_id} source requirement path missing")
        audit = row.get("missed_opportunity_audit") or {}
        require(audit.get("kill_scope") == "NOT_KILLED_SOURCE_CAPTURE_CONTRACT", issues, f"{row_id} audit scope mismatch")
        require(bool(audit.get("what_could_make_it_work")), issues, f"{row_id} missing repair path")

    result = {
        "verified": not issues,
        "issues": issues,
        "strategy_rows": len(rows),
        "total_required_fields": summary.get("total_required_fields"),
        "projection_ledger_rows": summary.get("projection_ledger_rows"),
        "projection_waiting_rows": summary.get("projection_waiting_rows"),
        "source_capture_log_rows_seen": summary.get("source_capture_log_rows_seen"),
        "proxy_r_rows_opened": summary.get("proxy_r_rows_opened"),
        "exact_r_rows_opened": summary.get("exact_r_rows_opened"),
        "safe_flags": summary.get("safe_flags"),
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
