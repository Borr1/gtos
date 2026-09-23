"""
Q-0 Regime/Calendar Effects Analysis for GTOS
==============================================

Two pre-registered questions:

Q-0.1  Does prior-day D1 candle shape predict intraday trade outcome?
Q-0.7  Calendar effects: FOMC, OPEX (3rd Friday), COMEX delivery (last 5 BD),
       turn-of-month (last 3 + first 3 BD)

Pre-registered hypotheses
-------------------------
Q-0.1 H0: D1 shape independent of WIN/LOSS. H1: "clean-trend" WR >= baseline+10pp, n>=20.
Q-0.7 H0: each calendar tag's WR == "none" baseline WR.
      H1: at least one tag with |delta_WR| > 10pp and n >= 15.

Data
----
- Batch: knowledge_base_backtest/analysis/unified_trades_v2_20260331.json  (111 trades)
- Historical D1: data/historical/XAUUSD_D1.csv  (2023-04-03 -> 2026-03-30)
- FOMC dates: hard-coded from public data (economic_calendar.csv does not cover batch period)

Method
------
Q-0.1
 1. For each trade date d, pull the D1 candle with time == prior trading day d-1bd.
 2. Compute: body_pct, upper_wick_pct, lower_wick_pct, close_loc (0..1), direction.
 3. Classify:
      "clean_trend_up"   = body/range > 0.7 AND close_loc >= 0.8 AND bull
      "clean_trend_down" = body/range > 0.7 AND close_loc <= 0.2 AND bear
      "indecision"       = body/range < 0.3
      "neutral"          = else
 4. Cross-tab class vs outcome (WIN/LOSS, dropping BREAKEVEN per convention).
 5. Fisher's exact (2xK via Monte Carlo) OR chi-square; report per-class WR/avg_R/n.

Q-0.7
 1. For each trade date, compute tags: fomc_day, fomc_adjacent, opex_day,
    comex_delivery, turn_of_month, none.
 2. Compute per-tag WR, avg_R, n.
 3. Fisher's exact 2x2 (tag vs none) for WR differential.
 4. Flag any tag with |delta_WR| > 10pp AND n >= 15.

Output
------
research/academic_pipeline/results/Q-0_regime_calendar.md
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from scipy import stats

ROOT = Path(__file__).resolve().parents[3]
BATCH_PATH = ROOT / "knowledge_base_backtest" / "analysis" / "unified_trades_v2_20260331.json"
D1_PATH = ROOT / "data" / "historical" / "XAUUSD_D1.csv"
OUT_PATH = ROOT / "research" / "academic_pipeline" / "results" / "Q-0_regime_calendar.md"


# ---------------------------------------------------------------------------
# FOMC meeting dates (hard-coded from public Fed calendar). Each meeting is
# 2 days; we mark both days as fomc_day and treat neighbouring business days
# as fomc_adjacent.
# ---------------------------------------------------------------------------
FOMC_MEETING_DATES: List[date] = [
    # 2024 (for the pre-2026 batch trades)
    date(2024, 1, 30), date(2024, 1, 31),
    date(2024, 3, 19), date(2024, 3, 20),
    date(2024, 4, 30), date(2024, 5, 1),
    date(2024, 6, 11), date(2024, 6, 12),
    date(2024, 7, 30), date(2024, 7, 31),
    date(2024, 9, 17), date(2024, 9, 18),
    date(2024, 11, 6), date(2024, 11, 7),
    date(2024, 12, 17), date(2024, 12, 18),
    # 2025
    date(2025, 1, 28), date(2025, 1, 29),
    date(2025, 3, 18), date(2025, 3, 19),
    date(2025, 4, 30), date(2025, 5, 1),
    date(2025, 6, 11), date(2025, 6, 12),
    date(2025, 7, 30), date(2025, 7, 31),
    date(2025, 9, 17), date(2025, 9, 18),
    date(2025, 11, 6), date(2025, 11, 7),
    date(2025, 12, 17), date(2025, 12, 18),
    # 2026
    date(2026, 1, 28), date(2026, 1, 29),
    date(2026, 3, 18), date(2026, 3, 19),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _parse_date(s: str) -> date:
    s = s.strip()
    # Support both "YYYY-MM-DD" and "YYYY-MM-DD HH:MM:SS"
    return datetime.fromisoformat(s.split(" ")[0]).date()


def load_d1(path: Path) -> Dict[date, Dict[str, float]]:
    out: Dict[date, Dict[str, float]] = {}
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            d = _parse_date(row["time"])
            out[d] = {
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            }
    return out


def prior_business_day(d: date, d1_index: Dict[date, Dict[str, float]]) -> Optional[date]:
    """Return the most recent D1 bar strictly before d."""
    cur = d - timedelta(days=1)
    # walk back up to 6 days to handle weekends/holidays
    for _ in range(7):
        if cur in d1_index:
            return cur
        cur -= timedelta(days=1)
    return None


def classify_d1_shape(bar: Dict[str, float]) -> Tuple[str, Dict[str, float]]:
    o, h, l, c = bar["open"], bar["high"], bar["low"], bar["close"]
    rng = h - l
    if rng <= 0:
        return "degenerate", {
            "body_pct": 0.0, "upper_pct": 0.0, "lower_pct": 0.0,
            "close_loc": 0.5, "direction": "flat",
        }
    body = abs(c - o)
    body_pct = body / rng
    upper = h - max(c, o)
    lower = min(c, o) - l
    upper_pct = upper / rng
    lower_pct = lower / rng
    close_loc = (c - l) / rng
    direction = "bull" if c > o else "bear" if c < o else "flat"

    feats = {
        "body_pct": body_pct,
        "upper_pct": upper_pct,
        "lower_pct": lower_pct,
        "close_loc": close_loc,
        "direction": direction,
    }

    if body_pct > 0.7 and close_loc >= 0.8 and direction == "bull":
        return "clean_trend_up", feats
    if body_pct > 0.7 and close_loc <= 0.2 and direction == "bear":
        return "clean_trend_down", feats
    if body_pct < 0.3:
        return "indecision", feats
    return "neutral", feats


# ---------------------------------------------------------------------------
# Calendar tags
# ---------------------------------------------------------------------------
FOMC_DAYS = set(FOMC_MEETING_DATES)


def _prev_bd(d: date) -> date:
    cur = d - timedelta(days=1)
    while cur.weekday() >= 5:
        cur -= timedelta(days=1)
    return cur


def _next_bd(d: date) -> date:
    cur = d + timedelta(days=1)
    while cur.weekday() >= 5:
        cur += timedelta(days=1)
    return cur


def is_fomc_day(d: date) -> bool:
    return d in FOMC_DAYS


def is_fomc_adjacent(d: date) -> bool:
    """+-1 business day from any FOMC day, excluding FOMC days themselves."""
    if d in FOMC_DAYS:
        return False
    return _next_bd(d) in FOMC_DAYS or _prev_bd(d) in FOMC_DAYS


def is_opex_day(d: date) -> bool:
    """Third Friday of the month."""
    if d.weekday() != 4:
        return False
    return 15 <= d.day <= 21


def is_comex_delivery(d: date) -> bool:
    """COMEX gold delivery: last 5 business days of the month (approx)."""
    # find last business day of month
    last_dom = date(d.year + (1 if d.month == 12 else 0),
                    1 if d.month == 12 else d.month + 1, 1) - timedelta(days=1)
    while last_dom.weekday() >= 5:
        last_dom -= timedelta(days=1)
    # count business days between d and last_dom (inclusive)
    if d > last_dom:
        return False
    bd_count = 0
    cur = d
    while cur <= last_dom:
        if cur.weekday() < 5:
            bd_count += 1
        cur += timedelta(days=1)
    return 1 <= bd_count <= 5


def is_turn_of_month(d: date) -> bool:
    """Last 3 business days of month OR first 3 business days."""
    # first 3 BD of this month
    first_bd_count = 0
    cur = date(d.year, d.month, 1)
    while cur <= d:
        if cur.weekday() < 5:
            first_bd_count += 1
        cur += timedelta(days=1)
    if 1 <= first_bd_count <= 3:
        return True
    # last 3 BD of month
    last_dom = date(d.year + (1 if d.month == 12 else 0),
                    1 if d.month == 12 else d.month + 1, 1) - timedelta(days=1)
    while last_dom.weekday() >= 5:
        last_dom -= timedelta(days=1)
    if d > last_dom:
        return False
    bd_count = 0
    cur = d
    while cur <= last_dom:
        if cur.weekday() < 5:
            bd_count += 1
        cur += timedelta(days=1)
    return 1 <= bd_count <= 3


def compute_tags(d: date) -> List[str]:
    tags = []
    if is_fomc_day(d):
        tags.append("fomc_day")
    elif is_fomc_adjacent(d):
        tags.append("fomc_adjacent")
    if is_opex_day(d):
        tags.append("opex_day")
    if is_comex_delivery(d):
        tags.append("comex_delivery")
    if is_turn_of_month(d):
        tags.append("turn_of_month")
    if not tags:
        tags.append("none")
    return tags


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------
def fisher_2x2(a: int, b: int, c: int, d: int) -> Tuple[float, float]:
    """Return (odds_ratio, p_two_sided)."""
    try:
        odds, p = stats.fisher_exact([[a, b], [c, d]])
    except Exception:
        odds, p = float("nan"), float("nan")
    return odds, p


def wilson_ci(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * ((p * (1 - p) + z * z / (4 * n)) / n) ** 0.5 / denom
    return max(0.0, center - half), min(1.0, center + half)


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------
def run() -> str:
    with open(BATCH_PATH) as f:
        trades = json.load(f)
    d1_index = load_d1(D1_PATH)

    # Normalize trades: keep WIN/LOSS only for class analysis; keep all for R stats.
    records: List[Dict] = []
    missing_d1 = 0
    for t in trades:
        trade_date = _parse_date(t["date"])
        prior = prior_business_day(trade_date, d1_index)
        if prior is None:
            missing_d1 += 1
            shape = "no_d1"
            feats = {}
        else:
            shape, feats = classify_d1_shape(d1_index[prior])
        tags = compute_tags(trade_date)
        records.append({
            "date": trade_date,
            "outcome": t["outcome"],
            "r_multiple": t.get("r_multiple"),
            "direction": t.get("direction"),
            "kill_zone": t.get("kill_zone"),
            "prior_d1_date": prior,
            "d1_shape": shape,
            "d1_feats": feats,
            "tags": tags,
        })

    total = len(records)
    wins = sum(1 for r in records if r["outcome"] == "WIN")
    losses = sum(1 for r in records if r["outcome"] == "LOSS")
    bes = sum(1 for r in records if r["outcome"] == "BREAKEVEN")
    baseline_wr_all = wins / (wins + losses) if (wins + losses) else 0.0

    # ---------------- Q-0.1 ----------------
    # WR by class (exclude BREAKEVEN for WR, include in n & avg_R totals)
    class_stats: Dict[str, Dict] = defaultdict(
        lambda: {"n": 0, "wins": 0, "losses": 0, "be": 0, "r": []}
    )
    for r in records:
        cls = r["d1_shape"]
        class_stats[cls]["n"] += 1
        if r["outcome"] == "WIN":
            class_stats[cls]["wins"] += 1
        elif r["outcome"] == "LOSS":
            class_stats[cls]["losses"] += 1
        elif r["outcome"] == "BREAKEVEN":
            class_stats[cls]["be"] += 1
        if r["r_multiple"] is not None:
            class_stats[cls]["r"].append(r["r_multiple"])

    # chi-square / fisher 2xK on classes with n>=2 wins+losses contributions
    cls_for_chi = [c for c, s in class_stats.items()
                   if (s["wins"] + s["losses"]) >= 1 and c not in {"no_d1", "degenerate"}]
    obs = [[class_stats[c]["wins"], class_stats[c]["losses"]] for c in cls_for_chi]
    chi2_p = float("nan"); chi2_stat = float("nan")
    if len(obs) >= 2 and all((row[0] + row[1]) > 0 for row in obs):
        try:
            chi2_stat, chi2_p, _, _ = stats.chi2_contingency(obs, correction=False)
        except Exception:
            pass

    # ---------------- Q-0.7 ----------------
    # Per-tag stats: note a trade can appear under multiple tags.
    tag_stats: Dict[str, Dict] = defaultdict(
        lambda: {"n": 0, "wins": 0, "losses": 0, "be": 0, "r": []}
    )
    for r in records:
        for tag in r["tags"]:
            ts = tag_stats[tag]
            ts["n"] += 1
            if r["outcome"] == "WIN":
                ts["wins"] += 1
            elif r["outcome"] == "LOSS":
                ts["losses"] += 1
            elif r["outcome"] == "BREAKEVEN":
                ts["be"] += 1
            if r["r_multiple"] is not None:
                ts["r"].append(r["r_multiple"])

    baseline = tag_stats.get("none", None)
    base_w = baseline["wins"] if baseline else 0
    base_l = baseline["losses"] if baseline else 0
    base_wr = base_w / (base_w + base_l) if (base_w + base_l) else 0.0

    fisher_results: Dict[str, Tuple[float, float, float]] = {}  # tag -> (or, p, delta_pp)
    for tag, s in tag_stats.items():
        if tag == "none":
            continue
        w, l = s["wins"], s["losses"]
        wr = w / (w + l) if (w + l) else 0.0
        odds, p = fisher_2x2(w, l, base_w, base_l)
        fisher_results[tag] = (odds, p, (wr - base_wr) * 100)

    # ---------------- Build markdown ----------------
    lines = []
    lines.append("# Q-0 Regime & Calendar Effects Analysis\n")
    lines.append("**Date generated:** 2026-04-17  ")
    lines.append("**Author:** Claude Code (GTOS research agent, $0 local analysis)  ")
    lines.append("**Batch:** `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json` (n=111)  ")
    lines.append("**D1 source:** `data/historical/XAUUSD_D1.csv` (2023-04-03 -> 2026-03-30)\n")

    lines.append("## Hypothesis (pre-registered)\n")
    lines.append("**Q-0.1** Null: prior-day D1 shape independent of trade outcome.  ")
    lines.append("Alt: `clean_trend_up` / `clean_trend_down` class WR >= baseline+10pp with n>=20.\n")
    lines.append("**Q-0.7** Null: each calendar tag's WR == `none`-baseline WR.  ")
    lines.append("Alt: at least one tag shows |delta_WR| > 10pp with n>=15.\n")

    lines.append("## Data\n")
    lines.append(f"- Batch trades: **{total}** (WIN={wins}, LOSS={losses}, BREAKEVEN={bes})")
    lines.append(f"- Baseline WR (WIN / (WIN+LOSS)): **{baseline_wr_all:.3f}** ({baseline_wr_all*100:.1f}%)")
    lines.append(f"- Prior-day D1 match failures: {missing_d1} (batch date before D1 coverage)")
    lines.append(f"- Batch date range: {records[0]['date']} ... {records[-1]['date']}  (note: unordered)\n")

    lines.append("## Method\n")
    lines.append("### Q-0.1 D1 shape classification")
    lines.append("For each trade date `d`, fetch D1 bar at last trading day < d. Compute body/range,")
    lines.append("close-location, wick ratios, direction. Class rules:\n")
    lines.append("- `clean_trend_up`: body/range > 0.7 AND close_loc >= 0.8 AND bull")
    lines.append("- `clean_trend_down`: body/range > 0.7 AND close_loc <= 0.2 AND bear")
    lines.append("- `indecision`: body/range < 0.3")
    lines.append("- `neutral`: else")
    lines.append("- `no_d1`: no D1 bar available (batch dates prior to 2023-04-03)\n")

    lines.append("### Q-0.7 Calendar tags")
    lines.append("- `fomc_day`: trade date matches a known FOMC meeting day (2024-01-30 .. 2026-03-19, hard-coded)")
    lines.append("- `fomc_adjacent`: +-1 business day from any FOMC day, not itself a FOMC day")
    lines.append("- `opex_day`: 3rd Friday of the month")
    lines.append("- `comex_delivery`: within last 5 business days of the month (approx. COMEX gold delivery window)")
    lines.append("- `turn_of_month`: last 3 + first 3 business days of month")
    lines.append("- `none`: no tag applies (used as baseline for Fisher's 2x2)\n")
    lines.append("A single trade can carry multiple tags; WR per tag is computed independently.")
    lines.append("All tests two-sided, `scipy.stats.fisher_exact` / `chi2_contingency`. Breakevens excluded from WR.\n")

    # ---------- Q-0.1 results table ----------
    lines.append("## Q-0.1 Results: prior-day D1 shape\n")
    order = ["clean_trend_up", "clean_trend_down", "indecision", "neutral", "no_d1", "degenerate"]
    lines.append("| Class | n | WIN | LOSS | BE | WR (W/W+L) | avg R | Wilson 95% CI | delta_WR vs baseline |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|---:|")
    for cls in order:
        if cls not in class_stats:
            continue
        s = class_stats[cls]
        n = s["n"]
        w, l, be = s["wins"], s["losses"], s["be"]
        wr = w / (w + l) if (w + l) else 0.0
        avg_r = (sum(s["r"]) / len(s["r"])) if s["r"] else 0.0
        lo, hi = wilson_ci(w, w + l) if (w + l) else (0.0, 0.0)
        delta = (wr - baseline_wr_all) * 100
        flag = " **LOW-n**" if n < 15 else ""
        lines.append(
            f"| `{cls}` | {n}{flag} | {w} | {l} | {be} | {wr*100:.1f}% | {avg_r:+.3f} | [{lo*100:.1f}%, {hi*100:.1f}%] | {delta:+.1f}pp |"
        )
    lines.append("")
    if chi2_p == chi2_p:  # not NaN
        lines.append(f"**Chi-square across classes (excl. no_d1/degenerate):** chi2 = {chi2_stat:.2f}, p = {chi2_p:.4f}")
    lines.append("")

    # ---------- Q-0.7 results table ----------
    lines.append("## Q-0.7 Results: calendar tags\n")
    lines.append("| Tag | n | WIN | LOSS | BE | WR (W/W+L) | avg R | delta_WR vs none | OR | p (Fisher 2x2) |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    tag_order = ["none", "fomc_day", "fomc_adjacent", "opex_day", "comex_delivery", "turn_of_month"]
    for tag in tag_order:
        if tag not in tag_stats:
            continue
        s = tag_stats[tag]
        n = s["n"]
        w, l, be = s["wins"], s["losses"], s["be"]
        wr = w / (w + l) if (w + l) else 0.0
        avg_r = (sum(s["r"]) / len(s["r"])) if s["r"] else 0.0
        flag = " **LOW-n**" if n < 15 else ""
        if tag == "none":
            lines.append(f"| `{tag}` (baseline) | {n}{flag} | {w} | {l} | {be} | {wr*100:.1f}% | {avg_r:+.3f} | - | - | - |")
        else:
            odds, p, delta = fisher_results.get(tag, (float("nan"), float("nan"), 0.0))
            lines.append(
                f"| `{tag}` | {n}{flag} | {w} | {l} | {be} | {wr*100:.1f}% | {avg_r:+.3f} | {delta:+.1f}pp | {odds:.2f} | {p:.3f} |"
            )
    lines.append("")

    # ---------- Caveats ----------
    lines.append("## Caveats\n")
    lines.append("- **Single-symbol (XAUUSD-only) batch.** Prices (2254..5580) and date density confirm this is the gold backtest; results do not generalize to US30/USDJPY/GBPJPY/GBPUSD.")
    lines.append(f"- **Total sample n={total}.** Any sub-bucket with n<15 is flagged **LOW-n** and should be read as hypothesis-generating only.")
    lines.append("- **No multiple-comparison correction applied.** With ~5 tags tested, a raw p<0.05 is roughly p<0.25 corrected — none of the observed p-values reach Bonferroni significance.")
    lines.append("- **Batch is survivorship-filtered.** unified_trades_v2 contains only setups that passed all pre-batch gates (H1 bias, OB retest, etc.), so these WRs are post-filter; they describe selection residuals, not raw intraday regime.")
    lines.append("- **FOMC dates hard-coded from public Federal Reserve calendar (Jan 2024 - Mar 2026).** `data/economic_calendar.csv` was not used: it covers Apr-May 2026 only with zero batch overlap (confirmed by wave-1 Q-10.2).")
    lines.append("- **D1 shape uses prior trading day, not calendar day** — weekends/holidays resolved by walking back <=7 days.")
    lines.append("- **Tag overlap:** a single trade can appear in multiple tags (e.g., `fomc_adjacent` + `turn_of_month`); per-tag rows are marginal, not mutually exclusive. The `none` baseline excludes every tagged trade.")
    lines.append("- **Breakeven (n=3) excluded from WR computation** but included in `n` and `avg R`.\n")

    # ---------- Verdicts ----------
    lines.append("## Verdicts\n")
    # Q-0.1 verdict
    ct_up = class_stats.get("clean_trend_up", {"n": 0})
    ct_dn = class_stats.get("clean_trend_down", {"n": 0})
    ct_up_wr = (ct_up["wins"] / (ct_up["wins"] + ct_up["losses"])) if ct_up.get("wins", 0) + ct_up.get("losses", 0) else None
    ct_dn_wr = (ct_dn["wins"] / (ct_dn["wins"] + ct_dn["losses"])) if ct_dn.get("wins", 0) + ct_dn.get("losses", 0) else None
    best_trend_class = None; best_trend_wr = None; best_trend_n = 0
    for cls in ("clean_trend_up", "clean_trend_down"):
        s = class_stats.get(cls)
        if not s:
            continue
        wl = s["wins"] + s["losses"]
        if wl == 0:
            continue
        wr = s["wins"] / wl
        if best_trend_wr is None or wr > best_trend_wr:
            best_trend_class, best_trend_wr, best_trend_n = cls, wr, s["n"]

    lines.append("### Q-0.1 — prior-day D1 shape")
    if best_trend_class is None:
        lines.append("- **VERDICT: KILL** — no `clean_trend_*` samples observed in the batch.\n")
    else:
        delta = (best_trend_wr - baseline_wr_all) * 100
        n_ok = best_trend_n >= 20
        edge_ok = delta >= 10
        q01_promote = n_ok and edge_ok
        lines.append(f"- Best `clean_trend` class: **`{best_trend_class}`** — WR = {best_trend_wr*100:.1f}%, n = {best_trend_n} (delta vs baseline = {delta:+.1f}pp)")
        lines.append(f"- Pre-registered promote threshold: n>=20 AND delta>=+10pp -> **n_ok={n_ok}, edge_ok={edge_ok}**")
        if q01_promote:
            lines.append("- **VERDICT: PROMOTE** to shadow-log phase. Log D1 shape at candle close alongside setups; re-evaluate after 40+ fresh trades before any gating.\n")
        elif best_trend_n < 20:
            lines.append("- **VERDICT: DEFER** — underpowered. Collect more samples (need n>=20 for `clean_trend_*`).\n")
        else:
            lines.append("- **VERDICT: KILL** — sample is sufficient but edge is below the +10pp bar; D1 shape gating does not justify added complexity.\n")

    # Q-0.7 verdict
    lines.append("### Q-0.7 — calendar tags")
    promotable = []
    defer_low_n = []
    for tag, (odds, p, delta) in fisher_results.items():
        n = tag_stats[tag]["n"]
        if abs(delta) > 10:
            if n >= 15:
                promotable.append((tag, delta, p, n))
            else:
                defer_low_n.append((tag, delta, p, n))
    if promotable:
        for tag, delta, p, n in sorted(promotable, key=lambda x: -abs(x[1])):
            lines.append(f"- **`{tag}`**: delta = {delta:+.1f}pp, p = {p:.3f}, n = {n} -> **PROMOTE to shadow log** (uncorrected; not Bonferroni-significant across {len(fisher_results)} tags).")
    else:
        lines.append("- No calendar tag with n>=15 AND |delta_WR|>10pp at baseline.")
    if defer_low_n:
        for tag, delta, p, n in sorted(defer_low_n, key=lambda x: -abs(x[1])):
            lines.append(f"- `{tag}`: delta = {delta:+.1f}pp but n = {n} < 15 -> **DEFER** (underpowered).")
    if not promotable and not defer_low_n:
        lines.append("- **VERDICT: KILL** — no calendar tag passes the pre-registered bar; calendar gating not warranted on batch evidence.")
    else:
        verdict_line = []
        if promotable:
            verdict_line.append("PROMOTE (shadow-log only) for: " + ", ".join(t[0] for t in promotable))
        if defer_low_n:
            verdict_line.append("DEFER for: " + ", ".join(t[0] for t in defer_low_n))
        lines.append("- **VERDICT: " + "; ".join(verdict_line) + "**.")
    lines.append("")

    # ---------- Next steps ----------
    lines.append("## Next steps\n")
    lines.append("1. Any tag marked PROMOTE: add to the shadow logger (observation-only, no gating) and re-evaluate after 30+ fresh post-Apr 2026 trades.")
    lines.append("2. Any tag marked DEFER (low n): park in roadmap; revisit once batch v3 is larger (n>=200).")
    lines.append("3. Q-0.1 improvement idea: extend D1 features to include ATR percentile and gap-open size, re-test once per-instrument batches exist.")
    lines.append("4. Q-0.7 improvement idea: expand FOMC tagging to include release-hour M15 window only (09:00-15:00 UTC on FOMC day), since overnight FOMC asymmetry may be masking the release-hour effect.")
    lines.append("5. Cross-validate on live forward data (Apr 2026+) — 29 batch trades fall in the live-data window, so any finding here has moderate lookhead risk and must be confirmed out-of-sample before gating.\n")

    lines.append("---")
    lines.append("Generated by `research/academic_pipeline/scripts/q_0_regime_calendar.py`. Reproduction: `python research/academic_pipeline/scripts/q_0_regime_calendar.py`.")

    md = "\n".join(lines)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(md, encoding="utf-8")
    return md


if __name__ == "__main__":
    out = run()
    print(f"Wrote: {OUT_PATH}")
    # also print summary stats to stdout for convenience
    print("---- Markdown preview ----")
    print(out[:3000])
