"""Q-13.10 — Volume Profile (VPOC / LVN) on XAUUSD M15.

Pre-registered hypotheses (written BEFORE looking at data):

H1 (VPOC reaction size) — When price (M15 close) returns to a VPOC bin of the
   trailing 30-day rolling volume profile, the mean absolute 12-candle
   forward excursion (measured in ATR multiples) is >= 1.2 x the mean
   absolute 12-candle excursion from a random (baseline) M15 close.
   Null: ratio == 1.0. Alt: ratio >= 1.2.

H2 (LVN traversal speed) — When price first enters a Low-Volume-Node bin
   (volume < 25 percent of VPOC in the same profile), the median number
   of M15 bars until price first CLOSES outside that bin is strictly
   less than 50 percent of the median "dwell" duration at a VPOC bin
   (median bars until price first closes outside the VPOC bin, starting
   from the same kind of first-entry event).
   Null: LVN_median_bars == VPOC_median_bars. Alt: LVN_median_bars <=
   0.5 * VPOC_median_bars.

Bonferroni correction: 2 primary tests, family alpha = 0.05, per-test
alpha = 0.025 (two-sided where applicable). Each primary test is also
reported with a permutation / bootstrap p-value.

Pre-registered cross-check (NOT part of Bonferroni family):
   If >= 80 percent of VPOC events co-locate with an existing H1 or H4
   order-block zone (range overlap of the OB high-low band with the VPOC
   bin), then any VPOC reaction edge is NOT novel and just restates the
   OB edge. Co-location reported in the final markdown.

Data:
   data/historical_2026/XAUUSD_M15.csv  (primary, price bins + reactions)
   data/historical_2026/XAUUSD_H1.csv   (OB context, co-location test)
   data/historical_2026/XAUUSD_H4.csv   (OB context, co-location test)

CRITICAL LIMITATION (reported upfront in the markdown):
   XAUUSD spot CFD data uses TICK volume (one increment per broker tick),
   NOT traded volume (COMEX / LBMA cleared notional). Tick volume is a
   known but imperfect proxy for true traded activity; it is biased by
   price volatility itself (fast markets register more ticks even at
   flat size). Every finding in this report is tick-weighted, not
   true-traded-volume-weighted. Treat with caution.

Rules honoured:
   - Hypotheses stated before data inspection (above).
   - n < 15 per bucket is flagged as underpowered.
   - Local only. No API calls. Deterministic (fixed RNG seed for the
     random-level baseline and bootstrap).
   - Script is the committed artifact; markdown is regenerated from this
     script.
"""

from __future__ import annotations

import csv
import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean, median

ROOT = Path(r"C:/Users/MSI/Documents/ai-trading-agent")
M15_PATH = ROOT / "data/historical_2026/XAUUSD_M15.csv"
H1_PATH = ROOT / "data/historical_2026/XAUUSD_H1.csv"
H4_PATH = ROOT / "data/historical_2026/XAUUSD_H4.csv"
OUT_PATH = ROOT / "research/academic_pipeline/results/Q-13_10_volume.md"

BIN_SIZE = 1.00            # $1.00 price bins (spec option 2)
ROLLING_DAYS = 30          # 30-day trailing profile
LVN_THRESHOLD_FRAC = 0.25  # LVN = bin volume < 25% of VPOC volume
FWD_BARS = 12              # 12 M15 candles forward for H1 reactions
ATR_WINDOW = 14            # ATR(14) on M15 for excursion normalisation
DWELL_MAX_BARS = 288       # cap dwell walk at 3 days (288 M15 = 3x96)
SEED = 20260417            # deterministic
N_BOOT = 10000             # bootstrap iterations for H1
N_PERM = 10000             # permutation iterations for H2
ALPHA_FAMILY = 0.05
N_TESTS = 2
ALPHA_PER_TEST = ALPHA_FAMILY / N_TESTS  # 0.025


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@dataclass
class Candle:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


def load_candles(path: Path) -> list[Candle]:
    out: list[Candle] = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            out.append(
                Candle(
                    ts=datetime.strptime(r["time"], "%Y-%m-%d %H:%M:%S"),
                    open=float(r["open"]),
                    high=float(r["high"]),
                    low=float(r["low"]),
                    close=float(r["close"]),
                    volume=float(r["volume"]),
                )
            )
    out.sort(key=lambda c: c.ts)
    return out


# ---------------------------------------------------------------------------
# Volume profile: TPO-equal distribution across high-low price bins
# ---------------------------------------------------------------------------

def _bin_low(price: float) -> float:
    """Return the lower edge of the bin containing *price* (rounded down to
    BIN_SIZE grid)."""
    return math.floor(price / BIN_SIZE) * BIN_SIZE


def _bins_for_candle(c: Candle) -> list[float]:
    """All bin-low values that the candle's high-low range overlaps."""
    lo = _bin_low(c.low)
    hi = _bin_low(c.high)
    bins: list[float] = []
    x = lo
    while x <= hi + 1e-9:
        bins.append(round(x, 2))
        x = round(x + BIN_SIZE, 2)
    return bins


