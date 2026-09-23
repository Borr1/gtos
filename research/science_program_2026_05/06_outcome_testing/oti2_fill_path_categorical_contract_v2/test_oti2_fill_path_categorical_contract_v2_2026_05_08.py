from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


DATE = "2026-05-08"
ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = Path(__file__).resolve().parent


def read_json(name: str):
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def read_jsonl(name: str):
    return [json.loads(line) for line in (OUT_DIR / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_universe_reconstruction_counts():
    universe = read_json(f"OTI2_FILL_PATH_UNIVERSE_RECONSTRUCTION_{DATE}.json")
    assert universe["candidate_universe_row_count"] == 34
    assert universe["required_source_counts"] == {
        "original_oti2_router_rows": 1,
        "oti1_source_authorized_entry_touch_rows": 22,
        "oti3_entry_touch_before_terminal_rows": 7,
        "oti3_same_timestamp_ambiguity_rows": 4,
    }
    assert universe["label_assigned_rows"] == 29
    assert universe["blocked_before_label_rows"] == 5


def test_row_decision_ledger_labels_and_blockers():
    rows = read_jsonl(f"OTI2_FILL_PATH_ROW_DECISION_LEDGER_{DATE}.jsonl")
    assert len(rows) == 34
    assert Counter(row["source_family"] for row in rows) == {
        "OTI1_PENDING_INTENT": 22,
        "OTI2_ORIGINAL_ROUTER": 1,
        "OTI3_USDJPY": 11,
    }
    assert Counter(row["categorical_fill_path_label"] for row in rows if row["categorical_fill_path_label"]) == {
        "fill_path_entry_before_protective_level_before_terminal_area": 4,
        "fill_path_entry_before_protective_level_no_terminal_observed": 22,
        "fill_path_entry_before_terminal_area_before_protective_level": 3,
    }
    blockers = Counter(code for row in rows for code in row["exact_blocker_codes"])
    assert blockers["BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE"] == 4
    assert blockers["BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED"] == 1
    assert blockers["BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP"] == 1


def test_oti3_same_timestamp_rows_remain_blocked_with_source_inspection():
    rows = read_jsonl(f"OTI2_FILL_PATH_ROW_DECISION_LEDGER_{DATE}.jsonl")
    same_timestamp = [
        row
        for row in rows
        if row["source_family"] == "OTI3_USDJPY"
        and row["source_order_resolution"]["same_timestamp_ambiguity"]
    ]
    assert {row["source_close_packet_row_id"] for row in same_timestamp} == {
        "NOFILL-CLOSE-ROW-0130",
        "NOFILL-CLOSE-ROW-0143",
        "NOFILL-CLOSE-ROW-0165",
        "NOFILL-CLOSE-ROW-0178",
    }
    for row in same_timestamp:
        assert row["eligibility_decision"] == "BLOCKED_BEFORE_LABEL"
        assert row["categorical_fill_path_label"] is None
        assert row["source_order_resolution"]["source_order_status"] == "not_resolvable_from_source_safe_tick_order"
        assert row["source_order_resolution"]["same_timestamp_inspection"]["rows_at_first_timestamp"] == 1


def test_contract_and_flags_preserve_no_promotion_boundary():
    contract = read_json(f"OTI2_FILL_PATH_FROZEN_CONTRACT_{DATE}.json")
    completion = read_json(f"OTI2_FILL_PATH_COMPLETION_AUDIT_{DATE}.json")
    for artifact in (contract, completion):
        assert artifact["promotion_verdict"] == "NO_PROMOTION_VERDICT"
        assert artifact["validation_safe"] is False
        assert artifact["outcome_review_opened"] is False
        assert artifact["live_effect"] is False
    assert contract["contract_status"] == "FROZEN_BEFORE_ROW_LABELING"


def test_source_hash_noleak_and_duplicate_sample_floor_audits():
    source_audit = read_json(f"OTI2_FILL_PATH_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json")
    duplicate_audit = read_json(f"OTI2_FILL_PATH_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json")
    assert source_audit["source_hash_missing_count"] == 0
    assert source_audit["source_hash_mismatch_count"] == 0
    assert source_audit["forbidden_output_key_hit_count"] == 0
    assert duplicate_audit["row_count"] == 34
    assert duplicate_audit["unique_nofill_duplicate_key_count"] == 34
    assert duplicate_audit["duplicate_key_conflicts"] == {}
    assert duplicate_audit["sample_floor_status"] == "UNDER_SAMPLE_FLOOR_NO_VALIDATION"
