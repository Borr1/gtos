"""Dumb-momentum-baseline shadow logger — observation-only.

Per A6's `research/dumb_momentum_baseline/REPORT.md`:

A6 found that the AI is NOT adding per-trade selectivity in the same-window
Jan 2 - Apr 13 2026 backtest comparison: dumb-baseline (mechanical 80%-retrace
pullback rule) Exp +0.36R vs F3-AI Exp +0.35R, n=11/13. The same-window
sample size is too small to claim definitively.

A6's recommendation: ship a $0 dumb-baseline live shadow log alongside live
trades for empirical comparison after 50-100 live trades. This module is that
shadow logger.

What this logger does
---------------------
On every M15 candle close (orchestrator hook, KZ-only), this logger:

1. Recomputes H1 BOS events from the cached MSO (re-using `detect_swings` /
   the same per-symbol H1 candle window the orchestrator already ingested).
2. Picks the *most recent* H1 BOS still inside a configurable look-back
   horizon (default 24 H1 candles).
3. Computes the impulse leg (most-recent opposite swing -> BOS candle close)
   and the corresponding 80%-retrace target.
4. If the latest M15 close has retraced >= the target, computes hypothetical
   entry/SL (1x M15-ATR(14) beyond entry)/TP (1.5R) and logs a "ENTER"
   record to ``shadow_logs/dumb_baseline_hypotheticals.jsonl``.

Outcome resolution
------------------
After a hypothetical "ENTER" is logged, the next 48 M15 candles are watched
for SL or TP touch. On every candle close after the entry, walk forward
through any hypothetical that has not yet resolved:

* If candle high >= TP for LONG (or low <= TP for SHORT) -> outcome=TP, R=+1.5
* If candle low <= SL for LONG (or high >= SL for SHORT) -> outcome=SL, R=-1.0
* If 48 M15 candles have elapsed without TP/SL -> outcome=TIMEOUT, R=0.0
  (computed from the 48th-bar close)

Open hypotheticals are kept in memory + persisted to disk every 5 candles
for crash-recovery. Outcomes are written by REPLAYING the JSONL with a
record-by-record rewrite (matches `proximity_shadow_logger.update_outcome`).

Strict contract
---------------
- This module never places a trade. Never affects orchestrator decisions.
- Hypotheticals do NOT count toward `kz_trades`, `concurrent_tracker`, or
  any production cap.
- Every public entry point is wrapped so failures can never propagate into
  the trading pipeline.
- A "max 1 fire / instrument / day" gate prevents runaway logging.

Storage
-------
- JSONL: ``shadow_logs/dumb_baseline_hypotheticals.jsonl`` (one line per
  hypothetical; same line is rewritten with outcome on resolution).
- State: ``shadow_logs/.dumb_baseline_state.json`` (per-symbol open
  hypotheticals + last fire date for the daily gate).

Companion analysis: ``scripts/dumb_baseline_compare.py``.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Module-level constants — tests override via module-ref monkeypatch
# (per MEMORY.md `project_pytest_contamination_forensics`).
SHADOW_LOG_PATH = Path("shadow_logs/dumb_baseline_hypotheticals.jsonl")
STATE_PATH = Path("shadow_logs/.dumb_baseline_state.json")
DEBUG_LOG_PATH = Path("shadow_logs/dumb_baseline_debug.jsonl")

# Constants matching A6 baseline_simulator.py
ATR_PERIOD = 14
MIN_RR = 1.5  # GTOS default
RETRACE_PCT = 0.80  # A6 canonical 80% retrace variant
LOOK_BACK_H1_CANDLES = 24  # only consider BOS events within last 24h
OUTCOME_TIMEOUT_M15_BARS = 48  # 12 hours

# Persist open-hypothetical state every N processed candles (crash recovery).
PERSIST_INTERVAL = 5


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass
class _Swing:
    index: int
    type: str  # "high" or "low"
    price: float
    time: str


@dataclass
class _BOSEvent:
    direction: str  # "bullish" or "bearish"
    candle_index: int
    time: str
    close_price: float
    causing_swing_index: int
    causing_swing_price: float


@dataclass
class _Hypothetical:
    """A live, in-memory hypothetical trade.

    Fields mirror the JSONL schema. Outcome fields default to None until the
    trade resolves (TP/SL/TIMEOUT).
    """
    hypothesis_id: str
    timestamp_utc: str
    candle_time: str
    symbol: str
    kz: str
    direction: str  # LONG or SHORT
    bos_direction: str  # bullish or bearish
    bos_h1_time: str
    entry: float
    sl: float
    tp: float
    atr_m15: float
    impulse_low: float
    impulse_high: float
    impulse_range: float
    retrace_pct: float
    bars_elapsed: int = 0
    outcome: Optional[str] = None  # TP / SL / TIMEOUT / None
    realized_r: Optional[float] = None
    time_in_trade_bars: Optional[int] = None
    exit_time: Optional[str] = None


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------


def _state_path_for(symbol: str, base: Path | None = None) -> Path:
    """Return per-symbol state file path.

    Each orchestrator owns its own state file (one per symbol) to avoid the
    multi-process write race observed 2026-04-29 — 4+ orchestrators racing
    on the shared ``.dumb_baseline_state.json`` with ``os.replace`` failing
    on Windows when another process held the file. Per-symbol files also
    eliminate the underlying read-modify-write data-loss race (orch A reads
    {A:x, B:y}, orch B reads same, both modify+write; second overwrites
    first's modification even when the rename succeeds).
    """
    target_base = base if base is not None else STATE_PATH
    return target_base.parent / f"{target_base.stem}.{symbol}.json"


def _load_state(symbol: str, path: Path | None = None) -> dict:
    """Return persisted per-symbol state, or {} on any read failure.

    Returns the symbol's state dict directly (no longer wrapped in the
    ``{symbol: sym_state}`` shape of the legacy combined-file format).

    Migration: if the per-symbol file does not exist AND ``path`` is the
    default (production), fall back to reading the legacy combined file at
    ``STATE_PATH`` and extracting ``legacy[symbol]``. After first save the
    per-symbol file is authoritative; the legacy file becomes dead state
    that an operator can remove.
    """
    target = path if path is not None else _state_path_for(symbol)
    try:
        if target.exists():
            data = json.loads(target.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    # Legacy fallback — only when caller relied on the default path.
    if path is None:
        try:
            if STATE_PATH.exists():
                legacy = json.loads(STATE_PATH.read_text(encoding="utf-8"))
                if isinstance(legacy, dict):
                    sub = legacy.get(symbol)
                    if isinstance(sub, dict):
                        return sub
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            pass
    return {}


def _save_state(symbol: str, sym_state: dict, path: Path | None = None) -> None:
    """Atomically replace the per-symbol state file.

    Failures are logged, never raise. Per-PID temp filename keeps writers
    isolated even when the same process spawns multiple writers concurrently.
    """
    target = path if path is not None else _state_path_for(symbol)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(
            json.dumps(sym_state, indent=2, sort_keys=True), encoding="utf-8"
        )
        os.replace(tmp, target)
    except OSError as exc:
        logger.warning(
            "dumb_baseline: state save failed for %s (%s)", symbol, exc
        )


def _append_jsonl(record: dict, path: Path) -> None:
    """Append a single JSON object as one line. Failures are logged, never raise."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError as exc:
        logger.warning("dumb_baseline: log write failed (%s)", exc)


