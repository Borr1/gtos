import importlib.util
import json
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent
BUILDER_PATH = BASE / "build_cnr_next_model_control_pack_2026_05_08.py"
DATE = "2026-05-08"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


def load_builder():
    spec = importlib.util.spec_from_file_location("cnr_next_model_builder", BUILDER_PATH)
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


def test_preregistration_contracts_cover_required_families():
    builder = load_builder()
    timing = builder.timing_preregistration()
    targets = builder.target_preregistration()

    assert set(timing["families"]) == {
        "CNR_E2_SIGNAL_EMITTED_AT_SOURCE",
        "CNR_E3_DECISION_LATENCY_AWARE",
        "CNR_E4_PRETOUCH_TRIGGER",
    }
    assert set(targets["families"]) == {
        "CNR_T1_FIXED_R_FROM_EXECUTABLE_QUOTE",
        "CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL",
        "CNR_T3_TERMINAL_TIMEBOX_OR_LIFECYCLE",
    }
    for payload in (timing, targets):
        assert payload["promotion_verdict"] == PROMOTION_VERDICT
        assert payload["validation_safe"] is False
        assert payload["outcome_review_opened"] is False
        assert payload["live_effect"] is False
        assert payload["no_outcomes_scored"] is True


def test_lifecycle_packet_exact_six_rows_and_no_r_scoring():
    builder = load_builder()
    contract = builder.lifecycle_label_contract()
    packet, rows = builder.build_lifecycle_packet(contract)
    oti8_no_terminal_hashes = {
        row["sidecar_row_sha256"]
        for row in builder.load_oti8_rows()
        if row.get("terminal_status") == "NO_TERMINAL_WITHIN_ORDERED_HORIZON"
    }
    allowed = set(contract["allowed_labels"])

    assert packet["status"] == "SOURCE_SAFE_LIFECYCLE_PACKET_BUILT_NO_R_SCORING"
    assert len(rows) == 6
    assert {row["sidecar_row_sha256"] for row in rows} == oti8_no_terminal_hashes
    assert {row["lifecycle_label"] for row in rows}.issubset(allowed)
    assert packet["r_scoring_performed"] is False
    assert packet["blocked_94_rows_scored"] is False
    for row in rows:
        assert row["promotion_verdict"] == PROMOTION_VERDICT
        assert row["validation_safe"] is False
        assert row["outcome_review_opened"] is False
        assert row["live_effect"] is False
        for key, _value in walk(row):
            assert key != "synthetic_r"
            assert not key.endswith("_r"), key
            assert key not in {"broker_actual_r", "account_history", "live_trade_result", "live_order_state", "hidden_path_label", "path_label"}


def test_forensics_is_discovery_only_and_uses_existing_bins():
    builder = load_builder()
    contract = builder.lifecycle_label_contract()
    _packet, rows = builder.build_lifecycle_packet(contract)
    forensics = builder.xagusd_forensics(rows)

    assert forensics["status"] == "DISCOVERY_ONLY_MECHANISM_FORENSICS_NO_RESCUE_NO_GATE"
    assert forensics["promotion_verdict"] == PROMOTION_VERDICT
    assert forensics["validation_safe"] is False
    assert forensics["outcome_review_opened"] is False
    assert forensics["live_effect"] is False
    assert "no new thresholds selected" in forensics["bin_source"]
    assert forensics["oti8_xagusd_summary"]["row_count"] == 8
    assert forensics["oti8_no_terminal_cluster"]["row_count"] == 6
    assert forensics["oti7_xagusd_summary"]["row_count"] > 0


def test_generated_artifacts_parse_and_preserve_boundaries():
    json_files = sorted(BASE.glob(f"CNR_*_{DATE}.json"))
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
        assert payload["live_order_state_accessed"] is False, path.name
        assert payload["paid_data_calls"] == 0, path.name
        assert payload["api_calls"] == 0, path.name
        assert payload["databento_calls"] == 0, path.name
        assert payload["mt5_order_calls"] == 0, path.name
        assert payload["mt5_account_calls"] == 0, path.name


def test_audit_and_completion_cover_prompt_requirements():
    audit = load_json(f"CNR_TIMING_TARGET_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}.json")
    completion = load_json(f"CNR_NEXT_MODEL_COMPLETION_AUDIT_{DATE}.json")
    rows = load_jsonl(f"CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET_{DATE}_ROWS.jsonl")

    assert audit["no_leak_scan"]["status"] == "PASS"
    assert audit["exact_six_row_scope_check"]["status"] == "PASS_EXACT_SIX"
    assert audit["blocked_94_not_scored_proof"]["status"] == "PASS_94_BLOCKED_ROWS_NOT_SCORED"
    assert audit["sample_floor"]["sample_floor_for_validation_met"] is False
    assert len(rows) == 6

    checklist = {item["requirement"]: item for item in completion["prompt_to_artifact_checklist"]}
    required = [
        "mandatory_gtos_preflight",
        "latest_handoff_read",
        "g12_oti8_next_lane_prompt_pack_read",
        "all_named_context_dirs_inventoried",
        "context_anchor",
        "CNR_E2_E3_E4_prereg",
        "CNR_T1_T2_T3_prereg",
        "source_contracts",
        "no_leak_duplicate_samplefloor",
        "six_row_no_terminal_scope",
        "lifecycle_packet_without_r_scoring",
        "xagusd_residual_forensics_discovery_only",
        "94_blocked_rows_not_scored",
        "no_broker_account_live_labels",
        "no_paid_api_databento_mt5_order_account_calls",
    ]
    for requirement in required:
        assert checklist[requirement]["status"].startswith("PASS"), requirement


def test_source_contract_inventory_includes_required_and_otr_context_dirs():
    contracts = load_json(f"CNR_TIMING_TARGET_SOURCE_CONTRACTS_{DATE}.json")
    directories = {entry["required_directory"] for entry in contracts["source_artifact_inventory"]}
    assert "g12_oti8_cnr061_post_result_audit" in directories
    assert "oti8_cnr061_quarantined_results" in directories
    assert "cnr061_geometry_horizon_sidecar" in directories
    assert "g12_oti5_otr061_post_audit" in directories
    assert "oti6_otr061_cnr_quarantined_results" in directories
    assert "otr061_xau_tick_recovery" in directories
    assert any(entry["parse_status"].startswith("PASS_") for entry in contracts["source_artifact_inventory"])
