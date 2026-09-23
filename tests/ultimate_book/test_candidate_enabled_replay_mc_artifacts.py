import json
from pathlib import Path


ROUTE = Path(
    "research/operations/final_moonshot_candidate_enabled_unified_replay_mc_2026_06_18"
)


def _load(name: str):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def test_candidate_enabled_route_core_numbers_and_boundaries():
    result = _load("CANDIDATE_ENABLED_REPLAY_MC_RESULT.json")
    verification = _load("CANDIDATE_ENABLED_REPLAY_MC_VERIFICATION_RESULT.json")

    assert result["ok"] is True
    assert verification["ok"] is True
    assert result["deployment_ready"] is True
    assert result["routing_activation_ready"] is True
    assert result["full_candidate_book_ready"] is True
    assert result["decision"] == "CANDIDATE_BOOK_REPLAY_MC_READY_AND_ACTIVE_CONFIG_ARMED"
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
    assert result["readiness_work_item_count"] == 0
    assert result["a8_reproduction"]["rows_exact"] is True
    assert result["a8_reproduction"]["column_maxdiff"] == 0.0
    assert result["unified_book_reproduction_delta"]["abs_sharpe_delta"] == 0.0
    assert result["orderflow_used"] is False
    assert result["broker_or_order_mutation"] is False
    assert result["mt5_bridge_touched"] is False
    assert result["vps_process_touched"] is False

    active = result["scenarios"]["active_core8_a8_baseline_no_candidates"]
    all_candidates = result["scenarios"]["candidate_all_on_active_a8"]
    ready_subset = result["scenarios"]["candidate_ready_whole_sleeves_on_active_a8"]

    assert active["sharpe"] == 0.147757
    assert all_candidates["sharpe"] == 0.277408
    assert ready_subset["sharpe"] == 0.277408
    assert all_candidates["mc"]["p_pass"] == 0.9999
    assert ready_subset["mc"]["p_pass"] == 0.9999
    assert set(result["ready_whole_sleeves"]) == {
        "asia_pdl_fade",
        "asian_fade",
        "kz_london_crypto_low",
        "liq_asia_up_low_metal",
        "metal_session_reversion",
        "ny_crypto_momentum",
        "orb_crypto_london",
        "vol_compression",
        "vss_fxcross_london_up_low",
    }
    assert result["unfinished_whole_sleeves"] == []


def test_candidate_enabled_route_ledgers_preserve_unfinished_and_ready_ideas():
    work_rows = (ROUTE / "CANDIDATE_READINESS_WORK_LEDGER.jsonl").read_text(
        encoding="utf-8"
    ).strip().splitlines()
    translation_rows = (ROUTE / "CANDIDATE_INSPIRE_NOT_KILL_TRANSLATION_LEDGER.jsonl").read_text(
        encoding="utf-8"
    ).strip().splitlines()
    mc_rows = (ROUTE / "CANDIDATE_ON_MC_LEDGER.jsonl").read_text(
        encoding="utf-8"
    ).strip().splitlines()

    assert len(work_rows) == 9
    assert len(translation_rows) == 9
    assert len(mc_rows) == 4

    work = [json.loads(line) for line in work_rows]
    readiness_reasons = {
        row["reason"]
        for row in work
        if row["reason"] != "whole_sleeve_currently_deployment_ready"
    }
    assert readiness_reasons == set()
    assert all(row["missing_ltf_stress_timeframes"] == [] for row in work)
    natgas = [row for row in work if row["symbol"] == "NATGAS_cash"]
    assert natgas == []

    translations = [json.loads(line) for line in translation_rows]
    by_sleeve = {row["sleeve"]: row for row in translations}
    assert by_sleeve["asia_pdl_fade"]["current_claim_status"] == "candidate_book_ready_member"
    assert by_sleeve["ny_crypto_momentum"]["current_claim_status"] == "candidate_book_ready_member"
    assert all(row["current_claim_status"] == "candidate_book_ready_member" for row in translations)
    assert all(row["runtime_effect_now"] == "none" for row in translations)
