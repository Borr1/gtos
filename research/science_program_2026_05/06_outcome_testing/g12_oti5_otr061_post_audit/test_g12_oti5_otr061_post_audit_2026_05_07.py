import json
from pathlib import Path

import pyarrow.parquet as pq


BASE = Path(__file__).resolve().parent
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


def load(name: str):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def walk_keys(value, path="$"):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield f"{path}.{key}", key
            yield from walk_keys(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            yield from walk_keys(item, f"{path}[{idx}]")


def test_generated_json_artifacts_parse_and_preserve_safety_flags():
    json_files = sorted(BASE.glob("G12_*2026-05-07.json"))
    assert json_files
    for path in json_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["promotion_verdict"] == PROMOTION_VERDICT, path.name
        assert payload["validation_safe"] is False, path.name
        assert payload["outcome_review_opened"] is False, path.name
        assert payload["live_effect"] is False, path.name


def test_terminal_decisions_accept_oti5_and_otr061_for_quarantined_scope_only():
    ledger = load("G12_OTI5_OTR061_DECISION_LEDGER_2026-05-07.json")
    assert ledger["terminal_decisions"] == {
        "OTI5": "ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE",
        "OTR061": "ACCEPT_PACKET_FOR_FUTURE_QUARANTINED_RESULT_AUDIT",
    }
    for decision in ledger["decisions"]:
        assert "promotion" not in decision["acceptance_scope"].lower() or "not" in decision["acceptance_scope"].lower()
    assert ledger["global_boundaries"]["no_validation_or_promotion_meaning"] is True


def test_oti5_method_claims_are_file_grounded_and_not_validation_stats():
    audit = load("G12_OTI5_RESULT_METHOD_AUDIT_2026-05-07.json")
    claims = {row["claim"]: row for row in audit["verified_claims"]}
    for key in [
        "raw_total_packet_rows",
        "source_ready_rows",
        "g12_blocked_rows_excluded",
        "unique_duplicate_groups",
        "duplicate_primary_rows",
        "resolved_synthetic_tick_r_rows",
        "terminal_sl_count",
        "terminal_tp1_count",
        "terminal_no_entry_count",
        "mean_resolved_synthetic_r",
        "dsr_status",
        "pbo_status",
        "effective_n_status",
    ]:
        assert claims[key]["status"] == "PASS", key
    assert audit["frozen_subset"]["source_ready_rows"] == 81
    assert len(audit["frozen_subset"]["excluded_record_ids"]) == 5
    assert audit["metric_summary"]["terminal_status_counts"] == {
        "ENTRY_TOUCHED_THEN_SL": 8,
        "ENTRY_TOUCHED_THEN_TP1": 1,
        "NO_ENTRY_TOUCH_NO_R_SCORED": 8,
    }
    assert audit["methodology_terminal_review"]["hidden_validation_route"] == "NO_HONEST_ROUTE_FROM_CURRENT_FILES"
    assert audit["audit_verdict"] == "PASS_ACCEPT_DISCOVERY_ONLY_CONTROLS_SOUND"


def test_oti5_negative_forensics_answers_failure_anatomy_without_rescue_rule():
    forensics = load("G12_OTI5_NEGATIVE_RESULT_FORENSICS_2026-05-07.json")
    assert forensics["primary_countable_rows"] == 17
    assert forensics["resolved_synthetic_rows"] == 9
    assert forensics["terminal_status_counts"] == {
        "ENTRY_TOUCHED_THEN_SL": 8,
        "ENTRY_TOUCHED_THEN_TP1": 1,
        "NO_ENTRY_TOUCH_NO_R_SCORED": 8,
    }
    assert len(forensics["casebook_primary_rows"]) == 17
    assert "did not identify" in forensics["failure_anatomy"]["headline"]
    assert len(forensics["future_hypotheses_to_register"]) >= 3
    assert any("threshold" in item for item in forensics["tempting_rescue_routes_rejected"])
    assert forensics["audit_verdict"] == "NEGATIVE_RESULT_LEARNED_NOT_PROMOTABLE"


def test_otr061_packet_recovery_claims_match_direct_parquet_evidence():
    audit = load("G12_OTR061_PACKET_RECOVERY_AUDIT_2026-05-07.json")
    stats = audit["parquet_direct_verification"]
    assert audit["terminal_g12_decision"] == "ACCEPT_PACKET_FOR_FUTURE_QUARANTINED_RESULT_AUDIT"
    assert stats["sha256"] == "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"
    assert stats["row_count"] == 89391
    assert stats["first_tick_utc"] == "2026-05-06T07:10:01.820000Z"
    assert stats["last_tick_utc"] == "2026-05-06T11:15:59.763000Z"
    assert stats["decision_quote"]["quote_timestamp_utc"] == "2026-05-06T07:14:59.889000Z"
    assert stats["decision_quote"]["executable_decision_price_long_ask"] == 4648.29
    assert stats["ordered_path"]["first_timestamp_utc"] == "2026-05-06T07:15:00.634000Z"
    assert stats["ordered_path"]["last_timestamp_utc"] == "2026-05-06T11:14:59.900000Z"
    assert stats["ordered_path"]["post_horizon_first_timestamp_utc"] == "2026-05-06T11:15:00.335000Z"
    assert audit["previous_blocker_answered"]["status"] == "YES_FOR_INPUT_PACKET_RECOVERY"

    parquet_path = BASE.parent / "otr061_xau_tick_recovery" / "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"
    table = pq.read_table(parquet_path)
    assert table.num_rows == 89391


def test_source_hash_noleak_and_duplicate_label_controls_remain_closed():
    source = load("G12_OTI5_OTR061_SOURCE_HASH_NOLEAK_AUDIT_2026-05-07.json")
    duplicate = load("G12_OTI5_OTR061_DUPLICATE_LABEL_AUDIT_2026-05-07.json")
    assert source["oti5_source_hash_review"]["source_gate_pass"] is True
    assert source["oti5_source_hash_review"]["material_source_hash_failure_count"] == 0
    assert source["otr061_source_hash_review"]["current_parquet_hash_matches_expected"] is True
    assert source["noleak_review"]["oti5_broker_actual_r_opened"] is False
    assert source["noleak_review"]["otr061_account_history_accessed"] is False
    assert source["noleak_review"]["otr061_result_label_key_hits"] == []
    assert source["audit_verdict"] == "PASS_SOURCE_HASH_AND_NOLEAK_FOR_QUARANTINED_SCOPE"

    assert duplicate["oti5_duplicate_denominator"]["unique_duplicate_group_count"] == 17
    assert duplicate["oti5_label_family"]["result_label_family"] == "synthetic_path_r_quarantined_discovery_only"
    assert duplicate["otr061_duplicate_and_label"]["record_count"] == 1
    assert duplicate["otr061_duplicate_and_label"]["label_family"] == "input_only_features_no_labels"
    assert duplicate["label_family_separation_verdict"] == "PASS_SYNTHETIC_PATH_R_AND_INPUT_ONLY_PACKET_SEPARATED"


def test_next_lane_prompt_is_one_physical_line_and_hardened():
    text = (BASE / "G12_OTI5_OTR061_NEXT_LANE_PROMPT_PACK_2026-05-07.md").read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if line.startswith("/goal ")]
    assert len(lines) == 1
    prompt = lines[0]
    assert "OTG0-PKT-061" in prompt
    assert "OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.json" in prompt
    assert "proof-or-impossibility" in prompt
    assert "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks" in prompt
    assert "no broker actual-R/account-history/live trade result/live order state" in prompt
    assert "no paid/API/Databento" in prompt
    assert "NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false" in prompt


def test_completion_audit_maps_prompt_requirements_to_pass():
    completion = load("G12_OTI5_OTR061_COMPLETION_AUDIT_2026-05-07.json")
    assert completion["can_mark_goal_complete_after_external_verification"] is True
    checklist = {row["requirement"]: row for row in completion["prompt_to_artifact_checklist"]}
    for requirement in [
        "mandatory_preflight_live_state_regenerated_and_read",
        "latest_handoff_read",
        "quick_reference_read",
        "research_doctrine_read",
        "research_current_state_read",
        "goal_session_discipline_read",
        "local_heavy_data_inventory_read",
        "oti5_controlling_artifacts_read",
        "otr061_controlling_artifacts_read",
        "prior_controls_read",
        "oti5_terminal_decision_written",
        "otr061_terminal_decision_written",
        "oti5_negative_forensics_written",
        "otr061_next_lane_prompt_written",
        "source_hash_noleak_audit_written",
        "duplicate_label_audit_written",
        "no_promotion_flags_preserved",
        "forbidden_surfaces_untouched_by_builder_scope",
    ]:
        assert checklist[requirement]["status"] == "PASS", requirement

