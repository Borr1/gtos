from src.research.moonshot_default_off_policy_router import (
    CONDITION_CHALLENGER_MODE,
    DEFAULT_POLICY,
    EXECUTION_POLICY_IDS,
    REJECTED_LIVE_BASELINE,
    route_moonshot_dynamic_execution,
    select_asof_displacement_policy,
)


def _event(**overrides):
    event = {
        "symbol": "XAUUSD",
        "side": "LONG",
        "framework": "fvg_fill",
        "candidate_origin_family": "origin_current_fvg_fill",
        "branch_label": "FOLLOW",
        "activated_frameworks": ["breaker_re_entry", "fvg_fill", "ob_retest"],
        "required_branch_labels": ["FOLLOW"],
        "broker_native_eligible_symbols": ["XAUUSD", "GBPJPY", "UK100"],
        "broker_native_exact_excluded_symbols": ["GER40"],
        "broker_native_eligible": True,
        "broker_native_exact_excluded": False,
        "session_bucket": "london_broad",
        "kill_zone_position": "in_london_early",
        "require_configured_kill_zone": True,
        "source_mode": "OHLC_M15_CSV",
        "source_path_feature_status": "computed_from_source_ohlc_asof",
        "source_window_complete": "True",
        "ordered_path_status": "ordered_path_not_ambiguous_in_m15_replay",
        "liquidity_sweep_proxy_state": "no_prior_20_sweep",
        "volatility_state_14_vs_50": "normal_recent_vs_baseline",
        "trend_state_20": "up",
        "current_bar_displacement_atr14": 0.5,
        "remaining_daily_cushion_r": 6.0,
        "remaining_overall_cushion_r": 8.0,
    }
    event.update(overrides)
    return event


def test_disabled_router_has_no_runtime_effect_and_no_policy_selection() -> None:
    decision = route_moonshot_dynamic_execution(_event())

    assert decision.decision_status == "disabled_vnext"
    assert decision.selected_policy is None
    assert decision.runtime_effect_now is False
    assert decision.candidate_use_allowed_now is False
    assert decision.broker_operation is False
    assert decision.paid_api_or_vendor_call is False


def test_activated_route_replaces_live_current_with_momentum_primary_default_off() -> None:
    decision = route_moonshot_dynamic_execution(_event(), enabled=True)

    assert decision.decision_status == "vnext_candidate_ready"
    assert decision.candidate_action == "TRADE_VNEXT_ACTIVATED_CANDIDATE"
    assert decision.selected_policy == DEFAULT_POLICY
    assert decision.execution_policy_id == EXECUTION_POLICY_IDS[DEFAULT_POLICY]
    assert decision.replaced_policy == REJECTED_LIVE_BASELINE
    assert decision.fixed_target_role == "baseline_comparator_only"
    assert decision.runtime_effect_now is False
    assert decision.candidate_use_allowed_now is False


def test_owner_activation_flags_are_required_even_for_ready_primary_route() -> None:
    active = route_moonshot_dynamic_execution(
        _event(),
        enabled=True,
        apply_to_execution=True,
    )

    assert active.candidate_use_allowed_now is True
    assert active.runtime_effect_now is True


def test_incomplete_source_window_is_capture_quality_not_selection_rule() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(source_window_complete="False"),
        enabled=True,
        apply_to_execution=True,
    )

    assert decision.decision_status == "vnext_candidate_ready"
    assert decision.selected_policy == DEFAULT_POLICY
    assert decision.source_quality_action == (
        "SOURCE_REPLAY_OK_WITH_FORWARD_CAPTURE_MONITORING_REQUIRED"
    )
    assert "source_window_incomplete_forward_capture_required" not in decision.refusal_reasons
    assert decision.candidate_use_allowed_now is True