# ---------------------------------------------------------------------------
# Defensive raw-data accessors
# ---------------------------------------------------------------------------


def _get_candles(raw_data: Any, tf_name: str) -> list[dict]:
    """Extract ``raw_data["candles"][tf_name]`` defensively. Returns [] on any miss."""
    try:
        if not isinstance(raw_data, dict):
            return []
        candles_dict = raw_data.get("candles") or {}
        if not isinstance(candles_dict, dict):
            return []
        candles = candles_dict.get(tf_name) or []
        if not isinstance(candles, list):
            return []
        return candles
    except Exception:  # noqa: BLE001 — never propagate
        return []


# ---------------------------------------------------------------------------
# Pure math helpers (mirror A6 baseline_simulator.py exactly)
# ---------------------------------------------------------------------------


def _detect_swings(candles: list[dict], min_bars: int = 2) -> list[_Swing]:
    """Detect swing highs/lows on a candle list. Mirrors `market_state.detect_swings`.

    A swing high at index i requires candles[i].high to be strictly greater
    than the highs of `min_bars` candles on each side. Mirror for swing lows.
    """
    swings: list[_Swing] = []
    n = len(candles)
    for i in range(min_bars, n - min_bars):
        try:
            is_swing_high = all(
                candles[i]["high"] > candles[i - j]["high"]
                and candles[i]["high"] > candles[i + j]["high"]
                for j in range(1, min_bars + 1)
            )
            if is_swing_high:
                swings.append(_Swing(
                    index=i, type="high",
                    price=float(candles[i]["high"]),
                    time=str(candles[i].get("time", "")),
                ))
            is_swing_low = all(
                candles[i]["low"] < candles[i - j]["low"]
                and candles[i]["low"] < candles[i + j]["low"]
                for j in range(1, min_bars + 1)
            )
            if is_swing_low:
                swings.append(_Swing(
                    index=i, type="low",
                    price=float(candles[i]["low"]),
                    time=str(candles[i].get("time", "")),
                ))
        except (KeyError, TypeError, ValueError):
            continue
    return sorted(swings, key=lambda s: s.index)


