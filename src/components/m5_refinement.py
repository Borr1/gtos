"""M5 Entry Refinement — Tighter Stop Loss via M5 Structural Analysis.

After the Primary Analyzer confirms a CANDIDATE on M15, this module calls
Claude Sonnet with 36 M5 candles to identify M5 structural swing points
within the setup zone.  The M5 analysis provides a TIGHTER stop loss,
which makes the 1.5R TP target a smaller dollar distance — more achievable.

Validated on 526 mechanical trades + 14 AI trades.
Result: +0.81R avg vs +0.33R baseline.  TP hit rate: 64% vs 14%.

Entry price is UNCHANGED (market at M15 close).  Only SL and TP are adjusted.
All failure paths fall back to M15 parameters — M5 never blocks a trade.

OB boundary clamp (2026-04-24): When M5 proposes a tighter SL that would
fall INSIDE the H1 OB zone, the SL is clamped to ob.low - buffer (LONG)
or ob.high + buffer (SHORT). Buffer = gate1.ob_retest_sl_min_buffer_atr
* M15_ATR (same multiplier and ATR window as permissions._ob_retest_sl_exception_applies
uses, so L2 re-check and Gate 1 see a consistent buffer).  If the clamp
cannot produce a valid tighter SL (e.g. clamped value is already at/beyond
the pre-M5 SL), the M5 refinement is skipped and the original M15 SL is kept.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from src.components.precision import _decimals_from_format, _snap_to_precision

logger = logging.getLogger(__name__)


def _resolve_price_decimals(full_config: Any, default: int = 2) -> int:
    """Resolve the AI display precision for the active instrument.

    SISTER-3 fix (research/sister_bug_audit_2026-04-27 finding #3): the
    pre-fix code unconditionally called ``round(*, 2)`` on the M5-refined
    SL/TP/distance before writing them back into the trade_parameters via
    ``apply_m5_overrides``. For 5-dp FX (GBPUSD/EURUSD), 3-dp JPY pairs
    (USDJPY/GBPJPY), and any instrument whose underlying quote precision
    exceeds 2dp, this destroyed precision and shipped a corrupted SL/TP
    to MT5 (e.g. GBPUSD SL ``1.27084`` -> ``1.27`` ≈ 12 pips of
    distortion).

    Resolves the per-instrument decimal count from
    ``full_config["prompt"]["price_format"]`` (e.g. ``".5f"`` -> ``5``).
    Falls back to *default* (2) when the config block is missing,
    malformed, or the format is unrecognized — matching the pre-fix
    XAUUSD-correct-by-coincidence behavior so no regression on indices.
    """
    if not isinstance(full_config, dict):
        return default
    fmt = full_config.get("prompt", {}).get("price_format")
    decimals = _decimals_from_format(fmt)
    return decimals if decimals is not None else default

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

M5_SYSTEM_PROMPT_TEMPLATE = (
    "You are an expert {symbol} scalper specializing in M5 entry refinement "
    "within confirmed Smart Money setups. A CANDIDATE trade has already been "
    "confirmed on M15. Your job is to find the tightest valid stop loss based "
    "on M5 structural levels within the setup zone."
)

# Default for backward compatibility
M5_SYSTEM_PROMPT = M5_SYSTEM_PROMPT_TEMPLATE.replace("{symbol}", "gold")


def build_m5_system_prompt(config: dict | None = None) -> str:
    """Build M5 system prompt with instrument-specific identity."""
    if config is None:
        return M5_SYSTEM_PROMPT
    symbol = config.get("market", {}).get("symbol", "XAUUSD")
    label = {"XAUUSD": "gold", "XAGUSD": "silver"}.get(symbol, symbol)
    return M5_SYSTEM_PROMPT_TEMPLATE.replace("{symbol}", label)


def build_m5_user_message(
    direction: str,
    entry_price: float,
    sl_price: float,
    sl_distance: float,
    zone_low: float,
    zone_high: float,
    kz: str,
    m5_candles_formatted: str,
    n_candles: int,
    config: dict | None = None,
) -> str:
    """Build M5 user message with instrument-appropriate formatting."""
    if config is None:
        config = {}
    ob_buffer = config.get("prompt", {}).get("ob_buffer", 1.50)
    price_fmt = config.get("prompt", {}).get("price_format", ".2f")
    symbol = config.get("market", {}).get("symbol", "XAUUSD")

    if symbol in ("EURUSD", "GBPUSD"):
        buffer_display = f"{ob_buffer / 0.0001:.1f} pips"
    elif symbol == "NAS100":
        buffer_display = f"{ob_buffer:.0f} points"
    else:
        buffer_display = f"${ob_buffer:.2f}"

    pf = lambda v: f"{v:{price_fmt}}"

    return f"""\
CONFIRMED M15 SETUP:
- Direction: {direction}
- M15 Entry: {pf(entry_price)}
- M15 SL: {pf(sl_price)} ({pf(sl_distance)} distance)
- Setup zone: {pf(zone_low)} to {pf(zone_high)}
- KZ: {kz}

M5 CANDLES ({n_candles} candles, most recent at bottom):
{m5_candles_formatted}

ANALYSIS INSTRUCTIONS:
1. Examine M5 candles for BOS, CHoCH, or swing structure WITHIN the setup zone {pf(zone_low)} to {pf(zone_high)}. \
Ignore swings outside this zone — even if more recent.
2. For LONG: Find the most recent M5 higher-low or bullish BOS/CHoCH whose swing-low price lies in ({pf(zone_low)}, {pf(zone_high)}). \
SL = swing_low − {buffer_display} buffer.
3. For SHORT: Find the most recent M5 lower-high or bearish BOS/CHoCH whose swing-high price lies in ({pf(zone_low)}, {pf(zone_high)}). \
SL = swing_high + {buffer_display} buffer.
4. The final M5 SL MUST sit STRICTLY in ({pf(zone_low)}, {pf(zone_high)}). \
For LONG: M5 SL must be ABOVE the M15 SL AND BELOW the entry — never above entry, never below M15 SL. \
For SHORT: M5 SL must be ABOVE the entry AND BELOW the M15 SL — never below entry, never above M15 SL. \
If no qualifying swing exists in this exact range, output NO_REFINEMENT — do NOT propose an SL outside this range.
5. Rate the M5 structure quality: HIGH (clean BOS with displacement), \
MEDIUM (visible structure but some overlap), LOW (no clear structure).
6. If no valid M5 structure exists in the zone, output NO_REFINEMENT.

OUTPUT (JSON only, no other text):
{{
  "decision": "REFINED" or "NO_REFINEMENT",
  "m5_quality": "HIGH" or "MEDIUM" or "LOW",
  "m5_sl": <price or null>,
  "m5_sl_distance": <distance or null>,
  "m5_structure": "bos" or "choch" or "higher_low" or "lower_high" or null,
  "reasoning": "<1-2 sentences>"
}}"""

# Legacy template for backward compatibility with code that uses .format()
M5_USER_TEMPLATE = """\
CONFIRMED M15 SETUP:
- Direction: {direction}
- M15 Entry: ${entry_price:.2f}
- M15 SL: ${sl_price:.2f} (${sl_distance:.2f} distance)
- Setup zone: ${zone_low:.2f} to ${zone_high:.2f}
- KZ: {kz}

M5 CANDLES ({n_candles} candles, most recent at bottom):
{m5_candles_formatted}

ANALYSIS INSTRUCTIONS:
1. Examine M5 candles for BOS, CHoCH, or swing structure WITHIN the setup zone ${zone_low:.2f} to ${zone_high:.2f}. \
Ignore swings outside this zone — even if more recent.
2. For LONG: Find the most recent M5 higher-low or bullish BOS/CHoCH whose swing-low price lies in (${zone_low:.2f}, ${zone_high:.2f}). \
SL = swing_low − $1.50 buffer.
3. For SHORT: Find the most recent M5 lower-high or bearish BOS/CHoCH whose swing-high price lies in (${zone_low:.2f}, ${zone_high:.2f}). \
SL = swing_high + $1.50 buffer.
4. The final M5 SL MUST sit STRICTLY in (${zone_low:.2f}, ${zone_high:.2f}). \
For LONG: M5 SL must be ABOVE the M15 SL AND BELOW the entry — never above entry, never below M15 SL. \
For SHORT: M5 SL must be ABOVE the entry AND BELOW the M15 SL — never below entry, never above M15 SL. \
If no qualifying swing exists in this exact range, output NO_REFINEMENT — do NOT propose an SL outside this range.
5. Rate the M5 structure quality: HIGH (clean BOS with displacement), \
MEDIUM (visible structure but some overlap), LOW (no clear structure).
6. If no valid M5 structure exists in the zone, output NO_REFINEMENT.

OUTPUT (JSON only, no other text):
{{
  "decision": "REFINED" or "NO_REFINEMENT",
  "m5_quality": "HIGH" or "MEDIUM" or "LOW",
  "m5_sl": <price or null>,
  "m5_sl_distance": <dollars or null>,
  "m5_structure": "bos" or "choch" or "higher_low" or "lower_high" or null,
  "reasoning": "<1-2 sentences>"
}}"""

# ---------------------------------------------------------------------------
# M5 candle formatting
# ---------------------------------------------------------------------------


def _zone_has_swing_candidate(
    direction: str,
    entry: float,
    m15_sl: float,
    m5_candles: list[dict] | None,
) -> bool:
    """Pre-flight: do any M5 candles have a low (LONG) / high (SHORT) inside the setup zone?

    A swing low is, by definition, a candle low; a swing high is a candle high.
    So *necessary* (not sufficient) for the AI to find a valid swing inside
    ``(m15_sl, entry)`` (LONG) / ``(entry, m15_sl)`` (SHORT) is that at least
    one candle low/high already lies inside that range.

    When this returns False, every M5 swing the AI could nominate sits outside
    the zone — the existing ``SL_OUT_OF_RANGE`` guard will reject any proposal
    and fall back to the M15 SL anyway. Skipping the AI call eliminates wasted
    Sonnet spend and the per-cycle WARNING that fires for stale-zone CANDIDATEs
    (e.g. ob_retest limits left pending while price has marched past entry).
    """
    if not m5_candles:
        return False
    if direction == "LONG":
        return any(m15_sl < c["low"] < entry for c in m5_candles)
    return any(entry < c["high"] < m15_sl for c in m5_candles)


def format_m5_candles(m5_candles: list[dict]) -> str:
    """Format M5 candles for the AI prompt.

    Each candle is a dict with keys: time, open, high, low, close, volume.
    """
    lines = []
    for i, c in enumerate(m5_candles):
        body = abs(c["close"] - c["open"])
        if c["close"] > c["open"]:
            tag = "BULL"
        elif c["close"] < c["open"]:
            tag = "BEAR"
        else:
            tag = "DOJI"
        ts = c["time"] if isinstance(c["time"], str) else str(c["time"])
        marker = " ← CURRENT" if i == len(m5_candles) - 1 else ""
        lines.append(
            f"[{i:2d}] {ts} O:{c['open']:.2f} H:{c['high']:.2f} "
            f"L:{c['low']:.2f} C:{c['close']:.2f} body:{body:.2f} "
            f"[{tag}]{marker}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# OB boundary helpers
# ---------------------------------------------------------------------------


def _find_matching_h1_ob(mso, entry_price: float, direction: str,
                          tolerance: float = 0.0) -> Optional[Any]:
    """Find the unmitigated H1 OB whose zone contains *entry_price*.

    Mirrors ``verification._find_matching_ob`` logic but filtered to the
    OB type that matches trade direction (bullish for LONG, bearish for SHORT)
    — same filter ``permissions._ob_retest_sl_exception_applies`` uses.

    Returns ``None`` if mso is missing, has no H1 timeframe, no OBs match,
    or direction is not ``LONG``/``SHORT``.
    """
    if mso is None:
        return None
    timeframes = getattr(mso, "timeframes", None)
    if timeframes is None:
        return None
    h1_tf = timeframes.get("H1") if hasattr(timeframes, "get") else None
    if h1_tf is None:
        return None
    ob_list = getattr(h1_tf, "order_blocks", None) or []
    expected_type = "bullish" if direction == "LONG" else "bearish"
    for ob in ob_list:
        if getattr(ob, "mitigated", False):
            continue
        if getattr(ob, "type", None) != expected_type:
            continue
        if ob.low - tolerance <= entry_price <= ob.high + tolerance:
            return ob
    return None


def _compute_ob_buffer(mso, full_config: dict | None) -> float:
    """Return the absolute-price buffer beyond OB boundary.

    Buffer = ``gate1.ob_retest_sl_min_buffer_atr`` * M15 ATR(14).

    Matches the multiplier and ATR window used by
    ``permissions._ob_retest_sl_exception_applies`` so the clamp's buffer
    and the Gate 1 SL-exception buffer stay in lockstep. Returns 0.0 if
    any input is missing (caller must treat 0 as "no buffer available").
    """
    if full_config is None:
        return 0.0
    gate1_cfg = full_config.get("gate1", {}) if isinstance(full_config, dict) else {}
    min_buffer_mult = gate1_cfg.get("ob_retest_sl_min_buffer_atr", 0.5)

    if mso is None:
        return 0.0
    timeframes = getattr(mso, "timeframes", None)
    if timeframes is None:
        return 0.0
    m15_tf = timeframes.get("M15") if hasattr(timeframes, "get") else None
    m15_atr = getattr(m15_tf, "atr_14", 0) if m15_tf else 0
    m15_atr = m15_atr or 0
    if m15_atr <= 0:
        return 0.0
    return float(m15_atr) * float(min_buffer_mult)


def clamp_m5_sl_to_ob_boundary(
    m5_sl: float,
    entry: float,
    pre_m5_sl: float,
    direction: str,
    matched_ob,
    buffer: float,
) -> dict:
    """Clamp M5-proposed SL so it never lands inside the H1 OB zone.

    Parameters
    ----------
    m5_sl
        The SL proposed by the M5 refinement AI.
    entry
        Trade entry price (M15 close).
    pre_m5_sl
        The original CANDIDATE SL from the primary analyzer (M15 SL).
        Used as the upper bound (LONG) / lower bound (SHORT) beyond which
        no further tightening is possible; if the clamp would produce an
        SL at/beyond that bound, the clamp reports ``feasible=False`` and
        the caller keeps the pre-M5 SL.
    direction
        "LONG" or "SHORT".
    matched_ob
        The H1 OrderBlock matched to this trade (bullish for LONG,
        bearish for SHORT). Must expose ``.low`` and ``.high`` attrs.
        If ``None``, the clamp is a no-op (returns clamped=False, feasible=True).
    buffer
        Absolute-price buffer to keep beyond the OB boundary. Non-negative.

    Returns
    -------
    dict
        ``{
            "clamped_sl": float,          # final SL after clamp
            "clamped": bool,              # True iff we moved m5_sl
            "feasible": bool,             # False means caller should skip M5 refinement entirely
            "reason": str,                # short explanation for logs
            "ob_boundary": float | None,  # ob.low for LONG, ob.high for SHORT
            "applied_buffer": float,      # the buffer actually used (may be 0)
        }``
    """
    buffer = max(float(buffer or 0.0), 0.0)

    if matched_ob is None:
        # No OB data → cannot clamp. Preserve legacy behavior (no-op).
        return {
            "clamped_sl": m5_sl,
            "clamped": False,
            "feasible": True,
            "reason": "no_matched_ob",
            "ob_boundary": None,
            "applied_buffer": buffer,
        }

    ob_low = float(getattr(matched_ob, "low"))
    ob_high = float(getattr(matched_ob, "high"))

    if direction == "LONG":
        # Valid SL must be below ob_low. Required: sl < ob_low - buffer.
        ob_boundary = ob_low
        target = ob_low - buffer
        if m5_sl < target:
            # Already outside OB + buffer → no clamp needed.
            return {
                "clamped_sl": m5_sl,
                "clamped": False,
                "feasible": True,
                "reason": "m5_sl_below_ob_boundary_buffer",
                "ob_boundary": ob_boundary,
                "applied_buffer": buffer,
            }
        # m5_sl >= ob_low - buffer → clamp down to target.
        # Feasibility: clamped SL must stay strictly inside (pre_m5_sl, entry).
        # If target <= pre_m5_sl, the clamp produces a SL equal to or BELOW
        # the pre-M5 SL → no tightening room; caller falls back to M15 SL.
        if target <= pre_m5_sl:
            return {
                "clamped_sl": pre_m5_sl,
                "clamped": False,
                "feasible": False,
                "reason": "clamped_sl_not_tighter_than_pre_m5_sl",
                "ob_boundary": ob_boundary,
                "applied_buffer": buffer,
            }
        if target >= entry:
            # Degenerate: OB boundary - buffer is above entry. Cannot clamp
            # to a valid LONG SL — fall back.
            return {
                "clamped_sl": pre_m5_sl,
                "clamped": False,
                "feasible": False,
                "reason": "ob_boundary_minus_buffer_above_entry",
                "ob_boundary": ob_boundary,
                "applied_buffer": buffer,
            }
        return {
            "clamped_sl": target,
            "clamped": True,
            "feasible": True,
            "reason": "m5_sl_inside_ob_clamped_to_boundary_minus_buffer",
            "ob_boundary": ob_boundary,
            "applied_buffer": buffer,
        }

    # SHORT: Valid SL must be above ob_high. Required: sl > ob_high + buffer.
    ob_boundary = ob_high
    target = ob_high + buffer
    if m5_sl > target:
        return {
            "clamped_sl": m5_sl,
            "clamped": False,
            "feasible": True,
            "reason": "m5_sl_above_ob_boundary_plus_buffer",
            "ob_boundary": ob_boundary,
            "applied_buffer": buffer,
        }
    if target >= pre_m5_sl:
        return {
            "clamped_sl": pre_m5_sl,
            "clamped": False,
            "feasible": False,
            "reason": "clamped_sl_not_tighter_than_pre_m5_sl",
            "ob_boundary": ob_boundary,
            "applied_buffer": buffer,
        }
    if target <= entry:
        return {
            "clamped_sl": pre_m5_sl,
            "clamped": False,
            "feasible": False,
            "reason": "ob_boundary_plus_buffer_below_entry",
            "ob_boundary": ob_boundary,
            "applied_buffer": buffer,
        }
    return {
        "clamped_sl": target,
        "clamped": True,
        "feasible": True,
        "reason": "m5_sl_inside_ob_clamped_to_boundary_plus_buffer",
        "ob_boundary": ob_boundary,
        "applied_buffer": buffer,
    }


# ---------------------------------------------------------------------------
# Core refinement function
# ---------------------------------------------------------------------------


def refine_entry_m5(
    analysis_output,
    m5_candles: list[dict] | None,
    m5_config: dict,
    llm_backend,
    mso=None,
) -> dict:
    """Refine SL using M5 structural analysis.

    Parameters
    ----------
    analysis_output
        PrimaryAnalysisOutput — the full PA result.  Has .trade_parameters.
    m5_candles
        List of M5 candle dicts (time, open, high, low, close, volume).
        Up to 36 candles BEFORE the M15 entry time.
    m5_config
        The ``m5_refinement`` section from agent_config.yaml.
    llm_backend
        LLMBackend instance for making the Sonnet call.
    mso
        MarketStateObject.  Used for the OB boundary clamp so the M5-
        refined SL never ends up inside the matched H1 OB zone (which would
        be L2-rejected post-refinement as REJECTED_L2_POST_M5, destroying
        an otherwise valid CANDIDATE).  If omitted/None, the clamp is a
        no-op and the module preserves its pre-2026-04-24 behavior.

    Returns
    -------
    dict
        ``{"applied": bool, "m5_result": dict, "overrides": dict|None}``
        If applied, *overrides* has keys ``stop_loss``, ``take_profit_1``,
        ``sl_distance``, ``risk_reward_ratio`` and M5 metadata fields.
        The caller is responsible for patching analysis_output.trade_parameters.
    """
    NO_CHANGE = {"applied": False, "m5_result": {}, "overrides": None}

    if not m5_config.get("enabled", False):
        return {**NO_CHANGE, "m5_result": {"decision": "DISABLED"}}

    tp = analysis_output.trade_parameters
    if tp is None:
        return {**NO_CHANGE, "m5_result": {"decision": "NO_TRADE_PARAMS"}}

    if not m5_candles or len(m5_candles) < 12:
        return {**NO_CHANGE, "m5_result": {"decision": "NO_DATA",
                                           "candles_available": len(m5_candles) if m5_candles else 0}}

    direction = tp.direction
    entry = tp.entry_price
    sl = tp.stop_loss
    sl_dist = abs(entry - sl)

    if direction == "LONG":
        zone_low, zone_high = sl, entry
    else:
        zone_low, zone_high = entry, sl

    # ------------------------------------------------------------------
    # Pre-flight zone-overlap check
    # ------------------------------------------------------------------
    # If no M5 candle low (LONG) / high (SHORT) lies inside the setup zone,
    # the AI cannot find a valid in-zone swing — its proposal will land
    # outside (m15_sl, entry) and trip the SL_OUT_OF_RANGE guard below.
    # Skip the API call to avoid wasting a Sonnet round-trip and to suppress
    # the per-cycle WARNING that floods the logs for stale-zone CANDIDATEs
    # (e.g. ob_retest limits still pending while price has marched well past
    # the original entry).
    if not _zone_has_swing_candidate(direction, entry, sl, m5_candles):
        return {**NO_CHANGE, "m5_result": {"decision": "NO_ZONE_STRUCTURE"}}

    # ------------------------------------------------------------------
    # Build prompt and call Sonnet
    # ------------------------------------------------------------------
    formatted = format_m5_candles(m5_candles)
    kz = getattr(analysis_output, "kill_zone", "unknown")

    # Use instrument-aware prompt if full config available, else legacy
    full_config = m5_config.get("_full_config")
    if full_config:
        user_msg = build_m5_user_message(
            direction=direction, entry_price=entry, sl_price=sl,
            sl_distance=sl_dist, zone_low=zone_low, zone_high=zone_high,
            kz=kz, m5_candles_formatted=formatted,
            n_candles=len(m5_candles), config=full_config,
        )
        system_prompt = build_m5_system_prompt(full_config)
    else:
        user_msg = M5_USER_TEMPLATE.format(
            direction=direction, entry_price=entry, sl_price=sl,
            sl_distance=sl_dist, zone_low=zone_low, zone_high=zone_high,
            kz=kz, n_candles=len(m5_candles),
            m5_candles_formatted=formatted,
        )
        system_prompt = M5_SYSTEM_PROMPT

    model = m5_config.get("model", "claude-sonnet-4-6")
    max_tokens = m5_config.get("max_tokens", 500)
    effort = m5_config.get("effort")
    timeout_s = m5_config.get("timeout_seconds", 60 if effort == "max" else 20)

    try:
        llm_response = llm_backend.call(
            system_prompt=system_prompt,
            user_message=user_msg,
            model=model,
            max_tokens=max_tokens,
            timeout=timeout_s,
            effort=effort,
        )
        raw_text = llm_response.text.strip()
    except Exception as exc:
        logger.warning("M5 API call failed: %s — using M15 SL.", exc)
        return {**NO_CHANGE, "m5_result": {"decision": "API_ERROR", "error": str(exc)}}

    # ------------------------------------------------------------------
    # Parse response
    # ------------------------------------------------------------------
    try:
        text = raw_text
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        m5_result: dict[str, Any] = json.loads(text)
    except (json.JSONDecodeError, IndexError):
        # One retry: try to extract JSON from response
        import re
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if match:
            try:
                m5_result = json.loads(match.group())
            except json.JSONDecodeError:
                logger.warning("M5 JSON parse failed on retry. Using M15 SL.")
                return {**NO_CHANGE, "m5_result": {"decision": "PARSE_ERROR",
                                                   "raw": raw_text[:300]}}
        else:
            logger.warning("M5 no JSON found in response. Using M15 SL.")
            return {**NO_CHANGE, "m5_result": {"decision": "PARSE_ERROR",
                                               "raw": raw_text[:300]}}

    # ------------------------------------------------------------------
    # Quality gate
    # ------------------------------------------------------------------
    quality = m5_result.get("m5_quality", "LOW")
    quality_gate = m5_config.get("quality_gate", ["HIGH", "MEDIUM"])

    if m5_result.get("decision") != "REFINED" or quality not in quality_gate:
        logger.info("M5: decision=%s quality=%s — using M15 SL.",
                     m5_result.get("decision"), quality)
        return {**NO_CHANGE, "m5_result": m5_result}

    # ------------------------------------------------------------------
    # Validate M5 SL
    # ------------------------------------------------------------------
    m5_sl = m5_result.get("m5_sl")
    if m5_sl is None:
        return {**NO_CHANGE, "m5_result": m5_result}

    # M5 SL must be between entry and M15 SL
    # Resolve per-instrument price precision so FX prices (5dp USDJPY / GBPUSD)
    # are not truncated to 2dp in WARN messages (cosmetic — no behavior impact).
    _warn_full_config = m5_config.get("_full_config")
    _warn_price_fmt = (
        _warn_full_config.get("prompt", {}).get("price_format", ".2f")
        if isinstance(_warn_full_config, dict) else ".2f"
    )
    _warn_tmpl = ("M5 SL $%(sl){fmt} outside valid range "
                  "[%(lo){fmt}, %(hi){fmt}]. Using M15 SL.").format(fmt=_warn_price_fmt)
    if direction == "LONG":
        if m5_sl >= entry or m5_sl < sl:
            logger.warning(_warn_tmpl, {"sl": m5_sl, "lo": sl, "hi": entry})
            return {**NO_CHANGE, "m5_result": {**m5_result, "decision": "SL_OUT_OF_RANGE"}}
    else:
        if m5_sl <= entry or m5_sl > sl:
            logger.warning(_warn_tmpl, {"sl": m5_sl, "lo": entry, "hi": sl})
            return {**NO_CHANGE, "m5_result": {**m5_result, "decision": "SL_OUT_OF_RANGE"}}

    # ------------------------------------------------------------------
    # OB boundary clamp (2026-04-24)
    # ------------------------------------------------------------------
    # M5 AI may propose an SL that lands INSIDE the H1 OB zone. Without
    # clamping, the post-M5 L2 re-check (orchestrator._log_candle
    # REJECTED_L2_POST_M5) fails sl_beyond_ob and destroys the CANDIDATE —
    # even though the original AI SL was valid. Clamp to ob.low - buffer
    # (LONG) / ob.high + buffer (SHORT) so the L2 re-check always passes.
    # If the clamp cannot produce a valid tighter SL, fall back to M15 SL.
    full_config = m5_config.get("_full_config")
    ob_tol_pct = (full_config.get("verification", {}).get("ob_price_tolerance_pct", 0.002)
                  if isinstance(full_config, dict) else 0.002)
    ob_tolerance = entry * ob_tol_pct if entry > 0 else 0.0

    matched_ob = _find_matching_h1_ob(mso, entry, direction, tolerance=ob_tolerance)
    buffer = _compute_ob_buffer(mso, full_config)

    clamp = clamp_m5_sl_to_ob_boundary(
        m5_sl=m5_sl,
        entry=entry,
        pre_m5_sl=sl,
        direction=direction,
        matched_ob=matched_ob,
        buffer=buffer,
    )
    if not clamp["feasible"]:
        # Clamped SL would violate the OB boundary OR leave no tightening
        # room relative to the M15 SL. Skip M5 refinement entirely; the
        # original CANDIDATE (with its valid AI SL) proceeds unchanged.
        logger.info(
            "M5 clamp: infeasible (%s) — keeping M15 SL (pre_m5_sl=%.5f, "
            "m5_sl=%.5f, ob_boundary=%s, buffer=%.5f).",
            clamp["reason"], sl, m5_sl, clamp["ob_boundary"], clamp["applied_buffer"],
        )
        return {
            **NO_CHANGE,
            "m5_result": {
                **m5_result,
                "decision": "CLAMP_INFEASIBLE",
                "clamp_reason": clamp["reason"],
                "clamp_ob_boundary": clamp["ob_boundary"],
                "clamp_applied_buffer": clamp["applied_buffer"],
            },
        }
    if clamp["clamped"]:
        logger.info(
            "M5 clamp: m5_sl %.5f -> %.5f (ob_boundary=%.5f, buffer=%.5f, "
            "reason=%s).",
            m5_sl, clamp["clamped_sl"], clamp["ob_boundary"],
            clamp["applied_buffer"], clamp["reason"],
        )
    m5_sl_clamp_applied = clamp["clamped"]
    m5_sl_pre_clamp = m5_sl
    m5_sl = clamp["clamped_sl"]

    # Raw distance from MARKET entry (M15 close) to (possibly clamped) M5 SL
    raw_m5_dist = abs(entry - m5_sl)

    # Reject unrealistically tight (<$3)
    if raw_m5_dist < 3.0:
        logger.warning("M5 raw SL distance $%.2f < $3 minimum. Using M15 SL.", raw_m5_dist)
        return {**NO_CHANGE, "m5_result": {**m5_result, "decision": "SL_TOO_TIGHT"}}

    # ------------------------------------------------------------------
    # Apply SL floor: max(raw_m5, floor_dollars, 1.5 × M15 ATR)
    # ------------------------------------------------------------------
    sl_floor = m5_config.get("sl_floor", 10.0)

    # Get ATR from the MSO (passed through trade_params or separately)
    # The permissions module already checks 1.5*ATR, but we enforce it here
    # so the M5 SL never fails Gate 1's ATR check.
    m15_atr = getattr(tp, "_m15_atr", 0) or 0
    atr_floor = 1.5 * m15_atr if m15_atr > 0 else 0

    final_sl_dist = max(raw_m5_dist, sl_floor, atr_floor)

    # Compute final SL and TP from floored distance
    if direction == "LONG":
        final_sl = entry - final_sl_dist
        final_tp = entry + 1.5 * final_sl_dist
    else:
        final_sl = entry + final_sl_dist
        final_tp = entry - 1.5 * final_sl_dist

    # SISTER-3 fix (research/sister_bug_audit_2026-04-27 #3): snap M5-refined
    # SL/TP/distance to the active instrument's display precision instead of
    # the legacy hardcoded ``round(*, 2)``. The 2-dp default destroyed
    # precision for FX (5-dp) and JPY pairs (3-dp) — apply_m5_overrides
    # writes these values directly back into tp.stop_loss/take_profit_1
    # which are then sent to MT5. ``_full_config`` is injected by the
    # orchestrator (orchestrator.py:1163); fall back to 2-dp when absent so
    # the legacy XAUUSD/index behavior remains bit-identical.
    _full_config = m5_config.get("_full_config")
    _decimals = _resolve_price_decimals(_full_config, default=2)
    overrides = {
        "stop_loss": _snap_to_precision(final_sl, _decimals),
        "take_profit_1": _snap_to_precision(final_tp, _decimals),
        "sl_distance": _snap_to_precision(final_sl_dist, _decimals),
        "risk_reward_ratio": 1.5,
        # M5 metadata (informational, not used by execution)
        "m5_refined": True,
        "m5_raw_sl": m5_sl,
        "m5_raw_sl_dist": _snap_to_precision(raw_m5_dist, _decimals),
        "m5_quality": quality,
        "m5_floor_applied": final_sl_dist > raw_m5_dist,
        "m5_structure": m5_result.get("m5_structure"),
        "m5_reasoning": m5_result.get("reasoning", ""),
        # OB boundary clamp metadata
        "m5_ob_clamp_applied": m5_sl_clamp_applied,
        # m5_ob_pre_clamp_sl is debug-only — keep at 5dp so any subsequent
        # post-mortem retains the AI's raw-emit precision verbatim.
        "m5_ob_pre_clamp_sl": round(m5_sl_pre_clamp, 5) if m5_sl_clamp_applied else None,
        "m5_ob_boundary": clamp["ob_boundary"],
        "m5_ob_clamp_buffer": clamp["applied_buffer"],
    }

    logger.info(
        "M5 REFINED: quality=%s structure=%s raw_dist=$%.2f -> floored=$%.2f "
        "(floor=$%.2f, atr_floor=$%.2f). SL=%.2f TP=%.2f",
        quality, m5_result.get("m5_structure"), raw_m5_dist, final_sl_dist,
        sl_floor, atr_floor, final_sl, final_tp,
    )

    return {"applied": True, "m5_result": m5_result, "overrides": overrides}


def apply_m5_overrides(analysis_output, overrides: dict):
    """Patch the trade_parameters on a PrimaryAnalysisOutput with M5 values.

    Modifies in place (Pydantic v2 models are mutable by default).
    Stores original M15 values for audit trail.
    """
    tp = analysis_output.trade_parameters
    if tp is None:
        return

    # Preserve originals
    tp._m15_original_sl = tp.stop_loss
    tp._m15_original_tp1 = tp.take_profit_1
    tp._m15_original_rr = tp.risk_reward_ratio

    # Apply M5 overrides (core trade fields only)
    tp.stop_loss = overrides["stop_loss"]
    tp.take_profit_1 = overrides["take_profit_1"]
    tp.risk_reward_ratio = overrides["risk_reward_ratio"]
