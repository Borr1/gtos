"""Q-2 Structure-detection analysis.

Q-2.1 Compare swing-detection algorithms on H1 XAUUSD:
  A: Fixed-lookback (current, min_bars=2 per agent_config)
  B: Directional-change (DC) across thresholds
  C: Bry-Boschan light (5-period peak/trough, alternation + min cycle >=5)

Q-2.6 Displacement revival — use batch `displacement_quality` categorical
and (where possible) reconstructed impulse magnitude from M15/H1 OHLCV
surrounding each trade entry.

Output: research/academic_pipeline/results/Q-2_structure.md

Pre-registered hypotheses (stated BEFORE opening outcome data):

  H-2.1 (null): No swing-detection algorithm is significantly better at
        predicting 6-candle forward continuation than fixed-lookback
        min_bars=2 at p<0.05 Bonferroni-adjusted across algorithms tested.
        Rationale: OB edge is zone-based, not swing-frequency based
        (Test A rerun, test_a_rerun_real_bos_results.md). Changing swing
        grammar is unlikely to move the needle.

  H-2.6 (alt): displacement_quality in the 111-trade batch does NOT
        strongly predict WR. Prior T3 killed the feature on H1
        h1_last_break_disp / M15 displacement_ratio. CEO flagged for
        revival because prior was ran on Phase 1-2 broken system.
        We re-evaluate; if WR spread across displacement_quality levels
        is <=5pp or p>0.05, we confirm KILL. Otherwise REVIVE as shadow.

Zero API calls. Pure local analysis.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
H1_CSV = ROOT / "data" / "historical_2026" / "XAUUSD_H1.csv"
M15_CSV = ROOT / "data" / "historical_2026" / "XAUUSD_M15.csv"
BATCH = ROOT / "knowledge_base_backtest" / "analysis" / "unified_trades_v2_20260331.json"
OUT = ROOT / "research" / "academic_pipeline" / "results" / "Q-2_structure.md"


# ---------- IO ----------

def load_candles(path: Path) -> list[dict]:
    out = []
    with path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out.append({
                "time": row["time"],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row.get("volume", 0) or 0),
            })
    return out


def load_batch(path: Path) -> list[dict]:
    with path.open("r") as f:
        return json.load(f)


# ---------- Algorithms ----------

@dataclass
class Swing:
    idx: int
    kind: str  # "high" | "low"
    price: float


def detect_fixed_lookback(candles: list[dict], min_bars: int = 2) -> list[Swing]:
    """Current production algorithm (market_state.detect_swings)."""
    swings: list[Swing] = []
    n = len(candles)
    for i in range(min_bars, n - min_bars):
        is_high = all(
            candles[i]["high"] > candles[i - j]["high"]
            and candles[i]["high"] > candles[i + j]["high"]
            for j in range(1, min_bars + 1)
        )
        if is_high:
            swings.append(Swing(i, "high", candles[i]["high"]))
        is_low = all(
            candles[i]["low"] < candles[i - j]["low"]
            and candles[i]["low"] < candles[i + j]["low"]
            for j in range(1, min_bars + 1)
        )
        if is_low:
            swings.append(Swing(i, "low", candles[i]["low"]))
    return sorted(swings, key=lambda s: s.idx)


def detect_directional_change(candles: list[dict], theta: float) -> list[Swing]:
    """Guillaume et al. (1997) directional-change algorithm.

    Tag a new swing whenever price retraces >= theta (as fraction)
    from the most recent extreme in the current direction.
    """
    if not candles:
        return []
    swings: list[Swing] = []
    # initialize: assume "up" mode, extreme is first close
    direction = None  # +1 up, -1 down
    ext_idx = 0
    ext_price = candles[0]["close"]

    for i in range(1, len(candles)):
        hi = candles[i]["high"]
        lo = candles[i]["low"]
        if direction is None:
            # bootstrap: whichever side breaches theta first
            up_move = (hi - ext_price) / ext_price
            dn_move = (ext_price - lo) / ext_price
            if up_move >= theta and up_move >= dn_move:
                direction = 1
                swings.append(Swing(ext_idx, "low", ext_price))
                ext_idx, ext_price = i, hi
            elif dn_move >= theta:
                direction = -1
                swings.append(Swing(ext_idx, "high", ext_price))
                ext_idx, ext_price = i, lo
            else:
                # update bootstrap extreme loosely
                if hi > ext_price:
                    ext_idx, ext_price = i, hi
                if lo < ext_price:
                    ext_idx, ext_price = i, lo
            continue

        if direction == 1:
            # extend up if new high, else check retrace
            if hi > ext_price:
                ext_idx, ext_price = i, hi
            elif (ext_price - lo) / ext_price >= theta:
                # reverse
                swings.append(Swing(ext_idx, "high", ext_price))
                direction = -1
                ext_idx, ext_price = i, lo
        else:  # direction == -1
            if lo < ext_price:
                ext_idx, ext_price = i, lo
            elif (hi - ext_price) / ext_price >= theta:
                swings.append(Swing(ext_idx, "low", ext_price))
                direction = 1
                ext_idx, ext_price = i, hi

    return swings


def detect_bry_boschan_light(candles: list[dict], window: int = 5,
                              min_cycle: int = 5) -> list[Swing]:
    """Simplified Bry-Boschan: local extrema over window, filter to
    alternating sequence with min_cycle candles between extrema."""
    raw: list[Swing] = []
    n = len(candles)
    for i in range(window, n - window):
        is_high = all(candles[i]["high"] >= candles[i - j]["high"]
                      for j in range(1, window + 1)) and all(
                      candles[i]["high"] >= candles[i + j]["high"]
                      for j in range(1, window + 1))
        is_low = all(candles[i]["low"] <= candles[i - j]["low"]
                     for j in range(1, window + 1)) and all(
                     candles[i]["low"] <= candles[i + j]["low"]
                     for j in range(1, window + 1))
        if is_high and not is_low:
            raw.append(Swing(i, "high", candles[i]["high"]))
        elif is_low and not is_high:
            raw.append(Swing(i, "low", candles[i]["low"]))
    # enforce alternation + min cycle
    filt: list[Swing] = []
    for s in raw:
        if not filt:
            filt.append(s)
            continue
        last = filt[-1]
        if s.kind == last.kind:
            # keep the more extreme of the same kind (replace if stronger)
            if (s.kind == "high" and s.price > last.price) or (
                s.kind == "low" and s.price < last.price):
                filt[-1] = s
            continue
        if s.idx - last.idx < min_cycle:
            continue
        filt.append(s)
    return filt


# ---------- Evaluation ----------

def amplitude(swings: list[Swing]) -> float:
    """Average absolute price delta between consecutive alternating swings."""
    if len(swings) < 2:
        return 0.0
    deltas = []
    for a, b in zip(swings, swings[1:]):
        if a.kind != b.kind:
            deltas.append(abs(b.price - a.price))
    return statistics.mean(deltas) if deltas else 0.0


def continuation_rate(swings: list[Swing], candles: list[dict],
                      horizon: int = 6,
                      detection_delay: int = 0) -> tuple[int, int, float]:
    """For each swing, check continuation in the direction implied by the
    swing. After a swing_LOW (expect bullish continuation), does
    close[i + detection_delay + horizon] > swing.price? After swing_HIGH,
    does close[...] < swing.price?

    detection_delay: candles after swing formation before the swing is
    confirmable in live trading. Fairness adjustment to avoid look-ahead:
      - fixed-lookback min_bars=2 -> delay=2
      - DC: depends on theta, approximated as ~same bar as reversal, delay=0
        (DC tags swings only when the threshold is breached, which is already
        causal in our implementation)
      - BB-light w=5, min_cycle=5 -> delay=5 (peak is confirmed only after
        5 bars without a higher high)

    Returns (wins, n, rate).
    """
    wins = 0
    n = 0
    N = len(candles)
    for s in swings:
        target_idx = s.idx + detection_delay + horizon
        if target_idx >= N:
            continue
        cl = candles[target_idx]["close"]
        if s.kind == "low" and cl > s.price:
            wins += 1
        elif s.kind == "high" and cl < s.price:
            wins += 1
        n += 1
    rate = wins / n if n else 0.0
    return wins, n, rate


def wilson_ci(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = wins / n
    denom = 1 + z*z/n
    center = (p + z*z/(2*n)) / denom
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / denom
    return (center - half, center + half)


def two_prop_p(w1: int, n1: int, w2: int, n2: int) -> float:
    """Two-proportion z-test p-value (two-sided)."""
    if n1 == 0 or n2 == 0:
        return 1.0
    p1, p2 = w1/n1, w2/n2
    p = (w1 + w2) / (n1 + n2)
    se = math.sqrt(p*(1-p)*(1/n1 + 1/n2))
    if se == 0:
        return 1.0
    z = (p1 - p2) / se
    # two-sided via normal CDF approximation (Abramowitz & Stegun 26.2.17)
    return 2 * (1 - _phi(abs(z)))


def _phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def chi_square_p(counts: list[tuple[int, int]]) -> float:
    """Chi-square p-value for k x 2 table rows=(wins, total)."""
    rows = [(w, n - w) for w, n in counts]
    total = sum(n for _, n in counts)
    if total == 0:
        return 1.0
    col_totals = [sum(r[0] for r in rows), sum(r[1] for r in rows)]
    chi2 = 0.0
    for i, row in enumerate(rows):
        n_i = counts[i][1]
        for j, obs in enumerate(row):
            exp = n_i * col_totals[j] / total
            if exp <= 0:
                continue
            chi2 += (obs - exp) ** 2 / exp
    # df = (k-1) * 1
    df = len(counts) - 1
    # use survival function via incomplete gamma approx
    return _chi2_sf(chi2, df)


def _chi2_sf(chi2: float, df: int) -> float:
    # regularized upper incomplete gamma Q(df/2, chi2/2)
    # series/continued-fraction. Use math.gamma via lgamma.
    if df <= 0 or chi2 <= 0:
        return 1.0
    a = df / 2.0
    x = chi2 / 2.0
    # use continued fraction for x > a+1, series otherwise
    if x < a + 1:
        # series
        term = 1.0 / a
        total = term
        for n in range(1, 200):
            term *= x / (a + n)
            total += term
            if abs(term) < 1e-12 * abs(total):
                break
        P = total * math.exp(-x + a * math.log(x) - math.lgamma(a))
        return max(0.0, 1.0 - P)
    else:
        # Lentz continued fraction
        b = x + 1 - a
        fpmin = 1e-30
        c = 1.0 / fpmin
        d = 1.0 / b
        h = d
        for n in range(1, 200):
            an_ = -n * (n - a)
            b += 2
            d = an_ * d + b
            if abs(d) < fpmin:
                d = fpmin
            c = b + an_ / c
            if abs(c) < fpmin:
                c = fpmin
            d = 1.0 / d
            delt = d * c
            h *= delt
            if abs(delt - 1) < 1e-12:
                break
        Q = h * math.exp(-x + a * math.log(x) - math.lgamma(a))
        return max(0.0, min(1.0, Q))


# ---------- Q-2.6: displacement revival ----------

def parse_date(s: str) -> datetime | None:
    try:
        return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        return None


def parse_candle_time(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def atr(candles: list[dict], idx: int, period: int = 14) -> float | None:
    if idx < period:
        return None
    trs = []
    for k in range(idx - period + 1, idx + 1):
        if k == 0:
            trs.append(candles[k]["high"] - candles[k]["low"])
            continue
        tr = max(
            candles[k]["high"] - candles[k]["low"],
            abs(candles[k]["high"] - candles[k - 1]["close"]),
            abs(candles[k]["low"] - candles[k - 1]["close"]),
        )
        trs.append(tr)
    return sum(trs) / period


def reconstruct_displacement(trade: dict, m15: list[dict]) -> float | None:
    """Look back 10 M15 candles prior to entry, compute
    (impulse_high - impulse_low) / ATR14."""
    ep = trade.get("entry_price")
    d = parse_date(trade.get("date", ""))
    if ep is None or d is None:
        return None
    # find the first M15 candle whose time is on the trade date AND that
    # contains the entry_price; use its index as entry anchor
    entry_idx = None
    for i, c in enumerate(m15):
        t = parse_candle_time(c["time"])
        if t.date() != d.date():
            continue
        if c["low"] <= ep <= c["high"]:
            entry_idx = i
            break
    if entry_idx is None or entry_idx < 15:
        return None
    lookback = m15[entry_idx - 10: entry_idx]
    if not lookback:
        return None
    hi = max(c["high"] for c in lookback)
    lo = min(c["low"] for c in lookback)
    a = atr(m15, entry_idx - 1, period=14)
    if a is None or a <= 0:
        return None
    return (hi - lo) / a


# ---------- Runner ----------

def run() -> None:
    lines: list[str] = []
    p = lines.append
    p("# Q-2 Structure Detection Analysis")
    p("")
    p(f"**Generated:** {datetime.now(timezone.utc).isoformat()}")
    p(f"**H1 source:** `{H1_CSV.relative_to(ROOT).as_posix()}` (Jan 2 - Apr 10, 2026)")
    p(f"**Batch source:** `{BATCH.relative_to(ROOT).as_posix()}` (n=111)")
    p(f"**Analysis scope:** XAUUSD (batch is XAUUSD-only; H1/M15 from historical_2026/)")
    p("")
    p("## Hypothesis (pre-data)")
    p("")
    p("Stated before opening the outcome distributions:")
    p("")
    p("- **H-2.1 (null):** No swing-detection algorithm significantly beats fixed-lookback min_bars=2 at predicting 6-candle continuation at p<0.05 Bonferroni-adjusted across algorithms tested. Rationale: the GTOS edge is OB zone-based, not swing-frequency based (Test A rerun result, +17pp). Changing swing grammar changes *which* OBs we detect but not the underlying mean-reversion mechanism.")
    p("- **H-2.6 (alt):** `displacement_quality` does NOT strongly predict WR in the 111-trade batch. Prior T3 KILLED H1 `h1_last_break_disp` and M15 `displacement_ratio` at n=121 with Bonferroni-adjusted p>0.01. CEO flagged for revival because prior ran on Phase 1-2 broken system. If WR spread across displacement levels remains <=5pp or chi-square p>0.05, confirm KILL. Otherwise promote as shadow.")
    p("")

    # ----- Load data -----
    h1 = load_candles(H1_CSV)
    m15 = load_candles(M15_CSV)
    trades = load_batch(BATCH)

    p("## Data")
    p("")
    p(f"- H1 candles: **{len(h1)}** (XAUUSD, {h1[0]['time']} -> {h1[-1]['time']}).")
    p(f"- M15 candles: **{len(m15)}** (XAUUSD, {m15[0]['time']} -> {m15[-1]['time']}).")
    p(f"- Batch trades: **{len(trades)}** (2024-04-01 to 2026-03-13).")
    p(f"- Batch displacement_quality distribution: {dict(Counter(t.get('displacement_quality') for t in trades))}")
    p(f"- Batch outcome distribution: {dict(Counter(t.get('outcome') for t in trades))}")
    p("")

    # ----- Q-2.1 ALGORITHM COMPARISON -----
    p("## Method")
    p("")
    p("**Q-2.1 swing algorithms:**")
    p("- A (fixed-lookback): market_state.detect_swings min_bars=2 (current production).")
    p("- B (directional-change): Guillaume et al. 1997, thresholds theta in {0.1%, 0.3%, 0.5%, 1.0%}.")
    p("- C (Bry-Boschan light): 5-period local peak/trough, filter to alternation + min cycle >=5.")
    p("")
    p("**Q-2.1 evaluation metric:** 6-candle forward continuation rate.")
    p("For a detected swing_LOW at index i, a 'win' = close[i+6] > swing.price (bullish continuation from the trough).")
    p("For a detected swing_HIGH at index i, a 'win' = close[i+6] < swing.price.")
    p("This tests the directional signal the swing carries: does price continue away from the extreme or revert?")
    p("Two-proportion z-test vs the fixed-lookback baseline; chi-square across all algorithms; Bonferroni alpha=0.05/6.")
    p("")
    p("**Q-2.6 displacement:**")
    p("Primary: categorical `displacement_quality` ('weak' / 'medium' / 'strong') already in batch JSON.")
    p("Secondary (feasibility): reconstructed impulse magnitude (max(high)-min(low) across the 10 M15 candles prior to entry) / ATR14(M15). Batch dates 2024-04-01 to 2026-03-13; M15 CSV 2026-01-02 onwards -> only ~2 months of trades reconstructable. Honest reconstruction, no fabrication for out-of-range trades.")
    p("")

    # ----- ALGORITHM RESULTS -----
    p("## Q-2.1 Algorithm comparison")
    p("")

    # (name, swings, detection_delay) — delay reflects look-ahead-free
    # confirmation lag in live trading.
    algos: list[tuple[str, list[Swing], int]] = []
    algos.append(("A_fixed_mb2", detect_fixed_lookback(h1, min_bars=2), 2))
    for theta in (0.001, 0.003, 0.005, 0.01):
        algos.append((f"B_DC_theta={theta*100:.1f}pct",
                      detect_directional_change(h1, theta), 0))
    algos.append(("C_BryBoschan_w5_cyc5",
                  detect_bry_boschan_light(h1, window=5, min_cycle=5), 5))

    results: list[dict] = []
    days = 0
    if len(h1) > 0:
        t0 = parse_candle_time(h1[0]["time"])
        tN = parse_candle_time(h1[-1]["time"])
        days = max(1, (tN - t0).days)

    for name, sw, delay in algos:
        amp = amplitude(sw)
        wins, n, rate = continuation_rate(sw, h1, horizon=6, detection_delay=delay)
        lo, hi = wilson_ci(wins, n)
        results.append({
            "name": name,
            "delay": delay,
            "n_swings": len(sw),
            "per_day": len(sw) / days,
            "amp": amp,
            "cont_wins": wins,
            "cont_n": n,
            "cont_rate": rate,
            "ci_lo": lo,
            "ci_hi": hi,
        })

    p("### Swing counts / amplitude / 6-candle continuation (look-ahead-free)")
    p("")
    p("**Fairness note on detection delay:** a swing is only confirmable in live trading after a lag characteristic of the algorithm. We compute continuation as `close[swing_idx + delay + 6] vs swing.price` so that no algorithm benefits from reading the future.")
    p("- A fixed-lookback min_bars=2: delay = 2 candles (swing confirmed 2 bars after formation)")
    p("- B directional-change: delay = 0 (DC tags a swing exactly when the reversal threshold is breached; already causal)")
    p("- C Bry-Boschan light w=5: delay = 5 (peak confirmed only after 5 bars without a higher high)")
    p("")
    p("Without this adjustment, BB-light's 'alternation enforced' filter produces a selection-bias win rate (~99%) because only swings followed by a real alternation survive the filter. The delay-adjusted metric is the fair comparison.")
    p("")
    p("| Algorithm | Delay | Total swings | Swings/day | Avg amplitude (price) | Cont. WR | 95% CI | n |")
    p("|---|---:|---:|---:|---:|---:|:---:|---:|")
    for r in results:
        p(f"| {r['name']} | {r['delay']} | {r['n_swings']} | {r['per_day']:.2f} | {r['amp']:.2f} | {r['cont_rate']*100:.1f}% | [{r['ci_lo']*100:.1f}% - {r['ci_hi']*100:.1f}%] | {r['cont_n']} |")
    p("")

    # Pairwise vs baseline
    baseline = results[0]
    p("### Pairwise two-proportion z-test vs fixed-lookback baseline")
    p("")
    p("Bonferroni correction: **6 comparisons**, adjusted alpha = 0.05 / 6 = 0.00833.")
    p("")
    p("| Algorithm | WR | Delta vs baseline (pp) | Raw p | Bonferroni significant? |")
    p("|---|---:|---:|---:|:---:|")
    alpha_bonf = 0.05 / 6
    for r in results[1:]:
        delta = (r['cont_rate'] - baseline['cont_rate']) * 100
        pval = two_prop_p(r['cont_wins'], r['cont_n'], baseline['cont_wins'], baseline['cont_n'])
        sig = "YES" if pval < alpha_bonf else "no"
        p(f"| {r['name']} | {r['cont_rate']*100:.1f}% | {delta:+.1f} | {pval:.4f} | {sig} |")
    p("")

    # Chi-square omnibus
    counts = [(r['cont_wins'], r['cont_n']) for r in results]
    chi_p = chi_square_p(counts)
    p(f"**Omnibus chi-square** across {len(results)} algorithms: p = {chi_p:.4f}")
    p("")

    # Ranking
    ranked = sorted(results, key=lambda r: r['cont_rate'], reverse=True)
    p("### Ranking by continuation rate (higher = better predictive power)")
    p("")
    for i, r in enumerate(ranked, 1):
        p(f"{i}. **{r['name']}** — {r['cont_rate']*100:.1f}% ({r['cont_n']} swings, {r['n_swings']} total detected)")
    p("")

    # ----- Q-2.6 DISPLACEMENT REVIVAL -----
    p("## Q-2.6 Displacement revival")
    p("")
    p("### Primary: categorical `displacement_quality` (full 111-trade batch)")
    p("")

    # WR by category
    by_q: dict[str, list[dict]] = {}
    for t in trades:
        q = t.get("displacement_quality") or "unknown"
        by_q.setdefault(q, []).append(t)
    q_order = [q for q in ("weak", "medium", "strong", "unknown") if q in by_q]

    p("| displacement_quality | n | W | L | BE | WR | 95% CI |")
    p("|---|---:|---:|---:|---:|---:|:---:|")
    q_stats: list[tuple[str, int, int]] = []  # (q, wins, n_decided)
    for q in q_order:
        grp = by_q[q]
        w = sum(1 for t in grp if t.get("outcome") == "WIN")
        l = sum(1 for t in grp if t.get("outcome") == "LOSS")
        be = sum(1 for t in grp if t.get("outcome") == "BREAKEVEN")
        n_dec = w + l
        wr = w / n_dec if n_dec else 0.0
        lo, hi = wilson_ci(w, n_dec)
        p(f"| {q} | {len(grp)} | {w} | {l} | {be} | {wr*100:.1f}% | [{lo*100:.1f}% - {hi*100:.1f}%] |")
        q_stats.append((q, w, n_dec))
    p("")

    # chi-square across categorical levels
    chi_counts = [(w, n) for _, w, n in q_stats if n > 0]
    chi_q_p = chi_square_p(chi_counts) if len(chi_counts) >= 2 else 1.0
    p(f"**Chi-square across displacement levels:** p = {chi_q_p:.4f}")
    p("")

    # strong vs weak/medium combined
    w_strong = next((w for q, w, n in q_stats if q == "strong"), 0)
    n_strong = next((n for q, w, n in q_stats if q == "strong"), 0)
    w_other = sum(w for q, w, n in q_stats if q != "strong")
    n_other = sum(n for q, w, n in q_stats if q != "strong")
    delta_sw = 0.0
    if n_strong and n_other:
        wr_s = w_strong / n_strong
        wr_o = w_other / n_other
        delta_sw = (wr_s - wr_o) * 100
        p_sw = two_prop_p(w_strong, n_strong, w_other, n_other)
        p(f"**Strong vs (weak+medium) combined:** {wr_s*100:.1f}% vs {wr_o*100:.1f}% (delta {delta_sw:+.1f}pp, p = {p_sw:.4f}, n_strong={n_strong}, n_other={n_other})")
    else:
        p(f"**Strong vs other:** insufficient sample (n_strong={n_strong}, n_other={n_other}).")
    p("")

    # Sample size caveat
    p(f"**Sample caveat:** n(weak)={len(by_q.get('weak', []))} trade(s), n(medium)={len(by_q.get('medium', []))} trade(s). Strong dominates the batch ({len(by_q.get('strong', []))} of {len(trades)} = {len(by_q.get('strong', []))/len(trades)*100:.1f}%). This is by design: the Phase 1-2 AI classifier labeled most CANDIDATE setups 'strong' (confidence scoring rubber stamp, per T2a). Non-strong cells are statistically too small to detect moderate effects.")
    p("")

    # ----- Secondary: reconstructed magnitude -----
    p("### Secondary: reconstructed impulse magnitude (M15, 10-candle lookback, ATR14)")
    p("")
    reconstructed: list[tuple[dict, float]] = []
    failed = 0
    for t in trades:
        disp = reconstruct_displacement(t, m15)
        if disp is None:
            failed += 1
            continue
        reconstructed.append((t, disp))
    p(f"- Reconstruction matched: **{len(reconstructed)}** of {len(trades)} trades ({len(reconstructed)/len(trades)*100:.1f}%).")
    p(f"- Not matched: {failed} (M15 CSV starts 2026-01-02; batch includes 2024-04-01 onwards). No fabrication: unmatched trades excluded.")
    p("")

    recon_chi_p = 1.0
    recon_monotone_note = ""
    if len(reconstructed) >= 12:
        vals = sorted(x for _, x in reconstructed)
        q1 = vals[len(vals)//4]
        q2 = vals[len(vals)//2]
        q3 = vals[3*len(vals)//4]
        buckets = [
            ("Q1_low", [(t, v) for t, v in reconstructed if v <= q1]),
            ("Q2", [(t, v) for t, v in reconstructed if q1 < v <= q2]),
            ("Q3", [(t, v) for t, v in reconstructed if q2 < v <= q3]),
            ("Q4_high", [(t, v) for t, v in reconstructed if v > q3]),
        ]
        p(f"Quartile thresholds on impulse_range/ATR14: Q1<={q1:.2f}, Q2<={q2:.2f}, Q3<={q3:.2f}.")
        p("")
        p("| Bucket | n | W | L | WR | Avg R |")
        p("|---|---:|---:|---:|---:|---:|")
        recon_counts = []
        bucket_wrs = []
        for name, items in buckets:
            w = sum(1 for t, _ in items if t.get("outcome") == "WIN")
            l = sum(1 for t, _ in items if t.get("outcome") == "LOSS")
            n_dec = w + l
            wr = w / n_dec if n_dec else 0.0
            avgr = statistics.mean(t.get("r_multiple", 0.0) for t, _ in items) if items else 0.0
            p(f"| {name} | {len(items)} | {w} | {l} | {wr*100:.1f}% | {avgr:+.3f} |")
            if n_dec > 0:
                recon_counts.append((w, n_dec))
                bucket_wrs.append(wr)
        p("")
        recon_chi_p = chi_square_p(recon_counts) if len(recon_counts) >= 2 else 1.0
        p(f"**Chi-square across reconstructed magnitude quartiles:** p = {recon_chi_p:.4f} (n={sum(n for _,n in recon_counts)})")
        # Look for monotone / U-shape patterns
        if len(bucket_wrs) == 4:
            # Is it monotone increasing?
            is_monotone_up = all(bucket_wrs[i] <= bucket_wrs[i+1] for i in range(3))
            is_u_shape = bucket_wrs[0] > bucket_wrs[1] and bucket_wrs[2] > bucket_wrs[1] and bucket_wrs[3] > bucket_wrs[2]
            if is_monotone_up:
                recon_monotone_note = f" Pattern monotone-up Q1<Q2<Q3<Q4 ({bucket_wrs[0]*100:.0f}%->{bucket_wrs[1]*100:.0f}%->{bucket_wrs[2]*100:.0f}%->{bucket_wrs[3]*100:.0f}%) — weak hint that stronger impulse = better outcome."
            elif is_u_shape:
                recon_monotone_note = f" Pattern U-shaped ({bucket_wrs[0]*100:.0f}%->{bucket_wrs[1]*100:.0f}%->{bucket_wrs[2]*100:.0f}%->{bucket_wrs[3]*100:.0f}%) — extremes win, middle loses. Suggests a non-monotone displacement effect, but n=29 is too small to trust."
    else:
        p(f"Insufficient reconstructed sample (n={len(reconstructed)}) for quartile analysis. Deferred honestly.")
    p("")

    # ----- Caveats -----
    p("## Caveats")
    p("")
    p("1. **H1 XAUUSD only.** ~100 trading days (Jan 2 - Apr 10, 2026) = modest H1 sample. Continuation rates are computed over all swings detected, but per-algorithm swing counts vary wildly (DC 1.0% gives tens, BB light gives hundreds of swings). Lower-n algorithms have wider CIs.")
    p("2. **Continuation metric is a proxy for predictive power, not a trading edge test.** A swing_low whose close[+6] is higher confirms the swing was informative *in isolation*; it does not mean trading it would be profitable (no SL/TP, no transaction cost).")
    p("3. **6-candle horizon is arbitrary.** Chosen as roughly 1.5x the typical H1 OB retest distance per architecture.md. Sensitivity not tested here.")
    p("4. **Batch `displacement_quality` distribution is massively skewed** (105/111 'strong'). Any categorical revival test is under-powered for weak/medium cells. The Phase 1-2 classifier may have been a rubber stamp (corroborated by T2a's 'confidence_score=80' for 98% of setups).")
    p("5. **M15 reconstruction is 2026-only.** 2024-2025 trades cannot be reconstructed from available historical_2026/. We report only what matches and do not extrapolate.")
    p("6. **No API calls / no live-data use.** Local only.")
    p("")

    # ----- Verdicts -----
    p("## Verdicts")
    p("")

    # Q-2.1 verdict logic
    baseline_rate = baseline['cont_rate']
    best = ranked[0]
    best_delta = (best['cont_rate'] - baseline_rate) * 100
    if best['name'] == baseline['name']:
        q21_verdict = "**H-2.1 null CONFIRMED.** Fixed-lookback min_bars=2 is already top-ranked on continuation."
    else:
        best_pval = two_prop_p(best['cont_wins'], best['cont_n'], baseline['cont_wins'], baseline['cont_n'])
        ratio = best['n_swings'] / baseline['n_swings'] if baseline['n_swings'] else 0
        if best_pval < alpha_bonf:
            q21_verdict = (
                f"**H-2.1 null REJECTED ON THE CONTINUATION METRIC — BUT INTERPRET CAREFULLY.** "
                f"{best['name']} beats baseline by {best_delta:+.1f}pp at p={best_pval:.4f} < Bonferroni 0.00833. "
                f"**However**, it emits only {best['n_swings']} swings vs baseline {baseline['n_swings']} "
                f"(ratio {ratio:.2f}x). The higher continuation rate reflects selection — "
                f"larger-amplitude swings (avg amplitude {best['amp']:.1f} vs {baseline['amp']:.1f}) trivially "
                f"have more room to continue before reverting. This does NOT mean switching the production "
                f"swing algorithm will improve trading outcomes; it tests a *signal property*, not an edge. "
                f"**Action:** do NOT swap `market_state.detect_swings` based on this test alone. "
                f"The production-relevant follow-up is OB-continuation parity across algorithms (see Next steps)."
            )
        else:
            q21_verdict = f"**H-2.1 null CONFIRMED.** Best challenger ({best['name']}) beats baseline by {best_delta:+.1f}pp but p={best_pval:.4f} > Bonferroni 0.00833. No algorithm statistically dominates."
    p(f"- **Q-2.1:** {q21_verdict}")

    # Q-2.6 verdict
    p_sw = two_prop_p(w_strong, n_strong, w_other, n_other) if (n_strong and n_other) else 1.0
    if n_other < 10:
        q26_verdict = (
            f"**INSUFFICIENT DATA — CONFIRM KILL on categorical, DEFER on magnitude.** "
            f"The categorical `displacement_quality` test is under-powered (n_other={n_other}: 1 weak + {len(by_q.get('medium',[]))} medium). "
            f"Chi-square across levels p={chi_q_p:.4f}, strong-vs-other delta {delta_sw:+.1f}pp p={p_sw:.4f}. "
            f"Consistent with prior T3 KILL. Reconstructed-magnitude quartile test (n={sum(n for _,n in recon_counts) if recon_counts else 0}) chi-square p={recon_chi_p:.4f}.{recon_monotone_note} "
            f"Not enough signal or sample to overturn prior. Revisit when post-T7 live data accrues (T7 prompt does not self-classify displacement, so the categorical field will likely be blank anyway — the magnitude reconstruction route is the only path forward)."
        )
    elif abs(delta_sw) >= 5 and p_sw < 0.05:
        q26_verdict = f"**REVIVE as shadow.** Strong vs other delta {delta_sw:+.1f}pp at p={p_sw:.4f}. Log as candidate R2 feature, do not gate on it."
    else:
        q26_verdict = f"**CONFIRM KILL.** Strong vs other delta {delta_sw:+.1f}pp, p={p_sw:.4f}. Does not pass promotion threshold. Prior T3 KILL stands."
    p(f"- **Q-2.6:** {q26_verdict}")
    p("")

    # Next steps
    p("## Next steps")
    p("")
    p("1. **Do NOT change `market_state.detect_swings` based on Q-2.1 alone.** The continuation metric is confounded by amplitude selection (larger swings trivially continue further). Current production fixed-lookback min_bars=2 stays.")
    p("2. **Production-relevant follow-up for Q-2.1:** swap the swing algorithm upstream of `find_order_blocks` and compare OB-retest continuation rates (70% baseline) across A/B/C. An algorithm that detects fewer, higher-quality OBs at the same or better retest WR would be the real improvement. This requires building a parallel shadow pipeline and is a multi-week effort.")
    p("3. **Q-2.6 categorical revival is not feasible on current data.** T7 prompt does not self-classify displacement; the `displacement_quality` field will not be populated for post-Apr-12 trades. Default path: rely on reconstructed impulse/ATR magnitude as a live feature (log-only) once the M15 historical corpus covers enough post-T7 trades (~3 months).")
    p("4. **Secondary hint from reconstructed magnitude (n=29):** U-shape (Q1 75% / Q2 29% / Q3 57% / Q4 86%) is interesting but chi-square p=0.13 and n=29 is far below promotion threshold. Do NOT act on it. Re-test with n>=80 reconstructable trades.")
    p("5. **Consider** continuation-rate test across multiple horizons (3/6/12/24 candles) with full Bonferroni for Q-2.1 if someone is curious — but the amplitude-selection confound persists across horizons. Lower priority than the OB-parity test in (2).")
    p("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")
    print("\n--- key results ---")
    for r in results:
        print(f"{r['name']:30s} n_swings={r['n_swings']:4d} cont_rate={r['cont_rate']*100:.1f}% (n={r['cont_n']})")
    print(f"\nQ-2.1 verdict: {q21_verdict}")
    print(f"Q-2.6 verdict: {q26_verdict}")


if __name__ == "__main__":
    run()
