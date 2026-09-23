from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
VERIFY_SCRIPT = ROUTE_DIR / "verify_g12_mac_inverse_avoid_filter_audit_2026_05_15.py"
RECOMPUTATION = ROUTE_DIR / "G12_MAC_INVERSE_AUDIT_RECOMPUTATION_LEDGER_2026-05-15.json"
DECISION = ROUTE_DIR / "G12_MAC_INVERSE_AUDIT_DECISION_LEDGER_2026-05-15.json"
DOOR_LEDGER = ROUTE_DIR / "G12_MAC_INVERSE_AUDIT_DOOR_BRANCH_LEDGER_2026-05-15.jsonl"
SOURCE_CANDIDATE = ROUTE_DIR / "MAC_INVERSE_AVOID_FILTER_CANDIDATE_DESIGN_LEDGER_2026-05-15.jsonl"
SOURCE_FAILURE = ROUTE_DIR / "MAC_INVERSE_FAILURE_ANATOMY_LEDGER_2026-05-15.jsonl"
SOURCE_FAIL_CLOSED = ROUTE_DIR / "MAC_INVERSE_FAIL_CLOSED_NON_APPLICABLE_LEDGER_2026-05-15.jsonl"
BLOCKER_LEDGER = ROUTE_DIR / "G12_MAC_INVERSE_AUDIT_BLOCKER_IMPOSSIBILITY_LEDGER_2026-05-15.jsonl"


def _load_verify_module():
    spec = importlib.util.spec_from_file_location("g12_mac_inverse_audit_verify", VERIFY_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _jsonl_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for line in handle if line.strip())


def test_g12_mac_inverse_audit_verifier_passes() -> None:
    result = _load_verify_module().verify()
    assert result["ok"], result["issues"]


def test_accepted_g12_pass_control_comparison_has_no_missing_or_mismatch() -> None:
    recomputation = json.loads(RECOMPUTATION.read_text(encoding="utf-8"))
    comparison = recomputation["pass_control_comparison"]
    assert comparison["accepted_delta_missing"] == 0
    assert comparison["accepted_delta_mismatch"] == 0
    assert comparison["accepted_delta_matches"] > 0
    assert comparison["accepted_full_row_missing"] == 0
    assert comparison["accepted_full_row_mismatch"] == 0
    assert comparison["accepted_full_row_matches"] == comparison["accepted_present_counts"]["True"]


def test_branch_and_blocker_ledgers_preserve_source_rows() -> None:
    door_rows = _jsonl_count(DOOR_LEDGER)
    source_candidate_rows = _jsonl_count(SOURCE_CANDIDATE)
    source_failure_rows = _jsonl_count(SOURCE_FAILURE)
    blocker_rows = _jsonl_count(BLOCKER_LEDGER)
    source_fail_closed_rows = _jsonl_count(SOURCE_FAIL_CLOSED)
    assert door_rows >= source_candidate_rows + source_failure_rows
    assert blocker_rows >= source_fail_closed_rows


def test_terminal_decision_preserves_safe_flags() -> None:
    decision = json.loads(DECISION.read_text(encoding="utf-8"))
    assert decision["terminal_decision"] == "ACCEPT_AS_G12_MAC_INVERSE_AVOID_FILTER_DESIGN_AUDIT_NO_PROMOTION"
    assert decision["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False
