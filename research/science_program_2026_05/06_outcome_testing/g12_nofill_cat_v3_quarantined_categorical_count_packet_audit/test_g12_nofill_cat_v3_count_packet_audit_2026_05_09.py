#!/usr/bin/env python3
"""Focused tests for the G12 NOFILL CAT V3 count-packet audit."""

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


def test_independent_recomputation_accepts_exact_universe_and_denominators():
    builder = load_module("build_g12_nofill_cat_v3_count_packet_audit_2026_05_09.py")
    analysis = builder.analyze()

    assert analysis["universe_total"] == 298
    assert analysis["universe_counts"] == {
        "accepted": 225,
        "blocked": 0,
        "reject": 65,
        "source_control": 4,
        "source_impossible": 4,
    }
    assert len(analysis["accepted_rows"]) == 225
    assert analysis["accepted_unique_keys"] == 182
    assert analysis["accepted_unique_groups"] == 139
    assert analysis["source_control_rows"] == [
        "NOFILL-CAT-ROW-0049",
        "NOFILL-CAT-ROW-0050",
        "NOFILL-CAT-ROW-0051",
        "NOFILL-CAT-ROW-0241",
    ]
    assert analysis["source_impossible_rows"] == [
        "NOFILL-CAT-ROW-0130",
        "NOFILL-CAT-ROW-0143",
        "NOFILL-CAT-ROW-0165",
        "NOFILL-CAT-ROW-0178",
    ]
    assert analysis["accepted_ids_match_contract"] is True
    assert analysis["exclusion_ids_match_contract"] is True


def test_reject_overlap_has_zero_denominator_effect():
    builder = load_module("build_g12_nofill_cat_v3_count_packet_audit_2026_05_09.py")
    analysis = builder.analyze()

    assert len(analysis["reject_key_overlap"]) == 47
    assert len(analysis["reject_group_overlap"]) == 47
    assert analysis["source_control_key_overlap"] == []
    assert analysis["source_impossible_key_overlap"] == []
    assert analysis["exclusion_denominator_violations"] == []


def test_duplicate_conflicts_and_label_families_are_clean():
    builder = load_module("build_g12_nofill_cat_v3_count_packet_audit_2026_05_09.py")
    analysis = builder.analyze()

    assert analysis["label_conflicts"] == []
    assert analysis["geometry_conflicts"] == []
    assert analysis["ordering_blockers"] == []
    assert analysis["denominator_conflicts"] == []
    assert analysis["group_denominator_conflicts"] == []
    assert analysis["row_label_counts"] == builder.EXPECTED_LABEL_COUNTS_ROW_LEVEL
    assert analysis["duplicate_key_label_counts"] == builder.EXPECTED_LABEL_COUNTS_DUPLICATE_KEY
    assert analysis["duplicate_group_label_counts"] == builder.EXPECTED_LABEL_COUNTS_DUPLICATE_GROUP


def test_source_hash_and_no_leak_checks_are_clean():
    builder = load_module("build_g12_nofill_cat_v3_count_packet_audit_2026_05_09.py")
    analysis = builder.analyze()

    assert analysis["source_recheck"]["strict_failure_count"] == 0
    assert analysis["source_recheck"]["missing_record_count"] == 0
    assert analysis["count_lane_hash_check"]["mismatch_count"] == 0
    assert analysis["count_lane_hash_check"]["missing_count"] == 0
    assert analysis["forbidden_key_hits"] == []
    assert analysis["accepted_flag_issues"] == []
    assert analysis["exclusion_flag_issues"] == []


def test_verifier_objective_coverage_is_accepting():
    builder = load_module("build_g12_nofill_cat_v3_count_packet_audit_2026_05_09.py")
    verifier = load_module("verify_g12_nofill_cat_v3_count_packet_audit_2026_05_09.py")
    payloads = builder.build_payloads()

    assert payloads[f"G12_NOFILL_CAT_V3_COUNT_AUDIT_DECISION_LEDGER_{DATE}.json"]["overall_decision"] == (
        "ACCEPT_AS_QUARANTINED_CATEGORICAL_COUNT_CONTROL_EVIDENCE"
    )
    coverage = verifier.objective_coverage(payloads)
    assert coverage == {"status": "PASS", "issues": []}
