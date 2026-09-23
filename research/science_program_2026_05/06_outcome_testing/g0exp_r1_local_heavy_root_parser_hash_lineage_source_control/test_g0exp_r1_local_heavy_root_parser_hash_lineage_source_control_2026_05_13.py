from __future__ import annotations

import json
from pathlib import Path

from verify_g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_2026_05_13 import verify


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
DATE_TAG = "2026-05-13"
PREFIX = "G0EXP_R1"


def load(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def test_source_root_ledger_covers_absolute_and_prior_roots_without_raw_copy():
    payload = load("SOURCE_ROOT_SEARCH_HASH_DEFERRAL_LEDGER")
    labels = {row["label"] for row in payload["scanned_roots"]}

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["validation_safe"] is False
    assert payload["outcome_review_opened"] is False
    assert payload["live_effect"] is False
    assert "absolute_main_repo_data_ticks" in labels
    assert "tmp_gtos_nextwave_worktrees" in labels
    assert "tmp_gtos_otb_prior_worktrees" in labels
    assert "sierrachart_root" in labels
    assert payload["hash_deferral_count"] >= 1
    assert payload["no_raw_market_blob_content_copied"] is True
    assert all("exact_rehash_procedure" in row for row in payload["hash_deferral_records"][:5])


def test_parser_matrix_hashes_code_and_schema_shapes():
    payload = load("PARSER_VERSION_SHAPE_FINGERPRINT_MATRIX")
    rows = payload["parser_rows"]
    schema_rows = payload["schema_shape_rows"]

    assert payload["parser_file_count"] >= 10
    assert payload["schema_shape_file_count"] >= 10
    assert any("scid" in row["path"].lower() for row in rows)
    assert all(row["parser_code_hash"] for row in rows[:20])
    assert all(row["shape_fingerprint"] for row in rows[:20])
    assert all(row["key_shape_fingerprint"] for row in schema_rows[:20])
    assert payload["matrix_status"] == "CLOSED_PARSER_AND_SCHEMA_FINGERPRINTS_EMITTED"


def test_lineage_manifest_binds_inputs_scripts_and_outputs():
    payload = load("ARTIFACT_LINEAGE_MANIFEST_BINDING_PROOF")

    assert payload["all_required_inputs_exist"] is True
    assert payload["all_route_scripts_hashed"] is True
    assert payload["raw_market_blob_outputs"] == []
    required_paths = {row["path"] for row in payload["upstream_input_rows"]}
    assert ".context/LIVE_STATE.md" in required_paths
    assert any(path.endswith("G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_GOAL_PROMPT_2026-05-13.md") for path in required_paths)
    assert len(payload["output_artifact_rows"]) >= 20


def test_blocker_decision_and_quarantine_ledgers_cover_assigned_and_overflow():
    blocker = load("BLOCKER_PURSUIT_LEDGER")
    decision = load("ACTIVE_QUESTION_STACK_ROUTE_DECISION_LEDGER")
    denom = load("DENOMINATOR_QUARANTINE_PROOF")
    assigned = {row["candidate_id"] for row in blocker["assigned_family_rows"]}

    assert assigned == {"R4-EXP-ROOT-001", "R4-EXP-PARSER-001", "EXP-ADV-001", "R4-EXP-CODEHIST-001"}
    assert blocker["all_assigned_families_reduced_to_closed_or_exact"] is True
    assert len(decision["adjacent_overflow_decisions"]) >= 6
    assert all(row["accepted_40_card_denominator_inclusion"] is False for row in decision["adjacent_overflow_decisions"])
    assert denom["accepted_40_count_recomputed_from_upstream"] == 40
    assert denom["r1_new_denominator_rows_added"] == 0
    assert denom["result_or_validation_opened"] is False


def test_no_raw_audit_and_output_manifest_stay_source_control_only():
    no_raw = load("NO_RAW_MARKET_BLOB_COMMIT_AUDIT")
    manifest = load("OUTPUT_MANIFEST")

    assert no_raw["audit_status"] == "PASS_NO_RAW_MARKET_BLOB_COMMIT_BY_THIS_ROUTE"
    assert no_raw["no_raw_market_blob_generated"] is True
    assert no_raw["no_scoped_dirty_raw_market_blob"] is True
    assert no_raw["no_forbidden_live_surface_in_scope"] is True
    assert manifest["raw_market_blob_artifact_count"] == 0
    assert all(row["sha256"] for row in manifest["artifacts"])


def test_saturation_completion_and_next_prompt_are_present():
    saturation = load("SATURATION_SELF_RED_TEAM_LEDGER")
    completion = load("COMPLETION_AUDIT")
    prompt = ROOT / "research/science_program_2026_05/04_goal_prompts/G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-13.md"
    starter = ROUTE_DIR / "G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT_STARTER_2026-05-13.txt"

    risks = {row["risk"] for row in saturation["checks"]}
    assert {"worktree_blindness", "ignored_heavy_data", "parser_drift", "eol_hash_drift", "manifest_self_hash", "raw_blob_risk", "accidental_denominator_admission"}.issubset(risks)
    assert saturation["same_evidence_class_gaps_remaining"] == []
    assert completion["completion_standard_satisfied_before_commit"] is True
    assert prompt.exists()
    assert starter.exists()
    assert "\n" not in starter.read_text(encoding="utf-8").strip()


def test_standalone_verifier_passes():
    result = verify(mark_focused_tests_ok=True, write_result=False)

    assert result["ok"], result["failures"]
    assert result["assigned_family_count_verified"] == 4
    assert result["accepted_40_count_verified"] == 40
    assert result["r1_new_denominator_rows_added"] == 0
    assert result["can_mark_goal_complete"] is True
