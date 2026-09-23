#!/usr/bin/env python3
"""l6 STEP 5 — the fill-probability inversion, mechanism and size.
Writes L6_FILLPROB_V1.json."""
import json, os, sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
from l6_lib import load, stats, mean, q  # noqa: E402


def main():
    rows = load()
    res = {"POOL": stats(rows)}
    have = [r for r in rows if r.get("execution_fill_probability") is not None]
    res["n_with_fillprob"] = len(have)
    res["n_null_fillprob"] = len(rows) - len(have)

    # ---- decile table
    vals = sorted(r["execution_fill_probability"] for r in have)
    n = len(vals)
    edges = [vals[int(round(k / 10 * (n - 1)))] for k in range(11)]
    res["decile_edges"] = [round(e, 6) for e in edges]
    dec = []
    for k in range(10):
        lo, hi = edges[k], edges[k + 1]
        if k < 9:
            sub = [r for r in have if lo <= r["execution_fill_probability"] < hi]
        else:
            sub = [r for r in have if lo <= r["execution_fill_probability"] <= hi]
        if not sub:
            continue
        s = stats(sub, f"d{k+1} [{round(lo,4)},{round(hi,4)}]")
        s["mean_fill_prob"] = mean([r["execution_fill_probability"] for r in sub])
        s["median_abs_entry_dist_R"] = q([abs(r["m"]) for r in sub if r.get("m") is not None], 0.5)
        s["median_bars_to_fill"] = q([r["fill_bar"] for r in sub if r.get("fill_bar") is not None], 0.5)
        s["mean_spread_r"] = mean([r.get("spread_r") for r in sub])
        dec.append(s)
    res["deciles"] = dec

    # ---- the exact value 0.92 (the marketable branch constant) vs the rest
    res["eq_0p92"] = stats([r for r in have if abs(r["execution_fill_probability"] - 0.92) < 1e-9], "==0.92")
    res["ne_0p92"] = stats([r for r in have if abs(r["execution_fill_probability"] - 0.92) >= 1e-9], "!=0.92")

    # ---- floors as enacted, both directions
    for name, thr in (("selector_0p45", 0.45), ("scheduler_0p80", 0.80), ("softened_0p25", 0.25),
                      ("offsession_0p70", 0.70), ("reduce_risk_0p80", 0.80)):
        below = [r for r in have if r["execution_fill_probability"] < thr]
        above = [r for r in have if r["execution_fill_probability"] >= thr]
        res[f"floor_{name}"] = {
            "threshold": thr,
            "below_n": len(below), "above_n": len(above),
            "below": stats(below), "above": stats(above),
            "inversion_h_gross": (round((stats(below)["h_gross_mean"] or 0) - (stats(above)["h_gross_mean"] or 0), 5)
                                  if below and above else None),
            "inversion_h_all": (round((stats(below)["h_all_mean"] or 0) - (stats(above)["h_all_mean"] or 0), 5)
                                if below and above else None),
        }

    # ---- monotone check on the portfolio contract (unfilled = 0)
    res["monotone_h_all_by_decile"] = [(d["value"], d["h_all_mean"], d["fill_rate_pct"], d["n"]) for d in dec]
    res["monotone_h_gross_by_decile"] = [(d["value"], d["h_gross_mean"], d["n"]) for d in dec]

    # ---- entry-distance is the confound: bucket by |m| (market-to-entry in R) directly
    md = [r for r in rows if r.get("m") is not None and r.get("born") != "born_past_stop"]
    buckets = [(0.0, 0.0), (0.0, 0.05), (0.05, 0.15), (0.15, 0.3), (0.3, 0.6), (0.6, 1.0), (1.0, 99)]
    eb = []
    for lo, hi in buckets:
        if lo == hi == 0.0:
            sub = [r for r in md if abs(r["m"]) == 0.0]
            lab = "exactly_at_market"
        else:
            sub = [r for r in md if lo < abs(r["m"]) <= hi]
            lab = f"({lo},{hi}]R"
        if sub:
            s = stats(sub, lab)
            s["mean_fill_prob"] = mean([r.get("execution_fill_probability") for r in sub])
            eb.append(s)
    res["by_entry_distance"] = eb

    with open(os.path.join(D, "L6_FILLPROB_V1.json"), "w") as fh:
        json.dump(res, fh, indent=1)

    print("POOL", {k: res["POOL"][k] for k in ("n", "h_gross_mean", "h_all_mean", "fill_rate_pct")})
    print("\n-- execution_fill_probability deciles --")
    print(f"{'bucket':26s} {'n':>6s} {'meanP':>7s} {'fill%':>6s} {'hGross':>8s} {'hAll':>8s} {'hWin%':>6s} {'|entry|R':>8s} {'spread_r':>8s}")
    for d in dec:
        print(f"{d['value'][:26]:26s} {d['n']:6d} {d['mean_fill_prob']:7.4f} {str(d['fill_rate_pct']):>6s} "
              f"{str(d['h_gross_mean']):>8s} {str(d['h_all_mean']):>8s} {str(d['h_win_pct']):>6s} "
              f"{str(d['median_abs_entry_dist_R']):>8s} {str(d['mean_spread_r']):>8s}")
    print("\n-- floors --")
    for k in [x for x in res if x.startswith("floor_")]:
        v = res[k]
        print(f"{k:24s} thr={v['threshold']} below n={v['below_n']:6d} hG={v['below']['h_gross_mean']} hAll={v['below']['h_all_mean']} | "
              f"above n={v['above_n']:6d} hG={v['above']['h_gross_mean']} hAll={v['above']['h_all_mean']} | inv_hG={v['inversion_h_gross']} inv_hAll={v['inversion_h_all']}")
    print("\n-- by entry distance --")
    for s in eb:
        print(f"{s['value'][:20]:20s} n={s['n']:6d} fill%={str(s['fill_rate_pct']):>6s} hG={str(s['h_gross_mean']):>8s} hAll={str(s['h_all_mean']):>8s} P={s['mean_fill_prob']}")


if __name__ == "__main__":
    main()
