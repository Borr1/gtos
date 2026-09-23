import json
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_market_expansion_swap_mode5_holding_repair_2026_06_18")
EXPECTED_DECISION = "MARKET_EXPANSION_SWAP_MODE5_HOLDING_PROXY_REPAIRED_DEFAULT_OFF_NOT_LIVE_AUTHORITY"


def _load(name):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _jsonl(name):
    return [json.loads(line) for line in (ROUTE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_swap_mode5_holding_boundary_counts_and_sources():
    result = _load("SWAP_MODE5_HOLDING_REPAIR_RESULT.json")
    verifier = _load("SWAP_MODE5_HOLDING_REPAIR_VERIFIER_RESULT.json")
    completion = _load("COMPLETION_AUDIT.json")
    saturation = _load("SATURATION_SELF_RED_TEAM_AUDIT.json")
    source_index = _load("PRIMARY_SOURCE_INDEX.json")
    rows = _jsonl("SOURCE_EVENT_SWAP_HOLDING_PROXY_LEDGER.jsonl")
    manifest = _jsonl("SOURCE_MANIFEST_LEDGER.jsonl")

    assert result["ok"] is True
    assert verifier["ok"] is True
    assert completion["ok"] is True
    assert saturation["ok"] is True
    assert result["decision"] == EXPECTED_DECISION
    assert result["live_authority"] is False
    assert result["deployment_ready"] is False
    assert result["promotion_ready"] is False
    assert result["config_patch_applied"] is False
    assert result["runtime_effect"] == "none_swap_mode5_holding_proxy_only"
    assert len(rows) == 2596
    assert result["mode5_event_count"] == 913
    assert result["point_mode_event_count"] == 1683
    assert len(manifest) == 14
    assert all(row["present"] is True for row in manifest)
    assert "mql5.com" in source_index["official_sources"][0]["url"]
    assert "360" in source_index["formula_facts"]["interest_current_formula"]


def test_swap_mode5_holding_proxy_preserves_live_gaps():
    result = _load("SWAP_MODE5_HOLDING_REPAIR_RESULT.json")
    summary = _load("SOURCE_EVENT_SWAP_HOLDING_PROXY_SUMMARY.json")
    requirements = _jsonl("UNRESOLVED_REQUIREMENT_LEDGER.jsonl")
    rows = _jsonl("SOURCE_EVENT_SWAP_HOLDING_PROXY_LEDGER.jsonl")
    forbidden = _load("FORBIDDEN_CALL_SCAN.json")

    assert summary["event_count"] == 2596
    assert summary["computed_event_count"] == 2596
    assert summary["mode5_event_count"] == 913
    assert summary["point_mode_event_count"] == 1683
    assert result["computed_event_count"] == summary["computed_event_count"]
    assert any(row["swap_conversion_status"] == "interest_current_mode5_holding_swap_proxy_computed" for row in rows)
    assert any(row["swap_conversion_status"] == "point_mode_holding_swap_proxy_computed" for row in rows)
    assert all(row["total_swap_r_per_lot_risk_proxy"] is not None for row in rows)
    assert all(row["live_authority_ready"] is False for row in rows)
    assert {row["requirement_id"] for row in requirements} == {
        "MX-SWAP-HOLDING-REQ-001",
        "MX-SWAP-HOLDING-REQ-002",
        "MX-SWAP-HOLDING-REQ-003",
        "MX-SWAP-HOLDING-REQ-004",
    }
    assert forbidden["ok"] is True
    assert forbidden["matches"] == []
