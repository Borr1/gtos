#!/usr/bin/env python3
"""Focused tests for the G12 HAZ-005 transition-clock source-repair audit."""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROUTE_DIR))

import verify_g12_haz005_transition_clock_repair_audit_2026_05_15 as verifier  # noqa: E402


@lru_cache(maxsize=1)
def verification_result():
    return verifier.verify(write_result=False)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_g12_verifier_accepts_current_artifacts():
    ok, result = verification_result()
    assert ok, result["failures"]
    assert all(check["ok"] for check in result["checks"])
    assert result["closeout_readiness"]["validation_safe"] is False
    assert result["closeout_readiness"]["outcome_review_opened"] is False
    assert result["closeout_readiness"]["live_effect"] is False


def test_repair_recomputation_preserves_full_790_row_split():
    rows = read_jsonl(ROUTE_DIR / "G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_SOURCE_REPAIR_RECOMPUTATION_LEDGER_2026-05-15.jsonl")
    assert len(rows) == 790
    assert sum(row["g12_acceptance_status"] == "ACCEPT_SOURCE_REPAIR_CANDIDATE_AS_G12_CONTROL_EVIDENCE_ONLY" for row in rows) == 5
    assert sum(row["g12_acceptance_status"] == "BOUNDED_NOT_REPAIRABLE_FROM_SEARCHED_SOURCES" for row in rows) == 785
    assert not [row for row in rows if row["g12_acceptance_status"] == "G12_REPAIR_RECOMPUTATION_MISMATCH"]


def test_decision_accepts_only_source_control_not_validation_or_live():
    decision = read_json(ROUTE_DIR / "G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_DECISION_LEDGER_2026-05-15.json")
    assert decision["terminal_decision"] == "ACCEPT_AS_G12_READY8_HAZ005_TRANSITION_CLOCK_SOURCE_REPAIR_AUDIT_NO_PROMOTION"
    assert decision["summary"]["same_g12_repairable_remaining"] == 0
    assert decision["summary"]["accepted_source_repair_candidate_rows"] == 5
    assert decision["summary"]["bounded_not_repairable_rows"] == 785
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False
    assert "not validation" in decision["accepted_downstream_use_boundary"]


def test_discrepancy_repair_and_saturation_close_same_g12_issues():
    discrepancies = read_jsonl(ROUTE_DIR / "G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_DISCREPANCY_REPAIR_LEDGER_2026-05-15.jsonl")
    assert discrepancies
    assert all(row["remaining_same_g12_issue"] is False for row in discrepancies)
    assert "G12_HAZ005_STALE_NEXT_G12_STARTER_MANIFEST_HASH" in {row["issue_id"] for row in discrepancies}
    saturation = read_json(ROUTE_DIR / "G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_SATURATION_SELF_RED_TEAM_2026-05-15.json")
    assert saturation["remaining_same_g12_repairable_issues"] == 0
    assert saturation["remaining_same_evidence_class_intelligence"] == 0
    assert saturation["no_arbitrary_top_n_policy_observed"] is True
