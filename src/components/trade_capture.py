"""Trade Data Capture.

Saves complete context for every CANDIDATE decision:
- Full MSO that the AI was given
- Complete prompt (system + user message) as sent
- Full AI response JSON
- Level 2 verification results
- Cross-instrument context
- Session memory state
- Gate results (per-check detail)
- Execution data (if trade is taken)
- Exit data (when trade closes)

Every CANDIDATE creates a trade record file, regardless of whether
the trade is executed, rejected by Level 2, or rejected by Gate 1.
This enables retroactive analysis of ALL decisions, not just trades taken.

CAPTURE_VERSION history:
- 1.0 (initial): baseline schema — metadata / decision_pipeline / mso / prompt /
  ai_response / trade_parameters / execution / exit.
- 1.1 (session 39, A3 instrumentation): adds top-level ``instrumentation`` block
  populated at CAND creation — target_ob_touch_count, m5_refined flag + details,
  sl_source, sl_buffer_applied (aliased to top level), h1_fvg_unfilled_count,
  m15_fvg_unfilled_count, h1_opp_ob_touch, detector_version_at_eval,
  kill_zone_bucket_15min.  Exit path also gains realized_R, time_in_trade_minutes,
  exit_reason (canonical TP1/TP2/SL/BE/TIMEOUT/MANUAL enum).  Fields are all
  nullable — a pre-1.1 record loaded by 1.1 code returns None for every new
  field and MUST NOT raise.  See research/a3_trade_record_instrumentation/.
"""

from __future__ import annotations

import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.security import get_sanitized_environment
from src.utils.file_io import atomic_write, load_json

logger = logging.getLogger(__name__)

CAPTURE_VERSION = "1.1"

# Canonical exit_reason enum — see _canonical_exit_reason().  Persisted under
# record["exit"]["exit_reason"] so Phase-2 sniper queries can group by outcome
# without fuzzy-matching the free-form exit_type strings.
EXIT_REASON_TP1 = "TP1"
EXIT_REASON_TP2 = "TP2"
EXIT_REASON_SL = "SL"
EXIT_REASON_BE = "BE"
EXIT_REASON_TIMEOUT = "TIMEOUT"
EXIT_REASON_MANUAL = "MANUAL"
EXIT_REASON_UNKNOWN = "UNKNOWN"

_VALID_EXIT_REASONS = {
    EXIT_REASON_TP1, EXIT_REASON_TP2, EXIT_REASON_SL,
    EXIT_REASON_BE, EXIT_REASON_TIMEOUT, EXIT_REASON_MANUAL,
    EXIT_REASON_UNKNOWN,
}


def _canonical_exit_reason(exit_type: Optional[str]) -> str:
    """Map free-form exit_type → canonical EXIT_REASON_* enum.

    Orchestrator's _finalize_exit passes strings like ``"tp_hit"``,
    ``"sl_hit"``, ``"breakeven"``, ``"timeout_2h"``, ``"manual_close"``,
    etc.  This keeps the mapping honest + debuggable in one place.
    """
    if not exit_type:
        return EXIT_REASON_UNKNOWN
    s = str(exit_type).strip().upper()
    # Order matters: check longer prefixes first.
    if s.startswith("TP2") or "TP_HIT_2" in s:
        return EXIT_REASON_TP2
    if s.startswith("TP1") or s == "TP_HIT" or "TP1" in s:
        return EXIT_REASON_TP1
    if s.startswith("SL") or "SL_HIT" in s or s == "STOP_LOSS":
        return EXIT_REASON_SL
    if "BREAKEVEN" in s or s.startswith("BE") or s == "BREAK_EVEN":
        return EXIT_REASON_BE
    if "TIMEOUT" in s or s.endswith("_2H") or "SESSION_TIMEOUT" in s:
        return EXIT_REASON_TIMEOUT
    if s == "BROKER_CLOSED":
        return EXIT_REASON_UNKNOWN
    if "MANUAL" in s or "CLOSE" in s:
        return EXIT_REASON_MANUAL
    return EXIT_REASON_UNKNOWN


