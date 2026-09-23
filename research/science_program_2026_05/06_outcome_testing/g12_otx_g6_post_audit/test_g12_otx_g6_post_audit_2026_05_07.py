import json
from pathlib import Path


BASE = Path(__file__).resolve().parent
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


def load(name: str):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def test_generated_json_artifacts_parse_and_preserve_safety_flags():
    json_files = sorted(BASE.glob("G12_OTX_G6_*2026-05-07.json"))
    assert json_files
    for path in json_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["promotion_verdict"] == PROMOTION_VERDICT, path.name
        assert payload["validation_safe"] is False, path.name
        assert payload["outcome_review_opened"] is False, path.name
        assert payload["live_effect"] is False, path.name


def test_packet_decisions_are_terminal_and_match_g12_post_audit_scope():
    ledger = load("G12_OTX_G6_POST_AUDIT_DECISION_LEDGER_2026-05-07.json")
    decisions = {row["packet_id"]: row["terminal_g12_decision"] for row in ledger["packet_decisions"]}
    assert decisions == {
        "OTG0-PKT-060": "BLOCKED_WITH_EXACT_IMPOSSIBILITY_FROM_APPROVED_LOCAL_TICKS",
        "OTG0-PKT-061": "BLOCKED_WITH_EXACT_PARTIAL_TICK_COVERAGE_EVIDENCE",
        "OTG0-PKT-062": "ACCEPTED_AS_QUARANTINED_DISCOVERY_ONLY_WITH_ROW_EXCLUSIONS",
        "OTG0-PKT-063": "ACCEPTED_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_WITH_FROZEN_SUBSET_EXCLUSIONS",
        "OTG0-PKT-066": "ACCEPTED_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_WITH_FROZEN_SUBSET_EXCLUSIONS",
    }


def test_absolute_tick_missing_window_is_machine_recorded():
    audit = load("G12_OTX_G6_SOURCE_HASH_TICK_COVERAGE_AUDIT_2026-05-07.json")
    assert audit["tick_root_exists"] is True
    assert audit["worktree_data_ticks_parquet_files"] == []
    xau = audit["critical_xau_2026_05_06"]
    assert xau["exists"] is True
    assert xau["min_ts_utc"] == "2026-05-06T17:16:17.131000+00:00"
    assert [window["row_count"] for window in xau["windows"]] == [0, 0, 0]
    assert audit["source_hash_verdict"] == "PASS_CURRENT_REHASH_EXCEPT_EXPECTED_CONTEXT_CHURN"


def test_no_leakage_audit_finds_no_forbidden_packet_or_source_hits():
    audit = load("G12_OTX_G6_LEAKAGE_NOLEAK_AUDIT_2026-05-07.json")
    assert audit["rebuilt_proposal_forbidden_key_hits"] == []
    assert audit["quarantined_result_forbidden_key_hits_excluding_allowed_synthetic_r"] == []
    assert audit["forbidden_source_path_hits"] == []
    assert audit["broker_actual_r_opened"] is False
    assert audit["blocked_packet_outcomes_opened"] is False


def test_duplicate_and_subset_policies_are_explicit():
    duplicate = load("G12_OTX_G6_DUPLICATE_DENOMINATOR_AUDIT_2026-05-07.json")
    assert duplicate["proposal_duplicate_summary_by_packet"]["OTG0-PKT-060"]["record_count"] == 80
    assert duplicate["proposal_duplicate_summary_by_packet"]["OTG0-PKT-060"]["unique_duplicate_group_count"] == 20
    assert duplicate["oti4b_countable_discovery_rows"] == 9
    subsets = duplicate["accepted_future_subset_policy"]
    assert subsets["OTG0-PKT-063"]["source_ready_rows"] == 81
    assert len(subsets["OTG0-PKT-063"]["excluded_record_ids"]) == 5
    assert subsets["OTG0-PKT-066"]["source_ready_rows"] == 3
    assert len(subsets["OTG0-PKT-066"]["excluded_record_ids"]) == 4


def test_method_stats_are_not_validation_claims():
    stats = load("G12_OTX_G6_METHOD_STATS_AUDIT_2026-05-07.json")
    assert stats["oti4b_countable_discovery_rows"] == 9
    assert stats["oti4b_resolved_synthetic_r_rows"] == 5
    assert stats["oti4b_mean_synthetic_r_resolved_only"] == -0.5
    assert stats["dsr_status"]["status"] == "NOT_COMPUTABLE_DISCOVERY_ONLY_AND_BELOW_SAMPLE_FLOOR"
    assert stats["pbo_status"]["status"] == "NOT_COMPUTABLE_NO_TRAIN_TEST_VARIANT_MATRIX"
    assert stats["statistical_verdict"] == "NOT_VALIDATION_NOT_COMPUTABLE_BELOW_SAMPLE_FLOOR"


def test_completion_audit_covers_prompt_requirements_and_saturation():
    completion = load("G12_OTX_G6_COMPLETION_AUDIT_2026-05-07.json")
    assert completion["can_mark_goal_complete"] is True
    checklist = {row["requirement"]: row for row in completion["prompt_to_artifact_checklist"]}
    for requirement in [
        "mandatory_preflight_live_state",
        "context_freshness_contract",
        "absolute_tick_path_inspected",
        "otx_required_files_read",
        "prior_context_read",
        "otg0_pkt_060_decided",
        "otg0_pkt_061_decided",
        "otg0_pkt_062_decided",
        "otg0_pkt_063_decided",
        "otg0_pkt_066_decided",
        "no_promotion_flags_preserved",
        "forbidden_surfaces_untouched",
    ]:
        assert checklist[requirement]["status"] == "PASS"
    assert len(completion["per_packet_saturation_ledger"]) == 5


def test_next_lane_prompt_pack_contains_accepted_lanes_and_blocked_tasks():
    text = (BASE / "G12_OTX_G6_NEXT_LANE_PROMPT_PACK_2026-05-07.md").read_text(encoding="utf-8")
    assert "OTG0-PKT-062" in text
    assert "OTG0-PKT-063" in text
    assert "OTG0-PKT-066" in text
    assert "mechanical_ob_bounds_asof_v1" in text
    assert "2026-05-06T07:10:00Z" in text
    assert "NO_PROMOTION_VERDICT" in text
