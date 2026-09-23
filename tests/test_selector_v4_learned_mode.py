"""Selector V4 learned-edge admission mode (default-off) tests.

Covers: disabled byte-identity, learned-floor substitution (both directions),
non-silent refusal fallback, required-mode source-required, learned risk
sizing gradient/clamp/segment-shrinkage math, and train/runtime feature
parity between ``extract_runtime_features`` and the dataset builder's
``extract_features``.
"""

import json

import pytest

from src.components.learned_edge_layer_v4 import (
    ARTIFACT_SCHEMA_VERSION,
    ASSET_CLASS_BY_SYMBOL as RUNTIME_ASSET_CLASS_BY_SYMBOL,
    load_learned_edge_artifact_cached,
    extract_runtime_features,
    score_learned_edge,
)
from src.components.selector_v4 import (
    _selected_policy_expected_net_calibration,
    evaluate_selector_v4_admission,
)
from src.research_infra.learned_edge_dataset_builder import (
    ASSET_CLASS_BY_SYMBOL as BUILDER_ASSET_CLASS_BY_SYMBOL,
    extract_features,
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
            "market-state", source_family="market_state", strength=0.74, confidence=0.78
        ),
        _follow_source(
            "cost-model",
            source_family="cost",
            strength=0.70,
            confidence=0.74,
            cost_sensitivity=0.12,
        ),
        _follow_source(
            "lifecycle-state", source_family="lifecycle", strength=0.68, confidence=0.72
        ),
        _follow_source(
            "source-completeness",
            source_family="source_completeness",
            strength=0.88,
            confidence=0.86,
        ),
    ]


