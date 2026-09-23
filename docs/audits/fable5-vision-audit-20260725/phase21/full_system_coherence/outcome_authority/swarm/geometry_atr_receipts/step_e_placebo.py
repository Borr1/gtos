"""Step E -- the control that decides whether the SIGNAL is doing the work.

A per-trade stop rescale is not a neutral operation even when its geometric mean is 1.0.
Shrinking a stop makes the -1R more likely AND (for a target that scales with the stop)
makes the +kR more likely; widening does the reverse. So a rescale drawn from the RIGHT
distribution but assigned to the WRONG trades can still move mean R. If it moves it by as
much as the real assignment does, then nothing about ATR14/ATR50 was measured -- only the
arithmetic of jittering stops.

Three arms, all at the headline band, all paired to the same CONTROL:

    CORRECTED   stop_mult_i = normalise(v_i ** beta)           (the real assignment)
    PLACEBO     the SAME multiset of multipliers, randomly PERMUTED within each sleeve,
                20 independent permutations -- so the distribution is identical and only
                the pairing with v is destroyed
    ANTI        stop_mult_i = normalise(v_i ** (-beta))        (the sign flipped)

If CORRECTED sits outside the placebo distribution and ANTI sits on the other side of
zero, the vol-ratio assignment is carrying the result. If CORRECTED sits inside the
placebo distribution, it is not.
"""

from __future__ import annotations

import collections
import datetime as _dt
import gzip
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/swarm-geom-20260811"
R1 = REPO + "/docs/audits/fable5-vision-audit-20260725/phase20/receipts/r1"
sys.path.insert(0, REPO)
sys.path.insert(0, R1)

import r1_estate_rewalk as R  # noqa: E402
from step_a_beta import _atr_vec, _true_range  # noqa: E402
from step_bcd import (  # noqa: E402
    ARMED, BANDS, EXCLUDED, HEADLINE_BAND, MAXBARS, SEED, TARGET_FIXED_PRICE,
    WINSOR_HI, WINSOR_LO, walk_pertrade,
)

OUTDIR = Path("/private/tmp/atr-scaling-20260811")
NPERM = 20


