"""A.2 direction-emission audit shadow logger — observation-only.

For every CANDIDATE the PrimaryAnalyzer emits, this logger appends a JSONL
row capturing the proposed trade direction relative to XAUUSD's D1
directional bias and the candidate instrument's static Pearson correlation
to XAU. Goal: 30+ days of live data to validate (or refute) the per-class
agent's class-bias finding (UK100 100% LONG, GER40 95% LONG, XAGUSD 17%
SHORT in the Q1-Q2-2026 backtest cohort) and gate Adapter A's ship
decision.

Why this matters
----------------
The per-class backtester surfaced what looks like a structural directional
skew on certain instruments, but the sample is small enough that prompt /
regime / data-window confounds are plausible. Shadow logging the live
emission distribution (no decision impact) gives the analyst a clean
empirical comparison set that is independent of the BT generator.

Hook point (orchestrator)
-------------------------
Called from ``src/components/orchestrator.py`` immediately after
``log_candidate_features`` runs and ONLY when the analyzer returned a
``CANDIDATE``. The cross-instrument context (``_ci_context_text`` +
``_xau_d1_direction_value``) is already populated by
``_compute_cross_instrument_context()`` at kill-zone entry, so the
``xau_d1_direction`` lookup is a property read.

Failure isolation
-----------------
Any exception during row construction or disk I/O is caught, logged at
WARNING level with traceback, and swallowed. Trading logic continues.
This logger is wholly independent of the orchestrator — it is the same
"additive shadow logger never breaks the pipeline" contract used by
``touch_count_gate_logger``, ``regime_shadow_logger``, and
``candidate_features_logger``.

Output
------
Append-only JSONL at ``shadow_logs/direction_emission_xau_audit.jsonl``.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.components.cross_instrument_correlation_gate import (
    lookup_correlation,
)

logger = logging.getLogger(__name__)

# Default sink. Tests must redirect by passing ``log_path`` (or by
# monkey-patching this module's ``SHADOW_LOG_PATH`` constant — see
# ``tests/conftest.py::_isolate_direction_emission_log``).
SHADOW_LOG_PATH = "shadow_logs/direction_emission_xau_audit.jsonl"

# XAUUSD self-correlation sentinel: the static correlation matrix
# intentionally returns ``None`` for same-symbol lookups (so the
# cross-instrument-correlation gate doesn't double-count XAU's own
# position), but the audit row should record the trivially-true 1.0
# for XAU candidates so downstream stratification is uniform.
_XAU_SELF_CORRELATION: float = 1.0


def _resolve_correlation_to_xau(symbol: str) -> Optional[float]:
    """Return the static Pearson correlation of *symbol* to XAUUSD.

    XAUUSD itself returns ``1.0`` — see ``_XAU_SELF_CORRELATION``. Unknown
    instruments return ``None``; downstream consumers must filter.
    """
    if not symbol:
        return None
    if symbol.upper() == "XAUUSD":
        return _XAU_SELF_CORRELATION
    try:
        return lookup_correlation(symbol, "XAUUSD")
    except Exception as exc:  # noqa: BLE001 — must never raise into logger
        logger.debug(
            "direction_emission_logger: correlation lookup failed for %s: %s",
            symbol, exc,
        )
        return None


def _resolve_alignment(
    proposed_direction: Optional[str],
    xau_d1_direction: Optional[str],
) -> Optional[bool]:
    """Compute direction-aligned-with-XAU boolean.

    Truth table::

        LONG  + bullish  → True
        SHORT + bearish  → True
        LONG  + bearish  → False
        SHORT + bullish  → False
        anything else    → None

    The "unclear", "unavailable", or "disabled" XAU directions all map to
    ``None`` (analyst stratifies these as their own bucket). Likewise an
    unknown proposed_direction yields ``None``.
    """
    if proposed_direction not in ("LONG", "SHORT"):
        return None
    if xau_d1_direction not in ("bullish", "bearish"):
        return None
    if proposed_direction == "LONG" and xau_d1_direction == "bullish":
        return True
    if proposed_direction == "SHORT" and xau_d1_direction == "bearish":
        return True
    return False


def _safe_get(obj: Any, *names: str, default: Any = None) -> Any:
    """Defensive getter that swallows AttributeError + TypeError + KeyError.

    Returns ``default`` on the first failed access. Mirrors the pattern in
    ``candidate_features_logger._safe_get``.
    """
    for name in names:
        try:
            val = getattr(obj, name)
            if val is not None:
                return val
        except Exception:
            pass
        try:
            val = obj[name]  # type: ignore[index]
            if val is not None:
                return val
        except Exception:
            pass
    return default


def _extract_proposed_direction(pa_output: Any) -> Optional[str]:
    """Return ``"LONG"`` / ``"SHORT"`` from CANDIDATE trade_parameters.

    Returns ``None`` for non-CANDIDATE outputs or missing trade_parameters.
    """
    if pa_output is None:
        return None
    decision = _safe_get(pa_output, "decision")
    if decision != "CANDIDATE":
        return None
    tp = _safe_get(pa_output, "trade_parameters")
    if tp is None:
        return None
    direction = _safe_get(tp, "direction")
    if direction in ("LONG", "SHORT"):
        return direction
    return None


def _extract_framework(pa_output: Any) -> Optional[str]:
    framework = _safe_get(pa_output, "framework")
    if isinstance(framework, str) and framework:
        return framework
    return None


def _extract_confidence_score(pa_output: Any) -> Optional[int]:
    """Pull confidence_score off the analyzer output if present.

    The schema declares a default of 0; we preserve None when absent so
    downstream analysis can distinguish "not provided" from "scored 0".
    """
    if pa_output is None:
        return None
    val = _safe_get(pa_output, "confidence_score")
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _extract_kill_zone(
    session_state: Optional[dict],
    pa_output: Any,
) -> str:
    """Resolve the kill_zone label.

    Order of precedence:
      1. ``session_state["kill_zone"]`` if non-empty (orchestrator passes
         the active KZ explicitly).
      2. ``pa_output.kill_zone`` (schema constrained to "london"/"ny").
      3. ``"outside"`` sentinel — the candle was evaluated outside any KZ.

    Returns one of ``london`` / ``ny`` / ``tokyo`` / ``outside``.
    """
    if isinstance(session_state, dict):
        kz = session_state.get("kill_zone")
        if isinstance(kz, str) and kz:
            return kz
    pa_kz = _safe_get(pa_output, "kill_zone")
    if isinstance(pa_kz, str) and pa_kz:
        return pa_kz
    return "outside"


def _candle_time_from(
    pa_output: Any,
    mso: Any,
    explicit: Optional[str],
) -> Optional[str]:
    """Return the candle close UTC ISO string, falling back gracefully.

    Order of precedence: explicit param → ``pa_output.timestamp_utc``
    → ``mso.timestamp_utc`` → ``None``.
    """
    if explicit:
        return str(explicit)
    pa_ts = _safe_get(pa_output, "timestamp_utc")
    if pa_ts:
        return str(pa_ts)
    mso_ts = _safe_get(mso, "timestamp_utc")
    if mso_ts:
        return str(mso_ts)
    return None


def _normalize_xau_direction(value: Any) -> str:
    """Normalize the upstream XAU direction value to a row-safe string.

    Inputs we expect from the orchestrator:
      - ``"bullish"`` / ``"bearish"`` — produced by
        :func:`src.utils.cross_instrument.get_xauusd_d1_direction`.
      - ``"unavailable"`` — same function, insufficient D1 data.
      - ``"disabled"`` — orchestrator-side sentinel for symbols listed in
        ``cross_instrument_context_disabled_for`` (e.g. GBPUSD), where
        ``_compute_cross_instrument_context`` short-circuits before
        calling the XAU helper. We log this distinctly so the analyst
        can separate "no XAU view captured" from "XAU view said
        unavailable".
      - ``"unclear"`` — defensive; the helper does not currently emit
        this, but the brief explicitly requested it as a possible value.
        Pass through verbatim if a future helper version returns it.
      - ``None`` / empty / unknown string — coerced to ``"unavailable"``
        so the row is still well-formed.
    """
    if value in ("bullish", "bearish", "unclear", "unavailable", "disabled"):
        return value  # type: ignore[return-value]
    if isinstance(value, str) and value:
        # Future-proof: pass through unrecognized non-empty strings rather
        # than coercing — preserves any new sentinel an upstream change
        # might introduce.
        return value
    return "unavailable"


def _build_row(
    *,
    candle_time_utc: Optional[str],
    instrument: str,
    proposed_direction: Optional[str],
    xau_d1_direction: str,
    correlation_to_xau: Optional[float],
    direction_aligned_with_xau: Optional[bool],
    kill_zone: str,
    confidence_score: Optional[int],
    framework: Optional[str],
) -> dict:
    """Assemble the audit row.

    Schema is ADDITIVE only — append new fields at the end of the dict;
    do not rename or remove existing keys. Consumers of earlier rows must
    continue to load without modification.
    """
    return {
        "logged_at_utc": datetime.now(timezone.utc).isoformat(),
        "candle_time_utc": candle_time_utc,
        "instrument": instrument,
        "proposed_direction": proposed_direction,
        "xau_d1_direction": xau_d1_direction,
        "correlation_to_xau": correlation_to_xau,
        "direction_aligned_with_xau": direction_aligned_with_xau,
        "kill_zone": kill_zone,
        "confidence_score": confidence_score,
        "framework": framework,
    }


def log_direction_emission(
    pa_output: Any,
    *,
    instrument: str,
    xau_d1_direction: Any,
    mso: Any = None,
    session_state: Optional[dict] = None,
    candle_time_utc: Optional[str] = None,
    log_path: Optional[str] = None,
) -> Optional[dict]:
    """Append one JSONL row capturing a CANDIDATE emission's XAU context.

    Args:
        pa_output: ``PrimaryAnalysisOutput``-like object. Must have
            ``decision == "CANDIDATE"`` for a row to be written —
            non-CANDIDATE outputs are a no-op (returns ``None``). The
            caller is responsible for the decision check; we re-validate
            defensively.
        instrument: Trading symbol (e.g. ``"XAUUSD"``, ``"GBPUSD"``).
        xau_d1_direction: Raw XAU D1 direction captured by the
            orchestrator (``"bullish"`` / ``"bearish"`` / ``"unavailable"``
            / ``"disabled"`` / ``"unclear"``). Normalized via
            :func:`_normalize_xau_direction`. Pass ``"disabled"`` for
            symbols in ``cross_instrument_context_disabled_for``.
        mso: ``MarketStateObject``-like; only used to fall back on
            ``timestamp_utc`` if neither *candle_time_utc* nor
            ``pa_output.timestamp_utc`` is set.
        session_state: Optional dict; we read ``kill_zone`` if present.
        candle_time_utc: Explicit candle-close timestamp override.
        log_path: Override the default sink. Tests use this with
            ``tmp_path``.

    Returns:
        The row dict that was written, or ``None`` if no row was written
        (non-CANDIDATE input or any failure path).

    This function MUST NEVER raise into the orchestrator. All exceptions
    are caught and logged via the ``logging`` module. Returning ``None``
    on failure is the contract.
    """
    try:
        proposed_direction = _extract_proposed_direction(pa_output)
        if proposed_direction is None:
            # Non-CANDIDATE or missing trade_parameters — silent no-op.
            return None

        xau_norm = _normalize_xau_direction(xau_d1_direction)
        ts = _candle_time_from(pa_output, mso, candle_time_utc)
        kz = _extract_kill_zone(session_state, pa_output)
        framework = _extract_framework(pa_output)
        confidence = _extract_confidence_score(pa_output)
        corr = _resolve_correlation_to_xau(instrument)
        aligned = _resolve_alignment(proposed_direction, xau_norm)

        row = _build_row(
            candle_time_utc=ts,
            instrument=instrument,
            proposed_direction=proposed_direction,
            xau_d1_direction=xau_norm,
            correlation_to_xau=corr,
            direction_aligned_with_xau=aligned,
            kill_zone=kz,
            confidence_score=confidence,
            framework=framework,
        )

        path = Path(log_path or SHADOW_LOG_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
        return row
    except Exception as exc:  # noqa: BLE001 — must never raise into orchestrator
        logger.warning(
            "direction_emission_logger failed: %s", exc, exc_info=True,
        )
        return None


__all__ = [
    "SHADOW_LOG_PATH",
    "log_direction_emission",
]
