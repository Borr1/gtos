from __future__ import annotations

import json
from pathlib import Path

import build_cnr_source_field_packet_builder_2026_05_07 as builder
import verify_cnr_source_field_packet_builder_2026_05_07 as verifier


LANE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-07"


def test_target_binding_keeps_future_targets_blocked_without_scoring():
    geometry = {
        "original_entry_price": 100.0,
        "original_stop_loss": 90.0,
        "original_take_profit_1": 115.0,
    }
    t0 = builder.target_binding("CNR_T0_ORIGINAL_TP1", geometry)
    t1 = builder.target_binding("CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY", geometry)
    assert t0["target_binding_status"] == "BOUND_INPUT_ONLY_ORIGINAL_TP1"
    assert t1["target_binding_status"] == "BLOCKED_TARGET_MODEL_NOT_PREBOUND_FOR_THIS_PACKET"
    assert "target_hit_timestamp" not in json.dumps(t0)
    assert "synthetic_path_r" not in json.dumps(t1)


def test_terminal_policy_is_pre_entry_geometry_gate_only():
    row = {
        "quote_source_status": "QUOTE_EXTRACTED_SOURCE_HASHED",
        "target_binding_status": "BOUND_INPUT_ONLY_ORIGINAL_TP1",
        "side": "LONG",
        "ask": 116.0,
        "bid": 115.5,
        "original_take_profit_1": 115.0,
    }
    policy = builder.terminal_policy(row)
    assert policy["terminal_state_policy"] == "TARGET_ALREADY_PASSED_BEFORE_ELIGIBLE_EXECUTABLE_ENTRY"
    assert policy["pre_entry_target_already_passed_check"] == "TRUE_SOURCE_GEOMETRY_GATE_NO_R_SCORING"


def test_generated_artifacts_verify_after_builder_run():
    builder.build()
    result = verifier.verify()
    assert result["status"] == "PASS", result
    assert result["row_count"] > 0
    assert result["quote_rows"] > 0
    assert set(result["packet_ids"]) == {
        "OTG0-PKT-060",
        "OTG0-PKT-061",
        "OTG0-PKT-062",
        "OTG0-PKT-063",
        "OTG0-PKT-066",
    }


def test_no_result_or_quarantine_output_directory_created():
    bad_dirs = [
        p
        for p in LANE_DIR.iterdir()
        if p.is_dir() and ("result" in p.name.lower() or "quarantine" in p.name.lower())
    ]
    assert bad_dirs == []
