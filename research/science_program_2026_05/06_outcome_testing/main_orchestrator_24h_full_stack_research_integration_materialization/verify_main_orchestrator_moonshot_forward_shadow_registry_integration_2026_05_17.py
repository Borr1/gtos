"""Verify moonshot selected-action forward-shadow registry integration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
LEDGER = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_FORWARD_SHADOW_REGISTRY_INTEGRATION_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_FORWARD_SHADOW_REGISTRY_INTEGRATION_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_FORWARD_SHADOW_REGISTRY_INTEGRATION_OUTPUT_MANIFEST_{DATE}.json"
RESULT = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_FORWARD_SHADOW_REGISTRY_INTEGRATION_VERIFICATION_RESULT_{DATE}.json"

EXPECTED_STRATEGY_IDS = {
    "MOONSHOT_DEFAULT_OFF_SCORER_APPLICATION_CONTROL",
    "MOONSHOT_MARKET_GAP_CONTROL",
    "MOONSHOT_NOFILL_FAMILY_SPLIT",
    "MOONSHOT_NOFILL_FAR_MISS_RETEST_REDESIGN",
    "MOONSHOT_NOFILL_NEAR_MISS_MARKET_ENTRY",
    "MOONSHOT_NOFILL_NEAR_MISS_OFFSET_ENTRY",
    "MOONSHOT_SOURCE_GUARD_SCOPE_CONTROL",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def require(condition: bool, issues: list[str], message: str) -> None:
    if not condition:
        issues.append(message)


def verify() -> dict[str, Any]:
    issues: list[str] = []
    rows = read_jsonl(LEDGER)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)

    require(len(rows) == 1918, issues, f"expected 1918 projected rows, got {len(rows)}")
    require(summary.get("projected_rows") == 1918, issues, "summary projected row mismatch")
    require(summary.get("projected_candidate_count") == 274, issues, "candidate count mismatch")
    require(summary.get("moonshot_registry_strategy_count") == 7, issues, "strategy count mismatch")
    require(set(summary.get("moonshot_registry_strategy_ids") or []) == EXPECTED_STRATEGY_IDS, issues, "strategy ids mismatch")
    require(set(summary.get("strategy_counts") or {}) == EXPECTED_STRATEGY_IDS, issues, "strategy count keys mismatch")
    for strategy_id in EXPECTED_STRATEGY_IDS:
        require(summary.get("strategy_counts", {}).get(strategy_id) == 274, issues, f"{strategy_id} count mismatch")
    require(summary.get("strategy_status_counts") == {"WAITING_FOR_MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE": 1918}, issues, "strategy status mismatch")
    require(summary.get("score_status_counts") == {"WAITING_SOURCE": 1918}, issues, "score status mismatch")
    require(
        summary.get("moonshot_selected_action_source_capture_status_counts")
        == {"SOURCE_CAPTURE_ROW_NOT_FOUND": 1918},
        issues,
        "source capture row status mismatch",
    )
    require(summary.get("source_capture_ready_rows") == 0, issues, "source ready rows not zero")
    require(summary.get("source_capture_waiting_rows") == 1918, issues, "source waiting rows mismatch")
    require(summary.get("proxy_r_rows") == 0, issues, "proxy R rows opened")
    require(summary.get("exact_r_rows") == 0, issues, "exact R rows opened")
    require(summary.get("counted_proxy_r_rows") == 0, issues, "counted proxy R rows opened")
    require(summary.get("runtime_score_allowed_rows") == 0, issues, "runtime score rows opened")
    require(summary.get("candidate_use_allowed_now_rows") == 0, issues, "candidate use rows opened")
    require(summary.get("live_effect_true_rows") == 0, issues, "live effect rows opened")
    require(manifest.get("counts", {}).get("projected_rows") == 1918, issues, "manifest projected rows mismatch")
    require(manifest.get("counts", {}).get("projected_candidate_count") == 274, issues, "manifest candidate mismatch")
    require(manifest.get("counts", {}).get("source_capture_waiting_rows") == 1918, issues, "manifest waiting mismatch")
    require(manifest.get("counts", {}).get("proxy_r_rows") == 0, issues, "manifest proxy mismatch")

    for row in rows:
        row_id = f"{row.get('candidate_id')}::{row.get('strategy_id')}::{row.get('asof_latest_candle_utc')}"
        require(row.get("strategy_id") in EXPECTED_STRATEGY_IDS, issues, f"{row_id} unexpected strategy id")
        require(row.get("strategy_status") == "WAITING_FOR_MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE", issues, f"{row_id} status mismatch")
        require(row.get("score_status") == "WAITING_SOURCE", issues, f"{row_id} score mismatch")
        require(row.get("strategy_proxy_r") is None, issues, f"{row_id} proxy R opened")
        require(row.get("counted_proxy_r") is False, issues, f"{row_id} counted proxy")
        require(row.get("runtime_score_allowed") is False, issues, f"{row_id} runtime score allowed")
        require(row.get("candidate_use_allowed_now") is False, issues, f"{row_id} candidate use allowed")
        require(row.get("live_effect") is False, issues, f"{row_id} live effect true")
        require(row.get("source_capture_ready") is False, issues, f"{row_id} source ready unexpectedly")
        require(
            row.get("moonshot_selected_action_source_capture_status") == "SOURCE_CAPTURE_ROW_NOT_FOUND",
            issues,
            f"{row_id} source-capture status mismatch",
        )
        require(
            row.get("moonshot_selected_action_source_capture_created_at_utc") is None,
            issues,
            f"{row_id} unexpected source-capture timestamp",
        )
        require(bool(row.get("source_capture_required_fields")), issues, f"{row_id} missing required fields")
        require(bool(row.get("source_capture_missing_fields")), issues, f"{row_id} missing missing-fields proof")
        require(row.get("underlying_intelligence_preserved") is True, issues, f"{row_id} intelligence not preserved")
        audit = row.get("missed_opportunity_audit") or {}
        require(bool(audit.get("what_was_tried")), issues, f"{row_id} audit missing what_was_tried")
        require(bool(audit.get("what_could_make_it_work")), issues, f"{row_id} audit missing repair path")

    result = {
        "verified": not issues,
        "issues": issues,
        "projected_rows": len(rows),
        "projected_candidate_count": summary.get("projected_candidate_count"),
        "moonshot_registry_strategy_count": summary.get("moonshot_registry_strategy_count"),
        "source_capture_waiting_rows": summary.get("source_capture_waiting_rows"),
        "proxy_r_rows": summary.get("proxy_r_rows"),
        "exact_r_rows": summary.get("exact_r_rows"),
        "safe_flags": summary.get("safe_flags"),
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
