from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
BUILDER_PATH = HERE / "build_unc004_source_confidence_mechanism_disentanglement_2026_05_15.py"
spec = importlib.util.spec_from_file_location("unc004_builder", BUILDER_PATH)
builder = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)


def synthetic_target(**overrides):
    row = {
        "target_family_id": "neutral_close_to_close_return_m15_horizons_v1",
        "terminal_status": "COMPUTABLE",
        "denominator_role": "per_card_pass_row",
        "close_to_close_percent_return": 0.001,
        "upside_excursion_percent": None,
        "downside_excursion_percent": None,
        "duplicate_proxy_denominator_key": "dup-1",
        "symbol": "XAUUSD_GC",
        "canonical_economic_group": "XAUUSD_GOLD_FUTURES_PROXY",
        "session_bucket": "LONDON_UTC_0700_1030",
        "source_segment_sha256": "seg-1",
        "source_confidence_tier": "LOW_CONFIDENCE_PARTIAL_PRIOR_DESCRIPTOR",
        "target_family_counts": {},
        "horizon_m15_bars": 4,
    }
    row.update(overrides)
    return row


def test_target_value_close_to_close_and_high_low():
    assert builder.target_value(synthetic_target(close_to_close_percent_return=-0.002)) == -0.002
    high_low = synthetic_target(
        target_family_id="neutral_high_low_excursion_m15_horizons_v1",
        close_to_close_percent_return=None,
        upside_excursion_percent=0.004,
        downside_excursion_percent=0.0015,
    )
    assert builder.target_value(high_low) == 0.0025
    incomplete = synthetic_target(
        target_family_id="neutral_high_low_excursion_m15_horizons_v1",
        close_to_close_percent_return=None,
        upside_excursion_percent=0.004,
        downside_excursion_percent=None,
    )
    assert builder.target_value(incomplete) is None


def test_metric_eligible_excludes_fail_closed_and_fail_role():
    assert builder.metric_eligible(synthetic_target())
    assert not builder.metric_eligible(synthetic_target(terminal_status="FAIL_CLOSED_NOT_COMPUTABLE"))
    assert not builder.metric_eligible(synthetic_target(denominator_role="per_card_fail_closed_row"))


def test_source_confidence_from_descriptor_row():
    low = {"prior_windows": {"16": {"complete": False}, "32": {"complete": False}}, "source_coverage_quality_bucket": "PARTIAL"}
    med = {"prior_windows": {"16": {"complete": True}, "32": {"complete": False}}, "source_coverage_quality_bucket": "PARTIAL"}
    high = {"prior_windows": {"16": {"complete": True}, "32": {"complete": True}}, "source_coverage_quality_bucket": "PARTIAL"}
    assert builder.source_confidence_from_descriptor_row(low)["source_confidence_tier"] == "LOW_CONFIDENCE_PARTIAL_PRIOR_DESCRIPTOR"
    assert builder.source_confidence_from_descriptor_row(med)["source_confidence_tier"] == "MEDIUM_CONFIDENCE_PRIOR16_ONLY"
    assert builder.source_confidence_from_descriptor_row(high)["source_confidence_tier"] == "HIGH_CONFIDENCE_PRIOR32_COMPLETE"


def test_comparison_record_classifies_positive_inverse_and_missing_control():
    pass_stats = builder.Stats()
    control_stats = builder.Stats()
    for i in range(30):
        pass_stats.update(synthetic_target(duplicate_proxy_denominator_key=f"p-{i}"), 0.002)
        control_stats.update(synthetic_target(duplicate_proxy_denominator_key=f"c-{i}"), 0.001)
    positive = builder.comparison_record("test", {"k": "v"}, pass_stats, control_stats, "2026-05-15T00:00:00Z")
    assert positive["comparison_classification"] == "POSITIVE_PASS_GT_CONTROL"
    inverse = builder.comparison_record("test", {"k": "v"}, control_stats, pass_stats, "2026-05-15T00:00:00Z")
    assert inverse["comparison_classification"] == "INVERSE_PASS_LT_CONTROL"
    missing = builder.comparison_record("test", {"k": "v"}, pass_stats, builder.Stats(), "2026-05-15T00:00:00Z")
    assert missing["comparison_classification"] == "NOT_COMPARABLE_MISSING_PASS_OR_CONTROL"


def test_stats_reports_underpower_and_concentration():
    stats = builder.Stats()
    for i in range(3):
        stats.update(synthetic_target(duplicate_proxy_denominator_key=f"d-{i}", symbol="XAUUSD_GC"), 0.001)
    record = stats.to_record()
    assert record["rows"] == 3
    assert record["unique_duplicate_denominator_count"] == 3
    assert "UNDERPOWERED_UNIQUE_DUPLICATE_FLOOR_LT_30" in record["concentration_or_power_warnings"]
    assert "SYMBOL_CONCENTRATION_GT_50PCT" in record["concentration_or_power_warnings"]
