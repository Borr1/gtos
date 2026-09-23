#!/usr/bin/env python3
"""a1 step 30 - a1-SCORER-V1: the anatomy wave's levers, combined into ONE rule,
priced jointly on January, then read UNCHANGED on February and March (and Apr/May).

    POPULATION  the AT-MARKET (live-expressible) cohort: entry_price == the
                decision-instant market price.  296/296 live captures are at-market
                (l10-X3); the live engine has never placed a pending entry order.

    G  GEO      admit if  risk_distance / range(M1 stamps D-15..D-1) > 0.60
                [x4: refusing geo<=0.60 refuses 23.1 % booking -0.30378]
                knowable AT the decision instant.

    C  CONFIRM  admit if  c0 > -0.15,  c0 = signed R of the close of stamp D
                [x4-F3: refused set -0.66506 vs kept -0.05327 on the whole pool]
                knowable at D + 60 s -- the live book's CURRENT poll cadence.

    S  STOPGONE refuse if the ORIGINAL stop was already traded through in [D, D+k)
                [the at-market analogue of x5's cancel: the immediate fill is
                 adversely selected]

    K  DELAY    market entry at D + 5 min, filling at the close of stamp D+4
                [l7 +0.0670 / x3 +0.0568 / x5 +0.0585 / x4 re-anchor +0.06672]
                risk distance UNCHANGED, so the stop re-anchors to fill - 1R and
                cost_r is invariant across every arm in this file.

    X  EXIT     stop at fill - 1R, NO take-profit, market close at D + 120 min
                [b1 / h6 cell B; trail-free, so no bar-resolution trail premium]

    COST        h1 four-term broker-true (spread_hour + commission + slippage + swap),
                charged once.  Jan/Feb/Mar only; Apr/May priced at hour-true + swap.

Every threshold was published by another lane BEFORE a1 ran.  Nothing is fitted here.
"""
from __future__ import annotations
import json
import os
import sys

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import a1_lib as A  # noqa: E402

MONTHS = ["202601", "202602", "202603", "202604", "202605"]
IS = ["202601"]
OOS = ["202602", "202603"]
OOS2 = ["202604", "202605"]

GEO_TH = 0.60
C0_TH = -0.15
K = 5
CONTRACTS = {
    "STOPONLY": dict(target=None, stop=-1.0),
    "INC": dict(target=2.0, stop=-1.0),
    "T3S1": dict(target=3.0, stop=-1.0),
}


class Arms:
    def __init__(self, mm):
        self.mm = mm
        self.M = A.Month(mm)
        self.cache = {}

    def gross(self, k, contract):
        key = (k, contract)
        if key not in self.cache:
            r, reason, _ = self.M.walk(k, **CONTRACTS[contract])
            self.cache[key] = (r, reason)
        return self.cache[key]

    def gates(self, k=K):
        M = self.M
        return {
            "G": np.nan_to_num(M.geo, nan=0.0) > GEO_TH,
            "C": M.c0 > C0_TH,
            "S": ~M.stopgone(k),
            "ALL": np.ones(M.n, dtype=bool),
        }


def price(a, mask, k, contract, label, cost=None, B=2000):
    M = a.M
    r, reason = a.gross(k, contract)
    c = M.cost if cost is None else cost
    m = mask & np.isfinite(r) & np.isfinite(c)
    out = A.summarize(r[m], c[m], M.day[m], M.rdp[m], reason[m], label=label, B=B)
    out.update(month=a.mm, k=k, contract=contract,
               admit_share=float(m.mean()))
    return out


