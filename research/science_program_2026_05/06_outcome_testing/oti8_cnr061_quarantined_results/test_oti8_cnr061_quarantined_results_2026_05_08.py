import importlib.util
import json
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent
BUILDER_PATH = BASE / "build_oti8_cnr061_quarantined_results_2026_05_08.py"
DATE = "2026-05-08"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


def load_builder():
    spec = importlib.util.spec_from_file_location("oti8_cnr061_builder", BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_json(name: str):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def load_jsonl(name: str):
    return [json.loads(line) for line in (BASE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def walk(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key, nested
            yield from walk(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from walk(nested)


def test_builder_recomputes_exact_cohort_and_blocked_counts():
    builder = load_builder()
    sidecar = builder.load_sidecar_rows()
    source_rows, source_by_hash, _ = builder.load_source_rows_for_pkt061()
    accepted_sources = {builder.accepted_source_hash(row) for row in sidecar}
    blocked = [row for row in source_rows if row.get("row_sha256") not in accepted_sources]
    countable_blocked = [row for row in blocked if row.get("countable_denominator_row") is True]
    accepted_denoms = {row["duplicate_denominator_key"] for row in sidecar}
    accepted_groups = {row["duplicate_group_id"] for row in sidecar}

    assert len(sidecar) == 8
    assert len(source_rows) == 102
    assert len(blocked) == 94
    assert {row.get("row_sha256") for row in blocked}.isdisjoint(accepted_sources)
    assert {row.get("record_id") for row in blocked}.isdisjoint({row["record_id"] for row in sidecar})
    assert {row.get("duplicate_denominator_key") for row in countable_blocked}.isdisjoint(accepted_denoms)
    assert {row.get("duplicate_group_id") for row in countable_blocked}.isdisjoint(accepted_groups)
    assert all(builder.recompute_source_row_hash(source_by_hash[source_hash]) == source_hash for source_hash in accepted_sources)
    assert all(builder.recompute_sidecar_hash(row) == row["sidecar_row_sha256"] for row in sidecar)


def test_ordered_tick_scoring_matches_frozen_result_summary():
    builder = load_builder()
    artifacts, rows, _prompt = builder.build_bundle()
    summary = artifacts["OTI8_CNR061_RESULT_LEDGER_2026-05-08"]["result_summary"]

    assert len(rows) == 8
    assert summary["row_level_all_eight_summary"]["target_before_stop_count"] == 2
    assert summary["row_level_all_eight_summary"]["no_terminal_count"] == 6
    assert summary["row_level_all_eight_summary"]["stop_before_target_count"] == 0
    assert summary["countable_duplicate_policy_summary"]["row_count"] == 4
    assert summary["countable_duplicate_policy_summary"]["target_before_stop_count"] == 2
    assert summary["countable_duplicate_policy_summary"]["no_terminal_count"] == 2

    first = next(row for row in rows if row["sidecar_row_sha256"].startswith("95480e42"))
    assert first["terminal_status"] == "TARGET_REACHED_BEFORE_STOP"
    assert first["score"]["terminal_event_utc"] == "2026-05-04T07:24:03.832000Z"
    assert first["score"]["terminal_price_side"] == "ask"
    assert first["score"]["synthetic_r"] == 0.054478301

    unresolved = next(row for row in rows if row["sidecar_row_sha256"].startswith("4e763958"))
    assert unresolved["terminal_status"] == "NO_TERMINAL_WITHIN_ORDERED_HORIZON"
    assert unresolved["score"]["max_favorable_r_within_horizon"] == 0.1668211307
    assert unresolved["score"]["synthetic_r"] is None


def test_generated_artifacts_preserve_quarantine_boundaries():
    json_files = sorted(BASE.glob(f"OTI8_CNR061_*_{DATE}.json"))
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


def test_source_no_leak_duplicate_label_artifacts_are_explicit():
    source = load_json(f"OTI8_CNR061_SOURCE_HASH_COVERAGE_REPORT_{DATE}.json")
    audit = load_json(f"OTI8_CNR061_NOLEAK_DUPLICATE_LABEL_AUDIT_{DATE}.json")

    assert source["source_hash_status"] == "PASS"
    assert source["all_required_sources_present"] is True
    assert source["all_source_hash_recomputes_match"] is True
    assert source["hash_failures"] == []
    assert source["prompt_named_missing_or_stale_artifacts"][0]["exists"] is False

    assert audit["no_leak_status"] == "PASS"
    assert audit["forbidden_input_key_hits"] == []
    assert audit["blocked_exclusion"]["accepted_rows"] == 8
    assert audit["blocked_exclusion"]["blocked_rows"] == 94
    assert audit["blocked_exclusion"]["countable_overlap"]["duplicate_denominator_key_overlap"] == []
    assert audit["blocked_exclusion"]["countable_overlap"]["duplicate_group_id_overlap"] == []
    assert audit["label_family_separation"]["broker_actual_r_opened"] is False
    assert audit["label_family_separation"]["hidden_path_labels_opened"] is False


def test_methodology_forensics_and_completion_cover_required_outputs():
    methodology = load_json(f"OTI8_CNR061_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_{DATE}.json")
    forensics = load_json(f"OTI8_CNR061_RESULT_FORENSICS_AND_LEARNING_LEDGER_{DATE}.json")
    completion = load_json(f"OTI8_CNR061_COMPLETION_AUDIT_{DATE}.json")
    rows = load_jsonl(f"OTI8_CNR061_RESULT_LEDGER_{DATE}_ROWS.jsonl")

    assert methodology["statistical_verdict"] == "NOT_VALIDATION_NOT_PROMOTION_DSR_PBO_NOT_COMPUTABLE"
    assert methodology["dsr"]["status"] == "not_computable"
    assert methodology["pbo"]["status"] == "not_computable"
    assert methodology["effective_n"]["duplicate_groups"] == 2
    assert methodology["sample_floor"]["sample_floor_pass"] is False

    assert len(forensics["failure_anatomy"]["target_reached_rows"]) == 2
    assert len(forensics["failure_anatomy"]["unresolved_rows"]) == 6
    assert forensics["status"] == "NEGATIVE_OR_TINY_N_LEARNING_RECORDED_NO_RESCUE"

    checklist = {row["requirement"]: row for row in completion["prompt_to_artifact_checklist"]}
    for requirement in [
        "mandatory_gtos_preflight",
        "context_anchor_before_scoring",
        "controlling_inputs_read",
        "method_freeze_before_label_review",
        "exact_8_accepted_rows",
        "exact_94_blocked_rows_excluded",
        "source_hash_recompute",
        "no_leak_forbidden_key_scan",
        "label_family_separation",
        "duplicate_denominator_audit",
        "row_level_and_countable_results",
        "methodology_report",
        "failure_forensics",
        "next_lane_prompt",
        "no_live_surface_changes",
    ]:
        assert checklist[requirement]["status"].startswith("PASS"), requirement
    assert len(rows) == 8


def test_generated_rows_do_not_claim_validation_or_live_effect():
    for row in load_jsonl(f"OTI8_CNR061_RESULT_LEDGER_{DATE}_ROWS.jsonl"):
        assert row["promotion_verdict"] == PROMOTION_VERDICT
        assert row["validation_safe"] is False
        assert row["outcome_review_opened"] is False
        assert row["live_effect"] is False
        assert row["broker_actual_r_accessed"] is False
        assert row["account_history_accessed"] is False
        assert row["live_trade_results_accessed"] is False
        for key, value in walk(row):
            if key in {"validation_safe", "outcome_review_opened", "live_effect"}:
                assert value is False
            assert key not in {"broker_actual_r", "account_history", "live_trade_result", "hidden_path_label", "path_label"}
