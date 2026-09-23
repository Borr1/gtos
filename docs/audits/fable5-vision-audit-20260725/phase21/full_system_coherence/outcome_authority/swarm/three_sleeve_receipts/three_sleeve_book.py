#!/usr/bin/env python3
"""THREE-SLEEVE BOOK RESTATEMENT -- the economics of the book that exists after 2026-08-11.

Measurement only.  No live path, no config, no broker call, no VPS touch, no `src/` byte.

WHY THIS EXISTS.  Two live changes landed 2026-08-11: `sub_mid_dn_revert` was disarmed on
both accounts (`SLEEVE_PULL_SUB_MID_DN_REVERT_V1.md`, host `47d0960e6`) and
`ultimate_book_one_unit_per_cluster_per_day` was restored to `true`
(`LIVE_BOOK_INTEGRITY_V1.md`).  Every published economic figure prices a FOUR-sleeve book
under a cap that was OFF.  This measures the three-sleeve book on three axes at once:

  1. COMPOSITION   -- `crypto, energy_agri, sub_xvol_pullback` (the resolved live set,
                      `armed_sleeves()`), against the four-sleeve book as the control.
  2. UNIVERSE      -- `AS_PUBLISHED` (every cache symbol) vs `CURRENT_SURFACE` (the symbols
                      each sleeve can actually generate on today) vs `FN_TRADEABLE`
                      (`CURRENT_SURFACE` minus the 7 canonicals redacted_account's broker does not
                      list).  Method and the FN-absent set are LIVE_BOOK_INTEGRITY_V1 §1.1's,
                      measured on the live terminal.
  3. INSTRUMENT    -- uncorrected (the caches are PRE-REPAIR: their walker cannot represent a
                      spread, W7_INSTRUMENT_RESTATEMENT_V1 §2) vs quote-side CORRECTED by the
                      same structural transfer W7 used -- per-sleeve `target -> stop`
                      migration drawn from its Jeffreys posterior Beta(k+1/2, n-k+1/2) on
                      r1's 22,354-row corrected walk, trail/maxbars deltas drawn from r1's own
                      empirical pool for that sleeve, stops exactly zero (13,221/13,221).

and it carries TWO uncertainties, never the simulation's seed noise:

  INSTRUMENT band -- percentiles over B replicates of the correction alone.
  JOINT band      -- percentiles over B replicates of (correction x moving-block bootstrap
                     over the book-day series, block 5), which is the band the EVIDENCE
                     supports.  W7 §3.3's central lesson: `p_pass 0.9172` was published with
                     se 0.001125 (MC seed noise) when the evidence supports +/- 0.149.

CONVENTION.  The deployable one throughout: `KELLY_HALF`, `RISK_LIVE_NOMINAL`, 2.0 % dial,
`nights="max"` (worst carry), forward 2025+ window, `P2_BOTH_PHASES` (both challenge phases --
a payout requires both).  Machinery imported unchanged: `scripts/mc_firm_rules.py`,
`scripts/recost_w7_validation.py`.

HYDRATION CONTROL (added after this script measured the hazard).  `recost_w7_validation`'s D4
re-sim reads `PRICE_DIRS = data/historical*`; on a sparse checkout WITHOUT `data/` it fails
OPEN and the FTMO three-sleeve mean R/book-day silently reads 0.41478 instead of 0.38077
(+8.9 %).  The script asserts the published control value before measuring anything.

Usage: python3 three_sleeve_book.py [B_REPLICATES] [out.json]
"""
from __future__ import annotations

import collections
import gzip
import json
import math
import random
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[8]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import mc_firm_rules as Q          # noqa: E402
import recost_w7_validation as M   # noqa: E402
from src.components.ultimate_book.sleeves.registry import active_specs   # noqa: E402
from src.safety.armed_set import armed_sleeves                          # noqa: E402

AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
R1_ROWS = AUD / "phase20/receipts/r1/R1_ESTATE_ROWS_V1.json.gz"

B = int(sys.argv[1]) if len(sys.argv) > 1 else 250
DEST = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "THREE_SLEEVE_BOOK_V1.json"
N_PATHS_POINT = 60_000
N_PATHS_REP = 20_000
BLOCK = 5

ARMED_TODAY = sorted(armed_sleeves())                      # the live set, resolved
FOUR = sorted(set(ARMED_TODAY) | {"sub_mid_dn_revert"})    # the control (yesterday's book)
# MEASURED 2026-08-11 on the live redacted_account terminal by symbols_get exhaustion (76 symbols):
# none of these 7 exists on that broker under any probed name (LIVE_BOOK_INTEGRITY_V1 §1.1).
FN_BROKER_ABSENT = {"XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD", "CORN_c", "COTTON_c", "DASHUSD"}

