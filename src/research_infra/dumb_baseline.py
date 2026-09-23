"""A1 — Full Historical Dumb-Baseline Replay.

Mechanical 80%-retrace OB-pullback baseline for the GTOS Phase 1 decay
diagnostic (research program K item A1, kickoff 2026-04-26).

Why this exists
===============
The strategic question this answers: is the H2-2026 XAUUSD WR decay
(64.5% H1 → 24.0% H2, χ²=0.006) AI-side or regime-side?

* If AI-vs-mechanical gap STAYS ~30-40pp throughout the year, the AI
  has lost something (system decay).
* If the gap NARROWS or CROSSES in H2 (mechanical also collapses), the
  market changed (regime decay).
* If the gap is small from the start, the AI was never adding much
  selectivity beyond OB-zone entry — the edge is the zone, not the AI.

This module computes the mechanical-arm side of that comparison:
for every historical CAND we have an MSO + recorded AI decision for, it
re-derives a mechanical entry (canonical OB-pullback rule), prices a
mechanical SL/TP using ``config/agent_config.yaml`` defaults, and
resolves the outcome from raw M15 OHLCV (``data/historical_2026/``).

The orchestrator (:class:`DumbBaselineReplay`) joins per-CAND mechanical
realized R against the AI's recorded realized R via the L56/L58 contract
``(symbol, normalized_candle_time, side)`` and emits per-month per-
instrument aggregates plus the strategic verdict block.

Hard rules
==========
* **No AI / Anthropic API calls.** Phase 1 = $0. This module is pure-
  Python OHLCV replay.
* **Read-only inputs.** ``knowledge_base/trade_records/``,
  ``knowledge_base/live_evaluations/``, ``data/historical_2026/`` are
  read-only. Outputs go to a caller-supplied directory.
* **No production-code dependencies.** This file does not import from
  ``src/components/`` (production trading code). It does not import
  from ``src/safety/``. It does not modify ``shadow_logs/``.
* **Walk-level vs realized-R discipline** (memory
  ``feedback_walk_level_evidence_not_predictive``): outcome rows carry
  BOTH the walk-level decision-flip AND the realized R-multiple.
  Aggregation surfaces both.
* **Never fabricate.** When mechanical or AI outcome is unresolvable,
  we record the row with ``None`` and exclude it from rate
  aggregations — never invent a value.

Mechanical rules (canonical 80%-retrace OB-pullback)
====================================================
For each CAND we look up:

1. ``side``       → the AI's recorded direction (LONG or SHORT). The
                    mechanical replay uses this so we test the same
                    setup the AI looked at, NOT whether the mechanical
                    arm would have picked a different side.
2. ``target OB``  → the most-recent (latest formation_time before
                    candle_close_time) H1 OB matching ``side`` from the
                    record's MSO ``timeframes.H1.order_blocks``. For
                    LONG we want a bullish OB; for SHORT we want a
                    bearish OB. Mitigated OBs are excluded (the AI
                    cannot enter mitigated zones).
3. ``mechanical entry`` → 80% into the OB from the entry side:
   * LONG : entry = OB.low + 0.80 * (OB.high - OB.low)
            (i.e. enter near the top of the OB, the canonical pullback)
            Note: the OB high is the resistance; price retraces
            DOWN INTO the OB — 80% retrace into a bullish OB means
            entering close to the top because the impulse came from
            below the OB. We use the AI's same convention here:
            for a bullish (demand) OB, "80% retrace" means the price
            dipped 80% of the OB-body from the impulse side
            (here ``high``) toward the protective side (``low``).
   * SHORT: entry = OB.high - 0.80 * (OB.high - OB.low)
4. ``mechanical SL`` → buffer beyond the protective OB edge:
   * buffer = max(sl_buffer_atr_multiplier * H1_ATR,
                  sl_buffer_min_ticks * tick_size)
   * LONG : SL = OB.low  - buffer
   * SHORT: SL = OB.high + buffer
5. ``mechanical TP`` → nearest opposing swing with implied RR ≥ 1.5;
   if none qualifies we fall back to ``entry ± 1.5 * (entry - SL)``
   (i.e. clamp to min RR). The fallback matches the live system's
   inverted-TP-correction guarantee that every trade has at least
   1.5R headroom.

Outcome resolution
==================
For the resolved (entry, SL, TP, side, candle_close_time) tuple, we:

1. Open the matching ``data/historical_2026/{SYMBOL}_M15.csv`` (note:
   ``US30_cash`` is canonical instrument key here; ``US30`` short form
   is also accepted as alias).
2. Walk forward starting at the next M15 candle whose ``time`` is
   strictly greater than ``candle_close_time`` (next bar).
3. For each bar:
   * **LONG**:  if low <= SL → SL hit, R = -1.0; if high >= TP → TP
                 hit, R = +RR (where RR = (TP-entry) / (entry-SL)).
   * **SHORT**: if high >= SL → SL hit, R = -1.0; if low <= TP → TP
                 hit, R = +RR.
4. **SL-first** rule on a bar that hits both — conservative, matches
   ``dumb_baseline_shadow_logger._resolve_outcomes`` and
   ``mechanical_backtest.simulate_trade``.
5. If neither fires within ``max_hold_bars`` (default 96 bars = 24h),
   outcome = ``TIMEOUT``, R = (close - entry) / (entry - SL) signed
   by direction (last-bar mark-to-market).

Join contract (mirrors L56 + L58)
=================================
Realized AI-R join key:
    (SYMBOL_UPPER, candle_close_time_minute_utc, side_or_None)

Trade records published in 2026 carry the AI's direction under
``decision_pipeline.ai_direction`` and realized R under
``decision_pipeline.outcome.r_multiple`` / ``exit.r_multiple``.

A side-less fallback (``None`` for side) lets us join when the trade
record omitted direction; matches the L58 ``_build_realized_r_index``
behaviour.

Out of scope
============
* Choosing whether the AI was correct. We surface the gap; we do not
  recommend a system change.
* Suggesting a new gate / prompt change. The brief is explicit:
  "your job is to surface the data, not to recommend system changes."
* Multi-framework dispatch. We replay only the OB-pullback canonical
  rule; ``fvg_fill`` and ``breaker_re_entry`` framework comparisons
  are A6 / D-track tasks, not A1.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Project-root resolution + default paths
# ---------------------------------------------------------------------------

# src/research_infra/dumb_baseline.py → project root is parents[2]
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

DEFAULT_TRADE_RECORDS_DIR: Path = PROJECT_ROOT / "knowledge_base" / "trade_records"
DEFAULT_OHLCV_DIR: Path = PROJECT_ROOT / "data" / "historical_2026"
DEFAULT_CONFIG_PATH: Path = PROJECT_ROOT / "config" / "agent_config.yaml"

#: Harness version embedded in summary.json; bump when contract changes.
HARNESS_VERSION: str = "A1-v1"

#: Canonical retrace fraction (matches A6 + dumb_baseline_shadow_logger).
RETRACE_PCT: float = 0.80

#: Default RR floor (mirrors ``risk.min_rr`` in agent_config.yaml).
DEFAULT_MIN_RR: float = 1.5

#: Maximum lookforward window for outcome resolution. 96 M15 bars = 24h.
DEFAULT_MAX_HOLD_BARS: int = 96


# ---------------------------------------------------------------------------
# Tick / pip table — mirrors mechanical_backtest.get_pip_size
# ---------------------------------------------------------------------------
#
# Per-instrument tick size used for the ``sl_buffer_min_ticks * tick``
# floor in the SL buffer formula. The OHLCV CSV files use the broker's
# native price precision; the tick is the smallest price increment the
# broker quotes.
TICK_SIZE: Dict[str, float] = {
    "XAUUSD": 0.01,        # gold: $0.01 per tick (price ~$2000 quoted to 2dp)
    "XAGUSD": 0.001,       # silver: $0.001 per tick
    "US30_cash": 0.01,     # FTMO US30 quoted to 2dp
    "US30": 0.01,          # alias
    "NAS100": 0.01,
    "USDJPY": 0.001,       # 5dp pricing → 0.001 = 1 tick; 1 pip = 0.01
    "GBPJPY": 0.001,
    "EURJPY": 0.001,
    "GBPUSD": 0.00001,     # 5dp FX
    "EURUSD": 0.00001,
}


# ---------------------------------------------------------------------------
# Symbol normalization
# ---------------------------------------------------------------------------

#: How to look up OHLCV files. Trade records use ``US30_cash``; the
#: data/historical_2026 dir uses ``US30_cash_M15.csv``. Map the
#: instrument key to the OHLCV file stem.
OHLCV_STEM: Dict[str, str] = {
    "XAUUSD": "XAUUSD",
    "XAGUSD": "XAGUSD",
    "US30_cash": "US30_cash",
    "US30": "US30_cash",
    "NAS100": "NAS100",
    "USDJPY": "USDJPY",
    "GBPJPY": "GBPJPY",
    "GBPUSD": "GBPUSD",
}


def _canonical_symbol(sym: str) -> str:
    """Return upper-case canonical instrument key.

    Note: ``US30`` and ``US30_cash`` are kept distinct in casing — the
    trade-records dirs use ``US30_cash``. We upper-case the alpha part
    but preserve underscored suffixes.
    """
    if not sym:
        return ""
    s = sym.strip()
    # Preserve _cash, _us etc. by upper-casing the prefix only.
    if "_" in s:
        prefix, rest = s.split("_", 1)
        return f"{prefix.upper()}_{rest.lower()}"
    return s.upper()


def _tick_size(symbol: str) -> float:
    """Return tick size for a symbol; defaults to 0.01 if unknown."""
    canonical = _canonical_symbol(symbol)
    return TICK_SIZE.get(canonical, TICK_SIZE.get(canonical.upper(), 0.01))


# ---------------------------------------------------------------------------
# Time normalization (mirrors L56/L58 contract)
# ---------------------------------------------------------------------------


def _normalize_to_utc_minute(ts: Any) -> Optional[dt.datetime]:
    """Normalize a timestamp to whole-minute UTC tz-aware datetime.

    Mirrors :func:`src.research_infra.f3_replay_engine._normalize_to_utc_minute`
    so realized-R indices built by L58 helpers are compatible.
    """
    if ts is None:
        return None
    if isinstance(ts, dt.datetime):
        parsed = ts
    else:
        s = str(ts).strip()
        if not s:
            return None
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            parsed = dt.datetime.fromisoformat(s)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    parsed = parsed.astimezone(dt.timezone.utc)
    return parsed.replace(second=0, microsecond=0)


def _make_cand_id(symbol: str, candle_close_time: dt.datetime) -> str:
    """Stable cand_id from (symbol, candle_close_time).

    Same shape as L58: ``"{SYMBOL_UPPER}|{ISO_UTC_MINUTE}"``.
    """
    return f"{_canonical_symbol(symbol).upper()}|{candle_close_time.isoformat()}"


# ---------------------------------------------------------------------------
# Pure data shapes
# ---------------------------------------------------------------------------


@dataclass
class MechanicalSetup:
    """A single mechanical entry plan derived from one CAND's MSO.

    All fields are pure floats / strings / datetimes — no pandas, no
    OHLCV. ``outcome`` resolution is a separate step.
    """

    # Identity
    cand_id: str
    symbol: str
    candle_close_time: dt.datetime
    side: str  # "LONG" | "SHORT"
    framework: str

    # OB the mechanical arm targeted
    ob_high: float
    ob_low: float
    ob_formation_time: Optional[str] = None
    ob_mitigated: bool = False
    ob_source_tf: str = "H1"

    # Pricing
    entry: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    rr: float = 0.0
    sl_buffer_used: float = 0.0
    h1_atr: Optional[float] = None
    tick_size: float = 0.01

    # Diagnostics — why we picked this OB / what fallbacks fired
    selection_reason: str = ""
    tp_source: str = ""  # "swing" or "rr_floor"
    skip_reason: Optional[str] = None  # None on success


@dataclass
class MechanicalOutcome:
    """Outcome of one mechanical setup walked forward through OHLCV.

    ``realized_r`` is the canonical R-multiple computed against the
    initial (entry, SL) distance:

        LONG : (exit_price - entry) / (entry - SL)
        SHORT: (entry - exit_price) / (SL - entry)

    For TP / SL hits the value is exact +RR / -1.0; for TIMEOUT it is
    the mark-to-market of the last bar's close.
    """

    cand_id: str
    outcome: str  # "TP" | "SL" | "TIMEOUT" | "NO_DATA" | "INVALID"
    realized_r: Optional[float]
    bars_in_trade: int
    exit_time: Optional[str]
    skip_reason: Optional[str] = None


@dataclass
class ReplayRow:
    """One per-CAND output row written to results.jsonl."""

    cand_id: str
    symbol: str
    candle_close_time: str  # ISO string
    period_month: str  # "YYYY-MM"
    side: Optional[str]
    framework: str
    kill_zone: str

    # AI arm (recorded)
    ai_decision: str
    ai_realized_r: Optional[float]
    ai_outcome_resolved: bool

    # Mechanical arm (computed)
    mechanical_skip_reason: Optional[str]
    mechanical_entry: Optional[float]
    mechanical_sl: Optional[float]
    mechanical_tp: Optional[float]
    mechanical_rr: Optional[float]
    mechanical_outcome: Optional[str]
    mechanical_realized_r: Optional[float]
    mechanical_bars_in_trade: Optional[int]

    # Walk-level: did mechanical arm even fire? Decision-level diff is
    # implicit (AI was CAND, mechanical fires whenever a usable OB is
    # in MSO).
    mechanical_fired: bool

    # Realized-R gap = AI - mechanical (positive: AI better; negative:
    # mechanical better). Populated only when both arms have a value.
    realized_r_gap: Optional[float]


# ---------------------------------------------------------------------------
# Config defaults loader
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BaselineConfig:
    """Mechanical-replay config — ATR / tick / RR defaults read from
    ``config/agent_config.yaml``.
    """

    sl_buffer_atr_multiplier: float = 0.25
    sl_buffer_min_ticks: int = 5
    min_rr: float = DEFAULT_MIN_RR
    retrace_pct: float = RETRACE_PCT
    max_hold_bars: int = DEFAULT_MAX_HOLD_BARS

    @classmethod
    def from_yaml(cls, path: Path = DEFAULT_CONFIG_PATH) -> "BaselineConfig":
        """Load defaults from agent_config.yaml. Falls back to dataclass
        defaults if the file is missing or PyYAML is unavailable.
        """
        try:
            import yaml  # type: ignore
        except ImportError:
            logger.warning("PyYAML not available; using BaselineConfig defaults")
            return cls()
        try:
            with path.open("r", encoding="utf-8") as fh:
                cfg = yaml.safe_load(fh) or {}
        except OSError as exc:
            logger.warning("Cannot read %s: %s — using defaults", path, exc)
            return cls()
        risk = cfg.get("risk") or {}
        return cls(
            sl_buffer_atr_multiplier=float(risk.get("sl_buffer_atr_multiplier", 0.25)),
            sl_buffer_min_ticks=int(risk.get("sl_buffer_min_ticks", 5)),
            min_rr=float(risk.get("min_rr", DEFAULT_MIN_RR)),
        )


# ---------------------------------------------------------------------------
# OB selection
# ---------------------------------------------------------------------------


def _select_target_ob(
    h1_obs: Sequence[Mapping[str, Any]],
    side: str,
    candle_close_time: dt.datetime,
) -> Tuple[Optional[Mapping[str, Any]], str]:
    """Pick the OB the mechanical arm targets.

    Selection rules (mirror live system OB-pullback semantics):

    * For LONG: bullish OB only.
    * For SHORT: bearish OB only.
    * The OB's ``formation_time`` must be strictly before
      ``candle_close_time`` (no future leakage).
    * Skip mitigated OBs — the live system rejects them at L2.
    * Among the survivors pick the one with the LATEST
      ``formation_time`` (the most-recent unmitigated zone — same
      heuristic the prompt instructs the AI to use).

    Returns ``(ob_dict_or_None, reason)``. On miss the reason explains
    why (NO_OBS / NO_BULLISH / NO_BEARISH / ALL_MITIGATED / ALL_FUTURE).
    """
    if not h1_obs:
        return None, "NO_OBS"
    target_type = "bullish" if side == "LONG" else "bearish"
    same_side = [ob for ob in h1_obs if ob.get("type") == target_type]
    if not same_side:
        return None, f"NO_{target_type.upper()}_OB"
    # Filter by formation_time < candle_close_time
    past = []
    for ob in same_side:
        ft = ob.get("formation_time")
        ft_norm = _normalize_to_utc_minute(ft)
        if ft_norm is None:
            # If the OB has no formation_time we cannot prove it's in
            # the past — drop conservatively.
            continue
        if ft_norm >= candle_close_time:
            continue
        past.append((ft_norm, ob))
    if not past:
        return None, "ALL_FUTURE_OR_UNDATED"
    # Drop mitigated
    unmitigated = [(ft, ob) for ft, ob in past if not ob.get("mitigated", False)]
    if not unmitigated:
        return None, "ALL_MITIGATED"
    # Latest formation_time wins
    unmitigated.sort(key=lambda pair: pair[0])
    return unmitigated[-1][1], "OK"


# ---------------------------------------------------------------------------
# Swing-based TP target
# ---------------------------------------------------------------------------


def _nearest_opposing_swing(
    swings: Sequence[Mapping[str, Any]],
    side: str,
    entry: float,
    candle_close_time: dt.datetime,
) -> Optional[float]:
    """Find the nearest opposing-side swing relative to the entry.

    For a LONG, the TP target is the next swing HIGH above entry that
    exists in the swings list at decision time (no future leakage).
    For a SHORT it's the next swing LOW below entry.

    Returns the swing price, or None if no qualifying swing exists.
    """
    if not swings:
        return None
    target_type = "high" if side == "LONG" else "low"
    candidates: List[float] = []
    for s in swings:
        if s.get("type") != target_type:
            continue
        ts = _normalize_to_utc_minute(s.get("time"))
        if ts is None or ts >= candle_close_time:
            continue
        try:
            price = float(s.get("price"))
        except (TypeError, ValueError):
            continue
        if side == "LONG" and price > entry:
            candidates.append(price)
        elif side == "SHORT" and price < entry:
            candidates.append(price)
    if not candidates:
        return None
    if side == "LONG":
        return min(candidates)  # nearest above entry
    return max(candidates)  # nearest below entry


# ---------------------------------------------------------------------------
# Pure mechanical entry computation
# ---------------------------------------------------------------------------


def compute_mechanical_entry(
    mso: Mapping[str, Any],
    side: str,
    *,
    symbol: str,
    candle_close_time: dt.datetime,
    framework: str = "ob_retest",
    cfg: Optional[BaselineConfig] = None,
    cand_id: Optional[str] = None,
) -> MechanicalSetup:
    """Compute the mechanical OB-pullback entry for one CAND.

    Pure function. Reads only from ``mso`` (a snapshot of the same MSO
    the AI saw at decision time) and ``cfg``. Returns a fully-populated
    :class:`MechanicalSetup`. On any reason we cannot price a trade, the
    returned object has ``skip_reason`` set and ``entry == sl == tp ==
    0.0`` — the caller should check ``skip_reason`` before using the
    pricing fields.

    Parameters
    ----------
    mso :
        The market-state snapshot. Must have
        ``timeframes.H1.order_blocks`` (a list) and
        ``timeframes.H1.atr_14`` for the SL buffer.
    side :
        "LONG" or "SHORT". Required — the mechanical arm tests the
        same side the AI did (we're not opining on direction
        selection here).
    symbol :
        Used for tick-size lookup.
    candle_close_time :
        Used to filter out OBs / swings that formed after the CAND.
    framework :
        Currently always treated as ``ob_retest`` (the only canonical
        pullback rule). Other framework strings produce
        ``skip_reason="UNSUPPORTED_FRAMEWORK"`` so the caller can
        surface them in the report.
    cfg :
        Mechanical config; defaults to ``BaselineConfig()`` (matches
        agent_config.yaml).
    cand_id :
        Pre-computed cand_id; if ``None`` we derive it from
        ``(symbol, candle_close_time)``.
    """
    if cfg is None:
        cfg = BaselineConfig()
    if cand_id is None:
        cand_id = _make_cand_id(symbol, candle_close_time)
    side_norm = (side or "").strip().upper()
    if side_norm not in {"LONG", "SHORT"}:
        return _empty_setup(cand_id, symbol, candle_close_time, side_norm,
                            framework, "INVALID_SIDE")

    if framework not in ("ob_retest", "", None):
        # We deliberately skip non-OB frameworks here. fvg_fill /
        # breaker_re_entry are different rules and out of scope for
        # A1's "OB-zone mechanical pullback" question.
        return _empty_setup(cand_id, symbol, candle_close_time, side_norm,
                            framework, "UNSUPPORTED_FRAMEWORK")

    timeframes = mso.get("timeframes") or {}
    h1 = timeframes.get("H1") or {}
    obs = h1.get("order_blocks") or []
    h1_atr_raw = h1.get("atr_14")
    h1_atr: Optional[float]
    try:
        h1_atr = float(h1_atr_raw) if h1_atr_raw is not None else None
    except (TypeError, ValueError):
        h1_atr = None

    ob, reason = _select_target_ob(obs, side_norm, candle_close_time)
    if ob is None:
        return _empty_setup(cand_id, symbol, candle_close_time, side_norm,
                            framework, reason)

    try:
        ob_high = float(ob["high"])
        ob_low = float(ob["low"])
    except (TypeError, ValueError, KeyError):
        return _empty_setup(cand_id, symbol, candle_close_time, side_norm,
                            framework, "BAD_OB_PRICES")
    if ob_high <= ob_low:
        return _empty_setup(cand_id, symbol, candle_close_time, side_norm,
                            framework, "DEGENERATE_OB")

    # 80% retrace into the OB:
    #   bullish OB: price comes down from above; entry near OB top
    #   bearish OB: price comes up from below; entry near OB bottom
    if side_norm == "LONG":
        entry = ob_low + cfg.retrace_pct * (ob_high - ob_low)
    else:
        entry = ob_high - cfg.retrace_pct * (ob_high - ob_low)

    # SL buffer
    tick = _tick_size(symbol)
    if h1_atr is not None and h1_atr > 0:
        atr_buf = cfg.sl_buffer_atr_multiplier * h1_atr
    else:
        atr_buf = 0.0
    tick_buf = cfg.sl_buffer_min_ticks * tick
    buffer = max(atr_buf, tick_buf)
    if buffer <= 0:
        return _empty_setup(cand_id, symbol, candle_close_time, side_norm,
                            framework, "BAD_SL_BUFFER")

    if side_norm == "LONG":
        sl = ob_low - buffer
    else:
        sl = ob_high + buffer

    sl_dist = abs(entry - sl)
    if sl_dist <= 0:
        return _empty_setup(cand_id, symbol, candle_close_time, side_norm,
                            framework, "DEGENERATE_SL")

    # TP: nearest opposing swing OR rr_floor fallback
    swings = h1.get("swings") or []
    swing_tp = _nearest_opposing_swing(swings, side_norm, entry, candle_close_time)
    tp_source = "rr_floor"
    if swing_tp is not None:
        if side_norm == "LONG":
            implied_rr = (swing_tp - entry) / sl_dist
        else:
            implied_rr = (entry - swing_tp) / sl_dist
        if implied_rr >= cfg.min_rr:
            tp = swing_tp
            tp_source = "swing"
        else:
            # Fallback: clamp to min_rr from entry
            if side_norm == "LONG":
                tp = entry + cfg.min_rr * sl_dist
            else:
                tp = entry - cfg.min_rr * sl_dist
    else:
        if side_norm == "LONG":
            tp = entry + cfg.min_rr * sl_dist
        else:
            tp = entry - cfg.min_rr * sl_dist

    rr = (abs(tp - entry) / sl_dist) if sl_dist > 0 else 0.0

    return MechanicalSetup(
        cand_id=cand_id,
        symbol=_canonical_symbol(symbol),
        candle_close_time=candle_close_time,
        side=side_norm,
        framework=framework or "ob_retest",
        ob_high=ob_high,
        ob_low=ob_low,
        ob_formation_time=ob.get("formation_time"),
        ob_mitigated=bool(ob.get("mitigated", False)),
        ob_source_tf="H1",
        entry=round(entry, 6),
        sl=round(sl, 6),
        tp=round(tp, 6),
        rr=round(rr, 4),
        sl_buffer_used=round(buffer, 6),
        h1_atr=h1_atr,
        tick_size=tick,
        selection_reason="OK",
        tp_source=tp_source,
        skip_reason=None,
    )


def _empty_setup(
    cand_id: str,
    symbol: str,
    candle_close_time: dt.datetime,
    side: str,
    framework: str,
    skip_reason: str,
) -> MechanicalSetup:
    return MechanicalSetup(
        cand_id=cand_id,
        symbol=_canonical_symbol(symbol),
        candle_close_time=candle_close_time,
        side=side or "",
        framework=framework or "",
        ob_high=0.0,
        ob_low=0.0,
        skip_reason=skip_reason,
    )


# ---------------------------------------------------------------------------
# OHLCV loading + caching
# ---------------------------------------------------------------------------


_OHLCV_CACHE: Dict[str, List[Dict[str, Any]]] = {}


def _ohlcv_path(symbol: str, ohlcv_dir: Path) -> Optional[Path]:
    """Resolve the ``{SYMBOL}_M15.csv`` path; ``None`` if missing."""
    canonical = _canonical_symbol(symbol)
    stem = OHLCV_STEM.get(canonical) or OHLCV_STEM.get(canonical.upper())
    if stem is None:
        # Last-resort: try the input verbatim
        stem = canonical
    p = ohlcv_dir / f"{stem}_M15.csv"
    if p.exists():
        return p
    return None


def _load_ohlcv(symbol: str, ohlcv_dir: Path) -> List[Dict[str, Any]]:
    """Load the M15 OHLCV CSV for ``symbol``. Cached per process.

    The CSV header is ``time,open,high,low,close,volume``; ``time`` is
    parsed to a tz-aware UTC datetime (the data was exported from MT5
    as broker-server time but the historical_2026 dump is in UTC per
    the archived export script under
    ``research/archive/root_legacy_artifacts_2026_05_31/root_files/``).

    Returns a list of dicts ordered by time ascending. Empty list if
    the file is missing.
    """
    cache_key = f"{_canonical_symbol(symbol)}|{ohlcv_dir}"
    if cache_key in _OHLCV_CACHE:
        return _OHLCV_CACHE[cache_key]
    path = _ohlcv_path(symbol, ohlcv_dir)
    if path is None:
        logger.warning("OHLCV file missing for %s under %s", symbol, ohlcv_dir)
        _OHLCV_CACHE[cache_key] = []
        return []
    rows: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as fh:
            header = fh.readline().strip().split(",")
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) < 5:
                    continue
                rec = dict(zip(header, parts))
                ts = _normalize_to_utc_minute(rec.get("time"))
                if ts is None:
                    continue
                try:
                    rows.append({
                        "time": ts,
                        "open": float(rec["open"]),
                        "high": float(rec["high"]),
                        "low": float(rec["low"]),
                        "close": float(rec["close"]),
                    })
                except (KeyError, TypeError, ValueError):
                    continue
    except OSError as exc:
        logger.warning("Cannot read %s: %s", path, exc)
        _OHLCV_CACHE[cache_key] = []
        return []
    rows.sort(key=lambda r: r["time"])
    _OHLCV_CACHE[cache_key] = rows
    return rows


def _bisect_first_after(
    rows: Sequence[Mapping[str, Any]], cutoff: dt.datetime
) -> int:
    """Return the index of the first row whose ``time > cutoff``.

    Standard bisect_right; rows must be sorted ascending. Returns
    ``len(rows)`` if all rows are at or before cutoff.
    """
    lo, hi = 0, len(rows)
    while lo < hi:
        mid = (lo + hi) // 2
        if rows[mid]["time"] <= cutoff:
            lo = mid + 1
        else:
            hi = mid
    return lo


# ---------------------------------------------------------------------------
# Outcome resolution
# ---------------------------------------------------------------------------


def resolve_mechanical_outcome(
    setup: MechanicalSetup,
    ohlcv_dir: Path = DEFAULT_OHLCV_DIR,
    *,
    max_hold_bars: int = DEFAULT_MAX_HOLD_BARS,
    ohlcv_rows: Optional[Sequence[Mapping[str, Any]]] = None,
    require_pending_fill: bool = True,
) -> MechanicalOutcome:
    """Walk M15 OHLCV forward from ``setup.candle_close_time`` and
    return the outcome.

    Two-stage walk-forward
    ----------------------
    Mechanical OB-pullback is a PENDING LIMIT order, not a market order.
    The trade only fills when price retraces back to the entry level. We
    enforce this in two stages:

    Stage 1 — Wait for fill. Walk bars until price visits the entry:

      * **LONG**:  fill when ``low <= entry`` (price pulls back into the OB)
      * **SHORT**: fill when ``high >= entry`` (price pulls back into the OB)

    If no fill within ``max_hold_bars``, ``outcome="NO_ENTRY"``,
    ``realized_r=None`` (the AI-vs-mechanical compare still works because
    ``mechanical_realized_r`` will be None and the row drops out of the
    matched-pair aggregate).

    Stage 2 — Walk for TP / SL after fill:

    * **LONG**:
        if ``low <= setup.sl`` -> outcome=SL, R=-1.0
        if ``high >= setup.tp`` -> outcome=TP, R=+RR
    * **SHORT**:
        if ``high >= setup.sl`` -> outcome=SL, R=-1.0
        if ``low <= setup.tp`` -> outcome=TP, R=+RR

    Both can fire on the same bar — SL-first conservative rule wins
    (matches A6 baseline_simulator + dumb_baseline_shadow_logger).

    On the ``max_hold_bars``-th bar without TP/SL, outcome=TIMEOUT,
    R=(close - entry)/sl_dist signed by direction. ``max_hold_bars`` is
    a HARD UPPER BOUND on Stage 1 + Stage 2 combined.

    Same-bar fill + outcome
    -----------------------
    If a bar fills the entry AND hits TP or SL on the same bar, we apply
    the SL-first rule against the fill bar's high/low range. Treating
    same-bar TP fills as wins with realized_r=+RR overstates wins; we
    treat them as ``outcome="SAME_BAR"`` with ``realized_r=None`` to
    flag the ambiguity (mid-bar order, no microstructure visibility).
    Tests: ``test_outcome_same_bar_skipped``.

    Parameters
    ----------
    ohlcv_rows :
        Optional pre-loaded rows for testing. When supplied, ``ohlcv_dir``
        is ignored.
    require_pending_fill :
        When True (default), the two-stage walk above is used. When False,
        we behave like a market order at the candle close — useful for
        unit-testing the outcome resolver in isolation. Production
        replays MUST keep the default.
    """
    if setup.skip_reason is not None:
        return MechanicalOutcome(
            cand_id=setup.cand_id,
            outcome="INVALID",
            realized_r=None,
            bars_in_trade=0,
            exit_time=None,
            skip_reason=setup.skip_reason,
        )

    sl_dist = abs(setup.entry - setup.sl)
    if sl_dist <= 0:
        return MechanicalOutcome(
            cand_id=setup.cand_id,
            outcome="INVALID",
            realized_r=None,
            bars_in_trade=0,
            exit_time=None,
            skip_reason="DEGENERATE_SL",
        )

    rows = list(ohlcv_rows) if ohlcv_rows is not None else _load_ohlcv(
        setup.symbol, ohlcv_dir
    )
    if not rows:
        return MechanicalOutcome(
            cand_id=setup.cand_id,
            outcome="NO_DATA",
            realized_r=None,
            bars_in_trade=0,
            exit_time=None,
            skip_reason="OHLCV_MISSING",
        )

    start_idx = _bisect_first_after(rows, setup.candle_close_time)
    end_idx = min(len(rows), start_idx + max_hold_bars)
    walk = rows[start_idx:end_idx]

    if not walk:
        return MechanicalOutcome(
            cand_id=setup.cand_id,
            outcome="NO_DATA",
            realized_r=None,
            bars_in_trade=0,
            exit_time=None,
            skip_reason="NO_FUTURE_BARS",
        )

    # Walk
    rr = (abs(setup.tp - setup.entry) / sl_dist) if sl_dist > 0 else 0.0
    bars_walked = 0
    filled = not require_pending_fill  # market-order mode = filled at start
    bars_in_trade = 0
    last_close: Optional[float] = None
    last_time: Optional[Any] = None
    for bar in walk:
        bars_walked += 1
        try:
            high = float(bar["high"])
            low = float(bar["low"])
            close = float(bar["close"])
        except (KeyError, TypeError, ValueError):
            continue
        last_close = close
        last_time = bar.get("time")

        if not filled:
            # Stage 1: wait for entry
            if setup.side == "LONG":
                fill_hit = low <= setup.entry
            else:
                fill_hit = high >= setup.entry
            if fill_hit:
                # Same-bar guard: if this bar would also hit SL or TP,
                # we can't safely resolve without microstructure.
                if setup.side == "LONG":
                    sl_hit_same = low <= setup.sl
                    tp_hit_same = high >= setup.tp
                else:
                    sl_hit_same = high >= setup.sl
                    tp_hit_same = low <= setup.tp
                if sl_hit_same or tp_hit_same:
                    return MechanicalOutcome(
                        cand_id=setup.cand_id,
                        outcome="SAME_BAR",
                        realized_r=None,
                        bars_in_trade=bars_walked,
                        exit_time=str(last_time),
                        skip_reason="FILL_AND_TPSL_SAME_BAR",
                    )
                filled = True
                bars_in_trade = 0
                continue
            # Not filled — keep walking
            continue

        # Stage 2: trade is filled, watch for TP / SL
        bars_in_trade += 1
        if setup.side == "LONG":
            sl_hit = low <= setup.sl
            tp_hit = high >= setup.tp
        else:  # SHORT
            sl_hit = high >= setup.sl
            tp_hit = low <= setup.tp
        # SL-first rule
        if sl_hit:
            return MechanicalOutcome(
                cand_id=setup.cand_id,
                outcome="SL",
                realized_r=-1.0,
                bars_in_trade=bars_in_trade,
                exit_time=str(last_time),
            )
        if tp_hit:
            return MechanicalOutcome(
                cand_id=setup.cand_id,
                outcome="TP",
                realized_r=round(rr, 4),
                bars_in_trade=bars_in_trade,
                exit_time=str(last_time),
            )

    # Out of bars
    if not filled:
        return MechanicalOutcome(
            cand_id=setup.cand_id,
            outcome="NO_ENTRY",
            realized_r=None,
            bars_in_trade=bars_walked,
            exit_time=str(last_time) if last_time is not None else None,
            skip_reason="NEVER_FILLED",
        )

    # Timeout: mark-to-market on last bar's close
    if last_close is None:
        return MechanicalOutcome(
            cand_id=setup.cand_id,
            outcome="NO_DATA",
            realized_r=None,
            bars_in_trade=bars_in_trade,
            exit_time=None,
            skip_reason="ALL_BARS_BAD",
        )

    if setup.side == "LONG":
        ttm_r = (last_close - setup.entry) / sl_dist
    else:
        ttm_r = (setup.entry - last_close) / sl_dist

    return MechanicalOutcome(
        cand_id=setup.cand_id,
        outcome="TIMEOUT",
        realized_r=round(ttm_r, 4),
        bars_in_trade=bars_in_trade,
        exit_time=str(last_time),
    )


# ---------------------------------------------------------------------------
# CAND iteration over trade records
# ---------------------------------------------------------------------------


def _iter_trade_records(
    trade_records_dir: Path, instruments: Optional[Sequence[str]] = None
) -> Iterator[Tuple[Path, Mapping[str, Any]]]:
    """Yield ``(path, record_dict)`` for every trade record JSON.

    Mirrors L58 ``_iter_trade_records`` to keep behavior consistent.
    """
    if not trade_records_dir.exists():
        return
    inst_filter: Optional[set] = None
    if instruments:
        inst_filter = {_canonical_symbol(i).upper() for i in instruments}
    for inst_dir in sorted(trade_records_dir.iterdir()):
        if not inst_dir.is_dir():
            continue
        if inst_filter is not None and inst_dir.name.upper() not in inst_filter:
            # Match both upper-cased and lowercased _cash suffix
            canonical = _canonical_symbol(inst_dir.name).upper()
            if canonical not in inst_filter:
                continue
        for path in sorted(inst_dir.glob("*.json")):
            if path.stem.startswith("_"):
                continue
            try:
                with path.open("r", encoding="utf-8") as fh:
                    yield path, json.load(fh)
            except Exception as exc:
                logger.warning("Skipping unreadable trade record %s: %s", path, exc)


def _extract_realized_r(rec: Mapping[str, Any]) -> Optional[float]:
    """Best-effort realized-R extraction (mirrors L58)."""
    pipeline = rec.get("decision_pipeline") or {}
    if isinstance(pipeline, Mapping):
        outcome = pipeline.get("outcome")
        if isinstance(outcome, Mapping):
            r = outcome.get("r_multiple")
            if isinstance(r, (int, float)):
                return float(r)
    exit_block = rec.get("exit")
    if isinstance(exit_block, Mapping):
        r = exit_block.get("r_multiple")
        if isinstance(r, (int, float)):
            return float(r)
    r = rec.get("r_multiple")
    if isinstance(r, (int, float)):
        return float(r)
    return None


def _extract_kill_zone(rec: Mapping[str, Any]) -> str:
    meta = rec.get("metadata") or {}
    return str(meta.get("kill_zone") or "")


def _extract_side(rec: Mapping[str, Any]) -> Optional[str]:
    """Extract AI direction from a trade record. Mirrors L58 behavior."""
    pipeline = rec.get("decision_pipeline") or {}
    if isinstance(pipeline, Mapping):
        side = pipeline.get("ai_direction")
        if side:
            return str(side).upper()
    tp = rec.get("trade_parameters") or {}
    if isinstance(tp, Mapping):
        side = tp.get("direction")
        if side:
            return str(side).upper()
    return None


# ---------------------------------------------------------------------------
# Replay orchestrator
# ---------------------------------------------------------------------------


@dataclass
class DumbBaselineReplay:
    """Top-level orchestrator. Iterates trade records, computes mechanical
    outcomes, joins to AI realized R, emits per-row + aggregated views.

    Construction is configuration-only; the actual work happens in
    :meth:`run` (or :meth:`run_one` for testing one CAND in isolation).
    """

    trade_records_dir: Path = DEFAULT_TRADE_RECORDS_DIR
    ohlcv_dir: Path = DEFAULT_OHLCV_DIR
    cfg: BaselineConfig = field(default_factory=BaselineConfig)
    instruments: Optional[Sequence[str]] = None
    since: Optional[dt.datetime] = None
    until: Optional[dt.datetime] = None

    def run_one(self, rec: Mapping[str, Any]) -> Optional[ReplayRow]:
        """Replay a single record. Returns ``None`` if the record has
        no candle_close_time (cannot identify) or no decision (the
        record was a non-CAND).
        """
        meta = rec.get("metadata") or {}
        candle_close_time = _normalize_to_utc_minute(meta.get("candle_time"))
        if candle_close_time is None:
            return None
        symbol_raw = meta.get("symbol") or ""
        if not symbol_raw:
            return None
        symbol = _canonical_symbol(symbol_raw)

        # Time filters
        if self.since is not None and candle_close_time < self.since:
            return None
        if self.until is not None and candle_close_time > self.until:
            return None

        pipeline = rec.get("decision_pipeline") or {}
        ai_decision = str(pipeline.get("ai_decision") or "")
        framework = str(pipeline.get("ai_framework") or "")
        side = _extract_side(rec)
        kill_zone = _extract_kill_zone(rec)

        # Realized AI R via the L58 join contract: trade_record holds
        # the same (symbol, candle_close_time, side) so it's a direct
        # lookup, not a multi-key join.
        ai_r = _extract_realized_r(rec)
        ai_resolved = ai_r is not None

        # Mechanical arm
        skip_reason: Optional[str] = None
        setup: Optional[MechanicalSetup] = None
        outcome: Optional[MechanicalOutcome] = None

        if not side:
            skip_reason = "NO_AI_SIDE"
        elif ai_decision != "CANDIDATE":
            # We could in principle replay non-CAND evaluations too,
            # but they don't carry the tight join semantics — skip.
            skip_reason = "NOT_CAND"
        else:
            mso = rec.get("mso") or {}
            if not mso:
                skip_reason = "NO_MSO"
            else:
                cand_id = _make_cand_id(symbol, candle_close_time)
                setup = compute_mechanical_entry(
                    mso, side,
                    symbol=symbol,
                    candle_close_time=candle_close_time,
                    framework=framework,
                    cfg=self.cfg,
                    cand_id=cand_id,
                )
                if setup.skip_reason is not None:
                    skip_reason = setup.skip_reason
                else:
                    outcome = resolve_mechanical_outcome(
                        setup, self.ohlcv_dir,
                        max_hold_bars=self.cfg.max_hold_bars,
                    )
                    if outcome.skip_reason is not None and outcome.outcome != "TIMEOUT":
                        skip_reason = outcome.skip_reason

        cand_id = (setup.cand_id if setup is not None
                   else _make_cand_id(symbol, candle_close_time))
        period_month = candle_close_time.strftime("%Y-%m")

        mech_realized = outcome.realized_r if outcome is not None else None
        mech_outcome_str = outcome.outcome if outcome is not None else None
        mech_bars = outcome.bars_in_trade if outcome is not None else None

        gap: Optional[float] = None
        if ai_r is not None and mech_realized is not None:
            gap = round(float(ai_r) - float(mech_realized), 4)

        return ReplayRow(
            cand_id=cand_id,
            symbol=symbol,
            candle_close_time=candle_close_time.isoformat(),
            period_month=period_month,
            side=side,
            framework=framework,
            kill_zone=kill_zone,
            ai_decision=ai_decision,
            ai_realized_r=ai_r,
            ai_outcome_resolved=ai_resolved,
            mechanical_skip_reason=skip_reason,
            mechanical_entry=setup.entry if (setup and setup.skip_reason is None) else None,
            mechanical_sl=setup.sl if (setup and setup.skip_reason is None) else None,
            mechanical_tp=setup.tp if (setup and setup.skip_reason is None) else None,
            mechanical_rr=setup.rr if (setup and setup.skip_reason is None) else None,
            mechanical_outcome=mech_outcome_str,
            mechanical_realized_r=mech_realized,
            mechanical_bars_in_trade=mech_bars,
            mechanical_fired=(setup is not None and setup.skip_reason is None),
            realized_r_gap=gap,
        )

    def run(self) -> List[ReplayRow]:
        """Iterate every trade record and emit per-CAND ReplayRow.

        Order is deterministic: instruments alphabetically, files
        alphabetically inside each instrument.
        """
        rows: List[ReplayRow] = []
        for path, rec in _iter_trade_records(self.trade_records_dir, self.instruments):
            try:
                row = self.run_one(rec)
            except Exception as exc:  # noqa: BLE001 — never propagate
                logger.warning("Failed to replay %s: %s", path, exc, exc_info=True)
                continue
            if row is not None:
                rows.append(row)
        return rows


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def _group_key(row: ReplayRow) -> Tuple[str, str]:
    """(period_month, symbol) — primary aggregation key."""
    return (row.period_month, row.symbol)


def _mean(xs: Sequence[Optional[float]]) -> Optional[float]:
    """Mean over not-None values; ``None`` if all None."""
    vals = [x for x in xs if x is not None]
    if not vals:
        return None
    return round(sum(vals) / len(vals), 4)


def _wr(xs: Sequence[Optional[float]]) -> Optional[float]:
    """Win rate (R > 0) over not-None values."""
    vals = [x for x in xs if x is not None]
    if not vals:
        return None
    wins = sum(1 for x in vals if x > 0)
    return round(wins / len(vals), 4)


def _stddev(xs: Sequence[float]) -> float:
    """Population stddev. Returns 0.0 for n<2."""
    if len(xs) < 2:
        return 0.0
    m = sum(xs) / len(xs)
    var = sum((x - m) ** 2 for x in xs) / len(xs)
    return math.sqrt(var)


def aggregate(rows: Sequence[ReplayRow]) -> Dict[str, Any]:
    """Aggregate replay rows into per-month per-instrument stats + the
    cross-half verdict block.

    Returns a dict serializable to summary.json.
    """
    # Per-cell aggregates
    cells: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for row in rows:
        key = _group_key(row)
        cell = cells.setdefault(key, {
            "period_month": row.period_month,
            "symbol": row.symbol,
            "ai_rs": [],
            "mechanical_rs": [],
            "matched_pairs": [],   # only rows where BOTH have R
            "mechanical_fired_count": 0,
            "n_rows": 0,
            "n_cand": 0,
            "skip_reasons": {},
        })
        cell["n_rows"] += 1
        if row.ai_decision == "CANDIDATE":
            cell["n_cand"] += 1
        if row.ai_realized_r is not None:
            cell["ai_rs"].append(row.ai_realized_r)
        if row.mechanical_realized_r is not None:
            cell["mechanical_rs"].append(row.mechanical_realized_r)
        if row.mechanical_fired:
            cell["mechanical_fired_count"] += 1
        if row.mechanical_skip_reason:
            cell["skip_reasons"][row.mechanical_skip_reason] = (
                cell["skip_reasons"].get(row.mechanical_skip_reason, 0) + 1
            )
        if row.ai_realized_r is not None and row.mechanical_realized_r is not None:
            cell["matched_pairs"].append(
                (float(row.ai_realized_r), float(row.mechanical_realized_r))
            )

    cell_rows: List[Dict[str, Any]] = []
    for key, cell in sorted(cells.items()):
        ai_rs: List[float] = cell["ai_rs"]
        mech_rs: List[float] = cell["mechanical_rs"]
        matched: List[Tuple[float, float]] = cell["matched_pairs"]
        cell_rows.append({
            "period_month": cell["period_month"],
            "symbol": cell["symbol"],
            "n_rows": cell["n_rows"],
            "n_cand": cell["n_cand"],
            "ai_n": len(ai_rs),
            "ai_mean_r": _mean(ai_rs),
            "ai_wr": _wr(ai_rs),
            "mechanical_fired": cell["mechanical_fired_count"],
            "mechanical_n": len(mech_rs),
            "mechanical_mean_r": _mean(mech_rs),
            "mechanical_wr": _wr(mech_rs),
            "matched_pairs": len(matched),
            "matched_ai_mean_r": (
                _mean([a for a, _ in matched]) if matched else None
            ),
            "matched_mechanical_mean_r": (
                _mean([m for _, m in matched]) if matched else None
            ),
            "matched_gap_mean_r": (
                round(sum(a - m for a, m in matched) / len(matched), 4)
                if matched else None
            ),
            "skip_reasons": cell["skip_reasons"],
        })

    # H1/H2 verdict
    def _half(period_month: str) -> str:
        # Months 01-02 = H1; 03+ = H2 (matches the H1/H2 framing in
        # CLAUDE.md unresolved item #4 — Jan+Feb 2026 vs Mar+Apr 2026).
        try:
            mm = int(period_month.split("-")[1])
        except (IndexError, ValueError):
            return "UNK"
        if 1 <= mm <= 2:
            return "H1"
        if 3 <= mm <= 6:
            return "H2"
        return "UNK"

    half_buckets: Dict[str, List[Tuple[float, float]]] = {"H1": [], "H2": []}
    for row in rows:
        h = _half(row.period_month)
        if h == "UNK":
            continue
        if row.ai_realized_r is not None and row.mechanical_realized_r is not None:
            half_buckets[h].append((row.ai_realized_r, row.mechanical_realized_r))

    def _half_stats(pairs: List[Tuple[float, float]]) -> Dict[str, Any]:
        if not pairs:
            return {
                "n": 0,
                "ai_mean_r": None,
                "mechanical_mean_r": None,
                "ai_wr": None,
                "mechanical_wr": None,
                "gap_mean_r": None,
                "gap_wr_pp": None,
            }
        ai_rs = [a for a, _ in pairs]
        mech_rs = [m for _, m in pairs]
        ai_wr = sum(1 for a in ai_rs if a > 0) / len(ai_rs)
        mech_wr = sum(1 for m in mech_rs if m > 0) / len(mech_rs)
        return {
            "n": len(pairs),
            "ai_mean_r": round(sum(ai_rs) / len(ai_rs), 4),
            "mechanical_mean_r": round(sum(mech_rs) / len(mech_rs), 4),
            "ai_wr": round(ai_wr, 4),
            "mechanical_wr": round(mech_wr, 4),
            "gap_mean_r": round(sum(a - m for a, m in pairs) / len(pairs), 4),
            "gap_wr_pp": round((ai_wr - mech_wr) * 100, 2),
        }

    h1_stats = _half_stats(half_buckets["H1"])
    h2_stats = _half_stats(half_buckets["H2"])

    # Per-month gap stability stddev (only months with matched pairs)
    monthly_gaps_pp: List[float] = []
    for cell in cell_rows:
        if cell["matched_pairs"] >= 1 and cell["matched_gap_mean_r"] is not None:
            # WR-pp gap per month
            ai_wr = cell["ai_wr"]
            mech_wr = cell["mechanical_wr"]
            if ai_wr is not None and mech_wr is not None:
                monthly_gaps_pp.append((ai_wr - mech_wr) * 100)
    gap_stddev_pp = round(_stddev(monthly_gaps_pp), 2)

    # Verdict diagnosis
    verdict = _diagnose(h1_stats, h2_stats, gap_stddev_pp)

    # Per-instrument coverage
    coverage: Dict[str, Dict[str, int]] = {}
    for row in rows:
        c = coverage.setdefault(row.symbol, {
            "n_cand_replayed": 0,
            "n_mechanical_fired": 0,
            "n_matched_pairs": 0,
        })
        if row.ai_decision == "CANDIDATE":
            c["n_cand_replayed"] += 1
        if row.mechanical_fired:
            c["n_mechanical_fired"] += 1
        if row.ai_realized_r is not None and row.mechanical_realized_r is not None:
            c["n_matched_pairs"] += 1

    return {
        "harness_version": HARNESS_VERSION,
        "config": asdict(BaselineConfig()) if isinstance(BaselineConfig(), object) else {},
        "n_rows_total": len(rows),
        "per_cell": cell_rows,
        "halves": {"H1": h1_stats, "H2": h2_stats},
        "monthly_gap_stddev_pp": gap_stddev_pp,
        "verdict": verdict,
        "per_instrument_coverage": coverage,
    }


def _diagnose(
    h1: Mapping[str, Any], h2: Mapping[str, Any], gap_stddev_pp: float
) -> Dict[str, Any]:
    """Map the halves+stddev into the SYSTEM/REGIME/MIXED/INCONCLUSIVE
    diagnosis.

    Decision tree (keeps the call mechanical and explainable):

    * INCONCLUSIVE if either half has fewer than 10 matched pairs.
    * REGIME_DECAY if mechanical mean R drops between H1 and H2 by
      ≥0.20R AND the gap delta H1→H2 is small (≤5pp WR change).
      The market changed; both arms collapsed together.
    * SYSTEM_DECAY if the AI-vs-mechanical gap WIDENS in H1's favor by
      ≥10pp WR or ≥0.30R, OR the gap REVERSES (AI was up, now down)
      such that mechanical beats AI by ≥5pp / ≥0.10R in H2. The AI
      lost something the market still rewards.
    * MIXED otherwise — both arms moved in the same direction but the
      AI's selectivity erosion is detectable at smaller magnitudes.
    """
    if h1.get("n", 0) < 10 or h2.get("n", 0) < 10:
        return {
            "diagnosis": "INCONCLUSIVE",
            "reasoning": (
                f"Insufficient matched pairs: H1 n={h1.get('n', 0)}, "
                f"H2 n={h2.get('n', 0)} (need >=10 each)."
            ),
            "h1_gap_wr_pp": h1.get("gap_wr_pp"),
            "h2_gap_wr_pp": h2.get("gap_wr_pp"),
            "gap_delta_pp": (
                None if h1.get("gap_wr_pp") is None or h2.get("gap_wr_pp") is None
                else round(h2.get("gap_wr_pp", 0) - h1.get("gap_wr_pp", 0), 2)
            ),
            "gap_stddev_pp": gap_stddev_pp,
        }

    h1_gap_pp = h1.get("gap_wr_pp", 0.0) or 0.0
    h2_gap_pp = h2.get("gap_wr_pp", 0.0) or 0.0
    h1_gap_r = h1.get("gap_mean_r", 0.0) or 0.0
    h2_gap_r = h2.get("gap_mean_r", 0.0) or 0.0
    gap_delta_pp = round(h2_gap_pp - h1_gap_pp, 2)

    h1_mech_r = h1.get("mechanical_mean_r", 0.0) or 0.0
    h2_mech_r = h2.get("mechanical_mean_r", 0.0) or 0.0
    mech_drop = h1_mech_r - h2_mech_r

    # SYSTEM_DECAY flags
    system_widening = (h1_gap_pp - h2_gap_pp) >= 10 or (h1_gap_r - h2_gap_r) >= 0.30
    gap_reversed = h1_gap_pp > 0 and h2_gap_pp < -5
    system_decay = system_widening or gap_reversed

    # REGIME_DECAY flag
    regime_decay = mech_drop >= 0.20 and abs(gap_delta_pp) <= 5

    if system_decay:
        diagnosis = "SYSTEM_DECAY"
        reasoning = (
            f"AI-vs-mechanical gap eroded H1->H2 (WR pp gap: {h1_gap_pp:+.1f} -> "
            f"{h2_gap_pp:+.1f}; delta {gap_delta_pp:+.1f}pp). "
            f"Mechanical mean R: {h1_mech_r:+.3f} -> {h2_mech_r:+.3f}. "
            "AI lost selectivity that the market continues to reward."
        )
    elif regime_decay:
        diagnosis = "REGIME_DECAY"
        reasoning = (
            f"Mechanical mean R dropped {mech_drop:+.3f}R H1->H2 ({h1_mech_r:+.3f} "
            f"-> {h2_mech_r:+.3f}) while AI-vs-mechanical gap stayed stable "
            f"(delta {gap_delta_pp:+.1f}pp). Market regime supports OB-zone "
            "trades less than it did; both arms collapsed together."
        )
    else:
        diagnosis = "MIXED"
        reasoning = (
            f"Neither pure system nor pure regime decay. "
            f"H1 gap {h1_gap_pp:+.1f}pp / {h1_gap_r:+.3f}R, "
            f"H2 gap {h2_gap_pp:+.1f}pp / {h2_gap_r:+.3f}R. "
            f"Mechanical drift {mech_drop:+.3f}R."
        )

    return {
        "diagnosis": diagnosis,
        "reasoning": reasoning,
        "h1_gap_wr_pp": round(h1_gap_pp, 2),
        "h2_gap_wr_pp": round(h2_gap_pp, 2),
        "gap_delta_pp": gap_delta_pp,
        "gap_stddev_pp": gap_stddev_pp,
        "h1_mechanical_mean_r": round(h1_mech_r, 4),
        "h2_mechanical_mean_r": round(h2_mech_r, 4),
    }


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def write_results_jsonl(rows: Sequence[ReplayRow], path: Path) -> None:
    """Write per-CAND results.jsonl. One JSON object per line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(asdict(r), default=str) + "\n")


