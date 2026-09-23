import json
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_candidate_subset_routing_dossier_2026_06_18")


def _load(name: str):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def test_candidate_subset_routing_dossier_result_and_boundaries():
    result = _load("CANDIDATE_SUBSET_ROUTING_DOSSIER_RESULT.json")
    verification = _load("CANDIDATE_SUBSET_ROUTING_DOSSIER_VERIFICATION_RESULT.json")

    assert result["ok"] is True
    assert verification["ok"] is True
    assert result["staged_ready_subset_dossier_ready"] is True
    assert result["routing_activation_ready"] is True
    assert result["full_candidate_book_ready"] is True
    assert result["decision"] == "FULL_CANDIDATE_BOOK_ACTIVE_CONFIG_ROUTING_DOSSIER_READY"
    assert result["runtime_effect_now"] == "candidate_book_active_in_config"
    assert result["active_config_candidate_book_enabled"] is True
    assert result["active_config_candidate_book_sleeves"] == [
        "asia_pdl_fade",
        "asian_fade",
        "kz_london_crypto_low",
        "liq_asia_up_low_metal",
        "metal_session_reversion",
        "ny_crypto_momentum",
        "orb_crypto_london",
        "vol_compression",
        "vss_fxcross_london_up_low",
    ]
    assert result["bridge_default_candidate_book_sleeves"] == []
    assert result["readiness_work_item_count"] == 0
    assert result["native_routing_repaired_symbol_count"] == 12
    assert result["ready_subset_all_symbols_activation_ready"] is True
    assert result["ready_subset_generation_candidates"] == result["ready_subset_registry_candidates"]
    assert result["ready_subset_generation_candidates"] == [
        "asia_pdl_fade",
        "asian_fade",
        "kz_london_crypto_low",
        "liq_asia_up_low_metal",
        "metal_session_reversion",
        "ny_crypto_momentum",
        "orb_crypto_london",
        "vol_compression",
        "vss_fxcross_london_up_low",
    ]
    assert result["ready_subset_mc"]["sharpe"] == 0.277408
    assert result["ready_subset_mc"]["mc"]["p_pass"] == 0.9999
    assert result["orderflow_used"] is False
    assert result["mt5_bridge_touched"] is False
    assert result["broker_or_order_mutation"] is False
    assert result["vps_process_touched"] is False


def test_candidate_subset_routing_ledger_preserves_full_book_work():
    result = _load("CANDIDATE_SUBSET_ROUTING_DOSSIER_RESULT.json")
    rows = [
        json.loads(line)
        for line in (ROUTE / "CANDIDATE_SUBSET_ROUTING_LEDGER.jsonl")
        .read_text(encoding="utf-8")
        .strip()
        .splitlines()
    ]

    assert result["dual_broker_native_decision_count"] == 0
    assert result["ftmo_expected_skip_decision_count"] == 0
    assert result["all_ftmo_expected_skip_symbol_count"] == 6
    assert result["natgas_research_only_count"] == 0
    native_repair_rows = [row for row in rows if row["ledger"] == "native_routing_repaired_symbol"]
    assert {row["symbol"] for row in native_repair_rows} == set(result["native_routing_repaired_symbols"])
    assert all(row["native_eligible"] is True for row in native_repair_rows)
    ready_rows = [row for row in rows if row["ledger"] == "ready_subset_symbol"]
    assert ready_rows
    assert all(row["status"] == "ACTIVATION_READY" for row in ready_rows)
    assert all(row["blocking_active_profile_gap_profiles"] == [] for row in ready_rows)
    assert all(row["missing_ltf_stress_timeframes"] == [] for row in rows)
    ftmo_rows = [row for row in rows if row["ledger"] == "all_ftmo_expected_skip_symbol"]
    assert {row["symbol"] for row in ftmo_rows} == {
        "DASHUSD",
        "LTCUSD",
        "XPDUSD",
        "XPTUSD",
        "XRPUSD",
        "XTZUSD",
    }
    assert all(row["blocking_active_profile_gap_profiles"] == [] for row in ftmo_rows)
    assert all(
        row["profile_missing_expected_skip_profiles"] == ["redacted_account"]
        for row in ftmo_rows
    )
    bridge_probe = result["bridge_probe"]
    assert bridge_probe["runtime_effect_now"] is False
    assert bridge_probe["candidate_book_sleeves"] == result["ready_subset_sleeves"]
    assert any(
        "ny_crypto_momentum" in unit["sleeve_members"] and unit["sized"] is True
        for unit in bridge_probe["ready_would_units"]
    )
    assert any(
        "vol_squeeze" in unit["sleeve_members"] and unit["sized"] is False
        for unit in bridge_probe["outside_would_units"]
    )
