"""
Q-16 adversarial / game-theoretic analysis — local-data only, $0 cost.

Four sub-questions:
    Q-16.1 Predatory trading / forced-flow detection:
        Can we flag candles with stop-hunt / forced-liquidation signatures
        (extreme range + volume spike + close near extreme), and do they
        systematically revert?
    Q-16.3 CFD/FX market design:
        Are there session-open / news-hour patterns unique to retail CFD
        venues (gaps, volatility clusters at specific minute-of-session)?
    Q-16.5 Informed vs uninformed flow (VPIN-style):
        Do OHLCV-derived bulk-volume classification flow imbalance metrics
        discriminate entry quality (high-VPIN vs low-VPIN WR gap)?
    Q-16.6 Game-theoretic response to SMC crowding:
        If OB retest is crowded, what is the defensive play? (qualitative,
        mapped against the current system's behavior.)

Pre-registered hypotheses & thresholds — see Q-16_adversarial.md header.

Data:
    data/historical_2026/XAUUSD_M15.csv  (Jan 2 - Apr 10 2026, ~6420 bars)
    data/historical_2026/XAUUSD_H1.csv   (same window, ~1600 bars)
    knowledge_base_backtest/analysis/unified_trades_v2_20260331.json  (n=111)

Output:
    research/academic_pipeline/results/Q-16_adversarial.md
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
M15_PATH = ROOT / "data" / "historical_2026" / "XAUUSD_M15.csv"
H1_PATH = ROOT / "data" / "historical_2026" / "XAUUSD_H1.csv"
TRADES_PATH = ROOT / "knowledge_base_backtest" / "analysis" / "unified_trades_v2_20260331.json"
OUT_MD = ROOT / "research" / "academic_pipeline" / "results" / "Q-16_adversarial.md"

# --------------------------------------------------------------------------- #
# Pre-registered parameters                                                   #
# --------------------------------------------------------------------------- #

# Q-16.1
ATR_PERIOD = 14
RANGE_ATR_THRESHOLD = 3.0           # candle range >= 3 * ATR14
VOLUME_WINDOW = 50                  # lookback for volume top-decile
VOLUME_TOP_DECILE = 0.90            # >= 90th pct over prior 50 bars
CLOSE_EXTREME_FRAC = 0.20           # close within 20% of high (or low)
REVERSION_LOOKAHEAD = 6             # 6 forward candles

# Q-16.3
# MT5 broker timestamps in CSV are typically EET (UTC+2 winter / UTC+3 summer DST).
# Data range Jan 2 - Apr 10 2026 straddles the Mar DST jump (EU DST = last Sun Mar
# = Mar 29 2026; US DST = 2nd Sun Mar = Mar 8 2026). We treat broker-clock hours
# directly (they align with broker sessions); session labels are defined in
# broker-clock terms and cross-referenced against UTC at the end.
# Broker-hour session opens (MT5 EET/EEST-ish clock):
SESSION_OPENS_BROKER = {
    "Sydney":   (22, 0),   # Sydney open in broker clock (~23:00 UTC-DST / 22:00 UTC)
    "Tokyo":    (2, 0),    # Tokyo open broker-clock (~00:00 UTC)
    "London":   (10, 0),   # London open broker-clock (~08:00 UTC summer / 09:00 UTC winter)
    "NewYork":  (15, 30),  # NY futures open broker-clock (~13:30 UTC)
}
# NOTE: 01:00 is the earliest bar observed (hour 0 absent); we default session
# segment windows to broker-clock hours that exist in the data and report
# UTC mapping caveats in the report.

# Q-16.5
VPIN_WINDOW = 50
VPIN_TERCILE = 1.0 / 3.0

# --------------------------------------------------------------------------- #
# Stats helpers                                                               #
# --------------------------------------------------------------------------- #

def _erf(x: float) -> float:
    # Abramowitz & Stegun 7.1.26 approximation
    a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
    p = 0.3275911
    sign = 1 if x >= 0 else -1
    x = abs(x)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
    return sign * y


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + _erf(x / math.sqrt(2.0)))


def two_prop_z(x1: int, n1: int, x2: int, n2: int) -> tuple[float, float]:
    """Two-proportion z, two-sided p."""
    if n1 == 0 or n2 == 0:
        return float("nan"), float("nan")
    p1, p2 = x1 / n1, x2 / n2
    p = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return 0.0, 1.0
    z = (p1 - p2) / se
    pval = 2.0 * (1.0 - norm_cdf(abs(z)))
    return z, pval


def one_prop_z(x: int, n: int, p0: float) -> tuple[float, float]:
    """One-proportion z-test vs p0, two-sided."""
    if n == 0:
        return float("nan"), float("nan")
    phat = x / n
    se = math.sqrt(p0 * (1 - p0) / n)
    if se == 0:
        return 0.0, 1.0
    z = (phat - p0) / se
    pval = 2.0 * (1.0 - norm_cdf(abs(z)))
    return z, pval


def welch_t(xs: list[float], ys: list[float]) -> tuple[float, float, int]:
    """Welch's t + two-sided p (normal approx)."""
    nx, ny = len(xs), len(ys)
    if nx < 2 or ny < 2:
        return float("nan"), float("nan"), 0
    mx, my = sum(xs) / nx, sum(ys) / ny
    vx = sum((x - mx) ** 2 for x in xs) / (nx - 1)
    vy = sum((y - my) ** 2 for y in ys) / (ny - 1)
    se = math.sqrt(vx / nx + vy / ny)
    if se == 0:
        return 0.0, 1.0, nx + ny - 2
    t = (mx - my) / se
    # Normal approx for df > 30 is fine
    df = int((vx / nx + vy / ny) ** 2 /
             ((vx / nx) ** 2 / max(1, nx - 1) + (vy / ny) ** 2 / max(1, ny - 1)))
    p = 2.0 * (1.0 - norm_cdf(abs(t)))
    return t, p, df


# --------------------------------------------------------------------------- #
# Data loaders                                                                #
# --------------------------------------------------------------------------- #

@dataclass
class Bar:
    time: datetime
    o: float
    h: float
    l: float
    c: float
    v: float


def load_bars(path: Path) -> list[Bar]:
    out: list[Bar] = []
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            out.append(Bar(
                datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S"),
                float(row["open"]), float(row["high"]),
                float(row["low"]),  float(row["close"]),
                float(row["volume"]),
            ))
    out.sort(key=lambda b: b.time)
    return out


