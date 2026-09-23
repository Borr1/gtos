from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-10"
PREFIX = "G0_NOFILL_HIST_SRCEXP_SYNTHESIS"
BUILDER_PATH = ROUTE_DIR / "build_g0_nofill_historical_source_expansion_packet_synthesis_control_review_2026_05_10.py"
VERIFIER_PATH = ROUTE_DIR / "verify_g0_nofill_historical_source_expansion_packet_synthesis_control_review_2026_05_10.py"


def _load_json(name: str):
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_decision_reconciles_required_counts_hash_and_next_route() -> None:
    builder = _load_module(BUILDER_PATH, "g0_src_exp_builder_decision")
    decision = _load_json(f"{PREFIX}_DECISION_LEDGER_{DATE}.json")

    assert decision["terminal_decision"] == builder.TERMINAL_DECISION
    assert decision["accepted_upstream_counts"]["admitted_source_bound_rows"] == 2
    assert decision["accepted_upstream_counts"]["blocked_rows"] == 37
    assert decision["accepted_upstream_counts"]["rejected_rows"] == 9
    assert decision["accepted_upstream_counts"]["duplicate_denominators"] == "2/2/2"
    assert decision["accepted_upstream_counts"]["repaired_packet_hash"] == builder.EXPECTED_PACKET_SHA
    assert decision["next_route_selected"] == "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE"


def test_catalog_refresh_and_evidence_chain_are_source_control_only() -> None:
    builder = _load_module(BUILDER_PATH, "g0_src_exp_builder_catalog")
    catalog = _load_json(f"{PREFIX}_CATALOG_REFRESH_LEDGER_{DATE}.json")
    evidence = _load_json(f"{PREFIX}_EVIDENCE_CHAIN_RECONCILIATION_{DATE}.json")

    assert catalog["catalog_row_count"] == 1200
    assert catalog["hash_manifest_hashed_file_count"] == 1076
    assert catalog["hash_manifest_large_file_deferral_count"] == 124
    assert catalog["blocker_implications"]["blockers_with_non_generatable_source_state_gap"] == 37
    assert "not_validation_safe" in catalog["catalog_presence_policy"]
    assert evidence["packet_hash"]["g12_packet_sha256_recomputed"] == builder.EXPECTED_PACKET_SHA
    assert evidence["closed_validation_gates"]["g12_future_route_validation_execution_remains_closed"] is True
    assert evidence["closed_validation_gates"]["g12_future_route_scoring_remains_closed"] is True


def test_all_blockers_have_terminal_classes_catalog_evidence_and_actions() -> None:
    ledger = _load_json(f"{PREFIX}_BLOCKER_ROUTE_LEDGER_{DATE}.json")

    assert ledger["blocked_row_count"] == 37
    assert len(ledger["rows"]) == 37
    assert ledger["action_class_counts"]["NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"] == 37
    for row in ledger["rows"]:
        assert row["terminal_route_class"]
        assert row["exact_next_action"]
        assert row["can_enter_clean_source_packet_now"] is False
        evidence = row["catalog_search_evidence"]
        assert "market_data_tick_match_count" in evidence
        assert evidence["source_state_catalog_applicability"] == "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE"
        assert evidence["source_state_catalog_reason"]
        assert evidence["pending_lifecycle_audit_row_found"] is True


def test_rejects_duplicates_validation_gap_and_parallelization_are_closed() -> None:
    reject = _load_json(f"{PREFIX}_REJECT_LEARNING_LEDGER_{DATE}.json")
    duplicate = _load_json(f"{PREFIX}_DUPLICATE_DENOMINATOR_CONTAMINATION_REVIEW_{DATE}.json")
    sealed = _load_json(f"{PREFIX}_SEALED_VALIDATION_READINESS_GAP_LEDGER_{DATE}.json")
    parallel = _load_json(f"{PREFIX}_PARALLELIZATION_DECISION_LEDGER_{DATE}.json")

    assert reject["rejected_row_count"] == 9
    assert len(reject["rows"]) == 9
    assert set(row["terminal_route_class"] for row in reject["rows"]) == {
        "PERMANENT_CLEAN_DENOMINATOR_EXCLUSION_CONTAMINATION_OR_EMBARGO"
    }
    assert duplicate["duplicate_denominators"] == "2/2/2"
    assert duplicate["row_level_count"] == 2
    assert duplicate["primary_duplicate_denominator_unique_count"] == 2
    assert duplicate["secondary_duplicate_denominator_unique_count"] == 2
    assert sealed["validation_ready"] is False
    assert sealed["sample_size_status"] == "INSUFFICIENT_SOURCE_CONTROL_ROWS_FOR_VALIDATION"
    assert parallel["decision"] == "ONE_BOTTLENECK_ROUTE_FIRST"


def test_next_route_prompt_and_completion_audit_are_exact() -> None:
    ranking = _load_json(f"{PREFIX}_SOURCE_EXPANSION_OPPORTUNITY_RANKING_{DATE}.json")
    completion = _load_json(f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json")
    prompt = (ROUTE_DIR / f"{PREFIX}_NEXT_ROUTE_PROMPT_PACK_{DATE}.md").read_text(encoding="utf-8")

    assert ranking["ranked_routes"][0]["route_id"] == "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE"
    assert ranking["ranked_routes"][0]["expected_terminal_decisions"]
    assert completion["can_mark_goal_complete"] is True
    assert completion["completion_standard_satisfied"] is True
    assert completion["missing_incomplete_or_weak_requirements"] == []
    assert "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE" in prompt
    assert "NO_PROMOTION_VERDICT" in prompt
    assert "validation_safe=false" in prompt
    assert "outcome_review_opened=false" in prompt
    assert "live_effect=false" in prompt


def test_verifier_accepts_current_route_package() -> None:
    verifier = _load_module(VERIFIER_PATH, "g0_src_exp_verifier")
    result = verifier.verify()

    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
    assert result["terminal_decision"] == "ACCEPT_WITH_EXACT_SOURCE_EXPANSION_OR_CATALOG_REFRESH_FOLLOWUPS"
    assert result["admitted_rows"] == 2
    assert result["blockers"] == 37
    assert result["rejects"] == 9
    assert result["duplicate_denominators"] == "2/2/2"
    assert result["catalog_rows"] == 1200
    assert result["catalog_hash_count"] == 1076
    assert result["catalog_large_deferrals"] == 124
