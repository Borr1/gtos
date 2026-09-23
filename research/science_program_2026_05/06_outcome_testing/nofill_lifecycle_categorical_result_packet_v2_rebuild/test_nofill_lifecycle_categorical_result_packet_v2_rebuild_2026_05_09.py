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


def read_jsonl(name: str):
    return [json.loads(line) for line in (OUT_DIR / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_exact_partition_counts_and_overlap():
    rows = read_jsonl(f"NOFILL_CAT_V2_ROW_DECISION_LEDGER_{DATE}.jsonl")
    accepted = read_json(f"NOFILL_CAT_V2_ACCEPTED_PACKET_{DATE}.json")["rows"]
    blockers = read_json(f"NOFILL_CAT_V2_BLOCKER_LEDGER_{DATE}.json")["rows"]
    rejects = read_json(f"NOFILL_CAT_V2_REJECT_LEDGER_{DATE}.json")["rows"]

    assert len(rows) == 298
    assert len(accepted) == 225
    assert len(blockers) == 8
    assert len(rejects) == 65

    accepted_ids = {row["packet_row_id"] for row in accepted}
    blocker_ids = {row["packet_row_id"] for row in blockers}
    reject_ids = {row["packet_row_id"] for row in rejects}
    assert not (accepted_ids & blocker_ids)
    assert not (accepted_ids & reject_ids)
    assert not (blocker_ids & reject_ids)
    assert len(accepted_ids | blocker_ids | reject_ids) == 298


def test_labels_only_on_accepted_rows_and_expected_label_counts():
    accepted_packet = read_json(f"NOFILL_CAT_V2_ACCEPTED_PACKET_{DATE}.json")
    blockers = read_json(f"NOFILL_CAT_V2_BLOCKER_LEDGER_{DATE}.json")["rows"]
    rejects = read_json(f"NOFILL_CAT_V2_REJECT_LEDGER_{DATE}.json")["rows"]

    assert accepted_packet["accepted_label_counts"] == {
        "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
        "fill_path_entry_before_protective_level_before_terminal_area": 4,
        "fill_path_entry_before_protective_level_no_terminal_observed": 22,
        "fill_path_entry_before_terminal_area_before_protective_level": 3,
        "nofill_terminal_before_entry": 110,
        "opening_drive_source_projection_ready_no_result_label": 51,
        "source_corrected_no_entry_through_pending_horizon": 32,
    }
    assert all(row["categorical_input_label"] for row in accepted_packet["rows"])
    assert all(row["in_accepted_packet_denominator"] is True for row in accepted_packet["rows"])
    assert all(row["categorical_input_label"] is None for row in blockers + rejects)
    assert all(row["categorical_lifecycle_label"] is None for row in blockers + rejects)
    assert all(row["in_accepted_packet_denominator"] is False for row in blockers + rejects)


def test_blockers_and_rejects_are_exact():
    blockers = read_json(f"NOFILL_CAT_V2_BLOCKER_LEDGER_{DATE}.json")
    rejects = read_json(f"NOFILL_CAT_V2_REJECT_LEDGER_{DATE}.json")

    assert blockers["blocker_summary"] == {
        "original_oti2_source_gap_rows": 1,
        "oti3_same_tick_order_ambiguities": 4,
        "oti4_may3_source_gaps": 3,
    }
    assert blockers["blocker_code_counts"] == {
        "BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE": 4,
        "BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP": 1,
        "BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED": 1,
        "BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP": 3,
    }
    assert rejects["reject_decision_counts"] == {
        "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26,
        "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39,
    }


def test_source_duplicate_completion_audits_pass():
    source = read_json(f"NOFILL_CAT_V2_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json")
    duplicate = read_json(f"NOFILL_CAT_V2_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json")
    completion = read_json(f"NOFILL_CAT_V2_COMPLETION_AUDIT_{DATE}.json")

    assert source["status"] == "PASS"
    assert source["missing_control_inputs"] == []
    assert source["forbidden_generated_key_hits"] == []
    assert source["inherited_g12_source_hash_record_count"] == 174
    assert duplicate["status"] == "PASS"
    assert duplicate["accepted_rows"] == 225
    assert duplicate["accepted_unique_nofill_duplicate_keys"] == 182
    assert duplicate["rejected_noncanonical_duplicate_rows"] == 39
    assert completion["completion_status"] == "PASS"
    assert completion["can_mark_goal_complete"] is True


def test_verifier_passes():
    verifier = load_module(
        "nofill_cat_v2_verifier",
        OUT_DIR / "verify_nofill_lifecycle_categorical_result_packet_v2_rebuild_2026_05_09.py",
    )
    report = verifier.run()
    assert report["verification_status"] == "PASS", report
    assert report["can_mark_goal_complete"] is True
