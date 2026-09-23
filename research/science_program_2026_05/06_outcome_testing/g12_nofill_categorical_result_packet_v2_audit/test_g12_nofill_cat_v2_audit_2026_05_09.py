from __future__ import annotations

import importlib.util
import json
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
DATE = "2026-05-09"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def read_json(name: str):
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def test_exact_partition_counts_overlap_and_sources():
    decision = read_json(f"G12_NOFILL_CAT_V2_DECISION_LEDGER_{DATE}.json")

    assert decision["status"] == "PASS"
    assert decision["partition_counts"] == {
        "accepted": 225,
        "accepted_prior": 52,
        "accepted_source_corrected": 173,
        "blocked": 8,
        "rejected": 65,
    }
    assert decision["decision_counts"] == {
        "ACCEPT_PRIOR_CATEGORICAL_LABEL": 52,
        "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 173,
        "BLOCK_EXACT_SOURCE_OR_ORDERING_GAP": 8,
        "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26,
        "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39,
    }
    assert decision["accepted_source_lane_counts"] == {
        "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET": 32,
        "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2": 29,
        "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT": 58,
        "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION": 51,
        "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT": 3,
        "prior_g12_categorical_packet_audit": 52,
    }
    assert decision["overlap_checks"]["accepted_blocker_overlap"] == []
    assert decision["overlap_checks"]["accepted_reject_overlap"] == []
    assert decision["overlap_checks"]["blocker_reject_overlap"] == []
    assert decision["overlap_checks"]["partition_unique_ids"] == 298


def test_label_counts_meanings_and_denominator_rules():
    decision = read_json(f"G12_NOFILL_CAT_V2_DECISION_LEDGER_{DATE}.json")
    noleak = read_json(f"G12_NOFILL_CAT_V2_NO_LEAK_LABEL_DUPLICATE_AUDIT_{DATE}.json")

    expected = {
        "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
        "fill_path_entry_before_protective_level_before_terminal_area": 4,
        "fill_path_entry_before_protective_level_no_terminal_observed": 22,
        "fill_path_entry_before_terminal_area_before_protective_level": 3,
        "nofill_terminal_before_entry": 110,
        "opening_drive_source_projection_ready_no_result_label": 51,
        "source_corrected_no_entry_through_pending_horizon": 32,
    }
    assert decision["accepted_label_counts"] == expected
    for label, count in expected.items():
        assert decision["label_meanings"][label]["count"] == count
        assert "not R/performance" in decision["label_meanings"][label]["does_not_prove"]

    accepted = [row for row in decision["row_decisions"] if row["g12_audit_decision"] == "ACCEPT_NARROW_INPUT_ONLY_ROW"]
    blocked_or_rejected = [row for row in decision["row_decisions"] if row["g12_audit_decision"] != "ACCEPT_NARROW_INPUT_ONLY_ROW"]
    assert len(accepted) == 225
    assert len(blocked_or_rejected) == 73
    assert all(row["categorical_input_label"] for row in accepted)
    assert all(row["categorical_input_label"] is None for row in blocked_or_rejected)
    assert all(row["in_accepted_packet_denominator"] is False for row in blocked_or_rejected)

    assert noleak["status"] == "PASS"
    assert noleak["countable_scope"]["performance_outcome_rows"] == 0
    assert noleak["countable_scope"]["validation_or_promotion_rows"] == 0
    assert noleak["sample_floor_posture"]["dsr_pbo_effective_n_status"] == "not_computable_no_result_values_opened"


def test_blocker_and_reject_reviews_are_exact():
    review = read_json(f"G12_NOFILL_CAT_V2_BLOCKER_REJECT_REVIEW_{DATE}.json")

    assert review["status"] == "PASS"
    assert review["blocked_row_count"] == 8
    assert review["rejected_row_count"] == 65
    assert review["blocker_code_counts"] == {
        "BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE": 4,
        "BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP": 1,
        "BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED": 1,
        "BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP": 3,
    }
    assert review["reject_decision_counts"] == {
        "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26,
        "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39,
    }
    assert review["blocker_reviews"]["oti4_may3_source_gaps"]["row_count"] == 3
    assert review["blocker_reviews"]["oti3_same_tick_order_ambiguities"]["row_count"] == 4
    assert review["blocker_reviews"]["original_oti2_source_gap"]["row_count"] == 1
    assert review["blocked_or_rejected_rows_have_no_label"] is True
    assert review["blocked_or_rejected_rows_in_denominator"] == []
    assert review["hidden_performance_reason_detected"] is False


def test_source_hash_and_blocker_proofs_pass():
    source = read_json(f"G12_NOFILL_CAT_V2_SOURCE_HASH_AUDIT_{DATE}.json")

    assert source["status"] == "PASS"
    assert source["missing_control_inputs"] == []
    assert source["v2_control_input_rehash"]["status"] == "PASS"
    assert source["v2_control_input_rehash"]["mismatches"] == []
    assert source["source_hash_drift_classification"] in {
        "NO_DRIFT",
        "NON_SOURCE_CONTROL_PROMPT_HASH_DRIFT_NO_DATA_INVALIDATION",
    }
    assert len(source["recomputed_oti3_same_tick_order_checks"]) == 4
    assert all(row["status"] == "PASS" and row["matching_tick_record_count"] == 1 for row in source["recomputed_oti3_same_tick_order_checks"])
    assert len(source["recomputed_oti4_may3_source_gap_checks"]) == 3
    assert all(
        row["status"] == "PASS"
        and all(file_check["required_range_count"] == 0 for file_check in row["file_checks"])
        for row in source["recomputed_oti4_may3_source_gap_checks"]
    )
    assert source["recomputed_original_oti2_source_gap_check"]["status"] == "PASS"
    assert source["recomputed_original_oti2_source_gap_check"]["row_count"] == 1


def test_verifier_passes_without_nested_pytest():
    verifier = load_module(
        "g12_cat_v2_verifier",
        OUT_DIR / "verify_g12_nofill_cat_v2_audit_2026_05_09.py",
    )
    report = verifier.verify_audit(run_pytest=False, write_audit=False)
    assert report["verification_status"]["status"] == "PASS", report
