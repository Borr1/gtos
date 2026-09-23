"""Focused tests for the Blocked17 orderflow/proxy G12 audit."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROUTE_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


build = load_module("g12_proxy_build_test", "build_g12_scid_blocked17_orderflow_proxy_contract_audit_2026_05_13.py")
verify_mod = load_module("g12_proxy_verify_test", "verify_g12_scid_blocked17_orderflow_proxy_contract_audit_2026_05_13.py")


def test_verifier_accepts_audit_without_writing() -> None:
    result = verify_mod.verify(write_result=False)
    assert result["ok"], result["failures"]
    assert result["terminal_decision"].startswith("ACCEPT_AS_G12")


def test_artifact_hash_audit_closes_only_prompt_manifest_drift() -> None:
    audit = build.read_json(build.ROUTE_DIR / f"{build.PREFIX}_ARTIFACT_HASH_AUDIT_{build.DATE}.json")
    assert audit["ok"] is True
    assert audit["strict_failure_count"] == 0
    assert audit["text_eol_equivalent_row_count"] == 5
    assert len(audit["same_g12_repairs_closed"]) == 1
    repair = audit["same_g12_repairs_closed"][0]
    assert repair["repair_status"] == "CLOSED_IN_G12_AUDIT_REHASH_PROJECTION"
    assert repair["old_manifest_sha256"] != repair["current_sha256"]


def test_source_family_contracts_fail_closed() -> None:
    audit = build.read_json(build.ROUTE_DIR / f"{build.PREFIX}_SOURCE_FAMILY_CONTRACT_AUDIT_{build.DATE}.json")
    assert audit["ok"] is True
    assert audit["contract_count"] == 4
    for row in audit["contract_rows"]:
        assert all(row["checks"].values()), row
        assert row["exact_access_requirement_if_unresolved"]


def test_equivalence_rows_are_context_only_and_non_equivalent() -> None:
    audit = build.read_json(build.ROUTE_DIR / f"{build.PREFIX}_EQUIVALENCE_NON_EQUIVALENCE_AUDIT_{build.DATE}.json")
    assert audit["ok"] is True
    assert audit["equivalence_row_count"] == 7
    for row in audit["rows"]:
        assert row["equivalence_status"] == "NON_EQUIVALENT_CONTEXT_OR_CONTROL_ONLY"
        assert row["checks"]["broker_cfd_truth_disallowed"] is True
        assert row["checks"]["may_score_results_now_false"] is True


def test_completion_audit_maps_all_prompt_requirements() -> None:
    completion = build.read_json(build.ROUTE_DIR / f"{build.PREFIX}_COMPLETION_AUDIT_{build.DATE}.json")
    assert completion["completion_standard_satisfied"] is True
    assert completion["missing_incomplete_or_weak_requirements"] == []
    checklist = {row["requirement"]: row for row in completion["prompt_to_artifact_checklist"]}
    for requirement in [
        "mandatory_preflight_and_context_reads",
        "exact_blocked17_denominator_preserved_other15_ready8_expansion_untouched",
        "artifact_hash_manifest_audit_and_same_g12_repair",
        "source_family_contracts_fail_closed",
        "proxy_equivalence_and_non_equivalence_context_only",
        "blockers_exact_not_vague_and_paid_free",
        "no_leak_safe_flags_and_forbidden_surface_closed",
        "verifier_and_focused_tests",
        "next_g0_or_g12_starter_if_accepted",
        "preserve_safe_posture",
    ]:
        assert checklist[requirement]["satisfied"] is True
