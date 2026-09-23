"""A2 — Per-Month Per-Instrument WR/ExpR Rolling 50-Trade Windows.

Pure-Python decay-velocity primitives. Surfaces realized-R based metrics
across rolling N-trade windows for each instrument and derives a per-instrument
linear-regression decay slope (WR over time) with associated p-value.

Strategic question
------------------
For each instrument the system trades, how fast is WR / Expectancy decaying
over time? Is decay uniform across the fleet, or concentrated on specific
instruments?

A2 is the per-instrument complement to A1's system-vs-regime split.

Design notes
------------
*Realized-R* — the slope is computed on **per-trade** outcomes (WR per
window; Exp R per window) — never on walk-level / structural proxies.
Walk-level evidence is not predictive of realized R (see
``feedback_walk_level_evidence_not_predictive``).

*Bonferroni* — the family of seven decay-slope hypothesis tests (one per
instrument) uses Bonferroni correction (multiply raw p by N_tested).

*Window choice* — default 50 trades. With per-trade WR variance ≈ 0.5 and
n=50, the Wilson 95% CI half-width on WR ≈ ±13.8pp; tight enough to read
trend direction at the chunk level. With ~100-150 filled trades over six
months, 50-trade windows give ~12 step-points (one per ~12 trades), which
is enough sample for a 4+ point regression.

This module is pure-Python (uses only ``math``/``statistics``/``json``).
No third-party dependencies — the same constraints as the rest of
``src/research_infra``.
"""

from __future__ import annotations

import json
import math
import os
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


# ────────────────────────────────────────────────────────────────────────────
# Public dataclasses
# ────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class WindowPoint:
    """A single rolling-window observation.

    Attributes
    ----------
    timestamp : datetime
        Wall-clock timestamp of the *last* trade in the window.
    n : int
        Number of trades in the window (== window size for full windows).
    wr : float
        Realised-R win rate ∈ [0, 1] over the window. Counts ``r > 0`` as
        a win (BE/exact-zero counts as loss for WR; included in Exp R).
    exp_r : float
        Mean realised R per trade over the window.
    window_index : int
        0-based index of this point in the series.
    """

    timestamp: datetime
    n: int
    wr: float
    exp_r: float
    window_index: int


@dataclass(frozen=True)
class RollingSeries:
    """Sequence of rolling-window observations for a single instrument."""

    symbol: str
    window: int
    points: tuple[WindowPoint, ...]
    total_trades: int

    def __iter__(self) -> Iterator[WindowPoint]:
        return iter(self.points)

    def __len__(self) -> int:
        return len(self.points)

    @property
    def is_empty(self) -> bool:
        return len(self.points) == 0


# ────────────────────────────────────────────────────────────────────────────
# Trade extraction helpers
# ────────────────────────────────────────────────────────────────────────────

# Possible field names a trade dict can use for realised R. Order is
# preference (first-found-wins).
_REALIZED_R_FIELDS = (
    "realized_r",
    "realized_R",
    "actual_r",
    "actual_R",
    "r_multiple",
    "rR",
)

_TIMESTAMP_FIELDS = (
    "candle_close_time",
    "candle_time",
    "timestamp",
    "exit_time",
    "date",
)


def _parse_timestamp(raw: Any) -> datetime | None:
    """Best-effort ISO-string-or-datetime → tz-aware UTC datetime."""
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    if not isinstance(raw, str):
        return None
    s = raw.strip()
    if not s:
        return None
    # YYYY-MM-DD shorthand
    if len(s) == 10 and s.count("-") == 2:
        try:
            return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    # ISO with optional Z suffix
    candidate = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _extract_realized_r(trade: dict) -> float | None:
    """Find the realised-R field on a trade dict, return None if not present.

    Looks at top-level fields first, then ``trade['exit']`` (per the v1.1
    instrumentation schema documented in
    ``research/a3_trade_record_instrumentation/README.md``).
    """
    for name in _REALIZED_R_FIELDS:
        if name in trade and trade[name] is not None:
            try:
                return float(trade[name])
            except (TypeError, ValueError):
                continue
    exit_block = trade.get("exit") if isinstance(trade.get("exit"), dict) else None
    if exit_block:
        for name in _REALIZED_R_FIELDS:
            if name in exit_block and exit_block[name] is not None:
                try:
                    return float(exit_block[name])
                except (TypeError, ValueError):
                    continue
    return None


