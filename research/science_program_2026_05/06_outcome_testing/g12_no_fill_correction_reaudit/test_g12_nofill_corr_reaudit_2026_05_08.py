#!/usr/bin/env python3
"""Focused tests for the G12 NOFILL correction reaudit artifacts."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
BUILDER_PATH = OUT_DIR / "build_g12_nofill_corr_reaudit_2026_05_08.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("g12_nofill_corr_reaudit_builder_test", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_builder()


def load_json(name: str):
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def test_builder_recomputes_acceptance_counts_and_row_0127() -> None:
    payloads = builder.build_payloads()
    assert payloads["decision"]["decision"] == "ACCEPT_CORRECTED_SOURCE_PACKET_AS_INPUT_ONLY_SOURCE_CLOSURE_EVIDENCE"
    counts = payloads["source_reaudit"]["packet_counts"]
    assert counts["rows_jsonl_count"] == 298
    assert counts["closure_status_counts"]["source_closed"] == 298
    assert counts["closure_status_counts"].get("source_blocked_exact", 0) == 0
    row = payloads["row_0127"]
    assert row["source_sha256"] == builder.EXPECTED_OTR_SHA256
    assert row["source_first_ts_utc"] == "2026-05-06T07:10:01.820000Z"
    assert row["source_last_ts_utc"] == "2026-05-06T11:15:59.763000Z"
    assert row["recomputed_first_source_event"]["event"] == "terminal_area"
    assert row["recomputed_first_source_event"]["first_touch_utc"] == builder.EXPECTED_ROW_0127_TOUCH


def test_generated_decision_and_completion_artifacts_preserve_research_only_flags() -> None:
    decision = load_json("G12_NOFILL_CORR_DECISION_LEDGER_2026-05-08.json")
    completion = load_json("G12_NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.json")
    for artifact in [decision, completion]:
        assert artifact["promotion_verdict"] == "NO_PROMOTION_VERDICT"
        assert artifact["validation_safe"] is False
        assert artifact["outcome_review_opened"] is False
        assert artifact["live_effect"] is False
    assert completion["can_mark_goal_complete"] is True
    assert all(item["status"] == "PASS" for item in completion["prompt_to_artifact_checklist"])


def test_exclusions_and_stale_blocker_controls_hold() -> None:
    source = load_json("G12_NOFILL_CORR_SOURCE_REAUDIT_2026-05-08.json")
    assert source["stale_blocker_status"]["status"] == "PASS"
    assert source["stale_blocker_status"]["active_BLOCKED_NO_TICKS_IN_WINDOW_rows"] == []
    assert source["stale_blocker_status"]["active_read_only_extraction_requests"] == []
    assert source["stale_blocker_status"]["source_request_manifest"]["active_request"] is False
    assert source["exclusion_status"]["status"] == "PASS"
    assert source["exclusion_status"]["six_t3_rows"]["t3_row_count"] == 6
    assert source["exclusion_status"]["blocked_94_cnr061"]["blocked_rows"] == 94
    assert source["exclusion_status"]["packet_oti8_cnr061_row_count"] == 0
    assert source["exclusion_status"]["packet_stop_after_original_horizon_label_count"] == 0


def test_no_leak_duplicate_samplefloor_and_label_family_controls_hold() -> None:
    audit = load_json("G12_NOFILL_CORR_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json")
    assert audit["status"] == "PASS"
    assert audit["forbidden_packet_key_hit_count"] == 0
    assert audit["unique_source_inventory_ids"] == 298
    assert audit["unique_duplicate_group_ids"] == 153
    assert audit["unique_nofill_duplicate_keys"] == 196
    assert audit["validation_sample_floor_status"] == "FALSE_SOURCE_CLOSURE_PACKET_NOT_RESULT_VALIDATION"
    assert audit["label_family_separation"]["no_stop_after_original_horizon_label"] is True
    assert audit["label_family_separation"]["no_r_performance_result_claim"] is True


def test_next_prompt_pack_keeps_result_contract_design_before_scoring() -> None:
    prompt = (OUT_DIR / "G12_NOFILL_CORR_NEXT_PROMPT_PACK_2026-05-08.md").read_text(encoding="utf-8")
    assert "NOFILL_LIFECYCLE_CLOSURE_RESULT_CONTRACT_DESIGN_V1" in prompt
    assert "do not score R/performance" in prompt
    assert "do not open outcomes" in prompt.lower()
    assert builder.EXPECTED_OTR_SHA256 in prompt
    assert builder.EXPECTED_ROW_0127_TOUCH in prompt
