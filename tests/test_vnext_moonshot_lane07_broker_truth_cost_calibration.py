from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ROUTE_DIR = (
    REPO_ROOT
    / "research/operations/vnext_moonshot_lane07_broker_truth_cost_calibration_2026_06_01"
)

ACTIVE_SYMBOLS = {
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
}


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lane07_symbol_spec_preserves_all_24_symbols_and_aliases():
    rows = _read_jsonl(ROUTE_DIR / "LANE07_SYMBOL_SPEC_SESSION_LEDGER.jsonl")
    by_symbol = {row["symbol"]: row for row in rows}

    assert set(by_symbol) == ACTIVE_SYMBOLS
    assert by_symbol["NAS100"]["broker_symbol"] == "NDX100"
    assert by_symbol["GER40"]["broker_symbol"] == "GER30"
    assert by_symbol["US30_cash"]["broker_symbol"] == "US30"
    assert by_symbol["XAUUSD"]["trade_tick_value_status"] == "BROKER_REAL_FROM_LANE06_SYMBOL_INFO"
    assert by_symbol["AUDJPY"]["trade_tick_value_status"] == "MISSING_EXACT_TICK_VALUE_EXPORT_REQUIRED"
    assert all(row["session_status"].startswith("MISSING_MT5_SESSION") for row in rows)


def test_lane07_broker_truth_keeps_broker_history_and_false_close_proof():
    rows = _read_jsonl(ROUTE_DIR / "LANE07_BROKER_TRUTH_LEDGER.jsonl")
    row_types = {row["row_type"] for row in rows}

    assert "mt5_history_order" in row_types
    assert "mt5_history_deal" in row_types
    assert "mt5_open_position" in row_types
    assert "lane06_lifecycle_reconciliation" in row_types
    assert any((row.get("raw") or {}).get("comment") == "preflight_test" for row in rows)
    assert any(
        row["row_type"] == "lane06_projected_vs_broker_reconciliation"
        and (row.get("raw") or {}).get("reconciliation_status")
        == "BROKER_CONTRADICTION_OPEN_POSITION_FALSE_CLOSE_NOTIFICATION"
        for row in rows
    )


def test_lane07_cost_and_downstream_contract_are_nonblocking():
    cost_rows = _read_jsonl(ROUTE_DIR / "LANE07_COST_CALIBRATION_LEDGER.jsonl")
    gap_rows = _read_jsonl(ROUTE_DIR / "LANE07_SOURCE_GAP_LEDGER.jsonl")
    contract = _read_json(ROUTE_DIR / "LANE07_DOWNSTREAM_CONTRACT.json")

    spread_symbols = {
        row["symbol"]
        for row in cost_rows
        if row.get("row_type") == "symbol_spread_snapshot_cost_proxy"
    }
    assert spread_symbols == ACTIVE_SYMBOLS
    assert any(
        row.get("row_type") == "symbol_commission_swap_observation"
        and row.get("symbol") == "XAUUSD"
        and row.get("entry_commission_per_lot_observed") is not None
        for row in cost_rows
    )
    assert {
        row["symbol"]
        for row in gap_rows
        if row.get("field") == "broker_trading_sessions_by_weekday"
    } == ACTIVE_SYMBOLS
    assert "feature_store" in contract["consumers"]
    assert "label_store" in contract["consumers"]
    assert "digital_twin_replay" in contract["consumers"]
    assert "do not block" in contract["missing_data_rule"].lower()
