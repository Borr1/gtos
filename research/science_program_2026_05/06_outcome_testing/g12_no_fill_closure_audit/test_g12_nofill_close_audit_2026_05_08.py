"""Focused tests for G12 NOFILL close audit artifacts."""

from __future__ import annotations

import json
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent


def load_json(name: str):
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def test_decision_accepts_input_only_source_closure_with_corrected_blocker():
    decision = load_json("G12_NOFILL_CLOSE_DECISION_LEDGER_2026-05-08.json")
    assert decision["terminal_verdict"] == "ACCEPT_AS_INPUT_ONLY_SOURCE_CLOSURE_EVIDENCE"
    assert decision["upstream_packet_reported_counts"] == {
        "packet_rows": 298,
        "source_blocked_exact": 1,
        "source_closed": 297,
    }
    assert decision["g12_audited_counts_after_local_source_search"] == {
        "packet_rows": 298,
        "source_blocked_exact": 0,
        "source_closed": 298,
    }


def test_universe_and_exclusions_are_exact():
    audit = load_json("G12_NOFILL_CLOSE_UNIVERSE_AND_EXCLUSION_AUDIT_2026-05-08.json")
    assert audit["packet_rows"] == 298
    assert audit["nofill_input_packet_rows"] == 298
    assert audit["closure_matches_accepted_nofill_universe"] is True
    assert audit["six_t3_rows_excluded"]["status"] == "PASS"
    assert audit["six_t3_rows_excluded"]["t3_row_count"] == 6
    assert audit["six_t3_rows_excluded"]["overlap_with_closure_packet"] == []
    assert audit["blocked_94_cnr061_excluded"]["blocked_rows"] == 94
    assert audit["blocked_94_cnr061_excluded"]["status"] == "PASS"


def test_row_0127_source_blocker_is_locally_resolved_without_scoring():
    closure = load_json("G12_NOFILL_CLOSE_SOURCE_CLOSURE_AUDIT_2026-05-08.json")
    row = closure["row_0127_resolution"]
    assert row["packet_row_id"] == "NOFILL-CLOSE-ROW-0127"
    assert row["g12_closure_status"] == "source_closed"
    assert row["g12_resolution_status"] == "SOURCE_CLOSED_BY_EXISTING_LOCAL_OTR061_TICK_FILE"
    assert row["source_sha256"] == "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"
    assert row["rows_inside_requested_window"] > 0
    assert row["terminal_area_touch_time_utc"] == "2026-05-06T07:15:00.634000Z"
    assert row["entry_touch_time_utc"] is None
    assert row["protective_level_touch_time_utc"] is None
    assert row["covers_decisive_source_event"] is True


def test_hash_noleak_and_flags_are_preserved():
    audit = load_json("G12_NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json")
    assert audit["g12_recomputed_hashes"]["strict_source_mismatch_count"] == 0
    assert audit["g12_recomputed_hashes"]["missing_count"] == 0
    assert audit["forbidden_packet_key_hits_count"] == 0
    assert audit["flag_violations"] == []
    assert audit["no_leak_status"] == "PASS"
    assert audit["asof_and_freeze_order"]["status"] == "PASS"
    assert audit["validation_safe"] is False
    assert audit["outcome_review_opened"] is False
    assert audit["live_effect"] is False
    assert audit["promotion_verdict"] == "NO_PROMOTION_VERDICT"


def test_blocker_manifest_is_retained_only_for_future_full_window_need():
    audit = load_json("G12_NOFILL_CLOSE_BLOCKER_AND_REQUEST_AUDIT_2026-05-08.json")
    assert audit["g12_source_blocker_decision"]["decision"] == "REJECT_UPSTREAM_EXACT_BLOCKER_AS_LOCALLY_RESOLVABLE"
    manifest = audit["source_request_manifest_audit"]
    assert manifest["symbol"] == "XAUUSD"
    assert manifest["start_utc"] == "2026-05-06T07:15:00Z"
    assert manifest["end_utc"] == "2026-05-06T17:15:00Z"
    assert manifest["must_hash_output"] is True
    assert manifest["current_audit_status"] == "NOT_NEEDED_FOR_SOURCE_ONLY_ROW_0127_CLOSURE_AFTER_OTR061_LOCAL_FILE_FOUND"


def test_duplicate_samplefloor_and_label_family_block_promotion():
    duplicate = load_json("G12_NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json")
    label = load_json("G12_NOFILL_CLOSE_LABEL_FAMILY_AUDIT_2026-05-08.json")
    assert duplicate["packet_rows"] == 298
    assert duplicate["g12_status"] == "PASS_DUPLICATE_AND_SAMPLE_FLOOR_CONTROLS_BLOCK_VALIDATION"
    assert label["status"] == "PASS_LABEL_FAMILY_SEPARATION_PRESERVED"
    assert label["validation_safe"] is False
