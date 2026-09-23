"""r2_analyse — arm economics, gap_r bands and the stale-age table, from one walk."""
from __future__ import annotations

import collections
import glob
import gzip
import json
import math
import sys

import numpy as np

RR = 1.5
POI = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}
WINDOWS = ["2025-10", "2025-11", "2025-12", "2026-01",
           "2026-02", "2026-03", "2026-04", "2026-05"]


def load():
    rows = []
    for w in WINDOWS:
        for line in gzip.open(f"/tmp/r2/econ/REC_{w}.jsonl.gz", "rt"):
            rows.append(json.loads(line))
    return rows


def stats(sel):
    if not sel:
        return None
    g = np.array([r["g"] for r in sel])
    c = np.array([r["c"] for r in sel])
    net = g - c
    n = len(sel)
    se = float(net.std(ddof=1) / math.sqrt(n)) if n > 1 else float("nan")
    fills = sum(1 for r in sel if r["fill"])
    return {
        "n": n,
        "gross_per_emission": float(g.mean()),
        "cost_per_emission": float(c.mean()),
        "net_per_emission": float(net.mean()),
        "net_se": se,
        "net_ci95": [float(net.mean() - 1.96 * se), float(net.mean() + 1.96 * se)],
        "net_total": float(net.sum()),
        "fills": fills,
        "fill_rate": fills / n,
        "net_per_fill": float(net.sum() / fills) if fills else None,
    }


# ---- the arm filters, exactly as the code gates them -----------------------
def keep(r, *, refuse_past_stop, max_gap_r, max_age_periods, min_gap_r=None):
    if max_age_periods is not None and r["age"] >= 15 * max_age_periods:
        return False
    if r["f"] in POI:
        if refuse_past_stop and r["gap"] < -1.0:
            return False
        if min_gap_r is not None and r["gap"] < min_gap_r:
            return False
        if max_gap_r is not None and r["gap"] >= max_gap_r:
            return False
    return True


ARMS = {
    "legacy":        dict(refuse_past_stop=False, max_gap_r=None, max_age_periods=None),
    "stale_only":    dict(refuse_past_stop=False, max_gap_r=None, max_age_periods=1.0),
    "paststop_only": dict(refuse_past_stop=True,  max_gap_r=None, max_age_periods=None),
    "default":       dict(refuse_past_stop=True,  max_gap_r=None, max_age_periods=1.0),
    "gapr_1p5":      dict(refuse_past_stop=True,  max_gap_r=1.5,  max_age_periods=1.0),
    "gapr_3":        dict(refuse_past_stop=True,  max_gap_r=3.0,  max_age_periods=1.0),
    "gapr_5":        dict(refuse_past_stop=True,  max_gap_r=5.0,  max_age_periods=1.0),
    "gapr_10":       dict(refuse_past_stop=True,  max_gap_r=10.0, max_age_periods=1.0),
    "min0":          dict(refuse_past_stop=True,  max_gap_r=None, max_age_periods=1.0,
                          min_gap_r=0.0),
    "band_0_to_rr":  dict(refuse_past_stop=True,  max_gap_r=1.5,  max_age_periods=1.0,
                          min_gap_r=0.0),
}


def main(out_path):
    rows = load()
    out = {"n_rows_walked": len(rows), "rr": RR, "windows": WINDOWS, "arms": {},
           "arms_by_family": {}, "gap_bands": {}, "age_table": {}, "per_window": {}}

    for name, cfg in ARMS.items():
        sel = [r for r in rows if keep(r, **cfg)]
        out["arms"][name] = {**stats(sel), "policy": cfg,
                             "kept_share": len(sel) / len(rows)}
        fam = {}
        for f in sorted({r["f"] for r in rows}):
            fs = [r for r in sel if r["f"] == f]
            fam[f] = stats(fs)
        out["arms_by_family"][name] = fam
        pw = {}
        for w in WINDOWS:
            pw[w] = stats([r for r in sel if r["w"] == w])
        out["per_window"][name] = pw

    # ---- fine gap_r bands over POI rows only (the object the far-side dial cuts)
    poi = [r for r in rows if r["f"] in POI]
    edges = [-math.inf, -1.0, 0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 7.5,
             10.0, 15.0, 25.0, math.inf]
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = [r for r in poi if lo <= r["gap"] < hi]
        if sel:
            out["gap_bands"][f"[{lo},{hi})"] = stats(sel)
    out["gap_bands_by_family"] = {}
    for f in sorted(POI):
        d = {}
        fr = [r for r in poi if r["f"] == f]
        for lo, hi in zip(edges[:-1], edges[1:]):
            sel = [r for r in fr if lo <= r["gap"] < hi]
            if sel:
                d[f"[{lo},{hi})"] = stats(sel)
        out["gap_bands_by_family"][f] = d

    # ---- staleness economics
    for lab, pred in (("age==0", lambda r: r["age"] == 0),
                      ("age>0", lambda r: r["age"] > 0),
                      ("0<age<=15", lambda r: 0 < r["age"] <= 15),
                      ("15<age<=60", lambda r: 15 < r["age"] <= 60),
                      ("60<age<=240", lambda r: 60 < r["age"] <= 240),
                      ("age>240", lambda r: r["age"] > 240)):
        out["age_table"][lab] = {
            "all": stats([r for r in rows if pred(r)]),
            "at_market": stats([r for r in rows if pred(r) and r["f"] not in POI]),
            "poi": stats([r for r in rows if pred(r) and r["f"] in POI]),
        }

    json.dump(out, open(out_path, "w"), indent=1)

    print(f"{'arm':16s} {'n':>9s} {'kept%':>7s} {'gross':>10s} {'cost':>9s} "
          f"{'NET/emis':>10s} {'ci95lo':>9s} {'ci95hi':>9s} {'fill%':>7s} {'net/fill':>9s}")
    for k, v in out["arms"].items():
        print(f"{k:16s} {v['n']:9d} {100*v['kept_share']:7.3f} {v['gross_per_emission']:10.5f} "
              f"{v['cost_per_emission']:9.5f} {v['net_per_emission']:10.5f} "
              f"{v['net_ci95'][0]:9.5f} {v['net_ci95'][1]:9.5f} "
              f"{100*v['fill_rate']:7.3f} {(v['net_per_fill'] or 0):9.5f}")
    print()
    print("POI gap_r bands (pooled):")
    print(f"{'band':16s} {'n':>9s} {'gross':>10s} {'cost':>9s} {'net':>10s} {'fill%':>7s}")
    for k, v in out["gap_bands"].items():
        print(f"{k:16s} {v['n']:9d} {v['gross_per_emission']:10.5f} {v['cost_per_emission']:9.5f} "
              f"{v['net_per_emission']:10.5f} {100*v['fill_rate']:7.3f}")
    print()
    print("age table (net/emission):")
    for k, v in out["age_table"].items():
        a, am, p = v["all"], v["at_market"], v["poi"]
        print(f"  {k:14s} all n={a['n']:8d} net={a['net_per_emission']:+9.5f} | "
              f"at_market n={(am or {}).get('n',0):7d} net={(am or {}).get('net_per_emission',float('nan')):+9.5f} | "
              f"poi n={(p or {}).get('n',0):8d} net={(p or {}).get('net_per_emission',float('nan')):+9.5f}")


if __name__ == "__main__":
    main(sys.argv[1])
