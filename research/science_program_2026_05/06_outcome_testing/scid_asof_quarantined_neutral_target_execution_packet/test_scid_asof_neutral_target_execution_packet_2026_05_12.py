from __future__ import annotations

import json
import sys
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROUTE_DIR))

import build_scid_asof_neutral_target_execution_packet_2026_05_12 as builder


def load_json(name: str) -> dict:
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def count_jsonl(name: str) -> int:
    with (ROUTE_DIR / name).open(encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def test_builder_reconciles_exact_input_counts_and_prerequisites() -> None:
    result = builder.build_all()
    assert result["terminal_count"] == 3014 * 4 * 2
    prereq = load_json(f"{builder.PREFIX}_PREREQUISITE_ACCEPTANCE_LEDGER_{builder.DATE_TAG}.json")
    assert all(prereq["acceptance_checks"].values())
    freeze = load_json(f"{builder.PREFIX}_PRE_TARGET_FREEZE_PACKET_{builder.DATE_TAG}.json")
    assert freeze["candidate_row_count"] == 3014
    assert freeze["bar_row_count"] == 7567
    assert freeze["partition_counts"]["SEALED_VALIDATION_CANDIDATE_DESIGN"] == 2432
    assert freeze["partition_counts"]["STRESS_ROBUSTNESS_CANDIDATE_DESIGN"] == 582
    assert freeze["denominator_group_count"] == 7


def test_every_candidate_horizon_family_has_one_terminal_status() -> None:
    builder.build_all()
    row_count = count_jsonl(f"{builder.PREFIX}_ROW_RESULTS_{builder.DATE_TAG}.jsonl")
    not_count = count_jsonl(f"{builder.PREFIX}_NOT_COMPUTABLE_LEDGER_{builder.DATE_TAG}.jsonl")
    assert row_count + not_count == 3014 * 4 * 2
    audit = load_json(f"{builder.PREFIX}_CONCENTRATION_DENOMINATOR_AUDIT_{builder.DATE_TAG}.json")
    assert audit["terminal_status_observed_combinations"] == audit["terminal_status_expected_combinations"]
    assert audit["terminal_duplicate_combination_count"] == 0


def test_descriptor_freeze_is_source_safe_and_pre_target() -> None:
    builder.build_all()
    desc = load_json(f"{builder.PREFIX}_DESCRIPTOR_FREEZE_LEDGER_{builder.DATE_TAG}.json")
    assert desc["descriptor_freeze_status"] == "FROZEN_BEFORE_TARGET_COMPUTATION"
    assert desc["descriptor_row_count"] == 3014
    assert "bars ending at or before entry_reference_time_utc" in " ".join(desc["descriptor_definitions"])


def test_not_computable_rows_fail_closed_without_imputation() -> None:
    builder.build_all()
    failure = load_json(f"{builder.PREFIX}_FAILURE_ANATOMY_LEDGER_{builder.DATE_TAG}.json")
    assert failure["not_computable_count"] >= 0
    assert "no imputation" in failure["failure_boundary"]
    for item in failure["same_evidence_class_blocker_pursuit"]:
        assert item["source_safe_repair_route"]


def test_safe_flags_and_no_strategy_scoring_remain_closed() -> None:
    builder.build_all()
    completion = load_json(f"{builder.PREFIX}_COMPLETION_AUDIT_{builder.DATE_TAG}.json")
    assert completion["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert completion["validation_safe"] is False
    assert completion["outcome_review_opened"] is False
    assert completion["live_effect"] is False
    assert completion["strategy_result_scoring_opened"] is False
    assert completion["can_mark_goal_complete"] is True


def test_next_g12_prompt_is_emitted() -> None:
    builder.build_all()
    assert builder.NEXT_G12_PROMPT.exists()
    text = builder.NEXT_G12_PROMPT.read_text(encoding="utf-8")
    assert "G12_SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_AUDIT_ONLY" in text
    assert "NO_PROMOTION_VERDICT" in text
