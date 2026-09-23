"""Tests for prop-firm profile overlay mechanism.

Validates that:
  1. No profile specified = base config preserved (backward compat).
  2. ftmo profile keeps 2.0% risk (FTMO baseline).
  3. redacted_account profile sets 1.0% risk + 0.25% reduced risk.
  4. Profile overlays apply BEFORE instrument overrides (correct layering).
  5. resolve_profile precedence: CLI arg > env var > None.
  6. Unknown profile raises ValueError.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from src.utils.config import (
    PROFILE_ENV_VAR,
    apply_instrument_overrides,
    apply_profile_overrides,
    resolve_profile,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_CONFIG_PATH = REPO_ROOT / "config" / "agent_config.yaml"


def _load_base_config() -> dict:
    with open(BASE_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── apply_profile_overrides ──────────────────────────────────


def test_no_profile_returns_config_unchanged():
    cfg = _load_base_config()
    base_risk = cfg["risk"]["risk_per_trade_pct"]
    result = apply_profile_overrides(cfg, None)
    assert result["risk"]["risk_per_trade_pct"] == base_risk


def test_empty_string_profile_returns_config_unchanged():
    cfg = _load_base_config()
    base_risk = cfg["risk"]["risk_per_trade_pct"]
    result = apply_profile_overrides(cfg, "")
    assert result["risk"]["risk_per_trade_pct"] == base_risk


def test_ftmo_profile_sets_2pct_risk():
    cfg = _load_base_config()
    result = apply_profile_overrides(cfg, "ftmo")
    assert result["risk"]["risk_per_trade_pct"] == 2.0
    assert result["drawdown_reduction"]["reduced_risk_pct"] == 0.5
    assert result["profile_name"] == "ftmo"


def test_redacted_account_profile_sets_2pct_risk():
    """S79 (commit 9549928, CEO-approved 2026-04-27): FN base risk raised
    1.0% → 2.0% per uniform_fn 2.0% bootstrap-MC verdict (+25.8pp P(pass)
    Phase 1). reduced_risk_pct preserves H29 25%-of-nominal defensive
    posture: half of 2.0% = 0.5% (was 0.25% under 1.0% baseline).
    """
    cfg = _load_base_config()
    result = apply_profile_overrides(cfg, "redacted_account")
    assert result["risk"]["risk_per_trade_pct"] == 2.0
    assert result["drawdown_reduction"]["reduced_risk_pct"] == 0.5
    assert result["profile_name"] == "redacted_account"
    assert result["risk"]["max_concurrent"] is None
    assert result["risk"]["max_concurrent_policy"] == (
        "disabled_for_vnext_selected_cell_aggregate_drawdown_budget"
    )
    assert "aggregate_drawdown_budget_not_trade_count" in result["risk"]["risk_policy_source"]


def test_redacted_account_preserves_unrelated_base_fields():
    """Profile overlay only touches risk + drawdown. Other sections untouched."""
    cfg = _load_base_config()
    base_min_rr = cfg["risk"]["min_rr"]
    base_model = cfg["ai"]["primary_model"]
    base_memory = cfg.get("session_memory_enabled", False)

    result = apply_profile_overrides(cfg, "redacted_account")
    assert result["risk"]["min_rr"] == base_min_rr
    assert result["ai"]["primary_model"] == base_model
    assert result.get("session_memory_enabled", False) == base_memory


def test_denominator_capture_research_profile_is_capture_only():
    cfg = _load_base_config()
    result = apply_profile_overrides(cfg, "denominator_capture_research")

    capture = result["denominator_forward_capture_contract"]
    assert result["profile_name"] == "denominator_capture_research"
    assert result["deployment"]["phase"] == 1
    assert result["trading_enabled"] is False
    assert result["runtime"]["broker_account_namespace"] == "denominator_capture_research"
    assert result["runtime_paths"]["shadow_logs_root"] == (
        "shadow_logs/denominator_capture_research"
    )
    assert capture["enabled"] is True
    assert capture["log_enabled"] is True
    assert capture["log_path"] == (
        "shadow_logs/denominator_capture_research/denominator_forward_capture.jsonl"
    )
    assert capture["requirement_families"] == [
        "pending_created_exact_decision_time",
        "m15_grid_order_lifecycle",
    ]


def test_unknown_profile_raises_valueerror():
    cfg = _load_base_config()
    with pytest.raises(ValueError, match="Unknown profile"):
        apply_profile_overrides(cfg, "not_a_real_firm")


def test_profile_overlay_applied_before_instrument_overrides():
    """Instrument overrides (per-symbol) should NOT undo profile risk setting.

    Profile layer sets global risk_per_trade_pct. Instrument layer typically
    only overrides market/risk/m5_refinement per-symbol fields like
    contract_size or sl_buffer_dollars — not risk_per_trade_pct.

    GBPUSD has no per-instrument risk_per_trade_pct override under FN, so
    it inherits the FN base of 2.0% (S79, commit 9549928).
    """
    cfg = _load_base_config()
    profiled = apply_profile_overrides(cfg, "redacted_account")
    final = apply_instrument_overrides(profiled, "GBPUSD")

    assert final["risk"]["risk_per_trade_pct"] == 2.0
    assert final["risk"]["max_concurrent"] is None
    assert final["risk"]["max_concurrent_policy"] == (
        "disabled_for_vnext_selected_cell_aggregate_drawdown_budget"
    )
    assert final["market"]["symbol"] == "GBPUSD"
    assert final["risk"]["contract_size"] == 100000


# ── US30 / US30_cash 2% explicit override under redacted_account ─────────────
#
# Originally added 2026-04-25 as 1% explicit override blocks (A10 audit
# Monday-blocker — without the blocks US30/US30_cash inherited the base
# 2.0%). S79 (commit 9549928, 2026-04-27) raised FN base to uniform_fn
# 2.0%; the per-instrument override blocks are preserved (now pinning at
# 2.0% which equals 1.0x the new base, preserving the Q4-25 ratio) so
# this layer's behavior remains explicit even though the value matches
# inherited base.


def test_redacted_account_us30_resolves_to_2pct():
    """US30 aliases to canonical US30_cash and resolves to 2% under redacted_account."""
    cfg = _load_base_config()
    profiled = apply_profile_overrides(cfg, "redacted_account")
    final = apply_instrument_overrides(profiled, "US30")
    assert final["risk"]["risk_per_trade_pct"] == 2.0
    assert final["market"]["symbol"] == "US30_cash"
    assert final["market"]["requested_symbol"] == "US30"
    assert final["market"]["mt5_symbol"] == "US30"


def test_redacted_account_us30_cash_resolves_to_2pct():
    """US30_cash (FTMO-broker symbol) must resolve to 2% under redacted_account.

    S79 (commit 9549928, 2026-04-27): explicit override block updated to
    2.0% (was 1.0% pre-S79). Preserves 1.0x base ratio under the new
    uniform_fn 2.0% baseline.
    """
    cfg = _load_base_config()
    profiled = apply_profile_overrides(cfg, "redacted_account")
    final = apply_instrument_overrides(profiled, "US30_cash")
    assert final["risk"]["risk_per_trade_pct"] == 2.0
    assert final["market"]["symbol"] == "US30_cash"


def test_redacted_account_us30_cash_preserves_other_instrument_fields():
    """Profile overlay must preserve current redacted_account US30 broker geometry.

    redacted_account uses native US30 contract geometry here, not the old base
    US30_cash fallback geometry.
    """
    cfg = _load_base_config()
    profiled = apply_profile_overrides(cfg, "redacted_account")
    final = apply_instrument_overrides(profiled, "US30_cash")
    assert final["risk"]["contract_size"] == 10
    assert final["market"]["contract_size"] == 10.0
    assert final["market"]["mt5_symbol"] == "US30"
    # Kill zones from base must still be present.
    assert "ny" in final["market"]["kill_zones"]


def test_ftmo_us30_cash_uses_account_specific_profile_risk():
    """FTMO US30 risk comes from the account-specific profile geometry."""
    cfg = _load_base_config()
    profiled = apply_profile_overrides(cfg, "ftmo")
    final = apply_instrument_overrides(profiled, "US30_cash")
    assert final["risk"]["risk_per_trade_pct"] == 1.0
    assert final["market"]["mt5_symbol"] == "US30.cash"


def test_no_profile_us30_cash_keeps_2pct_baseline():
    """Without any profile, US30_cash inherits the base 2% — the FN 1%
    override is profile-scoped, not a global policy change.
    """
    cfg = _load_base_config()
    final = apply_instrument_overrides(cfg, "US30_cash")
    assert final["risk"]["risk_per_trade_pct"] == 2.0


def test_redacted_account_xauusd_still_overridden_after_us30_addition():
    """Regression guard: XAUUSD per-instrument override under FN profile
    must NOT be disturbed by the US30/US30_cash blocks.

    S79 (commit 9549928, 2026-04-27): XAUUSD raised 0.5% → 1.0% to
    preserve the 0.5x-base ratio under the new uniform_fn 2.0% baseline
    (XAU/XAG remain a half-risk metals class).
    """
    cfg = _load_base_config()
    profiled = apply_profile_overrides(cfg, "redacted_account")
    final = apply_instrument_overrides(profiled, "XAUUSD")
    assert final["risk"]["risk_per_trade_pct"] == 1.0


# ── resolve_profile ──────────────────────────────────────────


def test_resolve_profile_explicit_wins_over_env(monkeypatch):
    monkeypatch.setenv(PROFILE_ENV_VAR, "redacted_account")
    assert resolve_profile("ftmo") == "ftmo"


def test_resolve_profile_falls_back_to_env(monkeypatch):
    monkeypatch.setenv(PROFILE_ENV_VAR, "redacted_account")
    assert resolve_profile(None) == "redacted_account"


def test_resolve_profile_returns_none_when_unset(monkeypatch):
    monkeypatch.delenv(PROFILE_ENV_VAR, raising=False)
    assert resolve_profile(None) is None


def test_resolve_profile_returns_none_for_empty_env(monkeypatch):
    monkeypatch.setenv(PROFILE_ENV_VAR, "")
    assert resolve_profile(None) is None


def test_resolve_profile_strips_whitespace(monkeypatch):
    monkeypatch.setenv(PROFILE_ENV_VAR, "  redacted_account  ")
    assert resolve_profile(None) == "redacted_account"


def test_resolve_profile_explicit_empty_string_falls_through(monkeypatch):
    """An explicit empty string should be treated as 'unset'."""
    monkeypatch.setenv(PROFILE_ENV_VAR, "redacted_account")
    assert resolve_profile("") == "redacted_account"