def main():
    R = {"spec": {"GEO_TH": GEO_TH, "C0_TH": C0_TH, "K": K, "EXIT": "STOPONLY",
                  "population": "at-market (live-expressible)",
                  "cost": "h1 four-term (Jan/Feb/Mar); hour-true+swap (Apr/May)"}}
    arms = {mm: Arms(mm) for mm in MONTHS}

    # ---------------------------------------------------------------- per month
    per = {}
    for mm in MONTHS:
        a = arms[mm]
        g = a.gates()
        book = g["G"] & g["C"] & g["S"]
        rec = {
            "n_pool": a.M.n,
            "BOOK": price(a, book, K, "STOPONLY", "BOOK"),
            "REF_shipped_k0_INC": price(a, g["ALL"], 0, "INC", "REF_shipped_k0_INC"),
            "REF_k0_STOPONLY": price(a, g["ALL"], 0, "STOPONLY", "REF_k0_STOPONLY"),
            "REF_k5_STOPONLY_allrows": price(a, g["ALL"], K, "STOPONLY", "REF_k5_STOPONLY_allrows"),
            "REFUSED_by_book": price(a, ~book, K, "STOPONLY", "REFUSED_by_book"),
            "REFUSED_by_book_at_k0_INC": price(a, ~book, 0, "INC", "REFUSED_by_book_at_k0_INC"),
        }
        # each gate on its own (own rows), plus the set it refuses
        for nm in ("G", "C", "S"):
            rec["GATE_%s_only" % nm] = price(a, g[nm], K, "STOPONLY", "GATE_%s_only" % nm)
            rec["GATE_%s_refused" % nm] = price(a, ~g[nm], K, "STOPONLY", "GATE_%s_refused" % nm)
        # leave-one-out (gate limbs: own rows; contract limbs: BOOK rows)
        rec["LOO_noG"] = price(a, g["C"] & g["S"], K, "STOPONLY", "LOO_noG")
        rec["LOO_noC"] = price(a, g["G"] & g["S"], K, "STOPONLY", "LOO_noC")
        rec["LOO_noS"] = price(a, g["G"] & g["C"], K, "STOPONLY", "LOO_noS")
        for kk in (0, 1, 2, 3, 8, 10, 15, 30):
            gk = a.gates(kk)
            bk = gk["G"] & gk["C"] & gk["S"]
            rec["LOO_k%d" % kk] = price(a, bk, kk, "STOPONLY", "LOO_k%d" % kk)
        for cn in ("INC", "T3S1"):
            rec["LOO_exit_%s" % cn] = price(a, book, K, cn, "LOO_exit_%s" % cn)
        # add-one-in from the shipped reference
        rec["AOI_G"] = price(a, g["G"], 0, "INC", "AOI_G")
        rec["AOI_C"] = price(a, g["C"], 0, "INC", "AOI_C")
        rec["AOI_S"] = price(a, a.gates(0)["S"], 0, "INC", "AOI_S")
        rec["AOI_K"] = price(a, g["ALL"], K, "INC", "AOI_K")
        rec["AOI_X"] = price(a, g["ALL"], 0, "STOPONLY", "AOI_X")
        rec["AOI_KX"] = price(a, g["ALL"], K, "STOPONLY", "AOI_KX")
        rec["AOI_GC"] = price(a, g["G"] & g["C"], 0, "INC", "AOI_GC")
        rec["AOI_GCS_k0INC"] = price(a, g["G"] & g["C"] & a.gates(0)["S"], 0, "INC",
                                     "AOI_GCS_k0INC")
        rec["gate_shares"] = {nm: float(g[nm].mean()) for nm in ("G", "C", "S")}
        rec["book_share"] = float(book.mean())
        per[mm] = rec
        print("%s BOOK n=%d net=%.6f gross=%.6f cost=%.6f  ref_k0INC=%.6f"
              % (mm, rec["BOOK"]["n"], rec["BOOK"]["net_R"], rec["BOOK"]["gross_R"],
                 rec["BOOK"]["cost_R"], rec["REF_shipped_k0_INC"]["net_R"]), flush=True)
    R["per_month"] = per

    # ---------------------------------------------------------------- pooled windows
    def pooled(mms, label, mask_fn, k, contract):
        gs, cs, ds, rd, rs = [], [], [], [], []
        for mm in mms:
            a = arms[mm]
            g = a.gates(k)
            m = mask_fn(a, g)
            r, reason = a.gross(k, contract)
            ok = m & np.isfinite(r)
            gs.append(r[ok]); cs.append(a.M.cost[ok]); ds.append(a.M.day[ok])
            rd.append(a.M.rdp[ok]); rs.append(reason[ok])
        g_ = np.concatenate(gs); c_ = np.concatenate(cs); d_ = np.concatenate(ds)
        rd_ = np.concatenate(rd); rs_ = np.concatenate(rs)
        out = A.summarize(g_, c_, d_, rd_, rs_, label=label, B=4000)
        out["months"] = mms
        return out

    BOOKMASK = lambda a, g: g["G"] & g["C"] & g["S"]          # noqa: E731
    ALLMASK = lambda a, g: g["ALL"]                            # noqa: E731

    R["windows"] = {
        "IS_jan_BOOK": pooled(IS, "IS_jan_BOOK", BOOKMASK, K, "STOPONLY"),
        "OOS_febmar_BOOK": pooled(OOS, "OOS_febmar_BOOK", BOOKMASK, K, "STOPONLY"),
        "OOS2_aprmay_BOOK": pooled(OOS2, "OOS2_aprmay_BOOK", BOOKMASK, K, "STOPONLY"),
        "ALL5_BOOK": pooled(MONTHS, "ALL5_BOOK", BOOKMASK, K, "STOPONLY"),
        "IS_jan_ALL_k0INC": pooled(IS, "IS_jan_ALL_k0INC", ALLMASK, 0, "INC"),
        "OOS_febmar_ALL_k0INC": pooled(OOS, "OOS_febmar_ALL_k0INC", ALLMASK, 0, "INC"),
        "OOS2_aprmay_ALL_k0INC": pooled(OOS2, "OOS2_aprmay_ALL_k0INC", ALLMASK, 0, "INC"),
        "IS_jan_ALL_k5STOP": pooled(IS, "IS_jan_ALL_k5STOP", ALLMASK, K, "STOPONLY"),
        "OOS_febmar_ALL_k5STOP": pooled(OOS, "OOS_febmar_ALL_k5STOP", ALLMASK, K, "STOPONLY"),
        "OOS2_aprmay_ALL_k5STOP": pooled(OOS2, "OOS2_aprmay_ALL_k5STOP", ALLMASK, K, "STOPONLY"),
        "IS_jan_REFUSED": pooled(IS, "IS_jan_REFUSED",
                                 lambda a, g: ~(g["G"] & g["C"] & g["S"]), K, "STOPONLY"),
        "OOS_febmar_REFUSED": pooled(OOS, "OOS_febmar_REFUSED",
                                     lambda a, g: ~(g["G"] & g["C"] & g["S"]), K, "STOPONLY"),
    }

    # ---------------------------------------------------------------- Q3 the trap test
    isw = R["windows"]["IS_jan_BOOK"]
    oosw = R["windows"]["OOS_febmar_BOOK"]
    oos2 = R["windows"]["OOS2_aprmay_BOOK"]
    R["Q3_trap_decomposition"] = {
        "IS_jan": {k: isw[k] for k in ("n", "gross_R", "cost_R", "net_R", "edge_toll")},
        "OOS_febmar": {k: oosw[k] for k in ("n", "gross_R", "cost_R", "net_R", "edge_toll")},
        "OOS2_aprmay": {k: oos2[k] for k in ("n", "gross_R", "cost_R", "net_R", "edge_toll")},
        "delta_net_febmar": oosw["net_R"] - isw["net_R"],
        "edge_component_febmar": oosw["gross_R"] - isw["gross_R"],
        "cost_component_febmar": -(oosw["cost_R"] - isw["cost_R"]),
        "gross_retained_febmar": (oosw["gross_R"] / isw["gross_R"]) if isw["gross_R"] else None,
        "cost_moved_febmar": (oosw["cost_R"] / isw["cost_R"] - 1.0) if isw["cost_R"] else None,
        "delta_net_aprmay": oos2["net_R"] - isw["net_R"],
        "edge_component_aprmay": oos2["gross_R"] - isw["gross_R"],
        "cost_component_aprmay": -(oos2["cost_R"] - isw["cost_R"]),
        "gross_retained_aprmay": (oos2["gross_R"] / isw["gross_R"]) if isw["gross_R"] else None,
        "b1_comparison": {"b1_gross_retained": 0.00308 / 0.11498,
                          "b1_cost_moved": 0.04778 / 0.04646 - 1.0,
                          "b1_delta_net": -0.044700 - 0.068530},
    }

    # ---------------------------------------------------------------- rank persistence
    def per_symbol(mms, k, contract, mask_fn):
        acc = {}
        for mm in mms:
            a = arms[mm]
            g = a.gates(k)
            m = mask_fn(a, g)
            r, _ = a.gross(k, contract)
            for s in np.unique(a.M.symbol[m]):
                sm = m & (a.M.symbol == s)
                acc.setdefault(s, {"g": [], "c": []})
                acc[s]["g"].append(r[sm])
                acc[s]["c"].append(a.M.cost[sm])
        return {s: {"n": int(sum(len(x) for x in v["g"])),
                    "gross": float(np.concatenate(v["g"]).mean()),
                    "cost": float(np.concatenate(v["c"]).mean())}
                for s, v in acc.items()}

    rp = {}
    for tag, k, cn in (("book_contract_k5_STOPONLY", K, "STOPONLY"),
                       ("shipped_k0_INC", 0, "INC")):
        a_is = per_symbol(IS, k, cn, ALLMASK)
        a_oo = per_symbol(OOS, k, cn, ALLMASK)
        common = sorted(set(a_is) & set(a_oo))
        common = [s for s in common if a_is[s]["n"] >= 30 and a_oo[s]["n"] >= 30]
        rp[tag] = {
            "n_instruments": len(common),
            "spearman_cost": A.spearman([a_is[s]["cost"] for s in common],
                                        [a_oo[s]["cost"] for s in common]),
            "spearman_gross": A.spearman([a_is[s]["gross"] for s in common],
                                         [a_oo[s]["gross"] for s in common]),
            "per_symbol_IS": {s: a_is[s] for s in common},
            "per_symbol_OOS": {s: a_oo[s] for s in common},
        }
    R["rank_persistence_IS_vs_OOS"] = rp

    with open(os.path.join(D, "A1_BOOK_V1.json"), "w") as f:
        json.dump(R, f, indent=1)
    print("\n--- windows ---")
    for k, v in R["windows"].items():
        print("%-26s n=%6d net=%+.6f gross=%+.6f cost=%.6f ratio=%6.3f t_day=%+.2f p=%.3f"
              % (k, v["n"], v["net_R"], v["gross_R"], v["cost_R"],
                 v["edge_toll"], v["t_day"], v["p_net_le0"]))
    print("\n--- Q3 ---")
    print(json.dumps(R["Q3_trap_decomposition"], indent=1))
    print("\n--- rank persistence ---")
    for k, v in rp.items():
        print(k, "cost", round(v["spearman_cost"], 4), "gross", round(v["spearman_gross"], 4),
              "n_inst", v["n_instruments"])


if __name__ == "__main__":
    main()
