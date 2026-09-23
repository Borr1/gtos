"""m2_final — build the two committed receipts from the walked rows."""
from __future__ import annotations
import datetime as dt
import glob
import json
from collections import defaultdict
import numpy as np

OUT = ("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/"
       "docs/audits/fable5-vision-audit-20260725/phase20/receipts/m2")


def dayblock_ci(vals, days, draws=4000, seed=101):
    rng = np.random.default_rng(seed)
    by = defaultdict(list)
    for v, d in zip(vals, days):
        by[d].append(float(v))
    keys = list(by)
    sums = np.array([np.sum(by[k]) for k in keys])
    cnts = np.array([len(by[k]) for k in keys])
    idx = rng.integers(0, len(keys), size=(draws, len(keys)))
    m = sums[idx].sum(1) / cnts[idx].sum(1)
    return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))], float((m <= 0).mean())


def cell(sel, key, days=None, ci=True):
    v = np.array([r[key] for r in sel if r.get(key) is not None], dtype=float)
    if not len(v):
        return None
    o = {"n": int(len(v)), "mean": float(v.mean())}
    if ci and days is not None:
        d = [dd for r, dd in zip(sel, days) if r.get(key) is not None]
        o["ci95"], o["p_le_0"] = dayblock_ci(v, d)
    return o


def block(rows, tag, arms, keys, extra_bins=True):
    out = {"n_rows": len(rows)}
    grid = {}
    for k in keys:
        sel = [r for r in rows if all(r.get(f"{a}_{k}") is not None for a in arms)]
        if not sel:
            continue
        days = [r["day"] for r in sel]
        c = {"n": len(sel)}
        for a in arms:
            c[a] = cell(sel, f"{a}_{k}", days, ci=a in ("bar", "tbid", "fill", "lvl", "mir"))
        dd = np.array([r[f"fill_{k}"] - r[f"tbid_{k}"] for r in sel])
        ci, p = dayblock_ci(dd, days)
        c["delta_fill_minus_tbid"] = {"mean": float(dd.mean()), "ci95": ci, "p_le_0": p}
        sig = np.array([r[f"fill_{k}"] - r[f"mir_{k}"] for r in sel
                        if r.get(f"mir_{k}") is not None])
        sd = [r["day"] for r in sel if r.get(f"mir_{k}") is not None]
        if len(sig):
            ci, p = dayblock_ci(sig, sd)
            c["signal_vs_mirror_tick"] = {"mean": float(sig.mean()), "ci95": ci,
                                          "p_le_0": p, "n": int(len(sig))}
        sigb = np.array([r[f"tbid_{k}"] - r[f"mirbar_{k}"] for r in sel
                         if r.get(f"mirbar_{k}") is not None])
        sdb = [r["day"] for r in sel if r.get(f"mirbar_{k}") is not None]
        if len(sigb):
            ci, p = dayblock_ci(sigb, sdb)
            c["signal_vs_mirror_bidtape"] = {"mean": float(sigb.mean()), "ci95": ci,
                                             "p_le_0": p, "n": int(len(sigb))}
        grid[k] = c
    out["grid"] = grid
    return out


# ============================================================ FROZEN ROSTER COHORT
froz = []
for p in sorted(glob.glob("/tmp/m2/walks/*.json")):
    froz.extend(json.load(open(p))["rows"])
KEYS = ["1.5_120", "1.5_240", "1.5_1440", "2_120", "2_240", "2_1440"]
ARMS = ["bar", "tbid", "lvl", "fill", "mir", "mirbar"]
F = block(froz, "frozen", ARMS, KEYS)
K, K2 = "1.5_120", "2_240"

# per instrument / per window / per quintile
def slices(rows, keyfn, name, k1, k2):
    o = {}
    for kk, sub in sorted(defaultdict(list, {v: [r for r in rows if keyfn(r) == v]
                                             for v in {keyfn(r) for r in rows}}).items()):
        sub = [r for r in sub if r.get(f"bar_{k1}") is not None and r.get(f"fill_{k1}") is not None]
        if not sub:
            continue
        days = [r["day"] for r in sub]
        e = {"n": len(sub),
             "median_d_bps": float(np.median([r["d_bps"] for r in sub])),
             "median_spread_bps": float(np.median([r["spread_bps"] for r in sub])),
             "median_spread_over_d": float(np.median([r["spread_over_d"] for r in sub])),
             "long_frac": float(np.mean([r["long"] for r in sub]))}
        for a in ("bar", "tbid", "fill", "lvl", "mir"):
            e[a] = cell(sub, f"{a}_{k1}", days, ci=(a == "fill"))
            e[a + "_2R"] = cell(sub, f"{a}_{k2}", None, ci=False)
        o[str(kk)] = e
    return o


