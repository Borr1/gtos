from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT"
DATE = "2026-05-10"
BUILDER_PATH = ROUTE_DIR / "build_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.py"
VERIFIER_PATH = ROUTE_DIR / "verify_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.py"


def _load_json(name: str):
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_three_prior_hash_blockers_are_closed() -> None:
    builder = _load_module(BUILDER_PATH, "g12_hash_reaudit_builder_light")
    closure = _load_json(f"{PREFIX}_EXACT_BLOCKER_CLOSURE_REAUDIT_{DATE}.json")

    assert closure["audit_passed"] is True
    assert closure["closed_requirement_count"] == 3
    assert {record["role"] for record in closure["records"]} == set(builder.EXPECTED_HASHES)
    for record in closure["records"]:
        assert record["current_recomputed_sha256"] == builder.EXPECTED_HASHES[record["role"]]
        assert record["target_manifest_sha256"] == record["current_recomputed_sha256"]
        assert record["closed"] is True


def test_target_source_manifest_and_packet_parser_hashes_are_current() -> None:
    builder = _load_module(BUILDER_PATH, "g12_hash_reaudit_builder_source")
    audit = _load_json(f"{PREFIX}_SOURCE_HASH_PARSER_HASH_RECOMPUTATION_AUDIT_{DATE}.json")

    assert audit["audit_passed"] is True
    assert audit["strict_hash_mismatch_count"] == 0
    assert audit["parser_asof_hash"] == builder.EXPECTED_HASHES["parser_or_verifier:builder"]
    assert audit["packet_parser_code_hashes"] == [builder.EXPECTED_HASHES["parser_or_verifier:builder"]]
    assert audit["checks"]["repair_recomputed_source_manifest_reports_zero_mismatches"] is True


def test_packet_semantics_counts_and_duplicates_are_unchanged() -> None:
    builder = _load_module(BUILDER_PATH, "g12_hash_reaudit_builder_semantic")
    audit = _load_json(f"{PREFIX}_SEMANTIC_NO_ROW_CHANGE_REAUDIT_{DATE}.json")

    assert audit["audit_passed"] is True
    assert audit["observed_row_identities"] == builder.EXPECTED_ROWS
    assert audit["target_admission_counts"]["admitted_packet_row_count"] == 2
    assert audit["target_admission_counts"]["blocked_candidate_count"] == 37
    assert audit["target_admission_counts"]["rejected_candidate_count"] == 9
    assert audit["duplicate_denominators"] == builder.EXPECTED_DUPLICATES
    assert audit["checks"]["repair_semantic_ledger_proves_hash_only_change"] is True


def test_packet_hash_and_verifier_reruns_pass() -> None:
    builder = _load_module(BUILDER_PATH, "g12_hash_reaudit_builder_packet")
    packet = _load_json(f"{PREFIX}_PACKET_HASH_MANIFEST_REAUDIT_{DATE}.json")
    target = _load_json(f"{PREFIX}_TARGET_VERIFIER_TEST_RERUN_AUDIT_{DATE}.json")
    repair = _load_json(f"{PREFIX}_REPAIR_VERIFIER_TEST_RERUN_AUDIT_{DATE}.json")

    assert packet["audit_passed"] is True
    assert packet["packet_sha256_recomputed"] == builder.EXPECTED_PACKET_SHA
    assert target["audit_passed"] is True
    assert target["checks"]["target_verifier_passed"] is True
    assert target["checks"]["target_focused_pytest_passed"] is True
    assert repair["audit_passed"] is True
    assert repair["checks"]["repair_verifier_passed"] is True
    assert repair["checks"]["repair_focused_pytest_passed"] is True


def test_safe_flags_future_route_and_completion_are_closed() -> None:
    noleak = _load_json(f"{PREFIX}_NOLEAK_SAFE_FLAG_LIVE_SURFACE_AUDIT_{DATE}.json")
    future = _load_json(f"{PREFIX}_FUTURE_ROUTE_ELIGIBILITY_LEDGER_{DATE}.json")
    completion = _load_json(f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json")
    prompt = (ROUTE_DIR / f"{PREFIX}_NEXT_ROUTE_PROMPT_PACK_{DATE}.md").read_text(encoding="utf-8")

    assert noleak["audit_passed"] is True
    assert noleak["safe_flag_issue_count"] == 0
    assert noleak["forbidden_packet_key_hit_count"] == 0
    assert future["accepted_for_next_evidence_class_prompt"] is True
    assert future["validation_execution_remains_closed"] is True
    assert completion["completion_standard_satisfied"] is True
    assert completion["can_mark_goal_complete"] is True
    assert "NO_PROMOTION_VERDICT" in prompt
    assert "validation_safe=false" in prompt
    assert "outcome_review_opened=false" in prompt
    assert "live_effect=false" in prompt


def test_verifier_accepts_current_g12_hash_reaudit_package() -> None:
    verifier = _load_module(VERIFIER_PATH, "g12_hash_reaudit_verifier")
    result = verifier.verify()

    assert result["ok"] is True
    assert result["terminal_decision"] == "ACCEPT_REPAIRED_SOURCE_CONTROL_PACKET_FOR_NEXT_EVIDENCE_CLASS_PROMPT"
    assert result["packet_row_count"] == 2
    assert result["blocked_candidate_count"] == 37
    assert result["rejected_candidate_count"] == 9
    assert result["duplicate_denominators"] == "2/2/2"
    assert result["remaining_exact_repair_blocker_count"] == 0