def write_summary_json(summary: Mapping[str, Any], path: Path) -> None:
    """Write summary.json (per-cell + halves + verdict)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)


def write_report_md(
    rows: Sequence[ReplayRow], summary: Mapping[str, Any], path: Path
) -> None:
    """Write a human-readable report.md.

    Sections:
      1. Headline: total rows, per-instrument coverage, matched pairs.
      2. Per-month per-instrument table.
      3. H1 vs H2 cross-comparison.
      4. Strategic verdict block (the format the brief specifies).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    lines.append("# A1 — Full Historical Dumb-Baseline Replay")
    lines.append("")
    lines.append(
        f"Harness version: `{summary.get('harness_version', HARNESS_VERSION)}` — "
        "mechanical 80%-retrace OB-pullback baseline. No AI calls; pure OHLCV replay."
    )
    lines.append("")
    lines.append("## Coverage")
    lines.append("")
    lines.append("| Symbol | CANDs replayed | Mechanical fired | Matched (AI+mech R) |")
    lines.append("|---|---:|---:|---:|")
    coverage = summary.get("per_instrument_coverage", {})
    for sym in sorted(coverage):
        c = coverage[sym]
        lines.append(
            f"| {sym} | {c['n_cand_replayed']} | "
            f"{c['n_mechanical_fired']} | {c['n_matched_pairs']} |"
        )
    lines.append("")

    # Per-month per-instrument
    lines.append("## Per-month per-instrument")
    lines.append("")
    lines.append(
        "| Month | Symbol | CAND n | AI n | AI mean R | AI WR | "
        "Mech n | Mech mean R | Mech WR | Matched | Gap (AI-Mech) R |"
    )
    lines.append(
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    )
    for cell in summary.get("per_cell", []):
        lines.append(
            f"| {cell['period_month']} | {cell['symbol']} | "
            f"{cell['n_cand']} | {cell['ai_n']} | "
            f"{_fmt_r(cell['ai_mean_r'])} | {_fmt_pct(cell['ai_wr'])} | "
            f"{cell['mechanical_n']} | {_fmt_r(cell['mechanical_mean_r'])} | "
            f"{_fmt_pct(cell['mechanical_wr'])} | {cell['matched_pairs']} | "
            f"{_fmt_r(cell['matched_gap_mean_r'])} |"
        )
    lines.append("")

    # H1 / H2
    halves = summary.get("halves", {})
    h1 = halves.get("H1", {})
    h2 = halves.get("H2", {})
    lines.append("## H1 vs H2 — matched-pair comparison")
    lines.append("")
    lines.append("| Half | n | AI mean R | AI WR | Mech mean R | Mech WR | Gap (AI-Mech) R | Gap WR pp |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for label, h in (("H1", h1), ("H2", h2)):
        lines.append(
            f"| {label} | {h.get('n', 0)} | "
            f"{_fmt_r(h.get('ai_mean_r'))} | {_fmt_pct(h.get('ai_wr'))} | "
            f"{_fmt_r(h.get('mechanical_mean_r'))} | {_fmt_pct(h.get('mechanical_wr'))} | "
            f"{_fmt_r(h.get('gap_mean_r'))} | {_fmt_pp(h.get('gap_wr_pp'))} |"
        )
    lines.append("")

    # Strategic verdict block — exact format the brief specifies
    verdict = summary.get("verdict", {})
    lines.append("## Strategic verdict")
    lines.append("")
    lines.append(
        f"- AI vs mechanical gap H1-2026: {_fmt_pp(verdict.get('h1_gap_wr_pp'))}"
    )
    lines.append(
        f"- AI vs mechanical gap H2-2026: {_fmt_pp(verdict.get('h2_gap_wr_pp'))}"
    )
    lines.append(
        f"- Gap delta H1→H2: {_fmt_pp(verdict.get('gap_delta_pp'))}"
    )
    lines.append(
        f"- Gap stability across months: {_fmt_pp(verdict.get('gap_stddev_pp'))}"
        " (stddev)"
    )
    lines.append("")
    lines.append(f"Diagnosis: {verdict.get('diagnosis', 'INCONCLUSIVE')}")
    lines.append(f"Reasoning: {verdict.get('reasoning', '')}")
    lines.append("")

    # Caveats footer
    lines.append("## Caveats")
    lines.append("")
    lines.append(
        "* This replay tests only the OB-pullback canonical rule. Multi-framework "
        "  comparisons (`fvg_fill`, `breaker_re_entry`) are out of scope."
    )
    lines.append(
        "* The mechanical arm uses the AI's recorded `direction` so we test the "
        "  same setup the AI looked at — we do NOT also opine on whether mechanical "
        "  picks a different side."
    )
    lines.append(
        "* Realized AI R is joined per L56/L58 contract `(symbol, candle_close_time, "
        "  side)`. CANDs without a recorded R are excluded from the pair-aggregates."
    )
    lines.append(
        "* `INCONCLUSIVE` verdict at low n is a research-discipline guard — do NOT "
        "  treat it as a recommendation either way."
    )
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def _fmt_r(v: Any) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):+.3f}"
    except (TypeError, ValueError):
        return "—"


