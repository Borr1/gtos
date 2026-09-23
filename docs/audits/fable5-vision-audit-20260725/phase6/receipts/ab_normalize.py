"""Session AB, deliverable 4: the scale-free normalization, refit pre-2024, validate 2024+.

    python3 docs/audits/fable5-vision-audit-20260725/phase6/receipts/ab_normalize.py

WHAT IS BEING REPAIRED, AND FOR WHICH SLEEVE
----------------------------------------------
`ab_ramp.py` measured the (b) case precisely once in the armed book: on the fixed
XAUUSD+XAGUSD panel, `sub_xvol_pullback`'s `vr >= 1.6` gate goes from a **0.0194** marginal
pass rate in 2015-2019 to **0.0490** in 2025+, with no symbol-mix change available to
explain it. `metals_core`'s `vr >= 1.2` moves the same direction (0.1407 -> 0.2105) and its
`ac60 >= 0.10` moves the other way (0.2177 -> 0.1538).

Each of those is a fixed level on a statistic whose own distribution moved. The scale-free
form fires on the statistic's **trailing percentile within its own symbol**, so the pass
rate is a constant of the rule instead of a property of the era.

THE PROTOCOL, AND WHY IT IS THE REVERSE OF THE DEFECT
-------------------------------------------------------
`p` is fitted on **pre-2024 bars only**, to match the production gate's own pre-2024 pass
rate. It is not fitted on returns. The variant is therefore a re-expression at the
production frequency, and everything the 2024+ era shows is attributable to the
re-expression rather than to a search. That is the exact inverse of
`build_survivor_book.py:60` / `KB7_growth_kelly_sizing.py:130`, which both select on
`d.year >= 2025` and then score on `d.year >= 2025`.

THE DIRECTION IS NOT ASSUMED
-----------------------------
The session brief is explicit that this can go the wrong way: *"if a scale-free threshold
makes a sleeve fire far more in 2015, its out-of-window economics may get worse, not
better. That is a real result and you should publish it as readily as the other
direction."* Both eras' economics are printed for every variant, and the ledger carries
every one.
"""

from __future__ import annotations

import json
import os
import pickle
import sys
import time
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.costs import load_broker_true_costs  # noqa: E402
from src.research_infra.regime_spine import conditions as C  # noqa: E402
from src.research_infra.regime_spine import normalize as N  # noqa: E402
from src.research_infra.regime_spine import ramp as R  # noqa: E402
from src.research_infra.regime_spine.archive import ARCHIVE, frames_for  # noqa: E402
from src.research_infra.regime_spine.sweep import evaluate  # noqa: E402
from src.research_infra.regime_spine.trials import TrialLedger  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "AB_NORMALIZATION_V1.json"
LEDGER = HERE / "AB_TRIAL_LEDGER.jsonl"
FRAME_CACHE = os.environ.get("AB_FRAME_CACHE", "")
FIT_LAST_YEAR = 2023

#: (sleeve, gate, two_sided). One row per fixed cut the ramp attribution flagged.
TARGETS = [
    ("sub_xvol_pullback", "vol_xhi", False),
    ("sub_xvol_pullback", "trend_up", False),
    ("metals_core", "vol_expansion", False),
    ("metals_core", "persistence", False),
    ("crypto", "persistence", False),
    ("energy_agri", "vol_expansion", False),
]
WINDOWS = (500, 1000, 2000)