def _canonical_broker_close_exit_reason(exit_data: dict) -> Optional[str]:
    """Classify broker-closed exits from MT5 deal reason/comment evidence."""
    if str(exit_data.get("exit_type") or "").strip().lower() != "broker_closed":
        return None

    comment = str(exit_data.get("broker_close_comment") or "").strip().lower()
    reason_raw = exit_data.get("broker_close_reason")
    try:
        reason = int(reason_raw)
    except (TypeError, ValueError):
        reason = None

    if comment.startswith("[sl") or " stop loss" in comment or reason == 4:
        return EXIT_REASON_SL
    if comment.startswith("[tp") or " take profit" in comment or reason == 5:
        if "tp1" in comment:
            return EXIT_REASON_TP1
        return EXIT_REASON_TP2
    return EXIT_REASON_UNKNOWN


def _kill_zone_bucket_15min(kill_zone: str, candle_time_iso: str) -> str:
    """Derive a 15-min kill-zone bucket label like ``london_0715``.

    Empty-safe: returns ``"{kz}_unknown"`` when candle_time cannot be parsed.
    """
    try:
        if isinstance(candle_time_iso, str):
            ct = datetime.fromisoformat(candle_time_iso.replace("Z", "+00:00"))
        else:
            ct = candle_time_iso
        return f"{kill_zone}_{ct.strftime('%H%M')}"
    except Exception:
        return f"{kill_zone}_unknown"


def _count_unfilled_fvgs(tf_state) -> int:
    """Count unfilled FVGs on a single timeframe.  Safe on None / dict / pydantic."""
    if tf_state is None:
        return 0
    try:
        fvgs = getattr(tf_state, "fair_value_gaps", None)
        if fvgs is None and isinstance(tf_state, dict):
            fvgs = tf_state.get("fair_value_gaps", [])
        if not fvgs:
            return 0
        count = 0
        for fvg in fvgs:
            filled = getattr(fvg, "filled", None)
            if filled is None and isinstance(fvg, dict):
                filled = fvg.get("filled", False)
            if not filled:
                count += 1
        return count
    except Exception as e:
        logger.debug("FVG counting failed: %s", e)
        return 0


def _nearest_opposing_ob_touch(
    mso,
    direction: Optional[str],
    entry_price: Optional[float],
) -> Optional[int]:
    """Return touch_count of the nearest OPPOSING-direction H1 OB.

    For a LONG setup we look for the nearest unmitigated bearish H1 OB ABOVE
    entry (the first supply zone that could reject the move).  For SHORT,
    the nearest unmitigated bullish H1 OB BELOW entry.

    Returns None when MSO/direction/entry is unusable or no OB found.
    """
    if not direction or entry_price is None or entry_price <= 0:
        return None
    try:
        timeframes = getattr(mso, "timeframes", None)
        if timeframes is None and isinstance(mso, dict):
            timeframes = mso.get("timeframes", {})
        if not timeframes:
            return None
        h1 = timeframes.get("H1") if isinstance(timeframes, dict) else timeframes.get("H1", None)
        if h1 is None:
            return None
        obs = getattr(h1, "order_blocks", None)
        if obs is None and isinstance(h1, dict):
            obs = h1.get("order_blocks", [])
        if not obs:
            return None

        required_type = "bearish" if direction == "LONG" else "bullish"
        best_ob = None
        best_dist = float("inf")
        for ob in obs:
            ob_type = getattr(ob, "type", None)
            mitigated = getattr(ob, "mitigated", None)
            low = getattr(ob, "low", None)
            high = getattr(ob, "high", None)
            touch = getattr(ob, "touch_count", None)
            if ob_type is None and isinstance(ob, dict):
                ob_type = ob.get("type")
                mitigated = ob.get("mitigated", False)
                low = ob.get("low")
                high = ob.get("high")
                touch = ob.get("touch_count", 0)
            if mitigated or ob_type != required_type:
                continue
            if low is None or high is None:
                continue
            # Directional filter: opposing OB must sit on the far side of entry.
            if direction == "LONG" and low < entry_price:
                continue
            if direction == "SHORT" and high > entry_price:
                continue
            midpoint = (low + high) / 2.0
            dist = abs(midpoint - entry_price)
            if dist < best_dist:
                best_dist = dist
                best_ob = ob

        if best_ob is None:
            return None
        touch = getattr(best_ob, "touch_count", None)
        if touch is None and isinstance(best_ob, dict):
            touch = best_ob.get("touch_count", 0)
        return int(touch) if touch is not None else 0
    except Exception as e:
        logger.debug("Opposing OB touch lookup failed: %s", e)
        return None