F["per_instrument"] = slices(froz, lambda r: r["sym"], "sym", K, K2)
F["per_window"] = slices(froz, lambda r: r["mm"], "mm", K, K2)

sel = [r for r in froz if r.get(f"bar_{K}") is not None]
db = np.array([r["d_bps"] for r in sel])
qs = np.percentile(db, [20, 40, 60, 80])
for r, q in zip(sel, np.searchsorted(qs, db, side="right")):
    r["_q"] = f"Q{int(q)+1}"
F["risk_distance_quintiles"] = slices(sel, lambda r: r["_q"], "q", K, K2)

names = {0: "stop", 1: "target", 2: "path_end"}
mig = defaultdict(int)
for r in froz:
    if r.get(f"barcode_{K}") is not None and r.get(f"code_{K}") is not None:
        mig[f"{names[r[f'barcode_{K}']]}->{names[r[f'code_{K}']]}"] += 1
F["exit_migration_barM1_to_tickfill"] = dict(sorted(mig.items()))

# intrabar-ordering control
sel = [r for r in froz if r.get(f"bar_{K2}") is not None and r.get(f"tbid_{K2}") is not None]
dd = np.array([r[f"bar_{K2}"] - r[f"tbid_{K2}"] for r in sel])
F["intrabar_ordering_M1_vs_tick"] = {
    "n": len(dd), "mean_bar_minus_tickbid": float(dd.mean()),
    "frac_rows_identical": float((np.abs(dd) < 1e-9).mean())}

F["join_control"] = {
    "n": len(froz),
    "bid_prev_tick_equals_roster_entry_frac": float(np.mean([r["join_exact"] for r in froz])),
    "what": "the M15 archive close == the last tick BID strictly before the decision "
            "instant; a wrong clock, a wrong symbol map or a MID/ASK tape all fail it",
}

# accumulation, three units, coverage-matched
for tag, pre in (("transacted", "cap_"), ("bid_tape", "capg_"), ("mid", "capm_")):
    full = [r for r in froz if all(r.get(pre + h) is not None
                                   for h in ("2h", "8h", "24h", "72h", "160h", "320h"))]
    acc = {}
    for hh in ("15m", "2h", "8h", "24h", "72h", "160h", "320h"):
        v = np.array([r[pre + hh] for r in full if r.get(pre + hh) is not None])
        acc[hh] = {"n": int(len(v)), "mean_bps": float(v.mean()) if len(v) else None}
    F[f"accumulation_{tag}"] = {"n_matched": len(full), "ladder": acc}
F["median_spread_bps"] = float(np.median([r["spread_bps"] for r in froz]))

# ============================================================ NEVER-READ OOS COHORT
oos, meta = [], {}
for p in sorted(glob.glob("/tmp/m2/oos/*.json")):
    d = json.load(open(p))
    meta[d["symbol"]] = {k: d[k] for k in ("status", "tick_name", "bid_identity_n",
                                           "bid_identity_frac", "n_ticks",
                                           "tick_first_utc", "tick_last_utc")}
    oos.extend(d["rows"])
O = block(oos, "oos", ARMS, KEYS)
O["meta"] = meta
O["per_instrument"] = slices(oos, lambda r: r["sym"], "sym", K, K2)


def isoweek(d):
    y, m, dd = (int(x) for x in d.split("-"))
    return "W%02d" % dt.date(y, m, dd).isocalendar()[1]


O["per_week"] = slices(oos, lambda r: isoweek(r["day"]), "wk", K, K2)
sel = [r for r in oos if r.get(f"bar_{K}") is not None]
db = np.array([r["d_bps"] for r in sel])
qs = np.percentile(db, [20, 40, 60, 80])
for r, q in zip(sel, np.searchsorted(qs, db, side="right")):
    r["_q"] = f"Q{int(q)+1}"
O["risk_distance_quintiles"] = slices(sel, lambda r: r["_q"], "q", K, K2)
mig = defaultdict(int)
for r in oos:
    if r.get(f"tbidcode_{K}") is not None and r.get(f"code_{K}") is not None:
        mig[f"{names[r[f'tbidcode_{K}']]}->{names[r[f'code_{K}']]}"] += 1
