from __future__ import annotations

from src.research_infra.candidate_registry_audit import (
    ACTION_REQUIRED,
    COMPLETE,
    COMPLETE_WITH_LIMITATIONS,
    build_candidate_registry_audit_row,
)


def _candidate(**overrides):
    row = {
        "schema_version": "strategy_follow_candidate_v1",
        "created_at_utc": "2026-05-04T07:15:15+00:00",
        "symbol": "NAS100",
        "broker_symbol": "NDX100",
        "candidate_id": "NAS100_2026-05-04T07:15:00+00:00",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "source_file": "live_orchestrator_candidate_path",
        "source_hash": "abc123",
        "side": "LONG",
        "framework": "ob_retest",
        "analysis_decision": "CANDIDATE",
        "final_outcome_at_log": "REJECTED_L2",
        "trade_parameters": {
            "direction": "LONG",
            "entry_price": 100.0,
            "stop_loss": 95.0,
            "take_profit_1": 107.5,
        },
        "external_confluence": {
            "sierra": {
                "status": "LOCAL_DEPTH_FILE_PRESENT_FEATURE_EXTRACTION_DEFERRED",
                "source_status": "LOCAL_SIERRA_DEPTH_CAPTURED",
                "parity_status": "DATABENTO_MBP10_PARITY_EXACT_ON_REGISTERED_NQ_PILOT",
                "interpretation_status": "USABLE_AS_REGISTERED_NQ_DEPTH_CONTEXT",
                "paid_fetch_attempted": False,
            },
            "databento": {
                "status": "NOT_FETCHED_OR_NO_CACHE_FOR_LIVE_CANDIDATE",
                "paid_fetch_attempted": False,
                "paid_data_calls": 0,
                "trigger_policy": {"trigger_status": "TRIGGER_ELIGIBLE_BUT_DISABLED_BY_ENV"},
            },
        },
        "structural_selector_metadata": {
            "capture_status": "DECISION_TIME_AVAILABLE_FIELDS_PRESERVED",
            "h1_setup_present": True,
            "m15_confirmation_present": True,
            "frameworks_evaluated_present": True,
            "mso_summary_present": True,
            "standalone_fvg_geometry_present": False,
            "structural_lock_event_present": False,
            "reentry_state_present": False,
            "cost_aware_min_r_present": False,
        },
        "strategy_snapshots": [{"strategy_id": "V2_STRUCT_OB_BOUNDARY"}],
        "verification": {"passed": False, "blocked_by": "m15_choch_exists"},
        "no_leak_status": "NO_POST_OUTCOME_FIELDS_IN_DECISION_CONTEXT",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def test_complete_candidate_registry_row_is_complete():
    row = build_candidate_registry_audit_row(
        1,
        _candidate(),
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert row["schema_version"] == "candidate_registry_audit_v1"
    assert row["registry_audit_status"] == COMPLETE
    assert row["trade_geometry_status"] == "TRADE_GEOMETRY_VALID"
    assert row["action_required_codes"] == []
    assert row["no_ai_calls"] is True


def test_source_blocked_candidate_is_explicitly_documented():
    candidate = _candidate(
        symbol="GBPJPY",
        broker_symbol="GBPJPY",
        source_hash=None,
        external_confluence={
            "sierra": {
                "status": "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
                "source_status": "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
                "parity_status": "SOURCE_BLOCKED",
                "interpretation_status": "BLOCKED_NO_PROXY",
                "paid_fetch_attempted": False,
            },
            "databento": {
                "status": "NOT_FETCHED_OR_NO_CACHE_FOR_LIVE_CANDIDATE",
                "paid_fetch_attempted": False,
                "paid_data_calls": 0,
                "trigger_policy": {"trigger_status": "SOURCE_BLOCKED"},
            },
        },
    )

    row = build_candidate_registry_audit_row(
        1,
        candidate,
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert row["registry_audit_status"] == COMPLETE_WITH_LIMITATIONS
    assert row["source_hash_status"] == "SOURCE_HASH_NULL_SOURCE_FILE_CAPTURED"
    assert "SOURCE_HASH_NULL_SOURCE_FILE_CAPTURED" in row["documented_limitation_codes"]
    assert row["action_required_codes"] == []


def test_absent_confluence_is_action_required():
    row = build_candidate_registry_audit_row(
        1,
        _candidate(external_confluence={}),
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert row["registry_audit_status"] == ACTION_REQUIRED
    assert "MISSING_REQUIRED_FIELD:external_confluence" in row["action_required_codes"]
    assert "MISSING_SIERRA_CONFLUENCE_OBJECT" in row["action_required_codes"]
    assert "MISSING_DATABENTO_CONFLUENCE_OBJECT" in row["action_required_codes"]


def test_early_candidate_structural_source_gap_is_documented():
    candidate = _candidate(source_hash=None)
    for field in ("structural_selector_metadata", "h1_setup", "m15_confirmation", "frameworks_evaluated"):
        candidate.pop(field, None)

    row = build_candidate_registry_audit_row(
        1,
        candidate,
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert row["registry_audit_status"] == COMPLETE_WITH_LIMITATIONS
    assert row["structural_metadata_status"]["status"] == "STRUCTURAL_METADATA_SOURCE_NOT_CAPTURED"
    assert "STRUCTURAL_SELECTOR_METADATA_SOURCE_NOT_CAPTURED_EARLY_CANDIDATE_ROW" in row["documented_limitation_codes"]