def _infer_sl_source(
    framework: Optional[str],
    sl_buffer_applied: Optional[float],
) -> str:
    """Best-effort inference of SL placement source at CAND time.

    - ``ob``: ob_retest framework with non-zero structural buffer — the
      typical structural SL at OB boundary.
    - ``structural``: any non-ob framework where AI emitted a non-zero buffer
      (swing-beyond placement).
    - ``atr_fallback``: zero buffer reported — AI placed SL mechanically
      rather than beyond a structural swing.  Gate 1 usually clamps this.
    - ``unknown``: no framework / no SL info.

    NB: this is a CAND-time inference from AI output only.  Post-clamp SL
    source mutations (Gate 1 floor/ATR override) are NOT reflected here —
    they would be a separate post-gate field in a later iteration.
    """
    if not framework:
        return "unknown"
    buf = sl_buffer_applied if sl_buffer_applied is not None else 0.0
    if framework == "ob_retest":
        return "ob" if buf > 0 else "atr_fallback"
    if buf > 0:
        return "structural"
    return "atr_fallback"


def _get_system_version() -> str:
    """Get current git commit hash, or 'unknown' if not in a repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
            env=get_sanitized_environment(),
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def _extract_system_prompt_text(system_blocks) -> str:
    """Extract the text content from system prompt blocks.

    The system prompt can be a string or a list of content blocks
    (used for prompt caching). Extract the text either way.
    """
    if isinstance(system_blocks, str):
        return system_blocks
    if isinstance(system_blocks, list):
        parts = []
        for block in system_blocks:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return str(system_blocks)


def _safe_model_dump(obj) -> Any:
    """Safely dump a Pydantic model or return as-is for dicts."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if isinstance(obj, dict):
        return obj
    return str(obj)


# ---------------------------------------------------------------------------
# Record creation and updates
# ---------------------------------------------------------------------------