def _extract_timestamp(trade: dict) -> datetime | None:
    """Find a usable timestamp on a trade dict."""
    for name in _TIMESTAMP_FIELDS:
        if name in trade and trade[name] is not None:
            ts = _parse_timestamp(trade[name])
            if ts is not None:
                return ts
    # Nested locations
    for parent in ("metadata", "exit", "trade_parameters"):
        block = trade.get(parent)
        if isinstance(block, dict):
            for name in _TIMESTAMP_FIELDS:
                if name in block and block[name] is not None:
                    ts = _parse_timestamp(block[name])
                    if ts is not None:
                        return ts
    return None


def _extract_symbol(trade: dict) -> str | None:
    """Find a usable symbol on a trade dict."""
    if "symbol" in trade and trade["symbol"]:
        return str(trade["symbol"]).upper()
    metadata = trade.get("metadata")
    if isinstance(metadata, dict) and metadata.get("symbol"):
        return str(metadata["symbol"]).upper()
    return None


def _is_filled(trade: dict) -> bool:
    """Heuristic: did this trade actually fill?

    Returns True iff a finite realised R can be extracted. The trade-record
    pipeline writes ``exit: null, execution: null`` for unfilled CANDs,
    and the v1.1 instrumentation schema only populates ``exit.realized_R``
    after a real fill. This is the canonical "did it fill?" signal.
    """
    r = _extract_realized_r(trade)
    return r is not None and math.isfinite(r)


# ────────────────────────────────────────────────────────────────────────────
# Core: rolling-window WR / Exp R
# ────────────────────────────────────────────────────────────────────────────

def rolling_window_wr_exp(trades: list[dict], window: int = 50) -> RollingSeries:
    """Compute rolling (WR, Exp R) over ``window``-trade buckets.

    Behaviour:
      - Trades are sorted by extracted timestamp ascending. Trades with no
        usable timestamp are dropped.
      - Trades with no usable realised R are dropped (i.e. unfilled trades
        are not counted toward the window).
      - If fewer than ``window`` trades remain, returns an empty series.
      - Each rolling window is **non-overlapping** (step == window). A
        non-overlapping series gives independent samples for the slope
        regression — overlapping windows would inflate the apparent
        regression d.o.f. and break the slope p-value's calibration.
        Window k covers trades [k*window, (k+1)*window).

    Parameters
    ----------
    trades : list of dict
        Each dict must carry (somewhere) a realised-R numeric field and a
        timestamp. See ``_REALIZED_R_FIELDS`` and ``_TIMESTAMP_FIELDS``.
    window : int, default 50
        Window size in trades. Must be ≥ 2.

    Returns
    -------
    RollingSeries
        Empty series if fewer than ``window`` filled trades.
    """
    if window < 2:
        raise ValueError(f"window must be >= 2, got {window}")
    if not isinstance(trades, list):
        raise TypeError(f"trades must be a list, got {type(trades).__name__}")

    # Filter + sort by timestamp ascending
    enriched: list[tuple[datetime, float, dict]] = []
    symbols_seen: list[str] = []
    for t in trades:
        if not isinstance(t, dict):
            continue
        ts = _extract_timestamp(t)
        r = _extract_realized_r(t)
        if ts is None or r is None or not math.isfinite(r):
            continue
        sym = _extract_symbol(t)
        if sym:
            symbols_seen.append(sym)
        enriched.append((ts, r, t))

    enriched.sort(key=lambda triple: triple[0])
    total = len(enriched)

    # Determine series symbol (first non-empty observed; "MIXED" if multiple)
    if symbols_seen:
        unique_syms = sorted(set(symbols_seen))
        symbol = unique_syms[0] if len(unique_syms) == 1 else "MIXED"
    else:
        symbol = "UNKNOWN"

    if total < window:
        return RollingSeries(symbol=symbol, window=window, points=tuple(), total_trades=total)

    points: list[WindowPoint] = []
    n_full = total // window
    for k in range(n_full):
        start = k * window
        end = start + window
        chunk = enriched[start:end]
        rs = [r for (_, r, _) in chunk]
        wins = sum(1 for r in rs if r > 0)
        wr = wins / window
        exp_r = sum(rs) / window
        last_ts = chunk[-1][0]
        points.append(WindowPoint(
            timestamp=last_ts,
            n=window,
            wr=wr,
            exp_r=exp_r,
            window_index=k,
        ))

    return RollingSeries(
        symbol=symbol,
        window=window,
        points=tuple(points),
        total_trades=total,
    )


