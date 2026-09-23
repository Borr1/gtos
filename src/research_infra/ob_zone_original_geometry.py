"""F11 — OB-zone advantage re-test with the ORIGINAL Test A geometry.

Why this exists
===============
F4 (commit ``48395e2``,
`research/edge_decomposition/F4_ob_zone_fresh_test_a/`) re-extracted BOS
events fresh from H1 OHLCV on the 2026-01-01 → 2026-04-24 window and
re-ran the OB-retest vs generic-pullback comparison. Verdict on H2-2026
was ``DECAYED_FRESH`` with delta = +0.9pp (corrected p = 1.0, n=480).
That is strikingly different from the original Test A's +17pp finding
(`.context/03_analysis/test_a_rerun_real_bos_results.md`, n=219, Fisher
p = 0.003).

But F4 changed two things at once relative to the original Test A:

1. **Baseline geometry**: F4 used the 50% Fibonacci retracement of the
   ``anchor_swing → bos_close`` impulse. The original Test A used an
   "80% retrace" baseline where 80% means 80% of the impulse range from
   the impulse origin (i.e. 20% of the way from anchor to BOS close —
   a DEEP pullback close to the swing-low / swing-high anchor). The
   original baseline sits much closer to the OB zone than the F4
   baseline; this is the geometry that produced the +17pp result.
2. **Statistical test**: F4 used a two-proportion pooled-z test for
   direct K52 comparability. The original Test A used a Fisher exact
   test (``test_a_rerun_real_bos_results.md`` Q2 row).

The open strategic question is: was F4's ``DECAYED_FRESH`` verdict
driven by genuine decay of the OB-zone advantage on H2-2026 data
(interpretation A), or by methodology drift away from the original
Test A's deeper baseline + Fisher test (interpretation B)?

F11 disambiguates. We re-run F4's analysis on F4's exact same fresh
population, but with:

1. The ORIGINAL Test A "80% impulse retrace" baseline (entry =
   ``anchor + 0.20 × impulse_range``, conservative SL beyond anchor).
2. BOTH Fisher exact AND pooled-z reported for cross-method sanity.

Hard rules
==========
* **No AI / Anthropic API calls.** Phase 1 = $0.
* **Read-only inputs.** ``data/historical_2026/`` and F4's saved
  population are read-only. Outputs go to a caller-supplied directory.
* **No production-code dependencies.** Mirrors F4's structural rule —
  re-uses ``ob_zone_test.extract_bos_events`` only.
* **Reuses F4's BOS extraction + dumb_baseline outcome resolver.**
  Identical M15 walk-forward semantics; only the entry/SL/TP geometry
  on the BASELINE arm differs from F4. The OB-retest arm is
  bit-for-bit identical to F4 (we re-use ``find_ob_retest_outcome``).
* **Never fabricate.** When entry / SL / TP cannot be priced
  (degenerate impulse, zero range, etc.), record the row with
  ``skip_reason`` and exclude from rate aggregations.
* **Paired population.** F11 operates on the SAME BOS event set as F4.
  By default, BOS events are loaded from F4's
  ``research/edge_decomposition/F4_ob_zone_fresh_test_a/population.jsonl``
  if available; otherwise re-extracted with the SAME parameters via
  ``extract_bos_events``.

Methodology — original-geometry pullback entry (80%-of-impulse-range)
======================================================================
For each BOS event in direction D:
  - Identify the impulse: ``impulse_range = bos_close - anchor_price``
    (positive for LONG, negative for SHORT).
  - For LONG: entry = ``anchor + (1 - 0.80) × impulse_range = anchor
    + 0.20 × impulse_range`` — i.e. 80% retracement back from BOS
    close toward the anchor swing low (a DEEP pullback, close to the
    impulse origin).
  - For SHORT: entry = ``anchor + (1 - 0.80) × impulse_range``
    (signed; impulse_range < 0 → entry < anchor by 20% of |range|).
  - SL = beyond the anchor swing extreme by the canonical buffer:
    ``max(0.25 × ATR_14, 5 × tick_size)`` (matches A1 dumb_baseline
    + F4 OB-retest defaults).
  - TP = ``entry ± 1.5 × |entry - SL|`` (min_rr floor).

The "80% retrace" framing in original Test A is anchored at the
impulse ORIGIN — a 95% retrace is DEEPER (closer to anchor) than an
80% retrace, which is DEEPER than a 50% retrace. F4's "50% Fibonacci"
sits at the midpoint and is SHALLOWER than the original baseline.
Mathematical equivalence:

  - 80%-retrace-from-origin (original Test A) → entry at 20% of range
    above anchor for LONG → "20% Fibonacci retracement" in modern SMC
    parlance (where 0% = swing high, 100% = swing low).
  - F4's "50% Fibonacci of swing → BOS close" → entry at 50% of range
    above anchor for LONG → mid-impulse.

F11's geometry restores the 20%-above-anchor entry the original test
used — substantially closer to where the OB zone sits in most BOS
patterns, hence a stricter test of the OB-zone advantage.

Statistical tests
=================
Both reported on the same paired counts:

1. **Fisher exact** (matches original Test A Q2 row) — exact two-tailed
   p-value via hypergeometric tail sums. Pure-Python (no scipy)
   implementation using ``math.lgamma`` for combinatorial logs.
2. **Pooled-variance two-proportion z-test** (matches K52 + F4) for
   direct cross-table comparability.

Both raw and Bonferroni-corrected p-values are reported for each test
(family size matches K52's canonical 5).

Verdict format
==============
F11's ``verdict`` field for each period is one of:
  - ``CONFIRMED`` — F11 (original geometry) on H2-2026 reports
    delta_pp ≥ +5pp AND corrected_p < 0.05 under EITHER test (close
    to the original +17pp result). Implies F4's DECAYED_FRESH was a
    methodology artefact.
  - ``METHODOLOGY_DRIFT`` — F11 (original geometry) on H2-2026 still
    reports |delta_pp| < 5pp AND corrected_p ≥ 0.05 under both tests
    (close to F4's +0.9pp result). Implies F4's DECAYED_FRESH is
    real decay; the methodology change did NOT explain the gap.
  - ``PARTIAL`` — F11 (original geometry) sits between the F4 result
    and the original Test A result (delta_pp between +5pp and +12pp,
    or significant under one test but not both). Implies BOTH effects
    contribute.
  - ``INCONCLUSIVE_FRESH_SAMPLE`` — n < 30 per arm.

Out of scope
============
* No multi-framework comparison (FVG / breaker). F11 specifically
  re-tests the OB-zone advantage geometry.
* No AI-vs-mechanical join. Same-mechanical-vs-same-mechanical, like
  F4 and the original Test A Q2.
* No re-evaluation of the original 219-event population. F11
  operates on F4's fresh population (or a re-extract if missing).
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import logging
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

# Reuse F4's BOS extraction + outcome resolver
from src.research_infra.dumb_baseline import (
    DEFAULT_OHLCV_DIR,
    MechanicalOutcome,
    MechanicalSetup,
    OHLCV_STEM,
    TICK_SIZE,
    _canonical_symbol,
    resolve_mechanical_outcome,
)
from src.research_infra.ob_zone_test import (
    ATR_PERIOD,
    BOSEvent,
    DEFAULT_FAMILY_SIZE,
    DEFAULT_MAX_HOLD_BARS,
    DEFAULT_MIN_RR,
    DEFAULT_SL_BUFFER_ATR_MULT,
    DEFAULT_SL_BUFFER_MIN_TICKS,
    H1_2026_END,
    Outcome,
    bonferroni_correct,
    extract_bos_events,
    find_ob_retest_outcome,
    _make_setup,
    _replace_nan,
    _sl_buffer,
    _two_prop_z_test,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Project-root resolution + harness identity
# ---------------------------------------------------------------------------

# src/research_infra/ob_zone_original_geometry.py → project root is parents[2]
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

#: Harness version embedded in summary.json; bump when contract changes.
HARNESS_VERSION: str = "F11-v1"

#: Canonical "80% retrace" of the impulse range from the impulse ORIGIN.
#: A LONG entry sits at ``anchor + (1 - 0.80) × impulse_range = anchor + 0.20
#: × impulse_range`` — close to the anchor swing low. This matches the
#: original Test A's "80% retrace baseline" geometry exactly.
ORIGINAL_RETRACE_PCT_FROM_ORIGIN: float = 0.80

#: F4's saved population path (default input). When present, F11 uses
#: F4's BOS events verbatim — guaranteeing the SAME population.
F4_POPULATION_PATH: Path = (
    PROJECT_ROOT / "research" / "edge_decomposition"
    / "F4_ob_zone_fresh_test_a" / "population.jsonl"
)

#: F11's canonical output dir (under research/edge_decomposition/).
DEFAULT_OUTPUT_DIR: Path = (
    PROJECT_ROOT / "research" / "edge_decomposition"
    / "F11_ob_zone_original_geometry"
)


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass
class F11PeriodSummary:
    """Per-period (Full / H1 / H2 / per-instrument) statistical summary.

    Holds counts + WR + delta + BOTH p-value tests so the caller can
    audit cross-method agreement.
    """

    period_label: str
    n_bos: int

    # Resolved counts (the 2x2 contingency table)
    ob_wins: int
    ob_resolved: int
    ob_filled: int
    gen_wins: int
    gen_resolved: int
    gen_filled: int

    # WRs + delta in pp
    ob_wr: float
    gen_wr: float
    delta_pp: float

    # Fisher exact test
    fisher_raw_p: float
    fisher_corrected_p: float

    # Pooled-z test (matches F4 / K52)
    z_raw_p: float
    z_corrected_p: float

    # Verdict label
    verdict: str
    notes: str


@dataclass
class F11Report:
    """Top-level F11 result.

    Attributes
    ----------
    n_bos_total : int
        Number of BOS events in F11's population (= F4's population
        when ``--use-f4-population`` is set, else freshly extracted).
    period_full / period_h1 / period_h2 : F11PeriodSummary
        Per-period statistical summaries.
    per_instrument : dict[str, F11PeriodSummary]
        Per-instrument summaries (full window).
    """

    # Tell pytest this is NOT a test class.
    __test__ = False

    harness_version: str
    generated_at: str
    start_date: str
    end_date: str
    instruments: Tuple[str, ...]
    family_size: int

    n_bos_total: int

    period_full: F11PeriodSummary
    period_h1: F11PeriodSummary
    period_h2: F11PeriodSummary
    per_instrument: Dict[str, F11PeriodSummary]

    # Source population provenance
    population_source: str  # "f4_jsonl" | "fresh_extract"
    population_path: Optional[str]  # f4 jsonl path if used

    # Decision rule constants
    n_min_floor: int = 30
    delta_pp_confirmed_floor: float = 5.0
    delta_pp_partial_floor: float = 5.0
    delta_pp_partial_ceiling: float = 12.0
    alpha: float = 0.05


# ---------------------------------------------------------------------------
# F11 baseline strategy: original Test A 80%-of-impulse-range retrace
# ---------------------------------------------------------------------------


def find_original_geometry_pullback_outcome(
    bos: BOSEvent,
    ohlcv_path: Path,
    *,
    retrace_from_origin_pct: float = ORIGINAL_RETRACE_PCT_FROM_ORIGIN,
    atr_mult: float = DEFAULT_SL_BUFFER_ATR_MULT,
    min_ticks: int = DEFAULT_SL_BUFFER_MIN_TICKS,
    min_rr: float = DEFAULT_MIN_RR,
    max_hold_bars: int = DEFAULT_MAX_HOLD_BARS,
    m15_ohlcv_dir: Optional[Path] = None,
    ohlcv_rows: Optional[Sequence[Mapping[str, Any]]] = None,
) -> Outcome:
    """Mechanical pullback outcome using the ORIGINAL Test A geometry.

    Entry: ``80% retrace`` of the impulse range *from the impulse
    origin* — equivalently, ``anchor + (1 - 0.80) × impulse_range``
    (= ``anchor + 0.20 × impulse_range``) for LONG, signed for SHORT.

    SL: beyond the anchor swing extreme by the canonical buffer
    (matches F4's generic-pullback SL convention — the "if the impulse
    origin breaks, the impulse hypothesis is wrong" interpretation).

    TP: ``entry ± min_rr × |entry - SL|`` (1.5R floor by default).

    Parameters
    ----------
    bos : BOSEvent
        Source BOS event (with anchor swing + ATR).
    ohlcv_path : Path
        Path used by ``resolve_mechanical_outcome`` to locate M15 data
        when ``ohlcv_rows`` is not supplied.
    retrace_from_origin_pct : float
        Defaults to 0.80 (canonical original-Test-A baseline).
    atr_mult, min_ticks, min_rr, max_hold_bars : float | int
        SL buffer + RR + hold ceiling (mirror F4 defaults).
    m15_ohlcv_dir, ohlcv_rows : optional
        Direct M15 row injection for tests; otherwise fall back to
        ``DEFAULT_OHLCV_DIR``.

    Returns
    -------
    Outcome
        With ``strategy="original_80pct_origin"`` and ``skip_reason``
        on degeneracy (zero impulse range, inverted impulse, etc.).
    """
    bos_id = f"{bos.symbol}|{bos.bos_time.isoformat()}"
    impulse_range = bos.bos_close - bos.anchor_swing_price

    if abs(impulse_range) < 1e-9:
        return Outcome(
            bos_id=bos_id,
            strategy="original_80pct_origin",
            skip_reason="DEGENERATE_IMPULSE",
            entry=None, sl=None, tp=None, rr=None,
            outcome=None, realized_r=None, bars_in_trade=None,
            exit_time=None,
        )

    if bos.direction == "LONG":
        if impulse_range <= 0:
            return Outcome(
                bos_id=bos_id, strategy="original_80pct_origin",
                skip_reason="INVERTED_IMPULSE",
                entry=None, sl=None, tp=None, rr=None,
                outcome=None, realized_r=None, bars_in_trade=None,
                exit_time=None,
            )
        # 80% retrace from origin → entry at (1 - 0.80) × range above anchor.
        entry = bos.anchor_swing_price + (1.0 - retrace_from_origin_pct) * impulse_range
    else:  # SHORT
        if impulse_range >= 0:
            return Outcome(
                bos_id=bos_id, strategy="original_80pct_origin",
                skip_reason="INVERTED_IMPULSE",
                entry=None, sl=None, tp=None, rr=None,
                outcome=None, realized_r=None, bars_in_trade=None,
                exit_time=None,
            )
        # impulse_range < 0; entry sits 20% × |range| below anchor.
        entry = bos.anchor_swing_price + (1.0 - retrace_from_origin_pct) * impulse_range

    buffer = _sl_buffer(bos, atr_mult=atr_mult, min_ticks=min_ticks)
    if buffer <= 0:
        return Outcome(
            bos_id=bos_id, strategy="original_80pct_origin",
            skip_reason="BAD_SL_BUFFER",
            entry=None, sl=None, tp=None, rr=None,
            outcome=None, realized_r=None, bars_in_trade=None,
            exit_time=None,
        )

    # SL beyond the impulse anchor (the "deep pullback baseline" SL —
    # mirror F4's generic_50pct semantics for direct comparability).
    if bos.direction == "LONG":
        sl = bos.anchor_swing_price - buffer
    else:
        sl = bos.anchor_swing_price + buffer

    sl_dist = abs(entry - sl)
    if sl_dist <= 0:
        return Outcome(
            bos_id=bos_id, strategy="original_80pct_origin",
            skip_reason="DEGENERATE_SL",
            entry=None, sl=None, tp=None, rr=None,
            outcome=None, realized_r=None, bars_in_trade=None,
            exit_time=None,
        )

    if bos.direction == "LONG":
        tp = entry + min_rr * sl_dist
    else:
        tp = entry - min_rr * sl_dist

    setup = _make_setup(bos, entry=entry, sl=sl, tp=tp)
    if m15_ohlcv_dir is None:
        m15_ohlcv_dir = DEFAULT_OHLCV_DIR
    out = resolve_mechanical_outcome(
        setup, m15_ohlcv_dir, max_hold_bars=max_hold_bars,
        ohlcv_rows=ohlcv_rows,
    )
    return Outcome(
        bos_id=bos_id,
        strategy="original_80pct_origin",
        skip_reason=out.skip_reason,
        entry=round(entry, 6),
        sl=round(sl, 6),
        tp=round(tp, 6),
        rr=round(abs(tp - entry) / sl_dist, 4) if sl_dist > 0 else None,
        outcome=out.outcome,
        realized_r=out.realized_r,
        bars_in_trade=out.bars_in_trade,
        exit_time=out.exit_time,
    )


# ---------------------------------------------------------------------------
# Pure-Python Fisher exact test (no scipy dependency)
# ---------------------------------------------------------------------------


def _log_binomial_coefficient(n: int, k: int) -> float:
    """Log of C(n, k) via lgamma — stable for large n."""
    if k < 0 or k > n:
        return float("-inf")
    return (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
    )


def _hypergeom_log_pmf(k: int, m: int, n: int, N: int) -> float:
    """Log P(X = k) for a hypergeometric draw.

    Where the urn has ``m`` successes and ``N - m`` failures and we
    draw ``n`` without replacement; ``k`` is the observed successes.

    Returns -inf when ``k`` is outside the legal range.
    """
    if k < max(0, n - (N - m)) or k > min(n, m):
        return float("-inf")
    return (
        _log_binomial_coefficient(m, k)
        + _log_binomial_coefficient(N - m, n - k)
        - _log_binomial_coefficient(N, n)
    )


def fisher_exact_test(wins_a: int, n_a: int, wins_b: int, n_b: int) -> float:
    """Two-tailed Fisher exact p-value for the 2x2 contingency table.

    Table:
                  wins   losses
        arm_a |  k_a |  n_a - k_a
        arm_b |  k_b |  n_b - k_b

    Computed by enumerating all hypergeometric outcomes for the
    margin-fixed table; sum of probabilities ≤ observed-table
    probability is the two-tailed p (Fisher's symmetry-around-mean
    convention as used by ``scipy.stats.fisher_exact(alternative='two-sided')``).

    Pure-Python; no scipy dependency. Returns ``1.0`` on degenerate
    margins, ``nan`` on invalid inputs.

    Parameters
    ----------
    wins_a, n_a : int
        Successes and total draws in arm A (e.g., OB).
    wins_b, n_b : int
        Successes and total draws in arm B (e.g., baseline).

    Returns
    -------
    float
        Two-tailed p-value in [0, 1].
    """
    if n_a < 0 or n_b < 0 or wins_a < 0 or wins_b < 0:
        return float("nan")
    if wins_a > n_a or wins_b > n_b:
        return float("nan")
    if n_a == 0 or n_b == 0:
        return 1.0

    # Margins (column sums)
    total_wins = wins_a + wins_b
    total_n = n_a + n_b
    if total_wins == 0 or total_wins == total_n:
        return 1.0  # Degenerate — both arms identical, no signal

    # Observed log-probability under H0 (independence)
    # Use arm A's wins as the cell of interest; the hypergeometric
    # draws ``n_a`` from a universe of ``total_n`` containing
    # ``total_wins`` successes.
    log_p_obs = _hypergeom_log_pmf(wins_a, total_wins, n_a, total_n)
    if not math.isfinite(log_p_obs):
        return 1.0  # Outside legal margin → no signal

    # Two-tailed: sum P(X = k) for all k where P(X = k) <= P(observed)
    # within the legal range [max(0, n_a - (total_n - total_wins)),
    # min(n_a, total_wins)].
    k_min = max(0, n_a - (total_n - total_wins))
    k_max = min(n_a, total_wins)

    # Numerical-stability epsilon: include outcomes whose log-prob is
    # within 1e-9 of the observed.
    eps = 1e-9
    log_terms: List[float] = []
    for k in range(k_min, k_max + 1):
        log_p = _hypergeom_log_pmf(k, total_wins, n_a, total_n)
        if not math.isfinite(log_p):
            continue
        if log_p <= log_p_obs + eps:
            log_terms.append(log_p)

    if not log_terms:
        return 1.0

    # Log-sum-exp for numerical stability
    log_max = max(log_terms)
    p = sum(math.exp(t - log_max) for t in log_terms)
    p_value = math.exp(log_max) * p
    return min(1.0, max(0.0, p_value))


# ---------------------------------------------------------------------------
# F4 population reader (for paired comparison on identical population)
# ---------------------------------------------------------------------------


def _bos_from_jsonl_row(row: Mapping[str, Any]) -> Optional[BOSEvent]:
    """Reconstruct a :class:`BOSEvent` from one F4 ``population.jsonl`` row.

    F4 serialises BOSEvent via ``asdict`` → datetime → isoformat string.
    We invert that: parse the isoformat strings back to tz-aware UTC
    datetimes; preserve all numeric fields.

    Returns ``None`` on malformed rows (logged at WARNING).
    """
    bos_dict = row.get("bos") if isinstance(row, dict) else None
    if not isinstance(bos_dict, dict):
        return None

    def _parse_dt(v: Any) -> Optional[dt.datetime]:
        if v is None:
            return None
        if isinstance(v, dt.datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=dt.timezone.utc)
            return v.astimezone(dt.timezone.utc)
        if isinstance(v, str):
            try:
                parsed = dt.datetime.fromisoformat(v)
            except ValueError:
                return None
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=dt.timezone.utc)
            return parsed.astimezone(dt.timezone.utc)
        return None

    try:
        bos_time = _parse_dt(bos_dict.get("bos_time"))
        swing_time = _parse_dt(bos_dict.get("swing_time"))
        anchor_time = _parse_dt(bos_dict.get("anchor_swing_time"))
        ob_time = _parse_dt(bos_dict.get("ob_time"))
        if bos_time is None or swing_time is None or anchor_time is None:
            return None
        return BOSEvent(
            symbol=str(bos_dict["symbol"]),
            bos_time=bos_time,
            bos_index=int(bos_dict["bos_index"]),
            direction=str(bos_dict["direction"]),
            swing_level_broken=float(bos_dict["swing_level_broken"]),
            swing_time=swing_time,
            anchor_swing_price=float(bos_dict["anchor_swing_price"]),
            anchor_swing_time=anchor_time,
            anchor_swing_index=int(bos_dict["anchor_swing_index"]),
            bos_close=float(bos_dict["bos_close"]),
            bos_high=float(bos_dict["bos_high"]),
            bos_low=float(bos_dict["bos_low"]),
            atr_at_bos=float(bos_dict["atr_at_bos"]),
            ob_high=(float(bos_dict["ob_high"])
                     if bos_dict.get("ob_high") is not None else None),
            ob_low=(float(bos_dict["ob_low"])
                    if bos_dict.get("ob_low") is not None else None),
            ob_index=(int(bos_dict["ob_index"])
                      if bos_dict.get("ob_index") is not None else None),
            ob_time=ob_time,
            ob_skip_reason=bos_dict.get("ob_skip_reason"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        logger.warning("Cannot parse BOS row: %s", exc)
        return None


def load_f4_population(
    population_path: Path = F4_POPULATION_PATH,
) -> List[BOSEvent]:
    """Load F4's ``population.jsonl`` and return the BOSEvent list.

    Empty list if the file is missing or every row fails to parse —
    callers should fall back to fresh extraction.
    """
    if not population_path.exists():
        logger.warning("F4 population missing: %s", population_path)
        return []

    events: List[BOSEvent] = []
    try:
        with population_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                bos = _bos_from_jsonl_row(row)
                if bos is not None:
                    events.append(bos)
    except OSError as exc:
        logger.warning("Cannot read F4 population %s: %s",
                       population_path, exc)
        return []

    return events


# ---------------------------------------------------------------------------
# Verdict classification
# ---------------------------------------------------------------------------


#: F4-published H2-2026 delta for the methodology-shift narrative
#: (from research/edge_decomposition/F4_ob_zone_fresh_test_a/results.json).
F4_PUBLISHED_H2_DELTA_PP: float = 0.948660714285709

#: Original Test A H2-equivalent published delta (from
#: .context/03_analysis/test_a_rerun_real_bos_results.md Q2 row).
ORIGINAL_TEST_A_DELTA_PP: float = 16.8


def classify_verdict(
    delta_pp: float,
    fisher_corrected_p: float,
    z_corrected_p: float,
    n_min_per_arm: int,
    *,
    n_min_floor: int = 30,
    delta_confirmed_floor: float = 5.0,
    delta_partial_floor: float = 5.0,
    delta_partial_ceiling: float = 12.0,
    alpha: float = 0.05,
    f4_published_delta_pp: float = F4_PUBLISHED_H2_DELTA_PP,
    original_delta_pp: float = ORIGINAL_TEST_A_DELTA_PP,
) -> Tuple[str, str]:
    """Map (delta, p, n) → (verdict, notes).

    Verdict ladder (most-to-least supportive of original Test A's
    +17pp survives on the H2-2026 population when the original
    geometry is restored):
      - ``CONFIRMED``: delta ≥ ``delta_partial_ceiling`` (default
        +12pp) on H2 AND at least one corrected p < α. Strong
        evidence the original advantage holds when the original
        geometry is restored — F4 was methodology drift.
      - ``PARTIAL``: delta in [``delta_partial_floor``,
        ``delta_partial_ceiling``) OR significant under one test
        but not both — methodology contributes AND decay contributes.
      - ``METHODOLOGY_DRIFT``: F4-like result (|delta| <
        ``delta_partial_floor`` AND no corrected p < α). The deeper
        baseline did NOT recover the advantage; F4's DECAYED_FRESH is
        real decay, not methodology.
      - ``INCONCLUSIVE_FRESH_SAMPLE``: per-arm n < ``n_min_floor``.

    The reasoning text always reports BOTH the absolute delta_pp
    *and* the methodology shift (F11 delta − F4 published delta) so
    the reader can see how much of the original-vs-F4 gap is
    attributable to methodology vs decay even when the verdict
    label is binary.
    """
    if n_min_per_arm < n_min_floor:
        return (
            "INCONCLUSIVE_FRESH_SAMPLE",
            f"Min resolved n = {n_min_per_arm} below floor "
            f"{n_min_floor}/arm; cannot adjudicate.",
        )

    if not math.isfinite(delta_pp):
        return (
            "INCONCLUSIVE_FRESH_SAMPLE",
            "delta_pp non-finite (degenerate WR).",
        )

    fisher_sig = (
        math.isfinite(fisher_corrected_p) and fisher_corrected_p < alpha
    )
    z_sig = math.isfinite(z_corrected_p) and z_corrected_p < alpha
    any_sig = fisher_sig or z_sig
    both_sig = fisher_sig and z_sig

    methodology_shift = delta_pp - f4_published_delta_pp
    decay_remaining = original_delta_pp - delta_pp

    shift_clause = (
        f"Methodology shift (F11 − F4) = "
        f"{methodology_shift:+.1f}pp; remaining decay vs original "
        f"+{original_delta_pp:.1f}pp = "
        f"{decay_remaining:+.1f}pp."
    )

    if delta_pp >= delta_partial_ceiling and any_sig:
        return (
            "CONFIRMED",
            f"delta = +{delta_pp:.1f}pp ≥ +{delta_partial_ceiling:g}pp "
            f"ceiling AND significant under "
            f"{'both' if both_sig else 'one'} test (Fisher corrected p "
            f"= {fisher_corrected_p:.4g}, z corrected p = "
            f"{z_corrected_p:.4g}). Original-geometry test recovers "
            f"OB-zone advantage close to original Test A's "
            f"+{original_delta_pp:.1f}pp; F4's DECAYED_FRESH was "
            f"methodology drift. {shift_clause}",
        )

    if delta_pp >= delta_partial_floor and any_sig:
        return (
            "PARTIAL",
            f"delta = +{delta_pp:.1f}pp ∈ "
            f"[+{delta_partial_floor:g}pp, +{delta_partial_ceiling:g}pp) "
            f"AND significant under "
            f"{'both' if both_sig else 'one'} test (Fisher corrected p = "
            f"{fisher_corrected_p:.4g}, z corrected p = "
            f"{z_corrected_p:.4g}). Original geometry partially recovers "
            f"the advantage; both decay AND methodology drift "
            f"contribute. {shift_clause}",
        )

    if delta_pp >= delta_partial_floor:
        return (
            "PARTIAL",
            f"delta = +{delta_pp:.1f}pp ≥ +{delta_partial_floor:g}pp "
            f"BUT no corrected p < α ({alpha}) — Fisher = "
            f"{fisher_corrected_p:.4g}, z = {z_corrected_p:.4g}. "
            f"Direction matches original Test A but not significant "
            f"under family-size {DEFAULT_FAMILY_SIZE} correction; "
            f"sample-size limited. {shift_clause}",
        )

    if -delta_partial_floor < delta_pp < delta_partial_floor:
        # F11 delta is small in absolute terms, but if the methodology
        # shift is non-trivial we explicitly call out partial methodology
        # contribution in the notes (verdict label still METHODOLOGY_DRIFT
        # because the absolute test failed both significance and floor).
        if methodology_shift >= 2.0:
            shift_caveat = (
                f" Note: F11 still shifted the H2 delta by "
                f"{methodology_shift:+.1f}pp vs F4 — methodology DID "
                f"contribute, but the residual decay "
                f"({decay_remaining:+.1f}pp vs original) dominates."
            )
        else:
            shift_caveat = ""
        return (
            "METHODOLOGY_DRIFT",
            f"delta = {delta_pp:+.1f}pp within "
            f"±{delta_partial_floor:g}pp AND no significant p "
            f"(Fisher = {fisher_corrected_p:.4g}, z = "
            f"{z_corrected_p:.4g}). Restoring the original baseline "
            f"geometry did NOT recover the +{original_delta_pp:.1f}pp "
            f"advantage. F4's DECAYED_FRESH verdict is supported — the "
            f"OB-zone advantage has genuinely decayed on H2-2026 data, "
            f"NOT explained away by methodology.{shift_caveat} "
            f"{shift_clause}",
        )

    # delta_pp <= -delta_partial_floor (baseline now beats OB)
    return (
        "METHODOLOGY_DRIFT",
        f"delta = {delta_pp:+.1f}pp NEGATIVE — baseline beats OB by "
        f"{abs(delta_pp):.1f}pp under original geometry. The OB-zone "
        f"advantage has not just decayed but reversed in this period. "
        f"Fisher = {fisher_corrected_p:.4g}, z = {z_corrected_p:.4g}. "
        f"{shift_clause}",
    )


# ---------------------------------------------------------------------------
# Period aggregation
# ---------------------------------------------------------------------------


def _wins_resolved_filled(outs: Sequence[Outcome]) -> Tuple[int, int, int]:
    """Mirror F4's _aggregate_period accounting:

    - ``filled`` = entry was reached (skip_reason None or outcome present
      AND outcome != "NO_ENTRY")
    - ``resolved`` = filled AND realized_r is not None (TP/SL/TIMEOUT
      with mark-to-market — excludes SAME_BAR)
    - ``wins`` = resolved AND realized_r > 0
    """
    filled = 0
    resolved = 0
    wins = 0
    for o in outs:
        if o.skip_reason is not None and o.outcome is None:
            continue
        if o.outcome == "NO_ENTRY":
            continue
        filled += 1
        if o.realized_r is None:
            continue
        resolved += 1
        if o.realized_r > 0:
            wins += 1
    return wins, resolved, filled


def aggregate_period(
    bos_list: Sequence[BOSEvent],
    ob_outcomes: Sequence[Outcome],
    f11_outcomes: Sequence[Outcome],
    *,
    period_label: str,
    family_size: int = DEFAULT_FAMILY_SIZE,
    n_min: int = 30,
    delta_confirmed_floor: float = 12.0,
    delta_partial_floor: float = 5.0,
    delta_partial_ceiling: float = 12.0,
    alpha: float = 0.05,
) -> F11PeriodSummary:
    """Compute counts + WR + delta + Fisher exact + pooled-z + verdict."""
    n_bos = len(bos_list)
    ob_wins, ob_resolved, ob_filled = _wins_resolved_filled(ob_outcomes)
    f11_wins, f11_resolved, f11_filled = _wins_resolved_filled(f11_outcomes)

    ob_wr = (ob_wins / ob_resolved) if ob_resolved > 0 else float("nan")
    f11_wr = (f11_wins / f11_resolved) if f11_resolved > 0 else float("nan")
    if math.isfinite(ob_wr) and math.isfinite(f11_wr):
        delta_pp = (ob_wr - f11_wr) * 100.0
    else:
        delta_pp = float("nan")

    fisher_raw = fisher_exact_test(ob_wins, ob_resolved, f11_wins, f11_resolved)
    fisher_corrected = bonferroni_correct(fisher_raw, family_size)

    z_raw = _two_prop_z_test(ob_wins, ob_resolved, f11_wins, f11_resolved)
    z_corrected = bonferroni_correct(z_raw, family_size)

    n_min_per_arm = min(ob_resolved, f11_resolved)
    verdict, notes = classify_verdict(
        delta_pp,
        fisher_corrected,
        z_corrected,
        n_min_per_arm,
        n_min_floor=n_min,
        delta_confirmed_floor=delta_confirmed_floor,
        delta_partial_floor=delta_partial_floor,
        delta_partial_ceiling=delta_partial_ceiling,
        alpha=alpha,
    )

    return F11PeriodSummary(
        period_label=period_label,
        n_bos=n_bos,
        ob_wins=ob_wins, ob_resolved=ob_resolved, ob_filled=ob_filled,
        gen_wins=f11_wins, gen_resolved=f11_resolved, gen_filled=f11_filled,
        ob_wr=ob_wr,
        gen_wr=f11_wr,
        delta_pp=delta_pp,
        fisher_raw_p=fisher_raw,
        fisher_corrected_p=fisher_corrected,
        z_raw_p=z_raw,
        z_corrected_p=z_corrected,
        verdict=verdict,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Public API: end-to-end F11 driver
# ---------------------------------------------------------------------------


def run_f11_original_geometry(
    start_date: dt.datetime,
    end_date: dt.datetime,
    instruments: Sequence[str],
    ohlcv_dir: Path = DEFAULT_OHLCV_DIR,
    *,
    family_size: int = DEFAULT_FAMILY_SIZE,
    n_min: int = 30,
    delta_confirmed_floor: float = 12.0,
    delta_partial_floor: float = 5.0,
    delta_partial_ceiling: float = 12.0,
    alpha: float = 0.05,
    h2_2026_split: dt.datetime = H1_2026_END,
    f4_population_path: Optional[Path] = F4_POPULATION_PATH,
    use_f4_population: bool = True,
    progress: Optional[Callable[[str], None]] = None,
) -> Tuple[F11Report, List[BOSEvent], List[Outcome], List[Outcome]]:
    """End-to-end F11.

    By default, F11 loads BOS events from F4's saved population (so the
    same population is scored under different baseline geometry). If
    F4's file is missing or ``use_f4_population=False``, we fall back
    to fresh extraction with the same parameters as F4.

    Returns (report, bos_events, ob_outcomes, f11_outcomes) with
    parallel indexing.
    """
    if progress is None:
        def progress(msg: str) -> None:  # noqa: ARG001
            pass

    population_source: str = "fresh_extract"
    population_path_str: Optional[str] = None
    all_bos: List[BOSEvent] = []

    if use_f4_population and f4_population_path and f4_population_path.exists():
        progress(f"Loading F4 population from {f4_population_path}")
        f4_bos = load_f4_population(f4_population_path)
        if f4_bos:
            # Filter to caller's instruments + window
            instr_set = {_canonical_symbol(s) for s in instruments}
            for b in f4_bos:
                if _canonical_symbol(b.symbol) not in instr_set:
                    continue
                if b.bos_time < start_date:
                    continue
                if b.bos_time > end_date:
                    continue
                all_bos.append(b)
            population_source = "f4_jsonl"
            population_path_str = str(f4_population_path)
            progress(f"  → {len(all_bos)} BOS events from F4 (post-filter)")
        else:
            progress("  F4 population unreadable; falling back to fresh extract")

    if not all_bos:
        progress("Re-extracting BOS events fresh from H1 OHLCV")
        for sym in instruments:
            canonical = _canonical_symbol(sym)
            stem = (
                OHLCV_STEM.get(canonical)
                or OHLCV_STEM.get(canonical.upper())
                or canonical
            )
            h1_path = ohlcv_dir / f"{stem}_H1.csv"
            progress(f"  Extracting {sym} from {h1_path.name}")
            bos = extract_bos_events(
                h1_path, symbol=sym, start=start_date, end=end_date,
            )
            all_bos.extend(bos)
            progress(f"    → {len(bos)} BOS events")
        population_source = "fresh_extract"

    progress(f"Total BOS events: {len(all_bos)}")

    # Compute outcomes per BOS — OB retest (F4 logic) + F11 baseline.
    all_ob: List[Outcome] = []
    all_f11: List[Outcome] = []

    # Group by symbol for OHLCV path resolution
    by_symbol: Dict[str, List[BOSEvent]] = {}
    for b in all_bos:
        by_symbol.setdefault(b.symbol, []).append(b)

    for sym, sym_events in by_symbol.items():
        canonical = _canonical_symbol(sym)
        stem = (
            OHLCV_STEM.get(canonical)
            or OHLCV_STEM.get(canonical.upper())
            or canonical
        )
        h1_path = ohlcv_dir / f"{stem}_H1.csv"
        progress(f"Resolving outcomes for {sym} ({len(sym_events)} events)")
        for b in sym_events:
            ob_o = find_ob_retest_outcome(b, h1_path, m15_ohlcv_dir=ohlcv_dir)
            f11_o = find_original_geometry_pullback_outcome(
                b, h1_path, m15_ohlcv_dir=ohlcv_dir,
            )
            all_ob.append(ob_o)
            all_f11.append(f11_o)

    # We re-order all_ob / all_f11 to match the *order in all_bos*.
    # The grouping above scrambled that. Rebuild parallel-indexed lists.
    progress("Rebuilding parallel-indexed outcome lists")
    by_id_ob: Dict[str, Outcome] = {o.bos_id: o for o in all_ob}
    by_id_f11: Dict[str, Outcome] = {o.bos_id: o for o in all_f11}
    all_ob = [
        by_id_ob.get(f"{b.symbol}|{b.bos_time.isoformat()}",
                     Outcome(
                         bos_id=f"{b.symbol}|{b.bos_time.isoformat()}",
                         strategy="ob_retest",
                         skip_reason="MISSING_OUTCOME",
                         entry=None, sl=None, tp=None, rr=None,
                         outcome=None, realized_r=None,
                         bars_in_trade=None, exit_time=None,
                     ))
        for b in all_bos
    ]
    all_f11 = [
        by_id_f11.get(f"{b.symbol}|{b.bos_time.isoformat()}",
                      Outcome(
                          bos_id=f"{b.symbol}|{b.bos_time.isoformat()}",
                          strategy="original_80pct_origin",
                          skip_reason="MISSING_OUTCOME",
                          entry=None, sl=None, tp=None, rr=None,
                          outcome=None, realized_r=None,
                          bars_in_trade=None, exit_time=None,
                      ))
        for b in all_bos
    ]

    # Per-instrument summaries (full window)
    per_instrument: Dict[str, F11PeriodSummary] = {}
    for sym in instruments:
        sym_idx = [
            i for i, b in enumerate(all_bos)
            if _canonical_symbol(b.symbol) == _canonical_symbol(sym)
        ]
        sym_bos = [all_bos[i] for i in sym_idx]
        sym_ob = [all_ob[i] for i in sym_idx]
        sym_f11 = [all_f11[i] for i in sym_idx]
        per_instrument[sym] = aggregate_period(
            sym_bos, sym_ob, sym_f11,
            period_label=f"full_{sym}",
            family_size=family_size,
            n_min=n_min,
            delta_confirmed_floor=delta_confirmed_floor,
            delta_partial_floor=delta_partial_floor,
            delta_partial_ceiling=delta_partial_ceiling,
            alpha=alpha,
        )

    # Period splits
    h1_idx = [i for i, b in enumerate(all_bos) if b.bos_time < h2_2026_split]
    h2_idx = [i for i, b in enumerate(all_bos) if b.bos_time >= h2_2026_split]

    period_full = aggregate_period(
        all_bos, all_ob, all_f11,
        period_label="full",
        family_size=family_size,
        n_min=n_min,
        delta_confirmed_floor=delta_confirmed_floor,
        delta_partial_floor=delta_partial_floor,
        delta_partial_ceiling=delta_partial_ceiling,
        alpha=alpha,
    )
    period_h1 = aggregate_period(
        [all_bos[i] for i in h1_idx],
        [all_ob[i] for i in h1_idx],
        [all_f11[i] for i in h1_idx],
        period_label="H1_2026",
        family_size=family_size,
        n_min=n_min,
        delta_confirmed_floor=delta_confirmed_floor,
        delta_partial_floor=delta_partial_floor,
        delta_partial_ceiling=delta_partial_ceiling,
        alpha=alpha,
    )
    period_h2 = aggregate_period(
        [all_bos[i] for i in h2_idx],
        [all_ob[i] for i in h2_idx],
        [all_f11[i] for i in h2_idx],
        period_label="H2_2026",
        family_size=family_size,
        n_min=n_min,
        delta_confirmed_floor=delta_confirmed_floor,
        delta_partial_floor=delta_partial_floor,
        delta_partial_ceiling=delta_partial_ceiling,
        alpha=alpha,
    )

    report = F11Report(
        harness_version=HARNESS_VERSION,
        generated_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        start_date=start_date.date().isoformat(),
        end_date=end_date.date().isoformat(),
        instruments=tuple(instruments),
        family_size=family_size,
        n_bos_total=len(all_bos),
        period_full=period_full,
        period_h1=period_h1,
        period_h2=period_h2,
        per_instrument=per_instrument,
        population_source=population_source,
        population_path=population_path_str,
        n_min_floor=n_min,
        delta_pp_confirmed_floor=delta_confirmed_floor,
        delta_pp_partial_floor=delta_partial_floor,
        delta_pp_partial_ceiling=delta_partial_ceiling,
        alpha=alpha,
    )
    return report, all_bos, all_ob, all_f11


# ---------------------------------------------------------------------------
# JSON-safe serialization
# ---------------------------------------------------------------------------


def _serialize_bos(bos: BOSEvent) -> dict:
    d = asdict(bos)
    for key in ("bos_time", "swing_time", "anchor_swing_time", "ob_time"):
        v = d.get(key)
        if isinstance(v, dt.datetime):
            d[key] = v.isoformat()
    return d


def _serialize_outcome(o: Outcome) -> dict:
    return asdict(o)


def serialize_population(
    bos_events: Sequence[BOSEvent],
    ob_outcomes: Sequence[Outcome],
    f11_outcomes: Sequence[Outcome],
) -> List[dict]:
    """One JSON row per BOS pairing OB retest + F11 original-geometry baseline."""
    out: List[dict] = []
    for b, ob_o, f11_o in zip(bos_events, ob_outcomes, f11_outcomes):
        out.append({
            "bos": _serialize_bos(b),
            "ob_retest": _serialize_outcome(ob_o),
            "original_80pct_origin": _serialize_outcome(f11_o),
        })
    return out


def _summary_to_dict(s: F11PeriodSummary) -> dict:
    return _replace_nan(asdict(s))


def serialize_report(report: F11Report) -> dict:
    """Convert F11Report to a JSON-safe dict (NaN/Inf replaced)."""
    return _replace_nan({
        "harness_version": report.harness_version,
        "generated_at": report.generated_at,
        "start_date": report.start_date,
        "end_date": report.end_date,
        "instruments": list(report.instruments),
        "family_size": report.family_size,
        "n_bos_total": report.n_bos_total,
        "period_full": asdict(report.period_full),
        "period_h1": asdict(report.period_h1),
        "period_h2": asdict(report.period_h2),
        "per_instrument": {k: asdict(v) for k, v in report.per_instrument.items()},
        "population_source": report.population_source,
        "population_path": report.population_path,
        "n_min_floor": report.n_min_floor,
        "delta_pp_confirmed_floor": report.delta_pp_confirmed_floor,
        "delta_pp_partial_floor": report.delta_pp_partial_floor,
        "delta_pp_partial_ceiling": report.delta_pp_partial_ceiling,
        "alpha": report.alpha,
    })
