"""A5 — Regime-Stratified WR Matrix.

Tags every CANDIDATE with the v2 H4 regime active at its candle-close time
(falling back to the production label, then UNTAGGED), then emits a
(instrument, regime) WR/ExpR matrix.

Canonical regime source
-----------------------
``shadow_logs/structure_detector_divergences.jsonl`` — written by
``src/components/structure_detector_shadow_logger.py`` at every M15 close
with one row per timeframe (D1 / H4 / H1 / M15) per symbol. We only consume
the **H4** rows; that is the cadence on which H1+ regime decisions are made
in production.

Per-row schema (relevant fields)::

    {
      "ts": "2026-04-15T13:15:00Z",        # M15-close timestamp (the H4
                                             # window currently containing this
                                             # M15 candle)
      "symbol": "XAUUSD",                  # may be empty for very-early
                                             # promotion-window rows
      "timeframe": "H4",
      "v1_direction": "bullish" | "bearish" | "transitional",
      "v2_direction": "bullish" | "bearish" | "transitional",
      "production_label": "bullish" | "bearish" | "transitional",
      "mode": "shadow" | "live_v2"         # which detector drives production
    }

Regime selection priority (per ADR-004 + A2 GO decision 2026-04-26)::

    1. ``v2_direction`` if non-empty (canonical regime classification)
    2. ``production_label`` as a fallback if v2 was missing
    3. ``UNTAGGED`` otherwise

Empty-``symbol`` rows (~5k under the live_v2 promotion period) cannot be
joined and are skipped during indexing — CANDs whose H4 window only matches
empty-symbol rows fall through to ``UNTAGGED``.

H4-window join rule
-------------------
For a CAND at candle-close ``t``, the active H4 regime is the **latest**
H4 row with ``ts <= t`` for the same symbol, subject to a freshness
threshold (default 6 hours — covers a full H4 bar plus weekend/dead-zone
slack). Rows older than the threshold are treated as ``UNTAGGED``.

Wilson 95% CI
-------------
The matrix uses the Wilson score interval (no continuity correction)
rather than the normal approximation. Wilson is the recommended small-
sample interval (n < 50) and is robust at extreme proportions (k=0 or
k=n) where the normal approximation collapses. Per memory
``project_distributional_findings.md``, fat-tail outcomes argue for
small-sample-honest CIs — Wilson is the cheap, principled default.

Low-n flag
----------
Cells with ``n < 10`` are emitted but flagged ``LOW_N`` in the summary.
The threshold is the standard "do not claim significance at n<20" rule
relaxed to n<10 because the matrix is regime-decomposed and we still
want visibility into thin cells (e.g. SHORT/bearish regimes, where v1
emitted ~0% for 8k+ windows). Cells with ``n == 0`` are emitted as
``EMPTY`` with no WR/ExpR / CI fields populated.
"""

from __future__ import annotations

import bisect
import json
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Optional

