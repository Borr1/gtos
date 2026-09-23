"""Focused tests for the blocked-17 LTF/orderflow/proxy G12 audit."""

from __future__ import annotations

import json
from pathlib import Path

import build_g12_scid_ltf_proxy_blocked17_source_status_audit_2026_05_12 as builder
import verify_g12_scid_ltf_proxy_blocked17_source_status_audit_2026_05_12 as verifier


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-12"


def read_json(name: str):
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def test_denominator_recomputes_exact_blocked17_from_g0_ledger():
    payloads = builder.target_payloads()
    audit = builder.build_denominator_audit(payloads)
    assert audit["ok"], audit
    assert len(audit["included_card_ids"]) == 17
    assert len(audit["excluded_blocked15_card_ids"]) == 15
    assert len(audit["ready_8_excluded_card_ids"]) == 8
    assert audit["checks"]["expansion_denominator_untouched"] is True
    assert "ADV-002" in audit["included_card_ids"]
    assert "ADV-004" in audit["excluded_blocked15_card_ids"]


def test_source_status_audit_requires_exact_fields_and_non_vague_statuses():
    payloads = builder.target_payloads()
    audit = builder.build_source_status_audit(payloads)
    assert audit["ok"], audit["failures"]
    assert audit["card_count"] == 17
    assert audit["required_status_families_present"]["SOURCE_EXISTS_NEEDS_PARSER"] is True
    assert audit["required_status_families_present"]["PROXY_VALIDITY_REQUIRES_CONTRACT"] is True
    assert audit["required_status_families_present"]["NON_GENERATABLE_HISTORICAL_SOURCE_STATE"] is True
    assert all(row["fields_match_g0_exact_missing_list"] for row in audit["per_card_rows"])


def test_source_inventory_and_proxy_hash_audits_preserve_non_equivalence():
    payloads = builder.target_payloads()
    inventory = builder.build_search_inventory_audit(payloads)
    proxy = builder.build_proxy_hash_asof_audit(payloads)
    noleak = builder.build_noleak_audit(payloads)
    assert inventory["ok"], inventory["failures"]
    assert inventory["source_inventory_count"] >= 100
    assert "sierrachart_data_root" in inventory["required_roots_present"]
    assert proxy["ok"], proxy["failures"]
    assert proxy["broker_native_cfd_truth_claims"] == 0
    assert proxy["proxy_rows_context_only"] >= 1
    assert noleak["ok"], noleak["failures"]


def test_completion_and_decision_accept_source_status_only():
    payloads = builder.target_payloads()
    audits = {
        "denominator": builder.build_denominator_audit(payloads),
        "artifacts": builder.build_artifact_audit(payloads),
        "source_status": builder.build_source_status_audit(payloads),
        "search_inventory": builder.build_search_inventory_audit(payloads),
        "proxy_hash_asof": builder.build_proxy_hash_asof_audit(payloads),
        "noleak": builder.build_noleak_audit(payloads),
    }
    decision = builder.build_decision_ledger(audits)
    completion = builder.build_completion_audit(audits, decision)
    assert decision["terminal_decision"] == "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY"
    assert decision["terminal_blockers"] == []
    assert completion["completion_standard_satisfied"] is True
    assert completion["validation_safe"] is False
    assert completion["outcome_review_opened"] is False
    assert completion["live_effect"] is False


def test_verifier_accepts_current_audit_when_focused_tests_marked():
    result = verifier.verify(source_route_focused_tests_ok=True, g12_audit_focused_tests_ok=True)
    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"] is True
    assert result["included_card_count_verified"] == 17
