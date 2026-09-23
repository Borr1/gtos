import importlib.util
import json
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent
BUILDER = BASE / "build_g12_oti6_cnr_post_audit_2026_05_07.py"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TARGET_STATUS = "RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION"
TERMINAL_DECISION = "ACCEPT_AS_QUARANTINED_TARGET_ALREADY_PASSED_DISCOVERY_EVIDENCE"


def load_builder():
    spec = importlib.util.spec_from_file_location("g12_oti6_cnr_builder", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_json(name: str):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def walk(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key, nested
            yield from walk(nested)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)


def test_builder_recomputes_geometry_and_accepts_target_already_passed():
    builder = load_builder()
    artifacts = builder.build_bundle()
    decision = artifacts["G12_OTI6_CNR_DECISION_LEDGER_2026-05-07"]
    geometry = artifacts["G12_OTI6_CNR_GEOMETRY_AUDIT_2026-05-07"]

    assert decision["terminal_g12_decision"] == TERMINAL_DECISION
    assert decision["terminal_status"] == TARGET_STATUS
    assert "synthetic_path_r is null" in decision["not_rejected_for"]
    assert geometry["answer"] == "YES_CNR_E0_GEOMETRY_WAS_APPLIED_BEFORE_R_SCORING"
    assert geometry["recomputed_geometry"]["cnr_e0_executable_entry"] == 4648.29
    assert geometry["recomputed_geometry"]["original_take_profit_1"] == 4582.77
    assert geometry["recomputed_geometry"]["distance_entry_to_tp1_price"] == 65.52
    assert geometry["recomputed_geometry"]["distance_entry_to_tp1_r"] == 4.62385321
    assert geometry["recomputed_geometry"]["target_already_passed_at_decision"] is True
    assert geometry["recomputed_geometry"]["cnr_e0_long_geometry_valid_for_original_target"] is False


def test_geometry_code_evidence_and_r_scoring_block_are_file_grounded():
    geometry = load_json("G12_OTI6_CNR_GEOMETRY_AUDIT_2026-05-07.json")
    code = geometry["code_evidence"]

    assert code["geometry_call_precedes_result_ledger"] is True
    assert code["target_already_passed_long_branch_line"] < code["geometry_call_line"]
    assert code["geometry_call_line"] < code["result_ledger_line"]
    assert geometry["oti6_result_controls"]["r_scoring_attempted"] is False
    assert geometry["oti6_result_controls"]["synthetic_path_r"] is None
    assert geometry["oti6_result_controls"]["synthetic_path_r_status"] == "NOT_COMPUTED_PREREGISTERED_GEOMETRY_NOT_ELIGIBLE"
    assert geometry["ordered_path_context_not_scored"]["path_trended_up_after_decision"] is True
    assert "not_scored_reason" in geometry["ordered_path_context_not_scored"]


def test_source_hash_noleak_boundaries_are_preserved():
    source = load_json("G12_OTI6_CNR_SOURCE_HASH_NOLEAK_AUDIT_2026-05-07.json")
    assert source["all_required_files_exist"] is True
    assert source["all_consumed_files_hashed"] is True
    assert source["parquet_hash_review"]["matches_oti6_expected"] is True
    assert source["oti6_source_gate_review"]["source_gate_status"] == "PASS"
    assert source["oti6_source_gate_review"]["hash_failures"] == []
    assert source["no_leak_review"]["label_family_gate_status"] == "PASS"
    assert source["no_leak_review"]["post_decision_context_not_used_for_cnr_e0_scoring"] is True
    for value in source["forbidden_reads_or_calls"].values():
        assert value in (False, 0)
    assert source["audit_verdict"] == "PASS_SOURCE_HASH_AND_NOLEAK_BOUNDARIES_PRESERVED"


def test_label_duplicate_audit_keeps_families_separate():
    duplicate = load_json("G12_OTI6_CNR_LABEL_DUPLICATE_AUDIT_2026-05-07.json")
    assert duplicate["accepted_packet_record_count"] == 1
    assert duplicate["duplicate_group_id"] == "G6_CNR|XAUUSD|2026-05-06|london|LONG|4561.52"
    labels = duplicate["label_family_separation"]
    assert labels["input_packet_label_family"] == "input_only_features_no_labels"
    assert labels["lifecycle_context_label_family"] == "lifecycle_no_fill_context_only"
    assert labels["result_label_family"] == "synthetic_path_r_quarantined_discovery_only_not_computed"
    assert labels["validation_label_family"] is None
    assert duplicate["label_boundary_verdict"] == "PASS_SYNTHETIC_PATH_R_NULL_NOT_POOLED_WITH_BROKER_OR_LIFECYCLE_LABELS"


def test_learning_ledger_says_model_too_late_not_mechanism_dead():
    learning = load_json("G12_OTI6_CNR_LEARNING_AND_NEXT_HYPOTHESIS_LEDGER_2026-05-07.json")
    assert learning["terminal_g12_decision"] == TERMINAL_DECISION
    assert learning["mechanism_interpretation"] == "CNR_MECHANISM_NOT_DEAD_CNR_E0_DECISION_CLOSE_MARKET_MODEL_TOO_LATE_FOR_THIS_ROW"
    assert any("does not prove continuation/no-retrace is dead" in item for item in learning["what_it_does_not_mean"])
    assert any("Score the post-decision upward path" in item for item in learning["post_hoc_routes_rejected"])
    next_hypothesis = learning["next_hypothesis_to_register"]
    assert next_hypothesis["lane_id"] == "CNR_TIMING_MODEL_PREREGISTRATION"
    assert next_hypothesis["scope"] == "preregistration/control only; no scoring opened"
    assert "do not score R" in next_hypothesis["one_line_goal_prompt"]


def test_next_lane_prompt_is_one_physical_line_and_control_only():
    text = (BASE / "G12_OTI6_CNR_NEXT_LANE_PROMPT_PACK_2026-05-07.md").read_text(encoding="utf-8")
    prompts = [line for line in text.splitlines() if line.startswith("/goal ")]
    assert len(prompts) == 1
    prompt = prompts[0]
    assert "CNR_TIMING_MODEL_PREREGISTRATION" in prompt
    assert "preregistration/control lane only" in prompt
    assert "before any outcome opening" in prompt
    assert "do not score R" in prompt
    assert "NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false" in prompt
    assert "broker actual-R/account-history/live trade results/live order state/paid/API/Databento/MT5 order calls" in prompt


def test_generated_json_artifacts_parse_and_preserve_flags():
    files = sorted(BASE.glob("G12_OTI6_CNR_*2026-05-07.json"))
    assert len(files) == 6
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["promotion_verdict"] == PROMOTION_VERDICT, path.name
        assert payload["validation_safe"] is False, path.name
        assert payload["outcome_review_opened"] is False, path.name
        assert payload["live_effect"] is False, path.name
        assert payload["broker_actual_r_accessed"] is False, path.name
        assert payload["account_history_accessed"] is False, path.name
        assert payload["live_order_state_accessed"] is False, path.name
        assert payload["live_trade_results_accessed"] is False, path.name
        assert payload["blocked_packet_outcome_source_read"] is False, path.name
        assert payload["api_calls"] == 0, path.name
        assert payload["databento_calls"] == 0, path.name
        assert payload["paid_data_calls"] == 0, path.name
        assert payload["mt5_order_calls"] == 0, path.name


def test_completion_audit_maps_prompt_requirements():
    completion = load_json("G12_OTI6_CNR_COMPLETION_AUDIT_2026-05-07.json")
    checklist = {row["requirement"]: row for row in completion["prompt_to_artifact_checklist"]}
    for requirement in [
        "mandatory_preflight_generate_live_state",
        "mandatory_preflight_live_state_read",
        "latest_numbered_handoff_read",
        "quick_reference_read",
        "research_operating_doctrine_read",
        "research_current_state_read",
        "goal_session_research_discipline_read",
        "local_heavy_data_inventory_read",
        "oti6_direct_inputs_read_md_json_builder_verifier_tests",
        "upstream_controls_read",
        "terminal_status_verified",
        "terminal_decision_chosen",
        "do_not_reject_for_null_synthetic_r",
        "cnr_e0_geometry_applied_before_r_scoring_audited",
        "source_hash_noleak_preserved",
        "label_duplicate_preserved",
        "learning_and_next_hypothesis_written",
        "next_preregistration_control_prompt_written",
        "no_promotion_flags_preserved",
        "no_forbidden_sources_or_calls",
    ]:
        assert checklist[requirement]["status"] == "PASS", requirement

