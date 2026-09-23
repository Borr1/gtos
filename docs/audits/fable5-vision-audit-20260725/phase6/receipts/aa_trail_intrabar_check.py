"""Is the trail repair real, or is it intrabar sequencing? Re-label and find out.

    python3 docs/audits/fable5-vision-audit-20260725/phase6/receipts/aa_trail_intrabar_check.py

Labelling `asian_fade` and `metal_session_reversion` under their production
`trailing_runner` contracts produced a large apparent improvement over the plain
stop/target/maxbars exit — +0.759 and +0.363 R/trade. That is the kind of number this
programme has been wrong about before, so it was checked before it was reported, and the
check found the reason:

    asian_fade                95.8 % of trail exits land on the FIRST bar after entry
    metal_session_reversion   84.5 %

`primitives.simulate` sets the running extreme from bar *j*'s own high and then checks, on
that same bar *j*, whether the low has retraced `trail_gap` from it. So a trail arms and
fills inside one M15 bar, at `high - gap`, on the assumption that within the bar the high
came before the low. No bar archive can support that assumption, and the whole of the
improvement rides on it.

This script re-labels both sleeves under `ExitPolicy(trail_lag_extremes=True)`, which
(a) refuses to fill on the bar that set the running extreme, and (b) fills at the bar's
OPEN when the market opened through the trail level, because a stop resting at a price the
bar never traded does not fill there. Everything else — the same candidates, the same bars,
the same generation — is held fixed, so the difference is the assumption and nothing else.

The three numbers are reported side by side and none is called "the" answer:

    plain          stop / target / maxbars, no trail            (what X's walk measured)
    trail_prod     the sleeve's own contract, production semantics  (an UPPER BOUND)
    trail_lagged   the same contract with the intrabar assumption removed  (a LOWER BOUND)

The truth is between them and only tick data can locate it, which is the honest statement
and also the exact scope of `FOURTH_REVIEW.md` §9's forward tick capture.
"""

from __future__ import annotations

import datetime as dt
import glob
import gzip
import json
import os
import statistics
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_M15  # noqa: E402
from src.components.ultimate_book.execution_packets import SLEEVE_EXIT_PROFILES  # noqa: E402
from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
IN = HERE / "AA_ESTATE_TRADES.json.gz"
OUT = HERE / "AA_TRAIL_INTRABAR_V1.json"
SLEEVES = ("asian_fade", "metal_session_reversion")


