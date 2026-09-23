from __future__ import annotations

from src.research_infra.wave3_follow_avoid_mixed_numeric_confluence import (
    SCHEMA_VERSION,
    build_numeric_confluence_source,
    final_numeric_confluence_mapping,
    summarize_numeric_confluence_sources,
)


def _metric(value: float, count: int = 1) -> dict:
    return {
        "sum": value,
        "mean": value / count,
        "match_rows_with_metric": count,
        "positive_rows": 1 if value > 0 else 0,
        "negative_rows": 1 if value < 0 else 0,
        "zero_rows": 1 if value == 0 else 0,
    }


def _row(**overrides) -> dict:
    row = {
        "review_row_id": "ROW-1",
        "event_scope": {"symbol": "XAUUSD", "side": "LONG", "route_session": "london"},
        "source_path": "research/source.jsonl",
        "source_component": "registry_scorer_module",
        "evidence_family": "unit_test_numeric_confluence",
        "timestamp_utc": "2026-06-04T20:00:00+00:00",
        "r_metric_traces": {
            "cost_adjusted_simulated_r": _metric(2.0),
            "stress_simulated_r": _metric(1.0),
            "proxy_score": _metric(0.5),
            "effective_n": _metric(25.0),
        },
    }
    row.update(overrides)
    return row


def test_numeric_confluence_source_contract_follow_is_not_trade_permission():
    source = build_numeric_confluence_source(
        _row(),
        decision="FOLLOW",
        cfg={"numeric_confluence_now_utc": "2026-06-04T20:30:00+00:00"},
    )

    assert source["schema_version"] == SCHEMA_VERSION
    assert source["source_id"] == "ROW-1"
    assert source["direction"] == "LONG"
    assert source["strength"] > 0
    assert source["confidence"] > 0
    assert source["reliability_history"]["effective_n"] == 25.0
    assert source["source_completeness"]["status"] == "complete"
    assert source["freshness"]["status"] == "timestamp_present"
    assert source["conflict_reason"] == "source_pressure_supports_direction_not_trade_permission"
    assert source["follow_is_trade_permission"] is False
    assert source["candidate_use_allowed_now_by_confluence"] is False


def test_numeric_confluence_avoid_and_mixed_are_structured():
    avoid = build_numeric_confluence_source(
        _row(
            review_row_id="AVOID-1",
            target_stop_order_class="STOP_FIRST_PROXY_DOMINANT",
            r_metric_traces={
                "cost_adjusted_simulated_r": _metric(-2.0),
                "stress_simulated_r": _metric(-1.0),
                "proxy_score": _metric(-0.5),
                "effective_n": _metric(30.0),
            },
        ),
        decision="AVOID",
        cfg={"numeric_confluence_now_utc": "2026-06-04T20:30:00+00:00"},
    )
    mixed = build_numeric_confluence_source(
        _row(
            review_row_id="MIXED-1",
            timestamp_utc=None,
            r_metric_traces={
                "cost_adjusted_simulated_r": _metric(2.0),
                "stress_simulated_r": _metric(-3.0),
                "proxy_score": _metric(0.0),
                "effective_n": _metric(10.0),
            },
        ),
        decision="MIXED",
        cfg={"numeric_confluence_now_utc": "2026-06-04T20:30:00+00:00"},
    )
    summary = summarize_numeric_confluence_sources([avoid, mixed])
    mapping = final_numeric_confluence_mapping(
        selected_decision="MIXED",
        resolution_evidence={"mode": "strict", "raw_decision_counts": {"AVOID": 1, "MIXED": 1}},
        confluence_summary=summary,
    )

    assert avoid["avoid_invalidation_type"] == "stop_first_or_adverse_path"
    assert avoid["conflict_reason"] == "avoid_invalidation:stop_first_or_adverse_path"
    assert mixed["structured_disagreement"]["present"] is True
    assert mixed["freshness"]["status"] == "source_timestamp_missing"
    assert mixed["source_completeness"]["status"] == "partial"
    assert summary["source_count"] == 2
    assert summary["structured_disagreement_sources"] == ["MIXED-1"]
    assert mapping["selected_label"] == "MIXED"
    assert mapping["action_type"] == "structured_disagreement_requires_downstream_resolution"
    assert mapping["runtime_candidate_use_permitted_by_confluence"] is False