def compute_atr(bars: list[Bar], period: int = 14) -> list[float]:
    """ATR using Wilder's smoothing; first `period` values are NaN-proxy (None)."""
    tr = [bars[0].h - bars[0].l]
    for i in range(1, len(bars)):
        prev_c = bars[i - 1].c
        tr.append(max(
            bars[i].h - bars[i].l,
            abs(bars[i].h - prev_c),
            abs(bars[i].l - prev_c),
        ))
    atr: list[float] = [float("nan")] * len(bars)
    if len(bars) < period:
        return atr
    seed = sum(tr[:period]) / period
    atr[period - 1] = seed
    for i in range(period, len(bars)):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


# --------------------------------------------------------------------------- #
# Q-16.1 — Forced-flow / stop-hunt detection                                  #
# --------------------------------------------------------------------------- #

def q16_1_forced_flow(bars: list[Bar]) -> dict:
    """
    Flag forced-flow candles:
        - range / ATR14 > RANGE_ATR_THRESHOLD
        - volume in top-decile over prior VOLUME_WINDOW bars
        - close within CLOSE_EXTREME_FRAC of high (bullish forced) or low (bearish)
    Measure 6-candle forward reversion WR against the candle's direction.
    Baseline: extreme-range candles *without* volume spike.
    """
    atr = compute_atr(bars, ATR_PERIOD)
    n = len(bars)
    forced_ups: list[int] = []
    forced_dns: list[int] = []
    baseline_ups: list[int] = []  # extreme-range, NOT top-vol, bullish closer
    baseline_dns: list[int] = []

    extreme_any = 0
    for i in range(VOLUME_WINDOW, n - REVERSION_LOOKAHEAD):
        a = atr[i]
        if a != a or a <= 0:  # NaN or zero
            continue
        rng = bars[i].h - bars[i].l
        if rng <= 0:
            continue
        if rng / a <= RANGE_ATR_THRESHOLD:
            continue
        extreme_any += 1
        # prior-50-bar volume distribution (exclusive of current)
        prior_vol = sorted(b.v for b in bars[i - VOLUME_WINDOW:i])
        thresh_idx = int(VOLUME_TOP_DECILE * len(prior_vol))  # 45 for 50 bars
        thresh_idx = min(thresh_idx, len(prior_vol) - 1)
        vol_thresh = prior_vol[thresh_idx]
        vol_spike = bars[i].v >= vol_thresh

        # Close position within range
        # rel = (close - low) / range ; near 1 = bullish forced up, near 0 = bearish forced down
        rel = (bars[i].c - bars[i].l) / rng
        bull_close = rel >= (1.0 - CLOSE_EXTREME_FRAC)
        bear_close = rel <= CLOSE_EXTREME_FRAC

        if not (bull_close or bear_close):
            continue

        if vol_spike:
            if bull_close:
                forced_ups.append(i)
            else:
                forced_dns.append(i)
        else:
            if bull_close:
                baseline_ups.append(i)
            else:
                baseline_dns.append(i)

    # Reversion test:
    # For a bullish forced-flow candle (closed near high), the contrarian position
    # is SHORT. "Reversion WIN" = at some point in the next 6 bars, price trades
    # back to the candle's midpoint (or lower). Symmetric for bearish.
    def reversion_wr(idxs: list[int], direction: str) -> tuple[int, int]:
        wins = 0
        for i in idxs:
            mid = (bars[i].h + bars[i].l) / 2.0
            hit = False
            for j in range(i + 1, min(i + 1 + REVERSION_LOOKAHEAD, n)):
                if direction == "bull":
                    # contrarian = short; reverts if price trades at or below mid
                    if bars[j].l <= mid:
                        hit = True
                        break
                else:
                    # bear; contrarian = long; reverts if price trades at or above mid
                    if bars[j].h >= mid:
                        hit = True
                        break
            if hit:
                wins += 1
        return wins, len(idxs)

    fu_w, fu_n = reversion_wr(forced_ups, "bull")
    fd_w, fd_n = reversion_wr(forced_dns, "bear")
    bu_w, bu_n = reversion_wr(baseline_ups, "bull")
    bd_w, bd_n = reversion_wr(baseline_dns, "bear")

    # Combined (pooled, both directions)
    f_w = fu_w + fd_w
    f_n = fu_n + fd_n
    b_w = bu_w + bd_w
    b_n = bu_n + bd_n

    # Forced-flow vs 50% null (one-prop test)
    z_vs_null, p_vs_null = one_prop_z(f_w, f_n, 0.50)
    # Forced-flow vs baseline (two-prop test)
    z_vs_base, p_vs_base = two_prop_z(f_w, f_n, b_w, b_n)

    return {
        "n_bars_eligible": n - VOLUME_WINDOW - REVERSION_LOOKAHEAD,
        "extreme_range_total": extreme_any,
        "forced_ups": fu_n, "forced_ups_wins": fu_w,
        "forced_dns": fd_n, "forced_dns_wins": fd_w,
        "baseline_ups": bu_n, "baseline_ups_wins": bu_w,
        "baseline_dns": bd_n, "baseline_dns_wins": bd_w,
        "forced_pooled_n": f_n, "forced_pooled_w": f_w,
        "forced_pooled_wr": (f_w / f_n) if f_n else float("nan"),
        "baseline_pooled_n": b_n, "baseline_pooled_w": b_w,
        "baseline_pooled_wr": (b_w / b_n) if b_n else float("nan"),
        "z_vs_null50": z_vs_null, "p_vs_null50": p_vs_null,
        "z_vs_baseline": z_vs_base, "p_vs_baseline": p_vs_base,
    }


# --------------------------------------------------------------------------- #
# Q-16.3 — Session-open patterns                                              #
# --------------------------------------------------------------------------- #

