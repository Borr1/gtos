from __future__ import annotations

from scripts.backfill_fvg_ob_confluence_source_geometry import (
    build_enriched_confluence_rows,
    summarize_existing_recovered_geometry,
)


def _candidate(candidate_id: str = "c1") -> dict:
    return {
        "schema_version": "strategy_follow_candidate_v1",
        "created_at_utc": "2026-05-12T03:00:10+00:00",
        "candidate_id": candidate_id,
        "symbol": "GBPJPY",
        "side": "LONG",
        "framework": "fvg_fill",
        "decision_time_utc": "2026-05-12T03:00:00+00:00",
        "h1_setup": {"poi_type": "FVG", "poi_price_level": 214.134},
        "trade_parameters": {"direction": "LONG", "entry_price": 214.134},
        "decision_time_structural_fields": {
            "schema_version": "decision_time_structural_fields_v1",
            "m15_snapshot": {
                "fair_value_gaps": [
                    {
                        "type": "bullish",
                        "bottom": 214.115,
                        "top": 214.153,
                        "midpoint": 214.134,
                        "formation_time": "2026-05-12T00:45:00+00:00",
                        "filled": False,
                    }
                ]
            },
            "h1_snapshot": {"order_blocks": [], "fair_value_gaps": []},
        },
    }


def _confluence(candidate_id: str = "c1") -> dict:
    return {
        "schema_version": "fvg_ob_confluence_forward_v1",
        "created_at_utc": "2026-05-12T03:00:20+00:00",
        "candidate_id": candidate_id,
        "symbol": "GBPJPY",
        "side": "LONG",
        "framework": "fvg_fill",
        "decision_time_utc": "2026-05-12T03:00:00+00:00",
        "bucket": "fvg_only",
        "decision_time_fields": {"framework": "fvg_fill", "h1_poi_type": "FVG"},
        "candidate_outcome_lane": "UNRESOLVED_REQUIRES_FORWARD_JOIN",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }


def test_source_geometry_backfill_appends_recovered_fvg_bounds():
    rows, summary = build_enriched_confluence_rows(
        confluence_rows=[_confluence()],
        candidate_rows=[_candidate()],
        generated_at_utc="2026-05-12T04:00:00+00:00",
    )

    assert summary["status_counts"]["enriched_rows"] == 1
    assert rows[0]["fvg_bounds"]["source_status"] == "MATCHED_M15_FVG_FROM_DECISION_MSO"
    assert rows[0]["fvg_bounds"]["low"] == 214.115
    assert rows[0]["fvg_bounds"]["high"] == 214.153
    assert rows[0]["manual_backfill_status"] == "FVG_OB_EXACT_GEOMETRY_RECOVERED_FROM_STRATEGY_FOLLOW_DECISION_MSO"
    assert rows[0]["no_execution"] is True


def test_source_geometry_backfill_skips_when_confluence_already_has_bounds():
    row = _confluence()
    row["fvg_bounds"] = {"low": 1.0, "high": 2.0}

    rows, summary = build_enriched_confluence_rows(
        confluence_rows=[row],
        candidate_rows=[_candidate()],
        generated_at_utc="2026-05-12T04:00:00+00:00",
    )

    assert rows == []
    assert summary["status_counts"]["already_exact_geometry"] == 1


def test_source_geometry_backfill_reports_existing_recovered_geometry():
    row = _confluence()
    row["fvg_bounds"] = {"low": 214.115, "high": 214.153}
    row["manual_backfill_status"] = "FVG_OB_EXACT_GEOMETRY_RECOVERED_FROM_STRATEGY_FOLLOW_DECISION_MSO"
    row["geometry_recovery_no_leak_status"] = "DECISION_TIME_MSO_ONLY_NO_POST_OUTCOME_FIELDS"
    row["exact_geometry_source_status"] = "FVG_EXACT_BOUNDS_MATCHED_FROM_DECISION_MSO"

    summary = summarize_existing_recovered_geometry([row])

    assert summary["rows"] == 1
    assert summary["status_counts"]["FVG_EXACT_BOUNDS_MATCHED_FROM_DECISION_MSO"] == 1
    assert summary["examples"][0]["candidate_id"] == "c1"
