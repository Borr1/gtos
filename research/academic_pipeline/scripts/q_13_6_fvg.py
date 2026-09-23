"""Q-13.6 / Q-2.4 FVG / Liquidity-Void Characterization for XAUUSD (M15 + H1).

Pre-registered hypotheses live in:
  research/academic_pipeline/results/Q-13_6_fvg.md  (Section 1)

Pipeline (zero API cost, local only):
  1. Load M15 + H1 candles from data/historical_2026/XAUUSD_*.csv.
  2. Detect 3-candle FVGs using the same convention as
     src/components/market_state.py::identify_fvgs — indices (i-1, i, i+1):
       - Bullish FVG: candles[i+1].low > candles[i-1].high
       - Bearish FVG: candles[i+1].high < candles[i-1].low
     NOTE: the task brief described the pattern with indices (i-2, i) with
     label swap; we use the production (i-1, i, i+1) convention because it
     is the system's operational definition. This is documented in the
     report.
  3. For each FVG compute:
       - gap_size_pct_atr: gap size / ATR14 at candle i-1
       - time_to_fill_candles: bars until price returns into zone
       - continuation_atr: max price move in impulse direction from
         candle i+1 close before fill (in ATR units at i-1)
       - filled_at_h: bool for horizons 20, 50, 100
  4. Classify each FVG:
       - IMPULSE-FVG: (high[i] - low[i]) >= 1.5 * ATR14(i-1)
         (mirrors detect_structure_breaks displacement_present threshold).
       - OB-ADJACENT: at least one OB (detected via the same swings + BOS
         pipeline as market_state.py) has formation_index within
         +/- OB_ADJ_WINDOW candles of i (the FVG's gap candle).
       - ISOLATED: not OB-ADJACENT.
  5. Two-proportion z-tests on fill-rate at h=50:
       - IMPULSE-FVG vs ISOLATED-only (NOT OB-ADJACENT and NOT IMPULSE).
     Bonferroni divisor = 2 (M15 and H1).
  6. Report statistics + verdict against pre-registered thresholds.

Output: research/academic_pipeline/results/Q-13_6_fvg.md
  Section 1 is the pre-registered hypothesis and is NOT touched.
  Sections 2+ are appended by this script.
"""

from __future__ import annotations

import csv
import math
import statistics
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Paths (absolute)
# ---------------------------------------------------------------------------

ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
SRC = ROOT / "src"
M15_CSV = ROOT / "data" / "historical_2026" / "XAUUSD_M15.csv"
H1_CSV = ROOT / "data" / "historical_2026" / "XAUUSD_H1.csv"
OUT_MD = ROOT / "research" / "academic_pipeline" / "results" / "Q-13_6_fvg.md"

# Inject project root so `from src.components.market_state import ...` resolves
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.components.market_state import (  # type: ignore  # noqa: E402
    detect_swings,
    identify_structure,
    detect_structure_breaks,
    identify_order_blocks,
)

# ---------------------------------------------------------------------------
# Pre-registered parameters
# ---------------------------------------------------------------------------

ATR_PERIOD = 14
IMPULSE_ATR_MULT = 1.5       # same as market_state.detect_structure_breaks
OB_ADJ_WINDOW = 10           # +/- candles around FVG gap candle
HORIZONS = [20, 50, 100]     # fill-horizons in candles
PRIMARY_HORIZON = 50
MIN_N_M15 = 20
MIN_N_H1 = 10


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------

def load_candles(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "time": r["time"],
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "volume": float(r.get("volume", 0) or 0),
            })
    return rows


# ---------------------------------------------------------------------------
# ATR (True Range, simple moving average, period=ATR_PERIOD)
# ---------------------------------------------------------------------------

def compute_atr(candles: list[dict], period: int = ATR_PERIOD) -> list[Optional[float]]:
    """Return ATR14 aligned to candles. atr[i] is the ATR ending at candle i.

    Uses the simple moving average of true range (Wilder-lite). None for
    indices where < period true ranges are available.
    """
    n = len(candles)
    tr: list[float] = [0.0] * n
    for i in range(n):
        h = candles[i]["high"]
        l = candles[i]["low"]
        if i == 0:
            tr[i] = h - l
        else:
            pc = candles[i - 1]["close"]
            tr[i] = max(h - l, abs(h - pc), abs(l - pc))
    out: list[Optional[float]] = [None] * n
    for i in range(period - 1, n):
        out[i] = sum(tr[i - period + 1:i + 1]) / period
    return out


# ---------------------------------------------------------------------------
# FVG detection — production (i-1, i, i+1) convention.
# ---------------------------------------------------------------------------

