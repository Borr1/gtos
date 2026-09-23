from research.operations.final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20 import (  # noqa: E501
    build_source_bound_execution_parity as parity,
)


def test_leakage_label_separates_refused_broker_cost_from_selector_leak() -> None:
    label = parity.leakage_label(
        {
            "candidate_generated_count": 3,
            "scorecard_selected_count": 0,
            "selector_action_counts": {"reject": 3},
            "pretrade_cost_packet_status_counts": {"REFUSED": 3},
        }
    )

    assert label == "candidate_generated_broker_cost_refused_not_executable"
    assert label in parity.BLOCKED_COUNTERFACTUAL_MISSED_LABELS
    assert parity.repair_stage_for_label(label) == "cost_authority_non_executable"


def test_leakage_label_keeps_cost_passed_selector_reject_as_selector_leak() -> None:
    label = parity.leakage_label(
        {
            "candidate_generated_count": 2,
            "scorecard_selected_count": 0,
            "selector_action_counts": {"reject": 2},
            "pretrade_cost_packet_status_counts": {"PASSED": 2},
        }
    )

    assert label == "candidate_generated_selector_reject"
    assert parity.repair_stage_for_label(label) == "selector_admission_calibration"


def test_leakage_label_maps_expired_unfilled_orders_to_fillability_leak() -> None:
    label = parity.leakage_label(
        {
            "candidate_generated_count": 1,
            "scorecard_selected_count": 1,
            "order_present_count": 1,
            "trade_count": 0,
            "risk_decision_counts": {"trade": 1},
            "order_status_counts": {
                "accepted_not_filled_pending_until_expiry": 1,
                "expired_unfilled": 1,
            },
        }
    )

    assert label == "order_accepted_not_filled"


def test_candidate_deviation_reason_uses_cost_refusal_before_selector_reason() -> None:
    reason = parity.candidate_deviation_reason(
        {
            "selector_action": "reject",
            "selector_reason": "broker_net_admission_ev_negative_after_cost",
            "pretrade_cost_packet_status": "REFUSED",
            "pretrade_cost_refusal_reasons": [
                "spread_r_exceeds_selected_cell_limit:1.216407>0.100000"
            ],
        },
        {},
    )

    assert reason == "broker_cost_refused:spread_r_exceeds_selected_cell_limit:1.216407>0.100000"


def test_candidate_deviation_reason_maps_expired_unfilled_orders_to_fillability_leak() -> None:
    reason = parity.candidate_deviation_reason(
        {"selector_action": "trade"},
        {
            "scheduler_option_present": True,
            "scheduler_selected": True,
            "order_present": True,
            "trade_present": False,
            "risk_decision_counts": {},
            "order_status_counts": parity.Counter(
                {"accepted_not_filled_pending_until_expiry": 1}
            ),
        },
    )

    assert reason == "order_accepted_not_filled"
