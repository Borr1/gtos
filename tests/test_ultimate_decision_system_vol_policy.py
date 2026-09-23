from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KERNEL_PATH = (
    ROOT
    / "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
    / "ULTIMATE_DECISION_SYSTEM/ultimate_decision_kernel.py"
)


def _load_kernel():
    spec = importlib.util.spec_from_file_location("ultimate_decision_kernel_under_test", KERNEL_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    old_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = old_write_bytecode
    return module


def _metals_context(**overrides):
    ctx = {
        "instrument": "XAUUSD",
        "asset_class": "metals",
        "setup": "fvg_retest_continuation",
        "direction": "long",
        "ac60": 0.18,
        "vol_floor_ok": True,
        "trend_state": "bullish",
        "n_active": 2,
        "dd_frac": 0.0,
        "session": "london",
        "weekday": "Tue",
        "cost_r": 0.018,
    }
    ctx.update(overrides)
    return ctx


def test_low_vol_is_exit_geometry_tier_not_size_boost():
    kernel = _load_kernel()

    low = kernel.decide(_metals_context(atr_ratio=1.2))
    mid = kernel.decide(_metals_context(atr_ratio=1.5))

    assert low["action"] == "TAKE"
    assert mid["action"] == "TAKE"
    assert low["size_pct"] == mid["size_pct"] == 2.2
    assert not any("vol-confidence" in reason for reason in low["reasons"])
    assert any("deep fixed 4.0R" in reason for reason in low["reasons"])
    assert any("deep fixed 3.0R" in reason for reason in mid["reasons"])


def test_high_vol_cap_is_fail_closed_without_defensive_flag():
    kernel = _load_kernel()

    high = kernel.decide(_metals_context(atr_ratio=1.9))

    assert high["action"] == "STAND_ASIDE"
    assert high["size_pct"] == 0.0
    assert any("VOL_CAP" in reason and "atr_ratio>=1.8" in reason for reason in high["reasons"])
