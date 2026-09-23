#!/usr/bin/env python3
"""Focused checks for the HAZ-005 route artifacts."""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROUTE_DIR))

import verify_haz005_transition_clock_split_and_source_repair_2026_05_15 as verifier  # noqa: E402


@lru_cache(maxsize=1)
def verification_result():
    return verifier.verify()


def read_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_verifier_accepts_current_artifacts():
    ok, result = verification_result()
    assert ok, result["failures"]
    assert all(check["ok"] for check in result["checks"])
    assert result["closeout_readiness"]["validation_safe"] is False
    assert result["closeout_readiness"]["outcome_review_opened"] is False
    assert result["closeout_readiness"]["live_effect"] is False


def test_repaired_packet_remains_g12_gated_candidate_evidence():
    rows = read_jsonl(ROUTE_DIR / "HAZ005_REPAIRED_DESCRIPTOR_ROW_PACKET_2026-05-15.jsonl")
    assert len(rows) == 5
    assert {row["repair_status"] for row in rows} == {"REPAIRED_FROM_LOCAL_SIERRA_CANDIDATE_REQUIRES_G12"}
    assert {row["source_admission_status"] for row in rows} == {"CANDIDATE_REPAIR_PACKET_REQUIRES_G12_SOURCE_AUDIT"}
    assert {row["validation_safe"] for row in rows} == {False}


def test_horizon_reversal_and_repair_sensitivity_are_preserved():
    sensitivity = json.loads((ROUTE_DIR / "HAZ005_SENSITIVITY_LEDGER_2026-05-15.json").read_text(encoding="utf-8"))
    assert sensitivity["original_role_counts"] == {
        "per_card_contrast_row": 1465,
        "per_card_fail_closed_row": 790,
        "per_card_pass_row": 759,
    }
    assert sensitivity["repaired_role_counts"] == {
        "per_card_contrast_row": 1470,
        "per_card_fail_closed_row": 785,
        "per_card_pass_row": 759,
    }
    assert sensitivity["reclassified_candidate_count"] == 5
    h1_h4 = [row for row in sensitivity["headline_pass_control_shift_rows"] if row["horizon_m15_bars"] in {1, 4}]
    h16 = [row for row in sensitivity["headline_pass_control_shift_rows"] if row["horizon_m15_bars"] == 16]
    assert h1_h4
    assert h16
    assert {row["repaired_classification"] for row in h1_h4} == {"POSITIVE_NEUTRAL_TARGET_MOVEMENT"}
    assert {row["repaired_classification"] for row in h16} == {"INVERSE_NEUTRAL_TARGET_MOVEMENT"}


def test_future_capture_contract_covers_all_remaining_sources():
    rows = read_jsonl(ROUTE_DIR / "HAZ005_EXACT_FUTURE_SOURCE_CAPTURE_FIELDS_2026-05-15.jsonl")
    assert len(rows) == 7
    assert {row["source_file_name"] for row in rows} == {
        "6BM26-CME.scid",
        "6EM26-CME.scid",
        "6JM26-CME.scid",
        "GCM26-COMEX.scid",
        "NQM26-CME.scid",
        "SIM26-COMEX.scid",
        "YMM26-CBOT.scid",
    }
    assert all(row["missing_prior16_bar_end_utc"] for row in rows)
    assert all(row["validation_safe"] is False for row in rows)


def test_instruction_coverage_ledger_closes_prompt_requirements():
    coverage = json.loads((ROUTE_DIR / "HAZ005_INSTRUCTION_COVERAGE_LEDGER_2026-05-15.json").read_text(encoding="utf-8"))
    rows = coverage["coverage_rows"]
    instructions = {row["instruction"] for row in rows}
    assert coverage["no_arbitrary_top_n_policy_observed"] is True
    assert coverage["same_evidence_class_exhaustion"]["remaining_same_class_repairable_blockers"] == 0
    assert all(row["status"] == "DONE" for row in rows)
    assert "mandatory preflight and active context use" in instructions
    assert "pursue fail-closed prior-16 repair through approved roots" in instructions
    assert "preserve safe boundaries" in instructions
