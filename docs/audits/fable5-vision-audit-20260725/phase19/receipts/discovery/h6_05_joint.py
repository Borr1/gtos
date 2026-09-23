"""h6 step 5 — for ONE contract, price every remaining lever JOINTLY on the same rows,
ablate each component's MARGINAL contribution, and report the full economics.

usage: python3 h6_05_joint.py <tag> <k> <target|None> <stop> <trail|None> <maxbars|None>
"""
import gzip, json, os, sys, time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h6_lib as H  # noqa: E402

# ------- the lever grids priced jointly on the same rows
BANDS = [("none", None, None),          # take every at-market candidate
         ("c0<=+0.10", None, 0.10), ("c0<=+0.05", None, 0.05),
         ("c0<=0", None, 0.0), ("c0<=-0.02", None, -0.02),
         ("c0<=-0.05", None, -0.05), ("c0<=-0.10", None, -0.10),
         ("c0>=0", 0.0, None), ("c0>=+0.05", 0.05, None),
         ("c0>=-0.05", -0.05, None), ("c0>=-0.10", -0.10, None),
         ("|c0|<=0.05", -0.05, 0.05), ("|c0|<=0.10", -0.10, 0.10),
         ("-0.20<=c0<=-0.02", -0.20, -0.02)]
GATES = [("ungated", None, None), ("shipped_0.10/0.15", 0.10, 0.15),
         ("tot<=0.30", None, 0.30), ("tot<=0.20", None, 0.20),
         ("tot<=0.15", None, 0.15), ("tot<=0.10", None, 0.10),
         ("tot<=0.075", None, 0.075), ("tot<=0.05", None, 0.05),
         ("tot<=0.04", None, 0.04), ("tot<=0.03", None, 0.03),
         ("tot<=0.02", None, 0.02), ("tot<=0.015", None, 0.015),
         ("tot<=0.01", None, 0.01),
         ("spr<=0.10", 0.10, None), ("spr<=0.05", 0.05, None),
         ("spr<=0.02", 0.02, None)]
FLOORS = [("none", None), ("0.45", 0.45), ("0.70", 0.70), ("0.80", 0.80),
          ("0.90", 0.90), ("0.93", 0.93)]


def parse(x):
    return None if x in ("None", "none", "-") else float(x)


