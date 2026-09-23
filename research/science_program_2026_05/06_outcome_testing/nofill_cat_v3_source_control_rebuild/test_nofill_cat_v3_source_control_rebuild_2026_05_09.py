from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


DATE = "2026-05-09"
OUT_DIR = Path(__file__).resolve().parent
EXPECTED_FAMILY_COUNTS = {
    "accepted": 225,
    "source_control": 4,
    "source_impossible": 4,
    "blocked": 0,
    "reject": 65,
}
MAY3_ROWS = {
    "NOFILL-CAT-ROW-0049",
    "NOFILL-CAT-ROW-0050",
    "NOFILL-CAT-ROW-0051",
}
XAU_ROW = "NOFILL-CAT-ROW-0241"
USDJPY_ROWS = {
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
}


def load_json(name: str):
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def load_rows():
    return [
        json.loads(line)
        for line in (OUT_DIR / f"NOFILL_CAT_V3_ROW_DECISION_LEDGER_{DATE}.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def full_family_counts(rows):
    counter = Counter(row["v3_terminal_family"] for row in rows)
    return {key: counter.get(key, 0) for key in EXPECTED_FAMILY_COUNTS}


def test_v3_universe_represents_all_298_rows_once():
    rows = load_rows()
    assert len(rows) == 298
    assert len({row["packet_row_id"] for row in rows}) == 298
    assert full_family_counts(rows) == EXPECTED_FAMILY_COUNTS


def test_required_target_rows_have_explicit_terminal_states_outside_denominator():
    rows = {row["packet_row_id"]: row for row in load_rows()}
    for row_id in MAY3_ROWS:
        assert rows[row_id]["v3_terminal_state"] == "SOURCE_CONTROL_MARKET_SESSION_EMPTY"
        assert rows[row_id]["in_accepted_packet_denominator"] is False
        assert rows[row_id]["categorical_lifecycle_label"] is None
    assert rows[XAU_ROW]["v3_terminal_state"] == "SOURCE_CONTROL_INPUT_ONLY_NO_ENTRY_THROUGH_CANCEL"
    assert rows[XAU_ROW]["in_accepted_packet_denominator"] is False
    for row_id in USDJPY_ROWS:
        assert rows[row_id]["v3_terminal_state"] == "SOURCE_IMPOSSIBLE_EXACT_ORDERING"
        assert rows[row_id]["exact_next_source_needed"]
        assert rows[row_id]["in_accepted_packet_denominator"] is False


def test_packet_counts_preserve_accepted_denominator_and_source_control_boundary():
    packet = load_json(f"NOFILL_CAT_V3_ACCEPTED_OR_SOURCE_CONTROL_PACKET_{DATE}.json")
    assert packet["accepted_denominator_row_count"] == 225
    assert packet["source_control_non_denominator_row_count"] == 4
    source_control_ids = {
        row["packet_row_id"]
        for row in packet["rows"]
        if row["v3_terminal_family"] == "source_control"
    }
    assert source_control_ids == MAY3_ROWS | {XAU_ROW}


def test_rejects_and_impossibles_are_not_denominator_rows_or_labeled():
    rows = load_rows()
    reject_rows = [row for row in rows if row["v3_terminal_family"] == "reject"]
    impossible_rows = [row for row in rows if row["v3_terminal_family"] == "source_impossible"]
    assert len(reject_rows) == 65
    assert len(impossible_rows) == 4
    for row in reject_rows + impossible_rows:
        assert row["in_accepted_packet_denominator"] is False
        assert row["categorical_lifecycle_label"] is None
        assert row["lifecycle_label_assigned"] is False


def test_no_leak_and_search_ledgers_keep_v3_non_promotional():
    hash_audit = load_json(f"NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json")
    search = load_json(f"NOFILL_CAT_V3_SOURCE_ROOT_SEARCH_LEDGER_{DATE}.json")
    completion = load_json(f"NOFILL_CAT_V3_COMPLETION_AUDIT_{DATE}.json")
    assert hash_audit["status"] == "PASS"
    assert hash_audit["noleak_checks"]["validation_safe_true_count"] == 0
    assert hash_audit["noleak_checks"]["outcome_review_opened_true_count"] == 0
    assert hash_audit["noleak_checks"]["live_effect_true_count"] == 0
    assert search["source_sequence_route_found"] is False
    assert completion["can_mark_goal_complete"] is True
