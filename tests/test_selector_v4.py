from datetime import datetime, timedelta

from src.components.gtos_vnext_runtime import evaluate_vnext_selector_v4_admission
from src.components.selector_v4 import (
    SELECTOR_V4_OPEN_REDUCED_SELECTOR_REASONS,
    SelectorV4AdmissionDecision,
    _package_new_entry_signed_authority_detail,
    evaluate_selector_v4_admission,
    selector_v4_action_blocks_execution,
    selector_v4_action_is_risk_bearing,
)
from src.research.reduced_risk_action_reason_contract import (
    OPEN_REDUCED_SELECTOR_REASONS,
    SELECTOR_REDUCE_RISK_NEW_ENTRY_BLOCK_REASONS,
)
from src.research.moonshot_scheduler_v4_best_trade_allocator import (
    stamp_package_new_entry_authority,
)
from src.research_infra.wave21_full_flow_truth import (
    PROBABILITY_TRUTH_STATUS,
    apply_probability_truth_to_event,
)


ULTIMATE_PACKAGE_SOURCE = (
    "research/operations/"
    "final_moonshot_ultimate_system_final_package_acceptance_compression_2026_06_19/"
    "FINAL_PACKAGE_SLEEVE_CANDIDATE_LEDGER.jsonl"
)


def _config(**overrides):
    cfg = {
        "selector_v4_enabled": True,
        "selector_v4_apply_to_execution": True,
        "selector_v4_live_activation_allowed": True,
        "selector_v4_min_broker_net_trade_ev_r": 0.10,
        "selector_v4_min_no_trade_ev_r": 0.02,
        "selector_v4_min_confluence_score": 0.15,
        "selector_v4_reduce_risk_multiplier": 0.5,
    }
    cfg.update(overrides)
    return {"gtos_vnext_runtime": cfg}


def _thesis(ev=0.32, probability=0.66, uncertainty=0.18, vetoes=None):
    return {
        "probability": probability,
        "EV": ev,
        "uncertainty": uncertainty,
        "vetoes": vetoes or [],
        "missing_source_penalty": 0.05,
        "confidence_calibration": 0.82,
        "source_completeness": 0.95,
        "evidence_class": "source_bound_design_fixture",
        "disagreement_state": "resolved",
        "rejected_alternatives": ["no-trade", "wait"],
    }


def _theses(**overrides):
    theses = {
        "long": _thesis(),
        "short": _thesis(ev=-0.18, probability=0.30),
        "no-trade": _thesis(ev=0.0, probability=0.40),
        "wait": _thesis(ev=0.04, probability=0.45),
        "scale": _thesis(ev=0.12, probability=0.54),
        "reduce": _thesis(ev=0.10, probability=0.52),
        "close": _thesis(ev=-0.05, probability=0.48),
        "reverse": _thesis(ev=-0.12, probability=0.34),
    }
    theses.update(overrides)
    return theses


def _follow_source(source_id="fam_primary", **overrides):
    source = {
        "source_id": source_id,
        "source_family": "selector",
        "label": "FOLLOW",
        "direction": "LONG",
        "strength": 0.86,
        "confidence": 0.84,
        "reliability_history": 0.78,
        "evidence_class": "source_bound_design_fixture",
        "freshness": 0.92,
        "cost_sensitivity": 0.10,
        "source_completeness": 0.96,
        "conflict_reason": None,
    }
    source.update(overrides)
    return source


def _required_confluence_sources():
    return [
        _follow_source("selector-framework", source_family="selector"),
        _follow_source(
            "market-state",
            source_family="market_state",
            strength=0.74,
            confidence=0.78,
        ),
        _follow_source(
            "cost-model",
            source_family="cost",
            strength=0.70,
            confidence=0.74,
            cost_sensitivity=0.12,
        ),
        _follow_source(
            "lifecycle-state",
            source_family="lifecycle",
            strength=0.68,
            confidence=0.72,
        ),
        _follow_source(
            "source-completeness",
            source_family="source_completeness",
            strength=0.88,
            confidence=0.86,
        ),
    ]


PREDECISION_FILLABILITY_BOUNDARY = "closed_m15_predecision_asof_no_postdecision_path"


def _predecision_limit_fillability(
    fill_probability,
    *,
    decision_time_utc="2026-05-05T06:15:00Z",
    **extra,
):
    """Model the nested fillability surface the way production actually emits it.

    `selector_v4._complete_execution_fillability_atom` (`selector_v4.py:453-537`)
    deliberately refuses to propagate a fill probability unless one surface carries a
    COMPLETE value+provenance tuple: it `continue`s at `:508` when either the source
    time or the source boundary is missing, "without cross-stitching" per its own
    docstring. A fixture supplying `fill_probability` alone therefore resolves
    `package_execution_fill_probability` to `None`, and every softening path that
    needs it -- off-session, numeric-disagreement, fill-floor, router-refusal bypass
    -- stops firing. That is why ten tests here expected `reduce-risk` /
    `open-reduced-risk` and got `reject`.

    Production never presents the value-only shape. The replay passes
    `current_price_source_time_utc` / `current_price_source_boundary` into
    `poi_execution_lifecycle.predecision_limit_fillability_from_geometry`
    (`v4_timewarp_simulated_live_research_loop.py:53891-53900`), and that function
    emits both keys on every return path (`poi_execution_lifecycle.py:148-160` for the
    degraded path, `:196-207` for the success path). So the engine's requirement is
    correct and these fixtures were the stale side of the contract.
    """
    decision_time = datetime.fromisoformat(decision_time_utc.replace("Z", "+00:00"))
    source_time_utc = (
        decision_time - timedelta(minutes=15)
    ).isoformat().replace("+00:00", "Z")
    surface = {
        "available": True,
        "fill_probability": fill_probability,
        "current_price_source_time_utc": source_time_utc,
        "source_boundary": PREDECISION_FILLABILITY_BOUNDARY,
        "uses_outcome_fields": False,
    }
    surface.update(extra)
    return surface


def _signed_package_new_entry_authority(
    *,
    candidate_id="selector_v4_fixture_001",
    decision_time_utc="2026-05-05T06:15:00Z",
    authority_hash=None,
    expected_hash=None,
    expected_net_r=1.20,
    probability=0.82,
    fill_probability=0.30,
    source_completeness=0.95,
):
    instance_key = f"{candidate_id}@@{decision_time_utc}"
    decision_time = datetime.fromisoformat(decision_time_utc.replace("Z", "+00:00"))
    fillability_source_time_utc = (
        decision_time - timedelta(minutes=15)
    ).isoformat().replace("+00:00", "Z")
    selector_reason = (
        "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
    )
    seed = {
        "candidate_id": candidate_id,
        "candidate_id_source": "candidate_id",
        "decision_time_utc": decision_time_utc,
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "ultimate_package_matched_member_axis_count": 1,
        "ultimate_package_admission_member_axis_match_count": 1,
        "ultimate_package_matched_member_axis_ids": [
            f"selector-fixture-axis:{candidate_id}"
        ],
        "selector_action": "open-reduced-risk",
        "selector_reason": selector_reason,
        "expected_net_r": expected_net_r,
        "probability": probability,
        "fill_probability": fill_probability,
        "execution_fill_probability": fill_probability,
        "execution_fill_probability_source": (
            "predecision_limit_fillability.fill_probability"
        ),
        "execution_fill_probability_source_time_utc": fillability_source_time_utc,
        "execution_fill_probability_source_boundary": (
            "closed_m15_predecision_asof_no_postdecision_path"
        ),
        "entry_quality_fill_probability": fill_probability,
        "limit_fillability_probability": fill_probability,
        "predecision_limit_fillability_probability": fill_probability,
        "predecision_limit_fillability_source_time_utc": fillability_source_time_utc,
        "predecision_limit_fillability_source_boundary": (
            "closed_m15_predecision_asof_no_postdecision_path"
        ),
        "predecision_limit_fillability": _predecision_limit_fillability(
            fill_probability, decision_time_utc=decision_time_utc
        ),
        "source_completeness": source_completeness,
        "source_completeness_status": "complete",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "selector_fixture.predecision.expected_net_r",
            "probability": "selector_fixture.predecision.probability",
            "fill_probability": "selector_fixture.predecision.fill_probability",
            "source_completeness": (
                "selector_fixture.predecision.source_completeness"
            ),
        },
        "candidate_decision_quality_source_boundary": (
            "predecision_selector_fixture_quality_no_outcome_fields"
        ),
        "candidate_decision_quality_alias_status": "exact_materialized",
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed_reason": (
            "selector_fixture_signed_authority"
        ),
        "package_replay_order_executable_authority_source": (
            "selector_fixture_predecision_authority"
        ),
        "pretrade_cost_packet_status": "PASSED",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "cost_authority": "broker_calibrated_replay_cost",
        "candidate_cost_r_fallback_is_authority": False,
    }
    stamped = stamp_package_new_entry_authority(
        seed,
        selector_action="open-reduced-risk",
        selector_reason=selector_reason,
        authority={
            "applies": True,
            "allowed": True,
            "authority_family": "fill_floor_softening",
            "authority_source": "selector_fixture_predecision_authority",
            "source_boundary": (
                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
            ),
        },
        action_intent="new_position",
    )
    fields = {
        key: value
        for key, value in stamped.items()
        if key.startswith("package_new_entry_authority_")
        or key == "expected_package_new_entry_authority_hash_sha256"
    }
    if authority_hash is not None:
        fields["package_new_entry_authority_hash_sha256"] = authority_hash
    if expected_hash is not None:
        fields["expected_package_new_entry_authority_hash_sha256"] = expected_hash
    return fields


