import json
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_market_expansion_activation_readiness_synthesis_2026_06_18")
EXPECTED_DECISION = "MARKET_EXPANSION_ACTIVATION_READINESS_SYNTHESIS_READY_DEFAULT_OFF_NOT_PROMOTED"
EXPECTED_REQ_IDS = {
    "MX-READINESS-REQ-001",
    "MX-READINESS-REQ-002",
    "MX-READINESS-REQ-003",
    "MX-READINESS-REQ-004",
    "MX-READINESS-REQ-005",
}


def _load(name):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _jsonl(name):
    return [json.loads(line) for line in (ROUTE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_activation_readiness_synthesis_boundary_and_counts():
    result = _load("MARKET_EXPANSION_ACTIVATION_READINESS_RESULT.json")
    verifier = _load("MARKET_EXPANSION_ACTIVATION_READINESS_VERIFIER_RESULT.json")
    summary = _load("CANDIDATE_AUTHORITY_SUMMARY.json")
    completion = _load("COMPLETION_AUDIT.json")
    saturation = _load("SATURATION_SELF_RED_TEAM_AUDIT.json")
    requirements = _jsonl("UNRESOLVED_REQUIREMENT_LEDGER.jsonl")
    boundary = _jsonl("PROMOTION_BOUNDARY_LEDGER.jsonl")
    matrix = _jsonl("CANDIDATE_AUTHORITY_MATRIX.jsonl")

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
    assert result["runtime_effect"] == "none_default_off_activation_readiness_synthesis_only"
    assert {row["requirement_id"] for row in requirements} == EXPECTED_REQ_IDS
    assert boundary_status["default_off_code_package"] == "ready_14_of_14"
    assert boundary_status["live_authority"] == "not_closed_0_of_14"
    assert boundary_status["config_patch"] == "not_applied"
    assert boundary_status["owner_vps_action"] == "required_not_executed_by_mac_route"

    assert len(matrix) == 14
    assert summary["candidate_count"] == 14
    assert summary["default_off_code_package_ready_count"] == 14
    assert summary["live_authority_ready_count"] == 0
    assert summary["deployment_ready_count"] == 0
    assert summary["promotion_ready_count"] == 0
    assert all(row["default_off_code_package_ready"] is True for row in matrix)
    assert all(row["live_authority_ready"] is False for row in matrix)


def test_activation_readiness_synthesis_authority_detail_preserved():
    summary = _load("CANDIDATE_AUTHORITY_SUMMARY.json")
    matrix = _jsonl("CANDIDATE_AUTHORITY_MATRIX.jsonl")
    local_repair = _jsonl("LOCAL_REPAIR_EXHAUSTION_LEDGER.jsonl")
    forbidden = _load("FORBIDDEN_CALL_SCAN.json")

    assert summary["runtime_generator_parity_closed_count"] == 14
    assert summary["broker_spec_snapshot_closed_count"] == 14
    assert summary["profit_conversion_closed_count"] == 14
    assert summary["source_cost_join_closed_count"] == 14
    assert summary["explicit_session_table_closed_count"] == 0
    assert summary["observed_m1_session_proxy_closed_count"] == 14
    assert summary["direct_fill_slippage_closed_count"] == 7
    assert summary["no_direct_fill_slippage_symbol_count"] == 7
    assert summary["commission_direct_or_family_proxy_closed_count"] == 14
    assert summary["direct_commission_authority_count"] == 7
    assert summary["family_proxy_commission_authority_count"] == 7
    assert summary["swap_point_mode_symbol_count"] == 11
    assert summary["swap_mode5_formula_required_symbol_count"] == 3

    assert all(row["observed_m1_session_proxy_closed"] is True for row in matrix)
    assert all(row["explicit_session_table_closed"] is False for row in matrix)
    assert all(row["commission_direct_or_family_proxy_closed"] is True for row in matrix)
    assert any(row["swap_mode5_formula_required"] is True for row in matrix)
    assert forbidden["ok"] is True
    assert forbidden["matches"] == []
    assert {row["repair_family"] for row in local_repair} >= {
        "runtime_generator_parity",
        "observed_m1_session_proxy",
        "commission_family_transfer",
        "historical_fill_slippage",
        "swap_to_r",
        "explicit_session_table",
    }
