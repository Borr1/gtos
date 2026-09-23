"""S7 - the nearest constructive variants at the cost frontier, and the
correlation of the surviving series to the armed book.

S6 established the crypto XS reversal's breakeven is an average weighted leg
spread of 25.77 bp on the full sample and 6.57 bp on 2023-2026.  Only BTCUSD
(0.16 bp) and ETHUSD (3.49 bp) are inside that on FTMO's book.  This file asks
the only remaining constructive question: is there a cost-feasible sub-universe
where the thing still pays, and does its return stream diversify the armed four.
"""
from __future__ import annotations
import gzip, json, math, os, sys, collections
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = "/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725"
from xs import build_matrices, make_returns       # noqa: E402
from rule import spread_table, run, stats         # noqa: E402

OUT = os.path.join(HERE, "receipts")
np.seterr(all="ignore")
ARMED = ["crypto", "energy_agri", "sub_mid_dn_revert", "sub_xvol_pullback"]


def armed_daily():
    """Per-day mean gross R for each armed sleeve, from the estate artifact of
    record (R1_ESTATE_ROWS_V2, whose r_old is asserted bit-identical to AQ's
    r_gross).  Keyed on the UTC entry date."""
    p = f"{REPO}/docs/audits/fable5-vision-audit-20260725/phase20/forward/receipts/R1_ESTATE_ROWS_V2.json.gz"
    rows = json.load(gzip.open(p, "rt"))
    acc = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        s = r.get("sleeve")
        if s not in ARMED:
            continue
        d = str(r.get("entry_utc", ""))[:10]
        if len(d) == 10:
            acc[s][d].append(float(r.get("r_old", np.nan)))
    out = {}
    for s in ARMED:
        out[s] = pd.Series({d: float(np.mean(v)) for d, v in acc[s].items()}).sort_index()
    return out


def main():
    M = make_returns(build_matrices())
    SP, PROV = spread_table(M)
    res = {}

    print("=== S7a: cost-feasible sub-universes, true per-leg spreads charged ===")
    UNIS = {
        "BTC_ETH": ["BTCUSD", "ETHUSD"],
        "CHEAP4_le7bp": ["BTCUSD", "ETHUSD", "DOTUSD", "ADAUSD"],
        "CHEAP6_le20bp": ["BTCUSD", "ETHUSD", "DOTUSD", "ADAUSD", "XTZUSD", "LTCUSD"],
        "COSTKNOWN8": [s for s in SP if s in set(M["syms"][M["CL"] == "crypto"])],
    }
    rows = []
    for nm, u in UNIS.items():
        u = [s for s in u if s in SP]
        qz = 2 if len(u) <= 4 else 3
        for window, (a, b) in {"FULL": (None, None),
                               "TEST_2023_2026": ("2023-01-01", "2026-07-01")}.items():
            df = run(M, SP, quant=qz, keep=set(u), min_univ=min(len(u), 2), start=a, end=b)
            if df is None:
                print(f"  {nm:14s} {window:14s} insufficient"); continue
            st = stats(df, f"{nm}|q{qz}|{window}")
            st["universe"] = u
            st["mean_leg_spread_bp"] = float(np.mean([SP[s] for s in u]))
            rows.append(st)
            print(f"  {nm:14s} {window:14s} n={st['n_days']:5d} gross {st['gross_bp']:+8.2f} "
                  f"cost {st['cost_bp']:6.2f} net {st['net_bp']:+8.2f} bp/day  t {st['t_net']:+5.2f} "
                  f"SR {st['sharpe_net_ann']:+5.2f}  yrs {st['pos_years']}/{st['tot_years']}")
    res["cost_feasible_cells"] = rows

    print("\n=== S7b: what the FULL-universe book needs, restated as a requirement ===")
    d0 = run(M, SP, quant=5, impute_bp=0.0, cost_mult=0.0)
    dT = run(M, SP, quant=5, impute_bp=0.0, cost_mult=0.0, start="2023-01-01", end="2026-07-01")
    for nm, d in (("FULL_SAMPLE", d0), ("TEST_2023_2026", dT)):
        need = d.gross_bp.mean() / 2.0
        res[f"required_leg_spread_bp_{nm}"] = float(need)
        print(f"  {nm:15s}: gross {d.gross_bp.mean():+7.2f} bp/day -> needs a weighted "
              f"leg spread below {need:6.2f} bp. FTMO offers that on "
              f"{[s for s in SP if SP[s] < need and s in set(M['syms'][M['CL']=='crypto'])]}")

    print("\n=== S7c: correlation of the crypto XS stream to the armed four ===")
    arm = armed_daily()
    ser = d0.set_index("date").gross_bp     # zero-cost stream: the most generous case
    serT = dT.set_index("date").gross_bp
    cors = {}
    for s in ARMED:
        a = arm[s]
        for nm, x in (("FULL", ser), ("TEST_2023_2026", serT)):
            j = pd.concat([x.rename("v"), a.rename("arm")], axis=1, join="inner").dropna()
            if len(j) < 20:
                cors[f"{s}|{nm}"] = dict(n=len(j), rho=None); continue
            rho = float(np.corrcoef(j["v"], j["arm"])[0, 1])
            cors[f"{s}|{nm}"] = dict(n=int(len(j)), rho=rho,
                                     p_approx=float(2 * (1 - _ncdf(abs(rho) * math.sqrt(max(len(j) - 2, 1))))))
            print(f"  {s:20s} {nm:14s} n={len(j):5d} rho={rho:+.4f}")
    res["correlation_to_armed"] = cors
    # armed book aggregate (equal weight of the four, days where any fires)
    A = pd.concat([arm[s].rename(s) for s in ARMED], axis=1).sort_index()
    book = A.mean(axis=1, skipna=True)
    for nm, x in (("FULL", ser), ("TEST_2023_2026", serT)):
        j = pd.concat([x.rename("v"), book.rename("book")], axis=1, join="inner").dropna()
        if len(j) >= 20:
            rho = float(np.corrcoef(j["v"], j["book"])[0, 1])
            res[f"rho_vs_armed_book_{nm}"] = dict(n=int(len(j)), rho=rho)
            print(f"  {'ARMED BOOK (mean of 4)':20s} {nm:14s} n={len(j):5d} rho={rho:+.4f}")

    print("\n=== S7d: overlap days -- how often does the XS book even coincide? ===")
    res["armed_trade_days"] = {s: int(len(arm[s])) for s in ARMED}
    print("  armed sleeve trade-days:", res["armed_trade_days"])
    print("  crypto XS book-days:", len(d0), "(daily by construction)")

    json.dump(res, open(f"{OUT}/S7_FRONTIER_AND_CORRELATION.json", "w"), indent=1, default=str)
    print("\nwritten", f"{OUT}/S7_FRONTIER_AND_CORRELATION.json")


def _ncdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


if __name__ == "__main__":
    main()
