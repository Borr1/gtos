from __future__ import annotations

import pytest

from src.components.executable_value_semantics import (
    EXPECTED_VALUE_ALREADY_FILL_ADJUSTED,
    EXPECTED_VALUE_GIVEN_FILL,
    PAYOFF_MAGNITUDE_REQUIRES_OUTCOME_AND_FILL,
    executable_expected_value,
)
from src.components.order_blocker_precedence import resolve_order_blockers
from src.components.poi_execution_lifecycle import (
    build_causal_poi_lifecycle_envelope,
    causal_poi_lifecycle_contract_failures,
    predecision_fillability_boundary_allowed,
    predecision_limit_fillability_from_geometry,
)
from src.components.poi_state_contract import finalize_poi_state, stable_poi_id


DECISION_TIME = "2026-05-14T01:15:00+00:00"
SOURCE_TIME = "2026-05-14T01:00:00+00:00"
FILL_BOUNDARY = "closed_m15_predecision_asof_no_postdecision_path"


def _poi_state(**overrides):
    source_times = [
        "2026-05-14T00:00:00+00:00",
        "2026-05-14T00:15:00+00:00",
        "2026-05-14T00:30:00+00:00",
    ]
    state = {
        "poi_id": stable_poi_id(
            symbol="US30_CASH",
            timeframe="M15",
            poi_type="fair_value_gap",
            direction="bullish",
            source_candle_times=source_times,
            zone_low=100.0,
            zone_high=102.0,
        ),
        "poi_type": "fair_value_gap",
        "poi_timeframe": "M15",
        "poi_direction": "bullish",
        "poi_zone_low": 100.0,
        "poi_zone_high": 102.0,
        "poi_source_candle_times": source_times,
        "poi_created_at_utc": "2026-05-14T00:45:00+00:00",
        "poi_state_asof_utc": SOURCE_TIME,
        "poi_age_hours": 0.25,
        "poi_touch_count": 0,
        "poi_overlap_bar_count": 0,
        "poi_touch_episode_count": 0,
        "poi_max_mitigation_fraction": 0.0,
        "poi_first_touch_time_utc": "",
        "poi_last_touch_time_utc": "",
        "poi_mitigation_status": "untouched",
        "poi_filled": False,
        "poi_invalidated": False,
        "poi_invalidation_time_utc": "",
        "poi_invalidation_reason": "",
        "poi_terminal_time_utc": "",
        "poi_terminal_reason": "",
        "poi_terminal_frozen": False,
    }
    state.update(overrides)
    return finalize_poi_state(state)


def _fillability(*, current_price: float, entry_price: float = 101.0):
    return predecision_limit_fillability_from_geometry(
        side="LONG",
        entry_price=entry_price,
        stop_loss=99.0,
        current_price=current_price,
        atr14=1.0,
        current_price_source="latest_closed_m15_close",
        current_price_source_time_utc=SOURCE_TIME,
        current_price_source_boundary=FILL_BOUNDARY,
        decision_time_utc=DECISION_TIME,
    )


def _lifecycle(state, fillability, *, distance_to_zone_price: float = 0.0):
    return build_causal_poi_lifecycle_envelope(
        poi_state=state,
        decision_time_utc=DECISION_TIME,
        fillability=fillability,
        distance_to_zone_price=distance_to_zone_price,
        distance_to_zone_atr=distance_to_zone_price,
        distance_to_midpoint_price=distance_to_zone_price,
        distance_to_midpoint_atr=distance_to_zone_price,
        scheduler_readiness_floor=0.45,
        scheduler_readiness_policy_source="test_floor",
        scheduler_readiness_policy_hash_sha256="a" * 64,
    )


def test_poi_state_v1_hash_ignores_separate_lifecycle_fields():
    base = _poi_state()
    raw = {key: value for key, value in base.items() if key != "poi_state_hash_sha256"}
    raw.pop("poi_state_contract_status", None)
    raw.pop("poi_state_contract_failures", None)
    extended = finalize_poi_state(
        {
            **raw,
            "causal_poi_lifecycle": {"scheduler_rankable_now": True},
            "causal_poi_lifecycle_hash_sha256": "b" * 64,
        }
    )
    assert extended["poi_state_hash_sha256"] == base["poi_state_hash_sha256"]


def test_lifecycle_rankability_is_hash_bound_to_execution_fillability():
    state = _poi_state()
    lifecycle = _lifecycle(state, _fillability(current_price=100.5))
    assert lifecycle["scheduler_rankable_now"] is True
    assert lifecycle["execution_allowed_by_poi_lifecycle"] is True
    assert lifecycle["contract_failures"] == []

    tampered = {**lifecycle, "execution_fill_probability": 0.01}
    assert "poi_lifecycle_hash_mismatch" in causal_poi_lifecycle_contract_failures(
        tampered,
        poi_state=state,
        decision_time_utc=DECISION_TIME,
    )


@pytest.mark.parametrize(
    "boundary",
    (
        "closed_m15_predecision_asof_no_postdecision_path",
        "asof_candidate_fields_only_no_postdecision_path",
        "predecision_source_no_outcome_fields",
    ),
)
def test_predecision_fillability_boundary_accepts_explicit_negative_qualifiers(
    boundary,
):
    assert predecision_fillability_boundary_allowed(boundary) is True


