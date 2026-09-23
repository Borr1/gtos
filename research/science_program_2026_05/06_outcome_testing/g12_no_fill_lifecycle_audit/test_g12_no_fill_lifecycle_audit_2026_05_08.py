#!/usr/bin/env python3
"""Focused tests for the G12 no-fill lifecycle audit."""

from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
BUILDER_PATH = OUT_DIR / "build_g12_no_fill_lifecycle_audit_2026_05_08.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("g12_nofill_builder_test", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


builder = load_builder()


def load_json(name: str):
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def test_universe_matches_t3_not_packet_eligible_keys():
    state = builder.load_state()
    packet_keys = {builder.row_key(r) for r in state["packet_rows"]}
    t3_not_keys = {builder.row_key(r) for r in state["t3_not_packet_eligible_rows"]}
    t3_blocker_keys = {builder.row_key(r) for r in state["t3_blocker"]["exact_blockers"]}
    assert len(state["packet_rows"]) == 298
    assert len(t3_not_keys) == 298
    assert packet_keys == t3_not_keys
    assert packet_keys == t3_blocker_keys


def test_excludes_t3_and_g12_blocked_cnr061_rows():
    state = builder.load_state()
    packet_keys = {builder.row_key(r) for r in state["packet_rows"]}
    accepted_keys = {builder.row_key(r) for r in state["t3_eligible_rows"]}
    assert len(state["t3_eligible_rows"]) == 6
    assert not packet_keys & accepted_keys
    assert "OTI8_CNR061" not in {r["source_lane"] for r in state["packet_rows"]}
    assert state["noleak"]["blocked_94_exclusion"]["status"] == "PASS"
    assert state["noleak"]["blocked_94_exclusion"]["blocked_rows"] == 94


def test_label_families_are_frozen_and_not_t3_reuse():
    state = builder.load_state()
    contract = state["contract"]
    rows = state["packet_rows"]
    labels = Counter(r["contract_label"] for r in rows)
    assert set(labels).issubset(set(contract["allowed_labels"]))
    assert "not_contract_eligible" in contract["allowed_labels"]
    assert "not_contract_eligible" not in labels
    assert "stop_after_original_horizon" not in labels
    assert "stop_after_original_horizon" not in contract["allowed_labels"]
    assert labels == {
        "no_fill_still_pending_at_frozen_lifecycle_horizon": 32,
        "no_fill_cancelled_wrong_side_before_fill": 22,
        "no_entry_touch_before_terminal_area": 46,
        "terminal_order_unclaimed_entry_touched_unresolved": 1,
        "source_blocked_no_price_compatible_m1": 69,
        "terminal_order_unclaimed_local_ohlc_bounded": 80,
        "no_entry_touch_no_r_scored": 48,
    }
    starts = {r["classification_started_at_utc"] for r in rows}
    assert all(start >= contract["contract_frozen_at_utc"] for start in starts)


def test_no_forbidden_packet_fields_or_value_claims():
    state = builder.load_state()
    hits = builder.scan_forbidden_packet_fields(state["packet_rows"])
    assert hits == []
    for row in state["packet_rows"]:
        assert row["promotion_verdict"] == "NO_PROMOTION_VERDICT"
        assert row["validation_safe"] is False
        assert row["outcome_review_opened"] is False
        assert row["live_effect"] is False
        assert row["no_r_performance_or_live_fields_carried"] is True


def test_duplicate_sample_floor_remains_blocked():
    audit = load_json("G12_NOFILL_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json")
    assert audit["status"] == "PASS"
    assert audit["packet_rows"] == 298
    assert audit["source_inventory_id_unique"] == 298
    assert audit["nofill_duplicate_key_unique"] == 196
    assert audit["validation_sample_floor_status"] == "FALSE_INPUT_ONLY_CONTROL_PACKET_NOT_VALIDATION"


def test_decision_and_completion_preserve_no_promotion_boundary():
    decision = load_json("G12_NOFILL_DECISION_LEDGER_2026-05-08.json")
    completion = load_json("G12_NOFILL_COMPLETION_AUDIT_2026-05-08.json")
    assert decision["overall_decision"] == "ACCEPT_AS_INPUT_ONLY_LIFECYCLE_SOURCE_EVIDENCE"
    for artifact in [decision, completion]:
        assert artifact["promotion_verdict"] == "NO_PROMOTION_VERDICT"
        assert artifact["validation_safe"] is False
        assert artifact["outcome_review_opened"] is False
        assert artifact["live_effect"] is False
