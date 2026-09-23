#!/usr/bin/env python3
"""W7 INSTRUMENT RESTATEMENT — part 2: instrument state, and the corrected restatement.

Measurement only.  No live path, no config, no broker, no VPS.

PART A — INSTRUMENT STATE OF EACH CACHE, by proof and not by prose.

  A1 CODE PATH (constructive).  Every cached `R` comes from
     `research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/
      geometry_lib.py:21 simulate()`, whose entry is `bars[i].c` (`:27`) with no
     `entry_price` parameter -- the repair's one and only degree of freedom
     (`src/research_infra/walkforward/exits.py:359`) does not exist in this walker.
     `Bar` (`geometry_lib.py:9-11`) carries `o,h,l,c,v` and nothing else, and the CSV
     loader `wave1_structure_setups_ict.py:71-73` drops the archive's `spread` column
     at load.  A walk cannot cross a spread it never loaded.

  A2 POPULATION IDENTITY (measured here).  If the walk had crossed a per-trade spread
     the cached R would carry a per-trade `spread/stop_distance` term.  That term is
     measured by the estate itself to vary by symbol and era (spread model era ratios
     span 50x on EURUSD and 0.18x on XAUUSD; r1 measures per-sleeve s/d medians from
     0.0093 to 0.0889).  Test: the dispersion of the charged cost recovered from
     stop-out rows.  Zero dispersion == no per-trade market-crossing term.

  A3 REJOINABILITY (measured here).  Whether a per-row identity against the corrected
     walk is even possible.

PART B — THE RESTATEMENT.

  The generator cannot be re-run: `data/mt5_research_exports/bridge_ftmo_deep_h4_*`
  (`wave1_structure_setups_ict.py:46-47`) is absent from this machine, and the loader
  fails OPEN to an empty universe rather than erroring.  So the correction is
  TRANSFERRED, structurally, from lane r1's 22,354-row corrected walk -- and the
  transfer is exact where it matters most, because r1 measures that the correction is
  identically ZERO on every level exit that does not migrate:

      stop   -> stop    13,221 / 13,221 rows, max |delta| = 1.1e-12
      target -> target   6,816 rows,          max |delta| = 5.3e-13
      target -> stop       732 rows           delta = -(1 + T)
      trail/maxbars migrations and level shifts carry the rest

  The cached R identifies its own exit reason exactly (a stop books -1 - c, a target
  books T - c, both to float precision), so 46.5 % of the book is provably unmoved and
  only the target and trail/maxbars rows carry any uncertainty at all.  That
  uncertainty is propagated by drawing the per-sleeve migration rate from its Jeffreys
  posterior and the trail/maxbars delta from r1's own empirical distribution, B times.
"""
from __future__ import annotations

import collections
import gzip
import json
import math
import pickle
import random
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[8]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import mc_firm_rules as Q          # noqa: E402
import recost_w7_validation as M   # noqa: E402

HERE = Path(__file__).resolve().parent
AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
R1_ROWS = AUD / "phase20/receipts/r1/R1_ESTATE_ROWS_V1.json.gz"
R1_DELTA = AUD / "phase20/receipts/r1/R1_ESTATE_DELTA_V1.json"
BOOKS_MC = AUD / "phase8/receipts/BOOKS_MC_V1.json"

ARMED_3 = ["crypto", "energy_agri", "sub_xvol_pullback"]
ARMED_4 = ARMED_3 + ["sub_mid_dn_revert"]
B_REPLICATES = 300
N_PATHS = 30_000
SEED = 1


