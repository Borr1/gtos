from __future__ import annotations

import json
import os
import sys
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
if str(OUT_DIR) not in sys.path:
    sys.path.insert(0, str(OUT_DIR))

import build_g12_nofill_result_contract_audit_2026_05_08 as builder
import verify_g12_nofill_result_contract_audit_2026_05_08 as verifier


DATE_STAMP = "2026-05-08"


def load_json(name: str) -> dict:
    with (OUT_DIR / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def test_builder_accepts_contract_and_preserves_starting_facts() -> None:
    builder.build_artifacts()
    decision = load_json(f"G12_NOFILL_RESULT_CONTRACT_DECISION_LEDGER_{DATE_STAMP}.json")
    facts = decision["starting_facts_verified"]
    assert decision["overall_decision"] == "ACCEPT_AS_FROZEN_RESULT_CONTRACT_FOR_FUTURE_CATEGORICAL_PACKET_AUDIT"
    assert facts["packet_rows"] == 298
    assert facts["source_closed"] == 298
    assert facts["source_blocked_exact"] == 0
    assert facts["row_0127_sha256"] == builder.EXPECTED_ROW_0127_SHA256
    assert facts["row_0127_first_terminal_area_touch"] == builder.EXPECTED_ROW_0127_FIRST_TOUCH
    assert facts["six_t3_excluded"] is True
    assert facts["blocked_94_cnr061_excluded"] is True


def test_source_noleak_audit_recomputes_row_0127_and_exclusions() -> None:
    builder.build_artifacts()
    source = load_json(f"G12_NOFILL_RESULT_CONTRACT_SOURCE_NOLEAK_AUDIT_{DATE_STAMP}.json")
    assert source["status"] == "PASS"
    assert source["row_0127_source_hash_recomputed"] == builder.EXPECTED_ROW_0127_SHA256
    assert source["row_0127_first_touch_recomputed"]["event"] == "terminal_area"
    assert source["row_0127_first_touch_recomputed"]["first_touch_utc"] == builder.EXPECTED_ROW_0127_FIRST_TOUCH
    assert source["forbidden_packet_field_hits"] == []
    assert source["blocked_cnr061_lane_rows_in_packet"] == []
    assert source["six_t3_overlap"] == []
    assert source["stop_after_original_horizon_hits"] == []


def test_rulebook_duplicate_and_blocker_gates_are_explicit() -> None:
    builder.build_artifacts()
    rulebook = load_json(f"G12_NOFILL_RESULT_CONTRACT_RULEBOOK_AUDIT_{DATE_STAMP}.json")
    duplicate = load_json(f"G12_NOFILL_RESULT_CONTRACT_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE_STAMP}.json")
    blockers = load_json(f"G12_NOFILL_RESULT_CONTRACT_BLOCKER_AND_GATE_LEDGER_{DATE_STAMP}.json")
    assert rulebook["status"] == "PASS"
    assert duplicate["status"] == "PASS"
    assert duplicate["recomputed_duplicate_state"]["nofill_duplicate_key_unique"] == 196
    assert duplicate["recomputed_duplicate_state"]["duplicate_group_id_unique"] == 153
    assert duplicate["frozen_policy"]["current_design_lane"]["can_claim_validation"] is False
    assert blockers["status"] == "PASS"
    assert blockers["contract_acceptance_blockers"] == []
    assert any("row-level eligibility" in gate for gate in blockers["exact_next_lane_gates"])
    assert any("R/performance" in gate for gate in blockers["exact_next_lane_gates"])


def test_verifier_passes_without_nested_pytest() -> None:
    builder.build_artifacts()
    os.environ["G12_NOFILL_RESULT_CONTRACT_SKIP_NESTED_PYTEST"] = "1"
    results = verifier.verify_audit(run_pytest=False, write_audit=True)
    assert results["verification_status"]["status"] == "PASS"
    audit = load_json(f"G12_NOFILL_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE_STAMP}.json")
    assert audit["completion_status"] == "PASS_G12_RESULT_CONTRACT_ACCEPTED"
    assert audit["can_mark_goal_complete"] is True