def _event(**overrides):
    event = {
        "candidate_id": "selector_v4_learned_fixture_001",
        "symbol": "XAUUSD",
        "side": "LONG",
        "session_bucket": "london",
        "trading_day": "2026-05-06",
        "decision_time_utc": "2026-05-06T08:15:00+00:00",
        # Learned-feature inputs (predecision only).
        "candidate_probability": 0.66,
        "candidate_ev_r": 0.29,
        "expected_cost_r": 0.03,
        "risk_reward_ratio": 2.0,
        "probability_packet": {
            "selected_thesis": {
                "probability": 0.66,
                "uncalibrated_probability": 0.60,
                "uncertainty": 0.18,
                "missing_source_penalty": 0.05,
                "source_completeness": 0.95,
                "disagreement_state": "resolved",
            }
        },
        "numeric_confluence": {"sources": _required_confluence_sources()},
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


def _artifact(
    *,
    fill_intercept=0.0,
    outcome_intercept=2.0,
    net_r_intercept=0.2,
    thresholds=None,
    segment_shrinkage=None,
    schema_version=ARTIFACT_SCHEMA_VERSION,
):
    """Minimal valid ultimate_learned_edge_layer_v1 artifact.

    Empty coefficient maps keep head logits at the intercept so learned
    outputs are exact: p = sigmoid(intercept), net_r = intercept.
    """

    return {
        "schema_version": schema_version,
        "generator_code_sha": "",
        "freeze_day": "2026-06-01",
        "valid_through_utc": "2030-01-01T00:00:00+00:00",
        "numeric_features": [
            {
                "name": "f_heuristic_probability",
                "median": 0.5,
                "mean": 0.0,
                "std": 1.0,
                "required": True,
            }
        ],
        "categorical_features": [],
        "heads": {
            "fill": {"coefficients": {}, "intercept": fill_intercept, "calibration": None},
            "outcome": {
                "coefficients": {},
                "intercept": outcome_intercept,
                "calibration": None,
            },
            "net_r": {
                "coefficients": {},
                "intercept": net_r_intercept,
                "clip": {"low": -1.5, "high": 5.0},
            },
        },
        "segment_shrinkage": segment_shrinkage or {},
        "thresholds": dict(
            thresholds
            or {
                "t_trade_expected_net_r": 0.15,
                "t_reduce_expected_net_r": 0.05,
                "min_fill_probability": 0.45,
            }
        ),
        "artifact_hash_sha256": "f" * 64,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "broker_runtime_change_status": False,
        "validation_result_status": False,
        "outcome_result_rows_status": False,
    }


def _write_artifact(tmp_path, artifact, name="learned_edge_artifact.json"):
    path = tmp_path / name
    path.write_text(json.dumps(artifact, sort_keys=True), encoding="utf-8")
    return str(path)


def test_selected_policy_calibration_prefers_package_authority_over_stale_event() -> None:
    stale_event = {
        "selected_policy_expected_net_calibration_status": (
            "selected_policy_expected_net_bridge_proxy_diagnostic_only"
        ),
        "selected_policy_expected_net_calibrated": False,
        "selected_policy_expected_net_calibration_source_boundary": (
            "selected_policy_expected_net_uncalibrated_bridge_proxy_predecision_quality"
        ),
    }
    decision_inputs = {
        "package_new_entry_authority_selected_policy_expected_net_calibration_status": (
            "owner_approved_reconstructed_replay_selected_policy_expected_net_calibrated"
        ),
        "package_new_entry_authority_selected_policy_expected_net_calibrated": True,
        "package_new_entry_authority_selected_policy_expected_net_calibration_source_boundary": (
            "owner_approved_reconstructed_replay_selected_policy_expected_net_predecision_no_outcome_boundary"
        ),
    }

    status, boundary, calibrated = _selected_policy_expected_net_calibration(
        {},
        decision_inputs,
        stale_event,
    )

    assert status == (
        "owner_approved_reconstructed_replay_selected_policy_expected_net_calibrated"
    )
    assert boundary == (
        "owner_approved_reconstructed_replay_selected_policy_expected_net_predecision_no_outcome_boundary"
    )
    assert calibrated is True


# ---------------------------------------------------------------------------
# (a) disabled -> byte-identical to baseline, no learned_edge application
# ---------------------------------------------------------------------------


def test_learned_mode_disabled_is_byte_identical_to_baseline(tmp_path):
    artifact_path = _write_artifact(tmp_path, _artifact())
    event = _event()

    baseline = evaluate_selector_v4_admission(event, _config())
    disabled = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_learned_edge_enabled=False,
            selector_v4_learned_edge_artifact_path=artifact_path,
            selector_v4_learned_edge_required=False,
            selector_v4_learned_risk_sizing_enabled=False,
        ),
    )

    assert baseline.to_record() == disabled.to_record()
    assert "learned_edge" not in disabled.to_record()
    assert "learned_edge" not in disabled.component_scores
    assert baseline.action == "trade"


# ---------------------------------------------------------------------------
# (b) enabled + scoring -> floors evaluate LEARNED values, not heuristics
# ---------------------------------------------------------------------------


def test_learned_floors_reject_when_heuristics_pass_but_learned_fails(tmp_path):
    # outcome intercept -2 -> learned probability sigmoid(-2) ~ 0.1192 < 0.58.
    artifact_path = _write_artifact(tmp_path, _artifact(outcome_intercept=-2.0))
    event = _event()

    baseline = evaluate_selector_v4_admission(event, _config())
    learned = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_learned_edge_enabled=True,
            selector_v4_learned_edge_artifact_path=artifact_path,
        ),
    )
    record = learned.to_record()

    assert baseline.action == "trade"
    assert learned.action == "reject"
    assert (
        "calibrated_admission_probability_below_generalized_floor"
        in learned.hard_reject_reasons
    )
    assert record["learned_edge"]["status"] == "scored"
    assert record["learned_edge"]["applied_to_floors"] is True
    assert record["learned_edge"]["probability"] == pytest.approx(0.11920292)
    assert record["learned_edge"]["fill_probability"] == pytest.approx(0.5)
    assert record["learned_edge"]["expected_net_r"] == pytest.approx(0.1)
    assert record["learned_edge"]["artifact_hash_sha256"] == "f" * 64
    # Heuristics preserved as shadow fields next to the learned scores.
    learned_scores = learned.component_scores["learned_edge"]
    assert learned_scores["heuristic_probability"] == pytest.approx(0.66)
    assert learned_scores["heuristic_ev_r"] == pytest.approx(0.20)
    # Floors ran through the learned path even with the guard config off.
    admission = learned.component_scores["admission_quality"]
    assert admission["learned_edge_floor_active"] is True
    assert admission["calibrated_admission_enabled"] is True


