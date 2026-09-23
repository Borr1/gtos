"""b1 step 11 — decompose the gate into its two limbs, then stress the book.

PART 1  The <=0.60 bps gate does two things at once:
          (a) it deletes 21 of 24 instruments outright
          (b) inside the three survivors it keeps only 40-97% of rows -- the cheap HOURS
        b1_09 showed the two limbs have opposite persistence. This part measures each
        alone, with a January-train / Feb-May-test protocol on both.

PART 2  Rank instruments by mean cost in R (the unit a constant-R book actually pays)
        rather than in bps -- b1_10's ranking used bps and admitted EURUSD, whose toll
        in R is 4.4x the index complex.

PART 3  STRESS on b1-BOOK-V1, Jan+Feb+Mar: cost x1.25 / x1.5 / x2, l10-F9 exit
        slippage, the January-era spread regime, and the h4 all-in live-grounded toll
        (1.577x the published basis).
"""
import json
import os
import sys
import time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import b1_np as N  # noqa: E402

MONTHS = ("2026-01", "2026-02", "2026-03", "2026-04", "2026-05")
M3, M2 = MONTHS[:3], MONTHS[3:]
K, EXIT, GATE = 3, "STOPONLY", 0.60
IDX3 = ("US30_cash", "GER40", "NAS100")


