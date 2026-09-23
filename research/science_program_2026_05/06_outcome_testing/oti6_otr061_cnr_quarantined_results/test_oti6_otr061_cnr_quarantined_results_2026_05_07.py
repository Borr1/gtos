import importlib.util
import json
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent
BUILDER_PATH = BASE / "build_oti6_otr061_cnr_quarantined_results_2026_05_07.py"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TARGET_STATUS = "RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION"


def load_builder():
    spec = importlib.util.spec_from_file_location("oti6_cnr_builder", BUILDER_PATH)
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


def test_builder_recomputes_recovered_tick_hash_and_coverage():
    builder = load_builder()
    parquet = builder.inspect_parquet(builder.PARQUET_PATH)

    assert parquet["sha256"] == "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"
    assert parquet["sha256_matches_expected"] is True
    assert parquet["row_count"] == 89391
    assert parquet["first_tick_utc"] == "2026-05-06T07:10:01.820000Z"
    assert parquet["last_tick_utc"] == "2026-05-06T11:15:59.763000Z"
    assert parquet["decision_quote"]["quote_timestamp_utc"] == "2026-05-06T07:14:59.889000Z"
    assert parquet["decision_quote"]["bid"] == 4647.65
    assert parquet["decision_quote"]["ask"] == 4648.29
    assert parquet["ordered_path"]["row_count"] == 88060
    assert parquet["ordered_path"]["first_timestamp_utc"] == "2026-05-06T07:15:00.634000Z"
    assert parquet["ordered_path"]["last_timestamp_utc"] == "2026-05-06T11:14:59.900000Z"
    assert parquet["ordered_path"]["post_horizon_first_timestamp_utc"] == "2026-05-06T11:15:00.335000Z"


def test_cnr_e0_geometry_blocks_r_scoring_before_path_scoring():
    builder = load_builder()
    artifacts = builder.build_bundle()
    geometry = artifacts["OTI6_CNR_GEOMETRY_AND_ELIGIBILITY_AUDIT_2026-05-07"]
    result = artifacts["OTI6_CNR_RESULT_LEDGER_2026-05-07"]

    assert geometry["original_gtos_geometry"] == {
        "base_r_price": 14.17,
        "entry_price": 4561.52,
        "geometry_valid": True,
        "side": "LONG",
        "stop_loss": 4547.35,
        "take_profit_1": 4582.77,
    }
    assert geometry["decision_quote_reconstructed_from_parquet"]["executable_decision_price_long_ask"] == 4648.29
    assert geometry["target_already_passed_at_decision"] is True
    assert geometry["eligibility_status"]["terminal_result_status"] == TARGET_STATUS
    assert geometry["distance_diagnostics"]["executable_entry_minus_tp1_price"] == 65.52

    assert result["result_status"] == TARGET_STATUS
    assert result["r_scoring_attempted"] is False
    assert result["synthetic_path_r"] is None
    assert result["result_row"]["synthetic_path_r_status"] == "NOT_COMPUTED_PREREGISTERED_GEOMETRY_NOT_ELIGIBLE"


def test_generated_json_artifacts_preserve_quarantine_flags():
    json_files = sorted(BASE.glob("OTI6_CNR_*2026-05-07.json"))
    assert json_files
    for path in json_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["promotion_verdict"] == PROMOTION_VERDICT, path.name
        assert payload["validation_safe"] is False, path.name
        assert payload["outcome_review_opened"] is False, path.name
        assert payload["live_effect"] is False, path.name
        assert payload["broker_actual_r_accessed"] is False, path.name
        assert payload["account_history_accessed"] is False, path.name
        assert payload["live_order_state_accessed"] is False, path.name
        assert payload["paid_data_calls"] == 0, path.name
        assert payload["api_calls"] == 0, path.name
        assert payload["databento_calls"] == 0, path.name
        assert payload["mt5_order_calls"] == 0, path.name


def test_source_hash_and_label_gates_are_explicit():
    source = load_json("OTI6_CNR_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json")
    duplicate = load_json("OTI6_CNR_DUPLICATE_LABEL_NOLEAK_AUDIT_2026-05-07.json")

    assert source["source_gate_status"] == "PASS"
    assert source["all_consumed_files_hashed"] is True
    assert source["hash_failures"] == []
    assert source["parquet_direct_verification"]["sha256_matches_expected"] is True
    assert source["forbidden_source_review"]["broker_actual_r_accessed"] is False
    assert source["forbidden_source_review"]["blocked_packet_outcome_source_read"] is False

    assert duplicate["label_family_gate_status"] == "PASS"
    assert duplicate["duplicate_group_id"] == "G6_CNR|XAUUSD|2026-05-06|london|LONG|4561.52"
    assert duplicate["broker_actual_r_opened"] is False
    assert duplicate["blocked_packet_outcomes_opened"] is False
    assert duplicate["post_decision_context_not_used_for_cnr_e0_scoring"] is True


def test_methodology_and_forensics_are_non_promotion_not_validation():
    methodology = load_json("OTI6_CNR_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-07.json")
    forensics = load_json("OTI6_CNR_RESULT_OR_IMPOSSIBILITY_FORENSICS_2026-05-07.json")

    assert methodology["dsr"]["status"] == "not_computable"
    assert methodology["pbo"]["status"] == "not_computable"
    assert methodology["effective_n"]["status"] == "not_computable_for_validation"
    assert methodology["sample_floor_review"]["current_r_scored_records"] == 0
    assert methodology["sample_floor_review"]["sample_floor_pass"] is False

    assert forensics["terminal_status"] == TARGET_STATUS
    assert forensics["not_a_forced_win_loss"] is True
    assert forensics["evidence"]["target_already_passed_by_price"] == 65.52
    assert "alternate" not in " ".join(forensics["row_teaches"]).lower()


def test_completion_audit_covers_prompt_requirements():
    completion = load_json("OTI6_CNR_COMPLETION_AUDIT_2026-05-07.json")
    assert completion["can_mark_goal_complete"] is True
    checklist = {row["requirement"]: row for row in completion["prompt_to_artifact_checklist"]}
    for requirement in [
        "objective_terminal_status",
        "mandatory_live_state_regenerated_and_read",
        "all_controlling_inputs_read_and_hashed",
        "otr061_g12_claims_recomputed",
        "original_geometry_recovered_from_source_line",
        "cnr_e0_geometry_applied_before_r_scoring",
        "long_ask_already_beyond_original_tp1_verified",
        "result_or_impossibility_forensics_written",
        "no_promotion_flags_preserved",
        "no_forbidden_result_or_live_sources_read",
        "forbidden_live_surface_diff_absent_at_build",
        "dsr_pbo_effective_n_reported",
    ]:
        assert checklist[requirement]["status"] == "PASS", requirement


def test_no_generated_artifact_sets_forbidden_truthy_flags_or_broker_result_keys():
    forbidden_truthy = {"validation_safe", "outcome_review_opened", "live_effect"}
    broker_forbidden = {"broker_actual_r", "account_history", "live_trade_result", "win_loss"}
    for path in BASE.glob("OTI6_CNR_*2026-05-07.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for key, value in walk(payload):
            if key in forbidden_truthy:
                assert value is False
            assert key not in broker_forbidden or value in (False, None, 0, "not_computable")
