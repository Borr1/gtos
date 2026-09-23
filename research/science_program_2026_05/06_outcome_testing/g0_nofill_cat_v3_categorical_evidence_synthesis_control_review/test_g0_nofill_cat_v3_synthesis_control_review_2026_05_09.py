#!/usr/bin/env python3
"""Focused tests for the G0 NOFILL CAT V3 synthesis/control review."""

from __future__ import annotations

import json

import build_g0_nofill_cat_v3_synthesis_control_review_2026_05_09 as builder
import verify_g0_nofill_cat_v3_synthesis_control_review_2026_05_09 as verifier


def test_recomputed_count_contract_facts_match_frozen_chain() -> None:
    inputs = builder.load_inputs()
    facts = builder.recompute_facts(inputs)

    assert facts["universe_equation"] == "298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject"
    assert facts["accepted_row_level_total"] == 225
    assert facts["primary_unique_nofill_duplicate_key_total"] == 182
    assert facts["secondary_unique_duplicate_group_id_total"] == 139
    assert facts["row_level_label_counts"] == builder.EXPECTED_ROW_LABELS
    assert facts["primary_nofill_duplicate_key_label_counts"] == builder.EXPECTED_PRIMARY_LABELS
    assert facts["secondary_duplicate_group_id_label_counts"] == builder.EXPECTED_SECONDARY_LABELS
    assert facts["reject_overlap_count"] == 47
    assert facts["source_noleak"]["source_hash_strict_failures"] == 0
    assert facts["source_noleak"]["source_hash_missing_records"] == 0
    assert facts["source_noleak"]["forbidden_row_key_or_value_hits"] == 0


def test_generated_outputs_exist_and_preserve_safe_flags() -> None:
    assert verifier.check_artifacts_exist()["status"] == "PASS"
    assert verifier.check_json_jsonl_parse()["status"] == "PASS"
    assert verifier.check_safe_flags()["status"] == "PASS"


def test_forbidden_terms_are_confined_to_policy_fields() -> None:
    result = verifier.check_forbidden_generated_fields()
    assert result["status"] == "PASS", result


def test_completion_audit_maps_prompt_to_artifacts() -> None:
    path = builder.OUT_DIR / "G0_NOFILL_CAT_V3_COMPLETION_AUDIT_2026-05-09.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    checklist_text = "\n".join(item["requirement"] for item in payload["prompt_to_artifact_checklist"])

    assert "GTOS preflight" in checklist_text
    assert "V3 source-control" in checklist_text
    assert "Frozen V3 result contract" in checklist_text
    assert "Count packet" in checklist_text
    assert "Duplicate/concentration" in checklist_text
    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["validation_safe"] is False
    assert payload["outcome_review_opened"] is False
    assert payload["live_effect"] is False
