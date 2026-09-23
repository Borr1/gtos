"""Focused tests for the SCID no-API ready-8 materialization packet."""

from __future__ import annotations

import json
from pathlib import Path

import build_scid_noapi_ready8_rowset_materialization_2026_05_12 as builder
import verify_scid_noapi_ready8_rowset_materialization_2026_05_12 as verifier


ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-12"
PREFIX = "SCID_NOAPI_READY8"


def path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def read_json(stem: str) -> dict:
    return json.loads(path(stem).read_text(encoding="utf-8"))


def read_jsonl(stem: str) -> list[dict]:
    return [
        json.loads(line)
        for line in path(stem, ".jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_ready8_rowset_materializes_all_candidates_and_cards() -> None:
    manifest = read_json("ROWSET_MANIFEST")
    assert manifest["accepted_card_denominator_count"] == 40
    assert manifest["ready_card_denominator_count"] == 8
    assert manifest["source_candidate_row_count"] == 3014
    assert manifest["rowset_row_count"] == 3014 * 8
    assert set(manifest["ready_card_ids"]) == set(builder.READY_CARD_IDS)
    assert set(manifest["per_card_row_counts"].values()) == {3014}
    assert manifest["row_level_exclusion_count"] == 0


def test_rowset_rows_are_source_hashed_asof_bound_and_non_scoring() -> None:
    rows = read_jsonl("ROWSET_ROWS")
    assert len(rows) == 3014 * 8
    assert len({row["candidate_input_row_id"] for row in rows}) == 3014
    assert len({row["duplicate_proxy_denominator_key"] for row in rows}) == 3014
    assert len({row["row_hash"] for row in rows}) == len(rows)
    forbidden = verifier.FORBIDDEN_EXACT_KEYS
    for row in rows[:100] + rows[-100:]:
        assert row["source_hash"]
        assert row["row_hash"]
        assert row["source_observed_asof_utc"] <= row["decision_asof_utc"]
        assert not (set(row) & forbidden)
        assert row["safe_flags"] == {
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        }


def test_contracts_and_manifests_keep_result_gate_closed() -> None:
    target = read_json("TARGET_HORIZON_CONTRACT")
    gate = read_json("RESULT_OPENING_GATE_DECISION")
    duplicate = read_json("DUPLICATE_DENOMINATOR_MANIFEST")
    partition = read_json("PARTITION_CONTROL_MANIFEST")
    baseline = read_json("BASELINE_CONTROL_ASSIGNMENT_MANIFEST")
    assert target["target_or_hazard_hits_computed"] is False
    assert target["performance_or_result_fields_present"] is False
    assert not verifier.recursive_key_hits(target)
    assert gate["may_score_results_now"] is False
    assert gate["g12_audit_required_before_any_result_opening"] is True
    assert duplicate["duplicate_key_collision_count"] == 0
    assert duplicate["incomplete_card_expansion_count"] == 0
    assert partition["source_candidate_partition_count"] == 3014
    assert baseline["deterministic_assignments_only"] is True
    assert baseline["result_or_performance_lookup_used"] is False


def test_blocked_and_expansion_denominators_remain_separate() -> None:
    blocker = read_json("BLOCKER_OR_DEPENDENCY_LEDGER")
    expansion = read_json("EXPANSION_OBSERVATION_LEDGER")
    assert blocker["ready8_source_control_blocker_count"] == 0
    assert blocker["blocked_32_denominator_preserved"] is True
    assert blocker["blocked_32_dependency_row_count"] == 32
    assert expansion["accepted_40_is_floor_not_ceiling"] is True
    assert expansion["all_expansion_observations_remain_outside_accepted_denominator"] is True
    assert expansion["all_expansion_observations_remain_outside_ready8_denominator"] is True


def test_verifier_accepts_materialized_packet_without_writing() -> None:
    result = verifier.verify(write_result=False)
    assert result["ok"], result["failures"]
    assert result["ready_card_count_verified"] == 8
    assert result["source_candidate_count_verified"] == 3014
    assert result["rowset_row_count_verified"] == 3014 * 8
