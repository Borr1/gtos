"""Session AB, deliverable 2: restate the out-of-window economics on the surface that existed.

    python3 docs/audits/fable5-vision-audit-20260725/phase6/receipts/ab_restate.py

WHAT IS WRONG WITH THE NUMBER BEING RESTATED
---------------------------------------------
`SESSION_V_ARMED_SET_MC_RESULT.md` section 7 prices the armed four at **-0.220 %/month**
over 2015-2019 and **+0.100 %/month** pre-2025. Both are computed on `load_book_rows()`,
the W7 validation streams, whose per-sleeve coverage is (measured, this session):

    crypto        2024-2026   (104 rows)      energy_agri   2021-2026  (162 rows)
    metals_core   2015-2026   (131 rows)      sub_xvol      2016-2026   (90 rows)

So the 2015-2019 cell is a **two-sleeve** book with `crypto` and `energy_agri` contributing
structurally nothing, and the pre-2025 cell is a four-sleeve book for one of its ten years.
Averaging those zeros into a monthly rate mixes *"the edge failed"* with *"the sleeve was
not there"*.

Two of those absences are the data's, not the sleeves'. Regenerating from the bar archive
moves `crypto` back to 2017 (BTCUSD's first bar) and `metals_core` back to 2005. The third
is real and unrepairable from this machine: **FTMO holds no oil bars before 2020-12-28**,
so `energy_agri` cannot be measured before 2021 at any price.

WHAT THIS DRIVER PRODUCES
--------------------------
The same four-window table, four ways, so the reader can see exactly what each correction
is worth:

  1. `as_measured`         every armed sleeve, every era — the direct analogue of V's table
                           on the regenerated stream
  2. `surface_conditioned` each era restricted to the sleeves that HAD a surface in it, and
                           each sleeve's own days only
  3. `strict_panel`        the two symbols present throughout (XAUUSD, XAGUSD) — the
                           composition control
  4. `per_sleeve`          each sleeve on its own available era, alone

CONVENTIONS, STATED SO THE COMPARISON IS HONEST
------------------------------------------------
The combination arithmetic is V's own: `armed_set_mc.comb_from` with `mc_firm_rules`'
half-Kelly bins and `DIAL`, so `monthly_pct = mean_R_per_book_day x dial x book_days/month
x 100` is computed by the same functions. The COST layer is not V's: this stream is
regenerated, so it is priced by `src.costs.cost_r` through `walkforward.panel.price_trades`
(the wave-5/6 broker-truth authority the estate walk uses) rather than by
`recost_w7_validation`'s per-row cost columns, which only exist for the cached rows. Levels
are therefore not bit-comparable to V's table; **era-to-era ratios inside this table are**,
and that is what the restatement turns on.

`R` is winsorised by `admission.winsorize_R`, matching the production labeler.
"""

from __future__ import annotations

import collections
import datetime as dt
import json
import os
import pickle
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
# `scripts/research/` is a regular package and shadows the repo-root `research` namespace
# package the moment `scripts/` is searchable. Pin the repo-root one first. (Session V's
# A/B measured the alternative as 6 unexplained regressions.)
_sp = sys.path[:]
try:
    sys.path[:] = [str(REPO)]
    import research.operations  # noqa: E402,F401
finally:
    sys.path[:] = _sp
sys.path.insert(0, str(REPO / "scripts"))

import mc_firm_rules as Q  # noqa: E402
import recost_w7_validation as M  # noqa: E402

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.primitives import simulate_detail  # noqa: E402
from src.research_infra.regime_spine import conditions as C  # noqa: E402
from src.research_infra.regime_spine import ramp as R_  # noqa: E402
from src.research_infra.regime_spine.archive import ARCHIVE, frames_for  # noqa: E402
from src.research_infra.regime_spine.trials import TrialLedger  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.costs import cost_r as _cost_r  # noqa: E402
from src.costs import load_broker_true_costs as _load_costs  # noqa: E402
from src.research_infra.walkforward.panel import TradeRecord, price_trades  # noqa: E402

import armed_set_mc as V  # noqa: E402  (imports Q/M; must follow them)

HERE = Path(__file__).resolve().parent
OUT = HERE / "AB_OUT_OF_WINDOW_RESTATED_V1.json"
LEDGER = HERE / "AB_TRIAL_LEDGER.jsonl"
FRAME_CACHE = os.environ.get("AB_FRAME_CACHE", "")

