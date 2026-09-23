from __future__ import annotations

import json
from pathlib import Path

from verify_g0_scid_asof_synthesis_validation_design_2026_05_11 import verify


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
DATE_TAG = "2026-05-11"
PREFIX = "G0_SCID_ASOF"


def load_json(name: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{name}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def load_jsonl(name: str) -> list[dict]:
    rows = []
    with (ROUTE_DIR / f"{PREFIX}_{name}_{DATE_TAG}.jsonl").open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_exact_packet_reconciliation_counts_and_terminal_decision():
    reconciliation = load_json("ACCEPTED_PACKET_RECONCILIATION")
    checks = {row["check_id"]: row for row in reconciliation["exact_count_checks"]}

    assert reconciliation["terminal_decision"] == "ACCEPT_AS_SOURCE_CONTROL_SCID_ASOF_CANDIDATE_INPUT_PACKET_ONLY"
    assert checks["source_control_bar_rows"]["actual"] == 7567
    assert checks["candidate_generator_input_only_rows"]["actual"] == 3014
    assert checks["accepted_bounded_scid_segments"]["actual"] == 9
    assert checks["candidate_denominator_economic_groups"]["actual"] == 7
    assert checks["discovery_exclusions"]["actual"] == 365
    assert checks["adversarial_baselines"]["actual"] == 4
    assert reconciliation["warnings_repaired"]["FORBIDDEN_SCAN_OVERMATCH_WIN_WINDOW"] is True
    assert reconciliation["warnings_repaired"]["TARGET_TESTS_DO_NOT_EXECUTE_HARD_FLOOR_CASE"] is True
    assert reconciliation["no_terminal_packet_blockers"] is True


def test_row_partition_covers_all_candidates_once_and_keeps_safe_flags():
    rows = load_jsonl("ROW_PARTITION_LEDGER")
    ids = [row["candidate_input_row_id"] for row in rows]

    assert len(rows) == 3014
    assert len(set(ids)) == 3014
    assert {row["partition_assignment"] for row in rows}.issubset(
        {"SEALED_VALIDATION_CANDIDATE_DESIGN", "STRESS_ROBUSTNESS_CANDIDATE_DESIGN"}
    )
    assert all(row["discovery_exposure_flag"] is False for row in rows)
    assert all(row["safe_flags"]["promotion_verdict"] == "NO_PROMOTION_VERDICT" for row in rows)
    assert all(row["safe_flags"]["validation_safe"] is False for row in rows)
    assert all(row["included_bar_hash_count"] == len(row["included_bar_hashes"]) for row in rows)


def test_duplicate_proxy_policy_baselines_science_horizon_and_next_prompt():
    duplicate = load_json("DUPLICATE_PROXY_DENOMINATOR_RULES")
    assert duplicate["candidate_denominator_group_count"] == 7
    assert duplicate["primary_counting_source_by_group"]["XAUUSD_GOLD_FUTURES_PROXY"] == "XAUUSD_GC"
    assert duplicate["primary_counting_source_by_group"]["US30_DOW_FUTURES_PROXY"] == "US30_YM"
    assert duplicate["duplicate_key_collisions"] == 0

    baselines = load_json("ADVERSARIAL_BASELINE_AND_ROBUSTNESS_PLAN")
    assert set(baselines["four_adversarial_baselines_preserved"]) == {
        "baseline_random_session_control",
        "baseline_shifted_entry_control",
        "baseline_momentum_continuation",
        "baseline_mean_reversion",
    }
    assert len(baselines["robustness_tests_required_before_promotion_discussion"]) >= 12

    science = load_json("SCIENCE_HORIZON_ROUTE_LEDGER")
    assert len(science["families"]) >= 9
    assert all(row["claim_status"] == "NO_CLAIM_WORKS" for row in science["families"])

    ranking = load_json("NEXT_ROUTE_RANKING")
    assert ranking["active_next_route"] == "G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT"
    assert ranking["validation_execution_prompt_emitted"] is False
    prompt_path = ROOT / "research/science_program_2026_05/04_goal_prompts/G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_GOAL_PROMPT_2026-05-11.md"
    prompt_text = prompt_path.read_text(encoding="utf-8")
    assert "Forbidden: validation execution" in prompt_text
    assert "NO_PROMOTION_VERDICT" in prompt_text
    assert "validation_safe=false" in prompt_text


def test_completion_audit_and_standalone_verifier_pass():
    result = verify()
    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"] is True

    completion = load_json("COMPLETION_AUDIT")
    assert completion["can_mark_goal_complete"] is True
    assert completion["completion_standard_satisfied"] is True
    assert completion["validation_safe"] is False
    assert completion["outcome_review_opened"] is False
    assert completion["live_effect"] is False
