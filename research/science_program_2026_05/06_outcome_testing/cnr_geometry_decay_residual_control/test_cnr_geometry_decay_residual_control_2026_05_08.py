from __future__ import annotations

import json
import sys
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[3]
sys.path.insert(0, str(TEST_DIR))

import build_cnr_geometry_decay_residual_control_2026_05_08 as builder  # noqa: E402


def test_geometry_fields_long_residual_from_executable_quote() -> None:
    row = {
        "side": "LONG",
        "ask": 105.0,
        "bid": 104.9,
        "original_entry_price": 100.0,
        "original_stop_loss": 95.0,
        "original_take_profit_1": 110.0,
        "quote_source_status": "QUOTE_EXTRACTED_SOURCE_HASHED",
        "source_sha256_hashes": ["abc"],
    }

    out = builder.geometry_fields(row)

    assert out["executable_quote_side"] == "ask"
    assert out["original_base_r_price"] == 5.0
    assert out["stop_r_from_executable_quote"] == 2.0
    assert out["residual_target_r_from_executable_quote"] == 0.5
    assert out["quote_displacement_from_original_entry_r"] == 1.0
    assert out["quote_displacement_from_original_tp1_r"] == -1.0
    assert out["market_entry_geometry_valid_for_original_tp1"] is True


def test_geometry_fields_short_invalid_stop_and_target_passed() -> None:
    stop_invalid = {
        "side": "SHORT",
        "ask": 76.0,
        "bid": 75.7,
        "original_entry_price": 75.0,
        "original_stop_loss": 75.5,
        "original_take_profit_1": 74.25,
        "quote_source_status": "QUOTE_EXTRACTED_SOURCE_HASHED",
        "source_sha256_hashes": ["abc"],
    }
    target_passed = {
        "side": "SHORT",
        "ask": 74.1,
        "bid": 74.0,
        "original_entry_price": 75.0,
        "original_stop_loss": 75.5,
        "original_take_profit_1": 74.25,
        "quote_source_status": "QUOTE_EXTRACTED_SOURCE_HASHED",
        "source_sha256_hashes": ["abc"],
    }

    invalid_out = builder.geometry_fields(stop_invalid)
    target_out = builder.geometry_fields(target_passed)

    assert invalid_out["stop_invalid_at_executable_quote"] is True
    assert invalid_out["market_entry_geometry_gate_state"] == "STOP_INVALID_AT_EXECUTABLE_QUOTE"
    assert target_out["target_already_passed_at_executable_quote"] is True
    assert target_out["market_entry_geometry_gate_state"] == "TARGET_ALREADY_PASSED_AT_EXECUTABLE_QUOTE"


def test_built_matrix_is_input_only_when_present() -> None:
    matrix_path = TEST_DIR / "CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX_2026-05-08.jsonl"
    if not matrix_path.exists():
        return
    rows = [json.loads(line) for line in matrix_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert len(rows) == 102
    for row in rows:
        assert row["promotion_verdict"] == "NO_PROMOTION_VERDICT"
        assert row["validation_safe"] is False
        assert row["outcome_review_opened"] is False
        assert row["live_effect"] is False
        assert not builder.FORBIDDEN_INPUT_ROW_KEYS.intersection(row)


def test_ready_source_rows_match_g12_shortlist() -> None:
    rows, ready, manifest, all_source_rows = builder.load_ready_source_rows()

    assert len(rows) == ready["ready_row_count"] == 102
    assert manifest["ready_input_only_rows"] == 102
    assert len(all_source_rows) == manifest["row_count"] == 6200
    assert {r["timing_model_family"] for r in rows} == {
        "CNR_E0_DECISION_CLOSE_MARKET",
        "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE",
    }
    assert {r["target_model_family"] for r in rows} == {"CNR_T0_ORIGINAL_TP1"}
