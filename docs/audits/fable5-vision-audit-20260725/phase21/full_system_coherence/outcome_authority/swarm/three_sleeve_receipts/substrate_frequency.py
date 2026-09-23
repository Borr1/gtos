#!/usr/bin/env python3
"""The frequency interaction: who won the single substrate unit, and what the pull costs.

Measurement only.  No live path, no config, no broker, no VPS.

WHY.  `sub_mid_dn_revert` carried 398 of the four armed sleeves' 754 W7-cache trades (52.8 %)
and 20 of FTMO's 42 armed symbol slots -- so the naive reading of its removal is "the book
loses half its trades".  That reading is wrong in BOTH directions and the direction is not
obvious a priori:

  * `sub_mid_dn_revert` and `sub_xvol_pullback` share the `substrate` cluster, and under the
    restored `one_unit_per_cluster_per_day` envelope only the day's FIRST substrate bar-group
    becomes a correlated unit.  Every trade the pulled sleeve took on a LATER bar of a day
    `sub_xvol_pullback` had already opened was already being suppressed -- removing it costs
    nothing there.
  * But every day where `sub_mid_dn_revert` fired FIRST, it was the sleeve that CONSUMED the
    substrate unit -- so its removal hands that slot to `sub_xvol_pullback` where the latter
    also fired, and loses the day entirely where it did not.

This measures the head-to-head directly, then converts it into the quantity that drives
time-to-payout: correlated units and book-days per calendar month.

POPULATIONS -- two, deliberately, because neither alone answers it:
  ARCHIVE  `phase20/forward/receipts/R1_ESTATE_ROWS_V2.json.gz` -- the ONLY per-trade
           artifact with an `entry_utc`, so it is the only one that can resolve WHICH SLEEVE
           FIRED FIRST inside a day.  22,354 trades.
  W7 CACHE `recost_w7_validation.build([])` -- the population every published `p_pass` is
           computed on.  It carries a DATE but no bar index, so it can answer "how many
           book-days" but NOT "who was first".  Stated, not worked around.

Usage: python3 substrate_frequency.py [out.json]
"""
from __future__ import annotations

import collections
import datetime as dt
import gzip
import json
import math
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[8]
for p in (REPO, REPO / "scripts"):
    sys.path.insert(0, str(p))

from src.components.ultimate_book import admission as A     # noqa: E402
from src.safety.armed_set import armed_sleeves              # noqa: E402
import mc_firm_rules as Q                                   # noqa: E402
import recost_w7_validation as M                            # noqa: E402

ROWS = (REPO / "docs/audits/fable5-vision-audit-20260725/phase20/forward/receipts"
        / "R1_ESTATE_ROWS_V2.json.gz")
EXEMPT = {"jpy"}
PULLED = "sub_mid_dn_revert"
THREE = sorted(armed_sleeves())
FOUR = sorted(set(THREE) | {PULLED})

mx, _e = A.resolve_market_expansion_sleeves(policy="positive_weighted12_after_swap",
                                            explicit_sleeves=())
REG = A.effective_registry(include_clean3=True, include_candidate_book=True,
                           include_market_expansion_book=True, market_expansion_sleeves=mx)
CONF = {k: float(v.confidence) for k, v in REG.items()}
CLUSTER = {s: A.cluster_of(s, REG) for s in FOUR}

D = json.load(gzip.open(ROWS))