def build_profile(window: list[Candle]) -> dict[float, float]:
    """TPO-equal: spread each candle's tick_volume uniformly across every
    $1 bin it overlaps. Returns {bin_low: cumulative volume}."""
    profile: dict[float, float] = {}
    for c in window:
        spanned = _bins_for_candle(c)
        if not spanned:
            continue
        share = c.volume / len(spanned)
        for b in spanned:
            profile[b] = profile.get(b, 0.0) + share
    return profile


def vpoc(profile: dict[float, float]) -> tuple[float, float] | None:
    if not profile:
        return None
    best_bin = max(profile.items(), key=lambda kv: kv[1])
    return best_bin  # (bin_low, volume)


def lvn_bins(profile: dict[float, float]) -> set[float]:
    if not profile:
        return set()
    _, vpoc_vol = vpoc(profile)  # type: ignore
    thr = vpoc_vol * LVN_THRESHOLD_FRAC
    # Only consider bins that fall inside the observed price range and had
    # at least one touch (>0 volume). A bin that never printed is not an LVN.
    return {b for b, v in profile.items() if 0 < v < thr}


# ---------------------------------------------------------------------------
# ATR(14) on M15 (Wilder / simple moving)
# ---------------------------------------------------------------------------

def atr_series(candles: list[Candle], window: int = ATR_WINDOW) -> list[float]:
    """Simple moving ATR over *window* bars. atr[i] uses TRs from i-window+1..i
    inclusive. Returns list same length as candles; entries < window-1 = 0.0.
    """
    tr: list[float] = [0.0] * len(candles)
    for i, c in enumerate(candles):
        if i == 0:
            tr[i] = c.high - c.low
        else:
            pc = candles[i - 1].close
            tr[i] = max(c.high - c.low, abs(c.high - pc), abs(c.low - pc))
    atr: list[float] = [0.0] * len(candles)
    running = 0.0
    for i in range(len(candles)):
        running += tr[i]
        if i >= window:
            running -= tr[i - window]
        if i >= window - 1:
            atr[i] = running / window
    return atr


# ---------------------------------------------------------------------------
# VPOC touch & reaction measurement
# ---------------------------------------------------------------------------

@dataclass
class VpocEvent:
    i: int                # candle index of the touch/close-in-bin event
    bin_low: float        # VPOC bin low edge
    vpoc_volume: float    # raw TPO volume of the VPOC bin


def find_vpoc_touch_events(
    candles: list[Candle],
    profiles_by_i: dict[int, dict[float, float]],
) -> list[VpocEvent]:
    """Emit a VpocEvent the FIRST time the M15 close enters a VPOC bin,
    measured against the profile that was current at bar i (i.e. the
    rolling 30-day profile built from bars strictly before i).

    First-entry = the previous bar's close was outside the current VPOC
    bin. This prevents back-to-back dwell bars from double-counting.
    """
    events: list[VpocEvent] = []
    prev_bin: float | None = None
    for i, c in enumerate(candles):
        prof = profiles_by_i.get(i)
        if not prof:
            prev_bin = _bin_low(c.close)
            continue
        vp = vpoc(prof)
        if vp is None:
            prev_bin = _bin_low(c.close)
            continue
        vpoc_bin, vpoc_vol = vp
        close_bin = _bin_low(c.close)
        if close_bin == vpoc_bin:
            # First-entry check: previous close was NOT in this same bin.
            # (If prev was also in the bin, we are in the middle of a dwell.)
            if prev_bin != vpoc_bin:
                events.append(VpocEvent(i=i, bin_low=vpoc_bin, vpoc_volume=vpoc_vol))
        prev_bin = close_bin
    return events


def forward_excursion_atr(
    candles: list[Candle],
    atr: list[float],
    i: int,
    n: int = FWD_BARS,
) -> float | None:
    """Max absolute excursion over the next *n* candles in ATR multiples.
    Excursion = max(high[i+1..i+n]) - min(low[i+1..i+n]) divided by atr[i].
    Returns None if insufficient forward data or atr[i] == 0.
    """
    if i + n >= len(candles):
        return None
    if atr[i] <= 0:
        return None
    window = candles[i + 1:i + 1 + n]
    hi = max(w.high for w in window)
    lo = min(w.low for w in window)
    return (hi - lo) / atr[i]


def forward_signed_move_atr(
    candles: list[Candle],
    atr: list[float],
    i: int,
    n: int = FWD_BARS,
) -> float | None:
    """Signed net move in ATR multiples: (close[i+n] - close[i]) / atr[i].
    Returns None if insufficient forward data or atr[i] == 0.
    """
    if i + n >= len(candles):
        return None
    if atr[i] <= 0:
        return None
    return (candles[i + n].close - candles[i].close) / atr[i]


# ---------------------------------------------------------------------------
# LVN traversal: bars until first close OUTSIDE the LVN bin
# ---------------------------------------------------------------------------

def dwell_bars(
    candles: list[Candle],
    i: int,
    bin_low: float,
    max_bars: int = DWELL_MAX_BARS,
) -> int | None:
    """Number of bars (>= 1) until the first candle whose CLOSE is outside
    [bin_low, bin_low + BIN_SIZE). Returns None if the walk is truncated
    by end-of-data or by *max_bars*."""
    j = i + 1
    upper = bin_low + BIN_SIZE
    end = min(len(candles), i + 1 + max_bars)
    while j < end:
        c = candles[j].close
        if c < bin_low or c >= upper:
            return j - i
        j += 1
    return None  # censored


