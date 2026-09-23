"""Focused tests for the ruin-aware risk governor V4 (pure budget/breaker math)."""

from __future__ import annotations

from src.components.risk_governor_v4 import (
    ACTION_ALLOW,
    ACTION_FLATTEN_HALT,
    ACTION_FLOOR_REVIEW,
    ACTION_REDUCE,
    ACTION_REFUSE,
    ACTIONS,
    BOUNDARY,
    FORBIDDEN_STATE_FIELDS,
    GovernorConfigV4,
    GovernorDecisionV4,
    evaluate_risk_governor_v4,
    governor_config_packet,
    pair_abs_correlation,
)

BINDING = GovernorConfigV4(enabled=True, apply_to_execution=True)


def _state(**overrides) -> dict:
    state = {
        "realized_day_pnl_pct": 0.0,
        "open_positions": [],
        "cluster_correlation": {},
        "requested_risk_pct": 1.0,
        "remaining_opportunity_weight": 0.0,
        "intraday_conservative_dd_pct": 0.0,
        "overall_dd_pct": 0.0,
    }
    state.update(overrides)
    return state


# ---------------------------------------------------------------------------
# Config defaults / from_runtime_config
# ---------------------------------------------------------------------------


def test_config_defaults_are_off_and_safe():
    cfg = GovernorConfigV4()
    assert cfg.enabled is False
    assert cfg.apply_to_execution is False
    assert cfg.daily_limit_pct == 5.0
    assert cfg.hard_reserve_pct == 0.5
    assert cfg.profit_recycle_fraction == 0.5
    assert cfg.corr_heat_cap == 1.5
    assert cfg.pacing_alpha == 1.0
    assert cfg.min_slice_pct == 0.25
    assert cfg.max_slice_pct == 2.0
    assert cfg.breaker_dd_pct == 4.2
    assert cfg.overall_dd_floor_pct == 8.0


def test_from_runtime_config_reads_keys_and_falls_back_to_defaults():
    cfg = GovernorConfigV4.from_runtime_config(
        {
            "gtos_vnext_runtime": {
                "risk_governor_v4_enabled": True,
                "risk_governor_v4_daily_limit_pct": "4.0",
                "risk_governor_v4_profit_recycle_fraction": 0.25,
                "risk_governor_v4_pacing_alpha": "not_a_number",
            }
        }
    )
    assert cfg.enabled is True
    assert cfg.apply_to_execution is False  # never implied by enabled
    assert cfg.daily_limit_pct == 4.0
    assert cfg.profit_recycle_fraction == 0.25
    assert cfg.pacing_alpha == 1.0  # unparseable -> default
    assert cfg.breaker_dd_pct == 4.2  # absent -> default


def test_from_runtime_config_handles_missing_or_none_config():
    assert GovernorConfigV4.from_runtime_config(None) == GovernorConfigV4()
    assert GovernorConfigV4.from_runtime_config({}) == GovernorConfigV4()


# ---------------------------------------------------------------------------
# Budget arithmetic
# ---------------------------------------------------------------------------


def test_base_budget_arithmetic_allows_within_budget():
    decision = evaluate_risk_governor_v4(BINDING, _state())
    assert decision.action == ACTION_ALLOW
    assert decision.approved_risk_pct == 1.0
    assert decision.budget_base_pct == 4.5  # daily_limit - reserve
    assert decision.budget_total_pct == 4.5
    assert decision.pacing_fraction == 1.0  # weight 0 -> no pacing drag
    assert decision.applied is True


def test_profit_recycle_expands_budget_by_kappa():
    decision = evaluate_risk_governor_v4(BINDING, _state(realized_day_pnl_pct=2.0))
    assert decision.profit_recycle_pct == 1.0  # kappa 0.5 * 2.0
    assert decision.loss_drag_pct == 0.0
    assert decision.budget_total_pct == 5.5


def test_losses_shrink_budget_one_to_one():
    decision = evaluate_risk_governor_v4(BINDING, _state(realized_day_pnl_pct=-2.0))
    assert decision.profit_recycle_pct == 0.0
    assert decision.loss_drag_pct == -2.0
    assert decision.budget_total_pct == 2.5