# ────────────────────────────────────────────────────────────────────────────
# Per-instrument aggregation
# ────────────────────────────────────────────────────────────────────────────

def per_instrument_decay_velocity(
    trade_records_dir: Path,
    window: int = 50,
    symbols: Iterable[str] | None = None,
    aux_index_path: Path | None = None,
) -> dict[str, RollingSeries]:
    """Aggregate trade records under ``trade_records_dir`` per-instrument.

    Layout assumed:
      ``trade_records_dir/{SYMBOL}/*.json``  (one decision-record JSON per file)

    Each file is loaded; only files where ``_is_filled`` is True are
    counted. The per-symbol filled-trade list is fed to
    ``rolling_window_wr_exp``.

    Parameters
    ----------
    trade_records_dir : Path
        Directory with per-symbol subdirectories of trade-record JSONs.
    window : int, default 50
        Window size.
    symbols : iterable of str, optional
        Filter to these symbols only (case-insensitive). If None, all
        subdirectories are read.
    aux_index_path : Path, optional
        Optional path to a ``_trade_index.json`` style file (single JSON
        with a top-level ``trades`` array of compact trade dicts). If
        provided, trades from this index are appended to the per-symbol
        lists (so historical batch trades that pre-date the v1.1
        instrumentation schema can be included). Trades are deduplicated
        by ``trade_id`` if present, else by ``(symbol, timestamp_iso)``.

    Returns
    -------
    dict[str, RollingSeries]
        Symbol → series mapping. Symbols with zero filled trades return
        an empty RollingSeries (rather than being absent from the dict)
        so the caller can distinguish "no fills" from "not requested".
    """
    trade_records_dir = Path(trade_records_dir)
    if not trade_records_dir.exists():
        raise FileNotFoundError(f"trade_records_dir does not exist: {trade_records_dir}")

    requested_set: set[str] | None
    if symbols is not None:
        requested_set = {s.upper() for s in symbols}
    else:
        requested_set = None

    # Step 1: per-symbol trade lists from the directory tree
    per_symbol: dict[str, list[dict]] = {}
    seen_trade_ids: dict[str, set[str]] = {}

    if trade_records_dir.is_dir():
        for sym_dir in sorted(trade_records_dir.iterdir()):
            if not sym_dir.is_dir():
                continue
            symbol = sym_dir.name.upper()
            if requested_set is not None and symbol not in requested_set:
                continue
            per_symbol.setdefault(symbol, [])
            seen_trade_ids.setdefault(symbol, set())
            for fp in sorted(sym_dir.glob("*.json")):
                try:
                    record = json.loads(fp.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if not isinstance(record, dict):
                    continue
                # Inject symbol + timestamp if missing at top-level for
                # downstream extraction
                if "symbol" not in record or not record.get("symbol"):
                    record["symbol"] = symbol
                if not _is_filled(record):
                    continue
                tid = (
                    record.get("trade_id")
                    or record.get("metadata", {}).get("trade_id")
                    if isinstance(record.get("metadata"), dict)
                    else record.get("trade_id")
                )
                if tid:
                    if tid in seen_trade_ids[symbol]:
                        continue
                    seen_trade_ids[symbol].add(tid)
                per_symbol[symbol].append(record)

    # Ensure all requested symbols have an entry even if dir is empty
    if requested_set is not None:
        for s in requested_set:
            per_symbol.setdefault(s, [])
            seen_trade_ids.setdefault(s, set())

    # Step 2: optional aux index merge
    if aux_index_path is not None:
        aux = Path(aux_index_path)
        if aux.exists():
            try:
                doc = json.loads(aux.read_text(encoding="utf-8"))
            except Exception:
                doc = None
            if isinstance(doc, dict):
                aux_trades = doc.get("trades")
                if isinstance(aux_trades, list):
                    for t in aux_trades:
                        if not isinstance(t, dict):
                            continue
                        sym = _extract_symbol(t)
                        if sym is None:
                            continue
                        if requested_set is not None and sym not in requested_set:
                            continue
                        if not _is_filled(t):
                            continue
                        per_symbol.setdefault(sym, [])
                        seen_trade_ids.setdefault(sym, set())
                        tid = t.get("trade_id")
                        if tid:
                            if tid in seen_trade_ids[sym]:
                                continue
                            seen_trade_ids[sym].add(tid)
                        per_symbol[sym].append(t)

    # Step 3: build per-symbol series
    out: dict[str, RollingSeries] = {}
    for sym, trades in per_symbol.items():
        out[sym] = rolling_window_wr_exp(trades, window=window)
        # Override symbol field on the series (rolling_window_wr_exp infers
        # it from observed trades; we want it pinned to the directory name
        # for caller clarity)
        out[sym] = RollingSeries(
            symbol=sym,
            window=out[sym].window,
            points=out[sym].points,
            total_trades=out[sym].total_trades,
        )
    return out


# ────────────────────────────────────────────────────────────────────────────
# Slope regression + p-value
# ────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SlopeResult:
    """Linear regression result for a rolling series."""

    slope_per_window: float
    """Slope per window step (WR pp per 1 window)."""
    slope_per_30d: float
    """Slope normalised to per-30-days. Computed from average window
    duration. NaN when fewer than 2 points."""
    intercept: float
    p_value: float
    """Two-sided p-value under H0: slope == 0. Uses Student t with
    df = n_points - 2. NaN for n < 3."""
    r_squared: float
    n_points: int
    avg_window_days: float
    """Mean wall-clock days between consecutive window endpoints. NaN if
    n < 2."""


def _student_t_two_sided_p(t: float, df: int) -> float:
    """Two-sided p-value for Student-t statistic with ``df`` d.o.f.

    Uses a numerically stable continued-fraction expansion of the
    incomplete beta function (Lentz's method) — same as scipy's
    ``stats.t.sf`` but pure-Python so this module stays dependency-free.

    Returns NaN for df < 1.
    """
    if df < 1 or not math.isfinite(t):
        return float("nan")
    if t == 0:
        return 1.0
    # P(|T| >= |t|) = I_x(df/2, 1/2)  where x = df / (df + t^2)
    a = df / 2.0
    b = 0.5
    x = df / (df + t * t)
    # Regularised incomplete beta I_x(a, b)
    bt_log = (
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x if x > 0 else 1e-300)
        + b * math.log(1 - x if 1 - x > 0 else 1e-300)
    )
    bt = math.exp(bt_log)
    if x < (a + 1) / (a + b + 2):
        cf = _betacf(a, b, x)
        ix = bt * cf / a
    else:
        cf = _betacf(b, a, 1 - x)
        ix = 1.0 - bt * cf / b
    # The two-sided p is just I_x(a, b)
    return max(0.0, min(1.0, ix))


