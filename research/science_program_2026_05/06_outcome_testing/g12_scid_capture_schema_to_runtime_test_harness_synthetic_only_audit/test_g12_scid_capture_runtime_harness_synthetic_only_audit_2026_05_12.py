import json

import build_g12_scid_capture_runtime_harness_synthetic_only_audit_2026_05_12 as audit


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_recompute_fixture_matrix_from_disk_matches_required_counts():
    recomputation = audit.recompute_fixture_matrix()
    assert recomputation["fixture_matrix_ok"], recomputation
    assert recomputation["filesystem_fixture_file_count"] == 109
    assert recomputation["filesystem_row_fixture_count"] == 117
    assert recomputation["manifest_fixture_case_count"] == 109
    assert len(recomputation["capture_groups_expected"]) == 10


def test_unavailable_source_policy_is_exactly_ltf_orderflow_valid_only():
    recomputation = audit.recompute_fixture_matrix()
    per_group = recomputation["per_group_positive_and_unavailable_routes"]
    valid_unavailable_groups = {
        group
        for group, row in per_group.items()
        if row["unavailable_expected_valid"] is True
    }
    invalid_unavailable_groups = {
        group
        for group, row in per_group.items()
        if row["unavailable_expected_valid"] is False
    }
    assert valid_unavailable_groups == audit.MARKET_CONTEXT_UNAVAILABLE_GROUPS
    assert invalid_unavailable_groups == set(audit.CAPTURE_GROUPS) - audit.MARKET_CONTEXT_UNAVAILABLE_GROUPS


def test_recursive_noleak_recomputation_keeps_expected_valid_rows_clean():
    noleak = audit.recompute_no_leak()
    assert noleak["no_leak_ok"], noleak
    assert noleak["recomputed_expected_valid_forbidden_hit_fixtures"] == []
    assert noleak["recomputed_deliberate_negative_forbidden_hit_count"] == 10


def test_manifest_binding_policy_accepts_only_bounded_repair():
    manifest_binding = audit.audit_manifest_binding()
    assert manifest_binding["manifest_binding_policy_ok"], manifest_binding
    assert manifest_binding["output_manifest_self_hash_policy"] == "SELF_REFERENTIAL_MANIFEST_HASH_NON_BLOCKING"
    assert manifest_binding["valid_repair_policy"]["current_g12_prompt_hash_supersedes_stale_pre_hardening_hash"] is True
    assert manifest_binding["valid_repair_policy"]["output_manifest_self_hash_drift_is_nonblocking"] is True
    assert manifest_binding["valid_repair_policy"]["all_other_source_and_input_hash_mismatches_are_strict_blockers"] is True
    assert manifest_binding["invalid_repair_policy"]["all_other_source_and_input_hash_mismatches_are_strict_blockers"] is False


def test_generated_completion_audit_if_builder_has_run():
    completion_path = audit.AUDIT_DIR / f"{audit.PREFIX}_COMPLETION_AUDIT_{audit.DATE_TAG}.json"
    if not completion_path.exists():
        return
    completion = read_json(completion_path)
    assert completion["terminal_decision"] == audit.TERMINAL_ACCEPT
    assert completion["can_mark_goal_complete_after_scoped_commit"] is True
    assert all(item["satisfied"] for item in completion["completion_checklist"])
    assert completion["validation_safe"] is False
    assert completion["outcome_review_opened"] is False
    assert completion["live_effect"] is False
