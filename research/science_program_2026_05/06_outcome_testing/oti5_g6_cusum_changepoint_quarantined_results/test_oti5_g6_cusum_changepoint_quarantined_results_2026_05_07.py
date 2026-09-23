import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


BASE = Path(__file__).resolve().parent
BUILDER_PATH = BASE / "build_oti5_g6_cusum_changepoint_quarantined_results_2026_05_07.py"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


def load(name: str):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def load_builder():
    spec = importlib.util.spec_from_file_location("oti5_g6_cusum_builder", BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def walk_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key
            yield from walk_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from walk_keys(item)


def test_terminal_scoring_fixture_long_short_and_ambiguity():
    builder = load_builder()
    ts = datetime(2026, 5, 7, tzinfo=timezone.utc)
    long_rows = [
        {"ts_utc": ts, "bid": 99.9, "ask": 100.0},
        {"ts_utc": ts, "bid": 102.0, "ask": 102.1},
    ]
    long_result = builder.score_terminal_ticks(long_rows, side="LONG", entry=100.0, stop=99.0, tp1=102.0, reward_r=1.5)
    assert long_result["result_status"] == "ENTRY_TOUCHED_THEN_TP1"
    assert long_result["synthetic_r"] == 1.5

    short_rows = [
        {"ts_utc": ts, "bid": 101.0, "ask": 101.1},
        {"ts_utc": ts, "bid": 102.9, "ask": 103.0},
    ]
    short_result = builder.score_terminal_ticks(short_rows, side="SHORT", entry=101.0, stop=103.0, tp1=98.0, reward_r=1.5)
    assert short_result["result_status"] == "ENTRY_TOUCHED_THEN_SL"
    assert short_result["synthetic_r"] == -1.0

    ambiguous_rows = [{"ts_utc": ts, "bid": 102.0, "ask": 98.0}]
    ambiguous = builder.score_terminal_ticks(ambiguous_rows, side="LONG", entry=100.0, stop=103.0, tp1=102.0, reward_r=1.5)
    assert ambiguous["result_status"] == "AMBIGUOUS_TP_AND_SL_SAME_TICK"
    assert ambiguous["synthetic_r"] is None


def test_generated_json_artifacts_parse_and_preserve_quarantine_flags():
    json_files = sorted(BASE.glob("OTI5_G6_CUSUM_*2026-05-07.json"))
    assert json_files
    for path in json_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["promotion_verdict"] == PROMOTION_VERDICT, path.name
        assert payload["validation_safe"] is False, path.name
        assert payload["outcome_review_opened"] is False, path.name
        assert payload["live_effect"] is False, path.name


def test_frozen_subset_and_duplicate_denominator_are_enforced():
    duplicate = load("OTI5_G6_CUSUM_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.json")
    assert duplicate["raw_total_packet_rows"] == 86
    assert duplicate["raw_source_ready_rows"] == 81
    assert duplicate["unique_duplicate_group_count"] == 17
    assert duplicate["nonprimary_duplicate_rows"] == 64
    assert duplicate["denominator_policy_verdict"] == "PASS_DUPLICATE_DENOMINATOR_FROZEN_BEFORE_SCORING"
    assert duplicate["excluded_record_ids"] == [
        "OTG0-PKT-063|NAS100_2026-05-03T16:15:00+00:00",
        "OTG0-PKT-063|XAUUSD_2026-05-03T16:15:00+00:00",
        "OTG0-PKT-063|XAUUSD_2026-05-03T16:30:00+00:00",
        "OTG0-PKT-063|XAUUSD_2026-05-06T07:15:00+00:00",
        "OTG0-PKT-063|XAUUSD_2026-05-06T08:00:00+00:00",
    ]


def test_source_and_label_gates_pass_before_scoring():
    source = load("OTI5_G6_CUSUM_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json")
    label = load("OTI5_G6_CUSUM_LABEL_FAMILY_NOLEAK_REPORT_2026-05-07.json")

    assert source["local_heavy_data_inventory_enforced"] is True
    assert source["local_inventory_search_report"]["absolute_tick_root_exists"] is True
    assert source["source_gate_pass"] is True
    assert source["material_source_hash_failure_count"] == 0
    assert source["feature_asof_failures"] == []
    assert source["tick_files_rehashed"]

    assert label["label_family_gate_pass"] is True
    assert label["forbidden_input_key_hit_count"] == 0
    assert label["forbidden_source_path_hits"] == []
    assert label["broker_actual_r_opened"] is False
    assert label["live_trade_results_opened"] is False


def test_result_ledger_is_quarantined_discovery_only_with_expected_metrics():
    result = load("OTI5_G6_CUSUM_RESULT_LEDGER_2026-05-07.json")
    assert result["packet_id"] == "OTG0-PKT-063"
    assert result["result_status"] == "RESULT_QUARANTINED_DISCOVERY_ONLY"
    assert result["raw_source_ready_rows"] == 81
    assert result["unique_duplicate_group_count"] == 17
    assert result["scoring_gate_status"] == "PASS_SOURCE_NOLEAK_DUPLICATE_LABEL_CHECKS_BEFORE_SCORING"

    primary = result["primary_countable_summary"]
    assert primary["record_count"] == 17
    assert primary["resolved_synthetic_r_rows"] == 9
    assert primary["terminal_status_counts"] == {
        "ENTRY_TOUCHED_THEN_SL": 8,
        "ENTRY_TOUCHED_THEN_TP1": 1,
        "NO_ENTRY_TOUCH_NO_R_SCORED": 8,
    }
    assert primary["mean_synthetic_r_resolved_only"] == -0.72222222
    assert primary["failure_rate_resolved_terminal"] == 0.88888889

    rows = result["rows"]
    assert len(rows) == 81
    assert sum(1 for row in rows if row["duplicate_role"] == "COUNTABLE_PRIMARY_UNIQUE_DUPLICATE_GROUP") == 17
    for row in rows:
        assert row["result_source"] == "external_tick_parquet_recomputed_no_hidden_path_labels_no_broker_actual_r"
        keys = {str(key).lower() for key in walk_keys(row)}
        assert "broker_actual_r" not in keys
        assert "actual_r" not in keys
        assert "win_loss" not in keys


def test_dsr_pbo_effective_n_are_not_validation_computable():
    methodology = load("OTI5_G6_CUSUM_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-07.json")
    assert methodology["countable_primary_unique_duplicate_groups"] == 17
    assert methodology["dsr"]["status"] == "not_computable"
    assert methodology["pbo"]["status"] == "not_computable"
    assert methodology["effective_n"]["status"] == "not_computable_for_validation"
    assert methodology["statistical_verdict"] == "NOT_VALIDATION_NOT_COMPUTABLE_BELOW_SAMPLE_FLOOR"
    assert methodology["sample_floor_review"]["broker_actual_r_opened"] is False


def test_completion_audit_maps_required_prompt_items():
    completion = load("OTI5_G6_CUSUM_COMPLETION_AUDIT_2026-05-07.json")
    assert completion["can_mark_goal_complete"] is True
    checklist = {row["requirement"]: row for row in completion["prompt_to_artifact_checklist"]}
    for requirement in [
        "mandatory_preflight_live_state",
        "latest_numbered_handoff_read",
        "quick_reference_read",
        "research_doctrine_read",
        "research_current_state_read",
        "goal_session_discipline_read",
        "local_heavy_data_inventory_enforced",
        "g12_otx_controls_read",
        "frozen_81_row_subset_verified",
        "five_listed_rows_excluded",
        "source_hash_gate",
        "duplicate_denominator_frozen_before_scoring",
        "label_family_noleak_gate",
        "quarantined_result_or_impossibility_written",
        "dsr_pbo_effective_n_reported",
        "no_promotion_flags_preserved",
    ]:
        assert checklist[requirement]["status"] == "PASS", requirement
