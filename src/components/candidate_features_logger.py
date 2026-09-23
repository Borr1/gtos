"""Candidate Features Shadow Logger — observation-only.

For every AI evaluation (CANDIDATE and NO_TRADE), captures a flat record of
MSO-derived features plus the AI output so that a future ML meta-learner
(research thread "R2 meta-learning") can be trained on real live distribution
data.

This is an observation-only accumulator. It does not gate trades, does not
change any decision, and must never raise into the trading pipeline.

Output: one JSONL line per evaluation appended to
``shadow_logs/candidate_features_log.jsonl``.

Failure isolation:
    Any exception during feature extraction or disk I/O is caught, logged at
    WARNING level with traceback, and swallowed. Trading logic continues.
"""

from __future__ import annotations

import json
import logging
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.components.gtos_vnext_event_fields import enrich_cp281_event_contract_fields

logger = logging.getLogger(__name__)

SHADOW_LOG_PATH = "shadow_logs/candidate_features_log.jsonl"

# Map pa_output.kill_zone -> coarse session tag.
_SESSION_TAGS = {
    "london": "london",
    "ny": "ny",
    "tokyo": "tokyo",
}


def _safe_get(obj: Any, *names: str, default: Any = None) -> Any:
    """Attribute OR key getter that never raises.

    Tries each name sequentially as an attribute (getattr) then as a key
    (__getitem__). Returns ``default`` on any failure.
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


def _tf_state(mso: Any, tf_name: str) -> Any | None:
    """Fetch timeframe state from MSO.timeframes[tf_name] defensively."""
    try:
        tfs = _safe_get(mso, "timeframes", default=None)
        if tfs is None:
            return None
        # Support dict-like and object-like access
        try:
            return tfs.get(tf_name)  # type: ignore[attr-defined]
        except AttributeError:
            pass
        try:
            return tfs[tf_name]  # type: ignore[index]
        except (KeyError, TypeError):
            return None
    except Exception:
        return None


def _structure_direction(tf_state: Any | None) -> str | None:
    if tf_state is None:
        return None
    try:
        structure = getattr(tf_state, "structure", None)
        if structure is None and hasattr(tf_state, "get"):
            structure = tf_state.get("structure")
        if structure is None:
            return None
        return _safe_get(structure, "direction")
    except Exception:
        return None


def _iter_attr_list(obj: Any, name: str) -> list:
    """Return list-ish attribute or []."""
    val = _safe_get(obj, name)
    if val is None:
        return []
    try:
        return list(val)
    except Exception:
        return []


def _unmitigated_obs(tf_state: Any | None) -> list:
    """Return the list of unmitigated OBs for a TF state."""
    if tf_state is None:
        return []
    obs = _iter_attr_list(tf_state, "order_blocks")
    result = []
    for ob in obs:
        try:
            if getattr(ob, "mitigated", False):
                continue
            result.append(ob)
        except Exception:
            continue
    return result


def _unretested_breakers(tf_state: Any | None) -> list:
    """Return unretested breaker blocks for a TF state."""
    if tf_state is None:
        return []
    breakers = _iter_attr_list(tf_state, "breaker_blocks")
    result = []
    for breaker in breakers:
        try:
            if bool(_safe_get(breaker, "is_retested")):
                continue
            result.append(breaker)
        except Exception:
            continue
    return result


def _direction_counts(items: list, field: str) -> dict[str, int]:
    counts = {"bullish": 0, "bearish": 0}
    for item in items:
        direction = _safe_get(item, field)
        if direction in counts:
            counts[direction] += 1
    return counts


def _normalize_string_list(raw: Any) -> list[str]:
    if not isinstance(raw, (list, tuple)):
        return []
    return [str(item) for item in raw if isinstance(item, str) and item]


def _normalize_bool_map(raw: Any) -> dict[str, bool]:
    if not isinstance(raw, dict):
        return {}
    normalized: dict[str, bool] = {}
    for key, value in raw.items():
        if isinstance(key, str) and key:
            normalized[key] = bool(value)
    return normalized


def _ob_midpoint(ob: Any) -> float | None:
    try:
        hi = float(_safe_get(ob, "high"))
        lo = float(_safe_get(ob, "low"))
        return (hi + lo) / 2.0
    except (TypeError, ValueError):
        return None


def _nearest_opposing_ob_touch(
    obs: list,
    price: float | None,
    ai_direction: str | None,
) -> int:
    """Return touch_count of the nearest retest-candidate H1 OB for the AI
    direction.

    ADR-005 / Phase 1 Track A semantics (from
    `research/phase1_xauusd_reverse_engineering/slice_worker.py:107`, the
    ``compute_sl_and_rdenom`` docstring):

        direction=LONG → SL at last opposing (=bearish-from-BUY-view →
        actually a BULLISH OB in a bullish context [...]). The last
        BEARISH candle before an upward break — i.e. the bullish-direction
        OB: a demand zone whose HIGH is the entry and LOW is the SL.

    So despite the misleading "opposing" label Track A inherited from the
    SMC vocabulary, what's actually measured is the **SAME-DIRECTION retest
    OB's** touch_count — the demand zone for a LONG / supply zone for a
    SHORT — i.e. the zone the trade enters on. Its touch_count measures
    how many times that zone has been re-entered since formation. Phase 1
    Track A found fresh (touch=0) zones have ~11× the forward 2R-before-1R
    rate of used (touch≥2) zones (31.7% vs 2.8%, p=5e-16 Bonferroni).

    Mapping:
      LONG  → nearest unmitigated BULLISH H1 OB below price (demand zone
              candidate for retest-entry).
      SHORT → nearest unmitigated BEARISH H1 OB above price (supply zone
              candidate for retest-entry).

    We match Track A's selection precisely: for LONG, require ``ob.low <
    price`` and rank by ``|price - ob.high|``; for SHORT require
    ``ob.high > price`` and rank by ``|price - ob.low|``. When no
    candidate exists, return -1 (ATR-fallback scenario).

    Returns:
      - touch_count of the nearest same-direction retest OB (int, >=0)
      - -1 if no qualifying OB exists, no price available, or direction
        unknown. The aggregator MUST drop -1 rows from touch-strata
        calculations (they represent the atr_fallback SL path, where
        there's no OB to retest).
    """
    if ai_direction not in ("LONG", "SHORT"):
        return -1
    if not obs or price is None:
        return -1

    try:
        price_f = float(price)
    except (TypeError, ValueError):
        return -1

    # Track A selection: same-direction demand/supply zone with the correct
    # side-of-price constraint, ranked by proximity of the ENTRY edge
    # (ob.high for LONG, ob.low for SHORT) to price.
    best_dist = math.inf
    best_touch = -1
    for ob in obs:
        try:
            ob_type = getattr(ob, "type", None)
            if ob_type is None and hasattr(ob, "get"):
                ob_type = ob.get("type")
            hi = float(getattr(ob, "high", 0.0) or 0.0)
            lo = float(getattr(ob, "low", 0.0) or 0.0)
        except Exception:
            continue

        if ai_direction == "LONG":
            if ob_type != "bullish":
                continue
            if lo >= price_f:
                # Demand zone must sit BELOW (or straddle-below) current
                # price to be a retest candidate.
                continue
            dist = abs(price_f - hi)  # entry is ob.high
        else:  # SHORT
            if ob_type != "bearish":
                continue
            if hi <= price_f:
                continue
            dist = abs(price_f - lo)  # entry is ob.low

        if dist < best_dist:
            best_dist = dist
            try:
                best_touch = int(getattr(ob, "touch_count", 0) or 0)
            except Exception:
                best_touch = 0
    return best_touch


def _nearest_ob_distance_atr(
    obs: list,
    price: float | None,
    atr: float | None,
    trade_direction: str | None,
) -> float | None:
    """Compute |price - nearest OB midpoint| / ATR, signed if possible.

    - If ``trade_direction`` is LONG or SHORT, the result is signed such that
      positive = OB is ahead of price in the trade direction (i.e. for LONG,
      OB below price → negative; OB above price → positive).
    - If direction is unknown, returns unsigned magnitude.
    - Returns None if inputs are missing or ATR is zero.
    """
    if not obs or price is None or atr is None:
        return None
    try:
        atr_f = float(atr)
        if atr_f <= 0:
            return None
    except (TypeError, ValueError):
        return None

    best_signed = None
    best_abs = math.inf
    for ob in obs:
        mid = _ob_midpoint(ob)
        if mid is None:
            continue
        diff = mid - float(price)
        dist_abs = abs(diff)
        if dist_abs < best_abs:
            best_abs = dist_abs
            if trade_direction == "LONG":
                # Positive if OB ahead (above) of price for a long
                best_signed = diff
            elif trade_direction == "SHORT":
                # Positive if OB ahead (below) of price for a short
                best_signed = -diff
            else:
                best_signed = dist_abs

    if best_signed is None:
        return None
    try:
        return round(best_signed / atr_f, 6)
    except Exception:
        return None


def _nearest_pool_distance_atr(
    pools: list,
    price: float | None,
    atr: float | None,
    same_side: bool,
    trade_direction: str | None,
) -> float | None:
    """Distance (unsigned, in ATRs) to the nearest liquidity pool on the
    same or opposite side as the trade direction.

    'Same side' for a LONG = 'high' pools (overhead resistance / targets).
    'Same side' for a SHORT = 'low' pools (downside targets).
    Opposite side is the inverse.
    """
    if (not pools) or price is None or atr is None or trade_direction not in ("LONG", "SHORT"):
        return None
    try:
        atr_f = float(atr)
        if atr_f <= 0:
            return None
    except (TypeError, ValueError):
        return None

    long_same = "high"
    long_opp = "low"
    if trade_direction == "LONG":
        target_side = long_same if same_side else long_opp
    else:
        target_side = long_opp if same_side else long_same

    best = None
    for pool in pools:
        side = _safe_get(pool, "side")
        if side != target_side:
            continue
        try:
            p = float(_safe_get(pool, "price"))
        except (TypeError, ValueError):
            continue
        dist = abs(p - float(price)) / atr_f
        if best is None or dist < best:
            best = dist
    if best is None:
        return None
    try:
        return round(best, 6)
    except Exception:
        return None


def _pd_current_zone(pd_obj: Any, price: float | None) -> str | None:
    """Classify current price into premium / discount / equilibrium.

    Uses the fib_50 band when available, else a plain midpoint split.
    """
    if pd_obj is None or price is None:
        return None
    try:
        eq = _safe_get(pd_obj, "equilibrium_50")
        if eq is None:
            return None
        eq_f = float(eq)
        p = float(price)
        # Tight equilibrium band: ±0.1% of price (small but non-zero)
        band = max(abs(eq_f) * 0.0005, 1e-6)
        if p > eq_f + band:
            return "premium"
        if p < eq_f - band:
            return "discount"
        return "equilibrium"
    except Exception:
        return None


def _current_price_approx(mso: Any) -> float | None:
    """Best-effort current price from session_levels / last M15 candle."""
    try:
        levels = _safe_get(mso, "session_levels")
        if levels is not None:
            sh = _safe_get(levels, "session_high")
            sl = _safe_get(levels, "session_low")
            if sh is not None and sl is not None:
                try:
                    return (float(sh) + float(sl)) / 2.0
                except (TypeError, ValueError):
                    pass
    except Exception:
        pass
    return None


def _extract_evaluation_id(symbol: str, timestamp_utc: str) -> str:
    """Generate a stable-ish id from symbol + timestamp.

    Strips colons and other path/shell-unsafe chars so the id is safe
    to use as a filesystem key or CSV column.
    """
    safe_ts = re.sub(r"[^0-9A-Za-z_\-]", "_", timestamp_utc or "")
    safe_sym = re.sub(r"[^0-9A-Za-z_\-]", "_", symbol or "unknown")
    return f"{safe_sym}_{safe_ts}"


def _decision_of(pa_output: Any) -> str | None:
    return _safe_get(pa_output, "decision")


def _trade_parameters_flat(pa_output: Any) -> dict | None:
    """Flatten trade_parameters to a small dict if CANDIDATE; else None."""
    decision = _decision_of(pa_output)
    if decision != "CANDIDATE":
        return None
    tp = _safe_get(pa_output, "trade_parameters")
    if tp is None:
        return None
    out: dict[str, Any] = {
        "direction": _safe_get(tp, "direction"),
        "entry_price": _safe_get(tp, "entry_price"),
        "stop_loss": _safe_get(tp, "stop_loss"),
        "take_profit_1": _safe_get(tp, "take_profit_1"),
        "risk_reward_ratio": _safe_get(tp, "risk_reward_ratio"),
    }
    return out


def _build_row(
    pa_output: Any,
    mso: Any,
    symbol: str,
    evaluation_id: str,
    timestamp_utc: str,
    candle_close_utc: str | None,
    session_state: dict | None,
    pre_ai_gate_skipped: bool = False,
    pre_ai_gate_reason: str | None = None,
    ai_direction_evaluated: str | None = None,
    detector_version_at_eval: str | None = None,
    slice_tag: str | None = None,
    pre_ai_gate_bias: str | None = None,
    pre_ai_gate_enabled_frameworks: list[str] | None = None,
    pre_ai_gate_framework_poi_availability: dict[str, bool] | None = None,
) -> dict:
    """Assemble one flat dict representing this evaluation.

    All per-field extraction is wrapped so a single bad value cannot abort
    the whole row — missing fields become ``None`` in JSON.
    """
    # ── Identification ────────────────────────────────────────────────
    kill_zone = None
    if isinstance(session_state, dict):
        kill_zone = session_state.get("kill_zone")
    if kill_zone is None:
        kill_zone = _safe_get(pa_output, "kill_zone")
    session_tag = _SESSION_TAGS.get(kill_zone) if isinstance(kill_zone, str) else None

    day_of_week = None
    hour_utc = None
    candle_day_of_week = None
    candle_hour_utc = None
    timestamp_candle_lag_seconds = None
    try:
        ts_clean = (timestamp_utc or "").replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts_clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        day_of_week = dt.weekday()
        hour_utc = dt.hour
        if candle_close_utc:
            candle_clean = candle_close_utc.replace("Z", "+00:00")
            candle_dt = datetime.fromisoformat(candle_clean)
            if candle_dt.tzinfo is None:
                candle_dt = candle_dt.replace(tzinfo=timezone.utc)
            candle_day_of_week = candle_dt.weekday()
            candle_hour_utc = candle_dt.hour
            timestamp_candle_lag_seconds = (
                dt.astimezone(timezone.utc) - candle_dt.astimezone(timezone.utc)
            ).total_seconds()
    except Exception:
        pass

    # ── AI output ─────────────────────────────────────────────────────
    decision = _decision_of(pa_output)
    framework = _safe_get(pa_output, "framework")
    no_trade_reason = _safe_get(pa_output, "no_trade_reason")
    reasoning = _safe_get(pa_output, "reasoning")
    setup_grade = _safe_get(reasoning, "setup_grade") if reasoning is not None else None

    daily_bias = _safe_get(reasoning, "daily_bias") if reasoning is not None else None
    daily_bias_direction = _safe_get(daily_bias, "direction") if daily_bias is not None else None
    daily_bias_confidence = _safe_get(daily_bias, "confidence") if daily_bias is not None else None

    h4_alignment = _safe_get(reasoning, "h4_alignment") if reasoning is not None else None
    h4_aligned = _safe_get(h4_alignment, "aligned") if h4_alignment is not None else None

    m15_confirmation = _safe_get(reasoning, "m15_confirmation") if reasoning is not None else None
    m15_choch = _safe_get(m15_confirmation, "choch_detected") if m15_confirmation is not None else None

    # T7 "C-gate result" — the model output does not expose discrete C1/C2/C3
    # fields (the C-gate lives in the prompt, not the pydantic schema). We
    # reconstruct the two checks we can derive from the PA output:
    #   - c1_h1_bias_present: True if daily_bias direction is not 'ranging'
    #   - c3_direction_matches: True if trade direction matches daily bias
    c_gate = {
        "c1_h1_bias_present": (daily_bias_direction not in (None, "ranging")),
        "c2_m15_choch_detected": m15_choch,
        "c3_direction_matches": None,
    }
    tp = _safe_get(pa_output, "trade_parameters")
    tp_direction = _safe_get(tp, "direction") if tp is not None else None
    if tp_direction and daily_bias_direction:
        wanted = "LONG" if daily_bias_direction == "bullish" else (
            "SHORT" if daily_bias_direction == "bearish" else None
        )
        if wanted is not None:
            c_gate["c3_direction_matches"] = (tp_direction == wanted)

    # ── MSO: structure directions ─────────────────────────────────────
    h1_state = _tf_state(mso, "H1")
    m15_state = _tf_state(mso, "M15")
    d1_state = _tf_state(mso, "D1")

    h1_dir = _structure_direction(h1_state)
    m15_dir = _structure_direction(m15_state)
    d1_dir = _structure_direction(d1_state)

    # ── MSO: OB context (H1) ──────────────────────────────────────────
    h1_un_obs = _unmitigated_obs(h1_state)
    h1_ob_count = len(h1_un_obs)
    h1_ob_direction_counts = _direction_counts(h1_un_obs, "type")
    h1_unretested_breakers = _unretested_breakers(h1_state)
    h1_breaker_direction_counts = _direction_counts(h1_unretested_breakers, "direction")
    h1_touch_counts: list[int] = []
    for ob in h1_un_obs:
        try:
            tc = int(getattr(ob, "touch_count", 0) or 0)
        except Exception:
            tc = 0
        h1_touch_counts.append(tc)

    # ATRs
    def _atr_of(tf):
        if tf is None:
            return None
        try:
            return float(_safe_get(tf, "atr_14"))
        except (TypeError, ValueError):
            return None

    h1_atr = _atr_of(h1_state)
    m15_atr = _atr_of(m15_state)
    d1_atr = _atr_of(d1_state)

    # Current price for proximity
    price = _current_price_approx(mso)
    # Prefer trade_parameters.entry_price for signed direction context if CANDIDATE
    if price is None and tp is not None:
        try:
            ep = _safe_get(tp, "entry_price")
            if ep is not None:
                price = float(ep)
        except (TypeError, ValueError):
            pass

    nearest_ob_dist_atr = _nearest_ob_distance_atr(
        h1_un_obs, price, m15_atr or h1_atr, tp_direction
    )

    # ADR-005 / A1 backtest validation — opposing-OB touch count.
    # Prefer the caller-provided ai_direction_evaluated (set by the
    # orchestrator / simulator from deterministic bias BEFORE the AI call).
    # Fall back to tp_direction when a CANDIDATE was returned.
    # Log BOTH LONG and SHORT perspectives when direction is unknown so the
    # aggregator can stratify either way.
    _direction_for_opp_touch = (
        ai_direction_evaluated if ai_direction_evaluated in ("LONG", "SHORT")
        else tp_direction
    )
    h1_opp_ob_touch = _nearest_opposing_ob_touch(
        h1_un_obs, price, _direction_for_opp_touch
    )
    h1_opp_ob_touch_long = _nearest_opposing_ob_touch(h1_un_obs, price, "LONG")
    h1_opp_ob_touch_short = _nearest_opposing_ob_touch(h1_un_obs, price, "SHORT")

    # ── MSO: FVG counts ───────────────────────────────────────────────
    def _unfilled(tf):
        if tf is None:
            return []
        fvgs = _iter_attr_list(tf, "fair_value_gaps")
        out = []
        for f in fvgs:
            try:
                if getattr(f, "filled", False):
                    continue
                out.append(f)
            except Exception:
                continue
        return out

    h1_unfilled_fvgs = _unfilled(h1_state)
    m15_unfilled_fvgs = _unfilled(m15_state)
    h1_fvg_count = len(h1_unfilled_fvgs)
    m15_fvg_count = len(m15_unfilled_fvgs)
    h1_fvg_direction_counts = _direction_counts(h1_unfilled_fvgs, "type")
    m15_fvg_direction_counts = _direction_counts(m15_unfilled_fvgs, "type")

    # ── MSO: Liquidity pools ──────────────────────────────────────────
    pools = _iter_attr_list(mso, "liquidity_pools")
    pool_count_by_type: dict[str, int] = {}
    if pools:
        try:
            pool_count_by_type = dict(
                Counter(_safe_get(p, "type") for p in pools if _safe_get(p, "type") is not None)
            )
        except Exception:
            pool_count_by_type = {}

    atr_for_pool = m15_atr or h1_atr
    same_side_dist = _nearest_pool_distance_atr(pools, price, atr_for_pool, True, tp_direction)
    opp_side_dist = _nearest_pool_distance_atr(pools, price, atr_for_pool, False, tp_direction)

    # ── MSO: Premium / Discount ───────────────────────────────────────
    pd_obj = _safe_get(h1_state, "premium_discount") if h1_state is not None else None
    pd_eq50 = None
    try:
        if pd_obj is not None:
            pd_eq50_val = _safe_get(pd_obj, "equilibrium_50")
            pd_eq50 = float(pd_eq50_val) if pd_eq50_val is not None else None
    except (TypeError, ValueError):
        pd_eq50 = None
    pd_zone = _pd_current_zone(pd_obj, price)

    # ── MSO: Microstructure (M15 order-flow proxies) ──────────────────
    m15_clv_current = _safe_get(m15_state, "clv_current")
    m15_clv_avg_5 = _safe_get(m15_state, "clv_avg_5")
    m15_bvc_buy = _safe_get(m15_state, "bvc_buy_fraction")
    m15_net_flow_5 = _safe_get(m15_state, "net_flow_5")
    m15_sess_vol_ratio = _safe_get(m15_state, "session_vol_ratio") if symbol == "XAUUSD" else None

    # ── MSO: Sweeps ───────────────────────────────────────────────────
    sweeps = _iter_attr_list(mso, "detected_sweeps")
    sweep_count = len(sweeps)
    sweep_types: list[str] = []
    for s in sweeps:
        try:
            pool = _safe_get(s, "pool")
            pt = _safe_get(pool, "type") if pool is not None else None
            if pt is not None:
                sweep_types.append(pt)
        except Exception:
            continue

    pre_ai_frameworks = _normalize_string_list(pre_ai_gate_enabled_frameworks)
    pre_ai_framework_poi_availability = _normalize_bool_map(pre_ai_gate_framework_poi_availability)
    pre_ai_empty_frameworks = [
        framework
        for framework in pre_ai_frameworks
        if pre_ai_framework_poi_availability.get(framework) is False
    ]
    pre_ai_any_framework_has_poi = (
        any(pre_ai_framework_poi_availability.values())
        if pre_ai_framework_poi_availability
        else None
    )

    row: dict[str, Any] = {
        "schema_version": "candidate_features_log_v1",
        # Identification
        "timestamp_utc": timestamp_utc,
        "candle_close_utc": candle_close_utc,
        "symbol": symbol,
        "evaluation_id": evaluation_id,
        "kill_zone": kill_zone,
        "session_tag": session_tag,
        "day_of_week": day_of_week,
        "hour_utc": hour_utc,
        "candle_day_of_week": candle_day_of_week,
        "candle_hour_utc": candle_hour_utc,
        "timestamp_candle_lag_seconds": timestamp_candle_lag_seconds,

        # AI output
        "decision": decision,
        "framework": framework,
        "setup_grade": setup_grade,
        "c_gate_result": c_gate,
        "daily_bias_direction": daily_bias_direction,
        "daily_bias_confidence": daily_bias_confidence,
        "h4_aligned": h4_aligned,
        "m15_choch_detected": m15_choch,
        "trade_parameters": _trade_parameters_flat(pa_output),

        # ADR-005 / A1 backtest validation — additive stable field names.
        # These mirror existing fields (decision / mso_h1_fvg_count /
        # mso_m15_fvg_count) under the canonical names the ADR-005 analyzer
        # expects, plus touch/direction/provenance that the legacy row lacked.
        "ai_decision": decision,
        "ai_no_trade_reason": no_trade_reason,
        "ai_direction_evaluated": (
            ai_direction_evaluated if ai_direction_evaluated in ("LONG", "SHORT", "UNCLEAR")
            else tp_direction
        ),
        "h1_opp_ob_touch": h1_opp_ob_touch,
        "h1_opp_ob_touch_long": h1_opp_ob_touch_long,
        "h1_opp_ob_touch_short": h1_opp_ob_touch_short,
        "h1_fvg_unfilled_count": h1_fvg_count,
        "m15_fvg_unfilled_count": m15_fvg_count,
        "detector_version_at_eval": detector_version_at_eval,
        "slice_tag": slice_tag,

        # MSO — structure
        "mso_h1_structure_direction": h1_dir,
        "mso_m15_structure_direction": m15_dir,
        "mso_d1_structure_direction": d1_dir,

        # MSO — OB context
        "mso_h1_unmitigated_ob_count": h1_ob_count,
        "mso_h1_unmitigated_ob_count_bullish": h1_ob_direction_counts["bullish"],
        "mso_h1_unmitigated_ob_count_bearish": h1_ob_direction_counts["bearish"],
        "mso_h1_ob_touch_counts": h1_touch_counts,
        "mso_h1_nearest_ob_distance_atr": nearest_ob_dist_atr,
        "mso_h1_unretested_breaker_count": len(h1_unretested_breakers),
        "mso_h1_unretested_breaker_count_bullish": h1_breaker_direction_counts["bullish"],
        "mso_h1_unretested_breaker_count_bearish": h1_breaker_direction_counts["bearish"],

        # MSO — FVGs
        "mso_h1_fvg_count": h1_fvg_count,
        "mso_h1_fvg_count_bullish": h1_fvg_direction_counts["bullish"],
        "mso_h1_fvg_count_bearish": h1_fvg_direction_counts["bearish"],
        "mso_m15_fvg_count": m15_fvg_count,
        "mso_m15_fvg_count_bullish": m15_fvg_direction_counts["bullish"],
        "mso_m15_fvg_count_bearish": m15_fvg_direction_counts["bearish"],

        # MSO — Liquidity pools
        "mso_pool_count_by_type": pool_count_by_type,
        "mso_nearest_same_side_pool_distance_atr": same_side_dist,
        "mso_nearest_opposite_side_pool_distance_atr": opp_side_dist,

        # MSO — ATR
        "mso_h1_atr_14": h1_atr,
        "mso_m15_atr_14": m15_atr,
        "mso_d1_atr_14": d1_atr,

        # MSO — Premium/Discount
        "mso_pd_equilibrium_50": pd_eq50,
        "mso_pd_current_zone": pd_zone,

        # MSO — Microstructure (M15)
        "mso_m15_clv_current": m15_clv_current,
        "mso_m15_clv_avg_5": m15_clv_avg_5,
        "mso_m15_bvc_buy_fraction": m15_bvc_buy,
        "mso_m15_net_flow_5": m15_net_flow_5,
        "mso_m15_session_vol_ratio": m15_sess_vol_ratio,

        # MSO — Sweeps
        "mso_detected_sweeps_count": sweep_count,
        "mso_detected_sweeps_types": sweep_types,

        # Pre-AI-gate visibility (Thursday 2026-04-23 audit, bug 5)
        # When the H1 POI availability gate (``pre_ai_gates.py``) short-
        # circuits before the AI call, this row is still written so the
        # gated-candle distribution is visible to downstream audit
        # tooling. Consumers filter by ``pre_ai_gate_skipped``.
        "pre_ai_gate_skipped": bool(pre_ai_gate_skipped),
        "pre_ai_gate_reason": pre_ai_gate_reason,
        "pre_ai_gate_bias": pre_ai_gate_bias,
        "pre_ai_gate_enabled_frameworks": pre_ai_frameworks,
        "pre_ai_gate_framework_poi_availability": pre_ai_framework_poi_availability,
        "pre_ai_gate_empty_frameworks": pre_ai_empty_frameworks,
        "pre_ai_gate_any_framework_has_poi": pre_ai_any_framework_has_poi,
    }
    return enrich_cp281_event_contract_fields(
        row,
        source_path=SHADOW_LOG_PATH,
        default_source_component="candidate_features_logger",
    )


def log_candidate_features(
    pa_output: Any,
    mso: Any,
    symbol: str,
    evaluation_id: str | None = None,
    timestamp_utc: str | None = None,
    candle_close_utc: str | None = None,
    session_state: dict | None = None,
    log_path: str | None = None,
    pre_ai_gate_skipped: bool = False,
    pre_ai_gate_reason: str | None = None,
    ai_direction_evaluated: str | None = None,
    detector_version_at_eval: str | None = None,
    slice_tag: str | None = None,
    pre_ai_gate_bias: str | None = None,
    pre_ai_gate_enabled_frameworks: list[str] | None = None,
    pre_ai_gate_framework_poi_availability: dict[str, bool] | None = None,
) -> None:
    """Append one JSONL line capturing MSO features + AI output.

    Observation-only. Any exception is caught and logged as a WARNING —
    this function must NEVER raise into trading logic.

    Args:
        pa_output: PrimaryAnalysisOutput-like object (has .decision, .framework,
            .reasoning, .trade_parameters, .kill_zone). May be None when
            the pre-AI gate short-circuits — in that case the AI-output
            fields are None but the MSO fields are still populated.
        mso: MarketStateObject-like (has .timeframes, .liquidity_pools,
            .detected_sweeps, .session_levels).
        symbol: Trading symbol, e.g. "XAUUSD".
        evaluation_id: Optional explicit id; defaults to symbol + timestamp.
        timestamp_utc: ISO-8601 UTC string. Defaults to now() if None.
        candle_close_utc: Canonical M15 candle close timestamp when known.
            This is shadow-only and is preferred by validation joins; the
            legacy ``timestamp_utc`` remains the wall-clock evaluation time.
        session_state: Optional dict; we read ``kill_zone`` from it if present.
        log_path: Override output path (used by tests).
        pre_ai_gate_skipped: Thursday 2026-04-23 audit (bug 5). True when
            this row captures a candle where a pre-AI gate suppressed the
            AI call. Downstream consumers filter by this flag to audit
            what the gate suppresses without confusing gated-rows with
            AI-evaluated rows.
        pre_ai_gate_reason: Which gate skipped (e.g.
            ``"no_unmitigated_h1_pois"``). Meaningful only when
            ``pre_ai_gate_skipped`` is True.
        ai_direction_evaluated: Deterministic bias direction the AI was
            asked to evaluate for this candle (``"LONG"`` / ``"SHORT"`` /
            ``"UNCLEAR"``). When a CANDIDATE is returned and this is None,
            we fall back to ``trade_parameters.direction``. ADR-005.
        detector_version_at_eval: MSO structure detector version in effect
            during this candle (``"v1"`` / ``"v2_shadow"`` / ``"v2"``),
            from ``config.market_state.detector_version``. Logged so
            A1 backtest rows are attributable if the v2_shadow promotion
            changes the OB / structure distribution. ADR-005.
        slice_tag: Free-form string to attribute rows to a specific
            parallel-backtest slice (e.g. ``"xauusd_s3"``). Used by
            ``research/a1_adr005_backtest/analyze.py`` to merge slice logs
            while retaining provenance.
        pre_ai_gate_bias: Deterministic bias supplied to the pre-AI POI gate
            when the logger is called from a gated path.
        pre_ai_gate_enabled_frameworks: Frameworks evaluated by the pre-AI
            gate at this decision point.
        pre_ai_gate_framework_poi_availability: Framework -> POI-present map
            computed with the same helper used by the pre-AI gate.
    """
    try:
        ts = timestamp_utc or datetime.now(timezone.utc).isoformat()
        canonical_ts = candle_close_utc or _safe_get(mso, "candle_close_utc")
        eid = evaluation_id or _extract_evaluation_id(symbol, str(canonical_ts or ts))

        row = _build_row(
            pa_output, mso, symbol, eid, ts, str(canonical_ts) if canonical_ts else None, session_state,
            pre_ai_gate_skipped=pre_ai_gate_skipped,
            pre_ai_gate_reason=pre_ai_gate_reason,
            ai_direction_evaluated=ai_direction_evaluated,
            detector_version_at_eval=detector_version_at_eval,
            slice_tag=slice_tag,
            pre_ai_gate_bias=pre_ai_gate_bias,
            pre_ai_gate_enabled_frameworks=pre_ai_gate_enabled_frameworks,
            pre_ai_gate_framework_poi_availability=pre_ai_gate_framework_poi_availability,
        )

        path = Path(log_path or SHADOW_LOG_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    except Exception as exc:  # noqa: BLE001 — must never raise
        logger.warning("candidate_features_logger failed: %s", exc, exc_info=True)
