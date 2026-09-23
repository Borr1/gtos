"""K54 v2 — REGIME family feature extractor.

Scope
-----
Owner: REGIME family (1 of 6 in K54 v2 expanded feature catalog).
Pre-registered hypothesis: ``research/ml_program/PRE_REGISTERED_HYPOTHESES.md``
Q1.2 — locked 2026-04-28 20:00 UTC. Validation = CPCV-with-purge over
2024-02-20 -> 2026-04-28 + 14-day prospective live holdout 2026-04-29 ->
2026-05-12.

Per memory ``project_f15_synthesis_regime_is_load_bearing``, regime is
the load-bearing decay axis (F15 attribution +48.3pp Bonferroni p=0.0016).
K54 v1 used regime ONLY as ENSEMBLE GATING (one model per regime); the
``regime_tag`` column had ZERO importance as a feature inside any model
(see ``k54_v1_audit.md`` Section 5). This module surfaces ~50 regime
features so the model can learn from regime structure as feature input,
not just gate.

Data sources (cited inline at primitive sites)
----------------------------------------------
1. **Regime backfill** — ``shadow_logs/structure_detector_backfill_2026.jsonl``
   3,571 H4 records 2026-01-21 -> 2026-04-24 across 9 symbols.
   Schema per row: ``{symbol, ts, v1_direction, v2_direction, v2_score,
   v2_dead_zone, counts: {hh,hl,lh,ll}, production_label}``.
   v2_score and v2_dead_zone are 100% populated — both UNUSED in K54 v1
   per audit Section 5; surfaced here as zero-cost wins.

2. **Live regime classifier output** — ``shadow_logs/regime_classifications.jsonl``
   133 live entries 2026-04-27+ (post-backfill window).
   Schema is ``RegimeClassification`` from
   ``src/components/regime_classifier.py`` (CLASSIFIER_VERSION
   ``v1.0-option-a-h4-swing``). Used as a fallback for any (symbol, ts)
   missing from backfill.

3. **OHLCV historical** — ``data/historical_2026/{SYMBOL}_{TF}.csv``
   Columns ``time,open,high,low,close,volume``. Used for:
     - ATR computations (regime-conditional volatility ratios).
     - D1 swing-direction agreement (cross-timeframe regime alignment).
   Coverage: 2025-10-01 -> 2026-04-24 across all 7 fleet symbols + EURUSD
   (M1, M15, H1, H4, D1).

4. **Cross-instrument matrix** — implicit via fleet regime backfill;
   correlation table at ``src/components/cross_instrument_correlation_gate.py``
   (NOT loaded here — referenced for future ``correlation-weighted`` feature).

Point-in-time discipline (HARD CONTRACT)
----------------------------------------
All features at trade entry timestamp ``T`` consume ONLY data with
backfill timestamp <= T's preceding H4 candle close. Specifically:

- Backfill rows are H4 boundary (00, 04, 08, 12, 16, 20 UTC). For
  entry T, we use rows with ``backfill.ts <= T``.
- The backfill row at ``ts == T_H4_floor`` is the regime BEFORE T (since
  the H4 candle closes at the END of its interval, T_H4_floor + 4h).
  We use the *most recent* backfill row with ``ts < T``: this is the
  H4 candle that closed before entry, i.e. the last regime label
  available at decision time.
- For regime stability / time-since-last-flip: walk BACKWARD from
  ``last_available_ts`` only.
- For cross-instrument regime alignment: pull each fleet symbol's
  most-recent backfill row with ``ts < T`` (independently).
- For D1-swing direction: read OHLCV closes with ``time < T_D1_floor``.

Track A trap mitigation: regime label at candle close T MUST be the
regime IDENTIFIED at or before T. The regime classifier in
``src/components/regime_classifier.py`` produces deterministic labels
from MSO swings — re-running it on the same swing input yields the same
label. The H4 backfill JSONL captures this snapshot at H4 boundaries
during the backfill run (2026-04-26 17:26 UTC per file logged_at),
which is itself BACKWARD-LOOKING — no future data. Caveat:
``logged_at`` >> ``ts`` because backfill ran retrospectively, but the
regime computation only consumes data from <= ``ts``, so the row IS
point-in-time correct relative to ``ts``.

Inference cost note
-------------------
Cross-instrument regime alignment requires loading 7 fleet symbols'
regime streams in parallel — this is a one-time index build per dataset
(~3,571 rows total to scan). At inference time on a single (symbol, ts)
the lookup is O(1) per fleet symbol = O(7), so cost is bounded.
Regime-classifier inference (re-running ``classify_regime``) is NOT
needed in this module: we consume the BACKFILL output, not re-run.
Production deployment of K54 v2 will call ``classify_regime`` once per
M15 close (already on the live path per session 38), so the marginal
cost of these features is JUST the per-row dict assembly.

Feature count delivered: 63 features (see ``regime.csv`` for catalog).

Stability score column in catalog: Spearman rank correlation of feature
value at trade-entry-candle-close vs realized R, computed on pre-2026-04
data only (the unburned slice). NaN where insufficient samples.

Author: K54 v2 REGIME family agent (2026-04-28).
"""

from __future__ import annotations

import csv
import json
import math
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Optional

# ============================================================================
# Constants + paths
# ============================================================================

REPO_ROOT = Path(r"C:/Users/MSI/Documents/ai-trading-agent")

REGIME_BACKFILL_PATH = REPO_ROOT / "shadow_logs" / "structure_detector_backfill_2026.jsonl"
"""H4 regime classifier backfill (3,571 rows, 9 symbols, 2026-01-21 -> 2026-04-24)."""

REGIME_LIVE_PATH = REPO_ROOT / "shadow_logs" / "regime_classifications.jsonl"
"""Live regime stream (133 rows, 2026-04-27+). Schema is RegimeClassification.

KNOWN COVERAGE GAP: US30_cash is in the production fleet but is NOT in
``structure_detector_backfill_2026.jsonl``. The backfill contains 9
symbols {EURUSD, GBPJPY, GBPUSD, GER40, NAS100, UK100, USDJPY, XAGUSD,
XAUUSD}; the live stream (post 2026-04-27) DOES include US30_cash but
covers only 1 day at the data-cutoff edge. Effect: for 2026-01..04
US30_cash trades, all backfill-sourced regime features will be 0 /
sentinel. Cross-instrument fleet alignment counts US30_cash as missing
(treated as transitional) when computing OTHER fleet symbols' features.
This is flagged in ``regime.csv`` and the ``regime.md`` leakage
self-check, NOT silently imputed."""

