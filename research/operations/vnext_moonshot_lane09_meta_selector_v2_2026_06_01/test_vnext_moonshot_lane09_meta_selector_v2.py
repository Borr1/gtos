from __future__ import annotations

from build_vnext_moonshot_lane09_meta_selector_v2 import (
    DIMENSION_TEMPLATES,
    EXPECTED_DEPTH_ROWS,
    EXPECTED_REPLAY_GAP_ROWS,
    EXPECTED_REPLAY_ROWS,
    EXPECTED_SPLIT_STRESS_ROWS,
    FORBIDDEN_RUNTIME_CLAUSE_DIMENSIONS,
    classify_group,
    subtract_metrics,
    validate_clause_no_leak,
)


def test_lane08_contract_counts_are_terminal_inputs():
    assert EXPECTED_REPLAY_ROWS == 289_928
    assert EXPECTED_REPLAY_GAP_ROWS == 3_471_773
    assert EXPECTED_SPLIT_STRESS_ROWS == 1_536
    assert EXPECTED_DEPTH_ROWS == 9


def test_interaction_templates_cover_prompt_selector_space_without_friday_only_rule():
    flattened = {field for template in DIMENSION_TEMPLATES for field in template}

    for field in {
        "symbol",
        "session_bucket",
        "origin_family",
        "framework",
        "side",
        "regime_h4_state",
        "spread_r_bucket",
        "source_quality_status",
        "m15_volatility_state_14_vs_50",
        "correlation_cluster_join_state",
        "cost_status",
        "path_class",
    }:
        assert field in flattened
    assert "time_is_friday" not in flattened


def test_forensic_dimensions_are_not_runtime_clause_legal():
    clause = {
        "dimensions": ["origin_family", "path_class"],
        "dimension_values": {
            "origin_family": "current_ob_retest",
            "path_class": "loss_sl_or_stop_policy_exit",
        },
    }

    issues = validate_clause_no_leak(clause)

    assert issues == ["path_class"]
    assert "path_class" in FORBIDDEN_RUNTIME_CLAUSE_DIMENSIONS


def test_decision_classifier_promotes_strong_runtime_group():
    action, reason = classify_group(
        {
            "rows": 500,
            "known_r_rows": 500,
            "expectancy_r": 0.7,
            "cost_stress_expectancy_after_0_25r": 0.45,
            "cost_stress_expectancy_after_0_50r": 0.2,
            "profit_factor": 2.5,
            "win_rate": 0.55,
            "top_calendar_day_share": 0.05,
            "sealed_partition_count": 4,
        },
        ("origin_family", "session_bucket"),
        True,
    )

    assert action == "promote"
    assert "positive_expectancy" in reason


def test_decision_classifier_blocks_forensic_runtime_use():
    action, reason = classify_group(
        {
            "rows": 500,
            "known_r_rows": 500,
            "expectancy_r": -1.0,
            "cost_stress_expectancy_after_0_25r": -1.25,
            "profit_factor": 0.0,
            "win_rate": 0.0,
            "top_calendar_day_share": 0.01,
            "sealed_partition_count": 4,
        },
        ("origin_family", "path_class"),
        False,
    )

    assert action == "capture_repair_forensic_only"
    assert "not_legal_runtime_selector_feature" in reason


def test_leave_one_out_stress_subtracts_additive_metrics():
    metrics = subtract_metrics(
        {
            "rows": 10,
            "known_r_rows": 10,
            "wins": 6,
            "losses": 4,
            "breakevens": 0,
            "total_r": 8.0,
            "gross_profit_r": 12.0,
            "gross_loss_r": -4.0,
        },
        {
            "rows": 2,
            "known_r_rows": 2,
            "wins": 1,
            "losses": 1,
            "breakevens": 0,
            "total_r": 1.0,
            "gross_profit_r": 2.0,
            "gross_loss_r": -1.0,
        },
    )

    assert metrics["rows"] == 8
    assert metrics["known_r_rows"] == 8
    assert metrics["expectancy_r"] == 0.875
    assert metrics["profit_factor"] == 3.333333
    assert metrics["drawdown_note"].startswith("leave_one_out")