def q16_3_session_patterns(bars: list[Bar]) -> dict:
    """
    For each session (Sydney/Tokyo/London/NewYork), tag M15 bars by
    minute-of-session bucket: {0-15, 15-60, 60-mid (=3h), last 30m (=-30m
    of a 4h session)}. We use a 4-hour window starting at each session open
    as the session frame. Compare realized volatility (range / mid) and
    range vs the non-session baseline.
    """
    # Define session windows as 4h blocks starting at session open (broker clock)
    sessions = {}
    for name, (h, m) in SESSION_OPENS_BROKER.items():
        start_min = h * 60 + m
        sessions[name] = {
            "open_min": start_min,
            "buckets": {
                "first15":  (start_min, start_min + 15),
                "next15_60": (start_min + 15, start_min + 60),
                "midSession": (start_min + 60, start_min + 180),
                "last30": (start_min + 180, start_min + 240),
            },
        }

    # Baseline: all bars outside any session 4h window
    all_session_mins = set()
    for s in sessions.values():
        for mm in range(s["open_min"], s["open_min"] + 240):
            all_session_mins.add(mm % (24 * 60))

    # Collect per-bucket bars
    per_bucket: dict[tuple[str, str], list[Bar]] = defaultdict(list)
    baseline_bars: list[Bar] = []
    for b in bars:
        bar_min = b.time.hour * 60 + b.time.minute
        hit = False
        for name, s in sessions.items():
            for bname, (lo, hi) in s["buckets"].items():
                lo_m = lo % (24 * 60)
                hi_m = hi % (24 * 60)
                if lo_m < hi_m:
                    in_bucket = lo_m <= bar_min < hi_m
                else:
                    in_bucket = bar_min >= lo_m or bar_min < hi_m
                if in_bucket:
                    per_bucket[(name, bname)].append(b)
                    hit = True
        if not hit:
            baseline_bars.append(b)

    # Metrics per bucket: mean range, mean normalized range (range / mid)
    def summarize(bars_sub: list[Bar]) -> dict:
        if not bars_sub:
            return {"n": 0, "mean_range": float("nan"),
                    "mean_norm_range": float("nan"),
                    "mean_vol": float("nan")}
        rngs = [b.h - b.l for b in bars_sub]
        norms = [(b.h - b.l) / ((b.h + b.l) / 2.0) for b in bars_sub]
        vols = [b.v for b in bars_sub]
        return {
            "n": len(bars_sub),
            "mean_range": sum(rngs) / len(rngs),
            "mean_norm_range": sum(norms) / len(norms),
            "mean_vol": sum(vols) / len(vols),
        }

    base = summarize(baseline_bars)

    bucket_stats: dict[tuple[str, str], dict] = {}
    tests: list[dict] = []
    for (sname, bname), bsub in per_bucket.items():
        s = summarize(bsub)
        bucket_stats[(sname, bname)] = s
        # Welch's t vs baseline on range (not normalized — absolute dollar range)
        t, p, df = welch_t([b.h - b.l for b in bsub],
                           [b.h - b.l for b in baseline_bars])
        ratio = s["mean_range"] / base["mean_range"] if base["mean_range"] else float("nan")
        tests.append({
            "session": sname, "bucket": bname,
            "n": s["n"],
            "mean_range": s["mean_range"], "baseline_range": base["mean_range"],
            "ratio": ratio, "t": t, "p": p, "df": df,
        })

    tests.sort(key=lambda r: (-r["ratio"] if r["ratio"] == r["ratio"] else 0))
    return {
        "baseline": base,
        "per_bucket": {f"{k[0]}/{k[1]}": v for k, v in bucket_stats.items()},
        "tests": tests,
    }


# --------------------------------------------------------------------------- #
# Q-16.5 — VPIN proxy                                                         #
# --------------------------------------------------------------------------- #

def vpin_series(bars: list[Bar], window: int = VPIN_WINDOW) -> list[float]:
    """
    Bulk-Volume Classification:
        buy_frac = (close - low) / (high - low) if range > 0 else 0.5
        buy_vol  = buy_frac * volume
        sell_vol = (1 - buy_frac) * volume
    VPIN(i) = sum_j |buy_vol_j - sell_vol_j| / sum_j volume_j   over prior `window` bars.
    Returns list same length as bars (NaN until window filled).
    """
    imb = []
    vol = []
    for b in bars:
        rng = b.h - b.l
        buy_frac = ((b.c - b.l) / rng) if rng > 0 else 0.5
        buy_v = buy_frac * b.v
        sell_v = b.v - buy_v
        imb.append(abs(buy_v - sell_v))
        vol.append(b.v)

    out: list[float] = [float("nan")] * len(bars)
    for i in range(len(bars)):
        if i + 1 < window:
            continue
        lo = i + 1 - window
        sv = sum(vol[lo:i + 1])
        if sv <= 0:
            continue
        out[i] = sum(imb[lo:i + 1]) / sv
    return out


