"""A3 — Per-Month Per-Session Per-Regime [Per-Side] Stratification.

This module is the data-side companion to ``A6 (Bayesian decay attribution)``:
it slices realized-R outcomes across (month, session, regime[, side]) so a
downstream attribution can ask which combination of axes drove the headline
decay.

The 4th axis (``side``) was added per F2 to pinpoint where LONG selectivity
broke after A6 found that LONG-side decay (LONG WR 48.4% H1 → 18.8% H2) is
the dominant decay driver. A1/A2 callers that don't want the 4th axis can
opt out via ``stratify(..., side_stratified=False)`` — that path produces
exactly the legacy 3-axis (instrument, month, session, regime) output.

Design notes
------------
* **Pure functions; no side effects.** ``assign_session`` / ``assign_regime``
  / ``resolve_side`` / ``stratify`` / ``find_change_points`` all return
  values; the only IO is the optional structure-detector log read inside
  ``assign_regime``.
* **Walk-level evidence is not predictive of realized R** — see memory note
  ``feedback_walk_level_evidence_not_predictive``. The output of
  ``stratify`` is **realized R per stratum**, not gate-pass/reject counts.
* **DST-aware sessions.** Kill-zone windows in ``config/agent_config.yaml``
  are stamped in UTC and do NOT shift across BST/EDT transitions — the
  windows are defined in UTC permanently. This module respects that: a
  London session at 08:00 UTC is a London session whether it's January
  (GMT) or April (BST). DST tests verify the boundary remains stable.
* **Change-point detection.** A consecutive-month transition is flagged as
  a change point when, holding (instrument, session, regime[, side]) fixed,
  the WR shifts by ≥15pp AND both months have n ≥ ``min_n``. Bonferroni
  correction is applied across the family of strata searched.
* **UNTAGGED regime fallback.** Trades whose H4 window has no
  detector-log entry are assigned regime ``UNTAGGED``. The CLI reports the
  fraction so the reader knows the size of the blind spot — A5 will close
  it by recomputing the regime offline against historical bars.
* **UNKNOWN side fallback.** Trades whose ``direction`` field is missing
  AND whose entry/SL prices cannot disambiguate get ``UNKNOWN``. The CLI
  reports the rate as part of coverage.

Schema (canonical)
------------------
Trade dict (input)::

    {
        "candle_close_time": "2026-04-15T13:15:00Z",   # ISO-8601 UTC
        "symbol": "XAUUSD",
        "direction": "LONG"|"SHORT"|None,
        "r_multiple": 1.5 | -1.0 | 0.0,                # realized R
        # optional fallback fields used when direction is missing:
        "entry_price": 2050.0,
        "sl_price": 2040.0,
        ...                                              # extra fields tolerated
    }

Stratum row (output, side-stratified) — one per
``(instrument, month, session, regime, side)``::

    {
        "instrument": "XAUUSD",
        "month": "2026-03",
        "session": "London",
        "regime": "trending_bull",
        "side": "LONG",
        "n": 14,
        "wins": 9,
        "wr": 0.643,
        "exp_r": 0.43,
        "mean_r": 0.43,         # alias for exp_r — kept for downstream readability
        "total_r": 6.0,
        "long_n": 14,           # equals ``n`` when side=LONG, 0 otherwise
        "short_n": 0,
    }

When ``side_stratified=False`` is passed (or the legacy callers leave it
default), the output drops the ``side`` field entirely so the schema
matches the historical 3-axis row exactly. The ``find_change_points``
helper auto-detects which schema it was given.

ChangePoint row (output)::

    {
        "instrument": "XAUUSD",
        "session": "London",
        "regime": "trending_bull",
        "side": "LONG",        # only present in side-stratified mode
        "month_before": "2026-02",
        "month_after": "2026-03",
        "wr_before": 0.65,
        "wr_after": 0.20,
        "delta_pp": -45.0,
        "n_before": 20,
        "n_after": 15,
        "raw_p": 0.003,
        "bonf_p": 0.024,        # Bonferroni-corrected over the strata family
        "family_size": 8,       # number of strata searched
    }
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any, Iterable, Literal, Optional, Sequence

from src.research_infra.structure_log_loader import (
    build_h4_regime_index,
    discover_structure_log_paths,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

SessionLabel = Literal["Asia", "London", "NY", "Off"]

# Side labels. ``AGGREGATE`` is the sentinel used by the legacy 3-axis schema
# so a 3-axis stratum has a non-None ``side`` slot in the dataclass without
# leaking into the serialized row. ``UNKNOWN`` surfaces when the input trade
# has no ``direction`` and entry/SL price disambiguation also fails.
SideLabel = Literal["LONG", "SHORT", "UNKNOWN", "AGGREGATE"]

# Brief regime labels (normalized from the production regime classifier output).
# The structure-detector shadow log writes "bullish" / "bearish" / "transitional"
# / "insufficient_data" — those map to:
#   bullish      -> trending_bull
#   bearish      -> trending_bear
#   transitional -> range
#   insufficient_data -> UNTAGGED
# The pragmatic regime classifier (src/components/regime_classifier.py) also
# emits "chop" / "reversal_in_progress" / "unclear":
#   chop                  -> range
#   reversal_in_progress  -> reversal
#   unclear               -> UNTAGGED
RegimeLabel = Literal[
    "trending_bull",
    "trending_bear",
    "range",
    "reversal",
    "unclear",
    "UNTAGGED",
]

# Default kill-zone schedule mirroring config/agent_config.yaml. Used as a
# fallback when no config dict is passed (mostly tests). The CLI loads the
# real YAML via PyYAML.
DEFAULT_KILL_ZONES: dict[str, dict[str, dict[str, str]]] = {
    "XAUUSD": {
        "london": {"start_utc": "07:00", "end_utc": "10:30"},
        "ny": {"start_utc": "13:00", "end_utc": "17:00"},
    },
    "US30_cash": {
        "london": {"start_utc": "08:00", "end_utc": "10:30"},
        "ny": {"start_utc": "13:30", "end_utc": "16:00"},
    },
    "USDJPY": {
        "tokyo": {"start_utc": "00:00", "end_utc": "03:00"},
        "london": {"start_utc": "07:00", "end_utc": "09:30"},
        "ny": {"start_utc": "13:00", "end_utc": "15:30"},
    },
    "GBPJPY": {
        "tokyo": {"start_utc": "00:00", "end_utc": "03:00"},
        "london": {"start_utc": "07:00", "end_utc": "09:30"},
        "ny": {"start_utc": "13:00", "end_utc": "15:30"},
    },
    "GBPUSD": {
        "london": {"start_utc": "07:00", "end_utc": "12:00"},
        "ny": {"start_utc": "13:00", "end_utc": "15:30"},
    },
    "EURUSD": {
        "london": {"start_utc": "07:00", "end_utc": "12:00"},
    },
    "XAGUSD": {
        "ny": {"start_utc": "13:00", "end_utc": "17:00"},
    },
    "NAS100": {
        "ny": {"start_utc": "13:00", "end_utc": "17:00"},
    },
    "UK100": {
        "london": {"start_utc": "08:00", "end_utc": "12:00"},
        "ny": {"start_utc": "14:00", "end_utc": "19:00"},
    },
    "GER40": {
        "london": {"start_utc": "08:00", "end_utc": "12:00"},
        "ny": {"start_utc": "14:00", "end_utc": "19:00"},
    },
}


@dataclass(frozen=True)
class StratumKey:
    """Composite key for a (instrument, month, session, regime[, side]) stratum.

    ``side`` defaults to ``"AGGREGATE"`` to preserve the legacy 3-axis
    behaviour; pass ``"LONG"`` / ``"SHORT"`` / ``"UNKNOWN"`` to use the F2
    4th axis. The serializer (``to_row``) honours the
    ``side_stratified`` flag on the owning ``StratumOutcomes`` row so that
    AGGREGATE keys never leak the field into JSON.
    """

    instrument: str
    month: str  # "YYYY-MM"
    session: str  # "Asia"|"London"|"NY"|"Off"
    regime: str  # RegimeLabel
    side: str = "AGGREGATE"  # SideLabel — AGGREGATE in legacy 3-axis mode

    def as_tuple(self) -> tuple[str, str, str, str]:
        """Legacy 4-tuple used by callers that want the 3-axis identity.

        Side is intentionally dropped — the helper exists so existing test
        assertions like ``("XAUUSD", "2026-01", "NY", "trending_bull") in keys``
        keep working unchanged.
        """
        return (self.instrument, self.month, self.session, self.regime)

    def as_full_tuple(self) -> tuple[str, str, str, str, str]:
        """5-tuple including ``side`` — for side-stratified callers."""
        return (
            self.instrument,
            self.month,
            self.session,
            self.regime,
            self.side,
        )


@dataclass
class StratumOutcomes:
    """Realized-R outcomes for a single stratum."""

    key: StratumKey
    r_values: list[float] = field(default_factory=list)
    long_n: int = 0
    short_n: int = 0
    # When True, the row serializer emits the ``side`` column. When False
    # (legacy 3-axis), it is suppressed so existing downstream consumers see
    # the original schema unchanged.
    side_stratified: bool = False

    @property
    def n(self) -> int:
        return len(self.r_values)

    @property
    def wins(self) -> int:
        return sum(1 for r in self.r_values if r > 0)

    @property
    def wr(self) -> float:
        return self.wins / self.n if self.n else 0.0

    @property
    def exp_r(self) -> float:
        return sum(self.r_values) / self.n if self.n else 0.0

    @property
    def total_r(self) -> float:
        return sum(self.r_values)

    def to_row(self) -> dict[str, Any]:
        """Serialize to the stratum row schema."""
        row: dict[str, Any] = {
            "instrument": self.key.instrument,
            "month": self.key.month,
            "session": self.key.session,
            "regime": self.key.regime,
            "n": self.n,
            "wins": self.wins,
            "wr": self.wr,
            "exp_r": self.exp_r,
            "mean_r": self.exp_r,
            "total_r": self.total_r,
            "long_n": self.long_n,
            "short_n": self.short_n,
        }
        if self.side_stratified:
            row["side"] = self.key.side
        return row


# Public type alias used by the brief: dict keyed by composite key -> outcomes.
StratifiedOutcomes = dict[StratumKey, StratumOutcomes]


@dataclass(frozen=True)
class ChangePoint:
    """A month-over-month WR shift within a (instrument, session, regime[, side]).

    ``side`` defaults to ``"AGGREGATE"`` for legacy 3-axis change points; in
    side-stratified mode it carries one of ``LONG`` / ``SHORT`` / ``UNKNOWN``.
    The ``to_row`` serializer drops the field when it is AGGREGATE so the
    legacy schema stays bit-identical.
    """

    instrument: str
    session: str
    regime: str
    month_before: str
    month_after: str
    wr_before: float
    wr_after: float
    delta_pp: float  # signed, in percentage points
    n_before: int
    n_after: int
    raw_p: float
    bonf_p: float
    family_size: int
    side: str = "AGGREGATE"

    def to_row(self) -> dict[str, Any]:
        row: dict[str, Any] = {
            "instrument": self.instrument,
            "session": self.session,
            "regime": self.regime,
            "month_before": self.month_before,
            "month_after": self.month_after,
            "wr_before": self.wr_before,
            "wr_after": self.wr_after,
            "delta_pp": self.delta_pp,
            "n_before": self.n_before,
            "n_after": self.n_after,
            "raw_p": self.raw_p,
            "bonf_p": self.bonf_p,
            "family_size": self.family_size,
        }
        if self.side != "AGGREGATE":
            row["side"] = self.side
        return row


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------


def _coerce_to_utc(ts: Any) -> datetime:
    """Accept str or datetime; return a timezone-aware UTC ``datetime``.

    Strings ending in ``Z`` are interpreted as UTC. Strings missing a
    timezone offset are treated as UTC and a debug message is logged
    (the system's canonical timestamps are always UTC).
    """
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    if not isinstance(ts, str):
        raise TypeError(f"timestamp must be datetime or str, got {type(ts).__name__}")
    s = ts.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError as e:
        raise ValueError(f"could not parse ISO-8601 timestamp {ts!r}") from e
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_hhmm(s: str) -> time:
    """Parse ``HH:MM`` into a ``datetime.time``. Raises ValueError on bad input."""
    parts = s.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"expected HH:MM, got {s!r}")
    return time(hour=int(parts[0]), minute=int(parts[1]))


def _floor_h4_utc(ts: datetime) -> datetime:
    """Floor a UTC timestamp to the start of its 4-hour bucket.

    H4 candles open at 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC.
    Used by ``assign_regime`` to map a per-trade timestamp to its enclosing
    H4 window.
    """
    ts = ts.astimezone(timezone.utc)
    bucket_hour = (ts.hour // 4) * 4
    return ts.replace(hour=bucket_hour, minute=0, second=0, microsecond=0)


# ---------------------------------------------------------------------------
# assign_session
# ---------------------------------------------------------------------------


def assign_session(
    timestamp: Any,
    instrument: str,
    kill_zones_config: Optional[dict] = None,
) -> SessionLabel:
    """Classify a timestamp into Asia / London / NY / Off-hours.

    The classification is **strictly UTC**. ``kill_zones_config`` mirrors
    the per-instrument ``market.kill_zones`` block from
    ``config/agent_config.yaml``. When None, ``DEFAULT_KILL_ZONES`` is used.

    Mapping
    -------
    * ``tokyo`` → "Asia"
    * ``london`` → "London"
    * ``ny`` → "NY"
    * anything else → "Off"

    Window semantics
    ----------------
    Inclusive on the lower bound, exclusive on the upper bound. A trade
    stamped exactly at the kill-zone end is OFF. This matches the
    production permissions gate (``permissions.py`` rejects new orders
    once the candle close time is at-or-after the configured ``end_utc``).

    DST
    ---
    The kill-zone windows are stamped in UTC permanently — they do NOT
    shift across BST/EDT transitions. The London open is at 07:00 UTC
    in January and 07:00 UTC in April even though local clock-time
    perception of "London open" rotates by an hour. This is consistent
    with the configuration in ``config/agent_config.yaml``.

    Weekends
    --------
    A Saturday or Sunday timestamp inside a kill-zone window is still
    classified as that session — there are no live trades on weekends
    (MT5 closes), so any such row in the input is presumably synthetic
    or a backtest artifact and the caller is expected to filter. We do
    not silently drop rows here.
    """
    dt = _coerce_to_utc(timestamp)
    if not isinstance(instrument, str) or not instrument:
        raise ValueError("instrument must be a non-empty string")
    cfg = (kill_zones_config or DEFAULT_KILL_ZONES).get(instrument, {})
    if not cfg:
        # Unknown instrument: be conservative — Off.
        return "Off"

    t_now = dt.time()

    for zone_name, window in cfg.items():
        try:
            start = _parse_hhmm(window["start_utc"])
            end = _parse_hhmm(window["end_utc"])
        except (KeyError, ValueError) as e:
            logger.warning(
                "assign_session: malformed kill-zone window for %s/%s: %s",
                instrument,
                zone_name,
                e,
            )
            continue

        if start <= end:
            in_window = start <= t_now < end
        else:
            # Window straddles UTC midnight (rare; e.g. NZDUSD tokyo 22:00→02:00).
            in_window = t_now >= start or t_now < end

        if not in_window:
            continue

        zn = zone_name.lower()
        if zn in ("tokyo", "asia", "asian"):
            return "Asia"
        if zn == "london":
            return "London"
        if zn == "ny":
            return "NY"
        # Unknown name — log once and treat as Off so we don't silently
        # invent a new bucket downstream.
        logger.warning(
            "assign_session: unknown kill-zone name %r for %s; treating as Off",
            zone_name,
            instrument,
        )
        return "Off"

    return "Off"


# ---------------------------------------------------------------------------
# assign_regime
# ---------------------------------------------------------------------------


def _normalize_regime_label(raw: Optional[str]) -> str:
    """Map raw detector / classifier output to one of the brief's 5 labels.

    Brief labels: range / trending_bull / trending_bear / reversal / unclear.
    Returns ``UNTAGGED`` when the raw value is missing / empty.
    """
    if raw is None:
        return "UNTAGGED"
    s = str(raw).strip().lower()
    if not s:
        return "UNTAGGED"
    # Structure detector emits bullish/bearish/transitional/insufficient_data.
    if s in ("bullish", "trending_bull", "bull"):
        return "trending_bull"
    if s in ("bearish", "trending_bear", "bear"):
        return "trending_bear"
    if s in ("range", "ranging", "chop", "transitional"):
        return "range"
    if s in ("reversal", "reversal_in_progress"):
        return "reversal"
    if s in ("unclear", "insufficient_data"):
        return "unclear"
    # Unknown raw label — surface as UNTAGGED so it shows up in coverage stats
    # rather than being silently discarded into a wrong bucket.
    return "UNTAGGED"


# Loader logic lives in :mod:`src.research_infra.structure_log_loader` —
# A3 + A5 share the same discover-companions + parse + cache pipeline so
# a future rotation/backfill change doesn't have to be applied twice.
# This module imports :func:`build_h4_regime_index` and exposes a thin
# wrapper for the legacy ``_load_structure_log`` name to preserve
# backward compatibility for any downstream test that imported it.


def _load_structure_log(
    path: Path,
) -> dict[tuple[str, str, str], str]:
    """Backward-compatible wrapper around the shared H4 regime index.

    Delegates to :func:`structure_log_loader.build_h4_regime_index`; see
    that function's docstring for the discovery rules + cache contract.
    Kept under its original name so any downstream test or research
    script that imported the private helper continues to work.
    """
    return build_h4_regime_index(path)


def assign_regime(
    timestamp: Any,
    instrument: str,
    structure_log_path: Optional[Path],
) -> str:
    """Look up the regime label for the H4 window containing ``timestamp``.

    Returns one of:
    * ``trending_bull`` / ``trending_bear`` — directional H4 structure
    * ``range`` — H4 transitional / chop
    * ``reversal`` — recent counter-direction H4 BOS
    * ``unclear`` — insufficient H4 swings to classify
    * ``UNTAGGED`` — no detector-log entry for this window (blind spot)

    The lookup floors ``timestamp`` to the start of the enclosing H4
    window (00/04/08/12/16/20 UTC) and queries the log for
    ``(instrument, "H4", h4_ts)``. Missing → UNTAGGED.

    Notes
    -----
    * The shadow log does NOT log every H4 window — only V1↔V2
      divergences. So this lookup misses agreement-rows by design;
      A5 (the "fill the regime gap" task) is responsible for closing
      that hole by recomputing the regime offline against historical
      bars. Until then, the UNTAGGED rate is the size of the blind
      spot and the CLI surfaces it.
    * If ``structure_log_path`` is None, the function returns
      ``UNTAGGED`` for every call without raising — useful for unit
      tests that don't want to depend on log availability.
    """
    if structure_log_path is None:
        return "UNTAGGED"
    dt = _coerce_to_utc(timestamp)
    h4_floor = _floor_h4_utc(dt)
    ts_key = h4_floor.isoformat().replace("+00:00", "Z")
    log_map = _load_structure_log(structure_log_path)
    return log_map.get((instrument, "H4", ts_key), "UNTAGGED")


# ---------------------------------------------------------------------------
# stratify
# ---------------------------------------------------------------------------


def _trade_timestamp(t: dict[str, Any]) -> Optional[datetime]:
    """Return the trade's UTC timestamp from ``candle_close_time`` /
    ``candle_time`` / ``timestamp_utc`` / ``ts`` in that priority order."""
    for key in ("candle_close_time", "candle_time", "timestamp_utc", "ts"):
        if key in t and t[key] is not None:
            try:
                return _coerce_to_utc(t[key])
            except (TypeError, ValueError):
                continue
    return None


def resolve_side(t: dict[str, Any]) -> str:
    """Resolve a trade's side as one of ``LONG`` / ``SHORT`` / ``UNKNOWN``.

    Resolution order
    ----------------
    1. Explicit ``direction`` field — case-insensitive match against
       ``LONG`` / ``SHORT`` / ``BUY`` / ``SELL``. ``BUY``→LONG, ``SELL``→SHORT
       (some loaders, e.g. unified_csv via FTMO export, use the broker-side
       verb).
    2. Entry-vs-SL inference — when ``direction`` is missing or unparseable,
       compare ``entry_price`` (or ``open_price``) against ``sl_price``
       (or ``stop_loss``):

       * ``entry_price > sl_price`` → LONG
       * ``entry_price < sl_price`` → SHORT
       * equal / either missing → UNKNOWN

    3. Otherwise → ``UNKNOWN``. The CLI surfaces the UNKNOWN rate as part
       of coverage so a reader knows the size of the side blind spot.

    Notes
    -----
    * NaN-prices fall through to UNKNOWN — we deliberately do not raise.
    * The fallback inference is realized-R-correct even on filled trades
      because the entry price and SL are the order's planted endpoints; a
      LONG always plants SL below entry (and vice-versa).
    """
    direction = t.get("direction")
    if isinstance(direction, str):
        d = direction.strip().upper()
        if d in ("LONG", "BUY"):
            return "LONG"
        if d in ("SHORT", "SELL"):
            return "SHORT"
        # Anything non-empty that isn't a recognized side falls through to
        # the price-based inference rather than hard-erroring.

    # Inference fallback. Try a few common field name pairs.
    for entry_key, sl_key in (
        ("entry_price", "sl_price"),
        ("open_price", "sl_price"),
        ("entry_price", "stop_loss"),
        ("open_price", "stop_loss"),
        ("entry", "sl"),
    ):
        entry = t.get(entry_key)
        sl = t.get(sl_key)
        if entry is None or sl is None:
            continue
        try:
            ef = float(entry)
            sf = float(sl)
        except (TypeError, ValueError):
            continue
        # Reject NaN.
        if ef != ef or sf != sf:
            continue
        if ef > sf:
            return "LONG"
        if ef < sf:
            return "SHORT"
        # Equal: indeterminate.
        continue

    return "UNKNOWN"


def stratify(
    trades: Sequence[dict[str, Any]],
    instrument: str,
    *,
    kill_zones_config: Optional[dict] = None,
    structure_log_path: Optional[Path] = None,
    side_stratified: bool = False,
) -> StratifiedOutcomes:
    """Group realized-R outcomes by (instrument, month, session, regime[, side]).

    Parameters
    ----------
    trades:
        Sequence of trade dicts. Each must carry one of
        ``candle_close_time`` / ``candle_time`` / ``timestamp_utc`` / ``ts``
        plus ``symbol`` / ``r_multiple`` / ``direction``. Trades whose
        ``symbol`` differs from ``instrument`` are skipped.
    instrument:
        Filter — only trades for this symbol are included in the output.
    kill_zones_config:
        Optional override of the per-instrument kill-zone schedule. When
        None, ``DEFAULT_KILL_ZONES`` is used.
    structure_log_path:
        Optional path to ``shadow_logs/structure_detector_divergences.jsonl``
        (or its archived equivalent). When provided, the regime label is
        looked up from the log; otherwise every stratum is ``UNTAGGED``.
    side_stratified:
        When True, the 4th axis ``side`` (LONG/SHORT/UNKNOWN) is included
        in the stratum key + serialized row. When False (default), the
        legacy 3-axis schema is preserved bit-identical so existing
        downstream consumers (A1 / A2 / A6 backwards-compat callers) see
        no change.

    Returns
    -------
    Dict mapping ``StratumKey`` → ``StratumOutcomes``. Strata with zero
    trades are omitted (call ``find_change_points`` to consume).
    """
    out: StratifiedOutcomes = {}

    for t in trades:
        sym = t.get("symbol")
        if sym != instrument:
            continue
        ts = _trade_timestamp(t)
        if ts is None:
            continue
        r = t.get("r_multiple")
        if r is None:
            continue
        try:
            r_val = float(r)
        except (TypeError, ValueError):
            continue

        month = f"{ts.year:04d}-{ts.month:02d}"
        session = assign_session(ts, instrument, kill_zones_config)
        regime = assign_regime(ts, instrument, structure_log_path)
        # Side resolution always runs — we still need long_n / short_n
        # counts on the legacy 3-axis row for the existing schema.
        side = resolve_side(t)

        key_side = side if side_stratified else "AGGREGATE"
        key = StratumKey(
            instrument=instrument,
            month=month,
            session=session,
            regime=regime,
            side=key_side,
        )
        bucket = out.setdefault(
            key,
            StratumOutcomes(key=key, side_stratified=side_stratified),
        )
        bucket.r_values.append(r_val)
        if side == "LONG":
            bucket.long_n += 1
        elif side == "SHORT":
            bucket.short_n += 1
        # UNKNOWN doesn't increment either counter — it is reflected in
        # n - long_n - short_n on the row.

    return out


# ---------------------------------------------------------------------------
# find_change_points
# ---------------------------------------------------------------------------


def _two_proportion_p_value(wins_a: int, n_a: int, wins_b: int, n_b: int) -> float:
    """Two-sided two-proportion z-test p-value via the standard pooled formula.

    Returns 1.0 in degenerate cases (n_a or n_b == 0; identical pooled
    proportion of 0 or 1 with no variance) so the change point is flagged
    by the WR-shift criterion alone — no spurious low p-value.

    We deliberately implement this in pure Python (no scipy) so the
    research_infra package stays dependency-light. The normal-CDF
    approximation uses ``math.erfc`` which is fine for the precision we
    need here (Bonferroni-corrected significance at the 0.05 level).
    """
    import math

    if n_a <= 0 or n_b <= 0:
        return 1.0
    p_a = wins_a / n_a
    p_b = wins_b / n_b
    p_pool = (wins_a + wins_b) / (n_a + n_b)
    var = p_pool * (1.0 - p_pool) * (1.0 / n_a + 1.0 / n_b)
    if var <= 0:
        return 1.0
    z = (p_b - p_a) / math.sqrt(var)
    # Two-sided: 2 * (1 - Phi(|z|)) using erfc:
    #   1 - Phi(x) = 0.5 * erfc(x / sqrt(2))
    return float(math.erfc(abs(z) / math.sqrt(2.0)))


def find_change_points(
    stratified: StratifiedOutcomes,
    min_n: int = 10,
    *,
    delta_pp_threshold: float = 15.0,
) -> list[ChangePoint]:
    """Detect month-over-month WR shifts within (instrument, session, regime[, side]).

    A change point is flagged when:

    1. ``|wr_after - wr_before| >= delta_pp_threshold / 100`` (default 15pp)
    2. ``n_before >= min_n`` AND ``n_after >= min_n``
    3. Months are *consecutive* in the calendar (e.g. 2026-02 → 2026-03).

    Side handling
    -------------
    The function auto-detects whether the input was produced with
    ``side_stratified=True`` by checking whether any key carries a
    non-``AGGREGATE`` side. When side-stratified, change points are
    detected **within** a side (i.e. each (instrument, session, regime,
    side) family is its own sequence) — a LONG-only decay in NY trending
    will surface independently of any SHORT cohort in the same cell.
    When non-stratified (legacy), side is ignored and the family is
    (instrument, session, regime) as before.

    Bonferroni correction is applied across the full family of strata
    that contain at least one transition pair. ``family_size`` is
    recorded on each output row so a reader can verify the correction.

    Parameters
    ----------
    stratified:
        Output of :func:`stratify`.
    min_n:
        Minimum sample size on each side of the transition. Default 10
        (the brief's spec). Below this we never flag — the noise
        floor on a small-n WR is too high to call a "change".
    delta_pp_threshold:
        Minimum signed WR shift in *percentage points*. Default 15pp.

    Returns
    -------
    Sorted list of :class:`ChangePoint` rows, descending by
    ``|delta_pp|`` then ascending by ``bonf_p``.
    """
    # Auto-detect mode: if any key carries a real side label (LONG/SHORT/
    # UNKNOWN) we run side-stratified change detection; otherwise legacy
    # 3-axis. We deliberately check for non-AGGREGATE rather than the
    # presence of a side attribute because the dataclass always has the
    # field (with default AGGREGATE) so plain ``hasattr`` is useless.
    side_mode = any(
        key.side != "AGGREGATE" for key in stratified.keys()
    )

    # Group by (instrument, session, regime[, side]) for sequencing.
    GroupKey = tuple
    by_family: dict[GroupKey, list[StratumOutcomes]] = {}
    for key, bucket in stratified.items():
        if side_mode:
            family_key: GroupKey = (
                key.instrument,
                key.session,
                key.regime,
                key.side,
            )
        else:
            family_key = (key.instrument, key.session, key.regime)
        by_family.setdefault(family_key, []).append(bucket)

    # First pass: count the number of families with ≥ 2 strata and any
    # consecutive-month transition with both sides ≥ min_n + delta gate.
    # This is the family size for the Bonferroni correction. We exclude
    # families with no eligible transitions to avoid over-correcting.
    transitions: list[tuple[StratumOutcomes, StratumOutcomes]] = []
    for buckets in by_family.values():
        # Sort by month string ascending; "YYYY-MM" sorts lexicographically
        # in calendar order.
        buckets_sorted = sorted(buckets, key=lambda b: b.key.month)
        for prev, cur in zip(buckets_sorted, buckets_sorted[1:]):
            if not _months_consecutive(prev.key.month, cur.key.month):
                continue
            if prev.n < min_n or cur.n < min_n:
                continue
            if abs(cur.wr - prev.wr) * 100.0 < delta_pp_threshold:
                continue
            transitions.append((prev, cur))

    family_size = max(1, len(transitions))

    out: list[ChangePoint] = []
    for prev, cur in transitions:
        raw_p = _two_proportion_p_value(
            prev.wins, prev.n, cur.wins, cur.n
        )
        bonf_p = min(1.0, raw_p * family_size)
        # Side is taken from the bucket's key (always present, defaults to
        # AGGREGATE). The ChangePoint serializer drops it when AGGREGATE.
        out.append(
            ChangePoint(
                instrument=prev.key.instrument,
                session=prev.key.session,
                regime=prev.key.regime,
                month_before=prev.key.month,
                month_after=cur.key.month,
                wr_before=prev.wr,
                wr_after=cur.wr,
                delta_pp=(cur.wr - prev.wr) * 100.0,
                n_before=prev.n,
                n_after=cur.n,
                raw_p=raw_p,
                bonf_p=bonf_p,
                family_size=family_size,
                side=prev.key.side,
            )
        )

    out.sort(key=lambda cp: (-abs(cp.delta_pp), cp.bonf_p))
    return out


def _months_consecutive(month_a: str, month_b: str) -> bool:
    """True iff ``month_b`` is the month immediately after ``month_a``.

    Both strings must be ``YYYY-MM``.
    """
    try:
        ya, ma = (int(x) for x in month_a.split("-"))
        yb, mb = (int(x) for x in month_b.split("-"))
    except (ValueError, AttributeError):
        return False
    a_idx = ya * 12 + (ma - 1)
    b_idx = yb * 12 + (mb - 1)
    return b_idx - a_idx == 1


# ---------------------------------------------------------------------------
# Reporting helpers (used by the CLI; importable for ad-hoc analysis)
# ---------------------------------------------------------------------------


def coverage_summary(stratified: StratifiedOutcomes, min_n: int = 10) -> dict[str, Any]:
    """Compute coverage metrics for the report header.

    Returns ``{total_strata, strata_ge_min_n, total_trades,
    untagged_trades, untagged_pct, unknown_side_trades, unknown_side_pct,
    instruments, months, sessions, regimes, sides}``.

    The side-coverage fields are present unconditionally (they are zero
    when no UNKNOWN-side trades made it into the strata) so downstream
    consumers don't need a mode flag.
    """
    total_strata = len(stratified)
    strata_ge_min_n = sum(1 for b in stratified.values() if b.n >= min_n)
    total_trades = sum(b.n for b in stratified.values())
    untagged_trades = sum(
        b.n for k, b in stratified.items() if k.regime == "UNTAGGED"
    )
    untagged_pct = (untagged_trades / total_trades * 100.0) if total_trades else 0.0
    # Side coverage. In side-stratified mode, ``UNKNOWN`` is its own
    # stratum row. In legacy mode, the per-row UNKNOWN count is
    # ``n - long_n - short_n``.
    unknown_side_trades = 0
    for k, b in stratified.items():
        if k.side == "UNKNOWN":
            unknown_side_trades += b.n
        elif k.side == "AGGREGATE":
            unknown_side_trades += max(0, b.n - b.long_n - b.short_n)
    unknown_side_pct = (
        unknown_side_trades / total_trades * 100.0 if total_trades else 0.0
    )
    instruments = sorted({k.instrument for k in stratified})
    months = sorted({k.month for k in stratified})
    sessions = sorted({k.session for k in stratified})
    regimes = sorted({k.regime for k in stratified})
    sides = sorted({k.side for k in stratified})
    return {
        "total_strata": total_strata,
        "strata_ge_min_n": strata_ge_min_n,
        "total_trades": total_trades,
        "untagged_trades": untagged_trades,
        "untagged_pct": untagged_pct,
        "unknown_side_trades": unknown_side_trades,
        "unknown_side_pct": unknown_side_pct,
        "instruments": instruments,
        "months": months,
        "sessions": sessions,
        "regimes": regimes,
        "sides": sides,
    }


def stratified_to_rows(stratified: StratifiedOutcomes) -> list[dict[str, Any]]:
    """Sorted list of ``StratumOutcomes.to_row()`` dicts for serialization.

    Sort order: instrument → month → session → regime → side. Side is the
    last sort key so legacy 3-axis output (where every row's side is
    AGGREGATE) is unaffected.
    """
    rows = [b.to_row() for b in stratified.values()]
    rows.sort(
        key=lambda r: (
            r["instrument"],
            r["month"],
            r["session"],
            r["regime"],
            r.get("side", ""),
        )
    )
    return rows
