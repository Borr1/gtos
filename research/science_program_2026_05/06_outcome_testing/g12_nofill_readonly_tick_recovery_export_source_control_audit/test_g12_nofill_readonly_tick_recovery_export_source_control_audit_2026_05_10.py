"""Focused tests for the G12 NOFILL read-only tick recovery audit artifacts."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
BUILDER_PATH = ROUTE_DIR / "build_g12_nofill_readonly_tick_recovery_export_source_control_audit_2026_05_10.py"
spec = importlib.util.spec_from_file_location("g12_readonly_tick_audit_builder", BUILDER_PATH)
builder = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(builder)


def load(name: str) -> dict:
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def test_recomputed_counts_match_prompt_contract():
    machine = load(f"{builder.PREFIX}_MACHINE_LEDGER_{builder.DATE}.json")
    counts = machine["count_reconciliation"]["counts"]
    assert counts["upstream_tick_export_rows"] == 31
    assert counts["g12_grouped_request_rows"] == 22
    assert counts["target_recovered_grouped_rows"] == 20
    assert counts["owner_action_remaining_requests"] == 2
    assert counts["target_recovered_candidate_rows"] == 28
    assert counts["target_remaining_candidate_rows"] == 3
    assert counts["target_contamination_embargo_excluded_rows"] == 12
    assert machine["count_reconciliation"]["all_count_checks_pass"] is True


def test_target_json_artifacts_parse_and_safe_flags_remain_false():
    machine = load(f"{builder.PREFIX}_MACHINE_LEDGER_{builder.DATE}.json")
    parse = machine["target_json_parse"]
    assert parse["target_json_artifact_count"] >= 16
    assert parse["target_json_parse_failures"] == []
    assert parse["target_json_all_parse_and_safe"] is True


def test_recovered_sources_are_rehashed_and_cover_candidate_windows():
    audit = load(f"{builder.PREFIX}_SOURCE_HASH_WINDOW_COVERAGE_AUDIT_{builder.DATE}.json")
    assert audit["recovered_source_file_count"] == 20
    assert audit["rehashed_local_source_file_count"] == 20
    assert audit["hash_mismatch_count"] == 0
    assert audit["window_or_schema_failure_count"] == 0
    assert audit["all_recovered_sources_pass"] is True
    assert all(row["actual_in_requested_window_row_count"] > 0 for row in audit["rows"])
    assert all(row["candidate_window_checks"] for row in audit["rows"])


def test_remaining_xauusd_requests_are_exact_and_zero_tick_bugs_are_ruled_out():
    remaining = load(f"{builder.PREFIX}_REMAINING_REQUEST_EXHAUSTION_AUDIT_{builder.DATE}.json")
    assert remaining["exact_remaining_requests"] == ["XAUUSD|2026-04-15", "XAUUSD|2026-04-16"]
    assert remaining["remaining_candidate_row_count"] == 3
    assert remaining["recovery_ladder_exhaustion_pass"] is True
    assert remaining["target_filename_search"]["all_targeted_raw_searches_clear"] is True
    for row in remaining["zero_tick_rows"]:
        assert row["wrong_symbol_ruled_out"] is True
        assert row["wrong_utc_day_ruled_out"] is True
        assert row["terminal_disconnected_ruled_out"] is True
        assert row["unavailable_symbol_ruled_out"] is True
        assert row["extraction_error_ruled_out"] is True
        assert row["source_state_boundary_preserved"] is True
    scid = remaining["sierra_same_market_scid_audit"]
    assert scid["scid_window_rows_present"] is True
    assert scid["market_session_closure_explanation_ruled_out"] is True
    assert scid["admitted_as_recovered_tick_source"] is False


def test_no_raw_market_data_is_tracked_or_staged_and_next_route_is_active():
    noleak = load(f"{builder.PREFIX}_NOLEAK_STAGING_AUDIT_{builder.DATE}.json")
    assert noleak["audit_status"] == "PASS"
    assert noleak["raw_tick_or_csv_files_tracked"] == []
    assert noleak["raw_tick_or_csv_files_staged"] == []
    assert noleak["raw_tick_or_csv_files_visible_untracked"] == []
    assert noleak["forbidden_live_surface_paths"] == []
    next_route = load(f"{builder.PREFIX}_NEXT_ROUTE_RECOMMENDATION_{builder.DATE}.json")
    assert next_route["non_passive_next_route"] is True
    assert "XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE" == next_route[
        "recommended_route_id"
    ]
    assert next_route["one_line_starter"].startswith("/goal ")
    assert "NO_PROMOTION_VERDICT" in next_route["full_prompt"]


def test_completion_audit_accepts_with_required_safe_flags():
    completion = load(f"{builder.PREFIX}_COMPLETION_AUDIT_{builder.DATE}.json")
    assert completion["can_mark_goal_complete"] is True
    assert completion["missing_incomplete_or_weak_requirements"] == []
    assert completion["terminal_decision"] == builder.TERMINAL_DECISION
    assert completion["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert completion["validation_safe"] is False
    assert completion["outcome_review_opened"] is False
    assert completion["live_effect"] is False
