import json
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_market_expansion_live_authority_dossier_2026_06_18")


def _load(name: str):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _jsonl(name: str):
    return [json.loads(line) for line in (ROUTE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_live_authority_dossier_counts_boundaries_and_replay():
    result = _load("MARKET_EXPANSION_LIVE_AUTHORITY_DOSSIER_RESULT.json")
    verifier = _load("MARKET_EXPANSION_LIVE_AUTHORITY_DOSSIER_VERIFIER_RESULT.json")
    completion = _load("COMPLETION_AUDIT.json")
    zero = _load("ZERO_ACTIVE_BEHAVIOR_AUDIT.json")
    source = _jsonl("SOURCE_EVENT_COST_LEDGER.jsonl")
    cost = _jsonl("SOURCE_SESSION_SPEC_COST_FILL_LEDGER.jsonl")
    material = _jsonl("ALL_MATERIAL_ROW_LEDGER.jsonl")
    replay = _jsonl("PORTFOLIO_REPLAY_LEDGER.jsonl")
    daily = _jsonl("PORTFOLIO_DAILY_REPLAY_LEDGER.jsonl")

    assert result["ok"] is True
    assert verifier["ok"] is True
    assert result["decision"] == "MARKET_EXPANSION_LIVE_AUTHORITY_DOSSIER_BUILT_DEFAULT_OFF_NOT_PROMOTED"
    assert result["selectable_activation_candidate_count"] == 14
    assert result["source_event_cost_row_count"] == len(source) == 2596
    assert len(cost) == len(material) == 14
    assert {row["tag"] for row in cost} == {row["tag"] for row in material}
    assert {row["source_join_status"] for row in source} == {"joined_generator_parity_risk"}
    assert result["portfolio_proxy_replay_complete"] is True
    assert len(replay) == 8
    assert result["portfolio_daily_replay_row_count"] == len(daily) == 1679
    assert "candidate_plus_expansion_seed_0p025_cost3_r" in daily[0]
    assert "candidate_plus_expansion_seed_0p025_cost3_expansion_overlay_r" in daily[0]
    assert zero["zero_active_behavior_ok"] is True
    assert result["activation_weight_now"] == 0.0
    assert result["live_authority"] is False
    assert result["deployment_ready"] is False
    assert result["promotion_ready"] is False
    assert completion["forbidden_surfaces_touched"] == []
    assert completion["runtime_effect_boundary"] == "none_default_off_dossier_only"


def test_live_authority_dossier_cost_session_and_fill_statuses():
    result = _load("MARKET_EXPANSION_LIVE_AUTHORITY_DOSSIER_RESULT.json")
    bridge = _load("BROKER_SPEC_ENHANCED_CAPTURE.json")
    session = _load("SESSION_TABLE_UNAVAILABLE_PROOF.json")
    forbidden = _load("FORBIDDEN_CALL_SCAN.json")
    fill = _load("FILL_POLICY_DECISION.json")
    cost = _jsonl("SOURCE_SESSION_SPEC_COST_FILL_LEDGER.jsonl")
    replay = {row["scenario"]: row for row in _jsonl("PORTFOLIO_REPLAY_LEDGER.jsonl")}

    assert bridge["account_info_read"] is False
    assert bridge["symbol_select_called"] is False
    assert bridge["broker_or_order_mutation"] is False
    assert bridge["orderflow_used"] is False
    assert bridge["symbol_count"] == 14
    assert bridge["symbol_info_captured_count"] == 14
    assert bridge["stop_freeze_present_count"] == 14
    assert bridge["symbol_info_tick_captured_count"] == 14
    assert forbidden["ok"] is True
    assert forbidden["matches"] == []
    assert result["broker_explicit_session_table_present_count"] == bridge["explicit_session_table_present_count"]
    if bridge["explicit_session_table_present_count"] == 0:
        assert session["session_trade_method_available"] is False
        assert session["session_quote_method_available"] is False
    assert fill["decision"] == "LIMIT_FIRST_OR_GUARDED_D1_OPEN_MARKET_SKIP_OTHERWISE"
    assert fill["live_order_logic_changed"] is False
    assert all(row["commission_to_r_status"] == "not_available_in_symbol_info_or_activation_artifacts" for row in cost)
    assert all(row["slippage_to_r_status"] == "stress_proxy_cost2_cost3_only_not_broker_exact" for row in cost)
    assert all(row["fill_policy_status"] == "limit_first_or_guarded_open_market_policy_draft_not_live_order_logic" for row in cost)
    assert all("bridge_tick_spread_r_summary" in row for row in cost)
    assert replay["candidate_plus_expansion_seed_0p025_cost3"]["source_value_key"] == "proxy_r_cost3"
    assert replay["candidate_plus_expansion_seed_0p025_cost3"]["expansion_weight_per_tag"] == 0.025
    assert replay["candidate_plus_expansion_micro_0p0125_cost3"]["expansion_weight_per_tag"] == 0.0125
    assert replay["candidate_plus_expansion_ceiling_0p05_cost3"]["expansion_weight_per_tag"] == 0.05
