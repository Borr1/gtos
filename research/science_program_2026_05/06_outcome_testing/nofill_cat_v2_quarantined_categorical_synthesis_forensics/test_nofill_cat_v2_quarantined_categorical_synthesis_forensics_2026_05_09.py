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


def test_exact_partition_label_and_source_counts():
    synthesis = read_json(f"NOFILL_CAT_V2_FORENSICS_SYNTHESIS_{DATE}.json")

    assert synthesis["partition_counts"] == {
        "accepted": 225,
        "blocked": 8,
        "rejected": 65,
        "universe": 298,
    }
    assert synthesis["decision_counts"] == {
        "ACCEPT_PRIOR_CATEGORICAL_LABEL": 52,
        "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 173,
        "BLOCK_EXACT_SOURCE_OR_ORDERING_GAP": 8,
        "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26,
        "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39,
    }
    assert synthesis["accepted_label_counts"] == {
        "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
        "fill_path_entry_before_protective_level_before_terminal_area": 4,
        "fill_path_entry_before_protective_level_no_terminal_observed": 22,
        "fill_path_entry_before_terminal_area_before_protective_level": 3,
        "nofill_terminal_before_entry": 110,
        "opening_drive_source_projection_ready_no_result_label": 51,
        "source_corrected_no_entry_through_pending_horizon": 32,
    }
    assert synthesis["accepted_source_lane_counts"] == {
        "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET": 32,
        "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2": 29,
        "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT": 58,
        "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION": 51,
        "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT": 3,
        "prior_g12_categorical_packet_audit": 52,
    }


def test_slice_ledger_sums_and_duplicate_policy():
    slices = read_json(f"NOFILL_CAT_V2_FORENSICS_SLICE_LEDGER_{DATE}.json")

    assert slices["accepted_denominator"] == 225
    for key in ("by_label", "by_source_lane", "by_symbol", "by_session", "by_side"):
        assert sum(item["row_count"] for item in slices["accepted_slices"][key]) == 225

    duplicate = slices["duplicate_and_canonical_policy"]
    assert duplicate["accepted_unique_nofill_duplicate_keys"] == 182
    assert duplicate["duplicate_key_collision_count"] == 5
    assert duplicate["rows_in_duplicate_key_collisions"] == 48
    assert duplicate["collision_label_counts"] == {
        "opening_drive_source_projection_ready_no_result_label": 48
    }
    assert duplicate["oti5_canonical_duplicate_rows_accepted"] == 3
    assert duplicate["oti5_noncanonical_duplicate_rows_rejected"] == 39


def test_label_family_analysis_has_mechanisms_nonclaims_and_fill_path_rollup():
    labels = read_json(f"NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_{DATE}.json")

    expected_labels = {
        "canonical_duplicate_geometry_source_ready_no_label_assigned",
        "fill_path_entry_before_protective_level_before_terminal_area",
        "fill_path_entry_before_protective_level_no_terminal_observed",
        "fill_path_entry_before_terminal_area_before_protective_level",
        "nofill_terminal_before_entry",
        "opening_drive_source_projection_ready_no_result_label",
        "source_corrected_no_entry_through_pending_horizon",
    }
    assert set(labels["label_families"]) == expected_labels
    for item in labels["label_families"].values():
        assert item["plain_mechanism"]
        assert item["what_it_proves"]
        assert item["failure_anatomy"]
        assert item["future_hypothesis"]
        assert item["descriptive_only"] is True
        assert item["validation_safe"] is False
        assert "not R/performance" in item["what_it_does_not_prove"]
        assert "not validation" in item["what_it_does_not_prove"]
        assert "not promotion" in item["what_it_does_not_prove"]

    assert labels["oti2_fill_path_family_rollup"]["row_count"] == 29
    assert labels["oti2_fill_path_family_rollup"]["label_counts"] == {
        "fill_path_entry_before_protective_level_before_terminal_area": 4,
        "fill_path_entry_before_protective_level_no_terminal_observed": 22,
        "fill_path_entry_before_terminal_area_before_protective_level": 3,
    }


def test_blocker_reject_learning_is_exact_and_actionable():
    learning = read_json(f"NOFILL_CAT_V2_FORENSICS_BLOCKER_REJECT_LEARNING_{DATE}.json")

    assert learning["blocked_row_count"] == 8
    assert learning["rejected_row_count"] == 65
    assert learning["blocker_code_counts"] == {
        "BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE": 4,
        "BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP": 1,
        "BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED": 1,
        "BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP": 3,
    }
    assert learning["reject_decision_counts"] == {
        "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26,
        "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39,
    }
    assert learning["blocker_families"]["oti4_may3_source_gaps"]["row_count"] == 3
    assert learning["blocker_families"]["oti3_same_tick_order_ambiguities"]["row_count"] == 4
    assert learning["blocker_families"]["original_oti2_source_gap"]["row_count"] == 1
    for item in learning["blocker_families"].values():
        assert item["unblocker"]
        assert item["status"]
    assert learning["g12_recomputed_proofs_referenced"] == {
        "original_oti2_source_gap_rows": 1,
        "oti3_same_tick_checks": 4,
        "oti4_may3_source_gap_checks": 3,
    }


def test_noleak_future_and_completion_audits_pass():
    noleak = read_json(f"NOFILL_CAT_V2_FORENSICS_NO_LEAK_DUPLICATE_SOURCE_AUDIT_{DATE}.json")
    future = read_json(f"NOFILL_CAT_V2_FORENSICS_FUTURE_HYPOTHESIS_AND_CAPTURE_LEDGER_{DATE}.json")
    completion = read_json(f"NOFILL_CAT_V2_FORENSICS_COMPLETION_AUDIT_{DATE}.json")

    assert noleak["status"] == "PASS"
    assert noleak["missing_control_inputs"] == []
    assert all(item["status"] == "PASS" for item in noleak["contradiction_checks"])
    assert noleak["path_result_leakage_status"] == "PASS_NO_RESULT_VALUES_OPENED"
    assert noleak["hidden_semantics_status"] == "PASS_NO_HIDDEN_PERFORMANCE_LABELS_DETECTED"

    assert future["route_decision"]["primary_next_route"] == "G12_NOFILL_CAT_V2_QUARANTINED_CATEGORICAL_SYNTHESIS_FORENSICS_AUDIT"
    assert future["route_decision"]["secondary_route"] == "NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE"
    assert future["route_decision"]["quantitative_result_lane_status"] == "FORBIDDEN_UNTIL_SEPARATE_FROZEN_PREREG_G12_GATE_AND_SAMPLE_FLOOR"
    assert any(item["lane"] == "Residual 8 blocker-clear access lane" for item in future["future_control_lanes"])

    assert completion["completion_status"] == "PASS"
    assert completion["can_mark_goal_complete"] is True
    assert all(item["status"] == "PASS" for item in completion["prompt_to_artifact_checklist"])


def test_verifier_passes_without_nested_pytest():
    verifier = load_module(
        "nofill_cat_v2_forensics_verifier",
        OUT_DIR / "verify_nofill_cat_v2_quarantined_categorical_synthesis_forensics_2026_05_09.py",
    )
    report = verifier.verify_forensics(run_pytest=False, write_audit=False)
    assert report["verification_status"]["status"] == "PASS", report
    assert report["can_mark_goal_complete"] is True
