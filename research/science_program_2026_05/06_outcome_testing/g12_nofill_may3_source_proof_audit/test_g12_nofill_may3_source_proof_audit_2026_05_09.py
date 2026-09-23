from __future__ import annotations

import json
from pathlib import Path


LANE_DIR = Path(__file__).resolve().parent
TERMINAL_DECISION = "ACCEPT_AS_SOURCE_CONTROL_MARKET_SESSION_EMPTY_EVIDENCE_ONLY"
TARGET_ROWS = [
    "NOFILL-CAT-ROW-0049",
    "NOFILL-CAT-ROW-0050",
    "NOFILL-CAT-ROW-0051",
]


def load_json(name: str):
    return json.loads((LANE_DIR / name).read_text(encoding="utf-8"))


def test_decision_ledger_accepts_exact_three_source_control_rows_only():
    ledger = load_json("G12_NOFILL_MAY3_DECISION_LEDGER_2026-05-09.json")
    assert ledger["target_row_ids"] == TARGET_ROWS
    assert ledger["targeted_row_count"] == 3
    assert ledger["terminal_decision"] == TERMINAL_DECISION
    assert ledger["terminal_decision_counts"] == {TERMINAL_DECISION: 3}
    assert ledger["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert ledger["validation_safe"] is False
    assert ledger["outcome_review_opened"] is False
    assert ledger["live_effect"] is False
    assert all(row["source_control_only"] is True for row in ledger["row_decisions"])
    assert all(row["result_label_assigned"] is False for row in ledger["row_decisions"])
    assert all(row["cleared_into_accepted_denominator"] is False for row in ledger["row_decisions"])


def test_row_identity_matches_residual_blocker_lane():
    ledger = load_json("G12_NOFILL_MAY3_DECISION_LEDGER_2026-05-09.json")
    assert all(row["all_identity_fields_match_residual"] for row in ledger["row_matching_audit"])
    assert all(row["original_blocker_codes_match"] for row in ledger["row_matching_audit"])
    assert {row["residual_status_before_upstream_lane"] for row in ledger["row_matching_audit"]} == {
        "STILL_BLOCKED_WITH_EXACT_NEXT_SOURCE"
    }
    assert ledger["upstream_status_counts"] == {"MARKET_SESSION_NONTRADING_EMPTY_PROVEN_SOURCE_CONTROL": 3}


def test_source_hash_and_tick_zero_row_recompute():
    audit = load_json("G12_NOFILL_MAY3_SOURCE_HASH_AUDIT_2026-05-09.json")
    assert audit["strict_source_hashes_recomputed_ok"] is True
    assert audit["source_hash_records_checked"] == 36
    assert audit["strict_source_hash_records_checked"] == 34
    assert audit["mutable_control_hash_drift_count"] == 2
    assert all(
        row["sha256_matches_expected"] is True
        for row in audit["hash_audits"]
        if row["strict_hash_required"] is True
    )
    assert audit["tick_parquet_recompute"]["NAS100"]["window_rows"] == 0
    assert audit["tick_parquet_recompute"]["XAUUSD"]["window_rows"] == 0
    assert audit["tick_parquet_recompute"]["NAS100"]["first_timestamp_utc"] == "2026-05-03T22:00:00.391000Z"
    assert audit["tick_parquet_recompute"]["XAUUSD"]["first_timestamp_utc"] == "2026-05-03T22:00:00.780000Z"


def test_official_session_recheck_and_proxy_boundary():
    official = load_json("G12_NOFILL_MAY3_OFFICIAL_CME_SOURCE_RECHECK_2026-05-09.json")
    assert official["conversion"]["frozen_window_chicago_ct"]["start"] == "2026-05-03T08:00:00-05:00"
    assert official["conversion"]["frozen_window_new_york_et"]["start"] == "2026-05-03T09:00:00-04:00"
    assert official["conversion"]["official_globex_sunday_open_utc"] == "2026-05-03T22:00:00Z"
    assert official["conversion"]["window_is_before_official_sunday_open"] is True
    assert {source["source_owner"] for source in official["sources"]} == {"CME Group"}
    session_md = (LANE_DIR / "G12_NOFILL_MAY3_SESSION_AND_PROXY_AUDIT_2026-05-09.md").read_text(
        encoding="utf-8"
    )
    assert "source-control evidence" in session_md
    assert "not a result label" in session_md.lower()


def test_noleak_denominator_counts_and_completion_audit():
    completion = load_json("G12_NOFILL_MAY3_COMPLETION_AUDIT_2026-05-09.json")
    assert completion["objective_satisfied"] is True
    assert completion["terminal_decision"] == TERMINAL_DECISION
    assert completion["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert completion["validation_safe"] is False
    assert completion["outcome_review_opened"] is False
    assert completion["live_effect"] is False
    assert all(item["status"] == "PASS" for item in completion["prompt_to_artifact_checklist"])
    noleak_md = (LANE_DIR / "G12_NOFILL_MAY3_NOLEAK_DENOMINATOR_AUDIT_2026-05-09.md").read_text(
        encoding="utf-8"
    )
    assert '"rejected_rows": 65' in noleak_md
    assert '"blocked_exact_rows": 8' in noleak_md
    assert "six T3/CNR061 lifecycle rows" in noleak_md
