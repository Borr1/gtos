"""Adversarial proof for the closed Wave 21 truth Selector inputs."""

from __future__ import annotations

import copy

import pytest

from src.components.selector_input_projection import (
    SELECTOR_CONTEXT_INPUT_PROJECTION_STATUS_MATERIALIZED,
    SELECTOR_ORDER_AGNOSTIC_INPUT_PROJECTION_STATUS_MATERIALIZED,
    build_selector_context_input_projection_fields,
    build_selector_order_agnostic_input_projection_fields,
    selector_context_input_projection_failures,
    selector_order_agnostic_input_projection_failures,
    selector_truth_sanitized_inputs,
)
from src.components.selector_v4 import evaluate_selector_v4_admission


def _thesis(*, ev: float, probability: float) -> dict[str, object]:
    return {
        "probability": probability,
        "EV": ev,
        "uncertainty": 0.18,
        "missing_source_penalty": 0.05,
        "source_completeness": 0.95,
        "confidence_calibration": 0.82,
        "evidence_class": "source_bound_design_fixture",
        "vetoes": [],
        "disagreement_state": "resolved",
        "rejected_alternatives": ["no-trade", "wait"],
    }


def _theses() -> dict[str, dict[str, object]]:
    return {
        "long": _thesis(ev=0.32, probability=0.66),
        "short": _thesis(ev=-0.18, probability=0.30),
        "no-trade": _thesis(ev=0.0, probability=0.40),
        "wait": _thesis(ev=0.04, probability=0.45),
        "scale": _thesis(ev=0.12, probability=0.54),
        "reduce": _thesis(ev=0.10, probability=0.52),
        "close": _thesis(ev=-0.05, probability=0.48),
        "reverse": _thesis(ev=-0.12, probability=0.34),
    }


def _confluence_source(source_id: str = "selector-framework") -> dict[str, object]:
    return {
        "source_id": source_id,
        "source_family": "selector",
        "label": "FOLLOW",
        "direction": "LONG",
        "strength": 0.86,
        "confidence": 0.84,
        "reliability_history": 0.78,
        "freshness": 0.92,
        "source_completeness": 0.96,
        "cost_sensitivity": 0.10,
        "evidence_class": "source_bound_design_fixture",
    }


def _event() -> dict[str, object]:
    return {
        "candidate_id": "legacy-id-must-not-be-authority",
        "symbol": "XAUUSD.r",
        "side": "LONG",
        "decision_time_utc": "2026-05-26T13:00:00.000001Z",
        "origin_family": "current_fvg_fill",
        "generator_family_strategy_version": "current_fvg_fill.v1",
        "candidate_action_class": "NEW_EXPOSURE_CANDIDATE",
        "entry_reference_price": 100.0,
        "entry_reference_price_provenance": "closed_m15_reference",
        "entry_price": 100.0,
        "stop_loss": 99.0,
        "take_profit_1": 101.5,
        "risk_reward_ratio": 1.5,
        "candidate_transform_chain_root_sha256": "1" * 64,
        "emission_lineage_hash_sha256": "2" * 64,
        "emission_source_authority_root_sha256": "3" * 64,
        "emission_source_composition_root_sha256": "4" * 64,
        "emission_mso_source_receipt_root_sha256": "5" * 64,
        "emission_producer_code_root_sha256": "6" * 64,
        "emission_producer_config_sha256": "7" * 64,
        "emission_source_timeframe": "M15",
        "emission_source_timestamp_timezone_status": "timezone_aware",
        "source_window_complete": True,
        "numeric_confluence": {"sources": [_confluence_source()]},
        "probability_debate": {
            "selected_action": "long",
            "theses": _theses(),
        },
        "selected_cell": {
            "selected_cell_id": "xauusd_london_long_fixture",
            "broker_net_expectancy_r": 0.30,
            "stress_expectancy_r": 0.20,
            "risk_pct": 0.25,
            "rows": 64,
            "source_completeness": 0.94,
            "evidence_class": "source_bound_design_fixture",
            "source_status": "broker_net_design_fixture",
        },
        "cost": {
            "expected_total_cost_r": 0.03,
            "spread_r": 0.01,
            "slippage_stress_r": 0.01,
            "swap_r": 0.0,
            "commission_r": 0.004,
            "pretrade_cost_packet_status": "PASSED",
            "cost_source_gap_status": "source_bound_cost_authority_present",
            "cost_authority": "broker_calibrated_replay_cost",
            "candidate_cost_r_fallback_is_authority": False,
            "source_completeness": 0.95,
            "evidence_class": "pretrade_cost_design_fixture",
        },
        "lifecycle": {
            "duplicate_exposure": False,
            "same_symbol_conflict": "none",
            "open_trade_competition_status": "new_candidate_best",
            "ticket_bound_state": "no_open_ticket",
            "pending_partial_be_trailing_stale_state": "none",
            "source_completeness": 0.96,
            "evidence_class": "lifecycle_design_fixture",
        },
    }