def find_lvn_entry_events(
    candles: list[Candle],
    profiles_by_i: dict[int, dict[float, float]],
) -> list[tuple[int, float]]:
    """FIRST-entry LVN events: the previous close was NOT in an LVN bin
    of the profile current at bar i, but THIS close IS in an LVN bin.

    Returns list of (i, bin_low)."""
    out: list[tuple[int, float]] = []
    prev_was_lvn = False
    for i, c in enumerate(candles):
        prof = profiles_by_i.get(i)
        if not prof:
            prev_was_lvn = False
            continue
        lvn_set = lvn_bins(prof)
        close_bin = _bin_low(c.close)
        is_lvn = close_bin in lvn_set
        if is_lvn and not prev_was_lvn:
            out.append((i, close_bin))
        prev_was_lvn = is_lvn
    return out


def find_vpoc_entry_events_for_dwell(
    candles: list[Candle],
    profiles_by_i: dict[int, dict[float, float]],
) -> list[tuple[int, float]]:
    """Same first-entry logic but for VPOC bin — used to measure VPOC
    dwell for H2 (comparison baseline)."""
    out: list[tuple[int, float]] = []
    prev_in_vpoc = False
    for i, c in enumerate(candles):
        prof = profiles_by_i.get(i)
        if not prof:
            prev_in_vpoc = False
            continue
        vp = vpoc(prof)
        if vp is None:
            prev_in_vpoc = False
            continue
        vpoc_bin, _ = vp
        close_bin = _bin_low(c.close)
        in_vpoc = (close_bin == vpoc_bin)
        if in_vpoc and not prev_in_vpoc:
            out.append((i, vpoc_bin))
        prev_in_vpoc = in_vpoc
    return out


# ---------------------------------------------------------------------------
# Rolling-profile builder (30-day trailing window, keyed by candle index)
# ---------------------------------------------------------------------------

def build_rolling_profiles(
    candles: list[Candle], days: int = ROLLING_DAYS,
) -> dict[int, dict[float, float]]:
    """For each index i, build the profile from candles with ts in
    (candles[i].ts - days, candles[i].ts) (strictly before i, trailing).
    Returns {i: profile}. Skips i when the window has < 24*days*0.5 bars
    (i.e. less than half the expected M15 count, ~720 bars for 30d)."""
    out: dict[int, dict[float, float]] = {}
    min_bars = int(24 * 4 * days * 0.5)  # 24h * 4 M15/h * days * 0.5 = ~1440
    # Use two pointers — candles are time-sorted.
    left = 0
    for i, c in enumerate(candles):
        cutoff = c.ts - timedelta(days=days)
        while left < i and candles[left].ts < cutoff:
            left += 1
        window = candles[left:i]  # strictly before i
        if len(window) < min_bars:
            continue
        out[i] = build_profile(window)
    return out


# ---------------------------------------------------------------------------
# Baseline: random M15 close events matched to VPOC event count
# ---------------------------------------------------------------------------

def random_baseline_indices(
    candidate_indices: list[int],
    n_events: int,
    rng: random.Random,
) -> list[int]:
    """Sample *n_events* random candle indices from *candidate_indices*
    (with replacement if n_events > len(candidates))."""
    if n_events <= len(candidate_indices):
        return rng.sample(candidate_indices, n_events)
    return [rng.choice(candidate_indices) for _ in range(n_events)]


# ---------------------------------------------------------------------------
# Bootstrap / permutation tests
# ---------------------------------------------------------------------------

def bootstrap_mean_ratio(
    sample_a: list[float],
    sample_b: list[float],
    n_iter: int,
    rng: random.Random,
) -> tuple[float, float, tuple[float, float]]:
    """Returns (observed_ratio, p_value_lower_bound, ci95).
    observed_ratio = mean(a) / mean(b).
    p = fraction of bootstrap samples where ratio_b_resampled >=
        observed_ratio (one-sided test: H1 claims ratio >= 1.2).

    NOTE on the p-value: we bootstrap BOTH samples independently under the
    null (re-sample both with replacement, compute ratio). Under H0 the
    bootstrap ratio distribution is centred on the observed ratio, so the
    standard Efron-style p is calibrated by computing the fraction of
    bootstrap ratios <= 1.0 (evidence against ratio >= 1.2 is *absence*
    of that pattern). We report that tail probability.
    """
    mean_a = mean(sample_a) if sample_a else 0.0
    mean_b = mean(sample_b) if sample_b else 0.0
    if mean_b == 0:
        return (float("inf") if mean_a > 0 else 1.0, 1.0, (0.0, 0.0))
    obs = mean_a / mean_b
    ratios = []
    n_a, n_b = len(sample_a), len(sample_b)
    for _ in range(n_iter):
        a_res = [sample_a[rng.randrange(n_a)] for _ in range(n_a)]
        b_res = [sample_b[rng.randrange(n_b)] for _ in range(n_b)]
        mb = mean(b_res)
        if mb == 0:
            continue
        ratios.append(mean(a_res) / mb)
    ratios.sort()
    # 95% CI on observed ratio.
    lo_idx = max(0, int(0.025 * len(ratios)) - 1)
    hi_idx = min(len(ratios) - 1, int(0.975 * len(ratios)))
    ci = (ratios[lo_idx], ratios[hi_idx])
    # p = fraction of bootstrap ratios <= 1.0 (null: ratio == 1.0,
    # H1 alt: ratio >= 1.2). Strong evidence for H1 is few ratios <= 1.0.
    p_le1 = sum(1 for r in ratios if r <= 1.0) / len(ratios) if ratios else 1.0
    # Return the one-sided p for "ratio > 1": fraction <= 1.
    return obs, p_le1, ci


