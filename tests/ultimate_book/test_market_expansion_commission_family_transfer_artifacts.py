import json
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_market_expansion_commission_family_transfer_2026_06_18")
EXPECTED_DECISION = "COMMISSION_FAMILY_TRANSFER_PARTIAL_REPAIR_DEFAULT_OFF_NOT_PROMOTED"
EXPECTED_REQ_IDS = {
    "MX-COMMISSION-FAMILY-REQ-001",
    "MX-COMMISSION-FAMILY-REQ-002",
    "MX-COMMISSION-FAMILY-REQ-003",
    "MX-COMMISSION-FAMILY-REQ-004",
}


def _load(name: str):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _jsonl(name: str):
    return [json.loads(line) for line in (ROUTE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_commission_family_transfer_default_off_and_verifier_clean():
    result = _load("COMMISSION_FAMILY_TRANSFER_RESULT.json")
    verifier = _load("COMMISSION_FAMILY_TRANSFER_VERIFIER_RESULT.json")
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
    assert result["runtime_effect"] == "none_market_expansion_default_off_commission_family_transfer_only"
    assert {row["requirement_id"] for row in requirements} == EXPECTED_REQ_IDS
    assert blocker_repair == requirements
    assert set(result["deployment_not_ready_requirement_ids"]) == EXPECTED_REQ_IDS
    assert boundary_status["direct_or_family_commission_evidence"] == "closed_as_proxy_not_schedule"
    assert boundary_status["broker_exact_commission_schedule"] == "not_closed"
    assert boundary_status["owner_vps_action"] == "not_executed_by_mac_route"
    assert forbidden["ok"] is True
    assert forbidden["matches"] == []
    assert completion["forbidden_surfaces_touched"] == []


def test_commission_family_transfer_counts_and_no_schedule_overclaim():
    result = _load("COMMISSION_FAMILY_TRANSFER_RESULT.json")
    account_summary = _load("ACCOUNT_HISTORY_SYMBOL_COMMISSION_SUMMARY.json")
    transfer_summary = _load("TARGET_COMMISSION_TRANSFER_SUMMARY.json")
    account_rows = _jsonl("ACCOUNT_HISTORY_SYMBOL_COMMISSION_LEDGER.jsonl")
    transfer_rows = _jsonl("TARGET_COMMISSION_TRANSFER_LEDGER.jsonl")

    assert len(account_rows) == 15
    assert account_summary["symbol_count"] == 15
    assert account_summary["deal_count_total"] == 101
    assert account_summary["raw_ticket_or_deal_ids_stored"] is False
    assert account_summary["nonzero_commission_symbol_count"] == 8
    assert account_summary["zero_commission_symbol_count"] == 7
    assert all(row["raw_ticket_or_deal_ids_stored"] is False for row in account_rows)

    assert len(transfer_rows) == 14
    assert transfer_summary["target_symbol_count"] == 14
    assert transfer_summary["direct_authority_symbol_count"] == 7
    assert transfer_summary["family_proxy_symbol_count"] == 7
    assert transfer_summary["not_closed_symbol_count"] == 0
    assert transfer_summary["direct_or_family_proxy_symbol_count"] == 14
    assert transfer_summary["all_targets_have_direct_or_family_proxy"] is True
    assert transfer_summary["broker_exact_schedule_closed"] is False
    assert transfer_summary["status_counts"] == {
        "direct_observed_nonzero_commission": 2,
        "direct_observed_zero_commission": 5,
        "family_proxy_nonzero_commission": 3,
        "family_proxy_zero_commission": 4,
    }
    assert result["direct_commission_authority_symbol_count"] == 7
    assert result["family_proxy_commission_symbol_count"] == 7
    assert result["direct_or_family_proxy_symbol_count"] == 14
    assert result["broker_exact_schedule_closed"] is False
    assert all(row["commission_authority_class"] != "not_closed" for row in transfer_rows)
    assert all(row["raw_ticket_or_deal_ids_stored"] is False for row in transfer_rows)