def q16_5_vpin(bars: list[Bar], trades: list[dict]) -> dict:
    """
    Match each batch trade (2026-only, in CSV range) to the closing M15 bar
    immediately prior to trade date. Assign VPIN. Tercile split. Compare WR.
    """
    v_series = vpin_series(bars, VPIN_WINDOW)

    # Index bars by date for lookup: last bar of that trading day
    # Better: find last M15 bar with time < next day 00:00 on the trade date.
    by_date_last: dict[str, int] = {}
    for idx, b in enumerate(bars):
        key = b.time.strftime("%Y-%m-%d")
        by_date_last[key] = idx   # last occurrence wins (bars sorted)

    matched: list[tuple[dict, float]] = []
    skipped_no_bar = 0
    skipped_no_vpin = 0

    for t in trades:
        d = t.get("date", "")
        # Use the *prior* trading day's VPIN as the "flow context at entry"
        # (VPIN at t's own day would leak same-day outcome).
        trade_dt = datetime.strptime(d, "%Y-%m-%d")
        # Walk backward 1, 2, 3 days for the last available bar
        chosen_idx = None
        for back in range(1, 6):
            prev = (trade_dt - timedelta(days=back)).strftime("%Y-%m-%d")
            if prev in by_date_last:
                chosen_idx = by_date_last[prev]
                break
        if chosen_idx is None:
            skipped_no_bar += 1
            continue
        v = v_series[chosen_idx]
        if v != v:
            skipped_no_vpin += 1
            continue
        matched.append((t, v))

    # Tercile split
    if len(matched) < 9:
        return {
            "matched": len(matched),
            "skipped_no_bar": skipped_no_bar,
            "skipped_no_vpin": skipped_no_vpin,
            "underpowered": True,
            "terciles": {},
        }

    vpins = sorted(v for _, v in matched)
    q1 = vpins[int(len(vpins) * VPIN_TERCILE)]
    q2 = vpins[int(len(vpins) * (1 - VPIN_TERCILE)) - 1]

    def bucket(v: float) -> str:
        if v <= q1:
            return "low"
        if v >= q2:
            return "high"
        return "mid"

    terciles: dict[str, dict] = {
        "low": {"wins": 0, "losses": 0, "be": 0, "r_sum": 0.0},
        "mid": {"wins": 0, "losses": 0, "be": 0, "r_sum": 0.0},
        "high": {"wins": 0, "losses": 0, "be": 0, "r_sum": 0.0},
    }
    for trade, v in matched:
        b = bucket(v)
        o = trade.get("outcome", "")
        r = trade.get("r_multiple", 0.0)
        terciles[b]["r_sum"] += float(r)
        if o == "WIN":
            terciles[b]["wins"] += 1
        elif o == "LOSS":
            terciles[b]["losses"] += 1
        else:
            terciles[b]["be"] += 1

    for b, d in terciles.items():
        wl = d["wins"] + d["losses"]
        d["n_wl"] = wl
        d["n_all"] = wl + d["be"]
        d["wr"] = d["wins"] / wl if wl else float("nan")
        d["exp_r"] = d["r_sum"] / d["n_all"] if d["n_all"] else float("nan")

    # High vs low tercile two-prop
    hz, hp = two_prop_z(
        terciles["high"]["wins"], terciles["high"]["n_wl"],
        terciles["low"]["wins"],  terciles["low"]["n_wl"],
    )

    return {
        "matched": len(matched),
        "skipped_no_bar": skipped_no_bar,
        "skipped_no_vpin": skipped_no_vpin,
        "q1_threshold": q1,
        "q2_threshold": q2,
        "vpin_min": vpins[0],
        "vpin_median": vpins[len(vpins) // 2],
        "vpin_max": vpins[-1],
        "terciles": terciles,
        "high_vs_low_z": hz, "high_vs_low_p": hp,
        "gap_pp": (terciles["high"]["wr"] - terciles["low"]["wr"]) * 100
                 if terciles["high"].get("wr") == terciles["high"].get("wr")
                 and terciles["low"].get("wr") == terciles["low"].get("wr") else float("nan"),
    }


# --------------------------------------------------------------------------- #
# Q-16.6 — Game-theoretic response to SMC crowding (qualitative)              #
# --------------------------------------------------------------------------- #

def q16_6_gametheoretic_map() -> dict:
    """
    Map each candidate defensive play (a)-(d) against current system behavior.
    Qualitative; no stats. Evidence field states what WOULD update the view.
    """
    # Current system features (as of 2026-04-17) — cross-referenced against CLAUDE.md
    # and src/components:
    #   - touch_count gate: rejects OB with touch_count >= 2 (handoff 19/20; live)
    #   - partial_close shadow logger: Variant C 33% at 1.0R (handoff 13; shadow only)
    #   - proximity_shadow_logger: observation at candle close
    #   - liquidity_cluster gate: NEW, ships DISABLED, shadow-log first (handoff 20)
    #   - 5-instrument portfolio: XAUUSD, US30, USDJPY, GBPJPY, GBPUSD
    #   - m5_refinement: optional deeper entry refinement component
    plays = [
        {
            "option": "(a) Deeper entry / pre-retest",
            "defensive_rationale": "If crowd fills at the OB edge, pre-position closer to the OB mid / 50% zone to get filled before crowd liquidity absorbs the move.",
            "current_system": "PARTIAL. Limit-order architecture (handoff 16) lets price be caught on pullback; m5_refinement can tighten entry. No explicit 'mid-OB' entry pricing — default entry_price is AI-nominated edge.",
            "update_evidence": "If a batch sub-analysis shows mid-OB-50% entries have materially better MFE/R than edge entries on the same setups (n>=30, p<0.0125), tighten entry_price to 0.5 * (ob_high + ob_low) for LONGs.",
        },
        {
            "option": "(b) Earlier exit / skim first touch",
            "defensive_rationale": "If the crowd takes profit at +1R and unwinds the move, capture 33-50% at 1R before the reversal.",
            "current_system": "SHADOW-LOGGED. partial_close_shadow_logger (Variant C: 33% @ 1.0R) is running observation-only. Not yet promoted. BE shadow logger tracks +1R -> BE hypothetical.",
            "update_evidence": "If the partial_close shadow logger shows >0 delta_R with p<0.05 across 30+ trades, promote to live (per existing WF-2 promotion rules).",
        },
        {
            "option": "(c) Fade the SMC crowd (go opposite)",
            "defensive_rationale": "If OB retests systematically fail, the contrarian position becomes the edge. Stop-hunt / forced-flow candles (Q-16.1) are a direct instantiation of this.",
            "current_system": "NOT IMPLEMENTED. Q-16.4 contrarian framework was previously underpowered (n=2 matched). Q-16.1 adds candle-level forced-flow detection.",
            "update_evidence": "(1) Q-16.1 pooled reversion WR >= 55% with p<0.0125 AND baseline delta >= 5pp -> shadow-log a forced-flow contrarian signal. (2) Rolling-window WR of the live strategy trending negatively (Kendall tau < 0, p < 0.05 on a fresh window >= 40 trades) would warrant a directional flip trial.",
        },
        {
            "option": "(d) Alternative instruments / niche diversification",
            "defensive_rationale": "Crowd effects are correlated with venue popularity. Trading a less-crowded cross (e.g., USDJPY, GBPJPY) or a less-SMC-targeted instrument diversifies the adversary.",
            "current_system": "IMPLEMENTED. Portfolio is already 5 instruments. USDJPY batch WR 75.8% (n=33, p=1.96e-4) — strongest; GBPJPY 57.1% (n=42, weakest). GBPUSD observer-only. US30 68% continuation on sweep divergence (handoff H16).",
            "update_evidence": "If USDJPY live WR holds above XAUUSD live WR across another 30+ trades with p<0.05, CEO could allocate more risk budget to USDJPY. The 8% drawdown rule (H29) makes this automatic to some degree.",
        },
    ]
    return {"plays": plays}


# --------------------------------------------------------------------------- #
# Renderer                                                                    #
# --------------------------------------------------------------------------- #

def fmt(v, digits=3):
    if v is None:
        return "nan"
    try:
        if v != v:
            return "nan"
    except TypeError:
        return str(v)
    if isinstance(v, float):
        if math.isnan(v):
            return "nan"
        if abs(v) >= 1000:
            return f"{v:,.0f}"
        return f"{v:.{digits}f}"
    return str(v)


def render_markdown(q161, q163, q165, q166, trade_meta, bar_meta) -> str:
    out: list[str] = []
    out.append("# Q-16 Adversarial / Game-Theoretic Analysis")
    out.append("")
    out.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} local")
    out.append("Script: `research/academic_pipeline/scripts/q_16_adversarial.py`")
    out.append("Cost: $0 (local only).")
    out.append("")
    out.append("## Pre-registered hypotheses")
    out.append("")
    out.append("Stated BEFORE any data inspection. No post-hoc threshold tuning.")
    out.append("")
    out.append("**Q-16.1 — Predatory / forced-flow detection.**")
    out.append("")
    out.append("- H1. Candles where (range/ATR14) > 3 AND tick_volume is in top-decile of prior 50 bars AND close is within 20% of the candle's high (or low) exhibit a 6-candle forward reversion rate >= 55%, vs 50% null. One-prop z-test, two-sided.")
    out.append("- H2. Forced-flow candles show higher reversion WR than extreme-range-but-normal-volume candles (baseline). Two-prop z-test.")
    out.append("- Pre-registered significance: Bonferroni-adjusted α = 0.05/4 = 0.0125.")
    out.append("")
    out.append("**Q-16.3 — Session-open patterns.**")
    out.append("")
    out.append("- H3. At least one session-open bucket (first 15m / 15-60m / mid / last 30m) shows mean range >= 1.5× the non-session baseline, with Welch's t two-sided p < 0.01.")
    out.append("- H4. Sydney/Tokyo/London/NY opens (retail CFD-relevant hours) each differ measurably from baseline — report ratios even if non-significant.")
    out.append("")
    out.append("**Q-16.5 — OHLCV-VPIN proxy (informed vs uninformed flow).**")
    out.append("")
    out.append("- H5. Classifying tick_volume via close-in-range Bulk Volume Classification, then computing rolling 50-bar VPIN, and matching each XAUUSD trade to the prior-session VPIN: the WR gap between the top and bottom tercile is >= 5 percentage points with p < 0.0125 (two-prop z).")
    out.append("- H6. Trade-population terciles are balanced (within 20% of uniform).")
    out.append("")
    out.append("**Q-16.6 — Game-theoretic response to SMC crowding.**")
    out.append("")
    out.append("- Qualitative. Operational question: If OB retest is in fact crowded, which of (a) deeper entry, (b) earlier exit, (c) fade the crowd, (d) alternative instruments is the defensive play, and which does the current system already implement? The 'evidence that would update' field specifies what data would trigger re-classification.")
    out.append("")
    out.append("## Upfront caveats and scope")
    out.append("")
    out.append("- **Tick volume on CFD is a proxy for true trade volume.** CFD tick_volume = number of price updates received by the broker terminal, not volume traded at venue. High correlation with real volume in most regimes, but systematically biased during illiquid overnight hours (broker feed heartbeat dominates) and during news spikes (multiple price updates per true trade). This applies to Q-16.1 and Q-16.5.")
    out.append("- **MT5 broker clock.** CSVs are in broker-local time (typically EET/EEST; the data starts at 01:00 not 00:00, consistent with EET/EEST where hour 0 = 22:00/23:00 UTC the prior day). We label sessions by broker clock and report UTC equivalents in the Q-16.3 section. The Jan 2 - Apr 10 window straddles the Mar 8 2026 US DST change and the Mar 29 2026 EU DST change — this introduces minor session-drift noise that is not corrected here.")
    out.append("- **Data window is 2026-01-02 to 2026-04-10 only.** Historical CSVs do not extend pre-2026. Q-16.5 can only match batch trades within this window (~29/111).")
    out.append("- **Cross-reference with Wave 2.** Q-16.5 shares trade-population dependence with Q-crowding_retail.md (Q-8.3/Q-16.4); if a VPIN WR gap exists, it may be confounded with the same upward-trending WR documented there (Kendall tau +0.754, p<0.001). Sample-overlap flagged explicitly.")
    out.append("")
    out.append("## Data")
    out.append("")
    out.append(f"- **M15 bars:** `{M15_PATH.as_posix()}` — {bar_meta['n_m15']} bars, {bar_meta['m15_start']} → {bar_meta['m15_end']}.")
    out.append(f"- **H1 bars:** `{H1_PATH.as_posix()}` — {bar_meta['n_h1']} bars.")
    out.append(f"- **Batch trades:** `{TRADES_PATH.as_posix()}` — n={trade_meta['n']}. 2026-only subset used for Q-16.5 matching: n={trade_meta['n_2026']}.")
    out.append("")

    # ------------------------- Q-16.1 -------------------------
    out.append("## Q-16.1 — Predatory / forced-flow detection")
    out.append("")
    out.append("### Method (deterministic)")
    out.append("")
    out.append("1. Compute ATR14 on M15 bars (Wilder's smoothing).")
    out.append("2. For each bar i with i > 50 and i + 6 < N: flag if")
    out.append("   - (high-low) / ATR14 > 3.0, AND")
    out.append("   - volume >= 90th percentile of the prior 50 bars, AND")
    out.append("   - close within 20% of high (bullish forced) OR within 20% of low (bearish forced).")
    out.append("3. Reversion test: for a bullish forced candle, contrarian = SHORT; WIN if in the next 6 bars any bar's low <= candle mid. Symmetric for bearish.")
    out.append("4. Baseline: extreme-range candles (> 3x ATR) without top-decile volume. Same close-extreme and reversion rules.")
    out.append("")
    out.append("### Results")
    out.append("")
    out.append(f"- Eligible bars (post-ATR-warmup, pre-lookahead buffer): {q161['n_bars_eligible']:,}")
    out.append(f"- Extreme-range candles total (>3× ATR, any volume): {q161['extreme_range_total']}")
    out.append("")
    out.append("| subset | n | reversion wins | WR |")
    out.append("|---|---|---|---|")
    out.append(f"| forced UPs (bull close) | {q161['forced_ups']} | {q161['forced_ups_wins']} | {fmt(q161['forced_ups_wins']/q161['forced_ups']) if q161['forced_ups'] else 'nan'} |")
    out.append(f"| forced DNs (bear close) | {q161['forced_dns']} | {q161['forced_dns_wins']} | {fmt(q161['forced_dns_wins']/q161['forced_dns']) if q161['forced_dns'] else 'nan'} |")
    out.append(f"| **forced pooled** | **{q161['forced_pooled_n']}** | **{q161['forced_pooled_w']}** | **{fmt(q161['forced_pooled_wr'])}** |")
    out.append(f"| baseline UPs | {q161['baseline_ups']} | {q161['baseline_ups_wins']} | {fmt(q161['baseline_ups_wins']/q161['baseline_ups']) if q161['baseline_ups'] else 'nan'} |")
    out.append(f"| baseline DNs | {q161['baseline_dns']} | {q161['baseline_dns_wins']} | {fmt(q161['baseline_dns_wins']/q161['baseline_dns']) if q161['baseline_dns'] else 'nan'} |")
    out.append(f"| **baseline pooled** | **{q161['baseline_pooled_n']}** | **{q161['baseline_pooled_w']}** | **{fmt(q161['baseline_pooled_wr'])}** |")
    out.append("")
    out.append(f"- **Forced vs 50% null:** z = {fmt(q161['z_vs_null50'])}, two-sided p = {fmt(q161['p_vs_null50'])}")
    out.append(f"- **Forced vs baseline:** z = {fmt(q161['z_vs_baseline'])}, two-sided p = {fmt(q161['p_vs_baseline'])}")
    out.append("")
    # verdict
    f_wr = q161["forced_pooled_wr"]
    pass_null = (q161["p_vs_null50"] < 0.0125) and (f_wr >= 0.55)
    pass_base = q161["p_vs_baseline"] < 0.0125
    out.append("### Q-16.1 verdict")
    out.append("")
    if q161["forced_pooled_n"] < 20:
        out.append("**UNDERPOWERED** — n < 20 forced-flow candles. Extend data window or relax thresholds to re-test.")
    elif pass_null and pass_base:
        out.append(f"**SIGNAL** — forced-flow candles revert at {f_wr*100:.1f}% (vs 50% null, p={fmt(q161['p_vs_null50'])}) and beat the extreme-range baseline (p={fmt(q161['p_vs_baseline'])}). Meets pre-registered thresholds at α=0.0125. Candidate for a SHADOW-MODE contrarian entry signal on detected forced-flow bars.")
    elif pass_null:
        out.append(f"**PARTIAL** — forced-flow WR {f_wr*100:.1f}% is above 50% null (p={fmt(q161['p_vs_null50'])}) but indistinguishable from extreme-range baseline (p={fmt(q161['p_vs_baseline'])}). The 'forced-flow' signature is not adding edge over range-only filtering; effect is likely just 'large candles mean-revert'.")
    else:
        out.append(f"**NO SIGNAL** — forced-flow WR {f_wr*100:.1f}% does not reject the 50% null at α=0.0125 (p={fmt(q161['p_vs_null50'])}). Pre-registered threshold (>= 55% WR, p<0.0125) not met.")
    out.append("")

    # ------------------------- Q-16.3 -------------------------
    out.append("## Q-16.3 — Session-open patterns")
    out.append("")
    out.append("### Method")
    out.append("")
    out.append("1. For each of 4 sessions (Sydney, Tokyo, London, NewYork), define a 4-hour session window starting at broker-clock session open.")
    out.append("2. Within each window, bucket M15 bars by minute-of-session: first 15m, next 15-60m, mid-session (60-180m), last 30m.")
    out.append("3. Compare mean bar range to the non-session baseline (all M15 bars that fall in none of the 4 sessions).")
    out.append("4. Welch's t-test, two-sided. Pre-registered α = 0.01.")
    out.append("")
    base = q163["baseline"]
    out.append(f"- **Baseline (non-session bars):** n={base['n']}, mean range={fmt(base['mean_range'])}, mean norm-range={fmt(base['mean_norm_range'], 5)}, mean volume={fmt(base['mean_vol'])}")
    out.append("")
    out.append("### Session x bucket range vs baseline")
    out.append("")
    out.append("| session | bucket | n | mean_range | ratio (vs baseline) | welch t | p (two-sided) |")
    out.append("|---|---|---|---|---|---|---|")
    for r in q163["tests"]:
        p_str = "<0.001" if r["p"] < 0.001 else fmt(r["p"])
        out.append(f"| {r['session']} | {r['bucket']} | {r['n']} | {fmt(r['mean_range'])} | {fmt(r['ratio'], 2)}× | {fmt(r['t'])} | {p_str} |")
    out.append("")
    # UTC mapping
    out.append("### Broker-clock -> UTC mapping (approximate, DST-sensitive)")
    out.append("")
    out.append("| Session | Broker-clock open | UTC (pre-DST, Jan-Mar 8) | UTC (post-DST, Mar 29+) |")
    out.append("|---|---|---|---|")
    out.append("| Sydney | 22:00 broker | 20:00 UTC | 19:00 UTC |")
    out.append("| Tokyo | 02:00 broker | 00:00 UTC | 23:00 UTC (prev day) |")
    out.append("| London | 10:00 broker | 08:00 UTC | 07:00 UTC |")
    out.append("| NewYork | 15:30 broker | 13:30 UTC | 12:30 UTC |")
    out.append("")
    out.append("These UTC mappings are approximate — the CSV's broker clock is EET/EEST (UTC+2 winter, UTC+3 summer). The data window spans EU DST (Mar 29 2026) and US DST (Mar 8 2026); session-open windows will drift by 1h across the window. Any conclusion that hinges on a specific hour-bucket within < 30min precision should be re-computed with timezone-aware bars. For the pre-registered H3 threshold (1.5× ratio, p<0.01), DST drift is not material.")
    out.append("")
    out.append("### Q-16.3 verdict")
    out.append("")
    sig = [r for r in q163["tests"] if r["ratio"] == r["ratio"] and r["ratio"] >= 1.5 and r["p"] < 0.01]
    if sig:
        out.append(f"**SIGNAL** — {len(sig)} bucket(s) meet the pre-registered (ratio >= 1.5x, p < 0.01) threshold:")
        out.append("")
        for r in sig:
            p_str = "<0.001" if r["p"] < 0.001 else fmt(r["p"])
            out.append(f"- {r['session']} / {r['bucket']}: {fmt(r['ratio'],2)}× baseline, t={fmt(r['t'])}, p={p_str}")
        out.append("")
        out.append("These buckets are consistent with forced order flow / spread-cost amplification around session opens. Already partially captured by the GTOS kill zone schedule (London 07:00-10:30 UTC, NY 13:00-17:00 UTC for XAUUSD) — cross-check these session-opens are inside kill zones.")
    else:
        out.append("**NO STRONG SIGNAL** — no session-bucket cleared the 1.5× + p<0.01 pre-registered threshold. The GTOS kill-zone schedule may already be capturing the realized-volatility peaks, smoothing their apparent spikiness against a baseline that itself is dominated by London/NY overlap hours.")
    out.append("")

    # ------------------------- Q-16.5 -------------------------
    out.append("## Q-16.5 — OHLCV-VPIN proxy")
    out.append("")
    out.append("### Method")
    out.append("")
    out.append("1. Bulk Volume Classification: for each M15 bar, buy_frac = (close-low)/(high-low); buy_vol = buy_frac x volume; sell_vol = (1-buy_frac) x volume.")
    out.append("2. Rolling 50-bar VPIN: sum |buy_vol - sell_vol| / sum volume.")
    out.append("3. Match each batch trade by trade date -> prior trading day's last M15 bar VPIN. Prior-day is used (not same-day) to avoid trivial lookahead.")
    out.append("4. Tercile split on VPIN. Compute WR per tercile.")
    out.append("")
    out.append(f"- Matched trades: **{q165['matched']}** / batch {trade_meta['n']}")
    out.append(f"- Skipped (no prior M15 bar in window): {q165['skipped_no_bar']}")
    out.append(f"- Skipped (VPIN not yet converged at bar): {q165['skipped_no_vpin']}")
    if q165.get("underpowered"):
        out.append("")
        out.append("**UNDERPOWERED** — fewer than 9 matched trades for tercile analysis.")
    else:
        out.append(f"- VPIN range: {fmt(q165['vpin_min'], 4)} → {fmt(q165['vpin_max'], 4)} (median {fmt(q165['vpin_median'], 4)})")
        out.append(f"- Tercile thresholds: low<={fmt(q165['q1_threshold'], 4)}, high>={fmt(q165['q2_threshold'], 4)}")
        out.append("")
        out.append("| tercile | n (W+L+BE) | wins | losses | WR | exp_R |")
        out.append("|---|---|---|---|---|---|")
        for tname in ["low", "mid", "high"]:
            t = q165["terciles"][tname]
            out.append(f"| {tname} | {t['n_all']} | {t['wins']} | {t['losses']} | {fmt(t['wr'])} | {fmt(t['exp_r'])} |")
        out.append("")
        out.append(f"- **High vs low tercile:** z = {fmt(q165['high_vs_low_z'])}, two-sided p = {fmt(q165['high_vs_low_p'])}")
        out.append(f"- **WR gap (high - low):** {fmt(q165['gap_pp'], 1)} pp")
        out.append("")
    out.append("### Q-16.5 verdict")
    out.append("")
    if q165.get("underpowered") or q165["matched"] < 20:
        out.append(f"**UNDERPOWERED** — only {q165['matched']} trades matched inside the local 2026 data window, vs batch n={trade_meta['n']}. 2024-2025 trades cannot be matched (no local M15 CSV pre-2026). Re-run once the M15 gap is closed.")
    else:
        gap = q165.get("gap_pp", float("nan"))
        p = q165.get("high_vs_low_p", float("nan"))
        if p == p and p < 0.0125 and abs(gap) >= 5.0:
            direction = "higher" if gap > 0 else "lower"
            out.append(f"**SIGNAL** — high-VPIN tercile WR is {abs(gap):.1f}pp {direction} than low-VPIN (p={fmt(p)}). Meets pre-registered threshold (|gap| >= 5pp, p<0.0125). Candidate for shadow-logging VPIN at trade evaluation time. NOTE: sample-overlap caveat — the same upward-WR trend documented in Q-crowding_retail.md (Kendall tau +0.754) may confound this result if VPIN is correlated with trade date.")
        else:
            direction_note = ""
            if gap == gap and gap < 0:
                direction_note = f" Direction note: the sign is inverted from the naive 'informed flow helps' prior — low-VPIN (balanced flow) tercile WR is higher than high-VPIN (directionally imbalanced flow). If real, this would be consistent with 'strong directional flow before entry is a warning, not a signal' — but at p={fmt(p)} this is underpowered and not actionable. Revisit when the pre-2026 M15 data gap is closed."
            out.append(f"**NO SIGNAL** — WR gap (high-low) is {fmt(gap, 1)}pp with p={fmt(p)}. Pre-registered threshold (|gap| >= 5pp, p<0.0125) not met. OHLCV-derived VPIN does not discriminate entry quality on this sample.{direction_note}")
    out.append("")

    # ------------------------- Q-16.6 -------------------------
    out.append("## Q-16.6 — Game-theoretic response to SMC crowding")
    out.append("")
    out.append("Qualitative, no statistical test. Operational question: if OB-retest is a crowded trade, which defensive play should the system prefer?")
    out.append("")
    out.append("### Candidate responses, mapped against current system")
    out.append("")
    out.append("| Option | Defensive rationale | Current system | Evidence that would update |")
    out.append("|---|---|---|---|")
    for p in q166["plays"]:
        out.append(f"| {p['option']} | {p['defensive_rationale']} | {p['current_system']} | {p['update_evidence']} |")
    out.append("")
    out.append("### Q-16.6 verdict (qualitative)")
    out.append("")
    out.append("The current system is **primarily on plays (b) and (d)**: partial_close (shadow), BE shadow logger, and a 5-instrument portfolio explicitly diversifying away from pure XAUUSD-SMC exposure. Play (a) is partial via m5_refinement; play (c) is not implemented. Q-16.1 (this document) is the natural data-collection hook for play (c).")
    out.append("")
    out.append("If Q-16.1 surfaces a SIGNAL verdict, promote forced-flow contrarian as a candidate SHADOW-logged signal (observation-only), consistent with the WF-2 shadow-gate promotion protocol. Do not deploy as a live rule without 30+ shadow-observed outcomes and CEO approval.")
    out.append("")

    # ------------------------- Cross-references + caveats -------------------------
    out.append("## Caveats and cross-references")
    out.append("")
    out.append("1. **Tick-volume proxy bias.** CFD tick_volume is not real trade volume. Q-16.1 and Q-16.5 interpretations both degrade in overnight / illiquid / news-spike regimes. Independent L1-quote or tape data would strengthen both.")
    out.append("2. **Data window 2026-01-02 to 2026-04-10.** All historical-bar analysis is inside this quarter. No seasonal / multi-regime validation is possible locally.")
    out.append("3. **Sample overlap with Q-crowding_retail (Q-8.3/Q-16.4).** Q-16.5 uses the same batch trades. The +0.754 Kendall tau of rolling-window WR (documented there) is a time-trend confound for any VPIN-vs-WR relationship unless VPIN is de-trended.")
    out.append("4. **Broker-clock / DST.** All session-segmentation in Q-16.3 is in broker-clock. The Mar 8 (US) and Mar 29 (EU) DST changes drift each session open by 1h UTC — effect is small for 4h session buckets but real. A UTC-aware re-run is a future task.")
    out.append("5. **Multiple testing.** Four primary tests (Q-16.1 vs null, Q-16.1 vs baseline, Q-16.3 any session bucket, Q-16.5 high-vs-low). Bonferroni α = 0.0125 was pre-registered and applied.")
    out.append("6. **Q-16.6 is qualitative.** The 'evidence that would update' fields specify what would trigger re-classification; no statistical claims are made on the mapping itself.")
    out.append("")
    out.append("## Verdicts (summary)")
    out.append("")
    # quick summary
    q161_pool_wr = q161["forced_pooled_wr"]
    q161_pool_n = q161["forced_pooled_n"]
    if q161_pool_n < 20:
        v1 = "UNDERPOWERED"
    elif (q161["p_vs_null50"] < 0.0125) and (q161_pool_wr >= 0.55) and (q161["p_vs_baseline"] < 0.0125):
        v1 = f"SIGNAL (forced-flow reversion WR {q161_pool_wr*100:.1f}%, p<0.0125 vs null AND baseline)"
    elif (q161["p_vs_null50"] < 0.0125) and (q161_pool_wr >= 0.55):
        v1 = f"PARTIAL (WR {q161_pool_wr*100:.1f}% beats null but not baseline)"
    else:
        v1 = f"NO SIGNAL (WR {q161_pool_wr*100:.1f}%, p={fmt(q161['p_vs_null50'])})"
    sig_q163 = [r for r in q163["tests"] if r["ratio"] == r["ratio"] and r["ratio"] >= 1.5 and r["p"] < 0.01]
    if sig_q163:
        v3 = f"SIGNAL ({len(sig_q163)} bucket(s) >= 1.5× baseline at p<0.01)"
    else:
        v3 = "NO STRONG SIGNAL (no bucket cleared 1.5× + p<0.01)"
    if q165.get("underpowered") or q165["matched"] < 20:
        v5 = f"UNDERPOWERED ({q165['matched']} matched of {trade_meta['n']})"
    else:
        gap = q165.get("gap_pp", float("nan"))
        p = q165.get("high_vs_low_p", float("nan"))
        if p == p and p < 0.0125 and abs(gap) >= 5.0:
            v5 = f"SIGNAL (|gap|={abs(gap):.1f}pp, p={fmt(p)})"
        else:
            v5 = f"NO SIGNAL (|gap|={fmt(abs(gap), 1)}pp, p={fmt(p)})"
    out.append(f"- **Q-16.1 (forced-flow):** {v1}")
    out.append(f"- **Q-16.3 (session-open patterns):** {v3}")
    out.append(f"- **Q-16.5 (VPIN):** {v5}")
    out.append("- **Q-16.6 (crowding defense):** System is already on plays (b) and (d) (partial-close shadow + 5-instrument portfolio). (a) is partial, (c) is not implemented. Q-16.1 is the data hook for (c).")
    out.append("")
    out.append("## Next steps")
    out.append("")
    out.append("1. If Q-16.1 is SIGNAL: stand up a SHADOW-MODE logger that records forced-flow detections and 6-candle forward outcomes on live bars. 30+ observations with p<0.05 -> CEO review for WF-2 promotion.")
    out.append("2. If Q-16.3 is SIGNAL: audit that all hot buckets lie inside active kill zones. Any hot bucket *outside* kill zones is either (a) a kill-zone calibration miss or (b) a candidate micro-session to add.")
    out.append("3. If Q-16.5 is underpowered, close the pre-2026 M15 data gap (as with Q-crowding_retail) then re-run.")
    out.append("4. Q-16.6: when the partial-close shadow logger crosses 30 BE-triggered trades, re-run the evidence check in the play-(b) row and decide promote/kill per protocol.")
    out.append("5. **Do NOT deploy any of the above as live gates from this document.** These are adversarial-lens diagnostics. Live changes require the standard shadow-then-promote workflow and CEO approval.")
    out.append("")
    out.append("*End of report.*")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #

