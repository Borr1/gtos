"""
Q-10 Macro Factor Re-test  (v2 - circularity fix)
==================================================
Fixes the circular-proxy-sanity-check flagged by Wave 1 reviewers.

Reviewer finding (Issue 3):
    v1's "proxy correlation" computed r between USDJPY and a synthetic basket
    (0.5 USDJPY + 0.5 inv-GBPUSD). USDJPY appears on BOTH sides of the correlation,
    so any r > 0 is guaranteed mechanically by the USDJPY-in-basket component.
    The reported r=0.913 is therefore partially circular and does not measure
    proxy quality.

What v2 does differently:
    A) Reports the *non-circular* off-diagonal correlation r(USDJPY, inv-GBPUSD) -
       this is the cross-pair correlation between the two available USD-base
       instruments, with USDJPY on only ONE side.
    B) ALSO reports the v1 circular number and explicitly labels it as circular
       with the algebraic identity that links the two (since the circular r is
       a monotone function of the non-circular r for this particular basket).
    C) Adds a side-panel showing what the proxy quality *really* is, and
       annotates the body caveat so no one reads v1's 0.913 without knowing
       how it arises.

Everything else (the Q-10.1 alignment analysis, Q-10.2 data-gap declaration,
seed use, code structure) is unchanged - we are only correcting the proxy
sanity check and the accompanying prose.

Output: Q-10_macro_v2.md   and   Q-10_macro_v2.json
v1 files are not touched.
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
TRADES_JSON = ROOT / "knowledge_base_backtest" / "analysis" / "unified_trades_v2_20260331.json"
HIST_DIR = ROOT / "data" / "historical_2026"
CAL_CSV = ROOT / "data" / "economic_calendar.csv"
OUT_MD = ROOT / "research" / "academic_pipeline" / "results" / "Q-10_macro_v2.md"
OUT_JSON = ROOT / "research" / "academic_pipeline" / "results" / "Q-10_macro_v2.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_ohlc(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                {
                    "time": row["time"],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                }
            )
    return rows


def index_by_date(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {r["time"]: r for r in rows}


def pearson_r(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return float("nan")
    return num / (dx * dy)


def fisher_exact_2x2(a: int, b: int, c: int, d: int) -> float:
    from math import lgamma, exp

    def log_binom(n: int, k: int) -> float:
        if k < 0 or k > n:
            return float("-inf")
        return lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1)

    n = a + b + c + d
    row1 = a + b
    col1 = a + c

    def p_table(a_val: int) -> float:
        b_val = row1 - a_val
        c_val = col1 - a_val
        d_val = n - row1 - c_val
        if min(b_val, c_val, d_val) < 0:
            return 0.0
        lp = log_binom(row1, a_val) + log_binom(n - row1, col1 - a_val) - log_binom(n, col1)
        return exp(lp)

    p_obs = p_table(a)
    total = 0.0
    a_min = max(0, col1 - (n - row1))
    a_max = min(row1, col1)
    for a_val in range(a_min, a_max + 1):
        p_i = p_table(a_val)
        if p_i <= p_obs + 1e-15:
            total += p_i
    return min(1.0, total)


def chi2_2x2(a: int, b: int, c: int, d: int) -> tuple[float, float]:
    n = a + b + c + d
    if n == 0:
        return float("nan"), float("nan")
    row1 = a + b
    row2 = c + d
    col1 = a + c
    col2 = b + d
    if min(row1, row2, col1, col2) == 0:
        return 0.0, 1.0
    expected = [
        [row1 * col1 / n, row1 * col2 / n],
        [row2 * col1 / n, row2 * col2 / n],
    ]
    observed = [[a, b], [c, d]]
    chi = 0.0
    for i in range(2):
        for j in range(2):
            e = expected[i][j]
            if e > 0:
                chi += (observed[i][j] - e) ** 2 / e
    from math import erfc, sqrt
    p = erfc(sqrt(chi / 2.0))
    return chi, p


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def load_trades() -> list[dict[str, Any]]:
    with TRADES_JSON.open("r") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Q-10.1 proxy sanity check  (v2 - non-circular)
# ---------------------------------------------------------------------------
def compute_proxy_sanity_v2() -> dict[str, Any]:
    """Compute three correlations that are RELEVANT to proxy quality:

    1. r_off = corr(USDJPY_ret, inv_GBPUSD_ret).
       **Non-circular**: both pairs are USD-base, but USDJPY does NOT appear on
       the inv-GBPUSD side. If r_off is high, two independent USD pairs move
       together - evidence that USDJPY tracks a broad USD factor (which DXY
       also captures). This is the true proxy-quality number.

    2. r_circular_v1 = corr(USDJPY_ret, 0.5 USDJPY + 0.5 inv_GBPUSD)  [reproduced for auditing].
       Mathematically this is bounded below by pearson(USDJPY, USDJPY)=1 scaled
       by the USDJPY weight's standard deviation, so r_circular_v1 >= ~0.7 by
       construction even if r_off = 0.

    3. algebraic_identity_check: verifies that r_circular_v1 is consistent with
       the closed-form expression:
           r_circular = (sd_USDJPY + r_off * sd_invGBPUSD) /
                        sqrt(sd_USDJPY^2 + 2 r_off sd_USDJPY sd_invGBPUSD + sd_invGBPUSD^2)
       This makes the circularity transparent.
    """
    usdjpy = index_by_date(load_ohlc(HIST_DIR / "USDJPY_D1.csv"))
    gbpusd = index_by_date(load_ohlc(HIST_DIR / "GBPUSD_D1.csv"))
    dates_sorted = sorted(set(usdjpy.keys()) & set(gbpusd.keys()))
    usdjpy_ret: list[float] = []
    invgu_ret: list[float] = []
    basket_ret: list[float] = []
    for i in range(1, len(dates_sorted)):
        d_prev, d_cur = dates_sorted[i - 1], dates_sorted[i]
        uj_r = (usdjpy[d_cur]["close"] - usdjpy[d_prev]["close"]) / usdjpy[d_prev]["close"]
        # GBPUSD inverse return = USD strength relative to GBP
        gu_r = (gbpusd[d_prev]["close"] - gbpusd[d_cur]["close"]) / gbpusd[d_prev]["close"]
        basket = 0.5 * uj_r + 0.5 * gu_r
        usdjpy_ret.append(uj_r)
        invgu_ret.append(gu_r)
        basket_ret.append(basket)

    # Non-circular cross-correlation (the reviewer-acceptable number)
    r_off = pearson_r(usdjpy_ret, invgu_ret)
    # Circular v1 (audit trail)
    r_circular_v1 = pearson_r(usdjpy_ret, basket_ret)
    # Algebraic consistency check on r_circular_v1
    n = len(usdjpy_ret)
    mx = sum(usdjpy_ret) / n
    my = sum(invgu_ret) / n
    sd_x = math.sqrt(sum((v - mx) ** 2 for v in usdjpy_ret) / n)
    sd_y = math.sqrt(sum((v - my) ** 2 for v in invgu_ret) / n)
    # sd of basket and identity for r(x, a*x + b*y)
    a = 0.5
    b = 0.5
    # r(x, a x + b y) = (a sd_x + b r_off sd_y) / sqrt(a^2 sd_x^2 + 2 a b r_off sd_x sd_y + b^2 sd_y^2)
    denom = math.sqrt(a * a * sd_x * sd_x + 2 * a * b * r_off * sd_x * sd_y + b * b * sd_y * sd_y)
    r_circular_predicted = (
        (a * sd_x + b * r_off * sd_y) / denom if denom > 0 else float("nan")
    )

    return {
        "n": n,
        "date_range": (dates_sorted[0], dates_sorted[-1]) if dates_sorted else None,
        "non_circular": {
            "r_usdjpy_vs_inv_gbpusd": r_off,
            "interpretation": (
                "This is the cross-correlation between two INDEPENDENT USD-base "
                "daily returns. No variable appears on both sides. This is the "
                "number that actually measures proxy quality."
            ),
        },
        "circular_v1_reproduced": {
            "r_usdjpy_vs_basket_0p5_usdjpy_0p5_invgbpusd": r_circular_v1,
            "predicted_by_identity": r_circular_predicted,
            "identity_matches": (
                abs(r_circular_v1 - r_circular_predicted) < 1e-9
                if not (math.isnan(r_circular_v1) or math.isnan(r_circular_predicted))
                else False
            ),
            "caveat": (
                "CIRCULAR. USDJPY appears on both sides of the correlation. The "
                "reported r is bounded below by the USDJPY variance share of the "
                "basket and does NOT reflect proxy quality. Reported here only for "
                "audit and to document the v1 bug."
            ),
        },
        "sd_usdjpy": sd_x,
        "sd_inv_gbpusd": sd_y,
    }


# ---------------------------------------------------------------------------
# Q-10.1 analysis (unchanged from v1 except for proxy sanity block)
# ---------------------------------------------------------------------------
def classify_usd_direction(ret: float, threshold: float = 0.001) -> str:
    if ret > threshold:
        return "USD_up"
    if ret < -threshold:
        return "USD_down"
    return "USD_flat"


def q_10_1_analysis() -> dict[str, Any]:
    trades = load_trades()
    xauusd_trades = [t for t in trades if t.get("entry_price") is not None]
    usdjpy = index_by_date(load_ohlc(HIST_DIR / "USDJPY_D1.csv"))
    usdjpy_dates_sorted = sorted(usdjpy.keys())

    def prev_trading_day(date_str: str) -> str | None:
        prev = None
        for d in usdjpy_dates_sorted:
            if d < date_str:
                prev = d
            else:
                break
        return prev

    enriched: list[dict[str, Any]] = []
    skipped = 0
    skipped_reasons: Counter[str] = Counter()
    for t in xauusd_trades:
        d = t["date"]
        pd_ = prev_trading_day(d)
        if pd_ is None:
            skipped += 1
            skipped_reasons["trade_before_USDJPY_data_start"] += 1
            continue
        idx = usdjpy_dates_sorted.index(pd_)
        if idx == 0:
            skipped += 1
            skipped_reasons["no_T-2_bar_for_return"] += 1
            continue
        pd2 = usdjpy_dates_sorted[idx - 1]
        uj_ret = (usdjpy[pd_]["close"] - usdjpy[pd2]["close"]) / usdjpy[pd2]["close"]
        cls = classify_usd_direction(uj_ret, threshold=0.001)
        enriched.append(
            {
                "trade_id": t["trade_id"],
                "date": d,
                "direction": t["direction"],
                "outcome": t["outcome"],
                "r_multiple": t.get("r_multiple"),
                "usdjpy_ret_t_minus_1": uj_ret,
                "usd_class": cls,
            }
        )

    per_class: dict[str, dict[str, Any]] = defaultdict(lambda: {"n": 0, "wins": 0, "rs": []})
    for e in enriched:
        c = per_class[e["usd_class"]]
        c["n"] += 1
        if e["outcome"] == "WIN":
            c["wins"] += 1
        if e.get("r_multiple") is not None:
            c["rs"].append(e["r_multiple"])
    for k, v in per_class.items():
        v["wr"] = v["wins"] / v["n"] if v["n"] else float("nan")
        v["avg_r"] = sum(v["rs"]) / len(v["rs"]) if v["rs"] else float("nan")

    aligned_wins = aligned_losses = mis_wins = mis_losses = flat_wins = flat_losses = 0
    for e in enriched:
        if e["usd_class"] == "USD_flat":
            if e["outcome"] == "WIN":
                flat_wins += 1
            else:
                flat_losses += 1
            continue
        is_aligned = (e["usd_class"] == "USD_up" and e["direction"] == "SHORT") or (
            e["usd_class"] == "USD_down" and e["direction"] == "LONG"
        )
        if is_aligned:
            if e["outcome"] == "WIN":
                aligned_wins += 1
            else:
                aligned_losses += 1
        else:
            if e["outcome"] == "WIN":
                mis_wins += 1
            else:
                mis_losses += 1

    fisher_p = fisher_exact_2x2(aligned_wins, aligned_losses, mis_wins, mis_losses)
    chi, chi_p = chi2_2x2(aligned_wins, aligned_losses, mis_wins, mis_losses)

    return {
        "n_trades_total": len(trades),
        "n_trades_with_usdjpy_prev": len(enriched),
        "n_skipped": skipped,
        "skipped_reasons": dict(skipped_reasons),
        "per_class": {k: dict(v) for k, v in per_class.items()},
        "alignment": {
            "aligned_wins": aligned_wins,
            "aligned_losses": aligned_losses,
            "mis_wins": mis_wins,
            "mis_losses": mis_losses,
            "flat_wins": flat_wins,
            "flat_losses": flat_losses,
            "aligned_wr": (
                aligned_wins / (aligned_wins + aligned_losses)
                if (aligned_wins + aligned_losses) > 0
                else float("nan")
            ),
            "mis_wr": (
                mis_wins / (mis_wins + mis_losses)
                if (mis_wins + mis_losses) > 0
                else float("nan")
            ),
            "fisher_exact_p": fisher_p,
            "chi2": chi,
            "chi2_p": chi_p,
        },
        "proxy_sanity_v2": compute_proxy_sanity_v2(),
        "sample": enriched[:5],
    }


# ---------------------------------------------------------------------------
# Q-10.2 (unchanged)
# ---------------------------------------------------------------------------
def load_calendar() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with CAL_CSV.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("impact", "").upper() == "HIGH":
                rows.append(row)
    return rows


def q_10_2_analysis() -> dict[str, Any]:
    trades = load_trades()
    cal = load_calendar()
    trade_dates = [t["date"] for t in trades]
    trade_min, trade_max = min(trade_dates), max(trade_dates)
    cal_dates = [row["date"] for row in cal]
    cal_min = min(cal_dates) if cal_dates else None
    cal_max = max(cal_dates) if cal_dates else None
    overlap_trades = [t for t in trades if cal_min and t["date"] >= cal_min]
    events_in_trade_window = [row for row in cal if row["date"] <= trade_max]
    result: dict[str, Any] = {
        "n_trades": len(trades),
        "trade_date_range": (trade_min, trade_max),
        "n_calendar_events_high_impact": len(cal),
        "calendar_date_range": (cal_min, cal_max),
        "n_trades_within_calendar_window": len(overlap_trades),
        "n_calendar_events_within_trade_window": len(events_in_trade_window),
    }
    if len(overlap_trades) < 5 or len(events_in_trade_window) == 0:
        result["status"] = "DATA_GAP_STOP"
        result["reason"] = (
            "Economic calendar covers "
            + f"{cal_min}..{cal_max}, trade data ends {trade_max}. "
            + f"Trades within calendar window = {len(overlap_trades)}. "
            + "Insufficient overlap to perform legitimate event-proximity analysis."
        )
        return result
    result["status"] = "PROCEEDED"
    return result


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------
def fmt(x: Any, nd: int = 3) -> str:
    if x is None:
        return "n/a"
    if isinstance(x, float):
        if math.isnan(x):
            return "nan"
        return f"{x:.{nd}f}"
    return str(x)


def render_markdown(q1: dict[str, Any], q2: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Q-10.1 / Q-10.2 - Macro Factor Re-test (v2 - circularity fix)")
    lines.append("")
    lines.append("*Analysis date: 2026-04-17*")
    lines.append("*Trade population: 111 XAUUSD batch trades, 2024-04-01 to 2026-03-13*")
    lines.append("")
    lines.append("## v2 change log")
    lines.append("")
    lines.append(
        "**Wave 1 reviewer issue (Issue 3):** The v1 proxy-sanity-check "
        "computed `corr(USDJPY, 0.5*USDJPY + 0.5*inv_GBPUSD) = 0.913`, but USDJPY "
        "appears on **both sides** of that correlation. Any non-trivial r is "
        "guaranteed by construction, so the v1 number does not measure proxy "
        "quality."
    )
    lines.append("")
    lines.append("**v2 replaces the sanity check with two separate numbers:**")
    lines.append("")
    lines.append(
        "1. `r(USDJPY, inv-GBPUSD)` - the **non-circular** cross-correlation "
        "between two independent USD-base daily-return series. This is the real "
        "proxy-quality number."
    )
    lines.append(
        "2. `r(USDJPY, 0.5*USDJPY + 0.5*inv-GBPUSD)` - reproduced from v1 and "
        "explicitly labelled as circular. Its algebraic identity to the "
        "non-circular number is also verified numerically (ensures we understand "
        "why the number is large even when proxy quality is weak)."
    )
    lines.append("")
    lines.append(
        "Everything else (Q-10.1 alignment test, Q-10.2 data-gap declaration, "
        "seed use) is unchanged from v1."
    )
    lines.append("")

    lines.append("## Hypothesis (pre-data)")
    lines.append("")
    lines.append(
        "**Q-10.1:** USD strength (USDJPY up-day T-1) should preferentially support "
        "SHORT XAUUSD trades and undermine LONG XAUUSD trades. Expected alignment "
        "WR advantage ~5-10pp. H0 = independence."
    )
    lines.append("")
    lines.append(
        "**Q-10.2:** High-impact news proximity should reduce WR in the -12h..0 "
        "window and may increase WR in the 0..+2h window. H0 = independence."
    )
    lines.append("")

    lines.append("## Data")
    lines.append("")
    lines.append(f"- Trade file: `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json` "
                 f"(n={q1['n_trades_total']}, all inferred XAUUSD from price range)")
    lines.append(f"- Historical OHLCV: `data/historical_2026/` covers 2026-01-02 to 2026-04-13 "
                 f"(NO DXY file; USDJPY used as proxy)")
    lines.append(f"- Economic calendar: `data/economic_calendar.csv`, "
                 f"n={q2['n_calendar_events_high_impact']} HIGH events, "
                 f"range {q2['calendar_date_range'][0]} to {q2['calendar_date_range'][1]}")
    lines.append("")
    lines.append("### Data gaps (unchanged from v1)")
    lines.append("")
    lines.append("1. **No DXY feed.** Q-10.1 falls back to USDJPY proxy.")
    lines.append("2. **No trade `symbol` field.** All 111 trades inferred as XAUUSD by price level.")
    lines.append("3. **Calendar/trade date mismatch.** Calendar 2026-04-01+, trades end 2026-03-13.")
    lines.append(f"4. **USDJPY proxy available window.** n with T-1 bar = "
                 f"**{q1['n_trades_with_usdjpy_prev']}** of {q1['n_trades_total']}.")
    lines.append("")

    lines.append("## Q-10.1 DXY-gold (USDJPY proxy)")
    lines.append("")
    lines.append("### Proxy quality - non-circular analysis (v2)")
    lines.append("")
    lines.append(
        "DXY is approximately 57.6% EUR, 13.6% JPY, 11.9% GBP, 9.1% CAD, 4.2% SEK, 3.6% CHF. "
        "Only USDJPY (JPY, 13.6%) and inverse-GBPUSD (GBP, 11.9%) are available in the local "
        "historical data. No EUR pair. No CAD pair. JPY+GBP together capture ~25.5% of DXY "
        "directly. Good proxy quality would show that these two USD-base pairs co-move, even "
        "without a third anchor, because both respond to broad USD factors that also drive DXY."
    )
    lines.append("")
    ps = q1["proxy_sanity_v2"]
    r_off = ps["non_circular"]["r_usdjpy_vs_inv_gbpusd"]
    lines.append("#### Non-circular cross-pair correlation")
    lines.append("")
    lines.append(
        f"- **r(USDJPY daily return, inverse-GBPUSD daily return) = {fmt(r_off)}** "
        f"(n={ps['n']} days, {ps['date_range'][0]} to {ps['date_range'][1]})."
    )
    lines.append("")
    lines.append(
        "USDJPY is on the left side only; inverse-GBPUSD is on the right side only. "
        "No shared variable. This number *does* measure proxy quality."
    )
    lines.append("")
    if not math.isnan(r_off):
        if r_off > 0.5:
            quality = "STRONG - two independent USD-base pairs move together"
        elif r_off > 0.3:
            quality = "MODERATE - shared USD factor visible but not dominant"
        elif r_off > 0.1:
            quality = "WEAK - some co-movement"
        elif r_off > -0.1:
            quality = "NEGLIGIBLE - no shared USD factor at daily frequency"
        else:
            quality = "NEGATIVE - pairs move opposite to each other"
        lines.append(f"- Proxy quality: **{quality}**.")
        lines.append("")

    lines.append("#### v1 circular number (reproduced for audit)")
    lines.append("")
    r_circ = ps["circular_v1_reproduced"]["r_usdjpy_vs_basket_0p5_usdjpy_0p5_invgbpusd"]
    r_pred = ps["circular_v1_reproduced"]["predicted_by_identity"]
    id_match = ps["circular_v1_reproduced"]["identity_matches"]
    lines.append(
        f"- `r(USDJPY, 0.5*USDJPY + 0.5*inv-GBPUSD) = {fmt(r_circ)}` (v1 number reproduced)."
    )
    lines.append(
        f"- Algebraic identity prediction from r_off above: **{fmt(r_pred)}** "
        f"(match vs observed: {id_match})."
    )
    lines.append("")
    lines.append(
        "The circular number is inflated by the USDJPY-on-both-sides construction. "
        "Even if r_off were exactly 0, the circular number would still be approximately "
        f"sd_USDJPY / sqrt(sd_USDJPY^2 + sd_invGBPUSD^2) = "
        f"{fmt(ps['sd_usdjpy'] / math.sqrt(ps['sd_usdjpy']**2 + ps['sd_inv_gbpusd']**2))} "
        "by construction. Do not interpret the circular number as a measure of proxy quality."
    )
    lines.append("")

    lines.append("### Per-class WR")
    lines.append("")
    lines.append("| USD_class (USDJPY T-1 daily return) | n | wins | WR | avg R |")
    lines.append("|---|---|---|---|---|")
    for cls in ("USD_up", "USD_down", "USD_flat"):
        v = q1["per_class"].get(cls, {"n": 0, "wins": 0, "wr": float("nan"), "avg_r": float("nan")})
        lines.append(
            f"| {cls} (ret {'>+0.1%' if cls=='USD_up' else '<-0.1%' if cls=='USD_down' else 'in [-0.1%,+0.1%]'}) "
            f"| {v['n']} | {v['wins']} | {fmt(v['wr'])} | {fmt(v['avg_r'])} |"
        )
    lines.append("")

    align = q1["alignment"]
    lines.append("### Directional alignment test")
    lines.append("")
    lines.append(
        "Aligned = (USD_up & SHORT gold) or (USD_down & LONG gold). Mis-aligned = opposite."
    )
    lines.append("")
    lines.append("| Group | wins | losses | WR |")
    lines.append("|---|---|---|---|")
    lines.append(
        f"| Aligned | {align['aligned_wins']} | {align['aligned_losses']} | {fmt(align['aligned_wr'])} |"
    )
    lines.append(
        f"| Mis-aligned | {align['mis_wins']} | {align['mis_losses']} | {fmt(align['mis_wr'])} |"
    )
    lines.append(f"| Flat (excluded) | {align['flat_wins']} | {align['flat_losses']} | - |")
    lines.append("")
    lines.append(
        f"- **Fisher's exact p = {fmt(align['fisher_exact_p'])}** "
        f"(chi^2 = {fmt(align['chi2'])}, chi^2 p = {fmt(align['chi2_p'])})."
    )
    lines.append("")
    lines.append("### Recommendation (Q-10.1)")
    lines.append("")
    n_eff = q1["n_trades_with_usdjpy_prev"]
    aligned_n = align["aligned_wins"] + align["aligned_losses"]
    mis_n = align["mis_wins"] + align["mis_losses"]
    diff_pp = (
        (align["aligned_wr"] - align["mis_wr"]) * 100
        if not (math.isnan(align["aligned_wr"]) or math.isnan(align["mis_wr"]))
        else float("nan")
    )
    if n_eff < 20 or aligned_n < 5 or mis_n < 5:
        verdict = "**DATA GAP** - sample too small for inference"
    elif align["fisher_exact_p"] < 0.05:
        verdict = "**PROMOTE to shadow test** - statistically significant alignment effect"
    elif not math.isnan(diff_pp) and abs(diff_pp) >= 10.0:
        verdict = (
            "**INCONCLUSIVE / NEEDS MORE DATA** - effect size is large (>=10pp) but sample "
            "too small to reject H0."
        )
    else:
        verdict = "**KILL** - no meaningful alignment effect at this sample size"
    # v2 adds a proxy-quality note to the verdict
    if not math.isnan(r_off) and r_off < 0.3:
        verdict += (
            " (note: v2 proxy-quality check shows USDJPY<->inv-GBPUSD cross-correlation is "
            "only ~{:.2f}; USDJPY-as-DXY is weaker than v1 implied)".format(r_off)
        )
    lines.append(
        f"- Verdict: {verdict}. Aligned WR - Misaligned WR = {fmt(diff_pp)}pp "
        f"(n_aligned={aligned_n}, n_mis={mis_n}, n_total with proxy = {n_eff})."
    )
    lines.append("")

    lines.append("## Q-10.2 Economic calendar")
    lines.append("")
    lines.append("### Calendar data coverage")
    lines.append("")
    lines.append(f"- File: `data/economic_calendar.csv`, {q2['n_calendar_events_high_impact']} HIGH-impact events.")
    lines.append(f"- Calendar date range: **{q2['calendar_date_range'][0]} to {q2['calendar_date_range'][1]}**.")
    lines.append(f"- Trade date range: {q2['trade_date_range'][0]} to {q2['trade_date_range'][1]}.")
    lines.append(f"- **Trades inside calendar window: {q2['n_trades_within_calendar_window']}**.")
    lines.append("")
    if q2.get("status") == "DATA_GAP_STOP":
        lines.append("**DATA GAP - analysis stopped before computing statistics.**")
        lines.append("")
        lines.append(q2.get("reason", ""))
        lines.append("")
    lines.append("### Recommendation (Q-10.2)")
    lines.append("")
    lines.append(
        "- Verdict: **NEEDS MORE DATA**. Acquire a back-dated ForexFactory HIGH-impact feed "
        "for 2024-04 through 2026-03."
    )
    lines.append("")

    lines.append("## Overall recommendations")
    lines.append("")
    lines.append(f"- **Q-10.1 (USD proxy):** {verdict}.")
    lines.append(
        "- **Q-10.2 (calendar):** **DATA GAP**. Do not re-kill and do not promote."
    )
    lines.append("")
    lines.append("### Data acquisitions needed")
    lines.append("")
    lines.append(
        "1. **DXY (USD Index) daily OHLCV** - a true DXY feed removes the proxy question entirely."
    )
    lines.append(
        "2. **EUR/USD daily OHLCV** - would raise the non-circular proxy to the ~70% DXY-weight level."
    )
    lines.append(
        "3. **Back-dated HIGH-impact macro calendar 2024-04 through 2026-03** - for Q-10.2."
    )
    lines.append(
        "4. **Symbol tag on trade records.**"
    )
    lines.append("")
    lines.append("## Caveats")
    lines.append("")
    lines.append(
        f"- **Q-10.1 proxy quality (v2).** Non-circular r(USDJPY, inv-GBPUSD) = {fmt(r_off)}. "
        f"This is the number to trust. JPY+GBP together are ~25.5% of DXY weight. A strong EUR "
        f"move absent in either USDJPY or GBPUSD could be missed entirely."
    )
    lines.append(
        f"- **Q-10.1 sample size.** Only {n_eff} of {q1['n_trades_total']} trades have USDJPY T-1."
    )
    lines.append(
        "- **v1 circular number.** The 0.913 reported in v1 is algebraically inflated; do not "
        "use it to argue proxy quality. See 'v1 circular number (reproduced for audit)' above."
    )
    lines.append(
        "- **Q-10.2 calendar sparsity.** 32 HIGH events forward-populated, no overlap with trades."
    )
    lines.append(
        "- **Look-ahead hygiene.** USDJPY T-1 close is knowable at open of day T; no look-ahead."
    )
    lines.append("")
    lines.append("## Next steps (unchanged from v1)")
    lines.append("")
    lines.append(
        "1. Acquire DXY D1 feed; re-run analysis with true DXY rather than USDJPY proxy."
    )
    lines.append(
        "2. Acquire back-dated calendar 2024-04..2026-03; Q-10.2 branch auto-executes."
    )
    lines.append(
        "3. If DXY Q-10.1 shows >=5pp alignment effect at p<0.05, promote to shadow."
    )
    lines.append(
        "4. If DXY Q-10.1 shows no effect at n>=60, kill the hypothesis for real."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    q1 = q_10_1_analysis()
    q2 = q_10_2_analysis()
    md = render_markdown(q1, q2)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")
    OUT_JSON.write_text(json.dumps({"q10_1": q1, "q10_2": q2}, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_JSON}")
    ps = q1["proxy_sanity_v2"]
    print("---")
    print(f"Proxy quality (v2 non-circular): r(USDJPY, inv-GBPUSD) = "
          f"{ps['non_circular']['r_usdjpy_vs_inv_gbpusd']:.4f}  (n={ps['n']})")
    print(f"v1 circular (reproduced):   r(USDJPY, basket) = "
          f"{ps['circular_v1_reproduced']['r_usdjpy_vs_basket_0p5_usdjpy_0p5_invgbpusd']:.4f}")
    print(f"Identity predicted:          {ps['circular_v1_reproduced']['predicted_by_identity']:.4f}  "
          f"(match: {ps['circular_v1_reproduced']['identity_matches']})")
    print(f"Q-10.1 alignment diff = "
          f"{(q1['alignment']['aligned_wr'] - q1['alignment']['mis_wr'])*100:+.2f}pp   "
          f"Fisher p = {q1['alignment']['fisher_exact_p']:.4f}")


if __name__ == "__main__":
    main()