def _event(**overrides):
    event = {
        "candidate_id": "selector_v4_fixture_001",
        "symbol": "XAUUSD",
        "side": "LONG",
        "numeric_confluence": {
            "sources": _required_confluence_sources()
        },
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
    event.update(overrides)
    return event


def test_selector_v4_trade_decision_has_runtime_effect_when_authorized():
    decision = evaluate_selector_v4_admission(_event(), _config())
    record = decision.to_record()

    assert decision.action == "trade"
    assert decision.runtime_effect_now is True
    assert decision.candidate_use_allowed_now is True
    assert decision.broker_operation is False
    assert decision.broker_runtime_change_status is False
    assert decision.final_risk_pct == 0.25
    assert len(record["source_event_hash_sha256"]) == 64
    assert len(record["packet_hash_sha256"]) == 64
    assert record["field_group_statuses"]["probability_debate"]["selected_action"] == "long"
    assert record["field_group_statuses"]["numeric_confluence"]["source_count"] == 5


def test_truth_event_blocks_no_outcome_score_from_satisfying_selector_economics():
    laundered_theses = {}
    for action, raw_thesis in _theses().items():
        thesis = dict(raw_thesis)
        score = thesis["probability"]
        thesis["confidence_calibration"] = {
            "score": score,
            "calibrated_probability": score,
            "calibration_source_status": (
                "runtime_reliability_prior_no_outcome_calibration_claim"
            ),
        }
        thesis["calibration"] = score
        laundered_theses[action] = thesis
    event = _event(
        probability_debate={
            "selected_action": "long",
            "theses": laundered_theses,
        }
    )

    legacy = evaluate_selector_v4_admission(event, _config())
    truth_event = apply_probability_truth_to_event(
        event,
        probability_debate=event["probability_debate"],
    )
    truth = evaluate_selector_v4_admission(
        truth_event,
        _config(wave21_full_flow_truth_mode_enabled=True),
    )

    assert legacy.action == "trade"
    assert truth_event["probability_truth_status"] == PROBABILITY_TRUTH_STATUS
    assert truth.action == "source-required"
    assert truth.source_bound_candidate_use_allowed_now is False
    assert truth.replay_candidate_use_allowed_now is False
    assert any(
        field.startswith("probability_debate.theses.long.")
        for field in truth.source_required_fields
    )
    assert "broker_net_expectancy_r" not in truth_event["selected_cell"]
    assert "stress_expectancy_r" not in truth_event["selected_cell"]


def test_selector_record_preserves_raw_selector_action_under_downstream_mutation():
    decision = SelectorV4AdmissionDecision(
        schema_version="selector_v4_admission_decision_v1",
        component="selector_v4",
        enabled=True,
        apply_to_execution=True,
        live_activation_allowed_by_config=False,
        action="open-reduced-risk",
        would_action="reject",
        decision_status="fixture_materialized",
        reason="materialized_for_replay",
        runtime_effect_now=True,
        candidate_use_allowed_now=True,
        source_bound_candidate_use_allowed_now=True,
        replay_candidate_use_allowed_now=True,
        risk_multiplier=0.5,
        final_risk_pct=0.10,
        selector_reason="raw_selector_reject_before_materialization",
    )

    record = decision.to_record()

    assert record["action"] == "open-reduced-risk"
    assert record["would_action"] == "reject"
    assert record["selector_action"] == "reject"
    assert record["selector_reason"] == "raw_selector_reject_before_materialization"
    assert record["candidate_use_allowed_now_semantics"] == "live_runtime_effect"


def test_selector_action_and_would_action_contract():
    decision = evaluate_selector_v4_admission(
        _event(),
        _config(
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )
    record = decision.to_record()

    assert decision.action == "trade"
    assert decision.would_action == "trade"
    assert decision.selector_action == decision.would_action
    assert decision.selector_reason == decision.reason
    assert record["selector_action"] == record["would_action"] == "trade"
    assert record["selector_reason"] == record["reason"]
    assert record["candidate_use_allowed_now"] is False
    assert record["candidate_use_allowed_now_semantics"] == "live_runtime_effect"
    assert record["source_bound_candidate_use_allowed_now"] is True


def test_selector_open_reduced_reason_contract_stays_in_sync():
    assert SELECTOR_V4_OPEN_REDUCED_SELECTOR_REASONS == OPEN_REDUCED_SELECTOR_REASONS
    assert (
        "broker_net_admission_ev_below_full_trade_floor"
        not in SELECTOR_V4_OPEN_REDUCED_SELECTOR_REASONS
    )
    assert (
        "broker_net_admission_ev_below_full_trade_floor"
        not in SELECTOR_REDUCE_RISK_NEW_ENTRY_BLOCK_REASONS
    )
    assert (
        "ultimate_candidate_package_positive_predecision_off_session_reduce_risk"
        not in SELECTOR_V4_OPEN_REDUCED_SELECTOR_REASONS
    )
    assert (
        "ultimate_candidate_package_positive_predecision_off_session_reduce_risk"
        in SELECTOR_REDUCE_RISK_NEW_ENTRY_BLOCK_REASONS
    )


def test_selector_v4_runtime_bridge_uses_active_config():
    decision = evaluate_vnext_selector_v4_admission(
        config=_config(),
        candidate_context=_event(),
    )

    assert decision.action == "trade"
    assert decision.enabled is True
    assert decision.apply_to_execution is True
    assert decision.live_activation_allowed_by_config is True
    assert decision.runtime_effect_now is True


def test_selector_v4_can_still_report_no_runtime_effect_when_flags_are_disabled():
    decision = evaluate_selector_v4_admission(
        _event(),
        _config(
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    assert decision.action == "trade"
    assert decision.runtime_effect_now is False
    assert decision.candidate_use_allowed_now is False
    assert decision.source_bound_candidate_use_allowed_now is True
    assert decision.replay_candidate_use_allowed_now is False


def test_selector_v4_replay_eligibility_does_not_require_live_activation():
    decision = evaluate_selector_v4_admission(
        _event(),
        _config(selector_v4_live_activation_allowed=False),
    )
    record = decision.to_record()

    assert decision.action == "trade"
    assert decision.runtime_effect_now is False
    assert decision.candidate_use_allowed_now is False
    assert decision.source_bound_candidate_use_allowed_now is True
    assert decision.replay_candidate_use_allowed_now is True
    assert record["source_bound_candidate_use_allowed_now"] is True
    assert record["replay_candidate_use_allowed_now"] is True


def test_selector_v4_attaches_ultimate_candidate_package_shadow_packet():
    decision = evaluate_selector_v4_admission(
        _event(
            symbol="NAS100",
            side="LONG",
            framework="origin_volatility_compression_expansion",
            origin_family="volatility_compression_expansion",
            decision_time_utc="2026-05-05T06:15:00Z",
        ),
        _config(
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=False,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )
    record = decision.to_record()
    package = record["component_scores"]["ultimate_candidate_package"]

    assert package["decision_status"] == "shadow_sleeve_matches_found"
    assert package["matched_sleeve_count"] >= 2
    assert package["matched_scheduler_lifecycle_merge_sleeves"] >= 1
    assert package["matched_promote_default_off_sleeves"] == 1
    assert package["action"] == "shadow_no_execution"
    assert package["runtime_effect_now"] is False
    assert decision.runtime_effect_now is False


def test_selector_v4_package_preserves_complete_execution_fillability_atom() -> None:
    decision = evaluate_selector_v4_admission(
        _event(
            symbol="NAS100",
            side="LONG",
            framework="origin_volatility_compression_expansion",
            origin_family="volatility_compression_expansion",
            decision_time_utc="2026-05-05T06:15:00Z",
            execution_fill_probability=0.92,
            execution_fill_probability_source=(
                "predecision_limit_fillability.fill_probability"
            ),
            execution_fill_probability_source_time_utc=(
                "2026-05-05T06:00:00Z"
            ),
            execution_fill_probability_source_boundary=(
                "closed_m15_predecision_asof_no_postdecision_path"
            ),
            execution_fill_probability_authority_class=(
                "predecision_passive_limit_fillability_authority"
            ),
            predecision_limit_fillability={
                "available": True,
                "fill_probability": 0.92,
                "current_price_source_time_utc": "2026-05-05T06:00:00Z",
                "current_price_source_boundary": (
                    "closed_m15_predecision_asof_no_postdecision_path"
                ),
            },
        ),
        _config(
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=False,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    package = decision.component_scores["ultimate_candidate_package"]
    assert package["execution_fill_probability"] == 0.92
    assert package["predecision_limit_fillability_probability"] == 0.92
    assert package["execution_fill_probability_source"] == (
        "predecision_limit_fillability.fill_probability"
    )
    assert package["execution_fill_probability_source_time_utc"] == (
        "2026-05-05T06:00:00Z"
    )
    assert package["execution_fill_probability_source_boundary"] == (
        "closed_m15_predecision_asof_no_postdecision_path"
    )
    assert package["execution_fillability_atomic_status"] == "complete"


def test_selector_v4_package_drops_incomplete_execution_fillability_alias() -> None:
    decision = evaluate_selector_v4_admission(
        _event(
            symbol="NAS100",
            side="LONG",
            framework="origin_volatility_compression_expansion",
            origin_family="volatility_compression_expansion",
            decision_time_utc="2026-05-05T06:15:00Z",
            execution_fill_probability=0.92,
        ),
        _config(
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=False,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    package = decision.component_scores["ultimate_candidate_package"]
    assert package["execution_fill_probability"] is None
    assert package["execution_fillability_atomic_status"] == (
        "incomplete_not_executable"
    )
    assert package["execution_fillability_atomic_failure"] == (
        "execution_fillability_incomplete_value_only_not_propagated"
    )


def test_selector_v4_ultimate_package_aliases_preserve_zero_and_confidence() -> None:
    decision = evaluate_selector_v4_admission(
        _event(
            symbol="NAS100",
            side="LONG",
            framework="origin_volatility_compression_expansion",
            origin_family="volatility_compression_expansion",
            decision_time_utc="2026-05-05T06:15:00Z",
            source_completeness=0.0,
            candidate_probability=0.0,
            candidate_expected_net_r=0.0,
            candidate_ev_r=0.0,
            fill_probability=0.0,
            confidence=0.0,
            selected_cell={
                **_event()["selected_cell"],
                "source_completeness": 1.0,
                "broker_net_expectancy_r": 1.8,
                "fill_probability": 0.91,
                "confidence": 0.82,
            },
            probability_debate={
                "selected_action": "long",
                "theses": _theses(long=_thesis(ev=1.7, probability=0.93)),
            },
        ),
        _config(
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=False,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    package = decision.to_record()["component_scores"]["ultimate_candidate_package"]
    assert package["source_completeness"] == 0.0
    assert package["candidate_probability"] == 0.0
    assert package["candidate_expected_net_r"] == 0.0
    assert package["candidate_ev_r"] == 0.0
    assert package["fill_probability"] == 0.0
    assert package["candidate_fill_probability"] == 0.0
    assert package["confidence"] == 0.0
    assert package["candidate_confidence"] == 0.0


def test_selector_v4_ultimate_package_uses_candidate_action_thesis_before_selected_action() -> None:
    decision = evaluate_selector_v4_admission(
        _event(
            symbol="NAS100",
            side="LONG",
            framework="origin_volatility_compression_expansion",
            origin_family="volatility_compression_expansion",
            decision_time_utc="2026-05-05T06:15:00Z",
            candidate_probability=None,
            candidate_expected_net_r=None,
            candidate_ev_r=None,
            fill_probability=None,
            confidence=None,
            probability_debate={
                "selected_action": "no-trade",
                "theses": _theses(
                    long=_thesis(ev=1.7, probability=0.93),
                    **{"no-trade": _thesis(ev=-0.2, probability=0.12)},
                ),
            },
        ),
        _config(
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=False,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    package = decision.to_record()["component_scores"]["ultimate_candidate_package"]
    assert package["candidate_probability"] == 0.93
    assert package["probability"] == 0.93
    assert package["candidate_ev_r"] == 1.7
    assert package["candidate_package_quality_thesis_source"] == (
        "probability_debate_candidate_action_thesis"
    )
    assert package["confidence"] == 0.55
    assert package["candidate_confidence"] == 0.55
    assert package["candidate_decision_quality_field_sources"]["confidence"] == (
        "scheduler_default_missing_confidence_0_55"
    )
    assert package["confidence_missing_degraded_default_applied"] is True
    assert "confidence_missing_degraded_default_applied" in package[
        "candidate_decision_quality_optional_provenance_warnings"
    ]


def test_selector_v4_blocks_partial_be_runner_admission_quality_guard():
    decision = evaluate_selector_v4_admission(
        _event(
            route_session="off_configured_session",
            dynamic_geometry_policy="partial_be_runner",
        ),
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_block_partial_be_runner=True,
            selector_v4_block_off_configured_session_partial_be_runner=True,
            selector_v4_admission_quality_guard_source=(
                "research/operations/final_moonshot_v4_kiap_ultimate_system_repair_2026_06_07/"
                "ULTIMATE_WEAK_ACCEPTED_FILTER_LEDGER.jsonl"
            ),
        ),
    )
    record = decision.to_record()

    assert decision.action == "reject"
    assert decision.runtime_effect_now is False
    assert (
        "admission_quality_partial_be_runner_blocked_after_kiap_weak_accepted_drag"
        in decision.hard_reject_reasons
    )
    assert record["field_group_statuses"]["admission_quality"][
        "dynamic_geometry_policy"
    ] == "partial_be_runner"


def test_selector_v4_blocks_dynamic_router_refused_candidate_when_enforced():
    decision = evaluate_selector_v4_admission(
        _event(
            moonshot_dynamic_execution_router_v4={
                "candidate_use_allowed_now": False,
                "runtime_effect_now": False,
                "decision_status": "refuse_live_use_until_source_or_scope_repaired",
                "candidate_action": "ACTIVATED_CANDIDATE_HELD_FOR_SOURCE_OR_BRANCH_REPAIR",
            },
        ),
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
        ),
    )
    record = decision.to_record()

    assert decision.action == "reject"
    assert decision.runtime_effect_now is False
    assert (
        "admission_quality_dynamic_router_refused_candidate_use"
        in decision.hard_reject_reasons
    )
    assert record["field_group_statuses"]["admission_quality"][
        "dynamic_router_refusal_enforced"
    ] is True


def test_selector_v4_blocks_configured_session_origin_and_hour_drag_rules():
    config = _config(
        selector_v4_admission_quality_guard_enabled=True,
        selector_v4_block_partial_be_runner=True,
        selector_v4_admission_quality_blocked_session_origin_families=[
            {
                "route_session": "off_configured_session",
                "origin_families": ["liquidity_sweep_reclaim"],
                "reason": "admission_quality_off_session_origin_family_blocked_after_kiap_probe_drag",
            }
        ],
        selector_v4_admission_quality_blocked_utc_hour_buckets=["h08_09"],
    )

    family_decision = evaluate_selector_v4_admission(
        _event(
            route_session="off_configured_session",
            origin_family="liquidity_sweep_reclaim",
            dynamic_geometry_policy="momentum_exhaustion",
        ),
        config,
    )
    hour_decision = evaluate_selector_v4_admission(
        _event(
            route_session="london",
            origin_family="cross_asset_lead_lag",
            dynamic_geometry_policy="momentum_exhaustion",
            utc_hour_bucket="h08_09",
        ),
        config,
    )

    assert family_decision.action == "reject"
    assert (
        "admission_quality_off_session_origin_family_blocked_after_kiap_probe_drag"
        in family_decision.hard_reject_reasons
    )
    assert hour_decision.action == "reject"
    assert (
        "admission_quality_utc_hour_bucket_blocked_after_kiap_drag"
        in hour_decision.hard_reject_reasons
    )


def test_selector_v4_blocks_general_off_configured_session_entry_authority():
    config = _config(
        selector_v4_admission_quality_guard_enabled=True,
        selector_v4_block_off_configured_session_entries=True,
    )

    decision = evaluate_selector_v4_admission(
        _event(
            route_session="off_configured_session",
            origin_family="current_fvg_fill",
            dynamic_geometry_policy="momentum_exhaustion",
        ),
        config,
    )

    assert decision.action == "reject"
    assert (
        "admission_quality_off_configured_session_entry_blocked"
        in decision.hard_reject_reasons
    )


def test_selector_v4_off_configured_session_entry_can_open_reduced_risk_when_configured():
    decision = evaluate_selector_v4_admission(
        _event(
            route_session="off_configured_session",
            origin_family="current_fvg_fill",
            dynamic_geometry_policy="momentum_exhaustion",
        ),
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_block_off_configured_session_entries=True,
            selector_v4_off_configured_session_entry_action="open-reduced-risk",
        ),
    )

    assert decision.action == "open-reduced-risk"
    assert (
        decision.reason
        == "admission_quality_off_configured_session_open_reduced_risk_configured"
    )
    assert (
        "admission_quality_off_configured_session_open_reduced_risk_configured"
        in decision.reduced_risk_reasons
    )
    assert (
        "admission_quality_off_configured_session_entry_blocked"
        not in decision.reduced_risk_reasons
    )
    assert (
        "admission_quality_off_configured_session_entry_blocked"
        not in decision.hard_reject_reasons
    )


def test_selector_v4_package_positive_off_session_softens_to_open_reduced_risk() -> None:
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        route_session="off_configured_session",
        dynamic_geometry_policy="momentum_exhaustion",
        decision_time_utc="2026-05-05T06:15:00Z",
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.0,
            "stress_expectancy_r": 0.8,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.1, probability=0.78)),
        },
        fill_probability=0.82,
        predecision_limit_fillability=_predecision_limit_fillability(0.82),
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_block_off_configured_session_entries=True,
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_positive_predecision_off_session_softening_enabled=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    assert decision.action == "reduce-risk"
    assert (
        "admission_quality_off_configured_session_entry_blocked"
        not in decision.hard_reject_reasons
    )
    assert (
        "ultimate_candidate_package_positive_predecision_off_session_reduce_risk"
        in decision.reduced_risk_reasons
    )
    assert (
        "ultimate_candidate_package_positive_predecision_off_session_open_reduced_risk"
        not in decision.reduced_risk_reasons
    )
    package = decision.component_scores["ultimate_candidate_package"]
    assert package["package_replay_executable_candidate_use_allowed"] is True
    assert package["candidate_decision_quality_provenance_failures"] == []
    assert decision.runtime_effect_now is False


def test_selector_v4_package_quality_reads_candidate_decision_inputs_for_softening() -> None:
    selected_cell = {
        **_event()["selected_cell"],
        "broker_net_expectancy_r": 1.0,
        "stress_expectancy_r": 0.8,
    }
    selected_cell.pop("fill_probability", None)
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        route_session="off_configured_session",
        dynamic_geometry_policy="momentum_exhaustion",
        decision_time_utc="2026-05-05T06:15:00Z",
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell=selected_cell,
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.1, probability=0.68)),
        },
            candidate_decision_inputs={
                "expected_net_r": 0.94,
                "probability": 0.84,
                "fill_probability": 0.82,
                "execution_fill_probability": 0.82,
                "limit_fillability_probability": 0.82,
                "predecision_limit_fillability_probability": 0.82,
                "predecision_limit_fillability": _predecision_limit_fillability(
                    0.82
                ),
            "source_completeness": 1.0,
            "candidate_decision_quality_field_sources": {
                "expected_net_r": "fixture.predecision.expected_net_r",
                "probability": "fixture.predecision.probability",
                "fill_probability": "fixture.predecision.fill_probability",
                "source_completeness": "fixture.predecision.source_completeness",
            },
            "candidate_decision_quality_source_boundary": (
                "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
            ),
            "candidate_decision_quality_alias_status": "exact_materialized",
        },
    )
    event.pop("fill_probability", None)
    event.pop("candidate_fill_probability", None)

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_block_off_configured_session_entries=True,
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_positive_predecision_off_session_softening_enabled=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    record = decision.to_record()
    package = record["component_scores"]["ultimate_candidate_package"]
    assert package["fill_probability"] == 0.82
    assert package["source_completeness"] == 1.0
    assert package["candidate_decision_quality_field_sources"] == {
        "expected_net_r": "fixture.predecision.expected_net_r",
        "probability": "fixture.predecision.probability",
        "fill_probability": "fixture.predecision.fill_probability",
        "entry_quality_fill_probability": (
            "selector_v4.candidate_decision_inputs.fill_probability"
        ),
        # Provenance now names the nested surface the atom actually selected, rather
        # than the flat alias it used to be stitched from. `_complete_execution_
        # fillability_atom` labels a nested-sourced value with this exact literal
        # (`selector_v4.py:494-500`), and it is the same string the production-faithful
        # fixture in this file declares for the flat field
        # (`_signed_package_new_entry_authority`, "execution_fill_probability_source").
        "execution_fill_probability": "predecision_limit_fillability.fill_probability",
        "limit_fillability_probability": (
            "selector_v4.candidate_decision_inputs.limit_fillability_probability"
        ),
        "source_completeness": "fixture.predecision.source_completeness",
        "confidence": "scheduler_default_missing_confidence_0_55",
    }
    assert package["candidate_decision_quality_alias_status"] == "exact_materialized"
    assert package["candidate_decision_quality_provenance_failures"] == []
    quality_contract = record["component_scores"][
        "ultimate_candidate_package_quality_contract"
    ]
    assert quality_contract["valid"] is True
    assert (
        quality_contract["alias_status"]
        == "exact_materialized"
    )
    assert decision.action == "open-reduced-risk"
    assert (
        "ultimate_candidate_package_positive_predecision_off_session_open_reduced_risk"
        in decision.reduced_risk_reasons
    )


def test_selector_v4_limit_fillability_does_not_satisfy_entry_quality_fill() -> None:
    selected_cell = {**_event()["selected_cell"]}
    selected_cell.pop("fill_probability", None)
    event = _event(
        selected_cell=selected_cell,
        candidate_decision_inputs={
            "predecision_limit_fillability": {"fill_probability": 0.92},
        },
        predecision_limit_fillability={"fill_probability": 0.92},
    )
    event.pop("fill_probability", None)
    event.pop("candidate_fill_probability", None)

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_calibrated_admission_enabled=True,
            selector_v4_calibrated_admission_require_fill_probability=True,
            selector_v4_calibrated_admission_floor_failure_action="reject",
            selector_v4_calibrated_min_fill_probability=0.45,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    admission = decision.to_record()["component_scores"]["admission_quality"]
    assert admission["fill_probability"] is None
    assert admission["source_required_fields"] == [
        "selector_v4_calibrated_admission.fill_probability"
    ]
    assert decision.action == "source-required"


def test_selector_v4_quality_contract_rejects_execution_fillability_as_generic_fill_probability() -> None:
    selected_cell = {
        **_event()["selected_cell"],
        "broker_net_expectancy_r": 1.0,
        "stress_expectancy_r": 0.8,
        "source_completeness": 1.0,
    }
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        route_session="off_configured_session",
        dynamic_geometry_policy="momentum_exhaustion",
        decision_time_utc="2026-05-05T06:15:00Z",
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell=selected_cell,
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.1, probability=0.84)),
        },
        candidate_decision_inputs={
            "expected_net_r": 0.94,
            "probability": 0.84,
            "fill_probability": 0.82,
            "source_completeness": 1.0,
            "candidate_decision_quality_field_sources": {
                "expected_net_r": "fixture.predecision.expected_net_r",
                "probability": "fixture.predecision.probability",
                "fill_probability": (
                    "fixture.predecision_limit_fillability.fill_probability"
                ),
                "source_completeness": "fixture.predecision.source_completeness",
            },
            "candidate_decision_quality_source_boundary": (
                "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
            ),
            "candidate_decision_quality_alias_status": "exact_materialized",
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_block_off_configured_session_entries=True,
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_positive_predecision_off_session_softening_enabled=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    package = decision.component_scores["ultimate_candidate_package"]
    assert (
        "fill_probability_source_is_execution_fillability:"
        "fixture.predecision_limit_fillability.fill_probability"
    ) in package["candidate_decision_quality_provenance_failures"]
    assert package["package_replay_executable_candidate_use_allowed"] is False


def test_selector_v4_package_softening_fails_closed_on_invalid_quality_boundary() -> None:
    selected_cell = {
        **_event()["selected_cell"],
        "broker_net_expectancy_r": 1.0,
        "stress_expectancy_r": 0.8,
        "source_completeness": 1.0,
    }
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        route_session="off_configured_session",
        dynamic_geometry_policy="momentum_exhaustion",
        decision_time_utc="2026-05-05T06:15:00Z",
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell=selected_cell,
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.1, probability=0.84)),
        },
        candidate_decision_inputs={
            "expected_net_r": 0.94,
            "probability": 0.84,
            "fill_probability": 0.82,
            "source_completeness": 1.0,
            "candidate_decision_quality_field_sources": {
                "expected_net_r": "fixture.predecision.expected_net_r",
                "probability": "fixture.predecision.probability",
                "fill_probability": "fixture.predecision.fill_probability",
                "source_completeness": "fixture.predecision.source_completeness",
            },
            "candidate_decision_quality_source_boundary": (
                "postdecision_outcome_quality_rehydration"
            ),
            "candidate_decision_quality_alias_status": "exact_materialized",
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_block_off_configured_session_entries=True,
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_positive_predecision_off_session_softening_enabled=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    package = decision.component_scores["ultimate_candidate_package"]
    assert decision.action == "reject"
    assert "admission_quality_off_configured_session_entry_blocked" in (
        decision.hard_reject_reasons
    )
    assert package["package_replay_executable_candidate_use_allowed"] is False
    assert (
        "candidate_decision_quality_source_boundary_not_predecision"
        in package["candidate_decision_quality_provenance_failures"]
    )
    assert decision.replay_candidate_use_allowed_now is False


def test_selector_v4_package_positive_off_session_softening_is_default_off() -> None:
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        route_session="off_configured_session",
        dynamic_geometry_policy="momentum_exhaustion",
        decision_time_utc="2026-05-05T06:15:00Z",
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.0,
            "stress_expectancy_r": 0.8,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.1, probability=0.68)),
        },
        fill_probability=0.82,
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_block_off_configured_session_entries=True,
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    assert decision.action == "reject"
    assert (
        "admission_quality_off_configured_session_entry_blocked"
        in decision.hard_reject_reasons
    )
    assert (
        "ultimate_candidate_package_positive_predecision_off_session_open_reduced_risk"
        not in decision.reduced_risk_reasons
    )