def test_open_heat_uses_pairwise_correlation():
    decision = evaluate_risk_governor_v4(
        BINDING,
        _state(
            open_positions=[
                {"risk_pct": 1.0, "cluster": "fx", "be_reached": False},
                {"risk_pct": 1.0, "cluster": "jpy_fx", "be_reached": False},
            ],
            cluster_correlation={("fx", "jpy_fx"): 0.2},
        ),
    )
    # rho = 1 + min(0.5, |0.2|) = 1.2 for each leg -> heat 2.4
    assert decision.open_heat_pct == 2.4
    assert decision.budget_total_pct == 2.1


def test_missing_correlation_fails_closed_to_full_heat():
    decision = evaluate_risk_governor_v4(
        BINDING,
        _state(
            open_positions=[
                {"risk_pct": 1.0, "cluster": "fx", "be_reached": False},
                {"risk_pct": 1.0, "cluster": "jpy_fx", "be_reached": False},
            ],
            cluster_correlation={},  # unknown pair -> |corr| = 1.0
        ),
    )
    # rho capped at corr_heat_cap = 1.5 -> heat 3.0
    assert decision.open_heat_pct == 3.0
    assert decision.budget_total_pct == 1.5


def test_be_reached_frees_heat():
    decision = evaluate_risk_governor_v4(
        BINDING,
        _state(
            open_positions=[
                {"risk_pct": 1.0, "cluster": "fx", "be_reached": True},
                {"risk_pct": 1.0, "cluster": "jpy_fx", "be_reached": False},
            ],
            cluster_correlation={("fx", "jpy_fx"): 0.9},
        ),
    )
    # only the jpy_fx leg is live and it has no live neighbours -> rho 1.0
    assert decision.open_heat_pct == 1.0


def test_pair_abs_correlation_lookup_shapes():
    assert pair_abs_correlation({}, "fx", "fx") == 1.0
    assert pair_abs_correlation({("fx", "jpy_fx"): -0.6}, "jpy_fx", "fx") == 0.6
    assert pair_abs_correlation({"fx|jpy_fx": 0.4}, "fx", "jpy_fx") == 0.4
    assert pair_abs_correlation({}, "fx", "metals") == 1.0  # fail closed
    assert pair_abs_correlation(lambda a, b: 0.3, "fx", "metals") == 0.3
    assert pair_abs_correlation(None, "fx", "metals") == 1.0


# ---------------------------------------------------------------------------
# Pacing / slice clamps
# ---------------------------------------------------------------------------


def test_pacing_halves_budget_at_full_remaining_weight_and_max_slice_clamps():
    decision = evaluate_risk_governor_v4(
        BINDING, _state(remaining_opportunity_weight=1.0, requested_risk_pct=3.0)
    )
    assert decision.pacing_fraction == 0.5
    # min(3.0, 4.5 * 0.5) = 2.25 -> clamped to max_slice 2.0 -> reduce
    assert decision.action == ACTION_REDUCE
    assert decision.approved_risk_pct == 2.0


def test_refuse_when_budget_at_or_below_min_slice():
    decision = evaluate_risk_governor_v4(BINDING, _state(realized_day_pnl_pct=-4.25))
    assert decision.budget_total_pct == 0.25
    assert decision.action == ACTION_REFUSE
    assert decision.approved_risk_pct == 0.0
    assert any("min_slice" in reason for reason in decision.reasons)


def test_refuse_when_paced_slice_falls_below_min_slice():
    decision = evaluate_risk_governor_v4(BINDING, _state(requested_risk_pct=0.1))
    assert decision.action == ACTION_REFUSE
    assert decision.approved_risk_pct == 0.0
    assert any("below_min_slice" in reason for reason in decision.reasons)


def test_non_positive_request_refused():
    decision = evaluate_risk_governor_v4(BINDING, _state(requested_risk_pct=0.0))
    assert decision.action == ACTION_REFUSE
    assert decision.approved_risk_pct == 0.0


# ---------------------------------------------------------------------------
# Circuit breakers
# ---------------------------------------------------------------------------


def test_intraday_breaker_triggers_flatten_halt():
    decision = evaluate_risk_governor_v4(
        BINDING, _state(intraday_conservative_dd_pct=4.2)
    )
    assert decision.action == ACTION_FLATTEN_HALT
    assert decision.approved_risk_pct == 0.0