def test_same_bar_ambiguity_refuses_live_use_until_ordered_path_source_exists() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(ordered_path_status="same_bar_ambiguous_requires_ltf_or_tick_ordering"),
        enabled=True,
        apply_to_execution=True,
    )

    assert decision.decision_status == "refuse_live_use_until_source_or_scope_repaired"
    assert decision.candidate_action == "ACTIVATED_CANDIDATE_HELD_FOR_SOURCE_OR_BRANCH_REPAIR"
    assert "selected_policy_ordered_ltf_or_tick_path_required" in decision.refusal_reasons
    assert decision.candidate_use_allowed_now is False


def test_non_selected_policy_same_bar_ambiguity_does_not_block_momentum_primary() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(
            ordered_path_status="same_bar_ambiguous_requires_ltf_or_tick_ordering",
            selected_policy_ordered_path_status="ordered_path_not_ambiguous_in_m15_replay",
            selected_policy_same_bar_ambiguous=False,
        ),
        enabled=True,
        apply_to_execution=True,
    )

    assert decision.decision_status == "vnext_candidate_ready"
    assert decision.selected_policy == DEFAULT_POLICY
    assert decision.candidate_use_allowed_now is True
    assert "selected_policy_ordered_ltf_or_tick_path_required" not in decision.refusal_reasons
    assert any("non_selected_policy_same_bar" in note for note in decision.evidence_notes)


def test_off_configured_kill_zone_refuses_live_use_even_when_source_complete() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(kill_zone_position="off_configured_kill_zone_or_unconfigured_symbol"),
        enabled=True,
        apply_to_execution=True,
    )

    assert decision.decision_status == "refuse_live_use_until_source_or_scope_repaired"
    assert decision.candidate_action == "ACTIVATED_CANDIDATE_HELD_FOR_SOURCE_OR_BRANCH_REPAIR"
    assert "outside_configured_kill_zone_or_missing_schedule" in decision.refusal_reasons
    assert decision.candidate_use_allowed_now is False


def test_fvg_ny_sweep_uses_promoted_momentum_primary_not_trailing_or_be() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(session_bucket="ny_broad", liquidity_sweep_proxy_state="swept_prior_20_low"),
        enabled=True,
    )

    assert decision.selected_policy == DEFAULT_POLICY
    assert decision.selected_policy == "momentum_exhaustion"
    assert decision.exit_management_action == (
        "REPLACE_RETIRED_STATIC_BASELINE_WITH_MOMENTUM_EXHAUSTION_PRIMARY"
    )
    assert not any("trailing_runner_outperforms" in note for note in decision.evidence_notes)


def test_condition_challenger_keeps_fvg_high_displacement_on_momentum_primary() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(
            policy_router_mode=CONDITION_CHALLENGER_MODE,
            condition_challenger_enabled=True,
            session_bucket="ny_broad",
            current_bar_displacement_atr14=1.25,
        ),
        enabled=True,
    )

    assert decision.selected_policy == "momentum_exhaustion"
    assert decision.execution_policy_id == EXECUTION_POLICY_IDS["momentum_exhaustion"]
    assert decision.route_dimensions["retired_stage11_condition_policy"] == "trailing_runner"
    assert decision.exit_management_action == (
        "ROUTE_EXIT_POLICY_BY_PROMOTED_MOMENTUM_PRIMARY_EXCEPTION_LAYER"
    )
    assert "promoted_momentum_primary_exception_router_selected_live_policy" in decision.evidence_notes
    assert decision.runtime_effect_now is False


def test_condition_challenger_selects_momentum_for_swept_high_displacement() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(
            policy_router_mode=CONDITION_CHALLENGER_MODE,
            condition_challenger_enabled=True,
            session_bucket="ny_broad",
            liquidity_sweep_proxy_state="swept_prior_20_low",
            current_bar_displacement_atr14=1.25,
        ),
        enabled=True,
        apply_to_execution=True,
    )

    assert decision.selected_policy == "momentum_exhaustion"
    assert decision.execution_policy_id == EXECUTION_POLICY_IDS["momentum_exhaustion"]
    assert decision.candidate_use_allowed_now is True