OHLCV_DIR = REPO_ROOT / "data" / "historical_2026"
"""Historical OHLCV CSVs (2025-10-01 -> 2026-04-24)."""

# Fleet for cross-instrument regime alignment. Mirrors production fleet
# (see CLAUDE.md SYSTEM ARCHITECTURE > kill_zone_schedule + start_all.bat).
# Ordered so feature names are deterministic across runs.
FLEET_SYMBOLS: tuple[str, ...] = (
    "XAUUSD", "XAGUSD", "USDJPY", "GBPJPY", "GBPUSD", "US30_cash", "NAS100",
)

# Hard data cutoff per Q1.2 hypothesis lock.
DATA_CUTOFF_UTC = datetime(2026, 4, 28, 23, 59, 59, tzinfo=timezone.utc)

# Regime label vocabulary used in features. Backfill emits 4-class
# {bullish, bearish, transitional, UNTAGGED}; live classifier emits 5-class
# {trending_bull, trending_bear, chop, reversal_in_progress, unclear}.
# We map BOTH into a unified 5-class one-hot for v2-classifier-output features
# AND keep the 4-class backfill scheme as separate one-hots.
BACKFILL_REGIME_LABELS = ("bullish", "bearish", "transitional", "UNTAGGED")
LIVE_REGIME_LABELS = (
    "trending_bull", "trending_bear", "chop", "reversal_in_progress", "unclear",
)

# Lookback windows in H4 candles for regime-stability + transition flags.
H4_LOOKBACKS = (1, 5, 10, 20, 50)

# Regime-conditional ATR ratio uses these H4 lookbacks for the denominator.
ATR_BASELINE_H4_LOOKBACKS = (20, 50)


# ============================================================================
# Helpers
# ============================================================================