def create_trade_record(
    symbol: str,
    kill_zone: str,
    candle_time: str,
    mso,
    prompt_system,
    prompt_user: str,
    ai_response: dict,
    cross_instrument_context: Optional[str],
    session_memory: str,
    config: dict,
) -> dict:
    """Assemble the initial trade record when a CANDIDATE is produced.

    Returns the record dict (not yet written to disk).
    """
    tc_cfg = config.get("trade_capture", {})

    # Parse candle_time for path generation
    try:
        if isinstance(candle_time, str):
            ct = datetime.fromisoformat(candle_time.replace("Z", "+00:00"))
        else:
            ct = candle_time
    except (ValueError, TypeError):
        ct = datetime.now(timezone.utc)

    date_str = ct.strftime("%Y-%m-%d")
    time_str = ct.strftime("%H%M")
    trade_id = f"{symbol}_{date_str}_{kill_zone}_{time_str}"

    # Build system prompt text
    system_prompt_text = _extract_system_prompt_text(prompt_system)

    # --- A3 INSTRUMENTATION (v1.1): snapshot MSO + config at CAND time -------
    # Every field here is OPTIONAL with nullable default so backward-compat is
    # preserved — a pre-1.1 record loaded by 1.1 code returns None without
    # raising, and 1.1 records written to disk carry these fields even when
    # the underlying MSO/config didn't supply them.
    tp_dict = (ai_response.get("trade_parameters") or {}) if isinstance(ai_response, dict) else {}
    framework = ai_response.get("framework") if isinstance(ai_response, dict) else None
    ai_direction = tp_dict.get("direction") or None
    ai_entry_price = tp_dict.get("entry_price")
    sl_buffer = tp_dict.get("sl_buffer_applied")

    # FVG counts (MSO-derived, cheap pure calc)
    timeframes = getattr(mso, "timeframes", None)
    if timeframes is None and isinstance(mso, dict):
        timeframes = mso.get("timeframes", {})
    h1_tf = timeframes.get("H1") if isinstance(timeframes, dict) and timeframes else None
    m15_tf = timeframes.get("M15") if isinstance(timeframes, dict) and timeframes else None

    detector_version = None
    try:
        detector_version = (
            config.get("market_state", {}).get("detector_version")
            or config.get("structure_detector", {}).get("version")
        )
    except Exception:
        detector_version = None

    instrumentation = {
        # target_ob_touch_count — populated later by update_verification()
        # using the matched_ob on VerificationResult.
        "target_ob_touch_count": None,
        "target_ob_zone": None,
        # m5_refined — populated by update_m5_refinement() after the M5 call.
        "m5_refined": False,
        "m5_refinement_details": None,
        # sl_* — inferred from AI output at CAND time.
        "sl_source": _infer_sl_source(framework, sl_buffer),
        "sl_buffer_applied": sl_buffer,
        # FVG counts — MSO-derived.
        "h1_fvg_unfilled_count": _count_unfilled_fvgs(h1_tf),
        "m15_fvg_unfilled_count": _count_unfilled_fvgs(m15_tf),
        # Opposing OB touch — MSO-derived.
        "h1_opp_ob_touch": _nearest_opposing_ob_touch(mso, ai_direction, ai_entry_price),
        # Detector version snapshot — config-derived.
        "detector_version_at_eval": detector_version,
        # Kill-zone 15-min bucket — trivially derivable from candle_time.
        "kill_zone_bucket_15min": _kill_zone_bucket_15min(kill_zone, ct.isoformat() if hasattr(ct, "isoformat") else str(ct)),
    }

    record = {
        "metadata": {
            "trade_id": trade_id,
            "date": date_str,
            "symbol": symbol,
            "kill_zone": kill_zone,
            "candle_time": ct.isoformat() if hasattr(ct, "isoformat") else str(ct),
            "capture_version": CAPTURE_VERSION,
            "system_version": _get_system_version(),
        },
        "decision_pipeline": {
            "ai_decision": ai_response.get("decision", "CANDIDATE"),
            "ai_grade": (ai_response.get("reasoning", {}) or {}).get("setup_grade", ""),
            "ai_confidence": ai_response.get("confidence_score", 0),
            "ai_direction": (
                (ai_response.get("trade_parameters", {}) or {}).get("direction", "")
            ),
            "ai_framework": ai_response.get("framework", "none"),
            "level2_verification": None,
            "gate3_result": None,
            "gate1_result": None,
            "final_outcome": "PENDING",
        },
        "context_at_decision": {
            "cross_instrument_context": cross_instrument_context or "",
            "session_memory": session_memory or "",
        },
        "mso": _safe_model_dump(mso) if tc_cfg.get("save_mso", True) else "[omitted]",
        "prompt": {
            "system_prompt": system_prompt_text if tc_cfg.get("save_prompt", True) else "[omitted]",
            "user_message": prompt_user if tc_cfg.get("save_prompt", True) else "[omitted]",
        },
        "ai_response": ai_response,
        "trade_parameters": (ai_response.get("trade_parameters") or None),
        "execution": None,
        "exit": None,
        # A3 instrumentation block — see module docstring §CAPTURE_VERSION 1.1.
        "instrumentation": instrumentation,
    }

    return record


def update_verification(record: dict, verification_result) -> dict:
    """Add Level 2 verification results to the record.

    A3 (v1.1): also populates ``instrumentation.target_ob_touch_count`` +
    ``target_ob_zone`` from the ``matched_ob`` that the verifier resolved,
    so Phase-2 queries can filter by touch count without re-matching.
    """
    checks = []
    for c in verification_result.checks:
        checks.append({
            "name": c.name,
            "status": c.status,
            "detail": c.detail,
            "mso_value": c.mso_value,
            "ai_value": c.ai_value,
        })

    record["decision_pipeline"]["level2_verification"] = {
        "passed": verification_result.passed,
        "checks": checks,
        "blocked_by": verification_result.blocked_by,
    }

    # A3: populate target_ob_touch_count + zone from the matched OB.
    matched_ob = getattr(verification_result, "matched_ob", None)
    matched_bb = getattr(verification_result, "matched_breaker", None)
    inst = record.setdefault("instrumentation", {})
    if matched_ob is not None:
        touch = getattr(matched_ob, "touch_count", None)
        try:
            inst["target_ob_touch_count"] = int(touch) if touch is not None else None
        except (TypeError, ValueError):
            inst["target_ob_touch_count"] = None
        low = getattr(matched_ob, "low", None)
        high = getattr(matched_ob, "high", None)
        inst["target_ob_zone"] = {
            "low": low,
            "high": high,
            "type": getattr(matched_ob, "type", None),
            "formation_time": getattr(matched_ob, "formation_time", None),
        }
    elif matched_bb is not None:
        # Breaker-matched setups have no touch_count (breakers don't track it);
        # still snapshot the zone for Phase-2 analysis.
        inst["target_ob_touch_count"] = None
        inst["target_ob_zone"] = {
            "low": getattr(matched_bb, "zone_low", None),
            "high": getattr(matched_bb, "zone_high", None),
            "type": f"breaker_{getattr(matched_bb, 'direction', '')}",
            "formation_time": getattr(matched_bb, "formation_time", None),
        }
    return record