def test_router_ignores_future_outcome_labels_for_live_policy_selection() -> None:
    clean = route_moonshot_dynamic_execution(
        _event(
            policy_router_mode=CONDITION_CHALLENGER_MODE,
            condition_challenger_enabled=True,
            session_bucket="ny_broad",
            current_bar_displacement_atr14=1.25,
        ),
        enabled=True,
        apply_to_execution=True,
    )
    contaminated = route_moonshot_dynamic_execution(
        _event(
            policy_router_mode=CONDITION_CHALLENGER_MODE,
            condition_challenger_enabled=True,
            session_bucket="ny_broad",
            current_bar_displacement_atr14=1.25,
            hindsight_best_policy="be_after_trigger",
            comparison_momentum_exhaustion_r=-1.0,
            comparison_be_after_trigger_r=9.0,
            final_r=9.0,
        ),
        enabled=True,
        apply_to_execution=True,
    )

    assert contaminated.selected_policy == clean.selected_policy == "momentum_exhaustion"
    assert contaminated.execution_policy_id == clean.execution_policy_id
    assert "future_outcome_fields_present_but_ignored_by_live_router" in (
        contaminated.evidence_notes
    )
    assert "comparison_be_after_trigger_r" in (
        contaminated.route_dimensions["future_outcome_fields_ignored"]
    )


def test_condition_challenger_never_selects_fixed_15r_as_live_default() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(
            framework="ob_retest",
            candidate_origin_family="origin_current_ob_retest",
            policy_router_mode=CONDITION_CHALLENGER_MODE,
            condition_challenger_enabled=True,
            session_bucket="ny_broad",
            current_bar_displacement_atr14=0.25,
        ),
        enabled=True,
        apply_to_execution=True,
    )

    assert decision.selected_policy == DEFAULT_POLICY
    assert decision.execution_policy_id == EXECUTION_POLICY_IDS[DEFAULT_POLICY]
    assert decision.selected_policy == "momentum_exhaustion"
    assert decision.candidate_use_allowed_now is True


def test_condition_challenger_payload_is_ignored_unless_enabled() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(
            policy_router_mode=CONDITION_CHALLENGER_MODE,
            condition_challenger_enabled=False,
            session_bucket="ny_broad",
            current_bar_displacement_atr14=1.25,
        ),
        enabled=True,
        apply_to_execution=True,
    )

    assert decision.selected_policy == DEFAULT_POLICY
    assert decision.exit_management_action == (
        "REPLACE_RETIRED_STATIC_BASELINE_WITH_MOMENTUM_EXHAUSTION_PRIMARY"
    )
    assert "promoted_momentum_primary_exception_router_selected_live_policy" not in (
        decision.evidence_notes
    )
    assert decision.candidate_use_allowed_now is True


def test_condition_challenger_falls_back_to_momentum_primary_when_no_exception() -> None:
    policy, bucket = select_asof_displacement_policy(
        _event(
            framework="breaker_re_entry",
            session_bucket="tokyo_broad",
            current_bar_displacement_atr14=1.4,
        )
    )

    assert bucket == "high_disp"
    assert policy == DEFAULT_POLICY


def test_empty_partial_exception_list_disables_partial_be_runner() -> None:
    policy, bucket = select_asof_displacement_policy(
        _event(
            framework="liquidity_sweep_reclaim",
            candidate_origin_family="origin_liquidity_sweep_reclaim",
            session_bucket="london_broad",
            current_bar_displacement_atr14=1.4,
            partial_exception_origin_families=[],
        )
    )

    assert bucket == "high_disp"
    assert policy == DEFAULT_POLICY


def test_non_fvg_framework_is_activated_when_stage13_selector_includes_it() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(framework="ob_retest", candidate_origin_family="origin_current_ob_retest"),
        enabled=True,
        apply_to_execution=True,
    )

    assert decision.candidate_action == "TRADE_VNEXT_ACTIVATED_CANDIDATE"
    assert decision.selected_policy == DEFAULT_POLICY
    assert decision.candidate_use_allowed_now is True
    assert any("non_fvg_framework_promoted" in note for note in decision.evidence_notes)