# Published control: FTMO / three sleeves / AS_PUBLISHED / fwd / worst carry, at HEAD costs.
CONTROL_R_PER_BOOK_DAY = 0.38077
CONTROL_BOOK_DAYS = 117

SURFACE = {s.tag: set(s.on_surface)
           for s in active_specs(FOUR, include_candidate_book=True,
                                 include_market_expansion_book=True)}


def universe_filter(name):
    if name == "AS_PUBLISHED":
        return lambda r: True
    if name == "CURRENT_SURFACE":
        return lambda r: r["sym"] in SURFACE.get(r["sleeve"], set())
    if name == "FN_TRADEABLE":
        return lambda r: (r["sym"] in SURFACE.get(r["sleeve"], set())
                          and r["sym"] not in FN_BROKER_ABSENT)
    raise SystemExit(name)


def pctl(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    i = (len(xs) - 1) * q / 100.0
    lo, hi = int(math.floor(i)), int(math.ceil(i))
    return xs[lo] if lo == hi else xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def moving_block(series, rng, block=BLOCK):
    n = len(series)
    out = []
    while len(out) < n:
        s = rng.randrange(0, n)
        out.extend(series[s:s + block] if s + block <= n else series[s:] + series[:s + block - n])
    return out[:n]


def r1_calibration():
    """Per-sleeve quote-side correction structure, from r1's corrected walk."""
    r1 = json.load(gzip.open(R1_ROWS, "rt"))
    per, ptg, pmg, poth = {}, 0, 0, []
    for sl in sorted({r["sleeve"] for r in r1}):
        rs = [r for r in r1 if r["sleeve"] == sl]
        tg = [r for r in rs if r["reason_old"] == "target"]
        mig = [r for r in tg if r["reason_new"] != "target"]
        oth = [r["r_new_mid"] - r["r_old"] for r in rs if r["reason_old"] in ("trail", "maxbars")]
        per[sl] = dict(n=len(rs), n_target=len(tg), n_migrated=len(mig), other_deltas=oth,
                       mig_rate=(len(mig) / len(tg) if tg else None))
        ptg += len(tg)
        pmg += len(mig)
        poth += oth
    per["_POOLED_"] = dict(n=len(r1), n_target=ptg, n_migrated=pmg, other_deltas=poth,
                           mig_rate=pmg / ptg)
    return per


def cell_series(rows, keep, ufilter, acct, cm, sd_book):
    sub = [r for r in rows if r["sleeve"] in keep and ufilter(r)]
    days, comb, risk, vs = Q.series(sub, acct, cm, "max", sd_book, forward=True,
                                    kelly=Q.KELLY_HALF, risk_basis=Q.RISK_LIVE_NOMINAL)
    return sub, days, comb, risk


def calendar(days):
    a, b = min(days), max(days)
    months = (b.year - a.year) * 12 + (b.month - a.month) + 1
    return len(days) / months, Q.weekday_sessions(a, b)


def main():
    st = M.build([])
    rows = st["rows"]
    for r in rows:
        g = r["R"] + r["charged_cost_r"]
        r["_gross"] = g
        r["_reason"] = ("stop" if abs(g + 1.0) < 1e-6
                        else ("target" if (g > 0 and abs(g - round(g * 4) / 4) < 1e-6)
                              else "other"))
        r["R_legacy"] = r["R"]
    _, _, _, sd_book = M.build_matrix_from(rows, "R_legacy")

    cms = {a: {k: statistics.median(v) for k, v in Q._priced_pool(rows, a).items()}
           for a in ("FTMO", "redacted_account")}

    # ---- hydration control: refuse to measure on a fails-open sparse checkout ----------
    _, cdays, ccomb, _ = cell_series(rows, ARMED_TODAY, universe_filter("AS_PUBLISHED"),
                                     "FTMO", cms["FTMO"], sd_book)
    ctl = statistics.fmean(ccomb)
    if abs(ctl - CONTROL_R_PER_BOOK_DAY) > 5e-5 or len(cdays) != CONTROL_BOOK_DAYS:
        raise SystemExit(
            f"HYDRATION CONTROL FAILED: FTMO/3-sleeve/AS_PUBLISHED reads "
            f"{ctl:.5f} R/book-day over {len(cdays)} days; the published control is "
            f"{CONTROL_R_PER_BOOK_DAY} over {CONTROL_BOOK_DAYS}. The usual cause is an "
            f"absent data/historical* tree -- recost_w7_validation's D4 re-sim fails OPEN.")

    calib = r1_calibration()

    BOOKS = (("THREE_SLEEVE_ARMED", ARMED_TODAY), ("FOUR_SLEEVE_PRIOR", FOUR))
    UNIS = ("AS_PUBLISHED", "CURRENT_SURFACE", "FN_TRADEABLE")
    ACCTS = ("FTMO", "redacted_account")

    out = {
        "schema": "gtos.wave21.three_sleeve_book.v1",
        "measurement_only": True,
        "generated_by": "phase21/.../swarm/three_sleeve_receipts/three_sleeve_book.py",
        "armed_sleeves_resolved": ARMED_TODAY,
        "control_book_four_sleeve": FOUR,
        "fn_broker_absent_symbols": sorted(FN_BROKER_ABSENT),
        "surface": {k: sorted(v) for k, v in SURFACE.items()},
        "convention": {"kelly": Q.KELLY_HALF, "risk_basis": Q.RISK_LIVE_NOMINAL,
                       "dial_pct": Q.DIAL * 100, "nights": "sleeve_max (worst carry)",
                       "window": "forward_2025+", "rule": "P2_BOTH_PHASES"},
        "hydration_control": {"ftmo_three_sleeve_as_published_r_per_book_day": round(ctl, 5),
                              "expected": CONTROL_R_PER_BOOK_DAY, "book_days": len(cdays),
                              "status": "PASS"},
        "sd_book_reference": round(sd_book, 5),
        "instrument_calibration": {k: {kk: vv for kk, vv in v.items() if kk != "other_deltas"}
                                   for k, v in calib.items()},
        "replicates": B, "paths_point": N_PATHS_POINT, "paths_per_replicate": N_PATHS_REP,
        "bootstrap_block_days": BLOCK,
        "row_census": {}, "cells": {},
    }

    # ---- census -----------------------------------------------------------------------
    for bname, keep in BOOKS:
        base = [r for r in rows if r["sleeve"] in keep]
        cen = {}
        for u in UNIS:
            f = universe_filter(u)
            kept = [r for r in base if f(r)]
            cen[u] = dict(trades=len(kept),
                          pct_of_as_published=round(100.0 * len(kept) / max(1, len(base)), 2),
                          by_sleeve={sl: sum(1 for r in kept if r["sleeve"] == sl)
                                     for sl in keep})
        out["row_census"][bname] = dict(as_published_trades=len(base), universes=cen)

    # ---- point cells (uncorrected instrument, current cost layer) ----------------------
    for bname, keep in BOOKS:
        for u in UNIS:
            f = universe_filter(u)
            for acct in ACCTS:
                sub, days, comb, risk = cell_series(rows, keep, f, acct, cms[acct], sd_book)
                if not comb:
                    continue
                rules, _ = Q.rule_sets(acct)
                P2 = [r for r in rules if r.label == "P2_BOTH_PHASES"][0]
                res = Q.mc(comb, risk, P2, N_PATHS_POINT, seed_base=1)
                bdpm, wds = calendar(days)
                mu = statistics.fmean(comb)
                sd = statistics.stdev(comb) if len(comb) > 1 else 0.0
                se = sd / math.sqrt(len(comb)) if comb else 0.0
                out["cells"][f"{bname}|{u}|{acct}"] = dict(
                    book=bname, universe=u, account=acct, sleeves=list(keep),
                    trades=len(sub), book_days=len(days), book_days_per_month=round(bdpm, 3),
                    weekday_sessions=wds,
                    mean_r_per_book_day=round(mu, 5),
                    sd_r_per_book_day=round(sd, 5), se_mean_r_per_book_day=round(se, 5),
                    ci95_mean_r_per_book_day=[round(mu - 1.96 * se, 5), round(mu + 1.96 * se, 5)],
                    t_stat_mean=round(mu / se, 3) if se else None,
                    worst_day_unit_r=round(min(comb), 4), best_day_unit_r=round(max(comb), 4),
                    eff_risk_pct=round(risk * 100, 4),
                    uncorrected=dict(
                        p_pass=round(res["p_pass"], 5),
                        p_pass_mc_seed_se=round(res["se_p_pass"], 6),
                        p_fail_dd=round(res["p_fail_dd"], 5),
                        p_fail_daily=round(res["p_fail_daily"], 5),
                        p_timeout=round(res["p_timeout"], 5),
                        monthly_pct=round(100.0 * mu * risk * bdpm, 3),
                        median_book_days_to_pass=res["med_days_pass"],
                        median_calendar_days_to_pass=(
                            round(res["med_days_pass"] * wds / len(days))
                            if res["med_days_pass"] else None)),
                )
                print(f"POINT {bname:19s} {u:16s} {acct:11s} n={len(sub):4d} d={len(days):4d} "
                      f"R/bd={mu:+.5f} p_pass={res['p_pass']:.4f} "
                      f"%/mo={100.0*mu*risk*bdpm:+.3f}", flush=True)

    # ---- replicates: instrument-only band, and joint band -----------------------------
    rng = random.Random(20260811)
    inst = collections.defaultdict(lambda: collections.defaultdict(list))
    joint = collections.defaultdict(lambda: collections.defaultdict(list))
    for b in range(B):
        rates = {}
        for sl in {r["sleeve"] for r in rows}:
            c = calib.get(sl) or calib["_POOLED_"]
            if not c["n_target"]:
                c = calib["_POOLED_"]
            aa, bb = c["n_migrated"] + 0.5, c["n_target"] - c["n_migrated"] + 0.5
            x, y = rng.gammavariate(aa, 1.0), rng.gammavariate(bb, 1.0)
            rates[sl] = x / (x + y)
        crows = []
        for r in rows:
            d = 0.0
            if r["_reason"] == "target":
                if rng.random() < rates[r["sleeve"]]:
                    d = -1.0 - r["_gross"]
            elif r["_reason"] == "other":
                pool = (calib.get(r["sleeve"]) or {}).get("other_deltas") \
                    or calib["_POOLED_"]["other_deltas"]
                d = rng.choice(pool) if pool else 0.0
            q = dict(r)
            q["R_gross"] = r["R_gross"] + d
            crows.append(q)
        for bname, keep in BOOKS:
            for u in UNIS:
                f = universe_filter(u)
                for acct in ACCTS:
                    sub, days, comb, risk = cell_series(crows, keep, f, acct, cms[acct], sd_book)
                    if not comb:
                        continue
                    rules, _ = Q.rule_sets(acct)
                    P2 = [r for r in rules if r.label == "P2_BOTH_PHASES"][0]
                    bdpm, wds = calendar(days)
                    key = f"{bname}|{u}|{acct}"
                    mi = Q.mc(comb, risk, P2, N_PATHS_REP, seed_base=1)
                    mu = statistics.fmean(comb)
                    inst[key]["p_pass"].append(mi["p_pass"])
                    inst[key]["monthly_pct"].append(100.0 * mu * risk * bdpm)
                    inst[key]["mean_r_per_book_day"].append(mu)
                    inst[key]["median_calendar_days_to_pass"].append(
                        mi["med_days_pass"] * wds / len(days) if mi["med_days_pass"] else None)
                    bs = moving_block(comb, rng)
                    mj = Q.mc(bs, risk, P2, N_PATHS_REP, seed_base=1)
                    joint[key]["p_pass"].append(mj["p_pass"])
                    joint[key]["monthly_pct"].append(100.0 * statistics.fmean(bs) * risk * bdpm)
                    joint[key]["mean_r_per_book_day"].append(statistics.fmean(bs))
        if (b + 1) % 25 == 0:
            print(f"  replicate {b+1}/{B}", flush=True)

    def band(vals):
        v = [x for x in vals if x is not None]
        if not v:
            return None
        return dict(median=pctl(v, 50), p2_5=pctl(v, 2.5), p97_5=pctl(v, 97.5),
                    p10=pctl(v, 10), p90=pctl(v, 90), mean=statistics.fmean(v), n=len(v))

    for key, cell in out["cells"].items():
        cell["corrected_instrument"] = {m: band(v) for m, v in inst[key].items()}
        cell["joint_instrument_x_sampling"] = {m: band(v) for m, v in joint[key].items()}
        u0 = cell["uncorrected"]
        ci = cell["corrected_instrument"]
        cell["instrument_effect"] = dict(
            d_p_pass=round(ci["p_pass"]["median"] - u0["p_pass"], 5),
            d_monthly_pct=round(ci["monthly_pct"]["median"] - u0["monthly_pct"], 3))

    DEST.write_text(json.dumps(out, indent=1, default=str))
    print("\nWROTE", DEST)
    for key, c in out["cells"].items():
        ci, jt = c["corrected_instrument"], c["joint_instrument_x_sampling"]
        print(f"{key:52s} n={c['trades']:4d} d={c['book_days']:4d} "
              f"unc={c['uncorrected']['p_pass']:.4f} corr={ci['p_pass']['median']:.4f} "
              f"[{ci['p_pass']['p2_5']:.4f},{ci['p_pass']['p97_5']:.4f}] "
              f"JOINT={jt['p_pass']['median']:.4f} "
              f"[{jt['p_pass']['p2_5']:.4f},{jt['p_pass']['p97_5']:.4f}] "
              f"%/mo={ci['monthly_pct']['median']:+.3f}")


if __name__ == "__main__":
    main()
