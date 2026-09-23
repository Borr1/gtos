#!/usr/bin/env python3
"""W7 INSTRUMENT RESTATEMENT — part 1: the implied-edge inversion.

Measurement only.  Reads the committed W7 recost caches and the estate's own MC
machinery (`scripts/mc_firm_rules.py`, imported unchanged).  Touches no live path,
no config, no broker, no VPS.

WHAT THIS ANSWERS
-----------------
The owner has been shown `p_pass 0.9172` (FTMO, armed three, two-phase) as a fact.
A probability that high is not a property of the barriers -- it is a property of the
DRIFT the simulation was fed.  Nobody has ever published that drift as a number.
This inverts it:

  1. the implied per-trade net R and %/month the published cell assumes;
  2. the driftless floor, measured on the SAME barriers, block bootstrap, daily
     rule and time cap, by demeaning the book-day series and re-running the MC --
     plus the analytic gambler's-ruin benchmark for reference;
  3. `p_pass` recomputed at every edge the estate has actually MEASURED, including
     zero and the live 142-trade broker-true mean of -0.068 R;
  4. the trade-frequency assumption against Lane F's live count.

All scenarios are applied as a per-trade shift to `R_gross` and pushed through the
UNMODIFIED `mc_firm_rules.series()` + `mc()` path, so sizing, kelly bins, cost
pricing, carry and the firm rule ladder are the published ones throughout.
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[8]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import mc_firm_rules as Q          # noqa: E402
import recost_w7_validation as M   # noqa: E402

HERE = Path(__file__).resolve().parent

# The sets. `ARMED_3` is the set every published p_pass names.  `ARMED_4` is what the
# launcher actually runs today (M3 SESSION_M3_ESTATE_RESTATED.md section 1: mx_btcusd
# disarmed 2026-08-05, sub_mid_dn_revert armed on both accounts).
ARMED_3 = ["crypto", "energy_agri", "sub_xvol_pullback"]
ARMED_4 = ARMED_3 + ["sub_mid_dn_revert"]

PUBLISHED = {
    ("FTMO", "ARMED_3"): 0.917167,
    ("redacted_account", "ARMED_3"): 0.9331,
}

N_PATHS = 60_000
SEED = 1


def gambler_ruin(targets, floor):
    """Driftless P(reach every phase target before the static floor).

    Symmetric small steps: P(+a before -b) = b/(a+b).  Each phase resets equity to the
    initial balance, so the floor distance resets too.  Phases are independent.
    """
    p = 1.0
    per = []
    for t in targets:
        q = floor / (t + floor)
        per.append(q)
        p *= q
    return p, per


def cell_rows(rows, keep):
    return [r for r in rows if r["sleeve"] in keep]


def build_series(sub, acct, cm, sd_book, nights="max", forward=True):
    return Q.series(sub, acct, cm, nights, sd_book, forward=forward,
                    kelly=Q.KELLY_HALF, risk_basis=Q.RISK_LIVE_NOMINAL)


def trade_stats(sub, acct, cm, forward=True):
    """Per-trade net R for the cell, at the same carry the cell uses (sleeve max)."""
    vals = []
    for r in sub:
        if forward and r["date"].year < 2025:
            continue
        n = M.SLEEVE_MAX_NIGHTS[r["sleeve"]]
        c, _ = M.row_cost(r, acct, n, "sleeve_median", cm)
        if c is None:
            continue
        vals.append(dict(sleeve=r["sleeve"], gross=r["R_gross"], net=r["R_gross"] - c,
                         cost=c, date=r["date"]))
    return vals


def shifted(rows, delta):
    """Return a shallow copy of rows with every R_gross moved by `delta` R."""
    out = []
    for r in rows:
        q = dict(r)
        q["R_gross"] = r["R_gross"] + delta
        out.append(q)
    return out


def run_cell(sub, acct, cm, sd_book, rules, nights="max", forward=True, paths=N_PATHS):
    days, comb, risk, vs = build_series(sub, acct, cm, sd_book, nights, forward)
    res = Q.mc(comb, risk, rules, paths, seed_base=SEED)
    a, b = min(days), max(days)
    months = (b.year - a.year) * 12 + (b.month - a.month) + 1
    bdpm = len(days) / months
    mean_r = statistics.fmean(comb)
    return dict(book_days=len(days), months=months, book_days_per_month=bdpm,
                mean_r_per_book_day=mean_r, sd_unit_r=statistics.pstdev(comb),
                worst_day=min(comb), risk=risk, vol_scale=vs,
                monthly_pct=100.0 * mean_r * risk * bdpm,
                p_pass=res["p_pass"], se_p_pass=res["se_p_pass"],
                p_fail_dd=res["p_fail_dd"], p_fail_daily=res["p_fail_daily"],
                med_days_pass=res["med_days_pass"],
                first=str(a), last=str(b))


def solve_delta(sub, acct, cm, sd_book, rules, target_p, lo=-1.0, hi=1.0, tol=2e-4,
                paths=20_000):
    """Bisect the per-trade R shift that makes the cell's p_pass equal `target_p`."""
    def f(d):
        days, comb, risk, _ = build_series(shifted(sub, d), acct, cm, sd_book)
        return Q.mc(comb, risk, rules, paths, seed_base=SEED)["p_pass"]
    flo, fhi = f(lo), f(hi)
    if not (flo <= target_p <= fhi):
        return None, flo, fhi
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if abs(fm - target_p) < tol:
            return mid, flo, fhi
        if fm < target_p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi), flo, fhi


