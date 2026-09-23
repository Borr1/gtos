#!/usr/bin/env python3
"""Focused tests for READY8 fail-closed source repair artifacts."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
VERIFY_PATH = ROUTE_DIR / "verify_ready8_fail_closed_path_horizon_source_repair_2026_05_15.py"


def load_verifier():
    spec = importlib.util.spec_from_file_location("ready8_fail_closed_verifier", VERIFY_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_verifier_ok():
    module = load_verifier()
    result = module.verify()
    assert result["ok"], result["issues"]


def test_repair_counts_are_exact():
    module = load_verifier()
    result = module.verify()
    counts = result["counts"]
    assert counts["inventory_rows"] == 35811
    assert counts["repaired_bar_rows"] == 220
    assert counts["repaired_target_rows"] == 5320
    assert counts["inventory_counter"]["TARGET_FAIL_CLOSED_NOT_COMPUTABLE"] == 30560
    assert counts["inventory_counter"]["ROLE_FAIL_CLOSED_COMPUTABLE_EXCLUDED"] == 5251


def test_safe_flags_and_next_gate():
    module = load_verifier()
    checks = module.verify()["checks"]
    assert checks["safe_flags_ok"]
    assert checks["next_g12_prompt_exists"]
    assert checks["no_top_n_claimed"]
