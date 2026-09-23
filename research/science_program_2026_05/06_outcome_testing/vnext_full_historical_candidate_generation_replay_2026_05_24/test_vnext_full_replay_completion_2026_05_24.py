#!/usr/bin/env python3
"""Focused route-local test for the final vNext replay completion package."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def load_verifier():
    route_dir = Path(__file__).resolve().parent
    verifier_path = route_dir / "verify_vnext_full_replay_completion_2026_05_24.py"
    spec = importlib.util.spec_from_file_location("vnext_full_replay_completion_verifier", verifier_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_final_completion_package_verifies_from_disk():
    verifier = load_verifier()
    result = verifier.verify_outputs(write_result=False)
    assert result["status"] == "OK", result["failures"]
