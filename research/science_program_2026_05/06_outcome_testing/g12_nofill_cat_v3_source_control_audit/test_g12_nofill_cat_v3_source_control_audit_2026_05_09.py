from __future__ import annotations

import json
from pathlib import Path

import verify_g12_nofill_cat_v3_source_control_audit_2026_05_09 as verifier


DATE = "2026-05-09"
LANE_DIR = Path(__file__).resolve().parent
MAY3_ROWS = {
    "NOFILL-CAT-ROW-0049",
    "NOFILL-CAT-ROW-0050",
    "NOFILL-CAT-ROW-0051",
}
XAU_ROW = "NOFILL-CAT-ROW-0241"
USDJPY_ROWS = {
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
}


def load_json(name: str):
    return json.loads((LANE_DIR / name).read_text(encoding="utf-8"))


def test_verifier_passes_without_external_recursion():
    result = verifier.verify(run_external=False)
    assert result["ok"] is True, result["issues"]
    assert result["can_mark_goal_complete"] is True


def test_universe_counts_and_target_identities_are_exact():
    universe = load_json(f"G12_NOFILL_CAT_V3_UNIVERSE_AND_COUNT_AUDIT_{DATE}.json")
    assert universe["row_count"] == 298
    assert universe["unique_packet_row_ids"] == 298
    assert universe["terminal_family_counts"] == {
        "accepted": 225,
        "blocked": 0,
        "reject": 65,
        "source_control": 4,
        "source_impossible": 4,
    }
    assert universe["accepted_row_field_mismatch_count"] == 0
    assert set(universe["target_row_states"]) == MAY3_ROWS | {XAU_ROW} | USDJPY_ROWS


def test_source_control_rows_are_non_denominator_and_source_rechecked():
    audit = load_json(f"G12_NOFILL_CAT_V3_SOURCE_CONTROL_ROW_AUDIT_{DATE}.json")
    assert audit["status"] == "PASS"
    row_map = {row["packet_row_id"]: row for row in audit["row_audits"]}
    assert set(row_map) == MAY3_ROWS | {XAU_ROW}
    for row_id in MAY3_ROWS:
        row = row_map[row_id]
        assert row["decision"] == "ACCEPT_AS_SOURCE_CONTROL_MARKET_SESSION_EMPTY_EVIDENCE_ONLY"
        assert row["v3_denominator"] is False
        assert row["v3_lifecycle_label"] is None
        assert row["frozen_window_rows"] == 0
        assert row["accepted"] is True
    xau = row_map[XAU_ROW]
    assert xau["decision"] == "ACCEPT_AS_SOURCE_CONTROL_INPUT_ONLY_EVIDENCE"
    assert xau["v3_denominator"] is False
    assert xau["v3_lifecycle_label"] is None
    assert xau["may5_entry_touch"] is False
    assert xau["recovered_gap_entry_touch"] is False
    assert xau["recovered_gap_rows_rechecked"] == 549


def test_source_impossible_rows_have_exact_unblocker_and_same_tick_proof():
    audit = load_json(f"G12_NOFILL_CAT_V3_SOURCE_IMPOSSIBILITY_AUDIT_{DATE}.json")
    assert audit["status"] == "PASS"
    assert set(audit["source_impossible_row_ids"]) == USDJPY_ROWS
    assert audit["source_search"]["source_sequence_route_found"] is False
    assert "sequence" in audit["exact_unblocker"].lower()
    for row in audit["row_audits"]:
        assert row["packet_row_id"] in USDJPY_ROWS
        assert row["decision"] == "ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY"
        assert row["v3_denominator"] is False
        assert row["v3_lifecycle_label"] is None
        assert row["same_tick_impossibility_holds"] is True
        assert row["source_recheck"]["exact_timestamp_row_count"] == 1
        exact = row["source_recheck"]["exact_rows"][0]
        assert exact["entry_touch"] is True
        assert exact["protective_level"] is True
        assert exact["terminal_area"] is False


def test_reject_hash_duplicate_and_completion_boundaries():
    rejects = load_json(f"G12_NOFILL_CAT_V3_REJECT_DENOMINATOR_AUDIT_{DATE}.json")
    hashes = load_json(f"G12_NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json")
    duplicates = load_json(f"G12_NOFILL_CAT_V3_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json")
    completion = load_json(f"G12_NOFILL_CAT_V3_COMPLETION_AUDIT_{DATE}.json")

    assert rejects["rejected_row_count"] == 65
    assert rejects["reject_rows_outside_labels_denominators"] is True
    assert hashes["status"] == "PASS"
    assert hashes["strict_failure_count"] == 0
    assert hashes["missing_record_count"] == 0
    assert hashes["line_ending_only_mismatch_count"] == 1
    assert hashes["noleak_checks"]["forbidden_output_key_hit_count"] == 0
    assert duplicates["accepted_denominator_row_count"] == 225
    assert duplicates["sample_floor_policy"]["scored_sample_floor_opened"] is False
    assert not any(duplicates["nonaccepted_denominator_violations"].values())
    assert completion["can_mark_goal_complete"] is True
    assert completion["missing_incomplete_or_weak_requirements"] == []