def _fmt_pct(v: Any) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v) * 100:.1f}%"
    except (TypeError, ValueError):
        return "—"


def _fmt_pp(v: Any) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):+.2f}pp"
    except (TypeError, ValueError):
        return "—"


# ===========================================================================
# Batch-session source (alternative to trade_records)
# ===========================================================================
#
# Trade records in ``knowledge_base/trade_records/`` capture full MSO at
# decision time but do NOT carry realized R (outcome enrichment is a
# separate, async batch process; April 2026 trade records have outcome=None).
#
# Batch sessions in ``knowledge_base_backtest/sessions/{SYMBOL}/`` capture
# AI decisions per candle (with ``candle_time`` + ``trade_id``) and realized
# R via ``trade_summary.trades`` joined by ``trade_id``. They do NOT carry
# MSO snapshots, so the mechanical arm must re-derive the OB target from
# raw OHLCV. We re-use the A6 baseline approach: detect H1 BOS events on
# the OHLCV up to the candle, infer the impulse leg, and apply the same
# 80%-retrace pullback rule.
#
# This source is what gives us realized AI R for 2026-Q1 across 6
# instruments — the population A1 needs for the H1 vs H2 comparison.
#
# Symbol normalization: batch session filenames look like
# ``2026-01-05_session.json``; the symbol comes from the parent directory
# name (e.g. ``XAUUSD/``). The session JSON has ``"symbol": null`` in
# this dataset version, so the parent dir is authoritative.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _BatchCandidate:
    """One CAND extracted from a batch session JSON.

    We deliberately keep this struct minimal — only the fields we need
    to drive the mechanical replay + AI-R join.
    """

    cand_id: str
    symbol: str
    candle_close_time: dt.datetime
    side: Optional[str]
    framework: str
    kill_zone: str
    trade_id: Optional[str]
    ai_realized_r: Optional[float]
    ai_outcome: Optional[str]