def main(tag, k, target, stop, trail, maxbars):
    t0 = time.time()
    P, M = H.load()
    r, reason, ebar, trd, c0 = H.walk_all(P, k=k, target=target, stop=stop,
                                          trail=trail, maxbars=maxbars)
    out = {"tag": tag, "contract": {"k": k, "target": target, "stop": stop,
                                    "trail": trail, "maxbars": maxbars}}

    # ---------------- the full joint grid: band x gate x floor
    grid = []
    for bn, blo, bhi in BANDS:
        for gn, gs, gt in GATES:
            for fn, fl in FLOORS:
                sel = H.population(M, trd, c0, entry_lo=blo, entry_hi=bhi,
                                   gate_spread=gs, gate_total=gt, fill_floor=fl)
                if sel.sum() < 100:
                    continue
                s = H.score(r, M, sel, reason)
                s.update({"band": bn, "gate": gn, "floor": fn})
                for mn in ("2026-01", "2026-02", "2026-03"):
                    s2 = sel & (M["month"] == mn)
                    if s2.sum():
                        s["net_" + mn[-2:]] = float((r[s2] - M["cost_true"][s2]).mean())
                        s["n_" + mn[-2:]] = int(s2.sum())
                grid.append(s)
    out["joint_grid"] = grid
    print(f"{tag}: grid cells {len(grid)}  {time.time()-t0:.0f}s", flush=True)

    # ---------------- best cells
    for kf, lab in ((lambda s: s["net"], "best_net"),
                    (lambda s: s["ratio_bps"] if s["ratio_bps"] is not None else -9, "best_ratio"),
                    (lambda s: s["total_net_R"], "best_total_R")):
        cand = [s for s in grid if s["n"] >= 300]
        b = max(cand, key=kf)
        out[lab] = b
        print(" ", lab, b["band"], b["gate"], b["floor"], "n", b["n"],
              "net", round(b["net"], 5), "ratio", round(b["ratio_bps"] or 0, 4), flush=True)

    # ---------------- MARGINAL ablation, both directions, on the same rows
    #   forward:  baseline = shipped contract (k=0, 2R/-1R), no band, no gate, no floor
    #   each component ADDED alone, then all, then all-minus-one
    comps = {"D_delay": ("k", k), "E_exit": ("exit", (target, stop, trail, maxbars)),
             "B_band": ("band", None), "G_gate": ("gate", ("shipped", 0.10, 0.15)),
             "F_floor": ("floor", 0.45)}
    base_walk = H.walk_all(P, k=0, target=2.0, stop=-1.0, trail=None, maxbars=None)

    def cell(use_delay, use_exit, band, gate, floor):
        kk = k if use_delay else 0
        if use_exit:
            rr = H.walk_all(P, k=kk, target=target, stop=stop, trail=trail, maxbars=maxbars)
        else:
            rr = H.walk_all(P, k=kk, target=2.0, stop=-1.0, trail=None, maxbars=None)
        rv, rs, _e, td, cc = rr
        blo, bhi = band if band else (None, None)
        gs, gt = gate if gate else (None, None)
        sel = H.population(M, td, cc, entry_lo=blo, entry_hi=bhi, gate_spread=gs,
                           gate_total=gt, fill_floor=floor)
        return H.score(rv, M, sel, rs)

    BEST_BAND = out["best_net"]["band"]
    bb = next((b, lo, hi) for b, lo, hi in BANDS if b == BEST_BAND)
    bestband = (bb[1], bb[2]) if BEST_BAND != "none" else None
    BEST_GATE = out["best_net"]["gate"]
    bg = next((g, gs, gt) for g, gs, gt in GATES if g == BEST_GATE)
    bestgate = (bg[1], bg[2]) if BEST_GATE != "ungated" else None

    ab = {}
    ab["baseline_shipped"] = cell(False, False, None, None, None)
    ab["ADD_delay_only"] = cell(True, False, None, None, None)
    ab["ADD_exit_only"] = cell(False, True, None, None, None)
    ab["ADD_band_only"] = cell(False, False, bestband, None, None)
    ab["ADD_gate_only"] = cell(False, False, None, bestgate, None)
    ab["ADD_floor_only"] = cell(False, False, None, None, 0.45)
    ab["JOINT_all"] = cell(True, True, bestband, bestgate, 0.45)
    ab["JOINT_minus_delay"] = cell(False, True, bestband, bestgate, 0.45)
    ab["JOINT_minus_exit"] = cell(True, False, bestband, bestgate, 0.45)
    ab["JOINT_minus_band"] = cell(True, True, None, bestgate, 0.45)
    ab["JOINT_minus_gate"] = cell(True, True, bestband, None, 0.45)
    ab["JOINT_minus_floor"] = cell(True, True, bestband, bestgate, None)
    out["ablation"] = ab
    b0 = ab["baseline_shipped"]["net"]
    jt = ab["JOINT_all"]["net"]
    out["ablation_summary"] = {
        "baseline_net": b0, "joint_net": jt,
        "standalone": {c: ab["ADD_" + c + "_only"]["net"] - b0
                       for c in ("delay", "exit", "band", "gate", "floor")},
        "marginal": {c: jt - ab["JOINT_minus_" + c]["net"]
                     for c in ("delay", "exit", "band", "gate", "floor")}}
    out["ablation_summary"]["sum_standalone"] = sum(out["ablation_summary"]["standalone"].values())
    out["ablation_summary"]["sum_marginal"] = sum(out["ablation_summary"]["marginal"].values())
    out["ablation_summary"]["joint_gain"] = jt - b0
    print(" ablation joint", round(jt, 5), "base", round(b0, 5),
          "sum_standalone", round(out["ablation_summary"]["sum_standalone"], 5),
          "sum_marginal", round(out["ablation_summary"]["sum_marginal"], 5), flush=True)

    # ---------------- full economics at the ungated and at the best-net cell
    for lab, (blo, bhi, gs, gt, fl) in {
            "ungated_all": (None, None, None, None, None),
            "best_net_cell": ((bestband or (None, None))[0], (bestband or (None, None))[1],
                              (bestgate or (None, None))[0], (bestgate or (None, None))[1],
                              None)}.items():
        sel = H.population(M, trd, c0, entry_lo=blo, entry_hi=bhi, gate_spread=gs,
                           gate_total=gt, fill_floor=fl)
        rec = {"score": H.score(r, M, sel, reason),
               "per_symbol": H.by_group(r, M, sel, "symbol"),
               "per_family": H.by_group(r, M, sel, "family"),
               "per_hour": H.by_group(r, M, sel, "hour"),
               "per_session": H.by_group(r, M, sel, "session"),
               "per_month": H.by_group(r, M, sel, "month"),
               "per_day": H.by_day(r, M, sel),
               "boot_net": H.bootstrap_days(r, M, sel, field="net"),
               "boot_gross": H.bootstrap_days(r, M, sel, field="gross")}
        rec["n_symbols_gross_pos"] = sum(1 for v in rec["per_symbol"].values() if v["gross"] > 0)
        rec["n_symbols_net_pos"] = sum(1 for v in rec["per_symbol"].values() if v["net"] > 0)
        rec["n_symbols_ratio_gt_1"] = sum(1 for v in rec["per_symbol"].values()
                                          if (v["ratio_bps"] or 0) > 1)
        rec["n_days_net_pos"] = sum(1 for v in rec["per_day"].values() if v["net"] > 0)
        rec["n_days_gross_pos"] = sum(1 for v in rec["per_day"].values() if v["gross"] > 0)
        rec["n_days"] = len(rec["per_day"])
        days = sorted(rec["per_day"])
        cum = 0.0
        eq = []
        for d in days:
            cum += rec["per_day"][d]["sum_net"]
            eq.append(round(cum, 2))
        rec["equity_net_R"] = eq
        rec["max_drawdown_R"] = round(min((e - max(eq[:i + 1]) for i, e in enumerate(eq)),
                                          default=0.0), 2)
        out[lab] = rec
        print(" ", lab, "n", rec["score"]["n"], "net", round(rec["score"]["net"], 5),
              "ratio", round(rec["score"]["ratio_bps"] or 0, 4),
              "sym ratio>1", rec["n_symbols_ratio_gt_1"],
              "days net+", rec["n_days_net_pos"], "/", rec["n_days"], flush=True)

    json.dump(out, open(f"{D}/H6_JOINT_{tag}_V1.json", "w"), indent=1)
    print("wrote", f"H6_JOINT_{tag}_V1.json", round(time.time() - t0, 1), "s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), parse(sys.argv[3]), parse(sys.argv[4]),
         parse(sys.argv[5]), None if sys.argv[6] in ("None", "none", "-") else int(sys.argv[6]))