def _detect_bos_events(h1_candles: list[dict]) -> list[_BOSEvent]:
    """Detect every H1 BOS event (both directions) on the H1 series.

    Mirrors A6 `baseline_simulator.detect_all_bos_events` — BOTH directions
    fire (no production-style direction gate). Each broken swing fires once.
    """
    swings = _detect_swings(h1_candles, min_bars=2)
    swings_sorted = sorted(swings, key=lambda s: s.index)

    events: list[_BOSEvent] = []
    broken_high_levels: set[float] = set()
    broken_low_levels: set[float] = set()

    for i, c in enumerate(h1_candles):
        try:
            close = float(c["close"])
        except (KeyError, TypeError, ValueError):
            continue

        # Bullish BOS: most recent swing high strictly before i
        recent_high = None
        for s in swings_sorted:
            if s.index >= i:
                break
            if s.type == "high":
                recent_high = s
        if (recent_high
                and recent_high.price not in broken_high_levels
                and close > recent_high.price):
            broken_high_levels.add(recent_high.price)
            events.append(_BOSEvent(
                direction="bullish",
                candle_index=i,
                time=str(c.get("time", "")),
                close_price=close,
                causing_swing_index=recent_high.index,
                causing_swing_price=recent_high.price,
            ))

        # Bearish BOS
        recent_low = None
        for s in swings_sorted:
            if s.index >= i:
                break
            if s.type == "low":
                recent_low = s
        if (recent_low
                and recent_low.price not in broken_low_levels
                and close < recent_low.price):
            broken_low_levels.add(recent_low.price)
            events.append(_BOSEvent(
                direction="bearish",
                candle_index=i,
                time=str(c.get("time", "")),
                close_price=close,
                causing_swing_index=recent_low.index,
                causing_swing_price=recent_low.price,
            ))

    return events


def _impulse_leg(event: _BOSEvent, h1_candles: list[dict]) -> tuple[float, float]:
    """Return (impulse_low, impulse_high) for the BOS event. Mirrors A6 `impulse_leg`.

    For a bullish BOS, the impulse leg is from the most-recent swing low
    (origin of the up-leg) up to the BOS-candle close. We use the actual
    lowest low and highest high between those two indices to be robust to
    wicks. For a bearish BOS, mirror.
    """
    bos_idx = event.candle_index
    swing_idx = event.causing_swing_index
    if swing_idx is None or swing_idx >= bos_idx or swing_idx < 0:
        c = h1_candles[bos_idx]
        try:
            return (float(c["low"]), float(c["high"]))
        except (KeyError, TypeError, ValueError):
            return (0.0, 0.0)
    leg = h1_candles[swing_idx:bos_idx + 1]
    try:
        lo = min(float(c["low"]) for c in leg)
        hi = max(float(c["high"]) for c in leg)
    except (KeyError, TypeError, ValueError):
        return (0.0, 0.0)
    return (lo, hi)


