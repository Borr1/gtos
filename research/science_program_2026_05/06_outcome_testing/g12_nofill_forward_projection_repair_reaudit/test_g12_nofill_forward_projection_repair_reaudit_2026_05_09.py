from __future__ import annotations

import json
from pathlib import Path


DATE = "2026-05-09"
OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
PROJECTION_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/nofill_forward_source_safe_projection_builder"


def load_json(name: str):
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def load_projection_rows():
    path = PROJECTION_DIR / f"NOFILL_FORWARD_SOURCE_SAFE_PROJECTION_ROWS_{DATE}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_terminal_decision_accepts_source_control_only():
    decision = load_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_DECISION_LEDGER_{DATE}.json")
    assert decision["terminal_decision"] == "ACCEPT_AS_SOURCE_CONTROL_PROJECTION_EVIDENCE_ONLY"
    assert decision["can_accept_as_source_control_projection_evidence_only"] is True
    assert decision["blocking_failures"] == []
    assert decision["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False
    assert decision["opens_result_scoring"] is False


def test_exact_blockers_and_warning_are_closed():
    decision = load_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_DECISION_LEDGER_{DATE}.json")
    closure = {item["issue_id"]: item for item in decision["blocker_closure"]}
    assert closure["G12-PROJ-BLOCKER-001"]["reaudit_status"] == "CLOSED"
    assert (
        closure["G12-PROJ-BLOCKER-001"]["closure_evidence"]["returncode"] == 0
        or closure["G12-PROJ-BLOCKER-001"]["closure_evidence"][
            "core_survived_with_current_audit_dir_dirty_only"
        ]
        is True
    )
    assert closure["G12-PROJ-BLOCKER-002"]["reaudit_status"] == "CLOSED"
    assert closure["G12-PROJ-BLOCKER-002"]["closure_evidence"]["fields_outside_exhaustive_allowlist"] == []
    assert closure["G12-PROJ-WARN-001"]["reaudit_status"] == "CLOSED"
    assert closure["G12-PROJ-WARN-001"]["closure_evidence"]["collapsed_to_source_field_missing_rows"] == 0


def test_denominators_partition_and_reject_overlap_are_preserved():
    denominator = load_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_DENOMINATOR_AUDIT_{DATE}.json")
    assert denominator["status"] == "PASS"
    assert denominator["projection_row_count"] == 298
    assert denominator["family_counts"] == {
        "accepted": 225,
        "reject": 65,
        "source_control": 4,
        "source_impossible": 4,
    }
    assert denominator["accepted_row_level_denominator"] == 225
    assert denominator["primary_duplicate_key_denominator"] == 182
    assert denominator["secondary_duplicate_group_denominator"] == 139
    assert denominator["reject_overlap_rows_recomputed_by_key"] == 47
    assert denominator["reject_overlap_denominator_delta"]["row_level_count_delta_from_rejects"] == 0


def test_exhaustive_allowlist_is_exact_current_projection_key_set():
    rows = load_projection_rows()
    emitted_keys = sorted({key for row in rows for key in row})
    allowlist = load_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_ALLOWLIST_AUDIT_{DATE}.json")
    assert allowlist["status"] == "PASS"
    assert allowlist["allowed_fields_equal_emitted_keys"] is True
    assert allowlist["emitted_projection_keys"] == emitted_keys
    assert allowlist["fields_outside_exhaustive_allowlist"] == []
    assert allowlist["unused_exhaustive_allowlist_fields"] == []


def test_touch_not_observed_missing_status_semantics_are_repaired():
    rows = load_projection_rows()
    touch_not_observed = [
        row for row in rows if row.get("entry_touch_spread_status") == "TOUCH_NOT_OBSERVED_SOURCE_SAFE"
    ]
    assert len(touch_not_observed) == 113
    assert all(
        row["missing_statuses"].get("entry_touch_spread_value_source_safe")
        == "TOUCH_NOT_OBSERVED_VALUE_NOT_APPLICABLE"
        for row in touch_not_observed
    )
    missing = load_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_MISSING_STATUS_AUDIT_{DATE}.json")
    assert missing["status"] == "PASS"
    assert missing["collapsed_to_source_field_missing_rows"] == 0
    assert missing["touch_not_observed_value_not_applicable_rows"] == 113


def test_hash_no_leak_and_local_heavy_controls_pass():
    source_hash = load_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_SOURCE_HASH_AUDIT_{DATE}.json")
    assert source_hash["status"] == "PASS"
    assert source_hash["hash_recompute"]["status"] == "PASS"
    assert source_hash["hash_recompute"]["source_hash_records"] == 56
    assert source_hash["hash_recompute"]["parser_hash_records"] == 3
    assert source_hash["hash_recompute"]["source_hash_strict_failures"] == []
    assert source_hash["hash_recompute"]["parser_hash_strict_failures"] == []

    no_leak = load_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_NO_LEAK_AUDIT_{DATE}.json")
    assert no_leak["status"] == "PASS"
    assert no_leak["forbidden_projection_key_hits"] == []
    assert no_leak["forbidden_projection_value_token_hits"] == []
    assert no_leak["closed_control_flag_issues"] == []
    assert no_leak["spread_source_issues"] == []

    search = load_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_SEARCH_LEDGER_{DATE}.json")
    assert search["status"] == "PASS"
    assert search["prior_worktree_extra_needed_matches"] == []


def test_completion_audit_maps_prompt_requirements():
    completion = load_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_COMPLETION_AUDIT_{DATE}.json")
    assert completion["status"] == "PASS"
    assert completion["can_mark_goal_complete_after_verification_and_commit"] is True
    assert completion["missing_required_artifacts"] == []
    statuses = {item["requirement"]: item["status"] for item in completion["prompt_to_artifact_checklist"]}
    assert statuses["g12_proj_blocker_001_closed"] == "PASS"
    assert statuses["g12_proj_blocker_002_closed"] == "PASS"
    assert statuses["missing_status_warning_closed"] == "PASS"
    assert statuses["partition_and_denominators_preserved"] == "PASS"
    assert statuses["no_paid_api_databento_or_mt5_calls"] == "PASS"