ARMED = list(C.ARMED_FOUR)
MAXBARS = 80          # H4 x 80 = 320 h = SURVIVOR_BOOK_V1's structural horizon
SPEC = OPTIONS["B_balanced"]
_TRUTH = _load_costs()

ERAS = {
    "2015_2019": (2015, 2019),
    "pre_2025": (2000, 2024),
    "selection_window_2025plus": (2025, 2100),
    "all": (2000, 2100),
}


def build_frames() -> dict:
    want = sorted({s for n in ARMED for s in C.SLEEVES[n].surface})
    cache: dict = {}
    if FRAME_CACHE and Path(FRAME_CACHE).is_file():
        cache = pickle.load(open(FRAME_CACHE, "rb"))
    fr = frames_for(want, 16388, cache=cache)
    if FRAME_CACHE:
        with open(FRAME_CACHE, "wb") as fh:
            pickle.dump(cache, fh)
    return fr


def label(frames: dict) -> tuple[list[TradeRecord], dict]:
    """Regenerate every armed sleeve's trades from bars, through the sanctioned labeler."""
    recs: list[TradeRecord] = []
    meta: dict = {}
    ivl = dt.timedelta(hours=4)
    for name in ARMED:
        cond = C.SLEEVES[name]
        n = 0
        for canon in cond.surface:
            f = frames.get(canon)
            if f is None:
                continue
            for i, intent in C.fires(f, cond):
                if i + 2 >= len(f):
                    continue
                r, xi = simulate_detail(
                    f.bars, i, intent["direction"], stop_dist=intent["stop_dist"],
                    target_dist=intent["target_dist"], maxbars=MAXBARS, cost=0.0)
                recs.append(TradeRecord(
                    sleeve=name, symbol=f.symbol,
                    entry_utc=f.times_utc[i] + ivl, exit_utc=f.times_utc[xi] + ivl,
                    direction=int(intent["direction"]),
                    sl_distance_price=float(intent["stop_dist"]),
                    entry_price=float(f.bars[i].c), r_gross=float(winsorize_R(r)),
                    features={"decision_day": (f.times_utc[i] + ivl).strftime("%Y-%m-%d"),
                              "symbol_canonical": canon,
                              "hold_hours": round((xi - i) * 4.0, 4),
                              "stop_over_atr": (round(intent["stop_dist"] / f.atr[i], 5)
                                                if f.atr[i] > 0 else None),
                              "intra_size": float(intent.get("intra_size", 1.0))},
                ))
                n += 1
        meta[name] = n
    return recs, meta


def _v(x) -> float:
    """`CostBreakdown` terms may be plain floats or coverage-classed measures."""
    return float(getattr(x, "value", x)) if x is not None else 0.0


def price(recs: list[TradeRecord]) -> tuple[list[dict], dict]:
    priced, cov = price_trades(recs, SPEC)
    rows, drops = [], collections.Counter()
    for p in priced:
        if p.status != "priced" or p.r_net is None:
            drops[f"{p.trade.sleeve}:{p.status}"] += 1
            continue
        t = p.trade
        # `PricedTrade.cost_r` is the scalar total; the per-term split needs the
        # breakdown, so ask the cost layer for it directly. Same inputs, same call
        # `price_trades` made — asserted below by requiring the totals to agree.
        b = _cost_r(t.symbol, SPEC.account, t.holding_hours,
                    sl_distance_price=t.sl_distance_price, entry_price=t.entry_price,
                    side=t.side, entry_utc=t.entry_utc, costs=_TRUTH)
        if abs(_v(b.total_r) - float(p.cost_r)) > 1e-9:
            raise AssertionError(
                f"cost breakdown disagrees with price_trades for {t.sleeve}/{t.symbol}: "
                f"{_v(b.total_r)} vs {p.cost_r}")
        rows.append({
            "sleeve": t.sleeve, "symbol": t.symbol,
            "symbol_canonical": t.features["symbol_canonical"],
            "date": t.features["decision_day"], "year": t.entry_utc.year,
            "R": float(p.r_net), "R_gross": float(t.r_gross),
            "hold_hours": t.features["hold_hours"],
            "stop_over_atr": t.features.get("stop_over_atr"),
            "cost_total_r": _v(getattr(b, "total_r", None)),
            "cost_spread_r": _v(getattr(b, "spread_r", None)),
            "cost_commission_r": _v(getattr(b, "commission_r", None)),
            "cost_slippage_r": _v(getattr(b, "slippage_r", None)),
            "cost_swap_r": _v(getattr(b, "swap_r", None)),
        })
    return rows, {"drops": dict(drops),
                  "coverage": {k: round(v.coverage_frac, 4) for k, v in cov.items()}}