def test_non_follow_branch_requires_stage13_repaired_allowlist() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(branch_label="AVOID"),
        enabled=True,
        apply_to_execution=True,
    )

    assert decision.decision_status == "refuse_live_use_until_source_or_scope_repaired"
    assert "branch_semantics_not_follow_or_repaired" in decision.refusal_reasons
    assert decision.candidate_use_allowed_now is False


def test_repaired_branch_allowlist_promotes_prior_non_follow_label() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(branch_label="AVOID", repaired_branch_allowed=True),
        enabled=True,
        apply_to_execution=True,
    )

    assert decision.decision_status == "vnext_candidate_ready"
    assert decision.candidate_action == "TRADE_VNEXT_REPAIRED_BRANCH_CANDIDATE"
    assert decision.selected_branch == "moonshot_repaired_origin_current_fvg_fill"
    assert decision.candidate_use_allowed_now is True


def test_broader_origin_allowlist_promotes_non_old_three_origin_family() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(
            framework="liquidity_sweep_reclaim",
            candidate_origin_family="origin_liquidity_sweep_reclaim",
            branch_label="LEGACY",
            activated_origin_families=["liquidity_sweep_reclaim"],
            broader_origin_allowed=True,
            live_generation_status="generated_live_asof",
            policy_router_mode=CONDITION_CHALLENGER_MODE,
            condition_challenger_enabled=True,
        ),
        enabled=True,
        apply_to_execution=True,
    )

    assert decision.decision_status == "vnext_candidate_ready"
    assert decision.candidate_action == "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE"
    assert decision.selected_branch == "origin_liquidity_sweep_reclaim"
    assert decision.selected_policy == "partial_be_runner"
    assert decision.execution_policy_id == EXECUTION_POLICY_IDS["partial_be_runner"]
    assert decision.candidate_use_allowed_now is True


def test_live_raw_data_asof_status_is_valid_source_proof_for_broader_origin() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(
            framework="liquidity_sweep_reclaim",
            candidate_origin_family="origin_liquidity_sweep_reclaim",
            branch_label="FOLLOW",
            activated_origin_families=["liquidity_sweep_reclaim"],
            broader_origin_allowed=True,
            source_mode="LIVE_RAW_M15",
            source_path_feature_status="raw_data_m15_asof_complete",
            live_generation_status="generated_live_asof",
        ),
        enabled=True,
        apply_to_execution=True,
    )

    assert "source_path_not_asof_computed" not in decision.refusal_reasons
    assert decision.candidate_use_allowed_now is True


def test_candidate_quality_selector_matches_broad_session_alias() -> None:
    rule = {
        "rule_id": "test_lane03_london_liquidity_tradeable",
        "action": "tradeable_now",
        "session": "london_broad",
        "origin_family": "liquidity_sweep_reclaim",
    }
    decision = route_moonshot_dynamic_execution(
        _event(
            framework="liquidity_sweep_reclaim",
            candidate_origin_family="origin_liquidity_sweep_reclaim",
            branch_label="FOLLOW",
            activated_origin_families=["liquidity_sweep_reclaim"],
            broader_origin_allowed=True,
            source_mode="LIVE_RAW_M15",
            source_path_feature_status="raw_data_m15_asof_complete",
            live_generation_status="generated_live_asof",
            session_bucket="london",
            spread_r_at_candidate=0.04,
            candidate_quality_selector_enabled=True,
            candidate_quality_selector_apply_to_execution=True,
            candidate_quality_selector_tradeable_rules=[rule],
        ),
        enabled=True,
        apply_to_execution=True,
    )

    selector = decision.route_dimensions["candidate_quality_selector"]
    assert selector["classification"] == "tradeable_now"
    assert selector["session"] == "london_broad"
    assert selector["matched_rule"]["rule_id"] == "test_lane03_london_liquidity_tradeable"
    assert decision.candidate_use_allowed_now is True
    assert not any("weekend" in reason for reason in decision.refusal_reasons)