def main():
    m15 = load_bars(M15_PATH)
    h1 = load_bars(H1_PATH)
    trades = json.load(open(TRADES_PATH))
    trades_2026 = [t for t in trades if t.get("date", "").startswith("2026")]
    trade_meta = {"n": len(trades), "n_2026": len(trades_2026)}
    bar_meta = {
        "n_m15": len(m15),
        "n_h1": len(h1),
        "m15_start": m15[0].time.strftime("%Y-%m-%d %H:%M"),
        "m15_end":   m15[-1].time.strftime("%Y-%m-%d %H:%M"),
    }

    print(f"[q_16] loaded {len(m15)} M15, {len(h1)} H1, {len(trades)} trades (2026: {len(trades_2026)})")

    print("[q_16.1] scanning for forced-flow candles...")
    q161 = q16_1_forced_flow(m15)
    print(f"        forced pooled n={q161['forced_pooled_n']} wr={q161['forced_pooled_wr']}")

    print("[q_16.3] session-open pattern scan...")
    q163 = q16_3_session_patterns(m15)

    print("[q_16.5] VPIN classification + tercile split...")
    q165 = q16_5_vpin(m15, trades)
    print(f"        matched trades: {q165['matched']}")

    print("[q_16.6] rendering game-theoretic response map...")
    q166 = q16_6_gametheoretic_map()

    md = render_markdown(q161, q163, q165, q166, trade_meta, bar_meta)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[q_16] wrote {OUT_MD}")


if __name__ == "__main__":
    main()