def main() -> dict:
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AA")
    with gzip.open(IN, "rt") as fh:
        raw = json.load(fh)

    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)

    wanted = {r["symbol"] for s in SLEEVES for r in raw["trades"].get(s, [])}
    files = {}
    for p in glob.glob(f"{BARS}/FTMO_*_M15.csv.gz"):
        stem = os.path.basename(p)[len("FTMO_"):-len("_M15.csv.gz")]
        if res(stem) in wanted:
            files[(res(stem), TF_M15)] = p
    src = CsvBarSource(files, label="vps-bars-20260727-FTMO")
    series: dict[str, tuple[list[Bar], dict[dt.datetime, int]]] = {}
    for key, _p in files.items():
        rows = src._load(key)
        bars = [Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0))
                for r in rows]
        idx = {dt.datetime.fromisoformat(r["time"]): i for i, r in enumerate(rows)}
        series[key[0]] = (bars, idx)
    print(f"loaded {len(series)} M15 series for {sorted(wanted)}")

    out: dict = {
        "schema": "gtos.walkforward.trail_intrabar_check.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "source": str(IN.relative_to(REPO)),
        "question": ("Is the trail's measured improvement a real exit repair, or is it the "
                     "production simulator's same-bar arm-and-fill?"),
        "sleeves": {},
    }

    for sleeve in SLEEVES:
        rows = raw["trades"].get(sleeve) or []
        prof_s = SLEEVE_EXIT_PROFILES.get(sleeve, {})
        trig, gap = prof_s.get("trigger_r"), prof_s.get("trail_gap_r")
        rec: list[dict] = []
        for r in rows:
            bars, idx = series[r["symbol"]]
            i = idx.get(dt.datetime.fromisoformat(r["decision_bar_iso"]))
            if i is None:
                continue
            sl = float(r["sl_distance_price"])
            base = dict(target_dist=r["target_dist"], maxbars=raw["maxbars"])
            lag = replay(bars, i, int(r["direction"]), stop_dist=sl,
                         policy=ExitPolicy(**base, trail_arm=float(trig) * sl,
                                           trail_gap=float(gap) * sl,
                                           trail_lag_extremes=True, label="trail_lagged"))
            rec.append({
                "plain": float(r["r_gross_plain"]),
                "trail_prod": float(r["r_gross"]),
                "trail_lagged": float(winsorize_R(lag.r_gross)),
                "prod_bars": int(r["exit_bar_offset"]),
                "lag_bars": int(lag.bars_held),
                "prod_reason": r["exit_reason"],
                "lag_reason": lag.exit_reason,
            })
        if not rec:
            continue
        n = len(rec)

        def m(k):
            return statistics.fmean(x[k] for x in rec)

        first_bar = sum(1 for x in rec if x["prod_reason"] == "trail" and x["prod_bars"] == 1)
        n_trail = sum(1 for x in rec if x["prod_reason"] == "trail")
        out["sleeves"][sleeve] = {
            "n": n,
            "trigger_r": trig, "trail_gap_r": gap,
            "mean_r_plain": round(m("plain"), 6),
            "mean_r_trail_production": round(m("trail_prod"), 6),
            "mean_r_trail_lagged": round(m("trail_lagged"), 6),
            "delta_prod_vs_plain": round(m("trail_prod") - m("plain"), 6),
            "delta_lagged_vs_plain": round(m("trail_lagged") - m("plain"), 6),
            "share_of_apparent_gain_that_is_intrabar": (
                round(1.0 - (m("trail_lagged") - m("plain"))
                      / (m("trail_prod") - m("plain")), 5)
                if abs(m("trail_prod") - m("plain")) > 1e-9 else None
            ),
            "n_trail_exits_production": n_trail,
            "n_trail_exits_on_first_bar": first_bar,
            "frac_trail_exits_on_first_bar": round(first_bar / n_trail, 5) if n_trail else None,
            "lagged_exit_reasons": {
                k: sum(1 for x in rec if x["lag_reason"] == k)
                for k in sorted({x["lag_reason"] for x in rec})
            },
            "verdict": (
                "REAL — the benefit survives removing the intrabar assumption"
                if (m("trail_lagged") - m("plain")) > 0.5 * (m("trail_prod") - m("plain"))
                else "INTRABAR — most of the apparent benefit is the same-bar arm-and-fill"
            ),
        }
        for label, val in (("trail_production", m("trail_prod")),
                           ("trail_lagged", m("trail_lagged")),
                           ("plain", m("plain"))):
            ledger.record(mechanism="trail_exit_variant", sleeve=sleeve,
                          variant={"policy": label, "trigger_r": trig, "trail_gap_r": gap},
                          window="M15 archive 2024-2026", outcome="evaluated",
                          metric=val, metric_name="mean_r_gross")
        v = out["sleeves"][sleeve]
        print(f"\n{sleeve}: n={n}")
        print(f"  plain        {v['mean_r_plain']:+.5f} R/trade")
        print(f"  trail PROD   {v['mean_r_trail_production']:+.5f}  "
              f"(delta {v['delta_prod_vs_plain']:+.5f})   <- UPPER bound")
        print(f"  trail LAGGED {v['mean_r_trail_lagged']:+.5f}  "
              f"(delta {v['delta_lagged_vs_plain']:+.5f})   <- LOWER bound")
        print(f"  intrabar share of the apparent gain: "
              f"{v['share_of_apparent_gain_that_is_intrabar']}")
        print(f"  {v['verdict']}")

    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return out


if __name__ == "__main__":
    main()
