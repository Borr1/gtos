import json
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_candidate_full_book_live_activation_2026_06_18")

ALLOWLIST = [
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


def _load(name: str):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def test_full_candidate_book_live_activation_result_and_numbers():
    result = _load("CANDIDATE_FULL_BOOK_LIVE_ACTIVATION_RESULT.json")
    verification = _load("CANDIDATE_FULL_BOOK_LIVE_ACTIVATION_VERIFICATION_RESULT.json")
    completion = _load("COMPLETION_AUDIT.json")

    assert result["ok"] is True
    assert verification["ok"] is True
    assert completion["ok"] is True
    assert result["decision"] == "ARM_FULL_CANDIDATE_BOOK_LIVE_CONFIG_AND_HAND_TO_VPS"
    assert result["candidate_book_active"] is True
    assert result["candidate_book_profile"] == "runtime_executable_native_exit_v2"
    assert result["candidate_book_sleeves"] == ALLOWLIST
    assert result["ready_allowlist"] == ALLOWLIST

    active = result["active_core8_a8_baseline"]
    full = result["full_candidate_book"]
    assert active["sharpe"] == 0.147757
    assert full["sharpe"] == 0.277408
    assert full["mc"]["p_pass"] == 0.9999
    assert full["mc"]["p_fail_dd"] == 0.0001
    assert result["headline_improvement"]["sharpe_delta"] > 0
    assert result["headline_improvement"]["monthly_pct_delta"] > 0
    assert result["headline_improvement"]["p_fail_dd_delta"] < 0
    assert result["orderflow_used"] is False
    assert result["broker_or_order_mutation"] is False
    assert result["vps_process_touched"] is False


def test_full_candidate_book_live_activation_bridge_and_successor_lanes():
    result = _load("CANDIDATE_FULL_BOOK_LIVE_ACTIVATION_RESULT.json")
    saturation = _load("SATURATION_AUDIT.json")
    repair = _load("REPAIR_LEDGER.json")
    manifest = _load("OUTPUT_MANIFEST.json")
    rows = [
        json.loads(line)
        for line in (ROUTE / "DECISION_LEDGER.jsonl").read_text(encoding="utf-8").strip().splitlines()
    ]

    assert result["issue_count"] == 0
    assert all(check["passed"] is True for check in result["checks"])
    bridge = result["bridge_probe"]
    assert bridge["ready_runtime_effect_now"] is True
    assert bridge["ready_decision_status"] == "admitted_book_authority"
    assert bridge["ready_candidate_book_sleeves"] == ALLOWLIST
    assert any(
        "ny_crypto_momentum" in unit["sleeve_members"] and unit["sized"] is True
        for unit in bridge["ready_realized_units"]
    )
    assert any(
        "vol_squeeze" in unit["sleeve_members"] and unit["sized"] is False
        for unit in bridge["outside_would_units"]
    )
    assert bridge["broad_selector_apply_to_execution"] is False
    schedule = result["launcher_schedule_probe"]
    assert schedule["has_d1_candidate"] is True
    assert all(schedule["has_m15_candidates"].values())

    assert saturation["ok"] is True
    assert saturation["remaining_same_class_work"] == []
    assert repair["remaining_repairs"] == []
    by_row = {row["row"]: row for row in rows}
    assert by_row["natgas_translation"]["decision"] == (
        "exclude_from_live_allowlist_preserve_limit_entry_cost_revival_lane"
    )
    assert by_row["market_expansion_translation"]["decision"] == (
        "do_not_block_activation_create_expansion_data_availability_wave"
    )
    assert "CANDIDATE_FULL_BOOK_LIVE_ACTIVATION_PACKET.md" in manifest["files"]
    assert "NEXT_PROMPT.md" in manifest["files"]
