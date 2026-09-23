import json
from collections import Counter
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_market_expansion_proxy_m1_repair_2026_06_18")


def _load(name: str):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _jsonl(name: str):
    return [json.loads(line) for line in (ROUTE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_proxy_m1_repair_result_boundaries_and_counts():
    result = _load("MARKET_EXPANSION_PROXY_M1_REPAIR_RESULT.json")
    verifier = _load("MARKET_EXPANSION_PROXY_M1_REPAIR_VERIFIER_RESULT.json")
    export_manifest = _load("TARGETED_M1_EXPORT_MANIFEST.json")
    saturation = _load("SATURATION_AUDIT.json")
    candidates = _jsonl("EXACT_M1_REPAIR_CANDIDATE_LEDGER.jsonl")
    events = _jsonl("EXACT_M1_REPAIR_EVENT_LEDGER.jsonl")

    assert result["ok"] is True
    assert verifier["ok"] is True
    assert result["decision"] == "MARKET_EXPANSION_PROXY_M1_REPAIR_COMPLETE_NO_LIVE_AUTHORITY"
    assert result["proxy_candidate_count"] == len(candidates) == 10
    assert result["source_event_count"] == len(events)
    assert result["repaired_exact_m1_event_count"] == sum(
        1 for row in events if row["target2_exact_m1_net_r"] is not None
    )
    assert result["decision_counts"] == dict(sorted(Counter(row["decision"] for row in candidates).items()))
    assert export_manifest["bridge_reachable"] is True
    assert export_manifest["account_info_read"] is False
    assert export_manifest["orderflow_used"] is False
    assert export_manifest["broker_or_order_mutation"] is False
    assert result["activation_weight_now"] == 0.0
    assert result["live_authority"] is False
    assert result["orderflow_used"] is False
    assert result["broker_or_order_mutation"] is False
    assert result["account_info_read"] is False
    assert result["config_or_live_activation_changed"] is False
    assert result["vps_process_touched"] is False
    assert saturation["all_proxy_rows_processed"] is True
    assert saturation["all_proxy_events_processed"] is True
    assert saturation["no_arbitrary_top_n"] is True


def test_proxy_m1_repair_candidate_decisions_are_row_level():
    candidates = _jsonl("EXACT_M1_REPAIR_CANDIDATE_LEDGER.jsonl")
    expected_tags = {
        "mx_aus200_cash_d1_atr_mean_reversion",
        "mx_aus200_cash_d1_volume_surge_reversal",
        "mx_btcusd_d1_donchian_20_breakout",
        "mx_ethusd_d1_donchian_20_breakout",
        "mx_eu50_cash_d1_volume_surge_reversal",
        "mx_fra40_cash_d1_volume_surge_reversal",
        "mx_ger40_cash_d1_atr_mean_reversion",
        "mx_ger40_cash_d1_volume_surge_reversal",
        "mx_jp225_cash_d1_volume_surge_reversal",
        "mx_us30_cash_d1_volume_surge_reversal",
    }
    assert {row["tag"] for row in candidates} == expected_tags
    assert all(row["activation_weight_now"] == 0.0 for row in candidates)
    assert all(row["live_authority"] is False for row in candidates)
    assert all(row["source_event_count"] > 0 for row in candidates)
    assert all(
        row["decision"]
        in {
            "graduate_to_exact_m1_supported_default_off_metadata",
            "remain_proxy_repair_gated_missing_exact_m1_history",
            "transform_to_context_or_veto_due_negative_exact_m1",
        }
        for row in candidates
    )
    for row in candidates:
        if row["decision"] == "graduate_to_exact_m1_supported_default_off_metadata":
            assert row["repaired_exact_m1_event_count"] >= 20
            assert row["target2_exact_m1_summary"]["mean_r"] > 0
