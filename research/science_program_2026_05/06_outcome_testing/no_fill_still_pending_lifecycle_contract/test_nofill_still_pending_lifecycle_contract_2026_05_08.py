#!/usr/bin/env python3
"""Focused tests for the no-fill/still-pending lifecycle contract lane."""

from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
BUILDER_PATH = OUT_DIR / "build_nofill_still_pending_lifecycle_contract_2026_05_08.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("nofill_builder_test", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


builder = load_builder()


def load_json(name: str):
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def load_rows():
    rows = []
    for line in (OUT_DIR / "NOFILL_INPUT_ONLY_PACKET_2026-05-08_ROWS.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def test_contract_does_not_reuse_t3_label():
    contract = load_json("NOFILL_FROZEN_LIFECYCLE_CONTRACT_2026-05-08.json")
    assert contract["contract_id"] == builder.CONTRACT_ID
    assert "stop_after_original_horizon" not in contract["allowed_labels"]
    assert contract["validation_safe"] is False
    assert contract["outcome_review_opened"] is False
    assert contract["live_effect"] is False


def test_reconstructs_exact_298_non_t3_universe():
    rows, _inv, _blocker, g12_no_leak, _g12 = builder.reconstruct_universe()
    assert len(rows) == 298
    assert {row["lifecycle_label_or_blocker_label"] for row in rows} == {"not_packet_eligible"}
    assert "OTI8_CNR061" not in {row["source_lane"] for row in rows}
    assert g12_no_leak["blocked_94_exclusion"]["blocked_rows"] == 94
    assert g12_no_leak["blocked_94_exclusion"]["status"] == "PASS"


def test_packet_label_counts_are_expected():
    rows = load_rows()
    assert len(rows) == 298
    assert Counter(row["contract_label"] for row in rows) == {
        "no_fill_cancelled_wrong_side_before_fill": 22,
        "no_fill_still_pending_at_frozen_lifecycle_horizon": 32,
        "no_entry_touch_before_terminal_area": 46,
        "no_entry_touch_no_r_scored": 48,
        "source_blocked_no_price_compatible_m1": 69,
        "terminal_order_unclaimed_entry_touched_unresolved": 1,
        "terminal_order_unclaimed_local_ohlc_bounded": 80,
    }
    assert Counter(row["source_lane"] for row in rows) == {
        "OTI1_LIFECYCLE": 54,
        "OTI2_RISKBANK": 47,
        "OTI3_G3_GEOMETRY": 69,
        "OTI4_G6_OPENING_DRIVE": 80,
        "OTI5_G6_CUSUM": 48,
    }


def test_packet_rows_do_not_carry_forbidden_fields_or_t3_rows():
    rows = load_rows()
    hits = builder.scan_forbidden(rows)
    assert hits == []
    for row in rows:
        assert row["promotion_verdict"] == "NO_PROMOTION_VERDICT"
        assert row["validation_safe"] is False
        assert row["outcome_review_opened"] is False
        assert row["live_effect"] is False
        assert row["source_lane"] != "OTI8_CNR061"
        assert row["contract_label"] != "stop_after_original_horizon"
        for key in row:
            assert key.lower() not in builder.FORBIDDEN_PACKET_KEYS


def test_source_hash_ledger_has_no_mismatches():
    ledger = load_json("NOFILL_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json")
    assert ledger["hash_summary"]["expected_hash_mismatches"] == []
    # Missing expected files are allowed only as recorded source/blocker evidence.
    assert isinstance(ledger["hash_summary"]["missing_expected_files"], list)
    assert ledger["promotion_verdict"] == "NO_PROMOTION_VERDICT"


def test_noleak_sample_floor_remains_validation_blocked():
    audit = load_json("NOFILL_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json")
    assert audit["status"] == "PASS"
    assert audit["forbidden_packet_hits_count"] == 0
    assert audit["validation_sample_floor_status"] == "FALSE_INPUT_ONLY_CONTROL_PACKET_NOT_VALIDATION"
    assert audit["blocked_94_exclusion"]["status"] == "PASS"