def test_selector_v4_package_off_session_softening_does_not_bypass_cost_refusal() -> None:
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        route_session="off_configured_session",
        dynamic_geometry_policy="momentum_exhaustion",
        decision_time_utc="2026-05-05T06:15:00Z",
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "REFUSED",
                "refusal_reasons": ["total_cost_r_exceeds_limit"],
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.0,
            "stress_expectancy_r": 0.8,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.1, probability=0.78)),
        },
        fill_probability=0.82,
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_block_off_configured_session_entries=True,
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_positive_predecision_off_session_softening_enabled=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    assert decision.action == "reject"
    assert any(
        reason.startswith("broker_net_pretrade_cost_packet_refused")
        for reason in decision.hard_reject_reasons
    )
    assert (
        "ultimate_candidate_package_positive_predecision_off_session_open_reduced_risk"
        not in decision.reduced_risk_reasons
    )


def test_selector_v4_repaired_replay_uses_package_session_tokens_for_off_session_namespace():
    config = _config(
        selector_v4_admission_quality_guard_enabled=True,
        selector_v4_block_off_configured_session_entries=True,
        selector_v4_package_session_token_authority_enabled=True,
        selector_v4_apply_to_execution=False,
        selector_v4_live_activation_allowed=False,
    )

    decision = evaluate_selector_v4_admission(
        _event(
            route_session="off_configured_session",
            session_bucket="off_configured_session",
            package_session_tokens=[
                "h08_09",
                "london_broad",
                "moonshot_h08_09",
                "off_configured_session",
            ],
            origin_family="current_fvg_fill",
            dynamic_geometry_policy="momentum_exhaustion",
        ),
        config,
    )

    admission = decision.component_scores["admission_quality"]
    assert decision.action == "trade"
    assert (
        "admission_quality_off_configured_session_entry_blocked"
        not in decision.hard_reject_reasons
    )
    assert admission["raw_route_session"] == "off_configured_session"
    assert admission["route_session"] == "london"
    assert admission["package_session_authority"]["applied"] is True
    assert decision.runtime_effect_now is False


def test_selector_v4_repaired_replay_uses_nested_package_session_tokens() -> None:
    config = _config(
        selector_v4_admission_quality_guard_enabled=True,
        selector_v4_block_off_configured_session_entries=True,
        selector_v4_package_session_token_authority_enabled=True,
        selector_v4_apply_to_execution=False,
        selector_v4_live_activation_allowed=False,
    )

    decision = evaluate_selector_v4_admission(
        _event(
            route_session="off_configured_session",
            session_bucket="off_configured_session",
            package_session_tokens=[],
            candidate_decision_inputs={
                "symbol": "XAUUSD",
                "side": "LONG",
                "package_session_tokens": [
                    "h08_09",
                    "london_broad",
                    "moonshot_h08_09",
                    "off_configured_session",
                ],
            },
            origin_family="current_fvg_fill",
            dynamic_geometry_policy="momentum_exhaustion",
        ),
        config,
    )

    admission = decision.component_scores["admission_quality"]
    assert decision.action == "trade"
    assert (
        "admission_quality_off_configured_session_entry_blocked"
        not in decision.hard_reject_reasons
    )
    assert admission["raw_route_session"] == "off_configured_session"
    assert admission["route_session"] == "london"
    assert admission["package_session_authority"]["applied"] is True
    assert admission["package_session_authority"]["package_session_tokens"] == [
        "h08_09",
        "london_broad",
        "moonshot_h08_09",
        "off_configured_session",
    ]


def test_selector_v4_package_session_tokens_do_not_bypass_raw_off_session_loss_rules():
    config = _config(
        selector_v4_admission_quality_guard_enabled=True,
        selector_v4_block_off_configured_session_entries=True,
        selector_v4_package_session_token_authority_enabled=True,
        selector_v4_admission_quality_blocked_session_origin_families=[
            {
                "route_session": "off_configured_session",
                "origin_families": ["current_fvg_fill"],
                "reason": "fixture_raw_off_session_loss_rule",
            }
        ],
        selector_v4_apply_to_execution=False,
        selector_v4_live_activation_allowed=False,
    )

    decision = evaluate_selector_v4_admission(
        _event(
            route_session="off_configured_session",
            session_bucket="off_configured_session",
            package_session_tokens=[
                "h08_09",
                "london_broad",
                "moonshot_h08_09",
                "off_configured_session",
            ],
            origin_family="current_fvg_fill",
            dynamic_geometry_policy="momentum_exhaustion",
        ),
        config,
    )

    admission = decision.component_scores["admission_quality"]
    assert decision.action == "reject"
    assert "fixture_raw_off_session_loss_rule" in decision.hard_reject_reasons
    assert (
        "admission_quality_off_configured_session_entry_blocked"
        not in decision.hard_reject_reasons
    )
    assert admission["route_session"] == "london"
    assert admission["exact_rule_route_session"] == "off_configured_session"


def test_selector_v4_blocks_symbol_specific_broad_dynamic_loss_combos():
    config = _config(
        selector_v4_admission_quality_guard_enabled=True,
        selector_v4_admission_quality_blocked_session_origin_symbols=[
            {
                "route_session": "off_configured_session",
                "origin_families": ["origin_displacement_continuation"],
                "symbols": ["EURGBP", "BTCUSD"],
                "reason": "admission_quality_broad_dynamic_accepted_loss_symbol_family_blocked",
            },
            {
                "route_session": "off_configured_session",
                "origin_families": ["origin_cross_asset_lead_lag"],
                "broker_symbols": ["USOIL_cash"],
                "reason": "admission_quality_broad_dynamic_accepted_loss_symbol_family_blocked",
            },
        ],
    )

    eurgbp_decision = evaluate_selector_v4_admission(
        _event(
            symbol="EURGBP",
            route_session="off_configured_session",
            origin_family="origin_displacement_continuation",
            dynamic_geometry_policy="momentum_exhaustion",
        ),
        config,
    )
    usoil_decision = evaluate_selector_v4_admission(
        _event(
            symbol="",
            broker_symbol="USOIL_cash",
            route_session="off_configured_session",
            origin_family="origin_cross_asset_lead_lag",
            dynamic_geometry_policy="momentum_exhaustion",
        ),
        config,
    )

    assert eurgbp_decision.action == "reject"
    assert usoil_decision.action == "reject"
    assert (
        "admission_quality_broad_dynamic_accepted_loss_symbol_family_blocked"
        in eurgbp_decision.hard_reject_reasons
    )
    assert (
        eurgbp_decision.to_record()["field_group_statuses"]["admission_quality"][
            "symbol"
        ]
        == "eurgbp"
    )
    assert (
        usoil_decision.to_record()["field_group_statuses"]["admission_quality"][
            "symbol"
        ]
        == "usoil_cash"
    )


def test_selector_v4_symbol_specific_guard_preserves_broad_dynamic_winner_symbols():
    config = _config(
        selector_v4_admission_quality_guard_enabled=True,
        selector_v4_admission_quality_blocked_session_origin_symbols=[
            {
                "route_session": "off_configured_session",
                "origin_families": ["origin_displacement_continuation"],
                "symbols": ["EURGBP", "BTCUSD"],
                "reason": "admission_quality_broad_dynamic_accepted_loss_symbol_family_blocked",
            },
            {
                "route_session": "tokyo",
                "origin_families": ["origin_displacement_continuation"],
                "symbols": ["CHFJPY", "NZDUSD"],
                "reason": "admission_quality_broad_dynamic_accepted_loss_symbol_family_blocked",
            },
            {
                "route_session": "tokyo",
                "origin_families": ["origin_session_open_range_break"],
                "symbols": ["AUDUSD", "GBPJPY", "NZDUSD"],
                "reason": "admission_quality_broad_dynamic_accepted_loss_symbol_family_blocked",
            },
        ],
    )

    ethusd_decision = evaluate_selector_v4_admission(
        _event(
            symbol="ETHUSD",
            route_session="off_configured_session",
            origin_family="origin_displacement_continuation",
            dynamic_geometry_policy="momentum_exhaustion",
        ),
        config,
    )
    eurjpy_decision = evaluate_selector_v4_admission(
        _event(
            symbol="EURJPY",
            route_session="tokyo",
            origin_family="origin_displacement_continuation",
            dynamic_geometry_policy="momentum_exhaustion",
        ),
        config,
    )
    gbpjpy_decision = evaluate_selector_v4_admission(
        _event(
            symbol="GBPJPY",
            route_session="tokyo",
            origin_family="origin_session_open_range_break",
            dynamic_geometry_policy="momentum_exhaustion",
        ),
        config,
    )
    audjpy_decision = evaluate_selector_v4_admission(
        _event(
            symbol="AUDJPY",
            route_session="tokyo",
            origin_family="origin_session_open_range_break",
            dynamic_geometry_policy="momentum_exhaustion",
        ),
        config,
    )

    assert ethusd_decision.action == "trade"
    assert eurjpy_decision.action == "trade"
    assert gbpjpy_decision.action == "reject"
    assert audjpy_decision.action == "trade"
    assert not ethusd_decision.hard_reject_reasons
    assert not eurjpy_decision.hard_reject_reasons


def test_selector_v4_symbol_specific_guard_can_scope_to_side():
    config = _config(
        selector_v4_admission_quality_guard_enabled=True,
        selector_v4_admission_quality_blocked_session_origin_symbols=[
            {
                "route_session": "off_configured_session",
                "origin_families": ["origin_displacement_continuation"],
                "symbols": ["ETHUSD"],
                "sides": ["SHORT"],
                "reason": "admission_quality_broad_dynamic_accepted_loss_symbol_family_blocked",
            },
        ],
    )

    long_decision = evaluate_selector_v4_admission(
        _event(
            symbol="ETHUSD",
            side="LONG",
            route_session="off_configured_session",
            origin_family="origin_displacement_continuation",
            dynamic_geometry_policy="momentum_exhaustion",
        ),
        config,
    )
    short_decision = evaluate_selector_v4_admission(
        _event(
            symbol="ETHUSD",
            side="SHORT",
            route_session="off_configured_session",
            origin_family="origin_displacement_continuation",
            dynamic_geometry_policy="momentum_exhaustion",
        ),
        config,
    )

    assert long_decision.action == "trade"
    assert short_decision.action == "reject"
    assert (
        short_decision.to_record()["field_group_statuses"]["admission_quality"]["side"]
        == "short"
    )


def test_selector_v4_exact_broad_dynamic_rules_can_be_diagnostic_only():
    decision = evaluate_selector_v4_admission(
        _event(
            symbol="EURGBP",
            route_session="off_configured_session",
            origin_family="origin_displacement_continuation",
            dynamic_geometry_policy="momentum_exhaustion",
        ),
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_admission_quality_exact_block_rules_mode="diagnostic",
            selector_v4_admission_quality_blocked_session_origin_symbols=[
                {
                    "route_session": "off_configured_session",
                    "origin_families": ["origin_displacement_continuation"],
                    "symbols": ["EURGBP"],
                    "reason": "admission_quality_broad_dynamic_accepted_loss_symbol_family_blocked",
                }
            ],
        ),
    )
    record = decision.to_record()
    admission = record["field_group_statuses"]["admission_quality"]

    assert decision.action == "trade"
    assert not decision.hard_reject_reasons
    assert admission["exact_block_rules_mode"] == "diagnostic"
    assert (
        "admission_quality_broad_dynamic_accepted_loss_symbol_family_blocked"
        in admission["diagnostic_reasons"]
    )


def test_selector_v4_generalized_calibrated_admission_rejects_low_expected_net():
    decision = evaluate_selector_v4_admission(
        _event(
            fill_probability=0.80,
            source_completeness=0.95,
            selected_cell={
                "selected_cell_id": "weak_net_fixture",
                "broker_net_expectancy_r": 0.09,
                "stress_expectancy_r": 0.08,
                "risk_pct": 0.25,
                "rows": 64,
                "source_completeness": 0.94,
                "evidence_class": "source_bound_design_fixture",
                "source_status": "broker_net_design_fixture",
            },
        ),
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_calibrated_admission_enabled=True,
            selector_v4_calibrated_min_expected_net_r=0.10,
            selector_v4_calibrated_min_probability=0.58,
            selector_v4_calibrated_min_fill_probability=0.45,
            selector_v4_calibrated_min_source_completeness=0.65,
        ),
    )
    admission = decision.to_record()["field_group_statuses"]["admission_quality"]

    assert decision.action == "reject"
    assert (
        "calibrated_admission_expected_net_r_below_generalized_floor"
        in decision.hard_reject_reasons
    )
    assert admission["calibrated_admission_enabled"] is True


