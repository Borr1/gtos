#!/usr/bin/env python3
"""Session CA (B2120-B2134) — BB's fill truth, applied to the numbers Borhen has actually seen.

    python3 .../phase14/receipts/ca_fill_truth_restate.py --stage cache
    python3 .../phase14/receipts/ca_fill_truth_restate.py --stage armed
    python3 .../phase14/receipts/ca_fill_truth_restate.py --stage stops
    python3 .../phase14/receipts/ca_fill_truth_restate.py            # all three

WHAT BB LEFT OPEN, AND WHY IT IS THE HIGHEST-VALUE ITEM ON ITS HANDOFF
-----------------------------------------------------------------------
`SESSION_BB_SLEEVE_SUPPLY_RESULT.md` measured that the live placement path suppresses 32 %
of the armed four's archive decisions, and that every published calendar figure divides by a
book-day count with **no placement guard**. It then refused to apply the 1.333x it measured
to `BOOKS_MC_V1`'s rows, because those rows are built from the **W7 recost caches** and the
1.333x is a property of the **archive walk** (its own A5). Direction certain, magnitude not.
Handoff item 1: *"re-derive book_days on the W7 cache population ... this is the highest-value
item here — it changes numbers already in front of Borhen."*

This file does that, and the honest instrument is a **lower bound**, for a reason that is a
property of the caches rather than a choice:

  The live guard has TWO clauses. `already_placed_today` (`book_owner.py:1727-1735`) keys on
  (sleeve, symbol, decision day) -- and the cache rows carry exactly `{sleeve, sym, date,
  year, R}`, so that clause is computable EXACTLY on this population. The one-open-position-
  per-broker-symbol clause (`:1823-1850`, via `_same_broker_symbol_open_exposures`
  `:386-399`) needs entry and exit times, and **no exit index survives in any cache**
  (`SESSION_N_W7_RECOST_RESULT.md` §8.1). So the day-key clause alone is measured, the other
  is named as unmeasurable here, and every number below is stamped LOWER_BOUND.

That is not a hedge. On BB's archive population the day-key clause was **131 of 279**
suppressed decisions -- nearly half -- and it is the half that survives any objection to an
exit model, because a day key needs no exit at all.

THE ARMED SET IS NOT BB'S ARMED SET ANY MORE
---------------------------------------------
BB measured `crypto, energy_agri, sub_xvol_pullback, sub_mid_dn_revert` and stamped the set
its thresholds belong to, with handoff item 4: *"re-run whenever `--tags` changes."* It has
changed twice since: `mx_btcusd_d1_donchian_20_breakout` was armed on FTMO on 2026-07-31
(`phase13/receipts/MX_ACTIVATION_20260731.md`, host `d6c9c4b19`) **on `--frontier-exits`,
i.e. at `target_5R`, not at its committed 2R contract**. So FTMO runs five sleeves and
redacted_account four, and the fifth trades BTCUSD -- a symbol `crypto` already holds, which is
exactly the case where a new sleeve does not ADD a fill but REPLACES one. `--stage armed`
measures both books at the contract each actually runs.

BOUNDARY. Offline and pure. Reads committed artifacts, the two W7 caches and the read-only
bar archive; writes one JSON and one owner page. No broker, no VPS, no config write. Arms
nothing and recommends no arming.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import json
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
P6 = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
P7 = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
P8 = REPO / "docs/audits/fable5-vision-audit-20260725/phase8/receipts"
P11 = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts"
P13 = REPO / "docs/audits/fable5-vision-audit-20260725/phase13/receipts"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(P7))
sys.path.insert(0, str(P13))

OUT = HERE / "CA_FILL_TRUTH_RESTATE_V1.json"
ESTATE = P11 / "AQ_ESTATE_TRADES_V2.json.gz"
BOOKS_MC = P8 / "BOOKS_MC_V1.json"
STOPS = P11 / "FIVE_SLEEVE_STOP_CONDITIONS_V1.json"
BB_FILL = P13 / "BB_FILL_TRUTH_V1.json"

MX = "mx_btcusd_d1_donchian_20_breakout"
#: The armed sets as of 2026-07-31, per account, from the ceremony receipts.
ARMED = {
    "FTMO": ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert", MX),
    "redacted_account": ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert"),
}
ARMED_PROVENANCE = {
    "FTMO": ("phase13/receipts/MX_ACTIVATION_20260731.md (host d6c9c4b19, ~01:26Z) on top of "
             "phase8/receipts/FXJPY_PULL_20260730.md (fx_jpy pulled ~14:57Z, host 7017c6745). "
             "mx_btcusd runs on --frontier-exits, i.e. the target_5R cell."),
    "redacted_account": ("phase8/receipts/FN_ARMING_20260730.md + FIVE_SLEEVE_EXPANSION_20260730.md; "
                   "four sleeves, no frontier, untouched by the mx ceremony."),
}
ARCHIVE_END = dt.date(2026, 7, 27)


# =====================================================================================
# STAGE cache — the day-key clause on the W7 recost population (BB handoff 1)
# =====================================================================================
def _dedup_day_key(rows: list[dict]) -> tuple[list[dict], dict]:
    """Keep the FIRST row per (sleeve, sym, date); return (kept, telemetry).

    Order is the cache's own order, which is the only order that exists on this population --
    there is no entry timestamp to sort by. `--stage cache` reports the sensitivity to that
    choice (last-instead-of-first) beside every figure, because a tie-break that moves a
    result is a finding and one that does not is a control.
    """
    seen: set = set()
    kept: list[dict] = []
    drop = collections.Counter()
    for r in rows:
        k = (r["sleeve"], r["sym"], r["date"])
        if k in seen:
            drop[r["sleeve"]] += 1
            continue
        seen.add(k)
        kept.append(r)
    return kept, dict(drop)


def _dedup_day_key_last(rows: list[dict]) -> list[dict]:
    by: dict = {}
    for r in rows:
        by[(r["sleeve"], r["sym"], r["date"])] = r
    return [r for _k, r in sorted(by.items(), key=lambda kv: (kv[0][2], kv[0][0], kv[0][1]))]


def stage_cache(paths: int) -> dict:
    import mc_firm_rules as Q
    M = Q.M

    st = M.build([])
    rows = st["rows"]
    for r in rows:
        r["R_legacy"] = r["R"]
    _, _, _, sd_book = M.build_matrix_from(rows, "R_legacy")

    kept, dropped = _dedup_day_key(rows)
    kept_last = _dedup_day_key_last(rows)
    print(f"cache population: {len(rows)} rows -> {len(kept)} after the day-key clause "
          f"({1 - len(kept)/len(rows):.1%} suppressed, LOWER BOUND)", flush=True)

    per_sleeve = {}
    for s in sorted({r["sleeve"] for r in rows}):
        n = sum(1 for r in rows if r["sleeve"] == s)
        k = sum(1 for r in kept if r["sleeve"] == s)
        per_sleeve[s] = {"cache_rows": n, "after_day_key_clause": k,
                         "suppressed": n - k,
                         "suppressed_frac_LOWER_BOUND": round(1 - k / n, 5) if n else None}

    # The books whose numbers are published. `mx_btcusd` has NO cache rows at all -- its 318
    # trades live in AA's archive walk (`ai_books_mc.py:25`) -- so the armed FTMO book is
    # NOT priceable on this population and there is no cell claiming to be it. The
    # cache-resident four are named as the four they are.
    books = {
        "ARMED_CACHE_RESIDENT_4": list(ARMED["redacted_account"]),
        "SURVIVORS_BOTH_ACCOUNTS_3": ["crypto", "energy_agri", "sub_xvol_pullback"],
        "ALL_11_BOOK_OF_RECORD": sorted({r["sleeve"] for r in rows}),
    }
    out_books: dict = {}
    for label, keep in books.items():
        cell = {}
        for acct in ("FTMO", "redacted_account"):
            cm = {k: statistics.median(v)
                  for k, v in Q._priced_pool(rows, acct).items()}
            arms = {}
            for guard, pool in (("published_no_guard", rows),
                                ("day_key_guard", kept),
                                ("day_key_guard_tiebreak_last", kept_last)):
                sub = [dict(r) for r in pool if r["sleeve"] in keep]
                if not sub:
                    continue
                days, comb, risk, vs = Q.series(
                    sub, acct, cm, "max", sd_book, forward=True,
                    kelly=Q.KELLY_HALF, risk_basis=Q.RISK_LIVE_NOMINAL)
                if not days:
                    continue
                a, b = min(days), max(days)
                sess = Q.weekday_sessions(a, b)
                months = (b.year - a.year) * 12 + (b.month - a.month) + 1
                c = dict(book_days=len(days), weekday_sessions=sess,
                         book_days_per_calendar_month=len(days) / months,
                         mean_r_per_book_day=statistics.fmean(comb),
                         risk=risk, vol_scale=vs)
                rules, _firm = Q.rule_sets(acct)
                res = {}
                for rr in rules:
                    if rr.label not in ("L4_FIRM_TRUE_PH1", "P2_BOTH_PHASES"):
                        continue
                    m = Q.mc(comb, risk, rr, paths)
                    d = Q._derived(c, m)
                    res[rr.label] = {"p_pass": m["p_pass"], **d}
                arms[guard] = {**{k: (round(v, 6) if isinstance(v, float) else v)
                                  for k, v in c.items()},
                               "rules": res}
            if arms:
                cell[acct] = arms
        out_books[label] = {"sleeves_priced": sorted(keep), "accounts": cell}
        for acct, arms in cell.items():
            a0 = arms.get("published_no_guard")
            a1 = arms.get("day_key_guard")
            if not (a0 and a1):
                continue
            p2a = (a0["rules"].get("P2_BOTH_PHASES") or {})
            p2b = (a1["rules"].get("P2_BOTH_PHASES") or {})
            print(f"  {label:28s} {acct:11s} "
                  f"book_days {a0['book_days']:4d}->{a1['book_days']:4d}  "
                  f"%/mo {p2a.get('monthly_pct_calendar'):7.3f}->"
                  f"{p2b.get('monthly_pct_calendar'):7.3f}  "
                  f"P2 p_pass {p2a.get('p_pass'):.4f}->{p2b.get('p_pass'):.4f}  "
                  f"cal-days {p2a.get('median_calendar_days_to_pass')}->"
                  f"{p2b.get('median_calendar_days_to_pass')}", flush=True)

    return {
        "what": ("BB handoff 1: re-derive book_days on the W7 recost cache population and "
                 "restate the calendar columns every published %/mo and days-to-pass rests on."),
        "VERDICT": (
            "CLOSED WITH A NEGATIVE RESULT, and the negative is the useful part. The "
            "measurable clause cannot move `book_days` AT ALL -- not empirically, "
            "STRUCTURALLY: it keeps the first row of every (sleeve, symbol, day), so a day "
            "that carried a decision still carries a fill and no day can be emptied. Measured "
            "here 382->382, 173->173, 117->117, and `clause_isolation_on_the_archive` shows "
            "the same clause alone costs 0 book-days on the population where BOTH clauses can "
            "run. So the calendar-clock inflation BB measured is attributable ENTIRELY to the "
            "clause that needs exit times, and no arithmetic on these caches can produce a "
            "corrected calendar column. BB's refusal to transfer its 1.333x was right and now "
            "has a mechanism behind it rather than a caution."),
        "and_the_economic_half_is_BRACKETED_not_corrected": (
            "the guard does move `mean_r_per_book_day`, because it deletes the second and "
            "later trades on a (sleeve, symbol, day) and those trades carry R. But WHICH one "
            "survives is set by an intra-day ordering the cache does not record: keep-first "
            "makes the armed-four cell BETTER (4.955 -> 5.370 %/mo) and keep-last makes it "
            "WORSE (-> 4.537). The published figure sits inside that bracket, so it is not "
            "shown to be wrong -- it is shown to be unresolvable on this population to better "
            "than about +/-0.42 %/month. Closing it needs entry times, which is the archive "
            "population, which is `armed` above."),
        "instrument": (
            "the live guard's DAY-KEY clause only (book_owner.py:1727-1735: one placement per "
            "(sleeve, symbol, decision day)). The one-open-position-per-broker-symbol clause "
            "(:1823-1850) needs entry/exit times and no exit index survives in any cache "
            "(SESSION_N §8.1), so it is NOT applied. Every figure here is a LOWER BOUND on the "
            "suppression and therefore an UPPER BOUND on the surviving economics."),
        "arithmetic_that_moves": (
            "monthly_pct_calendar = mean_r_per_book_day * risk * book_days_per_calendar_month "
            "(mc_firm_rules.py:625-627) and median_calendar_days_to_pass = med_days_pass * "
            "weekday_sessions / book_days (:622-624). The guard moves BOTH the numerator "
            "(which rows survive, so the daily series changes) and the divisor (how many days "
            "carry a fill), which is why this is measured rather than scaled by BB's 1.333x."),
        "conventions": ("forward 2025+, sleeve_max nights (worst carry), live nominal "
                        "half-Kelly -- the cell BOOKS_MC_V1 publishes as the armed book's."),
        "cache_rows_total": len(rows),
        "cache_rows_after_day_key_clause": len(kept),
        "suppressed_frac_LOWER_BOUND": round(1 - len(kept) / len(rows), 5),
        "per_sleeve": per_sleeve,
        "dropped_by_sleeve": dropped,
        "books": out_books,
        "clause_isolation_on_the_archive": _clause_isolation(),
    }


def _clause_isolation() -> dict:
    """Run each guard clause ALONE on the archive walk, where both clauses are computable.

    The point is not the totals -- BB published those. It is the BOOK-DAY column: if the
    day-key clause alone costs zero book-days here, where the data is complete, then its
    zero on the cache population is a property of the clause rather than a shortage of
    evidence, and the cache genuinely cannot answer BB's handoff-1 question.
    """
    import bb_fill_truth as FT
    est = json.loads(gzip.open(ESTATE, "rt").read())
    book = ARMED["redacted_account"]           # BB's four -- the set BB measured, for comparability
    proj = FT.project([r for s in book for r in (est["trades"].get(s) or [])])
    rows = sorted((r for r in proj if r["sleeve"] in book),
                  key=lambda r: (r["entry_utc"], r["sleeve"], r["symbol"]))

    def _run(day_key: bool, occupancy: bool) -> dict:
        busy: dict = {}
        placed: set = set()
        filled = []
        for r in rows:
            sym = FT._canon(r["symbol"])
            e, x = FT._dtp(r["entry_utc"]), FT._dtp(r["exit_utc"])
            if day_key and (r["sleeve"], sym, r["decision_day"]) in placed:
                continue
            held = busy.get(sym)
            if occupancy and held is not None and e < held:
                continue
            busy[sym] = x
            placed.add((r["sleeve"], sym, r["decision_day"]))
            filled.append(r)
        days = {r["decision_day"] for r in filled}
        return {"fills": len(filled), "book_days": len(days)}

    none = _run(False, False)
    both = _run(True, True)
    out = {
        "population": "AQ_ESTATE_TRADES_V2 archive walk, the four cache-resident armed sleeves",
        "no_guard": none,
        "day_key_clause_only": _run(True, False),
        "symbol_occupancy_clause_only": _run(False, True),
        "both_clauses": both,
    }
    for k in ("day_key_clause_only", "symbol_occupancy_clause_only", "both_clauses"):
        out[k]["book_days_lost_vs_no_guard"] = none["book_days"] - out[k]["book_days"]
        out[k]["fills_lost_vs_no_guard"] = none["fills"] - out[k]["fills"]
    out["reading"] = (
        f"the day-key clause alone costs "
        f"{out['day_key_clause_only']['book_days_lost_vs_no_guard']} book-days and "
        f"{out['day_key_clause_only']['fills_lost_vs_no_guard']} fills; the symbol-occupancy "
        f"clause alone costs {out['symbol_occupancy_clause_only']['book_days_lost_vs_no_guard']}"
        f" book-days. The calendar clock is the second clause's doing, and the second clause "
        f"is the one the caches cannot express.")
    print(f"  clause isolation: no_guard {none}  day_key_only "
          f"{out['day_key_clause_only']}  occupancy_only "
          f"{out['symbol_occupancy_clause_only']}  both {both}", flush=True)
    return out


# =====================================================================================
# STAGE armed — the CURRENT armed sets, at the contract each actually runs
# =====================================================================================
def _mx_rows_at(cell: str) -> tuple[list[dict], dict]:
    """`mx_btcusd`'s AA rows re-labelled at `cell` ('as_walked' or 'target_5R')."""
    import ad_exit_sweep as AD
    est = json.loads(gzip.open(ESTATE, "rt").read())
    base = est["trades"][MX]
    series, index, _ = AD.load_bars()
    costs = AD.load_broker_true_costs(AD.COSTS)
    rule = AD.resolve_rule("FTMO-Server3")
    if cell == "as_walked":
        var = AD.AS_WALKED
    else:
        var = AD.Variant(name="target_5R", family="target",
                         target_mode="fixed_r", target_r=5.0)
    rows, tel = AD.resimulate(base, var, series, index, costs, "FTMO", rule)
    return rows, dict(tel)


