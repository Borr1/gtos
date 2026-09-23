"""d6_mech — the mechanism, the ablation and the truncation table.

  1  precision-IS-edge, measured on the best separator rather than on the minute
     floor: displacement deciles x {paired share, paired-leg net, phantom net,
     combined net}
  2  the ablation: family set / timing / geometry / contract / target, each
     priced on the SAME rows
  3  exit mix and maxbars truncation share at the winner
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PBG = HERE.parent / "pbg"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PBG))
sys.path.insert(0, str(HERE.parents[5]))

import d6_lib as D  # noqa: E402
import pbg_econ as E  # noqa: E402
import pbg_lib as L  # noqa: E402


def feats(month, fams):
    rows = D.load(month, fams=fams)
    tape = E.Tape(L.SYMBOLS, [month])
    out = []
    for r in rows:
        P = r.get("P")
        if not P:
            continue
        i = tape.idx(r["t_part"])
        j = tape.idx(r["b"])
        if j < 0 or i <= j:
            continue
        o = tape.o[r["s"]][j:i]
        h = tape.h[r["s"]][j:i]
        lo = tape.l[r["s"]][j:i]
        ok = ~np.isnan(h)
        if not ok.any():
            continue
        bar_open = float(o[ok][0])
        d = P["d"]
        long = r["sd"] == "L"
        out.append({
            "m": month, "day": r["day_part"], "f": r["f"],
            "paired": 1 if r.get("C") else 0,
            "net": P["g2"] - P["cr"], "gross": P["g2"], "cost": P["cr"],
            "disp_r": ((P["e"] - bar_open) if long else (bar_open - P["e"])) / d,
            "k": r["k"],
        })
    return out


def blk(rows):
    if not rows:
        return {"n": 0}
    n = np.array([r["net"] for r in rows])
    by_day = defaultdict(lambda: [0.0, 0])
    for r in rows:
        by_day[r["m"] + "|" + r["day"]][0] += r["net"]
        by_day[r["m"] + "|" + r["day"]][1] += 1
    return {"n": int(len(n)), "net_r": float(n.mean()),
            "gross_r": float(np.mean([r["gross"] for r in rows])),
            "days_positive": sum(1 for d in by_day if by_day[d][0] > 0),
            "n_days": len(by_day)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    months = [m for m in args.months.split(",") if m] or D.months_available()
    E5 = set(D.EARLY5)

    res = {"months": months,
           "generated_utc": datetime.now(timezone.utc).isoformat()}

    # ---------------------------------------------------- 1. precision IS edge
    data = []
    for m in months:
        data += feats(m, E5)
    dv = np.array([r["disp_r"] for r in data])
    qs = np.percentile(dv, np.arange(10, 100, 10))
    bins = np.digitize(dv, qs)
    tbl = []
    for b in range(10):
        sub = [r for r, i in zip(data, bins) if i == b]
        if not sub:
            continue
        pr = [r for r in sub if r["paired"]]
        ph = [r for r in sub if not r["paired"]]
        tbl.append({
            "decile": b + 1,
            "disp_r_lo": float(min(r["disp_r"] for r in sub)),
            "disp_r_hi": float(max(r["disp_r"] for r in sub)),
            "n": len(sub),
            "precision_paired_share": len(pr) / len(sub),
            "paired_leg": blk(pr), "phantom_leg": blk(ph), "combined": blk(sub),
        })
    res["displacement_deciles"] = tbl

    # cumulative "take only the top-x deciles" book
    cum = []
    order = sorted(range(len(tbl)), key=lambda i: -tbl[i]["decile"])
    keep = set()
    for i in order:
        keep.add(tbl[i]["decile"])
        sub = [r for r, b in zip(data, bins) if (b + 1) in keep]
        pr = [r for r in sub if r["paired"]]
        cum.append({"top_deciles": sorted(keep, reverse=True), "n": len(sub),
                    "precision": len(pr) / len(sub) if sub else None,
                    "book": blk(sub), "paired_leg_only": blk(pr)})
    res["cumulative_displacement_floor"] = cum

    # ---------------------------------------------------- 2. the ablation
    atm = {m: D.load(m, fams=set(D.AT_MARKET)) for m in months}

    def paired_rows(fams):
        out = []
        for m in months:
            out += [r for r in atm[m] if r["f"] in fams and r.get("C") and r.get("P")]
        return out

    def delta(rows, a, b, target=2.0):
        return D.paired_delta(rows, a, b, target=target)

    ab = {}
    for name, fams in (("EARLY5", E5), ("ALL7", set(D.AT_MARKET)),
                       ("liquidity_sweep_reclaim_only", {"liquidity_sweep_reclaim"}),
                       ("EARLY5_minus_lsr", E5 - {"liquidity_sweep_reclaim"})):
        rr = paired_rows(fams)
        ab[name] = {
            "n_paired": len(rr),
            "delta_net_total_2R": delta(rr, "P", "C"),
            "delta_net_timing_only_d0_2R": delta(rr, "D", "C"),
            "delta_net_total_1p5R": delta(rr, "P", "C", target=1.5),
            "delta_net_timing_only_d0_1p5R": delta(rr, "D", "C", target=1.5),
            "close_arm_2R": D.summarise([(r, "C") for r in rr], "close_2R"),
            "close_arm_1p5R": D.summarise([(r, "C") for r in rr], "close_1.5R", target=1.5),
            "partial_arm_2R": D.summarise([(r, "P") for r in rr], "partial_2R"),
            "partial_arm_1p5R": D.summarise([(r, "P") for r in rr], "partial_1.5R", target=1.5),
        }
    res["ablation_family_timing_geometry_target"] = ab

    # POI contract, for the at-market-vs-limit axis
    poi = []
    for m in months:
        poi += [r for r in D.load(m, fams=set(D.POI)) if r.get("C") and r.get("P")]
    res["ablation_contract_POI"] = {
        "n_paired": len(poi),
        "close_arm": D.summarise([(r, "C") for r in poi], "poi_close"),
        "partial_arm": D.summarise([(r, "P") for r in poi], "poi_partial"),
        "delta_net": D.paired_delta(poi, "P", "C"),
        "delta_net_d0": D.paired_delta(poi, "D", "C"),
    }

    # generator's own take-profit, where it exists
    own = {"n_with_own_tp": 0}
    tot_c = tot_p = 0.0
    nc = npp = 0
    for m in months:
        for r in atm[m]:
            if r["f"] not in E5:
                continue
            C, P = r.get("C"), r.get("P")
            if C and "gown" in C:
                tot_c += C["gown"] - C["cr"]
                nc += 1
            if P and "gown" in P:
                tot_p += P["gown"] - P["cr"]
                npp += 1
    own["close_arm_own_tp_net_r"] = tot_c / nc if nc else None
    own["close_arm_n"] = nc
    own["partial_arm_own_tp_net_r"] = tot_p / npp if npp else None
    own["partial_arm_n"] = npp
    res["ablation_generator_own_take_profit"] = own

    # ---------------------------------------------------- 3. truncation at the winner
    winner = []
    for m in months:
        winner += [(r, "P") for r in atm[m] if r["f"] in E5 and r.get("C") and r.get("P")]
    res["winner_exit_mix"] = D.summarise(winner, "A2_paired_partial_2R")
    res["winner_exit_mix_1p5R"] = D.summarise(winner, "A2_paired_partial_1.5R", target=1.5)
    close_w = [(r, "C") for r in atm[months[0]] if r["f"] in E5 and r.get("C") and r.get("P")]
    res["incumbent_exit_mix_first_month"] = D.summarise(close_w, "close_2R")

    Path(args.out).write_text(json.dumps(res, indent=1))
    print("wrote", args.out)


if __name__ == "__main__":
    main()