def update_m5_refinement(record: dict, m5_out: dict) -> dict:
    """Snapshot M5 refinement outcome into the record's instrumentation block.

    Called by orchestrator after ``refine_entry_m5`` returns, regardless of
    whether overrides were applied.  ``m5_out`` is the native refinement
    result dict ``{"applied": bool, "m5_result": dict, "overrides": dict|None}``.

    Best-effort — schema drift in m5_out must not break capture.
    """
    if not isinstance(m5_out, dict):
        return record
    inst = record.setdefault("instrumentation", {})
    try:
        inst["m5_refined"] = bool(m5_out.get("applied", False))
        # Snapshot the overrides dict verbatim (m5_quality, m5_raw_sl_dist,
        # sl_distance, take_profit_1, etc.).  When not applied, still capture
        # the m5_result.decision for traceability.
        if m5_out.get("applied"):
            inst["m5_refinement_details"] = {
                "applied": True,
                "overrides": m5_out.get("overrides"),
                "m5_result_decision": (m5_out.get("m5_result") or {}).get("decision"),
            }
        else:
            inst["m5_refinement_details"] = {
                "applied": False,
                "m5_result_decision": (m5_out.get("m5_result") or {}).get("decision"),
            }
    except Exception as e:
        logger.debug("M5 refinement snapshot failed: %s", e)
    return record


def update_gate_results(
    record: dict,
    gate3_result: Optional[dict],
    gate1_result: Optional[dict],
) -> dict:
    """Add Gate 3 and Gate 1 check results."""
    record["decision_pipeline"]["gate3_result"] = gate3_result
    record["decision_pipeline"]["gate1_result"] = gate1_result
    return record


def update_execution(record: dict, execution_data: dict) -> dict:
    """Add execution data after order fills."""
    record["execution"] = execution_data
    return record


def update_exit(record: dict, exit_data: dict) -> dict:
    """Add exit data when trade closes.

    A3 (v1.1): normalizes exit fields into canonical Phase-2 names:
    - ``exit_reason``  — canonical enum from _canonical_exit_reason(exit_type)
    - ``realized_R``   — alias for ``actual_r``
    - ``time_in_trade_minutes`` — alias for ``hold_time_minutes``
    Original keys are preserved; aliases make Phase-2 queries uniform across
    v1.0 + v1.1 records (v1.0 records get nulls for missing fields).
    """
    if not isinstance(exit_data, dict):
        record["exit"] = exit_data
        return record
    enriched = dict(exit_data)
    # Canonical exit_reason — takes exit_data["exit_reason"] if the caller
    # already set one (override), else derives from exit_type.
    reason = enriched.get("exit_reason")
    broker_reason = _canonical_broker_close_exit_reason(enriched)
    if broker_reason and reason in {None, "", EXIT_REASON_UNKNOWN, EXIT_REASON_MANUAL}:
        reason = broker_reason
    elif not reason or reason not in _VALID_EXIT_REASONS:
        reason = broker_reason or _canonical_exit_reason(enriched.get("exit_type"))
    enriched["exit_reason"] = reason
    # realized_R alias — prefer existing realized_R, then actual_r.
    if "realized_R" not in enriched:
        enriched["realized_R"] = enriched.get("actual_r")
    # time_in_trade_minutes alias — prefer existing, then hold_time_minutes.
    if "time_in_trade_minutes" not in enriched:
        enriched["time_in_trade_minutes"] = enriched.get("hold_time_minutes")
    record["exit"] = enriched
    return record


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def _record_path(record: dict, base_path: str) -> Path:
    """Compute the file path for a trade record."""
    meta = record["metadata"]
    symbol = meta["symbol"]
    date_str = meta["date"]
    kz = meta["kill_zone"]

    try:
        ct = datetime.fromisoformat(meta["candle_time"].replace("Z", "+00:00"))
        time_str = ct.strftime("%H%M")
    except (ValueError, TypeError):
        time_str = "0000"

    suffix = _record_identity_suffix(meta)
    filename = f"{date_str}_{kz}_{time_str}{suffix}.json"
    return Path(base_path) / symbol / filename


