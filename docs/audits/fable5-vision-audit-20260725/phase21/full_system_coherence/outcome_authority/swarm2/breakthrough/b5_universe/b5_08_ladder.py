"""B5 step (b3) — the detectability ladder recomputed on the expanded universe.

Lane 4's design, unchanged: two-sided alpha 0.05, power 80 %, so n = k*(sigma/mu)^2 with
k = (z_0.975 + z_0.80)^2 = 7.8489 bets.  Correlation enters only through the effective-bet
count, never by assumption.  Annualised IR = (mu/sigma) * sqrt(bets per year).

Anchors carried from Lane 4 so the rows compare:
  armed 3 sleeves, FTMO, per book-day : IC +0.2798, 46.0 eff bets/yr, IR 1.898, 26.15 months
  funnel, measured within-window edge : IC +0.0026, 22,169 eff bets/yr, IR 0.390, 620.45 months
  six-week answer requires             : IR 7.92  (= 17.4x the armed book's effective breadth)

Writes <OUT>/B5_LADDER_V1.json.
"""
import json, math, os, glob

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "b5_receipts")
K = 7.8489
TRADING_DAYS = 252.0

LANE4 = {
    "armed_3_FTMO_per_book_day": {"ic": 0.2798, "eff_bets_yr": 46.0, "ir": 1.898, "months": 26.15},
    "armed_3_r1_archive_per_trade": {"ic": 0.4656, "eff_bets_yr": 55.6, "ir": 3.473, "months": 7.81},
    "nine_sleeve_out_of_selection": {"ic": 0.0863, "eff_bets_yr": 790.0, "ir": 2.426, "months": 16.00},
    "all_29_sleeves_day_level": {"ic": -0.0636, "eff_bets_yr": 110.3, "ir": -0.668, "months": 211.24},
    "funnel_measured": {"ic": 0.0026, "eff_bets_yr": 22169.0, "ir": 0.390, "months": 620.45},
}


def ladder_from_cell(cell, span_years):
    """A rebalance is the bet.  IC = mean/SD per rebalance; rate = rebalances per year."""
    n = cell["n_rebal"]
    m = cell["gross_mean_volnorm"]
    t = cell["gross_t"]
    if not t or not n:
        return None
    sd = abs(m) * math.sqrt(n) / abs(t)
    ic = abs(m) / sd
    rate = n / span_years
    ir = ic * math.sqrt(rate)
    months = 12.0 * K / (ic * ic * rate) if ic > 0 else None
    out = {"n_rebal": n, "span_years": round(span_years, 2), "rebalances_per_year": round(rate, 2),
           "gross_abs_mean": abs(m), "sd_per_rebal": sd, "IC_per_bet": ic,
           "IR_annualised": ir, "months_to_powered_answer": months,
           "breadth_multiple_for_six_weeks": (ir and (7.92 / ir) ** 2) or None}
    nm = cell.get("net_mean_volnorm")
    if nm is not None:
        net_trade_dir = abs(m) - abs(m - nm)
        ic_n = net_trade_dir / sd
        out["net_in_tradeable_direction"] = net_trade_dir
        out["cost_per_rebal_volunits"] = abs(m - nm)
        out["IC_per_bet_net"] = ic_n
        out["IR_annualised_net"] = ic_n * math.sqrt(rate)
        out["months_to_powered_answer_net"] = (12.0 * K / (ic_n * ic_n * rate)) if ic_n > 0 else None
    return out


def years(a, b):
    import datetime
    d0 = datetime.date(int(a[:4]), int(a[5:7]), int(a[8:10]))
    d1 = datetime.date(int(b[:4]), int(b[5:7]), int(b[8:10]))
    return max((d1 - d0).days / 365.25, 0.5)


