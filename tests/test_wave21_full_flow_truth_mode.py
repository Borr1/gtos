from __future__ import annotations

from src.components.probability_debate_v4 import ProbabilityDebateTeamEngineV4
from src.research_infra.wave21_full_flow_truth import (
    PROBABILITY_TRUTH_STATUS,
    apply_probability_truth_to_event,
    geometry_bound_outcome_calibration_disposition,
    strip_probability_economic_authority,
    wave21_full_flow_truth_mode_enabled,
)


def test_wave21_full_flow_truth_mode_is_explicit_boolean_and_default_off() -> None:
    assert wave21_full_flow_truth_mode_enabled({}) is False
    assert (
        wave21_full_flow_truth_mode_enabled(
            {"gtos_vnext_runtime": {"wave21_full_flow_truth_mode_enabled": False}}
        )
        is False
    )
    assert (
        wave21_full_flow_truth_mode_enabled(
            {"gtos_vnext_runtime": {"wave21_full_flow_truth_mode_enabled": "true"}}
        )
        is False
    )
    assert (
        wave21_full_flow_truth_mode_enabled(
            {"gtos_vnext_runtime": {"wave21_full_flow_truth_mode_enabled": True}}
        )
        is True
    )


def _no_outcome_calibration_debate() -> dict:
    return {
        "selected_action": "long",
        "theses": [
            {
                "action": "long",
                "probability": 0.91,
                "uncalibrated_probability": 0.94,
                "EV": 1.31,
                "ev_r": 1.31,
                "reward_r": 2.0,
                "loss_r": 1.0,
                "cost_r": 0.04,
                "confidence_calibration": {
                    "score": 0.91,
                    "calibrated_probability": 0.91,
                    "calibration_source_status": (
                        "runtime_reliability_prior_no_outcome_calibration_claim"
                    ),
                },
                "calibration": 0.91,
                "uncertainty": 0.12,
                "support": 0.88,
            }
        ],
    }


def test_no_outcome_calibration_is_only_action_support_in_truth_mode() -> None:
    projected = strip_probability_economic_authority(_no_outcome_calibration_debate())
    thesis = projected["theses"][0]

    assert thesis["action_support_score"] == 0.91
    assert thesis["action_support_score_status"].endswith(
        "no_outcome_calibration_claim"
    )
    assert thesis["uncertainty"] == 0.12
    assert thesis["support"] == 0.88
    for forbidden in (
        "probability",
        "uncalibrated_probability",
        "EV",
        "ev_r",
        "reward_r",
        "loss_r",
        "cost_r",
        "confidence_calibration",
        "calibration",
    ):
        assert forbidden not in thesis


def test_actual_debate_engine_projection_has_no_ev_derived_rank_or_reason() -> None:
    decision = ProbabilityDebateTeamEngineV4(
        {
            "gtos_vnext_runtime": {
                "probability_debate_team_engine_v4": {"enabled": True}
            }
        }
    ).evaluate(
        {
            "candidate_id": "truth-projection-adversary",
            "symbol": "XAUUSD",
            "candidate_direction": "LONG",
            "risk_reward_ratio": 2.0,
            "cost_r": 0.04,
            "sources": [],
        }
    )
    raw = decision.to_record()

    assert raw["ranked_actions"]
    assert raw["rejected_alternatives"]
    assert "prob=" in raw["reason"] and "ev=" in raw["reason"]
    assert all("selection_score" in thesis for thesis in raw["theses"])

    projected = strip_probability_economic_authority(raw)

    for key in (
        "debate_controls",
        "field_group_statuses",
        "packet_hash_sha256",
        "ranked_actions",
        "reason",
        "rejected_alternatives",
        "runtime_disposition",
        "selected_action",
        "selected_direction",
        "selected_thesis",
        "source_event_hash_sha256",
    ):
        assert key not in projected
    assert len(projected["theses"]) == 8
    for thesis in projected["theses"]:
        assert set(thesis) == {
            "action",
            "action_support_score",
            "action_support_score_status",
            "direction",
            "disagreement_state",
            "evidence_class",
            "missing_source_penalty",
            "opposition",
            "source_completeness",
            "source_ids",
            "support",
            "uncertainty",
        }
    assert strip_probability_economic_authority(projected) == projected


def test_truth_event_recursively_removes_laundered_probability_and_ev_aliases() -> None:
    event = {
        "probability": 0.91,
        "probability_raw": 0.93,
        "probability_pct": 91.0,
        "candidate_probability": 0.91,
        "candidate_ev_r": 1.31,
        "expectancy": 1.31,
        "executable_expected_value": 1.27,
        "candidate_expected_net_r": 1.27,
        "fill_probability": 0.42,
        "broker_probability_calibration": {"score": 0.91},
        "broker_cost_calibration": {"spread_r": 0.04},
        "broker_calibrated_expected_cost_r": 0.04,
        "selected_cell": {
            "broker_net_expectancy_r": 1.27,
            "stress_expectancy_r": 1.22,
            "risk_pct": 0.25,
        },
        "nested": {
            "expected_net_r": 1.27,
            "confidence_calibration": {"score": 0.91},
        },
    }

    projected = apply_probability_truth_to_event(
        event,
        probability_debate=_no_outcome_calibration_debate(),
    )

    assert projected["probability_truth_status"] == PROBABILITY_TRUTH_STATUS
    assert projected["probability_truth_economic_authority_allowed"] is False
    assert "fill_probability" not in projected
    assert projected["broker_cost_calibration"] == {"spread_r": 0.04}
    assert projected["broker_calibrated_expected_cost_r"] == 0.04
    assert projected["selected_cell"] == {"risk_pct": 0.25}
    assert projected["nested"] == {}
    for forbidden in (
        "probability",
        "probability_raw",
        "probability_pct",
        "candidate_probability",
        "candidate_ev_r",
        "expectancy",
        "executable_expected_value",
        "candidate_expected_net_r",
        "broker_probability_calibration",
    ):
        assert forbidden not in projected


def test_geometry_revalidation_hook_never_accepts_unsupported_or_stale_packet() -> None:
    packet = {"geometry_contract_hash_sha256": "a" * 64}
    original_geometry = {"packet_hash_sha256": "a" * 64}
    final_geometry = {"packet_hash_sha256": "b" * 64}

    unsupported = geometry_bound_outcome_calibration_disposition(
        packet,
        original_geometry,
    )
    stale = geometry_bound_outcome_calibration_disposition(packet, final_geometry)

    assert unsupported["status"] == PROBABILITY_TRUTH_STATUS
    assert unsupported["economic_authority_allowed"] is False
    assert unsupported["reason"].endswith("model_version_unsupported")
    assert stale["status"] == PROBABILITY_TRUTH_STATUS
    assert stale["economic_authority_allowed"] is False
    assert stale["reason"].endswith("stale_after_geometry_change")
