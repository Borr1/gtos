import importlib.util
import json
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent
BUILDER_PATH = BASE / "build_g12_cnr_next_model_control_audit_2026_05_08.py"
DATE = "2026-05-08"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


def load_builder():
    spec = importlib.util.spec_from_file_location("g12_cnr_next_builder", BUILDER_PATH)
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
        for nested in value:
            yield from walk(nested)


def test_builder_recomputes_six_stop_after_horizon_rows():
    builder = load_builder()
    control = builder.load_control_pack()
    upstream = builder.load_upstream()
    lifecycle = builder.lifecycle_recompute(control, upstream)

    assert lifecycle["status"] == "PASS"
    assert lifecycle["row_count"] == 6
    assert lifecycle["oti8_no_terminal_row_count"] == 6
    assert lifecycle["label_counts"] == {"stop_after_original_horizon": 6}
    assert not lifecycle["source_hash_failures"]
    assert not lifecycle["forbidden_lifecycle_key_hits"]


def test_timing_and_target_audit_decisions_are_blocked_not_promoted():
    builder = load_builder()
    control = builder.load_control_pack()
    audit = builder.timing_target_prereg_audit(control)
    family_decisions = {item["family_id"]: item["decision"] for item in audit["family_audits"]}

    assert audit["decision"] == "ACCEPT_AS_RESEARCH_CONTROL_PREREGISTRATION_WITH_SOURCE_BLOCKERS"
    assert audit["timing_family_set_check"]["status"] == "PASS"
    assert audit["target_family_set_check"]["status"] == "PASS"
    assert family_decisions["CNR_E2_SIGNAL_EMITTED_AT_SOURCE"].endswith("BLOCK_CURRENT_ROWS")
    assert family_decisions["CNR_E3_DECISION_LATENCY_AWARE"].endswith("BLOCK_CURRENT_ROWS")
    assert family_decisions["CNR_E4_PRETOUCH_TRIGGER"].endswith("BLOCK_CURRENT_ROWS")
    assert family_decisions["CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL"] == "ACCEPT_AS_RESEARCH_PREREGISTRATION_BLOCK_SOURCE_READINESS"
    assert "LIFECYCLE_EVIDENCE_ONLY" in family_decisions["CNR_T3_TERMINAL_TIMEBOX_OR_LIFECYCLE"]


def test_source_noleak_duplicate_audit_preserves_boundaries_and_blocked_94():
    builder = load_builder()
    control = builder.load_control_pack()
    upstream = builder.load_upstream()
    lifecycle = builder.lifecycle_recompute(control, upstream)
    audit = builder.source_noleak_duplicate_audit(control, upstream, lifecycle)

    assert audit["boundary_flag_scan"]["status"] == "PASS"
    assert audit["lifecycle_forbidden_key_scan"]["status"] == "PASS"
    assert audit["blocked_94_exclusion"]["status"] == "PASS"
    assert audit["blocked_94_exclusion"]["blocked_rows"] == 94
    assert audit["blocked_94_exclusion"]["packet_rows_from_blocked_set"] == []
    assert audit["duplicate_denominator_review"]["row_count"] == 6
    assert audit["duplicate_denominator_review"]["unique_duplicate_groups"] == 1
    assert audit["sample_floor_review"]["sample_floor_for_validation_met"] is False


def test_lifecycle_audit_states_proves_and_does_not_prove_without_r_keys():
    audit = load_json(f"G12_CNR061_LIFECYCLE_PACKET_AUDIT_{DATE}.json")
    assert audit["decision"] == "ACCEPT_LIFECYCLE_EVIDENCE_ONLY"
    assert audit["scope_check"]["status"] == "PASS"
    assert audit["independent_lifecycle_recompute"]["label_counts"] == {"stop_after_original_horizon": 6}
    text = " ".join(audit["what_this_does_not_prove"])
    assert "does not compute or validate R/performance" in text
    assert "does not score, rescue, or reclassify the 94" in text
    for key, _value in walk(audit):
        assert key != "synthetic_r"
        assert key != "broker_actual_r"
        assert key != "account_history"
        assert key != "live_order_state"


def test_all_generated_json_preserve_research_boundaries():
    for path in BASE.glob(f"G12_CNR_*_{DATE}.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["promotion_verdict"] == PROMOTION_VERDICT, path.name
        assert payload["validation_safe"] is False, path.name
        assert payload["outcome_review_opened"] is False, path.name
        assert payload["live_effect"] is False, path.name
        assert payload["broker_actual_r_accessed"] is False, path.name
        assert payload["account_history_accessed"] is False, path.name
        assert payload["live_trade_results_accessed"] is False, path.name
        assert payload["live_order_state_accessed"] is False, path.name
        assert payload["paid_data_calls"] == 0, path.name
        assert payload["databento_calls"] == 0, path.name
        assert payload["mt5_order_calls"] == 0, path.name
        assert payload["mt5_account_calls"] == 0, path.name


def test_completion_checklist_covers_prompt_requirements():
    completion = load_json(f"G12_CNR_NEXT_COMPLETION_AUDIT_{DATE}.json")
    checklist = {item["requirement"]: item["status"] for item in completion["prompt_to_artifact_checklist"]}
    required = [
        "mandatory_gtos_preflight",
        "context_anchor_before_decisions",
        "required_control_inputs_read",
        "upstream_artifacts_read",
        "local_heavy_data_search",
        "E2_E3_E4_timing_preregistration",
        "T1_T2_T3_target_preregistration",
        "source_contracts",
        "no_leak_controls",
        "duplicate_sample_floor_controls",
        "exact_six_lifecycle_rows",
        "all_six_stop_after_original_horizon",
        "source_hash_recompute",
        "94_blocked_rows_excluded",
        "xagusd_residual_forensics",
        "next_lane_prompt_guidance",
    ]
    for item in required:
        assert item in checklist
        assert checklist[item].startswith("PASS"), item


def test_prompt_pack_keeps_next_lane_source_safe():
    prompt = (BASE / f"G12_CNR_NEXT_PROMPT_PACK_{DATE}.md").read_text(encoding="utf-8")
    assert "CNR_T3_LIFECYCLE_EXPANSION_SOURCE_PACKET_V1" in prompt
    assert "do not compute R/performance" in prompt
    assert "No 94 blocked-row scoring" in prompt
    assert "NO_PROMOTION_VERDICT" in prompt
