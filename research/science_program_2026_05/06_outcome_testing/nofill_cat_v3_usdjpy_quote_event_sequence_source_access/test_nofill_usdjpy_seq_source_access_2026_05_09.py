from __future__ import annotations

import json
from pathlib import Path

import build_nofill_usdjpy_seq_source_access_2026_05_09 as builder
import verify_nofill_usdjpy_seq_source_access_2026_05_09 as verifier


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-09"
TARGET_ROWS = set(builder.TARGET_ROWS)


def load_json(name: str):
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def test_predicate_status_long_and_short_same_tick() -> None:
    long_row = {"side": "LONG", "entry_price": 159.037, "protective_level_price": 158.879, "terminal_area_price": 159.274}
    long_tick = {"bid": 158.745, "ask": 158.845}
    assert builder.predicate_status(long_row, long_tick) == {
        "entry_touch": True,
        "protective_level": True,
        "terminal_area": False,
    }

    short_row = {"side": "SHORT", "entry_price": 156.628, "protective_level_price": 156.822, "terminal_area_price": 156.337}
    short_tick = {"bid": 157.282, "ask": 157.292}
    assert builder.predicate_status(short_row, short_tick) == {
        "entry_touch": True,
        "protective_level": True,
        "terminal_area": False,
    }


def test_artifacts_cover_all_four_rows_after_build() -> None:
    builder.main()
    proof = load_json(f"NOFILL_USDJPY_SEQ_EVENT_ORDER_PROOF_PACKET_{DATE}.json")
    rows = proof["row_proofs"]
    assert {row["packet_row_id"] for row in rows} == TARGET_ROWS
    assert all(row["terminal_decision"] == "SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES" for row in rows)
    assert all(row["exact_timestamp_row_count"] == 1 for row in rows)
    assert all(set(row["simultaneous_predicates_on_first_row"]) == {"entry_touch", "protective_level"} for row in rows)


def test_source_search_has_no_sequence_like_fields() -> None:
    builder.main()
    search = load_json(f"NOFILL_USDJPY_SEQ_SOURCE_SEARCH_LEDGER_{DATE}.json")
    assert search["source_search_conclusion"] == "NO_BROKER_NATIVE_SEQUENCE_SOURCE_FOUND"
    assert search["field_name_probe_result"]["source_files_with_sequence_like_fields"] == []
    assert search["sierra_proxy_sources"]["usable_for_same_tick_ordering"] is False
    assert search["databento_local_proxy_sources"]["paid_or_api_call_made"] is False


def test_completion_audit_preserves_safety_flags() -> None:
    builder.main()
    completion = load_json(f"NOFILL_USDJPY_SEQ_COMPLETION_AUDIT_{DATE}.json")
    noleak = load_json(f"NOFILL_USDJPY_SEQ_NO_LEAK_AND_DUPLICATE_AUDIT_{DATE}.json")
    assert completion["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert completion["validation_safe"] is False
    assert completion["outcome_review_opened"] is False
    assert completion["live_effect"] is False
    assert completion["can_mark_goal_complete"] is True
    assert noleak["forbidden_key_hits"] == []
    assert not any(noleak["unsafe_flag_hits"].values())


def test_verifier_passes() -> None:
    builder.main()
    result = verifier.verify()
    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