def _iter_batch_sessions(
    sessions_root: Path, instruments: Optional[Sequence[str]] = None
) -> Iterator[Tuple[str, Path, Mapping[str, Any]]]:
    """Yield ``(symbol, path, session_dict)`` per batch session JSON.

    Layout: ``sessions_root/{SYMBOL}/<date>_session.json``. The symbol
    comes from the parent-dir name (the ``symbol`` field is often
    ``None`` in the captured JSON).
    """
    if not sessions_root.exists():
        return
    inst_filter: Optional[set] = None
    if instruments:
        inst_filter = {_canonical_symbol(i).upper() for i in instruments}
    for inst_dir in sorted(sessions_root.iterdir()):
        if not inst_dir.is_dir():
            continue
        if inst_filter is not None:
            if (_canonical_symbol(inst_dir.name).upper() not in inst_filter
                    and inst_dir.name.upper() not in inst_filter):
                continue
        for path in sorted(inst_dir.glob("*.json")):
            if path.stem.startswith("_"):
                continue
            try:
                with path.open("r", encoding="utf-8") as fh:
                    session = json.load(fh)
            except Exception as exc:
                logger.warning("Skipping unreadable batch session %s: %s",
                               path, exc)
                continue
            yield inst_dir.name, path, session


def _extract_batch_candidates(
    symbol: str, path: Path, session: Mapping[str, Any]
) -> List[_BatchCandidate]:
    """Extract CANDs from a batch session and join their realized R.

    Returns one :class:`_BatchCandidate` per CANDIDATE with a ``trade_id``.
    CANDs without a trade_id (decision flagged but execution skipped) are
    dropped — we cannot join them.
    """
    ce = session.get("candle_evaluations") or []
    ts = session.get("trade_summary") or {}
    if not isinstance(ts, Mapping):
        return []
    trades = ts.get("trades") or []
    trade_by_id: Dict[str, Mapping[str, Any]] = {}
    for t in trades:
        if isinstance(t, Mapping) and t.get("trade_id"):
            trade_by_id[t["trade_id"]] = t

    out: List[_BatchCandidate] = []
    canonical = _canonical_symbol(symbol)
    for c in ce:
        if not isinstance(c, Mapping):
            continue
        if c.get("decision") != "CANDIDATE":
            continue
        trade_id = c.get("trade_id")
        if not trade_id:
            continue
        candle_close_time = _normalize_to_utc_minute(c.get("candle_time"))
        if candle_close_time is None:
            continue
        framework = str(c.get("framework") or "")
        kz = str(c.get("kill_zone") or "")
        side = c.get("direction") or None
        if side:
            side = str(side).upper()
        # Realized R from the joined trade
        trade = trade_by_id.get(trade_id) or {}
        r_raw = trade.get("r_multiple")
        try:
            ai_r = float(r_raw) if r_raw is not None else None
        except (TypeError, ValueError):
            ai_r = None
        out.append(_BatchCandidate(
            cand_id=_make_cand_id(canonical, candle_close_time),
            symbol=canonical,
            candle_close_time=candle_close_time,
            side=side,
            framework=framework,
            kill_zone=kz,
            trade_id=trade_id,
            ai_realized_r=ai_r,
            ai_outcome=trade.get("outcome"),
        ))
    return out