def _m15_atr(m15_candles: list[dict], up_to_idx: int, period: int = ATR_PERIOD) -> Optional[float]:
    """Compute Wilder's ATR(period) on M15 candles up to (but not including) up_to_idx.

    Mirrors A6 `m15_atr` (recursive smoothing matches market_state.compute_session_atr).
    Returns None if fewer than period+1 candles available.
    """
    if up_to_idx < period + 1:
        return None
    trs: list[float] = []
    start = max(0, up_to_idx - period * 4)
    for i in range(start, up_to_idx):
        if i == 0:
            continue
        try:
            h = float(m15_candles[i]["high"])
            lo = float(m15_candles[i]["low"])
            prev_c = float(m15_candles[i - 1]["close"])
        except (KeyError, TypeError, ValueError):
            continue
        trs.append(max(h - lo, abs(h - prev_c), abs(lo - prev_c)))
    if len(trs) < period:
        return None
    atr = sum(trs[:period]) / period
    for tr in trs[period:]:
        atr = (atr * (period - 1) + tr) / period
    return atr


# ---------------------------------------------------------------------------
# State / Hypothetical helpers
# ---------------------------------------------------------------------------


def _utc_date(iso_timestamp: str | None) -> str:
    """UTC date (YYYY-MM-DD) for an ISO timestamp, or today's UTC date.

    Accepts both naive and tz-aware ISO strings. Anything unparseable falls
    back to the process's current UTC date.
    """
    if iso_timestamp:
        try:
            ts = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return ts.astimezone(timezone.utc).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _hypothetical_to_record(h: _Hypothetical) -> dict:
    """Serialize Hypothetical -> JSONL record dict."""
    return asdict(h)


def _record_to_hypothetical(record: dict) -> Optional[_Hypothetical]:
    """Inverse of `_hypothetical_to_record`. Returns None on schema mismatch."""
    try:
        return _Hypothetical(**{
            k: record.get(k)
            for k in _Hypothetical.__dataclass_fields__.keys()
        })
    except (TypeError, ValueError):
        return None


def _make_hypothesis_id(symbol: str, candle_time: str) -> str:
    """Stable id from (symbol, candle_time). One hypothetical per (symbol, candle)."""
    safe = "".join(c if c.isalnum() else "_" for c in candle_time)
    return f"{symbol}_dumb_{safe}"


# ---------------------------------------------------------------------------
# JSONL outcome rewrite
# ---------------------------------------------------------------------------


def _update_outcome_in_jsonl(
    hypothesis_id: str,
    outcome: str,
    realized_r: float,
    time_in_trade_bars: int,
    exit_time: str,
    log_path: Path | None = None,
) -> bool:
    """Replay JSONL, rewrite the matching `hypothesis_id` row with outcome fields.

    Returns True if a row was updated, False otherwise. Failures are logged,
    never raised. Mirrors `proximity_shadow_logger.update_proximity_outcome`.
    """
    target = log_path if log_path is not None else SHADOW_LOG_PATH
    try:
        if not target.exists():
            return False
        lines = target.read_text(encoding="utf-8").strip().split("\n")
        new_lines: list[str] = []
        updated = False
        for line in lines:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                # Don't drop unparseable lines — preserve raw.
                new_lines.append(line)
                continue
            if (
                rec.get("hypothesis_id") == hypothesis_id
                and rec.get("outcome") is None
            ):
                rec["outcome"] = outcome
                rec["realized_r"] = round(float(realized_r), 4)
                rec["time_in_trade_bars"] = int(time_in_trade_bars)
                rec["exit_time"] = exit_time
                updated = True
            new_lines.append(json.dumps(rec))
        if updated:
            target.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        return updated
    except OSError as exc:
        logger.warning("dumb_baseline: outcome rewrite failed (%s)", exc)
        return False


