from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
BUILDER_PATH = HERE / "build_scid_ready8_discriminative_sealed_validation_after_opening_gate_2026_05_13.py"
spec = importlib.util.spec_from_file_location("ready8_sealed_validation_builder", BUILDER_PATH)
builder = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)


def synthetic_row(**overrides):
    row = {
        "card_id": "BEH-001",
        "partition_assignment": "SEALED_VALIDATION_CANDIDATE_DESIGN",
        "target_family_id": "neutral_close_to_close_return_m15_horizons_v1",
        "horizon_m15_bars": 4,
        "denominator_role": "per_card_pass_row",
        "terminal_status": "COMPUTABLE",
        "close_to_close_percent_return": 0.001,
        "upside_excursion_percent": None,
        "downside_excursion_percent": None,
        "duplicate_proxy_denominator_key": "dup-1",
        "canonical_economic_group": "XAUUSD_GOLD_FUTURES_PROXY",
        "source_segment_sha256_expected": "seg-1",
        "symbol": "XAUUSD_GC",
        "descriptor_contrast_key": "OPENING_DRIVE_FIRST_30M",
        "descriptor_values": {
            "session_bucket": "LONDON_UTC_0700_1030",
            "session_open_bucket": "OPENING_DRIVE_FIRST_30M",
        },
        "mechanism_family": "behavioral_session_opening_drive",
        "science_domain": "behavioral_timing",
    }
    row.update(overrides)
    return row


def test_primary_movement_close_and_high_low():
    close_row = synthetic_row(close_to_close_percent_return=-0.002)
    assert builder.primary_movement_value(close_row) == -0.002
    high_low_row = synthetic_row(
        target_family_id="neutral_high_low_excursion_m15_horizons_v1",
        close_to_close_percent_return=None,
        upside_excursion_percent=0.004,
        downside_excursion_percent=0.0015,
    )
    assert builder.primary_movement_value(high_low_row) == 0.0025


def test_metric_eligible_excludes_noncomputable_and_fail_closed_role():
    assert builder.metric_eligible(synthetic_row())
    assert not builder.metric_eligible(synthetic_row(terminal_status="FAIL_CLOSED_NOT_COMPUTABLE"))
    assert not builder.metric_eligible(synthetic_row(denominator_role="per_card_fail_closed_row"))


def test_metric_stats_reports_duplicate_floor_and_concentration():
    stats = builder.MetricStats()
    for i in range(3):
        stats.update(synthetic_row(duplicate_proxy_denominator_key=f"dup-{i}", symbol="XAUUSD_GC"), 0.001 * (i + 1))
    record = stats.to_record()
    assert record["rows"] == 3
    assert record["unique_duplicate_denominator_count"] == 3
    assert record["underpowered_unique_duplicate_floor_lt_30"] is True
    assert "SYMBOL_CONCENTRATION_GT_50PCT" in record["concentration_or_power_warnings"]
    assert record["positive_movement_rate"] == 1.0


def test_compare_record_classifies_positive_and_inverse():
    pass_stats = builder.MetricStats()
    control_stats = builder.MetricStats()
    for i in range(30):
        pass_stats.update(synthetic_row(duplicate_proxy_denominator_key=f"p-{i}"), 0.002)
        control_stats.update(synthetic_row(duplicate_proxy_denominator_key=f"c-{i}", denominator_role="per_card_contrast_row"), 0.001)
    record = builder.compare_record("test_family", builder.make_key({"card_id": "BEH-001"}), pass_stats, control_stats, "pass_vs_control")
    assert record["comparison_classification"] == "POSITIVE_PASS_GT_CONTROL"
    inverse = builder.compare_record("test_family", builder.make_key({"card_id": "BEH-001"}), control_stats, pass_stats, "pass_vs_control")
    assert inverse["comparison_classification"] == "INVERSE_PASS_LT_CONTROL"


def test_branch_dimensions_include_descriptor_and_interaction_families():
    families = {family for family, _ in builder.branch_dimensions(synthetic_row())}
    assert "card_descriptor_value_target_family_horizon" in families
    assert "card_descriptor_pair_interaction_target_family_horizon" in families
    assert "card_source_segment_target_family_horizon" in families
    assert "card_session_target_family_horizon" in families
