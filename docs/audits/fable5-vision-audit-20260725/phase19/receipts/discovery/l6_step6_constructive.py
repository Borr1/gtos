#!/usr/bin/env python3
"""l6 STEP 6 — the constructive counterfactual: what a gate stack built on the MEASURED
sign of each gate produces, against the as-shipped stack. IN-SAMPLE on January by
construction — this is a mechanism demonstration, not an admission claim.
Writes L6_CONSTRUCTIVE_V1.json."""
import json, os, sys
from itertools import product

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
from l6_lib import load, stats, mean  # noqa: E402


def f(r, k, d=0.0):
    v = r.get(k)
    return d if v is None else float(v)


SHIPPED = {
    "S1_spread_cap_0p10": lambda r: f(r, "spread_r") > 0.10,
    "S2_total_cost_0p15": lambda r: f(r, "cost_r") > 0.15,
    "S3_ev_negative": lambda r: f(r, "expected_net_r", 1.0) < 0.0,
    "S4_sel_min_ev_0p10": lambda r: f(r, "expected_net_r", 1.0) < 0.10,
    "S5_fill_floor_0p45": lambda r: f(r, "execution_fill_probability", 1.0) < 0.45,
    "S6_sched_fill_0p80": lambda r: f(r, "execution_fill_probability", 1.0) < 0.80,
    "S7_sched_min_ev_0p20": lambda r: f(r, "expected_net_r", 1.0) < 0.20,
    "S8_off_session": lambda r: r.get("route_session") == "off_configured_session",
}
CAND = {
    "C1_total_cost_0p15": lambda r: f(r, "cost_r") > 0.15,
    "C2_block_marketable": lambda r: (r.get("m") is not None and r["m"] < 0.0),
    "C3_block_past_stop": lambda r: r.get("born") == "born_past_stop",
    "C4_require_dist_0p3": lambda r: (r.get("m") is None or r["m"] < 0.3),
    "C5_require_dist_1p0": lambda r: (r.get("m") is None or r["m"] < 1.0),
    "C6_off_session": lambda r: r.get("route_session") == "off_configured_session",
    "C7_block_fillprob_hi": lambda r: f(r, "execution_fill_probability", 0.0) >= 0.92,
    "C8_spread_corr_0p10": lambda r: f(r, "spread_r") / 7.3 > 0.10,
}


def book(rows, M, active):
    return [rows[i] for i in range(len(rows)) if not any(M[k][i] for k in active)]


def day_stats(sub):
    byday = {}
    for r in sub:
        if r.get("takeable"):
            byday.setdefault(r["decision_time_utc"][:10], []).append(r["hr"])
        elif r.get("born") != "born_past_stop" and not r.get("filled"):
            byday.setdefault(r["decision_time_utc"][:10], []).append(0.0)
    days = sorted(byday)
    if not days:
        return {}
    dm = {d: round(sum(byday[d]) / len(byday[d]), 4) for d in days}
    return {"n_days": len(days),
            "day_pos_frac": round(sum(1 for d in days if dm[d] > 0) / len(days), 4),
            "day_means": dm}


def main():
    rows = load()
    res = {"POOL": stats(rows)}
    MS = {k: [bool(fn(r)) for r in rows] for k, fn in SHIPPED.items()}
    MC = {k: [bool(fn(r)) for r in rows] for k, fn in CAND.items()}

    shipped = book(rows, MS, list(SHIPPED))
    res["AS_SHIPPED_STACK"] = stats(shipped)
    res["AS_SHIPPED_STACK"].update(day_stats(shipped))
    res["AS_SHIPPED_STACK"]["first_emission"] = stats([r for r in shipped if r.get("is_first_emission")])

    keys = list(CAND)
    books = []
    for mask in product([0, 1], repeat=len(keys)):
        active = [k for k, m in zip(keys, mask) if m]
        keep = book(rows, MC, active)
        if len(keep) < 50:
            continue
        s = stats(keep)
        s["active"] = active
        s["n_active"] = len(active)
        books.append(s)
    res["n_books"] = len(books)

    ladder = {}
    for minn in (250, 500, 1000, 2000, 4000):
        cand = [b for b in books if b["h_all_n"] >= minn]
        if not cand:
            continue
        best = max(cand, key=lambda b: b["h_all_mean"])
        keep = book(rows, MC, best["active"])
        best = dict(best)
        best.update(day_stats(keep))
        best["first_emission"] = stats([r for r in keep if r.get("is_first_emission")])
        ladder[f"min{minn}"] = best
    res["best_ladder"] = ladder

    # named reference stacks
    named = {
        "NONE": [],
        "COST_ONLY": ["C1_total_cost_0p15"],
        "COST+NOT_MARKETABLE": ["C1_total_cost_0p15", "C2_block_marketable"],
        "NOT_MARKETABLE_ONLY": ["C2_block_marketable"],
        "DIST0p3_ONLY": ["C4_require_dist_0p3"],
        "DIST1p0_ONLY": ["C5_require_dist_1p0"],
        "COST+DIST0p3": ["C1_total_cost_0p15", "C4_require_dist_0p3"],
        "COST+DIST1p0": ["C1_total_cost_0p15", "C5_require_dist_1p0"],
        "COST+NOTMKT+OFFSESSION": ["C1_total_cost_0p15", "C2_block_marketable", "C6_off_session"],
        "SPREADCORR+NOTMKT": ["C8_spread_corr_0p10", "C2_block_marketable"],
        "ALL_CANDIDATE": keys,
    }
    nm = {}
    for lab, active in named.items():
        keep = book(rows, MC, active)
        s = stats(keep)
        s.update(day_stats(keep))
        s["first_emission"] = stats([r for r in keep if r.get("is_first_emission")])
        s["active"] = active
        nm[lab] = s
    res["named_stacks"] = nm

    with open(os.path.join(D, "L6_CONSTRUCTIVE_V1.json"), "w") as fh:
        json.dump(res, fh, indent=1)

    K = ("h_all_n", "h_all_mean", "h_all_net_corr73_mean", "h_win_pct", "h_gross_mean")
    print("POOL           ", {k: res["POOL"][k] for k in K})
    print("AS_SHIPPED(8)  ", {k: res["AS_SHIPPED_STACK"][k] for k in K},
          "days+", res["AS_SHIPPED_STACK"].get("day_pos_frac"),
          "1stEm", res["AS_SHIPPED_STACK"]["first_emission"]["h_all_mean"])
    print("\n-- named stacks --")
    for lab, s in nm.items():
        print(f"{lab:26s} n={s['h_all_n']:6d} hAll={str(s['h_all_mean']):>9s} hAllNet={str(s['h_all_net_corr73_mean']):>9s} "
              f"win={str(s['h_win_pct']):>6s} days+={str(s.get('day_pos_frac')):>6s} 1stEm_n={s['first_emission']['h_all_n']:5d} 1stEm={s['first_emission']['h_all_mean']}")
    print("\n-- best by size floor --")
    for k, b in ladder.items():
        print(f"{k:8s} n={b['h_all_n']:6d} hAll={b['h_all_mean']} hAllNet={b['h_all_net_corr73_mean']} days+={b.get('day_pos_frac')} :: {b['active']}")


if __name__ == "__main__":
    main()