def _betacf(a: float, b: float, x: float, max_iter: int = 200, eps: float = 3e-16) -> float:
    """Continued-fraction expansion for the incomplete beta function.

    Translated from Numerical Recipes §6.4 (modified Lentz).
    """
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d_ = 1.0 - qab * x / qap
    if abs(d_) < 1e-30:
        d_ = 1e-30
    d_ = 1.0 / d_
    h = d_
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        # Even step
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d_ = 1.0 + aa * d_
        if abs(d_) < 1e-30:
            d_ = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30:
            c = 1e-30
        d_ = 1.0 / d_
        h *= d_ * c
        # Odd step
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d_ = 1.0 + aa * d_
        if abs(d_) < 1e-30:
            d_ = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30:
            c = 1e-30
        d_ = 1.0 / d_
        delta = d_ * c
        h *= delta
        if abs(delta - 1.0) < eps:
            return h
    return h


def _ols(xs: list[float], ys: list[float]) -> tuple[float, float, float, float]:
    """Plain OLS. Returns (slope, intercept, r2, p_value)."""
    n = len(xs)
    if n < 2:
        return float("nan"), float("nan"), float("nan"), float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    ssxx = sum((x - mx) ** 2 for x in xs)
    ssxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    ssyy = sum((y - my) ** 2 for y in ys)
    if ssxx <= 0:
        return float("nan"), my, float("nan"), float("nan")
    slope = ssxy / ssxx
    intercept = my - slope * mx
    if n < 3 or ssyy <= 0:
        # Cannot compute residual SE / r² → both undefined
        if ssyy <= 0:
            r2 = float("nan")
        else:
            r2 = 1.0 - sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys)) / ssyy
        return slope, intercept, r2, float("nan")
    # Residual SS
    rss = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    r2 = 1.0 - rss / ssyy if ssyy > 0 else float("nan")
    se_residual = math.sqrt(rss / (n - 2)) if n > 2 else float("nan")
    if not math.isfinite(se_residual) or se_residual <= 0 or ssxx <= 0:
        return slope, intercept, r2, float("nan")
    se_slope = se_residual / math.sqrt(ssxx)
    if se_slope <= 0 or not math.isfinite(se_slope):
        return slope, intercept, r2, float("nan")
    t_stat = slope / se_slope
    p = _student_t_two_sided_p(t_stat, df=n - 2)
    return slope, intercept, r2, p