def test_selector_v4_generalized_calibrated_admission_rejects_low_probability():
    decision = evaluate_selector_v4_admission(
        _event(
            fill_probability=0.80,
            source_completeness=0.95,
            probability_debate={
                "selected_action": "long",
                "theses": _theses(long=_thesis(probability=0.54)),
            },
        ),
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_calibrated_admission_enabled=True,
            selector_v4_calibrated_min_probability=0.58,
        ),
    )

    assert decision.action == "reject"
    assert (
        "calibrated_admission_probability_below_generalized_floor"
        in decision.hard_reject_reasons
    )


def test_selector_v4_generalized_calibrated_admission_uses_fill_when_present():
    decision = evaluate_selector_v4_admission(
        _event(fill_probability=0.30, source_completeness=0.95),
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_calibrated_admission_enabled=True,
            selector_v4_calibrated_min_fill_probability=0.45,
        ),
    )

    assert decision.action == "reject"
    assert (
        "calibrated_admission_fill_probability_below_generalized_floor"
        in decision.hard_reject_reasons
    )


def test_selector_v4_generalized_calibrated_admission_rejects_low_source_completeness():
    decision = evaluate_selector_v4_admission(
        _event(fill_probability=0.80, source_completeness=0.40),
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_calibrated_admission_enabled=True,
            selector_v4_calibrated_min_source_completeness=0.65,
        ),
    )

    assert decision.action == "reject"
    assert (
        "calibrated_admission_source_completeness_below_generalized_floor"
        in decision.hard_reject_reasons
    )


def test_selector_v4_consumes_wave3_numeric_confluence_packet_shape():
    event = _event(
        numeric_confluence={
            "sources": [
                {
                    "source_id": "follow-row",
                    "categorical_label": "FOLLOW",
                    "direction": "LONG",
                    "strength": 0.82,
                    "confidence": 0.80,
                    "reliability_history": {
                        "status": "reliability_metric_present",
                        "reliability_score": 1.0,
                    },
                    "freshness": {
                        "status": "timestamp_present",
                        "freshness_score": 0.99,
                    },
                    "source_completeness": {
                        "status": "complete",
                        "score": 1.0,
                    },
                    "cost_sensitivity": {
                        "status": "cost_and_stress_metrics_present",
                        "cost_sensitivity_score": 0.08,
                    },
                    "conflict_reason": "source_pressure_supports_direction_not_trade_permission",
                    "avoid_invalidation_type": None,
                    "evidence_class": "source_bound_runtime_evidence",
                    "follow_is_trade_permission": False,
                }
            ]
        }
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(selector_v4_required_confluence_source_families=["selector"]),
    )

    assert decision.action == "trade"
    assert decision.source_required_fields == ()
    confluence = decision.component_scores["numeric_confluence"]
    assert confluence["source_scores"][0]["label"] == "FOLLOW"
    assert confluence["source_scores"][0]["source_family"] == "selector"
    assert confluence["average_source_completeness"] == 1.0


def test_selector_v4_missing_required_market_state_confluence_family_is_source_required():
    event = _event(
        numeric_confluence={
            "sources": [
                source
                for source in _required_confluence_sources()
                if source["source_family"] != "market_state"
            ]
        }
    )

    decision = evaluate_selector_v4_admission(event, _config())

    assert decision.action == "source-required"
    assert (
        "numeric_confluence.required_source_families.market_state"
        in decision.source_required_fields
    )
    confluence = decision.component_scores["numeric_confluence"]
    assert confluence["missing_required_source_families"] == ["market_state"]
    assert "market_state" not in confluence["present_source_families"]


def test_selector_v4_rejects_future_result_confluence_evidence_as_source():
    event = _event(
        numeric_confluence={
            "sources": [
                *[
                    source
                    for source in _required_confluence_sources()
                    if source["source_family"] != "selector"
                ],
                _follow_source(
                    "selector-future-result",
                    source_family="selector",
                    evidence_class="post_decision_outcome_final_r_result_row",
                ),
            ]
        }
    )

    decision = evaluate_selector_v4_admission(event, _config())
    confluence = decision.component_scores["numeric_confluence"]

    assert decision.action == "source-required"
    assert "selector" not in confluence["present_source_families"]
    assert "selector" in confluence["missing_required_source_families"]
    assert confluence["source_scores"][-1]["source_contract_status"] == (
        "source_contract_violation"
    )
    assert any(
        "evidence_class_contract_violation" in field
        for field in decision.source_required_fields
    )


def test_selector_v4_rejects_future_result_probability_thesis_evidence():
    event = _event(
        probability_debate={
            "selected_action": "long",
            "theses": _theses(
                long=_thesis(
                    ev=0.80,
                    probability=0.92,
                    uncertainty=0.05,
                )
                | {"evidence_class": "validation_result_outcome_exact_r"}
            ),
        }
    )

    decision = evaluate_selector_v4_admission(event, _config())
    probability = decision.component_scores["probability_debate"]

    assert decision.action == "source-required"
    assert probability["candidate_thesis"]["source_contract_status"] == (
        "source_contract_violation"
    )
    assert any(
        field.startswith("probability_debate.theses.long.evidence_class_contract_violation")
        for field in decision.source_required_fields
    )


def test_selector_v4_rejects_future_result_selected_cell_evidence():
    event = _event(
        selected_cell={
            **_event()["selected_cell"],
            "evidence_class": "actual_exact_r_result_row",
        }
    )

    decision = evaluate_selector_v4_admission(event, _config())
    broker_net = decision.component_scores["broker_net_selected_cell"]

    assert decision.action == "source-required"
    assert broker_net["source_contract_status"] == "source_contract_violation"
    assert any(
        field.startswith("selected_cell.evidence_class_contract_violation")
        for field in decision.source_required_fields
    )


def test_selector_v4_allows_negated_broker_real_cash_proxy_cost_label():
    event = _event(cost={**_event()["cost"], "evidence_class": "proxy cost not broker-real cash"})

    decision = evaluate_selector_v4_admission(event, _config())
    cost = decision.component_scores["cost"]

    assert decision.action == "trade"
    assert cost["source_contract_status"] == "predecision_source_allowed"
    assert cost["source_contract_violation"] is None


def test_selector_v4_rejects_proxy_cost_authority_even_if_numeric_cost_passes():
    event = _event(
        cost={
            **_event()["cost"],
            "cost_authority": "timewarp_candidate_cost_proxy",
            "candidate_cost_r_fallback_is_authority": True,
        }
    )

    decision = evaluate_selector_v4_admission(event, _config())
    cost = decision.component_scores["cost"]

    assert decision.action == "reject"
    assert cost["cost_authority_block_reason"] == (
        "broker_net_cost_authority_not_executable:timewarp_candidate_cost_proxy"
    )
    assert any(
        reason == "broker_net_cost_authority_not_executable:timewarp_candidate_cost_proxy"
        for reason in decision.hard_reject_reasons
    )


def test_selector_v4_accepts_nested_broker_cost_packet_total_and_authority():
    event = _event(
        cost={
            "source_completeness": 0.95,
            "evidence_class": "pretrade_cost_design_fixture",
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
                "cost_source_gap_status": "source_bound_cost_authority_present",
                "candidate_cost_r_fallback_is_authority": False,
                "total_cost_r": 0.03,
            },
        }
    )

    decision = evaluate_selector_v4_admission(event, _config())
    cost = decision.component_scores["cost"]

    assert decision.action == "trade"
    assert cost["expected_total_cost_r"] == 0.03
    assert cost["cost_authority"] == "broker_calibrated_replay_cost"
    assert cost["cost_authority_block_reason"] is None
    assert "cost.expected_total_cost_r" not in cost["missing_fields"]


def test_selector_v4_rejects_refused_broker_net_pretrade_cost_packet():
    event = _event(
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "REFUSED",
                "refusal_reasons": [
                    "total_cost_r_exceeds_limit:0.197272>0.150000",
                ],
            },
        }
    )

    decision = evaluate_selector_v4_admission(event, _config())
    cost = decision.component_scores["cost"]

    assert decision.action == "reject"
    assert cost["pretrade_cost_packet_refused"] is True
    assert any(
        reason.startswith("broker_net_pretrade_cost_packet_refused")
        for reason in decision.hard_reject_reasons
    )


def test_selector_v4_rejects_flat_replay_refused_cost_packet():
    event = _event(
        cost=None,
        broker_calibrated_expected_cost_r=0.31,
        expected_cost_r=0.31,
        pretrade_cost_packet_status="REFUSED",
        pretrade_cost_refusal_reasons=[
            "total_cost_r_exceeds_limit:0.310000>0.150000"
        ],
        cost_source_completeness=0.95,
        cost_evidence_class="pretrade_cost_design_fixture",
    )

    decision = evaluate_selector_v4_admission(event, _config())
    cost = decision.component_scores["cost"]

    assert decision.action == "reject"
    assert cost["status"] == "cost_model_scored"
    assert cost["expected_total_cost_r"] == 0.31
    assert cost["pretrade_cost_packet_refused"] is True
    assert cost["pretrade_cost_refusal_reasons"] == [
        "total_cost_r_exceeds_limit:0.310000>0.150000"
    ]
    assert any(
        reason.startswith("broker_net_pretrade_cost_packet_refused")
        for reason in decision.hard_reject_reasons
    )


def test_selector_v4_canonical_reject_reason_prioritizes_cost_over_router_refusal():
    event = _event(
        moonshot_dynamic_execution_router_v4={
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "decision_status": "refuse_live_use_until_source_or_scope_repaired",
            "candidate_action": "ACTIVATED_CANDIDATE_HELD_FOR_SOURCE_OR_BRANCH_REPAIR",
        },
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "REFUSED",
                "refusal_reasons": [
                    "total_cost_r_exceeds_limit:0.197272>0.150000",
                ],
            },
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
        ),
    )

    assert decision.action == "reject"
    assert decision.reason.startswith("broker_net_pretrade_cost_packet_refused")
    assert (
        "admission_quality_dynamic_router_refused_candidate_use"
        in decision.hard_reject_reasons
    )
    assert any(
        reason.startswith("broker_net_pretrade_cost_packet_refused")
        for reason in decision.hard_reject_reasons
    )


def test_selector_v4_package_admission_keeps_cost_packet_refusal_hard_reject():
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.82,
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "REFUSED",
                "refusal_reasons": [
                    "total_cost_r_exceeds_limit:0.197272>0.150000",
                ],
            },
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )
    package = decision.component_scores["ultimate_candidate_package"]

    assert package["source_bound_package_candidate_use_allowed"] is True
    assert package["admission_sleeve_match_count"] > 0
    assert decision.action == "reject"
    assert any(
        reason.startswith("broker_net_pretrade_cost_packet_refused")
        for reason in decision.hard_reject_reasons
    )
    assert not any(
        reason.startswith("ultimate_candidate_package_soft_admission:")
        for reason in decision.reduced_risk_reasons
    )


def test_selector_v4_package_admission_keeps_negative_ev_after_cost_hard_reject():
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.82,
        cost={
            **_event()["cost"],
            "expected_total_cost_r": 0.35,
            "pretrade_broker_net_cost_packet": {
                "status": "REFUSED",
                "refusal_reasons": [
                    "total_cost_r_exceeds_limit:0.350000>0.150000",
                ],
            },
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    assert decision.action == "reject"
    assert "broker_net_admission_ev_negative_after_cost" in decision.hard_reject_reasons


def test_selector_v4_does_not_double_charge_cost_against_broker_net_ev():
    event = _event(
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 0.25,
            "stress_expectancy_r": 0.22,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=0.32, probability=0.72)),
        },
        cost={
            **_event()["cost"],
            "expected_total_cost_r": 0.25,
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(selector_v4_max_expected_cost_r=0.40),
    )

    assert "broker_net_admission_ev_negative_after_cost" not in decision.hard_reject_reasons
    assert decision.action == "reduce-risk"
    assert decision.reason == "broker_net_admission_ev_below_full_trade_floor"
    assert decision.component_scores["broker_net_admission_ev_r"] == 0.07
    assert decision.component_scores["broker_net_admission_ev_components"] == [
        {"source": "broker_net_expectancy_r", "net_ev_r": 0.25},
        {"source": "stress_expectancy_r", "net_ev_r": 0.22},
        {"source": "probability_thesis_ev_after_cost", "net_ev_r": 0.07},
    ]


def test_selector_v4_below_full_trade_floor_package_open_reduced_has_authority():
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        route_session="off_configured_session",
        dynamic_geometry_policy="momentum_exhaustion",
        decision_time_utc="2026-05-05T06:15:00Z",
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 0.25,
            "stress_expectancy_r": 0.22,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=0.32, probability=0.72)),
        },
        cost={
            **_event()["cost"],
            "expected_total_cost_r": 0.25,
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        source_completeness=1.0,
        source_window_complete=True,
        fill_probability=0.82,
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_max_expected_cost_r=0.40,
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_replay_admission_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_live_activation_allowed=False,
            ultimate_candidate_package_final_package_selected=False,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
            ultimate_candidate_package_broker_net_gradient_open_reduced_risk_enabled=True,
        ),
    )

    authority = decision.component_scores[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ]
    assert decision.action == "open-reduced-risk"
    assert decision.reason == "broker_net_admission_ev_below_full_trade_floor"
    assert authority["applies"] is True
    assert authority["allowed"] is True
    assert authority["authority_family"] == "broker_net_admission_gradient"
    assert authority["broker_net_gradient_open_reduced_pre_allowed"] is True
    assert authority["ultimate_package_replay_admission_enabled"] is True
    assert authority["ultimate_package_apply_to_execution"] is True


def test_selector_v4_below_full_trade_floor_package_defaults_to_reduce_risk():
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        route_session="off_configured_session",
        dynamic_geometry_policy="momentum_exhaustion",
        decision_time_utc="2026-05-05T06:15:00Z",
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 0.25,
            "stress_expectancy_r": 0.22,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=0.32, probability=0.72)),
        },
        cost={
            **_event()["cost"],
            "expected_total_cost_r": 0.25,
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        source_completeness=1.0,
        source_window_complete=True,
        fill_probability=0.82,
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_max_expected_cost_r=0.40,
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_replay_admission_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_live_activation_allowed=False,
            ultimate_candidate_package_final_package_selected=False,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    open_authority = decision.component_scores[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ]
    reduce_authority = decision.component_scores[
        "ultimate_candidate_package_reduce_risk_authority"
    ]
    assert decision.action == "reduce-risk"
    assert decision.reason == "broker_net_admission_ev_below_full_trade_floor"
    assert open_authority["applies"] is False
    assert open_authority["broker_net_gradient_open_reduced_pre_allowed"] is False
    assert reduce_authority["applies"] is True
    assert reduce_authority["allowed"] is True
    assert reduce_authority["authority_family"] == "broker_net_admission_gradient"


def test_selector_v4_dynamic_router_refusal_can_reduce_risk_for_replay_package():
    event = _event(
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        }
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reduce-risk",
        ),
    )

    assert decision.action == "reduce-risk"
    assert (
        "admission_quality_dynamic_router_refused_candidate_use"
        in decision.reduced_risk_reasons
    )
    assert (
        "admission_quality_dynamic_router_refused_candidate_use"
        not in decision.hard_reject_reasons
    )


def test_selector_v4_dynamic_router_refusal_can_open_reduced_when_configured():
    event = _event(
        moonshot_dynamic_execution_router_v4={
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "decision_status": "refuse_live_use_until_source_or_scope_repaired",
            "candidate_action": "ACTIVATED_CANDIDATE_HELD_FOR_SOURCE_OR_BRANCH_REPAIR",
        }
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="open-reduced-risk",
        ),
    )

    assert decision.action == "open-reduced-risk"
    assert (
        decision.reason
        == "admission_quality_dynamic_router_refusal_open_reduced_risk_configured"
    )
    assert (
        "admission_quality_dynamic_router_refusal_open_reduced_risk_configured"
        in decision.reduced_risk_reasons
    )
    assert (
        "admission_quality_dynamic_router_refused_candidate_use"
        not in decision.hard_reject_reasons
    )