def permutation_median_diff(
    sample_a: list[float],
    sample_b: list[float],
    n_iter: int,
    rng: random.Random,
) -> tuple[float, float]:
    """Permutation test: H0 median(a) == median(b). Alt: median(a) < median(b).
    Returns (observed_diff, p_value_one_sided).
    observed_diff = median(a) - median(b); under H2 we want this to be
    strongly negative (LVN traversal faster than VPOC dwell).
    """
    if not sample_a or not sample_b:
        return 0.0, 1.0
    obs = median(sample_a) - median(sample_b)
    pool = list(sample_a) + list(sample_b)
    n_a = len(sample_a)
    more_extreme = 0
    for _ in range(n_iter):
        rng.shuffle(pool)
        a = pool[:n_a]
        b = pool[n_a:]
        if median(a) - median(b) <= obs:
            more_extreme += 1
    p = more_extreme / n_iter
    return obs, p


# ---------------------------------------------------------------------------
# OB co-location check (H1 & H4 order blocks vs VPOC bin)
# ---------------------------------------------------------------------------

@dataclass
class Swing:
    idx: int
    price: float
    kind: str  # "H" or "L"


def swings_fractal(candles: list[Candle], L: int = 2) -> list[Swing]:
    """Simple 5-bar fractal swings (L=2 bars either side)."""
    out: list[Swing] = []
    for i in range(L, len(candles) - L):
        window = candles[i - L: i + L + 1]
        h = candles[i].high
        l = candles[i].low
        if h == max(w.high for w in window) and sum(1 for w in window if w.high == h) == 1:
            out.append(Swing(idx=i, price=h, kind="H"))
        if l == min(w.low for w in window) and sum(1 for w in window if w.low == l) == 1:
            out.append(Swing(idx=i, price=l, kind="L"))
    return sorted(out, key=lambda s: s.idx)


def detect_obs_simple(
    candles: list[Candle], swings: list[Swing],
) -> list[tuple[int, float, float]]:
    """Simplified OB detector for co-location: after each swing, the last
    opposite-colour candle before the swing index is the OB.

    For a swing-HIGH at index k (bearish setup), walk back up to 10 bars
    and pick the last BULLISH candle — that is the bearish OB.
    For a swing-LOW at index k (bullish setup), walk back up to 10 bars
    and pick the last BEARISH candle — that is the bullish OB.

    Returns list of (formation_idx, ob_low, ob_high). Deduplicated by
    formation index.
    """
    seen: set[int] = set()
    out: list[tuple[int, float, float]] = []
    for s in swings:
        k = s.idx
        lo = max(0, k - 10)
        if s.kind == "H":
            for j in range(k - 1, lo - 1, -1):
                c = candles[j]
                if c.close > c.open:  # bullish candle -> bearish OB
                    if j in seen:
                        break
                    seen.add(j)
                    out.append((j, c.low, c.high))
                    break
        else:
            for j in range(k - 1, lo - 1, -1):
                c = candles[j]
                if c.close < c.open:  # bearish candle -> bullish OB
                    if j in seen:
                        break
                    seen.add(j)
                    out.append((j, c.low, c.high))
                    break
    return out


def ob_zones_at_or_before(
    obs: list[tuple[int, float, float]],
    ts_limit_idx: int,
) -> list[tuple[float, float]]:
    """Return list of (low, high) for every OB whose formation index < ts_limit_idx.
    We use index instead of timestamp because obs are computed on the same
    timeframe."""
    return [(lo, hi) for (idx, lo, hi) in obs if idx < ts_limit_idx]