def decay_slope(series: RollingSeries) -> SlopeResult:
    """Linear-regression slope of WR over time for a rolling series.

    Convention:
      - Positive slope → improving (WR rising over time).
      - Negative slope → decaying (WR falling over time).

    Two normalisations are returned:
      - ``slope_per_window`` — pp per window step (raw OLS coefficient
        on the window-index axis).
      - ``slope_per_30d`` — pp per 30 calendar days. Derived from the
        mean wall-clock duration between consecutive window endpoints.

    Returns
    -------
    SlopeResult
        ``slope_per_window``, ``slope_per_30d``, ``intercept``,
        ``p_value``, ``r_squared``, ``n_points``, ``avg_window_days``.

    For series with fewer than 2 points the slope is NaN. For fewer than
    3 points the p-value is NaN (no residual degrees of freedom).
    """
    points = list(series.points)
    n = len(points)
    if n < 2:
        return SlopeResult(
            slope_per_window=float("nan"),
            slope_per_30d=float("nan"),
            intercept=float("nan"),
            p_value=float("nan"),
            r_squared=float("nan"),
            n_points=n,
            avg_window_days=float("nan"),
        )

    xs = [float(p.window_index) for p in points]
    ys = [p.wr for p in points]
    slope, intercept, r2, p = _ols(xs, ys)

    # Average wall-clock days per window
    deltas = [
        (points[i].timestamp - points[i - 1].timestamp).total_seconds() / 86400.0
        for i in range(1, n)
    ]
    avg_days = statistics.mean(deltas) if deltas else float("nan")
    if avg_days and math.isfinite(avg_days) and avg_days > 0:
        slope_per_30d = slope * (30.0 / avg_days)
    else:
        slope_per_30d = float("nan")

    return SlopeResult(
        slope_per_window=slope,
        slope_per_30d=slope_per_30d,
        intercept=intercept,
        p_value=p,
        r_squared=r2,
        n_points=n,
        avg_window_days=avg_days,
    )


