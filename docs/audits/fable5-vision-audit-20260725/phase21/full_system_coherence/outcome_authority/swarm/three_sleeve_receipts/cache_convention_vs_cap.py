#!/usr/bin/env python3
"""Does the W7-cache MC convention describe a CAPPED book? Measured, not assumed.

Measurement only.  No live path, no config, no broker, no VPS.

WHY THIS EXISTS.  Every published `p_pass` is computed on a day series built by
`recost_w7_validation.build_matrix_from`, which reduces each sleeve to ONE value per date --
the mean of that sleeve's trades that day, times its confidence.  That is a third convention,
distinct from both arms of the cluster-envelope A/B:

  cap OFF     every (cluster, day, bar) group is a full fresh correlated unit
  cap ON      only the day's FIRST bar-group per cluster is a unit  (the live rule since
              2026-08-11T10:39Z, `book_owner.py:2066`)
  DAY-AVERAGE one unit per (cluster, day) whose R is the mean of ALL that day's members
              -- what the cache's own day matrix implies

Two consequences, and the second is the one that changes how the published figures should be
read:

  1. FOR THE THREE-SLEEVE BOOK, cluster == sleeve.  `crypto`->crypto, `energy_agri`->energy,
     `sub_xvol_pullback`->substrate are three distinct clusters, so `one_unit_per_cluster_
     per_day` and the cache's one-row-per-sleeve-per-day reduction now count the SAME number
     of units.  They did NOT for the four-sleeve book, where `sub_xvol_pullback` and
     `sub_mid_dn_revert` were both `substrate` and the cache gave them a column each.
  2. What remains is not a COUNT difference but an OUTCOME difference: the capped book takes
     the FIRST bar-group's R, the cache takes the day's AVERAGE.  This measures that residual
     directly, on the archive, so the published three-sleeve figures can be labelled
     optimistic or pessimistic rather than merely "not cap-aware".

POPULATION: the archive (`R1_ESTATE_ROWS_V2`), the only per-trade artifact with `entry_utc`.
Within-corpus A/B/C only; not comparable to a published `p_pass` level.

Usage: python3 cache_convention_vs_cap.py [out.json]
"""
from __future__ import annotations

import collections
import datetime as dt
import gzip
import json
import math
import random
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

ROWS = (REPO / "docs/audits/fable5-vision-audit-20260725/phase20/forward/receipts"
        / "R1_ESTATE_ROWS_V2.json.gz")
EXEMPT = {"jpy"}
PATHS = 40000
THREE = sorted(armed_sleeves())
FOUR = sorted(set(THREE) | {"sub_mid_dn_revert"})

mx, _e = A.resolve_market_expansion_sleeves(policy="positive_weighted12_after_swap",
                                            explicit_sleeves=())
REG = A.effective_registry(include_clean3=True, include_candidate_book=True,
                           include_market_expansion_book=True, market_expansion_sleeves=mx)
CONF = {k: float(v.confidence) for k, v in REG.items()}
D = json.load(gzip.open(ROWS))


def three_arms(rows, rkey="r_new_mid"):
    """Four day-series over the same trades.

    `day_average` is the CLUSTER-level day mean; `sleeve_day_average` is the SLEEVE-level day
    mean, which is exactly what `recost_w7_validation.build_matrix_from` builds and therefore
    exactly the convention every published `p_pass` rests on. For the three-sleeve book the
    two coincide (cluster == sleeve); for the four-sleeve book they do not, and only
    `sleeve_day_average` is the cache convention there.
    """
    byday = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        t = dt.datetime.fromisoformat(r["entry_utc"])
        cl = A.cluster_of(r["sleeve"], REG) or "__unknown__"
        byday[(cl, t.date().isoformat())][t.isoformat()].append(r)
    off, on, avg = (collections.defaultdict(float), collections.defaultdict(float),
                    collections.defaultdict(float))
    n_off = n_on = n_avg = 0
    for (cl, day), bars in byday.items():
        order = sorted(bars)
        members = [x for b in order for x in bars[b]]
        for i, b in enumerate(order):
            g = bars[b]
            u = statistics.fmean([x[rkey] for x in g]) * max(CONF.get(x["sleeve"], 0.0) for x in g)
            off[day] += u
            n_off += 1
            if i == 0 or cl in EXEMPT:
                on[day] += u
                n_on += 1
        if cl in EXEMPT:
            for b in order:
                g = bars[b]
                avg[day] += (statistics.fmean([x[rkey] for x in g])
                             * max(CONF.get(x["sleeve"], 0.0) for x in g))
                n_avg += 1
        else:
            avg[day] += (statistics.fmean([x[rkey] for x in members])
                         * max(CONF.get(x["sleeve"], 0.0) for x in members))
            n_avg += 1

    # the cache's own reduction: one row per (sleeve, date), value = day-mean x confidence
    sav = collections.defaultdict(float)
    n_sav = 0
    per_sleeve_day = collections.defaultdict(list)
    for r in rows:
        d = dt.datetime.fromisoformat(r["entry_utc"]).date().isoformat()
        per_sleeve_day[(r["sleeve"], d)].append(r[rkey])
    for (sl, d), vals in per_sleeve_day.items():
        sav[d] += statistics.fmean(vals) * CONF.get(sl, 0.0)
        n_sav += 1

    days = sorted(set(off) | set(on) | set(avg) | set(sav))
    return (days, [off.get(d, 0.0) for d in days], [on.get(d, 0.0) for d in days],
            [avg.get(d, 0.0) for d in days], [sav.get(d, 0.0) for d in days],
            dict(units_cap_off=n_off, units_cap_on=n_on, units_day_average=n_avg,
                 units_sleeve_day_average=n_sav))


