import json
from pathlib import Path


ROUTE = Path(
    "research/operations/final_moonshot_candidate_bridge_spec_ltf_work_2026_06_18"
)


def _load(name: str):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _load_jsonl(name: str):
    return [
        json.loads(line)
        for line in (ROUTE / name).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_candidate_bridge_route_closes_ltf_gap_without_mutation():
    result = _load("CANDIDATE_BRIDGE_SPEC_LTF_WORK_RESULT.json")
    verification = _load("CANDIDATE_BRIDGE_SPEC_LTF_WORK_VERIFICATION_RESULT.json")

    assert result["ok"] is True
    assert verification["ok"] is True
    assert result["bridge_read_only"] is True
    assert result["candidate_symbol_count"] == 14
    assert result["ftmo_bridge_native_symbol_count"] == 14
    assert result["ltf_gap_count_after_bridge_export"] == 0
    assert set(result["m1_repaired_symbols"]) == {"XPDUSD", "XPTUSD", "XRPUSD"}
    assert result["orderflow_used"] is False
    assert result["broker_or_order_mutation"] is False
    assert result["vps_process_touched"] is False


def test_candidate_bridge_route_preserves_broker_specific_work_split():
    result = _load("CANDIDATE_BRIDGE_SPEC_LTF_WORK_RESULT.json")
    decisions = {
        row["symbol"]: row
        for row in _load_jsonl("CANDIDATE_BRIDGE_WORK_DECISION_LEDGER.jsonl")
    }

    assert set(result["profile_patchable_dual_broker_symbols"]) == {
        "AUDUSD",
        "EURGBP",
        "EURUSD",
        "GBPUSD",
        "NZDUSD",
        "USDCAD",
        "USDCHF",
    }
    assert set(result["ftmo_patchable_subset_symbols"]) == {
        "DASHUSD",
        "LTCUSD",
        "XPDUSD",
        "XPTUSD",
        "XRPUSD",
        "XTZUSD",
    }
    assert result["research_only_cost_revival_symbols"] == ["NATGAS_cash"]
    assert decisions["DASHUSD"]["deployment_status"] == (
        "ftmo_patchable_requires_broker_specific_subset_or_redacted_account_export"
    )
    assert decisions["NATGAS_cash"]["deployment_status"] == "research_only_cost_revival_work"
    assert decisions["XPDUSD"]["m1_stress_available"] is True
