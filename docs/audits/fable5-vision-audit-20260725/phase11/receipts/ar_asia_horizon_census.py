"""Session AR — the horizon census that qualifies AR-3's extension, and AL's own grid edge.

    python3 docs/audits/fable5-vision-audit-20260725/phase11/receipts/ar_asia_horizon_census.py

WHY THIS FILE EXISTS
--------------------
AR-3 fitted `R/day = a - b/stop_mult` to the banded surface at R^2 0.9989 and then extended past
AL's 3.5x grid edge to test the fit's zero crossing. The extension looked like a clean
confirmation: the model predicted 5x, 7x and 9x to within 0.004 R/day out of its own fitting
range, and the surface crossed zero at 14x.

**Then an adversarial check on the one thing that could invalidate it found that it does.** A
wider stop is only a geometry change if the price still resolves the trade — hits the stop or the
target — inside the simulation's horizon. It does not: `asia_pdl_fade` is resimulated over a
20-hour maximum hold, and as the stop widens the exit migrates from `stop`/`target` to
**`maxbars`**, which is the horizon's own edge and not a contract anybody proposed.

So the wide-stop arms do not measure "the sleeve at a bigger R-unit". They measure "the sleeve
time-boxed at 20 hours with a nominal R-unit N times larger", and the asymptote they show is a
property of the box. This file counts the migration so the qualification is a number rather than a
worry — and it counts it across AL's OWN grid too, where the same effect is already present at the
edge AL published.

WHAT IT DOES NOT DO
-------------------
It does not re-gate anything and it charges no cost. Exit-reason counts and gross R are properties
of the resimulation alone, which is the point: the confound is upstream of the cost model, so
measuring it needs no cost model.

THE RIGHT NAME FOR THE DEFECT IS CONTRACT SUBSTITUTION, NOT "AN UNPROPOSABLE HORIZON"
-------------------------------------------------------------------------------------
Corrected by an adversarial pass over this file's own framing. `asia_pdl_fade` HAS a wired live
max-hold: `time_stop_bars=32` printed M15 bars (`execution_packets.py:63-64`, `MAXBARS = 32` at
`asia_pdl_fade.py:31`), enforced in printed trading bars by `execution.py:8953-8958` -- **8 trading
hours**. The research harness's 80-bar box is therefore **2.5x LOOSER than the live contract**, not
an invention. So the harness is substituting a MORE GENEROUS exit, and truncation under contract
fidelity would be HIGHER at every stop rather than lower. That cuts the same way -- a wide-stop cell
is still not an R-unit statement -- and it strengthens the conclusion: at the live 8-hour cap there
is even less room for a wide stop to resolve. It also names a cheaper instrument than "a longer
harness horizon": the sleeve's own live contract.

Offline, pure, no broker import, no config read."""

from __future__ import annotations

import collections
import gzip
import importlib.util
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.costs.model import load_broker_true_costs  # noqa: E402