def test_selector_v4_package_positive_router_refusal_softens_to_reduce_risk_by_default() -> None:
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        **_signed_package_new_entry_authority(
            expected_net_r=1.2,
            probability=0.92,
            fill_probability=0.92,
            source_completeness=1.0,
        ),
        fill_probability=0.92,
        predecision_limit_fillability={
            "available": True,
            "fill_probability": 0.92,
            "expected_fill_probability": 0.92,
        },
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.2,
            "stress_expectancy_r": 1.1,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.2, probability=0.92)),
        },
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
        selected_policy_expected_net_calibration_status="calibrated",
        selected_policy_expected_net_calibration_source=(
            "selected_policy_replay_calibration_packet"
        ),
        selected_policy_expected_net_calibration_source_boundary=(
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    assert decision.action == "reduce-risk"
    assert (
        "admission_quality_dynamic_router_refused_candidate_use"
        not in decision.hard_reject_reasons
    )
    assert (
        "ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk"
        in decision.reduced_risk_reasons
    )
    assert decision.component_scores[
        "ultimate_candidate_package_router_refusal_release"
    ]["open_reduced_risk_allowed"] is False
    assert decision.runtime_effect_now is False


def test_selector_v4_package_router_refusal_softening_honors_origin_family_allowlist() -> None:
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.92,
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.2,
            "stress_expectancy_r": 1.1,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.2, probability=0.92)),
        },
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
        selected_policy_expected_net_calibration_status="calibrated",
        selected_policy_expected_net_calibration_source=(
            "selected_policy_replay_calibration_packet"
        ),
        selected_policy_expected_net_calibration_source_boundary=(
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_dynamic_router_refusal_enabled=True,
            ultimate_candidate_package_dynamic_router_refusal_softening_allowed_origin_families=[
                "structural_distance_extreme",
                "session_open_range_break",
            ],
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    release = decision.component_scores[
        "ultimate_candidate_package_router_refusal_release"
    ]
    assert decision.action == "reject"
    assert (
        "admission_quality_dynamic_router_refused_candidate_use"
        in decision.hard_reject_reasons
    )
    assert (
        "ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk"
        not in decision.reduced_risk_reasons
    )
    assert release["origin_family"] == "volatility_compression_expansion"
    assert release["allowed_origin_families"] == [
        "structural_distance_extreme",
        "session_open_range_break",
    ]
    assert release["origin_family_allowed"] is False
    assert release["softening_allowed"] is False


def test_selector_v4_source_bound_router_refusal_materializes_without_origin_allowlist() -> None:
    event = _event(
        candidate_id="broadorigin_7a88c86edf0da97f2506af7f",
        symbol="USDCAD",
        side="LONG",
        origin_family="origin_current_ob_retest",
        current_framework="ob_retest",
        framework="ob_retest",
        decision_time_utc="2026-06-02T09:30:00+00:00",
        fill_probability=0.95,
        predecision_limit_fillability=_predecision_limit_fillability(
            0.92,
            decision_time_utc="2026-06-02T09:30:00+00:00",
            expected_fill_probability=0.92,
        ),
        cost={
            **_event()["cost"],
            "expected_total_cost_r": 0.09479054,
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
                "cost_source_gap_status": "source_bound_cost_authority_present",
                "candidate_cost_r_fallback_is_authority": False,
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.223647613641,
            "stress_expectancy_r": 1.10,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(
                long=_thesis(ev=1.223647613641, probability=0.9339424935)
            ),
        },
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
        selected_policy_expected_net_calibration_status="calibrated",
        selected_policy_expected_net_calibration_source=(
            "selected_policy_replay_calibration_packet"
        ),
        selected_policy_expected_net_calibration_source_boundary=(
            "owner_approved_reconstructed_replay_predecision_selected_policy_"
            "expected_net_no_outcome_fields_local_replay_final_closed_no_broker_"
            "order_mutation"
        ),
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            selector_v4_router_refusal_expected_net_policy_calibration_required=True,
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_replay_admission_enabled=True,
            ultimate_candidate_package_apply_to_execution=False,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_dynamic_router_refusal_enabled=True,
            ultimate_candidate_package_dynamic_router_refusal_softening_allowed_origin_families=[
                "fvg_fill",
                "breaker_re_entry",
            ],
            ultimate_candidate_package_source_bound_router_refusal_open_reduced_materialization_enabled=True,
            ultimate_candidate_package_source_bound_router_refusal_materialization_min_expected_net_r=0.55,
            ultimate_candidate_package_source_bound_router_refusal_materialization_min_probability=0.70,
            ultimate_candidate_package_source_bound_router_refusal_materialization_min_fill_probability=0.80,
            ultimate_candidate_package_source_bound_router_refusal_materialization_min_source_completeness=0.95,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
            ultimate_candidate_package_live_activation_allowed=False,
            ultimate_candidate_package_final_package_selected=False,
        ),
    )

    release = decision.component_scores[
        "ultimate_candidate_package_router_refusal_release"
    ]
    authority = decision.component_scores[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ]
    assert decision.action == "open-reduced-risk"
    assert decision.reason == (
        "source_bound_router_refusal_open_reduced_materialized_for_replay"
    )
    assert (
        "admission_quality_dynamic_router_refused_candidate_use"
        not in decision.hard_reject_reasons
    )
    assert release["origin_family"] == "ob_retest"
    assert release["origin_family_allowed"] is False
    assert release["source_bound_router_refusal_authority_allowed"] is True
    assert release["source_bound_open_reduced_materialization_allowed"] is True
    assert release["source_bound_materialization_fill_probability"] == 0.92
    assert release["execution_fill_probability"] == 0.92
    assert authority["allowed"] is True
    assert authority["authority_family"] == "router_refusal_softening"
    assert authority["source_bound_router_refusal_authority_allowed"] is True
    assert decision.replay_candidate_use_allowed_now is True
    assert decision.live_activation_allowed_by_config is False


def test_selector_v4_source_bound_router_refusal_respects_execution_fill_floor() -> None:
    event = _event(
        candidate_id="broadorigin_7a88c86edf0da97f2506af7f",
        symbol="USDCAD",
        side="LONG",
        origin_family="origin_current_ob_retest",
        current_framework="ob_retest",
        framework="ob_retest",
        decision_time_utc="2026-06-02T09:30:00+00:00",
        fill_probability=0.95,
        predecision_limit_fillability=_predecision_limit_fillability(
            0.557568388,
            decision_time_utc="2026-06-02T09:30:00+00:00",
            expected_fill_probability=0.557568388,
        ),
        cost={
            **_event()["cost"],
            "expected_total_cost_r": 0.09479054,
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
                "cost_source_gap_status": "source_bound_cost_authority_present",
                "candidate_cost_r_fallback_is_authority": False,
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.223647613641,
            "stress_expectancy_r": 1.10,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(
                long=_thesis(ev=1.223647613641, probability=0.9339424935)
            ),
        },
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
        selected_policy_expected_net_calibration_status="calibrated",
        selected_policy_expected_net_calibration_source=(
            "selected_policy_replay_calibration_packet"
        ),
        selected_policy_expected_net_calibration_source_boundary=(
            "owner_approved_reconstructed_replay_predecision_selected_policy_"
            "expected_net_no_outcome_fields_local_replay_final_closed_no_broker_"
            "order_mutation"
        ),
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            selector_v4_router_refusal_expected_net_policy_calibration_required=True,
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_replay_admission_enabled=True,
            ultimate_candidate_package_apply_to_execution=False,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_dynamic_router_refusal_enabled=True,
            ultimate_candidate_package_dynamic_router_refusal_softening_allowed_origin_families=[
                "fvg_fill",
                "breaker_re_entry",
            ],
            ultimate_candidate_package_source_bound_router_refusal_open_reduced_materialization_enabled=True,
            ultimate_candidate_package_source_bound_router_refusal_materialization_min_expected_net_r=0.55,
            ultimate_candidate_package_source_bound_router_refusal_materialization_min_probability=0.70,
            ultimate_candidate_package_source_bound_router_refusal_materialization_min_fill_probability=0.80,
            ultimate_candidate_package_source_bound_router_refusal_materialization_min_source_completeness=0.95,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
            ultimate_candidate_package_live_activation_allowed=False,
            ultimate_candidate_package_final_package_selected=False,
        ),
    )

    release = decision.component_scores[
        "ultimate_candidate_package_router_refusal_release"
    ]
    assert decision.action == "reject"
    assert (
        "admission_quality_dynamic_router_refused_candidate_use"
        in decision.hard_reject_reasons
    )
    assert release["source_bound_router_refusal_authority_allowed"] is True
    assert release["source_bound_materialization_quality_allowed"] is False
    assert release["source_bound_open_reduced_materialization_allowed"] is False
    assert release["source_bound_materialization_fill_probability"] == 0.557568388
    assert release["execution_fill_probability"] == 0.557568388
    assert release["entry_quality_fill_probability"] == 0.95


def test_selector_v4_package_router_refusal_softening_allows_configured_origin_family() -> None:
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="origin_volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.92,
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.2,
            "stress_expectancy_r": 1.1,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.2, probability=0.92)),
        },
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
        predecision_limit_fillability={
            "fill_probability": 0.91,
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_dynamic_router_refusal_enabled=True,
            ultimate_candidate_package_dynamic_router_refusal_softening_allowed_origin_families=[
                "origin_volatility_compression_expansion"
            ],
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    release = decision.component_scores[
        "ultimate_candidate_package_router_refusal_release"
    ]
    assert decision.action == "reduce-risk"
    assert (
        "admission_quality_dynamic_router_refused_candidate_use"
        not in decision.hard_reject_reasons
    )
    assert (
        "ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk"
        in decision.reduced_risk_reasons
    )
    assert release["origin_family"] == "volatility_compression_expansion"
    assert release["allowed_origin_families"] == ["volatility_compression_expansion"]
    assert release["origin_family_allowed"] is True
    assert release["softening_allowed"] is True


def test_selector_v4_package_router_refusal_normalizes_current_origin_aliases() -> None:
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="origin_current_fvg_fill",
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.92,
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.2,
            "stress_expectancy_r": 1.1,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.2, probability=0.92)),
        },
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
        predecision_limit_fillability={
            "fill_probability": 0.91,
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_replay_admission_enabled=True,
            ultimate_candidate_package_apply_to_execution=False,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_dynamic_router_refusal_enabled=True,
            ultimate_candidate_package_dynamic_router_refusal_softening_allowed_origin_families=[
                "fvg_fill",
            ],
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    release = decision.component_scores[
        "ultimate_candidate_package_router_refusal_release"
    ]
    assert release["origin_family"] == "fvg_fill"
    assert release["origin_family_candidates"] == ["fvg_fill", "current_fvg_fill"]
    assert release["origin_family_raw_candidates"] == ["current_fvg_fill"]
    assert release["allowed_origin_families"] == ["fvg_fill"]
    assert release["origin_family_allowed"] is True
    assert decision.action == "reject"
    assert "ultimate_candidate_package_no_shadow_sleeve_match" in decision.hard_reject_reasons


def test_selector_v4_package_router_refusal_current_alias_stays_disallowed_when_not_configured() -> None:
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="origin_current_ob_retest",
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.92,
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.2,
            "stress_expectancy_r": 1.1,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.2, probability=0.92)),
        },
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_replay_admission_enabled=True,
            ultimate_candidate_package_apply_to_execution=False,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_dynamic_router_refusal_enabled=True,
            ultimate_candidate_package_dynamic_router_refusal_softening_allowed_origin_families=[
                "fvg_fill",
                "breaker_re_entry",
            ],
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    release = decision.component_scores[
        "ultimate_candidate_package_router_refusal_release"
    ]
    assert release["origin_family"] == "ob_retest"
    assert release["origin_family_candidates"] == ["ob_retest", "current_ob_retest"]
    assert release["origin_family_raw_candidates"] == ["current_ob_retest"]
    assert release["origin_family_allowed"] is False
    assert decision.action == "reject"


def test_selector_v4_package_router_refusal_softening_uses_signed_sleeve_origin_when_candidate_origin_missing() -> None:
    event = _event(
        symbol="GBPJPY",
        side="LONG",
        framework="broader_origin",
        origin_family=None,
        candidate_origin_family=None,
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.92,
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.2,
            "stress_expectancy_r": 1.1,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.2, probability=0.92)),
        },
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
        candidate_decision_quality_alias_status="materialized",
        candidate_decision_quality_source_boundary=(
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        candidate_decision_quality_field_sources={
            "expected_net_r": "unit_test.predecision.expected_net_r",
            "probability": "unit_test.predecision.probability",
            "fill_probability": "unit_test.predecision.fill_probability",
            "source_completeness": "unit_test.predecision.source_completeness",
        },
        ultimate_package_matched_sleeve_ids=[
            "fpsc_scheduler_lifecycle_merge_sleeve__broader_origin__session_open_range_break__long"
        ],
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_dynamic_router_refusal_enabled=True,
            ultimate_candidate_package_dynamic_router_refusal_softening_allowed_origin_families=[
                "session_open_range_break"
            ],
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    release = decision.component_scores[
        "ultimate_candidate_package_router_refusal_release"
    ]
    assert decision.action == "reduce-risk"
    assert (
        "admission_quality_dynamic_router_refused_candidate_use"
        not in decision.hard_reject_reasons
    )
    assert (
        "ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk"
        in decision.reduced_risk_reasons
    )
    assert release["origin_family"] == "session_open_range_break"
    assert release["origin_family_candidates"] == ["session_open_range_break"]
    assert release["package_sleeve_origin_families"] == ["session_open_range_break"]
    assert release["origin_family_allowed"] is True
    assert release["softening_allowed"] is True
    assert release["softening_allowed"] is True


def test_selector_v4_package_router_refusal_accepts_structured_sleeve_payloads() -> None:
    event = _event(
        symbol="GBPJPY",
        side="LONG",
        framework="broader_origin",
        origin_family=None,
        candidate_origin_family=None,
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.92,
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.2,
            "stress_expectancy_r": 1.1,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.2, probability=0.92)),
        },
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
        candidate_decision_quality_alias_status="materialized",
        candidate_decision_quality_source_boundary=(
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        candidate_decision_quality_field_sources={
            "expected_net_r": "unit_test.predecision.expected_net_r",
            "probability": "unit_test.predecision.probability",
            "confidence": "unit_test.predecision.confidence",
            "fill_probability": "unit_test.predecision.fill_probability",
            "source_completeness": "unit_test.predecision.source_completeness",
        },
        ultimate_package_matched_sleeve_ids=[
            {
                "id": (
                    "fpsc_scheduler_lifecycle_merge_sleeve__broader_origin__"
                    "session_open_range_break__long"
                )
            }
        ],
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_dynamic_router_refusal_enabled=True,
            ultimate_candidate_package_dynamic_router_refusal_softening_allowed_origin_families=[
                "session_open_range_break"
            ],
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    release = decision.component_scores[
        "ultimate_candidate_package_router_refusal_release"
    ]
    assert decision.action == "reduce-risk"
    assert release["package_sleeve_origin_families"] == ["session_open_range_break"]
    assert release["origin_family"] == "session_open_range_break"
    assert release["origin_family_allowed"] is True
    assert release["softening_allowed"] is True


def test_selector_v4_package_router_refusal_requires_scalar_sleeve_or_origin_family() -> None:
    event = _event(
        symbol="GBPJPY",
        side="LONG",
        framework="broader_origin",
        origin_family=None,
        candidate_origin_family=None,
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.92,
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.2,
            "stress_expectancy_r": 1.1,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.2, probability=0.92)),
        },
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
        candidate_decision_quality_alias_status="materialized",
        candidate_decision_quality_source_boundary=(
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        candidate_decision_quality_field_sources={
            "expected_net_r": "unit_test.predecision.expected_net_r",
            "probability": "unit_test.predecision.probability",
            "fill_probability": "unit_test.predecision.fill_probability",
            "source_completeness": "unit_test.predecision.source_completeness",
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_dynamic_router_refusal_enabled=True,
            ultimate_candidate_package_dynamic_router_refusal_softening_allowed_origin_families=[
                "session_open_range_break"
            ],
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    release = decision.component_scores[
        "ultimate_candidate_package_router_refusal_release"
    ]
    assert decision.action == "reject"
    assert release["package_sleeve_origin_families"] == []
    assert release["origin_family"] == "unknown"
    assert release["origin_family_allowed"] is False


def test_selector_v4_package_router_refusal_softening_keeps_unallowed_sleeve_origin_rejected() -> None:
    event = _event(
        symbol="GBPJPY",
        side="LONG",
        framework="broader_origin",
        origin_family=None,
        candidate_origin_family=None,
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.92,
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.2,
            "stress_expectancy_r": 1.1,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.2, probability=0.92)),
        },
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
        candidate_decision_quality_alias_status="materialized",
        candidate_decision_quality_source_boundary=(
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        candidate_decision_quality_field_sources={
            "expected_net_r": "unit_test.predecision.expected_net_r",
            "probability": "unit_test.predecision.probability",
            "fill_probability": "unit_test.predecision.fill_probability",
            "source_completeness": "unit_test.predecision.source_completeness",
        },
        ultimate_package_matched_sleeve_ids=[
            "fpsc_scheduler_lifecycle_merge_sleeve__broader_origin__displacement_continuation__long"
        ],
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_dynamic_router_refusal_enabled=True,
            ultimate_candidate_package_dynamic_router_refusal_softening_allowed_origin_families=[
                "session_open_range_break"
            ],
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    release = decision.component_scores[
        "ultimate_candidate_package_router_refusal_release"
    ]
    assert decision.action == "reject"
    assert (
        "admission_quality_dynamic_router_refused_candidate_use"
        in decision.hard_reject_reasons
    )
    assert release["origin_family"] == "displacement_continuation"
    assert release["origin_family_candidates"] == ["displacement_continuation"]
    assert release["origin_family_allowed"] is False
    assert release["softening_allowed"] is False


def test_selector_v4_package_replay_side_authority_blocks_configured_disallowed_side() -> None:
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.92,
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.2,
            "stress_expectancy_r": 1.1,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.2, probability=0.92)),
        },
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_dynamic_router_refusal_enabled=True,
            ultimate_candidate_package_replay_execution_allowed_sides=["SHORT"],
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    side_authority = decision.component_scores[
        "ultimate_candidate_package_replay_side_authority"
    ]
    assert decision.action == "reject"
    assert (
        "ultimate_candidate_package_side_not_allowed_by_repaired_profile"
        in decision.hard_reject_reasons
    )
    assert side_authority["policy_applies"] is True
    assert side_authority["side"] == "LONG"
    assert side_authority["allowed_sides"] == ["SHORT"]
    assert side_authority["allowed"] is False


