"""G2-M3 — the flat slippage constant BIASES every exit-frontier comparison in the estate.

THE MECHANISM, STATED BEFORE IT IS MEASURED
--------------------------------------------
`RECON_SLIPPAGE_ADJUDICATION_V1` measured slippage as **barrier-conditional**: a stop exit
costs +0.03932 R, a target exit costs 0.0 (favourable, not bankable, correct by design), a
time/maxbars exit +0.00141. The estate charges a **flat 0.02 on every trade**
(`config/agent_config.yaml:740`).

An exit-contract treatment is precisely a treatment that **moves mass between barriers**. A
wider target moves trades out of `target` (slippage 0.0) and into `stop` and `maxbars`. Under
the flat constant that migration is invisible, so **a wide-target cell is credited with a
slippage bill it would not actually pay, and the frontier over-ranks it.**

This is not a re-litigation of any admission. It is a measurement of a BIAS TERM that every
published exit-frontier number in the estate carries, including the two the program has argued
about most: `mx_btcusd_d1_donchian_20_breakout @ target_5R` (the former standing admission,
REJECTed 2026-08-07 under A1b's corrected null) and `sub_xvol_pullback @ target_4R` (an ARMED
sleeve, REJECTed by AU at all four bands).

Sign convention: `bias = (flat charge) - (barrier-true charge)`, per arm. The reported
`bias_on_the_contrast` is treatment-minus-control; a NEGATIVE value means the published
frontier **overstates** the treatment.

NO WRITES OUTSIDE THIS DIRECTORY. Measurement only.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[9]
B8 = REPO / ("docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/"
             "outcome_authority/swarm2/breakthrough")
for p in (str(REPO), str(B8)):
    if p not in sys.path:
        sys.path.insert(0, p)

from b8_paired_shadow.arms import (  # noqa: E402
    ArmUnavailable, partial_be_policy, published_policy, run_on_own_grid, target_r_policy,
)
from b8_paired_shadow.paired_stats import paired_summary  # noqa: E402
from b8_paired_shadow.substrate import Substrate  # noqa: E402

OUT = Path(__file__).resolve().parent / "receipts"
BAND = "mid"
CHARGED_FLAT = 0.02
ENTRY_LEG = 0.00663
LEG = {"stop": 0.03932, "trail": 0.03932, "target": 0.0,
       "time_stop": 0.00141, "maxbars": 0.00141, "rollover_flat": 0.00141}
USD_PER_R = 500.0

#: (label, sleeve, control policy, treatment policy) -- the estate's own live-vs-frontier
#: cells, taken from B8's seeded questions so the comparison is like-for-like.
CELLS = [
    ("mx_btcusd @ live_2R -> target_5R", "mx_btcusd_d1_donchian_20_breakout",
     lambda it: published_policy(it), lambda it: target_r_policy(it, 5.0)),
    ("sub_xvol_pullback @ live_3R -> target_4R", "sub_xvol_pullback",
     lambda it: published_policy(it), lambda it: target_r_policy(it, 4.0)),
    ("energy_agri @ plain_4R -> partial_be_runner_2R", "energy_agri",
     lambda it: target_r_policy(it, 4.0), lambda it: partial_be_policy(it, 2.0)),
    ("mx_ethusd @ live -> target_5R", "mx_ethusd_d1_donchian_20_breakout",
     lambda it: published_policy(it), lambda it: target_r_policy(it, 5.0)),
    ("crypto @ live -> target_4R", "crypto",
     lambda it: published_policy(it), lambda it: target_r_policy(it, 4.0)),
]


def slip(reason: str | None) -> float:
    return LEG.get(str(reason), 0.0)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sub = Substrate.load(verbose=False)
    res: dict[str, Any] = {
        "measurement": "G2-M3 exit-frontier slippage bias",
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
        "convention": "bias = flat_charge - barrier_true_charge, per arm; "
                      "bias_on_the_contrast = treatment - control. NEGATIVE means the "
                      "published frontier OVERSTATES the treatment.",
        "recon_legs": LEG, "charged_flat": CHARGED_FLAT, "usd_per_r": USD_PER_R,
        "cells": {},
    }
    for label, sleeve, cpol, tpol in CELLS:
        rows = []
        for it in sub.by_sleeve(sleeve):
            try:
                c = run_on_own_grid(it, sub, cpol(it), BAND)
                t = run_on_own_grid(it, sub, tpol(it), BAND)
            except ArmUnavailable:
                continue
            rows.append((it.decision_day, c, t))
        if not rows:
            res["cells"][label] = {"n": 0}
            continue
        days = [d for d, _, _ in rows]
        cmix = Counter(str(c.exit_reason) for _, c, _ in rows)
        tmix = Counter(str(t.exit_reason) for _, _, t in rows)
        n = len(rows)
        c_true = sum(slip(c.exit_reason) for _, c, _ in rows) / n
        t_true = sum(slip(t.exit_reason) for _, _, t in rows) / n
        d_r = [t.r - c.r for _, c, t in rows]
        s = paired_summary(d_r, days)
        # bias per arm: what the flat constant credits minus what RECON says is owed
        c_bias = CHARGED_FLAT - c_true
        t_bias = CHARGED_FLAT - t_true
        contrast_bias = t_bias - c_bias
        res["cells"][label] = {
            "sleeve": sleeve, "n": n, "n_days": len(set(days)),
            "control_exit_mix": {k: round(v / n, 4) for k, v in sorted(cmix.items())},
            "treatment_exit_mix": {k: round(v / n, 4) for k, v in sorted(tmix.items())},
            "control_barrier_true_slippage": round(c_true, 6),
            "treatment_barrier_true_slippage": round(t_true, 6),
            "published_delta_r_per_trade": round(s.mean, 6),
            "ci95_block": [round(s.ci95_block[0], 6), round(s.ci95_block[1], 6)]
            if s.ci95_block else None,
            "p_block": round(s.p_block, 6) if s.p_block is not None else None,
            "bias_on_the_contrast": round(contrast_bias, 6),
            "corrected_delta_r_per_trade": round(s.mean + contrast_bias, 6),
            "bias_as_share_of_published_delta": (round(abs(contrast_bias / s.mean), 4)
                                                 if s.mean else None),
            "usd": {"published": round(s.mean * USD_PER_R, 2),
                    "bias": round(contrast_bias * USD_PER_R, 2),
                    "corrected": round((s.mean + contrast_bias) * USD_PER_R, 2)},
        }
        c = res["cells"][label]
        print(f"{label:46s} n={n:4d} published{s.mean:+9.5f}  bias{contrast_bias:+9.5f} "
              f"({c['bias_as_share_of_published_delta']}) -> corrected"
              f"{c['corrected_delta_r_per_trade']:+9.5f}")

    (OUT / "G2_M3_EXIT_FRONTIER_SLIPPAGE_BIAS_V1.json").write_text(json.dumps(res, indent=1))
    print(f"-> {OUT / 'G2_M3_EXIT_FRONTIER_SLIPPAGE_BIAS_V1.json'}")


if __name__ == "__main__":
    main()