# ---------------------------------------------------------------------------
# Outcome scan against the latest M15 candle
# ---------------------------------------------------------------------------


def _resolve_outcomes(
    open_hypotheticals: list[_Hypothetical],
    latest_m15_candle: dict,
    log_path: Path | None = None,
) -> tuple[list[_Hypothetical], list[_Hypothetical]]:
    """Walk the latest M15 candle against every open hypothetical.

    Returns (still_open, just_resolved). Increments `bars_elapsed` for every
    open hypothetical regardless of resolution. Resolved hypotheticals are
    rewritten in the JSONL.

    Resolution rules
    ----------------
    For LONG:
        if candle.high >= TP -> outcome=TP, R=+MIN_RR
        if candle.low  <= SL -> outcome=SL, R=-1.0
    For SHORT:
        if candle.low  <= TP -> outcome=TP, R=+MIN_RR
        if candle.high >= SL -> outcome=SL, R=-1.0
    Both can fire on the same candle — we use the SL-first rule (conservative,
    matches A6 baseline_simulator default which checks SL before TP per leg).

    On the OUTCOME_TIMEOUT_M15_BARS-th candle without TP/SL, outcome=TIMEOUT,
    R is computed from the close of that candle.
    """
    try:
        c_high = float(latest_m15_candle.get("high"))
        c_low = float(latest_m15_candle.get("low"))
        c_close = float(latest_m15_candle.get("close"))
        c_time = str(latest_m15_candle.get("time", ""))
    except (TypeError, ValueError):
        # Bad candle — bump bars_elapsed only; can't resolve.
        for h in open_hypotheticals:
            h.bars_elapsed += 1
        return open_hypotheticals, []

    still_open: list[_Hypothetical] = []
    just_resolved: list[_Hypothetical] = []

    for h in open_hypotheticals:
        h.bars_elapsed += 1

        # Compute outcome candidates for this candle.
        outcome: Optional[str] = None
        realized_r: Optional[float] = None

        sl_dist = abs(h.entry - h.sl)
        if sl_dist <= 0:
            # Degenerate — drop without rewrite (data corruption).
            logger.warning(
                "dumb_baseline: degenerate hypothetical %s (sl_dist=0); dropping",
                h.hypothesis_id,
            )
            continue

        if h.direction == "LONG":
            sl_hit = c_low <= h.sl
            tp_hit = c_high >= h.tp
        else:
            sl_hit = c_high >= h.sl
            tp_hit = c_low <= h.tp

        # SL-first conservative rule (matches A6 `build_trade_from_bos`).
        if sl_hit:
            outcome = "SL"
            realized_r = -1.0
        elif tp_hit:
            outcome = "TP"
            realized_r = round(MIN_RR, 4)
        elif h.bars_elapsed >= OUTCOME_TIMEOUT_M15_BARS:
            outcome = "TIMEOUT"
            # R = (close_price - entry) / sl_dist, signed by direction
            if h.direction == "LONG":
                realized_r = round((c_close - h.entry) / sl_dist, 4)
            else:
                realized_r = round((h.entry - c_close) / sl_dist, 4)

        if outcome is not None:
            h.outcome = outcome
            h.realized_r = realized_r
            h.time_in_trade_bars = h.bars_elapsed
            h.exit_time = c_time
            _update_outcome_in_jsonl(
                hypothesis_id=h.hypothesis_id,
                outcome=outcome,
                realized_r=float(realized_r),
                time_in_trade_bars=h.bars_elapsed,
                exit_time=c_time,
                log_path=log_path,
            )
            just_resolved.append(h)
            logger.info(
                "DUMB_BASELINE_OUTCOME: %s %s %s realized_r=%+.3f bars=%d",
                h.hypothesis_id, h.direction, outcome, realized_r, h.bars_elapsed,
            )
        else:
            still_open.append(h)

    return still_open, just_resolved


# ---------------------------------------------------------------------------
# Decision: should we fire a new hypothetical right now?
# ---------------------------------------------------------------------------