def cost_profile(rows: list[dict], sleeve: str) -> dict:
    """Where a sleeve's cost goes — the difference between a verdict and a prescription.

    `FOURTH_REVIEW.md` section 2.2: *expectancy fails with gross > 0* prescribes a
    **cost-geometry repair**, and which term dominates says which repair. A swap-dominated
    sleeve wants an exit rule; a spread-dominated one wants a wider stop, because every
    cost here is a price drag divided by the stop and so scales as 1/stop.
    """
    sub = [r for r in rows if r["sleeve"] == sleeve]
    if not sub:
        return {}
    n = len(sub)
    terms = {k: round(statistics.fmean([r[f"cost_{k}_r"] for r in sub]), 5)
             for k in ("spread", "commission", "slippage", "swap")}
    tot = round(statistics.fmean([r["cost_total_r"] for r in sub]), 5)
    gross = round(statistics.fmean([r["R_gross"] for r in sub]), 5)
    soa = [r["stop_over_atr"] for r in sub if r["stop_over_atr"] is not None]
    return {
        "n": n,
        "mean_r_gross": gross,
        "mean_cost_r": tot,
        "mean_r_net": round(gross - tot, 5),
        "cost_terms_r": terms,
        "dominant_cost_term": max(terms, key=lambda k: terms[k]),
        "cost_share_of_gross": (round(tot / gross, 4) if gross else None),
        "mean_hold_hours": round(statistics.fmean([r["hold_hours"] for r in sub]), 2),
        "median_hold_hours": round(statistics.median([r["hold_hours"] for r in sub]), 2),
        "stop_over_atr": ({"median": round(statistics.median(soa), 4),
                           "p10": round(sorted(soa)[int(0.10 * (len(soa) - 1))], 4),
                           "p90": round(sorted(soa)[int(0.90 * (len(soa) - 1))], 4)}
                          if soa else None),
        "prescription": _prescribe(gross, tot, terms),
    }


def _prescribe(gross: float, tot: float, terms: dict) -> str:
    if gross <= 0:
        return ("gross is non-positive: this is not a cost-geometry case. Diagnose entry "
                "or regime conditioning before touching cost.")
    if gross - tot > 0:
        return "net-positive at the measured carry; no cost repair required."
    dom = max(terms, key=lambda k: terms[k])
    if dom in ("spread", "slippage", "commission"):
        return (f"gross {gross:+.4f} > 0 and cost is {dom}-dominated. Cost in R is a price "
                f"drag divided by the stop, so a stop-width sweep moves it as 1/stop while "
                f"the R-geometry moves with the path. Sweep it (ab_neighborhood.py) — do "
                f"not read the negative net as an absent edge.")
    return (f"gross {gross:+.4f} > 0 and cost is swap-dominated. This is the exit-repair "
            f"lane (FOURTH_REVIEW section 5.3): swap-aware exit, time-stop surface, "
            f"pre-rollover flat.")


def book_series(rows: list[dict], sleeves: list[str]) -> tuple[list[str], list[float]]:
    """V's own combination arithmetic on a day x sleeve matrix of raw day-mean R.

    `comb_from` applies `BOOK_CONF` and the half-Kelly `n_active` bin, exactly as
    `armed_set_mc` does for its "live" convention.
    """
    per: dict[str, dict[str, list[float]]] = {s: collections.defaultdict(list)
                                              for s in sleeves}
    for r in rows:
        if r["sleeve"] in per:
            per[r["sleeve"]][r["date"]].append(r["R"])
    days = sorted({d for s in sleeves for d in per[s]})
    raw = [[statistics.fmean(per[s][d]) if per[s].get(d) else 0.0 for s in sleeves]
           for d in days]
    return days, V.comb_from(raw, sleeves, Q.KELLY_HALF)


