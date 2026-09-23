from __future__ import annotations

import build_vnext_moonshot_lane05_feature_store_v1 as builder


def test_feature_schema_covers_required_families_without_outcome_features() -> None:
    schema = builder.feature_schema()
    families = {row["feature_namespace"] for row in schema}
    assert {"source_completeness", "news_calendar", "stale_label_flags", "selected_cell_risk_proof"} <= families
    forbidden = []
    for row in schema:
        name = row["feature_name"].lower()
        for token in builder.FORBIDDEN_FEATURE_TOKENS:
            if token in name and not (row["feature_name"].startswith("stale_label_") and token == "label_h"):
                forbidden.append(row["feature_name"])
    assert forbidden == []


def test_timeline_feature_row_excludes_path_labels_and_keeps_source_gaps() -> None:
    source_row = {
        "candidate_id": "cand_demo",
        "chosen_policy": "partial_be_runner",
        "cost_r": None,
        "cost_status": "missing_historical_live_cost_lifecycle_fields",
        "entry_time_utc": "2026-04-27T01:00:00+00:00",
        "exit_reason": "stop_loss",
        "final_r": -1.0,
        "framework": "broader_origin",
        "liquidity_sweep_proxy_state": "swept_prior_20_low_reclaimed_above",
        "m1_availability_status": "local_m1_bar_available_for_entry_minute",
        "mae_r": -1.2,
        "mfe_r": 0.8,
        "origin_family": "liquidity_sweep_reclaim",
        "path_class": "loss_sl_or_stop_policy_exit",
        "side": "LONG",
        "source_path": "data/mt5_research_exports/phase3_m15_2022_2026_fn_chunked_v1/XAGUSD_M15.csv",
        "source_quality_status": "m1_entry_minute_available",
        "source_time_utc": "2026-04-27T01:00:00+00:00",
        "source_use_state": "m15_ordered_path_proxy_with_m1_availability_state",
        "source_window_complete": True,
        "spread_r_bucket": "spread_or_cost_r_missing",
        "strict_tick_event_status": None,
        "symbol": "XAGUSD",
        "tick_availability_status": "local_tick_source_date_absent_after_data_ticks_search",
        "trend_state_20": "down",
        "volatility_state_14_vs_50": "recent_range_expansion_vs_atr50",
    }
    feature_row = builder.build_timeline_feature_row(
        source_row,
        line_number=1,
        source_hash="abc",
        strict_tick_index={},
        selected_cell_index={},
        scheduler_index={},
        correlation_index={},
        regime_index={},
        external_index={},
        generated_at="2026-06-01T00:00:00+00:00",
    )
    features = feature_row["features"]
    assert "final_r" not in features
    assert "exit_reason" not in features
    assert "mfe_r" not in features
    assert "path_class" not in features
    assert features["is_liquidity_sweep_reclaim"] is True
    assert features["cost_source_missing"] is True
    assert feature_row["source_gaps"]
    assert builder.feature_row_has_forbidden_fields(feature_row) == []


def test_external_macro_feature_respects_publication_asof() -> None:
    after_candidate = {
        "fred__available": True,
        "fred__VIXCLS__published_at_utc": "2026-04-28T00:00:00+00:00",
        "fred__VIXCLS__value": 99.0,
        "symbol": "XAUUSD",
    }
    values, gaps, state = builder.external_values(after_candidate, "2026-04-27T01:00:00+00:00")
    assert values["macro_fred_vixcls_value"] is None
    assert state == "snapshot_joined_but_some_publication_asof_invalid"
    assert any(gap["code"] == "macro_fred_vixcls_value_publication_after_candidate" for gap in gaps)


def test_canonical_candidate_feature_row_records_market_state_gap_instead_of_dropping_row() -> None:
    source_row = {
        "candidate_time_utc": "2026-03-06 07:30:00",
        "canonical_candidate_id": "lane03_cand_demo",
        "canonical_duplicate_key": "lane03_dup_demo",
        "first_source_path": "research/source.jsonl.gz",
        "framework": "breaker_re_entry",
        "mechanism_family": "breaker_re_entry",
        "origin_family": "market_bar_enumeration",
        "session": "unknown_session",
        "side": "unknown_side",
        "symbol": "USDCHF",
    }
    row = builder.build_canonical_candidate_feature_row(
        source_row,
        line_number=7,
        source_hash="abc",
        generated_at="2026-06-01T00:00:00+00:00",
    )
    assert row["features"]["is_breaker_re_entry"] is True
    assert row["features"]["candidate_time_known"] is True
    assert row["source_gaps"][0]["code"] == "lane03_market_state_features_not_materialized"
    assert builder.feature_row_has_forbidden_fields(row) == []
