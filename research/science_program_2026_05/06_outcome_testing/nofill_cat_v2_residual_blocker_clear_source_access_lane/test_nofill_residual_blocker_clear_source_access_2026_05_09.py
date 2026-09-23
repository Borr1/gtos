from __future__ import annotations

import json
from pathlib import Path

import build_nofill_residual_blocker_clear_source_access_2026_05_09 as builder
import verify_nofill_residual_blocker_clear_source_access_2026_05_09 as verifier


LANE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-09"


def test_blocker_scope_is_exactly_eight_with_expected_families() -> None:
    rows = builder.load_blocker_rows()
    assert len(rows) == 8
    counts = {}
    for row in rows:
        counts[row["source_lane"]] = counts.get(row["source_lane"], 0) + 1
        assert row["in_accepted_packet_denominator"] is False
        assert row["categorical_lifecycle_label"] is None
    assert counts == {
        "OTI4_G6_OPENING_DRIVE": 3,
        "OTI3_G3_GEOMETRY": 4,
        "OTI2_RISKBANK": 1,
    }


def test_reject_count_stays_sixty_five() -> None:
    assert builder.load_reject_count() == 65


def test_generated_outputs_have_source_control_statuses_only() -> None:
    path = LANE_DIR / f"NOFILL_RESIDUAL_BLOCKER_ROW_DECISION_LEDGER_{DATE}.jsonl"
    assert path.exists()
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 8
    assert {row["terminal_source_control_status"] for row in rows} <= builder.ALLOWED_TERMINAL_STATUSES
    assert all(row["promotion_verdict"] == builder.PROMOTION_VERDICT for row in rows)
    assert not any(row["validation_safe"] for row in rows)
    assert not any(row["outcome_review_opened"] for row in rows)
    assert not any(row["live_effect"] for row in rows)
    assert not any(row["cleared_into_accepted_denominator"] for row in rows)
    assert not any(row["categorical_lifecycle_label"] is not None for row in rows)


def test_clearance_packet_preserves_no_promotion_boundary() -> None:
    packet = json.loads(
        (LANE_DIR / f"NOFILL_RESIDUAL_BLOCKER_CLEARANCE_PACKET_{DATE}.json").read_text(
            encoding="utf-8"
        )
    )
    assert packet["targeted_blocker_count"] == 8
    assert packet["reject_total_preserved_outside_labels_denominators"] == 65
    assert packet["accepted_denominator_rows_added"] == 0
    assert packet["promotion_verdict"] == builder.PROMOTION_VERDICT
    assert packet["validation_safe"] is False
    assert packet["outcome_review_opened"] is False
    assert packet["live_effect"] is False
    assert packet["opens_result_scoring"] is False
    assert packet["can_open_validation"] is False
    assert packet["can_promote"] is False


def test_search_ledger_covers_all_three_blocker_families() -> None:
    search = json.loads(
        (LANE_DIR / f"NOFILL_RESIDUAL_BLOCKER_SOURCE_SEARCH_LEDGER_{DATE}.json").read_text(
            encoding="utf-8"
        )
    )
    families = {record["family"] for record in search["source_records"]}
    assert {
        "oti4_may3_opening_range",
        "oti2_xauusd_active_window",
        "oti3_same_tick_event_order",
    } <= families
    assert search["searched_root_count"] >= 5


def test_verifier_passes_current_packet() -> None:
    result = verifier.verify()
    assert result["status"] == "PASS", result["issues"]
    assert result["can_mark_goal_complete"] is True