def main() -> int:
    t0 = time.time()
    rng = np.random.default_rng(SEED + 99)
    series, index = R.load_series()
    beta_doc = json.loads((OUTDIR / "STEP_A_BETA_V1.json").read_text())
    BETA = {15: beta_doc["per_timeframe"]["M15"]["two_sided_travel"]["beta"],
            16388: beta_doc["per_timeframe"]["H4"]["two_sided_travel"]["beta"],
            16408: beta_doc["per_timeframe"]["D1"]["two_sided_travel"]["beta"]}
    with gzip.open(R.TRADES, "rt") as fh:
        doc = json.load(fh)
    estate = {k: v for k, v in doc["trades"].items() if v and k not in EXCLUDED}

    def tid(k, r):
        return f"{r['sleeve']}#{k}"

    atr_cache = {}

    def atrs(key):
        if key not in atr_cache:
            bars, _ = series[key]
            n = len(bars)
            h = np.fromiter((b.h for b in bars), np.float64, n)
            l = np.fromiter((b.l for b in bars), np.float64, n)
            c = np.fromiter((b.c for b in bars), np.float64, n)
            tr = _true_range(h, l, c)
            atr_cache[key] = (_atr_vec(tr, 14), _atr_vec(tr, 50))
        return atr_cache[key]

    def build(sign):
        out = {}
        per_sleeve_ids = {}
        for sleeve, rows in sorted(estate.items()):
            raws, ids = [], []
            for k, r in enumerate(rows):
                key = (r["symbol"], int(r["timeframe"]))
                if key not in index:
                    continue
                i = index[key].get(_dt.datetime.fromisoformat(r["decision_bar_iso"]))
                if i is None:
                    continue
                a14, a50 = atrs(key)
                if i >= len(a14) or a50[i] <= 0 or a14[i] <= 0:
                    continue
                v = float(a14[i] / a50[i])
                raws.append(v ** (sign * BETA[int(r["timeframe"])]))
                ids.append(tid(k, r))
            if not raws:
                continue
            gm = float(np.exp(np.mean(np.log(raws))))
            wins = [min(WINSOR_HI, max(WINSOR_LO, x / gm)) for x in raws]
            for key, m in zip(ids, wins):
                out[key] = m
            per_sleeve_ids[sleeve] = (ids, wins)
        return out, per_sleeve_ids

    m_corr, per_sleeve = build(+1.0)
    m_anti, _ = build(-1.0)
    print(f"built multipliers ({time.time()-t0:.0f}s)", flush=True)

    def run(mults, tag):
        rows = {}
        for sleeve, trs in sorted(estate.items()):
            scales = sleeve not in TARGET_FIXED_PRICE
            out = []
            walk_pertrade(trs, series, index, "native", MAXBARS, HEADLINE_BAND, True,
                          mults, tid, target_scales=scales, collect=out)
            rows[sleeve] = out
        return rows

    ctrl = run({}, "control")
    corr = run(m_corr, "corrected")
    anti = run(m_anti, "anti")
    print(f"control/corrected/anti done ({time.time()-t0:.0f}s)", flush=True)

    def pooled_delta(a, b, names):
        av = np.array([x[1] for s in names for x in a[s]])
        bv = np.array([x[1] for s in names for x in b[s]])
        return float((bv - av).mean())

    all_names = sorted(estate)
    res = {
        "what": "placebo + anti-correction controls for the ATR14/ATR50 stop rescale",
        "band": HEADLINE_BAND, "n_permutations": NPERM,
        "groups": {},
    }
    groups = {"estate": all_names, "armed_four": list(ARMED)}
    groups.update({s: [s] for s in all_names})

    perms = []
    for p in range(NPERM):
        mp = {}
        for sleeve, (ids, wins) in per_sleeve.items():
            order = rng.permutation(len(ids))
            for j, key in enumerate(ids):
                mp[key] = wins[order[j]]
        perms.append(run(mp, f"placebo{p}"))
        print(f"  placebo {p+1}/{NPERM} ({time.time()-t0:.0f}s)", flush=True)

    for gname, names in groups.items():
        d_corr = pooled_delta(ctrl, corr, names)
        d_anti = pooled_delta(ctrl, anti, names)
        d_perm = [pooled_delta(ctrl, pm, names) for pm in perms]
        arr = np.array(d_perm)
        res["groups"][gname] = {
            "n_trades": sum(len(ctrl[s]) for s in names),
            "delta_corrected": d_corr,
            "delta_anti_correction": d_anti,
            "placebo_deltas": [float(x) for x in arr],
            "placebo_mean": float(arr.mean()),
            "placebo_sd": float(arr.std(ddof=1)),
            "placebo_min": float(arr.min()), "placebo_max": float(arr.max()),
            "corrected_outside_placebo_range": bool(d_corr > arr.max() or d_corr < arr.min()),
            "corrected_z_vs_placebo": (float((d_corr - arr.mean()) / arr.std(ddof=1))
                                       if arr.std(ddof=1) > 0 else None),
            "placebo_one_sided_p_ge_corrected": float((arr >= d_corr).mean()),
        }
    res["elapsed_s"] = round(time.time() - t0, 1)
    (OUTDIR / "STEP_E_PLACEBO_V1.json").write_text(json.dumps(res, indent=1))
    print("WROTE", OUTDIR / "STEP_E_PLACEBO_V1.json")
    for g in ("estate", "armed_four"):
        r = res["groups"][g]
        print(f"{g}: corrected {r['delta_corrected']:+.5f} | anti {r['delta_anti_correction']:+.5f} "
              f"| placebo mean {r['placebo_mean']:+.5f} sd {r['placebo_sd']:.5f} "
              f"range [{r['placebo_min']:+.5f},{r['placebo_max']:+.5f}] "
              f"outside={r['corrected_outside_placebo_range']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
