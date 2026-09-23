"""Focused tests for READY8 discriminative card rowset repair helpers and artifacts."""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
BUILD_PATH = HERE / "build_scid_ready8_discriminative_card_rowset_repair_2026_05_13.py"
VERIFY_PATH = HERE / "verify_scid_ready8_discriminative_card_rowset_repair_2026_05_13.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


build = load_module(BUILD_PATH, "ready8_build")
verify = load_module(VERIFY_PATH, "ready8_verify")


def candidate(ts: str, symbol: str = "XAUUSD_GC") -> dict:
    return {
        "candidate_input_row_id": f"candidate:{symbol}:{ts}",
        "duplicate_key": f"dup:{symbol}:{ts}",
        "canonical_economic_group": f"{symbol}_GROUP",
        "decision_asof_utc": ts,
        "partition_assignment": "SEALED_VALIDATION_CANDIDATE_DESIGN",
        "row_hash": "abc",
        "source_file_name": "source.scid",
        "symbol": symbol,
    }


def descriptor(**overrides) -> dict:
    base = {
        "session_bucket": "NEW_YORK_UTC_1300_1700",
        "time_of_day_bucket": "UTC_12_17",
        "source_coverage_quality_bucket": "PRIOR_96_PARTIAL_RECORD_PRESENT",
        "prior_windows": {
            "16": {"complete": True},
            "32": {"complete": True},
        },
        "prior_16_drift_bucket": "PRIOR_16_POSITIVE_DRIFT_P66_P100",
        "prior_16_range_bucket": "PRIOR_16_EXPANDED_RANGE_P66_P100",
        "prior_32_range_bucket": "PRIOR_32_EXPANDED_RANGE_P66_P100",
    }
    base.update(overrides)
    return base


def test_session_open_predicate_splits_pass_contrast_and_non_applicable():
    open_row = build.classify_card("BEH-001", candidate("2026-05-11T13:15:00.000Z"), descriptor(), {})
    later_row = build.classify_card("BEH-001", candidate("2026-05-11T15:00:00.000Z"), descriptor(), {})
    off_row = build.classify_card("BEH-001", candidate("2026-05-11T22:00:00.000Z"), descriptor(session_bucket="GLOBAL_OFF_SESSION_OR_TRANSITION"), {})
    assert open_row["denominator_role"] == "per_card_pass_row"
    assert later_row["denominator_role"] == "per_card_contrast_row"
    assert off_row["denominator_role"] == "per_card_non_applicable_row"


def test_haz001_waiting_time_fail_closed_and_long_gap_pass():
    first = build.classify_card("HAZ-001", candidate("2026-05-11T13:15:00.000Z"), descriptor(), {})
    long_gap = build.classify_card("HAZ-001", candidate("2026-05-11T15:00:00.000Z"), descriptor(), {"previous_candidate_gap_minutes": 105, "prior_24h_candidate_count": 3})
    dense = build.classify_card("HAZ-001", candidate("2026-05-11T15:15:00.000Z"), descriptor(), {"previous_candidate_gap_minutes": 15, "prior_24h_candidate_count": 80})
    assert first["denominator_role"] == "per_card_fail_closed_row"
    assert "MISSING_PRIOR_CANDIDATE_FOR_WAITING_TIME" in first["fail_closed_reasons"]
    assert long_gap["denominator_role"] == "per_card_pass_row"
    assert dense["descriptor_values"]["candidate_density_bucket"] == "DENSE_BURST_PRIOR24_GE64"


def test_mac004_metals_fix_window_and_non_metal_non_applicable():
    metal = build.classify_card("MAC-004", candidate("2026-05-11T09:30:00.000Z", "XAUUSD_GC"), descriptor(), {})
    non_metal = build.classify_card("MAC-004", candidate("2026-05-11T09:30:00.000Z", "NAS100_NQ"), descriptor(), {})
    assert metal["denominator_role"] == "per_card_pass_row"
    assert metal["descriptor_contrast_key"] == "METAL_FIX_WINDOW_PLUS_MINUS_30M"
    assert non_metal["denominator_role"] == "per_card_non_applicable_row"


def test_unc004_confidence_tiers_are_source_only():
    high = build.classify_card("UNC-004", candidate("2026-05-11T13:15:00.000Z"), descriptor(), {})
    low = build.classify_card("UNC-004", candidate("2026-05-11T13:15:00.000Z"), descriptor(prior_windows={"16": {"complete": False}, "32": {"complete": False}}, prior_16_drift_percent=None, prior_32_range_percent=None), {})
    assert high["descriptor_values"]["source_confidence_tier"] == "HIGH_CONFIDENCE_PRIOR32_COMPLETE"
    assert high["denominator_role"] == "per_card_contrast_row"
    assert low["descriptor_values"]["source_confidence_tier"] == "LOW_CONFIDENCE_PARTIAL_PRIOR_DESCRIPTOR"
    assert low["denominator_role"] == "per_card_pass_row"


def test_hash_bucket_deterministic():
    assert build.hash_bucket("same-key", "ADV-003") == build.hash_bucket("same-key", "ADV-003")
    assert build.hash_bucket("same-key", "ADV-003").startswith("DUPLICATE_HASH_BUCKET_")


def test_generated_artifacts_verify():
    result = verify.verify_outputs()
    assert result["ok"], [check for check in result["checks"] if not check["ok"]]
