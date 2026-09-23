import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
DATE = "2026-05-08"


def read_json(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def test_completion_audit_covers_prompt_requirements():
    audit = read_json(f"OTI4_OPENING_DRIVE_COMPLETION_AUDIT_{DATE}.json")
    assert audit["can_mark_goal_complete"] is True
    assert audit["row_count"] == 80
    assert audit["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert audit["validation_safe"] is False
    assert audit["outcome_review_opened"] is False
    assert audit["live_effect"] is False
    assert audit["proof_status_counts"] == {
        "EXACT_IMPOSSIBILITY_OR_SOURCE_BLOCKER": 11,
        "SOURCE_HASHED_RANGE_BREAKOUT_ASOF_PROOF": 69,
    }
    assert audit["row_route_decision_counts"] == {
        "CONTRACT_REVISED_EXCLUDE_BREAKOUT_SIDE_MISMATCH": 12,
        "CONTRACT_REVISED_EXCLUDE_DECISION_BEFORE_FROZEN_RANGE_CLOSE": 8,
        "CONTRACT_REVISED_EXCLUDE_NO_BREAKOUT_ASOF": 6,
        "PATCH_SOURCE_PROJECTION_READY_FOR_FUTURE_CONTRACT_AUDIT": 51,
        "SOURCE_BLOCKED_EXACT_RANGE_TICK_WINDOW_EMPTY": 3,
    }
    assert audit["source_hash_mismatch_count"] == 0
    assert audit["result_labels_assigned"] == 0
    assert all(item["status"] == "covered" for item in audit["prompt_to_artifact_checklist"])


def test_row_ledger_has_proof_or_exact_blocker_for_every_row():
    rows = [
        json.loads(line)
        for line in (OUT / f"OTI4_OPENING_DRIVE_ROW_DECISION_LEDGER_ROWS_{DATE}.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) == 80
    packet_ids = {row["packet_row_id"] for row in rows}
    assert len(packet_ids) == 80
    for row in rows:
        assert row["promotion_verdict"] == "NO_PROMOTION_VERDICT"
        assert row["validation_safe"] is False
        assert row["outcome_review_opened"] is False
        assert row["live_effect"] is False
        assert row["result_label_assigned"] is False
        if row["row_proof_status"] == "SOURCE_HASHED_RANGE_BREAKOUT_ASOF_PROOF":
            assert row["range_high"] is not None
            assert row["range_low"] is not None
            assert row["breakout_side"] in {"UP", "DOWN", "NO_BREAKOUT_ASOF"}
            assert row["source_hashed_range_bars"]["bars_sha256"]
            assert row["source_hashed_range_bars"]["bar_count"] > 0
            assert row["source_hashed_breakout_scan_bars"]["bars_sha256"]
            assert row["as_of_provenance"]["feature_asof_utc_lte_decision_asof_utc"] is True
        else:
            assert row["row_proof_status"] == "EXACT_IMPOSSIBILITY_OR_SOURCE_BLOCKER"
            assert row["exact_blocker_code"] in {
                "BLOCK_OTI4_RANGE_NOT_COMPLETE_ASOF_DECISION",
                "BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP",
            }
            assert row["exact_blocker_reason"]


def test_source_hash_audit_and_search_ledger_are_machine_checkable():
    source_audit = read_json(f"OTI4_OPENING_DRIVE_SOURCE_HASH_ASOF_DUPLICATE_AUDIT_{DATE}.json")
    search = read_json(f"OTI4_OPENING_DRIVE_SOURCE_SEARCH_LEDGER_{DATE}.json")
    assert source_audit["all_rows_have_proof_or_exact_blocker"] is True
    assert source_audit["source_hash_mismatch_count"] == 0
    assert source_audit["asof_failure_count_for_source_corrected_rows"] == 0
    assert source_audit["original_duplicate_group_count"] == 17
    assert source_audit["source_corrected_contract_key_count"] == 16
    assert search["source_hash_mismatch_count"] == 0
    assert search["no_approved_csv_covering_empty_2026_05_03_range_windows"] is True


def test_outputs_do_not_open_forbidden_result_or_live_surfaces():
    forbidden_positive_fragments = [
        '"validation_safe": true',
        '"outcome_review_opened": true',
        '"live_effect": true',
        '"result_label_assigned": true',
        '"broker_actual_r_inspected": true',
        '"account_history_inspected": true',
        '"live_order_deal_position_labels_inspected": true',
        '"paid_network_api_databento_mt5_calls": true',
        '"outcome_scoring_run": true',
    ]
    for path in OUT.glob(f"OTI4_OPENING_DRIVE_*_{DATE}.json*"):
        text = path.read_text(encoding="utf-8").lower()
        for fragment in forbidden_positive_fragments:
            assert fragment not in text
