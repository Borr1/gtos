from __future__ import annotations

import json
from pathlib import Path

from build_vnext_moonshot_lane01_data_universe_source_authority import (
    ACTIVE_SYMBOLS,
    REQUIRED_TIMEFRAMES,
    ROUTE_DIR,
)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_lane01_inventory_authority_and_parser_contracts_are_materialized():
    inventory = load_jsonl(ROUTE_DIR / "DATA_SOURCE_INVENTORY.jsonl")
    parser_results = load_jsonl(ROUTE_DIR / "PARSER_CHECK_RESULTS.jsonl")
    authority = load_json(ROUTE_DIR / "SOURCE_AUTHORITY_MAP.json")
    parser_registry = load_json(ROUTE_DIR / "PARSER_CHECKER_REGISTRY.json")

    assert inventory
    assert len(parser_results) == len(inventory)
    assert authority["global_counts"]["file_count"] == len(inventory)
    assert authority["global_counts"]["authority_counts"]["broker_real_truth"] > 0
    assert authority["global_counts"]["authority_counts"]["mt5_market_history"] > 0
    assert authority["global_counts"]["authority_counts"]["local_mt5_cache"] > 0
    assert authority["global_counts"]["authority_counts"]["selected_denominator"] > 0
    assert {p["parser_id"] for p in parser_registry["parsers"]} >= {
        "csv_ohlc_time_series_v1",
        "parquet_tick_bid_ask_v1",
        "jsonl_runtime_route_ledger_v1",
        "json_summary_contract_v1",
        "mt5_native_cache_inventory_v1",
    }


def test_lane01_gap_ledger_preserves_all_symbol_timeframe_and_broker_requirements():
    gaps = load_jsonl(ROUTE_DIR / "SOURCE_GAP_LEDGER.jsonl")
    keys = {
        (row.get("symbol"), row.get("timeframe"))
        for row in gaps
        if row.get("gap_family") == "market_history_timeframe_coverage"
    }
    assert len(keys) == len(ACTIVE_SYMBOLS) * len(REQUIRED_TIMEFRAMES)
    for symbol in ACTIVE_SYMBOLS:
        for timeframe in REQUIRED_TIMEFRAMES:
            assert (symbol, timeframe) in keys

    families = {row["gap_family"] for row in gaps}
    assert "selected_denominator_tick_availability_status" in families
    assert "selected_denominator_m1_availability_status" in families
    assert "broker_specs" in families
    assert "account_deal_order_position_history" in families
    assert "cost_fields" in families


def test_lane01_dependency_and_runtime_boundaries_are_explicit():
    dependencies = load_jsonl(ROUTE_DIR / "DEPENDENCY_STATE_LEDGER.jsonl")
    acquisition = load_jsonl(ROUTE_DIR / "SOURCE_ACQUISITION_ATTEMPT_LEDGER.jsonl")
    result_use = load_json(ROUTE_DIR / "RESULT_USE_STATUS.json")
    contracts = load_json(ROUTE_DIR / "DOWNSTREAM_SOURCE_CONTRACTS.json")

    dep_by_id = {row["dependency_id"]: row for row in dependencies}
    assert dep_by_id["absolute_master_route"]["exists"] is True
    assert dep_by_id["absolute_master_route"]["dependency_state"] == "present_consumed"
    assert dep_by_id["lane02_selected_denominator_counts"]["selected_surface_rows"] == 289600

    broker_export_rows = [
        row for row in acquisition if row["root_id"] == "direct_broker_server_mt5_readonly_export"
    ]
    assert broker_export_rows
    assert broker_export_rows[0]["status"] == "not_executed_in_this_lane_due_compliant_vps_dependency_recorded"

    assert result_use["lane01_owns_r_scoring"] is False
    assert result_use["runtime_effect_boundary"] == "no live behavior change"
    assert "historical_microscope" in contracts["contracts"]
    assert "broker_truth_cost_calibration" in contracts["contracts"]
    assert "command_center_production_dossier" in contracts["contracts"]
