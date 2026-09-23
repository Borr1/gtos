"""Correction pass: how many trades MATERIALLY change, and where the change lives.

`_paired_delta`'s `n_changed` counts any nonzero difference, which for this intervention
is mostly floating-point dust: a stop exit returns exactly -1 R and a target exit exactly
+k R no matter how wide the stop is (R is measured in units of that same stop), so those
rows differ only in the last bits. The economically real changes are (a) rows whose EXIT
REASON moves and (b) rows that exit on `maxbars` or `trail`, whose R is a price distance
divided by the rescaled stop. This measures both, at the headline band.
"""

from __future__ import annotations

import collections
import gzip
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/swarm-geom-20260811"
sys.path.insert(0, REPO)
sys.path.insert(0, REPO + "/docs/audits/fable5-vision-audit-20260725/phase20/receipts/r1")

import r1_estate_rewalk as R  # noqa: E402
from step_bcd import (  # noqa: E402
    ARMED, EXCLUDED, HEADLINE_BAND, MAXBARS, TARGET_FIXED_PRICE, walk_pertrade,
)

OUTDIR = Path("/private/tmp/atr-scaling-20260811")
TOL = 1e-9


def main() -> int:
    t0 = time.time()
    series, index = R.load_series()
    main_doc = json.loads((OUTDIR / "ATR_SCALING_ESTATE_V1.json").read_text())
    beta_doc = main_doc["step_a_travel_exponent"]
    BETA = {15: beta_doc["per_timeframe"]["M15"]["two_sided_travel"]["beta"],
            16388: beta_doc["per_timeframe"]["H4"]["two_sided_travel"]["beta"],
            16408: beta_doc["per_timeframe"]["D1"]["two_sided_travel"]["beta"]}
    with gzip.open(R.TRADES, "rt") as fh:
        doc = json.load(fh)
    estate = {k: v for k, v in doc["trades"].items() if v and k not in EXCLUDED}

    import datetime as _dt

    from step_a_beta import _atr_vec, _true_range
    from step_bcd import WINSOR_HI, WINSOR_LO

    def tid(k, r):
        return f"{r['sleeve']}#{k}"

    cache = {}

    def atrs(key):
        if key not in cache:
            bars, _ = series[key]
            n = len(bars)
            h = np.fromiter((b.h for b in bars), np.float64, n)
            l = np.fromiter((b.l for b in bars), np.float64, n)
            c = np.fromiter((b.c for b in bars), np.float64, n)
            cache[key] = (_atr_vec(_true_range(h, l, c), 14),
                          _atr_vec(_true_range(h, l, c), 50))
        return cache[key]

    mults = {}
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
            raws.append(float(a14[i] / a50[i]) ** BETA[int(r["timeframe"])])
            ids.append(tid(k, r))
        if not raws:
            continue
        gm = float(np.exp(np.mean(np.log(raws))))
        for key, x in zip(ids, raws):
            mults[key] = min(WINSOR_HI, max(WINSOR_LO, x / gm))

    out = {"band": HEADLINE_BAND, "tolerance": TOL, "per_sleeve": {}}
    tot = collections.Counter()
    armed = collections.Counter()
    for sleeve, rows in sorted(estate.items()):
        scales = sleeve not in TARGET_FIXED_PRICE
        c, n = [], []
        walk_pertrade(rows, series, index, "native", MAXBARS, HEADLINE_BAND, True, {},
                      tid, target_scales=scales, collect=c)
        walk_pertrade(rows, series, index, "native", MAXBARS, HEADLINE_BAND, True, mults,
                      tid, target_scales=scales, collect=n)
        assert [x[0] for x in c] == [x[0] for x in n]
        mat = sum(1 for a, b in zip(c, n) if abs(a[1] - b[1]) > TOL)
        rc = sum(1 for a, b in zip(c, n) if a[2] != b[2])
        soft = sum(1 for a in c if a[2] in ("maxbars", "trail", "time_stop"))
        rec = {"n": len(c), "n_material_change": mat,
               "frac_material_change": mat / len(c) if c else None,
               "n_exit_reason_changed": rc,
               "n_control_exits_with_path_dependent_R": soft,
               "mean_abs_material_delta_R": (
                   float(np.mean([abs(a[1] - b[1]) for a, b in zip(c, n)
                                  if abs(a[1] - b[1]) > TOL])) if mat else 0.0)}
        out["per_sleeve"][sleeve] = rec
        for k, v in (("n", len(c)), ("mat", mat), ("rc", rc), ("soft", soft)):
            tot[k] += v
            if sleeve in ARMED:
                armed[k] += v
        print(f"  {sleeve:40s} n={len(c):5d} material={mat:5d} reason={rc:4d} "
              f"({time.time()-t0:.0f}s)", flush=True)

    out["estate_total"] = {"n": tot["n"], "n_material_change": tot["mat"],
                           "frac_material_change": tot["mat"] / tot["n"],
                           "n_exit_reason_changed": tot["rc"],
                           "n_control_exits_with_path_dependent_R": tot["soft"]}
    out["armed_four"] = {"n": armed["n"], "n_material_change": armed["mat"],
                         "frac_material_change": armed["mat"] / armed["n"],
                         "n_exit_reason_changed": armed["rc"],
                         "n_control_exits_with_path_dependent_R": armed["soft"]}
    out["note"] = ("`frac_changed` in `per_sleeve.*.bands.*.paired_delta_R_per_trade` "
                   "counts ANY nonzero difference and is therefore ~1.0 everywhere: a "
                   "stop exit is exactly -1 R and a target exit exactly +k R in units of "
                   "the SAME stop that was rescaled, so those rows move only in the last "
                   "bits. Read `n_material_change` (|delta| > 1e-9) and "
                   "`n_exit_reason_changed` instead.")
    main_doc["material_change_audit"] = out
    (OUTDIR / "ATR_SCALING_ESTATE_V1.json").write_text(
        json.dumps(main_doc, indent=1, default=str))
    print(json.dumps(out["estate_total"], indent=1))
    print(json.dumps(out["armed_four"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