def build_frames(sleeves) -> dict:
    want = sorted({s for n in sleeves for s in C.SLEEVES[n].surface})
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
    sleeves = sorted({s for s, _, _ in TARGETS})
    frames = build_frames(sleeves)
    truth = load_broker_true_costs()
    led = TrialLedger(LEDGER, session="AB", append=True)

    stats = sorted({next(g.stat for g in C.SLEEVES[s].gates if g.name == gname)
                    for s, gname, _ in TARGETS})
    print(f"attaching trailing ranks for {stats} at windows {WINDOWS} ...", flush=True)
    for w in WINDOWS:
        N.attach_ranks(frames, stats, window=w)
    print(f"  ranks attached in {time.time()-t0:.0f}s", flush=True)

    out: dict = {
        "schema": "gtos.wave6.regime_spine.normalization.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "bars_archive": ARCHIVE,
        "fit_last_year": FIT_LAST_YEAR,
        "windows": list(WINDOWS),
        "variants": {},
    }

    for sleeve, gname, two_sided in TARGETS:
        cond = C.SLEEVES[sleeve]
        base = evaluate(frames, cond, costs=truth, fit_last_year=FIT_LAST_YEAR)
        print(f"\n=== {sleeve} / {gname}", flush=True)
        print(f"  production      n={base['all']['n']:5d} "
              f"net={base['all']['mean_r_net']} "
              f"R/day={base['all']['mean_r_net_per_day']} | "
              f"fit n={base['fit']['n']:5d} {base['fit']['mean_r_net']} | "
              f"val n={base['validate']['n']:5d} {base['validate']['mean_r_net']}")
        node = {"production": base, "fits": {}}

        for w in WINDOWS:
            fit = N.fit_percentile(frames, cond, gname, window=w,
                                   fit_last_year=FIT_LAST_YEAR, two_sided=two_sided)
            if fit.get("fitted_p") is None:
                node["fits"][str(w)] = {"fit": fit}
                continue
            var, pname = N.percentile_variant(cond, gname, window=w,
                                              two_sided=two_sided, p=fit["fitted_p"])
            res = evaluate(frames, var, costs=truth, fit_last_year=FIT_LAST_YEAR)
            fun = R.funnel_by_period(frames, var, grain="year")
            prod_fun = R.funnel_by_period(frames, cond, grain="year")
            node["fits"][str(w)] = {
                "fit": fit,
                "param": pname,
                "result": res,
                "fires_by_year_normalized": {y: fun[y].fires for y in sorted(fun)},
                "fires_by_year_production": {y: prod_fun[y].fires for y in sorted(prod_fun)},
            }
            led.log("normalization", sleeve, f"{gname}|pct@{w}|p={fit['fitted_p']:.4f}",
                    {"gate": gname, "window": w, "p": fit["fitted_p"],
                     "two_sided": two_sided},
                    {"n": res["all"]["n"], "mean_r_net": res["all"]["mean_r_net"],
                     "fit_mean_r_net": res["fit"]["mean_r_net"],
                     "validate_mean_r_net": res["validate"]["mean_r_net"]},
                    note="p fitted to production's pre-2024 pass rate, not to returns")
            print(f"  pct@{w:<5d} p={fit['fitted_p']:.4f} "
                  f"n={res['all']['n']:5d} net={res['all']['mean_r_net']} "
                  f"R/day={res['all']['mean_r_net_per_day']} | "
                  f"fit n={res['fit']['n']:5d} {res['fit']['mean_r_net']} | "
                  f"val n={res['validate']['n']:5d} {res['validate']['mean_r_net']}")

        out["variants"][f"{sleeve}|{gname}"] = node

    # ---- the question the whole deliverable exists to answer ------------------------
    verdicts = {}
    for k, node in out["variants"].items():
        prod = node["production"]
        best = None
        for w, v in node["fits"].items():
            if "result" not in v:
                continue
            r = v["result"]
            if r["fit"]["mean_r_net"] is None:
                continue
            if best is None or r["fit"]["mean_r_net"] > best[1]:
                best = (w, r["fit"]["mean_r_net"], r)
        if best is None:
            verdicts[k] = "no evaluable normalized variant"
            continue
        w, fit_net, r = best
        pf = prod["fit"]["mean_r_net"]
        vf = prod["validate"]["mean_r_net"]
        fires = node["fits"][w]
        verdicts[k] = {
            "best_window": w,
            "fit_era_production": pf, "fit_era_normalized": fit_net,
            "validate_era_production": vf,
            "validate_era_normalized": r["validate"]["mean_r_net"],
            "n_production": prod["all"]["n"], "n_normalized": r["all"]["n"],
            "reading": _read(pf, fit_net, prod["all"]["n"], r["all"]["n"]),
            **_silence(fires.get("fires_by_year_production", {}),
                       fires.get("fires_by_year_normalized", {})),
        }
    out["verdicts"] = verdicts
    print("\n=== verdicts (fit era = pre-2024, the era the production cut was NOT chosen on)")
    for k, v in verdicts.items():
        if isinstance(v, str):
            print(f"  {k:36s} {v}")
            continue
        print(f"  {k:36s} n {v['n_production']:5d} -> {v['n_normalized']:5d}   "
              f"fit-era net {v['fit_era_production']} -> {v['fit_era_normalized']}")
        print(f"      {v['reading']}")
        if v.get("silent_years_filled_by_normalization"):
            print(f"      silent years FILLED: "
                  f"{v['silent_years_filled_by_normalization']}  "
                  f"(fires/yr CV {v['fires_per_year_cv_production']} -> "
                  f"{v['fires_per_year_cv_normalized']})")
        if v.get("years_lost_to_normalization"):
            print(f"      years lost: {v['years_lost_to_normalization']}")

    out["n_trials_logged"] = led.n_trials
    led.write_summary(HERE / "AB_TRIAL_BUDGET_RESULT.json")
    led.close()
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True, default=str) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e6:.2f} MB); "
          f"{led.n_trials} trials; {time.time()-t0:.0f}s")
    return out