def test_selector_v4_package_replay_side_authority_keeps_configured_allowed_side() -> None:
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.92,
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.2,
            "stress_expectancy_r": 1.1,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.2, probability=0.92)),
        },
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_dynamic_router_refusal_enabled=True,
            ultimate_candidate_package_replay_execution_allowed_sides=["LONG"],
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    side_authority = decision.component_scores[
        "ultimate_candidate_package_replay_side_authority"
    ]
    assert decision.action == "reduce-risk"
    assert (
        "ultimate_candidate_package_side_not_allowed_by_repaired_profile"
        not in decision.hard_reject_reasons
    )
    assert (
        "ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk"
        in decision.reduced_risk_reasons
    )
    assert side_authority["policy_applies"] is True
    assert side_authority["side"] == "LONG"
    assert side_authority["allowed_sides"] == ["LONG"]
    assert side_authority["allowed"] is True


def test_selector_v4_package_positive_router_refusal_can_opt_into_open_reduced_risk() -> None:
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        **_signed_package_new_entry_authority(
            expected_net_r=1.2,
            probability=0.92,
            fill_probability=0.92,
            source_completeness=1.0,
        ),
        fill_probability=0.92,
        predecision_limit_fillability={
            "available": True,
            "fill_probability": 0.92,
            "expected_fill_probability": 0.92,
        },
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.2,
            "stress_expectancy_r": 1.1,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.2, probability=0.92)),
        },
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
        selected_policy_expected_net_calibration_status="calibrated",
        selected_policy_expected_net_calibration_source=(
            "selected_policy_replay_calibration_packet"
        ),
        selected_policy_expected_net_calibration_source_boundary=(
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed=True,
            selector_v4_router_refusal_expected_net_policy_calibration_required=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    assert decision.action == "open-reduced-risk"
    assert (
        "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk"
        in decision.reduced_risk_reasons
    )
    assert decision.component_scores[
        "ultimate_candidate_package_router_refusal_release"
    ]["open_reduced_risk_allowed"] is True


def test_selector_v4_source_bound_router_refusal_uses_package_role_authority() -> None:
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.91,
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 0.72,
            "stress_expectancy_r": 0.60,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=0.72, probability=0.74)),
        },
        predecision_limit_fillability=_predecision_limit_fillability(0.91),
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_dynamic_router_refusal_enabled=True,
            ultimate_candidate_package_dynamic_router_refusal_softening_allowed_origin_families=[
                "structural_distance_extreme",
                "session_open_range_break",
            ],
            ultimate_candidate_package_source_bound_router_refusal_open_reduced_materialization_enabled=True,
            ultimate_candidate_package_source_bound_router_refusal_materialization_min_expected_net_r=0.55,
            ultimate_candidate_package_source_bound_router_refusal_materialization_min_probability=0.70,
            ultimate_candidate_package_source_bound_router_refusal_materialization_min_fill_probability=0.80,
            ultimate_candidate_package_source_bound_router_refusal_materialization_min_source_completeness=0.95,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    assert decision.action == "open-reduced-risk"
    assert (
        "admission_quality_dynamic_router_refused_candidate_use"
        not in decision.hard_reject_reasons
    )
    assert (
        "source_bound_router_refusal_open_reduced_materialized_for_replay"
        in decision.reduced_risk_reasons
    )
    authority = decision.component_scores[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ]
    assert authority["allowed"] is True
    release = decision.component_scores[
        "ultimate_candidate_package_router_refusal_release"
    ]
    assert release["source_bound_open_reduced_materialization_allowed"] is True
    assert release["source_bound_materialization_quality_allowed"] is True
    assert release["role_disposition"] == "admission_candidate"
    assert release["source_bound_package_role_materialization_allowed"] is True
    assert release["entry_quality_fill_probability"] == 0.91
    assert release["execution_fill_probability"] == 0.91
    assert release["origin_family_allowed"] is False
    assert decision.runtime_effect_now is False


def test_selector_v4_source_bound_router_refusal_uses_execution_fillability_floor() -> None:
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.93,
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 0.72,
            "stress_expectancy_r": 0.60,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=0.72, probability=0.74)),
        },
        predecision_limit_fillability=_predecision_limit_fillability(0.542466481),
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_dynamic_router_refusal_enabled=True,
            ultimate_candidate_package_dynamic_router_refusal_softening_allowed_origin_families=[
                "structural_distance_extreme",
                "session_open_range_break",
            ],
            ultimate_candidate_package_source_bound_router_refusal_open_reduced_materialization_enabled=True,
            ultimate_candidate_package_source_bound_router_refusal_materialization_min_expected_net_r=0.55,
            ultimate_candidate_package_source_bound_router_refusal_materialization_min_probability=0.70,
            ultimate_candidate_package_source_bound_router_refusal_materialization_min_fill_probability=0.90,
            ultimate_candidate_package_source_bound_router_refusal_materialization_min_source_completeness=0.95,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    assert decision.action == "reject"
    assert (
        "admission_quality_dynamic_router_refused_candidate_use"
        in decision.hard_reject_reasons
    )
    assert (
        "source_bound_router_refusal_open_reduced_materialized_for_replay"
        not in decision.reduced_risk_reasons
    )
    release = decision.component_scores[
        "ultimate_candidate_package_router_refusal_release"
    ]
    assert release["source_bound_open_reduced_materialization_allowed"] is False
    assert release["source_bound_materialization_quality_allowed"] is False
    assert release["entry_quality_fill_probability"] == 0.93
    assert release["execution_fill_probability"] == 0.542466481
    assert release["source_bound_package_role_materialization_allowed"] is True
    assert decision.runtime_effect_now is False


def test_selector_v4_source_bound_router_refusal_blocks_no_sleeve_match_even_allowed_origin_family() -> None:
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="origin_fvg_fill",
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.91,
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 0.72,
            "stress_expectancy_r": 0.60,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=0.72, probability=0.74)),
        },
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_dynamic_router_refusal_enabled=True,
            ultimate_candidate_package_dynamic_router_refusal_softening_allowed_origin_families=[
                "fvg_fill",
            ],
            ultimate_candidate_package_source_bound_router_refusal_open_reduced_materialization_enabled=True,
            ultimate_candidate_package_source_bound_router_refusal_materialization_min_expected_net_r=0.55,
            ultimate_candidate_package_source_bound_router_refusal_materialization_min_probability=0.70,
            ultimate_candidate_package_source_bound_router_refusal_materialization_min_fill_probability=0.80,
            ultimate_candidate_package_source_bound_router_refusal_materialization_min_source_completeness=0.95,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    assert decision.action == "reject"
    assert (
        "admission_quality_dynamic_router_refused_candidate_use"
        in decision.hard_reject_reasons
    )
    assert (
        "source_bound_router_refusal_open_reduced_materialized_for_replay"
        not in decision.reduced_risk_reasons
    )
    authority = decision.component_scores[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ]
    assert authority["allowed"] is False
    release = decision.component_scores[
        "ultimate_candidate_package_router_refusal_release"
    ]
    assert release["source_bound_open_reduced_materialization_allowed"] is False
    assert release["origin_family"] == "fvg_fill"
    assert release["origin_family_allowed"] is True
    assert release["role_disposition"] == "no_sleeve_match"
    assert release["role_disposition_executable"] is True
    assert decision.runtime_effect_now is False


def test_selector_v4_package_replay_admission_softens_router_refusal_default_off() -> None:
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.92,
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.2,
            "stress_expectancy_r": 1.1,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.2, probability=0.92)),
        },
        predecision_limit_fillability=_predecision_limit_fillability(0.92),
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_replay_admission_enabled=True,
            ultimate_candidate_package_apply_to_execution=False,
            ultimate_candidate_package_live_activation_allowed=False,
            ultimate_candidate_package_final_package_selected=False,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    package = decision.component_scores["ultimate_candidate_package"]
    authority = decision.component_scores[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ]
    assert decision.action == "reduce-risk"
    assert package["apply_to_execution"] is False
    assert package["replay_admission_enabled"] is True
    assert package["source_bound_package_candidate_use_allowed"] is True
    assert authority["ultimate_package_replay_admission_enabled"] is True
    assert authority["ultimate_package_apply_to_execution"] is False
    assert (
        "ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk"
        in decision.reduced_risk_reasons
    )
    assert (
        "admission_quality_dynamic_router_refused_candidate_use"
        not in decision.hard_reject_reasons
    )
    assert decision.runtime_effect_now is False
    assert decision.apply_to_execution is False
    assert decision.live_activation_allowed_by_config is False
    assert decision.candidate_use_allowed_now is False
    assert decision.replay_candidate_use_allowed_now is True


def test_selector_v4_package_replay_authority_survives_closed_production_apply_gate() -> None:
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.92,
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.2,
            "stress_expectancy_r": 1.1,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.2, probability=0.92)),
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_replay_admission_enabled=True,
            ultimate_candidate_package_apply_to_execution=False,
            ultimate_candidate_package_live_activation_allowed=False,
            ultimate_candidate_package_final_package_selected=False,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    assert decision.action == "trade"
    assert decision.runtime_effect_now is False
    assert decision.candidate_use_allowed_now is False
    assert decision.source_bound_candidate_use_allowed_now is True
    assert decision.replay_candidate_use_allowed_now is True


def test_selector_v4_package_positive_router_refusal_full_trade_release_is_replay_local() -> None:
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        **_signed_package_new_entry_authority(
            expected_net_r=1.2,
            probability=0.92,
            fill_probability=0.92,
            source_completeness=1.0,
        ),
        fill_probability=0.92,
        predecision_limit_fillability={
            "available": True,
            "fill_probability": 0.92,
            "expected_fill_probability": 0.92,
        },
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.2,
            "stress_expectancy_r": 1.1,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.2, probability=0.92)),
        },
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_positive_predecision_router_refusal_full_trade_allowed=True,
            ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    assert decision.action == "trade"
    assert decision.risk_multiplier == 1.0
    assert (
        "admission_quality_dynamic_router_refused_candidate_use"
        not in decision.hard_reject_reasons
    )
    assert (
        "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk"
        not in decision.reduced_risk_reasons
    )
    release = decision.component_scores["ultimate_candidate_package_router_refusal_release"]
    assert release["full_trade_release_requested"] is True
    assert release["full_trade_release_allowed"] is True
    assert release["full_trade_release_block_reason"] is None
    assert release["full_trade_release_reason"] == (
        "positive_predecision_router_refusal_full_trade_released_by_config_and_quality"
    )
    assert decision.runtime_effect_now is False
    assert decision.candidate_use_allowed_now is False
    assert decision.replay_candidate_use_allowed_now is True


def test_selector_v4_package_router_refusal_softening_stays_reduce_risk_without_stress_edge() -> None:
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.82,
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            key: value
            for key, value in {
                **_event()["selected_cell"],
                "broker_net_expectancy_r": 1.0,
                "stress_expectancy_r": None,
                "source_completeness": 1.0,
            }.items()
            if value is not None
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.1, probability=0.78)),
        },
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_dynamic_router_refusal_enabled=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    assert decision.action == "reduce-risk"
    assert (
        "admission_quality_dynamic_router_refused_candidate_use"
        not in decision.hard_reject_reasons
    )
    assert (
        "ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk"
        in decision.reduced_risk_reasons
    )
    assert decision.runtime_effect_now is False


def test_selector_v4_package_router_softening_does_not_override_cost_refusal() -> None:
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "REFUSED",
                "refusal_reasons": ["total_cost_r_exceeds_limit"],
            },
        },
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.0,
            "stress_expectancy_r": 0.8,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.1, probability=0.78)),
        },
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_source_bound_router_refusal_open_reduced_materialization_enabled=True,
            ultimate_candidate_package_positive_predecision_router_refusal_full_trade_allowed=True,
            ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    assert decision.action == "reject"
    assert any(
        reason.startswith("broker_net_pretrade_cost_packet_refused")
        for reason in decision.hard_reject_reasons
    )
    assert (
        "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk"
        not in decision.reduced_risk_reasons
    )
    release = decision.component_scores["ultimate_candidate_package_router_refusal_release"]
    assert release["full_trade_release_requested"] is False
    assert release["full_trade_release_allowed"] is False


def test_selector_v4_package_router_softening_requires_broker_cost_pass() -> None:
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "SOURCE_GAP",
                "authority": "broker_calibrated_replay_cost",
            },
        },
        selected_cell={
            key: value
            for key, value in {
                **_event()["selected_cell"],
                "broker_net_expectancy_r": 1.0,
                "stress_expectancy_r": None,
            }.items()
            if value is not None
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.1, probability=0.78)),
        },
        moonshot_dynamic_execution_router_v4={
            "decision_status": "refused_candidate_use",
            "candidate_use_allowed_now": False,
            "runtime_effect_now": False,
            "candidate_action": "held_for_source_or_branch_repair",
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_enforce_dynamic_router_refusal=True,
            selector_v4_dynamic_router_refusal_action="reject",
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_dynamic_router_refusal_enabled=True,
            ultimate_candidate_package_soften_dynamic_router_refusal_requires_broker_cost_pass=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    assert decision.action == "reject"
    assert (
        "admission_quality_dynamic_router_refused_candidate_use"
        in decision.hard_reject_reasons
    )
    assert (
        "ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk"
        not in decision.reduced_risk_reasons
    )


def test_selector_v4_calibrated_floor_failure_can_reduce_risk_for_replay_package():
    event = _event(fill_probability=0.20)

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_calibrated_admission_enabled=True,
            selector_v4_calibrated_admission_floor_failure_action="reduce-risk",
            selector_v4_calibrated_min_fill_probability=0.45,
        ),
    )

    assert decision.action == "reduce-risk"
    assert (
        "calibrated_admission_fill_probability_below_generalized_floor"
        in decision.reduced_risk_reasons
    )
    assert (
        "calibrated_admission_fill_probability_below_generalized_floor"
        not in decision.hard_reject_reasons
    )


