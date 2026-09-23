from __future__ import annotations

from src.research_infra.mso_snapshot_join import (
    JOIN_MISSING,
    JOINED_EXACT,
    build_candidate_mso_join_row,
    canonical_mso_snapshot,
)


def _evaluation(**overrides):
    row = {
        "schema_version": "strategy_follow_evaluation_v1",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00_pre_ai",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "session": "london",
        "kill_zone": "london",
        "source_file": "live_orchestrator_mso_pre_ai",
        "source_hash": "mso-hash",
        "evaluation_stage": "MSO_COMPUTED_PRE_AI",
        "ai_dependency": "NO_AI_REQUIRED_FOR_ROW",
        "ai_status": "NOT_CALLED_AT_ROW_TIME",
        "mso_summary": {
            "timestamp_utc": "2026-05-04T07:15:05+00:00",
            "timeframes": {
                "D1": {"structure_direction": "bullish", "order_block_count": 2},
                "H4": {"structure_direction": "bearish", "order_block_count": 3},
                "H1": {"structure_direction": "bearish", "order_block_count": 4},
                "M15": {"structure_direction": "transitional", "order_block_count": 5},
            },
        },
        "strategy_snapshots": [{"strategy_id": "V2_STRUCT_OB_BOUNDARY"}],
    }
    row.update(overrides)
    return row


def _candidate(**overrides):
    row = {
        "schema_version": "strategy_follow_candidate_v1",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "session": "london",
        "kill_zone": "london",
        "side": "SHORT",
        "framework": "ob_retest",
        "h1_setup": {"poi_identified": True, "poi_type": "OB", "poi_price_level": 2300.25, "zone": "premium"},
        "frameworks_evaluated": {
            "ob_retest": "qualified=True reason='target H1 OB present'",
            "fvg_fill": "qualified=False reason='no fvg'",
        },
        "mso_summary": {
            "timeframes": {
                "D1": {"structure_direction": "bullish", "order_block_count": 2},
                "H4": {"structure_direction": "bearish", "order_block_count": 3},
                "H1": {"structure_direction": "bearish", "order_block_count": 4},
                "M15": {"structure_direction": "transitional", "order_block_count": 5},
            }
        },
    }
    row.update(overrides)
    return row


def test_canonical_snapshot_carries_bias_poi_and_framework_qualification():
    snapshot = canonical_mso_snapshot(_evaluation(), _candidate())

    assert snapshot["schema_version"] == "mso_decision_snapshot_v1"
    assert snapshot["timeframe_bias"]["H1"] == "bearish"
    assert snapshot["candidate_poi"]["poi_type"] == "OB"
    assert snapshot["framework_qualification"]["frameworks"]["ob_retest"]["qualified"] is True
    assert snapshot["source_provenance"]["source_file"] == "live_orchestrator_mso_pre_ai"


def test_join_selects_exact_live_mso_over_shadow_observer():
    shadow = _evaluation(
        source_file="shadow_observer_mso_no_ai",
        candidate_id="XAUUSD_2026-05-04T07:15:00+00:00_shadow_observer",
        broker_symbol="XAUUSD.shadow",
    )
    live = _evaluation()

    row = build_candidate_mso_join_row(
        10,
        _candidate(),
        [(1, shadow), (2, live)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert row["join_status"] == JOINED_EXACT
    assert row["evaluation_line_no"] == 2
    assert row["mso_snapshot"]["source_provenance"]["source_file"] == "live_orchestrator_mso_pre_ai"
    assert row["context_comparison_status"] == "JOINED_CONTEXT_MATCHED"


def test_missing_exact_mso_writes_join_missing_with_nearest_diagnostic():
    row = build_candidate_mso_join_row(
        10,
        _candidate(decision_time_utc="2026-05-04T07:30:00+00:00"),
        [(1, _evaluation())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert row["join_status"] == JOIN_MISSING
    assert row["context_comparison_status"] == JOIN_MISSING
    assert row["nearest_mso_delta_seconds"] == 900.0
    assert row["mso_snapshot"] is None
    assert row["promotion_verdict"] == "NO_PROMOTION_VERDICT"


def test_join_flags_context_mismatch():
    row = build_candidate_mso_join_row(
        10,
        _candidate(
            mso_summary={
                "timeframes": {
                    "D1": {"structure_direction": "bearish", "order_block_count": 2},
                    "H4": {"structure_direction": "bearish", "order_block_count": 3},
                    "H1": {"structure_direction": "bearish", "order_block_count": 4},
                    "M15": {"structure_direction": "transitional", "order_block_count": 5},
                }
            }
        ),
        [(1, _evaluation())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert row["join_status"] == JOINED_EXACT
    assert row["context_comparison_status"] == "MSO_CONTEXT_MISMATCH"
    assert row["context_mismatches"][0]["field"] == "mso_summary.timeframes.D1.structure_direction"