def price_window(rows: list[dict], sleeves: list[str], lo: int, hi: int, *,
                 clip_start: dt.date | None = None) -> dict | None:
    sel = [r for r in rows if lo <= r["year"] <= hi
           and (clip_start is None or dt.date.fromisoformat(r["date"]) >= clip_start)]
    if not sel or not sleeves:
        return None
    days, comb = book_series(sel, sleeves)
    if not days:
        return None
    d0, d1 = dt.date.fromisoformat(days[0]), dt.date.fromisoformat(days[-1])
    # ERA bounds, not observed bounds: a quiet era must not shrink its own denominator.
    elo = max(dt.date(max(lo, 2000), 1, 1), clip_start or dt.date(1900, 1, 1))
    ehi = min(dt.date(min(hi, 2026), 12, 31), dt.date(2026, 7, 26))
    months = (ehi.year - elo.year) * 12 + (ehi.month - elo.month) + 1
    bdpm = len(days) / months if months else 0.0
    mean_r = statistics.fmean(comb)
    sess = R_.weekday_sessions(elo, ehi)
    return {
        "sleeves": list(sleeves), "n_trades": len(sel), "book_days": len(days),
        "era_first": elo.isoformat(), "era_last": ehi.isoformat(),
        "first_book_day": days[0], "last_book_day": days[-1],
        "calendar_months": months, "weekday_sessions": sess,
        "density_pct": round(100 * len(days) / sess, 3) if sess else None,
        "book_days_per_calendar_month": round(bdpm, 3),
        "mean_r_per_book_day": round(mean_r, 5),
        "total_r": round(sum(comb), 3),
        "worst_day_pct_of_equity": round(100 * min(comb) * Q.DIAL, 4),
        "monthly_pct_calendar_live_dial": round(mean_r * Q.DIAL * bdpm * 100, 4),
        "convention": ("comb_from(raw, sleeves, KELLY_HALF) x DIAL; "
                       f"DIAL={Q.DIAL}; cost = src.costs.cost_r via GateSpec "
                       f"{SPEC.spec_id}"),
    }


