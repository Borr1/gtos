"""h2_final — consolidate the headline cells and the Q3 answer, hour-true."""
from __future__ import annotations

import json
import os
import sys

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h2_lib as H  # noqa: E402
import h2_scan  # noqa: E402
import h2_hourcost as HC  # noqa: E402
import h2_cash as CASH  # noqa: E402


def boot(sub, B=5000, seed=20260806):
    """Day-block bootstrap of mean net_r."""
    rng = np.random.default_rng(seed)
    byday = {}
    for r in sub:
        byday.setdefault(r["day"], []).append(r["g"] - r["c_hr"])
    days = list(byday)
    arrs = [np.array(byday[d]) for d in days]
    n = len(days)
    outv = np.empty(B)
    for b in range(B):
        pick = rng.integers(0, n, n)
        v = np.concatenate([arrs[i] for i in pick])
        outv[b] = v.mean()
    return {"mean": round(float(np.mean([x for a in arrs for x in a])), 6),
            "ci_lo": round(float(np.quantile(outv, 0.025)), 6),
            "ci_hi": round(float(np.quantile(outv, 0.975)), 6),
            "p_le_0": round(float((outv <= 0).mean()), 5), "day_blocks": n, "draws": B}


def main():
    rows = h2_scan.build()
    HC.attach(rows)
    for r in rows:
        r["cash"] = CASH.in_cash(r)
    out = {}

    def blk(sub, label):
        s = HC.restat(sub)
        if s is None:
            return None
        s["label"] = label
        s["share_of_book"] = round(len(sub) / len(rows), 5)
        s["bootstrap"] = boot(sub)
        s["edge_toll_r"] = s["edge_cost_r"]
        s["edge_toll_bps"] = round(s["gross_bps"] / s["cost_bps"], 4) if s["cost_bps"] > 0 else None
        return s

    inn = [r for r in rows if r["cash"] is True]
    H1 = [r for r in inn if r["symbol"] in ("GER40", "NAS100")]
    H2_ = [r for r in inn if r["symbol"] == "GER40"]
    H3 = [r for r in inn if r["symbol"] == "NAS100"]
    H4 = [r for r in inn if r["symbol"] in ("GER40", "NAS100", "UK100", "SPX500", "XAUUSD", "US30_cash")]
    out["headline"] = {
        "GER40_NAS100_cash_open": blk(H1, "GER40+NAS100 inside own cash session"),
        "GER40_cash_open": blk(H2_, "GER40 cash session"),
        "NAS100_cash_open": blk(H3, "NAS100 cash session"),
        "six_index_metal_cash_open": blk(H4, "6 cheapest instruments, cash session"),
        "whole_book": blk(rows, "all 43,755, hour-true"),
        "cash_open_all": blk(inn, "all instruments, cash session only"),
    }
    # month-by-month for the headline
    for k in ("GER40_NAS100_cash_open", "GER40_cash_open", "NAS100_cash_open"):
        pass

    # Q3 answer, hour-true, at the symbol level and the cell level
    sy = H.group(rows, lambda r: r["symbol"])
    st = {s: HC.restat(v) for s, v in sy.items()}
    ks = sorted(st)
    q3 = {
        "symbol_level": {
            "n": len(ks),
            "spearman_gross_bps_vs_cost_bps": H.spearman([st[k]["gross_bps"] for k in ks],
                                                         [st[k]["cost_bps"] for k in ks]),
            "spearman_gross_r_vs_cost_r": H.spearman([st[k]["gross_r"] for k in ks],
                                                     [st[k]["cost_r"] for k in ks]),
            "spearman_net_r_vs_cost_r": H.spearman([st[k]["net_r"] for k in ks],
                                                   [st[k]["cost_r"] for k in ks]),
            "spearman_net_r_vs_cost_bps": H.spearman([st[k]["net_r"] for k in ks],
                                                     [st[k]["cost_bps"] for k in ks]),
        }
    }
    # cost explains what share of cross-sectional net variance?
    gb = np.array([st[k]["gross_bps"] for k in ks])
    cb = np.array([st[k]["cost_bps"] for k in ks])
    nr = np.array([st[k]["net_r"] for k in ks])
    cr = np.array([st[k]["cost_r"] for k in ks])
    q3["symbol_level"]["r2_net_r_on_cost_r"] = round(float(np.corrcoef(nr, cr)[0, 1] ** 2), 4)
    q3["symbol_level"]["r2_net_r_on_gross_r"] = round(
        float(np.corrcoef(nr, np.array([st[k]["gross_r"] for k in ks]))[0, 1] ** 2), 4)
    q3["symbol_level"]["r2_margin_bps_on_cost_bps"] = round(
        float(np.corrcoef(gb - cb, cb)[0, 1] ** 2), 4)
    q3["symbol_level"]["r2_margin_bps_on_gross_bps"] = round(
        float(np.corrcoef(gb - cb, gb)[0, 1] ** 2), 4)
    # within the cash-session window, is the relationship different?
    sy2 = H.group(inn, lambda r: r["symbol"])
    st2 = {s: HC.restat(v) for s, v in sy2.items()}
    k2 = sorted(st2)
    q3["symbol_level_cash_open"] = {
        "n": len(k2),
        "spearman_gross_bps_vs_cost_bps": H.spearman([st2[k]["gross_bps"] for k in k2],
                                                     [st2[k]["cost_bps"] for k in k2]),
        "spearman_net_r_vs_cost_r": H.spearman([st2[k]["net_r"] for k in k2],
                                               [st2[k]["cost_r"] for k in k2]),
    }
    out["q3"] = q3

    # what does the cash rule do to cost and edge, decomposed
    out["cash_rule_decomposition"] = {
        "book_cost_r": round(float(np.mean([r["c_hr"] for r in rows])), 6),
        "cash_cost_r": round(float(np.mean([r["c_hr"] for r in inn])), 6),
        "cost_cut_pct": round(100 * (1 - np.mean([r["c_hr"] for r in inn])
                                     / np.mean([r["c_hr"] for r in rows])), 3),
        "book_gross_r": round(float(np.mean([r["g"] for r in rows])), 6),
        "cash_gross_r": round(float(np.mean([r["g"] for r in inn])), 6),
        "gross_lift_pct": round(100 * (np.mean([r["g"] for r in inn])
                                       / np.mean([r["g"] for r in rows]) - 1), 3),
        "book_kept_pct": round(100 * len(inn) / len(rows), 3),
    }

    with open(os.path.join(D, "H2_FINAL_V1.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    for k, v in out["headline"].items():
        if not v:
            continue
        print("%-28s n=%-6d (%5.1f%%) gross=%+.6f cost=%.6f net=%+.6f  edge:toll R=%.3f bps=%.3f"
              % (k, v["n"], 100 * v["share_of_book"], v["gross_r"], v["cost_r"], v["net_r"],
                 v["edge_toll_r"], v["edge_toll_bps"]))
        print("    tclu=%+.2f  boot95=[%+.6f,%+.6f] P(<=0)=%.4f  d+%d/%d  months %s"
              % (v["t_net_clu"] or 0, v["bootstrap"]["ci_lo"], v["bootstrap"]["ci_hi"],
                 v["bootstrap"]["p_le_0"], v["days_pos_net"], v["days"], v["months"]))
    q = out["q3"]["symbol_level"]
    print("\nQ3 across 24 symbols (hour-true): sp(gross_bps,cost_bps)=%+.3f  sp(gross_r,cost_r)=%+.3f  sp(net_r,cost_r)=%+.3f"
          % (q["spearman_gross_bps_vs_cost_bps"], q["spearman_gross_r_vs_cost_r"],
             q["spearman_net_r_vs_cost_r"]))
    print("   R2(net_r | cost_r)=%.4f   R2(net_r | gross_r)=%.4f   R2(margin_bps | cost_bps)=%.4f   R2(margin_bps | gross_bps)=%.4f"
          % (q["r2_net_r_on_cost_r"], q["r2_net_r_on_gross_r"],
             q["r2_margin_bps_on_cost_bps"], q["r2_margin_bps_on_gross_bps"]))
    c = out["cash_rule_decomposition"]
    print("\ncash rule: keeps %.1f%% of the book, cuts cost %.1f%% (%.6f -> %.6f R), lifts gross %.1f%% (%.6f -> %.6f R)"
          % (c["book_kept_pct"], c["cost_cut_pct"], c["book_cost_r"], c["cash_cost_r"],
             c["gross_lift_pct"], c["book_gross_r"], c["cash_gross_r"]))


if __name__ == "__main__":
    main()