def main():
    out = {
        "schema": "gtos.wave21.w7_implied_edge.v1",
        "what": ("Inverts every published W7 p_pass into the per-trade edge it assumes, "
                 "measures the driftless floor on the same barriers, and recomputes "
                 "p_pass at every edge the estate has actually measured."),
        "machinery": "scripts/mc_firm_rules.py imported unchanged; no sealed route edited",
        "n_paths": N_PATHS,
        "measurement_only": True,
    }

    # ---- analytic driftless benchmarks, per firm's MEASURED rules -------------------
    ruin = {}
    for acct in ("FTMO", "redacted_account"):
        _, fr = Q.rule_sets(acct)
        t1, t2, ml = fr["target_ph1"], fr["target_ph2"], fr["maxdd_limit"]
        p1, _ = gambler_ruin((t1,), ml)
        p2, per = gambler_ruin((t1, t2), ml)
        ruin[acct] = dict(target_ph1=t1, target_ph2=t2, max_loss=ml,
                          driftless_phase1=p1, driftless_both_phases=p2,
                          per_phase=per,
                          formula="P(+a before -b) = b/(a+b); equity resets each phase")
    out["analytic_driftless_gamblers_ruin"] = ruin

    # ---- build the book once -------------------------------------------------------
    st = M.build([])
    rows = st["rows"]
    for r in rows:
        r["R_legacy"] = r["R"]
    _, _, _, sd_book = M.build_matrix_from(rows, "R_legacy")
    out["sd_book_reference"] = sd_book

    cms = {}
    for acct in ("FTMO", "redacted_account"):
        pool = {}
        for r in rows:
            c = r[f"cost_{acct}"]
            if c["status"] == "priced":
                pool.setdefault(r["sleeve"], []).append(c["cost_ex_swap_r"])
        cms[acct] = {k: statistics.median(v) for k, v in pool.items()}

    out["books"] = {}
    for label, keep in (("ARMED_3", ARMED_3), ("ARMED_4", ARMED_4)):
        for acct in ("FTMO", "redacted_account"):
            sub = cell_rows(rows, keep)
            cm = cms[acct]
            rules, fr = Q.rule_sets(acct)
            P2 = [r for r in rules if r.label == "P2_BOTH_PHASES"][0]
            L4 = [r for r in rules if r.label == "L4_FIRM_TRUE_PH1"][0]

            base = run_cell(sub, acct, cm, sd_book, P2)
            base_l4 = run_cell(sub, acct, cm, sd_book, L4)

            tv = trade_stats(sub, acct, cm)
            nets = [t["net"] for t in tv]
            grosses = [t["gross"] for t in tv]
            n = len(nets)
            mean_net = statistics.fmean(nets)
            se_net = statistics.pstdev(nets) / math.sqrt(n) if n > 1 else 0.0
            mean_gross = statistics.fmean(grosses)
            se_gross = statistics.pstdev(grosses) / math.sqrt(n) if n > 1 else 0.0
            trades_per_book_day = n / base["book_days"]

            # --- scenarios ------------------------------------------------------------
            scen = {}
            scen["PUBLISHED_INSTRUMENT"] = base

            # zero GROSS edge: every trade's gross R shifted to mean 0, cost still charged
            scen["ZERO_GROSS_EDGE"] = run_cell(shifted(sub, -mean_gross), acct, cm,
                                               sd_book, P2)
            # zero NET edge
            scen["ZERO_NET_EDGE"] = run_cell(shifted(sub, -mean_net), acct, cm,
                                             sd_book, P2)
            # the live broker-true mean: -0.068 R/trade net (Lane F, n=142)
            scen["LIVE_142_TRADE_MEAN_MINUS_0_068R"] = run_cell(
                shifted(sub, -0.068 - mean_net), acct, cm, sd_book, P2)
            # driftless: demean the BOOK-DAY series itself (shape and tails preserved)
            days, comb, risk, _ = build_series(sub, acct, cm, sd_book)
            mu = statistics.fmean(comb)
            dm = [v - mu for v in comb]
            r_dm = Q.mc(dm, risk, P2, N_PATHS, seed_base=SEED)
            b0, b1 = min(days), max(days)
            months = (b1.year - b0.year) * 12 + (b1.month - b0.month) + 1
            scen["DRIFTLESS_DEMEANED_BOOK_DAY_SERIES"] = dict(
                book_days=len(dm), months=months,
                book_days_per_month=len(dm) / months,
                mean_r_per_book_day=0.0, sd_unit_r=statistics.pstdev(dm),
                worst_day=min(dm), risk=risk, monthly_pct=0.0,
                p_pass=r_dm["p_pass"], se_p_pass=r_dm["se_p_pass"],
                p_fail_dd=r_dm["p_fail_dd"], p_fail_daily=r_dm["p_fail_daily"],
                med_days_pass=r_dm["med_days_pass"],
                note=("same barriers, same block bootstrap, same daily rule, same "
                      "sizing; only the location of the book-day distribution is set "
                      "to zero"))

            # --- inversion: what shift reproduces the PUBLISHED number? ---------------
            inv = {}
            pub = PUBLISHED.get((acct, label))
            if pub is not None:
                d, flo, fhi = solve_delta(sub, acct, cm, sd_book, P2, pub)
                inv["published_p_pass"] = pub
                inv["per_trade_R_shift_to_reach_published"] = d
                inv["implied_per_trade_net_R"] = None if d is None else mean_net + d
                inv["bracket_p_pass_at_shift_minus1R"] = flo
                inv["bracket_p_pass_at_shift_plus1R"] = fhi
            # what shift lands on the driftless analytic value?
            d50, _, _ = solve_delta(sub, acct, cm, sd_book, P2,
                                    ruin[acct]["driftless_both_phases"])
            inv["per_trade_R_shift_to_reach_analytic_driftless"] = d50
            inv["implied_per_trade_net_R_at_analytic_driftless"] = (
                None if d50 is None else mean_net + d50)

            out["books"][f"{acct}:{label}"] = dict(
                account=acct, set=label, sleeves=keep,
                firm_rules=fr,
                n_trades_forward_2025_plus=n,
                trades_per_book_day=trades_per_book_day,
                mean_gross_R_per_trade=mean_gross, se_gross=se_gross,
                mean_net_R_per_trade=mean_net, se_net=se_net,
                ci95_net_R_per_trade=[mean_net - 1.96 * se_net, mean_net + 1.96 * se_net],
                mean_cost_R_per_trade=statistics.fmean([t["cost"] for t in tv]),
                published_p_pass=pub,
                p_pass_L4_phase1_this_harness=base_l4["p_pass"],
                scenarios=scen, inversion=inv)

    (HERE / "W7_IMPLIED_EDGE_V1.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: v for k, v in out.items() if k != "books"}, indent=1,
                     default=str))
    for k, b in out["books"].items():
        print(f"\n=== {k} ===")
        print(f"  n_trades(fwd2025+)={b['n_trades_forward_2025_plus']} "
              f"trades/book-day={b['trades_per_book_day']:.3f}")
        print(f"  mean gross R/trade = {b['mean_gross_R_per_trade']:+.4f} "
              f"(se {b['se_gross']:.4f})")
        print(f"  mean NET   R/trade = {b['mean_net_R_per_trade']:+.4f} "
              f"(se {b['se_net']:.4f})  CI95 "
              f"[{b['ci95_net_R_per_trade'][0]:+.4f},{b['ci95_net_R_per_trade'][1]:+.4f}]")
        for sn, s in b["scenarios"].items():
            print(f"    {sn:38s} meanR/bd={s['mean_r_per_book_day']:+.5f} "
                  f"%/mo={s['monthly_pct']:+7.3f}  P2 p_pass={s['p_pass']:.5f} "
                  f"(se {s['se_p_pass']:.5f})")
        print("  inversion:", json.dumps(b["inversion"], default=str))


if __name__ == "__main__":
    main()