def test_candidate_quality_selector_maps_moonshot_hourly_session_to_off_kz_broad() -> None:
    rule = {
        "rule_id": "test_lane03_off_kz_liquidity_tradeable",
        "action": "tradeable_now",
        "session": "off_kz_broad",
        "origin_family": "liquidity_sweep_reclaim",
    }
    decision = route_moonshot_dynamic_execution(
        _event(
            framework="liquidity_sweep_reclaim",
            candidate_origin_family="origin_liquidity_sweep_reclaim",
            branch_label="FOLLOW",
            activated_origin_families=["liquidity_sweep_reclaim"],
            broader_origin_allowed=True,
            source_mode="LIVE_RAW_M15",
            source_path_feature_status="raw_data_m15_asof_complete",
            live_generation_status="generated_live_asof",
            session_bucket="moonshot_h11_12",
            route_session="moonshot_h11_12",
            kill_zone_position="in_moonshot_h11_12_repo_schedule_repaired",
            spread_r_at_candidate=0.04,
            candidate_quality_selector_enabled=True,
            candidate_quality_selector_apply_to_execution=True,
            candidate_quality_selector_tradeable_rules=[rule],
        ),
        enabled=True,
        apply_to_execution=True,
    )

    selector = decision.route_dimensions["candidate_quality_selector"]
    assert selector["classification"] == "tradeable_now"
    assert selector["session"] == "off_kz_broad"
    assert selector["matched_rule"]["rule_id"] == "test_lane03_off_kz_liquidity_tradeable"
    assert "candidate_quality_session_origin_not_in_selected_denominator_package" not in (
        decision.refusal_reasons
    )
    assert decision.candidate_use_allowed_now is True


def test_candidate_quality_selector_avoid_rule_overrides_tradeable_rule() -> None:
    broad_rule = {
        "rule_id": "test_lane03_london_ob_tradeable",
        "action": "tradeable_now",
        "session": "london_broad",
        "origin_family": "current_ob_retest",
        "framework": "ob_retest",
    }
    avoid_rule = {
        "rule_id": "test_lane03_usdjpy_ob_avoid",
        "action": "no_trade_by_evidence",
        "refusal_reason": "candidate_quality_negative_selected_denominator_rule",
        "symbol": "USDJPY",
        "side": "LONG",
        "session": "london_broad",
        "origin_family": "current_ob_retest",
        "framework": "ob_retest",
    }
    decision = route_moonshot_dynamic_execution(
        _event(
            symbol="USDJPY",
            side="LONG",
            framework="ob_retest",
            candidate_origin_family="origin_current_ob_retest",
            broker_native_eligible_symbols=["USDJPY"],
            session_bucket="london_broad",
            spread_r_at_candidate=0.03,
            candidate_quality_selector_enabled=True,
            candidate_quality_selector_apply_to_execution=True,
            candidate_quality_selector_tradeable_rules=[broad_rule, avoid_rule],
        ),
        enabled=True,
        apply_to_execution=True,
    )

    selector = decision.route_dimensions["candidate_quality_selector"]
    assert selector["classification"] == "no_trade_by_evidence"
    assert selector["matched_rule"]["rule_id"] == "test_lane03_usdjpy_ob_avoid"
    assert "candidate_quality_negative_selected_denominator_rule" in decision.refusal_reasons
    assert decision.candidate_use_allowed_now is False


def test_candidate_quality_selector_reduce_rule_stays_tradeable_with_risk_multiplier() -> None:
    reduce_rule = {
        "rule_id": "test_lane03_usdjpy_ob_reduce",
        "action": "reduce_risk_by_evidence",
        "risk_multiplier": 0.5,
        "symbol": "USDJPY",
        "side": "LONG",
        "session": "london_broad",
        "origin_family": "current_ob_retest",
        "framework": "ob_retest",
    }
    decision = route_moonshot_dynamic_execution(
        _event(
            symbol="USDJPY",
            side="LONG",
            framework="ob_retest",
            candidate_origin_family="origin_current_ob_retest",
            broker_native_eligible_symbols=["USDJPY"],
            session_bucket="london_broad",
            spread_r_at_candidate=0.03,
            candidate_quality_selector_enabled=True,
            candidate_quality_selector_apply_to_execution=True,
            candidate_quality_selector_tradeable_rules=[reduce_rule],
        ),
        enabled=True,
        apply_to_execution=True,
    )

    selector = decision.route_dimensions["candidate_quality_selector"]
    assert selector["classification"] == "reduce_risk_by_evidence"
    assert selector["matched_rule"]["rule_id"] == "test_lane03_usdjpy_ob_reduce"
    assert selector["risk_multiplier"] == 0.5
    assert decision.candidate_use_allowed_now is True