def test_learned_floors_admit_when_heuristics_fail_but_learned_passes(tmp_path):
    artifact_path = _write_artifact(tmp_path, _artifact(outcome_intercept=2.0))
    # Thesis probability 0.54 fails the static calibrated floor (0.58).
    event = _event(
        fill_probability=0.80,
        probability_debate={
            "selected_action": "long",
            "theses": _theses(long=_thesis(probability=0.54)),
        },
    )
    base_cfg = dict(
        selector_v4_admission_quality_guard_enabled=True,
        selector_v4_calibrated_admission_enabled=True,
    )

    baseline = evaluate_selector_v4_admission(event, _config(**base_cfg))
    learned = evaluate_selector_v4_admission(
        event,
        _config(
            **base_cfg,
            selector_v4_learned_edge_enabled=True,
            selector_v4_learned_edge_artifact_path=artifact_path,
        ),
    )

    assert baseline.action == "reject"
    assert (
        "calibrated_admission_probability_below_generalized_floor"
        in baseline.hard_reject_reasons
    )
    assert learned.action == "trade"
    assert learned.hard_reject_reasons == ()
    assert learned.to_record()["learned_edge"]["probability"] == pytest.approx(
        0.88079708
    )


# ---------------------------------------------------------------------------
# (c) refusal fallback -> explicit reason recorded, decision matches baseline
# ---------------------------------------------------------------------------


def test_load_failure_falls_back_to_static_floors_with_explicit_reason(tmp_path):
    missing_path = str(tmp_path / "missing_artifact.json")
    event = _event()

    baseline = evaluate_selector_v4_admission(event, _config())
    fallback = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_learned_edge_enabled=True,
            selector_v4_learned_edge_artifact_path=missing_path,
        ),
    )
    record = fallback.to_record()

    assert fallback.action == baseline.action == "trade"
    assert fallback.reason == baseline.reason
    assert fallback.risk_multiplier == baseline.risk_multiplier
    assert fallback.final_risk_pct == baseline.final_risk_pct
    assert record["learned_edge"]["status"] == "fallback_static_floor"
    assert record["learned_edge"]["fallback_reason"].startswith(
        "learned_edge_unavailable_static_floor_fallback:"
    )
    assert record["learned_edge"]["applied_to_floors"] is False
    assert record["learned_edge"]["applied_to_sizing"] is False


def test_scorer_refusal_falls_back_with_refusal_detail(tmp_path):
    artifact_path = _write_artifact(
        tmp_path, _artifact(schema_version="wrong_schema_v0"), name="bad_schema.json"
    )
    event = _event()

    baseline = evaluate_selector_v4_admission(event, _config())
    fallback = evaluate_selector_v4_admission(
        event,
        _config(
            selector_v4_learned_edge_enabled=True,
            selector_v4_learned_edge_artifact_path=artifact_path,
        ),
    )
    reason = fallback.to_record()["learned_edge"]["fallback_reason"]

    assert fallback.action == baseline.action == "trade"
    assert reason.startswith("learned_edge_unavailable_static_floor_fallback:")
    assert "refused_artifact_invalid" in reason


# ---------------------------------------------------------------------------
# (d) required=True + refusal -> source-required, never silent
# ---------------------------------------------------------------------------


def test_required_refusal_is_source_required(tmp_path):
    missing_path = str(tmp_path / "missing_artifact.json")

    decision = evaluate_selector_v4_admission(
        _event(),
        _config(
            selector_v4_learned_edge_enabled=True,
            selector_v4_learned_edge_required=True,
            selector_v4_learned_edge_artifact_path=missing_path,
        ),
    )
    record = decision.to_record()

    assert decision.action == "source-required"
    assert (
        "learned_edge_artifact_unavailable_or_refused"
        in decision.source_required_fields
    )
    assert decision.runtime_effect_now is False
    assert record["learned_edge"]["status"] == "refused_source_required"


