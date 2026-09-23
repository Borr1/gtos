#!/usr/bin/env python3
"""d7 — WHAT WOULD HAVE TO BE TRUE.

Inverse reasoning on the CORRECT population (f1's per-row roster walks, 8 open windows,
day-restricted to each sealed arm's own trading days). Nothing sampled.

Stage 1: load + the exact baseline algebra + every single-lever solve.
Writes /tmp/d7/D7_STAGE1.json
"""
import gzip, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = os.path.join(HERE, "f1_rows")
OUT = "/tmp/d7"
os.makedirs(OUT, exist_ok=True)

WINDOWS = ["2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05"]
POI = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}
DEFECT = "current_breaker_re_entry"


def load():
    days = json.load(open(os.path.join(HERE, "f1_ARM_TRADING_DAYS_V1.json")))
    syms, fams = {}, {}
    S, F, W, D, G, C, FI, PA, RE = [], [], [], [], [], [], [], [], []
    reasons = {}
    for wi, w in enumerate(WINDOWS):
        ok = set(days[w])
        with gzip.open(os.path.join(ROWS, f"RR_{w}.json.gz"), "rt") as f:
            arr = json.load(f)
        kept = 0
        for r in arr:
            if r["day"] not in ok:
                continue
            kept += 1
            s = r["sym"]
            if s not in syms:
                syms[s] = len(syms)
            fa = r["fam"]
            if fa not in fams:
                fams[fa] = len(fams)
            rr = r["reason"]
            if rr not in reasons:
                reasons[rr] = len(reasons)
            S.append(syms[s]); F.append(fams[fa]); W.append(wi)
            D.append(r["d_bps"]); G.append(r["g"]); C.append(r["c"])
            FI.append(1 if r["filled"] else 0); PA.append(1 if r["past"] else 0)
            RE.append(reasons[rr])
        del arr
        print(f"  {w}: kept {kept}", file=sys.stderr)
    d = dict(
        sym=np.array(S, dtype=np.int16), fam=np.array(F, dtype=np.int8),
        win=np.array(W, dtype=np.int8), d_bps=np.array(D, dtype=np.float64),
        g=np.array(G, dtype=np.float64), c=np.array(C, dtype=np.float64),
        filled=np.array(FI, dtype=bool), past=np.array(PA, dtype=bool),
        reason=np.array(RE, dtype=np.int8),
        syms={v: k for k, v in syms.items()}, fams={v: k for k, v in fams.items()},
        reasons={v: k for k, v in reasons.items()},
    )
    return d


def stats(g, c, label, n_days=None):
    """Full economic + breakeven algebra for one cohort."""
    n = len(g)
    if n == 0:
        return {"tag": label, "n": 0}
    G = float(g.mean()); C = float(c.mean()); N = G - C
    net = g - c
    win = g > 0
    nw = int(win.sum())
    p = nw / n
    a = float(g[win].mean()) if nw else 0.0            # mean winner size (gross R)
    lose = ~win
    b = float((-g[lose]).mean()) if int(lose.sum()) else 0.0   # mean loser size (>=0)
    payoff = a / b if b > 0 else float("inf")
    be_gross = b / (a + b) if (a + b) > 0 else float("nan")     # p for gross = 0
    be_net = (b + C) / (a + b) if (a + b) > 0 else float("nan")  # p for net = 0
    # standard errors
    sd_g = float(g.std(ddof=1)) if n > 1 else float("nan")
    sd_n = float(net.std(ddof=1)) if n > 1 else float("nan")
    se_g = sd_g / math.sqrt(n); se_n = sd_n / math.sqrt(n)
    return {
        "tag": label, "n": n,
        "gross": G, "cost": C, "net": N,
        "gross_total": float(g.sum()), "net_total": float(net.sum()),
        "win_rate": p, "n_win": nw,
        "winner_mean_a": a, "loser_mean_b": b, "payoff": payoff,
        "breakeven_gross": be_gross, "breakeven_net": be_net,
        "gap_gross_pp": (p - be_gross) * 100.0, "gap_net_pp": (p - be_net) * 100.0,
        "sd_gross": sd_g, "se_gross": se_g, "t_gross": G / se_g if se_g else float("nan"),
        "sd_net": sd_n, "se_net": se_n, "t_net": N / se_n if se_n else float("nan"),
        "ci95_net": [N - 1.96 * se_n, N + 1.96 * se_n],
        "median_d_bps": float(np.median(np.asarray(g) * 0 + 0)) if False else None,
    }


