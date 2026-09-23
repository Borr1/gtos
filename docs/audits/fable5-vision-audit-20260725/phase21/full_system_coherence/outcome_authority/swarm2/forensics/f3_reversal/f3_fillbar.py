#!/usr/bin/env python3
"""F3 (7b) — is the FILL BAR abnormal?  The control the artifact check needs.

The fill bar's range is 0.390 R at the median and the median stop loser's whole
favourable excursion is 0.395 R.  That equality only means "the excursion is one bar
of noise" if the bar is a NORMAL bar.  If instead we systematically enter on bars
several times the instrument's usual range, then the finding is stronger and
different: we are entering into displacement, and the stop is set at a distance the
instrument covers in two or three minutes.

Control: the same symbol's M1 ranges over the 60 bars preceding the fill, expressed
in the SAME trade's R.  Matched on symbol, time of day and volatility regime by
construction.
"""
import gzip, json, pickle, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from f3_walk import load_symbol_series, log

TMP = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f3")
MONTHS = ["feb", "apr", "may", "jun", "jul"]


def main():
    rec = []
    for month in MONTHS:
        ser = load_symbol_series(month)
        trades = pickle.load(gzip.open(TMP / f"f3_trades_{month}.pkl.gz", "rb"))
        for t in trades:
            S = ser.get(t["sym"])
            if S is None:
                continue
            tm = S["t"]
            fi = int(np.searchsorted(tm, t["fill_min"], side="left"))
            if fi >= len(tm) or tm[fi] != t["fill_min"] or fi < 61:
                continue
            r = t["risk"]
            fill_rng = float(S["h"][fi] - S["l"][fi]) / r
            prior = (S["h"][fi - 60:fi] - S["l"][fi - 60:fi]) / r
            rec.append((t["month"], t["term_kind"], t["ot"], fill_rng,
                        float(np.median(prior)), float(prior.mean()),
                        float(t["term_gross"] - t["ded"]), float(t["mfe"])))
        log(stage="fillbar", month=month, n=len(rec))
    fr = np.array([x[3] for x in rec]); pm = np.array([x[4] for x in rec])
    term = np.array([x[1] for x in rec]); ot = np.array([x[2] for x in rec])
    net = np.array([x[6] for x in rec])
    ratio = fr / np.maximum(pm, 1e-12)
    out = {"schema": "gtos.f3.fillbar.v1", "n": len(rec),
           "median_fill_bar_range_R": float(np.median(fr)),
           "median_prior60_bar_range_R": float(np.median(pm)),
           "median_ratio_fillbar_to_prior60": float(np.median(ratio)),
           "mean_ratio": float(np.mean(ratio)),
           "stop_distance_in_normal_M1_bars": float(1.0 / np.median(pm)),
           "stop_distance_in_fill_bars": float(1.0 / np.median(fr)),
           "by_order_type": {o: dict(
               n=int((ot == o).sum()),
               median_fill_bar_range_R=float(np.median(fr[ot == o])),
               median_prior60_R=float(np.median(pm[ot == o])),
               median_ratio=float(np.median(ratio[ot == o]))) for o in sorted(set(ot))},
           "by_terminal": {k: dict(
               n=int((term == k).sum()),
               median_fill_bar_range_R=float(np.median(fr[term == k])),
               median_ratio=float(np.median(ratio[term == k]))) for k in sorted(set(term))}}
    q = np.quantile(ratio, np.linspace(0, 1, 6))
    out["net_R_by_fillbar_ratio_quintile"] = {}
    for a in range(5):
        hi = ratio <= q[a + 1] if a == 4 else ratio < q[a + 1]
        k = (ratio >= q[a]) & hi
        out["net_R_by_fillbar_ratio_quintile"][f"{q[a]:.2f}-{q[a+1]:.2f}"] = dict(
            n=int(k.sum()), mean_net_R=float(net[k].mean()))
    (HERE / "F3_FILLBAR.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
