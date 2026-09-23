from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
VERIFY_SCRIPT = ROUTE_DIR / "verify_mac001_mac004_inverse_avoid_filter_validation_design_2026_05_15.py"


def _load_verify_module():
    spec = importlib.util.spec_from_file_location("mac_inverse_verify", VERIFY_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_mac_inverse_route_verifier_passes() -> None:
    result = _load_verify_module().verify()
    assert result["ok"], result["issues"]


def test_required_mac_ledgers_exist() -> None:
    required = [
        "MAC_INVERSE_PASS_CONTROL_RECOMPUTATION_LEDGER_2026-05-15.jsonl",
        "MAC_INVERSE_LEAVE_ONE_STRESS_LEDGER_2026-05-15.jsonl",
        "MAC_INVERSE_AVOID_FILTER_CANDIDATE_DESIGN_LEDGER_2026-05-15.jsonl",
        "MAC_INVERSE_INTERACTION_LEDGER_2026-05-15.jsonl",
        "MAC_INVERSE_COMPLETION_AUDIT_2026-05-15.json",
    ]
    missing = [name for name in required if not (ROUTE_DIR / name).exists()]
    assert not missing
