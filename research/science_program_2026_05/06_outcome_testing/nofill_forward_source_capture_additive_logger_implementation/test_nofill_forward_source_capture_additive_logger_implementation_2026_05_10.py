"""Focused tests for the NOFILL source-capture additive logger implementation package."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build_nofill_forward_source_capture_additive_logger_implementation_2026_05_10 as builder
import verify_nofill_forward_source_capture_additive_logger_implementation_2026_05_10 as verifier
from src.research_infra import forward_capture as fc

DATE = "2026-05-10"


def _json(name: str) -> dict:
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def test_required_artifacts_exist_after_builder() -> None:
    builder.main()
    missing = [name for name in builder.REQUIRED_ARTIFACTS if not (BASE / name).exists()]
    assert missing == []


def test_coverage_ledger_matches_runtime_contract_and_design() -> None:
    builder.main()
    coverage = _json(f"NOFILL_FORWARD_SOURCE_CAPTURE_55_FIELD_IMPLEMENTATION_COVERAGE_LEDGER_{DATE}.json")

    assert coverage["implemented_field_count"] == 55
    assert coverage["future_logger_field_count"] == 20
    assert coverage["field_name_match"] is True
    assert coverage["all_55_implemented_or_fail_closed"] is True
    assert set(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS) == {
        row["field_name"] for row in coverage["fields"]
    }


def test_no_leak_audit_rejects_raw_secret_leakage() -> None:
    builder.main()
    audit = _json(f"NOFILL_FORWARD_SOURCE_CAPTURE_NOLEAK_REDACTION_AUDIT_{DATE}.json")

    assert audit["audit_passed"] is True
    assert audit["leaked_secret_markers"] == []
    assert audit["forbidden_output_keys"] == []
    assert audit["raw_value_hashing_allowed"] is False
    assert audit["redaction_status_fields"]["forbidden_field_scan_status"] == "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED"


def test_safe_flags_remain_closed_in_all_json_artifacts() -> None:
    builder.main()
    for path in BASE.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("promotion_verdict") == "NO_PROMOTION_VERDICT"
        assert data.get("validation_safe") is False
        assert data.get("outcome_review_opened") is False
        assert data.get("live_effect") is False


def test_verifier_accepts_current_package() -> None:
    builder.main()
    assert verifier.main() == 0
    result = _json(f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_VERIFICATION_RESULT_{DATE}.json")
    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