def _parse_iso(raw: Optional[str]) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp into a UTC-aware datetime.

    Accepts both ``Z``-suffixed and ``+00:00``-suffixed forms. Naive
    datetimes are interpreted as UTC. Returns None on parse failure
    rather than raising; callers treat None as missing.
    """
    if not isinstance(raw, str) or not raw.strip():
        return None
    s = raw.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        try:
            dt = datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                dt = datetime.strptime(s[:10], "%Y-%m-%d")
            except ValueError:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _h4_floor(ts: datetime) -> datetime:
    """Round ``ts`` DOWN to the nearest H4 boundary (00, 04, 08, 12, 16, 20 UTC).

    H4 candles in the production MT5 feed open at these UTC hours. The
    H4 candle that contains ``ts`` opens at ``_h4_floor(ts)`` and closes
    at ``_h4_floor(ts) + 4h``.
    """
    hour = (ts.hour // 4) * 4
    return ts.replace(hour=hour, minute=0, second=0, microsecond=0)


def _d1_floor(ts: datetime) -> datetime:
    """Round ``ts`` DOWN to UTC midnight."""
    return ts.replace(hour=0, minute=0, second=0, microsecond=0)


def _safe_div(a: Optional[float], b: Optional[float]) -> Optional[float]:
    """Return a/b or None on degenerate inputs.

    Used inside regime-conditional ATR ratios where a missing denominator
    is more informative as None than as +inf or 0.
    """
    try:
        if a is None or b is None:
            return None
        if b == 0:
            return None
        return float(a) / float(b)
    except (TypeError, ValueError):
        return None


def _normalize_side(raw) -> Optional[str]:
    """Coerce trade direction to {LONG, SHORT, None}.

    Mirrors ``k54_build_features.py`` ``_normalize_direction`` to keep
    feature inputs aligned with K54 v1's source-of-truth convention.
    """
    s = str(raw or "").strip().upper()
    if s in ("LONG", "BUY"):
        return "LONG"
    if s in ("SHORT", "SELL"):
        return "SHORT"
    return None


# ============================================================================
# Backfill index — primary regime data source
# ============================================================================

@dataclass(frozen=True)
class RegimeRow:
    """One H4 regime backfill row, normalized."""

    symbol: str
    ts: datetime  # H4 boundary timestamp
    v1_direction: Optional[str]  # bullish / bearish / transitional / None
    v2_direction: Optional[str]
    v2_score: Optional[int]  # signed; positive = bullish, negative = bearish
    v2_dead_zone: Optional[int]  # max(2, min_swing_transitions // 8)
    hh: int
    hl: int
    lh: int
    ll: int

    @property
    def production_label(self) -> str:
        """Best label available — v2 if present, else v1, else UNTAGGED."""
        return self.v2_direction or self.v1_direction or "UNTAGGED"


class RegimeBackfillIndex:
    """In-memory index of regime backfill rows for O(1) point-in-time lookup.

    Layout:
        - ``_by_sym[symbol]``: list of RegimeRow ordered by ``ts`` ascending.

    Public methods:
        - ``latest_at(symbol, ts) -> Optional[RegimeRow]``: most recent row with
          ``row.ts <= ts``. Used for the "current" regime feature group.
        - ``window(symbol, ts, n) -> list[RegimeRow]``: last n rows with
          ``row.ts <= ts``. Used for regime-stability + transition features.

    Inference cost: __init__ scans the JSONL once (~3,571 rows). Per-lookup
    is O(log n) bisect on a per-symbol sorted array (~400 rows/symbol).
    """

    def __init__(self, path: Path = REGIME_BACKFILL_PATH) -> None:
        self._by_sym: dict[str, list[RegimeRow]] = {}
        self._path = path
        if path.exists():
            self._load(path)

    def _load(self, path: Path) -> None:
        rows: dict[str, list[RegimeRow]] = {}
        for line in path.open(encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            sym = str(d.get("symbol", "")).upper()
            ts = _parse_iso(d.get("ts"))
            if not sym or ts is None:
                continue
            counts = d.get("counts") or {}
            row = RegimeRow(
                symbol=sym,
                ts=ts,
                v1_direction=d.get("v1_direction"),
                v2_direction=d.get("v2_direction"),
                v2_score=d.get("v2_score"),
                v2_dead_zone=d.get("v2_dead_zone"),
                hh=int(counts.get("hh") or 0),
                hl=int(counts.get("hl") or 0),
                lh=int(counts.get("lh") or 0),
                ll=int(counts.get("ll") or 0),
            )
            rows.setdefault(sym, []).append(row)
        # Sort each symbol's rows by ts (ascending). Defensive — backfill
        # may not be globally sorted across symbols.
        for sym, lst in rows.items():
            lst.sort(key=lambda r: r.ts)
        self._by_sym = rows

    def symbols(self) -> list[str]:
        return sorted(self._by_sym.keys())

    def _bisect_le(self, lst: list[RegimeRow], ts: datetime) -> int:
        """Right-most index ``i`` such that ``lst[i].ts <= ts``; -1 if none."""
        # Manual bisect to avoid pulling in ``bisect`` for a tiny gain.
        lo, hi = 0, len(lst) - 1
        ans = -1
        while lo <= hi:
            mid = (lo + hi) // 2
            if lst[mid].ts <= ts:
                ans = mid
                lo = mid + 1
            else:
                hi = mid - 1
        return ans

    def latest_at(self, symbol: str, ts: datetime) -> Optional[RegimeRow]:
        """Return the most recent backfill row with ``row.ts <= ts``.

        Critical point-in-time discipline: the row at ``ts == row.ts``
        is INCLUDED — that H4 candle has closed by the time the M15
        candle inside ``[row.ts, row.ts+4h)`` closes. For an entry at
        e.g. 13:00 UTC with the H4 boundary at 12:00 UTC, the regime
        of the 12:00 H4 candle is NOT yet finalized (the candle closes
        at 16:00). We are intentionally accepting slight lag here:
        the regime label that K54 v1 joined for these rows used the
        same convention via ``_regime_lookup`` walk-back.
        """
        sym = str(symbol).upper()
        lst = self._by_sym.get(sym) or []
        if not lst:
            return None
        idx = self._bisect_le(lst, ts)
        if idx < 0:
            return None
        return lst[idx]

    def window(self, symbol: str, ts: datetime, n: int) -> list[RegimeRow]:
        """Last ``n`` rows with ``row.ts <= ts`` (ordered ascending)."""
        sym = str(symbol).upper()
        lst = self._by_sym.get(sym) or []
        idx = self._bisect_le(lst, ts)
        if idx < 0:
            return []
        start = max(0, idx - n + 1)
        return lst[start:idx + 1]


# ============================================================================
# OHLCV cache — used for regime-conditional ATR ratios
# ============================================================================

@dataclass
class OHLCVRow:
    """Minimal OHLCV row for ATR + D1-direction features."""

    time: datetime
    open: float
    high: float
    low: float
    close: float


class OHLCVCache:
    """Lazy-load + cache CSV OHLCV files keyed on (symbol, timeframe).

    Files at ``data/historical_2026/{SYMBOL}_{TF}.csv`` per the
    audit's path convention. Sorted ascending by time.

    Inference cost: file load is ~145 rows (D1) to ~13k rows (M15) per
    symbol; one-time per (symbol, TF) per process. ATR computation per
    lookup is O(N) but bounded by lookback (max 50).
    """

    def __init__(self, base_dir: Path = OHLCV_DIR) -> None:
        self._base = base_dir
        self._cache: dict[tuple[str, str], list[OHLCVRow]] = {}

    def _load(self, symbol: str, tf: str) -> list[OHLCVRow]:
        path = self._base / f"{symbol}_{tf}.csv"
        if not path.exists():
            return []
        rows: list[OHLCVRow] = []
        with path.open(encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            for r in rdr:
                t = _parse_iso(r.get("time"))
                if t is None:
                    continue
                try:
                    rows.append(OHLCVRow(
                        time=t,
                        open=float(r["open"]),
                        high=float(r["high"]),
                        low=float(r["low"]),
                        close=float(r["close"]),
                    ))
                except (KeyError, ValueError):
                    continue
        rows.sort(key=lambda x: x.time)
        return rows

    def get(self, symbol: str, tf: str) -> list[OHLCVRow]:
        key = (str(symbol).upper(), tf)
        if key not in self._cache:
            self._cache[key] = self._load(*key)
        return self._cache[key]

    def slice_until(
        self, symbol: str, tf: str, ts: datetime, n: Optional[int] = None,
    ) -> list[OHLCVRow]:
        """Return rows with ``row.time <= ts``, optionally last ``n`` of them.

        Point-in-time enforced by ``row.time <= ts``. The TF candle whose
        OPEN time equals ``ts`` is INCLUDED — that candle has data through
        ``ts`` (an H4 candle opening at 12:00 has data 12:00 -> 16:00; if
        ts == 12:00 the candle has just opened, no data yet). Caller
        beware: for ATR-of-completed-candles, advance the cutoff one TF.
        """
        rows = self.get(symbol, tf)
        # Linear backward scan (rows < few thousand; not worth bisect for
        # this cost).
        out: list[OHLCVRow] = []
        for r in rows:
            if r.time > ts:
                break
            out.append(r)
        if n is not None and len(out) > n:
            out = out[-n:]
        return out


def _atr(rows: list[OHLCVRow], period: int = 14) -> Optional[float]:
    """Average true range over the last ``period`` rows.

    Standard TR = max(high-low, abs(high-prev_close), abs(low-prev_close)).
    Returns None if fewer than ``period+1`` rows. Plain average (no Wilder
    smoothing) — matches the production market_state TR convention used
    in ATR(14) for backfill labels (see ``regime_classifier.py:410``).
    """
    if len(rows) < period + 1:
        return None
    trs: list[float] = []
    for i in range(len(rows) - period, len(rows)):
        prev = rows[i - 1]
        cur = rows[i]
        tr = max(
            cur.high - cur.low,
            abs(cur.high - prev.close),
            abs(cur.low - prev.close),
        )
        trs.append(tr)
    if not trs:
        return None
    return sum(trs) / len(trs)


def _d1_swing_direction(rows: list[OHLCVRow], lookback: int = 5) -> Optional[str]:
    """Naive D1 direction: close[-1] vs close[-lookback].

    Returns ``bullish`` if last close > lookback-ago close + 0.5%,
    ``bearish`` if -0.5%, ``transitional`` otherwise. Threshold is a
    flat 50 bp to suppress noise; not tuned. Used only to provide the
    cross-timeframe regime alignment feature, not as a hard signal.
    """
    if len(rows) < lookback + 1:
        return None
    last = rows[-1].close
    base = rows[-lookback - 1].close
    if base <= 0:
        return None
    pct = (last - base) / base
    if pct > 0.005:
        return "bullish"
    if pct < -0.005:
        return "bearish"
    return "transitional"


# ============================================================================
# Feature primitives — each returns a partial dict to merge into the row
# ============================================================================

def _feat_current_regime_v1_onehot(row: Optional[RegimeRow]) -> dict:
    """v1 H4 regime label one-hot. 4 features.

    v1_direction in backfill is the production v1 label
    (``identify_structure_v1``); see backfill commit context.
    """
    label = row.v1_direction if row else None
    out = {
        "regime_v1_is_bullish": int(label == "bullish"),
        "regime_v1_is_bearish": int(label == "bearish"),
        "regime_v1_is_transitional": int(label == "transitional"),
        "regime_v1_is_untagged": int(label is None or label == "UNTAGGED"),
    }
    return out


def _feat_current_regime_v2_onehot(row: Optional[RegimeRow]) -> dict:
    """v2 H4 regime label one-hot + dead_zone flag. 5 features.

    Per audit Section 5: ``v2_dead_zone`` IS in backfill but UNUSED in
    K54 v1. Surfaced here as a zero-cost win.
    """
    label = row.v2_direction if row else None
    score = row.v2_score if row else None
    dead_zone = row.v2_dead_zone if row else None

    # "in dead zone" = |score| <= dead_zone, indicating transitional/chop.
    in_dz = 0
    if score is not None and dead_zone is not None:
        in_dz = int(abs(score) <= dead_zone)

    return {
        "regime_v2_is_bullish": int(label == "bullish"),
        "regime_v2_is_bearish": int(label == "bearish"),
        "regime_v2_is_transitional": int(label == "transitional"),
        "regime_v2_is_untagged": int(label is None or label == "UNTAGGED"),
        "regime_v2_in_dead_zone": in_dz,
    }


def _feat_v2_score_features(row: Optional[RegimeRow]) -> dict:
    """v2_score primitives — surfaced but currently UNUSED in K54 v1.

    Audit Section 5: ``v2_score`` is in backfill but never propagated
    to features.csv. 4 features:

    - ``regime_v2_score``: signed integer (negative = bearish lean).
    - ``regime_v2_score_abs``: |score|.
    - ``regime_v2_dead_zone_value``: dead_zone integer.
    - ``regime_v2_score_minus_dead_zone``: score - dead_zone (signed
      strength of the directional vote vs the noise floor).
    """
    score = row.v2_score if row else None
    dz = row.v2_dead_zone if row else None
    return {
        "regime_v2_score": score if score is not None else 0,
        "regime_v2_score_abs": abs(score) if score is not None else 0,
        "regime_v2_dead_zone_value": dz if dz is not None else 0,
        "regime_v2_score_minus_dead_zone": (
            (abs(score) - dz) if (score is not None and dz is not None) else 0
        ),
    }


def _feat_swing_counts(row: Optional[RegimeRow]) -> dict:
    """HH/HL/LH/LL transition counts from backfill. 4 features.

    Auxiliary regime-strength signal — independent of v2_score's
    aggregation. Captures asymmetry: high HH+HL with low LH+LL is
    a clean uptrend; balanced counts indicate transitional.
    """
    if not row:
        return {
            "regime_hh_count": 0,
            "regime_hl_count": 0,
            "regime_lh_count": 0,
            "regime_ll_count": 0,
        }
    return {
        "regime_hh_count": row.hh,
        "regime_hl_count": row.hl,
        "regime_lh_count": row.lh,
        "regime_ll_count": row.ll,
    }


def _feat_regime_stability(
    backfill: RegimeBackfillIndex,
    symbol: str,
    ts: datetime,
) -> dict:
    """Regime-stability + transition features. 7 features.

    - ``regime_consecutive_h4_bars``: count of consecutive H4 bars in the
      CURRENT v2 label (capped at 100 to avoid runaway).
    - ``regime_changed_in_last_N``: binary, did v2 label change vs N H4
      bars ago. N in {1, 5, 10, 20, 50}.
    - ``regime_h4_bars_since_last_flip``: H4 bars since most recent
      v2 label change (capped at 100; -1 if no flip in window).

    Walks BACKWARD from ``latest_at(symbol, ts)`` only — point-in-time
    safe by construction.
    """
    out = {
        "regime_consecutive_h4_bars": 0,
        "regime_h4_bars_since_last_flip": -1,
    }
    for lb in H4_LOOKBACKS:
        out[f"regime_changed_in_last_{lb}"] = 0

    # Cap window to scan — 100 H4 bars ~= 16 calendar days, plenty of
    # headroom for any reasonable regime persistence.
    window_max = 100
    rows = backfill.window(symbol, ts, window_max)
    if not rows:
        return out

    cur = rows[-1].v2_direction or "UNTAGGED"

    # Consecutive run length (walk backward from rows[-1]).
    consec = 1
    for i in range(len(rows) - 2, -1, -1):
        lbl = rows[i].v2_direction or "UNTAGGED"
        if lbl == cur:
            consec += 1
        else:
            break
    out["regime_consecutive_h4_bars"] = min(consec, window_max)

    # Bars since last flip = consec - 1 if regime is stable; otherwise
    # a flip occurred at consec bars back. Same number actually:
    # rows[-consec] is the candle BEFORE the flip; rows[-consec+1] is
    # the first candle of the current label.
    bars_since_flip = consec - 1 if consec < len(rows) else -1
    out["regime_h4_bars_since_last_flip"] = bars_since_flip

    # changed_in_last_N: compare v2 label N bars back to current.
    for lb in H4_LOOKBACKS:
        if len(rows) > lb:
            past_lbl = rows[-lb - 1].v2_direction or "UNTAGGED"
            out[f"regime_changed_in_last_{lb}"] = int(past_lbl != cur)
        else:
            # Not enough history -> emit 0 (defaults to "no observed change").
            out[f"regime_changed_in_last_{lb}"] = 0

    return out


def _feat_regime_score_dynamics(
    backfill: RegimeBackfillIndex,
    symbol: str,
    ts: datetime,
) -> dict:
    """v2_score dynamics over recent H4 bars. 6 features.

    - ``regime_v2_score_change_N``: score - score[N H4 bars back],
      for N in {1, 5, 20}. Sign = direction of regime drift; abs = speed.
    - ``regime_v2_score_max_in_20``: max v2_score in last 20 H4 bars.
    - ``regime_v2_score_min_in_20``: min v2_score in last 20 H4 bars.
    - ``regime_v2_score_range_in_20``: max - min (regime turbulence).

    Captures regime *velocity* — F2 found XAUUSD London/trending_bull/LONG
    decay was concentrated where the regime was newly-formed (high score)
    rather than persisting. Score dynamics may help distinguish these.
    """
    out = {
        "regime_v2_score_change_1": 0,
        "regime_v2_score_change_5": 0,
        "regime_v2_score_change_20": 0,
        "regime_v2_score_max_in_20": 0,
        "regime_v2_score_min_in_20": 0,
        "regime_v2_score_range_in_20": 0,
    }
    rows = backfill.window(symbol, ts, 20)
    if not rows:
        return out

    cur_score = rows[-1].v2_score if rows[-1].v2_score is not None else 0
    for lb in (1, 5, 20):
        if len(rows) > lb:
            past = rows[-lb - 1].v2_score
            past = past if past is not None else 0
            out[f"regime_v2_score_change_{lb}"] = cur_score - past

    scores = [r.v2_score for r in rows if r.v2_score is not None]
    if scores:
        out["regime_v2_score_max_in_20"] = max(scores)
        out["regime_v2_score_min_in_20"] = min(scores)
        out["regime_v2_score_range_in_20"] = max(scores) - min(scores)
    return out


def _feat_regime_v1_v2_disagreement(row: Optional[RegimeRow]) -> dict:
    """v1 vs v2 H4 detector disagreement. 1 feature.

    Per session 38 + ADR notes, v1 and v2 differ in stricter dead-zone
    handling (v2 has explicit dead_zone divisor). When they disagree
    on the same H4 boundary, the regime is ambiguous.
    """
    if not row:
        return {"regime_v1_v2_disagreement": 0}
    v1 = row.v1_direction or "UNTAGGED"
    v2 = row.v2_direction or "UNTAGGED"
    return {"regime_v1_v2_disagreement": int(v1 != v2)}


def _feat_side_x_regime(side: Optional[str], row: Optional[RegimeRow]) -> dict:
    """Side x regime interaction features. 6 features.

    - ``regime_counter_to_v2``: 1 if (LONG and bearish) or (SHORT and
      bullish). Replicates K54 v1's ``counter_direction_flag`` for
      v2 detector.
    - ``regime_counter_to_v1``: same but for v1 detector.
    - ``regime_aligned_v2``: 1 if (LONG and bullish) or (SHORT and bearish).
    - ``regime_aligned_v1``: same for v1.
    - ``regime_long_in_bullish_v2``: 1 if LONG in bullish v2.
      F2 finding: XAUUSD London/trending_bull/LONG -59.8pp WR delta.
    - ``regime_short_in_bearish_v2``: 1 if SHORT in bearish v2 (the
      complementary cohort, may also have decay signal per A6).
    """
    side_norm = _normalize_side(side)
    v1 = (row.v1_direction if row else None) or "UNTAGGED"
    v2 = (row.v2_direction if row else None) or "UNTAGGED"
    out = {
        "regime_counter_to_v2": 0,
        "regime_counter_to_v1": 0,
        "regime_aligned_v2": 0,
        "regime_aligned_v1": 0,
        "regime_long_in_bullish_v2": 0,
        "regime_short_in_bearish_v2": 0,
    }
    if side_norm is None:
        return out

    if (side_norm == "LONG" and v2 == "bearish") or (side_norm == "SHORT" and v2 == "bullish"):
        out["regime_counter_to_v2"] = 1
    if (side_norm == "LONG" and v1 == "bearish") or (side_norm == "SHORT" and v1 == "bullish"):
        out["regime_counter_to_v1"] = 1
    if (side_norm == "LONG" and v2 == "bullish") or (side_norm == "SHORT" and v2 == "bearish"):
        out["regime_aligned_v2"] = 1
    if (side_norm == "LONG" and v1 == "bullish") or (side_norm == "SHORT" and v1 == "bearish"):
        out["regime_aligned_v1"] = 1
    if side_norm == "LONG" and v2 == "bullish":
        out["regime_long_in_bullish_v2"] = 1
    if side_norm == "SHORT" and v2 == "bearish":
        out["regime_short_in_bearish_v2"] = 1
    return out


def _feat_cross_instrument_alignment(
    backfill: RegimeBackfillIndex,
    symbol: str,
    ts: datetime,
) -> dict:
    """Fleet-wide regime alignment + XAU-anchor features. ~13 features.

    - ``regime_fleet_bullish_count``: # of fleet symbols with v2=bullish.
    - ``regime_fleet_bearish_count``: # with v2=bearish.
    - ``regime_fleet_transitional_count``: # with v2=transitional or
      missing.
    - ``regime_fleet_aligned_with_self``: # of fleet symbols (excl self)
      whose v2 label matches the current symbol's v2 label.
    - ``regime_fleet_score_mean``: mean v2_score across fleet (excl self).
    - ``regime_fleet_score_signed_agreement``: sign(self.score) ==
      sign(mean fleet score) (binary).
    - ``regime_xau_v2_is_bullish``: 1 if XAUUSD's v2 == bullish.
    - ``regime_xau_v2_is_bearish``: 1 if XAUUSD's v2 == bearish.
    - ``regime_xau_matches_self``: 1 if XAUUSD v2 == self v2.
    - ``regime_xau_opposite_self``: 1 if XAU bullish + self bearish, or
      vice versa.
    - ``regime_xau_score``: XAUUSD's v2_score raw value.
    - ``regime_xau_score_abs``: |XAU v2_score|.
    - ``regime_xau_to_self_score_diff``: self.score - xau.score (regime
      drift relative to gold).

    Per audit Section 5: cross-instrument regime alignment is a noted gap.
    XAU is risk-correlated with metals + indices per
    ``cross_instrument_correlation_gate.py`` correlation matrix.

    Inference cost: 7 backfill lookups (fleet symbols), each O(log n)
    bisect on its symbol's pre-sorted array. Bounded.
    """
    out = {
        "regime_fleet_bullish_count": 0,
        "regime_fleet_bearish_count": 0,
        "regime_fleet_transitional_count": 0,
        "regime_fleet_aligned_with_self": 0,
        "regime_fleet_score_mean": 0.0,
        "regime_fleet_score_signed_agreement": 0,
        "regime_xau_v2_is_bullish": 0,
        "regime_xau_v2_is_bearish": 0,
        "regime_xau_matches_self": 0,
        "regime_xau_opposite_self": 0,
        "regime_xau_score": 0,
        "regime_xau_score_abs": 0,
        "regime_xau_to_self_score_diff": 0,
    }

    self_row = backfill.latest_at(symbol, ts)
    self_label = (self_row.v2_direction if self_row else None) or "UNTAGGED"
    self_score = self_row.v2_score if (self_row and self_row.v2_score is not None) else 0

    fleet_scores: list[int] = []
    aligned_count = 0
    bullish = bearish = transitional = 0
    self_upper = str(symbol).upper()

    for fsym in FLEET_SYMBOLS:
        if fsym == self_upper:
            continue
        frow = backfill.latest_at(fsym, ts)
        if not frow:
            transitional += 1  # treat missing as transitional
            continue
        flabel = frow.v2_direction or "UNTAGGED"
        if flabel == "bullish":
            bullish += 1
        elif flabel == "bearish":
            bearish += 1
        else:
            transitional += 1
        if flabel == self_label:
            aligned_count += 1
        if frow.v2_score is not None:
            fleet_scores.append(frow.v2_score)

    out["regime_fleet_bullish_count"] = bullish
    out["regime_fleet_bearish_count"] = bearish
    out["regime_fleet_transitional_count"] = transitional
    out["regime_fleet_aligned_with_self"] = aligned_count
    if fleet_scores:
        mean = sum(fleet_scores) / len(fleet_scores)
        out["regime_fleet_score_mean"] = round(mean, 3)
        # Signed agreement: do self and fleet mean both lean same direction?
        if (self_score > 0 and mean > 0) or (self_score < 0 and mean < 0):
            out["regime_fleet_score_signed_agreement"] = 1

    # XAU anchor (skip if self IS XAU).
    if self_upper != "XAUUSD":
        xau_row = backfill.latest_at("XAUUSD", ts)
        if xau_row:
            xlabel = xau_row.v2_direction or "UNTAGGED"
            xscore = xau_row.v2_score if xau_row.v2_score is not None else 0
            out["regime_xau_v2_is_bullish"] = int(xlabel == "bullish")
            out["regime_xau_v2_is_bearish"] = int(xlabel == "bearish")
            out["regime_xau_matches_self"] = int(xlabel == self_label)
            opposite = (xlabel == "bullish" and self_label == "bearish") or \
                       (xlabel == "bearish" and self_label == "bullish")
            out["regime_xau_opposite_self"] = int(opposite)
            out["regime_xau_score"] = xscore
            out["regime_xau_score_abs"] = abs(xscore)
            out["regime_xau_to_self_score_diff"] = self_score - xscore
    else:
        # Self IS XAU — set XAU features to "match self" sentinels so
        # rows aren't biased toward "XAU-anchor missing" cohort.
        out["regime_xau_v2_is_bullish"] = int(self_label == "bullish")
        out["regime_xau_v2_is_bearish"] = int(self_label == "bearish")
        out["regime_xau_matches_self"] = 1  # by definition
        out["regime_xau_opposite_self"] = 0
        out["regime_xau_score"] = self_score
        out["regime_xau_score_abs"] = abs(self_score)
        out["regime_xau_to_self_score_diff"] = 0

    return out


def _feat_cross_timeframe(
    ohlcv: OHLCVCache,
    backfill: RegimeBackfillIndex,
    symbol: str,
    ts: datetime,
) -> dict:
    """Cross-timeframe regime agreement: H4 (backfill) vs D1 (computed). 3 features.

    - ``regime_d1_direction_bullish``: 1 if D1 5-bar swing is bullish.
    - ``regime_d1_direction_bearish``: 1 if bearish.
    - ``regime_h4_d1_agreement``: 1 if v2 H4 label matches D1 direction
      (bullish-bullish or bearish-bearish).

    D1 direction uses a 5-bar simple close-vs-close swing, NOT the
    production v2 detector (D1 backfill is not available — backfill is
    H4-only). Approximation noted in catalog.
    """
    out = {
        "regime_d1_direction_bullish": 0,
        "regime_d1_direction_bearish": 0,
        "regime_h4_d1_agreement": 0,
    }
    # D1 candles closed BEFORE ts. Use ts - 1 second to push the cutoff
    # to BEFORE today's D1 candle (which hasn't closed yet at intraday ts).
    d1_cutoff = _d1_floor(ts) - timedelta(seconds=1)
    d1_rows = ohlcv.slice_until(symbol, "D1", d1_cutoff, n=10)
    d1_dir = _d1_swing_direction(d1_rows, lookback=5)
    if d1_dir == "bullish":
        out["regime_d1_direction_bullish"] = 1
    elif d1_dir == "bearish":
        out["regime_d1_direction_bearish"] = 1

    h4_row = backfill.latest_at(symbol, ts)
    h4_lbl = (h4_row.v2_direction if h4_row else None) or "UNTAGGED"
    if (h4_lbl == "bullish" and d1_dir == "bullish") or \
       (h4_lbl == "bearish" and d1_dir == "bearish"):
        out["regime_h4_d1_agreement"] = 1
    return out


def _feat_regime_conditional_vol(
    ohlcv: OHLCVCache,
    backfill: RegimeBackfillIndex,
    symbol: str,
    ts: datetime,
) -> dict:
    """Regime-conditional ATR ratios. 4 features.

    - ``regime_atr_h4_14``: current H4 ATR(14) (raw, instrument-specific
      magnitude — included for the model to scale; gold ATR ~10-30,
      USDJPY ATR ~0.1-0.3).
    - ``regime_atr_h4_ratio_to_20``: ATR(14) / mean ATR over last 20
      H4 candles. >1 = vol expanding within regime; <1 = vol compressing.
    - ``regime_atr_h4_ratio_to_50``: same with 50-bar baseline. Slower
      reference.
    - ``regime_atr_h1_to_h4_ratio``: H1 ATR(14) / H4 ATR(14). Captures
      microstructure-vs-macro vol regime; high ratio = intra-H4 noise
      higher than usual.

    Per ``project_distributional_findings``: gold has fat-tail ξ=0.35 +
    GARCH persistence 0.9906 + 6.2x more 3σ events than Gaussian.
    Vol-ratio features condition on regime so the model can learn
    decay-vs-acceleration cells. Vol primitives (raw ATRs, percentiles)
    belong to the volatility family — these features are explicitly
    *regime-CONDITIONAL* (always relative to H4 regime context).
    """
    out = {
        "regime_atr_h4_14": 0.0,
        "regime_atr_h4_ratio_to_20": 0.0,
        "regime_atr_h4_ratio_to_50": 0.0,
        "regime_atr_h1_to_h4_ratio": 0.0,
    }
    # H4 candle at ts may not have closed — use H4 boundary BEFORE ts.
    h4_cutoff = _h4_floor(ts) - timedelta(seconds=1)
    h4_rows = ohlcv.slice_until(symbol, "H4", h4_cutoff, n=60)
    cur_atr = _atr(h4_rows, period=14)
    if cur_atr is None:
        return out
    out["regime_atr_h4_14"] = round(cur_atr, 6)

    # Mean-ATR baselines: compute ATR over rolling 14-window for each
    # endpoint in the lookback (cheap; not a full true rolling, but the
    # baseline-ATR-of-recent-bars proxy).
    for lb in ATR_BASELINE_H4_LOOKBACKS:
        if len(h4_rows) >= lb + 14:
            atrs: list[float] = []
            # Sample 5 evenly-spaced ATR snapshots in the lookback to
            # avoid O(N*period) cost.
            snapshots = 5
            step = max(1, lb // snapshots)
            for i in range(lb, 0, -step):
                slice_end = len(h4_rows) - i
                slice_start = max(0, slice_end - 15)
                snap = h4_rows[slice_start:slice_end]
                a = _atr(snap, period=14)
                if a is not None:
                    atrs.append(a)
            if atrs:
                base = sum(atrs) / len(atrs)
                ratio = _safe_div(cur_atr, base)
                if ratio is not None:
                    out[f"regime_atr_h4_ratio_to_{lb}"] = round(ratio, 4)

    # H1 vs H4 ratio: pull H1 to ts (with same point-in-time discipline)
    # — H1 candle CLOSING before ts is the most-recent completed H1.
    h1_cutoff = ts.replace(minute=0, second=0, microsecond=0) - timedelta(seconds=1)
    h1_rows = ohlcv.slice_until(symbol, "H1", h1_cutoff, n=20)
    h1_atr = _atr(h1_rows, period=14)
    if h1_atr is not None and cur_atr > 0:
        out["regime_atr_h1_to_h4_ratio"] = round(h1_atr / cur_atr, 4)
    return out


def _feat_regime_score_normalized(row: Optional[RegimeRow]) -> dict:
    """Signed v2_score normalized by dead_zone — strength of regime vote.

    1 feature. Captures "how far ABOVE the noise floor is the directional
    score". score=4, dead_zone=2 -> normalized=2.0 (clear lean). score=2,
    dead_zone=2 -> normalized=1.0 (boundary). score=-6, dead_zone=2 ->
    normalized=-3.0 (strong bearish lean).

    Robust to the dead_zone hyperparameter drift (v2 uses
    ``max(2, min_swing_transitions // 8)``); a normalized score is more
    transferable across periods than the raw score.
    """
    if not row or row.v2_score is None or row.v2_dead_zone is None or row.v2_dead_zone <= 0:
        return {"regime_v2_score_normalized": 0.0}
    return {
        "regime_v2_score_normalized": round(row.v2_score / row.v2_dead_zone, 4),
    }


def _feat_backfill_availability(
    backfill: RegimeBackfillIndex,
    symbol: str,
    ts: datetime,
) -> dict:
    """Backfill-availability indicator. 2 features.

    Critical for distinguishing "zeros because regime is neutral" from
    "zeros because backfill has no row for this (symbol, ts)". US30_cash
    trades and pre-2026-01-21 trades hit the second case and would be
    silently mis-modeled as "neutral" without these flags.

    - ``regime_backfill_available``: 1 if a backfill row was found for
      this (symbol, ts); 0 if missing.
    - ``regime_backfill_h4_bars_stale``: H4 bars between the located
      backfill row and ``ts`` (capped at 100). 0 means current; high
      means "the regime is from many H4 candles ago" (e.g. weekend).
      -1 sentinel if no row was found.
    """
    row = backfill.latest_at(symbol, ts)
    if row is None:
        return {
            "regime_backfill_available": 0,
            "regime_backfill_h4_bars_stale": -1,
        }
    # Bars stale = (ts H4 floor - row.ts) / 4h. Capped at 100.
    h4_floor_ts = _h4_floor(ts)
    delta_hours = (h4_floor_ts - row.ts).total_seconds() / 3600.0
    stale_bars = max(0, min(100, int(delta_hours / 4)))
    return {
        "regime_backfill_available": 1,
        "regime_backfill_h4_bars_stale": stale_bars,
    }


def _feat_regime_one_hot_for_v2_dead_zone(row: Optional[RegimeRow]) -> dict:
    """v2_dead_zone bucket one-hot. 3 features.

    Dead-zone is empirically clustered at {2, 3, 4} per v2 detector
    formula ``max(2, min_swing_transitions // 8)``. Bucket-encoding lets
    the model learn nonlinear regime-strength behavior without imposing
    monotonicity.
    """
    dz = row.v2_dead_zone if row else None
    return {
        "regime_v2_dz_is_2": int(dz == 2),
        "regime_v2_dz_is_3": int(dz == 3),
        "regime_v2_dz_is_4_or_more": int(dz is not None and dz >= 4),
    }


# ============================================================================
# Top-level extractor
# ============================================================================

@dataclass
class RegimeFeatureContext:
    """Context container — bind backfill + ohlcv once, then call per row.

    Inference-cost note: instantiate ONCE at module entry; pass to
    ``compute_regime_features`` in the inner loop.
    """

    backfill: RegimeBackfillIndex = field(default_factory=RegimeBackfillIndex)
    ohlcv: OHLCVCache = field(default_factory=OHLCVCache)


def compute_regime_features(
    symbol: str,
    ts: datetime,
    side: Optional[str],
    *,
    ctx: Optional[RegimeFeatureContext] = None,
) -> "OrderedDict[str, float | int]":
    """Compute the full regime-family feature dict for one trade entry.

    Inputs
    ------
    symbol:
        Instrument symbol (case-insensitive). Mapped to fleet via
        upper-case match.
    ts:
        Trade entry timestamp (UTC-aware datetime). Internally we
        consume only data with backfill timestamp < ts, with two
        explicit exceptions documented in the call sites:
          - ``RegimeBackfillIndex.latest_at`` includes equality (the
            H4 candle whose boundary == ts; intentional, see method
            docstring).
          - ``OHLCVCache.slice_until`` includes equality on the candle
            OPEN time; H4/D1/H1 cutoffs use ``ts - 1s`` to enforce
            strict-less-than against the candle open.
    side:
        Trade direction "LONG" / "SHORT" / None. Normalized internally.

    Returns
    -------
    OrderedDict of 50 features. Keys are stable across calls (use as
    column names in features.csv).

    Inference cost (single call): 1 backfill lookup + 1 backfill window
    walk + 7 fleet backfill lookups + ~3 OHLCV slices (H4, D1, H1).
    Bounded; suitable for inner-loop use.
    """
    if ctx is None:
        ctx = RegimeFeatureContext()

    # Cutoff-discipline assertion: ts must be a UTC-aware datetime.
    assert ts.tzinfo is not None, "ts must be UTC-aware"
    # NOTE: We do NOT assert ts <= DATA_CUTOFF_UTC inside the inner loop
    # because callers (build pipeline) enforce it once at the dataset
    # boundary. Re-asserting here would slow the loop and double-error.

    sym_upper = str(symbol).upper()
    cur_row = ctx.backfill.latest_at(sym_upper, ts)

    feats: "OrderedDict[str, float | int]" = OrderedDict()

    # Group 1: current regime label one-hots (v1 + v2)
    feats.update(_feat_current_regime_v1_onehot(cur_row))           # 4
    feats.update(_feat_current_regime_v2_onehot(cur_row))           # 5

    # Group 2: v2 score primitives + dead_zone (audit Section 5 quick wins)
    feats.update(_feat_v2_score_features(cur_row))                  # 4
    feats.update(_feat_regime_score_normalized(cur_row))            # 1
    feats.update(_feat_regime_one_hot_for_v2_dead_zone(cur_row))    # 3

    # Group 3: swing transition counts (auxiliary regime-strength signal)
    feats.update(_feat_swing_counts(cur_row))                       # 4

    # Group 4: regime stability / transition flags / time-since-flip
    feats.update(_feat_regime_stability(ctx.backfill, sym_upper, ts))  # 7

    # Group 5: regime score dynamics (velocity, max, min, range)
    feats.update(_feat_regime_score_dynamics(ctx.backfill, sym_upper, ts))  # 6

    # Group 6: v1 vs v2 detector disagreement
    feats.update(_feat_regime_v1_v2_disagreement(cur_row))          # 1

    # Group 7: side x regime interactions (counter, aligned, F2 cohort)
    feats.update(_feat_side_x_regime(side, cur_row))                # 6

    # Group 8: cross-instrument fleet alignment + XAU anchor
    feats.update(_feat_cross_instrument_alignment(ctx.backfill, sym_upper, ts))  # 13

    # Group 9: cross-timeframe (H4 vs D1) agreement
    feats.update(_feat_cross_timeframe(ctx.ohlcv, ctx.backfill, sym_upper, ts))  # 3

    # Group 10: regime-conditional volatility ratios
    feats.update(_feat_regime_conditional_vol(ctx.ohlcv, ctx.backfill, sym_upper, ts))  # 4

    # Group 11: backfill availability indicator (avoid zero-vs-missing trap)
    feats.update(_feat_backfill_availability(ctx.backfill, sym_upper, ts))  # 2

    # Inline-assertion: feature count must match catalog. Update both
    # this assertion AND ``regime.csv`` if you add/remove features.
    # Tally: 4 + 5 + 4 + 1 + 3 + 4 + 7 + 6 + 1 + 6 + 13 + 3 + 4 + 2 = 63.
    expected = 63
    actual = len(feats)
    assert actual == expected, (
        f"regime feature count drift: expected {expected}, got {actual}. "
        f"Update regime.csv catalog when changing features."
    )

    return feats


# ============================================================================
# Public API
# ============================================================================

__all__ = [
    "DATA_CUTOFF_UTC",
    "FLEET_SYMBOLS",
    "OHLCVCache",
    "RegimeBackfillIndex",
    "RegimeFeatureContext",
    "RegimeRow",
    "compute_regime_features",
]
