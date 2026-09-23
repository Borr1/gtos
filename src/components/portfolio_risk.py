"""Correlation-aware position sizing.

Before approving a CANDIDATE, checks if there is an open position on
a correlated instrument and reduces risk accordingly.

Correlation pairs are hard-coded from screening (design doc:
exports/multi_instrument/correlation_sizing_design.md).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from src.components.gtos_vnext_runtime import (
    normalize_vnext_symbol_key,
    resolve_vnext_symbol_family,
)

logger = logging.getLogger(__name__)


@dataclass
class CorrelationAdjustment:
    """Result of a correlation risk check."""
    adjusted: bool
    original_risk_pct: float
    final_risk_pct: float
    reason: str
    correlated_instrument: Optional[str] = None
    group_name: Optional[str] = None


# Default correlation groups — overridable via config
DEFAULT_CORRELATION_GROUPS = {
    "EUR_GBP": {
        "instruments": ["EURUSD", "GBPUSD"],
        "max_combined_risk_pct": 1.5,
    },
    "AUD_NZD": {
        "instruments": ["AUDUSD", "NZDUSD"],
        "max_combined_risk_pct": 1.5,
    },
    "US_INDICES": {
        "instruments": ["US30_cash", "US500", "NAS100"],
        "max_combined_risk_pct": 1.5,
    },
    "PRECIOUS_METALS": {
        "instruments": ["XAUUSD", "XAGUSD"],
        "max_combined_risk_pct": 1.5,
    },
    "JPY_CROSSES": {
        "instruments": ["USDJPY", "EURJPY", "GBPJPY"],
        "max_combined_risk_pct": 1.5,
    },
}

VNEXT_FAMILY_TO_PORTFOLIO_GROUP_SYMBOL = {
    "EURUSD_6E_FAMILY": "EURUSD",
    "GBPUSD_6B_FAMILY": "GBPUSD",
    "NAS100_NQ_FAMILY": "NAS100",
    "SPX500_ES_FAMILY": "US500",
    "US30_YM_FAMILY": "US30_cash",
    "USDJPY_6J_FAMILY": "USDJPY",
    "XAGUSD_SILVER_FAMILY": "XAGUSD",
    "XAUUSD_GC_FAMILY": "XAUUSD",
}

SYMBOL_ALIASES = {
    "US30": "US30_cash",
    "US30_CASH": "US30_cash",
    "US30.cash": "US30_cash",
    "US500": "US500",
    "US500_CASH": "US500",
    "US500.cash": "US500",
    "SPX500": "US500",
}


def _canonical_group_symbol(symbol: str) -> str:
    """Normalize broker/proxy/futures aliases for correlation groups."""
    if not symbol:
        return symbol
    family = resolve_vnext_symbol_family(symbol)
    if family in VNEXT_FAMILY_TO_PORTFOLIO_GROUP_SYMBOL:
        return VNEXT_FAMILY_TO_PORTFOLIO_GROUP_SYMBOL[family]
    key = normalize_vnext_symbol_key(symbol)
    return SYMBOL_ALIASES.get(symbol) or SYMBOL_ALIASES.get(key) or symbol


def check_correlation_risk(
    symbol: str,
    base_risk_pct: float,
    open_positions: list[dict],
    config: dict | None = None,
) -> CorrelationAdjustment:
    """Check if the new trade conflicts with open correlated positions.

    Args:
        symbol: The instrument we want to trade (e.g. "GBPJPY")
        base_risk_pct: The normal risk per trade (e.g. 1.0)
        open_positions: List of dicts with at minimum {"symbol": str, "risk_pct": float}
        config: Full agent config — looks for "correlation_groups" key

    Returns:
        CorrelationAdjustment with possibly reduced risk_pct
    """
    groups = _load_groups(config)

    if not open_positions:
        return CorrelationAdjustment(
            adjusted=False,
            original_risk_pct=base_risk_pct,
            final_risk_pct=base_risk_pct,
            reason="no_open_positions",
        )

    # Find which group(s) this symbol belongs to
    candidate_symbol = _canonical_group_symbol(symbol)
    for group_name, group_cfg in groups.items():
        instruments = group_cfg.get("instruments", [])
        canonical_instruments = {_canonical_group_symbol(item) for item in instruments}
        if candidate_symbol not in canonical_instruments:
            continue

        max_combined = group_cfg.get("max_combined_risk_pct", 1.5)

        # Check if any open position is in the same group
        for pos in open_positions:
            pos_symbol = pos.get("symbol", "")
            canonical_pos_symbol = _canonical_group_symbol(pos_symbol)
            if (
                canonical_pos_symbol in canonical_instruments
                and canonical_pos_symbol != candidate_symbol
            ):
                pos_risk = pos.get("risk_pct", base_risk_pct)

                # Calculate remaining budget for this group
                remaining = max_combined - pos_risk
                if remaining <= 0:
                    logger.warning(
                        "RISK_SKIP_CORRELATION: %s skipped — %s already at %.1f%% "
                        "(group %s max %.1f%%)",
                        symbol, pos_symbol, pos_risk, group_name, max_combined,
                    )
                    return CorrelationAdjustment(
                        adjusted=True,
                        original_risk_pct=base_risk_pct,
                        final_risk_pct=0.0,
                        reason=f"skip_correlated: {pos_symbol} at {pos_risk}% "
                               f"(group {group_name} max {max_combined}%)",
                        correlated_instrument=pos_symbol,
                        group_name=group_name,
                    )

                final_risk = round(min(base_risk_pct, remaining), 2)
                if final_risk < base_risk_pct:
                    logger.info(
                        "RISK_REDUCED_CORRELATION: %s %.1f%% -> %.1f%% "
                        "(%s position open, group %s)",
                        symbol, base_risk_pct, final_risk,
                        pos_symbol, group_name,
                    )
                    return CorrelationAdjustment(
                        adjusted=True,
                        original_risk_pct=base_risk_pct,
                        final_risk_pct=final_risk,
                        reason=f"reduced_correlated: {symbol} {base_risk_pct}% -> "
                               f"{final_risk}% ({pos_symbol} position open)",
                        correlated_instrument=pos_symbol,
                        group_name=group_name,
                    )

    return CorrelationAdjustment(
        adjusted=False,
        original_risk_pct=base_risk_pct,
        final_risk_pct=base_risk_pct,
        reason="no_correlation_conflict",
    )


def _load_groups(config: dict | None) -> dict:
    """Load correlation groups from config, falling back to defaults."""
    if config and "correlation_groups" in config:
        return config["correlation_groups"]
    return DEFAULT_CORRELATION_GROUPS
