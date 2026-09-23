"""Session AB, deliverable 1: attribute the armed book's frequency ramp.

    python3 docs/audits/fable5-vision-audit-20260725/phase6/receipts/ab_ramp.py

THE CLAIM BEING ATTACKED
-------------------------
`SESSION_V_ARMED_SET_MC_RESULT.md` section 7 prices the armed four at **+0.100 %/month**
pre-2025 and **-0.220 %/month** over 2015-2019, against **+2.617 %/month** inside the
window that selected them, and records that the book's density of weekday sessions runs
**0.4 % (2015) to 28.7 % (2025)**. Every reading of that table so far has treated it as
evidence about the *rules*. It is at least partly evidence about the *data*, and nobody
had separated the two.

This driver separates them, three ways, over the whole H4 archive:

  1. **Surface availability** — when each sleeve's symbols first exist and first clear
     the live warmup floor. A sleeve cannot fire before that date, so any monthly rate
     attributed to it before then is measuring its absence.
  2. **The funnel** — per year, per sleeve: evaluable (symbol, bar) slots, then each
     production gate's conditional and marginal pass rate, then fires. The product is
     exact, so the log ramp decomposes with no residual.
  3. **Threshold drift** — for every gate that is a fixed cut on a continuous statistic,
     where that cut sits in each year's own distribution of the statistic. A cut whose
     percentile rank slides is cause (b) and `ab_normalize.py` repairs it; a cut whose
     rank holds while the fire rate moves is cause (c) and the deliverable is a named
     regime variable.

WHAT IS AND IS NOT A TRIAL HERE
--------------------------------
Nothing in this driver is a trial: it evaluates one configuration — the production
defaults — and selects nothing. The ledger row it writes records that, so the count is
auditable rather than merely absent.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import pickle
import sys
import time
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.research_infra.regime_spine import conditions as C  # noqa: E402
from src.research_infra.regime_spine import ramp as R  # noqa: E402
from src.research_infra.regime_spine.archive import (  # noqa: E402
    ARCHIVE,
    frames_for,
    surface_availability,
)
from src.research_infra.regime_spine.trials import TrialLedger  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "AB_RAMP_ATTRIBUTION_V1.json"
LEDGER = HERE / "AB_TRIAL_LEDGER.jsonl"
FRAME_CACHE = os.environ.get("AB_FRAME_CACHE", "")

SLEEVES = ("metals_core", "crypto", "energy_agri", "sub_xvol_pullback",
           "metals_softband")

#: V's four windows, as period-key lists.
ERAS = {
    "2015_2019": [str(y) for y in range(2015, 2020)],
    "pre_2025": [str(y) for y in range(2000, 2025)],
    "selection_window_2025plus": [str(y) for y in range(2025, 2027)],
    "all": [str(y) for y in range(2000, 2027)],
}


def build_frames() -> dict:
    want = sorted({s for n in SLEEVES for s in C.SLEEVES[n].surface})
    cache: dict = {}
    if FRAME_CACHE and Path(FRAME_CACHE).is_file():
        cache = pickle.load(open(FRAME_CACHE, "rb"))
    fr = frames_for(want, 16388, cache=cache)
    if FRAME_CACHE:
        with open(FRAME_CACHE, "wb") as fh:
            pickle.dump(cache, fh)
    return fr


def main() -> dict:
    t0 = time.time()
    frames = build_frames()
    print(f"frames: {len(frames)} symbols in {time.time()-t0:.1f}s", flush=True)

    led = TrialLedger(LEDGER, session="AB")

    out: dict = {
        "schema": "gtos.wave6.regime_spine.ramp_attribution.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "bars_archive": ARCHIVE,
        "gate_chains": C.describe(),
        "sleeves": {},
    }

    for name in SLEEVES:
        cond = C.SLEEVES[name]
        print(f"\n=== {name} ===", flush=True)

        avail = surface_availability(cond.surface, cond.timeframe,
                                     warmup_bars=cond.warmup_bars)
        present = [s for s, v in avail.items() if v.get("in_archive")]
        absent = [s for s, v in avail.items() if not v.get("in_archive")]
        first_eval = [v["first_evaluable_utc"] for v in avail.values()
                      if v.get("first_evaluable_utc")]
        sleeve_open = min(first_eval) if first_eval else None
        full_surface = max(first_eval) if first_eval and not absent else None
        print(f"  surface {len(present)}/{len(cond.surface)} in archive; "
              f"absent={absent}")
        print(f"  first evaluable bar anywhere: {sleeve_open}")

        fun = R.funnel_by_period(frames, cond, grain="year")
        years = sorted(fun)
        print(f"  {'year':6s} {'slots':>8s} {'syms':>5s} {'fires':>6s} {'per 1k':>8s}  gates")
        for y in years:
            f = fun[y]
            rates = f.rates(cond.gate_names())
            gs = " ".join(f"{g[:9]}={rates[g]:.3f}" if rates[g] is not None else f"{g[:9]}=-"
                          for g in cond.gate_names())
            print(f"  {y:6s} {f.slots:8d} {len(f.symbols):5d} {f.fires:6d} "
                  f"{1000*f.fires/f.slots if f.slots else 0:8.3f}  {gs}")

        decs = {}
        panels = {}
        for a, b in (("2015_2019", "selection_window_2025plus"),
                     ("pre_2025", "selection_window_2025plus")):
            decs[f"{a}__vs__{b}"] = R.decompose(fun, cond, ERAS[a], ERAS[b])
            # THE COMPOSITION CONTROL. The surface grows from 1-3 symbols to 13 in 2021,
            # so an unrestricted rate change confounds "the gate moved" with "the gate is
            # now being asked about indices instead of gold". Redo it on the symbols
            # present in BOTH eras and report the two side by side.
            panel = R.strict_panel(frames, cond, ERAS[a], ERAS[b])
            if panel:
                pf = R.funnel_by_period(frames, cond, grain="year", symbols=panel)
                panels[f"{a}__vs__{b}"] = {
                    "panel": panel,
                    **R.decompose(pf, cond, ERAS[a], ERAS[b]),
                }
                pd_ = panels[f"{a}__vs__{b}"]
                print(f"  fixed panel {panel}: fires {pd_['era_a']['fires']} -> "
                      f"{pd_['era_b']['fires']}, log_ratio="
                      f"{pd_['log_fire_ratio']}")

        pct = R.threshold_percentile_ranks(frames, cond, grain="year")
        panel_all = R.strict_panel(frames, cond, ERAS["2015_2019"],
                                   ERAS["selection_window_2025plus"])
        pct_panel = (R.threshold_percentile_ranks(frames, cond, grain="year",
                                                  symbols=panel_all)
                     if panel_all else {})
        mtf = (R.mtf_decomposition(frames, cond, grain="year")
               if any(g.name == "mtf_conflict" for g in cond.gates) else None)
        mtf_panel = (R.mtf_decomposition(frames, cond, grain="year", symbols=panel_all)
                     if (mtf and panel_all) else None)

        out["sleeves"][name] = {
            "common_panel_2015_2019_vs_2025plus": panel_all,
            "decompositions_fixed_panel": panels,
            "threshold_percentile_ranks_fixed_panel": pct_panel,
            "mtf_decomposition": mtf,
            "mtf_decomposition_fixed_panel": mtf_panel,
            "surface_availability": avail,
            "n_symbols_in_archive": len(present),
            "n_symbols_absent": len(absent),
            "symbols_absent": absent,
            "first_evaluable_utc_any_symbol": sleeve_open,
            "first_evaluable_utc_full_surface": full_surface,
            "funnel_by_year": {y: fun[y].to_json(cond.gate_names()) for y in years},
            "decompositions": decs,
            "threshold_percentile_ranks": pct,
        }
        led.log("ramp_attribution", name, "production_defaults", dict(cond.defaults),
                {"fires_total": sum(fun[y].fires for y in years),
                 "eval_slots_total": sum(fun[y].slots for y in years)},
                note="single configuration, nothing selected on — logged for auditability")

    # -----------------------------------------------------------------------------
    # the book-level restatement of V's density number
    # -----------------------------------------------------------------------------
    print("\n=== armed-four book density, and what it is measured on ===", flush=True)
    armed = [s for s in C.ARMED_FOUR]
    fires_by_day: dict[str, set[str]] = defaultdict(set)
    open_of: dict[str, dt.date] = {}
    for name in armed:
        cond = C.SLEEVES[name]
        firsts = []
        for canon in cond.surface:
            f = frames.get(canon)
            if f is None or len(f) < cond.warmup_bars:
                continue
            firsts.append(f.times_utc[cond.warmup_bars - 1].date())
            for i, _ in C.fires(f, cond):
                fires_by_day[f.times_utc[i].date().isoformat()].add(name)
        if firsts:
            open_of[name] = min(firsts)

    book_open = min(open_of.values()) if open_of else None
    all_open = max(open_of.values()) if len(open_of) == len(armed) else None
    days = sorted(fires_by_day)
    density = {}
    for lab, yrs in ERAS.items():
        sel = [d for d in days if d[:4] in yrs]
        if not sel:
            continue
        lo, hi = dt.date.fromisoformat(sel[0]), dt.date.fromisoformat(sel[-1])
        # era bounds, not observed bounds — a silent era must not shrink its own denominator
        y0, y1 = int(min(yrs)), int(max(yrs))
        elo = max(dt.date(y0, 1, 1), book_open or dt.date(y0, 1, 1))
        ehi = min(dt.date(y1, 12, 31), dt.date(2026, 7, 26))
        sess = R.weekday_sessions(elo, ehi)
        months = (ehi.year - elo.year) * 12 + (ehi.month - elo.month) + 1
        n_sleeves_open = sum(1 for s, d in open_of.items() if d <= ehi)
        density[lab] = {
            "book_days": len(sel),
            "era_first_day": elo.isoformat(), "era_last_day": ehi.isoformat(),
            "weekday_sessions": sess,
            "density_pct": round(100 * len(sel) / sess, 3) if sess else None,
            "book_days_per_calendar_month": round(len(sel) / months, 3) if months else None,
            "sleeves_with_surface_in_era": n_sleeves_open,
            "sleeves_with_surface": sorted(s for s, d in open_of.items() if d <= ehi),
            "sleeves_structurally_absent": sorted(s for s in armed
                                                  if s not in open_of or open_of[s] > ehi),
            "first_day_observed": sel[0], "last_day_observed": sel[-1],
        }
        print(f"  {lab:26s} book_days={len(sel):4d} density={density[lab]['density_pct']:6.3f}% "
              f"bd/mo={density[lab]['book_days_per_calendar_month']:6.3f} "
              f"sleeves_with_surface={n_sleeves_open}/4 "
              f"absent={density[lab]['sleeves_structurally_absent']}")

    per_year = {}
    for y in range(2000, 2027):
        sel = [d for d in days if d[:4] == str(y)]
        lo = max(dt.date(y, 1, 1), book_open or dt.date(y, 1, 1))
        hi = min(dt.date(y, 12, 31), dt.date(2026, 7, 26))
        if hi < lo:
            continue
        sess = R.weekday_sessions(lo, hi)
        n_open = sum(1 for s, d in open_of.items() if d <= hi)
        per_year[str(y)] = {
            "book_days": len(sel), "weekday_sessions": sess,
            "density_pct": round(100 * len(sel) / sess, 3) if sess else None,
            "sleeves_with_surface": n_open,
            "density_pct_per_open_sleeve": (round(100 * len(sel) / sess / n_open, 3)
                                            if sess and n_open else None),
        }

    out["armed_four_density"] = {
        "sleeve_surface_open_utc": {k: v.isoformat() for k, v in sorted(open_of.items())},
        "book_first_evaluable": book_open.isoformat() if book_open else None,
        "all_four_have_surface_from": all_open.isoformat() if all_open else None,
        "by_era": density,
        "by_year": per_year,
        "note": ("Book-day = a calendar day on which at least one armed sleeve's rule "
                 "fired anywhere on its surface, regenerated from bars. Denominator is "
                 "the era's weekday sessions, clipped at the first date ANY armed sleeve "
                 "had an evaluable bar."),
    }

    print("\n  density by year (armed four):")
    print(f"  {'year':6s} {'bd':>4s} {'sess':>5s} {'dens%':>7s} {'open':>5s} {'dens/open%':>10s}")
    for y, v in sorted(per_year.items()):
        print(f"  {y:6s} {v['book_days']:4d} {v['weekday_sessions']:5d} "
              f"{v['density_pct']:7.3f} {v['sleeves_with_surface']:5d} "
              f"{v['density_pct_per_open_sleeve'] if v['density_pct_per_open_sleeve'] is not None else 0:10.3f}")

    out["n_trials_logged"] = led.n_trials
    led.write_summary(HERE / "AB_TRIAL_BUDGET_RESULT.json")
    led.close()

    OUT.write_text(json.dumps(out, indent=1, sort_keys=True, default=str) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e6:.2f} MB) "
          f"in {time.time()-t0:.1f}s")
    return out


if __name__ == "__main__":
    main()
