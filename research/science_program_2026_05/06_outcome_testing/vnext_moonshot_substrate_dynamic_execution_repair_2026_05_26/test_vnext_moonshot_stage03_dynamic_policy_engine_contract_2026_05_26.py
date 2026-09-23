from __future__ import annotations

import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"


def test_stage03_contract_is_pure_and_default_off() -> None:
    contract = json.loads(
        (ROUTE_DIR / f"VNEXT_MOONSHOT_DYNAMIC_POLICY_ENGINE_CONTRACT_{DATE_ID}.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["banned_imports"] == []
    assert contract["purity_contract"]["no_mt5"] is True
    assert contract["purity_contract"]["no_broker_mutation"] is True
    assert contract["execution_effect"] == "research_replay_only_default_off_no_runtime_flag_flip"
    assert contract["first_incomplete_invariant_after_stage03"] == "STAGE_04_FULL_POLICY_DYNAMIC_REPLAY"


def test_stage03_policy_manifest_covers_required_exit_families() -> None:
    rows = [
        json.loads(line)
        for line in (ROUTE_DIR / f"VNEXT_MOONSHOT_DYNAMIC_POLICY_MANIFEST_{DATE_ID}.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    names = {row["policy_name"] for row in rows}
    assert {
        "legacy_fixed_1.5r",
        "ai_target",
        "live_current_j46_j49",
        "partial_be_runner",
        "be_after_trigger",
        "trailing_runner",
        "time_stop_only",
        "early_cut_if_no_progress",
        "path_aware_runner",
    } <= names
    live = next(row for row in rows if row["policy_name"] == "live_current_j46_j49")
    assert live["tp1_r"] == 3.0
    assert live["final_target_r"] == 6.0
    assert live["time_stop_bars"] == 12
    assert live["partial_close_ratio"] == 0.0


def test_stage03_matrix_contains_ambiguous_and_profit_cases() -> None:
    rows = [
        json.loads(line)
        for line in (ROUTE_DIR / f"VNEXT_MOONSHOT_DYNAMIC_POLICY_TEST_MATRIX_{DATE_ID}.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    assert any(row["replay_status"] == "ambiguous" for row in rows)
    assert any(row["policy_name"] == "live_current_j46_j49" and row["final_r"] == 6.0 for row in rows)
