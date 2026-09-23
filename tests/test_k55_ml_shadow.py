import json

from src.research_infra.k55_ml_shadow import (
    ACTION_REQUIRED,
    FEATURE_BUNDLE_VERSION,
    FEATURE_READY_MODEL_PENDING,
    MODEL_SCHEMA_VERSION,
    PREDICTION_COMPUTED,
    TARGET_VERSION,
    build_ml_shadow_rows,
    forbidden_feature_keys,
)


def _candidate(**overrides):
    row = {
        "schema_version": "strategy_follow_candidate_v1",
        "candidate_id": "NAS100_2026-05-04T17:00:00+00:00",
        "created_at_utc": "2026-05-04T17:00:26+00:00",
        "decision_time_utc": "2026-05-04T17:00:00+00:00",
        "asof_cutoff_utc": "2026-05-04T17:00:00+00:00",
        "symbol": "NAS100",
        "broker_symbol": "NDX100",
        "side": "LONG",
        "framework": "ob_retest",
        "session": "ny",
        "analysis_decision": "CANDIDATE",
        "trade_parameters": {
            "direction": "LONG",
            "entry_price": 27446.2,
            "stop_loss": 27387.1,
            "take_profit_1": 27534.8,
            "risk_reward_ratio": 1.5,
            "sl_buffer_applied": 10.0,
        },
        "mso_summary": {
            "timeframes": {
                "D1": {"structure_direction": "bullish", "order_block_count": 1, "unmitigated_order_block_count": 1, "fvg_count": 2, "breaker_block_count": 0},
                "H4": {"structure_direction": "bullish", "order_block_count": 2, "unmitigated_order_block_count": 1, "fvg_count": 3, "breaker_block_count": 0},
                "H1": {"structure_direction": "bullish", "order_block_count": 3, "unmitigated_order_block_count": 2, "fvg_count": 4, "breaker_block_count": 1},
                "M15": {"structure_direction": "bullish", "order_block_count": 4, "unmitigated_order_block_count": 2, "fvg_count": 5, "breaker_block_count": 0},
            }
        },
        "external_confluence": {
            "sierra": {"status": "FEATURES_EXTRACTED", "source_status": "LOCAL_SIERRA_DEPTH_CAPTURED"},
            "databento": {"status": "NOT_FETCHED_OR_NO_CACHE_FOR_LIVE_CANDIDATE", "trigger_policy": {"trigger_status": "TRIGGER_READY"}},
        },
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def _decision(**overrides):
    row = {
        "schema_version": "decision_layer_diagnostics_join_v1",
        "row_key": "decision-row",
        "candidate_id": "NAS100_2026-05-04T17:00:00+00:00",
        "created_at_utc": "2026-05-05T00:00:00+00:00",
        "decision_time_utc": "2026-05-04T17:00:00+00:00",
        "decision_diagnostics_status": "DECISION_DIAGNOSTICS_JOINED",
        "candidate_features_join_status": "DIAGNOSTIC_NEAR_TIME_JOINED",
        "candidate_features_context": {
            "mso": {
                "m15_bvc_buy_fraction": 0.62,
                "m15_clv_current": 0.2,
                "m15_clv_avg_5": 0.1,
                "m15_session_vol_ratio": 1.4,
                "h1_nearest_ob_distance_atr": 0.3,
            },
            "c_gate_result": {
                "c1_h1_bias_present": True,
                "c2_m15_choch_detected": True,
                "c3_direction_matches": True,
            },
        },
        "verification_passed": True,
        "verification_context": {"l2_check_summary": {"m15_choch_exists": "PASS", "sl_beyond_ob": "PASS"}},
    }
    row.update(overrides)
    return row


def _mso(**overrides):
    row = {
        "schema_version": "candidate_mso_snapshot_join_v1",
        "row_key": "mso-row",
        "candidate_id": "NAS100_2026-05-04T17:00:00+00:00",
        "created_at_utc": "2026-05-05T00:00:00+00:00",
        "decision_time_utc": "2026-05-04T17:00:00+00:00",
        "mso_snapshot": {
            "structural_state": {
                "D1": {"structure_direction": "bullish", "order_block_count": 1, "unmitigated_order_block_count": 1, "fvg_count": 2, "breaker_block_count": 0},
                "H4": {"structure_direction": "bullish", "order_block_count": 2, "unmitigated_order_block_count": 1, "fvg_count": 3, "breaker_block_count": 0},
                "H1": {"structure_direction": "bullish", "order_block_count": 3, "unmitigated_order_block_count": 2, "fvg_count": 4, "breaker_block_count": 1},
                "M15": {"structure_direction": "bullish", "order_block_count": 4, "unmitigated_order_block_count": 2, "fvg_count": 5, "breaker_block_count": 0},
            }
        },
    }
    row.update(overrides)
    return row


def _mechanical(**overrides):
    row = {
        "schema_version": "mechanical_context_diagnostics_join_v1",
        "row_key": "mechanical-row",
        "candidate_id": "NAS100_2026-05-04T17:00:00+00:00",
        "created_at_utc": "2026-05-05T00:00:00+00:00",
        "decision_time_utc": "2026-05-04T17:00:00+00:00",
        "mechanical_context_status": "MECHANICAL_CONTEXT_DIAGNOSTICS_JOINED",
        "path_context": {
            "path_label": "entry_touched_then_reached_tp1",
            "touched_entry": True,
            "hit_tp1": True,
            "hit_sl": False,
        },
        "proximity_context": {"join_status": "CONTEXT_NEAR_TIME_JOINED", "distance_atr_ratio": 0.25, "h1_ob_count": 5, "m15_ob_count": 7, "relevant_ob_count": 12},
        "liquidity_distance_context": {"join_status": "CONTEXT_NEAR_TIME_GEOMETRY_JOINED", "pool_summary": {"violating_pool_count": 1, "nearest_pool_distance_to_sl": 12.0}},
        "displacement_context": {"join_status": "DISPLACEMENT_ASOF_JOINED", "displacement_ratio": 2.2, "body_to_atr": 1.1},
        "structure_divergence_context": {"join_status": "STRUCTURE_DIVERGENCE_TIMEFRAME_ROWS_JOINED", "timeframes": {"H1": {"v2_score": 5}, "M15": {"v2_score": 8}}},
    }
    row.update(overrides)
    return row


def _sierra_depth(**overrides):
    row = {
        "schema_version": "sierra_depth_feature_snapshot_v1",
        "row_key": "sierra-depth-row",
        "candidate_id": "NAS100_2026-05-04T17:00:00+00:00",
        "created_at_utc": "2026-05-05T00:00:00+00:00",
        "decision_time_utc": "2026-05-04T17:00:00+00:00",
        "features_present": True,
        "depth_interpretation_allowed": True,
        "feature_status": "FEATURES_EXTRACTED",
        "features": {
            "pre60_median_total_depth10": 1200,
            "event15_median_total_depth10": 900,
            "event15_thin_depth10_rate": 0.3,
            "event15_median_depth10_imbalance": -0.2,
        },
    }
    row.update(overrides)
    return row


def test_missing_model_artifact_builds_feature_bundle_without_prediction():
    rows = build_ml_shadow_rows(
        [(1, _candidate())],
        mso_rows=[(1, _mso())],
        decision_rows=[(1, _decision())],
        mechanical_rows=[(1, _mechanical())],
        sierra_depth_rows=[(1, _sierra_depth())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["ml_shadow_status"] == FEATURE_READY_MODEL_PENDING
    assert row["prediction"]["inference_enabled"] is False
    assert row["prediction"]["ml_score"] is None
    assert row["ml_label_eligibility"] == "SYNTHETIC_PATH_CONTEXT_ONLY"
    assert row["label_contract"]["synthetic_path_label"] == "entry_touched_then_reached_tp1"
    assert not forbidden_feature_keys(row["feature_vector"])
    assert "mechanical_structure_h1_v2_score" in row["feature_vector"]
    assert "path_label" not in json.dumps(row["feature_vector"])


def test_registered_json_model_computes_read_only_prediction(tmp_path):
    model_path = tmp_path / "k55_fixture_model.json"
    model_path.write_text(
        json.dumps(
            {
                "schema_version": MODEL_SCHEMA_VERSION,
                "model_version": "k55_fixture_linear_v1",
                "target_version": TARGET_VERSION,
                "feature_bundle_version": FEATURE_BUNDLE_VERSION,
                "threshold": 0.5,
                "weights": {
                    "bias": -0.2,
                    "decision_verification_passed": 1.0,
                    "orderflow_sierra_features_present": 0.4,
                },
            }
        ),
        encoding="utf-8",
    )

    rows = build_ml_shadow_rows(
        [(1, _candidate())],
        mso_rows=[(1, _mso())],
        decision_rows=[(1, _decision())],
        mechanical_rows=[(1, _mechanical())],
        sierra_depth_rows=[(1, _sierra_depth())],
        model_artifact_path=model_path,
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["ml_shadow_status"] == PREDICTION_COMPUTED
    assert row["prediction"]["inference_enabled"] is True
    assert row["prediction"]["model_version"] == "k55_fixture_linear_v1"
    assert row["prediction"]["ml_signal"] == "ML_SHADOW_WOULD_TAKE"
    assert row["ai_calls"] == 0
    assert row["order_calls"] == 0


def test_invalid_model_artifact_is_action_required(tmp_path):
    model_path = tmp_path / "bad_model.json"
    model_path.write_text(
        json.dumps(
            {
                "schema_version": MODEL_SCHEMA_VERSION,
                "model_version": "bad",
                "target_version": "stale_target",
                "feature_bundle_version": FEATURE_BUNDLE_VERSION,
                "threshold": 0.5,
                "weights": {"bias": 0.0},
            }
        ),
        encoding="utf-8",
    )

    rows = build_ml_shadow_rows(
        [(1, _candidate())],
        mso_rows=[(1, _mso())],
        decision_rows=[(1, _decision())],
        mechanical_rows=[(1, _mechanical())],
        model_artifact_path=model_path,
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert rows[0]["ml_shadow_status"] == "ML_SHADOW_MODEL_ARTIFACT_INVALID_INFERENCE_DISABLED"
    assert "TARGET_VERSION_MISMATCH" in rows[0]["action_required_codes"]


def test_forbidden_feature_keys_detect_post_outcome_names():
    assert forbidden_feature_keys({"safe_feature": 1.0, "broker_actual_r": 1.0}) == ["broker_actual_r"]
    assert forbidden_feature_keys({"path_label_encoded": 1.0}) == ["path_label_encoded"]
