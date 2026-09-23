import json
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_market_expansion_broker_authority_probe_2026_06_18")
EXPECTED_DECISION = "BROKER_AUTHORITY_PARTIAL_REPAIR_DEFAULT_OFF_NOT_PROMOTED"
EXPECTED_REQ_IDS = {
    "MX-BROKER-AUTH-REQ-001",
    "MX-BROKER-AUTH-REQ-002",
    "MX-BROKER-AUTH-REQ-003",
    "MX-BROKER-AUTH-REQ-004",
    "MX-BROKER-AUTH-REQ-005",
}


def _load(name: str):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _jsonl(name: str):
    return [json.loads(line) for line in (ROUTE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_broker_authority_probe_default_off_and_verifier_clean():
    result = _load("BROKER_AUTHORITY_PROBE_RESULT.json")
    verifier = _load("BROKER_AUTHORITY_PROBE_VERIFIER_RESULT.json")
    completion = _load("COMPLETION_AUDIT.json")
    saturation = _load("SATURATION_SELF_RED_TEAM_AUDIT.json")
    requirements = _jsonl("UNRESOLVED_REQUIREMENT_LEDGER.jsonl")
    blocker_repair = _jsonl("BLOCKER_REPAIR_REQUIREMENT_LEDGER.jsonl")
    boundary = _jsonl("PROMOTION_BOUNDARY_LEDGER.jsonl")
    forbidden = _load("FORBIDDEN_CALL_SCAN.json")

    boundary_status = {row["gate"]: row["status"] for row in boundary}

    assert result["ok"] is True
    assert verifier["ok"] is True
    assert completion["ok"] is True
    assert saturation["ok"] is True
    assert result["decision"] == EXPECTED_DECISION
    assert result["live_authority"] is False
    assert result["deployment_ready"] is False
    assert result["promotion_ready"] is False
    assert result["config_patch_applied"] is False
    assert result["runtime_effect"] == "none_market_expansion_default_off_broker_authority_probe_only"
    assert {row["requirement_id"] for row in requirements} == EXPECTED_REQ_IDS
    assert blocker_repair == requirements
    assert set(result["deployment_not_ready_requirement_ids"]) == EXPECTED_REQ_IDS
    assert boundary_status["session_table_authority"] == "not_closed"
    assert boundary_status["commission_authority"] == "partial_not_closed"
    assert boundary_status["account_currency_profit_conversion"] == "closed_for_probe_symbols"
    assert boundary_status["swap_to_r_authority"] == "partial_not_closed"
    assert boundary_status["fill_slippage_limit_authority"] == "not_closed_not_mutated"
    assert boundary_status["owner_vps_action"] == "not_executed_by_mac_route"
    assert forbidden["ok"] is True
    assert forbidden["matches"] == []
    assert completion["forbidden_surfaces_touched"] == []


def test_broker_authority_probe_readonly_evidence_counts():
    result = _load("BROKER_AUTHORITY_PROBE_RESULT.json")
    bridge = _load("BRIDGE_METHOD_SURFACE.json")
    account = _load("ACCOUNT_TERMINAL_REDACTED_AUDIT.json")
    session = _load("SESSION_TABLE_REMOTE_PROOF.json")
    deals = _load("DEAL_HISTORY_COMMISSION_SUMMARY.json")
    conversion = _load("ORDER_CALC_PROFIT_CONVERSION_SUMMARY.json")
    swap = _load("SWAP_TO_R_PARTIAL_AUTHORITY_SUMMARY.json")
    deal_rows = _jsonl("DEAL_HISTORY_COMMISSION_LEDGER.jsonl")
    conversion_rows = _jsonl("ORDER_CALC_PROFIT_CONVERSION_LEDGER.jsonl")
    swap_rows = _jsonl("SWAP_TO_R_PARTIAL_AUTHORITY_LEDGER.jsonl")

    assert bridge["bridge_initialized"] is True
    assert bridge["bridge_host_method_probe_scope"] == "localhost RPyC bridge-host MT5 module, not VPS"
    assert bridge["approved_read_method_available"]["account_info"] is True
    assert bridge["approved_read_method_available"]["history_deals_get"] is True
    assert bridge["approved_read_method_available"]["order_calc_profit"] is True
    assert account["account_info_read"] is True
    assert account["terminal_info_read"] is True
    assert account["raw_account_values_stored"] is False
    assert account["redacted_account"]["currency"] == "USD"
    assert account["redacted_account"]["login_hash"]
    assert session["proof_scope"] == "local siliconmetatrader5 client and localhost bridge-host MT5 module, not VPS"
    assert session["session_table_closed"] is False
    assert session["client_symbol_info_session_trade"] is False
    assert session["bridge_host_symbol_info_session_trade"] is False
    assert session["symbol_info_session_like_key_count"] == 0

    assert len(deal_rows) == 14
    assert deals["symbol_count"] == 14
    assert deals["direct_history_symbol_count"] == 7
    assert deals["nonzero_commission_symbol_count"] == 2
    assert deals["observed_zero_commission_symbol_count"] == 5
    assert deals["no_direct_history_symbol_count"] == 7
    assert deals["all_symbols_commission_authority_closed"] is False
    assert result["commission_direct_history_symbol_count"] == 7
    assert result["commission_all_symbols_closed"] is False

    assert len(conversion_rows) == 14
    assert conversion["symbol_count"] == 14
    assert conversion["closed_symbol_count"] == 14
    assert conversion["all_symbols_closed"] is True
    assert float(conversion["max_abs_ratio_error_vs_symbol_info"]) <= 0.005
    assert result["profit_conversion_closed_symbol_count"] == 14
    assert result["profit_conversion_all_symbols_closed"] is True

    assert len(swap_rows) == 28
    assert swap["side_row_count"] == 28
    assert swap["point_mode_side_rows_computed"] == 22
    assert swap["mode5_or_other_side_rows_not_closed"] == 6
    assert swap["all_swap_to_r_closed"] is False
    assert result["swap_point_mode_side_rows_computed"] == 22
    assert result["swap_all_symbols_closed"] is False
