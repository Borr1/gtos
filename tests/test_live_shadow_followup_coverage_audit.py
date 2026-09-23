from __future__ import annotations

import json

from scripts.audit_live_shadow_followup_coverage import build_report


def test_followup_coverage_audit_includes_deep_dive_source_lanes(tmp_path):
    payload = build_report(tmp_path)
    rows = {row["id"]: row for row in payload["rows"]}

    assert payload["schema_version"] == "live_shadow_followup_coverage_audit_v1"
    assert rows["LIVE-FOLLOW-023"]["coverage_status"] == "VERIFIER_REQUIRED_WITH_LOCAL_ROWS"
    assert "shadow_logs/xauusd_same_market_extension_status.jsonl" in rows["LIVE-FOLLOW-026"]["row_paths"]
    assert "shadow_logs/es_mes_preregistration_status.jsonl" in rows["LIVE-FOLLOW-027"]["row_paths"]
    assert "shadow_logs/shadow_observer_hardening_status.jsonl" in rows["LIVE-FOLLOW-033"]["row_paths"]
    assert "shadow_logs/shadow_observer_hardening_status.jsonl" in rows["LIVE-FOLLOW-008"]["row_paths"]
    assert "shadow_logs/cross_instrument_correlation_decisions.jsonl" in rows["LIVE-FOLLOW-016"]["row_paths"]
    assert rows["LIVE-FOLLOW-027"]["coverage_status"] == "PRE_REGISTRATION_REQUIRED"
    assert rows["LIVE-FOLLOW-030"]["coverage_status"] == "PARTIAL_FORWARD_CONTEXT_PLUS_SOURCE_BLOCKERS"


def test_followup_coverage_audit_detects_strategy_follow_rows(tmp_path):
    shadow_dir = tmp_path / "shadow_logs"
    shadow_dir.mkdir()
    (shadow_dir / "strategy_follow_evaluations.jsonl").write_text(
        json.dumps(
            {
                "schema_version": "strategy_follow_evaluation_v1",
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    payload = build_report(tmp_path)
    rows = {row["id"]: row for row in payload["rows"]}

    assert rows["LIVE-FOLLOW-001"]["coverage_status"] == "ROWS_PRESENT"
    assert rows["LIVE-FOLLOW-001"]["files"][0]["latest_schema"] == "strategy_follow_evaluation_v1"