def main():
    t0 = time.time()
    M, G, _ = N.load()
    cost = M["cost_hour"]
    cbps = cost * M["bpsfac"]
    g = G[(K, EXIT)]
    gate = cbps <= GATE + 1e-12
    inst = np.isin(M["symbol"], IDX3)
    out = {}

    # ---------------------------------------------------------------- PART 1
    limbs = {
        "both limbs (b1-BOOK-V1)": gate,
        "instrument limb only (the 3 survivors, all hours)": inst,
        "hour limb only (<=0.60bps INSIDE the 3 survivors)": inst & gate,
        "hour limb REMOVED, instruments kept": inst & ~gate,
        "instrument limb removed, gate kept elsewhere": gate & ~inst,
    }
    out["PART1_limbs"] = {}
    for lab, m in limbs.items():
        d = {"hunt_3m": N.slim(N.score(g, cost, M, m & np.isin(M["month"], M3))),
             "oos_2m": N.slim(N.score(g, cost, M, m & np.isin(M["month"], M2))),
             "pooled_5m": N.slim(N.score(g, cost, M, m))}
        for mm in MONTHS:
            d[mm] = N.slim(N.score(g, cost, M, m & (M["month"] == mm)))
        out["PART1_limbs"][lab] = d

    # ---------------------------------------------------------------- PART 2
    jan = M["month"] == "2026-01"
    rr = {}
    for s in sorted(set(M["symbol"].tolist())):
        q = jan & (M["symbol"] == s) & np.isfinite(cost)
        if q.sum() >= 20:
            rr[s] = float(cost[q].mean())
    order_R = [k for k, _ in sorted(rr.items(), key=lambda x: x[1])]
    out["january_cost_R_order"] = order_R
    out["january_cost_R_values"] = {k: round(v, 5) for k, v in
                                    sorted(rr.items(), key=lambda x: x[1])}
    out["PART2_costR_ranked_book"] = {}
    for mn in (1, 2, 3, 4, 5, 6, 8, 10):
        ch = order_R[:mn]
        pm = np.isin(M["symbol"], ch)
        out["PART2_costR_ranked_book"][str(mn)] = {
            "instruments": ch,
            "TRAIN_january": N.slim(N.score(g, cost, M, pm & jan)),
            "TEST_feb_to_may": N.slim(N.score(g, cost, M, pm & np.isin(M["month"], MONTHS[1:]))),
            "pooled_5m": N.slim(N.score(g, cost, M, pm))}

    # the three-index set with a strict train/test on the SET itself
    out["PART2_idx3_trainjan_testfebmay"] = {
        "instruments": list(IDX3),
        "TRAIN_january": N.slim(N.score(g, cost, M, inst & jan)),
        "TEST_feb_to_may": N.slim(N.score(g, cost, M, inst & np.isin(M["month"], MONTHS[1:]))),
        "TEST_apr_may_only": N.slim(N.score(g, cost, M, inst & np.isin(M["month"], M2)))}

    # ---------------------------------------------------------------- PART 3
    h1c = M["cost_h1"]
    sel3 = gate & np.isin(M["month"], M3) & np.isfinite(h1c)
    # l10-F9 exit slippage converted to R at this book's own stop geometry: the receipt
    # gives 0.032236 R/trade mean on clean stop exits (h4 sec 6). Charge it on the
    # STOPPED share only, which is what a stop exit is.
    stopped = np.abs(g + 1.0) < 1e-9
    exitslip = np.where(stopped, 0.032236, 0.0)
    stress = {
        "base (h1 four-term)": h1c,
        "cost x1.25": h1c * 1.25,
        "cost x1.50": h1c * 1.50,
        "cost x2.00": h1c * 2.00,
        "h4 all-in live-grounded (x1.577)": h1c * 1.577,
        "+ l10-F9 exit slippage on stop exits": h1c + exitslip,
        "+ exit slippage AND cost x1.5": h1c * 1.5 + exitslip,
        "January-era spread regime (h1 era-true)": M["cost_h1_era"],
        "+ entry slippage doubled (h4 +0.1165bps)": h1c + 0.1165 / M["bpsfac"],
    }
    out["PART3_stress_hunt3m"] = {}
    for lab, c in stress.items():
        out["PART3_stress_hunt3m"][lab] = N.slim(N.score(g, c, M, sel3))
    # the same stresses on the five-month gated book at the hour-true basis
    out["PART3_stress_5m"] = {}
    for lab, mult in (("base", 1.0), ("x1.25", 1.25), ("x1.5", 1.5), ("x1.577", 1.577),
                      ("x2.0", 2.0)):
        out["PART3_stress_5m"][lab] = N.slim(N.score(g, cost * mult, M, gate))

    # ---- how far short is the OOS book, stated as a requirement
    o = N.score(g, cost, M, gate & np.isin(M["month"], M2))
    out["SHORTFALL_oos"] = {
        "gross_R": o["gross_R"], "cost_R": o["cost_R"], "net_R": o["net_R"],
        "gross_multiple_required": (o["cost_R"] / o["gross_R"] if o["gross_R"] > 0 else None),
        "cost_cut_required_pct": (1 - o["gross_R"] / o["cost_R"]) * 100,
        "note": "to break even the OOS book needs either that multiple on its gross or "
                "that percentage cut in its toll"}

    out["elapsed_s"] = round(time.time() - t0, 1)
    with open(f"{D}/B1_DECOMPOSE_V1.json", "w") as f:
        json.dump(out, f, indent=1)

    print("PART 1 — the two limbs of the gate, hour-true cost")
    print(f"  {'limb':52}{'hunt n':>8}{'hunt net':>10}{'oos n':>7}{'oos net':>9}"
          f"{'5m net':>9}{'5m ratio':>9}")
    for lab, d in out["PART1_limbs"].items():
        h, o2, p = d["hunt_3m"], d["oos_2m"], d["pooled_5m"]
        if not p.get("n"):
            print(f"  {lab:52}  EMPTY (the gate admits nothing outside the 3 instruments)")
            continue
        f2 = lambda x, k: (x[k] if x.get("n") else 0.0)
        print(f"  {lab:52}{h.get('n',0):>8}{f2(h,'net_R'):>+10.5f}{o2.get('n',0):>7}"
              f"{f2(o2,'net_R'):>+9.5f}{p['net_R']:>+9.5f}{(p['ratio_R'] or 0):>9.3f}")
    print()
    print("PART 2 — instruments ranked by JANUARY mean cost in R (not bps)")
    print("  order:", order_R[:8])
    for mn, r in out["PART2_costR_ranked_book"].items():
        te = r["TEST_feb_to_may"]
        print(f"   m={mn:>2} {','.join(r['instruments'])[:44]:44} TEST n={te['n']:>6} "
              f"net={te['net_R']:>+9.5f} ratio={(te['ratio_R'] or 0):>7.3f}")
    p2 = out["PART2_idx3_trainjan_testfebmay"]
    print(f"  IDX3 train-Jan n={p2['TRAIN_january']['n']} net={p2['TRAIN_january']['net_R']:+.5f}"
          f" | test Feb-May n={p2['TEST_feb_to_may']['n']} "
          f"net={p2['TEST_feb_to_may']['net_R']:+.5f} "
          f"ratio={p2['TEST_feb_to_may']['ratio_R']:.3f}")
    print()
    print("PART 3 — STRESS on b1-BOOK-V1, Jan+Feb+Mar (n=3,728)")
    for lab, s in out["PART3_stress_hunt3m"].items():
        print(f"  {lab:44} cost={s['cost_R']:.5f} net={s['net_R']:>+9.5f} "
              f"ratio={(s['ratio_R'] or 0):>7.3f} tday={(s['t_net_day'] or 0):>+6.2f}")
    print()
    print("SHORTFALL (April+May):", json.dumps(
        {k: (round(v, 5) if isinstance(v, float) else v)
         for k, v in out["SHORTFALL_oos"].items() if k != "note"}))
    print("elapsed", out["elapsed_s"])


if __name__ == "__main__":
    main()
