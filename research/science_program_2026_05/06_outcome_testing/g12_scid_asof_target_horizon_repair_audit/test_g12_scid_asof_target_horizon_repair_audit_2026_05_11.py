from __future__ import annotations

import json
import sys
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROUTE_DIR))

import build_g12_scid_asof_target_horizon_repair_audit_2026_05_11 as builder


def load(name: str) -> dict:
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def test_counts_are_recomputed_from_packet_and_rowset_sources() -> None:
    builder.build_all()
    counts = load(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_COUNT_RECONCILIATION_{builder.DATE_TAG}.json")

    assert counts["pass"] is True
    assert counts["actual_counts"]["candidate_rows"] == 3014
    assert counts["actual_counts"]["sealed_rows"] == 2432
    assert counts["actual_counts"]["stress_rows"] == 582
    assert counts["actual_counts"]["discovery_exclusions"] == 365
    assert counts["actual_counts"]["denominator_groups"] == 7
    assert counts["actual_counts"]["known_families"] == 11


def test_family_matrix_keeps_strategy_families_non_executable() -> None:
    builder.build_all()
    family = load(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_FAMILY_MATRIX_REVIEW_{builder.DATE_TAG}.json")

    assert family["pass"] is True
    assert family["status_counts"] == {"CONTROL_ONLY": 4, "SOURCE_SAFE_NEUTRAL_TARGET_ONLY": 7}
    assert family["checks"]["no_family_strategy_executable"] is True


def test_rulebook_accepts_only_neutral_source_safe_targets() -> None:
    builder.build_all()
    rulebook = load(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_RULEBOOK_REVIEW_{builder.DATE_TAG}.json")

    assert rulebook["pass"] is True
    assert rulebook["horizon_set_m15_bars"] == [1, 4, 16, 32]
    assert rulebook["target_definition_count"] == 8
    assert rulebook["checks"]["all_target_defs_forbid_strategy_edge_interpretation"] is True
    assert rulebook["checks"]["side_rule_neutral"] is True


def test_source_field_contract_preserves_non_generatable_intent_boundary() -> None:
    builder.build_all()
    source = load(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_SOURCE_FIELD_CONTRACT_REVIEW_{builder.DATE_TAG}.json")

    assert source["pass"] is True
    assert source["checks"]["strategy_missing_fields_not_derivable_from_neutral_bars"] is True
    assert source["checks"]["strategy_derivation_attempts_exhaustive"] is True
    assert source["checks"]["strategy_expansion_requirements_exact"] is True


def test_decision_does_not_accept_validation_or_strategy_execution() -> None:
    builder.build_all()
    decision = load(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_DECISION_LEDGER_{builder.DATE_TAG}.json")

    assert decision["terminal_decision"] == "ACCEPT_AS_G12_SOURCE_SAFE_NEUTRAL_TARGET_RULEBOOK_CONTROL_EVIDENCE_ONLY"
    assert decision["accepted_source_safe_neutral_target_rulebook_only"] is True
    assert decision["accepted_strategy_family_execution"] is False
    assert decision["accepted_validation_execution"] is False
    assert decision["accepted_result_scoring"] is False
    assert decision["accepted_promotion"] is False
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False


def test_raw_blob_dirty_audit_is_scoped_and_non_blocking_for_unrelated_dirt() -> None:
    builder.build_all()
    audit = load(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_RAW_BLOB_DIRTY_STATE_{builder.DATE_TAG}.json")

    assert audit["raw_blob_audit_pass"] is True
    assert audit["scoped_dirty_state_pass"] is True
    assert isinstance(audit["dirty_state_ledger"], list)
