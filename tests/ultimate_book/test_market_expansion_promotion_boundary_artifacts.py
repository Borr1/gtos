import json
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_market_expansion_promotion_boundary_2026_06_18")
EXPECTED_DECISION = "MARKET_EXPANSION_PROMOTION_BOUNDARY_READY_NOT_PROMOTED"
EXPECTED_REQ_IDS = {
    "MX-PROMO-REQ-001",
    "MX-PROMO-REQ-002",
    "MX-PROMO-REQ-003",
    "MX-PROMO-REQ-004",
    "MX-PROMO-REQ-005",
}


def _load(name: str):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _jsonl(name: str):
    return [json.loads(line) for line in (ROUTE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_promotion_boundary_default_off_not_promoted():
    result = _load("MARKET_EXPANSION_PROMOTION_BOUNDARY_RESULT.json")
    verifier = _load("MARKET_EXPANSION_PROMOTION_BOUNDARY_VERIFIER_RESULT.json")
    completion = _load("COMPLETION_AUDIT.json")
    zero = _load("ZERO_ACTIVE_BEHAVIOR_AUDIT.json")
    config_patch = _load("CONFIG_PATCH_PROPOSAL.json")
    requirements = _jsonl("UNRESOLVED_REQUIREMENT_LEDGER.jsonl")
    blocker_repair = _jsonl("BLOCKER_REPAIR_REQUIREMENT_LEDGER.jsonl")
    boundary = _jsonl("PROMOTION_BOUNDARY_LEDGER.jsonl")

    activation = config_patch["activation_patch_yaml"]["gtos_vnext_runtime"]
    rollback = config_patch["rollback_patch_yaml"]["gtos_vnext_runtime"]
    boundary_status = {row["gate"]: row["status"] for row in boundary}

    assert result["ok"] is True
    assert verifier["ok"] is True
    assert completion["ok"] is True
    assert result["decision"] == EXPECTED_DECISION
    assert result["live_authority"] is False
    assert result["deployment_ready"] is False
    assert result["promotion_ready"] is False
    assert result["config_patch_applied"] is False
    assert result["runtime_effect"] == "none_market_expansion_default_off_promotion_boundary_only"
    assert zero["zero_active_behavior_ok"] is True
    assert zero["active_config_include_market_expansion_book"] is False
    assert zero["active_config_market_expansion_sleeves"] == []
    assert zero["bridge_default_include_market_expansion_book"] is False
    assert zero["bridge_default_market_expansion_sleeves"] == []
    assert zero["explicit_allowlist_market_expansion_count"] == 14
    assert zero["empty_allowlist_decision_status"] == "fail_closed_market_expansion_requires_explicit_sleeves"
    assert config_patch["status"] == "not_applied_owner_action_only"
    assert activation["ultimate_book_include_market_expansion_book"] is True
    assert activation["ultimate_book_market_expansion_profile"] == "default_off_market_expansion_d1_target2_v1"
    assert len(activation["ultimate_book_market_expansion_sleeves"]) == 14
    assert rollback == {
        "ultimate_book_include_market_expansion_book": False,
        "ultimate_book_market_expansion_sleeves": [],
    }
    assert {row["requirement_id"] for row in requirements} == EXPECTED_REQ_IDS
    assert blocker_repair == requirements
    assert set(result["deployment_not_ready_requirement_ids"]) == EXPECTED_REQ_IDS
    assert set(result["deployment_not_ready_reasons"]) == {row["requirement"] for row in requirements}
    assert boundary_status["session_commission_slippage_swap_fill_authority"] == "not_closed"
    assert boundary_status["owner_vps_action"] == "not_executed_by_mac_route"


def test_promotion_boundary_pretrade_packets_and_bridge_limits():
    result = _load("MARKET_EXPANSION_PROMOTION_BOUNDARY_RESULT.json")
    summary = _load("PRETRADE_COST_PACKET_SUMMARY.json")
    root_refusal = _load("ROOT_CONFIG_PRETRADE_REFUSAL_AUDIT.json")
    bridge = _load("BRIDGE_SURFACE_NEGATIVE_PROOF.json")
    forbidden = _load("FORBIDDEN_CALL_SCAN.json")
    rows = _jsonl("PRETRADE_COST_PACKET_LEDGER.jsonl")

    assert len(rows) == 28
    assert summary["row_count"] == 28
    assert summary["status_counts"] == {"PASSED": 28}
    assert summary["refusal_count"] == 0
    assert summary["swap_captured_count"] == 28
    assert result["profile_merged_pretrade_packet_row_count"] == 28
    assert result["profile_merged_pretrade_packet_pass_count"] == 28
    assert {row["packet"]["status"] for row in rows} == {"PASSED"}
    assert all(row["refusal_reason"] is None for row in rows)
    assert all(row["packet"]["symbol_spec_source_status"] == "captured" for row in rows)
    assert all((row["packet"]["swap"] or {}).get("source_status") == "captured" for row in rows)
    assert root_refusal["status"] == "REFUSED"
    assert root_refusal["refusal_reason"] == "missing_broker_account_profile_namespace"
    assert bridge["installed_client_imported"] is True
    assert bridge["has_symbol_info"] is True
    assert bridge["has_symbol_info_tick"] is True
    assert bridge["has_symbol_info_session_trade"] is False
    assert bridge["has_symbol_info_session_quote"] is False
    assert bridge["commission_like_symbol_info_keys"] == []
    assert result["bridge_commission_like_symbol_info_key_count"] == 0
    assert forbidden["ok"] is True
    assert forbidden["matches"] == []
