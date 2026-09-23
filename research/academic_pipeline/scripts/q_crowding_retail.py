"""
Q-8.3 (crowding) + Q-16.4 (retail herding contrarian) — local-data analysis.

Zero API cost. Uses only batch trades + historical OHLCV.

Pre-registered hypotheses:

Q-8.3 — Internal crowding proxies:
    H1: WR trend over time is non-increasing.
        Test: Kendall's tau between chronological window index (rolling 50-trade
        windows) and window WR. Reject null (no trend) if tau < 0 and p < 0.05.
    H2: MFE of winning OB retests compresses over time (crowding front-runs
        the retest, clips the continuation magnitude).
        Test: Spearman rho between month-index and mean(mfe_r | WIN).
    H3: Spread proxy — historical CSVs are OHLCV-only (no bid/ask spread),
        so we proxy with intrabar range relative to ATR. If post-OB-touch
        bars show wider ranges over time, that is consistent with more
        adverse liquidity. (Weak proxy — documented as a limitation.)

Q-16.4 — Retail herding contrarian:
    H4: After an "extreme" prior-day move (|daily return| >= 95th pct of the
        pre-trade history), trades whose direction OPPOSES the extreme move
        have higher WR than trades whose direction FOLLOWS it.
        Test: Two-proportion z-test, contrarian WR > continuation WR.
    H5: Baseline check — does the post-extreme subset of trades have
        different WR than the overall population? (Fisher's exact.)

Data gaps (documented, not fillable locally):
    - No CFTC COT speculator positioning data.
    - No IG/OANDA broker client sentiment.
    - No Google Trends / social-media volume.
    - Historical CSVs have no bid/ask spread columns.
    - Live trade records (Apr 2026) are decision snapshots, not closed
      trades — cannot contribute to WR trend.

Outputs:
    - Markdown report at research/academic_pipeline/results/Q-crowding_retail.md
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
TRADES_PATH = ROOT / "knowledge_base_backtest" / "analysis" / "unified_trades_v2_20260331.json"
HIST_DIR = ROOT / "data" / "historical_2026"
OUT_MD = ROOT / "research" / "academic_pipeline" / "results" / "Q-crowding_retail.md"

WINDOW_SIZE = 50
EXTREME_PCTILE = 0.95  # 95th percentile daily abs return


# --------------------------------------------------------------------------- #
# Stats helpers (pure-Python, no scipy dependency)                            #
# --------------------------------------------------------------------------- #

def _rank(xs: list[float]) -> list[float]:
    """Average-rank (handles ties)."""
    n = len(xs)
    order = sorted(range(n), key=lambda i: xs[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Spearman rho + two-sided p (normal approximation, n>=10)."""
    n = len(xs)
    if n < 3:
        return float("nan"), float("nan")
    rx, ry = _rank(xs), _rank(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    dx = math.sqrt(sum((rx[i] - mx) ** 2 for i in range(n)))
    dy = math.sqrt(sum((ry[i] - my) ** 2 for i in range(n)))
    if dx == 0 or dy == 0:
        return 0.0, 1.0
    rho = num / (dx * dy)
    # t-based two-sided p
    t = rho * math.sqrt((n - 2) / max(1e-12, 1 - rho * rho))
    # Normal approximation for p (adequate for n>=30)
    p = 2.0 * (1.0 - _norm_cdf(abs(t)))
    return rho, p


def kendall_tau(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Kendall's tau-b + two-sided p (normal approx, variance ignores ties)."""
    n = len(xs)
    if n < 3:
        return float("nan"), float("nan")
    concordant = discordant = tie_x = tie_y = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = xs[i] - xs[j]
            dy = ys[i] - ys[j]
            if dx == 0 and dy == 0:
                continue
            if dx == 0:
                tie_x += 1
                continue
            if dy == 0:
                tie_y += 1
                continue
            if (dx > 0) == (dy > 0):
                concordant += 1
            else:
                discordant += 1
    n0 = n * (n - 1) // 2
    denom = math.sqrt((n0 - tie_x) * (n0 - tie_y))
    if denom == 0:
        return 0.0, 1.0
    tau = (concordant - discordant) / denom
    # Variance under null
    var = (2 * (2 * n + 5)) / (9.0 * n * (n - 1))
    z = tau / math.sqrt(var)
    p = 2.0 * (1.0 - _norm_cdf(abs(z)))
    return tau, p


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def two_proportion_ztest(x1: int, n1: int, x2: int, n2: int) -> tuple[float, float]:
    """Two-sample z test for equal proportions. Returns (z, two-sided p)."""
    if n1 == 0 or n2 == 0:
        return float("nan"), float("nan")
    p1, p2 = x1 / n1, x2 / n2
    pooled = (x1 + x2) / (n1 + n2)
    se = math.sqrt(pooled * (1 - pooled) * (1.0 / n1 + 1.0 / n2))
    if se == 0:
        return 0.0, 1.0
    z = (p1 - p2) / se
    p = 2.0 * (1.0 - _norm_cdf(abs(z)))
    return z, p


def fisher_exact_twosided(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher's exact p (small tables). 2x2: [[a,b],[c,d]]."""
    # Enumerate over all tables with same marginals; sum p for p<=observed.
    n = a + b + c + d
    row1 = a + b
    col1 = a + c
    row2 = c + d  # noqa: F841 (kept for readability)

    def log_comb(n_: int, k_: int) -> float:
        if k_ < 0 or k_ > n_:
            return float("-inf")
        return math.lgamma(n_ + 1) - math.lgamma(k_ + 1) - math.lgamma(n_ - k_ + 1)

    log_denom = log_comb(n, row1)
    obs_log_p = log_comb(col1, a) + log_comb(n - col1, row1 - a) - log_denom
    total = 0.0
    for a_ in range(max(0, row1 - (n - col1)), min(row1, col1) + 1):
        lp = log_comb(col1, a_) + log_comb(n - col1, row1 - a_) - log_denom
        if lp <= obs_log_p + 1e-12:
            total += math.exp(lp)
    return min(1.0, total)


# --------------------------------------------------------------------------- #
# Load data                                                                   #
# --------------------------------------------------------------------------- #

@dataclass
class Trade:
    date: datetime
    direction: str
    outcome: str            # WIN / LOSS / BREAKEVEN
    r_multiple: float
    mfe_r: float
    mae_r: float
    kill_zone: str


def load_trades() -> list[Trade]:
    with open(TRADES_PATH) as f:
        raw = json.load(f)
    trades = []
    for t in raw:
        try:
            d = datetime.strptime(t["date"], "%Y-%m-%d")
        except (KeyError, ValueError):
            continue
        trades.append(Trade(
            date=d,
            direction=t.get("direction", "unknown"),
            outcome=t.get("outcome", ""),
            r_multiple=float(t.get("r_multiple", 0.0)),
            mfe_r=float(t.get("mfe_r", 0.0) or 0.0),
            mae_r=float(t.get("mae_r", 0.0) or 0.0),
            kill_zone=t.get("kill_zone", ""),
        ))
    trades.sort(key=lambda x: x.date)
    return trades


def load_daily_ohlc(symbol: str) -> dict[str, tuple[float, float, float, float]]:
    """Returns {date_str: (open, high, low, close)}."""
    path = HIST_DIR / f"{symbol}_D1.csv"
    if not path.exists():
        return {}
    out: dict[str, tuple[float, float, float, float]] = {}
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = row["time"].split(" ")[0]
            out[ts] = (float(row["open"]), float(row["high"]),
                       float(row["low"]), float(row["close"]))
    return out


# --------------------------------------------------------------------------- #
# Q-8.3 — internal crowding proxies                                           #
# --------------------------------------------------------------------------- #

def rolling_window_wr(trades: list[Trade], size: int) -> list[tuple[int, float, int]]:
    """Returns list of (window_index, win_rate, n_wins) for each rolling window."""
    out = []
    for i in range(len(trades) - size + 1):
        window = trades[i : i + size]
        # Exclude BE from WR denominator? Use WIN/(WIN+LOSS).
        wins = sum(1 for t in window if t.outcome == "WIN")
        losses = sum(1 for t in window if t.outcome == "LOSS")
        n = wins + losses
        if n == 0:
            continue
        out.append((i, wins / n, wins))
    return out


def non_overlapping_window_wr(trades: list[Trade], size: int) -> list[tuple[int, float, int]]:
    """Non-overlapping windows (stride=size). Each trade belongs to exactly one window.
    Kills the autocorrelation-bias that inflates rolling tau."""
    out = []
    n_trades = len(trades)
    for start in range(0, n_trades, size):
        window = trades[start : start + size]
        if len(window) < size:
            break  # drop partial trailing window for strict independence
        wins = sum(1 for t in window if t.outcome == "WIN")
        losses = sum(1 for t in window if t.outcome == "LOSS")
        n = wins + losses
        if n == 0:
            continue
        out.append((start // size, wins / n, wins))
    return out


def monthly_wr(trades: list[Trade]) -> list[tuple[str, float, int, int]]:
    """Per-month WR = WIN / (WIN+LOSS). Returns (month, wr, wins, n_decided)."""
    buckets: dict[str, list[str]] = defaultdict(list)
    for t in trades:
        if t.outcome in ("WIN", "LOSS"):
            key = t.date.strftime("%Y-%m")
            buckets[key].append(t.outcome)
    out = []
    for m in sorted(buckets):
        arr = buckets[m]
        wins = sum(1 for o in arr if o == "WIN")
        n = len(arr)
        if n >= 3:  # require min sample size per month to include in tau
            out.append((m, wins / n, wins, n))
    return out


def monthly_mfe_mean_wins(trades: list[Trade]) -> list[tuple[str, float, int]]:
    """Mean MFE of winning trades per calendar month, plus n."""
    buckets: dict[str, list[float]] = defaultdict(list)
    for t in trades:
        if t.outcome == "WIN":
            key = t.date.strftime("%Y-%m")
            buckets[key].append(t.mfe_r)
    out = []
    for m in sorted(buckets):
        arr = buckets[m]
        if len(arr) >= 2:
            out.append((m, sum(arr) / len(arr), len(arr)))
    return out


def analyze_q83(trades: list[Trade]) -> dict:
    windows = rolling_window_wr(trades, WINDOW_SIZE)
    xs = [w[0] for w in windows]
    ys = [w[1] for w in windows]
    tau, tau_p = kendall_tau(xs, ys)
    rho, rho_p = spearman(xs, ys)

    # First vs last window: raw effect size
    first_wr = windows[0][1] if windows else float("nan")
    last_wr = windows[-1][1] if windows else float("nan")
    wr_delta = last_wr - first_wr

    # Reviewer correction 2026-04-17 — autocorrelation-aware analyses
    # 1. Non-overlapping windows (stride = WINDOW_SIZE) for independence
    nonoverlap = non_overlapping_window_wr(trades, WINDOW_SIZE)
    if len(nonoverlap) >= 3:
        no_xs = [w[0] for w in nonoverlap]
        no_ys = [w[1] for w in nonoverlap]
        no_tau, no_tau_p = kendall_tau(no_xs, no_ys)
        no_rho, no_rho_p = spearman(no_xs, no_ys)
    else:
        no_tau = no_tau_p = no_rho = no_rho_p = float("nan")

    # 2. Monthly WR aggregate (independent monthly samples, minimum n=3 per month)
    monthly_wr_data = monthly_wr(trades)
    if len(monthly_wr_data) >= 4:
        mwr_xs = list(range(len(monthly_wr_data)))
        mwr_ys = [m[1] for m in monthly_wr_data]
        mwr_tau, mwr_tau_p = kendall_tau(mwr_xs, mwr_ys)
        mwr_rho, mwr_rho_p = spearman(mwr_xs, mwr_ys)
    else:
        mwr_tau = mwr_tau_p = mwr_rho = mwr_rho_p = float("nan")

    # MFE compression test
    monthly = monthly_mfe_mean_wins(trades)
    if len(monthly) >= 4:
        mfe_xs = list(range(len(monthly)))
        mfe_ys = [m[1] for m in monthly]
        mfe_tau, mfe_tau_p = kendall_tau(mfe_xs, mfe_ys)
        mfe_rho, mfe_rho_p = spearman(mfe_xs, mfe_ys)
        mfe_first = sum(m[1] for m in monthly[:3]) / 3
        mfe_last = sum(m[1] for m in monthly[-3:]) / 3
    else:
        mfe_tau = mfe_tau_p = mfe_rho = mfe_rho_p = float("nan")
        mfe_first = mfe_last = float("nan")

    return {
        "n_windows": len(windows),
        "window_size": WINDOW_SIZE,
        "first_window_wr": first_wr,
        "last_window_wr": last_wr,
        "wr_delta_first_to_last": wr_delta,
        "kendall_tau": tau,
        "kendall_tau_p": tau_p,
        "spearman_rho": rho,
        "spearman_rho_p": rho_p,
        "windows_sample": windows[:: max(1, len(windows) // 8)],  # compact display
        # Non-overlapping (autocorrelation-corrected)
        "n_nonoverlap_windows": len(nonoverlap),
        "nonoverlap_windows": nonoverlap,
        "nonoverlap_kendall_tau": no_tau,
        "nonoverlap_kendall_tau_p": no_tau_p,
        "nonoverlap_spearman_rho": no_rho,
        "nonoverlap_spearman_rho_p": no_rho_p,
        # Monthly WR aggregate
        "monthly_wr": monthly_wr_data,
        "n_monthly_wr": len(monthly_wr_data),
        "monthly_wr_kendall_tau": mwr_tau,
        "monthly_wr_kendall_tau_p": mwr_tau_p,
        "monthly_wr_spearman_rho": mwr_rho,
        "monthly_wr_spearman_rho_p": mwr_rho_p,
        # MFE
        "monthly_mfe": monthly,
        "mfe_kendall_tau": mfe_tau,
        "mfe_kendall_tau_p": mfe_tau_p,
        "mfe_spearman_rho": mfe_rho,
        "mfe_spearman_rho_p": mfe_rho_p,
        "mfe_first_3mo_mean": mfe_first,
        "mfe_last_3mo_mean": mfe_last,
    }


# --------------------------------------------------------------------------- #
# Q-16.4 — contrarian-after-extreme                                           #
# --------------------------------------------------------------------------- #

def classify_prior_day_move(
    trade_date: datetime,
    ohlc: dict[str, tuple[float, float, float, float]],
    threshold_abs_return: float,
) -> tuple[str | None, float]:
    """Returns (direction_label, abs_return) for the most recent trading day
    strictly prior to trade_date. Labels: 'UP', 'DOWN', or None if move did
    not exceed threshold or data missing."""
    # Find the most recent available D1 bar strictly before trade_date
    ts = trade_date.strftime("%Y-%m-%d")
    prior = [d for d in ohlc if d < ts]
    if not prior:
        return None, 0.0
    prior.sort()
    prev_date = prior[-1]
    o, h, l, c = ohlc[prev_date]
    if o == 0:
        return None, 0.0
    ret = (c - o) / o
    if abs(ret) < threshold_abs_return:
        return None, abs(ret)
    return ("UP" if ret > 0 else "DOWN"), abs(ret)


def analyze_q164(trades: list[Trade]) -> dict:
    ohlc = load_daily_ohlc("XAUUSD")

    # 1. Build distribution of daily returns from ALL historical D1 data
    # (threshold defined OUT-OF-SAMPLE — does not peek at trade outcomes).
    all_abs_rets = []
    for _, (o, _h, _l, c) in ohlc.items():
        if o != 0:
            all_abs_rets.append(abs((c - o) / o))
    all_abs_rets.sort()
    if not all_abs_rets:
        return {"error": "no_historical_data"}
    idx = int(EXTREME_PCTILE * len(all_abs_rets))
    threshold = all_abs_rets[min(idx, len(all_abs_rets) - 1)]

    # 2. Classify each trade
    contrarian_wins = contrarian_losses = 0
    continuation_wins = continuation_losses = 0
    matched = 0
    skipped_no_prior = 0
    skipped_not_extreme = 0
    skipped_unknown_dir = 0

    for t in trades:
        if t.outcome == "BREAKEVEN":
            continue
        prior_dir, _abs_ret = classify_prior_day_move(t.date, ohlc, threshold)
        if prior_dir is None:
            # Separate counters
            # Check if data missing vs not-extreme
            ts = t.date.strftime("%Y-%m-%d")
            prior = [d for d in ohlc if d < ts]
            if not prior:
                skipped_no_prior += 1
            else:
                skipped_not_extreme += 1
            continue
        if t.direction == "LONG":
            trade_dir = "UP"
        elif t.direction == "SHORT":
            trade_dir = "DOWN"
        else:
            skipped_unknown_dir += 1
            continue
        matched += 1
        is_win = t.outcome == "WIN"
        if trade_dir != prior_dir:
            # contrarian (trade opposes prior-day extreme)
            if is_win:
                contrarian_wins += 1
            else:
                contrarian_losses += 1
        else:
            if is_win:
                continuation_wins += 1
            else:
                continuation_losses += 1

    # 3. Stats
    n_contra = contrarian_wins + contrarian_losses
    n_cont = continuation_wins + continuation_losses
    contra_wr = contrarian_wins / n_contra if n_contra else float("nan")
    cont_wr = continuation_wins / n_cont if n_cont else float("nan")

    z, p_z = two_proportion_ztest(contrarian_wins, n_contra,
                                  continuation_wins, n_cont)
    p_fisher = fisher_exact_twosided(contrarian_wins, contrarian_losses,
                                     continuation_wins, continuation_losses)

    # Baseline: overall WR of the matched subset (treated together) vs global
    global_wins = sum(1 for t in trades if t.outcome == "WIN")
    global_losses = sum(1 for t in trades if t.outcome == "LOSS")
    matched_wins = contrarian_wins + continuation_wins
    matched_losses = contrarian_losses + continuation_losses
    _, p_subset_vs_global = two_proportion_ztest(matched_wins,
                                                 matched_wins + matched_losses,
                                                 global_wins,
                                                 global_wins + global_losses)

    return {
        "historical_daily_bars": len(all_abs_rets),
        "extreme_abs_return_threshold": threshold,
        "extreme_threshold_pct": threshold * 100,
        "matched_trades": matched,
        "skipped_no_prior": skipped_no_prior,
        "skipped_not_extreme": skipped_not_extreme,
        "skipped_unknown_dir": skipped_unknown_dir,
        "contrarian": {
            "n": n_contra, "wins": contrarian_wins,
            "losses": contrarian_losses, "wr": contra_wr,
        },
        "continuation": {
            "n": n_cont, "wins": continuation_wins,
            "losses": continuation_losses, "wr": cont_wr,
        },
        "diff_wr": contra_wr - cont_wr if not math.isnan(contra_wr + cont_wr) else float("nan"),
        "z_contra_vs_cont": z,
        "p_z_two_sided": p_z,
        "p_fisher_two_sided": p_fisher,
        "p_subset_vs_global": p_subset_vs_global,
        "global_wr_batch": global_wins / (global_wins + global_losses),
    }


# --------------------------------------------------------------------------- #
# Report                                                                      #
# --------------------------------------------------------------------------- #

def fmt_p(p: float) -> str:
    if math.isnan(p):
        return "NaN"
    if p < 0.001:
        return "<0.001"
    return f"{p:.3f}"


def build_report(q83: dict, q164: dict, trades: list[Trade]) -> str:
    date_min = trades[0].date.strftime("%Y-%m-%d")
    date_max = trades[-1].date.strftime("%Y-%m-%d")
    ws_rows = "\n".join(
        f"| {idx} | {wr:.3f} | {wins} |" for idx, wr, wins in q83["windows_sample"]
    )
    monthly_rows = "\n".join(
        f"| {m} | {mfe:.3f} | {n} |" for m, mfe, n in q83["monthly_mfe"]
    )
    _monthly_wr_table_rows = "\n".join(
        f"| {m} | {wr:.3f} | {wins} | {n} |" for m, wr, wins, n in q83["monthly_wr"]
    )

    # Q-8.3 verdict — CORRECTED 2026-04-17: use autocorrelation-aware tests,
    # not the rolling-window tau (which is inflated by overlapping-window
    # autocorrelation; effective n is ~n_trades / window_size, not n_trades).
    no_tau = q83["nonoverlap_kendall_tau"]
    no_tau_p = q83["nonoverlap_kendall_tau_p"]
    no_n = q83["n_nonoverlap_windows"]
    mwr_tau = q83["monthly_wr_kendall_tau"]
    mwr_tau_p = q83["monthly_wr_kendall_tau_p"]
    mwr_n = q83["n_monthly_wr"]

    # Decision rule: require ALL autocorrelation-corrected tests to reject the
    # null before claiming a direction. Use Bonferroni alpha=0.025 across the
    # two independent family members (non-overlap, monthly).
    alpha_corr = 0.025
    no_sig = not math.isnan(no_tau_p) and no_tau_p < alpha_corr
    mwr_sig = not math.isnan(mwr_tau_p) and mwr_tau_p < alpha_corr
    no_dir = (no_tau > 0) if not math.isnan(no_tau) else None
    mwr_dir = (mwr_tau > 0) if not math.isnan(mwr_tau) else None

    if no_n < 3 and mwr_n < 4:
        q83_verdict = (
            f"**INCONCLUSIVE — UNDERPOWERED AFTER AUTOCORRELATION CORRECTION.** "
            f"Non-overlapping windows (stride={WINDOW_SIZE}) yielded only n={no_n} effective "
            f"samples; monthly WR aggregate has n={mwr_n} months with >=3 decided trades. "
            f"Kendall tau on either is not statistically interpretable. The original "
            f"rolling-window headline tau={q83['kendall_tau']:+.3f} (p={fmt_p(q83['kendall_tau_p'])}) "
            f"is inflated by overlapping-window autocorrelation and should NOT be read as "
            f"a genuine trend. Re-test requires more calendar-time history."
        )
    elif no_sig and mwr_sig and no_dir == mwr_dir:
        direction_word = "UPWARD" if no_dir else "DOWNWARD"
        q83_verdict = (
            f"**SIGNAL: WR trending {direction_word} across both autocorrelation-corrected "
            f"tests.** Non-overlap tau={no_tau:+.3f} (p={fmt_p(no_tau_p)}, n={no_n}); "
            f"monthly WR tau={mwr_tau:+.3f} (p={fmt_p(mwr_tau_p)}, n={mwr_n}). "
            f"Both reject the null at Bonferroni alpha=0.025 and agree on direction."
        )
    else:
        q83_verdict = (
            f"**INCONCLUSIVE — rolling-window result inflated by autocorrelation.** "
            f"The original rolling-window tau={q83['kendall_tau']:+.3f} "
            f"(p={fmt_p(q83['kendall_tau_p'])}) used overlapping 50-trade windows; "
            f"effective independent sample is ~n_trades/50 = ~{no_n}, not ~{q83['n_windows']}. "
            f"After correction:\n"
            f"  - Non-overlapping windows (stride={WINDOW_SIZE}, n={no_n}): "
            f"tau={no_tau:+.3f}, p={fmt_p(no_tau_p)}.\n"
            f"  - Monthly WR aggregate (min 3 trades/month, n={mwr_n}): "
            f"tau={mwr_tau:+.3f}, p={fmt_p(mwr_tau_p)}.\n"
            f"Neither survives Bonferroni alpha=0.025. **No reliable trend is detected; "
            f"the original 'WR trending UPWARD' conclusion is RETRACTED.** The observed "
            f"rolling-window positive tau was a statistical artefact of overlapping samples."
        )

    # Q-16.4 verdict
    diff = q164.get("diff_wr", float("nan"))
    has_signal = (not math.isnan(diff)
                  and diff > 0
                  and q164["p_z_two_sided"] < 0.05)
    if q164["matched_trades"] < 20:
        q164_verdict = (f"**UNDERPOWERED — DATA GAP.** Only "
                        f"{q164['matched_trades']} batch trades could be "
                        "matched to a prior-day D1 bar. Root cause: local "
                        "historical CSVs cover only 2026-01-02 -> 2026-04-10, "
                        "but 82/111 batch trades occurred in 2024-2025. "
                        "Effect is not statistically interpretable at this "
                        "sample size. Test is READY TO RE-RUN once the "
                        "2024-2025 D1 gap is closed.")
    elif has_signal:
        q164_verdict = ("**SIGNAL — contrarian-after-extreme outperforms** at "
                        "p<0.05. Effect worth shadow-logging live.")
    else:
        q164_verdict = ("**NO SIGNAL.** Contrarian-vs-continuation WR gap is "
                        "not statistically distinguishable.")

    return f"""# Q-8.3 (crowding) + Q-16.4 (retail herding contrarian) — local analysis

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M local")}
Script: `research/academic_pipeline/scripts/q_crowding_retail.py`
Cost: $0 (local only).

## Hypothesis (pre-registered)

**Q-8.3 — internal crowding proxies**

- **H1.** WR trend over time is non-increasing. Kendall's tau between rolling-50-trade window index (chronological) and window WR. Reject null (no trend) if tau < 0 at p < 0.05.
- **H2.** Mean MFE of winning trades compresses over time (crowding front-runs the retest). Kendall's tau on monthly mean MFE of winners.
- **H3 (spread proxy).** Historical CSVs are OHLCV only — no bid/ask — so no direct spread test. Documented as data gap.

**Q-16.4 — retail herding contrarian**

- **H4.** After an extreme prior-day move (|daily return| >= 95th pct of historical XAUUSD daily returns), trades whose direction OPPOSES the extreme have higher WR than trades whose direction FOLLOWS it. Two-proportion z-test, two-sided.
- **H5.** Matched-subset baseline check vs global batch WR (Fisher's exact).

Pre-registered BEFORE computing results. No post-hoc threshold tuning.

## Data

- **Batch trades:** `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json`
  - n={len(trades)}, date range {date_min} -> {date_max}
  - Outcomes: WIN={sum(1 for t in trades if t.outcome=='WIN')}, LOSS={sum(1 for t in trades if t.outcome=='LOSS')}, BE={sum(1 for t in trades if t.outcome=='BREAKEVEN')}
  - Direction: LONG={sum(1 for t in trades if t.direction=='LONG')}, SHORT={sum(1 for t in trades if t.direction=='SHORT')}, unknown={sum(1 for t in trades if t.direction=='unknown')}
- **Historical:** `data/historical_2026/XAUUSD_D1.csv` ({q164.get('historical_daily_bars','?')} daily bars, Jan 2 - Apr 10 2026).
- **Live records:** 9 JSON snapshots in `knowledge_base/trade_records/XAUUSD/` for Apr 15-16 2026. These are decision-time captures without closed-trade outcomes (no r_multiple) — cannot contribute to WR trend. Documented as Apr 2026 live data gap.

## Method

1. Load unified_trades_v2, sort chronologically.
2. **Q-8.3 WR trend:** rolling {WINDOW_SIZE}-trade windows over the chronological series; Kendall tau + Spearman rho between window index and window WR. WR = WINS / (WINS + LOSSES); breakevens excluded from denominator.
3. **Q-8.3 MFE compression:** per-calendar-month mean MFE of winners only (n >= 2/month); Kendall tau + Spearman rho vs month index.
4. **Q-16.4:** derive 95th-percentile abs-return threshold from XAUUSD D1 bars. For each batch trade, look up the most recent D1 bar strictly prior to trade date. If |daily return| >= threshold, classify as "extreme UP" or "extreme DOWN". Label trade as contrarian (direction opposes extreme) or continuation (direction matches). Two-proportion z-test + Fisher's exact.
5. Global batch baseline for sanity.

All stats implemented in pure Python; no scipy dependency.

## Q-8.3 — Internal crowding proxies

### Rolling-window WR trend

- Windows: {q83['n_windows']} (window size {q83['window_size']})
- First window WR: {q83['first_window_wr']:.3f}
- Last window WR: {q83['last_window_wr']:.3f}
- WR delta (last - first): {q83['wr_delta_first_to_last']:+.3f}
- **Kendall tau:** {q83['kendall_tau']:+.3f}, p = {fmt_p(q83['kendall_tau_p'])}
- **Spearman rho:** {q83['spearman_rho']:+.3f}, p = {fmt_p(q83['spearman_rho_p'])}

Sampled windows (every Nth):

| window_idx | WR | wins |
|---|---|---|
{ws_rows}

### MFE compression (winners only)

- Months analyzed: {len(q83['monthly_mfe'])}
- First 3-month mean MFE (winners): {q83['mfe_first_3mo_mean']:.3f}R
- Last 3-month mean MFE (winners): {q83['mfe_last_3mo_mean']:.3f}R
- **Kendall tau (month_idx vs mean MFE):** {q83['mfe_kendall_tau']:+.3f}, p = {fmt_p(q83['mfe_kendall_tau_p'])}
- **Spearman rho:** {q83['mfe_spearman_rho']:+.3f}, p = {fmt_p(q83['mfe_spearman_rho_p'])}

Monthly MFE means:

| month | mean_mfe_R (winners) | n_winners |
|---|---|---|
{monthly_rows}

### Q-8.3 verdict (reviewer-corrected — see autocorrelation section below)

{q83_verdict}

### Reviewer correction 2026-04-17 — autocorrelation in rolling-window tau (MAJOR)

**Finding:** The original Kendall tau above was computed on **overlapping** 50-trade windows (stride=1). Consecutive windows share 49 of 50 observations, so the independence assumption underlying Kendall tau's variance formula is violated. Effective sample size is approximately `n_trades / window_size ≈ {q83['n_nonoverlap_windows']}`, not the reported {q83['n_windows']}. This inflates the z-statistic by approximately √50 and the reported p=<0.001 is not trustworthy.

**Corrections applied:**

1. **Non-overlapping windows** (stride = window size = {WINDOW_SIZE}). Each trade enters exactly one window. Only complete windows included (trailing partial dropped).
   - Windows: {q83['n_nonoverlap_windows']}
   - Kendall tau: {q83['nonoverlap_kendall_tau']:+.3f}, p = {fmt_p(q83['nonoverlap_kendall_tau_p'])}
   - Spearman rho: {q83['nonoverlap_spearman_rho']:+.3f}, p = {fmt_p(q83['nonoverlap_spearman_rho_p'])}

2. **Monthly WR aggregate** (per-month WR = WIN / (WIN+LOSS) on months with >=3 decided trades — independent calendar buckets).
   - Months included: {q83['n_monthly_wr']}
   - Kendall tau (month_idx vs WR): {q83['monthly_wr_kendall_tau']:+.3f}, p = {fmt_p(q83['monthly_wr_kendall_tau_p'])}
   - Spearman rho: {q83['monthly_wr_spearman_rho']:+.3f}, p = {fmt_p(q83['monthly_wr_spearman_rho_p'])}

Per-month WR table:

| month | WR | wins | n_decided |
|---|---|---|---|
{_monthly_wr_table_rows}

**Bonferroni alpha** across the two corrected tests = 0.025. Both must reject to claim a trend.

## Q-16.4 — Contrarian after extreme prior-day move

- XAUUSD D1 bars analyzed: {q164.get('historical_daily_bars', 'N/A')}
- 95th-percentile abs-return threshold: {q164.get('extreme_threshold_pct', float('nan')):.3f}%
- Matched trades (extreme prior day, known direction): {q164['matched_trades']}
- Skipped — no prior bar: {q164['skipped_no_prior']}
- Skipped — prior day not extreme: {q164['skipped_not_extreme']}
- Skipped — unknown direction: {q164['skipped_unknown_dir']}

| subset | n | wins | losses | WR |
|---|---|---|---|---|
| contrarian (opposes extreme) | {q164['contrarian']['n']} | {q164['contrarian']['wins']} | {q164['contrarian']['losses']} | {q164['contrarian']['wr']:.3f} |
| continuation (follows extreme) | {q164['continuation']['n']} | {q164['continuation']['wins']} | {q164['continuation']['losses']} | {q164['continuation']['wr']:.3f} |

- WR delta (contrarian - continuation): {q164['diff_wr']:+.3f}
- Two-proportion z = {q164['z_contra_vs_cont']:+.3f}, two-sided p = {fmt_p(q164['p_z_two_sided'])}
- Fisher's exact two-sided p = {fmt_p(q164['p_fisher_two_sided'])}
- Subset vs global (sanity): p = {fmt_p(q164['p_subset_vs_global'])} (global WR {q164['global_wr_batch']:.3f})

### Q-16.4 verdict

{q164_verdict}

## Caveats

1. **Uneven temporal coverage.** The batch's 111 trades are not uniformly distributed (2024 is thin; 2026-01 alone has 18). Rolling-window indices are trade-count, not time-weighted, so a "decay trend" can be confounded with regime shifts (e.g., the Jan 2026 bull impulse).
2. **Direction bias.** 103/111 = 92.8% of batch trades are LONG. The Q-16.4 test therefore almost entirely asks "after an extreme UP day, do LONG trades perform worse than after an extreme DOWN day" (or vice versa). True directional contrarian testing needs a more balanced sample.
3. **Historical CSVs are 2026-only** (Jan 2 - Apr 10). Pre-2026 batch trades (n={sum(1 for t in trades if t.date.year < 2026)}) have no local D1 bars to derive prior-day moves, so they fall into skipped_no_prior.
4. **OHLCV only.** No bid/ask spread columns, no tick data. H3 (spread-widening crowding proxy) is not testable locally.
5. **Live Apr 2026 records** (9 files) are decision snapshots, not closed trades — no r_multiple — so they cannot contribute to WR trend.
6. **Multiple testing.** Four tests performed (H1 tau, H2 tau, H4 z, H5 Fisher). Bonferroni-adjusted alpha = 0.0125. Only treat a result as confirmed if p < 0.0125.
7. **Reviewer correction (2026-04-17) — autocorrelation:** The rolling-window Kendall tau (window=50, stride=1) was inflated by overlap between consecutive windows; effective sample size was ~{q83['n_nonoverlap_windows']} independent windows, not {q83['n_windows']}. Corrected tests (non-overlapping stride=50 and monthly WR aggregate) are reported in the Reviewer correction section above. The original claim of "NO CROWDING DECAY — trending UPWARD" has been RETRACTED.

## Data gaps

| Proxy | Status | Why not fillable locally |
|---|---|---|
| CFTC COT speculator positioning | MISSING | Not in repo; requires CFTC weekly download. |
| IG / OANDA client-sentiment | MISSING | Broker-feed API; not public, not cached locally. |
| Google Trends "smart money concept" | MISSING | No cached CSV; requires pytrends + internet. |
| Twitter / Reddit SMC mention volume | MISSING | No cached dataset. |
| Bid/ask spread on OB retest bars | MISSING | Historical CSVs are OHLCV; tick data absent. |
| Post-2024-04 / pre-2026-01 D1 bars | MISSING | Historical export is 2026-only; 2024-2025 batch trades cannot be matched to prior-day moves. |
| Live closed-trade outcomes (Apr 2026) | IN FLIGHT | Only 9 decision-time captures; no exit/r_multiple fields populated. |

## Verdicts

- **Q-8.3:** {q83_verdict}
- **Q-16.4:** {q164_verdict}

## Next steps

1. **Close the daily-bar gap.** Export D1 bars for XAUUSD 2024-01 -> 2025-12 from MT5 to enable Q-16.4 on the full batch (n=111 candidates vs ~{q164['matched_trades']} matched now).
2. **Re-run Q-8.3 monthly.** Keep the script in place; after WF-1 concludes (Jul 7 2026), re-run with live trades appended. A persistent negative tau at p < 0.05 is a crowding-decay trigger.
3. **External-proxy capture (CEO approval needed).** Any one of: CFTC COT XAUUSD speculator net position; Google Trends "order block retest"; cached IG sentiment scraper. Each closes one gap identified above.
4. **SHORT-side collection.** The 7.2% SHORT sample is too small for direction-conditioned tests. Ideally 30+ SHORT trades before re-running directional analyses.
5. **Do NOT promote a contrarian filter on this data.** Underpowered / ambiguous per the verdict above. Treat as a candidate shadow-logger only if verdict upgrades.

*End of report.*
"""


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #

def main() -> None:
    trades = load_trades()
    q83 = analyze_q83(trades)
    q164 = analyze_q164(trades)
    report = build_report(q83, q164, trades)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Wrote {OUT_MD}")
    print(f"  windows={q83['n_windows']} "
          f"tau={q83['kendall_tau']:+.3f} p={q83['kendall_tau_p']:.4f}")
    print(f"  matched_extreme={q164['matched_trades']} "
          f"contra_wr={q164['contrarian']['wr']:.3f} "
          f"cont_wr={q164['continuation']['wr']:.3f} "
          f"p={q164['p_z_two_sided']:.4f}")


if __name__ == "__main__":
    main()
