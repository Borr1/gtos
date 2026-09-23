"""Session BB (B1976-B1999) — the supply hunt, ranked by FIRE RATE and priced.

    python3 .../phase13/receipts/bb_supply_rank.py --stage fire
    python3 .../phase13/receipts/bb_supply_rank.py --stage gate
    python3 .../phase13/receipts/bb_supply_rank.py --stage price
    python3 .../phase13/receipts/bb_supply_rank.py            # all, then rank

THE QUESTION
------------
`BB_FILL_TRUTH_V1.json` measured that the armed four fill **1.39 times a week** and hold
**4.23 book-days a month** once the live placement guards are applied, and that the calendar
clock every published figure uses is 1.33x optimistic because it divides by an unserialized
book-day count. The plan's Stage-1 risk is therefore live, not hypothetical.

This file asks the other half: **what could honestly raise it.** Not "which sleeve has the
best expectancy" — the estate has asked that a dozen times — but *which generator adds FILLS
the armed book does not already have*, at what cost in pass probability.

THE AXIS IS MARGINAL, AND THAT IS THE POINT
--------------------------------------------
A candidate's own trade count is not its supply. Two corrections, both measured here:

  * the same occupancy queue that eats 32 % of the armed four eats a candidate's fills too,
    and worse if it shares symbols with the book (`sub_xvol_pullback` and
    `sub_mid_dn_revert` already collide on eight symbols);
  * a candidate that fires on a symbol the book already holds does not add a fill, it
    *replaces* one — so its marginal contribution can be far below its raw rate and, for a
    symbol-colliding candidate, could in principle be negative for the incumbent.

So the ranking axis is `fills(armed4 + candidate) - fills(armed4)` through the live guards,
on one common window, and the per-sleeve displacement is published beside it.

THE WINDOW IS SET BY AVAILABILITY, NOT BY RESULTS
--------------------------------------------------
2024-10-29 .. 2026-07-27: the date the last of the armed four's symbols enters the archive
(DASHUSD H4), which `BB_FILL_TRUTH_V1` already fixed for the incumbent book. Every candidate
is measured on the same calendar so the counts are comparable, and any candidate whose own
symbols do not fully exist in it is flagged rather than silently under-counted. This is X's
leak-free criterion (`x_common_window_book.py`: "set by data availability, not by results").

THE ECONOMICS COLUMN IS THE RATIFIED RULE, AND IT IS NOT A NEW CUT
-------------------------------------------------------------------
`RECORDED`, all four cost bands, `B_balanced` at the sealed alpha 0.10, corrected against
`CANDIDATE_BOOK_V1` (53) — the ratified rule (`POPULATION_RULE_V1.ratified_rule`,
`CANDIDATE_FAMILY_V1.ratified_rule`). The band travels with every verdict and no admission
is printed bare. The commission's ">= N/week" screen is published as a continuous column
with N left to the reader, per this session's declared cut rule
(`CANDIDATE_FAMILY_V10.json -> bb_declaration_note`).

WHAT THIS FILE DOES NOT DO
---------------------------
It arms nothing and recommends no arming. Its output is a ranked, priced shortlist for
Borhen, in the OD-AI-3 shape: what each candidate buys in fills and calendar, what it costs
in `p_pass`, and whether it passes an admission standard (mostly: no, and that is said).

BOUNDARY. Offline and pure. Reads committed receipts and the read-only bar archive; writes
one JSON. Touches no broker, no config, no R2-bound path.
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
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(P7))
sys.path.insert(0, str(HERE))

ESTATE = P11 / "AQ_ESTATE_TRADES_V2.json.gz"
AK_TRADES = P8 / "AK_SUPPLY_TRADES.json.gz"
FAMILY = HERE / "CANDIDATE_FAMILY_V10.json"
FILL_TRUTH = HERE / "BB_FILL_TRUTH_V1.json"
OUT = HERE / "BB_SUPPLY_RANK_V1.json"

ARMED4 = ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert")
WINDOW_FROM = dt.date(2024, 10, 29)
ARCHIVE_END = dt.date(2026, 7, 27)
ACCOUNT, SERVER = "FTMO", "FTMO-Server3"
BANDS = (None, "low", "mid", "high")

import bb_fill_truth as FT  # noqa: E402  (the projection + guard model, imported not copied)


def _weeks(a, b):
    return max((b - a).days, 0) / 7.0


# =====================================================================================
# substrate
# =====================================================================================
def load_pools() -> tuple[dict, dict]:
    """(estate trades by sleeve, provenance). AQ's V2 plus AK's four unregistered ones."""
    est = json.loads(gzip.open(ESTATE, "rt").read())
    pool = {s: list(r) for s, r in est["trades"].items() if r}
    prov = {s: "AQ_ESTATE_TRADES_V2" for s in pool}
    tf = dict(est["timeframe_by_sleeve"])
    if AK_TRADES.is_file():
        ak = json.loads(gzip.open(AK_TRADES, "rt").read())
        for s, rows in (ak.get("trades") or {}).items():
            if not rows or s in pool:
                continue
            pool[s] = list(rows)
            prov[s] = "AK_SUPPLY_TRADES"
            tf.setdefault(s, (ak.get("timeframe_by_sleeve") or {}).get(s, "?"))
    return pool, {"provenance": prov, "timeframe": tf}


# =====================================================================================
# STAGE fire — the marginal-supply axis. Outcome-blind: FT.project() is the only path in.
# =====================================================================================
def fire(pool: dict, meta: dict) -> dict:
    def win(rows):
        return [r for r in rows
                if WINDOW_FROM <= dt.date.fromisoformat(r["entry_utc"][:10]) <= ARCHIVE_END]

    base_rows = FT.project([r for s in ARMED4 for r in win(pool.get(s) or [])])
    base = FT.occupancy(base_rows, ARMED4)
    base_n = base["n_live_equivalent_fills"]
    wk = _weeks(WINDOW_FROM, ARCHIVE_END)

    cov = FT.bar_coverage()
    rows_out = {}
    for cand in sorted(pool):
        if cand in ARMED4:
            continue
        crows = win(pool[cand])
        if not crows:
            rows_out[cand] = {"n_in_window": 0, "note": "no decisions in the common window"}
            continue
        book = tuple(ARMED4) + (cand,)
        proj = FT.project([r for s in book for r in win(pool.get(s) or [])])
        with_c = FT.occupancy(proj, book)
        per = with_c["per_sleeve"]
        incumbent_before = {s: base["per_sleeve"][s]["live_equivalent_fills"] for s in ARMED4}
        incumbent_after = {s: per[s]["live_equivalent_fills"] for s in ARMED4}
        displaced = {s: incumbent_before[s] - incumbent_after[s] for s in ARMED4
                     if incumbent_before[s] != incumbent_after[s]}

        # availability inside the common window: is this candidate fully measurable here?
        tf = meta["timeframe"].get(cand, "H4")
        late = {}
        for sym in {FT._canon(r["symbol"]) for r in crows}:
            c = cov.get(f"{sym}|{tf}") or {}
            if c.get("first") and dt.date.fromisoformat(c["first"]) > WINDOW_FROM:
                late[sym] = c["first"]

        rows_out[cand] = {
            "provenance": meta["provenance"].get(cand),
            "timeframe": tf,
            "n_in_window": len(crows),
            "own_archive_rate_per_week": round(len(crows) / wk, 4),
            "own_live_equivalent_fills": per[cand]["live_equivalent_fills"],
            "own_suppression_frac": per[cand]["suppression_frac"],
            "book_fills_before": base_n,
            "book_fills_after": with_c["n_live_equivalent_fills"],
            "MARGINAL_fills": with_c["n_live_equivalent_fills"] - base_n,
            "MARGINAL_fills_per_week": round(
                (with_c["n_live_equivalent_fills"] - base_n) / wk, 4),
            "displaces_incumbent_fills": displaced,
            "symbols_not_fully_available_in_window": late or None,
            "shares_symbols_with_armed_four": sorted(
                {FT._canon(r["symbol"]) for r in crows}
                & {FT._canon(r["symbol"]) for s in ARMED4 for r in win(pool.get(s) or [])}),
        }
    return {
        "window": f"{WINDOW_FROM.isoformat()}..{ARCHIVE_END.isoformat()}",
        "window_basis": ("the date the last of the armed four's symbols enters the archive "
                         "(DASHUSD H4). Availability, never results — X's criterion."),
        "weeks": round(wk, 1),
        "armed_four_baseline": {
            "archive_decisions": base["n_archive_decisions"],
            "live_equivalent_fills": base_n,
            "fills_per_week": round(base_n / wk, 4),
            "per_sleeve": base["per_sleeve"],
        },
        "candidates": rows_out,
    }


# =====================================================================================
# STAGE gate — the estate at the RATIFIED rule, all four bands
# =====================================================================================
def gate(pool: dict) -> dict:
    import ad_exit_sweep as AD
    from src.research_infra.walkforward import candidate_family as CF
    from src.research_infra.walkforward import era_population as EP
    from src.research_infra.walkforward import run_gate
    from src.research_infra.walkforward.options import OPTIONS

    costs = AD.load_broker_true_costs(AD.COSTS)
    allow = AD.allowlist()
    fam = CF.load_candidate_family(FAMILY)
    arms: dict[str, dict] = {}
    for band in BANDS:
        t0 = time.time()
        o = OPTIONS["B_balanced"]
        spec = o.with_(spec_id=f"{o.spec_id}_bb_supply",
                       sleeve_symbol_allowlist=allow, spread_band=band)
        spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=fam)
        recs0 = {s: AD.to_records(r) for s, r in pool.items()}
        recs, spec, mix = EP.apply("RECORDED", recs0, spec, account=ACCOUNT)
        res = run_gate(recs, spec, costs=costs, server=SERVER, diagnose=False)
        key = band or "flat_37_day_snapshot_CONTROL"
        arms[key] = {
            "band": key, "band_is_control": band is None,
            "population": "RECORDED", "option": "B_balanced", "alpha": spec.alpha,
            "declared_family_size": spec.declared_family_size,
            "declared_family_id": spec.declared_family_id,
            "spec_sha256": spec.seal(),
            "n_sleeves_judged": len(res.verdicts),
            "population_mix": mix,
            "seconds": round(time.time() - t0, 1),
            "verdicts": {
                s: {"verdict": v.verdict.value,
                    "n_trades": v.n_trades,
                    "pooled_oos_mean_r": v.pooled_oos_mean_r,
                    "p_raw": v.p_raw, "q_value": v.q_value,
                    "failing_core_gates": [g for g, d in v.gates.items()
                                           if isinstance(d, dict) and d.get("pass") is False],
                    "first_reason": (v.reasons[0] if v.reasons else None)}
                for s, v in sorted(res.verdicts.items())},
        }
        adm = [s for s, v in res.verdicts.items() if v.verdict.value == "ADMIT"]
        print(f"  gate RECORDED band={key:28s} judged={len(res.verdicts):3d} "
              f"ADMIT={adm} ({arms[key]['seconds']}s)", flush=True)
    return {
        "rule": ("the RATIFIED rule: RECORDED population (POPULATION_RULE_V1.ratified_rule), "
                 "B_balanced at the sealed alpha 0.10 (CANDIDATE_FAMILY_V1.ratified_rule), "
                 "corrected against CANDIDATE_BOOK_V1, band published with every verdict"),
        "arms": arms,
    }


# =====================================================================================
# STAGE price — the fifth sleeve, in the OD-AI-3 shape
# =====================================================================================
def price(pool: dict, shortlist, *, paths: int) -> dict:
    import yaml
    sys.path.insert(0, str(REPO / "scripts"))
    import mc_firm_rules as Q
    from src.research_infra.walkforward import TradeRecord
    from src.research_infra.walkforward.book_replay import (
        BookConfig, BookTrade, book_daily_series, book_stats, replay_book)
    from src.research_infra.walkforward.options import OPTIONS
    from src.research_infra.walkforward.panel import price_trades

    spec = OPTIONS["B_balanced"].with_(spec_id="bb_supply_price_cost")
    rt = dict(yaml.safe_load(open(REPO / "config/agent_config.yaml"))
              .get("gtos_vnext_runtime") or {})
    rt["ultimate_book_include_clean3"] = True

    priced: dict[str, list] = {}
    for sleeve in set(ARMED4) | set(shortlist):
        rows = [r for r in (pool.get(sleeve) or [])
                if WINDOW_FROM <= dt.date.fromisoformat(r["entry_utc"][:10]) <= ARCHIVE_END]
        if not rows:
            continue
        recs = [TradeRecord(
            sleeve=r["sleeve"], symbol=r["symbol"],
            entry_utc=dt.datetime.fromisoformat(r["entry_utc"]),
            exit_utc=dt.datetime.fromisoformat(r["exit_utc"]),
            direction=int(r["direction"]),
            sl_distance_price=float(r["sl_distance_price"]),
            entry_price=float(r["entry_price"]), r_gross=float(r["r_gross"]),
            features={"symbol_canonical": r["symbol_canonical"],
                      "decision_day": r["decision_day"],
                      "decision_bar_iso": r["decision_bar_iso"],
                      "timeframe": r["timeframe"]}) for r in rows]
        p, _c = price_trades(recs, spec)
        keep = [BookTrade(
            sleeve=x.trade.sleeve, symbol=x.trade.symbol,
            symbol_canonical=x.trade.features["symbol_canonical"],
            entry_utc=x.trade.entry_utc, exit_utc=x.trade.exit_utc,
            direction=x.trade.direction, stop_dist=x.trade.sl_distance_price,
            entry_price=x.trade.entry_price, r_net=float(x.r_net),
            decision_day=str(x.trade.features["decision_day"]),
            decision_bar_iso=str(x.trade.features["decision_bar_iso"]),
            timeframe=x.trade.features["timeframe"])
            for x in p if x.status == "priced" and x.r_net is not None]
        if keep:
            priced[sleeve] = keep

    rules, firm = Q.rule_sets(ACCOUNT)
    of_record = {r.label: r for r in rules if r.label in ("L4_FIRM_TRUE_PH1",
                                                          "P2_BOTH_PHASES")}
    sess = FT._weekday_sessions(WINDOW_FROM, ARCHIVE_END)
    wk = _weeks(WINDOW_FROM, ARCHIVE_END)

    def one(label, sleeves):
        flat = [t for s in sleeves if s in priced for t in priced[s]]
        if not flat:
            return None
        res = replay_book(flat, BookConfig(runtime=rt, sleeves=tuple(sorted(sleeves)),
                                           label=f"bb_{label}"))
        st = book_stats(res)
        series = book_daily_series(res)
        vals = list(series.values())
        if len(vals) < 6:
            return {"n_placed": st["n_placed"], "book_days": len(vals),
                    "note": "series too short to price"}
        dens = len(vals) / sess
        mc = {}
        for lbl, r in of_record.items():
            m = Q.mc(vals, 1.0, r, paths, seed_base=1, start_equity=Q_START_EQ)
            md = m["med_days_pass"]
            mc[lbl] = {
                "p_pass": round(m["p_pass"], 5),
                "p_fail_dd": round(m["p_fail_dd"], 5),
                "p_fail_daily": round(m["p_fail_daily"], 5),
                "p_timeout": round(m["p_timeout"], 5),
                "median_book_days_to_pass": md,
                "median_calendar_days_to_pass": (round(md / dens * 7 / 5) if md and dens
                                                 else None),
            }
        by_sleeve = dict(collections.Counter(p["sleeve"] for p in res.placed))
        cand_name = [s for s in sleeves if s not in ARMED4]
        cand_name = cand_name[0] if cand_name else None
        wiring = None
        if cand_name and by_sleeve.get(cand_name, 0) == 0:
            unit_rej = {k: v for k, v in res.rejections.items() if k.startswith("unit:")}
            wiring = {
                "candidate": cand_name,
                "n_candidates_it_contributed": sum(
                    1 for t in flat if t.sleeve == cand_name),
                "n_placed": 0,
                "diagnosis": ("the PRODUCTION sizer emitted no sizeable unit for this "
                              "sleeve. `admission.effective_registry` has no entry for it, "
                              "so `size_correlated_units` has no confidence to size it "
                              "with. This is AK's LIVE_WIRING_GAP reproduced mechanically: "
                              "the sleeve cannot reach a book until a `SleeveSpec` exists "
                              "for it, and AK's REGISTRY_EDIT_PROPOSAL is that edit."),
                "unit_rejections": unit_rej,
                "HARNESS_CAVEAT": (
                    "live, DF-1 (`book_engine.py:452-453`) drops an out-of-registry spec "
                    "BEFORE generation, so such a sleeve never produces a candidate at "
                    "all. This harness feeds candidates directly, so any size shift on the "
                    "incumbents in this row is a harness artifact, NOT a live hazard, and "
                    "must not be read as one."),
            }
        return {
            "sleeves": sorted(sleeves),
            "n_candidates_priced": len(flat),
            "n_placed": st["n_placed"],
            "placed_by_sleeve": by_sleeve,
            "candidate_placed": (by_sleeve.get(cand_name, 0) if cand_name else None),
            "WIRING_GAP": wiring,
            "rejections": dict(sorted(res.rejections.items(), key=lambda kv: -kv[1])),
            "fills_per_week": round(st["n_placed"] / wk, 4),
            "book_days": len(vals),
            "book_day_density": round(dens, 5),
            "book_days_per_calendar_month": round(len(vals) / 22.0, 3),
            "mean_daily_frac": round(statistics.fmean(vals), 6),
            "sum_r_net": st["sum_r_net"],
            "total_return_pct": st["total_return_pct"],
            "max_drawdown_pct": st["max_drawdown_pct"],
            "book_daily_sharpe": st["book_daily_sharpe"],
            "mc": mc,
        }

    out = {"baseline_armed_four": one("armed4", ARMED4)}
    for cand in shortlist:
        r = one(f"armed4+{cand}", tuple(ARMED4) + (cand,))
        if r:
            out[f"armed4+{cand}"] = r
            print(f"  price armed4+{cand:34s} n={r.get('n_placed')} "
                  f"fills/wk={r.get('fills_per_week')} "
                  f"P2={r.get('mc', {}).get('P2_BOTH_PHASES', {}).get('p_pass')}", flush=True)
    return {
        "instrument": ("book_replay.replay_book for the book, mc_firm_rules.mc for the "
                       "challenge probability — both imported, neither reimplemented"),
        "firm_rules": firm,
        "start_equity": Q_START_EQ,
        "start_equity_basis": ("FTMO's equity on 2026-07-29 in units of its initial balance "
                               "(mc_firm_rules.py:156-157). The remaining distance to the "
                               "measured 10 % phase-1 target from here is +1.97 % of current "
                               "equity, which is the target BB_FILL_TRUTH_V1's clock uses."),
        "window": f"{WINDOW_FROM.isoformat()}..{ARCHIVE_END.isoformat()}",
        "paths": paths,
        "books": out,
        "caveat": ("every book here is measured on ONE 21-month window at the production "
                   "sizer. It is not an admission and no candidate in it passes one; read "
                   "the gate column beside it."),
    }


Q_START_EQ = 1.0787228


# =====================================================================================
def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all",
                    choices=("all", "fire", "gate", "price"))
    ap.add_argument("--paths", type=int, default=20000)
    ap.add_argument("--shortlist-n", type=int, default=8,
                    help="how many candidates to PRICE. Not a cut on the ranking, which "
                         "publishes every member; pricing is the expensive stage and its "
                         "budget is declared here rather than chosen after the fact.")
    args = ap.parse_args(argv)

    # The declaration must not have moved since it was committed.
    fam_doc = json.loads(FAMILY.read_text())
    print(f"family declaration {FAMILY.name} self_sha256 "
          f"{fam_doc['self_sha256'][:16]} — CANDIDATE_BOOK_V1 size "
          f"{fam_doc['families']['CANDIDATE_BOOK_V1']['high_water_size']}", flush=True)

    pool, meta = load_pools()
    doc: dict = {
        "schema": "gtos.live.sleeve_supply_rank.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase13/receipts/"
                         "bb_supply_rank.py"),
        "session": "BB", "blocks": "B1976-B1999",
        "armed_set": list(ARMED4),
        "declared_family": {"file": FAMILY.name, "sha256": fam_doc["self_sha256"],
                            "cut_rule": fam_doc["bb_declaration_note"][
                                "the_cut_rule_is_declared_not_just_the_axis"]},
        "pools": {"n_members": len(pool),
                  "by_provenance": dict(collections.Counter(meta["provenance"].values()))},
        "arms_nothing": ("this file is a ranked, priced shortlist for the owner. It arms "
                         "nothing and recommends no arming."),
        "READING": {
            "what_stands": (
                "DESCRIPTIVE, and it is enough to decide with: of the 15 candidates that "
                "would raise the armed four's fill rate by more than 1/week, 13 carry "
                "NEGATIVE cost-true OOS expectancy on RECORDED at the mid band. The two "
                "that do not are the two smallest suppliers of them. Priced through the "
                "production sizer, buying cadence from the negative ones is brutal: "
                "armed4+asia_pdl_fade takes fills 1.27 -> 8.87/week and P2 p_pass "
                "1.0 -> 0.1835 at an 11.25 % drawdown."),
            "what_does_NOT_stand": (
                "an estate-wide 'supply and edge are anti-correlated' LAW. This session's "
                "own adversarial pass measured it and it is not there: Spearman(marginal "
                "fills/week, OOS R/day) = -0.214 (p 0.267) over 28 candidates, and once "
                "the mechanical frequency-times-cost term in a PER-DAY expectancy is "
                "removed it is +0.015 (p 0.938) per trade. The first draft of this "
                "session's finding asserted the law; the measurement refused it. See "
                "BB_ADVERSARIAL_V1.json -> A2_cost_vs_edge."),
            "and_the_refutation_is_the_more_useful_result": (
                "if the high-supply sleeves were worse PER DECISION, the estate would have "
                "no cadence to buy and the only answer would be new generation. They are "
                "not: they are worse per DAY because they trade more often and pay more "
                "cost per day. That routes the prescription to the cost geometry — Session "
                "AY's lane — where the same sleeves could move without a single new "
                "signal. It does NOT make any of them armable today."),
        },
    }

    f = fire(pool, meta)
    doc["fire_rate"] = f
    ranked = sorted(
        ((c, r) for c, r in f["candidates"].items() if r.get("MARGINAL_fills_per_week")),
        key=lambda kv: -kv[1]["MARGINAL_fills_per_week"])
    print(f"\nfire: armed four fill {f['armed_four_baseline']['fills_per_week']}/week in "
          f"{f['weeks']:.0f} weeks; top marginal suppliers:")
    for c, r in ranked[:12]:
        print(f"  {c:38s} +{r['MARGINAL_fills_per_week']:.3f}/wk "
              f"(own {r['own_archive_rate_per_week']:.3f}/wk, "
              f"suppressed {r['own_suppression_frac']:.0%}, "
              f"displaces {sum(r['displaces_incumbent_fills'].values())})")

    if args.stage in ("all", "gate"):
        print("\ngate at the ratified rule:", flush=True)
        doc["gate_at_ratified_rule"] = gate(pool)

    if args.stage in ("all", "price"):
        # The priced set is the union of two PRE-DECLARED screens, neither chosen after the
        # ranking was seen: (a) the top-N by marginal fills/week, N declared as a compute
        # budget in --shortlist-n; (b) the commission's own screen, verbatim — "fire >= N/week
        # with NON-NEGATIVE cost-true economics on RECORDED" — which is a screen written
        # before any of this was measured. Publishing the union rather than either alone is
        # what stops the expensive stage from quietly becoming the cut.
        top = [c for c, _ in ranked[:args.shortlist_n]]
        mid = ((doc.get("gate_at_ratified_rule") or {}).get("arms", {})
               .get("mid", {}).get("verdicts", {}))
        nonneg = [c for c, _ in ranked
                  if (mid.get(c, {}).get("pooled_oos_mean_r") or -1.0) >= 0.0]
        short = sorted(set(top) | set(nonneg), key=lambda c:
                       -f["candidates"][c]["MARGINAL_fills_per_week"])
        doc["shortlist_priced"] = {
            "members": short,
            "screen_a_top_n_by_marginal_fills": top,
            "screen_b_commission_nonnegative_recorded_economics": nonneg,
            "why_the_union": ("the top-N alone would price only the negative-expectancy "
                              "suppliers and the non-negative screen alone would price only "
                              "the quiet ones; the trade-off is the deliverable, so both "
                              "arms of it are priced"),
        }
        print(f"\nprice ({len(short)} = top {len(top)} by marginal fills U "
              f"{len(nonneg)} non-negative on RECORDED):", flush=True)
        doc["price"] = price(pool, short, paths=args.paths)

    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