def _silence(prod: dict, norm: dict) -> dict:
    """Did the scale-free cut actually un-silence anything?

    The summary metrics above are per-trade means and cannot see the thing the
    normalization exists to do: a fixed cut on a drifting statistic produces **years with
    zero fires**, and a percentile cut should fill them. `silent_years_filled` counts the
    years production never fired in that the variant does — the only direct evidence that
    the re-expression changed WHEN the sleeve trades rather than merely which bars.
    """
    if not prod or not norm:
        return {}
    years = sorted(set(prod) | set(norm))
    silent = [y for y in years if prod.get(y, 0) == 0]
    filled = [y for y in silent if norm.get(y, 0) > 0]
    lost = [y for y in years if prod.get(y, 0) > 0 and norm.get(y, 0) == 0]

    def cv(d: dict) -> Optional[float]:
        vals = [d.get(y, 0) for y in years]
        m = sum(vals) / len(vals) if vals else 0
        if not m:
            return None
        var = sum((v - m) ** 2 for v in vals) / len(vals)
        return round((var ** 0.5) / m, 4)

    return {
        "silent_years_production": silent,
        "silent_years_filled_by_normalization": filled,
        "years_lost_to_normalization": lost,
        "fires_per_year_cv_production": cv(prod),
        "fires_per_year_cv_normalized": cv(norm),
    }


def _read(prod_fit, norm_fit, n_prod, n_norm) -> str:
    if prod_fit is None:
        return "production has no fit-era trades — the normalization is the only measurement."
    if norm_fit is None:
        return "normalized variant has no fit-era trades."
    dn = (n_norm - n_prod) / n_prod if n_prod else None
    if norm_fit > prod_fit and n_norm >= n_prod:
        return (f"REPAIR: the scale-free cut is better out of the selection window "
                f"({prod_fit:+.4f} -> {norm_fit:+.4f}) on {dn:+.0%} sample. Carry it "
                f"forward as a candidate variant.")
    if norm_fit > prod_fit:
        return (f"BETTER BUT THINNER: {prod_fit:+.4f} -> {norm_fit:+.4f} on {dn:+.0%} "
                f"sample; the gain may be selection on a smaller set.")
    if n_norm > n_prod * 1.2:
        return (f"THE RAMP CUT THE OTHER WAY: the scale-free cut fires {dn:+.0%} more and "
                f"earns less out of window ({prod_fit:+.4f} -> {norm_fit:+.4f}). "
                f"Publishing it is the point — the fixed cut was doing work.")
    return (f"NO REPAIR: {prod_fit:+.4f} -> {norm_fit:+.4f} at {dn:+.0%} sample. The fixed "
            f"cut is not the defect for this gate.")


if __name__ == "__main__":
    main()
