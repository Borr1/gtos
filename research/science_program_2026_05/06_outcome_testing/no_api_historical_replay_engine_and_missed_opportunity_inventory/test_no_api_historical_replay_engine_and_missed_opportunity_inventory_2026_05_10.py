from __future__ import annotations

import json
from pathlib import Path

import build_no_api_historical_replay_engine_and_missed_opportunity_inventory_2026_05_10 as builder
import verify_no_api_historical_replay_engine_and_missed_opportunity_inventory_2026_05_10 as verifier


def test_source_family_and_partition_classification() -> None:
    tick_path = Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks\XAUUSD\2026-05-04.parquet")
    assert builder.classify_source_family(tick_path, "absolute_main_tick_root") == "MT5_TICK_PARQUET_CAPTURE"
    assert builder.evidence_class_for("MT5_TICK_PARQUET_CAPTURE") == "LOCAL_MARKET_DATA_CONTEXT_ONLY"
    assert builder.partition_for("MT5_TICK_PARQUET_CAPTURE", "LOCAL_MARKET_DATA_CONTEXT_ONLY", tick_path) == "context_only"

    sierra_path = Path(r"C:\SierraChart\Data\XAUUSD.scid")
    assert builder.classify_source_family(sierra_path, "sierra_chart_data_root") == "SIERRA_NATIVE_CONTEXT"

    replay_path = Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\external\validation\calendar_macro_bundle_v1\historical_opportunities\raw_ohlc_prequential_replay\raw_ohlc_prequential_events_20260501T120351Z.jsonl")
    assert builder.classify_source_family(replay_path, "absolute_main_data_root") == "RAW_OHLC_PRE_AI_REPLAY_LOG"
    assert builder.partition_for("RAW_OHLC_PRE_AI_REPLAY_LOG", "MECHANICAL_PRE_AI_REPLAY_CONTROL_OR_DISCOVERY_ONLY", replay_path) == "discovery_development"


def test_kill_zone_classifier() -> None:
    assert builder.kill_zone_for("XAUUSD", "2026-05-04T07:15:00+00:00") == "London"
    assert builder.kill_zone_for("XAUUSD", "2026-05-04T13:05:00+00:00") == "NY_SKIP_FIRST_15"
    assert builder.kill_zone_for("USDJPY", "2026-05-04T00:30:00+00:00") == "Tokyo"
    assert builder.kill_zone_for("NAS100", "2026-05-04T07:15:00+00:00") == "outside_configured_kill_zone"


def test_safe_flags_recursive_checker() -> None:
    payload = builder.base_payload("unit_test", nested={"validation_safe": False, "promotion_verdict": builder.PROMOTION_VERDICT})
    assert verifier.safe_flag_issues(payload) == []
    bad = dict(payload)
    bad["nested"] = {"validation_safe": True}
    assert verifier.safe_flag_issues(bad)


def test_generated_artifacts_if_present_are_verifiable() -> None:
    result_path = builder.ROUTE_DIR / verifier.RESULT_NAME
    if not result_path.exists():
        return
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert result["validation_safe"] is False
    assert result["outcome_review_opened"] is False
    assert result["live_effect"] is False
    assert result["selected_next_route_id"] == "NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE"
