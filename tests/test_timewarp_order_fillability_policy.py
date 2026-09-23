from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.research_infra import v4_timewarp_simulated_live_research_loop as timewarp


def test_guarded_market_fallback_waits_when_limit_fillability_is_high() -> None:
    asof = datetime(2025, 6, 11, 7, 15, tzinfo=timezone.utc)
    candidate = {
        "candidate_id": "candidate-high-fill",
        "symbol": "XAUUSD",
        "side": "SHORT",
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_sleeve_match_count": 1,
        "ultimate_package_role_disposition": "admission_candidate",
    }
    packets = {
        "candidate_probability": 0.86,
        "candidate_ev_r": 1.15,
        "cost_r": 0.07,
        "broker_calibrated_expected_cost_r": 0.07,
        "pretrade_broker_net_cost_packet": {
            "status": "PASSED",
            "authority": "broker_calibrated_replay_cost",
            "cost_source_gap_status": "source_bound_cost_authority_present",
            "candidate_cost_r_fallback_is_authority": False,
            "total_cost_r": 0.07,
        },
    }
    config = {
        "broad_live_as_if_replay_harness": {
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
        },
        "gtos_vnext_runtime": {
            "replay_order_fillability_policy_v1_enabled": True,
            "replay_order_fillability_policy_v1_require_package_execution_policy": True,
            "replay_order_fillability_policy_v1_fallback_delay_minutes": 30,
            "replay_order_fillability_policy_v1_min_candidate_probability": 0.58,
            "replay_order_fillability_policy_v1_min_candidate_ev_r": 0.20,
            "replay_order_fillability_policy_v1_min_candidate_expected_net_r_after_fallback": 0.40,
            "replay_order_fillability_policy_v1_min_fill_probability": 0.60,
            "replay_order_fillability_policy_v1_max_limit_fill_probability_for_fallback": 0.85,
            "replay_order_fillability_policy_v1_min_source_completeness": 0.75,
            "replay_order_fillability_policy_v1_max_expected_cost_r": 0.20,
            "replay_order_fillability_policy_v1_guarded_market_extra_cost_r": 0.05,
            "broad_live_as_if_replay_enforce_broker_cost_packet_status": True,
        },
    }

    decision = timewarp.replay_guarded_market_fallback_decision(
        config=config,
        candidate=candidate,
        packets=packets,
        scheduler_packet={},
        risk_authority={"risk_decision": "reduce-risk"},
        selected_option={},
        selected_inputs={"fill_probability": 0.92, "source_completeness": 0.95},
        limit_oracle_until_fallback={"fill_status": "not_filled_pending"},
        asof=asof,
        expiry=asof + timedelta(hours=2),
    )

    assert decision["status"] == "not_eligible"
    assert decision["reason"] == "limit_fill_probability_above_fallback_wait_ceiling"
    assert decision["max_limit_fill_probability_for_fallback"] == 0.85