def _config(**overrides: object) -> dict[str, object]:
    runtime: dict[str, object] = {
        "wave21_full_flow_truth_mode_enabled": True,
        "selector_v4_enabled": True,
        "selector_v4_apply_to_execution": True,
        "selector_v4_live_activation_allowed": False,
        "selector_v4_require_confluence_source_families": False,
        "selector_v4_min_broker_net_trade_ev_r": 0.10,
        "selector_v4_min_no_trade_ev_r": 0.02,
        "selector_v4_min_confluence_score": 0.15,
        "selector_v4_reduce_risk_multiplier": 0.5,
    }
    runtime.update(overrides)
    return {"gtos_vnext_runtime": runtime}


def _candidate_receipt(event: dict[str, object] | None = None) -> dict[str, object]:
    return build_selector_order_agnostic_input_projection_fields(event or _event())


def _context_receipt(
    event: dict[str, object] | None = None,
    config: dict[str, object] | None = None,
) -> dict[str, object]:
    return build_selector_context_input_projection_fields(
        event or _event(),
        config or _config(),
    )


def test_valid_candidate_and_context_are_separate_closed_packets() -> None:
    candidate = _candidate_receipt()
    context = _context_receipt()
    assert candidate["selector_order_agnostic_input_projection_status"] == (
        SELECTOR_ORDER_AGNOSTIC_INPUT_PROJECTION_STATUS_MATERIALIZED
    )
    assert context["selector_context_input_projection_status"] == (
        SELECTOR_CONTEXT_INPUT_PROJECTION_STATUS_MATERIALIZED
    )
    projection = candidate["selector_order_agnostic_input_projection"]
    assert projection["symbol"] == "XAUUSD.R"
    assert "candidate_id" not in projection
    assert "selected_cell" not in projection
    assert "cost" not in projection
    assert "lifecycle" not in projection
    assert set(context["selector_context_event_projection"]) == {
        "selected_cell",
        "cost",
        "lifecycle",
    }


def test_empty_and_every_required_candidate_atom_fail_closed() -> None:
    empty = build_selector_order_agnostic_input_projection_fields({})
    assert empty["selector_order_agnostic_input_projection_sha256"] is None
    assert empty["selector_order_agnostic_input_projection_missing_required_paths"]

    base = _event()
    for field in (
        "symbol",
        "side",
        "decision_time_utc",
        "origin_family",
        "generator_family_strategy_version",
        "candidate_action_class",
        "entry_reference_price",
        "entry_reference_price_provenance",
        "entry_price",
        "stop_loss",
        "take_profit_1",
        "candidate_transform_chain_root_sha256",
        "emission_lineage_hash_sha256",
        "emission_source_authority_root_sha256",
        "emission_source_composition_root_sha256",
        "emission_mso_source_receipt_root_sha256",
        "emission_producer_code_root_sha256",
        "emission_producer_config_sha256",
        "emission_source_timeframe",
        "emission_source_timestamp_timezone_status",
        "source_window_complete",
        "numeric_confluence",
        "probability_debate",
    ):
        changed = copy.deepcopy(base)
        changed.pop(field)
        receipt = _candidate_receipt(changed)
        assert receipt["selector_order_agnostic_input_projection_sha256"] is None, field


