from __future__ import annotations

from collections import Counter
from pathlib import Path

from scripts import analyze_lane7_open_questions_triage as mod


ROOT = Path(__file__).resolve().parents[1]


def test_lane7_triage_classifies_all_remaining_queue_tail():
    payload = mod.build_payload(ROOT)
    by_id = {row["id"]: row for row in payload["task_classifications"]}

    expected = {
        "RR-2": "DONE",
        "RR-3": "DONE",
        "RR-4": "DEFERRED_WITH_TRIGGER",
        "RR-7": "DEFERRED_WITH_TRIGGER",
        "U-1": "BLOCKED_WITH_REASON",
        "U-12": "BLOCKED_WITH_REASON",
        "U-17": "DONE",
        "U-2": "BLOCKED_WITH_REASON",
        "U-4": "DONE",
        "U-6": "BLOCKED_WITH_REASON",
        "U-9": "DONE",
        "L-3": "FILED_FOR_APPROVAL",
        "L-5": "DEFERRED_WITH_TRIGGER",
        "RR-5": "DEFERRED_WITH_TRIGGER",
        "RR-6": "DEFERRED_WITH_TRIGGER",
        "U-10": "DEFERRED_WITH_TRIGGER",
        "U-13": "DEFERRED_WITH_TRIGGER",
        "U-14": "DEFERRED_WITH_TRIGGER",
        "U-15": "DEFERRED_WITH_TRIGGER",
        "U-16": "DEFERRED_WITH_TRIGGER",
        "U-8": "BLOCKED_WITH_REASON",
        "Z-1": "DEFERRED_WITH_TRIGGER",
        "Z-2": "DEFERRED_WITH_TRIGGER",
        "Z-3": "DEFERRED_WITH_TRIGGER",
        "Z-4": "DEFERRED_WITH_TRIGGER",
    }

    assert {item_id: by_id[item_id]["status"] for item_id in expected} == expected
    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert Counter(expected.values()) == Counter(row["status"] for row in payload["task_classifications"])


