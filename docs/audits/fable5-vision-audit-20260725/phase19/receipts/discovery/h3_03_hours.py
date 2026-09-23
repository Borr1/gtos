"""h3-03 -- SESSION AND HOUR. What does trading only the cheapest hours save, and cost?

The tick archive carries a per-symbol median quoted spread FOR EVERY HOUR
(`spread_bps_median_by_broker_hour`, 263.9 M ticks). Nothing in this estate has ever used
it -- every published cost number, including the 2.457 bps headline, charges one flat
per-symbol median to every hour of the day.

Mapping is validated independently inside this script: the hour at which the spread peaks
must be the daily rollover, i.e. NY 17:00 = broker midnight. It is, on every FX pair.

Two frontiers are produced and they are NOT the same object:
  EX-ANTE   hours ranked by mean toll only. Cost is knowable before the trade, so this
            ranking uses no outcome information and can be run live.
  IN-SAMPLE hours ranked by realised net. Reported for the ceiling only; it is selection
            on the answer and is labelled as such everywhere.
"""
import json
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h3_lib as H  # noqa: E402

COL = "K5_TRAIL025"
rows = H.load_atmkt()
H.add_hour_cost(rows)
nohour = [r for r in rows if r.get("cost_true_hour") is None]
rows = [r for r in rows if r.get("cost_true_hour") is not None]

out = {"lane": "h3", "step": "hours", "contract": COL, "n": len(rows),
       "n_no_hour_profile": len(nohour)}

# ---------------------------------------------------------------- 0. mapping validation
val = {}
for s in sorted({r["symbol"] for r in rows}):
    p = H._profile(s)
    if not p:
        continue
    tk = H.TICK["ftmo:" + H.e_lib.TMAP.get(s, s)]
    hi = max(p.items(), key=lambda kv: kv[1]["bps"])
    val[s] = {"flat_bps": tk["spread_bps_median"], "peak_ny_hour": hi[0],
              "peak_bps": hi[1]["bps"], "peak_over_flat": hi[1]["bps"] / tk["spread_bps_median"],
              "hours_measured": len(p)}
out["hour_profile_validation"] = val
out["peak_at_ny17_count"] = sum(1 for v in val.values() if v["peak_ny_hour"] == 17)
out["symbols_with_profile"] = len(val)

# ---------------------------------------------------------- 1. flat vs hour-aware level
flat = H.summarize(rows, COL, "cost_true", "flat per-symbol median spread")
hourly = H.summarize(rows, COL, "cost_true_hour", "hour-aware spread")
out["flat_vs_hour_aware"] = {"flat": flat, "hour_aware": hourly,
                             "toll_bps_delta": hourly["toll_bps"] - flat["toll_bps"],
                             "toll_bps_ratio": hourly["toll_bps"] / flat["toll_bps"]}

# robustness: the naive (broker-3) mapping used elsewhere in the estate
rows_n = H.add_hour_cost([dict(r) for r in rows], naive=True)
out["naive_utc_mapping_arm"] = H.summarize(rows_n, COL, "cost_true_hour", "naive broker-3")


# ------------------------------------------------------------------ 2. the hour tables
def table(rows, keyf, name):
    acc = {}
    for r in rows:
        acc.setdefault(keyf(r), []).append(r)
    t = []
    for k, rs in sorted(acc.items()):
        d = H.summarize(rs, COL, "cost_true_hour", str(k))
        d["key"] = k
        d["share_of_opportunities"] = len(rs) / len(rows)
        d["toll_bps_flat"] = H.mean([x["cost_true"] * x["rdp"] * 1e4 for x in rs])
        d["spread_bps_quoted"] = H.mean([x["spread_bps_hour"] for x in rs])
        t.append(d)
    return {"axis": name, "cells": t}


out["by_ny_hour"] = table(rows, lambda r: r["ny_hour"], "ny_hour")
out["by_utc_hour"] = table(rows, lambda r: r["utc_hour"], "utc_hour")
out["by_session"] = table(rows, lambda r: r.get("session") or "none", "route_session")
out["by_dow"] = table(rows, lambda r: r["dow"], "day_of_week")