# ----------------------------------------------------------------------------------
# PART A
# ----------------------------------------------------------------------------------
def instrument_state(rows):
    """A2 + A3, measured on the caches themselves."""
    # A2 -- dispersion of the charged (market-crossing) cost, per (sleeve, symbol)
    by_pair = collections.defaultdict(list)
    for r in rows:
        by_pair[(r["sleeve"], r["sym"])].append(r)
    pairs = {}
    n_zero_disp = n_pairs_with_stops = 0
    for k, rs in by_pair.items():
        stops = [r for r in rs if abs(r["R"] + r["charged_cost_r"] + 1.0) < 1e-6]
        costs = sorted({round(r["charged_cost_r"], 9) for r in stops})
        basis = collections.Counter(r.get("charged_basis", "?") for r in rs)
        pairs[f"{k[0]}:{k[1]}"] = dict(
            n_rows=len(rs), n_stopouts=len(stops), n_distinct_charged_cost=len(costs),
            charged_cost_min=(costs[0] if costs else None),
            charged_cost_max=(costs[-1] if costs else None),
            charged_basis=dict(basis),
            first_year=min(r["year"] for r in rs), last_year=max(r["year"] for r in rs))
        if stops:
            n_pairs_with_stops += 1
            if len(costs) == 1:
                n_zero_disp += 1

    # exit-reason reconstruction from the exact atoms
    reason = collections.Counter()
    per_sleeve = collections.defaultdict(collections.Counter)
    for r in rows:
        g = r["R"] + r["charged_cost_r"]
        if abs(g + 1.0) < 1e-6:
            k = "stop"
        elif g > 0 and abs(g - round(g * 4) / 4) < 1e-6:
            k = "target"
        else:
            k = "other"
        r["_reason"] = k
        r["_gross"] = g
        reason[k] += 1
        per_sleeve[r["sleeve"]][k] += 1

    n = len(rows)
    return dict(
        n_rows=n,
        a2_flat_cost_identity=dict(
            claim=("if the walk crossed a per-trade spread, the cost recovered from "
                   "stop-out rows would inherit that spread's dispersion"),
            pairs_with_stopouts=n_pairs_with_stops,
            pairs_with_exactly_one_distinct_charged_cost=n_zero_disp,
            fraction=n_zero_disp / n_pairs_with_stops if n_pairs_with_stops else None,
            verdict=("ZERO per-trade dispersion on every flat pair -- the charge for "
                     "crossing the market is a scalar constant over the pair's whole "
                     "span, which a spread-crossing walk cannot produce"),
            per_pair=pairs),
        a2_exit_reason_reconstruction=dict(
            note=("a stop books exactly -1 - c and a target exactly T - c, so the "
                  "cached R identifies its own exit reason to float precision"),
            pooled=dict(reason),
            pooled_fraction={k: v / n for k, v in reason.items()},
            per_sleeve={k: dict(v) for k, v in per_sleeve.items()}),
    )


def rejoinability(rows):
    """A3 -- can the cache be joined row-for-row to any per-trade corrected artifact?"""
    key = collections.Counter((r["sleeve"], r["sym"], str(r["date"])) for r in rows)
    mult = collections.Counter(key.values())
    nonuniq = sum(v for k, v in key.items() if key[k] > 1)
    return dict(
        join_key="(sleeve, symbol, date)",
        n_rows=len(rows), n_distinct_keys=len(key),
        multiplicity_histogram={str(k): v for k, v in sorted(mult.items())},
        max_multiplicity=max(mult),
        rows_on_a_non_unique_key=nonuniq,
        fraction_non_unique=nonuniq / len(rows),
        verdict=("the cache carries no decision timestamp, no direction and no exit "
                 "index, so a per-row identity against the corrected walk is "
                 "IMPOSSIBLE, not merely unmeasured -- independently stamped by "
                 "phase21/w7_recost/PRIOR_RECONCILIATION_V1.json "
                 "(exact_rejoinable_from_cache_key: false on all four armed sleeves)"))


# ----------------------------------------------------------------------------------
# PART B -- the transfer
# ----------------------------------------------------------------------------------
def r1_calibration():
    r1 = json.load(gzip.open(R1_ROWS, "rt"))
    per = {}
    pooled_tgt = pooled_mig = 0
    pooled_other = []
    for sl in sorted({r["sleeve"] for r in r1}):
        rs = [r for r in r1 if r["sleeve"] == sl]
        tg = [r for r in rs if r["reason_old"] == "target"]
        mig = [r for r in tg if r["reason_new"] != "target"]
        oth = [r for r in rs if r["reason_old"] in ("trail", "maxbars")]
        d_oth = [r["r_new_mid"] - r["r_old"] for r in oth]
        per[sl] = dict(n=len(rs), n_target=len(tg), n_migrated=len(mig),
                       mig_rate=(len(mig) / len(tg) if tg else None),
                       other_deltas=d_oth,
                       sd_over_risk_median=statistics.median(
                           [r["spread_mid"] / r["sl_distance_price"] for r in rs]))
        pooled_tgt += len(tg)
        pooled_mig += len(mig)
        pooled_other += d_oth
    per["_POOLED_"] = dict(n=len(r1), n_target=pooled_tgt, n_migrated=pooled_mig,
                           mig_rate=pooled_mig / pooled_tgt,
                           other_deltas=pooled_other,
                           sd_over_risk_median=None)
    # verify the zero-delta identity this transfer rests on
    z_stop = [r for r in r1 if r["reason_old"] == "stop"]
    z_tgt = [r for r in r1 if r["reason_old"] == "target" and r["reason_new"] == "target"]
    ident = dict(
        stop_rows=len(z_stop),
        stop_max_abs_delta=max(abs(r["r_new_mid"] - r["r_old"]) for r in z_stop),
        target_kept_rows=len(z_tgt),
        target_kept_max_abs_delta=max(abs(r["r_new_mid"] - r["r_old"]) for r in z_tgt),
        migration_matrix=dict(collections.Counter(
            f"{r['reason_old']}->{r['reason_new']}" for r in r1)))
    return per, ident


