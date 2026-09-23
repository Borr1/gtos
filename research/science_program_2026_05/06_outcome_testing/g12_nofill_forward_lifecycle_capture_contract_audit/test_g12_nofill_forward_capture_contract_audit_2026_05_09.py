#!/usr/bin/env python3
"""Focused tests for the G12 NOFILL forward lifecycle capture contract audit."""

from __future__ import annotations

import importlib.util
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
DATE = "2026-05-09"


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, OUT_DIR / name)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_evidence_chain_recomputes_frozen_counts_and_denominators() -> None:
    builder = load_module("build_g12_nofill_forward_capture_contract_audit_2026_05_09.py")
    duplicate = builder.analyze_evidence_chain()

    assert duplicate["status"] == "PASS"
    assert duplicate["universe_equation"]["total"] == 298
    assert duplicate["universe_equation"]["terminal_counts"] == {
        "accepted": 225,
        "blocked": 0,
        "reject": 65,
        "source_control": 4,
        "source_impossible": 4,
    }
    assert duplicate["denominators"]["row_level_accepted"] == 225
    assert duplicate["denominators"]["unique_nofill_duplicate_key"] == 182
    assert duplicate["denominators"]["unique_duplicate_group_id"] == 139
    assert duplicate["mandatory_exclusions"]["source_control_rows"] == builder.SOURCE_CONTROL_ROWS
    assert duplicate["mandatory_exclusions"]["source_impossible_rows"] == builder.SOURCE_IMPOSSIBLE_ROWS
    assert duplicate["reject_overlap"]["reject_key_overlap_count"] == 47
    assert duplicate["reject_overlap"]["denominator_delta_after_accepted_first_filter"] == {
        "duplicate_group": 0,
        "duplicate_key": 0,
        "row_level": 0,
    }


def test_schema_audit_accepts_with_exact_blockers_not_promotion() -> None:
    builder = load_module("build_g12_nofill_forward_capture_contract_audit_2026_05_09.py")
    schema = builder.analyze_forward_schema()

    assert schema["promotion_verdict"] == builder.PROMOTION_VERDICT
    assert schema["validation_safe"] is False
    assert schema["outcome_review_opened"] is False
    assert schema["live_effect"] is False
    assert schema["status"] == "PASS_WITH_EXACT_CONTRACT_BLOCKERS"
    assert schema["field_count"] == 80
    assert schema["family_count"] == 12
    assert schema["coverage_assessment"]["source_asof_timestamp_fields"] == "PASS"
    assert schema["coverage_assessment"]["duplicate_denominator_controls"] == "PASS"
    assert schema["coverage_assessment"]["capture_latency"] == "PARTIAL_WITH_BLOCKER"
    assert schema["coverage_assessment"]["cost_spread_slippage_execution_observability"] == "PARTIAL_WITH_BLOCKER"
    assert len(schema["exact_contract_blockers"]) == 3


def test_no_leak_source_audit_rejects_raw_log_consumption() -> None:
    builder = load_module("build_g12_nofill_forward_capture_contract_audit_2026_05_09.py")
    noleak = builder.analyze_no_leak_source()

    assert noleak["promotion_verdict"] == builder.PROMOTION_VERDICT
    assert noleak["validation_safe"] is False
    assert noleak["outcome_review_opened"] is False
    assert noleak["live_effect"] is False
    assert noleak["status"] == "PASS_WITH_RAW_SOURCE_PROJECTION_REQUIRED"
    assert noleak["artifact_flag_issues"] == []
    assert noleak["raw_log_hazards_requiring_allowlist_projection"]
    assert noleak["source_code_hazards_requiring_allowlist_projection"]
    assert noleak["local_heavy_data_search"]["searched_roots"]


def test_decision_payload_is_accept_with_exact_blockers() -> None:
    builder = load_module("build_g12_nofill_forward_capture_contract_audit_2026_05_09.py")
    duplicate = builder.analyze_evidence_chain()
    schema = builder.analyze_forward_schema()
    noleak = builder.analyze_no_leak_source()
    decision = builder.decision_payload(schema=schema, noleak=noleak, duplicate=duplicate)

    assert decision["terminal_g12_verdict"] == "ACCEPT_WITH_EXACT_CONTRACT_BLOCKERS"
    assert decision["decision_status"] == "PASS_ACCEPTED_WITH_BLOCKERS"
    assert decision["blocking_failures"] == []
    assert len(decision["accepted_contract_claims"]) >= 5
    assert len(decision["exact_contract_blockers"]) == 3
    assert "result scoring" in decision["forbidden_future_routes"]


def test_verifier_objective_coverage_passes_on_builder_payloads() -> None:
    builder = load_module("build_g12_nofill_forward_capture_contract_audit_2026_05_09.py")
    verifier = load_module("verify_g12_nofill_forward_capture_contract_audit_2026_05_09.py")
    payloads = builder.build_payloads()

    coverage = verifier.objective_coverage(payloads)
    assert coverage == {"status": "PASS", "issues": []}