@dataclass
class FVG:
    idx: int                 # gap-candle (middle) index
    side: str                # "bull" (impulse up) or "bear" (impulse down)
    top: float               # zone upper bound
    bottom: float            # zone lower bound
    gap_size: float          # top - bottom (in price)
    gap_size_pct_atr: Optional[float]
    impulse_candle_range: float  # high[i] - low[i]
    atr_at_i_minus_1: Optional[float]
    is_impulse: bool         # (high[i]-low[i]) >= 1.5 * atr14[i-1]
    # Filled in later:
    is_ob_adjacent: bool = False
    time_to_fill: Optional[int] = None   # candles from i+1 to fill; None if unfilled
    filled_h20: bool = False
    filled_h50: bool = False
    filled_h100: bool = False
    continuation_atr: float = 0.0        # max distance (ATR units) beyond entry-side of gap before fill


def detect_fvgs(candles: list[dict], atr: list[Optional[float]]) -> list[FVG]:
    out: list[FVG] = []
    n = len(candles)
    for i in range(1, n - 1):
        lo_iplus = candles[i + 1]["low"]
        hi_iminus = candles[i - 1]["high"]
        hi_iplus = candles[i + 1]["high"]
        lo_iminus = candles[i - 1]["low"]
        range_i = candles[i]["high"] - candles[i]["low"]
        atr_i_minus_1 = atr[i - 1] if i - 1 < len(atr) else None

        # Bullish FVG (impulse up leaves a gap above): low[i+1] > high[i-1]
        if lo_iplus > hi_iminus:
            gap_size = lo_iplus - hi_iminus
            is_impulse = (atr_i_minus_1 is not None
                          and range_i >= IMPULSE_ATR_MULT * atr_i_minus_1)
            out.append(FVG(
                idx=i, side="bull",
                top=lo_iplus, bottom=hi_iminus,
                gap_size=gap_size,
                gap_size_pct_atr=(gap_size / atr_i_minus_1
                                  if atr_i_minus_1 and atr_i_minus_1 > 0 else None),
                impulse_candle_range=range_i,
                atr_at_i_minus_1=atr_i_minus_1,
                is_impulse=is_impulse,
            ))

        # Bearish FVG: high[i+1] < low[i-1]
        elif hi_iplus < lo_iminus:
            gap_size = lo_iminus - hi_iplus
            is_impulse = (atr_i_minus_1 is not None
                          and range_i >= IMPULSE_ATR_MULT * atr_i_minus_1)
            out.append(FVG(
                idx=i, side="bear",
                top=lo_iminus, bottom=hi_iplus,
                gap_size=gap_size,
                gap_size_pct_atr=(gap_size / atr_i_minus_1
                                  if atr_i_minus_1 and atr_i_minus_1 > 0 else None),
                impulse_candle_range=range_i,
                atr_at_i_minus_1=atr_i_minus_1,
                is_impulse=is_impulse,
            ))

    return out


# ---------------------------------------------------------------------------
# Fill & continuation measurement (look-ahead-safe: only uses indices > i+1)
# ---------------------------------------------------------------------------

def measure_fill_and_continuation(fvgs: list[FVG], candles: list[dict],
                                  atr: list[Optional[float]]) -> None:
    """Compute, for each FVG:
      - time_to_fill: bars from i+1 until price returns into the gap zone.
      - filled_h20/h50/h100: fill by that many candles after i+1.
      - continuation_atr: max adverse-to-fill travel (ATR units) before fill.

    Fill rule:
      * Bull FVG: filled when a candle's LOW <= FVG.top (price retraces DOWN into the gap).
      * Bear FVG: filled when a candle's HIGH >= FVG.bottom (price retraces UP into the gap).

    Continuation rule (impulse direction):
      * Bull FVG: max((candle.high - FVG.top) for candles until fill), / ATR.
      * Bear FVG: max((FVG.bottom - candle.low) for candles until fill), / ATR.
    """
    n = len(candles)
    for fvg in fvgs:
        start = fvg.idx + 2  # first candle AFTER the 3-candle pattern
        denom = fvg.atr_at_i_minus_1 if (fvg.atr_at_i_minus_1 and fvg.atr_at_i_minus_1 > 0) else None
        max_cont = 0.0
        fill_bar: Optional[int] = None
        for k in range(start, n):
            c = candles[k]
            if fvg.side == "bull":
                cont = c["high"] - fvg.top
                if cont > max_cont:
                    max_cont = cont
                if c["low"] <= fvg.top:
                    fill_bar = k - start + 1  # candles since i+1 (1-indexed)
                    break
            else:
                cont = fvg.bottom - c["low"]
                if cont > max_cont:
                    max_cont = cont
                if c["high"] >= fvg.bottom:
                    fill_bar = k - start + 1
                    break
        fvg.time_to_fill = fill_bar
        fvg.continuation_atr = (max_cont / denom) if denom else 0.0
        fvg.filled_h20 = fill_bar is not None and fill_bar <= 20
        fvg.filled_h50 = fill_bar is not None and fill_bar <= 50
        fvg.filled_h100 = fill_bar is not None and fill_bar <= 100


