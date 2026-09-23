"""sl_beyond_ob L2 verification decision shadow logger — observation-only.

For every L2 ``_check_sl_beyond_ob`` evaluation that produces a non-SKIP
result (PASS or FAIL/REJECT) inside ``verify_candidate``, this logger
appends a JSONL row capturing the geometric inputs + decision so that a
post-30-day data accumulation can compute hypothetical realized R via
H1 forward-resolution.

A.1 deferred-changes spec
-------------------------
Source: ``.context/02_session_handoffs/40_apr26_DEFERRED_CHANGES_MASTER.md``.
The proposed sl_beyond_ob strict-``<`` -> ``<=`` relaxation was REJECTED
2026-04-19 (T2.9; cross-instrument audit T4.26 found pattern is
NAS100-specific) and the AI-side root cause shipped in FA-2 (`fa35cc0`).
This logger collects the live distribution of REJECTs the gate fires in
production so a future +43R/mo "relax decision" can be re-evaluated
after >=30 production rejection events / >=6 weeks live data drawn from
the production regime.

Schema mirrors ``touch_count_gate_logger`` (ADR-005) deliberately:
    - candle_time (UTC)
    - symbol
    - l2_decision (PASS / REJECT)
    - l2_reason (the existing reason string from verification.py)
    - proposed_entry, proposed_sl, proposed_tp1
    - ob_high, ob_low (the zone boundaries the check used)
    - direction (LONG / SHORT)
    - framework (ob_retest / fvg_fill / breaker_re_entry)
    - h1_atr (so post-hoc analysis can compute SL-distance-as-fraction-of-ATR)
    - confidence_score (when available on PrimaryAnalysisOutput)

Failure isolation
-----------------
Any exception during disk I/O or row construction is caught, logged at
WARNING level with traceback, and swallowed. L2 verification logic
continues — the gate evaluation is wholly independent of this module.
If logging fails, the L2 result is still returned on schedule.

Output
------
Append-only JSONL at ``shadow_logs/sl_beyond_ob_decisions.jsonl``.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Default sink. Tests must redirect by passing ``log_path`` (or by
# monkey-patching this module's ``SHADOW_LOG_PATH`` constant).
SHADOW_LOG_PATH = "shadow_logs/sl_beyond_ob_decisions.jsonl"


def _safe_attr(obj: Any, name: str, default: Any = None) -> Any:
    """Defensive getattr that swallows AttributeError + TypeError."""
    try:
        val = getattr(obj, name, default)
        return val if val is not None else default
    except Exception:
        return default


def _coerce_float(val: Any) -> Optional[float]:
    """Convert val to float, returning None on failure."""
    try:
        if val is None:
            return None
        return float(val)
    except (TypeError, ValueError):
        return None


def _candle_time_from_mso(mso: Any) -> Optional[str]:
    """Pull ``mso.timestamp_utc`` — the candle-close timestamp for this eval."""
    try:
        ts = getattr(mso, "timestamp_utc", None)
        if ts is None and hasattr(mso, "get"):
            ts = mso.get("timestamp_utc")
        return str(ts) if ts is not None else None
    except Exception:
        return None


def _h1_atr_from_mso(mso: Any) -> Optional[float]:
    """Extract H1 atr_14 from the MSO timeframes dict."""
    try:
        tfs = getattr(mso, "timeframes", None)
        if tfs is None:
            return None
        h1 = None
        try:
            h1 = tfs.get("H1") if hasattr(tfs, "get") else tfs["H1"]
        except (KeyError, TypeError, AttributeError):
            return None
        if h1 is None:
            return None
        return _coerce_float(getattr(h1, "atr_14", None))
    except Exception:
        return None


def _zone_from_match(matched_ob: Any, matched_bb: Any) -> tuple[Optional[float], Optional[float], Optional[str]]:
    """Resolve (ob_low, ob_high, zone_label) from whichever match is set.

    Mirrors the conditional in ``_check_sl_beyond_ob`` — OB takes priority
    over breaker (matches the verification.py check ordering).
    """
    if matched_ob is not None:
        return (
            _coerce_float(_safe_attr(matched_ob, "low")),
            _coerce_float(_safe_attr(matched_ob, "high")),
            "OB",
        )
    if matched_bb is not None:
        return (
            _coerce_float(_safe_attr(matched_bb, "zone_low")),
            _coerce_float(_safe_attr(matched_bb, "zone_high")),
            "breaker",
        )
    return None, None, None


def _build_row(
    *,
    symbol: Optional[str],
    framework: Optional[str],
    decision: str,
    l2_reason: Optional[str],
    direction: Optional[str],
    proposed_entry: Optional[float],
    proposed_sl: Optional[float],
    proposed_tp1: Optional[float],
    ob_low: Optional[float],
    ob_high: Optional[float],
    zone_label: Optional[str],
    h1_atr: Optional[float],
    confidence_score: Optional[int],
    candle_time: Optional[str],
) -> dict:
    """Assemble the A.1 shadow log row.

    The schema is ADDITIVE only — new fields appended at the end of the
    dict; existing keys must never be renamed or removed. Consumers of
    earlier rows must continue to load without modification.
    """
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "candle_time": candle_time,
        "symbol": symbol,
        "framework": framework,
        "l2_decision": decision,
        "l2_reason": l2_reason,
        "direction": direction,
        "proposed_entry": proposed_entry,
        "proposed_sl": proposed_sl,
        "proposed_tp1": proposed_tp1,
        "ob_low": ob_low,
        "ob_high": ob_high,
        "zone_label": zone_label,
        "h1_atr": h1_atr,
        "confidence_score": confidence_score,
    }


def log_sl_beyond_ob_decision(
    *,
    analysis: Any,
    mso: Any,
    config: Optional[dict],
    matched_ob: Any,
    matched_bb: Any,
    check_result: Any,
    log_path: Optional[str] = None,
) -> None:
    """Append one JSONL row capturing the sl_beyond_ob L2 decision.

    Args:
        analysis: ``PrimaryAnalysisOutput`` (or test-double); used for
            ``trade_parameters`` (entry/sl/tp1/direction), ``framework``,
            and ``confidence_score``.
        mso: ``MarketStateObject``; used to pull ``timestamp_utc`` and
            ``timeframes["H1"].atr_14``.
        config: Live config dict; used to (a) honor the
            ``shadow_loggers.sl_beyond_ob_decisions_logger.enabled`` gate
            and (b) extract ``market.symbol`` for the row's ``symbol``
            field. Pass ``None`` and the logger uses defaults (enabled=True,
            symbol="UNKNOWN").
        matched_ob: H1 OrderBlock matched by ``_check_h1_poi_exists``,
            or None.
        matched_bb: BreakerBlock matched by ``_check_h1_poi_exists``,
            or None.
        check_result: The ``VerificationCheck`` returned by
            ``_check_sl_beyond_ob``. Provides ``status`` (PASS/FAIL/SKIP)
            and ``detail`` (human-readable reason). Logger maps SKIP to
            no-op; PASS/FAIL are written as PASS/REJECT to mirror ADR-005
            schema vocabulary.
        log_path: Override the default sink. Tests use this with
            ``tmp_path``.

    This function MUST NEVER raise into the L2 decision path. All
    exceptions are caught and logged via the ``logging`` module.
    """
    try:
        # Config gate — honored even before any work to keep the disabled
        # path zero-cost.
        if config is not None:
            try:
                logger_cfg = (config.get("shadow_loggers", {}) or {}).get(
                    "sl_beyond_ob_decisions_logger", {}
                ) or {}
                if not logger_cfg.get("enabled", True):
                    return
            except Exception:
                # Malformed config dict — fall through to default-enabled
                # (fail-open for observability).
                pass

        status = _safe_attr(check_result, "status", "")
        # SKIP rows are not interesting for this study — the gate didn't
        # actually evaluate. Drop them silently.
        if status == "SKIP":
            return

        # Map verification.py vocabulary to ADR-005 PASS/REJECT vocabulary.
        if status == "PASS":
            decision = "PASS"
        elif status == "FAIL":
            decision = "REJECT"
        else:
            # Unknown status (WARN, etc.) — log as-is so analysts can spot
            # surprises without losing the row.
            decision = str(status) if status else "UNKNOWN"

        # ── Pull from analysis.trade_parameters ────────────────────────
        tp = _safe_attr(analysis, "trade_parameters", None)
        direction = _safe_attr(tp, "direction") if tp is not None else None
        proposed_entry = _coerce_float(_safe_attr(tp, "entry_price")) if tp is not None else None
        proposed_sl = _coerce_float(_safe_attr(tp, "stop_loss")) if tp is not None else None
        proposed_tp1 = _coerce_float(_safe_attr(tp, "take_profit_1")) if tp is not None else None

        # ── Pull from analysis ────────────────────────────────────────
        framework = _safe_attr(analysis, "framework", None)
        confidence_raw = _safe_attr(analysis, "confidence_score", None)
        try:
            confidence_score = int(confidence_raw) if confidence_raw is not None else None
        except (TypeError, ValueError):
            confidence_score = None

        # ── Pull from MSO ──────────────────────────────────────────────
        candle_time = _candle_time_from_mso(mso)
        h1_atr = _h1_atr_from_mso(mso)

        # ── Pull from matched zone ────────────────────────────────────
        ob_low, ob_high, zone_label = _zone_from_match(matched_ob, matched_bb)

        # ── Pull from check_result ────────────────────────────────────
        l2_reason = _safe_attr(check_result, "detail", None)

        # ── Pull from config ──────────────────────────────────────────
        symbol: Optional[str] = None
        if config is not None:
            try:
                symbol = (config.get("market", {}) or {}).get("symbol")
            except Exception:
                symbol = None

        row = _build_row(
            symbol=symbol,
            framework=framework,
            decision=decision,
            l2_reason=l2_reason,
            direction=direction,
            proposed_entry=proposed_entry,
            proposed_sl=proposed_sl,
            proposed_tp1=proposed_tp1,
            ob_low=ob_low,
            ob_high=ob_high,
            zone_label=zone_label,
            h1_atr=h1_atr,
            confidence_score=confidence_score,
            candle_time=candle_time,
        )

        path = Path(log_path or SHADOW_LOG_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    except Exception as exc:  # noqa: BLE001 — must never raise into L2
        logger.warning(
            "sl_beyond_ob_shadow_logger failed: %s", exc, exc_info=True,
        )


__all__ = [
    "SHADOW_LOG_PATH",
    "log_sl_beyond_ob_decision",
]
