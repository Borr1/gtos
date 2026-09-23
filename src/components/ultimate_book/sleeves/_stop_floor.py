"""The exact stop-floor expression already used by three legacy generators.

This is an identity-only refactor. It does not authorize a floor on any additional sleeve,
add validation, or establish an economic, promotion, or full-flow claim.
"""

from __future__ import annotations

__all__ = ["DEFAULT_ATR_STOP_FLOOR", "floor_stop"]

#: Existing value from metals, metals_ob_micro, and structural_retest.
DEFAULT_ATR_STOP_FLOOR = 0.25


def floor_stop(raw: float, atr: float, floor_atr: float = DEFAULT_ATR_STOP_FLOOR) -> float:
    """Return the legacy expression without coercion, validation, or exception handling."""
    return max(raw, floor_atr * atr)