def wilson(k, n, z=1.96):
    """Wilson score interval -- the honest interval for a share on a small count."""
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def head_to_head(rows, window_label):
    """Who won the single substrate unit, day by day, on the archive."""
    sub = [r for r in rows if CLUSTER.get(r["sleeve"]) == "substrate"]
    byday = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in sub:
        t = dt.datetime.fromisoformat(r["entry_utc"])
        byday[t.date().isoformat()][t.isoformat()].append(r)

    cnt = collections.Counter()
    pulled_first_days, xvol_first_days = [], []
    for day, bars in byday.items():
        order = sorted(bars)
        first = bars[order[0]]
        names = {x["sleeve"] for x in sub_of(byday, day)}
        first_names = {x["sleeve"] for x in first}
        both = ("sub_xvol_pullback" in names) and (PULLED in names)
        if both:
            cnt["days_both_sleeves_fired"] += 1
            if first_names == {PULLED}:
                cnt["contested_won_by_pulled"] += 1
            elif first_names == {"sub_xvol_pullback"}:
                cnt["contested_won_by_survivor"] += 1
            else:
                cnt["contested_first_bar_is_shared"] += 1
        elif PULLED in names:
            cnt["days_only_pulled_fired"] += 1
        else:
            cnt["days_only_survivor_fired"] += 1
        if first_names == {PULLED}:
            pulled_first_days.append(day)
        if "sub_xvol_pullback" in first_names:
            xvol_first_days.append(day)

    n_days = len(byday)
    ex = cnt["days_only_pulled_fired"]
    lo, hi = wilson(ex, n_days)
    return {
        "window": window_label,
        "substrate_trades": len(sub),
        "substrate_cluster_days": n_days,
        **dict(cnt),
        "share_of_substrate_days_lost_outright_pct": round(100.0 * ex / max(1, n_days), 2),
        "share_lost_outright_wilson95_pct": [round(100 * lo, 2) if lo is not None else None,
                                             round(100 * hi, 2) if hi is not None else None],
        "days_the_pulled_sleeve_consumed_the_unit": len(pulled_first_days),
        "note": ("`contested_won_by_pulled` days are NOT lost -- under the cap the survivor "
                 "inherits the unit that day. Only `days_only_pulled_fired` is an outright "
                 "loss of a substrate unit."),
    }


def sub_of(byday, day):
    out = []
    for bar in byday[day].values():
        out.extend(bar)
    return out


def unit_counts(rows, book):
    """Correlated units per month, cap OFF and cap ON, for one book."""
    rs = [r for r in rows if r["sleeve"] in book]
    byday = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rs:
        t = dt.datetime.fromisoformat(r["entry_utc"])
        byday[(A.cluster_of(r["sleeve"], REG) or "?", t.date().isoformat())][t.isoformat()].append(r)
    off = on = 0
    days_off, days_on = set(), set()
    for (cl, day), bars in byday.items():
        order = sorted(bars)
        off += len(order)
        days_off.add(day)
        on += 1 if cl not in EXEMPT else len(order)
        days_on.add(day)
    if not days_off:
        return None
    ds = sorted(days_off)
    a = dt.date.fromisoformat(ds[0])
    b = dt.date.fromisoformat(ds[-1])
    months = (b.year - a.year) * 12 + (b.month - a.month) + 1
    return dict(trades=len(rs), span_months=months,
                units_cap_off=off, units_cap_on=on,
                units_per_month_cap_off=round(off / months, 3),
                units_per_month_cap_on=round(on / months, 3),
                trading_days=len(days_off),
                trading_days_per_month=round(len(days_off) / months, 3),
                first_day=ds[0], last_day=ds[-1])


def cache_bookdays():
    """W7 cache: book-days and per-month rate for both books, both accounts."""
    st = M.build([])
    rows = st["rows"]
    for r in rows:
        r["R_legacy"] = r["R"]
    _, _, _, sd_book = M.build_matrix_from(rows, "R_legacy")
    out = {}
    for bname, keep in (("THREE_SLEEVE_ARMED", THREE), ("FOUR_SLEEVE_PRIOR", FOUR)):
        cm = {k: statistics.median(v) for k, v in Q._priced_pool(rows, "FTMO").items()}
        sub = [r for r in rows if r["sleeve"] in keep]
        days, comb, risk, _ = Q.series(sub, "FTMO", cm, "max", sd_book, forward=True,
                                       kelly=Q.KELLY_HALF, risk_basis=Q.RISK_LIVE_NOMINAL)
        a, b = min(days), max(days)
        months = (b.year - a.year) * 12 + (b.month - a.month) + 1
        # days on which EACH sleeve contributes a non-zero daily value
        per_sleeve_days = {}
        for sl in keep:
            s2 = [r for r in rows if r["sleeve"] == sl]
            d2 = sorted({r["date"] for r in s2 if getattr(r["date"], "year", 0) >= 2025})
            per_sleeve_days[sl] = len(d2)
        out[bname] = dict(trades=len(sub), book_days=len(days),
                          book_days_per_month=round(len(days) / months, 3),
                          span_months=months,
                          mean_r_per_book_day=round(statistics.fmean(comb), 5),
                          per_sleeve_forward_days=per_sleeve_days)
    return out