def stats(s):
    return dict(n_days=len(s), mean_r_per_day=round(statistics.fmean(s), 5),
                sd=round(statistics.pstdev(s), 5), worst=round(min(s), 4))


def paired(a, b, seed=1):
    rnd = random.Random(seed)
    diff = [y - x for x, y in zip(a, b)]
    n = len(diff)
    boots = sorted(statistics.fmean([diff[rnd.randrange(n)] for _ in range(n)])
                   for _ in range(20000))
    sd = statistics.stdev(diff) if n > 1 else 0.0
    return dict(delta=round(statistics.fmean(diff), 5),
                ci95=[round(boots[500], 5), round(boots[19499], 5)],
                t=round(statistics.fmean(diff) / (sd / math.sqrt(n)), 3) if sd else None)


out = {"schema": "gtos.wave21.cache_convention_vs_cap.v1", "measurement_only": True,
       "population": "ARCHIVE (R1_ESTATE_ROWS_V2) -- within-corpus A/B/C only",
       "books": {"THREE_SLEEVE_ARMED": THREE, "FOUR_SLEEVE_PRIOR": FOUR},
       "clusters": {s: A.cluster_of(s, REG) for s in FOUR},
       "arms": {}}

for bname, book in (("THREE_SLEEVE_ARMED", THREE), ("FOUR_SLEEVE_PRIOR", FOUR)):
    rs = [r for r in D if r["sleeve"] in book]
    for wlabel, sel in (("all_years", rs),
                        ("forward_2025_plus", [r for r in rs if r["entry_utc"] >= "2025-01-01"])):
        days, so, sn, sa, sv, un = three_arms(sel)
        blk = {"units": un,
               "cap_off": stats(so), "cap_on": stats(sn), "day_average": stats(sa),
               "sleeve_day_average_THE_CACHE_CONVENTION": stats(sv),
               "cache_convention_vs_cap_on": paired(sn, sv),
               "day_average_vs_cap_on": paired(sn, sa),
               "day_average_vs_cap_off": paired(so, sa),
               "cluster_and_sleeve_day_average_coincide":
                   un["units_day_average"] == un["units_sleeve_day_average"],
               "mc": {}}
        for acct in ("FTMO", "redacted_account"):
            rule = [r for r in Q.rule_sets(acct)[0] if r.label == "P2_BOTH_PHASES"][0]
            for risk, rlabel in ((0.020, "dial_2.000pct"),):
                res = {}
                for arm, ser in (("cap_off", so), ("cap_on", sn), ("day_average", sa),
                                 ("sleeve_day_average", sv)):
                    m = Q.mc(ser, risk, rule, PATHS, seed_base=1)
                    res[arm] = {"p_pass": round(m["p_pass"], 6),
                                "p_fail_daily": round(m["p_fail_daily"], 6),
                                "p_fail_dd": round(m["p_fail_dd"], 6)}
                blk["mc"][f"{acct}|{rlabel}"] = res
        out["arms"][f"{bname}|{wlabel}"] = blk

DEST = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "CACHE_CONVENTION_VS_CAP_V1.json"
DEST.write_text(json.dumps(out, indent=1))
print("WROTE", DEST)
for k, v in out["arms"].items():
    u = v["units"]
    print(f"\n{k}  units off/on/clusterAvg/sleeveAvg = {u['units_cap_off']}/"
          f"{u['units_cap_on']}/{u['units_day_average']}/{u['units_sleeve_day_average']}  "
          f"cluster==sleeve? {v['cluster_and_sleeve_day_average_coincide']}")
    print(f"  R/day  cap_off {v['cap_off']['mean_r_per_day']:+.5f}  "
          f"cap_on {v['cap_on']['mean_r_per_day']:+.5f}  "
          f"CACHE(sleeve-day avg) {v['sleeve_day_average_THE_CACHE_CONVENTION']['mean_r_per_day']:+.5f}")
    c = v["cache_convention_vs_cap_on"]
    print(f"  CACHE - cap_on = {c['delta']:+.5f} CI95 {c['ci95']}  t={c['t']}")
    for a, r in v["mc"].items():
        print(f"    {a:26s} p_pass off {r['cap_off']['p_pass']:.4f} | on "
              f"{r['cap_on']['p_pass']:.4f} | CACHE {r['sleeve_day_average']['p_pass']:.4f}")
