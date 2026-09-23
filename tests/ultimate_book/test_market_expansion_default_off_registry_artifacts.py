import json
from collections import Counter
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_market_expansion_default_off_registry_2026_06_18")
DESIGN_ROUTE = Path("research/operations/final_moonshot_market_expansion_default_off_design_2026_06_18")


def _load(name: str):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _jsonl(name: str):
    return [json.loads(line) for line in (ROUTE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_default_off_registry_artifacts_preserve_design_and_boundaries():
    result = _load("MARKET_EXPANSION_DEFAULT_OFF_REGISTRY_RESULT.json")
    verifier = _load("MARKET_EXPANSION_DEFAULT_OFF_REGISTRY_VERIFIER_RESULT.json")
    active_audit = _load("ACTIVE_BEHAVIOR_AUDIT.json")
    completion = _load("COMPLETION_AUDIT.json")
    saturation = _load("SATURATION_AUDIT.json")
    repair = _load("REPAIR_LEDGER.json")
    design_result = json.loads((DESIGN_ROUTE / "MARKET_EXPANSION_DEFAULT_OFF_DESIGN_RESULT.json").read_text(encoding="utf-8"))
    rows = _jsonl("DEFAULT_OFF_REGISTRY_SPEC_LEDGER.jsonl")
    decisions = _jsonl("DECISION_LEDGER.jsonl")

    assert result["ok"] is True
    assert verifier["ok"] is True
    assert result["decision"] == "MARKET_EXPANSION_DEFAULT_OFF_REGISTRY_METADATA_INSTALLED_NO_LIVE_AUTHORITY"
    assert result["source_design_route"].endswith("market_expansion_default_off_design_2026_06_18")
    assert result["metadata_spec_count"] == design_result["accepted_default_off_count"] == 16
    assert result["m1_supported_metadata_count"] == design_result["m1_supported_design_count"] == 6
    assert result["proxy_repair_gated_metadata_count"] == design_result["proxy_repair_gated_design_count"] == 10
    assert len(rows) == 16
    assert Counter(row["design_status"] for row in rows) == {
        "default_off_spec_design_ready": 6,
        "repair_gated_default_off_spec_only": 10,
    }
    assert Counter(row["family"] for row in rows) == {
        "crypto_alt_or_major": 3,
        "indices_context": 11,
        "jpy_fx": 2,
    }
    assert Counter(row["mechanism"] for row in rows) == {
        "d1_atr_mean_reversion": 4,
        "d1_donchian_20_breakout": 4,
        "d1_volume_surge_reversal": 8,
    }
    assert active_audit["market_expansion_names_in_effective_registry"] == []
    assert active_audit["market_expansion_names_in_candidate_book_registry"] == []
    assert active_audit["market_expansion_runtime_names"] == []
    assert active_audit["activation_weight_sum"] == 0.0
    assert result["activation_weight_now"] == 0.0
    assert result["live_authority"] is False
    assert result["orderflow_used"] is False
    assert result["broker_or_order_mutation"] is False
    assert result["config_or_live_activation_changed"] is False
    assert result["vps_process_touched"] is False
    assert completion["runtime_effect"] == "none_metadata_only"
    assert saturation["all_design_rows_installed_as_metadata"] is True
    assert saturation["no_runtime_activation_names"] is True
    assert saturation["no_arbitrary_top_n"] is True
    assert "exact M1 repair for proxy rows" in repair["remaining_same_evidence_class_work"]
    assert any(row["decision"] == result["decision"] for row in decisions)


def test_default_off_registry_artifacts_match_design_ledger_fields():
    rows = _jsonl("DEFAULT_OFF_REGISTRY_SPEC_LEDGER.jsonl")
    design_rows = [
        json.loads(line)
        for line in (DESIGN_ROUTE / "DEFAULT_OFF_IMPLEMENTATION_SPEC_LEDGER.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_tag = {row["tag"]: row for row in rows}
    design_by_tag = {f"mx_{row['file_symbol'].lower()}_{row['mechanism']}": row for row in design_rows}
    assert set(by_tag) == set(design_by_tag)

    fields = {
        "file_symbol",
        "broker_symbol",
        "family",
        "mechanism",
        "design_status",
        "candidate_seed_weight",
        "candidate_weight_ceiling",
        "activation_weight_now",
        "symbol_collision_winner",
        "target2_exact_m1_event_count",
        "target2_m15_proxy_event_count",
        "target2_ordered_mean_r",
        "full_book_delta_sharpe",
    }
    for tag, row in by_tag.items():
        design = design_by_tag[tag]
        for field in fields:
            assert row[field] == design[field]

    collision_losers = {row["tag"] for row in rows if not row["symbol_collision_winner"]}
    assert collision_losers == {
        "mx_aus200_cash_d1_volume_surge_reversal",
        "mx_ger40_cash_d1_volume_surge_reversal",
    }
