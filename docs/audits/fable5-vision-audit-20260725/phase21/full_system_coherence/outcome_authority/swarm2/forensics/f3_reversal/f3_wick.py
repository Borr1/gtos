#!/usr/bin/env python3
"""F3 (0b) — is the residual adverse drift REAL, or is it the wick?

`drift_after_touch` is built on MFE, and MFE is the bar HIGH (long) / LOW (short).
A high is a maximum over the minute; it can be one tick.  Touching +1 R on a wick is
not the same as being able to SELL at +1 R, so part of the -0.088 R deficit may be a
measurement convention rather than an adverse market.

This re-walks the identical population and recomputes the same statistic with the
excursion defined on the bar CLOSE -- a level the position could actually have been
exited at with a resting order or a bar-close rule.  If the deficit collapses, the
"bank at +1 R" prize is an artifact and no exit rule can collect it.  If it survives,
it is real money and it is collectable.
"""
import csv, gzip, json, os, pickle, sys, time
import datetime as dt
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from f3_walk import (BARS, CACHE, GEOM, MONTH_SRC, at, load_symbol_series, log, mins)

TMP = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f3")
OUT = Path(__file__).resolve().parent
MONTHS = ["feb", "apr", "may", "jun", "jul"]
THETAS = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5]
R_USD = 250.0


def walk(month):
    ser = load_symbol_series(month)
    geom = {}
    with gzip.open(GEOM / f"geom_{month}.jsonl.gz", "rt") as fh:
        for line in fh:
            r = json.loads(line)
            geom[r["k"]] = r
    keep = {t["k"]: t for t in pickle.load(gzip.open(TMP / f"f3_trades_{month}.pkl.gz", "rb"))}
    out = []
    for k, t in keep.items():
        g = geom[k]
        S = ser.get(t["sym"])
        if S is None:
            continue
        d = 1 if str(t["side"]).upper() == "LONG" else -1
        tm = S["t"]
        i0 = int(np.searchsorted(tm, t["fill_min"], side="left"))
        # side="left": include every bar strictly BEFORE the terminal minute.  A
        # TIME_STOP marks at TT[j]+1 and an intrabar barrier at TT[j]+1, so both keep
        # their own bar; only an open-gap terminal loses its bar, which is the bar the
        # trade ended ON.  The `mfe_high_vs_stored_max_abs_dev` receipt below is what
        # proves the window matches the validated walker rather than asserting it.
        i1 = int(np.searchsorted(tm, t["term_min"], side="left"))
        if i1 <= i0 or tm[i0] != t["fill_min"]:
            continue
        eoff = S["s"][i0:i1] if d < 0 else 0.0
        C = S["c"][i0:i1] + eoff
        H = (S["h"][i0:i1] + eoff) if d > 0 else (S["l"][i0:i1] + eoff)
        fp, risk = t["fp"], t["risk"]
        favc = (C - fp) * d / risk
        favh = (H - fp) * d / risk
        # For the CLOSE arm the mark is the CLOSE AT FIRST CROSSING, which OVERSHOOTS
        # theta.  Benchmarking it against theta would credit the overshoot as drift --
        # the exact class of error this lane exists to catch.  The WICK arm needs no
        # such correction: price is continuous, so the first touch of theta is AT theta,
        # which is also what a resting take-profit limit at +theta would fill at.
        marks = []
        for th in THETAS:
            j = np.nonzero(favc >= th)[0]
            marks.append(float(favc[j[0]]) if len(j) else np.nan)
        out.append((k, t["month"], t["day"], float(favc.max()), float(favh.max()),
                    float(t["term_gross"]), float(t["mfe"]), marks))
    log(stage="wick_month", month=month, n=len(out))
    return out


def boot_days(vals, days, n=3000, seed=41):
    vals = np.asarray(vals, float)
    ud, inv = np.unique(np.asarray(days), return_inverse=True)
    idx = [np.nonzero(inv == i)[0] for i in range(len(ud))]
    rng = np.random.default_rng(seed)
    mu = np.array([vals[np.concatenate([idx[i] for i in rng.integers(0, len(ud), len(ud))])].mean()
                   for _ in range(n)])
    return float(vals.mean()), [float(np.percentile(mu, 2.5)), float(np.percentile(mu, 97.5))], \
        float(2 * min((mu <= 0).mean(), (mu >= 0).mean()))


def main():
    rows = []
    for m in MONTHS:
        rows += walk(m)
    mfc = np.array([r[3] for r in rows]); mfh = np.array([r[4] for r in rows])
    gr = np.array([r[5] for r in rows]); day = np.array([r[2] for r in rows])
    chk = np.array([r[6] for r in rows])
    out = {"schema": "gtos.f3.wick.v1", "n": len(rows),
           "mfe_high_vs_stored_max_abs_dev": float(np.max(np.abs(mfh - chk))),
           "question": "does the adverse drift after a favourable excursion survive when "
                       "the excursion is defined on a transactable bar CLOSE instead of "
                       "the bar high/low wick?",
           "ladder": {}}
    marks = np.array([r[7] for r in rows], dtype=float)
    for ti, th in enumerate(THETAS):
        a = mfc >= th; b = mfh >= th
        da, ca, pa = boot_days(gr[a] - marks[a, ti], day[a])       # vs the ACTUAL mark
        dnaive, _, _ = boot_days(gr[a] - th, day[a], n=200)        # the biased version
        db, cb, pb = boot_days(gr[b] - th, day[b])
        out["ladder"][str(th)] = dict(
            close_based=dict(n=int(a.sum()), mean_mark_R=float(np.nanmean(marks[a, ti])),
                             overshoot_R=float(np.nanmean(marks[a, ti]) - th),
                             drift_vs_actual_mark_R=da, ci95=ca, p=pa,
                             drift_vs_theta_R_BIASED=dnaive,
                             total_R=float(da * a.sum()), total_usd=float(da * a.sum() * R_USD)),
            wick_based=dict(n=int(b.sum()), drift_R=db, ci95=cb, p=pb,
                            total_R=float(db * b.sum()), total_usd=float(db * b.sum() * R_USD)),
            share_of_wick_deficit_surviving_on_closes=float(da / db) if db else None)
    (OUT / "F3_WICK.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
