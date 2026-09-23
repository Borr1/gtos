#!/usr/bin/env python3
"""Focused tests for the NOFILL forward source-safe projection builder."""

from __future__ import annotations

import json
from pathlib import Path

import build_nofill_forward_source_safe_projection_builder_2026_05_09 as builder


OUT_DIR = Path(__file__).resolve().parent
ROWS_PATH = OUT_DIR / "NOFILL_FORWARD_SOURCE_SAFE_PROJECTION_ROWS_2026-05-09.jsonl"


def load_rows() -> list[dict]:
    return [json.loads(line) for line in ROWS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_pending_projection_redacts_ticket_and_execution_values() -> None:
    source = builder.SourceLogRow(
        rel_path="shadow_logs/pending_limit_lifecycle.jsonl",
        line_no=1,
        row={
            "pending_order_mode": "INTERNAL_CANDLE_POLLED_INTENT",
            "broker_pending_order_created": True,
            "native_pending_order_type": "BUY_LIMIT",
            "mt5_order_ticket": 09,
            "pending_ticket": "secret-pending-ticket",
            "trade_state_ticket": 987654321,
            "broker_fill_state": "filled",
            "order_send_success": True,
            "slippage_price": 1.25,
        },
        sha256="abc",
        source_type="pending_limit_lifecycle_source_safe_projection",
        route="test",
    )
    projected = builder.pending_projection([source])
    assert projected["pending_order_mode_source_safe"] == "INTERNAL_CANDLE_POLLED_INTENT"
    assert projected["broker_pending_order_created_status"] == "NATIVE_PENDING_OBSERVABILITY_PRESENT_REDACTED"
    assert projected["native_pending_order_type_source_safe"] == "BUY_LIMIT"
    assert projected["raw_ticket_field_present_status"] == "RAW_TICKET_VALUE_PRESENT_REDACTED"
    assert projected["mt5_order_ticket_redaction_status"] == "SOURCE_TICKET_VALUE_REDACTED"

    row = {
        **projected,
        "slippage_label_status": "NOT_OPENED_FOR_SOURCE_CONTROL",
        "execution_quality_label_status": "NOT_OPENED_FOR_SOURCE_CONTROL",
        "cost_testing_gate_status": "COST_TESTING_NOT_OPENED",
    }
    text = json.dumps(row, sort_keys=True)
    assert "09" not in text
    assert "secret-pending-ticket" not in text


def test_generated_projection_rows_preserve_denominators() -> None:
    rows = load_rows()
    assert len(rows) == 298
    family_counts = {}
    for row in rows:
        family_counts[row["v3_terminal_family"]] = family_counts.get(row["v3_terminal_family"], 0) + 1
    assert family_counts == {
        "accepted": 225,
        "reject": 65,
        "source_control": 4,
        "source_impossible": 4,
    }
    assert sum(row["row_level_denominator_member"] for row in rows) == 225
    assert sum(row["nofill_duplicate_key_count_member"] for row in rows) == 182
    assert sum(row["duplicate_group_id_count_member"] for row in rows) == 139
    assert {
        row["packet_row_id"]
        for row in rows
        if row["v3_terminal_family"] == "source_control"
    } == builder.SOURCE_CONTROL_ROWS
    assert {
        row["packet_row_id"]
        for row in rows
        if row["v3_terminal_family"] == "source_impossible"
    } == builder.SOURCE_IMPOSSIBLE_ROWS


def test_generated_rows_have_required_addendum_fields_and_closed_flags() -> None:
    rows = load_rows()
    allowlist = json.loads(
        (OUT_DIR / "NOFILL_FORWARD_ALLOWLIST_PROJECTION_SPEC_2026-05-09.json").read_text(encoding="utf-8")
    )
    exhaustive_allowed = set(allowlist["exhaustive_projection_output_fields_allowed"])
    for row in rows:
        assert set(builder.ADDENDUM_FIELD_NAMES).issubset(row)
        assert set(row).issubset(exhaustive_allowed)
        assert row["promotion_verdict"] == "NO_PROMOTION_VERDICT"
        assert row["validation_safe"] is False
        assert row["outcome_review_opened"] is False
        assert row["live_effect"] is False
        assert row["opens_result_scoring"] is False
        assert row["slippage_label_status"] == "NOT_OPENED_FOR_SOURCE_CONTROL"
        assert row["execution_quality_label_status"] == "NOT_OPENED_FOR_SOURCE_CONTROL"
        assert row["cost_testing_gate_status"] == "COST_TESTING_NOT_OPENED"
        assert isinstance(row["missing_statuses"], dict)


def test_touch_not_observed_spread_missing_status_is_not_source_missing() -> None:
    rows = load_rows()
    not_observed = [row for row in rows if row["entry_touch_spread_status"] == "TOUCH_NOT_OBSERVED_SOURCE_SAFE"]
    assert len(not_observed) == 113
    assert all(
        row["missing_statuses"]["entry_touch_spread_value_source_safe"] == "TOUCH_NOT_OBSERVED_VALUE_NOT_APPLICABLE"
        for row in not_observed
    )


def test_forbidden_audit_and_denominator_audit_pass() -> None:
    forbidden = json.loads(
        (OUT_DIR / "NOFILL_FORWARD_TICKET_REDACTION_AND_FORBIDDEN_FIELD_AUDIT_2026-05-09.json").read_text(
            encoding="utf-8"
        )
    )
    denominator = json.loads(
        (OUT_DIR / "NOFILL_FORWARD_DENOMINATOR_AND_EXCLUSION_AUDIT_2026-05-09.json").read_text(
            encoding="utf-8"
        )
    )
    assert forbidden["status"] == "PASS"
    assert forbidden["row_issue_count"] == 0
    assert denominator["status"] == "PASS"
    assert denominator["projection_denominator_effect"] == "NO_CHANGE_SOURCE_CONTROL_METADATA_ONLY"


def test_search_ledger_records_prior_worktree_saturation() -> None:
    ledger = json.loads(
        (OUT_DIR / "NOFILL_FORWARD_SOURCE_INVENTORY_AND_SEARCH_LEDGER_2026-05-09.json").read_text(
            encoding="utf-8"
        )
    )
    assert ledger["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert ledger["validation_safe"] is False
    assert ledger["prior_worktree_log_search"]
    assert all(
        item["extra_needed_candidate_matches_beyond_current"] == 0
        for item in ledger["prior_worktree_log_search"]
    )
    assert any(root["root"].endswith("/data/ticks") for root in ledger["absolute_local_heavy_roots"])


def test_mutable_context_snapshots_are_not_strict_source_hashes() -> None:
    manifest = json.loads(
        (OUT_DIR / "NOFILL_FORWARD_SOURCE_HASH_MANIFEST_2026-05-09.json").read_text(encoding="utf-8")
    )
    by_path = {item["path"]: item for item in manifest}
    for path in (".context/LIVE_STATE.md", ".context/00_core/research_current_state.md"):
        assert by_path[path]["exists"] is True
        assert by_path[path]["strict_hash_recompute"] is False
        assert by_path[path]["hash_policy"] == "mutable_context_snapshot_presence_only"


def test_text_hash_manifests_include_lf_normalized_fallbacks() -> None:
    source_manifest = json.loads(
        (OUT_DIR / "NOFILL_FORWARD_SOURCE_HASH_MANIFEST_2026-05-09.json").read_text(encoding="utf-8")
    )
    parser_manifest = json.loads(
        (OUT_DIR / "NOFILL_FORWARD_PARSER_HASH_MANIFEST_2026-05-09.json").read_text(encoding="utf-8")
    )
    text_source_rows = [
        item
        for item in source_manifest
        if item["path"].endswith((".md", ".py", ".json", ".jsonl", ".txt", ".yaml", ".yml"))
    ]
    assert text_source_rows
    assert all(item["line_ending_policy"] == "lf_normalized_fallback" for item in text_source_rows)
    assert all(item["sha256_lf_normalized"] for item in text_source_rows)
    assert all(item["line_ending_policy"] == "lf_normalized_fallback" for item in parser_manifest)
    assert all(item["sha256_lf_normalized"] for item in parser_manifest)
