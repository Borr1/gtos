"""
Q-14.9 Market-Maker Inventory Reversion + Q-14.11 Structural Compression Breakout
==================================================================================

Two non-zone mechanism tests on XAUUSD 2026 historical data (Jan 2 - Apr 10).
Local, $0 API.

PRE-REGISTERED HYPOTHESES (stated BEFORE looking at data)
----------------------------------------------------------

Q-14.9  MM inventory reversion
    H0: After an extension candle (|close - MA20| / ATR14 > 2.0 on M15),
        P(reversion at horizon k in {3, 6, 12}) equals baseline reversion
        probability measured at non-extension candles.
    H1 (prior): P(reversion | extension) > P(reversion | baseline).
        Mechanism: retail capitulation + MM inventory skew predicts
        mean reversion after extreme displacement.  Literature: Hasbrouck
        market-making inventory control (1991), Grossman-Miller (1988).
    Directional split (also pre-registered):
        - "too-far-up": extension_z > +2.0 -> expect reversion DOWN
        - "too-far-down": extension_z < -2.0 -> expect reversion UP
    Pre-registered pass: reversion prob >= 60% at ANY k with p_bonf < 0.017
    (CEO spec: alpha/3 for 3 horizons).  Bonferroni across full study
    (two questions combined) = 0.05 / 8 tests = 0.00625 as strict-joint
    threshold, but we report both per-question and joint Bonferroni.

Q-14.11  Structural compression breakout
    H0: Breakout continuation WR from compression states equals breakout
        continuation WR from non-compression states.
    H1 (prior): compression-breakout WR >= baseline + 5pp, p < 0.05.
        Mechanism: low-vol regimes cluster trapped directional energy;
        Bollinger squeeze -> breakout literature (Bollinger 2001, Connors).
    Compression definition (pre-registered):
        - Bollinger bandwidth (20, 2sigma) < 25th percentile of its own
          100-bar history AND
        - Keltner Channel width (MA20 +/- 2*ATR14) < 25th percentile of its
          own 100-bar history
    Breakout definition: first candle whose CLOSE exceeds BB upper/lower
        OR KC upper/lower (whichever hit first).
    Continuation WR: 6-candle forward WR in breakout direction (price closes
        in breakout direction at t+6 relative to breakout candle close).

PRE-REGISTERED CROSS-CHECK
---------------------------
Q-14.11 could be redundant with H25's session-vol monitor (W1/W2/W3 decay
within kill zones).  H25 tracks candle-range by intra-session position;
Q-14.11 tracks breakout direction from statistically-defined compression.
If compression periods cluster 1:1 with session-open W1 volatility peaks,
the signal collapses to a known H25 finding.  Flagged explicitly in report.

JOINT BONFERRONI
----------------
Total tests across both questions:
  Q-14.9 : 3 horizons (k=3,6,12) x 3 groupings (all, too-far-up, too-far-down) = 9 tests
  Q-14.11: 1 primary test (compression-breakout WR vs non-compression)
  Joint Bonferroni alpha = 0.05 / 10 = 0.005
We REPORT raw p and joint_bonf_p for every test.  Pre-registered pass thresholds:
  - Q-14.9 per-horizon: p_raw < 0.017 (alpha/3 per CEO spec)
  - Q-14.11: p_raw < 0.05
Plus joint Bonferroni passes at p_joint < 0.05.
"""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
M15_CSV = ROOT / "data" / "historical_2026" / "XAUUSD_M15.csv"
H1_CSV = ROOT / "data" / "historical_2026" / "XAUUSD_H1.csv"
OUT_MD = ROOT / "research" / "academic_pipeline" / "results" / "Q-14_9_11.md"


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------
def wilson_ci(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = wins / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def two_proportion_z_test(x1: int, n1: int, x2: int, n2: int) -> tuple[float, float]:
    """Two-proportion z-test (two-sided).  Returns (z, p)."""
    if n1 == 0 or n2 == 0:
        return (0.0, 1.0)
    p1 = x1 / n1
    p2 = x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return (0.0, 1.0)
    z = (p1 - p2) / se
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    return (z, p)


def one_sided_binom_p(wins: int, n: int, p0: float) -> float:
    """One-sided (greater) exact binomial test p-value."""
    if n == 0:
        return 1.0
    # P(X >= wins | n, p0)
    return float(1 - stats.binom.cdf(wins - 1, n, p0))


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
def load_ohlc(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").reset_index(drop=True)
    return df


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.rolling(period, min_periods=period).mean()


# ---------------------------------------------------------------------------
# Q-14.9  MM inventory reversion
# ---------------------------------------------------------------------------
def run_q_14_9(m15: pd.DataFrame) -> dict[str, Any]:
    df = m15.copy()
    df["ma20"] = df["close"].rolling(20, min_periods=20).mean()
    df["atr14"] = atr(df, 14)
    df["disp"] = df["close"] - df["ma20"]                     # signed displacement
    df["ext_z"] = df["disp"] / df["atr14"]                    # extension z-score
    df["sign_disp"] = np.sign(df["disp"])                     # +1 above MA, -1 below

    ks = [3, 6, 12]
    max_k = max(ks)

    # Compute forward closes
    for k in ks:
        df[f"close_fwd_{k}"] = df["close"].shift(-k)

    # Reversion event at horizon k: sign(close[t+k] - close[t]) is OPPOSITE to sign(close[t] - MA20[t])
    # Equivalently: price at t+k moves back TOWARD the mean direction.
    #   If disp>0 (above MA), reversion = close[t+k] < close[t]
    #   If disp<0 (below MA), reversion = close[t+k] > close[t]
    df_valid = df.dropna(subset=["ma20", "atr14", f"close_fwd_{max_k}", "sign_disp"]).copy()
    df_valid = df_valid[df_valid["sign_disp"] != 0]

    THRESH = 2.0
    df_valid["is_ext_up"] = df_valid["ext_z"] > THRESH
    df_valid["is_ext_down"] = df_valid["ext_z"] < -THRESH
    df_valid["is_ext"] = df_valid["is_ext_up"] | df_valid["is_ext_down"]
    df_valid["is_baseline"] = df_valid["ext_z"].abs() <= THRESH

    results: dict[str, Any] = {
        "total_bars_analyzed": int(len(df_valid)),
        "n_extension_up": int(df_valid["is_ext_up"].sum()),
        "n_extension_down": int(df_valid["is_ext_down"].sum()),
        "n_extension_any": int(df_valid["is_ext"].sum()),
        "n_baseline": int(df_valid["is_baseline"].sum()),
        "horizons": {},
    }

    for k in ks:
        fwd = df_valid[f"close_fwd_{k}"]
        cur = df_valid["close"]
        move = fwd - cur
        sign_disp = df_valid["sign_disp"]
        # reversion: sign(move) == -sign(sign_disp)
        is_reversion = (np.sign(move) * sign_disp) < 0

        per_k: dict[str, Any] = {}

        for group_name, mask in (
            ("all_extensions", df_valid["is_ext"]),
            ("too_far_up", df_valid["is_ext_up"]),
            ("too_far_down", df_valid["is_ext_down"]),
        ):
            ext_mask = mask & is_reversion.notna()
            n_ext = int(ext_mask.sum())
            x_ext = int(is_reversion[ext_mask].sum())
            # Baseline matching directional sign for too_far_up/down?
            # Mechanism spec: baseline = non-extension candles of ANY sign for "all_extensions".
            # For directional groupings, baseline should match sign to avoid trivial asymmetry:
            if group_name == "all_extensions":
                base_mask = df_valid["is_baseline"] & is_reversion.notna()
            elif group_name == "too_far_up":
                base_mask = df_valid["is_baseline"] & (df_valid["sign_disp"] > 0) & is_reversion.notna()
            else:  # too_far_down
                base_mask = df_valid["is_baseline"] & (df_valid["sign_disp"] < 0) & is_reversion.notna()

            n_base = int(base_mask.sum())
            x_base = int(is_reversion[base_mask].sum())

            if n_ext == 0 or n_base == 0:
                per_k[group_name] = {
                    "n_ext": n_ext, "x_ext": x_ext, "p_ext": None,
                    "wilson_ext": (0.0, 0.0),
                    "n_base": n_base, "x_base": x_base, "p_base": None,
                    "wilson_base": (0.0, 0.0),
                    "z": None, "p_raw": None, "delta_pp": None,
                    "p_bonf_perq": None,
                    "threshold_60_pass": False,
                    "passes_prereg": False,
                }
                continue

            p_ext = x_ext / n_ext
            p_base = x_base / n_base
            wi_e = wilson_ci(x_ext, n_ext)
            wi_b = wilson_ci(x_base, n_base)
            z, p_raw = two_proportion_z_test(x_ext, n_ext, x_base, n_base)
            delta = (p_ext - p_base) * 100
            # Bonferroni within question: 3 horizons x 3 groupings = 9 tests
            p_bonf_perq = min(1.0, p_raw * 9)
            threshold_60 = p_ext >= 0.60
            # Pre-reg pass (per CEO spec): >=60% AND p_bonf < 0.017
            passes = threshold_60 and (p_raw * 3) < 0.017  # alpha/3 per CEO spec
            per_k[group_name] = {
                "n_ext": n_ext, "x_ext": x_ext, "p_ext": p_ext,
                "wilson_ext": wi_e,
                "n_base": n_base, "x_base": x_base, "p_base": p_base,
                "wilson_base": wi_b,
                "z": z, "p_raw": p_raw,
                "delta_pp": delta,
                "p_bonf_perq": p_bonf_perq,
                "threshold_60_pass": threshold_60,
                "passes_prereg": passes,
            }

        results["horizons"][k] = per_k

    return results


# ---------------------------------------------------------------------------
# Q-14.11  Compression breakout
# ---------------------------------------------------------------------------
def run_q_14_11(m15: pd.DataFrame) -> dict[str, Any]:
    df = m15.copy()
    df["ma20"] = df["close"].rolling(20, min_periods=20).mean()
    df["stdev20"] = df["close"].rolling(20, min_periods=20).std(ddof=0)
    df["bb_upper"] = df["ma20"] + 2 * df["stdev20"]
    df["bb_lower"] = df["ma20"] - 2 * df["stdev20"]
    df["bb_width"] = df["bb_upper"] - df["bb_lower"]

    df["atr14"] = atr(df, 14)
    df["kc_upper"] = df["ma20"] + 2 * df["atr14"]
    df["kc_lower"] = df["ma20"] - 2 * df["atr14"]
    df["kc_width"] = df["kc_upper"] - df["kc_lower"]

    # Rolling 100-bar 25th percentile of each width (EXCLUDING current bar, shift by 1)
    df["bb_q25_100"] = df["bb_width"].shift(1).rolling(100, min_periods=100).quantile(0.25)
    df["kc_q25_100"] = df["kc_width"].shift(1).rolling(100, min_periods=100).quantile(0.25)

    df["is_compression"] = (
        (df["bb_width"] < df["bb_q25_100"]) & (df["kc_width"] < df["kc_q25_100"])
    )

    # Detect compression REGIME state transitions.
    # We want to identify "compression periods" (contiguous runs of compression=True)
    # and detect the first breakout candle following each period (or during,
    # for intra-compression breakouts).
    # Operationally: walk forward; track "inside_compression" flag; when a
    # candle's close breaks BB OR KC upper/lower, mark a breakout.

    df = df.dropna(subset=["bb_upper", "kc_upper", "bb_q25_100", "kc_q25_100"]).reset_index(drop=True)

    breakouts: list[dict[str, Any]] = []  # all breakouts (with/without prior compression)
    in_compression = False
    compression_start_idx = None

    # Pre-reg: first candle whose close exceeds BB OR KC upper/lower is the breakout.
    # We'll detect a breakout at candle i if close_i > max(bb_upper_i, kc_upper_i) or close_i < min(bb_lower_i, kc_lower_i).
    # And track whether that breakout occurred during or within a short window after a compression regime.

    LOOKBACK_COMPRESSION_WINDOW = 3  # candles after compression ends, still counts as "from compression"
    last_compression_end_idx = -999

    for i in range(len(df)):
        row = df.iloc[i]
        compressed = bool(row["is_compression"])
        if compressed and not in_compression:
            in_compression = True
            compression_start_idx = i
        elif (not compressed) and in_compression:
            in_compression = False
            last_compression_end_idx = i - 1  # the last compression candle was i-1

        upper_break = row["close"] > max(row["bb_upper"], row["kc_upper"])
        lower_break = row["close"] < min(row["bb_lower"], row["kc_lower"])
        if upper_break or lower_break:
            # Determine if this is "from compression": either currently compressed or within LOOKBACK of last compression
            from_compression = in_compression or (i - last_compression_end_idx) <= LOOKBACK_COMPRESSION_WINDOW
            direction = 1 if upper_break else -1
            # 6-candle continuation: is close[i+6] in the direction of the breakout relative to close[i]?
            if i + 6 < len(df):
                fwd_close = df.iloc[i + 6]["close"]
                cur_close = row["close"]
                if direction > 0:
                    win = fwd_close > cur_close
                else:
                    win = fwd_close < cur_close
                breakouts.append(
                    {
                        "idx": i,
                        "time": row["time"],
                        "close": cur_close,
                        "direction": direction,
                        "from_compression": from_compression,
                        "win": bool(win),
                        "fwd_close_t6": float(fwd_close),
                    }
                )

    # Dedup: if consecutive candles re-trigger breakout, keep only the first in each run
    # (first-touch semantics per pre-reg)
    deduped: list[dict[str, Any]] = []
    last_dir = 0
    last_idx = -999
    MIN_GAP = 6  # new breakout requires 6-candle gap or direction change
    for b in breakouts:
        if b["direction"] == last_dir and (b["idx"] - last_idx) < MIN_GAP:
            continue
        deduped.append(b)
        last_dir = b["direction"]
        last_idx = b["idx"]

    comp_breaks = [b for b in deduped if b["from_compression"]]
    non_comp_breaks = [b for b in deduped if not b["from_compression"]]

    def wr_block(lst: list[dict[str, Any]]) -> dict[str, Any]:
        if not lst:
            return {"n": 0, "wins": 0, "wr": 0.0, "wilson_lo": 0.0, "wilson_hi": 0.0}
        n = len(lst)
        wins = sum(1 for b in lst if b["win"])
        lo, hi = wilson_ci(wins, n)
        return {"n": n, "wins": wins, "wr": wins / n, "wilson_lo": lo, "wilson_hi": hi}

    comp_stats = wr_block(comp_breaks)
    non_comp_stats = wr_block(non_comp_breaks)

    z, p_raw = two_proportion_z_test(
        comp_stats["wins"], comp_stats["n"],
        non_comp_stats["wins"], non_comp_stats["n"],
    )
    delta_pp = (comp_stats["wr"] - non_comp_stats["wr"]) * 100 if comp_stats["n"] and non_comp_stats["n"] else 0.0

    passes_prereg = (delta_pp >= 5.0) and (p_raw < 0.05)

    # Cross-check: volatility clustering overlap with H25 session-vol?
    # H25 finding: volatility PEAKS at session open (W1) and decays (W2, W3).
    # Compression is the OPPOSITE pattern (low vol).  If compression periods
    # are systematically outside London/NY kill zones, they represent a
    # complementary signal; if they cluster in kill zones, they overlap.

    comp_mask = df["is_compression"].fillna(False)
    comp_hours = df.loc[comp_mask, "time"].dt.hour
    hour_histogram = comp_hours.value_counts().sort_index().to_dict()
    # Kill zones (UTC): London 07-10, NY 13-17 for XAUUSD
    kz_london_count = int(((comp_hours >= 7) & (comp_hours <= 10)).sum())
    kz_ny_count = int(((comp_hours >= 13) & (comp_hours <= 17)).sum())
    total_comp_candles = int(comp_hours.size)
    kz_total = kz_london_count + kz_ny_count
    kz_frac = kz_total / total_comp_candles if total_comp_candles else 0.0

    # Expected KZ frac if compression uniformly distributed: London 4h + NY 5h = 9/24 = 0.375
    expected_kz_frac = (4 + 5) / 24
    # Deviation test: one-sample proportion test
    if total_comp_candles > 0:
        z_hours, p_hours = stats.binomtest(kz_total, total_comp_candles, expected_kz_frac).pvalue, None
        # binomtest returns a BinomTestResult in scipy>=1.7; use pvalue attribute
        try:
            p_hours_val = z_hours  # already pvalue
        except Exception:
            p_hours_val = 1.0
    else:
        p_hours_val = 1.0

    return {
        "n_total_bars": int(len(df)),
        "n_compression_bars": int(comp_mask.sum()),
        "compression_frac": float(comp_mask.mean()),
        "n_breakouts_total": len(deduped),
        "n_breakouts_from_compression": len(comp_breaks),
        "n_breakouts_non_compression": len(non_comp_breaks),
        "comp_stats": comp_stats,
        "non_comp_stats": non_comp_stats,
        "delta_pp": delta_pp,
        "z": z,
        "p_raw": p_raw,
        "passes_prereg": passes_prereg,
        "hour_histogram_compression": hour_histogram,
        "kz_london_count": kz_london_count,
        "kz_ny_count": kz_ny_count,
        "kz_frac_of_compression": kz_frac,
        "expected_kz_frac_uniform": expected_kz_frac,
        "p_kz_vs_uniform": p_hours_val,
    }


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------
def fmt_pct(x: float | None) -> str:
    if x is None:
        return "n/a"
    return f"{x * 100:.1f}%"


def fmt_pp(x: float | None) -> str:
    if x is None:
        return "n/a"
    return f"{x:+.1f}pp"


def fmt_p(x: float | None) -> str:
    if x is None:
        return "n/a"
    if x < 1e-4:
        return f"{x:.2e}"
    return f"{x:.4f}"


def render_md(q149: dict[str, Any], q1411: dict[str, Any], joint_bonf_m: int) -> str:
    lines: list[str] = []
    lines.append("# Q-14.9 + Q-14.11 Non-Zone Mechanisms")
    lines.append("")
    lines.append(
        "Generated by `research/academic_pipeline/scripts/q_14_9_11_mm_compression.py` "
        "(local, $0 API)."
    )
    lines.append("")
    # -------- Hypotheses (pre-reg) --------
    lines.append("## Pre-registered hypotheses")
    lines.append("")
    lines.append("### Q-14.9  MM inventory reversion")
    lines.append("- **H0**: P(reversion | extension, k) = P(reversion | baseline, k).")
    lines.append("- **H1 (prior)**: Extensions (|close - MA20| / ATR14 > 2.0) are followed by")
    lines.append("  reversion more often than non-extension baseline.")
    lines.append("- **Directional split**: too-far-up vs too-far-down tested separately.")
    lines.append("- **Pre-registered pass**: reversion prob >= 60% at ANY k with p_raw*3 < 0.017")
    lines.append("  (CEO spec: alpha/3 for 3 horizons, per-question).")
    lines.append("")
    lines.append("### Q-14.11  Structural compression breakout")
    lines.append("- **H0**: Compression-breakout continuation WR = non-compression breakout WR.")
    lines.append("- **H1 (prior)**: compression-breakout WR >= baseline + 5pp, p < 0.05.")
    lines.append("- **Compression**: BB20 bandwidth < 25th pct of own 100-bar history AND KC")
    lines.append("  (MA20 +/- 2*ATR14) width < 25th pct of own 100-bar history.")
    lines.append("- **Breakout**: first candle whose close exceeds BB OR KC upper/lower after")
    lines.append("  a 6-bar deduplication gap.")
    lines.append("- **Continuation WR**: close[t+6] in breakout direction vs close[t].")
    lines.append("")
    lines.append("### Joint Bonferroni")
    lines.append(f"- Total tests across both questions: **{joint_bonf_m}** (9 for Q-14.9, 1 for Q-14.11).")
    lines.append(f"- Joint Bonferroni alpha = 0.05 / {joint_bonf_m} = **{0.05 / joint_bonf_m:.4f}**.")
    lines.append("- Both per-question and joint thresholds reported per test.")
    lines.append("")

    # -------- Data --------
    lines.append("## Data")
    lines.append("")
    lines.append(f"- Source: `data/historical_2026/XAUUSD_M15.csv` (Jan 2 - Apr 10 2026).")
    lines.append(f"- Total M15 bars analyzed after rolling-window warmup: **{q149['total_bars_analyzed']}** (Q-14.9)")
    lines.append(f"  / **{q1411['n_total_bars']}** (Q-14.11; 100-bar warmup for percentile).")
    lines.append(f"- H1 CSV loaded but not used (Q-14.9 and Q-14.11 both defined on M15 per CEO spec).")
    lines.append("")

    # -------- Q-14.9 Results --------
    lines.append("## Q-14.9 Results — MM inventory reversion")
    lines.append("")
    lines.append(f"- Extension candles (|z| > 2.0): **{q149['n_extension_any']}** total")
    lines.append(f"  - Too-far-up (z > +2.0): {q149['n_extension_up']}")
    lines.append(f"  - Too-far-down (z < -2.0): {q149['n_extension_down']}")
    lines.append(f"- Baseline candles (|z| <= 2.0): **{q149['n_baseline']}**")
    lines.append("")
    lines.append("### Reversion probability by horizon x grouping")
    lines.append("")
    lines.append("| k | grouping | n_ext | P(rev\\|ext) | Wilson 95% CI | n_base | P(rev\\|base) | delta | p_raw | p_bonf_perq | p_joint_bonf | 60%? | pre-reg pass |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for k in (3, 6, 12):
        for group in ("all_extensions", "too_far_up", "too_far_down"):
            r = q149["horizons"][k][group]
            p_joint = min(1.0, r["p_raw"] * joint_bonf_m) if r["p_raw"] is not None else None
            wi_e = r["wilson_ext"]
            lines.append(
                f"| {k} | {group} "
                f"| {r['n_ext']} | {fmt_pct(r['p_ext'])} "
                f"| [{fmt_pct(wi_e[0])}, {fmt_pct(wi_e[1])}] "
                f"| {r['n_base']} | {fmt_pct(r['p_base'])} "
                f"| {fmt_pp(r['delta_pp'])} "
                f"| {fmt_p(r['p_raw'])} "
                f"| {fmt_p(r['p_bonf_perq'])} "
                f"| {fmt_p(p_joint)} "
                f"| {'YES' if r['threshold_60_pass'] else 'no'} "
                f"| {'**PASS**' if r['passes_prereg'] else 'no'} |"
            )
    lines.append("")
    any_149_pass = any(
        q149["horizons"][k][g]["passes_prereg"]
        for k in (3, 6, 12)
        for g in ("all_extensions", "too_far_up", "too_far_down")
    )
    lines.append(f"**Any cell passes pre-registered Q-14.9 threshold**: **{'YES' if any_149_pass else 'NO'}**")
    lines.append("")

    # -------- Q-14.11 Results --------
    lines.append("## Q-14.11 Results — Compression breakout")
    lines.append("")
    lines.append(f"- Total M15 bars analyzed: **{q1411['n_total_bars']}**")
    lines.append(
        f"- Compression bars (joint BB & KC < 25th pct): "
        f"**{q1411['n_compression_bars']}** ({fmt_pct(q1411['compression_frac'])})"
    )
    lines.append(f"- Total deduplicated breakouts: **{q1411['n_breakouts_total']}**")
    lines.append(f"- From compression: {q1411['n_breakouts_from_compression']}")
    lines.append(f"- Non-compression: {q1411['n_breakouts_non_compression']}")
    lines.append("")
    cs = q1411["comp_stats"]
    ncs = q1411["non_comp_stats"]
    lines.append("### Continuation WR comparison (6-candle forward)")
    lines.append("")
    lines.append("| group | n | wins | WR | Wilson 95% CI |")
    lines.append("|---|---|---|---|---|")
    lines.append(
        f"| Compression breakout | {cs['n']} | {cs['wins']} | {fmt_pct(cs['wr'])} "
        f"| [{fmt_pct(cs['wilson_lo'])}, {fmt_pct(cs['wilson_hi'])}] |"
    )
    lines.append(
        f"| Non-compression breakout | {ncs['n']} | {ncs['wins']} | {fmt_pct(ncs['wr'])} "
        f"| [{fmt_pct(ncs['wilson_lo'])}, {fmt_pct(ncs['wilson_hi'])}] |"
    )
    lines.append("")
    p_joint_1411 = min(1.0, q1411["p_raw"] * joint_bonf_m) if q1411["p_raw"] is not None else None
    lines.append(f"- Delta (compression - non-compression): **{fmt_pp(q1411['delta_pp'])}**")
    lines.append(f"- z = {q1411['z']:.3f}, p_raw = **{fmt_p(q1411['p_raw'])}**")
    lines.append(f"- p_joint_bonf (x{joint_bonf_m}) = **{fmt_p(p_joint_1411)}**")
    lines.append(f"- Pre-reg pass (delta >= 5pp AND p < 0.05): **{'YES' if q1411['passes_prereg'] else 'NO'}**")
    lines.append("")

    # -------- Redundancy cross-check --------
    lines.append("### Redundancy cross-check with H25 session volatility monitor")
    lines.append("")
    lines.append(
        "H25 tracks candle-range decay within each kill-zone session (W1/W2/W3). "
        "Q-14.11 compression is a statistical low-vol regime definition across the "
        "full 24h tape.  Overlap check: where do compression candles fall by hour?"
    )
    lines.append("")
    lines.append(f"- Compression candles in London KZ (07-10 UTC): **{q1411['kz_london_count']}**")
    lines.append(f"- Compression candles in NY KZ (13-17 UTC): **{q1411['kz_ny_count']}**")
    lines.append(
        f"- Fraction of compression candles inside any kill zone: "
        f"**{fmt_pct(q1411['kz_frac_of_compression'])}**"
    )
    lines.append(
        f"- Expected fraction if uniform across 24h: "
        f"**{fmt_pct(q1411['expected_kz_frac_uniform'])}**"
    )
    lines.append(f"- Binomial test (compression KZ count vs uniform expectation) p = {fmt_p(q1411['p_kz_vs_uniform'])}")
    lines.append("")
    kz_frac = q1411["kz_frac_of_compression"]
    exp_frac = q1411["expected_kz_frac_uniform"]
    if kz_frac < exp_frac * 0.85:
        redundancy_note = (
            "Compression candles are **UNDER-REPRESENTED in kill zones** relative "
            "to uniform expectation.  Q-14.11 thus captures a signal that is "
            "largely **distinct** from H25's intra-session vol peak (which lives "
            "IN kill zones).  Not redundant with H25."
        )
    elif kz_frac > exp_frac * 1.15:
        redundancy_note = (
            "Compression candles are **OVER-REPRESENTED in kill zones** "
            f"({fmt_pct(kz_frac)} vs {fmt_pct(exp_frac)} expected).  This is a "
            "SCALE-ARTIFACT rather than a W3 decay overlap: BB stdev(20) and "
            "KC ATR(14) both ride UP during the active session, so the "
            "rolling 25th-pct percentile rides up with them.  'Compression' "
            "measured this way means 'relative contraction WITHIN a high-vol "
            "regime', not 'absolutely quiet tape'.  Q-14.11 is therefore a "
            "**relative-vol-regime signal**, NOT a Tokyo/quiet-hours effect.  "
            "Partial conceptual overlap with H25 (both describe intra-session "
            "vol structure); distinct in mechanism (H25 = W1>W2>W3 decay "
            "magnitude; Q-14.11 = breakout direction after local contraction).  "
            "**Flagged for redundancy review** — if promoted, must be gated "
            "jointly with H25 to avoid double-counting."
        )
    else:
        redundancy_note = (
            "Compression candles are distributed roughly uniformly across kill "
            "zones and non-kill-zone hours.  Q-14.11 signal is **neither a pure "
            "kill-zone effect nor purely off-hours** — it is a volatility-regime "
            "signal that overlaps with H25 only at the margins."
        )
    lines.append(redundancy_note)
    lines.append("")
    # Hour histogram summary for transparency
    lines.append("#### Compression-candle count by hour (UTC)")
    lines.append("")
    lines.append("| hour | count |")
    lines.append("|---|---|")
    for h in sorted(q1411["hour_histogram_compression"].keys()):
        lines.append(f"| {h:02d} | {q1411['hour_histogram_compression'][h]} |")
    lines.append("")

    # -------- Verdicts --------
    lines.append("## Verdicts")
    lines.append("")
    # Q-14.9 — collect which cells passed and which direction drove it
    passing_cells_149 = [
        (k, g) for k in (3, 6, 12)
        for g in ("all_extensions", "too_far_up", "too_far_down")
        if q149["horizons"][k][g]["passes_prereg"]
    ]
    up_wins = any(g == "too_far_up" for _, g in passing_cells_149)
    down_wins = any(g == "too_far_down" for _, g in passing_cells_149)
    if any_149_pass:
        cell_list_md = ", ".join(f"k={k} {g}" for k, g in passing_cells_149)
        if down_wins and not up_wins:
            asymmetry_note = (
                "  Notable **directional asymmetry**: only the too-far-down "
                "grouping passes.  Extreme lows bounce (reversion-up) more than "
                "extreme highs fall (reversion-down).  This is consistent with "
                "an up-biased 2026 tape (gold in uptrend during Fed cuts) — "
                "extreme lows are retail capitulation into an uptrend and "
                "revert quickly, while extreme highs are trend continuation "
                "and do NOT revert.  **Effect may not generalize** to a "
                "trendless or down-biased regime."
            )
        elif up_wins and not down_wins:
            asymmetry_note = (
                "  Notable **directional asymmetry**: only the too-far-up "
                "grouping passes.  This is the opposite of 2026's up-biased "
                "regime and deserves replication in a bear or range sample."
            )
        else:
            asymmetry_note = ""
        lines.append(
            f"- **Q-14.9 (MM inventory reversion)**: Pre-registered threshold MET "
            f"at {len(passing_cells_149)} of 9 (k, grouping) cell(s): {cell_list_md}.  "
            "Effect is consistent with inventory-skew mean-reversion prior "
            "in this regime." + asymmetry_note
        )
    else:
        lines.append(
            "- **Q-14.9 (MM inventory reversion)**: Pre-registered threshold "
            "NOT met.  No (k, grouping) cell reached both >=60% reversion "
            "probability AND p_raw*3 < 0.017.  Extension candles on M15 do not "
            "exhibit statistically-anomalous reversion over k in {3,6,12} "
            "horizons.  Prior is **NOT supported** at this resolution."
        )
    # Q-14.11
    if q1411["passes_prereg"]:
        lines.append(
            "- **Q-14.11 (compression breakout)**: Pre-registered threshold MET "
            "(compression WR >= non-compression + 5pp, p < 0.05).  "
            "Effect size "
            f"{fmt_pp(q1411['delta_pp'])}, p_raw = {fmt_p(q1411['p_raw'])}.  "
            "Worth elevating to a shadow-logged gate."
        )
    else:
        lines.append(
            "- **Q-14.11 (compression breakout)**: Pre-registered threshold "
            "NOT met.  Delta "
            f"{fmt_pp(q1411['delta_pp'])}, p_raw = {fmt_p(q1411['p_raw'])}.  "
            "Prior is **NOT supported** on 2026 XAUUSD M15 data."
        )
    # Joint Bonferroni
    joint_fail_count = 0
    joint_pass_cells: list[str] = []
    for k in (3, 6, 12):
        for g in ("all_extensions", "too_far_up", "too_far_down"):
            r = q149["horizons"][k][g]
            if r["p_raw"] is not None and r["p_raw"] * joint_bonf_m < 0.05:
                joint_pass_cells.append(f"Q-14.9 k={k} {g}")
    if q1411["p_raw"] is not None and q1411["p_raw"] * joint_bonf_m < 0.05:
        joint_pass_cells.append("Q-14.11 compression breakout")
    if joint_pass_cells:
        lines.append(
            "- **Joint Bonferroni pass (p_joint < 0.05)**: "
            + ", ".join(joint_pass_cells)
        )
    else:
        lines.append(
            "- **Joint Bonferroni**: zero tests pass across both questions.  "
            f"Threshold p_joint < 0.05 requires p_raw < {0.05 / joint_bonf_m:.4f}."
        )
    lines.append("")

    # -------- Caveats --------
    lines.append("## Caveats")
    lines.append("")
    lines.append(
        "1. **XAUUSD only** — 2026 window, Jan 2 - Apr 10 (~3.5 months).  Results "
        "may not generalize to US30, FX majors, or other regimes."
    )
    lines.append(
        "2. **Broker tick-volume, not true volume** — data is retail MT5 OHLCV; "
        "not order flow, not prints.  All volume-agnostic here."
    )
    lines.append(
        "3. **No economic-calendar control** — extensions during NFP / FOMC / "
        "CPI are included.  A filtered rerun around macro windows could isolate "
        "regime-dependent reversion differently."
    )
    lines.append(
        "4. **Compression definition is joint BB AND KC** — pre-registered.  "
        "Using EITHER (OR) would increase sample at the cost of signal purity."
    )
    lines.append(
        "5. **Continuation WR uses 6-candle horizon only for Q-14.11** — "
        "pre-registered.  A sweep across k={3,6,12} would multiply tests and "
        "was deliberately NOT done to respect Bonferroni budget."
    )
    lines.append(
        "6. **Reversion metric is sign-based, not magnitude-based** — Q-14.9 "
        "measures P(direction reverses), not expected R-multiple.  A trader "
        "would care about magnitude; use as signal-screen only."
    )
    lines.append(
        "7. **No overlapping-observation correction** — consecutive M15 bars are "
        "serially correlated; reported p-values treat events as independent and "
        "may be slightly optimistic.  True effective sample size is lower than "
        "nominal n."
    )
    lines.append("")

    # -------- Next steps --------
    lines.append("## Next steps")
    lines.append("")
    lines.append(
        "1. If any Q-14.9 cell survives joint Bonferroni, replicate on the other "
        "4 instruments (US30, USDJPY, GBPJPY, GBPUSD) before promoting to any "
        "production gate.  Sample gate: >=3/5 instruments reproduce."
    )
    lines.append(
        "2. If Q-14.11 fails on 2026 XAUUSD but shows directional signal, extend "
        "to multi-year 2023-2025 M15 to check whether 2026 is anomalously "
        "trend-biased (Fed cutting regime).  Do NOT promote without multi-year."
    )
    lines.append(
        "3. Revisit Q-14.9 with an R-multiple outcome (ATR-normalized forward "
        "excursion) rather than sign-only reversion.  Sign can flip with noise; "
        "magnitude is what matters for trade expectancy."
    )
    lines.append(
        "4. **Do not deploy based on this single test**.  Even a Bonferroni-"
        "passing cell on one instrument, one 3.5-month window, one tape bias "
        "(bull) is hypothesis-generating, not production-ready.  Pre-commit "
        "replication gates BEFORE touching trading logic:"
    )
    lines.append("   - >=3/5 instruments show same direction + >=50% of original delta")
    lines.append("   - 2023-2025 multi-year replication shows consistent effect")
    lines.append("   - Regime-split (bull/bear/range year) passes in >=2/3")
    lines.append("   If any replication gate fails, log as 'tested, regime-bound' and close.")
    lines.append("")
    lines.append(
        "5. Post-hoc threshold tuning (e.g., trying |z|>1.5 or |z|>2.5 because "
        "2.0 partially worked) is explicitly off-limits per CLAUDE.md agent-"
        "reliability rules.  Any follow-up rerun must pre-register a new "
        "hypothesis with distinct mechanism justification."
    )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("Loading M15 data...")
    m15 = load_ohlc(M15_CSV)
    print(f"  {len(m15)} bars, {m15['time'].min()} -> {m15['time'].max()}")
    print("Loading H1 data (reference only)...")
    h1 = load_ohlc(H1_CSV)
    print(f"  {len(h1)} bars, {h1['time'].min()} -> {h1['time'].max()}")

    print("\nRunning Q-14.9 (MM inventory reversion)...")
    q149 = run_q_14_9(m15)
    print(f"  ext_any={q149['n_extension_any']}, baseline={q149['n_baseline']}")
    for k in (3, 6, 12):
        r = q149["horizons"][k]["all_extensions"]
        if r["p_ext"] is not None:
            print(f"  k={k}: P(rev|ext)={r['p_ext']:.3f} vs base={r['p_base']:.3f} delta={r['delta_pp']:+.1f}pp p={r['p_raw']:.4f}")

    print("\nRunning Q-14.11 (compression breakout)...")
    q1411 = run_q_14_11(m15)
    print(
        f"  comp_bars={q1411['n_compression_bars']} / {q1411['n_total_bars']} "
        f"({q1411['compression_frac']:.1%})"
    )
    print(
        f"  breakouts: comp={q1411['n_breakouts_from_compression']} "
        f"vs non-comp={q1411['n_breakouts_non_compression']}"
    )
    cs = q1411["comp_stats"]
    ncs = q1411["non_comp_stats"]
    print(
        f"  WR: comp={cs['wr']:.3f} (n={cs['n']}) vs non-comp={ncs['wr']:.3f} (n={ncs['n']})"
    )
    print(
        f"  delta={q1411['delta_pp']:+.1f}pp p_raw={q1411['p_raw']:.4f}"
    )

    joint_bonf_m = 10  # 9 cells for Q-14.9 + 1 for Q-14.11
    md = render_md(q149, q1411, joint_bonf_m)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"\nWrote {OUT_MD}")


if __name__ == "__main__":
    main()
