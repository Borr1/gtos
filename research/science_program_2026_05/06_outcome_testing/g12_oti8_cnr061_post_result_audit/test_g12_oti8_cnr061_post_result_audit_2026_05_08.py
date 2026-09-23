import importlib.util
import json
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent
BUILDER_PATH = BASE / "build_g12_oti8_cnr061_post_result_audit_2026_05_08.py"
DATE = "2026-05-08"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


def load_builder():
    spec = importlib.util.spec_from_file_location("g12_oti8_builder", BUILDER_PATH)
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


def test_build_bundle_accepts_oti8_as_quarantined_discovery_evidence():
    builder = load_builder()
    bundle = builder.build_bundle("2026-05-08T00:00:00Z")
    decision = bundle["decision"]

    assert decision["decision"] == "ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE"
    assert decision["promotion_verdict"] == PROMOTION_VERDICT
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False
    assert "not validation-safe" in decision["non_promotion_boundary"] or "not validation" in decision["non_promotion_boundary"]


def test_source_hash_noleak_audit_recomputes_all_required_hashes():
    builder = load_builder()
    bundle = builder.build_bundle("2026-05-08T00:00:00Z")
    source = bundle["source"]

    assert source["hash_recompute_status"] == "PASS"
    assert source["source_policy_verdict"] == "PASS_SOURCE_HASHED_AND_NO_FORBIDDEN_LABEL_LEAKAGE"
    assert source["source_hash_failures"] == []
    assert len(source["sidecar_row_hash_recompute"]) == 8
    assert all(row["matches"] for row in source["sidecar_row_hash_recompute"])
    assert len(source["source_row_hash_recompute"]) == 8
    assert all(row["matches"] for row in source["source_row_hash_recompute"])
    assert {row["path"].split("\\")[-1] for row in source["quote_and_ordered_path_source_hash_recompute"]} == {
        "2026-05-04.parquet",
        "2026-05-05.parquet",
    }
    assert all(row["matches_all_declared_hashes"] for row in source["quote_and_ordered_path_source_hash_recompute"])
    assert source["forbidden_label_and_flag_scan"]["status"] == "PASS"


def test_duplicate_blocked_overlap_and_methodology_are_quarantined():
    builder = load_builder()
    duplicate = builder.build_bundle("2026-05-08T00:00:00Z")["duplicate"]
    blocked = duplicate["blocked_row_exclusion"]

    assert blocked["accepted_rows"] == 8
    assert blocked["blocked_rows"] == 94
    assert blocked["status"] == "PASS_EXACT_8_ACCEPTED_94_BLOCKED_AND_ZERO_COUNTABLE_OVERLAP"
    assert blocked["raw_blocked_overlap_disclosed"]["duplicate_denominator_key_overlap"]
    assert blocked["countable_blocked_overlap"] == {
        "duplicate_denominator_key_overlap": [],
        "duplicate_group_id_overlap": [],
        "record_id_overlap": [],
        "source_row_hash_overlap": [],
    }
    assert duplicate["method_freeze_before_scoring_evidence"]["method_comment_line"] < duplicate["method_freeze_before_scoring_evidence"]["terminal_score_call_line"]
    assert duplicate["methodology_noncomputability"]["statistical_verdict"] == "NOT_VALIDATION_NOT_PROMOTION_DSR_PBO_NOT_COMPUTABLE"
    assert duplicate["methodology_noncomputability"]["sample_floor"]["sample_floor_pass"] is False


def test_result_integrity_identifies_tiny_positive_and_no_terminal_rows():
    builder = load_builder()
    integrity = builder.build_bundle("2026-05-08T00:00:00Z")["integrity"]

    assert integrity["integrity_status"] == "PASS_TERMINAL_SCORING_INTERNALLY_CONSISTENT"
    assert integrity["row_level_summary"]["row_count"] == 8
    assert integrity["row_level_summary"]["target_before_stop_count"] == 2
    assert integrity["row_level_summary"]["no_terminal_count"] == 6
    assert integrity["countable_summary"]["row_count"] == 4
    assert len(integrity["terminal_target_rows"]) == 2
    assert all(row["tiny_residual_r"] for row in integrity["terminal_target_rows"])
    assert {row["synthetic_r"] for row in integrity["terminal_target_rows"]} == {0.054478301}
    assert len(integrity["unresolved_no_terminal_rows"]) == 6
    assert all(row["unresolved_condition_pass"] for row in integrity["unresolved_no_terminal_rows"])


def test_generated_artifacts_preserve_required_quarantine_flags():
    json_files = sorted(BASE.glob(f"G12_OTI8_CNR061_*_{DATE}.json"))
    assert json_files
    for path in json_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["promotion_verdict"] == PROMOTION_VERDICT, path.name
        assert payload["validation_safe"] is False, path.name
        assert payload["outcome_review_opened"] is False, path.name
        assert payload["live_effect"] is False, path.name
        assert payload["broker_actual_r_accessed"] is False, path.name
        assert payload["account_history_accessed"] is False, path.name
        assert payload["live_trade_results_accessed"] is False, path.name
        assert payload["paid_data_calls"] == 0, path.name
        assert payload["api_calls"] == 0, path.name
        assert payload["databento_calls"] == 0, path.name
        assert payload["mt5_order_calls"] == 0, path.name
        for key, value in walk(payload):
            if key in {"validation_safe", "outcome_review_opened", "live_effect"}:
                assert value is False


def test_completion_checklist_covers_prompt_requirements():
    completion = load_json(f"G12_OTI8_CNR061_COMPLETION_AUDIT_{DATE}.json")
    checklist = {row["requirement"]: row for row in completion["prompt_to_artifact_checklist"]}
    for requirement in [
        "mandatory_gtos_preflight",
        "context_anchor",
        "all_oti8_result_artifacts_read",
        "all_upstream_context_artifacts_read",
        "exact_8_accepted_row_hashes",
        "exact_94_blocked_row_exclusion",
        "source_hash_recomputation",
        "no_leak_label_family_audit",
        "duplicate_policy_raw_vs_countable_overlap",
        "method_freeze_before_scoring",
        "terminal_scoring_integrity",
        "tiny_positive_no_terminal_forensics",
        "dsr_pbo_effective_n_noncomputability",
        "g12_decision_accept_block_reject",
        "next_lane_prompt_pack",
    ]:
        assert checklist[requirement]["status"].startswith("PASS"), requirement