def test_selector_v4_strong_fill_floor_bypass_is_open_reduced_risk_by_default():
    base_event = _event()
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        **_signed_package_new_entry_authority(),
        fill_probability=0.30,
        candidate_ev_r=1.20,
        selected_cell={
            **base_event["selected_cell"],
            "broker_net_expectancy_r": 1.20,
            "stress_expectancy_r": 1.05,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.20, probability=0.82)),
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_calibrated_admission_enabled=True,
            selector_v4_calibrated_admission_floor_failure_action="reduce-risk",
            selector_v4_calibrated_min_fill_probability=0.45,
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_strong_fill_floor_bypass_enabled=True,
            ultimate_candidate_package_strong_fill_floor_bypass_min_expected_net_r=0.70,
            ultimate_candidate_package_strong_fill_floor_bypass_min_probability=0.70,
            ultimate_candidate_package_strong_fill_floor_bypass_min_fill_probability=0.20,
        ),
    )

    assert decision.action == "open-reduced-risk"
    assert (
        "calibrated_admission_fill_probability_below_generalized_floor"
        in decision.reduced_risk_reasons
    )
    assert (
        "ultimate_candidate_package_fill_floor_bypass_reduce_risk_only"
        in decision.reduced_risk_reasons
    )


def test_selector_v4_strong_fill_floor_bypass_full_trade_requires_explicit_flag():
    base_event = _event()
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        **_signed_package_new_entry_authority(),
        fill_probability=0.30,
        candidate_ev_r=1.20,
        selected_cell={
            **base_event["selected_cell"],
            "broker_net_expectancy_r": 1.20,
            "stress_expectancy_r": 1.05,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.20, probability=0.82)),
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_calibrated_admission_enabled=True,
            selector_v4_calibrated_admission_floor_failure_action="reduce-risk",
            selector_v4_calibrated_min_fill_probability=0.45,
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_strong_fill_floor_bypass_enabled=True,
            ultimate_candidate_package_strong_fill_floor_bypass_full_trade_allowed=True,
            ultimate_candidate_package_strong_fill_floor_bypass_min_expected_net_r=0.70,
            ultimate_candidate_package_strong_fill_floor_bypass_min_probability=0.70,
            ultimate_candidate_package_strong_fill_floor_bypass_min_fill_probability=0.20,
        ),
    )

    assert decision.action == "trade"
    assert (
        "calibrated_admission_fill_probability_below_generalized_floor"
        not in decision.reduced_risk_reasons
    )


def test_selector_v4_package_fill_floor_softening_can_be_disabled():
    base_event = _event()
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.30,
        candidate_ev_r=1.20,
        selected_cell={
            **base_event["selected_cell"],
            "broker_net_expectancy_r": 1.20,
            "stress_expectancy_r": 1.05,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.20, probability=0.82)),
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_calibrated_admission_enabled=True,
            selector_v4_calibrated_admission_floor_failure_action="reject",
            selector_v4_calibrated_min_fill_probability=0.45,
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_selector_fill_floor_enabled=False,
        ),
    )

    assert decision.action == "reject"
    assert (
        "calibrated_admission_fill_probability_below_generalized_floor"
        in decision.hard_reject_reasons
    )
    assert not any(
        reason.startswith("ultimate_candidate_package_soft_admission:")
        for reason in decision.reduced_risk_reasons
    )


def test_selector_v4_package_fill_floor_softening_requires_cost_pass_and_positive_edge():
    base_event = _event()
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        **_signed_package_new_entry_authority(),
        fill_probability=0.30,
        candidate_ev_r=1.20,
        selected_cell={
            **base_event["selected_cell"],
            "broker_net_expectancy_r": 1.20,
            "stress_expectancy_r": 1.05,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.20, probability=0.82)),
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_calibrated_admission_enabled=True,
            selector_v4_calibrated_admission_floor_failure_action="reject",
            selector_v4_calibrated_min_fill_probability=0.45,
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_selector_fill_floor_enabled=True,
            ultimate_candidate_package_soften_selector_fill_floor_requires_broker_cost_pass=True,
            ultimate_candidate_package_soften_selector_fill_floor_requires_positive_predecision_edge=True,
            scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_source_completeness=0.65,
        ),
    )

    assert decision.action == "open-reduced-risk"
    assert (
        "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
        in decision.reduced_risk_reasons
    )
    assert (
        "ultimate_candidate_package_selector_fill_floor_softening_broker_cost_passed"
        in decision.reduced_risk_reasons
    )
    assert (
        "calibrated_admission_fill_probability_below_generalized_floor"
        not in decision.hard_reject_reasons
    )
    open_reduced_authority = decision.component_scores[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ]
    assert open_reduced_authority["applies"] is True
    assert open_reduced_authority["allowed"] is True
    assert open_reduced_authority["authority_family"] == "fill_floor_softening"
    assert open_reduced_authority["broker_cost_passed_for_package_router"] is True
    assert open_reduced_authority["positive_predecision_package_edge"] is True
    assert (
        open_reduced_authority["package_new_entry_signed_authority"]["signed"]
        is True
    )
    reduce_risk_authority = decision.component_scores[
        "ultimate_candidate_package_reduce_risk_authority"
    ]
    assert reduce_risk_authority["applies"] is False


def test_selector_v4_package_fill_floor_softening_requires_signed_package_authority():
    base_event = _event()
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.30,
        candidate_ev_r=1.20,
        selected_cell={
            **base_event["selected_cell"],
            "broker_net_expectancy_r": 1.20,
            "stress_expectancy_r": 1.05,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.20, probability=0.82)),
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_calibrated_admission_enabled=True,
            selector_v4_calibrated_admission_floor_failure_action="reject",
            selector_v4_calibrated_min_fill_probability=0.45,
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_selector_fill_floor_enabled=True,
            ultimate_candidate_package_soften_selector_fill_floor_requires_broker_cost_pass=True,
            ultimate_candidate_package_soften_selector_fill_floor_requires_positive_predecision_edge=True,
            scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_source_completeness=0.65,
        ),
    )

    assert decision.action == "reject"
    assert (
        "calibrated_admission_fill_probability_below_generalized_floor"
        in decision.hard_reject_reasons
    )
    assert (
        "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
        not in decision.reduced_risk_reasons
    )
    signed_authority = decision.component_scores[
        "ultimate_candidate_package_new_entry_signed_authority"
    ]
    assert signed_authority["signed"] is False
    assert signed_authority["status"] == (
        "package_new_entry_authority_required_not_true"
    )
    open_reduced_authority = decision.component_scores[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ]
    assert open_reduced_authority["allowed"] is False
    assert open_reduced_authority["fill_floor_softening_signed_authority_ok"] is False


def test_selector_v4_package_fill_floor_softening_rejects_unbound_or_stale_signed_authority():
    base_event = _event()
    config = _config(
        selector_v4_admission_quality_guard_enabled=True,
        selector_v4_calibrated_admission_enabled=True,
        selector_v4_calibrated_admission_floor_failure_action="reject",
        selector_v4_calibrated_min_fill_probability=0.45,
        ultimate_candidate_package_enabled=True,
        ultimate_candidate_package_shadow_enabled=True,
        ultimate_candidate_package_apply_to_execution=True,
        ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
        ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
        ultimate_candidate_package_soften_selector_fill_floor_enabled=True,
        ultimate_candidate_package_soften_selector_fill_floor_requires_broker_cost_pass=True,
        ultimate_candidate_package_soften_selector_fill_floor_requires_positive_predecision_edge=True,
        scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_source_completeness=0.65,
    )

    valid_authority = _signed_package_new_entry_authority()
    cases = [
        (
            {
                **_signed_package_new_entry_authority(expected_hash=""),
            },
            "expected_package_new_entry_authority_hash_missing",
        ),
        (
            _signed_package_new_entry_authority(
                authority_hash="selector-fixture-authority",
                expected_hash="selector-fixture-authority",
            ),
            "package_new_entry_authority_hash_not_sha256_hex",
        ),
        (
            _signed_package_new_entry_authority(candidate_id="stale_candidate"),
            "package_new_entry_authority_candidate_id_mismatch",
        ),
        (
            _signed_package_new_entry_authority(
                decision_time_utc="2026-05-05T06:16:00Z"
            ),
            "package_new_entry_authority_decision_time_utc_mismatch",
        ),
        (
            {
                **valid_authority,
                "package_new_entry_authority_source_boundary": "",
            },
            "package_new_entry_authority_source_boundary_missing",
        ),
        (
            {
                **valid_authority,
                "package_new_entry_authority_uses_outcome_fields": True,
            },
            "package_new_entry_authority_uses_outcome_fields_not_false",
        ),
    ]

    for authority_fields, expected_status in cases:
        event = _event(
            symbol="NAS100",
            side="LONG",
            origin_family="volatility_compression_expansion",
            decision_time_utc="2026-05-05T06:15:00Z",
            fill_probability=0.30,
            candidate_ev_r=1.20,
            selected_cell={
                **base_event["selected_cell"],
                "broker_net_expectancy_r": 1.20,
                "stress_expectancy_r": 1.05,
            },
            probability_debate={
                "selected_action": "long",
                "theses": _theses(long=_thesis(ev=1.20, probability=0.82)),
            },
            **authority_fields,
        )

        decision = evaluate_selector_v4_admission(event, config)

        assert decision.action == "reject"
        assert (
            "calibrated_admission_fill_probability_below_generalized_floor"
            in decision.hard_reject_reasons
        )
        signed_authority = decision.component_scores[
            "ultimate_candidate_package_new_entry_signed_authority"
        ]
        assert signed_authority["signed"] is False
        assert signed_authority["status"] == expected_status
        assert expected_status in signed_authority["failures"]
        open_reduced_authority = decision.component_scores[
            "ultimate_candidate_package_open_reduced_risk_authority"
        ]
        assert open_reduced_authority["allowed"] is False
        assert (
            open_reduced_authority["fill_floor_softening_signed_authority_ok"]
            is False
        )


def test_selector_v4_uses_later_valid_deep_envelope_instead_of_invalid_direct_payload():
    valid_authority = _signed_package_new_entry_authority(
        expected_net_r=1.31,
        probability=0.87,
        fill_probability=0.36,
    )
    invalid_direct = {
        **valid_authority,
        "expected_package_new_entry_authority_hash_sha256": "0" * 64,
    }
    event = {
        "candidate_id": "selector_v4_fixture_001",
        "decision_time_utc": "2026-05-05T06:15:00Z",
        "ultimate_candidate_package_open_reduced_risk_authority": invalid_direct,
        "selector_packet": {
            "component_scores": {
                "candidate_decision_inputs": {
                    "ultimate_candidate_package_open_reduced_risk_authority": (
                        valid_authority
                    )
                }
            }
        },
    }

    detail = _package_new_entry_signed_authority_detail(event, {}, None)

    assert detail["signed"] is True
    assert detail["authority_hash_source"].endswith(
        "candidate_decision_inputs.ultimate_candidate_package_open_reduced_risk_authority"
    )
    assert detail["package_new_entry_authority_payload"]["expected_net_r"] == 1.31


def test_selector_v4_package_fill_floor_softening_reads_runtime_short_alias():
    base_event = _event()
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        **_signed_package_new_entry_authority(),
        fill_probability=0.30,
        candidate_ev_r=1.20,
        selected_cell={
            **base_event["selected_cell"],
            "broker_net_expectancy_r": 1.20,
            "stress_expectancy_r": 1.05,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.20, probability=0.82)),
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_calibrated_admission_enabled=True,
            selector_v4_calibrated_admission_floor_failure_action="reject",
            selector_v4_calibrated_min_fill_probability=0.45,
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_selector_fill_floor_enabled=True,
            ultimate_candidate_package_soften_selector_fill_floor_requires_broker_cost_pass=True,
            ultimate_candidate_package_soften_selector_fill_floor_requires_positive_predecision_edge=True,
            selector_reduce_risk_package_fill_floor_min_fill_probability=0.25,
            scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_source_completeness=0.65,
        ),
    )

    authority = decision.component_scores[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ]
    assert decision.action == "open-reduced-risk"
    assert authority["allowed"] is True
    assert authority["authority_family"] == "fill_floor_softening"
    assert authority["fill_floor_softening_min_fill_probability"] == 0.25


def test_selector_v4_package_fill_floor_softening_uses_configured_source_floor():
    base_event = _event()
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        **_signed_package_new_entry_authority(),
        fill_probability=0.30,
        source_completeness=0.70,
        candidate_ev_r=1.20,
        selected_cell={
            **base_event["selected_cell"],
            "broker_net_expectancy_r": 1.20,
            "stress_expectancy_r": 1.05,
            "source_completeness": 0.70,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.20, probability=0.82)),
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_calibrated_admission_enabled=True,
            selector_v4_calibrated_admission_floor_failure_action="reject",
            selector_v4_calibrated_min_fill_probability=0.45,
            selector_v4_calibrated_min_source_completeness=0.65,
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_selector_fill_floor_enabled=True,
            ultimate_candidate_package_soften_selector_fill_floor_min_fill_probability=0.20,
            scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_source_completeness=0.65,
        ),
    )

    authority = decision.component_scores[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ]
    assert decision.action == "open-reduced-risk"
    assert authority["allowed"] is True
    assert authority["derived_executable_min_source_completeness"] == 0.65
    assert authority["derived_executable_quality_authority"] is True


def test_selector_v4_fill_floor_softening_requires_executable_fillability_floor():
    base_event = _event()
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.30,
        candidate_ev_r=1.20,
        selected_cell={
            **base_event["selected_cell"],
            "broker_net_expectancy_r": 1.20,
            "stress_expectancy_r": 1.05,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.20, probability=0.82)),
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_calibrated_admission_enabled=True,
            selector_v4_calibrated_admission_floor_failure_action="reject",
            selector_v4_calibrated_min_fill_probability=0.45,
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_selector_fill_floor_enabled=True,
            ultimate_candidate_package_soften_selector_fill_floor_requires_broker_cost_pass=True,
            ultimate_candidate_package_soften_selector_fill_floor_requires_positive_predecision_edge=True,
            ultimate_candidate_package_soften_selector_fill_floor_min_fill_probability=0.45,
            scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_source_completeness=0.65,
        ),
    )

    authority = decision.component_scores[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ]
    assert decision.action == "reject"
    assert (
        "calibrated_admission_fill_probability_below_generalized_floor"
        in decision.hard_reject_reasons
    )
    assert authority["allowed"] is False
    assert authority["fill_floor_softening_fillability_ok"] is False


def test_selector_v4_fill_floor_package_reason_precedes_weak_numeric_disagreement():
    base_event = _event()
    mixed_sources = [
        *_required_confluence_sources()[:-1],
        _follow_source(
            "mixed-avoid-source",
            source_family="source_completeness",
            label="MIXED",
            direction="LONG",
            strength=0.42,
            confidence=0.52,
            conflict_reason="source_pressure_mixed_not_full_risk_permission",
        ),
    ]
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        **_signed_package_new_entry_authority(),
        numeric_confluence={"sources": mixed_sources},
        fill_probability=0.30,
        candidate_ev_r=1.20,
        selected_cell={
            **base_event["selected_cell"],
            "broker_net_expectancy_r": 1.20,
            "stress_expectancy_r": 1.05,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.20, probability=0.82)),
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_calibrated_admission_enabled=True,
            selector_v4_calibrated_admission_floor_failure_action="reject",
            selector_v4_calibrated_min_fill_probability=0.45,
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_selector_fill_floor_enabled=True,
            ultimate_candidate_package_soften_selector_fill_floor_requires_broker_cost_pass=True,
            ultimate_candidate_package_soften_selector_fill_floor_requires_positive_predecision_edge=True,
        ),
    )

    assert decision.action == "open-reduced-risk"
    assert (
        "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
        in decision.reduced_risk_reasons
    )
    assert "numeric_confluence_structured_disagreement" in decision.reduced_risk_reasons
    assert (
        "ultimate_candidate_package_numeric_disagreement_open_reduced_risk"
        not in decision.reduced_risk_reasons
    )
    open_reduced_authority = decision.component_scores[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ]
    assert open_reduced_authority["applies"] is True
    assert open_reduced_authority["allowed"] is True
    assert open_reduced_authority["authority_family"] == "fill_floor_softening"