def main():
    eig = json.load(open(os.path.join(OUT, "B5_EIGEN_BREADTH_V1.json")))["universes"]
    var = json.load(open(os.path.join(OUT, "B5_EFFECTIVE_BREADTH_V1.json")))["universes"]
    res = {"design": {"alpha": 0.05, "power": 0.80, "k": K,
                      "definition": "n = k*(sigma/mu)^2 bets; IR = IC*sqrt(bets/yr); "
                                    "months = 12*k/(IC^2 * bets_per_yr)"},
           "lane4_anchors": LANE4, "breadth": {}, "cells": {}}

    # --- breadth side: effective bets per year on each universe, both instruments
    for u in eig:
        e, v = eig.get(u), var.get(u)
        if not e:
            continue
        row = {
            "n_symbols": e["n_symbols_used"],
            "lane4_variance_ratio_N_eff_per_day": (v or {}).get("RAW", {}).get("N_eff_per_day") if v else None,
            "eigen_N_eff_all_factors": e["N_eff_ALL_FACTORS"],
            "eigen_N_eff_ex_market": e["N_eff_EX_MARKET"],
            "eigen_N_eff_ex_top3": e["N_eff_EX_TOP3"],
            "mean_pairwise_corr": e["mean_pairwise_corr"],
            "pc1_variance_share": e["top_eigenvalue_share"],
        }
        for kk, lab in (("eigen_N_eff_all_factors", "directional"),
                        ("eigen_N_eff_ex_market", "market_neutral")):
            row[f"eff_bets_per_year_{lab}"] = row[kk] * TRADING_DAYS
            row[f"breadth_multiple_vs_armed_book_{lab}"] = row[kk] * TRADING_DAYS / LANE4["armed_3_FTMO_per_book_day"]["eff_bets_yr"]
        res["breadth"][u] = row

    # --- ladder side: every measured XS cell
    for path in sorted(glob.glob(os.path.join(OUT, "xs_cells", "*.json"))):
        d = json.load(open(path))
        for sig, cell in d.get("cells", {}).items():
            sp = years(cell["first"][:10], cell["last"][:10])
            L = ladder_from_cell(cell, sp)
            if L:
                L["perm_p"] = cell["perm_p_two_sided"]
                L["gross_t"] = cell["gross_t"]
                L["turnover"] = cell["turnover"]
                res["cells"][f"{d['universe']}|{sig}"] = L
    for path in [os.path.join(OUT, "B5_COSTVOL_AND_KILLS_V1.json")]:
        if os.path.exists(path):
            d = json.load(open(path))
            for name, cell in d["cells"].items():
                sp = years(cell["first"][:10], cell["last"][:10])
                L = ladder_from_cell(cell, sp)
                if L:
                    L["perm_p"] = cell["perm_p_two_sided"]
                    L["gross_t"] = cell["gross_t"]
                    L["turnover"] = cell["turnover"]
                    res["cells"][name] = L

    json.dump(res, open(os.path.join(OUT, "B5_LADDER_V1.json"), "w"), indent=1)

    print(f"{'universe':30s} {'K':>4s} {'Neff_dir':>9s} {'Neff_neut':>9s} {'effbets/yr':>11s} {'xArmedBook':>11s}")
    for u, r in res["breadth"].items():
        print(f"{u:30s} {r['n_symbols']:4d} {r['eigen_N_eff_all_factors']:9.2f} {r['eigen_N_eff_ex_market']:9.2f} "
              f"{r['eff_bets_per_year_directional']:11.0f} {r['breadth_multiple_vs_armed_book_directional']:11.1f}")
    print()
    print(f"{'cell':42s} {'IC':>8s} {'reb/yr':>7s} {'IR':>7s} {'months':>8s} {'IRnet':>7s} {'monthsNet':>10s}")
    keep = sorted(res["cells"].items(), key=lambda kv: -(kv[1].get("IR_annualised") or 0))
    for k2, v in keep[:22]:
        print(f"{k2:42s} {v['IC_per_bet']:8.4f} {v['rebalances_per_year']:7.1f} {v['IR_annualised']:7.3f} "
              f"{v['months_to_powered_answer']:8.1f} "
              f"{(('%7.3f' % v['IR_annualised_net']) if v.get('IR_annualised_net') is not None else '     NA')} "
              f"{(('%10.1f' % v['months_to_powered_answer_net']) if v.get('months_to_powered_answer_net') else '        NA')}")


if __name__ == "__main__":
    main()