# ---------------------------------------------------------------- 3. the FRONTIERS
def frontier(rows, keyf, rank_by, name, per_month_check=True):
    acc = {}
    for r in rows:
        acc.setdefault(keyf(r), []).append(r)
    stats = {}
    for k, rs in acc.items():
        g, t, n, keep = H.scored(rs, COL, "cost_true_hour")
        stats[k] = {"n": len(g), "edge_bps": H.mean(g), "toll_bps": H.mean(t),
                    "net_bps": H.mean(n),
                    "net_r": H.mean([x[COL] - x["cost_true_hour"] for x in keep])}
    order = sorted(stats, key=lambda k: (stats[k][rank_by] if rank_by != "toll_bps"
                                         else stats[k]["toll_bps"]),
                   reverse=(rank_by != "toll_bps"))
    kept, fr = [], []
    ntot = len(rows)
    for k in order:
        kept.append(k)
        sub = [r for r in rows if keyf(r) in set(kept)]
        d = H.summarize(sub, COL, "cost_true_hour", ",".join(map(str, kept)))
        d["cells_kept"] = len(kept)
        d["last_added"] = k
        d["keep_rate"] = len(sub) / ntot
        d["net_bps_per_opportunity"] = d["net_bps"] * d["keep_rate"]
        d["net_r_per_opportunity"] = d["net_r"] * d["keep_rate"]
        d["kept"] = list(kept)
        if per_month_check:
            d["by_month"] = {m: H.summarize([r for r in sub if r["month"] == m], COL,
                                            "cost_true_hour", m)
                             for m in sorted(H.MONTHS)}
        fr.append(d)
    return {"axis": name, "ranked_by": rank_by, "cell_stats": stats, "frontier": fr}


out["frontier_ny_hour_exante_cost"] = frontier(rows, lambda r: r["ny_hour"], "toll_bps",
                                               "ny_hour cheapest-first (EX ANTE)")
out["frontier_ny_hour_insample_net"] = frontier(rows, lambda r: r["ny_hour"], "net_bps",
                                                "ny_hour best-net-first (IN SAMPLE)")

# ------------------------------------------- 4. stability of the ex-ante hour ranking
per_m = {}
for m in sorted(H.MONTHS):
    sub = [r for r in rows if r["month"] == m]
    acc = {}
    for r in sub:
        acc.setdefault(r["ny_hour"], []).append(r)
    per_m[m] = {k: H.mean([x["cost_true_hour"] * x["rdp"] * 1e4 for x in rs])
                for k, rs in acc.items()}
out["toll_bps_by_hour_by_month"] = per_m
common = set.intersection(*[set(v) for v in per_m.values()])
ranks = {m: {k: i for i, k in enumerate(sorted(common, key=lambda k: per_m[m][k]))}
         for m in per_m}
mm = sorted(H.MONTHS)
import itertools  # noqa: E402


def spearman(a, b):
    ks = sorted(set(a) & set(b))
    ra = {k: i for i, k in enumerate(sorted(ks, key=lambda k: a[k]))}
    rb = {k: i for i, k in enumerate(sorted(ks, key=lambda k: b[k]))}
    n = len(ks)
    d2 = sum((ra[k] - rb[k]) ** 2 for k in ks)
    return 1 - 6 * d2 / (n * (n * n - 1)) if n > 1 else None


out["hour_cost_rank_spearman_between_months"] = {
    f"{a}|{b}": spearman(per_m[a], per_m[b]) for a, b in itertools.combinations(mm, 2)}

p = H.dump(out, "H3_HOURS_V1.json")
print("n=%d  no_profile=%d  symbols_with_profile=%d  peak_at_NY17=%d"
      % (out["n"], out["n_no_hour_profile"], out["symbols_with_profile"],
         out["peak_at_ny17_count"]))
print("FLAT      toll=%.4f bps edge=%.4f net=%.4f" % (flat["toll_bps"], flat["edge_bps"], flat["net_bps"]))
print("HOURAWARE toll=%.4f bps edge=%.4f net=%.4f  (ratio %.4f)"
      % (hourly["toll_bps"], hourly["edge_bps"], hourly["net_bps"],
         out["flat_vs_hour_aware"]["toll_bps_ratio"]))
print("NAIVE-UTC toll=%.4f bps" % out["naive_utc_mapping_arm"]["toll_bps"])
print("\nEX-ANTE cheapest-hour frontier (NY hour):")
print("%3s %5s %7s %9s %9s %9s %7s %11s" % ("k", "add", "keep", "edge", "toll", "net", "e/t", "net/opp"))
for d in out["frontier_ny_hour_exante_cost"]["frontier"]:
    print("%3d %5s %6.3f %9.4f %9.4f %9.4f %7.3f %11.5f"
          % (d["cells_kept"], d["last_added"], d["keep_rate"], d["edge_bps"], d["toll_bps"],
             d["net_bps"], d["edge_over_toll"], d["net_bps_per_opportunity"]))
print("->", p)