def main() -> dict:
    t0 = time.time()
    frames = build_frames()
    recs, gen = label(frames)
    rows, cost_meta = price(recs)
    print(f"generated {len(recs)} trades {gen}; priced {len(rows)}; "
          f"drops {cost_meta['drops']}", flush=True)
    print("coverage:", cost_meta["coverage"], flush=True)

    led = TrialLedger(LEDGER, session="AB", append=True)

    # when each sleeve's surface opens (first evaluable bar anywhere on its surface)
    opens: dict[str, dt.date] = {}
    for name in ARMED:
        cond = C.SLEEVES[name]
        fs = [frames[c].times_utc[cond.warmup_bars - 1].date()
              for c in cond.surface
              if c in frames and len(frames[c]) >= cond.warmup_bars]
        if fs:
            opens[name] = min(fs)

    out: dict = {
        "schema": "gtos.wave6.regime_spine.out_of_window_restated.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "bars_archive": ARCHIVE,
        "gate_spec": SPEC.spec_id,
        "maxbars": MAXBARS,
        "n_trades_generated": gen,
        "cost": cost_meta,
        "sleeve_surface_open": {k: v.isoformat() for k, v in sorted(opens.items())},
        "validation_cache_coverage": {},
    }

    # what the cache V measured actually contained, so the restatement names its target
    cache_rows = M.load_book_rows()
    for name in ARMED:
        ys = sorted({str(r["date"])[:4] for r in cache_rows if r["sleeve"] == name})
        out["validation_cache_coverage"][name] = {
            "n_rows": sum(1 for r in cache_rows if r["sleeve"] == name),
            "first_year": ys[0] if ys else None, "last_year": ys[-1] if ys else None,
        }

    tables: dict = {}

    # 1. as measured — every armed sleeve, every era
    tables["as_measured"] = {lab: price_window(rows, ARMED, lo, hi)
                             for lab, (lo, hi) in ERAS.items()}

    # 2. surface-conditioned — only the sleeves that had a surface, clipped to when the
    #    book itself opened
    sc = {}
    for lab, (lo, hi) in ERAS.items():
        ehi = min(dt.date(min(hi, 2026), 12, 31), dt.date(2026, 7, 26))
        have = [s for s in ARMED if s in opens and opens[s] <= ehi]
        clip = min((opens[s] for s in have), default=None)
        node = price_window(rows, have, lo, hi, clip_start=clip)
        if node is not None:
            node["sleeves_absent_in_era"] = [s for s in ARMED if s not in have]
            node["clip_start"] = clip.isoformat() if clip else None
        sc[lab] = node
    tables["surface_conditioned"] = sc

    # 3. strict panel — the composition control
    panel = {"XAUUSD", "XAGUSD"}
    prows = [r for r in rows if r["symbol_canonical"] in panel]
    psleeves = sorted({r["sleeve"] for r in prows})
    tables["strict_panel_xau_xag"] = {
        lab: price_window(prows, psleeves, lo, hi) for lab, (lo, hi) in ERAS.items()}

    # 3b. THE LIKE-FOR-LIKE CELL — the same four-sleeve book, inside and outside the
    #     window that selected it, over the era in which all four actually existed.
    #     Every other row of every other table compares books of different sizes; this one
    #     does not, and it is the only cell that isolates the residual question.
    all_four_open = max(opens.values()) if len(opens) == len(ARMED) else None
    lfl = {}
    if all_four_open is not None:
        for lab, lo, hi in (("out_of_selection_window", 2021, 2024),
                            ("selection_window", 2025, 2100),
                            ("both", 2021, 2100)):
            lfl[lab] = price_window(rows, ARMED, lo, hi, clip_start=all_four_open)
        canary = ["metals_core", "crypto", "energy_agri"]
        lfl["canary_three_config_runnable"] = {
            lab: price_window(rows, canary, lo, hi, clip_start=all_four_open)
            for lab, lo, hi in (("out_of_selection_window", 2021, 2024),
                                ("selection_window", 2025, 2100),
                                ("both", 2021, 2100))}
        a, b = lfl["out_of_selection_window"], lfl["selection_window"]
        if a and b:
            lfl["_reading"] = {
                "all_four_open_from": all_four_open.isoformat(),
                "book_days_per_month_ratio": round(
                    b["book_days_per_calendar_month"] / a["book_days_per_calendar_month"], 4),
                "r_per_book_day_ratio": (round(b["mean_r_per_book_day"]
                                               / a["mean_r_per_book_day"], 3)
                                         if a["mean_r_per_book_day"] else None),
                "why": ("SESSION_V §7 attributes the 26x selection-window multiple to BOTH "
                        "terms — 'the edge per book-day is 5.3x higher and the firing "
                        "frequency is 7.1x higher'. Held to one book over the era that "
                        "book existed, the FREQUENCY term is flat and only the per-day "
                        "edge moves. V's frequency term was the surface arriving, not the "
                        "market speeding up."),
            }
    tables["like_for_like_all_four_open"] = lfl

    # 4. per sleeve, alone, on its own available era
    ps = {}
    for name in ARMED:
        srows = [r for r in rows if r["sleeve"] == name]
        node = {}
        for lab, (lo, hi) in ERAS.items():
            node[lab] = price_window(srows, [name], lo, hi,
                                     clip_start=opens.get(name))
        node["own_era_only"] = price_window(srows, [name], 2000, 2100,
                                            clip_start=opens.get(name))
        by_year = collections.Counter(r["year"] for r in srows)
        node["trades_by_year"] = dict(sorted(by_year.items()))
        node["mean_r_net_per_trade"] = (round(statistics.fmean([r["R"] for r in srows]), 5)
                                        if srows else None)
        node["mean_r_gross_per_trade"] = (
            round(statistics.fmean([r["R_gross"] for r in srows]), 5) if srows else None)
        node["median_hold_hours"] = (round(statistics.median(
            [r["hold_hours"] for r in srows]), 3) if srows else None)
        ps[name] = node
        led.log("restatement", name, "regenerated_stream_own_era",
                {"maxbars": MAXBARS, "gate_spec": SPEC.spec_id},
                {"n": len(srows), "mean_r_net_per_trade": node["mean_r_net_per_trade"]},
                note="one configuration per sleeve; nothing selected on")
    tables["per_sleeve"] = ps

    out["cost_profile"] = {s: cost_profile(rows, s) for s in ARMED}
    out["tables"] = tables
    out["n_trials_logged"] = led.n_trials
    led.write_summary(HERE / "AB_TRIAL_BUDGET_RESULT.json")
    led.close()

    # ---- print ----------------------------------------------------------------------
    def show(title: str, tab: dict) -> None:
        print(f"\n=== {title}")
        print(f"  {'window':28s} {'sleeves':>7s} {'trades':>7s} {'bd':>5s} {'bd/mo':>7s} "
              f"{'dens%':>7s} {'R/bd':>9s} {'%/mo':>8s}")
        for lab in ERAS:
            v = tab.get(lab)
            if not v:
                print(f"  {lab:28s} {'-':>7s}")
                continue
            print(f"  {lab:28s} {len(v['sleeves']):7d} {v['n_trades']:7d} "
                  f"{v['book_days']:5d} {v['book_days_per_calendar_month']:7.3f} "
                  f"{v['density_pct'] if v['density_pct'] is not None else 0:7.3f} "
                  f"{v['mean_r_per_book_day']:9.5f} "
                  f"{v['monthly_pct_calendar_live_dial']:8.3f}")

    print("\n=== cost geometry — where each sleeve's cost goes")
    print(f"  {'sleeve':20s} {'n':>4s} {'gross':>8s} {'cost':>7s} {'net':>8s} "
          f"{'spread':>7s} {'swap':>7s} {'comm':>6s} {'slip':>6s} {'stop/ATR':>9s} dom")
    for s_ in ARMED:
        c = out["cost_profile"][s_]
        if not c:
            continue
        so = c["stop_over_atr"]["median"] if c["stop_over_atr"] else float("nan")
        t = c["cost_terms_r"]
        print(f"  {s_:20s} {c['n']:4d} {c['mean_r_gross']:+8.4f} {c['mean_cost_r']:7.4f} "
              f"{c['mean_r_net']:+8.4f} {t['spread']:7.4f} {t['swap']:7.4f} "
              f"{t['commission']:6.4f} {t['slippage']:6.4f} {so:9.3f} "
              f"{c['dominant_cost_term']}")
        print(f"      -> {c['prescription']}")

    show("1. as measured (all four armed sleeves, all eras)", tables["as_measured"])
    show("2. surface-conditioned (only sleeves that existed)",
         tables["surface_conditioned"])
    show("3. strict panel XAUUSD+XAGUSD", tables["strict_panel_xau_xag"])

    lfl = tables["like_for_like_all_four_open"]
    if lfl.get("_reading"):
        print(f"\n=== 3b. LIKE FOR LIKE — the same four-sleeve book, from "
              f"{lfl['_reading']['all_four_open_from']} (all four have a surface)")
        print(f"  {'window':28s} {'trades':>7s} {'bd':>5s} {'bd/mo':>7s} {'dens%':>7s} "
              f"{'R/bd':>9s} {'%/mo':>8s}")
        for lab in ("out_of_selection_window", "selection_window", "both"):
            v = lfl.get(lab)
            if not v:
                continue
            print(f"  {lab:28s} {v['n_trades']:7d} {v['book_days']:5d} "
                  f"{v['book_days_per_calendar_month']:7.3f} {v['density_pct']:7.3f} "
                  f"{v['mean_r_per_book_day']:9.5f} "
                  f"{v['monthly_pct_calendar_live_dial']:8.3f}")
        r = lfl["_reading"]
        print(f"  -> book-days/month ratio {r['book_days_per_month_ratio']}x, "
              f"R per book-day ratio {r['r_per_book_day_ratio']}x")
    for name in ARMED:
        print(f"\n=== 4. {name} alone (surface opens {opens.get(name)})")
        print(f"  by year: {ps[name]['trades_by_year']}")
        print(f"  mean R net/trade {ps[name]['mean_r_net_per_trade']}, "
              f"gross {ps[name]['mean_r_gross_per_trade']}, "
              f"median hold {ps[name]['median_hold_hours']} h")
        show(f"   {name}", {k: v for k, v in ps[name].items() if k in ERAS})

    OUT.write_text(json.dumps(out, indent=1, sort_keys=True, default=str) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)} in {time.time()-t0:.1f}s")
    return out


if __name__ == "__main__":
    main()
