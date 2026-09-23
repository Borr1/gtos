#!/usr/bin/env python3
"""Focused tests for NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
BUILDER_PATH = OUT_DIR / "build_nofill_lifecycle_closure_source_packet_2026_05_08.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("nofill_close_builder", BUILDER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_builder()


def load_json(name: str):
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def load_jsonl(name: str):
    return [json.loads(line) for line in (OUT_DIR / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_packet_universe_and_exclusions():
    packet = load_json("NOFILL_CLOSE_ROW_PACKET_2026-05-08.json")
    rows = load_jsonl("NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl")
    assert packet["packet_row_count"] == 298
    assert len(rows) == 298
    assert len({row["source_inventory_id"] for row in rows}) == 298
    assert not any(row["source_lane"] == "OTI8_CNR061" for row in rows)
    assert "stop_after_original_horizon" not in {row["closure_label"] for row in rows}


def test_frozen_contract_before_classification():
    anchor = load_json("NOFILL_CLOSE_CONTEXT_ANCHOR_2026-05-08.json")
    contract = load_json("NOFILL_CLOSE_FROZEN_SOURCE_CONTRACT_2026-05-08.json")
    packet = load_json("NOFILL_CLOSE_ROW_PACKET_2026-05-08.json")
    assert anchor["written_at_utc"] <= contract["contract_frozen_at_utc"]
    assert contract["contract_frozen_at_utc"] <= packet["classification_started_at_utc"]


def test_required_closure_counts():
    packet = load_json("NOFILL_CLOSE_ROW_PACKET_2026-05-08.json")
    counts = packet["closure_label_counts"]
    assert counts["pending_cancelled_wrong_side_before_fill_source_confirmed"] == 22
    assert counts["pending_cancelled_system_or_new_day_before_fill_source_confirmed"] == 8
    assert counts["pending_still_open_at_frozen_horizon_source_confirmed"] == 24
    assert counts["entry_not_touched_before_terminal_area_source_confirmed"] == 46
    assert counts["entry_not_touched_through_tick_horizon_source_confirmed"] == 48
    assert counts["price_compatible_m1_source_recovered"] == 69
    assert counts["terminal_sequence_tick_source_projected_no_score"] == 80
    assert "terminal_order_unclaimed_due_same_bar_or_ltf_gap" not in counts


def test_oti1_metadata_projection_complete():
    rows = load_jsonl("NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl")
    oti1 = [row for row in rows if row["source_lane"] == "OTI1_LIFECYCLE"]
    assert len(oti1) == 54
    assert all(row["projected_symbol"] for row in oti1)
    assert all(row["projected_session"] for row in oti1)
    assert all(row["projected_side"] for row in oti1)
    assert all(row["source_projection"]["projection_status"] == "PROJECTED_FROM_SANITIZED_LIFECYCLE_SOURCE" for row in oti1)


def test_source_recovery_and_exact_blocker():
    rows = load_jsonl("NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl")
    blocker_ledger = load_json("NOFILL_CLOSE_ROW_BLOCKER_LEDGER_2026-05-08.json")
    recovered = [row for row in rows if row["closure_label"] == "price_compatible_m1_source_recovered"]
    assert len(recovered) == 69
    assert all(row["source_evidence"]["decision_covered_by_recovered_source"] for row in recovered)
    assert all(row["source_evidence"]["entry_price_compatible_with_recovered_source"] for row in recovered)
    blocked = [row for row in rows if row["closure_status"] == "source_blocked_exact"]
    assert blocked == []
    assert not [
        row for row in rows
        if any("BLOCKED_NO_TICKS_IN_WINDOW" in blocker for blocker in row.get("exact_blockers", []))
    ]
    requests = blocker_ledger["read_only_extraction_requests"]
    assert requests == []
    superseded = blocker_ledger["superseded_read_only_extraction_requests"]
    assert len(superseded) == 1
    assert superseded[0]["packet_row_id"] == "NOFILL-CLOSE-ROW-0127"
    assert superseded[0]["current_audit_status"] == "SUPERSEDED_BY_EXISTING_LOCAL_OTR061_SOURCE_EVIDENCE"
    assert superseded[0]["source_gap"] == "RESOLVED_FORMER_BLOCKED_NO_TICKS_IN_WINDOW"
    assert superseded[0]["terminal_area_touch_time_utc"] == "2026-05-06T07:15:00.634000Z"
    manifest = REPO_ROOT / superseded[0]["request_manifest_path"]
    assert manifest.exists()
    manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_payload["request_id"] == superseded[0]["request_id"]
    assert manifest_payload["active_request"] is False


def test_row_0127_source_closed_from_otr061_tick_recovery():
    rows = load_jsonl("NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl")
    row = next(item for item in rows if item["packet_row_id"] == "NOFILL-CLOSE-ROW-0127")
    projection = row["source_evidence"]["tick_terminal_sequence_projection"]
    selected = projection["selected_supplemental_source_files"]
    assert row["closure_status"] == "source_closed"
    assert row["closure_label"] == "terminal_sequence_tick_source_projected_no_score"
    assert row["projected_symbol"] == "XAUUSD"
    assert row["projected_side"] == "LONG"
    assert row["decision_asof_utc"] == "2026-05-06T07:15:00+00:00"
    assert projection["terminal_area_touch_time_utc"] == "2026-05-06T07:15:00.634000Z"
    assert projection["entry_touch_time_utc"] is None
    assert len(selected) == 1
    assert selected[0].endswith(
        "research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\"
        "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"
    ) or selected[0].endswith(
        "research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/"
        "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"
    )
    assert projection["source_sha256"][selected[0]] == "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"
    assert projection["supplemental_tick_source_search"]["selected_source_files"] == selected


def test_no_forbidden_fields_or_flags():
    rows = load_jsonl("NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl")
    noleak = load_json("NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json")
    assert not builder.scan_forbidden(rows)
    assert noleak["status"] == "PASS"
    assert noleak["forbidden_packet_hits_count"] == 0
    assert noleak["account_history_accessed"] is False
    assert noleak["broker_actual_r_accessed"] is False
    assert noleak["live_trade_results_accessed"] is False
    assert noleak["mt5_account_calls"] == 0
    assert noleak["mt5_order_calls"] == 0
    assert all(row["promotion_verdict"] == "NO_PROMOTION_VERDICT" for row in rows)
    assert not any(row["validation_safe"] for row in rows)
    assert not any(row["outcome_review_opened"] for row in rows)
    assert not any(row["live_effect"] for row in rows)


def test_duplicate_samplefloor_and_hash_audits():
    duplicate = load_json("NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json")
    source = load_json("NOFILL_CLOSE_SOURCE_SEARCH_LEDGER_2026-05-08.json")
    assert duplicate["packet_rows"] == 298
    assert duplicate["validation_sample_floor_status"] == "FALSE_SOURCE_CLOSURE_PACKET_NOT_RESULT_VALIDATION"
    assert duplicate["status"] == "PASS"
    assert not source["hash_mismatches"]
    assert not source["missing_expected_files"]
    assert source["consumed_source_file_count"] >= 40