def test_overall_floor_triggers_owner_review_and_outranks_breaker():
    decision = evaluate_risk_governor_v4(
        BINDING, _state(overall_dd_pct=8.0, intraday_conservative_dd_pct=9.0)
    )
    assert decision.action == ACTION_FLOOR_REVIEW
    assert decision.approved_risk_pct == 0.0


def test_below_thresholds_no_breaker():
    decision = evaluate_risk_governor_v4(
        BINDING, _state(intraday_conservative_dd_pct=4.19, overall_dd_pct=7.99)
    )
    assert decision.action == ACTION_ALLOW


# ---------------------------------------------------------------------------
# Fail-closed doctrine
# ---------------------------------------------------------------------------


def test_missing_required_state_refuses():
    for key in (
        "realized_day_pnl_pct",
        "open_positions",
        "requested_risk_pct",
        "remaining_opportunity_weight",
        "intraday_conservative_dd_pct",
        "overall_dd_pct",
    ):
        state = _state()
        state.pop(key)
        decision = evaluate_risk_governor_v4(BINDING, state)
        assert decision.action == ACTION_REFUSE, key
        assert decision.approved_risk_pct == 0.0
        assert any(key in reason for reason in decision.reasons), key


def test_forbidden_outcome_fields_in_state_refuse():
    for field in FORBIDDEN_STATE_FIELDS:
        decision = evaluate_risk_governor_v4(BINDING, dict(_state(), **{field: 1.0}))
        assert decision.action == ACTION_REFUSE, field
        assert any("forbidden_outcome_field" in reason for reason in decision.reasons)


def test_non_mapping_state_refuses():
    decision = evaluate_risk_governor_v4(BINDING, None)  # type: ignore[arg-type]
    assert decision.action == ACTION_REFUSE


# ---------------------------------------------------------------------------
# Default-off shadow contract
# ---------------------------------------------------------------------------


def test_default_off_is_shadow_only_with_would_fields():
    decision = evaluate_risk_governor_v4(GovernorConfigV4(), _state())
    assert decision.applied is False
    assert decision.would_action == decision.action
    assert decision.would_approved_risk_pct == decision.approved_risk_pct
    assert "shadow_only_not_applied_to_execution" in decision.reasons
    assert "governor_disabled_default_off" in decision.reasons
    packet = decision.to_packet()
    assert packet["execution_binding"] == "shadow_only_not_applied_to_execution"


def test_enabled_without_apply_to_execution_stays_shadow():
    cfg = GovernorConfigV4(enabled=True, apply_to_execution=False)
    decision = evaluate_risk_governor_v4(cfg, _state(intraday_conservative_dd_pct=9.0))
    assert decision.applied is False
    assert decision.action == ACTION_FLATTEN_HALT  # computed governance visible
    assert decision.would_action == ACTION_FLATTEN_HALT
    assert "shadow_only_not_applied_to_execution" in decision.reasons


def test_binding_decision_has_no_would_shadow():
    decision = evaluate_risk_governor_v4(BINDING, _state())
    assert decision.applied is True
    assert decision.would_action is None
    assert decision.would_approved_risk_pct is None


# ---------------------------------------------------------------------------
# Packets / determinism
# ---------------------------------------------------------------------------


def test_packet_carries_boundary_stamps_and_valid_action():
    packet = evaluate_risk_governor_v4(BINDING, _state()).to_packet()
    for key, value in BOUNDARY.items():
        assert packet[key] is value
    assert packet["schema_version"] == "risk_governor_decision_v4"
    assert packet["component"] == "risk_governor_v4"
    assert packet["action"] in ACTIONS
    config_packet = governor_config_packet(BINDING)
    for key, value in BOUNDARY.items():
        assert config_packet[key] is value


def test_evaluate_is_deterministic():
    state = _state(
        realized_day_pnl_pct=1.3,
        open_positions=[{"risk_pct": 0.7, "cluster": "fx", "be_reached": False}],
        remaining_opportunity_weight=0.4,
        requested_risk_pct=1.7,
    )
    first = evaluate_risk_governor_v4(BINDING, state)
    second = evaluate_risk_governor_v4(BINDING, state)
    assert isinstance(first, GovernorDecisionV4)
    assert first == second
    assert first.to_packet() == second.to_packet()