# ---------------------------------------------------------------------------
# (e) learned risk sizing multiplier math incl. clamp
# ---------------------------------------------------------------------------


def _sizing_config(artifact_path, **overrides):
    return _config(
        selector_v4_learned_edge_enabled=True,
        selector_v4_learned_edge_artifact_path=artifact_path,
        selector_v4_learned_risk_sizing_enabled=True,
        **overrides,
    )


def test_learned_sizing_gradient_replaces_binary_multiplier(tmp_path):
    # expected_net_r = p_fill * net_r = 0.5 * 0.2 = 0.10
    # m = clip((0.10 - 0.05) / (0.15 - 0.05), 0, 1) * (0.5 + 0.5 * 1.0) = 0.5
    artifact_path = _write_artifact(tmp_path, _artifact())

    decision = evaluate_selector_v4_admission(_event(), _sizing_config(artifact_path))
    record = decision.to_record()

    assert decision.action == "trade"
    assert decision.risk_multiplier == pytest.approx(0.5)
    assert decision.final_risk_pct == pytest.approx(0.125)
    assert record["learned_edge"]["applied_to_sizing"] is True
    assert record["learned_edge"]["applied_to_floors"] is True


def test_learned_sizing_clamps_high_to_one(tmp_path):
    # expected_net_r = 0.5 * 5.0 = 2.5 -> gradient clips to 1.0 -> m = 1.0.
    artifact_path = _write_artifact(
        tmp_path, _artifact(net_r_intercept=5.0), name="high_net.json"
    )

    decision = evaluate_selector_v4_admission(_event(), _sizing_config(artifact_path))

    assert decision.action == "trade"
    assert decision.risk_multiplier == 1.0
    assert decision.to_record()["learned_edge"]["applied_to_sizing"] is True


def test_learned_sizing_clamps_low_to_zero(tmp_path):
    # expected_net_r = 0.5 * 0.1 = 0.05 == t_reduce -> gradient 0 -> m = 0.0.
    artifact_path = _write_artifact(
        tmp_path, _artifact(net_r_intercept=0.1), name="low_net.json"
    )

    decision = evaluate_selector_v4_admission(
        _event(),
        _sizing_config(artifact_path, selector_v4_calibrated_min_expected_net_r=0.0),
    )

    assert decision.action == "trade"
    assert decision.risk_multiplier == 0.0
    assert decision.final_risk_pct == 0.0
    assert decision.runtime_effect_now is False
    assert decision.to_record()["learned_edge"]["applied_to_sizing"] is True


def test_learned_sizing_segment_shrinkage_weight_shrinks_multiplier(tmp_path):
    # Segment weight n/(n+k) = 40/80 = 0.5 on both heads -> w_seg = 0.5,
    # base rates equal to the unshrunk probabilities so the floors still pass:
    # m = 0.5 * (0.5 + 0.5 * 0.5) = 0.375.
    p_outcome_raw = 0.8807970779778823  # sigmoid(2.0)
    segment_shrinkage = {
        "key_fields": ["f_asset_class", "f_session_bucket"],
        "k": 40.0,
        "min_weight": 0.0,
        "fill": {
            "global_base_rate": 0.5,
            "segments": {"metals|london": {"base_rate": 0.5, "n": 40.0}},
        },
        "outcome": {
            "global_base_rate": p_outcome_raw,
            "segments": {"metals|london": {"base_rate": p_outcome_raw, "n": 40.0}},
        },
    }
    artifact = _artifact(segment_shrinkage=segment_shrinkage)
    artifact_path = _write_artifact(tmp_path, artifact, name="shrunk.json")
    event = _event()

    # Cross-check the score the selector should consume.
    scored = score_learned_edge(extract_runtime_features(event), artifact)
    assert scored["status"] == "scored"
    assert scored["segment_shrinkage_weights"] == {"fill": 0.5, "outcome": 0.5}

    decision = evaluate_selector_v4_admission(event, _sizing_config(artifact_path))

    assert decision.action == "trade"
    assert decision.risk_multiplier == pytest.approx(0.375)
    assert decision.final_risk_pct == pytest.approx(0.09375)