# ---------------------------------------------------------------------------
# OB-adjacency classification
# ---------------------------------------------------------------------------

def classify_ob_adjacency(fvgs: list[FVG], candles: list[dict]) -> None:
    """Detect OBs using the same pipeline as market_state.py and mark FVGs
    whose gap-candle is within +/- OB_ADJ_WINDOW of any OB's formation_index.
    """
    swings = detect_swings(candles, min_bars=2)
    structure = identify_structure(swings)
    events = detect_structure_breaks(candles, swings, structure)
    obs = identify_order_blocks(candles, events)
    ob_indices = sorted(ob.formation_index for ob in obs)
    if not ob_indices:
        return
    # Two-pointer sweep (FVGs sorted by idx)
    fvgs_sorted = sorted(fvgs, key=lambda f: f.idx)
    j = 0
    for fvg in fvgs_sorted:
        lo = fvg.idx - OB_ADJ_WINDOW
        hi = fvg.idx + OB_ADJ_WINDOW
        # advance j past indices < lo
        while j < len(ob_indices) and ob_indices[j] < lo:
            j += 1
        # check if any ob_idx in [lo, hi]
        fvg.is_ob_adjacent = (j < len(ob_indices) and ob_indices[j] <= hi)


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------

def prop_ci(k: int, n: int) -> tuple[float, float]:
    """Wilson 95% CI for a proportion."""
    if n == 0:
        return (0.0, 0.0)
    z = 1.96
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    spread = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - spread), min(1.0, centre + spread))


def two_prop_z(k1: int, n1: int, k2: int, n2: int) -> tuple[float, float]:
    """Two-proportion z-test (two-sided). Returns (delta_pp, p_value)."""
    if n1 == 0 or n2 == 0:
        return (0.0, 1.0)
    p1 = k1 / n1
    p2 = k2 / n2
    p = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return ((p1 - p2) * 100.0, 1.0)
    z = (p1 - p2) / se
    # normal CDF via erf
    p_two = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return ((p1 - p2) * 100.0, p_two)


def percentile(xs: list[float], p: float) -> float:
    if not xs:
        return float("nan")
    xs_sorted = sorted(xs)
    k = (len(xs_sorted) - 1) * p / 100.0
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return xs_sorted[int(k)]
    return xs_sorted[lo] * (hi - k) + xs_sorted[hi] * (k - lo)


def summarize_numeric(xs: list[float]) -> dict:
    xs = [x for x in xs if x is not None and not math.isnan(x)]
    if not xs:
        return {"n": 0}
    return {
        "n": len(xs),
        "mean": statistics.fmean(xs),
        "median": statistics.median(xs),
        "p25": percentile(xs, 25),
        "p75": percentile(xs, 75),
        "min": min(xs),
        "max": max(xs),
    }


# ---------------------------------------------------------------------------
# Per-timeframe analysis
# ---------------------------------------------------------------------------

@dataclass
class TFReport:
    tf: str
    n_candles: int
    n_fvgs_total: int
    n_bull: int
    n_bear: int
    n_impulse: int
    n_ob_adj: int
    n_isolated_only: int           # NOT OB-ADJACENT and NOT IMPULSE
    gap_size_atr_summary: dict
    impulse_gap_size_atr_summary: dict
    isolated_gap_size_atr_summary: dict
    fill_rate_all: dict            # h20, h50, h100
    fill_rate_impulse: dict
    fill_rate_isolated: dict
    fill_rate_ob_adj: dict
    ttf_summary_all: dict
    ttf_summary_impulse: dict
    ttf_summary_isolated: dict
    cont_summary_impulse: dict
    cont_summary_isolated: dict
    z_test_impulse_vs_isolated_h50: dict  # delta_pp, p_value
    first_time: str
    last_time: str