# ---------------------------------------------------------------------------
# OHLCV-derived swing + BOS detection (mirrors A6 baseline_simulator)
# ---------------------------------------------------------------------------


def _detect_swings_ohlcv(
    bars: Sequence[Mapping[str, Any]], min_bars: int = 2
) -> List[Dict[str, Any]]:
    """Detect swing highs / lows on a bar list. Mirrors A6 ``detect_swings``.

    A swing high at index i requires ``bars[i].high`` strictly greater
    than ``min_bars`` candles either side. Mirror for swing lows. Same
    semantics as ``src.components.dumb_baseline_shadow_logger._detect_swings``.
    """
    swings: List[Dict[str, Any]] = []
    n = len(bars)
    for i in range(min_bars, n - min_bars):
        try:
            high_i = float(bars[i]["high"])
            low_i = float(bars[i]["low"])
        except (KeyError, TypeError, ValueError):
            continue
        is_high = all(
            high_i > float(bars[i - j]["high"]) and high_i > float(bars[i + j]["high"])
            for j in range(1, min_bars + 1)
        )
        if is_high:
            swings.append({
                "index": i, "type": "high",
                "price": high_i,
                "time": bars[i].get("time"),
            })
        is_low = all(
            low_i < float(bars[i - j]["low"]) and low_i < float(bars[i + j]["low"])
            for j in range(1, min_bars + 1)
        )
        if is_low:
            swings.append({
                "index": i, "type": "low",
                "price": low_i,
                "time": bars[i].get("time"),
            })
    return sorted(swings, key=lambda s: s["index"])


