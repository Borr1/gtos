#!/usr/bin/env python3
"""Focused tests for NOFILL_LIFECYCLE_CLOSURE_SOURCE_CORRECTION_V1."""

from __future__ import annotations

import json
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
UPSTREAM_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet"
OTR061_SHA256 = "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"


def load_json(name: str):
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def load_upstream_json(name: str):
    return json.loads((UPSTREAM_DIR / name).read_text(encoding="utf-8"))


def load_upstream_rows():
    return [
        json.loads(line)
        for line in (UPSTREAM_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_required_correction_artifacts_exist_and_parse():
    required_json = [
        "NOFILL_CORR_CONTEXT_ANCHOR_2026-05-08.json",
        "NOFILL_CORR_SOURCE_RESOLUTION_LEDGER_2026-05-08.json",
        "NOFILL_CORR_PATCH_LEDGER_2026-05-08.json",
        "NOFILL_CORR_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json",
        "NOFILL_CORR_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
        "NOFILL_CORR_FORENSICS_AND_LEARNING_2026-05-08.json",
        "NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.json",
    ]
    required_md = [name.replace(".json", ".md") for name in required_json] + [
        "NOFILL_CORR_G12_REAUDIT_PROMPT_PACK_2026-05-08.md",
    ]
    for name in required_json:
        assert load_json(name)["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    for name in required_md:
        assert (OUT_DIR / name).exists()


def test_upstream_packet_corrected_counts_and_row_0127():
    packet = load_upstream_json("NOFILL_CLOSE_ROW_PACKET_2026-05-08.json")
    rows = load_upstream_rows()
    row = next(item for item in rows if item["packet_row_id"] == "NOFILL-CLOSE-ROW-0127")
    projection = row["source_evidence"]["tick_terminal_sequence_projection"]
    selected = projection["selected_supplemental_source_files"]
    assert packet["packet_row_count"] == 298
    assert packet["closure_status_counts"] == {"source_closed": 298}
    assert row["closure_status"] == "source_closed"
    assert row["closure_label"] == "terminal_sequence_tick_source_projected_no_score"
    assert row["projected_symbol"] == "XAUUSD"
    assert projection["terminal_area_touch_time_utc"] == "2026-05-06T07:15:00.634000Z"
    assert selected and selected[0].endswith("OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet")
    assert projection["source_sha256"][selected[0]] == OTR061_SHA256
    assert not any(
        "BLOCKED_NO_TICKS_IN_WINDOW" in blocker
        for item in rows
        for blocker in item.get("exact_blockers", [])
    )


def test_stale_readonly_request_is_superseded_not_active():
    blocker = load_upstream_json("NOFILL_CLOSE_ROW_BLOCKER_LEDGER_2026-05-08.json")
    assert blocker["source_closed_rows"] == 298
    assert blocker["source_blocked_exact_rows"] == 0
    assert blocker["read_only_extraction_requests"] == []
    superseded = blocker["superseded_read_only_extraction_requests"]
    assert len(superseded) == 1
    assert superseded[0]["packet_row_id"] == "NOFILL-CLOSE-ROW-0127"
    assert superseded[0]["active_request"] is False
    assert superseded[0]["current_audit_status"] == "SUPERSEDED_BY_EXISTING_LOCAL_OTR061_SOURCE_EVIDENCE"
    manifest = REPO_ROOT / superseded[0]["request_manifest_path"]
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["active_request"] is False
    assert payload["source_gap"] == "RESOLVED_FORMER_BLOCKED_NO_TICKS_IN_WINDOW"


def test_correction_hash_noleak_duplicate_and_flags():
    source = load_json("NOFILL_CORR_SOURCE_RESOLUTION_LEDGER_2026-05-08.json")
    hash_noleak = load_json("NOFILL_CORR_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json")
    duplicate = load_json("NOFILL_CORR_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json")
    assert source["row_0127_resolution"]["source_closes_row"] is True
    assert source["row_0127_resolution"]["source_sha256"] == OTR061_SHA256
    assert source["row_0127_resolution"]["source_first_ts_utc"] == "2026-05-06T07:10:01.820000Z"
    assert source["row_0127_resolution"]["source_last_ts_utc"] == "2026-05-06T11:15:59.763000Z"
    assert hash_noleak["status"] == "PASS"
    assert hash_noleak["forbidden_packet_hits_count"] == 0
    assert hash_noleak["otr061_source_hash"]["matches"] is True
    assert duplicate["status"] == "PASS"
    assert duplicate["validation_sample_floor_status"] == "FALSE_SOURCE_CLOSURE_PACKET_NOT_RESULT_VALIDATION"
    assert duplicate["closure_status_counts"] == {"source_closed": 298}


def test_g12_reaudit_prompt_and_completion_boundaries():
    prompt = (OUT_DIR / "NOFILL_CORR_G12_REAUDIT_PROMPT_PACK_2026-05-08.md").read_text(encoding="utf-8")
    completion = load_json("NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.json")
    assert "298 source_closed" in prompt
    assert "0 source_blocked_exact" in prompt
    assert "NOFILL-CLOSE-ROW-0127" in prompt
    assert OTR061_SHA256 in prompt
    assert completion["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert completion["validation_safe"] is False
    assert completion["outcome_review_opened"] is False
    assert completion["live_effect"] is False
