#!/usr/bin/env python3
"""Focused tests for the READY8 R7 expanded packet design."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-15"


def load_json(name: str):
    with (ROUTE_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(name: str):
    with (ROUTE_DIR / name).open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def test_prerequisites_and_safe_flags_are_closed():
    prerequisites = load_json(f"READY8_EXPANDED_PACKET_PREREQUISITE_ACCEPTANCE_INSPECTION_LEDGER_{DATE}.json")
    assert prerequisites["all_prerequisites_accepted"] is True
    assert prerequisites["prerequisite_count"] == 7
    for prerequisite in prerequisites["prerequisites"]:
        assert prerequisite["accepted"] is True
        flags = prerequisite["safe_flags_observed"]
        assert flags["promotion_verdict"] == "NO_PROMOTION_VERDICT"
        assert flags["validation_safe"] is False
        assert flags["outcome_review_opened"] is False
        assert flags["live_effect"] is False


def test_failure_intelligence_statuses_preserve_branch_information():
    rows = read_jsonl(f"READY8_EXPANDED_PACKET_BRANCH_CLASSIFICATION_LEDGER_{DATE}.jsonl")
    statuses = Counter(row["branch_status"] for row in rows)
    assert statuses["CONTROL_EXPLAINED_EDGE_CLAIM_KILLED_INTELLIGENCE_PRESERVED"] == 2608
    assert statuses["WEAKENED_BY_CONTROL_ENVELOPE_INTELLIGENCE_PRESERVED"] == 14
    assert statuses["EDGE_CLAIM_KILLED_INTELLIGENCE_PRESERVED"] > 0
    assert statuses["FAIL_CLOSED_REMAINS_EXCLUDED_WITH_CAPTURE_REQUIREMENT"] == 1
    for row in read_jsonl(f"READY8_EXPANDED_PACKET_KILLED_DEFERRED_MECHANISM_LEDGER_{DATE}.jsonl"):
        assert row["kill_scope"] == "unsupported_edge_claim_only_not_branch_intelligence"
        assert row["what_was_learned"]
        assert row["why_failed_or_weakened"]
        assert row["explaining_mechanism"]
        assert row["disposition"] in {"control-adjusted", "adjusted", "preserved", "split and preserved", "proven impossible inside current source set"}
        assert row["implication"] in {"control rule", "packet-design row", "future retest candidate", "avoid rule", "source-capture requirement"}


def test_packet_rowset_counts_are_all_material_not_rank_cutoff():
    rows = read_jsonl(f"READY8_EXPANDED_PACKET_ROWSET_DESIGN_{DATE}.jsonl")
    families = Counter(row["packet_family"] for row in rows)
    assert families["HAZ001_DECONCENTRATED_RETEST"] == 143
    assert families["UNC004_SOURCE_CONFIDENCE_DIAGNOSTIC"] == 1
    assert families["MAC_INVERSE_AVOID_FILTER_DESIGN"] == 32
    assert families["HAZ005_REPAIRED_DESCRIPTOR_SOURCE_CONTROL"] == 5
    assert families["CONTROL_RESIDUAL_FAILURE_INTELLIGENCE"] == 1
    assert len(rows) == 182
    coverage = load_json(f"READY8_EXPANDED_PACKET_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json")
    assert coverage["arbitrary_cutoff_used"] is False
    assert coverage["same_evidence_class_remaining"] == 0


def test_fail_closed_consumption_is_bounded():
    policy = load_json(f"READY8_EXPANDED_PACKET_FAIL_CLOSED_INCLUSION_EXCLUSION_POLICY_{DATE}.json")
    assert policy["accepted_repaired_target_rows_for_r7"] == 5320
    assert policy["remaining_fail_closed_target_rows"] == 25240
    assert policy["role_excluded_rows_unchanged"] == 5251
    repaired = read_jsonl(f"READY8_EXPANDED_PACKET_REPAIRED_TARGET_CONSUMPTION_LEDGER_{DATE}.jsonl")
    assert len(repaired) == 5320
    assert all(row["consumption_status"] == "R7_MAY_CONSUME_SOURCE_REPAIR_ONLY_NOT_VALIDATION" for row in repaired)


def test_completion_audit_has_no_missing_items():
    completion = load_json(f"READY8_EXPANDED_PACKET_COMPLETION_AUDIT_{DATE}.json")
    assert completion["criteria_status"]["all_prerequisites_accepted"] is True
    assert completion["criteria_status"]["failure_intelligence_doctrine_applied"] is True
    assert completion["criteria_status"]["arbitrary_cutoff_used"] is False
    assert completion["criteria_status"]["same_evidence_class_intelligence_remaining"] == 0
    assert completion["missing_or_incomplete_items"] == []