def _record_identity_suffix(meta: dict) -> str:
    """Return a path-safe suffix for multi-candidate same-candle records."""
    raw = (
        meta.get("record_path_suffix")
        or meta.get("candidate_id")
        or meta.get("broader_origin_candidate_id")
    )
    if raw in (None, ""):
        return ""
    text = str(raw).strip()
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in text)
    safe = safe.strip("_")
    return f"_{safe[:96]}" if safe else ""


def save_trade_record(
    record: dict,
    base_path: str = "knowledge_base/trade_records",
) -> Optional[str]:
    """Write the record to disk using atomic write pattern.

    Creates directory structure if needed.
    Returns the file path on success, None on failure.
    Never raises — trade capture must not block the pipeline.
    """
    try:
        path = _record_path(record, base_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(str(path), record)
        logger.info("Trade record saved: %s", path)
        return str(path)
    except Exception as e:
        logger.error("Failed to save trade record: %s", e)
        return None


def load_trade_record(filepath: str) -> dict:
    """Load a trade record for analysis."""
    return load_json(filepath)


# ---------------------------------------------------------------------------
# Pending record trade_id index (T2.6 — race-free recovery)
# ---------------------------------------------------------------------------
# The orchestrator needs to reattach an in-memory _pending_trade_record_path
# to a restored PendingLimitIntent after a restart.  Without an explicit index,
# the recovery code has to glob the symbol dir and match on intent trade_id,
# which is fragile under clock skew, multi-order-per-day, and crash-after-save
# timing.  We maintain a trade_id -> record_path index under
# ``{base_path}/{symbol}/_pending_records_index.json`` so recovery is a
# deterministic O(1) dict lookup.

_PENDING_INDEX_FILENAME = "_pending_records_index.json"


def _pending_index_path(symbol: str, base_path: str) -> Path:
    return Path(base_path) / symbol / _PENDING_INDEX_FILENAME


def _load_pending_index(symbol: str, base_path: str) -> dict:
    """Load the pending records index; returns {} on missing/corrupt."""
    path = _pending_index_path(symbol, base_path)
    if not path.exists():
        return {}
    try:
        data = load_json(str(path))
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.warning("Pending records index unreadable (%s) — treating as empty", e)
        return {}


def index_pending_record(
    trade_id: str, record_path: str, symbol: str,
    base_path: str = "knowledge_base/trade_records",
) -> None:
    """Register a LIMIT_PLACED record path under its intent trade_id.

    Never raises — indexing is best-effort; recovery still falls back to a
    glob scan if the index is missing or corrupt.
    """
    if not trade_id or not record_path:
        return
    try:
        index = _load_pending_index(symbol, base_path)
        index[trade_id] = record_path
        path = _pending_index_path(symbol, base_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(str(path), index)
    except Exception as e:
        logger.warning("Failed to index pending record for %s: %s", trade_id, e)


def lookup_pending_record(
    trade_id: str, symbol: str,
    base_path: str = "knowledge_base/trade_records",
) -> Optional[str]:
    """Return the record path for trade_id, or None if not indexed."""
    if not trade_id:
        return None
    return _load_pending_index(symbol, base_path).get(trade_id)


def remove_pending_record(
    trade_id: str, symbol: str,
    base_path: str = "knowledge_base/trade_records",
) -> None:
    """Drop a trade_id from the pending index.  No-op if absent."""
    if not trade_id:
        return
    try:
        index = _load_pending_index(symbol, base_path)
        if trade_id not in index:
            return
        index.pop(trade_id, None)
        path = _pending_index_path(symbol, base_path)
        if index:
            atomic_write(str(path), index)
        else:
            # Keep the directory tidy when the index empties.
            try:
                path.unlink()
            except FileNotFoundError:
                pass
    except Exception as e:
        logger.warning(
            "Failed to remove pending record entry for %s: %s", trade_id, e,
        )


# ---------------------------------------------------------------------------
# Gate result builders
# ---------------------------------------------------------------------------

def build_gate3_result(denial, session_state: dict, mt5,
                       symbol: str = "XAUUSD") -> dict:
    """Build detailed Gate 3 result dict.

    Called regardless of pass/fail to capture check details.
    """
    checks_run = [
        "daily_loss",
        "trades_today",
        "trades_kz",
        "same_symbol_vnext_lifecycle_conflict",
        "concurrent_cap",
        "cross_instrument_correlation_cluster",
        "mt5_connected",
        "spread",
    ]
    result = {
        "passed": denial is None or denial.gate != "gate3_circuit_breaker",
        "checks_run": checks_run,
        "details": {},
    }

    result["details"]["daily_pnl_pct"] = session_state.get("daily_pnl_pct", 0.0)
    result["details"]["trades_today"] = session_state.get("trades_today", 0)
    kz = session_state.get("current_kill_zone", "")
    result["details"]["trades_in_kz"] = session_state.get(f"trades_{kz}", 0)

    try:
        connected = mt5.is_connected()
        result["details"]["mt5_connected"] = connected
        tick = mt5.get_tick(symbol)
        result["details"]["spread_cents"] = tick.spread_cents if tick else None
    except Exception:
        result["details"]["mt5_connected"] = False
        result["details"]["spread_cents"] = None

    try:
        positions = mt5.get_positions(symbol)
        if positions is None:
            result["details"]["same_symbol_position_snapshot"] = {
                "available": False,
                "reason": "mt5_get_positions_returned_none",
            }
        else:
            result["details"]["same_symbol_position_snapshot"] = {
                "available": True,
                "symbol": symbol,
                "open_position_count": len(positions),
                "tickets": [getattr(pos, "ticket", None) for pos in positions],
            }
    except Exception:
        result["details"]["same_symbol_position_snapshot"] = {
            "available": False,
            "reason": "mt5_snapshot_exception",
        }
    result["details"]["same_symbol_vnext_lifecycle_conflict"] = {
        "runtime_authority": "permissions.check_permissions",
        "status": (
            "rejected"
            if denial
            and denial.gate == "gate3_circuit_breaker"
            and str(denial.reason).startswith("same_symbol_")
            else "not_rejected_or_not_reached"
        ),
    }
    result["details"]["concurrent_cap"] = {
        "runtime_authority": "permissions.check_permissions",
        "status": (
            "rejected"
            if denial
            and denial.gate == "gate3_circuit_breaker"
            and denial.reason == "concurrent_cap_reached"
            else "not_rejected_or_not_reached"
        ),
    }
    result["details"]["cross_instrument_correlation_cluster"] = {
        "runtime_authority": "permissions.check_permissions",
        "status": (
            "rejected"
            if denial
            and denial.gate == "gate3_circuit_breaker"
            and denial.reason == "cross_instrument_correlation_excess"
            else "not_rejected_or_not_reached"
        ),
    }

    if denial and denial.gate == "gate3_circuit_breaker":
        result["passed"] = False
        result["details"]["denial_reason"] = denial.reason
        result["details"]["denial_details"] = denial.details

    return result


def build_gate1_result(denial, analysis, mso) -> dict:
    """Build detailed Gate 1 result dict.

    Called regardless of pass/fail to capture check details.
    """
    checks_run = [
        "grade", "direction", "rr", "tp1_side", "tp1_range",
        "sl_floor", "sl_atr", "sl_max_pct",
    ]

    result = {
        "passed": denial is None or denial.gate != "gate1_safety",
        "checks_run": checks_run,
        "details": {},
    }

    reasoning = getattr(analysis, "reasoning", None)
    tp = getattr(analysis, "trade_parameters", None)

    if reasoning:
        result["details"]["grade"] = reasoning.setup_grade
    if tp:
        result["details"]["direction"] = tp.direction
        result["details"]["rr"] = tp.risk_reward_ratio
        result["details"]["sl_distance"] = abs(tp.entry_price - tp.stop_loss)

    if denial and denial.gate == "gate1_safety":
        result["passed"] = False
        result["details"]["denial_reason"] = denial.reason
        result["details"]["denial_details"] = denial.details

    return result
