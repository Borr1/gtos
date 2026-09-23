#!/usr/bin/env python3
"""Restate the armed book's economics over the universe each ACCOUNT can actually trade.

Method: the published machinery, unmodified, driven on a symbol-filtered row set.
`mc_firm_rules.build_cells` is not called; its body is reproduced here for the named books
only, so the filter can be inserted at the one seam where `sym` exists
(`recost_w7_validation.build([])["rows"]`).  Every convention -- cost map, nights, kelly
bins, risk basis, dial, seed_base, path count -- is the published one, and the AS_PUBLISHED
row of the output is the control that proves it.
"""
import json
import statistics
import sys
from pathlib import Path

REPO = Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import recost_w7_validation as M          # noqa: E402
import mc_firm_rules as Q                 # noqa: E402
from src.components.ultimate_book.sleeves.registry import active_specs  # noqa: E402
from src.safety.armed_set import armed_sleeves  # noqa: E402

PATHS = int(sys.argv[1]) if len(sys.argv) > 1 else 40000

ARMED4 = sorted(armed_sleeves())
ARMED3 = ["crypto", "energy_agri", "sub_xvol_pullback"]          # the published book
# MEASURED 2026-08-11 on the live redacted_account terminal (symbols_get exhaustion, 76 symbols):
# none of these 7 exists on that broker under any probed name.
FN_BROKER_ABSENT = {"XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD", "CORN_c", "COTTON_c", "DASHUSD"}

SURFACE = {s.tag: set(s.on_surface)
           for s in active_specs(ARMED4, include_candidate_book=True,
                                 include_market_expansion_book=True)}

st = M.build([])
ROWS = st["rows"]
for r in ROWS:
    r["R_legacy"] = r["R"]
_, _, _, SD_BOOK = M.build_matrix_from(ROWS, "R_legacy")


def universe_filter(name):
    """Row predicate for one universe. `sym` is the cache's canonical symbol."""
    if name == "AS_PUBLISHED":
        return lambda r: True
    if name == "CURRENT_SURFACE":
        return lambda r: r["sym"] in SURFACE.get(r["sleeve"], set())
    if name == "FN_TRADEABLE":
        return lambda r: (r["sym"] in SURFACE.get(r["sleeve"], set())
                          and r["sym"] not in FN_BROKER_ABSENT)
    raise SystemExit(name)


def cost_map(acct, rows):
    return {k: statistics.median(v) for k, v in Q._priced_pool(rows, acct).items()}


def cell(sub, acct, cm, nights, forward, kelly, basis):
    days, comb, risk, vs = Q.series(sub, acct, cm, nights, SD_BOOK,
                                    forward=forward, kelly=kelly, risk_basis=basis)
    a, b = min(days), max(days)
    months = (b.year - a.year) * 12 + (b.month - a.month) + 1
    return dict(comb=comb, risk=risk, vol_scale=vs, book_days=len(days),
                weekday_sessions=Q.weekday_sessions(a, b),
                book_days_per_calendar_month=len(days) / months,
                mean_r_per_book_day=statistics.fmean(comb),
                worst_day_unit_r=min(comb), best_day_unit_r=max(comb),
                sd_unit_r=statistics.pstdev(comb),
                window="forward_2025+" if forward else "full_2015_2026",
                nights="sleeve_max" if nights == "max" else nights)


out = {
    "schema": "gtos.live_book_integrity.fn_universe_restatement.v1",
    "generated_by": "phase21/.../swarm/live_book_integrity_receipts/restate_fn_universe.py",
    "mc_paths": PATHS,
    "dial_pct": Q.DIAL * 100,
    "sd_book_reference": round(SD_BOOK, 5),
    "convention": {"kelly": Q.KELLY_HALF, "risk_basis": Q.RISK_LIVE_NOMINAL,
                   "why": "the DEPLOYABLE convention -- the one the live book implements; "
                          "BOOKS_MC_V1.json's cache_books.live_nominal_half_kelly"},
    "fn_broker_absent_symbols": sorted(FN_BROKER_ABSENT),
    "armed_sleeves_declared": ARMED4,
    "surface": {k: sorted(v) for k, v in SURFACE.items()},
    "row_census": {},
    "cells": [],
}

# ---- row census: how much of the published population each universe keeps ----
for book_name, book in (("ARMED_3_PUBLISHED", ARMED3), ("ARMED_4_DECLARED", ARMED4)):
    cens = {}
    base = [r for r in ROWS if r["sleeve"] in book]
    for uname in ("AS_PUBLISHED", "CURRENT_SURFACE", "FN_TRADEABLE"):
        f = universe_filter(uname)
        kept = [r for r in base if f(r)]
        cens[uname] = {
            "trades": len(kept),
            "pct_of_published": round(100.0 * len(kept) / max(1, len(base)), 2),
            "by_sleeve": {sl: sum(1 for r in kept if r["sleeve"] == sl) for sl in book},
        }
    out["row_census"][book_name] = {"published_trades": len(base), "universes": cens}

# ---- the grid ----
for book_name, book in (("ARMED_3_PUBLISHED", ARMED3), ("ARMED_4_DECLARED", ARMED4)):
    for uname in ("AS_PUBLISHED", "CURRENT_SURFACE", "FN_TRADEABLE"):
        f = universe_filter(uname)
        sub_all = [r for r in ROWS if r["sleeve"] in book and f(r)]
        for acct in ("FTMO", "redacted_account"):
            # cost map from the SAME universe the book trades (medians of priced rows)
            cm = cost_map(acct, [r for r in ROWS if f(r)])
            for nights in (1.0, "max"):
                c = cell(list(sub_all), acct, cm, nights, True, Q.KELLY_HALF,
                         Q.RISK_LIVE_NOMINAL)
                rules = {}
                for r in Q.rule_sets(acct)[0]:
                    if r.label not in ("L4_FIRM_TRUE_PH1", "P2_BOTH_PHASES"):
                        continue
                    m = Q.mc(c["comb"], c["risk"], r, PATHS, seed_base=1)
                    rules[r.label] = {"p_pass": round(m["p_pass"], 6),
                                      "se_p_pass": round(m["se_p_pass"], 6),
                                      "p_fail_dd": round(m["p_fail_dd"], 6),
                                      "p_fail_daily": round(m["p_fail_daily"], 6),
                                      "p_timeout": round(m["p_timeout"], 6),
                                      **Q._derived(c, m)}
                out["cells"].append({
                    "book": book_name, "universe": uname, "account": acct,
                    "key": f"fwd_nights_{nights if nights != 'max' else 'max'}",
                    "sleeves": sorted(book),
                    "trades": len(sub_all),
                    "book_days": c["book_days"],
                    "mean_r_per_book_day": round(c["mean_r_per_book_day"], 5),
                    "sd_unit_r": round(c["sd_unit_r"], 5),
                    "worst_day_unit_r": round(c["worst_day_unit_r"], 5),
                    "eff_risk_pct": round(c["risk"] * 100, 3),
                    "rules": rules})
                print(f"{book_name:18s} {uname:16s} {acct:11s} "
                      f"nights={str(nights):5s} n={len(sub_all):5d} days={c['book_days']:4d} "
                      f"P2={rules.get('P2_BOTH_PHASES', {}).get('p_pass')} "
                      f"mo%={rules.get('P2_BOTH_PHASES', {}).get('monthly_pct_calendar')}",
                      flush=True)

dest = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/lbi/FN_UNIVERSE_RESTATEMENT_V1.json")
dest.write_text(json.dumps(out, indent=1))
print("WROTE", dest)