def _detect_bos_events_ohlcv(
    bars: Sequence[Mapping[str, Any]]
) -> List[Dict[str, Any]]:
    """Detect every H1 BOS event on a bar series (both directions).

    Mirrors A6 ``detect_all_bos_events``. Each broken swing fires once.
    Returns events with ``direction``, ``candle_index``, ``time``,
    ``close_price``, ``causing_swing_index``, ``causing_swing_price``.
    """
    swings = _detect_swings_ohlcv(bars, min_bars=2)
    events: List[Dict[str, Any]] = []
    broken_high: set = set()
    broken_low: set = set()
    for i, bar in enumerate(bars):
        try:
            close = float(bar["close"])
        except (KeyError, TypeError, ValueError):
            continue
        # Bullish BOS (most recent swing high strictly before i)
        recent_high = None
        for s in swings:
            if s["index"] >= i:
                break
            if s["type"] == "high":
                recent_high = s
        if (recent_high is not None
                and recent_high["price"] not in broken_high
                and close > recent_high["price"]):
            broken_high.add(recent_high["price"])
            events.append({
                "direction": "bullish",
                "candle_index": i,
                "time": bar.get("time"),
                "close_price": close,
                "causing_swing_index": recent_high["index"],
                "causing_swing_price": recent_high["price"],
            })
        # Bearish BOS
        recent_low = None
        for s in swings:
            if s["index"] >= i:
                break
            if s["type"] == "low":
                recent_low = s
        if (recent_low is not None
                and recent_low["price"] not in broken_low
                and close < recent_low["price"]):
            broken_low.add(recent_low["price"])
            events.append({
                "direction": "bearish",
                "candle_index": i,
                "time": bar.get("time"),
                "close_price": close,
                "causing_swing_index": recent_low["index"],
                "causing_swing_price": recent_low["price"],
            })
    return events