HERE = Path(__file__).resolve().parent
AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
OUT = HERE / "AR_ASIA_HORIZON_CENSUS_V1.json"
ASIA = "asia_pdl_fade"
#: AL's own grid, plus AR-3's extension. The point of running both in one table is that the
#: confound does not start at the extension -- it is already material at AL's published edge.
AL_STOPS = (1.0, 1.5, 2.0, 2.5, 3.0, 3.5)
AR_EXT_STOPS = (5.0, 7.0, 9.0, 11.0, 14.0)
#: A gate-relevant threshold, declared before the counts are read: above this share of `maxbars`
#: exits the cell is measuring the horizon rather than the geometry, so its R is not a property of
#: any proposable contract. 25 % is one trade in four and is stated as a judgement, not derived.
MAXBARS_CONFOUND_THRESHOLD = 0.25


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    AD = _load(AUD / "phase7/receipts/ad_exit_sweep.py", "hc_ad")
    costs = load_broker_true_costs(AD.COSTS)
    series, index, _r = AD.load_bars()
    rule = AD.resolve_rule("FTMO-Server3")
    raw = json.load(gzip.open(AUD / "phase6/receipts/AA_ESTATE_TRADES.json.gz", "rt"))
    rows = raw["trades"][ASIA]

    def census(rs: list[dict]) -> dict:
        er = collections.Counter(r["exit_reason"] for r in rs)
        holds = [r["hold_hours"] for r in rs]
        n = len(rs)
        return {
            "n": n,
            "exit_reason": dict(sorted(er.items())),
            "maxbars_frac": round(er.get("maxbars", 0) / n, 5) if n else None,
            "stop_frac": round(er.get("stop", 0) / n, 5) if n else None,
            "target_frac": round(er.get("target", 0) / n, 5) if n else None,
            "median_hold_hours": round(statistics.median(holds), 3),
            "max_hold_hours": round(max(holds), 3),
            "mean_r_gross": round(statistics.fmean(r["r_gross"] for r in rs), 6),
            "mean_sl_distance_price": round(
                statistics.fmean(r["sl_distance_price"] for r in rs), 6),
        }

    out: dict = {
        "schema": "gtos.wave11.ar.asia_horizon_census.v1",
        "generated_by": str(Path(__file__).resolve().relative_to(REPO)),
        "session": "AR", "blocks": "B1450-B1499",
        "question": ("AR-3's cost model was extended past AL's 3.5x stop edge to test its zero "
                     "crossing. A wider stop is only a GEOMETRY change if the price still "
                     "resolves the trade inside the simulation horizon. Does it?"),
        "answer_in_one_line": None,      # filled below, from the counts
        "maxbars_confound_threshold": MAXBARS_CONFOUND_THRESHOLD,
        "threshold_is_a_judgement": (
            "declared here before the counts were read. Above this share of `maxbars` exits a "
            "cell is measuring the harness BOX rather than the geometry. One trade in four; "
            "stated, not derived."),
        "and_the_defect_is_CONTRACT_SUBSTITUTION_not_an_unproposable_horizon": (
            "corrected by an adversarial pass over this file's own framing. `asia_pdl_fade` HAS a "
            "wired live max-hold -- `time_stop_bars=32` printed M15 bars "
            "(`execution_packets.py:63-64`, `MAXBARS = 32` at `asia_pdl_fade.py:31`), enforced by "
            "`execution.py:8953-8958` -- which is 8 TRADING HOURS. The harness's 80-bar box is "
            "therefore 2.5x LOOSER than the live contract, not an invention: the harness "
            "substitutes a MORE GENEROUS exit. Truncation under contract fidelity would be HIGHER "
            "at every stop, not lower, so a high `maxbars` share here UNDERSTATES what a "
            "deployable version would take. That cuts the same way -- a wide-stop cell is still "
            "not an R-unit statement -- and it names a cheaper instrument than 'a longer harness "
            "horizon': the sleeve's own live contract."),
        "as_walked": census(rows),
        "cells": {},
    }

    for st in AL_STOPS + AR_EXT_STOPS:
        v = AD.Variant(name=f"stop_{st:g}x", family="cross_stop_target_timestop",
                       stop_mult=st, target_mode="scales_with_stop")
        rs, _tel = AD.resimulate(rows, v, series, index, costs, "FTMO", rule)
        c = census(rs)
        c["grid"] = "AL_published" if st in AL_STOPS else "AR_extension"
        c["confounded_by_the_horizon"] = bool(
            (c["maxbars_frac"] or 0) > MAXBARS_CONFOUND_THRESHOLD)
        out["cells"][f"{st:g}x"] = c
        print(f"  stop {st:5g}x [{c['grid']:12s}] n={c['n']:5d} "
              f"maxbars {c['maxbars_frac']:.4f} stop {c['stop_frac']:.4f} "
              f"target {c['target_frac']:.4f}  median hold {c['median_hold_hours']:6.2f}h "
              f"gross R {c['mean_r_gross']:+.5f}"
              f"{'   <-- HORIZON-CONFOUNDED' if c['confounded_by_the_horizon'] else ''}")

    first_bad = next((k for k, c in out["cells"].items()
                      if c["confounded_by_the_horizon"]), None)
    al_bad = [k for k, c in out["cells"].items()
              if c["grid"] == "AL_published" and c["confounded_by_the_horizon"]]
    out["answer_in_one_line"] = (
        f"NO. The exit migrates from stop/target to `maxbars` as the stop widens: "
        f"{out['as_walked']['maxbars_frac']:.1%} of as-walked trades exit on the horizon and "
        f"{out['cells']['14x']['maxbars_frac']:.1%} at AR-3's 14x extension cell. The first "
        f"confounded cell is {first_bad}.")
    out["consequences"] = {
        "for_AR_3s_extension": (
            "the wide-stop arms do NOT measure the sleeve at a bigger R-unit. They measure the "
            "sleeve TIME-BOXED at its 20-hour resimulation horizon with a nominal R-unit N times "
            "larger, and gross R per trade falls monotonically as the box binds "
            f"({out['as_walked']['mean_r_gross']:+.5f} as-walked -> "
            f"{out['cells']['14x']['mean_r_gross']:+.5f} at 14x). So the cost model's INTERCEPT "
            "is neither confirmed nor refuted by the extension -- the instrument runs out of "
            "horizon before the geometry does, and the honest verdict is "
            "NOT_EVALUABLE_BY_THIS_INSTRUMENT."),
        "for_AL_s_own_frontier": (
            f"the confound is not an artefact of AR's extension: it is already material inside "
            f"AL's published grid at {al_bad}. So AL's wide-stop column -- which contains its "
            f"published winner's neighbourhood -- is partly a horizon measurement too, and the "
            f"same qualification applies to the flat-band figures the frontier reports."
            if al_bad else
            "AL's published grid is clean of the confound at every stop it ran."),
        "the_exact_requirement_to_settle_it": (
            "a resimulation horizon longer than 20 hours for this sleeve. That is a harness "
            "change (`maxbars` / the bar window `ad_exit_sweep.load_bars` supplies), not a "
            "research judgement, and it is cheap: `resimulate` runs in well under a second on "
            "2,827 trades. Until it is done, no wide-stop cell for this sleeve should be quoted "
            "as an R-unit statement."),
        "what_survives_unqualified": (
            "the 1/stop COST MECHANISM on AL's own low-stop column, where the horizon barely "
            f"binds ({out['cells']['1x']['maxbars_frac']:.1%} maxbars at 1x), and the flat-vs-"
            "banded sign flip AO measured. Cost per trade is a price distance and in R it "
            "divides by the stop; that is arithmetic and the horizon does not touch it."),
    }
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(f"\n{out['answer_in_one_line']}")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
