"""Focused tests for the G12 CNR T3 lifecycle audit builder."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent
BUILDER_PATH = BASE / "build_g12_cnr_t3_lifecycle_audit_2026_05_08.py"
DATE = "2026-05-08"


def load_builder():
    spec = importlib.util.spec_from_file_location("g12_cnr_t3_builder", BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_json(name: str):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def walk_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key
            yield from walk_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from walk_keys(nested)


def test_inventory_recompute_matches_304_six_298() -> None:
    builder = load_builder()
    t3 = builder.load_t3_artifacts()
    audit = builder.inventory_coverage_audit(t3)

    assert audit["status"] == "PASS"
    assert audit["recomputed_candidate_like_total"] == 304
    assert audit["packet_eligible_rows"] == 6
    assert audit["not_packet_eligible_rows"] == 298
    assert audit["recomputed_source_lane_counts"] == {
        "OTI1_LIFECYCLE": 54,
        "OTI2_RISKBANK": 47,
        "OTI3_G3_GEOMETRY": 69,
        "OTI4_G6_OPENING_DRIVE": 80,
        "OTI5_G6_CUSUM": 48,
        "OTI8_CNR061": 6,
    }


def test_lifecycle_recompute_verifies_all_six_stop_after_horizon() -> None:
    builder = load_builder()
    t3 = builder.load_t3_artifacts()
    audit = builder.lifecycle_packet_audit(t3)

    assert audit["status"] == "PASS"
    assert audit["decision"] == "ACCEPT_AS_CATEGORICAL_LIFECYCLE_SOURCE_EVIDENCE_ONLY"
    assert audit["packet_lifecycle_label_counts"] == {"stop_after_original_horizon": 6}
    assert audit["checks"]["tick_path_recompute_matches_labels"] is True
    assert audit["checks"]["contract_freeze_order_before_scan_in_builder"] is True
    assert len(audit["eligible_sidecar_hashes"]) == 6
    for row in audit["tick_path_recompute"]:
        assert row["status"] == "PASS"
        assert row["computed_lifecycle_label"] == "stop_after_original_horizon"


def test_source_no_leak_and_blocked_94_exclusion_hold() -> None:
    builder = load_builder()
    t3 = builder.load_t3_artifacts()
    audit = builder.source_hash_and_noleak_audit(t3)

    assert audit["status"] == "PASS"
    assert audit["decision"] == "ACCEPT_SOURCE_HASH_AND_NOLEAK_BOUNDARY"
    assert audit["forbidden_packet_key_hits"] == {}
    assert audit["boundary_scan"]["blocked_94_status_pass"] is True
    assert audit["blocked_94_exclusion"]["blocked_rows"] == 94
    assert audit["blocked_94_exclusion"]["packet_rows_from_blocked_set"] == []
    assert all(item["status"] == "PASS" for item in audit["consumed_tick_file_hash_checks"])


def test_duplicate_sample_floor_blocks_validation_not_research() -> None:
    builder = load_builder()
    t3 = builder.load_t3_artifacts()
    audit = builder.duplicate_samplefloor_audit(t3)

    assert audit["status"] == "PASS"
    assert audit["packet_row_count"] == 6
    assert audit["unique_duplicate_groups"] == 1
    assert audit["countable_denominator_rows"] == 2
    assert audit["sample_floor_for_validation_met"] is False
    assert "blocks validation and promotion" in audit["promotion_block"]


def test_298_blockers_and_next_route_are_exact() -> None:
    builder = load_builder()
    t3 = builder.load_t3_artifacts()
    inventory = builder.inventory_coverage_audit(t3)
    ledger = builder.blocker_and_route_ledger(t3, inventory)

    assert ledger["status"] == "PASS"
    assert ledger["blocker_count"] == 298
    assert ledger["exactness_checks"]["blockers_match_noneligible_inventory_ids"] is True
    assert ledger["exactness_checks"]["no_blocker_extended_tick_scan"] is True
    assert ledger["first_next_lane"]["route"] == "SEPARATE_NO_FILL_STILL_PENDING_LIFECYCLE_CONTRACT"
    assert "CNR_T1_FIXED_R_FROM_EXECUTABLE_QUOTE_PACKET" in {
        item["route"] for item in ledger["route_decision_ledger"]
    }


def test_generated_json_preserve_research_boundaries() -> None:
    forbidden = {
        "synthetic_r",
        "broker_actual_r",
        "account_history",
        "live_order_state",
        "hidden_path_label",
    }
    for path in BASE.glob(f"G12_CNR_T3_*_{DATE}.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT", path.name
        assert payload["validation_safe"] is False, path.name
        assert payload["outcome_review_opened"] is False, path.name
        assert payload["live_effect"] is False, path.name
        assert payload["broker_actual_r_accessed"] is False, path.name
        assert payload["account_history_accessed"] is False, path.name
        assert payload["live_trade_results_accessed"] is False, path.name
        assert payload["live_order_state_accessed"] is False, path.name
        assert payload["paid_data_calls"] == 0, path.name
        assert payload["databento_calls"] == 0, path.name
        assert payload["mt5_order_calls"] == 0, path.name
        assert payload["mt5_account_calls"] == 0, path.name
        if "LIFECYCLE_PACKET_AUDIT" in path.name:
            assert not (set(walk_keys(payload)) & forbidden)


def test_completion_checklist_and_prompt_pack_cover_stop_conditions() -> None:
    completion = load_json(f"G12_CNR_T3_COMPLETION_AUDIT_{DATE}.json")
    checklist = {item["requirement"]: item["status"] for item in completion["prompt_to_artifact_checklist"]}
    for requirement in [
        "304_row_inventory_coverage",
        "six_eligible_rows",
        "298_exact_blockers",
        "frozen_contract_before_scan",
        "source_hashes",
        "94_blocked_row_exclusion",
        "next_route_guidance",
    ]:
        assert requirement in checklist
        assert checklist[requirement].startswith("PASS"), requirement

    prompt = (BASE / f"G12_CNR_T3_NEXT_PROMPT_PACK_{DATE}.md").read_text(encoding="utf-8")
    assert "SEPARATE_NO_FILL_STILL_PENDING_LIFECYCLE_CONTRACT_V1" in prompt
    assert "do not compute R/performance" in prompt
    assert "No 94 blocked-row scoring" in prompt
    assert "NO_PROMOTION_VERDICT" in prompt