def stage_armed() -> dict:
    import bb_fill_truth as FT
    est = json.loads(gzip.open(ESTATE, "rt").read())
    tf_of = dict(est["timeframe_by_sleeve"])
    cov = FT.bar_coverage()

    pools: dict[str, list[dict]] = {s: list(v) for s, v in est["trades"].items() if v}
    mx5, tel5 = _mx_rows_at("target_5R")
    mxaw, telaw = _mx_rows_at("as_walked")
    print(f"mx_btcusd relabelled: as_walked n={len(mxaw)}  target_5R n={len(mx5)} "
          f"(telemetry {telaw} / {tel5})", flush=True)

    arms: dict = {}
    for acct, book in ARMED.items():
        for cell in (("target_5R", "as_walked_CONTROL") if MX in book else ("n_a",)):
            pool = dict(pools)
            label = acct
            if MX in book:
                pool[MX] = mx5 if cell == "target_5R" else mxaw
                label = f"{acct}::mx_{cell}"
            proj = FT.project([r for s in book for r in (pool.get(s) or [])])
            occ = FT.occupancy(proj, book)
            filled = set(occ["filled_keys"])
            cad = FT.cadence(proj, book, cov, filled, tf_of)
            lo = cad["book"]["live_equivalent"]
            ar = cad["book"]["archive"]
            arms[label] = {
                "account": acct, "armed_tags": list(book),
                "mx_contract": (None if MX not in book else cell),
                "provenance": ARMED_PROVENANCE[acct],
                "n_archive_decisions": occ["n_archive_decisions"],
                "n_live_equivalent_fills": occ["n_live_equivalent_fills"],
                "suppression_frac": occ["suppression_frac"],
                "per_sleeve": occ["per_sleeve"],
                # Per-sleeve RATES come from BB's cadence stage, never from
                # decisions/book-window: a sleeve's decisions span its own symbols'
                # availability, not the book's common window, and dividing one by the other
                # inflates any sleeve older than the book (a first cut of `stage_stops` did
                # exactly that and read `mx_btcusd` at 3.5 decisions/week).
                "cadence_per_sleeve": {
                    s: {"archive_fills_per_week":
                            (cad["per_sleeve"][s] or {}).get("availability_fills_per_week"),
                        "live_equivalent_fills_per_week":
                            (cad["per_sleeve"][s] or {}).get(
                                "availability_live_fills_per_week")}
                    for s in book},
                "FULL_SURFACE_from": lo.get("FULL_SURFACE_from"),
                "live_equivalent": lo, "archive_walk": ar,
            }
            print(f"  {label:28s} decisions={occ['n_archive_decisions']:4d} -> "
                  f"fills={occ['n_live_equivalent_fills']:4d} "
                  f"({occ['suppression_frac']:.1%} suppressed)  "
                  f"live {lo.get('FULL_SURFACE_fills_per_week')}/wk  "
                  f"book-days/mo {lo.get('FULL_SURFACE_book_days_per_calendar_month')}",
                  flush=True)

    # what the fifth sleeve actually bought, and what it displaced
    base = FT.project([r for s in ARMED["redacted_account"] for r in (pools.get(s) or [])])
    occ4 = FT.occupancy(base, ARMED["redacted_account"])
    marginal = {}
    for cell, rows in (("target_5R", mx5), ("as_walked", mxaw)):
        pool = dict(pools)
        pool[MX] = rows
        proj = FT.project([r for s in ARMED["FTMO"] for r in (pool.get(s) or [])])
        occ5 = FT.occupancy(proj, ARMED["FTMO"])
        before = {s: occ4["per_sleeve"][s]["live_equivalent_fills"]
                  for s in ARMED["redacted_account"]}
        after = {s: occ5["per_sleeve"][s]["live_equivalent_fills"]
                 for s in ARMED["redacted_account"]}
        marginal[cell] = {
            "book_fills_four": occ4["n_live_equivalent_fills"],
            "book_fills_five": occ5["n_live_equivalent_fills"],
            "MARGINAL_fills": occ5["n_live_equivalent_fills"] - occ4["n_live_equivalent_fills"],
            "mx_own_decisions": occ5["per_sleeve"][MX]["archive_decisions"],
            "mx_own_fills": occ5["per_sleeve"][MX]["live_equivalent_fills"],
            "mx_own_suppression": occ5["per_sleeve"][MX]["suppression_frac"],
            "incumbent_fills_displaced": {s: before[s] - after[s]
                                          for s in before if before[s] != after[s]},
        }
        print(f"  marginal[{cell:10s}] four={marginal[cell]['book_fills_four']} -> "
              f"five={marginal[cell]['book_fills_five']} "
              f"(+{marginal[cell]['MARGINAL_fills']}); mx {marginal[cell]['mx_own_fills']}"
              f"/{marginal[cell]['mx_own_decisions']} fills; displaced "
              f"{marginal[cell]['incumbent_fills_displaced']}", flush=True)

    return {
        "what": ("BB handoff 4: the fill-truth measurement is a property of the ARMED SET, and "
                 "the set changed twice after BB stamped it. Re-measured per account, with "
                 "`mx_btcusd` at the contract FTMO actually runs (target_5R via "
                 "--frontier-exits) and at its committed 2R contract as a control."),
        "arms": arms,
        "the_fifth_sleeve_marginal": marginal,
        "why_the_control": (
            "the frontier contract holds trades LONGER (AU: 89 targets vs 143 at 2R, 6 maxbars "
            "vs 0), and a longer hold occupies the broker symbol for longer. `mx_btcusd` trades "
            "BTCUSD, which `crypto` also trades, so the fifth sleeve can DISPLACE an incumbent "
            "fill rather than add one. Measuring it at 2R would price a book FTMO does not run."),
    }