def bin_overlaps_any_ob(
    bin_low: float,
    ob_zones: list[tuple[float, float]],
) -> bool:
    """True if [bin_low, bin_low + BIN_SIZE) intersects any OB zone."""
    bin_high = bin_low + BIN_SIZE
    for lo, hi in ob_zones:
        if hi >= bin_low and lo <= bin_high:
            return True
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    rng = random.Random(SEED)

    m15 = load_candles(M15_PATH)
    h1 = load_candles(H1_PATH)
    h4 = load_candles(H4_PATH)

    # Rolling profiles (30-day trailing, keyed by M15 index).
    profiles = build_rolling_profiles(m15, days=ROLLING_DAYS)
    profile_indices = sorted(profiles.keys())
    first_profile_idx = profile_indices[0] if profile_indices else None
    last_profile_idx = profile_indices[-1] if profile_indices else None

    # ATR series on M15.
    atr = atr_series(m15, ATR_WINDOW)

    # H1 / H4 OB detection (for co-location check).
    h1_swings = swings_fractal(h1, L=2)
    h4_swings = swings_fractal(h4, L=2)
    h1_obs = detect_obs_simple(h1, h1_swings)
    h4_obs = detect_obs_simple(h4, h4_swings)

    # Map H1 / H4 formation timestamp -> M15 index for "is OB already
    # formed at M15 index i?" checks.
    m15_ts_to_idx = {c.ts: i for i, c in enumerate(m15)}

    def h_ob_zones_before_m15_idx(
        obs: list[tuple[int, float, float]],
        htf_candles: list[Candle],
        m15_i: int,
    ) -> list[tuple[float, float]]:
        t_limit = m15[m15_i].ts
        return [
            (lo, hi)
            for (idx, lo, hi) in obs
            if htf_candles[idx].ts <= t_limit
        ]

    # --------------------------------------------------------------
    # VPOC touch events + 12-bar forward reaction (H1)
    # --------------------------------------------------------------
    vpoc_events = find_vpoc_touch_events(m15, profiles)

    vpoc_abs_exc: list[float] = []   # |range| / ATR, for H1 test
    vpoc_signed: list[float] = []    # signed close-close move / ATR, diagnostic

    for ev in vpoc_events:
        exc = forward_excursion_atr(m15, atr, ev.i, FWD_BARS)
        if exc is None:
            continue
        signed = forward_signed_move_atr(m15, atr, ev.i, FWD_BARS)
        vpoc_abs_exc.append(exc)
        if signed is not None:
            vpoc_signed.append(signed)

    # Baseline: random M15 closes in the same eligibility window (only
    # indices that (a) have a rolling profile, (b) have FWD_BARS room,
    # (c) have atr > 0). MATCH SAMPLE COUNT to VPOC events.
    eligible = [
        i for i in profile_indices
        if i + FWD_BARS < len(m15) and atr[i] > 0
    ]
    n_vpoc = len(vpoc_abs_exc)
    baseline_abs_exc: list[float] = []
    if eligible and n_vpoc > 0:
        # Sample one baseline per VPOC event count. For robustness, also
        # compute the full-population mean as a secondary check.
        baseline_sample_idx = random_baseline_indices(eligible, n_vpoc * 10, rng)
        for i in baseline_sample_idx:
            e = forward_excursion_atr(m15, atr, i, FWD_BARS)
            if e is not None:
                baseline_abs_exc.append(e)

    # H1 test: ratio of means.
    ratio_obs, ratio_p, ratio_ci = bootstrap_mean_ratio(
        vpoc_abs_exc, baseline_abs_exc, N_BOOT, rng,
    )

    # --------------------------------------------------------------
    # VPOC OB co-location
    # --------------------------------------------------------------
    colocated_h1 = 0
    colocated_h4 = 0
    colocated_any = 0
    total_col = 0
    for ev in vpoc_events:
        h1_zones = h_ob_zones_before_m15_idx(h1_obs, h1, ev.i)
        h4_zones = h_ob_zones_before_m15_idx(h4_obs, h4, ev.i)
        in_h1 = bin_overlaps_any_ob(ev.bin_low, h1_zones)
        in_h4 = bin_overlaps_any_ob(ev.bin_low, h4_zones)
        colocated_h1 += 1 if in_h1 else 0
        colocated_h4 += 1 if in_h4 else 0
        colocated_any += 1 if (in_h1 or in_h4) else 0
        total_col += 1

    # --------------------------------------------------------------
    # LVN traversal vs VPOC dwell (H2)
    # --------------------------------------------------------------
    lvn_events = find_lvn_entry_events(m15, profiles)
    vpoc_dwell_events = find_vpoc_entry_events_for_dwell(m15, profiles)

    lvn_bars: list[float] = []
    vpoc_bars: list[float] = []
    lvn_censored = 0
    vpoc_censored = 0
    for (i, b) in lvn_events:
        d = dwell_bars(m15, i, b, DWELL_MAX_BARS)
        if d is None:
            lvn_censored += 1
            continue
        lvn_bars.append(float(d))
    for (i, b) in vpoc_dwell_events:
        d = dwell_bars(m15, i, b, DWELL_MAX_BARS)
        if d is None:
            vpoc_censored += 1
            continue
        vpoc_bars.append(float(d))

    med_diff, perm_p = permutation_median_diff(lvn_bars, vpoc_bars, N_PERM, rng)

    # --------------------------------------------------------------
    # Report
    # --------------------------------------------------------------
    def fmt_ci(ci: tuple[float, float]) -> str:
        return f"[{ci[0]:.3f}, {ci[1]:.3f}]"

    vpoc_n = len(vpoc_abs_exc)
    base_n = len(baseline_abs_exc)
    lvn_n = len(lvn_bars)
    vpoc_dwell_n = len(vpoc_bars)

    h1_pass = (ratio_obs >= 1.2) and (ratio_p < ALPHA_PER_TEST)
    lvn_med = median(lvn_bars) if lvn_bars else float("nan")
    vpoc_med = median(vpoc_bars) if vpoc_bars else float("nan")
    h2_ratio = (lvn_med / vpoc_med) if (vpoc_bars and vpoc_med > 0) else float("nan")
    h2_pass = (
        vpoc_bars
        and lvn_bars
        and h2_ratio <= 0.5
        and perm_p < ALPHA_PER_TEST
    )

    colocate_pct = (colocated_any / total_col * 100.0) if total_col else 0.0

    lines: list[str] = []
    lines.append("# Q-13.10 Volume Profile (VPOC / LVN) — XAUUSD")
    lines.append("")
    lines.append(
        "Generated by `research/academic_pipeline/scripts/q_13_10_volume_profile.py` "
        "(local, $0 API)."
    )
    lines.append("")
    lines.append("## CRITICAL DATA LIMITATION")
    lines.append("")
    lines.append(
        "XAUUSD spot CFD OHLC uses **tick volume** (one unit per broker price "
        "update), not **traded volume** (cleared notional on COMEX / LBMA). Tick "
        "volume is a known but imperfect proxy for true activity, and is itself "
        "biased by price volatility (fast markets print more ticks at the same "
        "notional size). **Every finding below is tick-weighted and does not "
        "equal true-volume-weighted results.** Any promotion decision based on "
        "this analysis must acknowledge this proxy limitation."
    )
    lines.append("")
    lines.append("## Hypotheses (pre-registered before data inspection)")
    lines.append("")
    lines.append(
        "- **H1**: VPOC reactions show mean absolute 12-candle move (in ATR "
        "units) >= 1.2 x mean absolute 12-candle move from random M15 closes "
        "in the same eligibility window."
    )
    lines.append(
        "- **H2**: LVN traversal time (median bars to first close outside the "
        "LVN bin) <= 50 percent of VPOC dwell time (median bars to first "
        "close outside the VPOC bin, from the same kind of first-entry event)."
    )
    lines.append("")
    lines.append(
        f"Bonferroni: {N_TESTS} primary tests, family alpha = {ALPHA_FAMILY}, "
        f"per-test alpha = {ALPHA_PER_TEST:.3f}."
    )
    lines.append("")
    lines.append("Cross-check (not part of the Bonferroni family): if >= 80% of VPOC "
                 "events co-locate with an H1 or H4 OB zone, any VPOC reaction edge "
                 "is NOT novel — it just restates the OB edge.")
    lines.append("")
    lines.append("## Data")
    lines.append("")
    lines.append(f"- `data/historical_2026/XAUUSD_M15.csv` — {len(m15)} bars, "
                 f"{m15[0].ts.date()} .. {m15[-1].ts.date()}")
    lines.append(f"- `data/historical_2026/XAUUSD_H1.csv` — {len(h1)} bars "
                 f"(OB context).")
    lines.append(f"- `data/historical_2026/XAUUSD_H4.csv` — {len(h4)} bars "
                 f"(OB context).")
    if first_profile_idx is not None:
        lines.append(
            f"- Rolling profile eligibility window: M15 idx "
            f"{first_profile_idx}..{last_profile_idx} "
            f"({m15[first_profile_idx].ts.date()} .. "
            f"{m15[last_profile_idx].ts.date()}). "
            "First ~30 days are warm-up (no profile)."
        )
    lines.append("")
    lines.append("## Method")
    lines.append("")
    lines.append(
        f"- **Volume profile**: 30-day rolling window, ${BIN_SIZE:.2f} price "
        "bins. For each M15 candle in the window, tick_volume is spread "
        "uniformly (TPO-equal) across every $1 bin that the candle's "
        "high-low range overlaps."
    )
    lines.append(
        "- **VPOC**: the single bin with highest cumulative TPO-equal volume "
        "in the 30-day window at bar i (exclusive of i)."
    )
    lines.append(
        f"- **LVN**: any bin with cumulative volume > 0 but < "
        f"{LVN_THRESHOLD_FRAC * 100:.0f}% of the VPOC volume in the SAME "
        "profile. (Empty bins — no prints in the window — are NOT counted "
        "as LVN; a never-visited price isn't a 'low-volume node' so much "
        "as an untouched area.)"
    )
    lines.append(
        f"- **Touch / entry event** (first-entry): an M15 close transitions "
        f"from outside the bin to inside the bin. Dwell = bars (>=1) until "
        f"the first close back outside the bin. Dwell walk capped at "
        f"{DWELL_MAX_BARS} M15 bars (3 days)."
    )
    lines.append(
        f"- **Reaction**: forward excursion over {FWD_BARS} M15 bars = "
        f"(max_high - min_low) over bars i+1..i+{FWD_BARS}, divided by "
        f"ATR({ATR_WINDOW}) at bar i. This is the symmetric absolute-move "
        "metric. Signed close-close move / ATR reported as a diagnostic."
    )
    lines.append(
        "- **Baseline (H1)**: random M15 close events from the same "
        "eligibility set (has profile, has ATR, has 12 forward bars). "
        "Sampled with replacement at 10x the VPOC event count for variance "
        "reduction. RNG seed = {SEED}.".replace("{SEED}", str(SEED))
    )
    lines.append(
        f"- **Inference**: bootstrap (N={N_BOOT}) for the ratio of means "
        f"(H1); permutation (N={N_PERM}) for the median difference (H2). "
        "Both one-sided as stated above."
    )
    lines.append("")
    # Diagnostic: how often is price inside any bin of the VPOC?
    vpoc_bin_total_closes = 0
    eligible_for_diag = 0
    for i in profile_indices:
        prof = profiles[i]
        vp = vpoc(prof)
        if vp is None:
            continue
        eligible_for_diag += 1
        vpoc_bin, _ = vp
        if _bin_low(m15[i].close) == vpoc_bin:
            vpoc_bin_total_closes += 1
    vpoc_close_rate = (
        vpoc_bin_total_closes / eligible_for_diag * 100.0
        if eligible_for_diag else 0.0
    )

    lines.append("## Diagnostic — VPOC bin is a SINGLE $1 bin")
    lines.append("")
    lines.append(
        f"- M15 closes inside the VPOC bin (any, not first-entry): "
        f"**{vpoc_bin_total_closes}** of {eligible_for_diag} eligible bars "
        f"({vpoc_close_rate:.2f}%)."
    )
    lines.append(
        "- This rarity is by construction: the VPOC is exactly one $1 bin, "
        "and price is rarely at that specific bin. A widened 'VPOC zone' "
        "(e.g. VAH/VAL 70% value area) would produce more events but is "
        "NOT what the pre-registered hypothesis tests. The small VPOC "
        "event count is therefore the honest answer — not a bug."
    )
    lines.append("")
    lines.append("## H1 — VPOC reactions vs random baseline")
    lines.append("")
    lines.append(f"- VPOC touch events (first-entry, with forward room): **{vpoc_n}**")
    lines.append(f"- Baseline random-level events: **{base_n}**")
    if vpoc_n < 15:
        lines.append("")
        lines.append(
            f"> **Underpowered** (n={vpoc_n} < 15). Effect size reported; "
            "significance not claimed."
        )
    lines.append("")
    if vpoc_n > 0 and base_n > 0:
        lines.append(
            f"| metric | VPOC | Baseline | ratio (VPOC / baseline) |"
        )
        lines.append("|---|---|---|---|")
        lines.append(
            f"| mean abs 12-bar move (ATR) | "
            f"{mean(vpoc_abs_exc):.3f} | "
            f"{mean(baseline_abs_exc):.3f} | "
            f"{ratio_obs:.3f} |"
        )
        if vpoc_signed:
            lines.append(
                f"| mean signed 12-bar move (ATR) | "
                f"{mean(vpoc_signed):+.3f} | (n/a) | (diagnostic) |"
            )
        lines.append("")
        lines.append(f"- Bootstrap 95% CI on ratio: {fmt_ci(ratio_ci)}")
        lines.append(
            f"- One-sided bootstrap p (P[bootstrap ratio <= 1.0]): "
            f"**{ratio_p:.4f}**"
        )
        lines.append(
            f"- H1 decision @ alpha={ALPHA_PER_TEST:.3f}: "
            f"**{'PASS' if h1_pass else 'FAIL'}** "
            f"(need ratio >= 1.2 AND p < {ALPHA_PER_TEST:.3f}; "
            f"observed ratio = {ratio_obs:.3f}, p = {ratio_p:.4f})"
        )
    else:
        lines.append("_Insufficient sample for H1._")
    lines.append("")
    lines.append("## H2 — LVN traversal vs VPOC dwell")
    lines.append("")
    lines.append(
        f"- LVN first-entry events (uncensored): **{lvn_n}** "
        f"(censored at {DWELL_MAX_BARS} bars: {lvn_censored})"
    )
    lines.append(
        f"- VPOC first-entry events (uncensored): **{vpoc_dwell_n}** "
        f"(censored at {DWELL_MAX_BARS} bars: {vpoc_censored})"
    )
    if lvn_n < 15 or vpoc_dwell_n < 15:
        lines.append("")
        lines.append(
            f"> **Underpowered** (lvn_n={lvn_n}, vpoc_n={vpoc_dwell_n}; "
            "threshold 15). Effect size reported; significance not claimed."
        )
    lines.append("")
    if lvn_n > 0 and vpoc_dwell_n > 0:
        lines.append(f"| metric | LVN | VPOC | ratio (LVN / VPOC) |")
        lines.append("|---|---|---|---|")
        lines.append(
            f"| median bars to exit | "
            f"{lvn_med:.1f} | {vpoc_med:.1f} | {h2_ratio:.3f} |"
        )
        lines.append(
            f"| mean bars to exit | "
            f"{mean(lvn_bars):.2f} | {mean(vpoc_bars):.2f} | "
            f"{(mean(lvn_bars)/mean(vpoc_bars) if mean(vpoc_bars) else float('nan')):.3f} |"
        )
        lines.append("")
        lines.append(
            f"- Permutation one-sided p (H0: median(LVN)-median(VPOC) == 0; "
            f"alt: median(LVN) < median(VPOC)): **{perm_p:.4f}**"
        )
        lines.append(
            f"- H2 decision @ alpha={ALPHA_PER_TEST:.3f}: "
            f"**{'PASS' if h2_pass else 'FAIL'}** "
            f"(need median ratio <= 0.5 AND p < {ALPHA_PER_TEST:.3f}; "
            f"observed ratio = {h2_ratio:.3f}, p = {perm_p:.4f})"
        )
    else:
        lines.append("_Insufficient sample for H2._")
    lines.append("")
    lines.append("## Cross-check — VPOC vs OB co-location")
    lines.append("")
    if total_col:
        lines.append(
            f"- VPOC events evaluated: **{total_col}**"
        )
        lines.append(
            f"- Co-located with an H1 OB zone: {colocated_h1} "
            f"({colocated_h1 / total_col * 100:.1f}%)"
        )
        lines.append(
            f"- Co-located with an H4 OB zone: {colocated_h4} "
            f"({colocated_h4 / total_col * 100:.1f}%)"
        )
        lines.append(
            f"- Co-located with H1 OR H4 OB zone: **{colocated_any} "
            f"({colocate_pct:.1f}%)**"
        )
        lines.append("")
        if colocate_pct >= 80.0:
            lines.append(
                f"**Verdict: co-location >= 80% ({colocate_pct:.1f}%).** "
                "Any VPOC reaction edge is NOT novel — it just restates the "
                "existing OB zone edge. Do NOT promote VPOC as a separate "
                "feature."
            )
        else:
            lines.append(
                f"**Verdict: co-location = {colocate_pct:.1f}% < 80%.** "
                "If H1 passes, VPOC carries at least partial independent "
                "signal beyond existing OB zones."
            )
    else:
        lines.append("_No VPOC events in the sample to co-locate._")
    lines.append("")
    lines.append("## Combined decision")
    lines.append("")
    lines.append(
        f"- H1 (VPOC reaction size vs baseline): "
        f"**{'PASS' if h1_pass else 'FAIL'}** "
        f"(obs ratio = {ratio_obs:.3f}, p = {ratio_p:.4f})"
    )
    lines.append(
        f"- H2 (LVN traversal speed vs VPOC dwell): "
        f"**{'PASS' if h2_pass else 'FAIL'}** "
        f"(obs ratio = {h2_ratio:.3f}, p = {perm_p:.4f})"
    )
    lines.append(
        f"- OB co-location: {colocate_pct:.1f}% "
        f"({'novelty KILLED' if colocate_pct >= 80.0 else 'novelty possible'})"
    )
    lines.append("")
    if h1_pass and colocate_pct < 80.0 and h2_pass:
        verdict = (
            "**BOTH tests survive Bonferroni AND co-location < 80% — "
            "volume profile carries potentially novel signal. Recommend: "
            "SHADOW-LOG in production for 30+ events before any gate "
            "change. Re-evaluate on true-volume data (COMEX futures) "
            "before any live deployment — tick-volume proxy must not be "
            "the sole evidence.**"
        )
    elif (h1_pass or h2_pass) and colocate_pct < 80.0:
        verdict = (
            "**Only one primary test passes. Partial signal at best. "
            "Do NOT promote. Shadow log is optional; do not spend API on "
            "a single-edge finding built on a tick-volume proxy.**"
        )
    elif colocate_pct >= 80.0:
        verdict = (
            "**VPOC co-locates with existing OBs >= 80%. Even if any "
            "test passes statistically, the signal is not novel. "
            "KILL this feature — the edge lives in OBs already.**"
        )
    else:
        verdict = (
            "**Both primary tests fail. No volume-profile edge detected "
            "on tick-volume proxy. KILL — do not pursue further on this "
            "data source.**"
        )
    lines.append(verdict)
    lines.append("")
    lines.append("## Caveats & reproducibility")
    lines.append("")
    lines.append(
        f"- Deterministic. RNG seed = {SEED}. Bootstrap N = {N_BOOT}; "
        f"permutation N = {N_PERM}."
    )
    lines.append(
        f"- TPO-equal volume distribution is a standard approximation. An "
        "alternative HLC-weighted (TPV) distribution might produce different "
        "VPOC bins in choppy sessions; not tested here."
    )
    lines.append(
        "- Rolling window is 30 calendar days, not 30 trading days. At the "
        "FX/CFD level this includes weekends (no bars), which is acceptable "
        "because we filter by bar timestamp, not by calendar-day count."
    )
    lines.append(
        "- Dwell / traversal is censored at 3 days (288 M15 bars). Censored "
        "events are EXCLUDED from the median and the permutation test. "
        "If the censoring rates differ materially between LVN and VPOC, "
        "the comparison is biased; censoring rates are reported above."
    )
    lines.append(
        "- OB detection here uses a simplified 5-bar-fractal swing + last "
        "opposite candle backward walk (up to 10 bars). This is a proxy "
        "for the production `identify_order_blocks` in "
        "`src/components/market_state.py` and is sufficient for a "
        "co-location sanity check; it is NOT the production gate."
    )
    lines.append("")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")

    # Console summary for the operator.
    print(f"Wrote {OUT_PATH}")
    print(f"  VPOC events={vpoc_n} baseline={base_n} ratio={ratio_obs:.3f} p={ratio_p:.4f}")
    print(f"  LVN uncens={lvn_n} VPOC-dwell uncens={vpoc_dwell_n} "
          f"med_diff={med_diff:.1f} p={perm_p:.4f}")
    print(f"  VPOC-OB co-location (H1|H4): {colocate_pct:.1f}% of {total_col}")


if __name__ == "__main__":
    main()