def test_selector_v4_package_fill_floor_softening_does_not_bypass_cost_refusal():
    base_event = _event()
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        fill_probability=0.30,
        candidate_ev_r=1.20,
        selected_cell={
            **base_event["selected_cell"],
            "broker_net_expectancy_r": 1.20,
            "stress_expectancy_r": 1.05,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.20, probability=0.82)),
        },
        cost={
            **base_event["cost"],
            "pretrade_cost_packet_status": "REFUSED",
            "pretrade_cost_refusal_reasons": ["total_cost_r_exceeds_limit"],
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_admission_quality_guard_enabled=True,
            selector_v4_calibrated_admission_enabled=True,
            selector_v4_calibrated_admission_floor_failure_action="reject",
            selector_v4_calibrated_min_fill_probability=0.45,
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            ultimate_candidate_package_soften_selector_fill_floor_enabled=True,
            ultimate_candidate_package_soften_selector_fill_floor_requires_broker_cost_pass=True,
            ultimate_candidate_package_soften_selector_fill_floor_requires_positive_predecision_edge=True,
        ),
    )

    assert decision.action == "reject"
    assert any(
        reason.startswith("broker_net_pretrade_cost_packet_refused")
        for reason in decision.hard_reject_reasons
    )
    assert (
        "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
        not in decision.reduced_risk_reasons
    )


def test_selector_v4_complete_required_confluence_families_permits_trade():
    decision = evaluate_selector_v4_admission(_event(), _config())

    assert decision.action == "trade"
    confluence = decision.component_scores["numeric_confluence"]
    assert confluence["missing_required_source_families"] == []
    assert set(confluence["present_source_families"]) == {
        "selector",
        "market_state",
        "cost",
        "lifecycle",
        "source_completeness",
    }


def test_selector_v4_missing_probability_packet_is_source_required():
    event = _event(probability_debate=None)

    decision = evaluate_selector_v4_admission(event, _config())

    assert decision.action == "source-required"
    assert "probability_debate" in decision.source_required_fields
    assert decision.final_risk_pct == 0.0


def test_selector_v4_source_required_precedes_semantic_hard_rejects():
    event = _event(
        probability_debate=None,
        numeric_confluence={
            "sources": [
                _follow_source(
                    label="AVOID",
                    strength=0.96,
                    confidence=0.94,
                    invalidation_type="same_direction_stop_cluster_damage",
                )
            ]
        },
    )

    decision = evaluate_selector_v4_admission(event, _config())

    assert decision.action == "source-required"
    assert "probability_debate" in decision.source_required_fields
    assert any("avoid_same_direction_stop_cluster_damage" in item for item in decision.hard_reject_reasons)


def test_selector_v4_action_helpers_match_risk_bearing_contract():
    assert selector_v4_action_is_risk_bearing("trade") is True
    assert selector_v4_action_is_risk_bearing("reduce_risk") is True
    assert selector_v4_action_is_risk_bearing("open-reduced-risk") is True
    assert selector_v4_action_blocks_execution("reduce-risk") is False
    assert selector_v4_action_blocks_execution("open-reduced-risk") is False
    assert selector_v4_action_blocks_execution("source_required") is True
    assert selector_v4_action_blocks_execution("reject") is True


def test_selector_v4_package_positive_numeric_disagreement_stays_reduce_risk_by_default() -> None:
    mixed_sources = [
        *_required_confluence_sources()[:-1],
        _follow_source(
            "mixed-avoid-source",
            source_family="source_completeness",
            label="MIXED",
            direction="LONG",
            strength=0.42,
            confidence=0.52,
            conflict_reason="source_pressure_mixed_not_full_risk_permission",
        ),
    ]
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        numeric_confluence={"sources": mixed_sources},
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.2,
            "stress_expectancy_r": 1.1,
            "source_completeness": 1.0,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.3, probability=0.90)),
        },
        candidate_fill_probability=0.90,
        predecision_limit_fillability=_predecision_limit_fillability(0.90),
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    numeric_contract = decision.component_scores[
        "ultimate_candidate_package_numeric_disagreement_open_reduced_risk"
    ]
    assert decision.action == "reduce-risk"
    assert decision.reason == "numeric_confluence_structured_disagreement"
    assert numeric_contract["allowed"] is False
    assert numeric_contract["quality_allowed"] is True
    assert (
        "ultimate_candidate_package_numeric_disagreement_open_reduced_risk"
        not in decision.reduced_risk_reasons
    )
    open_reduced_authority = decision.component_scores[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ]
    assert open_reduced_authority["applies"] is False
    assert open_reduced_authority["allowed"] is False
    reduce_risk_authority = decision.component_scores[
        "ultimate_candidate_package_reduce_risk_authority"
    ]
    assert reduce_risk_authority["applies"] is True
    assert reduce_risk_authority["allowed"] is False
    assert reduce_risk_authority["authority_family"] is None
    assert reduce_risk_authority["numeric_disagreement_reduce_risk_authority"][
        "explicit_config_enabled"
    ] is False


def test_selector_v4_numeric_disagreement_gets_reduce_risk_package_authority() -> None:
    mixed_sources = [
        *_required_confluence_sources()[:-1],
        _follow_source(
            "mixed-avoid-source",
            source_family="source_completeness",
            label="MIXED",
            direction="LONG",
            strength=0.42,
            confidence=0.52,
            conflict_reason="source_pressure_mixed_not_full_risk_permission",
        ),
    ]
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        numeric_confluence={"sources": mixed_sources},
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 0.82,
            "stress_expectancy_r": 0.80,
            "source_completeness": 0.96,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=0.85, probability=0.76)),
        },
        candidate_fill_probability=0.30,
        predecision_limit_fillability=_predecision_limit_fillability(0.30),
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_expected_net_r=0.70,
            scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_probability=0.70,
            scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_fill_probability=0.20,
            scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_source_completeness=0.95,
            scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_authority_enabled=True,
            scheduler_v4_best_trade_allocator_selector_reduce_risk_numeric_disagreement_package_new_entry_authority_enabled=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    numeric_contract = decision.component_scores[
        "ultimate_candidate_package_numeric_disagreement_open_reduced_risk"
    ]
    assert decision.action == "reduce-risk"
    assert decision.reason == "numeric_confluence_structured_disagreement"
    assert numeric_contract["quality_allowed"] is False
    assert numeric_contract["min_expected_net_r"] == 1.10
    assert numeric_contract["min_probability"] == 0.90
    assert numeric_contract["min_fill_probability"] == 0.90
    assert numeric_contract["min_source_completeness"] == 0.95
    open_reduced_authority = decision.component_scores[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ]
    assert open_reduced_authority["applies"] is False
    assert open_reduced_authority["allowed"] is False
    assert open_reduced_authority["authority_family"] is None
    assert open_reduced_authority["broker_cost_passed_for_package_router"] is True
    reduce_risk_authority = decision.component_scores[
        "ultimate_candidate_package_reduce_risk_authority"
    ]
    assert reduce_risk_authority["applies"] is True
    assert reduce_risk_authority["allowed"] is True
    assert reduce_risk_authority["authority_family"] == "numeric_disagreement_softening"
    numeric_reduce_authority = decision.component_scores[
        "ultimate_candidate_package_numeric_disagreement_reduce_risk_authority"
    ]
    assert numeric_reduce_authority["allowed"] is True
    assert numeric_reduce_authority["quality_allowed"] is True
    assert numeric_reduce_authority["min_expected_net_r"] == 0.70
    assert numeric_reduce_authority["min_probability"] == 0.70
    assert numeric_reduce_authority["min_fill_probability"] == 0.20
    assert numeric_reduce_authority["min_source_completeness"] == 0.95
    assert numeric_reduce_authority["replay_only_no_live_runtime_effect"] is True


def test_selector_v4_numeric_disagreement_authority_requires_expected_net_calibration_when_enabled() -> None:
    mixed_sources = [
        *_required_confluence_sources()[:-1],
        _follow_source(
            "mixed-avoid-source",
            source_family="source_completeness",
            label="MIXED",
            direction="LONG",
            strength=0.42,
            confidence=0.52,
            conflict_reason="source_pressure_mixed_not_full_risk_permission",
        ),
    ]
    base_event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        numeric_confluence={"sources": mixed_sources},
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 0.82,
            "stress_expectancy_r": 0.80,
            "source_completeness": 0.96,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=0.85, probability=0.76)),
        },
        candidate_fill_probability=0.30,
        predecision_limit_fillability=_predecision_limit_fillability(0.30),
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
    )
    config = _config(
        ultimate_candidate_package_enabled=True,
        ultimate_candidate_package_shadow_enabled=True,
        ultimate_candidate_package_apply_to_execution=True,
        ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
        ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
        scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_expected_net_r=0.70,
        scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_probability=0.70,
        scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_fill_probability=0.20,
        scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_source_completeness=0.95,
        scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_authority_enabled=True,
        scheduler_v4_best_trade_allocator_selector_reduce_risk_numeric_disagreement_package_new_entry_authority_enabled=True,
        scheduler_v4_best_trade_allocator_selector_reduce_risk_open_reduced_expected_net_policy_calibration_required=True,
        selector_v4_apply_to_execution=False,
        selector_v4_live_activation_allowed=False,
    )

    uncalibrated = evaluate_selector_v4_admission(base_event, config)
    uncalibrated_authority = uncalibrated.component_scores[
        "ultimate_candidate_package_numeric_disagreement_reduce_risk_authority"
    ]
    assert uncalibrated.action == "reduce-risk"
    assert uncalibrated.reason == "numeric_confluence_structured_disagreement"
    assert uncalibrated_authority["allowed"] is False
    assert uncalibrated_authority["quality_allowed"] is False
    assert (
        uncalibrated_authority[
            "selected_policy_expected_net_calibration_required"
        ]
        is True
    )
    assert uncalibrated_authority["selected_policy_expected_net_calibrated"] is False

    calibrated_event = {
        **base_event,
        "selected_policy_expected_net_calibration_status": "calibrated",
        "selected_policy_expected_net_calibration_source": (
            "selected_policy_replay_calibration_packet"
        ),
        "selected_policy_expected_net_calibration_source_boundary": (
            "predecision_selected_policy_expected_net_calibration_no_outcome_fields"
        ),
    }
    calibrated = evaluate_selector_v4_admission(calibrated_event, config)
    calibrated_authority = calibrated.component_scores[
        "ultimate_candidate_package_numeric_disagreement_reduce_risk_authority"
    ]
    assert calibrated_authority["allowed"] is True
    assert calibrated_authority["quality_allowed"] is True
    assert calibrated_authority["selected_policy_expected_net_calibrated"] is True
    assert calibrated_authority["selected_policy_expected_net_calibration_status"] == (
        "calibrated"
    )


def test_selector_v4_weak_numeric_disagreement_stays_reduce_risk() -> None:
    mixed_sources = [
        *_required_confluence_sources()[:-1],
        _follow_source(
            "mixed-avoid-source",
            source_family="source_completeness",
            label="MIXED",
            direction="LONG",
            strength=0.42,
            confidence=0.52,
            conflict_reason="source_pressure_mixed_not_full_risk_permission",
        ),
    ]
    event = _event(
        symbol="NAS100",
        side="LONG",
        origin_family="volatility_compression_expansion",
        decision_time_utc="2026-05-05T06:15:00Z",
        numeric_confluence={"sources": mixed_sources},
        selected_cell={
            **_event()["selected_cell"],
            "broker_net_expectancy_r": 1.0,
            "stress_expectancy_r": 0.8,
        },
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=1.1, probability=0.68)),
        },
        candidate_fill_probability=0.90,
        cost={
            **_event()["cost"],
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
            },
        },
    )

    decision = evaluate_selector_v4_admission(
        event,
        _config(
            ultimate_candidate_package_enabled=True,
            ultimate_candidate_package_shadow_enabled=True,
            ultimate_candidate_package_apply_to_execution=True,
            ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
            ultimate_candidate_package_require_shadow_match_for_selector_v4=True,
            selector_v4_apply_to_execution=False,
            selector_v4_live_activation_allowed=False,
        ),
    )

    assert decision.action == "reduce-risk"
    assert decision.reason == "numeric_confluence_structured_disagreement"
    assert (
        "ultimate_candidate_package_numeric_disagreement_open_reduced_risk"
        not in decision.reduced_risk_reasons
    )
    reduce_risk_authority = decision.component_scores[
        "ultimate_candidate_package_reduce_risk_authority"
    ]
    assert reduce_risk_authority["allowed"] is False
    assert reduce_risk_authority["authority_family"] is None
    assert reduce_risk_authority["numeric_disagreement_reduce_risk_authority"][
        "quality_allowed"
    ] is False


def test_selector_v4_rejects_hard_avoid_invalidation():
    event = _event(
        numeric_confluence={
            "sources": [
                *_required_confluence_sources()[1:],
                _follow_source(
                    source_id="selector-hard-avoid",
                    source_family="selector",
                    label="AVOID",
                    strength=0.96,
                    confidence=0.94,
                    invalidation_type="same_direction_stop_cluster_damage",
                )
            ]
        }
    )

    decision = evaluate_selector_v4_admission(event, _config())

    assert decision.action == "reject"
    assert any("avoid_same_direction_stop_cluster_damage" in item for item in decision.hard_reject_reasons)


def test_selector_v4_preserves_no_trade_as_explicit_action():
    event = _event(probability_debate={"selected_action": "no-trade", "theses": _theses()})

    decision = evaluate_selector_v4_admission(event, _config())

    assert decision.action == "no-trade"
    assert decision.reason == "probability_debate_selected_no_trade"


def test_selector_v4_reduces_risk_for_high_probability_uncertainty():
    event = _event(
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(ev=0.34, probability=0.68, uncertainty=0.74)),
        }
    )

    decision = evaluate_selector_v4_admission(event, _config())

    assert decision.action == "reduce-risk"
    assert decision.risk_multiplier == 0.5
    assert decision.final_risk_pct == 0.125


def test_selector_v4_queues_when_debate_selects_wait():
    event = _event(probability_debate={"selected_action": "wait", "theses": _theses()})

    decision = evaluate_selector_v4_admission(event, _config())

    assert decision.action == "queue"
    assert "probability_debate_selected_wait" in decision.queue_reasons


def test_selector_v4_lists_forbidden_future_fields_without_using_them():
    base = _event()
    tainted = _event(exact_r=3.0, broker_real_net_r=2.4)

    clean_decision = evaluate_selector_v4_admission(base, _config())
    tainted_decision = evaluate_selector_v4_admission(tainted, _config())

    assert tainted_decision.action == clean_decision.action
    assert set(tainted_decision.ignored_forbidden_fields) == {"exact_r", "broker_real_net_r"}


def test_selector_v4_uses_explicit_package_generation_time_without_changing_default_callers():
    event = _event(decision_time_utc="2026-01-02T00:15:00+00:00")
    config = _config(
        ultimate_candidate_package_enabled=True,
        ultimate_candidate_package_shadow_enabled=True,
        ultimate_candidate_package_apply_to_execution=False,
        ultimate_candidate_package_registry_path=ULTIMATE_PACKAGE_SOURCE,
    )

    first = evaluate_selector_v4_admission(
        event,
        config,
        package_generated_utc="2026-01-02T00:15:00+00:00",
    )
    second = evaluate_selector_v4_admission(
        event,
        config,
        package_generated_utc="2026-01-02T00:15:00+00:00",
    )

    first_packet = first.component_scores["ultimate_candidate_package"]
    second_packet = second.component_scores["ultimate_candidate_package"]
    assert first_packet["generated_utc"] == "2026-01-02T00:15:00+00:00"
    assert second_packet["generated_utc"] == "2026-01-02T00:15:00+00:00"
    assert first_packet["packet_hash_sha256"] == second_packet["packet_hash_sha256"]
