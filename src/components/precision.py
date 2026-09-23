"""Precision-aware snapping helpers for the MSO-vs-AI display contract.

Single shared home for the two helpers introduced by HALLUC-1 (commit
``2c75f98``) so that downstream guards / verifiers can snap MSO underlying
floats to the same precision plane the AI was shown before performing
strict price comparisons.

Background
----------
The MSO renders OB.high / OB.low / FVG.bottom / FVG.top / breaker.zone_low /
breaker.zone_high to the AI at the instrument's ``prompt.price_format``
(e.g. ``.1f`` for NAS100, ``.2f`` for XAUUSD/US30/XAGUSD, ``.3f`` for JPY
pairs, ``.5f`` for FX). The AI then emits trade_parameters at that same
precision per the prompt's PRECISION + SELF-CHECK rules. Code-side
comparisons against the unrendered underlying floats break when the rendered
display value differs from the underlying — a sub-tick rendering delta forces
a deterministic guard violation even though the AI placed its emission "at
the edge" of what it was shown.

Concrete failure mode (NAS100 2026-04-27, HALLUC-1 forensic dump):

    OB.high underlying = 27262.16
    .1f rendering shown to AI = "27262.2"
    AI emits entry_price = 27262.2 (per spec — top of OB for LONG)
    Strict check:  27262.2 <= 27262.16  → False → deterministic DEMOTE

Sister bug class to ``project_eurusd_sl_root_cause`` and
``project_f12_us30_dual_mechanism_confirmed`` — same compound class
(MSO renders one precision, downstream checks another).

Helpers
-------
``_decimals_from_format(fmt)``
    Parse the decimal-place count from a Python format spec like ``.Nf``.
    Returns ``None`` for unrecognized formats (caller treats as "no
    snapping" and falls back to a safe default).

``_snap_to_precision(value, decimals)``
    Round ``value`` to ``decimals`` decimal places using ``ROUND_HALF_UP``
    via ``Decimal``. Matches Python f-string ``.Nf`` rendering closely
    enough for the intended use (display rendering for AI consumption).

The module is import-side-effect-free and contains no I/O.

Sites that consume this contract
--------------------------------
* ``primary_analyzer.guard_candidate_inconsistent_pois`` — HALLUC-1 (2c75f98).
* ``verification._check_entry_in_breaker`` — SISTER-1/2 (this branch).
* ``verification._check_entry_in_fvg`` — SISTER-4/5 (this branch).
* ``m5_refinement.refine_entry_m5`` — SISTER-3 (this branch; B-class
  hardcoded ``round(*, 2)`` replacement).
* ``verification._check_sl_beyond_ob`` — SISTER-consistency snap
  (2026-04-28 trending_bull-replay audit). Originally listed below
  as "safe by audit"; re-test found the ADR-006 tick-floor cannot
  absorb every rendering delta — the default 1-tick floor and
  tight-FX 5-8-tick floor both leave residual edge cases when the
  underlying float carries an extra decimal beyond the AI's display
  plane. Now snaps MSO ``OrderBlock.low/high`` +
  ``BreakerBlock.zone_low/high`` to the AI's display plane before the
  floor-tolerance comparison, identical to the SISTER-1/2/4/5 pattern.

Sites confirmed safe (by audit, not code)
-----------------------------------------
* ``verification._check_entry_in_ob`` / ``_check_h1_poi_exists`` — use
  ``_ob_tolerance(price) = price × 0.002`` (0.2%), which dominates any
  rendering delta.
* ``permissions._find_target_ob`` — uses ``sl_buffer_dollars`` (instrument-
  specific) which dominates any rendering delta.
* ``execution.py`` — compares vs MT5 tick (broker reality), not MSO floats.

See ``research/sister_bug_audit_2026-04-27/AUDIT_REPORT.md`` for the
SISTER-1/2/3/4/5 audit and
``research/a4_trending_bull_replay_2026-04-28/`` for the trending_bull
replay cohort whose live L2-rejected trades surfaced the residual gap
that motivated this SISTER-consistency snap;
``.context/06_decisions/`` for the precision-contract ADR.
"""

from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

# Re-exported public surface — sites importing these helpers should use this
# module's symbols directly. ``primary_analyzer.py`` re-exports them as
# module-level aliases for backward compatibility with the HALLUC-1 test
# suite (tests/test_precision_aware_guards.py imports from primary_analyzer).
__all__ = ["_decimals_from_format", "_snap_to_precision"]


_PRICE_FORMAT_RE = re.compile(r"^\.(\d+)f$")


def _decimals_from_format(fmt: Optional[str]) -> Optional[int]:
    """Parse the decimal-place count from a Python format spec like ``.Nf``.

    Parameters
    ----------
    fmt
        A format specifier such as ``".1f"`` or ``".5f"``. ``None`` and
        unrecognized strings (including ``"%.2f"``, ``".f"``, ``"1f"``,
        and the empty string) return ``None``.

    Returns
    -------
    int | None
        The integer number of decimals, or ``None`` for unrecognized
        formats. Callers treat ``None`` as "no snapping" — falling back
        to a safe per-call default (typically ``.2f``).
    """
    if not fmt:
        return None
    m = _PRICE_FORMAT_RE.match(fmt.strip())
    if not m:
        return None
    return int(m.group(1))


def _snap_to_precision(value: float, decimals: int) -> float:
    """Round *value* to *decimals* decimal places using ``ROUND_HALF_UP``.

    Matches Python's f-string ``.Nf`` behavior closely enough for the
    intended use (rendering prices for AI display). We use ``Decimal`` to
    avoid binary-float-repr drift on edge cases like ``27262.15`` (which
    in IEEE-754 binary is slightly below 27262.15 — naive ``round`` would
    round-to-even and yield ``27262.1``; Decimal+ROUND_HALF_UP yields
    ``27262.2``, matching ``f"{27262.15:.1f}"``).

    A negative ``decimals`` value is a programming error in the caller's
    config; we return ``value`` unchanged rather than raising — the caller
    is in a hot path (live trading) and a no-op is safer than a crash.
    """
    if decimals < 0:
        return value
    quantum = Decimal(10) ** -decimals
    return float(Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP))