def solve_levers(st):
    """Given a cohort's algebra, solve every single lever for net == 0."""
    p, a, b, C, G = st["win_rate"], st["winner_mean_a"], st["loser_mean_b"], st["cost"], st["gross"]
    n = st["n"]
    out = {}
    deficit = C - G          # R/trade that must be found
    out["deficit_r_per_trade"] = deficit

    # L1 WIN RATE ------------------------------------------------------------
    p_req = (b + C) / (a + b)
    out["L1_win_rate"] = {
        "current": p, "required": p_req, "delta_pp": (p_req - p) * 100.0,
        "multiple": p_req / p if p else float("nan"),
        "relative_lift_pct": (p_req / p - 1.0) * 100.0 if p else float("nan"),
        "share_of_book_that_must_convert_loser_to_winner": deficit / (a + b),
        "feasible": p_req <= 1.0,
    }
    # L2 WINNER SIZE (payoff up, losers unchanged) ---------------------------
    a_req = (C + (1 - p) * b) / p if p else float("inf")
    out["L2_winner_size"] = {
        "current_a": a, "required_a": a_req, "multiple": a_req / a if a else float("inf"),
        "current_payoff": a / b if b else float("inf"),
        "required_payoff": a_req / b if b else float("inf"),
        "payoff_multiple": (a_req / b) / (a / b) if a and b else float("inf"),
        "feasible": True,
    }
    # L3 LOSER SIZE (stop efficiency) ---------------------------------------
    b_req = (p * a - C) / (1 - p) if p < 1 else float("inf")
    out["L3_loser_size"] = {
        "current_b": b, "required_b": b_req,
        "multiple": b_req / b if b else float("nan"),
        "reduction_pct": (1 - b_req / b) * 100.0 if b else float("nan"),
        "feasible": b_req > 0,
        "gross_win_contribution_pa": p * a,
        "note": ("INFEASIBLE: even a zero-loss stop (b=0) leaves net = p*a - C = "
                 f"{p*a - C:+.5f}") if b_req <= 0 else "",
        "net_at_b_zero": p * a - C,
    }
    # L4 COST ----------------------------------------------------------------
    out["L4_cost"] = {
        "current_C": C, "required_C": G,
        "reduction_needed_pct": (1 - G / C) * 100.0 if C else float("nan"),
        "multiple_cheaper": C / G if G > 0 else float("inf"),
        "feasible": G > 0,
        "net_at_zero_cost": G,
        "note": "" if G > 0 else "INFEASIBLE: gross is <= 0, so even a FREE broker leaves the book at the gross.",
    }
    # L5 SAMPLE SIZE required to RESOLVE the deficit --------------------------
    sd = st["sd_net"]
    if deficit > 0 and sd == sd:
        n_res = (1.96 * sd / (deficit / 2.0)) ** 2   # CI95 half-width = half the required move
        n_sign = (1.96 * sd / deficit) ** 2          # CI95 half-width = the required move
        out["L5_resolution"] = {
            "sd_net": sd, "n_for_ci_halfwidth_eq_deficit": n_sign,
            "n_for_ci_halfwidth_eq_half_deficit": n_res,
            "current_n": n,
            "multiple_of_current_n": n_sign / n if n else float("nan"),
        }
    return out