def draw_correction(rows, calib, rng):
    """One replicate: return {id(row) -> delta} for the quote-side correction."""
    rates = {}
    for sl in {r["sleeve"] for r in rows}:
        c = calib.get(sl) or calib["_POOLED_"]
        k, n = c["n_migrated"], c["n_target"]
        if not n:
            c = calib["_POOLED_"]
            k, n = c["n_migrated"], c["n_target"]
        # Jeffreys posterior Beta(k+0.5, n-k+0.5), sampled by the ratio of two gammas
        a, b = k + 0.5, n - k + 0.5
        x, y = rng.gammavariate(a, 1.0), rng.gammavariate(b, 1.0)
        rates[sl] = x / (x + y)
    deltas = []
    for r in rows:
        sl = r["sleeve"]
        if r["_reason"] == "stop":
            deltas.append(0.0)                      # exact, r1: 13,221/13,221
        elif r["_reason"] == "target":
            if rng.random() < rates[sl]:
                deltas.append(-1.0 - r["_gross"])   # migrates to stop; books -1
            else:
                deltas.append(0.0)                  # exact, r1: max |delta| 5.3e-13
        else:
            pool = (calib.get(sl) or {}).get("other_deltas") or calib["_POOLED_"]["other_deltas"]
            deltas.append(rng.choice(pool) if pool else 0.0)
    return deltas, rates