# ────────────────────────────────────────────────────────────────────────────
# Bonferroni-aware verdict
# ────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class InstrumentVerdict:
    """Per-instrument decay verdict.

    Attributes
    ----------
    symbol : str
    n_total : int
        Total filled trades for this instrument.
    n_windows : int
        Number of full rolling windows.
    h1_wr : float
        WR over the first half of filled trades. NaN when n < 2 * window.
    h2_wr : float
        WR over the second half of filled trades. NaN when n < 2 * window.
    slope_per_30d : float
        Decay slope (pp per 30 days). NaN when n_windows < 2.
    p_value_raw : float
        Slope p-value (two-sided). NaN when n_windows < 3.
    p_value_bonferroni : float
        ``min(1, raw_p × N_tested)``. NaN when raw is NaN.
    verdict : str
        One of: ``DECAYING``, ``IMPROVING``, ``STABLE``,
        ``INSUFFICIENT_N``, ``INCONCLUSIVE``.
    """

    symbol: str
    n_total: int
    n_windows: int
    h1_wr: float
    h2_wr: float
    slope_per_30d: float
    p_value_raw: float
    p_value_bonferroni: float
    verdict: str
    slope_per_window: float = float("nan")
    avg_window_days: float = float("nan")


def _half_split_wr(series: RollingSeries, trades: list[dict]) -> tuple[float, float]:
    """H1/H2 WR — split the filled-trade *sequence* in half by index."""
    if not trades:
        return float("nan"), float("nan")
    # Sort trades by ts the same way rolling_window_wr_exp does
    enriched: list[tuple[datetime, float]] = []
    for t in trades:
        ts = _extract_timestamp(t)
        r = _extract_realized_r(t)
        if ts is None or r is None or not math.isfinite(r):
            continue
        enriched.append((ts, r))
    enriched.sort(key=lambda p: p[0])
    n = len(enriched)
    if n < 2:
        return float("nan"), float("nan")
    mid = n // 2
    h1 = enriched[:mid]
    h2 = enriched[mid:]
    h1_wr = sum(1 for _, r in h1 if r > 0) / len(h1) if h1 else float("nan")
    h2_wr = sum(1 for _, r in h2 if r > 0) / len(h2) if h2 else float("nan")
    return h1_wr, h2_wr


def classify_verdict(
    slope_result: SlopeResult,
    n_total: int,
    p_corrected: float,
    *,
    n_min: int = 20,
    alpha: float = 0.05,
) -> str:
    """Classify a per-instrument decay verdict per the spec rules.

    Rules (per A2 brief):
      - ``DECAYING`` only when ``n_total >= n_min`` AND
        ``p_corrected < alpha`` AND slope < 0.
      - ``IMPROVING`` only when ``n_total >= n_min`` AND
        ``p_corrected < alpha`` AND slope > 0.
      - ``INSUFFICIENT_N`` when ``n_total < n_min``.
      - ``STABLE`` when n is sufficient, slope is well-defined, and
        |slope_per_30d| < 1pp/month (very small absolute change) — even
        if not significant.
      - ``INCONCLUSIVE`` otherwise.
    """
    if n_total < n_min:
        return "INSUFFICIENT_N"
    slope = slope_result.slope_per_30d
    if not math.isfinite(slope):
        return "INCONCLUSIVE"
    if math.isfinite(p_corrected) and p_corrected < alpha:
        if slope < 0:
            return "DECAYING"
        if slope > 0:
            return "IMPROVING"
    if math.isfinite(slope) and abs(slope) < 0.01:  # < 1pp / 30 days
        return "STABLE"
    return "INCONCLUSIVE"