O["exit_migration_tickbid_to_tickfill"] = dict(sorted(mig.items()))
for tag, pre in (("transacted", "cap_"), ("bid_tape", "capg_"), ("mid", "capm_")):
    full = [r for r in oos if all(r.get(pre + h) is not None
                                  for h in ("2h", "8h", "24h", "72h", "160h", "320h"))]
    acc = {}
    for hh in ("15m", "2h", "8h", "24h", "72h", "160h", "320h"):
        v = np.array([r[pre + hh] for r in full if r.get(pre + hh) is not None])
        acc[hh] = {"n": int(len(v)), "mean_bps": float(v.mean()) if len(v) else None}
    O[f"accumulation_{tag}"] = {"n_matched": len(full), "ladder": acc}
O["median_spread_bps"] = float(np.median([r["spread_bps"] for r in oos]))

# ============================================================ THE BREAK-EVEN IN s/d
allr = [dict(r, _pop="frozen") for r in froz] + [dict(r, _pop="oos") for r in oos]
sel = [r for r in allr if r.get(f"fill_{K}") is not None]
edges = [0.0, 0.02, 0.04, 0.06, 0.08, 0.12, 0.18, 0.25, 0.35, 0.50, 0.75, 99.0]
be = []
for a, b in zip(edges[:-1], edges[1:]):
    sub = [r for r in sel if a <= r["spread_over_d"] < b]
    if len(sub) < 30:
        continue
    days = [r["day"] for r in sub]
    v = np.array([r[f"fill_{K}"] for r in sub])
    ci, p = dayblock_ci(v, days)
    be.append({"s_over_d_lo": a, "s_over_d_hi": b, "n": len(sub),
               "median_s_over_d": float(np.median([r["spread_over_d"] for r in sub])),
               "median_d_bps": float(np.median([r["d_bps"] for r in sub])),
               "tick_true_fill": float(v.mean()), "ci95": ci, "p_le_0": p,
               "bar_bid_tape": float(np.mean([r[f"tbid_{K}"] for r in sub
                                              if r.get(f"tbid_{K}") is not None]))})
BE = {"what": "tick-true R/trade by spread-over-risk, both tick cohorts pooled, "
              "shipped 1.5R target / 120 min horizon",
      "n": len(sel), "bins": be}

json.dump({"cohort": "frozen wave-19 roster, 4 tick-covered instruments x 7 windows "
                     "(2025-10..2026-04), lane-hold true-UTC bid/ask ticks", **F},
          open(OUT + "/M2_TICK_FROZEN_V1.json", "w"), indent=1)
json.dump({"cohort": "NEVER-READ 2026-06-18..07-24, 24 instruments, vps-ticks-20260726 "
                     "bid/ask, vps-bars-20260727 M15, broker clock -> true UTC", **O},
          open(OUT + "/M2_TICK_OOS_V1.json", "w"), indent=1)
json.dump(BE, open(OUT + "/M2_BREAKEVEN_V1.json", "w"), indent=1)
print("frozen n", F["n_rows"], "oos n", O["n_rows"])
for lbl, X in (("FROZEN", F), ("OOS", O)):
    g = X["grid"]
    print(f"--- {lbl}")
    for k, c in g.items():
        print(f"  {k:9s} n={c['n']:5d} bar {c['bar']['mean']:+.5f} tbid {c['tbid']['mean']:+.5f} "
              f"lvl {c['lvl']['mean']:+.5f} fill {c['fill']['mean']:+.5f} "
              f"mirror {c['mir']['mean']:+.5f} signal(tick) {c['signal_vs_mirror_tick']['mean']:+.5f} "
              f"p {c['fill']['p_le_0']:.4f}")
print("--- BREAK-EVEN")
for b in be:
    print(f"  s/d [{b['s_over_d_lo']:.2f},{b['s_over_d_hi']:.2f}) n={b['n']:5d} "
          f"med_s/d {b['median_s_over_d']:.4f} med_d_bps {b['median_d_bps']:7.2f} "
          f"bidtape {b['bar_bid_tape']:+.5f} tick {b['tick_true_fill']:+.5f} "
          f"ci [{b['ci95'][0]:+.4f},{b['ci95'][1]:+.4f}]")