def analyze_timeframe(tf_name: str, csv_path: Path) -> TFReport:
    candles = load_candles(csv_path)
    atr = compute_atr(candles)
    fvgs = detect_fvgs(candles, atr)
    measure_fill_and_continuation(fvgs, candles, atr)
    classify_ob_adjacency(fvgs, candles)

    gap_atr_all = [f.gap_size_pct_atr for f in fvgs if f.gap_size_pct_atr is not None]
    gap_atr_impulse = [f.gap_size_pct_atr for f in fvgs
                       if f.is_impulse and f.gap_size_pct_atr is not None]
    isolated = [f for f in fvgs if (not f.is_ob_adjacent) and (not f.is_impulse)]
    gap_atr_isolated = [f.gap_size_pct_atr for f in isolated if f.gap_size_pct_atr is not None]

    def fr(subset: list[FVG]) -> dict:
        if not subset:
            return {"n": 0, "h20": 0.0, "h50": 0.0, "h100": 0.0,
                    "k20": 0, "k50": 0, "k100": 0,
                    "ci20": (0.0, 0.0), "ci50": (0.0, 0.0), "ci100": (0.0, 0.0)}
        n = len(subset)
        k20 = sum(1 for f in subset if f.filled_h20)
        k50 = sum(1 for f in subset if f.filled_h50)
        k100 = sum(1 for f in subset if f.filled_h100)
        return {
            "n": n,
            "h20": k20 / n, "k20": k20, "ci20": prop_ci(k20, n),
            "h50": k50 / n, "k50": k50, "ci50": prop_ci(k50, n),
            "h100": k100 / n, "k100": k100, "ci100": prop_ci(k100, n),
        }

    impulse_subset = [f for f in fvgs if f.is_impulse]
    ob_adj_subset = [f for f in fvgs if f.is_ob_adjacent]

    ttf_all = [float(f.time_to_fill) for f in fvgs if f.time_to_fill is not None]
    ttf_imp = [float(f.time_to_fill) for f in impulse_subset if f.time_to_fill is not None]
    ttf_iso = [float(f.time_to_fill) for f in isolated if f.time_to_fill is not None]
    cont_imp = [f.continuation_atr for f in impulse_subset]
    cont_iso = [f.continuation_atr for f in isolated]

    fr_all = fr(fvgs)
    fr_imp = fr(impulse_subset)
    fr_iso = fr(isolated)
    fr_ob = fr(ob_adj_subset)

    if fr_imp["n"] > 0 and fr_iso["n"] > 0:
        delta, p_val = two_prop_z(fr_imp["k50"], fr_imp["n"],
                                  fr_iso["k50"], fr_iso["n"])
    else:
        delta, p_val = 0.0, 1.0

    return TFReport(
        tf=tf_name,
        n_candles=len(candles),
        n_fvgs_total=len(fvgs),
        n_bull=sum(1 for f in fvgs if f.side == "bull"),
        n_bear=sum(1 for f in fvgs if f.side == "bear"),
        n_impulse=len(impulse_subset),
        n_ob_adj=len(ob_adj_subset),
        n_isolated_only=len(isolated),
        gap_size_atr_summary=summarize_numeric(gap_atr_all),
        impulse_gap_size_atr_summary=summarize_numeric(gap_atr_impulse),
        isolated_gap_size_atr_summary=summarize_numeric(gap_atr_isolated),
        fill_rate_all=fr_all,
        fill_rate_impulse=fr_imp,
        fill_rate_isolated=fr_iso,
        fill_rate_ob_adj=fr_ob,
        ttf_summary_all=summarize_numeric(ttf_all),
        ttf_summary_impulse=summarize_numeric(ttf_imp),
        ttf_summary_isolated=summarize_numeric(ttf_iso),
        cont_summary_impulse=summarize_numeric(cont_imp),
        cont_summary_isolated=summarize_numeric(cont_iso),
        z_test_impulse_vs_isolated_h50={"delta_pp": delta, "p_value": p_val},
        first_time=candles[0]["time"] if candles else "",
        last_time=candles[-1]["time"] if candles else "",
    )


# ---------------------------------------------------------------------------
# Verdict logic (applied against pre-registered thresholds)
# ---------------------------------------------------------------------------