armed_all = [r for r in D if r["sleeve"] in FOUR]
armed_fwd = [r for r in armed_all if r["entry_utc"] >= "2025-01-01"]

out = {
    "schema": "gtos.wave21.substrate_frequency.v1",
    "measurement_only": True,
    "pulled_sleeve": PULLED,
    "books": {"THREE_SLEEVE_ARMED": THREE, "FOUR_SLEEVE_PRIOR": FOUR},
    "clusters": CLUSTER,
    "confidences": {s: CONF.get(s) for s in FOUR},
    "archive_head_to_head": {
        "all_years": head_to_head(armed_all, "all_years"),
        "forward_2025_plus": head_to_head(armed_fwd, "forward_2025_plus"),
    },
    "archive_unit_frequency": {
        "all_years": {b: unit_counts(armed_all, k)
                      for b, k in (("THREE_SLEEVE_ARMED", THREE), ("FOUR_SLEEVE_PRIOR", FOUR))},
        "forward_2025_plus": {b: unit_counts(armed_fwd, k)
                              for b, k in (("THREE_SLEEVE_ARMED", THREE),
                                           ("FOUR_SLEEVE_PRIOR", FOUR))},
    },
    "w7_cache_book_days": cache_bookdays(),
    "cache_limitation": ("the W7 cache carries a DATE but no bar index and no decision "
                         "timestamp, so it cannot resolve which sleeve fired first inside a "
                         "day; the head-to-head is archive-only and is labelled as such"),
}

# ---- the derived answer -------------------------------------------------------------
for w in ("all_years", "forward_2025_plus"):
    h = out["archive_head_to_head"][w]
    u3 = out["archive_unit_frequency"][w]["THREE_SLEEVE_ARMED"]
    u4 = out["archive_unit_frequency"][w]["FOUR_SLEEVE_PRIOR"]
    trade_share = 100.0 * (u4["trades"] - u3["trades"]) / max(1, u4["trades"])
    unit_off = 100.0 * (u4["units_cap_off"] - u3["units_cap_off"]) / max(1, u4["units_cap_off"])
    unit_on = 100.0 * (u4["units_cap_on"] - u3["units_cap_on"]) / max(1, u4["units_cap_on"])
    day_share = 100.0 * (u4["trading_days"] - u3["trading_days"]) / max(1, u4["trading_days"])
    out.setdefault("verdict", {})[w] = dict(
        pct_of_trades_removed=round(trade_share, 2),
        pct_of_units_removed_cap_OFF=round(unit_off, 2),
        pct_of_units_removed_cap_ON=round(unit_on, 2),
        pct_of_trading_days_removed=round(day_share, 2),
        amplification_trades_over_units_cap_on=(round(trade_share / unit_on, 2)
                                                if unit_on else None),
        substrate_days_lost_outright_pct=h["share_of_substrate_days_lost_outright_pct"],
        substrate_days_lost_outright_wilson95_pct=h["share_lost_outright_wilson95_pct"],
    )

DEST = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "SUBSTRATE_FREQUENCY_V1.json"
DEST.write_text(json.dumps(out, indent=1))
print("WROTE", DEST)
print(json.dumps(out["archive_head_to_head"], indent=1))
print(json.dumps(out["archive_unit_frequency"], indent=1))
print(json.dumps(out["w7_cache_book_days"], indent=1))
print(json.dumps(out["verdict"], indent=1))
