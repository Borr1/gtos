from __future__ import annotations

import json
from pathlib import Path

from verify_g0_fpb_sealed_partition_and_adversarial_baseline_packet_2026_05_11 import verify


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
DATE_TAG = "2026-05-11"
PREFIX = "G0_FPB_SEALED_PARTITION"


def load(name: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{name}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def test_counts_and_partition_block_current_discovery_universe():
    evidence = load("EVIDENCE_RECONCILIATION_LEDGER")
    assert evidence["all_counts_preserved"] is True
    checks = {row["check_id"]: row for row in evidence["count_checks"]}
    assert checks["raw_candidate_attempts"]["actual"] == 13_540_033
    assert checks["duplicate_candidate_keys"]["actual"] == 687_275
    assert checks["unique_nonduplicate_candidate_path_label_denominator"]["actual"] == 12_852_758
    assert checks["path_label_row_count"]["actual"] == 12_852_758
    assert checks["selected_source_count"]["actual"] == 365
    assert checks["excluded_source_slice_count"]["actual"] == 3135

    partition = load("PARTITION_LEDGER")
    assert partition["sealed_historical_validation_pool"]["current_source_rows"] == 0
    assert partition["sealed_historical_validation_pool"]["current_candidate_rows"] == 0
    assert partition["validation_execution_prompt_emitted"] is False
    assert partition["source_control_unblocker_prompt_emitted"] is True
    assert partition["discovery_pool"]["selected_packet_families"] == [
        "adjacent_range_compression_breakout",
        "ob_retest",
        "opening_drive_no_fill_lifecycle",
    ]


def test_baselines_ambiguity_concentration_and_source_contract_are_frozen():
    baseline = load("ADVERSARIAL_BASELINE_PACKET")
    assert baseline["all_four_baselines_frozen"] is True
    assert [row["family_id"] for row in baseline["baseline_controls"]] == [
        "baseline_random_session_control",
        "baseline_shifted_entry_control",
        "baseline_momentum_continuation",
        "baseline_mean_reversion",
    ]

    ambiguity = load("AMBIGUITY_UNRESOLVED_POLICY")
    assert set(ambiguity["fail_closed_labels_before_validation"]) == {
        "SAME_BAR_CONTEXT_AMBIGUOUS",
        "UNRESOLVED_BY_WINDOW",
        "UNRESOLVED_AT_SOURCE_END",
    }

    concentration = load("CONCENTRATION_AND_STRESS_REQUIREMENTS")
    assert concentration["caps"]["single_source_hash_max_share"] == 0.20
    assert concentration["caps"]["effective_n_family_floor"] == 30
    assert "all_four_baselines_required" in concentration["required_stress_tests"]

    source_contract = load("SOURCE_ASOF_NOLEAK_CONTRACT")
    assert source_contract["field_count"] >= 20
    assert all(row["no_leak_gate"] == "PASS_REQUIRED_BEFORE_VALIDATION" for row in source_contract["fields"])


def test_next_prompt_is_source_control_unblocker_not_validation():
    next_pack = load("NEXT_PROMPT_PACK")
    assert next_pack["next_prompt_type"] == "SOURCE_CONTROL_UNBLOCKER_NOT_VALIDATION"
    assert next_pack["validation_execution_prompt_emitted"] is False
    assert next_pack["source_control_unblocker_prompt_emitted"] is True

    prompt_path = ROOT / next_pack["next_prompt_path"]
    prompt_text = prompt_path.read_text(encoding="utf-8")
    assert "FPB_SOURCE_EXPANSION_AND_SEALED_POOL_MATERIALIZATION" in prompt_text
    assert "Forbidden: validation execution" in prompt_text
    assert "NO_PROMOTION_VERDICT" in prompt_text
    assert "validation_safe=false" in prompt_text
    assert "outcome_review_opened=false" in prompt_text
    assert "live_effect=false" in prompt_text


def test_hostile_review_no_lazy_blocker_and_verifier_pass():
    hostile = load("HOSTILE_EDGE_REVIEW_LEDGER")
    assert set(hostile["selected_family_reviews"]) == {
        "adjacent_range_compression_breakout",
        "ob_retest",
        "opening_drive_no_fill_lifecycle",
    }
    assert "fvg_fill" in hostile["deferred_or_excluded_family_reviews"]

    blocker = load("NO_LAZY_BLOCKER_LEDGER")
    assert blocker["remaining_vague_blockers"] == []
    assert blocker["remaining_same_evidence_class_gaps"] == []

    result = verify()
    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"] is True