from src.research_infra.structure_log_loader import (
    discover_structure_log_paths,
    load_structure_log_rows,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Maximum staleness of an H4 row to count as the "active" regime for a
#: CAND. 6 hours covers one full H4 bar (4 h) plus dead-zone / weekend
#: slack. Rows older than this for the queried symbol fall back to
#: ``UNTAGGED``.
DEFAULT_H4_FRESHNESS_HOURS: int = 6

#: Cells with n below this threshold are emitted but flagged ``LOW_N``.
LOW_N_THRESHOLD: int = 10

#: Sentinel regime returned when no H4 row is available for a CAND.
UNTAGGED: str = "UNTAGGED"

#: Wilson z for two-sided 95% CI (1.959964 ≈ 1.96).
_WILSON_Z_95: float = 1.959963984540054


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------


def _parse_iso8601_utc(ts: str) -> Optional[datetime]:
    """Parse an ISO-8601 UTC timestamp; return ``None`` on failure.

    Accepts both the trailing-Z form (``2026-04-15T13:15:00Z``) and the
    explicit-offset form (``2026-04-15T13:15:00+00:00``). Naive timestamps
    (no timezone) are interpreted as UTC.
    """
    if not isinstance(ts, str) or not ts:
        return None
    s = ts.strip()
    # Python's fromisoformat doesn't accept the bare 'Z' suffix until 3.11+.
    # Normalise it to '+00:00' for compatibility.
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# ---------------------------------------------------------------------------
# Wilson interval
# ---------------------------------------------------------------------------


def wilson_ci(k: int, n: int, z: float = _WILSON_Z_95) -> tuple[float, float]:
    """Two-sided Wilson score interval.

    Returns ``(lo, hi)`` as proportions in [0, 1]. For ``n == 0`` returns
    ``(0.0, 1.0)`` (maximally uninformative, no information about the
    underlying rate).

    Formula (no continuity correction)::

        center = (p + z^2 / (2n)) / (1 + z^2 / n)
        margin = z * sqrt(p (1-p) / n + z^2 / (4n^2)) / (1 + z^2 / n)

    where ``p = k / n``.
    """
    if n <= 0:
        return (0.0, 1.0)
    if k < 0 or k > n:
        raise ValueError(f"wilson_ci: k={k} out of range [0, {n}]")
    p = k / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    half_width = (
        z * math.sqrt(p * (1.0 - p) / n + z2 / (4.0 * n * n)) / denom
    )
    lo = max(0.0, center - half_width)
    hi = min(1.0, center + half_width)
    # Snap exact boundaries: when k=0 the analytic lo is exactly 0.0; when
    # k=n the analytic hi is exactly 1.0. Floating-point rounding of the
    # algebraic closed form can leave a 1e-16 gap (e.g. 0.9999999999999999
    # for k=n=10). Clamp the closed-form output to the analytic value at
    # the proportion boundaries so downstream consumers can rely on the
    # interval reaching the [0, 1] bounds when k is at the extreme.
    if k == 0:
        lo = 0.0
    if k == n:
        hi = 1.0
    return (lo, hi)


# ---------------------------------------------------------------------------
# Regime index
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _H4Entry:
    """A single H4 row, post-projection."""

    ts: datetime
    regime: str
    source: str  # "v2_direction" | "production_label"


@dataclass
class RegimeIndex:
    """In-memory index of H4 regime tags keyed by symbol.

    Internally stores, per symbol, a list of (ts, _H4Entry) sorted by ts
    so :meth:`lookup` can binary-search the latest tag at-or-before any
    query time.
    """

    #: Per-symbol sorted timestamps (epoch seconds for fast bisect).
    _timestamps: dict[str, list[float]] = field(default_factory=dict)
    #: Per-symbol entries, parallel to ``_timestamps``.
    _entries: dict[str, list[_H4Entry]] = field(default_factory=dict)
    #: Count of structure-log rows ingested (all timeframes).
    rows_total: int = 0
    #: Count of H4 rows accepted into the index.
    h4_rows_indexed: int = 0
    #: Count of H4 rows skipped because ``symbol`` was empty.
    h4_rows_skipped_no_symbol: int = 0
    #: Count of H4 rows skipped because regime selection produced UNTAGGED.
    h4_rows_skipped_no_regime: int = 0

    def lookup(
        self,
        symbol: str,
        when: datetime,
        *,
        freshness_hours: int = DEFAULT_H4_FRESHNESS_HOURS,
    ) -> Optional[_H4Entry]:
        """Return the latest H4 entry with ``ts <= when`` for ``symbol``.

        Returns ``None`` if no such entry exists or the candidate entry
        is older than ``freshness_hours``.
        """
        ts_list = self._timestamps.get(symbol)
        ent_list = self._entries.get(symbol)
        if not ts_list or not ent_list:
            return None
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        when_epoch = when.timestamp()
        # bisect_right gives index just past the last ts <= when_epoch.
        idx = bisect.bisect_right(ts_list, when_epoch)
        if idx == 0:
            return None
        candidate = ent_list[idx - 1]
        age_seconds = when_epoch - candidate.ts.timestamp()
        if age_seconds < 0:
            # No entry at-or-before; defensive (bisect_right shouldn't yield
            # this).
            return None
        if age_seconds > freshness_hours * 3600:
            return None
        return candidate

    def symbols(self) -> list[str]:
        """Sorted list of symbols with at least one H4 row indexed."""
        return sorted(self._timestamps.keys())


def _select_regime(row: dict) -> tuple[Optional[str], str]:
    """Return ``(regime, source_label)`` for a structure-log row.

    Priority: ``v2_direction`` -> ``production_label`` -> None.
    Empty strings, None, and unknown values map to None.
    """
    valid = ("bullish", "bearish", "transitional")
    v2 = row.get("v2_direction")
    if isinstance(v2, str) and v2 in valid:
        return v2, "v2_direction"
    prod = row.get("production_label")
    if isinstance(prod, str) and prod in valid:
        return prod, "production_label"
    return None, "none"


def load_regime_index(structure_log_path: Path | str) -> RegimeIndex:
    """Stream the structure detector log + companions and build a per-symbol H4 index.

    Companion discovery (rotated archives + offline backfill) is delegated
    to :mod:`src.research_infra.structure_log_loader` so A3 + A5 see the
    same row population (memory note ``feedback_engineer_systemic_not_patches``).
    The shared loader walks:

    1. The live ``structure_detector_divergences.jsonl``;
    2. Sibling ``structure_detector_*`` ``.jsonl`` / ``.jsonl.gz`` files
       (older deployments dropped archives next to the live log);
    3. ``research/archive/structure_detector_divergences/`` (canonical
       rotation target);
    4. The offline ``structure_detector_backfill_*.jsonl`` produced by
       ``scripts/research/backfill_v2_regime.py`` covering pre-detector
       H4 boundaries.

    Memory: O(H4 rows). Typical full corpus is 15-20k post-rotation
    plus 3.5k from the backfill — well under 5 MB.

    Parsing failures (malformed JSON / missing fields) are logged at
    DEBUG and skipped — never abort the whole index build because of one
    bad row. A corrupt-gzip companion is logged at WARNING and skipped.

    Notes
    -----
    * Treats a missing seed path as "no live log yet" rather than an
      error: the loader still reaches into the canonical archive dir +
      backfill sibling. A WARNING is emitted iff *no* companions are
      discovered and the seed path itself does not exist.
    * On collisions across files (same ``(symbol, ts)``), the **last**
      file's row wins — matching the A3 "latest write wins" contract.
    """
    path = Path(structure_log_path)
    index = RegimeIndex()

    companions = discover_structure_log_paths(path)
    if not companions:
        if not path.exists():
            logger.warning(
                "regime_matrix: structure log %s not found "
                "(and no companions discovered)",
                path,
            )
        return index

    # Stream rows through the shared loader. We need per-symbol "latest
    # write wins" semantics on (symbol, ts) collisions across rotated
    # files, so we stage into a dict keyed by (symbol, ts_iso) before
    # sorting; the last row to populate the key clobbers earlier ones.
    staged_by_key: dict[tuple[str, str], _H4Entry] = {}

    for row in load_structure_log_rows(path):
        index.rows_total += 1
        if row.get("timeframe") != "H4":
            continue
        symbol = row.get("symbol")
        if not isinstance(symbol, str) or not symbol:
            index.h4_rows_skipped_no_symbol += 1
            continue
        regime, src = _select_regime(row)
        if regime is None:
            index.h4_rows_skipped_no_regime += 1
            continue
        ts_raw = row.get("ts")
        ts = _parse_iso8601_utc(ts_raw if isinstance(ts_raw, str) else None)
        if ts is None:
            continue
        # Latest-write-wins: a later file's row replaces an earlier file's
        # row at the same (symbol, ts). Iteration order through
        # load_structure_log_rows is companion order (live log first by
        # naming convention, then lexicographic).
        key = (symbol, ts.isoformat())
        if key not in staged_by_key:
            index.h4_rows_indexed += 1
        staged_by_key[key] = _H4Entry(ts=ts, regime=regime, source=src)

    # Re-bucket by symbol, sort by ts, and build the parallel epoch list.
    by_symbol: dict[str, list[_H4Entry]] = {}
    for (symbol, _), entry in staged_by_key.items():
        by_symbol.setdefault(symbol, []).append(entry)
    for symbol, entries in by_symbol.items():
        entries.sort(key=lambda e: e.ts)
        index._timestamps[symbol] = [e.ts.timestamp() for e in entries]
        index._entries[symbol] = entries

    return index


# ---------------------------------------------------------------------------
# CAND tagging
# ---------------------------------------------------------------------------


def assign_regime_to_cand(
    cand: dict,
    regime_index: RegimeIndex,
    *,
    freshness_hours: int = DEFAULT_H4_FRESHNESS_HOURS,
) -> str:
    """Return the regime tag for a CAND, or :data:`UNTAGGED`.

    Required CAND fields:
      - ``symbol`` (str) — non-empty
      - ``candle_close_time`` (str) — ISO-8601 UTC. Falls back to
        ``candle_time`` then ``ts``. The first non-empty value parses
        successfully wins; otherwise the result is :data:`UNTAGGED`.
    """
    symbol = cand.get("symbol")
    if not isinstance(symbol, str) or not symbol:
        return UNTAGGED
    when_str: Optional[str] = None
    for key in ("candle_close_time", "candle_time", "ts"):
        v = cand.get(key)
        if isinstance(v, str) and v:
            when_str = v
            break
    if when_str is None:
        return UNTAGGED
    when = _parse_iso8601_utc(when_str)
    if when is None:
        return UNTAGGED
    entry = regime_index.lookup(symbol, when, freshness_hours=freshness_hours)
    if entry is None:
        return UNTAGGED
    return entry.regime


# ---------------------------------------------------------------------------
# Matrix builder
# ---------------------------------------------------------------------------


def _statistics(
    realized_rs: list[float],
) -> dict:
    """Distribution-aware summary stats for a vector of realized R."""
    if not realized_rs:
        return {
            "n": 0,
            "wins": 0,
            "wr": None,
            "exp_r_arith": None,
            "median_r": None,
            "min_r": None,
            "max_r": None,
            "wilson_lo": None,
            "wilson_hi": None,
        }
    n = len(realized_rs)
    wins = sum(1 for r in realized_rs if r > 0)
    sorted_rs = sorted(realized_rs)
    mid = n // 2
    if n % 2 == 1:
        median = sorted_rs[mid]
    else:
        median = 0.5 * (sorted_rs[mid - 1] + sorted_rs[mid])
    lo, hi = wilson_ci(wins, n)
    return {
        "n": n,
        "wins": wins,
        "wr": wins / n,
        "exp_r_arith": sum(realized_rs) / n,
        "median_r": median,
        "min_r": sorted_rs[0],
        "max_r": sorted_rs[-1],
        "wilson_lo": lo,
        "wilson_hi": hi,
    }


@dataclass
class RegimeMatrix:
    """The (instrument, regime) -> stats table.

    The internal storage is a flat ``cells`` dict keyed by ``(instrument,
    regime)`` so callers can iterate / pivot however they like.
    """

    cells: dict[tuple[str, str], dict] = field(default_factory=dict)
    instruments: list[str] = field(default_factory=list)
    regimes: list[str] = field(default_factory=list)
    untagged_count: int = 0
    total_cands: int = 0

    def cell_count(self, instrument: str, regime: str) -> int:
        """Return the number of CANDs in (instrument, regime), 0 if missing."""
        cell = self.cells.get((instrument, regime))
        if cell is None:
            return 0
        return int(cell.get("n", 0))

    def wilson_ci(self, instrument: str, regime: str) -> tuple[float, float] | None:
        """Return Wilson 95% CI for the (instrument, regime) WR, or None."""
        cell = self.cells.get((instrument, regime))
        if cell is None or cell.get("n", 0) == 0:
            return None
        return (cell["wilson_lo"], cell["wilson_hi"])

    def to_dataframe(self):
        """Return a pandas-ready list of dicts (no pandas dependency)."""
        rows = []
        for (instrument, regime), stats in sorted(self.cells.items()):
            row = {"instrument": instrument, "regime": regime}
            row.update(stats)
            row["low_n"] = stats["n"] < LOW_N_THRESHOLD
            rows.append(row)
        return rows

    def summary(self) -> dict:
        """Compact summary suitable for the verdict block."""
        # Average WR per regime across instruments where n>=LOW_N (so a
        # single fat USDJPY cell doesn't drown a regime average).
        regime_avg_wr: dict[str, list[float]] = {}
        regime_n_total: dict[str, int] = {}
        for (instrument, regime), stats in self.cells.items():
            if stats["n"] >= LOW_N_THRESHOLD and stats["wr"] is not None:
                regime_avg_wr.setdefault(regime, []).append(stats["wr"])
            regime_n_total[regime] = (
                regime_n_total.get(regime, 0) + stats["n"]
            )

        averaged = {
            r: (sum(vs) / len(vs)) if vs else None
            for r, vs in regime_avg_wr.items()
        }
        # best / worst — only over regimes with at least one non-LOW_N cell.
        # UNTAGGED is excluded from the ranking because it is a coverage
        # bookkeeping bucket (no H4 row available), not a regime; including
        # it confuses the verdict ("worst regime: UNTAGGED" is not a
        # actionable claim about market structure).
        scored = [
            (r, wr)
            for r, wr in averaged.items()
            if wr is not None and r != UNTAGGED
        ]
        if scored:
            best = max(scored, key=lambda x: x[1])
            worst = min(scored, key=lambda x: x[1])
            delta_pp = (best[1] - worst[1]) * 100.0
        else:
            best = (None, None)
            worst = (None, None)
            delta_pp = None

        return {
            "regime_avg_wr": averaged,
            "regime_total_n": regime_n_total,
            "best_regime": best[0],
            "best_avg_wr": best[1],
            "worst_regime": worst[0],
            "worst_avg_wr": worst[1],
            "wr_delta_pp": delta_pp,
            "untagged_count": self.untagged_count,
            "total_cands": self.total_cands,
            "untagged_fraction": (
                (self.untagged_count / self.total_cands)
                if self.total_cands > 0
                else None
            ),
        }


def build_wr_matrix(
    cands: Iterable[dict],
    regime_index: RegimeIndex,
    *,
    freshness_hours: int = DEFAULT_H4_FRESHNESS_HOURS,
) -> RegimeMatrix:
    """Aggregate a list of CANDs into the (instrument, regime) matrix.

    Each CAND must have:
      - ``symbol`` (str)
      - one of ``candle_close_time`` / ``candle_time`` / ``ts`` (ISO-8601)
      - ``r_multiple`` (float) — realized R for the trade

    CANDs missing ``r_multiple`` are excluded from the matrix entirely
    (they contribute neither to a cell nor to ``total_cands``); this keeps
    the WR/ExpR strictly realized-outcome-based per the task brief.
    """
    by_cell: dict[tuple[str, str], list[float]] = {}
    instruments: set[str] = set()
    regimes: set[str] = set()
    untagged = 0
    total_cands = 0

    for cand in cands:
        r = cand.get("r_multiple")
        if not isinstance(r, (int, float)):
            # Skip CANDs with no realized outcome (e.g. cancelled, still open).
            continue
        symbol = cand.get("symbol")
        if not isinstance(symbol, str) or not symbol:
            continue
        regime = assign_regime_to_cand(
            cand, regime_index, freshness_hours=freshness_hours
        )
        total_cands += 1
        instruments.add(symbol)
        regimes.add(regime)
        if regime == UNTAGGED:
            untagged += 1
        by_cell.setdefault((symbol, regime), []).append(float(r))

    cells: dict[tuple[str, str], dict] = {}
    for cell_key, rs in by_cell.items():
        cells[cell_key] = _statistics(rs)

    return RegimeMatrix(
        cells=cells,
        instruments=sorted(instruments),
        regimes=sorted(regimes),
        untagged_count=untagged,
        total_cands=total_cands,
    )


# ---------------------------------------------------------------------------
# CAND iteration helpers (used by the CLI)
# ---------------------------------------------------------------------------


def iter_cands_from_all_results(
    paths: Iterable[Path],
    *,
    realised_only: bool = True,
) -> Iterator[dict]:
    """Yield CANDs from a list of ``all_results.json`` backtest files.

    Each yielded dict carries the original record fields plus a few
    standardised convenience fields:
      - ``symbol`` filled from the row's ``symbol`` if present, else from
        the file-level ``symbol`` field.
      - ``candle_close_time`` set to the row's ``candle_time``.
      - ``source_file`` set to the basename of the source JSON.

    ``realised_only=True`` skips rows missing a numeric ``r_multiple``.
    """
    for fp in paths:
        try:
            with Path(fp).open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("regime_matrix: cannot read %s: %s", fp, exc)
            continue
        if not isinstance(data, dict):
            continue
        file_symbol = data.get("symbol")
        results = data.get("results")
        if not isinstance(results, list):
            continue
        for row in results:
            if not isinstance(row, dict):
                continue
            if row.get("decision") != "CANDIDATE":
                continue
            if realised_only:
                r = row.get("r_multiple")
                if not isinstance(r, (int, float)):
                    continue
            out = dict(row)
            if not out.get("symbol") and file_symbol:
                out["symbol"] = file_symbol
            ct = out.get("candle_time")
            if ct and "candle_close_time" not in out:
                out["candle_close_time"] = ct
            out["source_file"] = Path(fp).name
            yield out