def verdict(m15: TFReport, h1: TFReport) -> dict:
    BONF_ALPHA = 0.05 / 2  # 2 timeframes = 0.025

    # Primary threshold (M15)
    imp50 = m15.fill_rate_impulse["h50"] if m15.fill_rate_impulse["n"] > 0 else 0.0
    iso50 = m15.fill_rate_isolated["h50"] if m15.fill_rate_isolated["n"] > 0 else 0.0
    delta50_m15 = (imp50 - iso50) * 100.0
    p_m15 = m15.z_test_impulse_vs_isolated_h50["p_value"]

    imp50_h1 = h1.fill_rate_impulse["h50"] if h1.fill_rate_impulse["n"] > 0 else 0.0
    iso50_h1 = h1.fill_rate_isolated["h50"] if h1.fill_rate_isolated["n"] > 0 else 0.0
    delta50_h1 = (imp50_h1 - iso50_h1) * 100.0
    p_h1 = h1.z_test_impulse_vs_isolated_h50["p_value"]

    # Sample size gates
    enough_m15 = (m15.fill_rate_impulse["n"] >= MIN_N_M15
                  and m15.fill_rate_isolated["n"] >= MIN_N_M15)
    enough_h1 = (h1.fill_rate_impulse["n"] >= MIN_N_H1
                 and h1.fill_rate_isolated["n"] >= MIN_N_H1)

    # PROMOTE criteria
    h1_same_sign = (delta50_h1 > 0) == (delta50_m15 > 0)
    promote = (enough_m15 and enough_h1
               and imp50 >= 0.60
               and delta50_m15 >= 10.0
               and p_m15 < BONF_ALPHA
               and h1_same_sign
               and imp50_h1 >= 0.60
               and delta50_h1 >= 10.0
               and p_h1 < BONF_ALPHA)

    # SHADOW criteria (weaker, M15 only)
    shadow = (enough_m15
              and imp50 >= 0.55
              and delta50_m15 >= 5.0
              and not promote)

    insufficient = not enough_m15 or not enough_h1

    if promote:
        label = "PROMOTE"
    elif shadow:
        label = "SHADOW"
    elif insufficient:
        label = "INSUFFICIENT_DATA"
    else:
        label = "KILL"

    return {
        "label": label,
        "m15": {
            "imp50": imp50, "iso50": iso50, "delta_pp": delta50_m15,
            "p_value": p_m15, "n_imp": m15.fill_rate_impulse["n"],
            "n_iso": m15.fill_rate_isolated["n"],
        },
        "h1": {
            "imp50": imp50_h1, "iso50": iso50_h1, "delta_pp": delta50_h1,
            "p_value": p_h1, "n_imp": h1.fill_rate_impulse["n"],
            "n_iso": h1.fill_rate_isolated["n"],
        },
        "bonferroni_alpha": BONF_ALPHA,
        "enough_m15": enough_m15,
        "enough_h1": enough_h1,
        "h1_same_sign": h1_same_sign,
    }


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def fmt_pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def fmt_ci(ci: tuple[float, float]) -> str:
    return f"[{ci[0] * 100:.1f}% - {ci[1] * 100:.1f}%]"


def fmt_num(x: float) -> str:
    if math.isnan(x):
        return "nan"
    return f"{x:.2f}"


