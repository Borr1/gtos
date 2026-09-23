"""Focused tests for the CNR T3 lifecycle expansion packet builder."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
BUILDER_PATH = THIS_DIR / "build_cnr_t3_lifecycle_expansion_source_packet_2026_05_08.py"
spec = importlib.util.spec_from_file_location("cnr_t3_builder", BUILDER_PATH)
builder = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)


def test_contract_allowed_labels_exact() -> None:
    contract = builder.build_contract()
    assert contract["contract_id"] == "CNR_T3_LIFECYCLE_NO_TERMINAL_EXTENSION_V1"
    assert contract["allowed_labels"] == [
        "target_after_original_horizon",
        "stop_after_original_horizon",
        "ambiguous_target_stop_after_original_horizon",
        "still_no_terminal_after_extended_horizon",
        "source_horizon_insufficient",
        "not_packet_eligible",
    ]
    assert "synthetic_r" in contract["forbidden_fields"]
    assert contract["validation_safe"] is False


def test_quote_side_terminal_rule_short_long_and_ambiguous() -> None:
    assert builder.classify_tick_terminal("SHORT", bid=73.0, ask=74.2, stop=74.1, target=71.8) == (
        "stop_after_original_horizon",
        "ask",
    )
    assert builder.classify_tick_terminal("SHORT", bid=71.6, ask=71.7, stop=74.1, target=71.8) == (
        "target_after_original_horizon",
        "ask",
    )
    assert builder.classify_tick_terminal("LONG", bid=101.0, ask=101.2, stop=99.0, target=100.5) == (
        "target_after_original_horizon",
        "bid",
    )
    assert builder.classify_tick_terminal("LONG", bid=98.5, ask=98.7, stop=99.0, target=100.5) == (
        "stop_after_original_horizon",
        "bid",
    )
    assert builder.classify_tick_terminal("LONG", bid=100.0, ask=100.1, stop=100.0, target=100.0) == (
        "ambiguous_target_stop_after_original_horizon",
        "bid",
    )


def test_oti8_eligibility_requires_no_terminal_and_accepted_hash() -> None:
    row = {
        "terminal_status": "NO_TERMINAL_WITHIN_ORDERED_HORIZON",
        "sidecar_row_sha256": "accepted",
        "symbol": "XAGUSD",
        "side": "SHORT",
        "candidate_close_utc": "2026-05-05T16:30:00+00:00",
        "path_start_utc": "2026-05-05T16:30:00Z",
        "path_end_utc": "2026-05-05T20:30:00Z",
        "original_entry_price": 73.222,
        "original_stop_loss": 74.112,
        "original_take_profit_1": 71.887,
        "quote_source_sha256": "quotehash",
        "row_source_hash": "rowhash",
        "path_source_files": ["ticks.parquet"],
    }
    eligible, reason = builder.is_oti8_t3_eligible(row, {"accepted"})
    assert eligible is True
    assert "eligible" in reason
    row["sidecar_row_sha256"] = "blocked"
    eligible, reason = builder.is_oti8_t3_eligible(row, {"accepted"})
    assert eligible is False
    assert "accepted-row manifest" in reason


def test_non_oti8_no_entry_candidate_is_not_packet_eligible() -> None:
    row = {
        "record_id": "OTG0-PKT-063|XAGUSD_2026-05-04T07:15:00+00:00",
        "packet_id": "OTG0-PKT-063",
        "symbol": "XAUUSD",
        "side": "SHORT",
        "decision_asof_utc": "2026-05-04T07:15:00Z",
        "result_status": "NO_ENTRY_TOUCH_NO_R_SCORED",
        "path_start_utc": "2026-05-04T07:15:00Z",
        "path_end_utc": "2026-05-05T10:45:00Z",
    }
    candidate = builder.mk_candidate(
        1,
        "OTI5_G6_CUSUM",
        THIS_DIR / "dummy.jsonl",
        row,
        "result_status:NO_ENTRY_TOUCH_NO_R_SCORED",
        set(),
    )
    assert candidate.packet_eligible is False
    assert candidate.provisional_label == "not_packet_eligible"
    assert "not an original-horizon" in candidate.packet_eligibility_reason


def test_forbidden_packet_key_detector_recurses() -> None:
    assert builder.contains_forbidden_packet_key({"ok": [{"synthetic_r": 1.0}]}) == ["synthetic_r"]
    assert builder.contains_forbidden_packet_key({"lifecycle_label": "stop_after_original_horizon"}) == []