def test_legacy_id_and_order_policy_are_stripped_and_cannot_move_hash() -> None:
    base = _event()
    changed = copy.deepcopy(base)
    changed.update(
        {
            "candidate_id": "a-different-legacy-id",
            "candidate_order_type_hint": "LIMIT",
            "order_type": "STOP",
            "time_in_force": "GTC",
            "expiry_time_utc": "2026-05-27T13:00:00Z",
        }
    )
    first = _candidate_receipt(base)
    second = _candidate_receipt(changed)
    assert first["selector_order_agnostic_input_projection_sha256"] == second[
        "selector_order_agnostic_input_projection_sha256"
    ]
    assert {"candidate_id", "candidate_order_type_hint", "order_type", "time_in_force", "expiry_time_utc"}.issubset(
        set(second["selector_order_agnostic_input_projection_removed_non_authoritative_paths"])
    )


@pytest.mark.parametrize(
    ("path", "value"),
    [
        ("ultimate_candidate_package", {"target_action_intent": "new-position"}),
        ("moonshot_dynamic_execution_router_v4", {"action": "trade"}),
        ("predecision_limit_fillability", {"fill_probability": 0.99}),
        ("learned_edge", {"expected_r": 10.0}),
        ("renamed_outcome_packet", {"later_profit": 12.0}),
        ("source_fields", {"renamed_result": {"later_profit": 12.0}}),
    ],
)
def test_package_router_fillability_and_disguised_unknowns_refuse(
    path: str,
    value: object,
) -> None:
    event = _event()
    event[path] = value
    receipt = _candidate_receipt(event)
    assert receipt["selector_order_agnostic_input_projection_sha256"] is None
    assert receipt["selector_order_agnostic_input_projection_forbidden_outcome_paths"]


def test_candidate_decision_inputs_is_closed_to_debate_only() -> None:
    event = _event()
    event["candidate_decision_inputs"] = {
        "probability_debate": copy.deepcopy(event["probability_debate"]),
        "package_new_entry_authority_payload": {"target_action_intent": "trade"},
    }
    receipt = _candidate_receipt(event)
    assert receipt["selector_order_agnostic_input_projection_sha256"] is None
    assert (
        "candidate_decision_inputs.package_new_entry_authority_payload"
        in receipt["selector_order_agnostic_input_projection_forbidden_outcome_paths"]
    )


def test_nested_confluence_and_context_unknowns_refuse() -> None:
    event = _event()
    event["numeric_confluence"]["sources"][0]["future_gain_r"] = 3.0
    assert _candidate_receipt(event)[
        "selector_order_agnostic_input_projection_sha256"
    ] is None

    event = _event()
    event["selected_cell"]["hidden_outcome"] = 1.0
    assert _context_receipt(event)["selector_context_input_projection_sha256"] is None