def cell_for(rows, keep, acct, cm, sd_book, rules, paths=N_PATHS, forward=True):
    sub = [r for r in rows if r["sleeve"] in keep]
    days, comb, risk, vs = Q.series(sub, acct, cm, "max", sd_book, forward=forward,
                                    kelly=Q.KELLY_HALF, risk_basis=Q.RISK_LIVE_NOMINAL)
    if not comb:
        return None
    res = Q.mc(comb, risk, rules, paths, seed_base=SEED)
    a, b = min(days), max(days)
    months = (b.year - a.year) * 12 + (b.month - a.month) + 1
    bdpm = len(days) / months
    mean_r = statistics.fmean(comb)
    return dict(book_days=len(days), book_days_per_month=bdpm,
                mean_r_per_book_day=mean_r, monthly_pct=100.0 * mean_r * risk * bdpm,
                p_pass=res["p_pass"], med_days_pass=res["med_days_pass"],
                worst_day=min(comb), sd_unit_r=statistics.pstdev(comb))


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    i = (len(xs) - 1) * q / 100.0
    lo, hi = int(math.floor(i)), int(math.ceil(i))
    return xs[lo] if lo == hi else xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def main():
    st = M.build([])
    rows = st["rows"]
    for r in rows:
        r["R_legacy"] = r["R"]
    _, _, _, sd_book = M.build_matrix_from(rows, "R_legacy")

    cms = {}
    for acct in ("FTMO", "redacted_account"):
        pool = collections.defaultdict(list)
        for r in rows:
            c = r[f"cost_{acct}"]
            if c["status"] == "priced":
                pool[r["sleeve"]].append(c["cost_ex_swap_r"])
        cms[acct] = {k: statistics.median(v) for k, v in pool.items()}

    out = {
        "schema": "gtos.wave21.w7_instrument_state.v1",
        "measurement_only": True,
        "caches": {
            "INTEG_W3_streams_cache.pkl": str(M.W3_CACHE.relative_to(REPO)),
            "INTEG_W5_new_streams_cache.pkl": str(M.W5_CACHE.relative_to(REPO)),
        },
        "sd_book_reference": sd_book,
    }
    out["part_a_instrument_state"] = instrument_state(rows)
    out["part_a3_rejoinability"] = rejoinability(rows)

    calib, ident = r1_calibration()
    out["part_b_transfer"] = dict(
        why_not_a_rewalk=("data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022 and "
                          "..._2022_2026 (wave1_structure_setups_ict.py:46-47) are absent "
                          "from this machine; the loader fails OPEN to an empty universe "
                          "(:61-62), so a rebuild would silently produce empty streams"),
        zero_delta_identity=ident,
        calibration={k: {kk: vv for kk, vv in v.items() if kk != "other_deltas"}
                     for k, v in calib.items()},
        replicates=B_REPLICATES, n_paths_per_replicate=N_PATHS)

    # ---- baseline (uncorrected instrument, current cost layer) ----------------------
    books = {}
    for label, keep in (("ARMED_3", ARMED_3), ("ARMED_4", ARMED_4)):
        for acct in ("FTMO", "redacted_account"):
            rules, _ = Q.rule_sets(acct)
            P2 = [r for r in rules if r.label == "P2_BOTH_PHASES"][0]
            base = cell_for(rows, keep, acct, cms[acct], sd_book, P2, paths=60_000)
            books[f"{acct}:{label}"] = dict(baseline_uncorrected=base, corrected={})

    # ---- B replicates of the corrected instrument -----------------------------------
    rng = random.Random(20260811)
    acc = collections.defaultdict(lambda: collections.defaultdict(list))
    rate_draws = collections.defaultdict(list)
    for b in range(B_REPLICATES):
        deltas, rates = draw_correction(rows, calib, rng)
        for sl, v in rates.items():
            rate_draws[sl].append(v)
        crows = []
        for r, d in zip(rows, deltas):
            q = dict(r)
            q["R_gross"] = r["R_gross"] + d
            crows.append(q)
        for label, keep in (("ARMED_3", ARMED_3), ("ARMED_4", ARMED_4)):
            for acct in ("FTMO", "redacted_account"):
                rules, _ = Q.rule_sets(acct)
                P2 = [r for r in rules if r.label == "P2_BOTH_PHASES"][0]
                c = cell_for(crows, keep, acct, cms[acct], sd_book, P2)
                if c:
                    for k in ("p_pass", "monthly_pct", "mean_r_per_book_day",
                              "med_days_pass", "worst_day"):
                        acc[f"{acct}:{label}"][k].append(c[k])
        if (b + 1) % 50 == 0:
            print(f"  replicate {b+1}/{B_REPLICATES}", flush=True)

    for k, d in acc.items():
        books[k]["corrected"] = {
            m: dict(median=pct(v, 50), p2_5=pct(v, 2.5), p97_5=pct(v, 97.5),
                    mean=statistics.fmean(v), n=len(v))
            for m, v in d.items()}
        b0 = books[k]["baseline_uncorrected"]
        books[k]["instrument_effect"] = dict(
            d_p_pass=books[k]["corrected"]["p_pass"]["median"] - b0["p_pass"],
            d_monthly_pct=(books[k]["corrected"]["monthly_pct"]["median"]
                           - b0["monthly_pct"]),
            d_mean_r_per_book_day=(books[k]["corrected"]["mean_r_per_book_day"]["median"]
                                   - b0["mean_r_per_book_day"]))
    out["books"] = books
    out["migration_rate_posterior"] = {
        k: dict(median=pct(v, 50), p2_5=pct(v, 2.5), p97_5=pct(v, 97.5))
        for k, v in rate_draws.items()}

    (HERE / "W7_INSTRUMENT_STATE_V1.json").write_text(
        json.dumps(out, indent=1, default=str))

    a = out["part_a_instrument_state"]
    print("\n=== PART A: INSTRUMENT STATE ===")
    print("rows:", a["n_rows"])
    f = a["a2_flat_cost_identity"]
    print(f"A2 pairs with stop-outs: {f['pairs_with_stopouts']}; "
          f"exactly one distinct charged cost: "
          f"{f['pairs_with_exactly_one_distinct_charged_cost']} "
          f"({f['fraction']:.4f})")
    print("A2 exit mix:", a["a2_exit_reason_reconstruction"]["pooled"],
          {k: round(v, 4) for k, v in
           a["a2_exit_reason_reconstruction"]["pooled_fraction"].items()})
    r3 = out["part_a3_rejoinability"]
    print(f"A3 join key multiplicity max={r3['max_multiplicity']} "
          f"rows on non-unique key={r3['rows_on_a_non_unique_key']} "
          f"({r3['fraction_non_unique']:.4f})")
    print("\nzero-delta identity:", json.dumps(ident, default=str))
    print("\n=== PART B: RESTATEMENT ===")
    for k, v in books.items():
        b0 = v["baseline_uncorrected"]
        c = v["corrected"]
        print(f"\n{k}")
        print(f"  uncorrected : p_pass {b0['p_pass']:.5f}  %/mo {b0['monthly_pct']:+.3f}"
              f"  R/bd {b0['mean_r_per_book_day']:+.5f}  book_days {b0['book_days']}"
              f"  bdpm {b0['book_days_per_month']:.3f}")
        print(f"  CORRECTED   : p_pass {c['p_pass']['median']:.5f} "
              f"[{c['p_pass']['p2_5']:.5f},{c['p_pass']['p97_5']:.5f}]"
              f"  %/mo {c['monthly_pct']['median']:+.3f} "
              f"[{c['monthly_pct']['p2_5']:+.3f},{c['monthly_pct']['p97_5']:+.3f}]")
        print(f"  instrument effect: dp_pass {v['instrument_effect']['d_p_pass']:+.5f}"
              f"  d%/mo {v['instrument_effect']['d_monthly_pct']:+.3f}")


if __name__ == "__main__":
    main()