def _impulse_leg_ohlcv(
    event: Mapping[str, Any], bars: Sequence[Mapping[str, Any]]
) -> Tuple[float, float]:
    """Return (impulse_low, impulse_high) for a BOS event on OHLCV.

    Mirrors A6 ``impulse_leg``: scan the bars from causing_swing_index to
    BOS index and return (lowest low, highest high).
    """
    bos_idx = event["candle_index"]
    swing_idx = event["causing_swing_index"]
    if (swing_idx is None
            or swing_idx >= bos_idx
            or swing_idx < 0):
        try:
            return (float(bars[bos_idx]["low"]), float(bars[bos_idx]["high"]))
        except (KeyError, TypeError, ValueError):
            return (0.0, 0.0)
    leg = bars[swing_idx:bos_idx + 1]
    try:
        lo = min(float(b["low"]) for b in leg)
        hi = max(float(b["high"]) for b in leg)
    except (KeyError, TypeError, ValueError):
        return (0.0, 0.0)
    return (lo, hi)


def _h1_bars_up_to(
    h1_bars: Sequence[Mapping[str, Any]], cutoff: dt.datetime
) -> List[Mapping[str, Any]]:
    """Return H1 bars whose ``time <= cutoff`` (inclusive).

    H1 bars open on the hour; the cutoff is the M15 candle close, so
    we want every H1 that completed at or before the M15 close.
    """
    out: List[Mapping[str, Any]] = []
    for b in h1_bars:
        bt = b["time"] if isinstance(b["time"], dt.datetime) else _normalize_to_utc_minute(b["time"])
        if bt is None:
            continue
        if bt <= cutoff:
            out.append(b)
        else:
            break
    return out


def _h1_atr14(h1_bars: Sequence[Mapping[str, Any]]) -> Optional[float]:
    """Compute Wilder's ATR(14) on the *trailing* 14 H1 bars.

    Returns ``None`` if fewer than 15 bars available.
    """
    if len(h1_bars) < 15:
        return None
    trs: List[float] = []
    for i in range(len(h1_bars) - 14, len(h1_bars)):
        if i == 0:
            continue
        try:
            h = float(h1_bars[i]["high"])
            lo = float(h1_bars[i]["low"])
            prev_c = float(h1_bars[i - 1]["close"])
        except (KeyError, TypeError, ValueError):
            continue
        trs.append(max(h - lo, abs(h - prev_c), abs(lo - prev_c)))
    if not trs:
        return None
    atr = sum(trs[:14]) / min(len(trs), 14)
    for tr in trs[14:]:
        atr = (atr * 13 + tr) / 14
    return atr


