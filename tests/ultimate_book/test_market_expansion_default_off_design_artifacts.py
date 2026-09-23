import json
from collections import Counter
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_market_expansion_default_off_design_2026_06_18")
PROJECT_ROOT = Path(".")
RAW_SHA = "36359117717250ae23a969d397b00fc6309da64c566944a9d15b18a55df2d265"


def _load(name: str):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _jsonl(name: str):
    path = ROUTE / name
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_default_off_design_denominator_and_boundaries():
    result = _load("MARKET_EXPANSION_DEFAULT_OFF_DESIGN_RESULT.json")
    verification = _load("MARKET_EXPANSION_DEFAULT_OFF_DESIGN_VERIFIER_RESULT.json")
    input_manifest = _load("DEFAULT_OFF_INPUT_MANIFEST.json")
    saturation = _load("SATURATION_AUDIT.json")
    completion = _load("COMPLETION_AUDIT.json")
    design_rows = _jsonl("DEFAULT_OFF_IMPLEMENTATION_SPEC_LEDGER.jsonl")
    profile_rows = _jsonl("PROFILE_SPEC_COST_PREREQ_LEDGER.jsonl")
    repair_rows = _jsonl("M1_REPAIR_PLAN_LEDGER.jsonl")
    implementation_rows = _jsonl("IMPLEMENTATION_DECISION_LEDGER.jsonl")
    inspire_rows = _jsonl("INSPIRE_NOT_KILL_LEDGER.jsonl")

    assert result["ok"] is True
    assert verification["ok"] is True
    assert result["accepted_default_off_count"] == 16
    assert len(design_rows) == 16
    assert result["m1_supported_design_count"] == 6
    assert result["proxy_repair_gated_design_count"] == 10
    assert result["unique_symbol_count"] == 14
    assert result["symbol_collision_count"] == 2
    assert Counter(row["design_status"] for row in design_rows) == {
        "default_off_spec_design_ready": 6,
        "repair_gated_default_off_spec_only": 10,
    }
    assert len(profile_rows) == 16
    assert len(repair_rows) == 16
    assert len(implementation_rows) == 16
    assert len(inspire_rows) == 16
    assert all(row["activation_weight_now"] == 0.0 for row in design_rows)
    assert all(row["live_authority"] is False for row in design_rows)
    assert all(row["live_authority"] is False for row in implementation_rows)
    assert all(row["not_killed"] is True for row in repair_rows)
    assert all(row["not_killed"] is True for row in inspire_rows)
    assert input_manifest["g12_candidate_total"] == 820
    assert input_manifest["g12_accepted_default_off_count"] == 16
    assert input_manifest["raw_path_event_manifest"]["row_count"] == 19121
    assert input_manifest["raw_path_event_manifest"]["sha256"] == RAW_SHA
    assert input_manifest["raw_path_event_sha256_verified"] is True
    assert (PROJECT_ROOT / input_manifest["raw_path_event_manifest"]["path"]).exists()
    assert result["activation_weight_now"] == 0.0
    assert result["orderflow_used"] is False
    assert result["broker_or_order_mutation"] is False
    assert result["config_or_live_activation_changed"] is False
    assert result["vps_process_touched"] is False
    assert result["live_authority"] is False
    assert saturation["no_arbitrary_top_n"] is True
    assert saturation["candidate_book_separate_from_market_expansion"] is True
    assert completion["runtime_effect"] == "none_default_off_design_only"


def test_default_off_design_risk_budget_and_repair_gates():
    result = _load("MARKET_EXPANSION_DEFAULT_OFF_DESIGN_RESULT.json")
    risk_budget = _load("SELECTOR_RISK_BUDGET_SPEC.json")
    design_rows = _jsonl("DEFAULT_OFF_IMPLEMENTATION_SPEC_LEDGER.jsonl")
    collision_rows = _jsonl("SELECTOR_DEDUP_COLLISION_LEDGER.jsonl")
    repair_rows = _jsonl("M1_REPAIR_PLAN_LEDGER.jsonl")
    implementation_rows = _jsonl("IMPLEMENTATION_DECISION_LEDGER.jsonl")
    decision_rows = _jsonl("DECISION_LEDGER.jsonl")

    assert Counter(row["family"] for row in design_rows) == {
        "crypto_alt_or_major": 3,
        "indices_context": 11,
        "jpy_fx": 2,
    }
    assert Counter(row["mechanism"] for row in design_rows) == {
        "d1_atr_mean_reversion": 4,
        "d1_donchian_20_breakout": 4,
        "d1_volume_surge_reversal": 8,
    }
    assert {row["file_symbol"] for row in collision_rows} == {"AUS200_cash", "GER40_cash"}
    assert all(row["winner_mechanism"] == "d1_atr_mean_reversion" for row in collision_rows)
    assert risk_budget["global_activation_weight_now"] == 0.0
    assert risk_budget["candidate_seed_weight_for_m1_supported_design"] == 0.025
    assert risk_budget["candidate_seed_weight_for_proxy_supported_design"] == 0.0
    assert risk_budget["candidate_weight_ceiling_from_unit_sensitivity"] == 0.05
    assert risk_budget["family_counts"] == {
        "crypto_alt_or_major": 3,
        "indices_context": 11,
        "jpy_fx": 2,
    }
    assert risk_budget["mechanism_counts"] == {
        "d1_atr_mean_reversion": 4,
        "d1_donchian_20_breakout": 4,
        "d1_volume_surge_reversal": 8,
    }
    assert all(row["candidate_seed_weight"] == 0.025 for row in design_rows if row["design_status"] == "default_off_spec_design_ready")
    assert all(row["candidate_seed_weight"] == 0.0 for row in design_rows if row["design_status"] == "repair_gated_default_off_spec_only")
    assert sum(1 for row in repair_rows if row["m1_repair_required"]) == 10
    assert all(
        row["implementation_decision"] in {"write_default_off_spec", "write_repair_gated_default_off_spec"}
        for row in implementation_rows
    )
    assert any(row["decision"] == result["decision"] for row in decision_rows)