def test_candidate_quality_selector_missing_spread_requires_source_capture() -> None:
    rule = {
        "rule_id": "test_lane03_current_fvg_tradeable",
        "action": "tradeable_now",
        "session": "london_broad",
        "origin_family": "current_fvg_fill",
        "framework": "fvg_fill",
    }
    decision = route_moonshot_dynamic_execution(
        _event(
            session_bucket="london_broad",
            candidate_quality_selector_enabled=True,
            candidate_quality_selector_apply_to_execution=True,
            candidate_quality_selector_tradeable_rules=[rule],
        ),
        enabled=True,
        apply_to_execution=True,
    )

    selector = decision.route_dimensions["candidate_quality_selector"]
    assert selector["classification"] == "source_capture_required"
    assert "candidate_quality_spread_r_missing_for_selected_denominator_rule" in (
        decision.refusal_reasons
    )
    assert decision.candidate_use_allowed_now is False


def test_prop_governor_block_prevents_dynamic_router_runtime_effect() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(prop_governor_action="BLOCK"),
        enabled=True,
        apply_to_execution=True,
    )

    assert decision.prop_action == "OWNER_GATED_ACCOUNT_ABANDON_OR_RESTART"
    assert decision.candidate_use_allowed_now is False


def test_broker_native_exact_exclusion_refuses_activation() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(symbol="GER40", broker_native_eligible=False, broker_native_exact_excluded=True),
        enabled=True,
        apply_to_execution=True,
    )

    assert "broker_contract_invalid_or_unavailable" in decision.refusal_reasons
    assert decision.candidate_use_allowed_now is False


def test_symbol_outside_broker_native_activation_map_refuses_activation() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(symbol="USOIL_cash", broker_native_eligible_symbols=["XAUUSD"]),
        enabled=True,
        apply_to_execution=True,
    )

    assert "symbol_not_in_broker_native_activation_map" in decision.refusal_reasons
    assert decision.candidate_use_allowed_now is False


def test_broker_symbol_alias_normalization_accepts_dot_alias_for_cash_symbol() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(
            symbol="US30.cash",
            framework="ob_retest",
            candidate_origin_family="origin_current_ob_retest",
            broker_native_eligible_symbols=["US30_cash"],
        ),
        enabled=True,
        apply_to_execution=True,
    )

    assert "symbol_not_in_broker_native_activation_map" not in decision.refusal_reasons
    assert decision.candidate_use_allowed_now is True


def test_framework_outside_stage13_activated_set_refuses_activation() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(framework="liquidity_sweep_reclaim", activated_frameworks=["fvg_fill"]),
        enabled=True,
        apply_to_execution=True,
    )

    assert "framework_not_activated_in_stage13_full_moonshot_selector" in decision.refusal_reasons
    assert decision.candidate_use_allowed_now is False


def test_prop_boundary_returns_owner_gated_or_risk_reducing_action_without_broker_effect() -> None:
    reduce = route_moonshot_dynamic_execution(
        _event(remaining_daily_cushion_r=1.0),
        enabled=True,
        apply_to_execution=True,
    )
    abandon = route_moonshot_dynamic_execution(
        _event(remaining_overall_cushion_r=0.0),
        enabled=True,
        apply_to_execution=True,
    )

    assert reduce.prop_action == "REDUCE_RISK_OR_DEFER_UNTIL_RESET"
    assert abandon.prop_action == "OWNER_GATED_ACCOUNT_ABANDON_OR_RESTART"
    assert reduce.candidate_use_allowed_now is False
    assert abandon.candidate_use_allowed_now is False
    assert reduce.broker_operation is False
    assert abandon.broker_operation is False
