#!/usr/bin/env python3
"""F4 — can the ~10x gap between pool drift and transaction cost be closed?

F1 established: barrier-free pool drift +0.0301 R/trade against all-in cost
0.2868 R. This asks both ends of that ratio.

END 1 — COST. Cost in R is cost_price / risk_price. Decomposed by what a
        decision can actually choose: instrument, hour, order type, and the
        stop width that sets the denominator. Reports the floor reachable by
        SELECTION ALONE (no contract change) and the size of the surviving pool.

END 2 — EDGE. Uses this lane's side-flip instrument: the directional lift is
        P(real MFE >= k) - P(flipped MFE >= k) at the identical instant, and the
        barrier-free signed span return. Conditioned on hard structural cells
        (order type x family x hour x volatility state), not a ranking model.
        Reports the best cell's drift NET of its own cost.

END 3 — the MFE/|MAE| trailing-ratio cell test, out of sample: rank cells by
        TRAILING ratio, trade only ratio > 1, measure forward.

Read-only.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import pickle
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from f4_common import MONTHS, enrich, jdump, load_month  # noqa: E402

HERE = Path(__file__).parent
OUT = HERE / "receipts"
WALK = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane2")
BARS = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
            "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
MONTH_SRC = {"feb": "202602", "apr": "202604", "may": "202605",
             "jun": "202606", "jul": "202607"}
EPOCH = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
SEED = 20260812


def mins(t):
    return int((t - EPOCH).total_seconds() // 60)


def at(s):
    return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))


def load_m1_close(month):
    out = {}
    for p in sorted((BARS / f"bridge_ftmo_m1_{MONTH_SRC[month]}").glob("*_M1.csv")):
        sym = p.name[:-7]
        rows = []
        with p.open(newline="") as fh:
            for row in csv.DictReader(fh):
                rows.append((row["time"], row["close"]))
        rows = sorted(set(rows), key=lambda r: r[0])
        t = np.array([mins(at(r[0])) for r in rows], dtype=np.int64)
        keep = np.concatenate([[True], np.diff(t) > 0])
        out[sym] = dict(t=t[keep],
                        c=np.array([float(r[1]) for r, k in zip(rows, keep) if k]))
    return out


def boot(vals, n=2000, seed=SEED):
    a = np.asarray(vals, dtype=float)
    if len(a) < 20:
        return {"mean": float(a.mean()) if len(a) else None, "ci95": [None, None], "n": len(a)}
    rg = np.random.default_rng(seed)
    m = np.array([a[rg.integers(0, len(a), len(a))].mean() for _ in range(n)])
    return {"mean": float(a.mean()), "ci95": [float(np.quantile(m, .025)), float(np.quantile(m, .975))],
            "n": int(len(a)), "p_gt_0": float((m > 0).mean())}


def main():
    rows = []
    for m in MONTHS:
        rows += enrich(load_month(m))
    with gzip.open(HERE / "f4_excursion_join.pkl.gz", "rb") as f:
        exc = {r["candidate_occurrence_key"]: r for r in pickle.load(f)}
    with gzip.open(HERE / "f4_new_features.pkl.gz", "rb") as f:
        new = pickle.load(f)
    fil = []
    for r in rows:
        k = r["candidate_occurrence_key"]
        if k in exc:
            r["mfe"] = exc[k]["mfe"]
            r["mae"] = exc[k]["mae"]
            r["_new"] = new.get(k, {})
            fil.append(r)

    # ---- barrier-free signed span return, from M1 closes --------------------
    for m in MONTHS:
        S = load_m1_close(m)
        wk = {}
        with gzip.open(WALK / f"walk_{m}.pkl.gz", "rb") as f:
            for r in pickle.load(f):
                wk[r["k"]] = r
        for r in [x for x in fil if x["month"] == m]:
            w = wk.get(r["candidate_occurrence_key"])
            s = S.get(r["symbol"])
            if not w or s is None or not w.get("risk") or w.get("fp") is None:
                continue
            risk, fp, fm = float(w["risk"]), float(w["fp"]), int(w["fill_min"])
            span = mins(at(r["label_span_end_utc"])) - mins(at(r["label_span_start_utc"]))
            j = int(np.searchsorted(s["t"], fm + span, side="right")) - 1
            if j < 0 or risk <= 0:
                continue
            d = 1.0 if r["side"] == "LONG" else -1.0
            r["drift_r"] = float(d * (s["c"][j] - fp) / risk)   # barrier-free, gross of deductible
        print(f"drift {m} done", flush=True)
    fil = [r for r in fil if "drift_r" in r]
    print(f"rows with barrier-free drift: {len(fil)}")

    allin = np.array([r["cost_r"] for r in fil])
    drift = np.array([r["drift_r"] for r in fil])
    res = {"prereg_sha256": "bfe7c722c2f22d45dd8de072fb4e906352b254696a9eb61896ff53a303d68054",
           "n": len(fil),
           "pool_drift_barrier_free": boot(drift),
           "pool_all_in_cost_r": {"mean": float(allin.mean()), "median": float(np.median(allin)),
                                  "p10": float(np.quantile(allin, .1)),
                                  "p25": float(np.quantile(allin, .25)),
                                  "p75": float(np.quantile(allin, .75))},
           "ratio_cost_over_drift": float(allin.mean() / drift.mean()) if drift.mean() else None}

    # ================= END 1 — the cost floor by SELECTION ===================
    cost_cells = {}
    for keyname, keyf in (("symbol", lambda r: r["symbol"]),
                          ("order_type", lambda r: r["proposed_order_type"]),
                          ("utc_hour", lambda r: r["utc_hour"]),
                          ("family", lambda r: r["origin_family"])):
        g = defaultdict(list)
        for r in fil:
            g[keyf(r)].append(r)
        cost_cells[keyname] = {
            str(k): {"n": len(v),
                     "all_in_cost_r": float(np.mean([x["cost_r"] for x in v])),
                     "spread_r": float(np.mean([x["spread_r"] for x in v])),
                     "commission_r": float(np.mean([x["commission_r"] for x in v])),
                     "swap_r": float(np.mean([x["swap_cost_r"] for x in v])),
                     "drift_r": float(np.mean([x["drift_r"] for x in v])),
                     "net_drift_minus_cost": float(np.mean([x["drift_r"] - x["cost_r"] for x in v]))}
            for k, v in g.items() if len(v) >= 200}
    res["cost_by_cell"] = cost_cells

    # the floor reachable by selection alone: keep the cheapest q of the pool
    floor = {}
    for q in (0.05, 0.10, 0.25, 0.50):
        thr = float(np.quantile(allin, q))
        sub = [r for r in fil if r["cost_r"] <= thr]
        floor[f"cheapest_{int(q*100)}pct"] = {
            "cost_threshold_r": thr, "n": len(sub),
            "mean_cost_r": float(np.mean([r["cost_r"] for r in sub])),
            "drift": boot([r["drift_r"] for r in sub]),
            "net_drift_minus_cost": boot([r["drift_r"] - r["cost_r"] for r in sub]),
            "mean_risk_over_atr": float(np.mean([r["risk_over_atr"] for r in sub])),
            "trades_per_day": len(sub) / 100.0}
    res["cost_floor_by_selection"] = floor
    # what is cost made of, and is the denominator the lever?
    ra = np.array([r["risk_over_atr"] for r in fil])
    qs = np.quantile(ra, [0.2, 0.4, 0.6, 0.8])
    bins = np.digitize(ra, qs)
    res["cost_vs_stop_width"] = {
        f"risk_over_atr_quintile_{i+1}": {
            "n": int((bins == i).sum()),
            "mean_risk_over_atr": float(ra[bins == i].mean()),
            "all_in_cost_r": float(allin[bins == i].mean()),
            "drift_r": float(drift[bins == i].mean()),
            "net": float((drift - allin)[bins == i].mean())} for i in range(5)}

    # ================= END 2 — hard structural conditioning ==================
    def cellstats(rs):
        d = np.array([r["drift_r"] for r in rs])
        c = np.array([r["cost_r"] for r in rs])
        return {"n": len(rs), "drift": float(d.mean()), "cost": float(c.mean()),
                "net": float((d - c).mean()),
                "mfe_over_absmae": float(np.mean([r["mfe"] for r in rs]) /
                                         max(1e-9, abs(np.mean([r["mae"] for r in rs]))))}

    cells = defaultdict(list)
    for r in fil:
        vt = r["_new"].get("vol_term_d1_over_m15")
        vb = "NA" if vt is None or vt != vt else ("HI" if vt > 1.0 else "LO")
        cells[(r["proposed_order_type"], r["origin_family"], vb)].append(r)
    cand = {f"{a}|{b}|{c}": cellstats(v) for (a, b, c), v in cells.items() if len(v) >= 400}
    ranked = sorted(cand.items(), key=lambda kv: -kv[1]["net"])
    res["structural_cells"] = dict(ranked)
    res["best_structural_cells"] = dict(ranked[:8])
    best = ranked[0]
    res["best_cell_detail"] = {
        "cell": best[0], **best[1],
        "drift_boot": boot([r["drift_r"] for r in cells[tuple(best[0].split("|"))]]),
        "net_boot": boot([r["drift_r"] - r["cost_r"]
                          for r in cells[tuple(best[0].split("|"))]])}

    # ================= END 3 — trailing MFE/|MAE| cell test ==================
    # Cell = symbol x family x order_type. Rank by TRAILING ratio computed on all
    # strictly-prior months; trade only ratio > 1; measure the forward month.
    bycell = defaultdict(lambda: defaultdict(list))
    for r in fil:
        bycell[(r["symbol"], r["origin_family"], r["proposed_order_type"])][r["month"]].append(r)
    fwd_sel, fwd_all, sel_cells = [], [], []
    for f in MONTHS[1:]:
        prior = MONTHS[:MONTHS.index(f)]
        for cell, mm in bycell.items():
            past = [x for p in prior for x in mm.get(p, [])]
            fut = mm.get(f, [])
            if len(past) < 100 or len(fut) < 20:
                continue
            ratio = np.mean([x["mfe"] for x in past]) / max(1e-9, abs(np.mean([x["mae"] for x in past])))
            fwd_all += [x["drift_r"] - x["cost_r"] for x in fut]
            if ratio > 1.0:
                fwd_sel += [x["drift_r"] - x["cost_r"] for x in fut]
                sel_cells.append((f, "|".join(cell), round(float(ratio), 4), len(fut)))
    res["trailing_mfe_mae_ratio_test"] = {
        "rule": "cell = symbol x family x order_type; trade only cells whose TRAILING "
                "mean(MFE)/|mean(MAE)| > 1.0; forward month only; expanding window",
        "selected": boot(fwd_sel), "all_cells_comparator": boot(fwd_all),
        "n_cell_months_selected": len(sel_cells),
        "delta_vs_all": (float(np.mean(fwd_sel)) - float(np.mean(fwd_all))) if fwd_sel and fwd_all else None,
        "gross_drift_selected": boot([0.0]) if not fwd_sel else None,
    }
    if fwd_sel:
        res["trailing_mfe_mae_ratio_test"]["examples"] = sel_cells[:12]

    jdump(res, OUT / "F4_GAP_V1.json")

    print("\n=== END 1: COST FLOOR BY SELECTION ===")
    for k, v in floor.items():
        print(f"  {k:18s} thr={v['cost_threshold_r']:.4f} n={v['n']:6d} ({v['trades_per_day']:.0f}/day) "
              f"cost={v['mean_cost_r']:.4f} drift={v['drift']['mean']:+.4f} "
              f"net={v['net_drift_minus_cost']['mean']:+.4f} "
              f"CI[{v['net_drift_minus_cost']['ci95'][0]:+.4f},{v['net_drift_minus_cost']['ci95'][1]:+.4f}] "
              f"riskATR={v['mean_risk_over_atr']:.2f}")
    print("\n  cost vs stop width:")
    for k, v in res["cost_vs_stop_width"].items():
        print(f"    {k}: riskATR={v['mean_risk_over_atr']:.2f} cost={v['all_in_cost_r']:.4f} "
              f"drift={v['drift_r']:+.4f} net={v['net']:+.4f}")
    print("\n=== END 2: BEST STRUCTURAL CELLS (drift - cost) ===")
    for k, v in ranked[:8]:
        print(f"  {k:56s} n={v['n']:6d} drift={v['drift']:+.4f} cost={v['cost']:.4f} net={v['net']:+.4f}")
    print("  best cell boot:", res["best_cell_detail"]["net_boot"])
    print("\n=== END 3: TRAILING MFE/|MAE| RATIO ===")
    t = res["trailing_mfe_mae_ratio_test"]
    print("  selected:", t["selected"])
    print("  all     :", t["all_cells_comparator"])
    print("  delta   :", t["delta_vs_all"])


if __name__ == "__main__":
    main()
