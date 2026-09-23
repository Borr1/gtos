import json
from collections import Counter
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_market_expansion_g12_review_2026_06_18")
PROJECT_ROOT = Path(".")
RAW_SHA = "36359117717250ae23a969d397b00fc6309da64c566944a9d15b18a55df2d265"


def _load(name: str):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _jsonl(name: str):
    path = ROUTE / name
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_g12_review_denominator_decisions_and_boundaries():
    result = _load("MARKET_EXPANSION_G12_REVIEW_RESULT.json")
    verification = _load("MARKET_EXPANSION_G12_REVIEW_VERIFIER_RESULT.json")
    saturation = _load("SATURATION_AUDIT.json")
    completion = _load("COMPLETION_AUDIT.json")
    input_manifest = _load("G12_INPUT_MANIFEST.json")
    candidate_rows = _jsonl("G12_CANDIDATE_DECISION_LEDGER.jsonl")
    deep_rows = _jsonl("G12_DEEP_SELECTION_LEDGER.jsonl")
    inspire_rows = _jsonl("INSPIRE_NOT_KILL_LEDGER.jsonl")

    assert result["ok"] is True
    assert verification["ok"] is True
    assert result["candidate_result_count"] == 820
    assert len(candidate_rows) == 820
    assert result["deep_review_count"] == 75
    assert len(deep_rows) == 75
    assert Counter(row["followup_class"] for row in candidate_rows) == {
        "context_only_single_stock_cfd": 290,
        "context_or_negative_proxy": 383,
        "first_pass_promoted": 33,
        "near_miss_positive_proxy": 42,
        "positive_proxy_underpowered_or_unstable": 72,
    }
    assert Counter(row["g12_decision"] for row in candidate_rows) == {
        "context_only_single_stock_portfolio_inventory": 290,
        "context_or_veto_inventory": 383,
        "default_off_m1_supported_candidate": 6,
        "default_off_proxy_supported_candidate_requires_m1_repair": 10,
        "exact_repair_or_negative_control_required": 6,
        "successor_experiment_inventory": 72,
        "transformed_context_or_sizing_feature": 53,
    }
    assert result["default_off_candidate_count"] == 16
    assert result["default_off_m1_supported_count"] == 6
    assert result["default_off_proxy_supported_count"] == 10
    assert result["transformed_context_or_sizing_feature_count"] == 53
    assert result["exact_repair_or_negative_control_count"] == 6
    assert len(inspire_rows) == 820
    assert all(row["not_killed"] is True for row in inspire_rows)
    assert all(row["not_killed"] is True for row in candidate_rows)
    assert {"SPCX", "NATGAS_cash", "HEATOIL_c"}.isdisjoint({row["file_symbol"] for row in candidate_rows})
    assert input_manifest["raw_path_event_manifest"]["row_count"] == 19121
    assert input_manifest["raw_path_event_manifest"]["sha256"] == RAW_SHA
    assert input_manifest["raw_path_event_sha256_verified"] is True
    assert (PROJECT_ROOT / input_manifest["raw_path_event_manifest"]["path"]).exists()
    assert result["orderflow_used"] is False
    assert result["broker_or_order_mutation"] is False
    assert result["config_or_live_activation_changed"] is False
    assert result["vps_process_touched"] is False
    assert result["live_authority"] is False
    assert saturation["no_arbitrary_top_n"] is True
    assert saturation["all_candidate_rows_processed"] is True
    assert saturation["all_deep_rows_reviewed"] is True
    assert completion["runtime_effect"] == "none_research_review_only"


def test_g12_review_acceptance_gates_concentration_and_handoff():
    result = _load("MARKET_EXPANSION_G12_REVIEW_RESULT.json")
    full_book = _load("FULL_BOOK_INTERACTION_AUDIT.json")
    concentration = _load("CONCENTRATION_NULL_PLACEBO_AUDIT.json")
    accepted_rows = _jsonl("G12_ACCEPTED_DEFAULT_OFF_LEDGER.jsonl")
    implementation_rows = _jsonl("G12_IMPLEMENTATION_HANDOFF_LEDGER.jsonl")
    repair_rows = _jsonl("G12_EXACT_REPAIR_LEDGER.jsonl")
    decision_rows = _jsonl("DECISION_LEDGER.jsonl")

    assert len(accepted_rows) == 16
    assert len(implementation_rows) == 16
    assert len(repair_rows) == 820
    assert Counter(row["g12_decision"] for row in accepted_rows) == {
        "default_off_m1_supported_candidate": 6,
        "default_off_proxy_supported_candidate_requires_m1_repair": 10,
    }
    assert Counter(row["family"] for row in accepted_rows) == {
        "crypto_alt_or_major": 3,
        "indices_context": 11,
        "jpy_fx": 2,
    }
    assert Counter(row["mechanism"] for row in accepted_rows) == {
        "d1_atr_mean_reversion": 4,
        "d1_donchian_20_breakout": 4,
        "d1_volume_surge_reversal": 8,
    }
    for row in accepted_rows:
        gates = row["gates"]
        for gate in (
            "deep_replay_class",
            "ordered_events_ge_75",
            "ordered_path_coverage_ge_0p95",
            "ordered_mean_ge_0p05",
            "populated_splits_ge_3",
            "every_populated_split_positive",
            "min_split_mean_ge_0p01",
            "median_nonnegative_or_win_rate_ge_0p52",
            "full_book_delta_ge_0p00010",
            "corr_abs_le_0p06",
            "matched_current_book_days_ge_60",
            "ordered_path_ready",
            "source_placebo_pass_or_missing",
        ):
            assert gates[gate] is True
        if row["g12_decision"] == "default_off_m1_supported_candidate":
            assert gates["exact_m1_events_ge_20"] is True
        if row["g12_decision"] == "default_off_proxy_supported_candidate_requires_m1_repair":
            assert gates["exact_m1_events_ge_20"] is False
            assert gates["proxy_limited_m15_events_ge_75"] is True
            assert gates["proxy_limited_mean_ge_0p10"] is True

    assert all(row["live_authority"] is False for row in implementation_rows)
    assert all(row["implementation_scope"] == "candidate_registry_default_off_only" for row in implementation_rows)
    assert full_book["row_count"] == 75
    assert full_book["computed_count"] == 75
    assert full_book["positive_delta_count"] == 60
    assert full_book["negative_delta_count"] == 15
    assert concentration["accepted_count"] == 16
    assert concentration["accepted_mechanism_budget_warning"] is True
    assert concentration["no_arbitrary_top_n"] is True
    assert concentration["timing_null"]["random_day_reps"] == 200
    assert concentration["timing_null"]["p_value_summary"]["n"] == 75
    assert any(row["decision"] == result["decision"] for row in decision_rows)
