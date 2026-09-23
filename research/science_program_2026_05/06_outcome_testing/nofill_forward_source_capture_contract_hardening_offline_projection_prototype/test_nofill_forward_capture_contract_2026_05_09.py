#!/usr/bin/env python3
"""Focused tests for the NOFILL source-capture contract/prototype lane."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import build_nofill_forward_capture_contract_2026_05_09 as builder
import verify_nofill_forward_capture_contract_2026_05_09 as verifier


OUT_DIR = Path(__file__).resolve().parent


def load_json(name: str):
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def load_rows() -> list[dict]:
    return [
        json.loads(line)
        for line in (OUT_DIR / builder.PROTOTYPE_ROWS_NAME).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_contract_freezes_required_field_controls() -> None:
    contract = load_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_{builder.DATE}.json")
    assert contract["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert contract["validation_safe"] is False
    assert contract["outcome_review_opened"] is False
    assert contract["live_effect"] is False
    assert contract["field_count"] >= 55
    fields = {row["field_name"]: row for row in contract["fields"]}
    for name in (
        "capture_write_completed_at_utc",
        "capture_clock_skew_ms",
        "pending_order_mode_source_safe",
        "entry_touch_spread_value_source_safe",
        "same_tick_same_bar_ambiguity_status",
        "mt5_order_ticket_redaction_status",
        "nofill_duplicate_key_sha256",
        "forbidden_field_scan_status",
    ):
        assert name in fields
        assert fields[name]["fail_closed_status"] is True
        assert fields[name]["g12_acceptance_status"] == "PENDING_NEXT_G12_SOURCE_CAPTURE_ACCEPTANCE_AUDIT"
        assert fields[name]["live_logger_wiring_opened_now"] is False


def test_missing_status_vocab_keeps_states_distinct() -> None:
    vocab = load_json(f"NOFILL_FORWARD_MISSING_STATUS_VOCABULARY_{builder.DATE}.json")
    groups = vocab["canonical_groups"]
    assert set(groups) == {
        "MISSING_SOURCE_FIELD",
        "NOT_APPLICABLE",
        "NOT_OBSERVED_SOURCE_SAFE",
        "SOURCE_IMPOSSIBLE",
        "REDACTED",
        "NOT_YET_CAPTURED",
        "FORBIDDEN_FAIL_CLOSED",
    }
    assert "SOURCE_FIELD_MISSING" in groups["MISSING_SOURCE_FIELD"]["canonical_values"]
    assert "TOUCH_NOT_OBSERVED_VALUE_NOT_APPLICABLE" in groups["NOT_APPLICABLE"]["canonical_values"]
    assert "SOURCE_TICKET_VALUE_REDACTED" in groups["REDACTED"]["canonical_values"]


def test_prototype_rows_preserve_frozen_denominators() -> None:
    rows = load_rows()
    assert len(rows) == 298
    assert Counter(row["v3_terminal_family"] for row in rows) == {
        "accepted": 225,
        "reject": 65,
        "source_control": 4,
        "source_impossible": 4,
    }
    assert sum(row["row_level_denominator_member"] for row in rows) == 225
    assert sum(row["nofill_duplicate_key_count_member"] for row in rows) == 182
    assert sum(row["duplicate_group_id_count_member"] for row in rows) == 139
    assert all(row["contract_acceptance_state"] == "SOURCE_CONTROL_CONTRACT_FROZEN_G12_AUDIT_PENDING" for row in rows)
    assert all(row["opens_result_scoring"] is False and row["opens_live_wiring"] is False for row in rows)


def test_fixture_manifest_covers_prompt_required_cases_without_raw_values() -> None:
    manifest = load_json(f"NOFILL_FORWARD_FIXTURE_MANIFEST_{builder.DATE}.json")
    categories = {item["category"] for item in manifest["fixtures"]}
    assert set(manifest["required_fixture_categories"]).issubset(categories)
    redacted = next(item for item in manifest["fixtures"] if item["category"] == "redacted_ticket_row")
    redacted_payload = json.loads((builder.REPO_ROOT / redacted["path"]).read_text(encoding="utf-8"))
    assert redacted_payload["synthetic_source_control_input"]["raw_value_material_included"] is False
    assert redacted_payload["expected_projection"]["mt5_order_ticket_redaction_status"] == "SOURCE_TICKET_VALUE_REDACTED"
    forbidden = next(item for item in manifest["fixtures"] if item["category"] == "forbidden_field_examples")
    forbidden_payload = json.loads((builder.REPO_ROOT / forbidden["path"]).read_text(encoding="utf-8"))
    assert all(row["raw_value_material_included"] is False for row in forbidden_payload["forbidden_field_examples"])
    text = json.dumps(redacted_payload) + json.dumps(forbidden_payload)
    assert "09" not in text
    assert "SECRET" not in text


def test_no_leak_and_denominator_audits_pass() -> None:
    no_leak = load_json(f"NOFILL_FORWARD_NO_LEAK_AND_REDACTION_AUDIT_{builder.DATE}.json")
    denom = load_json(f"NOFILL_FORWARD_DUPLICATE_DENOMINATOR_CONTROL_AUDIT_{builder.DATE}.json")
    assert no_leak["status"] == "PASS"
    assert no_leak["raw_value_hits"] == []
    assert no_leak["forbidden_key_hits_in_prototype_rows"] == []
    assert no_leak["redaction_controls"]["raw_ticket_values_emitted"] is False
    assert no_leak["redaction_controls"]["raw_ticket_values_hashed"] is False
    assert denom["status"] == "PASS"
    assert denom["prototype_denominator_effect"] == "NO_CHANGE_SOURCE_CONTROL_METADATA_ONLY"


def test_source_hash_manifest_covers_sources_parsers_fixtures_and_generated_artifacts() -> None:
    manifest = load_json(f"NOFILL_FORWARD_SOURCE_HASH_MANIFEST_{builder.DATE}.json")
    assert manifest["record_counts"]["source_entries"] >= 20
    assert manifest["record_counts"]["parser_entries"] == 3
    assert manifest["record_counts"]["fixture_entries"] >= 11
    assert manifest["record_counts"]["generated_entries"] >= 20
    for group_name in ("source_entries", "parser_entries", "fixture_entries", "generated_entries"):
        for item in manifest[group_name]:
            assert item["exists"] is True
            assert item["sha256"]
    by_path = {item["path"]: item for item in manifest["source_entries"]}
    assert by_path[".context/LIVE_STATE.md"]["strict_hash_recompute"] is False
    assert by_path[".context/00_core/research_current_state.md"]["hash_policy"] == "mutable_context_snapshot_presence_only"


def test_lf_normalized_hash_fallback_is_text_gated(tmp_path: Path) -> None:
    text_artifact = tmp_path / "portable.md"
    text_artifact.write_bytes(b"alpha\r\nbeta\r\n")
    text_entry = {"path": str(text_artifact)}
    assert verifier.entry_allows_lf_normalized_fallback(text_entry) is True
    assert verifier.sha256_lf_normalized_file(text_artifact)

    binary_artifact = tmp_path / "payload.bin"
    binary_artifact.write_bytes(b"alpha\r\nbeta\r\n")
    binary_entry = {"path": str(binary_artifact)}
    assert verifier.entry_allows_lf_normalized_fallback(binary_entry) is False
    assert verifier.sha256_lf_normalized_file(binary_artifact) is None


def test_generated_verifier_passes() -> None:
    result = verifier.verify()
    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
    assert result["future_live_logger_wiring_lane_still_gated"] is True
