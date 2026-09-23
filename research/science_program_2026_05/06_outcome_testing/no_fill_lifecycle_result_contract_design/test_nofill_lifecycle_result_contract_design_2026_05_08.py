from __future__ import annotations

import json
import os
import sys
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
if str(OUT_DIR) not in sys.path:
    sys.path.insert(0, str(OUT_DIR))

import build_nofill_lifecycle_result_contract_design_2026_05_08 as builder
import verify_nofill_lifecycle_result_contract_design_2026_05_08 as verifier


DATE_STAMP = "2026-05-08"


def load_json(name: str) -> dict:
    with (OUT_DIR / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def test_builder_freezes_corrected_source_packet_counts() -> None:
    builder.build_artifacts()
    universe = load_json(f"NOFILL_RESULT_CONTRACT_UNIVERSE_AND_EXCLUSION_LEDGER_{DATE_STAMP}.json")
    assert universe["source_packet"]["packet_rows"] == 298
    assert universe["source_packet"]["source_closed_rows"] == 298
    assert universe["source_packet"]["source_blocked_exact_rows"] == 0
    assert universe["exclusions"]["six_t3_rows"]["t3_row_count"] == 6
    assert universe["exclusions"]["blocked_94_cnr061"]["blocked_rows"] == 94
    assert universe["current_result_opening_status"]["result_rows_opened"] == 0
    assert universe["current_result_opening_status"]["r_or_performance_rows_scored"] == 0


def test_rulebook_preserves_safety_flags_and_row_0127_evidence() -> None:
    builder.build_artifacts()
    rulebook = load_json(f"NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE_STAMP}.json")
    assert rulebook["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert rulebook["validation_safe"] is False
    assert rulebook["outcome_review_opened"] is False
    assert rulebook["live_effect"] is False
    evidence = rulebook["starting_evidence_locked"]
    assert evidence["row_0127_source_sha256"] == builder.ROW_0127_EXPECTED_SHA256
    assert evidence["row_0127_first_terminal_area_touch_utc"] == builder.ROW_0127_FIRST_TOUCH
    assert evidence["g12_decision"] == "ACCEPT_CORRECTED_SOURCE_PACKET_AS_INPUT_ONLY_SOURCE_CLOSURE_EVIDENCE"


def test_side_aware_parser_and_pending_intent_fields_are_exact() -> None:
    builder.build_artifacts()
    parser = load_json(f"NOFILL_RESULT_CONTRACT_TOUCH_AND_PATH_PARSER_{DATE_STAMP}.json")
    fields = load_json(f"NOFILL_RESULT_CONTRACT_FIELD_SOURCE_REQUIREMENTS_{DATE_STAMP}.json")
    assert parser["side_rules"]["LONG"]["entry_touch"] == "ask <= entry_price"
    assert parser["side_rules"]["LONG"]["terminal_area_touch"] == "bid >= terminal_area_price"
    assert parser["side_rules"]["SHORT"]["entry_touch"] == "bid >= entry_price"
    assert parser["side_rules"]["SHORT"]["terminal_area_touch"] == "ask <= terminal_area_price"
    required_pending = set(fields["required_pending_intent_closure_fields"])
    assert "entry_touched_at_utc" in required_pending
    assert "filled_at_utc" in required_pending
    assert "cancelled_at_utc" in required_pending
    assert "expired_at_utc" in required_pending
    assert "frozen_horizon_end_utc" in required_pending


def test_label_family_separation_and_blockers_do_not_open_performance_lane() -> None:
    builder.build_artifacts()
    rulebook = load_json(f"NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE_STAMP}.json")
    blockers = load_json(f"NOFILL_RESULT_CONTRACT_BLOCKER_LEDGER_{DATE_STAMP}.json")
    noleak = load_json(f"NOFILL_RESULT_CONTRACT_NOLEAK_ASOF_SCHEMA_{DATE_STAMP}.json")
    assert rulebook["result_label_families"]["categorical_lifecycle_only"]["nofill_terminal_before_entry"]["r_performance_allowed"] is False
    assert "broker_actual_r" in noleak["forbidden_fields"]
    assert "BLOCK_RESULT_FORBIDDEN_FIELD" in blockers["result_contract_blocker_rules"]
    assert "BLOCK_RESULT_EXCLUDED_CNR061_BLOCKED_ROW" in blockers["result_contract_blocker_rules"]
    assert blockers["row_0127_status"]["blocked_now"] is False


def test_duplicate_sample_floor_blocks_validation_and_promotion() -> None:
    builder.build_artifacts()
    duplicate = load_json(f"NOFILL_RESULT_CONTRACT_DUPLICATE_SAMPLEFLOOR_POLICY_{DATE_STAMP}.json")
    assert duplicate["current_duplicate_state"]["nofill_duplicate_key_unique"] == 196
    assert duplicate["current_duplicate_state"]["duplicate_group_id_unique"] == 153
    assert duplicate["sample_floor_policy"]["current_design_lane"]["can_claim_validation"] is False
    assert duplicate["sample_floor_policy"]["future_result_validation"]["minimum_unique_nofill_duplicate_key_overall"] >= 100
    assert duplicate["sample_floor_policy"]["promotion"]["requires_separate_promotion_dossier"] is True


def test_verifier_passes_without_nested_pytest() -> None:
    builder.build_artifacts()
    os.environ["NOFILL_RESULT_CONTRACT_SKIP_NESTED_PYTEST"] = "1"
    results = verifier.verify_contract(run_pytest=False, write_audit=True)
    assert results["verification_status"]["status"] == "PASS"
    audit = load_json(f"NOFILL_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE_STAMP}.json")
    assert audit["can_mark_goal_complete"] is True
    assert audit["completion_status"] == "PASS_FROZEN_RESULT_CONTRACT_DESIGN"
