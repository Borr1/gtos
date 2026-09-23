"""ADR-005 touch-count gate decision shadow logger — observation-only.

For every ``ob_retest`` framework CANDIDATE that reaches the
``_reject_if_touch_count_too_high`` gate in ``src/components/permissions.py``,
this logger appends a JSONL row capturing the gate's decision input + output:

    - the touch_count of the H1 OB selected by ``_find_target_ob``
    - the threshold value at decision time (configurable via
      ``gate1.touch_count_reject_threshold``)
    - the decision (``"PASS"`` or ``"REJECT"``)
    - a stable target_ob_id for cross-row tracing
      (``"{symbol}_{type}_{formation_time}"``, sanitized)

ADR-005 spec
------------
Source: ``.context/06_decisions/ADR-005_touch_count_shadow.md``.
The audit (A11) recommended LOOSEN_TO_3 from the touch-count counterfactual
on filled CANDs (n=98). The reviewer pass (A19, ``research/touch_count_audit/
REVIEWER_PASS.md`` referenced in the spec) REJECTED that recommendation
because the touch=2 advantage REVERSES across H1/H2 2026 regime split. The
default threshold remains 2 for the Monday 2026-04-27 FTMO challenge launch.

This logger collects the live distribution of touch_count values the gate
actually sees in production so the LOOSEN_TO_3 (or other threshold) decision
can be re-evaluated after ≥30 production rejection events / ≥6 weeks live
data. Crucially, both PASS and REJECT decisions are logged so the analyst
can compute:

    - P(REJECT | symbol, kill_zone) — gate firing rate per cohort
    - touch_count distribution among accepted CANDs (PASS rows)
    - touch_count distribution among rejected CANDs (REJECT rows)

Failure isolation
-----------------
Any exception during disk I/O or row construction is caught, logged at
WARNING level with traceback, and swallowed. Trading logic continues. The
gate evaluation is wholly independent of this module — if logging fails,
the gate's ExecutionDenial (or PASS) is still returned on schedule.

Output
------
Append-only JSONL at ``shadow_logs/touch_count_gate_decisions.jsonl``.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Default sink. Tests must redirect by passing ``log_path`` (or by
# monkey-patching this module's ``SHADOW_LOG_PATH`` constant).
SHADOW_LOG_PATH = "shadow_logs/touch_count_gate_decisions.jsonl"


def _sanitize(token: str | None) -> str:
    """Strip everything except [A-Za-z0-9_-] from ``token``.

    Used for the ``gate_target_ob_id`` so colons / spaces in formation_time
    do not break shell or filesystem tooling that consumes the JSONL.
    """
    if not token:
        return "unknown"
    return re.sub(r"[^0-9A-Za-z_\-]", "_", str(token))


def _safe_attr(obj: Any, name: str, default: Any = None) -> Any:
    """Defensive getattr that swallows AttributeError + TypeError."""
    try:
        val = getattr(obj, name, default)
        return val if val is not None else default
    except Exception:
        return default


def _build_target_ob_id(symbol: str, target_ob: Any) -> str:
    """Build ``{symbol}_{type}_{formation_time}`` (sanitized).

    When ``target_ob`` is None or missing fields, returns
    ``{symbol}_no_target_ob`` so the row is still distinguishable.
    """
    sym = _sanitize(symbol)
    if target_ob is None:
        return f"{sym}_no_target_ob"
    ob_type = _safe_attr(target_ob, "type", "unknown")
    formation_time = _safe_attr(target_ob, "formation_time", "unknown")
    return f"{sym}_{_sanitize(ob_type)}_{_sanitize(formation_time)}"


def _coerce_int(val: Any, default: int = 0) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _candle_time_from_mso(mso: Any) -> str | None:
    """Pull ``mso.timestamp_utc`` — the candle-close timestamp for this eval."""
    try:
        ts = getattr(mso, "timestamp_utc", None)
        if ts is None and hasattr(mso, "get"):
            ts = mso.get("timestamp_utc")
        return str(ts) if ts is not None else None
    except Exception:
        return None


def _build_row(
    *,
    symbol: str,
    framework: str | None,
    decision: str,
    target_ob: Any,
    threshold: int,
    candle_time: str | None,
    candidate_id: str | None,
) -> dict:
    """Assemble the ADR-005 shadow log row.

    The schema is ADDITIVE only — new fields appended at the end of the
    dict; existing keys must never be renamed or removed. Consumers of
    earlier rows must continue to load without modification.
    """
    if target_ob is not None:
        gate_target_ob_touch: Optional[int] = _coerce_int(
            _safe_attr(target_ob, "touch_count", 0), default=0
        )
        ob_low = _safe_attr(target_ob, "low")
        ob_high = _safe_attr(target_ob, "high")
        ob_type = _safe_attr(target_ob, "type")
    else:
        # No target OB found by ``_find_target_ob`` — typically because
        # the entry price doesn't sit inside any unmitigated H1 OB. The
        # gate silently passes in that case (it is a statistical filter
        # not a framework-conformance check). We still log so the
        # analyst can see the "no-OB" cohort.
        gate_target_ob_touch = None
        ob_low = None
        ob_high = None
        ob_type = None

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "candle_time": candle_time,
        "framework": framework,
        "gate_target_ob_touch": gate_target_ob_touch,
        "gate_threshold_at_eval": threshold,
        "gate_decision": decision,
        "gate_target_ob_id": _build_target_ob_id(symbol, target_ob),
        "candidate_id": candidate_id,
        "ob_low": ob_low,
        "ob_high": ob_high,
        "ob_type": ob_type,
    }


def log_touch_count_gate_decision(
    *,
    symbol: str,
    framework: str | None,
    target_ob: Any,
    threshold: int,
    decision: str,
    mso: Any = None,
    candidate_id: str | None = None,
    log_path: str | None = None,
) -> None:
    """Append one JSONL row capturing the touch-count gate decision.

    Args:
        symbol: Trading symbol (e.g. ``"XAUUSD"``).
        framework: ``"ob_retest"`` for the gated path, or whatever the
            ``PrimaryAnalysisOutput.framework`` reports. Logger still
            writes for non-ob_retest frameworks ONLY when this function
            is explicitly called for them — the caller in
            ``permissions.py`` short-circuits before invoking us for
            non-ob_retest paths.
        target_ob: The H1 OrderBlock returned by
            ``_find_target_ob``. May be None if no OB matched the entry
            price; in that case gate_target_ob_touch is logged as null
            and the row still records the candle, threshold, and PASS
            decision (the gate silently passes when there is no target).
        threshold: ``gate1.touch_count_reject_threshold`` value at eval
            time. Logged so retroactive analysis can correlate decisions
            with config-knob changes.
        decision: ``"PASS"`` or ``"REJECT"`` — the gate's outcome for
            this candle.
        mso: MarketStateObject for the candle (used to pull
            ``timestamp_utc``). Optional; if not provided the
            ``candle_time`` field is null and the analyst falls back to
            the row's ``timestamp_utc`` (clock-time-of-write).
        candidate_id: Free-form identifier for cross-log correlation
            with ``candidate_features_log.jsonl`` rows. Defaults to
            ``"{symbol}_{candle_time}"`` when None.
        log_path: Override the default sink. Tests use this with
            ``tmp_path``.

    This function MUST NEVER raise into the gate evaluation. All
    exceptions are caught and logged via the ``logging`` module.
    """
    try:
        if decision not in ("PASS", "REJECT", "N/A"):
            # Defensive: future callers might add new states. Log
            # whatever they pass so we don't lose data, but warn so a
            # future reader of the log can see the unexpected value.
            logger.warning(
                "touch_count_gate_logger: unexpected decision=%r — "
                "writing as-is", decision,
            )

        candle_time = _candle_time_from_mso(mso)
        cid = candidate_id or f"{_sanitize(symbol)}_{_sanitize(candle_time or 'unknown')}"

        row = _build_row(
            symbol=symbol,
            framework=framework,
            decision=decision,
            target_ob=target_ob,
            threshold=int(threshold),
            candle_time=candle_time,
            candidate_id=cid,
        )

        path = Path(log_path or SHADOW_LOG_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    except Exception as exc:  # noqa: BLE001 — must never raise into gate
        logger.warning(
            "touch_count_gate_logger failed: %s", exc, exc_info=True,
        )
