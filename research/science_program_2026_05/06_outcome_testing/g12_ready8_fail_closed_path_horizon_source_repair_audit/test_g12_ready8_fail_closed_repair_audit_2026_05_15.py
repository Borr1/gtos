#!/usr/bin/env python3
"""Focused tests for the G12 READY8 fail-closed source-repair audit."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
VERIFY_PATH = ROUTE_DIR / "verify_g12_ready8_fail_closed_repair_audit_2026_05_15.py"


def load_verifier():
    spec = importlib.util.spec_from_file_location("g12_ready8_fail_closed_verifier", VERIFY_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_verifier_accepts_audit_artifacts():
    module = load_verifier()
    result = module.verify(require_completion_tests=False)
    assert result["ok"], result["issues"]


def test_full_recomputation_ledgers_have_exact_counts():
    module = load_verifier()
    counts = module.verify(require_completion_tests=False)["counts"]
    assert counts["inventory_rows"] == 35_811
    assert counts["source_repaired_bar_rows"] == 220
    assert counts["target_repaired_rows"] == 5_320


def test_safe_flags_and_r7_rule_stay_closed():
    module = load_verifier()
    result = module.verify(require_completion_tests=False)
    checks = result["checks"]
    assert checks["decision_accepts"]
    assert checks["r7_may_consume_5320"]
    assert checks["remaining_fail_closed_exact"]
    assert checks["role_excluded_unchanged"]
    assert result["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert result["validation_safe"] is False
    assert result["outcome_review_opened"] is False
    assert result["live_effect"] is False
