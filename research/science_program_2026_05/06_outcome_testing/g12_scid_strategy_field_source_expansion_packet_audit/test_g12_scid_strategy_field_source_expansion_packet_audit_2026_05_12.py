from __future__ import annotations

import importlib.util
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
BUILD_PATH = ROUTE_DIR / "build_g12_scid_strategy_field_source_expansion_packet_audit_2026_05_12.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("g12_scid_strategy_field_audit_builder_test", BUILD_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_row_coverage_and_denominator_recompute_accepts_3014_rows():
    builder = load_builder()
    audits, _ = builder.build_audits()
    row = audits["row_coverage"]
    assert row["row_coverage_ok"] is True
    assert row["candidate_input_rows"] == 3014
    assert row["descriptor_rows"] == 3014
    assert row["closure_rows"] == 3014
    assert row["unique_closure_candidate_ids"] == 3014
    assert row["unique_closure_duplicate_proxy_denominator_keys"] == 3014
    assert row["duplicate_key_mismatch_count"] == 0


def test_field_status_profile_hashes_and_closed_source_values_recompute_cleanly():
    builder = load_builder()
    audits, _ = builder.build_audits()
    field = audits["field_status"]
    assert field["field_status_audit_ok"] is True
    assert field["row_hash_mismatch_count"] == 0
    assert field["closed_source_value_mismatch_count"] == 0
    assert field["field_status_counts_by_field"]["canonical_candidate_and_denominator"] == {"CLOSED_FROM_SOURCE": 3014}
    assert field["field_status_counts_by_field"]["intended_side_direction"] == {"FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014}
    assert field["field_status_counts_by_field"]["lower_timeframe_asof_path_availability"] == {"PROSPECTIVE_CAPTURE_REQUIRED": 3014}
    assert field["field_status_counts_by_field"]["broker_account_order_history_deal_position_evidence"] == {"FORBIDDEN_IN_THIS_EVIDENCE_CLASS": 3014}


def test_fail_closed_prospective_and_forbidden_requirements_are_specific():
    builder = load_builder()
    audits, _ = builder.build_audits()
    fail = audits["fail_prospective_forbidden"]
    assert fail["fail_prospective_forbidden_audit_ok"] is True
    assert fail["fail_closed_value_issue_count"] == 0
    assert fail["forbidden_status_issue_count"] == 0
    assert fail["prospective_requirement_specificity_issue_count"] == 0
    assert fail["missing_requirement_families"] == []


def test_no_leak_surface_and_source_hash_binding_are_clean():
    builder = load_builder()
    audits, _ = builder.build_audits()
    noleak = audits["noleak_surface"]
    source_hash = audits["source_hash"]
    assert noleak["no_leak_surface_audit_ok"] is True
    assert noleak["closure_exact_forbidden_result_key_hit_count"] == 0
    assert noleak["closure_exact_forbidden_broker_key_hit_count"] == 0
    assert noleak["raw_market_blob_paths_in_builder_diff"] == []
    assert noleak["trading_surface_paths_in_builder_diff"] == []
    assert source_hash["source_hash_binding_ok"] is True


def test_decision_accepts_packet_and_emits_next_g0_prompt():
    builder = load_builder()
    audits, _ = builder.build_audits()
    assert audits["decision"]["terminal_decision"] == builder.TERMINAL_ACCEPT
    assert audits["decision"]["accepted_g12_packet_control_evidence_only"] is True
    builder.write_next_g0_prompt()
    prompt_text = builder.NEXT_G0_PROMPT.read_text(encoding="utf-8")
    assert "G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_ONLY" in prompt_text
    assert "NO_PROMOTION_VERDICT" in prompt_text
    assert "forward capture implementation" in prompt_text