def _build_hypothetical_if_eligible(
    h1_candles: list[dict],
    m15_candles: list[dict],
    symbol: str,
    kz: str,
    candle_time_utc: str,
    look_back_h1: int = LOOK_BACK_H1_CANDLES,
) -> tuple[Optional[_Hypothetical], Optional[str]]:
    """Try to construct a hypothetical from current data.

    Returns (hypothetical, debug_reason). On success, hypothetical is
    populated; debug_reason is the success tag. On failure hypothetical is
    None and debug_reason explains why (NO_BOS / NO_RETRACE / etc.).

    Decision flow
    -------------
    1. Detect all H1 BOS events on the recent H1 window.
    2. Filter to events whose candle_index is within `look_back_h1` of the
       latest H1 candle.
    3. Pick the LATEST such event (most recent BOS dominates).
    4. Reconstruct impulse leg, compute 80%-retrace target.
    5. If latest M15 close has retraced past the target -> ENTER.
       Else -> NO_RETRACE.
    6. Compute SL = 1x ATR(M15,14) beyond entry, TP = 1.5R.
    7. Reject if SL/TP fully degenerate (impulse_range==0, ATR<=0, etc.).
    """
    if not h1_candles or not m15_candles:
        return None, "NO_DATA"

    bos_events = _detect_bos_events(h1_candles)
    if not bos_events:
        return None, "NO_BOS"

    latest_h1_idx = len(h1_candles) - 1
    recent = [
        e for e in bos_events
        if (latest_h1_idx - e.candle_index) <= look_back_h1
    ]
    if not recent:
        return None, "NO_RECENT_BOS"

    # Pick the most recent BOS — last in candle_index order.
    event = max(recent, key=lambda e: e.candle_index)

    impulse_low, impulse_high = _impulse_leg(event, h1_candles)
    impulse_range = impulse_high - impulse_low
    if impulse_range <= 0:
        return None, "DEGENERATE_IMPULSE"

    direction = "LONG" if event.direction == "bullish" else "SHORT"

    if direction == "LONG":
        entry_target = impulse_high - RETRACE_PCT * impulse_range
    else:
        entry_target = impulse_low + RETRACE_PCT * impulse_range

    # Latest M15 close is the candidate entry trigger.
    last_m15 = m15_candles[-1]
    try:
        close = float(last_m15["close"])
    except (KeyError, TypeError, ValueError):
        return None, "BAD_M15_CLOSE"

    if direction == "LONG":
        if close > entry_target:
            return None, "NO_RETRACE"
        if close < impulse_low:
            return None, "FULL_RETRACE"  # past impulse origin -> trend invalidated
    else:
        if close < entry_target:
            return None, "NO_RETRACE"
        if close > impulse_high:
            return None, "FULL_RETRACE"

    atr = _m15_atr(m15_candles, len(m15_candles), period=ATR_PERIOD)
    if atr is None or atr <= 0:
        return None, "BAD_ATR"

    if direction == "LONG":
        sl = close - atr
        tp = close + MIN_RR * atr
    else:
        sl = close + atr
        tp = close - MIN_RR * atr

    # Reject if the candle itself already breached the SL (matches A6).
    try:
        c_high = float(last_m15["high"])
        c_low = float(last_m15["low"])
    except (KeyError, TypeError, ValueError):
        return None, "BAD_M15_OHLC"

    if direction == "LONG" and c_low <= sl:
        return None, "SL_BREACHED_ENTRY"
    if direction == "SHORT" and c_high >= sl:
        return None, "SL_BREACHED_ENTRY"

    candle_time = str(last_m15.get("time") or candle_time_utc)
    h = _Hypothetical(
        hypothesis_id=_make_hypothesis_id(symbol, candle_time),
        timestamp_utc=candle_time_utc,
        candle_time=candle_time,
        symbol=symbol,
        kz=kz,
        direction=direction,
        bos_direction=event.direction,
        bos_h1_time=event.time,
        entry=round(close, 5),
        sl=round(sl, 5),
        tp=round(tp, 5),
        atr_m15=round(atr, 5),
        impulse_low=round(impulse_low, 5),
        impulse_high=round(impulse_high, 5),
        impulse_range=round(impulse_range, 5),
        retrace_pct=RETRACE_PCT,
    )
    return h, "ENTER"


