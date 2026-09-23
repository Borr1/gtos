from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path

import pandas as pd


OUT_DIR = Path(__file__).resolve().parent
ROWS_PATH = OUT_DIR / "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_2026-05-08_ROWS.jsonl"
PACKET_PATH = OUT_DIR / "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_2026-05-08.json"
COMPLETION_PATH = OUT_DIR / "OTI1_PENDING_INTENT_COMPLETION_AUDIT_2026-05-08.json"
HASH_AUDIT_PATH = OUT_DIR / "OTI1_PENDING_INTENT_SOURCE_HASH_NOLEAK_ASOF_AUDIT_2026-05-08.json"
BUILDER_PATH = OUT_DIR / "build_oti1_pending_intent_closure_source_packet_2026_05_08.py"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_builder():
    spec = importlib.util.spec_from_file_location("oti1_builder", BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_generated_packet_counts_and_posture_flags():
    rows = load_jsonl(ROWS_PATH)
    packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    completion = json.loads(COMPLETION_PATH.read_text(encoding="utf-8"))

    assert len(rows) == 54
    assert packet["row_count"] == 54
    assert packet["decision_counts"] == {
        "SOURCE_CORRECTED_ENTRY_TOUCH_REQUIRES_SEPARATE_FILL_PATH_CONTRACT": 22,
        "SOURCE_CORRECTED_NO_ENTRY_THROUGH_PENDING_HORIZON": 32,
    }
    assert Counter(row["row_decision_status"] for row in rows) == Counter(packet["decision_counts"])
    assert completion["can_mark_goal_complete"] is True
    assert all(row["promotion_verdict"] == "NO_PROMOTION_VERDICT" for row in rows)
    assert all(row["validation_safe"] is False for row in rows)
    assert all(row["outcome_review_opened"] is False for row in rows)
    assert all(row["live_effect"] is False for row in rows)


def test_required_fields_are_materialized_for_every_row():
    rows = load_jsonl(ROWS_PATH)
    required = {
        "entry_touched_at_utc",
        "filled_at_utc",
        "cancelled_at_utc",
        "expired_at_utc",
        "pending_intent_id_or_deterministic_key",
        "source_hash_path",
        "side_aware_touch_source",
        "as_of_rule",
        "pending_active_from_utc",
        "pending_active_until_utc",
        "frozen_horizon_start_utc",
        "frozen_horizon_end_utc",
        "last_observed_pending_state_at_utc",
    }
    for row in rows:
        assert required <= set(row)
        assert row["exact_blockers"] == []
        assert row["source_lane"] == "OTI1_LIFECYCLE"
        assert row["source_inventory_id"] not in {f"CNR-T3-CAND-{idx:04d}" for idx in range(1, 7)}

    touched = [row for row in rows if row["entry_touched_at_utc"]]
    no_touch = [row for row in rows if row["entry_touched_at_utc"] is None]
    assert len(touched) == 22
    assert len(no_touch) == 32
    assert all(row["filled_at_utc"] == row["entry_touched_at_utc"] for row in touched)
    assert all(row["row_decision_status"] == "SOURCE_CORRECTED_ENTRY_TOUCH_REQUIRES_SEPARATE_FILL_PATH_CONTRACT" for row in touched)


def test_hash_audit_and_forbidden_key_scan_pass():
    rows = load_jsonl(ROWS_PATH)
    hash_audit = json.loads(HASH_AUDIT_PATH.read_text(encoding="utf-8"))
    builder = load_builder()

    assert hash_audit["source_hash_missing_count"] == 0
    assert hash_audit["forbidden_key_hit_count"] == 0
    assert hash_audit["all_rows_false_flags"] is True
    assert builder.scan_forbidden_keys(rows) == []


def test_side_aware_touch_parser_long_and_short_rules():
    builder = load_builder()
    df = pd.DataFrame(
        {
            "ts_utc": pd.to_datetime(
                [
                    "2026-05-08T00:00:00Z",
                    "2026-05-08T00:00:01Z",
                    "2026-05-08T00:00:02Z",
                ],
                utc=True,
            ),
            "bid": [100.5, 99.7, 98.9],
            "ask": [100.7, 99.9, 99.1],
        }
    )

    long_touches = builder.compute_touches(df, "LONG", entry=100.0, protective=99.0, terminal=101.0)
    assert long_touches["entry_touch"]["timestamp_utc"] == "2026-05-08T00:00:01.000000Z"
    assert long_touches["protective_level_touch"]["timestamp_utc"] == "2026-05-08T00:00:02.000000Z"
    assert long_touches["terminal_area_touch"] is None

    short_touches = builder.compute_touches(df, "SHORT", entry=100.0, protective=101.0, terminal=99.2)
    assert short_touches["entry_touch"]["timestamp_utc"] == "2026-05-08T00:00:00.000000Z"
    assert short_touches["terminal_area_touch"]["timestamp_utc"] == "2026-05-08T00:00:02.000000Z"
    assert short_touches["protective_level_touch"] is None