def compute_mechanical_entry_from_ohlcv(
    *,
    symbol: str,
    candle_close_time: dt.datetime,
    side: str,
    h1_bars: Sequence[Mapping[str, Any]],
    cfg: Optional[BaselineConfig] = None,
    cand_id: Optional[str] = None,
    framework: str = "ob_retest",
) -> MechanicalSetup:
    """OHLCV-derived mechanical setup (used when no MSO snapshot exists).

    Detects the most-recent H1 BOS event up to ``candle_close_time``
    matching the requested side, reconstructs its impulse leg, and
    applies the same 80%-retrace pullback rule as
    :func:`compute_mechanical_entry`.

    "OB target" here is the impulse leg itself: for a bullish BOS, the
    impulse low is the protective edge and the BOS close is the
    "high" of the impulse. The mechanical 80% retrace is therefore
    ``impulse_low + 0.80 * (impulse_high - impulse_low)`` — the same
    formula compute_mechanical_entry uses but with impulse_high/low
    standing in for OB.high/low. This is intentional: the academic
    edge is "stop-cascade mean-reversion to pre-cascade equilibrium",
    and the impulse leg is that equilibrium-zone proxy.

    Caveats vs MSO-driven path
    --------------------------
    * No "mitigated" filter — we re-emit the BOS regardless of whether
      it has been touched. The original A6 simulator did the same.
    * The TP target is the rr_floor fallback; we do not search for
      opposing swings here (A6 didn't either).
    """
    if cfg is None:
        cfg = BaselineConfig()
    if cand_id is None:
        cand_id = _make_cand_id(symbol, candle_close_time)

    side_norm = (side or "").strip().upper()
    if side_norm not in {"LONG", "SHORT"}:
        return _empty_setup(cand_id, symbol, candle_close_time, side_norm,
                            framework, "INVALID_SIDE")

    if framework not in ("ob_retest", "", None):
        return _empty_setup(cand_id, symbol, candle_close_time, side_norm,
                            framework, "UNSUPPORTED_FRAMEWORK")

    bars_up_to = _h1_bars_up_to(h1_bars, candle_close_time)
    if not bars_up_to:
        return _empty_setup(cand_id, symbol, candle_close_time, side_norm,
                            framework, "NO_H1_BARS")

    events = _detect_bos_events_ohlcv(bars_up_to)
    target_dir = "bullish" if side_norm == "LONG" else "bearish"
    same_side = [e for e in events if e["direction"] == target_dir]
    if not same_side:
        return _empty_setup(cand_id, symbol, candle_close_time, side_norm,
                            framework, "NO_BOS")

    event = max(same_side, key=lambda e: e["candle_index"])
    impulse_low, impulse_high = _impulse_leg_ohlcv(event, bars_up_to)
    if impulse_high <= impulse_low:
        return _empty_setup(cand_id, symbol, candle_close_time, side_norm,
                            framework, "DEGENERATE_IMPULSE")

    if side_norm == "LONG":
        entry = impulse_low + cfg.retrace_pct * (impulse_high - impulse_low)
    else:
        entry = impulse_high - cfg.retrace_pct * (impulse_high - impulse_low)

    h1_atr = _h1_atr14(bars_up_to)
    tick = _tick_size(symbol)
    atr_buf = (cfg.sl_buffer_atr_multiplier * h1_atr) if h1_atr and h1_atr > 0 else 0.0
    tick_buf = cfg.sl_buffer_min_ticks * tick
    buffer = max(atr_buf, tick_buf)
    if buffer <= 0:
        return _empty_setup(cand_id, symbol, candle_close_time, side_norm,
                            framework, "BAD_SL_BUFFER")

    if side_norm == "LONG":
        sl = impulse_low - buffer
    else:
        sl = impulse_high + buffer

    sl_dist = abs(entry - sl)
    if sl_dist <= 0:
        return _empty_setup(cand_id, symbol, candle_close_time, side_norm,
                            framework, "DEGENERATE_SL")

    # rr_floor TP (A6 didn't search for swing TPs)
    if side_norm == "LONG":
        tp = entry + cfg.min_rr * sl_dist
    else:
        tp = entry - cfg.min_rr * sl_dist

    return MechanicalSetup(
        cand_id=cand_id,
        symbol=_canonical_symbol(symbol),
        candle_close_time=candle_close_time,
        side=side_norm,
        framework=framework or "ob_retest",
        ob_high=impulse_high,
        ob_low=impulse_low,
        ob_formation_time=str(event.get("time")),
        ob_mitigated=False,  # OHLCV path does not track mitigation
        ob_source_tf="H1_OHLCV",  # marker so report can distinguish
        entry=round(entry, 6),
        sl=round(sl, 6),
        tp=round(tp, 6),
        rr=cfg.min_rr,
        sl_buffer_used=round(buffer, 6),
        h1_atr=h1_atr,
        tick_size=tick,
        selection_reason="BOS_OHLCV",
        tp_source="rr_floor",
        skip_reason=None,
    )


# ---------------------------------------------------------------------------
# OHLCV H1 loader (mirrors _load_ohlcv but reads ``{SYMBOL}_H1.csv``)
# ---------------------------------------------------------------------------


def _load_h1_ohlcv(symbol: str, ohlcv_dir: Path) -> List[Dict[str, Any]]:
    """Load the H1 OHLCV CSV for ``symbol``. Cached per process.

    Returns sorted list of bar dicts; empty list if file missing.
    """
    cache_key = f"H1|{_canonical_symbol(symbol)}|{ohlcv_dir}"
    if cache_key in _OHLCV_CACHE:
        return _OHLCV_CACHE[cache_key]
    canonical = _canonical_symbol(symbol)
    stem = OHLCV_STEM.get(canonical) or OHLCV_STEM.get(canonical.upper(), canonical)
    p = ohlcv_dir / f"{stem}_H1.csv"
    if not p.exists():
        _OHLCV_CACHE[cache_key] = []
        return []
    rows: List[Dict[str, Any]] = []
    try:
        with p.open("r", encoding="utf-8") as fh:
            header = fh.readline().strip().split(",")
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) < 5:
                    continue
                rec = dict(zip(header, parts))
                ts = _normalize_to_utc_minute(rec.get("time"))
                if ts is None:
                    continue
                try:
                    rows.append({
                        "time": ts,
                        "open": float(rec["open"]),
                        "high": float(rec["high"]),
                        "low": float(rec["low"]),
                        "close": float(rec["close"]),
                    })
                except (KeyError, TypeError, ValueError):
                    continue
    except OSError as exc:
        logger.warning("Cannot read %s: %s", p, exc)
        _OHLCV_CACHE[cache_key] = []
        return []
    rows.sort(key=lambda r: r["time"])
    _OHLCV_CACHE[cache_key] = rows
    return rows


# ---------------------------------------------------------------------------
# Batch session orchestrator
# ---------------------------------------------------------------------------


@dataclass
class BatchSessionReplay:
    """Replay over batch sessions (alternative to trade_records).

    Used when we need realized AI R (which trade records don't carry).
    The mechanical arm here is OHLCV-derived (no MSO available).
    """

    sessions_root: Path
    ohlcv_dir: Path = DEFAULT_OHLCV_DIR
    cfg: BaselineConfig = field(default_factory=BaselineConfig)
    instruments: Optional[Sequence[str]] = None
    since: Optional[dt.datetime] = None
    until: Optional[dt.datetime] = None

    def _direction_for_cand(
        self,
        cand: _BatchCandidate,
        h1_bars: Sequence[Mapping[str, Any]],
    ) -> Optional[str]:
        """Resolve the side for the mechanical arm.

        Batch session CANDs don't always carry ``direction``. As a
        fallback, infer from the most-recent H1 BOS direction up to
        the candle (bullish BOS → LONG, bearish → SHORT). This matches
        A6's baseline approach.
        """
        if cand.side in {"LONG", "SHORT"}:
            return cand.side
        bars_up_to = _h1_bars_up_to(h1_bars, cand.candle_close_time)
        if not bars_up_to:
            return None
        events = _detect_bos_events_ohlcv(bars_up_to)
        if not events:
            return None
        latest = max(events, key=lambda e: e["candle_index"])
        return "LONG" if latest["direction"] == "bullish" else "SHORT"

    def run_one(self, cand: _BatchCandidate) -> Optional[ReplayRow]:
        """Replay one batch CAND. Returns None if filtered out."""
        if self.since is not None and cand.candle_close_time < self.since:
            return None
        if self.until is not None and cand.candle_close_time > self.until:
            return None

        h1 = _load_h1_ohlcv(cand.symbol, self.ohlcv_dir)
        side = self._direction_for_cand(cand, h1)
        skip_reason: Optional[str] = None
        setup: Optional[MechanicalSetup] = None
        outcome: Optional[MechanicalOutcome] = None

        if not side:
            skip_reason = "NO_AI_SIDE"
        else:
            if not h1:
                skip_reason = "NO_H1_OHLCV"
            else:
                setup = compute_mechanical_entry_from_ohlcv(
                    symbol=cand.symbol,
                    candle_close_time=cand.candle_close_time,
                    side=side,
                    h1_bars=h1,
                    cfg=self.cfg,
                    cand_id=cand.cand_id,
                    framework=cand.framework or "ob_retest",
                )
                if setup.skip_reason is not None:
                    skip_reason = setup.skip_reason
                else:
                    outcome = resolve_mechanical_outcome(
                        setup, self.ohlcv_dir,
                        max_hold_bars=self.cfg.max_hold_bars,
                    )
                    if outcome.skip_reason is not None and outcome.outcome != "TIMEOUT":
                        skip_reason = outcome.skip_reason

        period_month = cand.candle_close_time.strftime("%Y-%m")
        mech_realized = outcome.realized_r if outcome is not None else None
        mech_outcome_str = outcome.outcome if outcome is not None else None
        mech_bars = outcome.bars_in_trade if outcome is not None else None

        gap: Optional[float] = None
        if cand.ai_realized_r is not None and mech_realized is not None:
            gap = round(float(cand.ai_realized_r) - float(mech_realized), 4)

        return ReplayRow(
            cand_id=cand.cand_id,
            symbol=cand.symbol,
            candle_close_time=cand.candle_close_time.isoformat(),
            period_month=period_month,
            side=side,
            framework=cand.framework or "ob_retest",
            kill_zone=cand.kill_zone,
            ai_decision="CANDIDATE",
            ai_realized_r=cand.ai_realized_r,
            ai_outcome_resolved=cand.ai_realized_r is not None,
            mechanical_skip_reason=skip_reason,
            mechanical_entry=setup.entry if (setup and setup.skip_reason is None) else None,
            mechanical_sl=setup.sl if (setup and setup.skip_reason is None) else None,
            mechanical_tp=setup.tp if (setup and setup.skip_reason is None) else None,
            mechanical_rr=setup.rr if (setup and setup.skip_reason is None) else None,
            mechanical_outcome=mech_outcome_str,
            mechanical_realized_r=mech_realized,
            mechanical_bars_in_trade=mech_bars,
            mechanical_fired=(setup is not None and setup.skip_reason is None),
            realized_r_gap=gap,
        )

    def run(self) -> List[ReplayRow]:
        rows: List[ReplayRow] = []
        for symbol, path, session in _iter_batch_sessions(
            self.sessions_root, self.instruments
        ):
            try:
                cands = _extract_batch_candidates(symbol, path, session)
            except Exception as exc:  # noqa: BLE001 — never propagate
                logger.warning("Failed to extract from %s: %s", path, exc)
                continue
            for cand in cands:
                try:
                    row = self.run_one(cand)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed to replay batch CAND %s: %s",
                                   cand.cand_id, exc, exc_info=True)
                    continue
                if row is not None:
                    rows.append(row)
        return rows


def _count_batch_records(replay: "BatchSessionReplay") -> int:
    """Count batch CANDs that match the filter (used for --dry-run)."""
    n = 0
    for symbol, path, session in _iter_batch_sessions(
        replay.sessions_root, replay.instruments
    ):
        try:
            cands = _extract_batch_candidates(symbol, path, session)
        except Exception:
            continue
        for cand in cands:
            if replay.since is not None and cand.candle_close_time < replay.since:
                continue
            if replay.until is not None and cand.candle_close_time > replay.until:
                continue
            n += 1
    return n


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "BaselineConfig",
    "BatchSessionReplay",
    "DumbBaselineReplay",
    "HARNESS_VERSION",
    "MechanicalOutcome",
    "MechanicalSetup",
    "ReplayRow",
    "RETRACE_PCT",
    "TICK_SIZE",
    "aggregate",
    "compute_mechanical_entry",
    "compute_mechanical_entry_from_ohlcv",
    "resolve_mechanical_outcome",
    "write_report_md",
    "write_results_jsonl",
    "write_summary_json",
]