def build_per_instrument_verdicts(
    series_map: dict[str, RollingSeries],
    trades_map: dict[str, list[dict]],
    *,
    n_min: int = 20,
    alpha: float = 0.05,
    bonferroni_n: int | None = None,
) -> dict[str, InstrumentVerdict]:
    """Build the per-instrument verdict block.

    Parameters
    ----------
    series_map : dict[str, RollingSeries]
        Output of ``per_instrument_decay_velocity``.
    trades_map : dict[str, list[dict]]
        Per-symbol filled-trade lists (used for H1/H2 WR split).
    n_min : int
        Minimum total trades for a non-INSUFFICIENT_N verdict.
    alpha : float
        Significance threshold on the *corrected* p-value.
    bonferroni_n : int, optional
        Number of tests to correct for. If None, defaults to the count
        of symbols that have at least 3 windows (i.e. were actually
        tested). This is the canonical Bonferroni denominator: tests
        that could not be run do not consume α budget.

    Returns
    -------
    dict[str, InstrumentVerdict]
    """
    # Compute slopes
    slopes: dict[str, SlopeResult] = {}
    for sym, series in series_map.items():
        slopes[sym] = decay_slope(series)

    if bonferroni_n is None:
        # Count instruments where slope p-value is meaningful (n_points >= 3)
        n_tested = sum(1 for s in slopes.values() if math.isfinite(s.p_value))
        bonferroni_n = max(1, n_tested)

    verdicts: dict[str, InstrumentVerdict] = {}
    for sym, series in series_map.items():
        sr = slopes[sym]
        n_total = series.total_trades
        h1_wr, h2_wr = _half_split_wr(series, trades_map.get(sym, []))
        if math.isfinite(sr.p_value):
            p_corr = min(1.0, sr.p_value * bonferroni_n)
        else:
            p_corr = float("nan")
        verdict = classify_verdict(sr, n_total, p_corr, n_min=n_min, alpha=alpha)
        verdicts[sym] = InstrumentVerdict(
            symbol=sym,
            n_total=n_total,
            n_windows=len(series),
            h1_wr=h1_wr,
            h2_wr=h2_wr,
            slope_per_30d=sr.slope_per_30d,
            slope_per_window=sr.slope_per_window,
            p_value_raw=sr.p_value,
            p_value_bonferroni=p_corr,
            avg_window_days=sr.avg_window_days,
            verdict=verdict,
        )
    return verdicts


# ────────────────────────────────────────────────────────────────────────────
# Concentration heuristic
# ────────────────────────────────────────────────────────────────────────────

def decay_concentration(verdicts: dict[str, InstrumentVerdict]) -> tuple[str, str]:
    """Return ``(label, reasoning)`` for the fleet-level concentration.

    - ``UNIFORM`` when ≥ 2 instruments are DECAYING, or when none are.
    - ``CONCENTRATED_ON_<SYM>[,<SYM>...]`` when 1 or 2 instruments
      are DECAYING (the rest STABLE / IMPROVING / INCONCLUSIVE /
      INSUFFICIENT_N).
    """
    decaying = [v.symbol for v in verdicts.values() if v.verdict == "DECAYING"]
    improving = [v.symbol for v in verdicts.values() if v.verdict == "IMPROVING"]
    stable = [v.symbol for v in verdicts.values() if v.verdict == "STABLE"]
    insufficient = [v.symbol for v in verdicts.values() if v.verdict == "INSUFFICIENT_N"]
    inconclusive = [v.symbol for v in verdicts.values() if v.verdict == "INCONCLUSIVE"]

    parts = []
    if decaying:
        parts.append(f"DECAYING={','.join(decaying)}")
    if improving:
        parts.append(f"IMPROVING={','.join(improving)}")
    if stable:
        parts.append(f"STABLE={','.join(stable)}")
    if inconclusive:
        parts.append(f"INCONCLUSIVE={','.join(inconclusive)}")
    if insufficient:
        parts.append(f"INSUFFICIENT_N={','.join(insufficient)}")
    summary = "; ".join(parts) if parts else "no verdicts"

    if len(decaying) == 0:
        label = "UNIFORM"
    elif len(decaying) >= 3:
        label = "UNIFORM"
    else:
        label = f"CONCENTRATED_ON_{','.join(sorted(decaying))}"
    return label, summary