# =====================================================================================
# STAGE stops — what fill truth does to AS's pre-registered conditions
# =====================================================================================
def stage_stops(armed: dict) -> dict:
    cond = json.loads(STOPS.read_text())
    #: Every threshold AS pre-registered is denominated in FILLS or in R, never in calendar
    #: time. Fill truth does not move a single threshold VALUE -- it moves how long the owner
    #: waits before the condition can be evaluated at all, and that is the number a person
    #: reading a monitor actually needs.
    horizons = {
        "S1a_risk_floor": ("fills_to_trip_at_archive_expectancy", "per_sleeve_account"),
        "S1b_evidence_floor": (None, "per_sleeve_account"),
        "S2_gross_negative": ("min_fills", None),
        "S5_stop_out_run": ("stop_run", None),
    }
    rows = {}
    for acct, book in ARMED.items():
        key = f"{acct}::mx_target_5R" if acct == "FTMO" else acct
        arm = armed["arms"].get(key) or armed["arms"].get(acct)
        if not arm:
            continue
        per = arm["per_sleeve"]
        rates = arm["cadence_per_sleeve"]
        for sleeve in book:
            ps = per.get(sleeve) or {}
            rt = rates.get(sleeve) or {}
            f_live = rt.get("live_equivalent_fills_per_week") or 0.0
            f_arch = rt.get("archive_fills_per_week") or 0.0
            sk = f"{acct}::{sleeve}"
            base = ((cond["conditions"]["S1a_risk_floor"].get("per_sleeve_account") or {})
                    .get(sk) or {})
            n_s1 = base.get("fills_to_trip_at_archive_expectancy")
            out = {
                "armed": True,
                "archive_decisions": ps.get("archive_decisions"),
                "live_equivalent_fills": ps.get("live_equivalent_fills"),
                "own_suppression_frac": ps.get("suppression_frac"),
                "fills_per_week_archive_convention": round(f_arch, 4),
                "fills_per_week_LIVE_EQUIVALENT": round(f_live, 4),
                "rate_basis": ("per-symbol rate over each symbol's OWN bar-availability "
                               "window, summed (bb_fill_truth.cadence -> "
                               "availability_[live_]fills_per_week)"),
                "cadence_inflation_x": (round(f_arch / f_live, 3) if f_live else None),
                "weeks_to_evaluate": {},
            }
            for cid, n in (("S1a_risk_floor", n_s1),
                           ("S1b_evidence_floor", 60),
                           ("S2_gross_negative", 20),
                           ("S5_stop_out_run", 9)):
                if not n:
                    continue
                out["weeks_to_evaluate"][cid] = {
                    "fills_required": n,
                    "weeks_at_archive_convention": (round(n / f_arch, 1) if f_arch else None),
                    "weeks_at_LIVE_fill_rate": (round(n / f_live, 1) if f_live else None),
                    "months_at_LIVE_fill_rate": (round(n / f_live / 4.348, 1)
                                                 if f_live else None),
                }
            rows[sk] = out
    return {
        "what": ("what fill truth does to `phase11/receipts/FIVE_SLEEVE_STOP_CONDITIONS_V1.json`. "
                 "Answer, stated first because it is the part that could be misread: it moves "
                 "NO threshold. Every one is denominated in R or in FILLS, and a fill is a fill "
                 "whether or not the guard ate its siblings."),
        "what_it_DOES_move": (
            "the calendar time before any of them can be evaluated. S1b's bootstrap horizon is "
            "60 FILLS and S2 needs 20 over >= 8 day blocks; at the live-equivalent per-sleeve "
            "fill rate those are the numbers below, and several of them are longer than the "
            "evaluation windows anyone has been assuming."),
        "the_one_threshold_that_IS_calendar_denominated": (
            "`scripts/book_silence_check.py`'s 15/22 silent weekday sessions -- and it is "
            "already at fill truth, because BB derived it from the live-equivalent gap "
            "distribution. It is a property of the ARMED SET, so it is restated here for the "
            "current sets rather than inherited from BB's four."),
        "per_sleeve_account": rows,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all", choices=("all", "cache", "armed", "stops"))
    ap.add_argument("--paths", type=int, default=20000)
    a = ap.parse_args(argv)
    t0 = time.time()
    doc: dict = {
        "schema": "gtos.wave14.ca.fill_truth_restate.v1",
        "session": "CA", "blocks": "B2120-B2134",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "armed_sets": {k: list(v) for k, v in ARMED.items()},
        "armed_set_provenance": ARMED_PROVENANCE,
        "reads": {"bb_fill_truth": str(BB_FILL.relative_to(REPO)),
                  "books_mc": str(BOOKS_MC.relative_to(REPO)),
                  "stop_conditions": str(STOPS.relative_to(REPO)),
                  "estate": str(ESTATE.relative_to(REPO))},
        "arms_nothing": ("every number here is a measurement or a restatement. No config byte "
                         "moves, no R2-bound path is touched, no broker-capable script runs."),
    }
    prev = json.loads(OUT.read_text()) if OUT.is_file() else {}
    if a.stage in ("all", "armed"):
        doc["armed"] = stage_armed()
    elif prev.get("armed"):
        doc["armed"] = prev["armed"]
    if a.stage in ("all", "cache"):
        doc["cache_population"] = stage_cache(a.paths)
    elif prev.get("cache_population"):
        doc["cache_population"] = prev["cache_population"]
    if a.stage in ("all", "stops") and doc.get("armed"):
        doc["stop_conditions_at_fill_truth"] = stage_stops(doc["armed"])
    doc["seconds_total"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
