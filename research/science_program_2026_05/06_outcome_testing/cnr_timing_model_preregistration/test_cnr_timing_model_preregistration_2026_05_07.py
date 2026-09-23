import json
from pathlib import Path


BASE = Path(__file__).resolve().parent
DATE = "2026-05-07"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


def load(stem: str):
    return json.loads((BASE / f"{stem}_{DATE}.json").read_text(encoding="utf-8"))


def test_required_artifacts_exist_and_preserve_flags():
    stems = [
        "CNR_TIMING_MODEL_PREREGISTRATION",
        "CNR_TIMING_MODEL_SOURCE_FIELD_CONTRACT",
        "CNR_TIMING_MODEL_LATENCY_CAPTURE_SPEC",
        "CNR_TIMING_MODEL_NOLEAK_DUPLICATE_LABEL_POLICY",
        "CNR_TIMING_MODEL_MULTITIMEFRAME_EVIDENCE_MAP",
        "CNR_TIMING_MODEL_BLOCKER_AND_SAMPLE_FLOOR_LEDGER",
        "CNR_TIMING_MODEL_DATA_EXPANSION_PLAN",
        "CNR_TIMING_MODEL_NEXT_PACKET_PLAN",
        "CNR_TIMING_MODEL_CORRECT_DIRECTION_FAILURE_ANATOMY",
        "CNR_TIMING_MODEL_RECURSIVE_AMBIGUITY_LEDGER",
        "CNR_TIMING_MODEL_ANTI_BOXING_REVIEW",
        "CNR_TIMING_MODEL_CONTEXT_ANCHOR",
        "CNR_TIMING_MODEL_COMPLETION_AUDIT",
    ]
    for stem in stems:
        assert (BASE / f"{stem}_{DATE}.md").exists(), stem
        payload = load(stem)
        assert payload["promotion_verdict"] == PROMOTION_VERDICT, stem
        assert payload["validation_safe"] is False, stem
        assert payload["outcome_review_opened"] is False, stem
        assert payload["live_effect"] is False, stem


def test_preregistration_freezes_terminal_states_and_model_families():
    payload = load("CNR_TIMING_MODEL_PREREGISTRATION")
    terminal_states = {row["terminal_state"] for row in payload["terminal_states"]}
    for state in [
        "TARGET_ALREADY_PASSED_BEFORE_ELIGIBLE_EXECUTABLE_ENTRY",
        "NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF",
        "INSUFFICIENT_PRE_ENTRY_PATH_EVIDENCE",
        "SAME_BAR_OR_TERMINAL_ORDER_AMBIGUITY",
        "MISSING_SOURCE_HASH",
        "MISSING_QUOTE_SIDE",
        "DUPLICATE_DENOMINATOR_EXCLUSION",
        "CONTEXT_ONLY_ROW",
        "FUTURE_OUTCOME_TEST_ELIGIBLE_ONLY_AFTER_G12_G0_AUDIT",
    ]:
        assert state in terminal_states
    model_ids = {row["model_family_id"] for row in payload["future_model_families"]}
    assert {"CNR_E0_DECISION_CLOSE_MARKET", "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE", "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK", "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW", "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER"} <= model_ids
    target_ids = {row["target_model_id"] for row in payload["target_models"]}
    assert {"CNR_T0_ORIGINAL_TP1", "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY", "CNR_T2_ASOF_STRUCTURAL_LEVEL", "CNR_T3_TIMEBOX_TERMINAL"} <= target_ids


def test_correct_direction_anatomy_does_not_score_or_rescue():
    payload = load("CNR_TIMING_MODEL_CORRECT_DIRECTION_FAILURE_ANATOMY")
    assert payload["failure_type"] == "ENTRY_CLOCK_TOO_LATE_FOR_ORIGINAL_TARGET_GEOMETRY"
    assert payload["anatomy_verdict"] == "CORRECT_DIRECTION_MOVE_STUDIED_WITHOUT_SCORING_OR_RESCUE"
    events = {row["event"]: row for row in payload["timeline"]}
    assert events["decision_quote"]["evidence"]["ask"] == 4648.29
    assert events["decision_quote"]["interpretation"].startswith("LONG executable ask 4648.29")
    assert payload["target_eligibility"]["continuation_target"].startswith("future-only")


def test_source_contract_and_no_leak_policy_keep_forbidden_fields_out():
    source = load("CNR_TIMING_MODEL_SOURCE_FIELD_CONTRACT")
    assert source["quote_side_rule"]["LONG"].startswith("entry")
    assert "synthetic_path_r" in source["forbidden_fields"]
    policy = load("CNR_TIMING_MODEL_NOLEAK_DUPLICATE_LABEL_POLICY")
    assert policy["duplicate_denominator_policy"]["primary_denominator"] == "G6_CNR|symbol|trade_date|session|side|original_entry_price"
    assert any("target-already-passed" in rule for rule in policy["no_leak_controls"])


def test_multitimeframe_and_anti_boxing_cover_required_classes():
    mtf = load("CNR_TIMING_MODEL_MULTITIMEFRAME_EVIDENCE_MAP")
    roles = {row["timeframe"]: row["role"] for row in mtf["timeframe_roles"]}
    assert roles["tick_or_quote"] == "execution_timeframe"
    assert roles["M15"] == "trigger_timeframe"
    assert roles["H1_H4_D1"] == "context_timeframe"
    anti = load("CNR_TIMING_MODEL_ANTI_BOXING_REVIEW")
    classes = {row["class"] for row in anti["limitation_classes"]}
    assert {"timeframe", "data_location", "data_modality", "instrument_symbol", "science_domain", "model_class", "code_artifact_history", "access_path", "question_scope"} <= classes


def test_small_n_has_expansion_plan_not_stop_reason():
    ledger = load("CNR_TIMING_MODEL_BLOCKER_AND_SAMPLE_FLOOR_LEDGER")
    sample = [row for row in ledger["blockers"] if row["blocker_id"] == "B6_SAMPLE_SIZE"][0]
    assert sample["status"] == "NOT_A_PREREGISTRATION_BLOCKER_VALIDATION_BLOCKER_ONLY"
    expansion = load("CNR_TIMING_MODEL_DATA_EXPANSION_PLAN")
    manifest = expansion["next_extraction_manifest"]
    assert manifest["row_unit"] == "unique duplicate denominator per timing-family/target-model pair"
    assert "signal_emitted_utc" in manifest["fields"]
    assert "synthetic_path_r" in manifest["forbidden_fields"]


def test_completion_audit_instruction_coverage_is_machine_checkable():
    completion = load("CNR_TIMING_MODEL_COMPLETION_AUDIT")
    checklist = {row["requirement"]: row["status"] for row in completion["prompt_to_artifact_checklist"]}
    for required in [
        "run_generate_live_state",
        "controlling_inputs_read",
        "no_outcome_scoring",
        "freeze_timing_models",
        "freeze_target_models",
        "freeze_latency_capture",
        "freeze_no_leak_duplicate_policy",
        "data_expansion_not_small_n_stop",
        "anti_boxing_review",
        "context_anchor",
        "forbidden_live_surface",
    ]:
        assert checklist[required] == "satisfied"