def main():
    print("loading...", file=sys.stderr)
    d = load()
    n_all = len(d["g"])
    print(f"total rows {n_all}", file=sys.stderr)

    famname = np.array([d["fams"][i] for i in range(len(d["fams"]))])
    fam_of = famname[d["fam"]]
    is_defect = fam_of == DEFECT
    is_poi = np.isin(fam_of, list(POI))

    filled = d["filled"]
    clean = filled & (~d["past"]) & (~is_defect)
    atmkt = clean & (~is_poi)

    g, c = d["g"], d["c"]
    res = {"schema": "gtos.wave19.d7.stage1.v1", "windows": WINDOWS,
           "row_count_day_restricted": int(n_all)}

    cohorts = {
        "EMISSIONS_ALL": np.ones(n_all, dtype=bool),
        "FILLS_ALL": filled,
        "CLEAN": clean,
        "CLEAN_ATMARKET": atmkt,
        "CLEAN_POI": clean & is_poi,
        "DEFECT_FAMILY": filled & is_defect,
    }
    res["cohorts"] = {}
    for k, m in cohorts.items():
        st = stats(g[m], c[m], k)
        st["median_d_bps"] = float(np.median(d["d_bps"][m]))
        st["mean_d_bps"] = float(d["d_bps"][m].mean())
        st["toll_bps"] = float((c[m] * d["d_bps"][m]).mean())  # cost in price-bps
        st["levers"] = solve_levers(st)
        res["cohorts"][k] = st

    # ---- per window on CLEAN -------------------------------------------------
    res["clean_by_window"] = {}
    for wi, w in enumerate(WINDOWS):
        m = clean & (d["win"] == wi)
        st = stats(g[m], c[m], w)
        st["toll_bps"] = float((c[m] * d["d_bps"][m]).mean())
        res["clean_by_window"][w] = st

    # ---- per family / per symbol on CLEAN-equivalent -------------------------
    def by(keyarr, names, mask, tag):
        out = {}
        for i, nm in names.items():
            m = mask & (keyarr == i)
            if m.sum() < 30:
                continue
            st = stats(g[m], c[m], nm)
            st["median_d_bps"] = float(np.median(d["d_bps"][m]))
            st["toll_bps"] = float((c[m] * d["d_bps"][m]).mean())
            st["share_of_pop"] = float(m.sum()) / float(mask.sum())
            out[nm] = st
        return out

    res["by_family_fills"] = by(d["fam"], d["fams"], filled, "family")
    res["by_symbol_clean"] = by(d["sym"], d["syms"], clean, "symbol")
    res["by_family_clean"] = by(d["fam"], d["fams"], clean, "family_clean")

    with open(os.path.join(OUT, "D7_STAGE1.json"), "w") as f:
        json.dump(res, f, indent=1, default=float)

    # cache arrays for stage 2
    np.savez_compressed(os.path.join(OUT, "d7_arrays.npz"),
                        sym=d["sym"], fam=d["fam"], win=d["win"], d_bps=d["d_bps"],
                        g=g, c=c, filled=filled, past=d["past"], reason=d["reason"],
                        clean=clean, atmkt=atmkt, is_poi=is_poi, is_defect=is_defect)
    json.dump({"syms": d["syms"], "fams": d["fams"], "reasons": d["reasons"]},
              open(os.path.join(OUT, "d7_names.json"), "w"), default=str)

    # console summary
    for k in ["FILLS_ALL", "CLEAN", "CLEAN_ATMARKET"]:
        s = res["cohorts"][k]
        L = s["levers"]
        print(f"\n{k}: n={s['n']} gross={s['gross']:+.5f} cost={s['cost']:.5f} net={s['net']:+.5f}")
        print(f"  p={s['win_rate']:.5f} a={s['winner_mean_a']:.5f} b={s['loser_mean_b']:.5f} "
              f"payoff={s['payoff']:.4f} be_gross={s['breakeven_gross']:.5f} be_net={s['breakeven_net']:.5f}")
        print(f"  deficit={L['deficit_r_per_trade']:+.5f}  L1 need p={L['L1_win_rate']['required']:.5f} "
              f"(+{L['L1_win_rate']['delta_pp']:.3f}pp, x{L['L1_win_rate']['multiple']:.4f})")
        print(f"  L2 need a={L['L2_winner_size']['required_a']:.4f} (x{L['L2_winner_size']['multiple']:.4f})  "
              f"L3 b_req={L['L3_loser_size']['required_b']:+.4f} feasible={L['L3_loser_size']['feasible']}  "
              f"L4 cost_feasible={L['L4_cost']['feasible']} net@C=0 {L['L4_cost']['net_at_zero_cost']:+.5f}")


if __name__ == "__main__":
    main()