def test_learned_sizing_not_applied_when_action_not_risk_bearing(tmp_path):
    artifact_path = _write_artifact(
        tmp_path, _artifact(outcome_intercept=-2.0), name="reject_path.json"
    )

    decision = evaluate_selector_v4_admission(_event(), _sizing_config(artifact_path))

    assert decision.action == "reject"
    assert decision.risk_multiplier == 0.0
    assert decision.to_record()["learned_edge"]["applied_to_sizing"] is False


# ---------------------------------------------------------------------------
# (f) runtime feature parity with the dataset builder
# ---------------------------------------------------------------------------


def _candidate_microscope_row():
    return {
        "candidate_id": "cand_parity_001",
        "origin_family": "session_open_range_break",
        "framework": "broad_dynamic",
        "symbol": "XAUUSD",
        "side": "long",
        "route_session": "london",
        "session_bucket": "london",
        "utc_hour_bucket": "h08_09",
        "kill_zone": "london_open",
        "trading_day": "2026-05-06",
        "decision_time_utc": "2026-05-06T08:15:00+00:00",
        "dynamic_geometry_policy": "momentum_exhaustion",
        "dynamic_execution_policy_id": "momentum_exhaustion_v2",
        "candidate_probability": 0.61,
        "candidate_ev_r": 0.22,
        "expected_cost_r": 0.04,
        "risk_reward_ratio": 2.4,
        "entry_price": 2350.0,
        "entry_reference": 2348.5,
        "stop_loss": 2344.0,
        "simulated_open_positions_seen": 2,
        "simulated_pending_orders_seen": 1,
        "probability_packet": {
            "selected_thesis": {
                "probability": 0.63,
                "uncalibrated_probability": 0.58,
                "uncertainty": 0.20,
                "missing_source_penalty": 0.05,
                "source_completeness": 0.90,
                "disagreement_state": "resolved",
            }
        },
    }


def test_runtime_feature_parity_with_dataset_builder():
    row = _candidate_microscope_row()

    assert extract_runtime_features(row) == extract_features(
        row, n_competing_in_group=1
    )


def test_runtime_feature_parity_with_explicit_n_competing():
    row = _candidate_microscope_row()

    runtime = extract_runtime_features({**row, "n_competing_in_group": 3})
    builder = extract_features(row, n_competing_in_group=3)

    assert runtime == builder
    assert runtime["f_n_competing_in_group"] == 3.0


def test_runtime_day_of_week_falls_back_to_decision_time():
    row = _candidate_microscope_row()
    row.pop("trading_day")

    features = extract_runtime_features(row)

    assert features["f_day_of_week"] == "wed"


def test_runtime_asset_class_map_matches_builder():
    assert RUNTIME_ASSET_CLASS_BY_SYMBOL == BUILDER_ASSET_CLASS_BY_SYMBOL


# ---------------------------------------------------------------------------
# artifact cache
# ---------------------------------------------------------------------------


def test_artifact_cache_returns_same_object_and_invalidates_on_rewrite(tmp_path):
    path = tmp_path / "cached_artifact.json"
    path.write_text(json.dumps(_artifact(), sort_keys=True), encoding="utf-8")

    first = load_learned_edge_artifact_cached(path)
    second = load_learned_edge_artifact_cached(str(path))
    assert first is second

    rewritten = _artifact(net_r_intercept=1.25)
    path.write_text(
        json.dumps(rewritten, sort_keys=True) + "\n", encoding="utf-8"
    )
    third = load_learned_edge_artifact_cached(path)
    assert third is not first
    assert third["heads"]["net_r"]["intercept"] == 1.25


def test_artifact_cache_raises_on_missing_path(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_learned_edge_artifact_cached(tmp_path / "does_not_exist.json")
