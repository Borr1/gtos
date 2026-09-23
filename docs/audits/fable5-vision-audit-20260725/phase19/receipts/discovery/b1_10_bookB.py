"""b1 step 10 — BOOK-B: the limb that actually travels, tested the strict way.

b1_09 separated the gate into two limbs and they behave completely differently:
    instrument limb  cost rank Spearman hunt->OOS = 0.9922   TRAVELS
    hour limb        the within-symbol cheap-hour selection  DOES NOT
So the honest book is the one that keeps only the limb with persistence.

BOOK-B: rank the 24 instruments by their own mean broker-true round-trip toll in bps.
        Take the cheapest three. Trade every candidate on them, at every hour.
        Enter at market at +3 min; stop -1R, no target, no trail, close at +120 min.
The instrument choice consults NO outcome column of any kind -- only the toll.

PROTOCOL, and this is the point of the step: the instruments are selected on JANUARY
COST ALONE, then the book is read on February..May, four months it never saw. A
sensitivity over m in {1,2,3,4,5} instruments is reported so the "three" is not a fit
either, and a fully rolling variant re-selects on each month's own cost.
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
K, EXIT = 3, "STOPONLY"


def main():
    t0 = time.time()
    M, G, _ = N.load()
    cost = M["cost_hour"]
    cbps = cost * M["bpsfac"]
    g = G[(K, EXIT)]
    out = {"spec": {"k": K, "exit": EXIT, "cost_basis": "hour-true three-term",
                    "selection_input": "mean cost_bps only; no outcome column"}}

    # ---- the cost ranking, per month and pooled: is it stable?
    rank = {}
    for m in MONTHS + ("ALL",):
        sel = np.ones(len(cost), bool) if m == "ALL" else (M["month"] == m)
        d = {}
        for s in sorted(set(M["symbol"].tolist())):
            q = sel & (M["symbol"] == s) & np.isfinite(cbps)
            if q.sum() >= 20:
                d[s] = float(cbps[q].mean())
        rank[m] = dict(sorted(d.items(), key=lambda x: x[1]))
    out["cost_rank_by_month"] = {m: list(v) for m, v in rank.items()}
    out["cost_bps_by_month"] = {m: {k: round(v, 4) for k, v in v2.items()}
                               for m, v2 in rank.items()}
    jan_order = list(rank["2026-01"])
    out["january_cost_order"] = jan_order
    out["order_identical_all_months"] = all(list(rank[m])[:6] == jan_order[:6] for m in MONTHS)

    # ---- BOOK-B at m instruments chosen on JANUARY COST ONLY, read on Feb..May
    out["train_january_cost_test_feb_may"] = {}
    for mnum in (1, 2, 3, 4, 5, 6, 8):
        chosen = jan_order[:mnum]
        pm = np.isin(M["symbol"], chosen)
        rec = {"instruments": chosen,
               "TRAIN_january": N.slim(N.score(g, cost, M, pm & (M["month"] == "2026-01"))),
               "TEST_feb_to_may": N.slim(N.score(g, cost, M,
                                                 pm & np.isin(M["month"], MONTHS[1:]))),
               "pooled_5m": N.slim(N.score(g, cost, M, pm))}
        for mm in MONTHS:
            rec["m_" + mm] = N.slim(N.score(g, cost, M, pm & (M["month"] == mm)))
        out["train_january_cost_test_feb_may"][str(mnum)] = rec

    # ---- headline BOOK-B (three instruments) with the full statistic set
    chosen = jan_order[:3]
    pm = np.isin(M["symbol"], chosen)
    s = N.score(g, cost, M, pm, want_equity=True)
    out["BOOK_B_equity"] = {"days": s.pop("equity_days"), "cum_net_R": s.pop("equity_net_R"),
                            "day_mean_net_R": s.pop("day_net_R")}
    out["BOOK_B_pooled_5m"] = N.slim(s)
    out["BOOK_B_instruments"] = chosen
    out["BOOK_B_hunt_3m"] = N.slim(N.score(g, cost, M, pm & np.isin(M["month"], MONTHS[:3])))
    out["BOOK_B_oos_2m"] = N.slim(N.score(g, cost, M, pm & np.isin(M["month"], MONTHS[3:])))
    out["BOOK_B_per_symbol"] = {s2: N.slim(N.score(g, cost, M, pm & (M["symbol"] == s2)))
                                for s2 in chosen}
    out["BOOK_B_per_month"] = {m: N.slim(N.score(g, cost, M, pm & (M["month"] == m)))
                               for m in MONTHS}

    sel = pm & np.isfinite(g)
    net = g[sel] - cost[sel]
    rng = np.random.default_rng(20260806)
    ud, inv = np.unique(M["day"][sel], return_inverse=True)
    Gn = len(ud)
    ssum = np.bincount(inv, weights=net, minlength=Gn)
    scnt = np.bincount(inv, minlength=Gn).astype(float)
    idx = rng.integers(0, Gn, size=(4000, Gn))
    mm = np.sort(ssum[idx].sum(axis=1) / scnt[idx].sum(axis=1))
    out["BOOK_B_bootstrap_5m"] = {"p025": float(mm[100]), "p50": float(mm[2000]),
                                  "p975": float(mm[3899]), "p_le_0": float((mm <= 0).mean())}
    out["BOOK_B_truncation"] = {
        "stopped_share": float((np.abs(g[sel] + 1.0) < 1e-9).mean()),
        "time_exit_share": float((np.abs(g[sel] + 1.0) >= 1e-9).mean()),
        "share_gross_gt_2R": float((g[sel] > 2).mean()),
        "top1pct_share_of_total_net": (float(np.sort(net)[-max(1, len(net) // 100):].sum()
                                             / net.sum()) if net.sum() > 0 else None)}

    # ---- k and exit sensitivity of BOOK-B on the five months
    out["BOOK_B_k_exit_surface"] = []
    for k in N.KS:
        for cx in N.TRAIL_FREE + ("TRAIL025",):
            r = N.score(G[(k, cx)], cost, M, pm)
            r.update({"k": k, "exit": cx})
            out["BOOK_B_k_exit_surface"].append(N.slim(r))

    # ---- rolling monthly re-selection (cost of the PREVIOUS month picks the next)
    roll = []
    tot_n, tot_net = 0, 0.0
    for i in range(1, len(MONTHS)):
        prev, cur = MONTHS[i - 1], MONTHS[i]
        ch = list(rank[prev])[:3]
        q = np.isin(M["symbol"], ch) & (M["month"] == cur)
        r = N.score(g, cost, M, q)
        r.update({"month": cur, "chosen_on": prev, "instruments": ch})
        roll.append(N.slim(r))
        tot_n += r["n"]; tot_net += r["net_R"] * r["n"]
    out["rolling_reselection"] = {"months": roll, "pooled_n": tot_n,
                                  "pooled_net_R": (tot_net / tot_n if tot_n else None)}

    out["elapsed_s"] = round(time.time() - t0, 1)
    with open(f"{D}/B1_BOOKB_V1.json", "w") as f:
        json.dump(out, f, indent=1)

    print("JANUARY COST ORDER (cheapest first):", jan_order[:8])
    print("cost-order top-6 identical in all five months:", out["order_identical_all_months"])
    print()
    print("BOOK-B  instruments chosen on JANUARY COST ONLY, read on Feb..May")
    print(f"  {'m':>2} {'instruments':40} {'TRAIN n':>8} {'TRAIN net':>10} "
          f"{'TEST n':>7} {'TEST net':>9} {'TEST ratio':>10} {'tday':>6}")
    for mn, rec in out["train_january_cost_test_feb_may"].items():
        tr, te = rec["TRAIN_january"], rec["TEST_feb_to_may"]
        print(f"  {mn:>2} {','.join(rec['instruments'])[:40]:40} {tr['n']:>8} "
              f"{tr['net_R']:>+10.5f} {te['n']:>7} {te['net_R']:>+9.5f} "
              f"{(te['ratio_R'] or 0):>10.3f} {(te['t_net_day'] or 0):>+6.2f}")
    print()
    b = out["BOOK_B_pooled_5m"]
    print(f"BOOK-B pooled five months: n={b['n']} gross={b['gross_R']:+.6f} "
          f"cost={b['cost_R']:.6f} net={b['net_R']:+.6f} ratio={b['ratio_R']:.4f} "
          f"tday={b['t_net_day']:+.3f} days={b['n_days_net_pos']}/{b['n_days']}")
    print("  months: " + "  ".join(
        f"{m[-2:]}:{out['BOOK_B_per_month'][m]['net_R']:+.5f}" for m in MONTHS))
    print("  bootstrap:", {k: round(v, 5) for k, v in out["BOOK_B_bootstrap_5m"].items()})
    print("  per symbol:", {k: (v["n"], round(v["net_R"], 5), round(v["ratio_R"] or 0, 3))
                            for k, v in out["BOOK_B_per_symbol"].items()})
    r = out["rolling_reselection"]
    print(f"  rolling re-selection: n={r['pooled_n']} net={r['pooled_net_R']:+.6f}")
    print("elapsed", out["elapsed_s"])


if __name__ == "__main__":
    main()