def test_alias_conflicts_refuse_in_every_packet_family() -> None:
    event = _event()
    event["direction"] = "SHORT"
    assert _candidate_receipt(event)[
        "selector_order_agnostic_input_projection_sha256"
    ] is None

    event = _event()
    event["candidate_decision_inputs"] = {
        "debate": {"selected_action": "short", "theses": _theses()}
    }
    assert _candidate_receipt(event)[
        "selector_order_agnostic_input_projection_sha256"
    ] is None

    event = _event()
    event["broker_net_selected_cell"] = copy.deepcopy(event["selected_cell"])
    event["broker_net_selected_cell"]["risk_pct"] = 0.1
    assert _context_receipt(event)["selector_context_input_projection_sha256"] is None

    event = _event()
    event["broker_cost"] = copy.deepcopy(event["cost"])
    event["broker_cost"]["expected_total_cost_r"] = 0.5
    assert _context_receipt(event)["selector_context_input_projection_sha256"] is None

    event = _event()
    event["same_symbol_lifecycle"] = copy.deepcopy(event["lifecycle"])
    event["same_symbol_lifecycle"]["duplicate_exposure"] = True
    assert _context_receipt(event)["selector_context_input_projection_sha256"] is None


def test_nested_packet_alias_conflicts_and_duplicate_debate_actions_refuse() -> None:
    event = _event()
    event["cost"]["pretrade_broker_net_cost_packet"] = {
        "expected_total_cost_r": 0.03,
        "total_cost_r": 0.9,
    }
    assert _context_receipt(event)["selector_context_input_projection_sha256"] is None

    event = _event()
    event["lifecycle"]["same_symbol_lifecycle_v4_packet"] = {
        "action": "allow",
        "candidate": {
            "candidate_id": "one",
            "replay_candidate_id": "two",
        },
    }
    assert _context_receipt(event)["selector_context_input_projection_sha256"] is None

    event = _event()
    rows = []
    for action, thesis in _theses().items():
        rows.append({"action": action, **thesis})
    rows.append({"action": "buy", **_thesis(ev=0.4, probability=0.7)})
    event["probability_debate"] = {
        "selected_action": "long",
        "theses": rows,
    }
    assert _candidate_receipt(event)[
        "selector_order_agnostic_input_projection_sha256"
    ] is None


def test_source_order_and_set_permutations_are_canonical_but_duplicates_refuse() -> None:
    first = _event()
    second = copy.deepcopy(first)
    first["numeric_confluence"]["sources"] = [
        _confluence_source("z-source"),
        _confluence_source("a-source"),
    ]
    second["numeric_confluence"]["sources"] = list(
        reversed(first["numeric_confluence"]["sources"])
    )
    first["probability_debate"]["vetoes"] = ["b", "a", "b"]
    second["probability_debate"]["vetoes"] = ["a", "b"]
    assert _candidate_receipt(first)[
        "selector_order_agnostic_input_projection_sha256"
    ] == _candidate_receipt(second)["selector_order_agnostic_input_projection_sha256"]

    duplicate = _event()
    duplicate["numeric_confluence"]["sources"] = [
        _confluence_source("same"),
        _confluence_source("same"),
    ]
    assert _candidate_receipt(duplicate)[
        "selector_order_agnostic_input_projection_sha256"
    ] is None


def test_context_moves_only_context_hash_and_active_unsafe_config_refuses() -> None:
    base = _event()
    changed = copy.deepcopy(base)
    changed["cost"]["expected_total_cost_r"] = 0.09
    changed["lifecycle"]["same_symbol_conflict"] = "opposite-direction-open"
    assert _candidate_receipt(base)[
        "selector_order_agnostic_input_projection_sha256"
    ] == _candidate_receipt(changed)["selector_order_agnostic_input_projection_sha256"]
    assert _context_receipt(base)["selector_context_input_projection_sha256"] != (
        _context_receipt(changed)["selector_context_input_projection_sha256"]
    )

    unsafe = _context_receipt(
        base,
        _config(selector_v4_learned_edge_enabled=True),
    )
    assert unsafe["selector_context_input_projection_sha256"] is None
    assert any(
        "unsafe_active_policy" in item
        for item in unsafe["selector_context_forbidden_or_unknown_paths"]
    )

    unknown = _context_receipt(
        base,
        _config(selector_v4_future_untyped_policy=1),
    )
    assert unknown["selector_context_input_projection_sha256"] is None


