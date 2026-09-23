#!/usr/bin/env python3
"""Simulate T7 C-gate prompt on the live trading period (April 7-12, 2026).

Evaluates every kill-zone M15 candle with the deployed T7 prompt and compares
against what P2A v1 actually decided (from live evaluation logs).

Usage:
    # Option A: From MT5 (run on Windows machine)
    python scripts/simulate_t7_live_period.py --source mt5

    # Option B: From TradingView CSV exports (run anywhere)
    # First export M15/H1/H4/D1 CSVs covering Apr 1-12 for each instrument
    # Save to data/historical/{SYMBOL}_{TF}.csv
    python scripts/simulate_t7_live_period.py --source csv

    # Dry run: build MSOs and count candles, don't call API
    python scripts/simulate_t7_live_period.py --source csv --dry-run

    # Single instrument
    python scripts/simulate_t7_live_period.py --source csv --symbol XAUUSD

    # Custom dates
    python scripts/simulate_t7_live_period.py --source csv --start 2026-04-07 --end 2026-04-12

    # Budget cap (default $10)
    python scripts/simulate_t7_live_period.py --source csv --budget 5

Cost estimate: ~$0.015 per evaluation × ~100 candles/instrument × 5 instruments = ~$7.50
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time as time_mod
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from src.components.gtos_vnext_runtime import (  # noqa: E402
    normalize_vnext_symbol_key,
    resolve_vnext_symbol_family,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────

SYMBOLS = ["XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"]
RAW_CANDIDATE_DECISIONS = (
    "CANDIDATE",
    "REJECTED_L2",
    "BLOCKED_LIMIT",
    "NO_TRADE_PARSE_FAIL",
    "NO_TRADE_LIVE_GUARD",
)

# Kill zone windows (UTC) per instrument
KZ_WINDOWS = {
    "XAUUSD":    {"london": (time(7, 0), time(10, 30)), "ny": (time(13, 0), time(17, 0))},
    "US30_cash": {"london": (time(8, 0), time(10, 30)), "ny": (time(13, 30), time(16, 0))},
    "USDJPY":    {"london": (time(7, 0), time(9, 30)),  "ny": (time(13, 0), time(15, 30)), "tokyo": (time(0, 0), time(3, 0))},
    "GBPJPY":    {"london": (time(7, 0), time(9, 30)),  "ny": (time(13, 0), time(15, 30)), "tokyo": (time(0, 0), time(3, 0))},
    "GBPUSD":    {"london": (time(7, 0), time(12, 0)),  "ny": (time(13, 0), time(15, 30))},
    # Research-only (added 2026-04-18 for elephant-alpha batch sim):
    "EURUSD":    {"london": (time(7, 0), time(12, 0)),  "ny": (time(13, 0), time(15, 30))},
    # Tier 2 instrument expansion validation (added 2026-04-25 for XAGUSD F3 backtest):
    # Base config XAUUSD KZ leaks via deep_merge (london remains 07:00-10:30); XAGUSD's
    # explicit override defines NY 13:00-17:00 (extended end per config comment "Extended
    # from 15:30 — 48.6% cont, 1.02 MFE/MAE"). Mirroring the actual production-merged config.
    "XAGUSD":    {"london": (time(7, 0), time(10, 30)), "ny": (time(13, 0), time(17, 0))},
    # Tier 2 NAS100 (updated 2026-04-25 for F3 backtest). agent_config.yaml NAS100 only
    # explicitly overrides NY (13:00-17:00, "Extended from 15:30 — 50.4% cont, 1.04 MFE/MAE").
    # Base XAUUSD london 07:00-10:30 leaks via deep_merge -> live merged config has
    # london 07:00-10:30 + ny 13:00-17:00. Prior research-only entry used US30-style
    # (london 08:00-10:30 + ny 13:30-16:00), which does NOT match what live NAS100 trades.
    "NAS100":    {"london": (time(7, 0), time(10, 30)), "ny": (time(13, 0), time(17, 0))},
    # Tier 2 UK100 / FTSE 100 (added 2026-04-25 for tier2_uk100 F3 backtest).
    # Per CEO task brief + research/instrument_expansion_2026-04-25/03_MICROSTRUCTURE.md:
    #   London 08:00-12:00 UTC (FTSE cash open 08:00 GMT / 07:00 BST during DST;
    #     covers London-late mini-peak 10:00-12:00 = 13.3% of daily motion);
    #   NY-afternoon 14:00-19:00 UTC (peak 25.2% concentrated 15:00-19:00).
    "UK100":     {"london": (time(8, 0), time(12, 0)),  "ny": (time(14, 0), time(19, 0))},
}

OUTPUT_DIR = _PROJECT_ROOT / "research" / "t7_live_simulation"

# API cost (Sonnet 4.6 with effort=max)
INPUT_COST_PER_TOK = 3.0 / 1_000_000
OUTPUT_COST_PER_TOK = 15.0 / 1_000_000

# Fill-check epsilon per instrument (2 × tick_size in price units).
# A candle_close within epsilon of entry is treated as "at-market" (always fills).
# For honest limit-order simulation this MUST scale with instrument tick size — a
# single constant 0.05 was correct for XAUUSD/indices but ~500 pips on EURUSD.
# Unknown symbols fall back to 0.05 with a WARNING log (see _epsilon_for_symbol).
EPSILON_BY_SYMBOL = {
    "XAUUSD":    0.20,      # 2 × 0.10 tick
    "US30":      2.0,       # 2 × 1.0 tick
    "US30_cash": 2.0,       # alias used in SYMBOLS
    "NAS100":    2.0,       # 2 × 1.0 tick
    "USDJPY":    0.02,      # 2 × 0.01 tick (≈ 2 pips)
    "GBPJPY":    0.02,      # 2 × 0.01 tick (≈ 2 pips)
    "EURUSD":    0.0002,    # 2 × 0.00001 tick (≈ 2 pips)
    "GBPUSD":    0.0002,    # 2 × 0.00001 tick (≈ 2 pips)
    "XAGUSD":    0.002,     # 2 × 0.001 tick (silver tick = 0.001)
    "SPX500":    0.50,      # 2 x 0.25 ES family tick
    "US500":     0.50,      # broker alias for SPX500/ES family
    "UK100":     0.2,       # 2 × 0.1 tick (FTSE 100 broker tick = 0.1 pt)
}
EPSILON_SYMBOL_BY_VNEXT_FAMILY = {
    "EURUSD_6E_FAMILY": "EURUSD",
    "GBPUSD_6B_FAMILY": "GBPUSD",
    "NAS100_NQ_FAMILY": "NAS100",
    "SPX500_ES_FAMILY": "SPX500",
    "US30_YM_FAMILY": "US30",
    "USDJPY_6J_FAMILY": "USDJPY",
    "XAGUSD_SILVER_FAMILY": "XAGUSD",
    "XAUUSD_GC_FAMILY": "XAUUSD",
}
_DEFAULT_FILL_EPSILON = 0.05  # legacy fallback; emits WARNING
_EPSILON_WARNED: set[str] = set()


def _epsilon_lookup_keys(symbol: str | None) -> tuple[str, ...]:
    if symbol is None:
        return ()
    raw = str(symbol).strip()
    if not raw:
        return ()
    family = resolve_vnext_symbol_family(raw)
    return tuple(dict.fromkeys((
        raw,
        raw.upper(),
        normalize_vnext_symbol_key(raw),
        EPSILON_SYMBOL_BY_VNEXT_FAMILY.get(family, ""),
    )))


def _epsilon_for_symbol(symbol: str | None) -> float:
    """Return the at-market fill epsilon for `symbol`, warning once on unknowns."""
    for lookup_key in _epsilon_lookup_keys(symbol):
        if lookup_key in EPSILON_BY_SYMBOL:
            return EPSILON_BY_SYMBOL[lookup_key]
    key = symbol or "<missing>"
    if key not in _EPSILON_WARNED:
        logger.warning(
            "No per-instrument _FILL_EPSILON for symbol=%s; using legacy default %s. "
            "Counterfactual outcomes may be inflated on non-gold/non-index tick sizes.",
            key, _DEFAULT_FILL_EPSILON,
        )
        _EPSILON_WARNED.add(key)
    return _DEFAULT_FILL_EPSILON

# ── Data loading ─────────────────────────────────────────────────────────

def _apply_live_candidate_output_guards(result: dict, pa_obj):
    """Apply live PrimaryAnalyzer candidate-output guards to replay results."""
    if result.get("decision") != "CANDIDATE" or pa_obj is None:
        return result, pa_obj

    from src.components.primary_analyzer import (
        guard_candidate_degenerate_params,
        guard_candidate_null_params,
        guard_candidate_wrong_side_sl,
    )

    guarded = guard_candidate_null_params(pa_obj)
    guarded = guard_candidate_degenerate_params(guarded)
    guarded = guard_candidate_wrong_side_sl(guarded)
    if guarded.decision == "CANDIDATE":
        return result, guarded

    reason = guarded.no_trade_reason or guarded.wait_reason or "live_candidate_output_guard"
    result["decision"] = "NO_TRADE_LIVE_GUARD"
    result["no_trade_reason"] = reason
    result["live_guard_demoted"] = True
    result["live_guard_reason"] = reason
    result["l2_passed"] = "skipped"
    result["l2_reason"] = f"live_candidate_output_guard:{reason}"
    return result, guarded


def load_csv_data(symbol: str, data_dir: str | None = None) -> dict[str, list[dict]]:
    """Load TradingView CSVs for all timeframes."""
    from scripts.historical_data_loader import parse_tradingview_csv
    historical_dir = Path(data_dir) if data_dir else _PROJECT_ROOT / "data" / "historical_2026"
    candles = {}
    for tf in ("D1", "H4", "H1", "M15"):
        csv_path = historical_dir / f"{symbol}_{tf}.csv"
        if csv_path.exists():
            candles[tf] = parse_tradingview_csv(csv_path)
            logger.info("Loaded %s %s: %d candles (%s to %s)",
                        symbol, tf, len(candles[tf]),
                        candles[tf][0]["time"][:10] if candles[tf] else "?",
                        candles[tf][-1]["time"][:10] if candles[tf] else "?")
        else:
            logger.warning("Missing CSV: %s", csv_path)
            candles[tf] = []
    return candles


def load_mt5_data(symbol: str, start_date: date, end_date: date) -> dict[str, list[dict]]:
    """Pull historical data from MT5."""
    try:
        from src.mt5.mt5_interface import MT5Interface
    except ImportError:
        logger.error("MT5 not available. Use --source csv instead.")
        sys.exit(1)

    mt5 = MT5Interface()
    if not mt5.initialize():
        logger.error("MT5 initialization failed")
        sys.exit(1)

    from src.components.data_ingestion import TF_MAP, DEFAULT_LOOKBACKS

    # MT5 symbol mapping
    mt5_symbol = symbol.replace("_cash", ".cash") if "_cash" in symbol else symbol

    candles = {}
    for tf_name, tf_const in TF_MAP.items():
        # Pull enough history for lookback + simulation window
        lookback = DEFAULT_LOOKBACKS[tf_name]
        extra_days = (end_date - start_date).days + 30  # buffer for lookback
        start_dt = datetime.combine(start_date - timedelta(days=extra_days), time(0), timezone.utc)
        end_dt = datetime.combine(end_date + timedelta(days=1), time(0), timezone.utc)

        raw = mt5.get_candles_range(mt5_symbol, tf_const, start_dt, end_dt)
        if raw:
            candles[tf_name] = raw
            logger.info("MT5 %s %s: %d candles", symbol, tf_name, len(raw))
        else:
            logger.warning("MT5 returned no data for %s %s", symbol, tf_name)
            candles[tf_name] = []

    mt5.shutdown()
    return candles


# ── Kill zone candle enumeration ─────────────────────────────────────────

def enumerate_kz_candles(
    m15_candles: list[dict],
    symbol: str,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """Find all M15 candles within kill zone windows for the date range."""
    kz_windows = KZ_WINDOWS.get(symbol, KZ_WINDOWS["XAUUSD"])
    results = []

    for candle in m15_candles:
        dt = datetime.fromisoformat(candle["time"].replace("Z", "+00:00"))
        d = dt.date()
        if d < start_date or d > end_date:
            continue
        # Skip weekends
        if dt.weekday() >= 5:
            continue

        t = dt.time()
        for kz_name, (kz_start, kz_end) in kz_windows.items():
            if kz_start <= t < kz_end:
                results.append({
                    "candle_time": candle["time"],
                    "date": str(d),
                    "kill_zone": kz_name,
                    "close": candle["close"],
                    "high": candle["high"],
                    "low": candle["low"],
                })
                break

    return results


# ── MSO generation ───────────────────────────────────────────────────────

def build_mso_for_candle(
    all_candles: dict[str, list[dict]],
    candle_time: str,
    target_date: date,
    config: dict,
) -> object:
    """Build an MSO for a specific M15 candle using Component 2."""
    from scripts.historical_data_loader import build_raw_data, compute_session_levels
    from src.components.market_state import compute_market_state

    # Compute session levels from M15 candles
    session_levels = compute_session_levels(all_candles.get("M15", []), target_date)

    # Build raw data (same format as Component 1 output). Passing the
    # canonical symbol from config so the MSO's symbol-dependent paths —
    # XAUUSD session-ATR gate in compute_market_state + structure detector
    # shadow logger — see the correct instrument label in the sim path.
    raw_data = build_raw_data(
        all_candles, target_date, candle_time, session_levels,
        equal_level_tolerance=config.get("model_a", {}).get("equal_level_tolerance", 2.50),
        symbol=config.get("market", {}).get("symbol"),
    )

    # Run Component 2 (market state analyzer)
    mso = compute_market_state(raw_data, config)
    return mso


# ── Production gates (standalone versions of orchestrator methods) ────────

def ob_proximity_prescreen(mso, current_price: float, tolerance_pct: float = 0.01) -> tuple[bool, str]:
    """Skip API call if price is far from all active H1 OBs or breaker blocks.

    Uses 1.0% tolerance (5× L2's 0.2%) to avoid false negatives.
    L2's _check_h1_poi_exists accepts both OBs (unmitigated) and breaker blocks
    (unretested) as valid POI — so the prescreen must check both.
    If no active H1 zone exists within tolerance, L2 will reject anyway.

    Returns (passed, reason).  passed=True means "proceed to API".
    """
    h1 = mso.timeframes.get("H1") if hasattr(mso, "timeframes") else None
    if h1 is None:
        return False, "no_h1_data"

    tol = current_price * tolerance_pct

    # Check order blocks (unmitigated)
    for ob in (h1.order_blocks or []):
        if ob.mitigated:
            continue
        if ob.low - tol <= current_price <= ob.high + tol:
            return True, f"near_ob_{ob.low:.2f}-{ob.high:.2f}"

    # Check breaker blocks (unretested) — L2 also accepts these as valid POI
    for bb in (h1.breaker_blocks or []):
        if bb.is_retested:
            continue
        if bb.zone_low - tol <= current_price <= bb.zone_high + tol:
            return True, f"near_breaker_{bb.zone_low:.2f}-{bb.zone_high:.2f}"

    # Price is far from every active zone — find nearest for diagnostic
    gap_candidates = []
    for ob in (h1.order_blocks or []):
        if not ob.mitigated:
            gap_candidates.append(min(abs(current_price - ob.high), abs(current_price - ob.low)))
    for bb in (h1.breaker_blocks or []):
        if not bb.is_retested:
            gap_candidates.append(min(abs(current_price - bb.zone_high), abs(current_price - bb.zone_low)))

    if not gap_candidates:
        has_any = bool(h1.order_blocks or h1.breaker_blocks)
        return False, "no_unmitigated_obs" if has_any else "no_h1_obs"

    gap_pct = min(gap_candidates) / current_price * 100
    return False, f"price_far_from_ob_{gap_pct:.1f}pct"


def _compute_deterministic_bias(mso) -> dict:
    """Same as Orchestrator._compute_deterministic_bias — deterministic bias from MSO."""
    tfs = mso.timeframes if hasattr(mso, "timeframes") else {}

    def _dir(tf_name):
        tf = tfs.get(tf_name)
        if tf is None:
            return "unavailable"
        structure = getattr(tf, "structure", None)
        return structure.direction if structure else "unavailable"

    d1, h4, h1, m15 = _dir("D1"), _dir("H4"), _dir("H1"), _dir("M15")
    directional = ("bullish", "bearish")

    if d1 in directional:
        bias, source = d1, "D1"
    elif h4 in directional and h4 == h1:
        bias, source = h4, "H4+H1_consensus"
    elif h4 in directional:
        bias, source = h4, "H4_primary"
    else:
        bias, source = "no_bias", "none"

    return {"bias": bias, "source": source, "d1": d1, "h4": h4, "h1": h1, "m15": m15}


_XAUUSD_EXPERTISE = """## Gold Market Expertise

SESSION DYNAMICS:
- London KZ captures the LBMA AM Fix (09:30 UTC during BST, 10:30 UTC during GMT). \
Fix-related institutional flow concentrates 30-60 minutes before the fix. \
Structural breaks during this window carry higher conviction.
- NY KZ overlaps with COMEX futures open (~12:20-13:00 UTC). The heaviest COMEX \
volume occurs in the first 2-3 hours. The collision between European closing flows \
and American opening flows in the first 15 minutes can create false initial moves.
- Asian session (00:00-07:00 UTC) produces ranges. Asian high/low become visible \
reference levels on institutional screens. XAUUSD Asian range sweeps are \
continuation events, NOT reversals.

DISPLACEMENT MECHANICS:
- Stop-loss orders cluster at visible structural levels (below swing lows, above \
swing highs). When triggered, the cascade creates one-directional flow surge.
- The OB zone represents the last equilibrium BEFORE the cascade. Retest means \
price returning to pre-cascade fair value.
- Stronger cascades (fewer candles, larger body-to-range ratio) create stronger \
zones. A single-candle impulse means concentrated flow. A 4+ candle gradual \
move means distributed flow — weaker zone.
- Three-candle gaps (FVG) in the impulse signal exceptionally strong cascades \
with higher continuation rates.

GOLD-SPECIFIC:
- Central bank buying (~850+ tonnes/year) creates a structural demand floor. \
In bull regimes, bullish OB retests have fundamental support.
- DXY-gold inverse correlation is stable. Strong USD = gold headwind. \
When evaluating bearish gold setups, consider whether USD strength is a driver.
- Gold trades on a CFD derived from COMEX futures. Exact-pip precision is less \
reliable than structural zone identification."""


def _compute_align_context(mso, bias_result: dict, symbol: str = "XAUUSD") -> str:
    """Same as Orchestrator._compute_align_context — alignment score + bias injection + expertise."""
    directions = {}
    for tf_name in ("D1", "H4", "H1", "M15"):
        tf_state = mso.timeframes.get(tf_name)
        directions[tf_name] = tf_state.structure.direction if tf_state else "unavailable"

    bullish = sum(1 for d in directions.values() if d == "bullish")
    bearish = sum(1 for d in directions.values() if d == "bearish")
    dominant = "bullish" if bullish >= bearish else "bearish"
    score = max(bullish, bearish)
    detail = ", ".join(f"{tf}={d}" for tf, d in directions.items())

    lines = [
        "## Timeframe Alignment",
        f"Alignment score: {score}/4 ({dominant})",
        f"  {detail}",
        "  Historical edge: 3-4 aligned TFs show +7-9pp better continuation.",
        "  Score 0-1 means most timeframes disagree — higher bar for entry.",
        "",
        "## Directional Bias (COMPUTED — DO NOT OVERRIDE)",
        f"Bias: {bias_result['bias']} (source: {bias_result['source']})",
        f"  D1={bias_result['d1']}, H4={bias_result['h4']}, "
        f"H1={bias_result['h1']}, M15={bias_result['m15']}",
        "  This bias has been computed deterministically from market structure. "
        "Use it as given for U1. Do NOT re-derive directional bias.",
    ]
    if bias_result["bias"] in ("bullish", "bearish"):
        lines.append(
            f"  Trade direction: {'LONG' if bias_result['bias'] == 'bullish' else 'SHORT'} only."
        )

    # Instrument-specific domain expertise (matches orchestrator._get_instrument_expertise)
    if symbol == "XAUUSD":
        lines.append("")
        lines.append(_XAUUSD_EXPERTISE)

    return "\n".join(lines)


# ── T7 evaluation ────────────────────────────────────────────────────────

async def evaluate_with_t7(
    mso: object,
    kill_zone: str,
    config: dict,
    additional_context: str = "",
) -> tuple[dict, float]:
    """Evaluate a single MSO with the T7 prompt. Returns (result_dict, cost)."""
    import anthropic
    from src.prompts.primary_analyzer_prompt import build_system_prompt, build_user_message, build_static_context

    system_prompt = build_system_prompt(config)
    static_ctx = build_static_context(mso)
    candle_time = getattr(mso, "timestamp_utc", "") or ""
    # Use candle time as "current time" so the model sees consistent timestamps
    current_time = candle_time if candle_time else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    user_msg = build_user_message(
        mso, {}, current_time,
        kill_zone=kill_zone,
        additional_context=additional_context,
    )

    client = anthropic.Anthropic()

    try:
        model_id = config.get("ai", {}).get("primary_model", "claude-sonnet-4-6")
        effort = config.get("ai", {}).get("primary_effort", "max")
        response = client.messages.create(
            model=model_id,
            max_tokens=2000,
            temperature=0,
            output_config={"effort": effort},
            system=f"{system_prompt}\n\n## Static Context (D1/H4/Session)\n{static_ctx}",
            messages=[{"role": "user", "content": user_msg}],
        )

        text = response.content[0].text if response.content else ""
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = input_tokens * INPUT_COST_PER_TOK + output_tokens * OUTPUT_COST_PER_TOK

        # Parse decision from response
        result, pa_obj = _parse_response(text, candle_time, kill_zone)
        result["raw_response"] = text
        result["input_tokens"] = input_tokens
        result["output_tokens"] = output_tokens
        result["cost"] = round(cost, 4)

        return result, cost, pa_obj

    except Exception as e:
        logger.error("API call failed for %s: %s", candle_time, e)
        return {
            "candle_time": candle_time,
            "kill_zone": kill_zone,
            "decision": "ERROR",
            "error": str(e),
            "cost": 0,
        }, 0.0, None


def _parse_response(text: str, candle_time: str, kill_zone: str):
    """Extract decision from T7 JSON response.

    Returns (report_dict, pa_obj).  *pa_obj* is a validated
    ``PrimaryAnalysisOutput`` when the full production parse succeeds,
    ``None`` otherwise (L2 verification will be skipped).
    """
    from src.utils.validation import strip_json_fences
    from src.components.primary_analyzer import _normalize_pa_fields
    from src.models.analysis_models import PrimaryAnalysisOutput

    cleaned = strip_json_fences(text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "candle_time": candle_time,
            "kill_zone": kill_zone,
            "decision": "PARSE_ERROR",
            "error": "JSON decode failed",
        }, None

    # Build lightweight report dict (always succeeds)
    report = {
        "candle_time": candle_time,
        "kill_zone": kill_zone,
        "decision": data.get("decision", "PARSE_ERROR"),
        "h1_direction": data.get("reasoning", {}).get("daily_bias", {}).get("direction", "?"),
        "setup_grade": data.get("reasoning", {}).get("setup_grade", "?"),
        "no_trade_reason": data.get("no_trade_reason", ""),
        "direction": (data.get("trade_parameters") or {}).get("direction", ""),
        "entry_price": (data.get("trade_parameters") or {}).get("entry_price", 0),
        "stop_loss": (data.get("trade_parameters") or {}).get("stop_loss", 0),
        "take_profit_1": (data.get("trade_parameters") or {}).get("take_profit_1", 0),
    }

    # Try production-grade validation (needed for L2 verification)
    pa_obj = None
    try:
        _normalize_pa_fields(data)
        pa_obj = PrimaryAnalysisOutput.model_validate(data)
    except Exception as e:
        logger.debug("PA model_validate failed (L2 will be skipped): %s", e)

    return report, pa_obj


# ── Outcome lookup ───────────────────────────────────────────────────────

def compute_outcome(
    candidate: dict,
    m15_candles: list[dict],
    symbol: str | None = None,
) -> dict:
    """For a CANDIDATE, check if price reached TP or SL in subsequent candles.

    Checks entry fill validity: for a LONG with entry < candle_close (limit buy),
    the fill only happens when a subsequent candle L <= entry. For a LONG with
    entry > candle_close (buy stop), fill happens when H >= entry. If the entry
    limit/stop is never reached before TP/SL, returns UNFILLED — the trade never
    executed in live trading.

    `symbol` selects the per-instrument fill epsilon (see EPSILON_BY_SYMBOL). If
    None, falls back to `candidate["symbol"]`, then to the legacy default 0.05.
    """
    entry = candidate.get("entry_price", 0)
    sl = candidate.get("stop_loss", 0)
    tp = candidate.get("take_profit_1", 0)
    direction = candidate.get("direction", "LONG")
    candle_close = candidate.get("candle_close")  # close price at evaluation time

    if not entry or not sl or not tp:
        return {"outcome": "UNKNOWN", "reason": "missing_prices"}

    candle_time = candidate["candle_time"]
    # Determine fill behaviour only when we have a close price to compare against.
    # Use a per-instrument epsilon to treat entry ≈ close as "at-market" (always fills).
    fill_epsilon = _epsilon_for_symbol(symbol or candidate.get("symbol"))
    needs_fill_check = candle_close is not None and abs(entry - candle_close) > fill_epsilon
    entry_filled = not needs_fill_check  # trivially filled when entry ≈ close

    found_start = False
    for candle in m15_candles:
        if candle["time"] == candle_time:
            found_start = True
            continue
        if not found_start:
            continue

        h = candle["high"]
        l = candle["low"]

        # ── Fill check ──────────────────────────────────────────────────────
        if not entry_filled:
            if direction == "LONG":
                # Limit buy (entry < close): fill when price pulls back down to entry
                # Buy stop (entry > close): fill when price rallies up to entry
                if entry < candle_close and l <= entry:
                    entry_filled = True
                elif entry > candle_close and h >= entry:
                    entry_filled = True
            else:  # SHORT
                # Limit sell (entry > close): fill when price rallies up to entry
                # Sell stop (entry < close): fill when price drops down to entry
                if entry > candle_close and h >= entry:
                    entry_filled = True
                elif entry < candle_close and l <= entry:
                    entry_filled = True
            if not entry_filled:
                continue  # TP/SL irrelevant until filled

        if direction == "LONG":
            if l <= sl:
                return {"outcome": "LOSS", "r_multiple": -1.0, "exit_candle": candle["time"]}
            if h >= tp:
                sl_dist = entry - sl
                r = (tp - entry) / sl_dist if sl_dist > 0 else 0
                return {"outcome": "WIN", "r_multiple": round(r, 2), "exit_candle": candle["time"]}
        else:  # SHORT
            if h >= sl:
                return {"outcome": "LOSS", "r_multiple": -1.0, "exit_candle": candle["time"]}
            if l <= tp:
                sl_dist = sl - entry
                r = (entry - tp) / sl_dist if sl_dist > 0 else 0
                return {"outcome": "WIN", "r_multiple": round(r, 2), "exit_candle": candle["time"]}

    if not entry_filled:
        return {"outcome": "UNFILLED", "reason": "entry_limit_never_reached"}
    return {"outcome": "OPEN", "reason": "no_exit_in_data"}


# ── P2A v1 comparison ────────────────────────────────────────────────────

def _normalize_p2a_candle_time(ct: str) -> str:
    """Convert P2A candle_time to simulation candle_time format.

    P2A records candle_time as ~seconds after M15 candle close
    (e.g. '2026-04-07T07:15:48.173643+00:00').
    Simulation uses candle open time with clean minutes
    (e.g. '2026-04-07T07:00:00Z').

    Algorithm: floor to M15 boundary (that's the close time),
    then subtract 15 min to get the candle open time.
    """
    dt = datetime.fromisoformat(ct.replace("Z", "+00:00"))
    # Floor to minute, then to M15 boundary
    dt = dt.replace(second=0, microsecond=0)
    dt = dt.replace(minute=(dt.minute // 15) * 15)
    # Subtract 15 minutes: close time → open time
    dt = dt - timedelta(minutes=15)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def load_live_evaluations(symbol: str) -> dict[str, dict]:
    """Load P2A v1 live evaluation logs, keyed by normalized candle_time."""
    eval_dir = _PROJECT_ROOT / "knowledge_base" / "live_evaluations" / symbol
    evals = {}
    if not eval_dir.exists():
        return evals
    for f in sorted(eval_dir.glob("*.jsonl")):
        with open(f) as fh:
            for line in fh:
                rec = json.loads(line.strip())
                ct = rec.get("candle_time", "")
                if ct:
                    key = _normalize_p2a_candle_time(ct)
                    evals[key] = rec
    logger.debug("P2A evaluations loaded: %d (normalized to candle open times)", len(evals))
    return evals


# ── Main ─────────────────────────────────────────────────────────────────

async def run_simulation(args):
    import yaml
    from src.utils.config import apply_instrument_overrides
    from src.components.orchestrator import prescreen_mso

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    budget_limit = args.budget
    symbols = [args.symbol] if args.symbol else SYMBOLS

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_results = []
    total_cost = 0.0

    for symbol in symbols:
        logger.info("=" * 60)
        logger.info("Processing %s", symbol)

        # Load config with instrument overrides
        with open(_PROJECT_ROOT / "config" / "agent_config.yaml") as fh:
            config = yaml.safe_load(fh)
        config = apply_instrument_overrides(config, symbol)

        # F3 backtest: allow CLI override of market_state.detector_version
        # without touching agent_config.yaml (which the live fleet reads).
        if args.detector_version is not None:
            config.setdefault("market_state", {})["detector_version"] = args.detector_version
            logger.info("%s: detector_version override -> %s", symbol, args.detector_version)

        # Load data
        if args.source == "mt5":
            all_candles = load_mt5_data(symbol, start, end)
        else:
            all_candles = load_csv_data(symbol, data_dir=args.data_dir)

        if not all_candles.get("M15"):
            logger.warning("No M15 data for %s — skipping", symbol)
            continue

        # Check date coverage
        last_m15 = all_candles["M15"][-1]["time"][:10]
        if last_m15 < str(start):
            logger.warning("%s M15 data ends at %s — before simulation start %s. "
                           "Export fresh CSVs or use --source mt5.", symbol, last_m15, start)
            continue

        # Enumerate KZ candles
        kz_candles = enumerate_kz_candles(all_candles["M15"], symbol, start, end)
        logger.info("%s: %d kill-zone candles in %s to %s", symbol, len(kz_candles), start, end)

        if args.dry_run:
            # Production-faithful dry-run: apply same gates as real pipeline
            inst_cfg = config
            skip_first_ny = inst_cfg.get("skip_first_ny_candle", False)
            would_send_api = 0
            skip_prescreen = 0
            skip_nobias = 0
            skip_ny = 0
            skip_ob_proximity = 0
            mso_errors = 0
            for i, kz_candle in enumerate(kz_candles):
                target_date = date.fromisoformat(kz_candle["date"])
                kill_zone = kz_candle["kill_zone"]

                # C3: skip first NY candle
                if skip_first_ny and kill_zone == "ny":
                    dt = datetime.fromisoformat(kz_candle["candle_time"].replace("Z", "+00:00"))
                    if dt.hour == 13 and dt.minute == 0:
                        skip_ny += 1
                        continue

                try:
                    mso = build_mso_for_candle(all_candles, kz_candle["candle_time"], target_date, config)
                except Exception:
                    mso_errors += 1
                    continue

                # C7: prescreen
                passed, _ = prescreen_mso(mso)
                if not passed:
                    skip_prescreen += 1
                    continue

                # C7: deterministic bias
                bias = _compute_deterministic_bias(mso)
                if bias["bias"] == "no_bias":
                    skip_nobias += 1
                    continue

                # OB proximity prescreen — skip if price far from all H1 OBs
                ob_ok, _ = ob_proximity_prescreen(mso, kz_candle["close"])
                if not ob_ok:
                    skip_ob_proximity += 1
                    continue

                would_send_api += 1

                if (i + 1) % 200 == 0:
                    logger.info("  ... scanned %d/%d candles (%d would hit API)",
                                i + 1, len(kz_candles), would_send_api)

            est_cost = would_send_api * 0.029  # actual XAUUSD avg: $35.03/1198 calls = $0.029/call
            logger.info(
                "DRY RUN: %s — %d KZ candles | skip: prescreen=%d, no_bias=%d, first_ny=%d, ob_proximity=%d, mso_err=%d | API calls=%d",
                symbol, len(kz_candles), skip_prescreen, skip_nobias, skip_ny, skip_ob_proximity, mso_errors, would_send_api,
            )
            logger.info(
                "DRY RUN: %s — estimated cost: $%.2f (%.0f%% of candles reach API)",
                symbol, est_cost, 100 * would_send_api / max(len(kz_candles), 1),
            )
            continue

        # Load P2A v1 live evaluations for comparison
        live_evals = load_live_evaluations(symbol)
        logger.info("Loaded %d P2A v1 live evaluations for comparison", len(live_evals))

        # Evaluate each candle
        symbol_results = []
        # Production gate tracking
        from src.components.verification import verify_candidate

        trades_today = {}  # date -> count
        trades_this_kz = {}  # (date, kz) -> count
        # Config: skip first NY candle for XAUUSD
        inst_cfg = config  # instrument overrides already merged by apply_instrument_overrides
        skip_first_ny = inst_cfg.get("skip_first_ny_candle", False)
        min_rr = config.get("drawdown_reduction", {}).get("min_rr",
                    config.get("risk", {}).get("min_rr", 1.5))

        for i, kz_candle in enumerate(kz_candles):
            # Budget check
            if total_cost >= budget_limit:
                logger.warning("Budget limit $%.2f reached. Stopping.", budget_limit)
                break

            candle_time = kz_candle["candle_time"]
            kill_zone = kz_candle["kill_zone"]
            target_date = date.fromisoformat(kz_candle["date"])

            logger.info("[%d/%d] %s %s %s", i + 1, len(kz_candles),
                        symbol, candle_time[:16], kill_zone)

            # ── C3: Skip first NY candle (13:00 UTC) ──
            if skip_first_ny and kill_zone == "ny":
                dt = datetime.fromisoformat(candle_time.replace("Z", "+00:00"))
                if dt.hour == 13 and dt.minute == 0:
                    symbol_results.append({
                        "candle_time": candle_time, "kill_zone": kill_zone,
                        "decision": "NO_TRADE", "no_trade_reason": "skip_first_ny_candle",
                        "symbol": symbol, "date": kz_candle["date"], "cost": 0,
                    })
                    continue

            # Build MSO
            try:
                mso = build_mso_for_candle(all_candles, candle_time, target_date, config)
            except Exception as e:
                logger.error("MSO build failed: %s", e)
                continue

            # ── C7: Production prescreen — D1/H4 directional check ──
            passed, reason = prescreen_mso(mso)
            if not passed:
                symbol_results.append({
                    "candle_time": candle_time, "kill_zone": kill_zone,
                    "decision": "NO_TRADE", "no_trade_reason": f"prescreen:{reason}",
                    "symbol": symbol, "date": kz_candle["date"], "cost": 0,
                })
                continue

            # ── C7: Deterministic bias — skip if no valid bias ──
            bias_result = _compute_deterministic_bias(mso)
            if bias_result["bias"] == "no_bias":
                symbol_results.append({
                    "candle_time": candle_time, "kill_zone": kill_zone,
                    "decision": "NO_TRADE", "no_trade_reason": f"no_bias:D1={bias_result['d1']},H4={bias_result['h4']}",
                    "symbol": symbol, "date": kz_candle["date"], "cost": 0,
                })
                continue

            # ── OB proximity prescreen — skip if price far from all H1 OBs ──
            ob_ok, ob_reason = ob_proximity_prescreen(mso, kz_candle["close"])
            if not ob_ok:
                symbol_results.append({
                    "candle_time": candle_time, "kill_zone": kill_zone,
                    "decision": "NO_TRADE", "no_trade_reason": f"ob_proximity:{ob_reason}",
                    "symbol": symbol, "date": kz_candle["date"], "cost": 0,
                })
                continue

            # ── C6: Compute alignment context + deterministic bias injection ──
            align_context = _compute_align_context(mso, bias_result, symbol=symbol)

            # Evaluate with T7
            result, cost, pa_obj = await evaluate_with_t7(mso, kill_zone, config,
                                                           additional_context=align_context)
            total_cost += cost

            # Add metadata
            result["symbol"] = symbol
            result["date"] = kz_candle["date"]
            result["prescreen"] = "pass"
            result["bias"] = bias_result["bias"]
            result["bias_source"] = bias_result["source"]
            result["candle_close"] = kz_candle["close"]  # needed for fill validity check

            # ── ADR-005 / A1 backtest validation shadow log ──
            # Captures MSO features + AI output so the backtest can measure
            # whether the production AI discriminates on h1_opp_ob_touch +
            # h1_fvg_unfilled_count + m15_fvg_unfilled_count. Log on BOTH
            # CAND + NO_TRADE paths. Failure-isolated (never raises).
            # The destination path is overridable via env var so each
            # parallel slice writes to its own file.
            if args.a1_backtest_log_path or os.environ.get("A1_BACKTEST_LOG_PATH"):
                try:
                    from src.components.candidate_features_logger import (
                        log_candidate_features as _a1_log,
                    )
                    a1_direction = (
                        "LONG" if bias_result["bias"] == "bullish"
                        else "SHORT" if bias_result["bias"] == "bearish"
                        else "UNCLEAR"
                    )
                    a1_detver = config.get("market_state", {}).get("detector_version")
                    a1_slice = args.slice_tag or f"{symbol}_{start}"
                    a1_log_path = args.a1_backtest_log_path or os.environ.get("A1_BACKTEST_LOG_PATH")
                    _a1_log(
                        pa_output=pa_obj,
                        mso=mso,
                        symbol=symbol,
                        timestamp_utc=str(candle_time),
                        session_state={"kill_zone": kill_zone},
                        log_path=a1_log_path,
                        ai_direction_evaluated=a1_direction,
                        detector_version_at_eval=a1_detver,
                        slice_tag=a1_slice,
                    )
                except Exception as _a1_exc:  # noqa: BLE001
                    logger.debug("A1 ADR-005 shadow-log outer guard: %s", _a1_exc)

            # ── Process CANDIDATEs through production gates ──
            if result.get("decision") == "CANDIDATE":
                result, pa_obj = _apply_live_candidate_output_guards(result, pa_obj)
                if result.get("decision") == "NO_TRADE_LIVE_GUARD":
                    logger.info("  Live output guard demoted: %s", result["live_guard_reason"])

            if result.get("decision") == "CANDIDATE":
                entry = result.get("entry_price", 0)
                sl = result.get("stop_loss", 0)
                tp1 = result.get("take_profit_1", 0)
                direction = result.get("direction", "LONG")

                # ── C2: L2 Verification (runs on ORIGINAL AI prices, before correction) ──
                if pa_obj is not None:
                    try:
                        verification = verify_candidate(pa_obj, mso, config)
                        result["l2_passed"] = verification.passed
                        if not verification.passed:
                            fail_check = next(
                                (c for c in verification.checks if c.status == "FAIL"), None
                            )
                            result["l2_reason"] = (
                                f"{verification.blocked_by}: {fail_check.detail[:80]}"
                                if fail_check else verification.blocked_by
                            )
                            result["decision"] = "REJECTED_L2"
                            logger.info("  L2 REJECTED: %s", result["l2_reason"])
                    except Exception as e:
                        result["l2_passed"] = "error"
                        result["l2_reason"] = str(e)[:80]
                        logger.warning("  L2 check error (non-blocking): %s", e)
                else:
                    # Production behavior: PA parse failure → format correction retry → NO_TRADE.
                    # We can't retry (costs $), so conservatively match production's final outcome.
                    result["decision"] = "NO_TRADE_PARSE_FAIL"
                    result["l2_passed"] = "skipped"
                    result["l2_reason"] = "PA parse failed — L2 requires structured output"
                    logger.info("  PA parse failed → NO_TRADE_PARSE_FAIL (production would retry then reject)")

                # ── C4: Detect and correct inverted TP/SL geometry (after L2) ──
                if result.get("decision") == "CANDIDATE":
                    if direction == "LONG" and entry and (sl > entry or tp1 <= entry):
                        raw_dist = abs(entry - sl)
                        if raw_dist > 0:
                            result["stop_loss"] = entry - raw_dist
                            result["take_profit_1"] = entry + min_rr * raw_dist
                            sl = result["stop_loss"]
                            tp1 = result["take_profit_1"]
                            result["inverted_tp_corrected"] = True
                            logger.info("  Inverted LONG corrected: SL=%.2f TP1=%.2f", sl, tp1)
                    elif direction == "SHORT" and entry and (sl < entry or tp1 >= entry):
                        raw_dist = abs(sl - entry)
                        if raw_dist > 0:
                            result["stop_loss"] = entry + raw_dist
                            result["take_profit_1"] = entry - min_rr * raw_dist
                            sl = result["stop_loss"]
                            tp1 = result["take_profit_1"]
                            result["inverted_tp_corrected"] = True
                            logger.info("  Inverted SHORT corrected: SL=%.2f TP1=%.2f", sl, tp1)

            # ── C5: Track trade limits (2/day, 1/KZ) ──
            if result.get("decision") == "CANDIDATE":
                day_key = kz_candle["date"]
                kz_key = (kz_candle["date"], kill_zone)
                day_count = trades_today.get(day_key, 0)
                kz_count = trades_this_kz.get(kz_key, 0)

                if day_count >= 2:
                    result["decision"] = "BLOCKED_LIMIT"
                    result["block_reason"] = f"max_daily_trades_sim ({day_count} already)"
                elif kz_count >= 1:
                    result["decision"] = "BLOCKED_LIMIT"
                    result["block_reason"] = f"max_kz_trades ({kz_count} in {kill_zone})"
                else:
                    trades_today[day_key] = day_count + 1
                    trades_this_kz[kz_key] = kz_count + 1

            # Compute outcome for trades that would actually execute
            if result.get("decision") == "CANDIDATE":
                outcome = compute_outcome(result, all_candles["M15"], symbol=symbol)
                result.update(outcome)

            # Compare with P2A v1
            p2a = live_evals.get(candle_time, {})
            result["p2a_decision"] = p2a.get("decision", "N/A")
            result["p2a_bias"] = p2a.get("daily_bias_direction", "N/A")
            result["p2a_reason"] = (p2a.get("no_trade_reason") or "")[:80]

            symbol_results.append(result)

            # Rate limit: ~1 req/sec (only for API calls)
            if result.get("cost", 0) > 0:
                time_mod.sleep(0.5)

        all_results.extend(symbol_results)

        # Save per-symbol results
        out_path = OUTPUT_DIR / f"{symbol}_t7_simulation.json"
        with open(out_path, "w") as f:
            json.dump({"symbol": symbol, "start": str(start), "end": str(end),
                        "n_evaluated": len(symbol_results), "results": symbol_results}, f, indent=2)
        logger.info("Saved %s: %d results", out_path, len(symbol_results))

    # ── Generate report ──────────────────────────────────────────────────

    if args.dry_run:
        return

    report_lines = [
        "# T7 Production-Faithful Simulation Report",
        f"**Dates:** {start} to {end}",
        f"**Total KZ candles:** {len(all_results)}",
        f"**Total API cost:** ${total_cost:.2f}",
        f"**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)",
        "",
        "**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,",
        "L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.",
        "",
    ]

    # ── Summary table ──
    report_lines.append("## Summary by Instrument")
    report_lines.append("")
    report_lines.append("| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |")
    report_lines.append("|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|")

    for symbol in symbols:
        sym_results = [r for r in all_results if r.get("symbol") == symbol]
        if not sym_results:
            continue
        n = len(sym_results)
        api_calls = sum(1 for r in sym_results if r.get("cost", 0) > 0)
        raw_cand = [r for r in sym_results if r.get("decision") in RAW_CANDIDATE_DECISIONS]
        l2_reject = [r for r in sym_results if r.get("decision") == "REJECTED_L2"]
        blocked = [r for r in sym_results if r.get("decision") == "BLOCKED_LIMIT"]
        final_trades = [r for r in sym_results if r.get("decision") == "CANDIDATE"]
        raw_cr = len(raw_cand) / api_calls * 100 if api_calls else 0
        live_cr = len(final_trades) / api_calls * 100 if api_calls else 0

        wins = [r for r in final_trades if r.get("outcome") == "WIN"]
        losses = [r for r in final_trades if r.get("outcome") == "LOSS"]
        resolved = [r for r in final_trades if r.get("outcome") in ("WIN", "LOSS")]
        wr = len(wins) / len(resolved) * 100 if resolved else 0
        total_r = sum(r.get("r_multiple", 0) for r in resolved)
        exp = total_r / len(resolved) if resolved else 0

        report_lines.append(
            f"| {symbol:8s} | {n:9d} | {api_calls:9d} | {len(raw_cand):7d} | {len(l2_reject):9d} | "
            f"{len(blocked):11d} | {len(final_trades):11d} | {raw_cr:7.1f}% | {live_cr:8.1f}% | "
            f"{len(wins):4d} | {len(losses):6d} | {wr:3.0f}% | {total_r:+6.1f}R | {exp:+.3f}R |"
        )

    report_lines.append("")

    # ── Pipeline funnel ──
    all_api = [r for r in all_results if r.get("cost", 0) > 0]
    prescreen_skip = [r for r in all_results if "prescreen:" in (r.get("no_trade_reason") or "")]
    nobias_skip = [r for r in all_results if "no_bias:" in (r.get("no_trade_reason") or "")]
    ob_proximity_skip = [r for r in all_results if "ob_proximity:" in (r.get("no_trade_reason") or "")]
    ny_skip = [r for r in all_results if r.get("no_trade_reason") == "skip_first_ny_candle"]
    all_raw_cand = [r for r in all_results if r.get("decision") in RAW_CANDIDATE_DECISIONS]
    all_l2_reject = [r for r in all_results if r.get("decision") == "REJECTED_L2"]
    all_parse_fail = [r for r in all_results if r.get("decision") == "NO_TRADE_PARSE_FAIL"]
    all_live_guard = [r for r in all_results if r.get("decision") == "NO_TRADE_LIVE_GUARD"]
    all_blocked = [r for r in all_results if r.get("decision") == "BLOCKED_LIMIT"]
    all_final = [r for r in all_results if r.get("decision") == "CANDIDATE"]
    all_unfilled = [r for r in all_final if r.get("outcome") == "UNFILLED"]
    all_inverted = [r for r in all_results if r.get("inverted_tp_corrected")]

    report_lines.append("## Pipeline Funnel")
    report_lines.append("")
    report_lines.append(f"- Total KZ candles: {len(all_results)}")
    report_lines.append(f"- Skipped (prescreen D1/H4): {len(prescreen_skip)}")
    report_lines.append(f"- Skipped (no bias): {len(nobias_skip)}")
    report_lines.append(f"- Skipped (OB proximity): {len(ob_proximity_skip)}")
    report_lines.append(f"- Skipped (first NY candle): {len(ny_skip)}")
    report_lines.append(f"- Sent to API: {len(all_api)}")
    report_lines.append(f"- AI returned CANDIDATE: {len(all_raw_cand)} (raw CR: {len(all_raw_cand)/max(len(all_api),1)*100:.1f}%)")
    report_lines.append(f"  - Inverted TP corrected: {len(all_inverted)}")
    report_lines.append(f"  - L2 Rejected: {len(all_l2_reject)}")
    report_lines.append(f"  - PA parse failed → NO_TRADE: {len(all_parse_fail)} (production would retry then reject)")
    report_lines.append(f"  - Live output guard demoted: {len(all_live_guard)}")
    report_lines.append(f"  - Blocked by trade limits: {len(all_blocked)}")
    report_lines.append(f"- **Final CANDIDATE decisions: {len(all_final)}** (live CR: {len(all_final)/max(len(all_api),1)*100:.1f}%)")
    if all_unfilled:
        report_lines.append(f"  - ⚠ Entry limit never filled (unfilled): {len(all_unfilled)} — excluded from WR/expectancy")
    report_lines.append("")

    # ── Monthly breakdown (S1) ──
    report_lines.append("## Monthly Breakdown")
    report_lines.append("")
    report_lines.append("| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |")
    report_lines.append("|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|")

    months = sorted(set(r.get("date", "")[:7] for r in all_results if r.get("date")))
    for month in months:
        m_results = [r for r in all_results if (r.get("date") or "").startswith(month)]
        m_api = sum(1 for r in m_results if r.get("cost", 0) > 0)
        m_raw = [r for r in m_results if r.get("decision") in RAW_CANDIDATE_DECISIONS]
        m_final = [r for r in m_results if r.get("decision") == "CANDIDATE"]
        m_cr = len(m_final) / m_api * 100 if m_api else 0
        m_wins = [r for r in m_final if r.get("outcome") == "WIN"]
        m_losses = [r for r in m_final if r.get("outcome") == "LOSS"]
        m_resolved = [r for r in m_final if r.get("outcome") in ("WIN", "LOSS")]
        m_wr = len(m_wins) / len(m_resolved) * 100 if m_resolved else 0
        m_total_r = sum(r.get("r_multiple", 0) for r in m_resolved)
        m_exp = m_total_r / len(m_resolved) if m_resolved else 0
        report_lines.append(
            f"| {month:7s} | {m_api:9d} | {len(m_raw):8d} | {len(m_final):11d} | {m_cr:8.1f}% | "
            f"{len(m_wins):4d} | {len(m_losses):6d} | {m_wr:3.0f}% | {m_total_r:+6.1f}R | {m_exp:+.3f}R |"
        )
    report_lines.append("")

    # ── Risk metrics (S2) ──
    all_final_trades = [r for r in all_results if r.get("decision") == "CANDIDATE"]
    unfilled_trades = [r for r in all_final_trades if r.get("outcome") == "UNFILLED"]
    resolved_trades = [r for r in all_final_trades if r.get("outcome") in ("WIN", "LOSS")]

    if resolved_trades:
        r_multiples = [r.get("r_multiple", 0) for r in resolved_trades]
        cumulative_r = []
        running = 0
        max_consec_loss = 0
        curr_consec_loss = 0
        for rm in r_multiples:
            running += rm
            cumulative_r.append(running)
            if rm < 0:
                curr_consec_loss += 1
                max_consec_loss = max(max_consec_loss, curr_consec_loss)
            else:
                curr_consec_loss = 0

        peak = 0
        max_dd = 0
        for cr in cumulative_r:
            peak = max(peak, cr)
            dd = peak - cr
            max_dd = max(max_dd, dd)

        total_weeks = ((end - start).days + 1) / 7
        total_months = ((end - start).days + 1) / 30.44

        report_lines.append("## Risk Metrics")
        report_lines.append("")
        if unfilled_trades:
            report_lines.append(f"- ⚠ Unfilled (entry limit never reached): {len(unfilled_trades)} — excluded from all metrics below")
        report_lines.append(f"- Total resolved trades: {len(resolved_trades)}")
        report_lines.append(f"- Win rate: {sum(1 for r in r_multiples if r > 0)/len(r_multiples)*100:.1f}%")
        report_lines.append(f"- Expectancy per trade: {sum(r_multiples)/len(r_multiples):+.3f}R")
        report_lines.append(f"- Total R: {sum(r_multiples):+.1f}R")
        report_lines.append(f"- Max consecutive losses: {max_consec_loss}")
        report_lines.append(f"- Max drawdown: {max_dd:.1f}R")
        report_lines.append(f"- Trades per week: {len(resolved_trades)/max(total_weeks,1):.1f}")
        report_lines.append(f"- Trades per month: {len(resolved_trades)/max(total_months,1):.1f}")
        report_lines.append("")

    # ── KZ and direction distribution (S3) ──
    report_lines.append("## Trade Distribution")
    report_lines.append("")
    if all_final_trades:
        london = [r for r in all_final_trades if r.get("kill_zone") == "london"]
        ny = [r for r in all_final_trades if r.get("kill_zone") == "ny"]
        longs = [r for r in all_final_trades if r.get("direction") == "LONG"]
        shorts = [r for r in all_final_trades if r.get("direction") == "SHORT"]
        report_lines.append(f"- London: {len(london)} ({len(london)/len(all_final_trades)*100:.0f}%)")
        report_lines.append(f"- NY: {len(ny)} ({len(ny)/len(all_final_trades)*100:.0f}%)")
        report_lines.append(f"- LONG: {len(longs)} ({len(longs)/len(all_final_trades)*100:.0f}%)")
        report_lines.append(f"- SHORT: {len(shorts)} ({len(shorts)/len(all_final_trades)*100:.0f}%)")
    report_lines.append("")

    # ── Day-by-day breakdown ──
    report_lines.append("## Day-by-Day Detail")
    report_lines.append("")

    dates = sorted(set(r.get("date", "") for r in all_results))
    for d in dates:
        day_results = [r for r in all_results if r.get("date") == d]
        cands = [r for r in day_results if r.get("decision") == "CANDIDATE"]
        l2_rej = [r for r in day_results if r.get("decision") == "REJECTED_L2"]
        blocked_lim = [r for r in day_results if r.get("decision") == "BLOCKED_LIMIT"]
        api_calls_day = sum(1 for r in day_results if r.get("cost", 0) > 0)
        report_lines.append(f"### {d}")
        report_lines.append(f"- API calls: {api_calls_day} | Trades: {len(cands)} | L2 rejected: {len(l2_rej)} | Limit blocked: {len(blocked_lim)}")
        if cands:
            for c in cands:
                report_lines.append(
                    f"  - {c.get('kill_zone')} {c.get('candle_time','')[:16]} "
                    f"→ {c.get('direction')} entry={c.get('entry_price'):.2f} "
                    f"SL={c.get('stop_loss'):.2f} TP1={c.get('take_profit_1'):.2f} "
                    f"→ **{c.get('outcome', '?')}** {c.get('r_multiple', '?')}R"
                    f"{' [inverted→corrected]' if c.get('inverted_tp_corrected') else ''}"
                )
        elif not l2_rej and not blocked_lim:
            report_lines.append("  - (no candidates)")
        report_lines.append("")

    # ── T7 vs P2A v1 comparison ──
    report_lines.append("## T7 vs P2A v1 Decision Comparison")
    report_lines.append("")
    t7_yes_p2a_no = [r for r in all_results
                     if r.get("decision") == "CANDIDATE" and r.get("p2a_decision") != "CANDIDATE"]
    t7_no_p2a_yes = [r for r in all_results
                     if r.get("decision") != "CANDIDATE" and r.get("p2a_decision") == "CANDIDATE"]
    both_yes = [r for r in all_results
                if r.get("decision") == "CANDIDATE" and r.get("p2a_decision") == "CANDIDATE"]

    report_lines.append(f"- Both CANDIDATE: {len(both_yes)}")
    report_lines.append(f"- T7 CANDIDATE, P2A NO_TRADE: {len(t7_yes_p2a_no)}")
    report_lines.append(f"- T7 NO_TRADE, P2A CANDIDATE: {len(t7_no_p2a_yes)}")
    report_lines.append("")

    # ── Caveats ──
    report_lines.append("## Caveats")
    report_lines.append("")
    report_lines.append("- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).")
    report_lines.append("- **No spread simulation:** Entry prices are AI-quoted, no spread added.")
    report_lines.append("- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.")
    report_lines.append("- **KB context empty:** Production passes last-10-trade context; simulation does not.")
    report_lines.append("")

    report_path = OUTPUT_DIR / "t7_live_simulation_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    logger.info("Report saved: %s", report_path)

    # Also save combined results
    combined_path = OUTPUT_DIR / "all_results.json"
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump({"start": str(start), "end": str(end),
                    "total_cost": round(total_cost, 2),
                    "results": all_results}, f, indent=2)
    logger.info("Combined results: %s", combined_path)


def main():
    parser = argparse.ArgumentParser(description="T7 live period simulation")
    parser.add_argument("--source", choices=["csv", "mt5"], default="csv",
                        help="Data source: csv (TradingView exports) or mt5 (live MT5)")
    parser.add_argument("--start", default="2026-04-07", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default="2026-04-12", help="End date (YYYY-MM-DD)")
    parser.add_argument("--symbol", default=None, help="Single instrument (default: all 5)")
    parser.add_argument("--budget", type=float, default=10.0, help="Max API spend in USD")
    parser.add_argument("--dry-run", action="store_true", help="Count candles only, no API calls")
    parser.add_argument("--data-dir", default=None,
                        help="Override CSV directory (default: data/historical)")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory for per-symbol JSON + all_results.json (default: research/t7_live_simulation). Use a unique path per process when running parallel slices to avoid clobbering.")
    parser.add_argument("--detector-version", choices=["v1", "v2_shadow", "v2"], default=None,
                        help="Override market_state.detector_version from config (F3 backtest: pass 'v2' to route production through identify_structure_v2).")
    parser.add_argument("--a1-backtest-log-path", default=None,
                        help="If set, write one candidate_features JSONL row per evaluation "
                             "(CAND + NO_TRADE) to this path. Used by "
                             "research/a1-adr005-backtest-validation. Also honors env var "
                             "A1_BACKTEST_LOG_PATH.")
    parser.add_argument("--slice-tag", default=None,
                        help="Free-form tag used to attribute ADR-005 shadow rows to the "
                             "originating parallel-backtest slice (e.g. 'xauusd_s3').")
    args = parser.parse_args()

    global OUTPUT_DIR
    if args.output_dir:
        OUTPUT_DIR = Path(args.output_dir)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    asyncio.run(run_simulation(args))


if __name__ == "__main__":
    main()
