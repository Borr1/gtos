import json
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_candidate_natgas_decomposition_2026_06_18")


def _load(name: str):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def test_natgas_decomposition_preserves_ex_natgas_sleeve():
    result = _load("ASIA_PDL_FADE_NATGAS_DECOMPOSITION_RESULT.json")
    completion = _load("COMPLETION_AUDIT.json")

    assert result["ok"] is True
    assert completion["ok"] is True
    assert result["decision"] == "SPLIT_NATGAS_FROM_ASIA_PDL_FADE__DEPLOYABLE_EX_NATGAS_SURFACE_READY"
    assert result["excluded_cost_repair_symbols"] == ["NATGAS_cash"]
    assert result["natgas_hard_drop_guard_present"] is True
    assert result["tick_spread_floor_R"] >= result["tick_spread_floor_untradeable_R"]
    assert result["natgas_only"]["raw_trade"]["n"] == 18
    assert result["natgas_only"]["splits"]["train"]["n"] == 0
    assert result["natgas_only"]["splits"]["sealed"]["meanR"] < 0
    assert result["ex_natgas"]["raw_trade"]["n"] == 7524
    assert result["ex_natgas"]["every_split_positive"] is True
    assert result["ex_natgas"]["splits"]["train"]["meanR"] > 0
    assert result["ex_natgas"]["splits"]["oos"]["meanR"] > 0
    assert result["ex_natgas"]["splits"]["sealed"]["meanR"] > 0
    assert result["orderflow_used"] is False
    assert result["broker_or_order_mutation"] is False
    assert result["vps_process_touched"] is False


def test_natgas_decomposition_writes_bridge_and_daily_artifacts():
    bridge = _load("MT5_NATGAS_BRIDGE_READONLY_SNAPSHOT.json")
    daily = _load("ASIA_PDL_FADE_EX_NATGAS_DAILY_SERIES.json")
    manifest = _load("OUTPUT_MANIFEST.json")

    assert bridge["read_only"] is True
    assert bridge["symbol"] == "NATGAS_cash"
    assert bridge["native_symbol"] == "NATGAS.cash"
    assert bridge["orderflow_used"] is False
    assert bridge["broker_or_order_mutation"] is False
    assert len(daily) == 2571
    assert "ASIA_PDL_FADE_PER_SYMBOL_LEDGER.jsonl" in manifest["files"]
    assert "MT5_NATGAS_BRIDGE_READONLY_SNAPSHOT.json" in manifest["files"]