def test_context_empty_or_missing_truth_config_refuses() -> None:
    receipt = build_selector_context_input_projection_fields({}, {})
    assert receipt["selector_context_input_projection_sha256"] is None
    assert {"selected_cell", "cost", "lifecycle"}.issubset(
        set(receipt["selector_context_missing_required_paths"])
    )


def test_post_selector_and_scheduler_outputs_cannot_rewrite_preselector_root() -> None:
    event = _event()
    base = _candidate_receipt(event)
    event.update(
        {
            "selector_action": "trade",
            "selector_reason": "broker_net_trade",
            "component_scores": {"unsafe_if_reprojected": True},
            "risk_pct": 0.2,
            "scheduler_option_identity_sha256": "8" * 64,
        }
    )
    current = _candidate_receipt(event)
    assert current["selector_order_agnostic_input_projection_sha256"] == base[
        "selector_order_agnostic_input_projection_sha256"
    ]


def test_sanitized_payload_is_exact_selector_call_surface_and_preserves_safe_behavior() -> None:
    event = _event()
    event.update(
        {
            "candidate_order_type_hint": "LIMIT",
            "candidate_id": "legacy-moves-nothing",
            "account_id": "never-in-selector-event",
        }
    )
    result = selector_truth_sanitized_inputs(event, _config())
    assert result["status"] == "materialized"
    sanitized = result["sanitized_event"]
    assert sanitized is not None
    assert not {
        "candidate_id",
        "candidate_order_type_hint",
        "account_id",
        "ultimate_candidate_package",
        "dynamic_policy",
        "predecision_limit_fillability",
    }.intersection(sanitized)

    source_safe_original = copy.deepcopy(event)
    source_safe_original.pop("candidate_id")
    source_safe_original.pop("candidate_order_type_hint")
    source_safe_original.pop("account_id")
    original_decision = evaluate_selector_v4_admission(source_safe_original, _config())
    sanitized_decision = evaluate_selector_v4_admission(
        sanitized,
        result["sanitized_config"],
    )
    assert (
        sanitized_decision.action,
        sanitized_decision.reason,
        sanitized_decision.component_scores,
        sanitized_decision.source_required_fields,
    ) == (
        original_decision.action,
        original_decision.reason,
        original_decision.component_scores,
        original_decision.source_required_fields,
    )


def test_receipts_recompute_current_inputs_and_reject_tamper() -> None:
    event = _event()
    config = _config()
    candidate = _candidate_receipt(event)
    context = _context_receipt(event, config)
    assert selector_order_agnostic_input_projection_failures(event, candidate) == ()
    assert selector_context_input_projection_failures(event, config, context) == ()

    geometry_mutation = copy.deepcopy(event)
    geometry_mutation["stop_loss"] = 98.5
    assert selector_order_agnostic_input_projection_failures(
        geometry_mutation,
        candidate,
    )

    context_mutation = copy.deepcopy(event)
    context_mutation["cost"]["expected_total_cost_r"] = 0.10
    assert selector_context_input_projection_failures(
        context_mutation,
        config,
        context,
    )

    tampered = dict(candidate)
    tampered["selector_order_agnostic_input_projection_sha256"] = "0" * 64
    assert selector_order_agnostic_input_projection_failures(event, tampered)


def test_naive_time_nonfinite_and_unsupported_primitives_refuse() -> None:
    event = _event()
    event["decision_time_utc"] = "2026-05-26T13:00:00"
    assert _candidate_receipt(event)[
        "selector_order_agnostic_input_projection_sha256"
    ] is None

    event = _event()
    event["entry_price"] = float("nan")
    assert _candidate_receipt(event)[
        "selector_order_agnostic_input_projection_sha256"
    ] is None

    event = _event()
    event["numeric_confluence"]["sources"][0]["confidence"] = object()
    assert _candidate_receipt(event)[
        "selector_order_agnostic_input_projection_sha256"
    ] is None
