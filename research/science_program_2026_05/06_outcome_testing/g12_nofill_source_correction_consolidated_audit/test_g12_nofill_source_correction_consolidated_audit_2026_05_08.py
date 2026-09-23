from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path


DATE = "2026-05-08"
OUT_DIR = Path(__file__).resolve().parent


def load_json(name: str) -> dict:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def test_universe_reconciles_298_and_prior_52() -> None:
    payload = load_json(f"G12_NOFILL_SOURCE_CORRECTION_UNIVERSE_RECONCILIATION_{DATE}.json")
    assert payload["source_universe"]["row_count"] == 298
    assert payload["source_universe"]["prior_accepted_categorical_rows"] == 52
    assert payload["source_universe"]["prior_blocked_rows"] == 246
    assert payload["router_reconciliation"]["router_matches_prior_blocked_packet_ids"] is True
    assert payload["router_reconciliation"]["router_overlap_with_prior_accepted"] == []
    assert payload["six_t3_overlap"] == []
    assert payload["blocked_cnr061_overlap"] == []


def test_final_accept_block_reject_counts_and_lane_breakdown() -> None:
    payload = load_json(f"G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_{DATE}.json")
    assert payload["row_count"] == 298
    assert payload["final_decision_counts"] == {
        "ACCEPT_PRIOR_CATEGORICAL_LABEL": 52,
        "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 173,
        "BLOCK_EXACT_SOURCE_OR_ORDERING_GAP": 8,
        "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26,
        "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39,
    }
    rows = payload["row_decisions"]
    assert len({row["packet_row_id"] for row in rows}) == 298
    assert sum(1 for row in rows if row["accepted_source_lane"] == "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2" and row["consolidated_decision"].startswith("ACCEPT")) == 29
    assert sum(1 for row in rows if row["accepted_source_lane"] == "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION" and row["consolidated_decision"] == "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED") == 26
    assert sum(1 for row in rows if row["accepted_source_lane"] == "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT" and row["consolidated_decision"] == "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE") == 39


def test_accepted_shortlist_and_blocker_ledger_are_exact() -> None:
    accepted = load_json(f"G12_NOFILL_SOURCE_CORRECTION_ACCEPTED_ROW_SHORTLIST_{DATE}.json")
    blockers = load_json(f"G12_NOFILL_SOURCE_CORRECTION_BLOCKER_LEDGER_{DATE}.json")
    assert accepted["accepted_row_count"] == 225
    assert blockers["blocked_row_count"] == 8
    assert blockers["blocker_code_counts"] == {
        "BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE": 4,
        "BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP": 1,
        "BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED": 1,
        "BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP": 3,
    }


def test_source_hash_noleak_and_red_team_checks() -> None:
    payload = load_json(f"G12_NOFILL_SOURCE_CORRECTION_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json")
    assert payload["status"] == "PASS"
    assert payload["missing_source_hash_records"] == []
    assert payload["source_hash_mismatches"] == []
    assert payload["forbidden_output_key_hits"] == []
    assert len(payload["oti3_same_timestamp_red_team_checks"]) == 4
    assert {row["matching_tick_record_count"] for row in payload["oti3_same_timestamp_red_team_checks"]} == {1}
    assert len(payload["oti4_may3_source_gap_red_team_checks"]) == 3
    assert {row["local_tick_required_range_count"] for row in payload["oti4_may3_source_gap_red_team_checks"]} == {0}


def test_duplicate_policy_and_flags() -> None:
    duplicate = load_json(f"G12_NOFILL_SOURCE_CORRECTION_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json")
    decision = load_json(f"G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_{DATE}.json")
    assert duplicate["oti5_canonical_rows_accepted_for_rebuild"] == [
        "NOFILL-CAT-ROW-0001",
        "NOFILL-CAT-ROW-0016",
        "NOFILL-CAT-ROW-0017",
    ]
    assert duplicate["oti5_noncanonical_rows_rejected_from_denominator"] == 39
    assert duplicate["dsr_pbo_effective_n_status"] == "not_computable_no_result_values_opened"
    for payload in [duplicate, decision]:
        assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
        assert payload["validation_safe"] is False
        assert payload["outcome_review_opened"] is False
        assert payload["live_effect"] is False
    for row in decision["row_decisions"]:
        assert row["promotion_verdict"] == "NO_PROMOTION_VERDICT"
        assert row["validation_safe"] is False
        assert row["outcome_review_opened"] is False
        assert row["live_effect"] is False


def test_verifier_no_nested_pytest_passes() -> None:
    spec = importlib.util.spec_from_file_location(
        "g12_nofill_source_corr_verifier",
        OUT_DIR / "verify_g12_nofill_source_correction_consolidated_audit_2026_05_08.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    os.environ["G12_NOFILL_SOURCE_CORRECTION_SKIP_NESTED_PYTEST"] = "1"
    result = module.verify(run_pytest=False, write_audit=False)
    assert result["verification_status"] == "PASS"
    assert result["can_mark_goal_complete"] is True
