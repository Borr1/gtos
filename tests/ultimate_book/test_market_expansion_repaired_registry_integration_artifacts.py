import json
from collections import Counter
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_market_expansion_repaired_registry_integration_2026_06_18")
PROXY_ROUTE = Path("research/operations/final_moonshot_market_expansion_proxy_m1_repair_2026_06_18")


def _load(name: str):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _proxy_load(name: str):
    return json.loads((PROXY_ROUTE / name).read_text(encoding="utf-8"))


def _jsonl(name: str):
    return [json.loads(line) for line in (ROUTE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def _proxy_jsonl(name: str):
    return [json.loads(line) for line in (PROXY_ROUTE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_repaired_registry_integration_counts_and_boundaries():
    result = _load("MARKET_EXPANSION_REPAIRED_REGISTRY_INTEGRATION_RESULT.json")
    verifier = _load("MARKET_EXPANSION_REPAIRED_REGISTRY_INTEGRATION_VERIFIER_RESULT.json")
    active_audit = _load("ACTIVE_BEHAVIOR_AUDIT.json")
    completion = _load("COMPLETION_AUDIT.json")
    saturation = _load("SATURATION_AUDIT.json")
    repair = _load("REPAIR_LEDGER.json")
    rows = _jsonl("REPAIRED_REGISTRY_INTEGRATION_LEDGER.jsonl")
    proxy_result = _proxy_load("MARKET_EXPANSION_PROXY_M1_REPAIR_RESULT.json")

    assert result["ok"] is True
    assert verifier["ok"] is True
    assert result["decision"] == "MARKET_EXPANSION_REPAIRED_REGISTRY_INTEGRATED_NO_LIVE_AUTHORITY"
    assert result["source_proxy_m1_repair_route"].endswith("market_expansion_proxy_m1_repair_2026_06_18")
    assert result["metadata_spec_count"] == len(rows) == 16
    assert result["exact_m1_supported_metadata_count"] == 15
    assert result["proxy_repair_gated_metadata_count"] == 0
    assert result["transformed_context_or_veto_count"] == 1
    assert result["selectable_default_off_count"] == 14
    assert result["candidate_seed_enabled_count"] == 14
    assert result["repaired_graduated_metadata_count"] == 9
    assert result["repaired_transformed_metadata_count"] == 1
    assert result["repaired_exact_m1_event_count"] == proxy_result["repaired_exact_m1_event_count"] == 692
    assert result["new_exact_m1_events_added"] == proxy_result["new_exact_m1_events_added"] == 592
    assert Counter(row["design_status"] for row in rows) == {
        "default_off_spec_design_ready": 15,
        "transformed_context_or_veto_after_exact_m1_repair": 1,
    }
    assert Counter(row["candidate_seed_weight"] for row in rows) == {0.025: 14, 0.0: 2}
    assert active_audit["market_expansion_names_in_effective_registry"] == []
    assert active_audit["market_expansion_names_in_candidate_book_registry"] == []
    assert active_audit["market_expansion_runtime_names"] == []
    assert active_audit["activation_weight_sum"] == 0.0
    assert result["activation_weight_now"] == 0.0
    assert result["live_authority"] is False
    assert result["orderflow_used"] is False
    assert result["broker_or_order_mutation"] is False
    assert result["account_info_read"] is False
    assert result["config_or_live_activation_changed"] is False
    assert result["vps_process_touched"] is False
    assert completion["runtime_effect"] == "none_metadata_only"
    assert saturation["all_proxy_repair_gates_cleared_or_transformed"] is True
    assert saturation["no_arbitrary_top_n"] is True
    assert "cleared proxy-repair-gated metadata count from 10 to 0" in repair["completed_repairs"]


def test_repaired_registry_integration_preserves_row_level_repair_decisions():
    rows = _jsonl("REPAIRED_REGISTRY_INTEGRATION_LEDGER.jsonl")
    repair_rows = _proxy_jsonl("EXACT_M1_REPAIR_CANDIDATE_LEDGER.jsonl")
    by_tag = {row["tag"]: row for row in rows}
    repair_by_tag = {row["tag"]: row for row in repair_rows}
    decisions = _jsonl("DECISION_LEDGER.jsonl")

    assert set(repair_by_tag) <= set(by_tag)
    assert by_tag["mx_ger40_cash_d1_atr_mean_reversion"]["design_status"] == (
        "transformed_context_or_veto_after_exact_m1_repair"
    )
    assert by_tag["mx_ger40_cash_d1_atr_mean_reversion"]["candidate_seed_weight"] == 0.0
    assert by_tag["mx_ger40_cash_d1_atr_mean_reversion"]["target2_ordered_mean_r"] == -0.0005
    collision_losers = {row["tag"] for row in rows if not row["symbol_collision_winner"]}
    assert collision_losers == {
        "mx_aus200_cash_d1_atr_mean_reversion",
        "mx_ger40_cash_d1_atr_mean_reversion",
    }

    for tag, repair_row in repair_by_tag.items():
        row = by_tag[tag]
        summary = repair_row["target2_exact_m1_summary"]
        assert row["target2_exact_m1_event_count"] == repair_row["repaired_exact_m1_event_count"]
        assert row["source_repair_exact_m1_mean_r"] == summary["mean_r"]
        assert row["source_repair_every_populated_split_positive"] == summary["every_populated_split_positive"]
        if repair_row["decision"] == "graduate_to_exact_m1_supported_default_off_metadata":
            assert row["design_status"] == "default_off_spec_design_ready"
        else:
            assert row["design_status"] == "transformed_context_or_veto_after_exact_m1_repair"

    split_review_tags = {
        row["tag"]
        for row in rows
        if row.get("source_repair_every_populated_split_positive") is False
        and row["design_status"] == "default_off_spec_design_ready"
    }
    assert split_review_tags == {
        "mx_jp225_cash_d1_volume_surge_reversal",
        "mx_us30_cash_d1_volume_surge_reversal",
    }
    assert any(row["decision"] == "PRESERVE_SPLIT_CONFLICT_GRADUATES_AS_DEFAULT_OFF_NOT_LIVE" for row in decisions)
