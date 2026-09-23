import json
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_market_expansion_fill_session_probe_2026_06_18")
EXPECTED_DECISION = "FILL_SESSION_PARTIAL_REPAIR_DEFAULT_OFF_NOT_PROMOTED"
EXPECTED_REQ_IDS = {
    "MX-FILL-SESSION-REQ-001",
    "MX-FILL-SESSION-REQ-002",
    "MX-FILL-SESSION-REQ-003",
    "MX-FILL-SESSION-REQ-004",
    "MX-FILL-SESSION-REQ-005",
}


def _load(name: str):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _jsonl(name: str):
    return [json.loads(line) for line in (ROUTE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_fill_session_probe_default_off_and_verifier_clean():
    result = _load("FILL_SESSION_PROBE_RESULT.json")
    verifier = _load("FILL_SESSION_PROBE_VERIFIER_RESULT.json")
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
    assert result["runtime_effect"] == "none_market_expansion_default_off_fill_session_probe_only"
    assert {row["requirement_id"] for row in requirements} == EXPECTED_REQ_IDS
    assert blocker_repair == requirements
    assert set(result["deployment_not_ready_requirement_ids"]) == EXPECTED_REQ_IDS
    assert boundary_status["historical_fill_slippage"] == "partial_not_closed"
    assert boundary_status["observed_quote_session_proxy"] == "proxy_available_not_live_authority"
    assert boundary_status["explicit_session_table"] == "not_closed"
    assert boundary_status["prospective_limit_queue_fillability"] == "not_closed_not_mutated"
    assert boundary_status["owner_vps_action"] == "not_executed_by_mac_route"
    assert forbidden["ok"] is True
    assert forbidden["matches"] == []
    assert completion["forbidden_surfaces_touched"] == []


def test_fill_session_probe_aggregate_fill_and_session_counts():
    result = _load("FILL_SESSION_PROBE_RESULT.json")
    fill_summary = _load("HISTORY_ORDER_DEAL_FILL_SUMMARY.json")
    field_audit = _load("HISTORY_ORDER_DEAL_FIELD_AUDIT.json")
    session_summary = _load("OBSERVED_M1_SESSION_AVAILABILITY_SUMMARY.json")
    fill_rows = _jsonl("HISTORY_ORDER_DEAL_FILL_LEDGER.jsonl")
    session_rows = _jsonl("OBSERVED_M1_SESSION_AVAILABILITY_LEDGER.jsonl")

    assert len(fill_rows) == 14
    assert fill_summary["symbol_count"] == 14
    assert fill_summary["direct_fill_symbol_count"] == 7
    assert fill_summary["no_direct_fill_symbol_count"] == 7
    assert fill_summary["joined_entry_deal_count_total"] == 57
    assert fill_summary["all_symbols_fill_slippage_closed"] is False
    assert fill_summary["fill_authority_status_counts"] == {
        "direct_observed_historical_order_deal_fill_slippage": 7,
        "not_closed_no_direct_joined_fill_rows": 7,
    }
    assert result["direct_fill_symbol_count"] == 7
    assert result["historical_fill_slippage_all_symbols_closed"] is False
    assert result["prospective_limit_queue_fillability_closed"] is False
    assert result["joined_entry_deal_count_total"] == 57
    assert result["max_slippage_abs_r_observed"] == fill_summary["max_slippage_abs_r_observed"]
    assert all(row["raw_ticket_or_order_ids_stored"] is False for row in fill_rows)
    assert field_audit["raw_ticket_or_order_ids_stored"] is False
    assert "ticket" in field_audit["order_field_names"]
    assert "order" in field_audit["deal_field_names"]

    assert len(session_rows) == 14
    assert session_summary["symbol_count"] == 14
    assert session_summary["symbols_with_m1_bars"] == 14
    assert session_summary["explicit_session_table_closed"] is False
    assert session_summary["observed_session_proxy_status_counts"] == {
        "observed_24_7_like_quote_availability_proxy": 3,
        "observed_restricted_weekday_quote_availability_proxy": 9,
        "observed_weekday_24h_quote_availability_proxy": 2,
    }
    assert result["symbols_with_m1_session_proxy"] == 14
    assert result["explicit_session_table_closed"] is False
    assert all(row["m1_bar_count"] > 0 for row in session_rows)
    assert all(row["explicit_session_table_status"] == "not_explicit_session_table" for row in session_rows)