@pytest.mark.parametrize(
    "boundary",
    (
        "postdecision_reconstructed_path",
        "predecision_plus_outcome_label",
        "asof_actual_fill_result",
        "broker_live_realized_fill",
    ),
)
def test_predecision_fillability_boundary_rejects_unsafe_sources(boundary):
    assert predecision_fillability_boundary_allowed(boundary) is False


def test_terminal_and_dormant_pois_are_visible_but_not_scheduler_rankable():
    dormant = _lifecycle(
        _poi_state(),
        _fillability(current_price=120.0),
        distance_to_zone_price=18.0,
    )
    assert dormant["visible_candidate"] is True
    assert dormant["poi_proximity_state"] == "dormant"
    assert dormant["scheduler_rankable_now"] is False

    invalidated = _poi_state(
        poi_invalidated=True,
        poi_invalidation_time_utc=SOURCE_TIME,
        poi_invalidation_reason="bullish_fvg_close_below_far_boundary",
        poi_terminal_time_utc=SOURCE_TIME,
        poi_terminal_reason="bullish_fvg_close_below_far_boundary",
        poi_terminal_frozen=True,
    )
    terminal = _lifecycle(invalidated, _fillability(current_price=100.5))
    assert terminal["poi_lifecycle_state"] == "invalidated"
    assert terminal["scheduler_rankable_now"] is False


def test_executable_value_applies_declared_probability_units_once():
    common = {
        "expected_net_r": 2.0,
        "probability": 0.8,
        "execution_fill_probability": 0.25,
        "source_completeness": 0.9,
    }
    already_adjusted = executable_expected_value(
        **common,
        semantics=EXPECTED_VALUE_ALREADY_FILL_ADJUSTED,
    )
    conditional = executable_expected_value(
        **common,
        semantics=EXPECTED_VALUE_GIVEN_FILL,
    )
    payoff = executable_expected_value(
        **common,
        semantics=PAYOFF_MAGNITUDE_REQUIRES_OUTCOME_AND_FILL,
    )
    assert already_adjusted["executable_expected_value"] == 1.8
    assert conditional["executable_expected_value"] == 0.45
    assert payoff["executable_expected_value"] == pytest.approx(0.36)


def test_specific_blocker_precedence_demotes_generic_selector_alias():
    resolved = resolve_order_blockers(
        "selector_reduce_risk_new_entry_not_order_authority",
        "admission_quality_off_configured_session_entry_blocked",
        "execution_fillability_below_poi_scheduler_readiness_floor",
        signed_order_proposal_allowed=True,
    )
    assert resolved["primary_family"] == "session_authority"
    assert resolved["primary_reason"] == (
        "admission_quality_off_configured_session_entry_blocked"
    )
    assert resolved["co_blockers"] == [
        "execution_fillability_below_poi_scheduler_readiness_floor"
    ]
    assert resolved["superseded_aliases"] == [
        "selector_reduce_risk_new_entry_not_order_authority"
    ]


def test_namespaced_poi_lifecycle_reason_outranks_generic_package_blocker():
    resolved = resolve_order_blockers(
        {
            "risk_finalizer_causal_poi_lifecycle": {
                "primary_reason": (
                    "execution_fillability_below_poi_scheduler_readiness_floor"
                ),
                "scheduler_rankable_now": False,
            },
        },
        "package_executable_authority_required_not_met",
        signed_order_proposal_allowed=False,
    )

    assert resolved["primary_family"] == "execution_fillability"
    assert resolved["primary_reason"] == (
        "execution_fillability_below_poi_scheduler_readiness_floor"
    )
    assert resolved["primary_source"] == (
        "reason_surface[0].risk_finalizer_causal_poi_lifecycle.primary_reason"
    )
    assert resolved["co_blockers"] == [
        "package_executable_authority_required_not_met"
    ]


def test_scheduler_ready_poi_lifecycle_reason_is_not_a_blocker():
    resolved = resolve_order_blockers(
        {
            "causal_poi_lifecycle": {
                "primary_reason": "poi_scheduler_readiness_passed",
                "scheduler_rankable_now": True,
            }
        },
        "off_configured_session_requires_explicit_off_session_authority",
    )

    assert resolved["primary_reason"] == (
        "off_configured_session_requires_explicit_off_session_authority"
    )
    assert "poi_scheduler_readiness_passed" not in resolved[
        "all_observed_reasons"
    ]


def test_stop_hazard_risk_cap_is_sizing_metadata_not_terminal_blocker():
    resolved = resolve_order_blockers(
        {
            "risk_decision_reason": (
                "predecision_stop_hazard_guard_risk_cap_applied"
            )
        },
        "ordered_tick_required_for_adverse_before_profit_sequence_not_satisfied",
    )

    assert resolved["primary_reason"] == (
        "ordered_tick_required_for_adverse_before_profit_sequence_not_satisfied"
    )
    assert "predecision_stop_hazard_guard_risk_cap_applied" not in resolved[
        "all_observed_reasons"
    ]


def test_stop_hazard_block_remains_terminal_blocker():
    resolved = resolve_order_blockers(
        "predecision_stop_hazard_guard_blocked",
        "scheduler_materialization_skipped_not_selected",
    )

    assert resolved["primary_reason"] == "predecision_stop_hazard_guard_blocked"
    assert resolved["primary_family"] == "risk_safety"
