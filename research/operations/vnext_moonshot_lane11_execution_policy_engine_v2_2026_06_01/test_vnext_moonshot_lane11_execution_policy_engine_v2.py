from __future__ import annotations

from build_vnext_moonshot_lane11_execution_policy_engine_v2 import (
    BASELINE_POLICY_VARIANTS,
    BE_TIMINGS,
    PARTIAL_CLOSE_RATIOS,
    PARTIAL_TRIGGER_R,
    RUNNER_TARGETS_R,
    TIME_STOP_MODES,
    build_expanded_policy_variant_registry,
    expanded_variant_bucket_status,
    simulate_expanded_partial_proxy,
    lifecycle_requirements_for_policy,
    metric_add,
    metric_close,
    metric_new,
    modify_feasibility_for_policy,
    resolve_policy_variant,
    result_for_policy,
    validate_router_package_no_leak,
)


def test_partial_runner_requires_ticket_bound_partial_and_residual_lifecycle():
    requirements = lifecycle_requirements_for_policy("partial_be_runner")

    assert requirements["requires_partial_close_ticket_binding"] is True
    assert requirements["requires_residual_ticket_binding"] is True
    assert requirements["requires_be_modify"] is True


def test_rejected_modify_blocks_modify_dependent_policy():
    result = modify_feasibility_for_policy(
        "trailing_runner",
        {"trade_stops_level": 0, "trade_freeze_level": 0},
        {"risk_price_distance": 10.0},
        {"stop_modify_rejections": 10016},
    )

    assert result["modify_feasible_proxy"] is False
    assert result["modify_feasibility_status"] == "observed_modify_rejection"


def test_non_modify_policy_is_feasible_without_modify_loop():
    result = modify_feasibility_for_policy(
        "time_stop",
        {"trade_stops_level": 10, "trade_freeze_level": 5},
        None,
        None,
    )

    assert result["requires_order_modify"] is False
    assert result["modify_feasible_proxy"] is True


def test_hybrid_strict_trailing_uses_trailing_only_when_strict_and_modify_feasible():
    row = {
        "origin_family": "liquidity_sweep_reclaim",
        "decision_inputs": {"meta_selector": {"chosen_policy": "partial_be_runner"}},
    }

    assert (
        resolve_policy_variant(
            "hybrid_strict_trailing_challenger_else_current_router",
            row,
            True,
            True,
        )
        == "trailing_runner"
    )
    assert (
        resolve_policy_variant(
            "hybrid_strict_trailing_challenger_else_current_router",
            row,
            False,
            True,
        )
        == "partial_be_runner"
    )


def test_result_prefers_strict_tick_over_proxy_for_same_policy():
    result = result_for_policy(
        variant="momentum_exhaustion",
        resolved_policy="momentum_exhaustion",
        row={"result_payload": {"label_values": {}}},
        lane02_row={"r_by_policy": {"momentum_exhaustion": 2.0}},
        strict_tick_row={
            "r_by_policy": {"momentum_exhaustion": 1.5},
            "exit_reason_by_policy": {"momentum_exhaustion": "strict_exit"},
            "exit_time_by_policy": {"momentum_exhaustion": "2026-01-01T00:00:00+00:00"},
        },
        friday_rows=None,
    )

    assert result["gross_r"] == 1.5
    assert result["evidence_class"] == "strict_tick_bid_ask_policy_replay"


def test_no_leak_validator_rejects_future_label_fields_in_package_rule():
    issues = validate_router_package_no_leak(
        [{"rule": {"source_bound_proxy_r": 1.0, "policy_variant": "momentum_exhaustion"}}]
    )

    assert issues


def test_metric_tracks_cost_stress_drawdown_and_loss_streak():
    metric = metric_new()
    for value in (1.0, -1.0, -1.0, 2.0, 0.0):
        metric_add(
            metric,
            gross_r=value,
            cost_median_r=0.1,
            cost_p90_r=0.2,
            cost_high_r=0.5,
            duration_seconds=60.0,
            mfe_r=1.5,
            mae_r=-0.5,
            evidence_class="m15_proxy_policy_replay",
        )
    closed = metric_close(metric)

    assert closed["known_r_rows"] == 5
    assert closed["gross_total_r"] == 1.0
    assert closed["net_median_total_r"] == 0.5
    assert closed["max_drawdown_r"] == 2.0
    assert closed["max_loss_streak"] == 2


def test_expanded_policy_registry_is_not_baseline_only_and_covers_required_domains():
    registry = build_expanded_policy_variant_registry()
    variant_ids = {row["variant_id"] for row in registry}
    families = {row["family"] for row in registry}

    assert len(registry) > len(BASELINE_POLICY_VARIANTS)
    assert set(BASELINE_POLICY_VARIANTS).issubset(variant_ids)
    assert "partial_be_runner_parameter_sweep" in families
    assert "trailing_runner_parameter_sweep" in families
    assert "time_stop_parameter_sweep" in families
    assert "hybrid_policy_router" in families

    partial_rows = [row for row in registry if row["family"] == "partial_be_runner_parameter_sweep"]
    observed_ratios = {row["parameters"]["partial_close_ratio"] for row in partial_rows}
    observed_triggers = {row["parameters"]["partial_trigger_r"] for row in partial_rows}
    observed_be_timings = {row["parameters"]["be_timing"] for row in partial_rows}
    observed_targets = {row["parameters"]["runner_target_r"] for row in partial_rows}

    assert observed_ratios == set(PARTIAL_CLOSE_RATIOS)
    assert observed_triggers == set(PARTIAL_TRIGGER_R)
    assert observed_be_timings == set(BE_TIMINGS)
    assert observed_targets == set(RUNNER_TARGETS_R)
    assert {row["parameters"]["time_stop_mode"] for row in registry if row["family"] == "time_stop_parameter_sweep"} == set(TIME_STOP_MODES)


def test_expanded_variant_bucket_feasibility_is_not_global_gap_only():
    registry = build_expanded_policy_variant_registry()
    partial_variant = next(
        row
        for row in registry
        if row["family"] == "partial_be_runner_parameter_sweep"
        and row["parameters"]["partial_trigger_r"] == 1.0
        and row["parameters"]["be_timing"] == "be_after_partial"
        and row["parameters"]["runner_target_r"] == 2.0
    )

    assert expanded_variant_bucket_status(partial_variant, "m15_proxy")[0] == "expanded_replay_feasible"
    assert expanded_variant_bucket_status(partial_variant, "strict_tick_subset")[0] == "not_replayable_source_gap"


def test_expanded_partial_proxy_simulates_nonbaseline_result_from_m15_fields():
    row = {
        "result_payload": {
            "label_values": {
                "mfe_r": 2.5,
                "mae_r": -0.2,
                "source_bound_proxy_r": 1.4,
                "one_r_reached": True,
                "sl_before_1r": False,
            }
        }
    }
    params = {
        "partial_close_ratio": 0.5,
        "partial_trigger_r": 1.0,
        "be_timing": "be_after_partial",
        "runner_target_r": 2.0,
    }

    gross_r, gap = simulate_expanded_partial_proxy(row, params)

    assert gap is None
    assert gross_r == 1.5