def render_tf_section(r: TFReport) -> str:
    def fr_row(label: str, fr_dict: dict) -> str:
        if fr_dict["n"] == 0:
            return f"| {label} | 0 | — | — | — | — | — | — |"
        return (
            f"| {label} | {fr_dict['n']} "
            f"| {fmt_pct(fr_dict['h20'])} | {fmt_ci(fr_dict['ci20'])} "
            f"| {fmt_pct(fr_dict['h50'])} | {fmt_ci(fr_dict['ci50'])} "
            f"| {fmt_pct(fr_dict['h100'])} | {fmt_ci(fr_dict['ci100'])} |"
        )

    def summary_row(label: str, s: dict) -> str:
        if s.get("n", 0) == 0:
            return f"| {label} | 0 | — | — | — | — | — | — |"
        return (
            f"| {label} | {s['n']} | {fmt_num(s['mean'])} | {fmt_num(s['median'])} "
            f"| {fmt_num(s['p25'])} | {fmt_num(s['p75'])} "
            f"| {fmt_num(s['min'])} | {fmt_num(s['max'])} |"
        )

    lines = []
    lines.append(f"## {r.tf} — raw population")
    lines.append("")
    lines.append(f"- Candles loaded: **{r.n_candles}** ({r.first_time} -> {r.last_time})")
    lines.append(f"- FVGs detected: **{r.n_fvgs_total}** ({r.n_bull} bull, {r.n_bear} bear)")
    if r.n_candles > 0:
        lines.append(f"- Formation rate: **{r.n_fvgs_total / r.n_candles:.3f}** FVGs/candle "
                     f"(1 FVG every {r.n_candles / max(1, r.n_fvgs_total):.1f} candles)")
    lines.append(f"- IMPULSE-FVG count: **{r.n_impulse}** "
                 f"({r.n_impulse / max(1, r.n_fvgs_total) * 100:.1f}% of all FVGs)")
    lines.append(f"- OB-ADJACENT count: **{r.n_ob_adj}** "
                 f"({r.n_ob_adj / max(1, r.n_fvgs_total) * 100:.1f}% of all FVGs)")
    lines.append(f"- ISOLATED-only (neither OB-adj nor impulse): **{r.n_isolated_only}** "
                 f"({r.n_isolated_only / max(1, r.n_fvgs_total) * 100:.1f}% of all FVGs)")
    lines.append("")

    lines.append("### Gap size (gap / ATR14 at candle i-1)")
    lines.append("")
    lines.append("| Subset | n | mean | median | p25 | p75 | min | max |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    lines.append(summary_row("all FVGs", r.gap_size_atr_summary))
    lines.append(summary_row("IMPULSE-FVG", r.impulse_gap_size_atr_summary))
    lines.append(summary_row("ISOLATED-only", r.isolated_gap_size_atr_summary))
    lines.append("")

    lines.append("### Fill rate by horizon (candles after FVG formation)")
    lines.append("")
    lines.append("| Subset | n | h=20 | 95% CI | h=50 (PRIMARY) | 95% CI | h=100 | 95% CI |")
    lines.append("|---|---:|---:|:---:|---:|:---:|---:|:---:|")
    lines.append(fr_row("all FVGs", r.fill_rate_all))
    lines.append(fr_row("IMPULSE-FVG", r.fill_rate_impulse))
    lines.append(fr_row("ISOLATED-only", r.fill_rate_isolated))
    lines.append(fr_row("OB-ADJACENT", r.fill_rate_ob_adj))
    lines.append("")

    lines.append("### Time-to-fill (candles, FILLED FVGs only)")
    lines.append("")
    lines.append("| Subset | n | mean | median | p25 | p75 | min | max |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    lines.append(summary_row("all filled FVGs", r.ttf_summary_all))
    lines.append(summary_row("IMPULSE-FVG filled", r.ttf_summary_impulse))
    lines.append(summary_row("ISOLATED-only filled", r.ttf_summary_isolated))
    lines.append("")

    lines.append("### Continuation-before-fill (max impulse-direction move in ATR units)")
    lines.append("")
    lines.append("| Subset | n | mean | median | p25 | p75 | min | max |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    lines.append(summary_row("IMPULSE-FVG", r.cont_summary_impulse))
    lines.append(summary_row("ISOLATED-only", r.cont_summary_isolated))
    lines.append("")

    delta = r.z_test_impulse_vs_isolated_h50["delta_pp"]
    p = r.z_test_impulse_vs_isolated_h50["p_value"]
    lines.append("### Primary test: IMPULSE-FVG vs ISOLATED-only fill rate at h=50")
    lines.append("")
    lines.append(f"- Delta (IMPULSE - ISOLATED): **{delta:+.1f}pp**")
    lines.append(f"- Two-proportion z-test p-value: **{p:.4f}**")
    lines.append(f"- Bonferroni-adjusted alpha (2 timeframes): 0.025 — "
                 f"{'**SIGNIFICANT**' if p < 0.025 else 'not significant'}")
    lines.append("")
    return "\n".join(lines)


def render_verdict_section(v: dict) -> str:
    lines = []
    lines.append("## Verdict (pre-registered gate)")
    lines.append("")
    lines.append(f"- **Result label:** **{v['label']}**")
    lines.append(f"- Bonferroni-adjusted alpha: {v['bonferroni_alpha']}")
    lines.append(f"- Sample size gate M15 (n>=20 each class): "
                 f"{'pass' if v['enough_m15'] else 'FAIL'} "
                 f"(n_impulse={v['m15']['n_imp']}, n_isolated={v['m15']['n_iso']})")
    lines.append(f"- Sample size gate H1 (n>=10 each class): "
                 f"{'pass' if v['enough_h1'] else 'FAIL'} "
                 f"(n_impulse={v['h1']['n_imp']}, n_isolated={v['h1']['n_iso']})")
    lines.append(f"- H1 sign matches M15: {v['h1_same_sign']}")
    lines.append("")
    lines.append("### Per-timeframe test summary")
    lines.append("")
    lines.append("| TF | IMPULSE fill h=50 | ISOLATED fill h=50 | Delta (pp) | p-value | n_imp | n_iso |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for tf_name, d in [("M15", v["m15"]), ("H1", v["h1"])]:
        lines.append(
            f"| {tf_name} | {d['imp50'] * 100:.1f}% | {d['iso50'] * 100:.1f}% "
            f"| {d['delta_pp']:+.1f} | {d['p_value']:.4f} "
            f"| {d['n_imp']} | {d['n_iso']} |"
        )
    lines.append("")
    lines.append("### Verdict rules applied")
    lines.append("")
    lines.append("- PROMOTE: n sufficient on both TFs AND IMPULSE fill h=50 >= 60% on BOTH AND delta >= +10pp on BOTH AND p < 0.025 on BOTH AND H1 sign matches M15.")
    lines.append("- SHADOW: M15 IMPULSE fill h=50 >= 55% AND delta >= +5pp on M15, but PROMOTE conditions not all met.")
    lines.append("- KILL: neither PROMOTE nor SHADOW triggered and samples sufficient.")
    lines.append("- INSUFFICIENT_DATA: n-class gates failed on either TF.")
    lines.append("")
    return "\n".join(lines)


def render_overlap_disclosure(m15: TFReport, h1: TFReport) -> str:
    lines = []
    lines.append("## Overlap disclosure — corroboration vs novelty")
    lines.append("")
    lines.append("The prior GTOS finding is **'FVG-in-impulse' adds +7-20pp WR across 6 instruments** (CLAUDE.md Validated Numbers table, entry-signal level). The present study tests the **structural** property — raw fill rate and continuation of FVGs as objects on the chart, independent of any trade decision. The two measurements are orthogonal: a high structural fill rate can coexist with a low trade WR (and vice versa), since the trade result also depends on entry price, SL, and TP mechanics that are not modelled here.")
    lines.append("")
    lines.append("Statements below mark each primary finding as CORROBORATION or NOVEL:")
    lines.append("")
    for (name, r) in [("M15", m15), ("H1", h1)]:
        if r.fill_rate_impulse["n"] == 0 or r.fill_rate_isolated["n"] == 0:
            lines.append(f"- **{name}:** insufficient data for the overlap disclosure.")
            continue
        imp = r.fill_rate_impulse["h50"]
        iso = r.fill_rate_isolated["h50"]
        cont_imp = r.cont_summary_impulse.get("median", 0.0)
        cont_iso = r.cont_summary_isolated.get("median", 0.0)
        if imp > iso + 0.05 and cont_imp > cont_iso:
            tag = "CORROBORATES prior (IMPULSE fills more AND travels further)."
        elif imp > iso + 0.05 and cont_imp <= cont_iso:
            tag = ("PARTIAL corroboration (IMPULSE fills more, but continuation is not larger). "
                   "The prior WR-lift may reflect fill-side protection more than entry-side momentum.")
        elif imp <= iso + 0.05:
            tag = ("Does NOT corroborate the structural version of the prior on this TF — "
                   "the prior is about trade WR not fill rate, so this is consistent but not supportive.")
        else:
            tag = "Mixed."
        lines.append(f"- **{name}:** IMPULSE fill h=50 = {imp * 100:.1f}% vs ISOLATED {iso * 100:.1f}%, "
                     f"median continuation IMPULSE = {cont_imp:.2f} ATR vs ISOLATED {cont_iso:.2f} ATR. {tag}")
    lines.append("")
    return "\n".join(lines)


def render_caveats() -> str:
    return """## Caveats

1. **Single instrument, single window.** XAUUSD only, Jan 2 -> Apr 10 2026 (~100 trading days). M15 ~6420 candles, H1 ~1606 candles. Fills at h=100 require the FVG to form at least 100 candles before the end of the window — late-window FVGs are right-censored (treated as unfilled at the far horizon if no fill has yet occurred). A Kaplan-Meier treatment would be cleaner; we report the simple cumulative rate.

2. **FVG definition chosen to match production.** We use the `identify_fvgs` indices (i-1, i, i+1) from `src/components/market_state.py`. The task brief described the pattern with indices (i-2, i), which is operationally equivalent (the gap candle is the middle candle; the brief's notation swaps the anchor). We document the mapping and honour the production convention.

3. **Impulse threshold is a single 1.5x ATR rule.** Chosen to match `detect_structure_breaks` `displacement_present`. Not swept. An impulse candle is an object-level property of candle i; the FVG itself is defined by i-1 and i+1. A gap can exist without the middle candle being an impulse, and an impulse candle may leave no gap.

4. **OB-ADJACENCY window is +/-10 candles.** Not swept. Corresponds to the production back-walk distance in `identify_order_blocks` (10-candle lookback from the break). Different windows would change the ISOLATED vs OB-ADJACENT split.

5. **Fill = any wick overlap.** A bull FVG is "filled" the first time a candle's low <= top of the gap. Some traders require body-based fill or 50% midpoint fill. We use wick-based because it is the most permissive (gives the highest fill rate) — any stricter rule would only make the comparisons more conservative.

6. **Continuation-before-fill can be zero.** If the first post-pattern candle wicks straight back into the gap, continuation_atr = 0 even for a formally-flagged IMPULSE-FVG. This is correct and reflects real behaviour.

7. **Multiple-testing.** Only h=50 is primary; h=20 and h=100 are descriptive. Bonferroni divisor = 2 (M15 and H1). All secondary tests (gap-size distribution, time-to-fill medians, OB-ADJACENT fill rates) are exploratory and do NOT meet the promotion threshold no matter the p-value.

8. **Right-censoring of continuation metric.** `continuation_atr` is measured from candle i+2 until fill, or until end-of-data. Unfilled FVGs have their continuation measured over whatever remaining candles exist. This may bias ISOLATED / fast-fill FVGs' max continuation downward relative to IMPULSE / long-persist FVGs.

9. **Not a trade edge test.** High fill rate with large continuation-before-fill is a necessary but not sufficient condition for an entry-signal edge. This study does not implement SL/TP/spread/slippage, so no PnL or WR is computed.

10. **No API calls.** Local analysis only.
"""


def render_next_steps() -> str:
    return """## Next steps

1. **If verdict is PROMOTE or SHADOW:** add an observation-only shadow logger for detected M15 FVGs (formation time, side, gap_size_pct_atr, is_impulse, is_ob_adjacent, fill outcome at h=50). Mirror the existing `proximity_shadow_logger.py` pattern. At least 30 trades worth of post-deployment data before any trading-logic change is proposed (per CLAUDE.md).

2. **If verdict is KILL:** record the test outcome and deprioritise FVG structural classification as an entry feature. The prior +7-20pp WR-lift finding stands on its own (trade-outcome measurement) but is not corroborated at the structural fill-rate layer.

3. **Extend to other instruments.** The Validated Numbers +7-20pp figure is cross-instrument (6 symbols). Running this exact script on USDJPY, GBPJPY, GBPUSD, US30 requires only swapping the CSV paths and rerunning. Bonferroni divisor becomes 2 x 5 = 10.

4. **Sensitivity analyses that are allowed under the pre-registered rules:**
   - Different ATR lookback (21, 50) — separately reported, not replacing primary.
   - Different impulse threshold (1.25, 1.75, 2.0 ATR) — sweep, report the full curve, do not cherry-pick.
   - Body-based fill rule vs wick-based — robustness check.

5. **What would require new pre-registration:** any re-classification scheme (e.g. "high-impulse FVG" = 2.5 ATR), any different horizon set, any subset of the sample by session or regime.
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not M15_CSV.exists():
        raise FileNotFoundError(M15_CSV)
    if not H1_CSV.exists():
        raise FileNotFoundError(H1_CSV)

    m15 = analyze_timeframe("M15", M15_CSV)
    h1 = analyze_timeframe("H1", H1_CSV)
    v = verdict(m15, h1)

    # Append sections to existing file (Section 1 = pre-registered hypothesis)
    assert OUT_MD.exists(), f"Pre-registered hypothesis file missing at {OUT_MD}"
    existing = OUT_MD.read_text(encoding="utf-8")

    parts = [existing.rstrip() + "\n\n"]
    parts.append(f"## 2. Data audit\n\n"
                 f"- M15 candles: **{m15.n_candles}** ({m15.first_time} -> {m15.last_time})\n"
                 f"- H1 candles: **{h1.n_candles}** ({h1.first_time} -> {h1.last_time})\n"
                 f"- Generated: {datetime.now(timezone.utc).isoformat()}\n"
                 f"- Script: `research/academic_pipeline/scripts/q_13_6_fvg.py`\n\n")
    parts.append(render_tf_section(m15) + "\n")
    parts.append(render_tf_section(h1) + "\n")
    parts.append(render_verdict_section(v) + "\n")
    parts.append(render_overlap_disclosure(m15, h1) + "\n")
    parts.append(render_caveats() + "\n")
    parts.append(render_next_steps() + "\n")

    OUT_MD.write_text("".join(parts), encoding="utf-8")

    # Short stdout summary
    print(f"M15 FVGs: {m15.n_fvgs_total} (impulse={m15.n_impulse}, isolated_only={m15.n_isolated_only}, ob_adj={m15.n_ob_adj})")
    print(f"H1  FVGs: {h1.n_fvgs_total} (impulse={h1.n_impulse}, isolated_only={h1.n_isolated_only}, ob_adj={h1.n_ob_adj})")
    print(f"M15 IMPULSE fill h=50: {m15.fill_rate_impulse['h50'] * 100:.1f}%  "
          f"ISOLATED h=50: {m15.fill_rate_isolated['h50'] * 100:.1f}%  "
          f"delta={m15.z_test_impulse_vs_isolated_h50['delta_pp']:+.1f}pp  "
          f"p={m15.z_test_impulse_vs_isolated_h50['p_value']:.4f}")
    print(f"H1  IMPULSE fill h=50: {h1.fill_rate_impulse['h50'] * 100:.1f}%  "
          f"ISOLATED h=50: {h1.fill_rate_isolated['h50'] * 100:.1f}%  "
          f"delta={h1.z_test_impulse_vs_isolated_h50['delta_pp']:+.1f}pp  "
          f"p={h1.z_test_impulse_vs_isolated_h50['p_value']:.4f}")
    print(f"Verdict: {v['label']}")


if __name__ == "__main__":
    main()
