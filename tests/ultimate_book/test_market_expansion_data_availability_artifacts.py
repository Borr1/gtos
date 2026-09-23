import json
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_market_expansion_data_availability_2026_06_18")


def _load(name: str):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _jsonl(name: str):
    return [
        json.loads(line)
        for line in (ROUTE / name).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_market_expansion_inventory_and_boundaries():
    result = _load("MARKET_EXPANSION_DATA_AVAILABILITY_RESULT.json")
    verification = _load("MARKET_EXPANSION_DATA_AVAILABILITY_VERIFICATION_RESULT.json")
    inventory = _load("MARKET_SYMBOL_INVENTORY.json")
    aliases = _load("BROKER_NATIVE_ALIAS_MAP.json")

    assert result["ok"] is True
    assert verification["ok"] is True
    assert result["decision"] == "MARKET_EXPANSION_DATA_AVAILABILITY_READY_FOR_SCORING"
    assert result["broker_native_symbol_count"] == 167
    assert result["validation_ready_symbol_count"] == 164
    assert result["coverage_gap_count"] == 0
    assert result["coverage_gap_closure_complete"] is True
    assert result["export_needed_symbol_count"] == 0
    assert result["visible_symbol_count"] >= 166
    assert result["full_trade_mode_symbol_count"] == 166
    assert result["quarantined_spec_symbol_count"] == 1
    assert result["spec_status_counts"] == {
        "quarantined_non_full_trade_mode": 1,
        "trade_ready": 166,
    }
    assert inventory["bridge"]["strict_symbol_spec_only"] is True
    assert inventory["bridge"]["account_info_read"] is False
    assert "account" not in inventory["bridge"]
    assert inventory["symbol_count"] == 167
    assert len(aliases["aliases"]) == 167
    assert result["orderflow_used"] is False
    assert result["broker_or_order_mutation"] is False
    assert result["vps_process_touched"] is False
    assert result["config_or_live_activation_changed"] is False

    families = result["family_counts"]
    for family in (
        "non_jpy_fx_cross",
        "metals_copper",
        "metal_cross",
        "agri_softs",
        "crypto_alt_or_major",
        "indices_context",
        "dxy_context",
        "single_stock_cfd",
    ):
        assert families[family] > 0
    assert families["non_jpy_fx_cross"] == 19
    assert families["single_stock_cfd"] == 59


def test_market_expansion_gap_commands_and_inspire_not_kill_rows():
    result = _load("MARKET_EXPANSION_DATA_AVAILABILITY_RESULT.json")
    priority_rows = _jsonl("SYMBOL_CLASS_TAXONOMY_PRIORITY_LEDGER.jsonl")
    gap_rows = _jsonl("COVERAGE_GAP_LEDGER.jsonl")
    mechanism_rows = _jsonl("CANDIDATE_MECHANISM_MAP.jsonl")
    saturation = _load("SATURATION_AUDIT.json")
    protocol = (ROUTE / "EXPANSION_VALIDATION_PROTOCOL.md").read_text(encoding="utf-8")
    next_prompt = (ROUTE / "NEXT_PROMPT.md").read_text(encoding="utf-8")

    assert len(priority_rows) == result["broker_native_symbol_count"]
    assert len(gap_rows) == result["coverage_gap_count"]
    assert all(row["blocks_current_candidate_book"] is False for row in gap_rows)
    assert all(row["orderflow_used"] is False and row["read_only"] is True for row in gap_rows)
    assert all(row["asset_class"] for row in gap_rows)
    assert all(row["spec_status"] for row in gap_rows)
    assert all("--yes-live-readonly" in row["safe_export_command"] for row in gap_rows)
    assert all("scripts/export_mt5_research_ohlcv.py" in row["safe_export_command"] for row in gap_rows)
    labels = [
        row["safe_export_command"].split("--label ", 1)[1].split(" ", 1)[0]
        for row in gap_rows
    ]
    assert len(labels) == len(set(labels))

    by_symbol = {row["file_symbol"]: row for row in priority_rows}
    for required_symbol, expected_family in {
        "AAPL": "single_stock_cfd",
        "SPCX": "single_stock_cfd",
        "AUDCAD": "non_jpy_fx_cross",
    }.items():
        assert by_symbol[required_symbol]["family"] == expected_family
    assert by_symbol["SPCX"]["spec_status"] == "quarantined_non_full_trade_mode"
    assert by_symbol["SPCX"]["validation_source_ready"] is True
    assert by_symbol["SPCX"]["validation_ready"] is False
    assert by_symbol["SPCX"]["trade_mode_full"] is False
    assert by_symbol["SPCX"]["missing_timeframes"] == []
    assert by_symbol["AAPL"]["asset_class"] == "single_stock_cfd"
    assert by_symbol["AUDCAD"]["asset_class"] == "fx"
    assert by_symbol["NATGAS_cash"]["hard_dropped_runtime_status"] is True
    assert by_symbol["HEATOIL_c"]["hard_dropped_runtime_status"] is True
    assert by_symbol["NATGAS_cash"]["validation_ready"] is False
    assert "limit-entry revival lane" in by_symbol["NATGAS_cash"]["transformed_use"]
    assert all(row["useful_inspiration"] for row in priority_rows)
    assert all(row["revival_gate"] for row in priority_rows)
    assert all("source_spans" in row for row in priority_rows)
    assert all("spread_snapshot" in row for row in priority_rows)

    families = {row["family"] for row in mechanism_rows}
    assert "tick_volume" in families
    assert "dxy_context" in families
    assert all("orderflow" in row["forbidden_data"] for row in mechanism_rows)
    assert saturation["no_arbitrary_top_n"] is True
    assert saturation["not_blocking_current_live_candidate_book"] is True
    assert "Data availability is only the first gate" in protocol
    assert "goal_session_research_discipline.md" in next_prompt
    assert "Do not use orderflow/depth" in next_prompt