# ---------------------------------------------------------------------------
# Public entry point — called once per M15 candle close
# ---------------------------------------------------------------------------


def process_candle(
    symbol: str,
    raw_data: Any,
    kz: str,
    *,
    timestamp_utc: Optional[str] = None,
    log_path: Path | None = None,
    debug_log_path: Path | None = None,
    state_path: Path | None = None,
    enable_debug: bool = False,
    look_back_h1: int = LOOK_BACK_H1_CANDLES,
) -> dict:
    """Top-level orchestrator hook. Pure observation; never gates trades.

    Parameters
    ----------
    symbol:
        Instrument symbol (e.g. "XAUUSD").
    raw_data:
        Output of `ingest_live_data` — must have ``candles.H1`` + ``candles.M15``
        lists. Anything else is treated as missing data (fail-open).
    kz:
        Active kill zone name. Empty string is allowed but every fire is
        gated to "kz != ''" (we're called from `_process_candle` which is
        already KZ-only — defensive for offline use).
    timestamp_utc:
        Optional ISO timestamp override. Defaults to ``datetime.now(UTC).isoformat()``.
    log_path / debug_log_path / state_path:
        Test-only path overrides.
    enable_debug:
        When True, emit a NO_BOS/NO_RETRACE/etc. row to ``debug_log_path``
        (one per call). Default False to avoid log churn in production.
    look_back_h1:
        Look-back window in H1 candles for BOS events (default 24).

    Returns
    -------
    dict with keys: action ("ENTER"/"NO_FIRE"/"SKIP_OUT_OF_KZ"/etc.),
    open_count (current open hypotheticals after the call), reason (debug tag).

    Failure isolation
    -----------------
    Every internal exception is caught; the function returns
    ``{"action": "ERROR", "open_count": 0, "reason": "<exc-type>"}`` rather
    than raising into the orchestrator.
    """
    log_p = log_path if log_path is not None else SHADOW_LOG_PATH
    state_p = state_path if state_path is not None else _state_path_for(symbol)
    debug_p = debug_log_path if debug_log_path is not None else DEBUG_LOG_PATH

    ts = timestamp_utc or datetime.now(timezone.utc).isoformat()

    try:
        # Load this symbol's state directly. Per-symbol files (since 2026-04-29)
        # eliminate the multi-process write race that lost dumb_baseline writes
        # via Windows ``os.replace`` failures + read-modify-write contention.
        sym_state = _load_state(symbol, path=state_p)
        if not isinstance(sym_state, dict) or not sym_state:
            sym_state = {"open": [], "last_fire_date": "", "candles_since_persist": 0}

        open_records = sym_state.get("open") or []
        if not isinstance(open_records, list):
            open_records = []

        open_hyps: list[_Hypothetical] = []
        for r in open_records:
            if not isinstance(r, dict):
                continue
            h = _record_to_hypothetical(r)
            if h is not None and h.outcome is None:
                open_hyps.append(h)

        # Outcome resolution against latest M15 candle (whether or not in KZ —
        # active hypotheticals must keep advancing across KZ boundaries).
        m15 = _get_candles(raw_data, "M15")
        latest_m15 = m15[-1] if m15 else None

        if latest_m15 is not None and open_hyps:
            open_hyps, _resolved = _resolve_outcomes(
                open_hyps, latest_m15, log_path=log_p,
            )

        # Out-of-KZ short-circuit (after outcome resolution).
        if not kz:
            sym_state["open"] = [_hypothetical_to_record(h) for h in open_hyps]
            sym_state["candles_since_persist"] = int(sym_state.get("candles_since_persist", 0)) + 1
            if sym_state["candles_since_persist"] >= PERSIST_INTERVAL:
                sym_state["candles_since_persist"] = 0
            _save_state(symbol, sym_state, path=state_p)

            if enable_debug:
                _append_jsonl({
                    "timestamp": ts, "symbol": symbol, "kz": kz,
                    "action": "SKIP_OUT_OF_KZ", "open_count": len(open_hyps),
                }, debug_p)
            return {"action": "SKIP_OUT_OF_KZ", "open_count": len(open_hyps), "reason": "no_kz"}

        # Daily fire gate — at most ONE hypothetical per (symbol, UTC date).
        today = _utc_date(ts)
        last_fire = str(sym_state.get("last_fire_date", ""))
        already_fired_today = last_fire == today

        # H1 candles needed for the firing decision.
        h1 = _get_candles(raw_data, "H1")
        if not h1 or not m15:
            if enable_debug:
                _append_jsonl({
                    "timestamp": ts, "symbol": symbol, "kz": kz,
                    "action": "SKIP_NO_DATA", "open_count": len(open_hyps),
                }, debug_p)
            sym_state["open"] = [_hypothetical_to_record(h) for h in open_hyps]
            _save_state(symbol, sym_state, path=state_p)
            return {"action": "SKIP_NO_DATA", "open_count": len(open_hyps), "reason": "no_candles"}

        if already_fired_today:
            sym_state["open"] = [_hypothetical_to_record(h) for h in open_hyps]
            sym_state["candles_since_persist"] = int(sym_state.get("candles_since_persist", 0)) + 1
            if sym_state["candles_since_persist"] >= PERSIST_INTERVAL:
                sym_state["candles_since_persist"] = 0
            _save_state(symbol, sym_state, path=state_p)
            if enable_debug:
                _append_jsonl({
                    "timestamp": ts, "symbol": symbol, "kz": kz,
                    "action": "SKIP_DAILY_GATE", "open_count": len(open_hyps),
                }, debug_p)
            return {
                "action": "SKIP_DAILY_GATE",
                "open_count": len(open_hyps),
                "reason": "already_fired_today",
            }

        # Try to build a hypothetical.
        hyp, reason = _build_hypothetical_if_eligible(
            h1_candles=h1,
            m15_candles=m15,
            symbol=symbol,
            kz=kz,
            candle_time_utc=ts,
            look_back_h1=look_back_h1,
        )

        if hyp is None:
            if enable_debug:
                _append_jsonl({
                    "timestamp": ts, "symbol": symbol, "kz": kz,
                    "action": "NO_FIRE", "reason": reason or "unknown",
                    "open_count": len(open_hyps),
                }, debug_p)
            sym_state["open"] = [_hypothetical_to_record(h) for h in open_hyps]
            sym_state["candles_since_persist"] = int(sym_state.get("candles_since_persist", 0)) + 1
            if sym_state["candles_since_persist"] >= PERSIST_INTERVAL:
                sym_state["candles_since_persist"] = 0
            _save_state(symbol, sym_state, path=state_p)
            return {"action": "NO_FIRE", "open_count": len(open_hyps), "reason": reason or "unknown"}

        # FIRE — append to JSONL and add to open list.
        _append_jsonl(_hypothetical_to_record(hyp), log_p)
        open_hyps.append(hyp)
        sym_state["last_fire_date"] = today
        sym_state["open"] = [_hypothetical_to_record(h) for h in open_hyps]
        sym_state["candles_since_persist"] = 0  # always persist on fire
        _save_state(symbol, sym_state, path=state_p)

        logger.info(
            "DUMB_BASELINE_FIRE: %s %s %s entry=%.5f sl=%.5f tp=%.5f atr=%.5f kz=%s",
            symbol, hyp.direction, hyp.bos_direction,
            hyp.entry, hyp.sl, hyp.tp, hyp.atr_m15, kz,
        )

        return {
            "action": "ENTER",
            "open_count": len(open_hyps),
            "reason": "fired",
            "hypothesis_id": hyp.hypothesis_id,
        }

    except Exception as exc:  # noqa: BLE001 — this logger MUST never raise
        logger.warning("dumb_baseline: unexpected failure (%s)", exc, exc_info=True)
        return {"action": "ERROR", "open_count": 0, "reason": type(exc).__name__}
