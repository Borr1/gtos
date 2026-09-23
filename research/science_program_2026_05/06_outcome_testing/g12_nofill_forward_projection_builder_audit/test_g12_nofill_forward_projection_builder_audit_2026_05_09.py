#!/usr/bin/env python3
"""Focused tests for the independent G12 projection-builder audit."""

from __future__ import annotations

import json
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent


def load_json(name: str) -> dict:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def test_denominator_recomputation_preserves_frozen_universe() -> None:
    data = load_json("G12_NOFILL_FORWARD_PROJECTION_BUILDER_DENOMINATOR_AUDIT_2026-05-09.json")
    assert data["status"] == "PASS"
    assert data["projection_row_count"] == 298
    assert data["family_counts"] == {
        "accepted": 225,
        "reject": 65,
        "source_control": 4,
        "source_impossible": 4,
    }
    assert data["accepted_row_level_denominator"] == 225
    assert data["primary_duplicate_key_denominator"] == 182
    assert data["secondary_duplicate_group_denominator"] == 139
    assert data["reject_overlap_rows_recomputed_by_key"] == 47
    assert data["reject_overlap_denominator_delta"] == {
        "row_level_count_delta_from_rejects": 0,
        "nofill_duplicate_key_count_delta_from_rejects": 0,
        "duplicate_group_id_count_delta_from_rejects": 0,
        "reason": "Accepted rows are filtered before denominator counting; reject/source-control/source-impossible rows have all count-member flags false.",
    }


def test_source_hash_no_leak_audit_blocks_allowlist_gap_only() -> None:
    data = load_json("G12_NOFILL_FORWARD_PROJECTION_BUILDER_SOURCE_HASH_NOLEAK_AUDIT_2026-05-09.json")
    assert data["hash_recompute"]["status"] == "PASS"
    assert data["forbidden_projection_key_hits"] == []
    assert data["forbidden_projection_value_token_hits"] == []
    assert data["closed_flag_issues"] == []
    assert data["spread_source_issues"] == []
    assert data["unsafe_fields_outside_declared_allowlist"] == []
    assert "projection_schema_version" in data["fields_outside_declared_allowlist"]
    assert data["missing_status_semantic_tightening_rows"] == 113
    assert data["decision_spread_status_counts"] == {
        "CAPTURED_SOURCE_SAFE": 167,
        "SOURCE_FIELD_MISSING": 131,
    }
    assert data["entry_touch_spread_status_counts"] == {
        "CAPTURED_SOURCE_SAFE": 59,
        "SOURCE_FIELD_MISSING": 126,
        "TOUCH_NOT_OBSERVED_SOURCE_SAFE": 113,
    }


def test_local_heavy_search_finds_no_extra_needed_prior_worktree_matches() -> None:
    data = load_json("G12_NOFILL_FORWARD_PROJECTION_BUILDER_LOCAL_HEAVY_SEARCH_AUDIT_2026-05-09.json")
    assert data["status"] == "PASS"
    assert data["needed_missing_candidate_id_count"] == 38
    assert data["prior_worktree_extra_needed_matches"] == []
    assert data["prior_worktree_log_files_checked"] >= 8
    assert all(item["exists"] for item in data["absolute_local_heavy_roots_checked"])


def test_decision_blocks_acceptance_with_exact_repair_route() -> None:
    decision = load_json("G12_NOFILL_FORWARD_PROJECTION_BUILDER_DECISION_LEDGER_2026-05-09.json")
    issues = load_json("G12_NOFILL_FORWARD_PROJECTION_BUILDER_ADVERSARIAL_ISSUE_LEDGER_2026-05-09.json")
    assert decision["terminal_verdict"] == "BLOCK_ACCEPTANCE_PENDING_EXACT_REPAIR"
    assert decision["can_accept_as_source_control_projection_evidence_only"] is False
    assert set(decision["blocking_issue_ids"]) == {"G12-PROJ-BLOCKER-001", "G12-PROJ-BLOCKER-002"}
    assert issues["blocking_issue_count"] == 2
    issue_ids = {item["issue_id"] for item in issues["issues"]}
    assert {"G12-PROJ-BLOCKER-001", "G12-PROJ-BLOCKER-002", "G12-PROJ-WARN-001"}.issubset(issue_ids)


def test_completion_audit_maps_prompt_requirements_to_evidence() -> None:
    completion = load_json("G12_NOFILL_FORWARD_PROJECTION_BUILDER_COMPLETION_AUDIT_2026-05-09.json")
    assert completion["can_mark_goal_complete_after_verification_and_commit"] is True
    assert completion["can_accept_projection_builder_as_g12_source_control_evidence"] is False
    statuses = {item["requirement"]: item["status"] for item in completion["prompt_to_artifact_checklist"]}
    assert statuses["mandatory_preflight"] == "PASS"
    assert statuses["recompute_298_universe"] == "PASS"
    assert statuses["recompute_225_182_139"] == "PASS"
    assert statuses["source_parser_hashes"] == "PASS"
    assert statuses["allowlist_projection_rules"] == "FAIL"
    assert statuses["upstream_projection_verifier_rerun"] == "FAIL"
    assert statuses["missing_status_semantics"] == "WARN"
