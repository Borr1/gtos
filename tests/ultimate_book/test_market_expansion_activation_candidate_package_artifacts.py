import json
from collections import Counter
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_market_expansion_activation_candidate_package_2026_06_18")


def _load(name: str):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _jsonl(name: str):
    return [json.loads(line) for line in (ROUTE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_activation_candidate_package_counts_and_boundaries():
    result = _load("MARKET_EXPANSION_ACTIVATION_CANDIDATE_PACKAGE_RESULT.json")
    verifier = _load("MARKET_EXPANSION_ACTIVATION_CANDIDATE_PACKAGE_VERIFIER_RESULT.json")
    completion = _load("COMPLETION_AUDIT.json")
    saturation = _load("SATURATION_AUDIT.json")
    active_audit = _load("ACTIVE_BEHAVIOR_AUDIT.json")
    rows = _jsonl("ACTIVATION_CANDIDATE_ROW_LEDGER.jsonl")
    generator_rows = _jsonl("GENERATOR_IMPLEMENTATION_DECISION_LEDGER.jsonl")

    assert result["ok"] is True
    assert verifier["ok"] is True
    assert result["decision"] == "MARKET_EXPANSION_ACTIVATION_CANDIDATE_PACKAGE_READY_DEFAULT_OFF_NOT_LIVE_AUTHORITY"
    assert result["selectable_activation_candidate_count"] == len(rows) == 14
    assert result["broker_spec_ready_count"] == 14
    assert result["broker_contract_min_volume_ready_count"] == 14
    assert result["broker_execution_spec_live_complete_count"] == 0
    assert result["positive_cost3_mean_count"] == 14
    assert result["cost1_split_pass_count"] == 13
    assert result["cost2_split_pass_count"] == 10
    assert result["cost3_split_pass_count"] == 9
    assert result["exact_or_ordered_split_pass_count"] == 12
    assert result["runtime_generator_implemented_count"] == 0
    assert result["runtime_generator_not_implemented_count"] == len(generator_rows) == 14
    assert result["deployment_ready"] is False
    assert result["activation_candidate_package_ready"] is True
    assert result["activation_weight_now"] == 0.0
    assert result["live_authority"] is False
    assert result["orderflow_used"] is False
    assert result["broker_or_order_mutation"] is False
    assert result["account_info_read"] is False
    assert result["config_or_live_activation_changed"] is False
    assert result["vps_process_touched"] is False
    assert active_audit["market_expansion_names_in_effective_registry"] == []
    assert active_audit["market_expansion_names_in_candidate_book_registry"] == []
    assert active_audit["market_expansion_names_in_candidate_built"] == []
    assert active_audit["market_expansion_names_in_candidate_registry_candidates"] == []
    assert active_audit["market_expansion_runtime_names"] == []
    assert active_audit["activation_weight_sum"] == 0.0
    assert completion["result_materialization_status"] == "all_14_selectable_rows_materialized"
    assert completion["forbidden_surfaces_touched"] == []
    assert saturation["no_arbitrary_top_n"] is True
    assert saturation["all_selectable_rows_materialized"] is True


def test_activation_candidate_package_row_controls_and_generator_contracts():
    rows = _jsonl("ACTIVATION_CANDIDATE_ROW_LEDGER.jsonl")
    generators = _jsonl("GENERATOR_IMPLEMENTATION_DECISION_LEDGER.jsonl")
    sizing = _jsonl("SPLIT_STABILITY_SIZING_LEDGER.jsonl")
    interactions = _jsonl("FULL_BOOK_INTERACTION_REPLAY_LEDGER.jsonl")
    subagents = _jsonl("SUBAGENT_REVIEW_INTEGRATION_LEDGER.jsonl")
    by_tag = {row["tag"]: row for row in rows}
    sizing_by_tag = {row["tag"]: row for row in sizing}

    assert Counter(row["family"] for row in rows) == {
        "crypto_alt_or_major": 3,
        "indices_context": 9,
        "jpy_fx": 2,
    }
    assert Counter(row["mechanism"] for row in rows) == {
        "d1_atr_mean_reversion": 2,
        "d1_donchian_20_breakout": 4,
        "d1_volume_surge_reversal": 8,
    }
    assert {row["subagent"] for row in subagents} == {"Franklin", "Lovelace"}
    assert {row["tag"] for row in generators} == set(by_tag)
    assert {row["tag"] for row in sizing} == set(by_tag)
    assert {row["tag"] for row in interactions} == set(by_tag)

    for row in rows:
        assert row["activation_weight_now"] == 0.0
        assert row["runtime_effect"] == "none_metadata_package_only"
        assert row["broker_contract_min_volume_ready"] is True
        assert row["broker_execution_spec_complete_for_live_authority"] is False
        assert "runtime_generator_parity" in row["broker_execution_spec_missing_fields"]
        assert "explicit_broker_trading_session_table" in row["broker_execution_spec_missing_fields"]
        assert row["session_source_status"]["broker_trading_session_status"] == (
            "explicit_mt5_symbol_session_table_capture_required_before_live_authority"
        )

    for row in generators:
        assert row["current_generator_code_status"] == "not_implemented_in_runtime"
        assert row["implementation_decision"] == "metadata_only_pending_explicit_default_off_runtime_generator"
        assert "D1 next-open" in row["non_implementation_requirement"]
        assert any("ultimate_book_include_market_expansion_book" in item for item in row["required_runtime_safety_design"])

    assert by_tag["mx_jp225_cash_d1_volume_surge_reversal"]["target2_split_every_populated_positive"] is False
    assert by_tag["mx_us30_cash_d1_volume_surge_reversal"]["target2_split_every_populated_positive"] is False
    assert "negative_path_split_requires_holdout_or_sizing_gate_before_activation" in sizing_by_tag[
        "mx_jp225_cash_d1_volume_surge_reversal"
    ]["activation_stage_controls"]
    assert "negative_path_split_requires_holdout_or_sizing_gate_before_activation" in sizing_by_tag[
        "mx_us30_cash_d1_volume_surge_reversal"
    ]["activation_stage_controls"]
    assert "cost3_split_stress_not_all_positive_requires_initial_weight_cap_or_limit_order_model" in sizing_by_tag[
        "mx_spn35_cash_d1_volume_surge_reversal"
    ]["activation_stage_controls"]
