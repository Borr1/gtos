#!/usr/bin/env python3
"""F3 (0) — THE NULL THAT EXPLAINS MOST OF IT, measured rather than asserted.

Before attributing a reversal to a level, an hour or a liquidity event, price the
hypothesis that there is nothing to attribute.

Optional stopping: if the price process carries no drift, then marking a position at
the instant it first touches +theta R is a FAIR mark, and whatever exit rule is
applied afterwards -- barrier, clock, anything not using the future -- the terminal
must average +theta R.  A driftless walk that has gone +1 R therefore gives back, on
average, exactly the +1 R it gained.  "It came back" is then not an event with a
cause; it is the absence of drift.

So the whole reversal question reduces to one measurable number per threshold:

    DRIFT_AFTER_TOUCH(theta) = E[terminal gross R | MFE >= theta] - theta

Zero means a fair game and no cause to find.  Negative means the pool is genuinely
adverse AFTER it has gone our way, which is a real effect that needs an explanation.

The same statistic is then cut by every candidate cause, which converts each one
from "is it associated with reversals" into "does it break the fair game".
"""
import gzip, json, pickle, sys
from collections import defaultdict
from pathlib import Path
import datetime as dt
import numpy as np

WT = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
sys.path.insert(0, str(WT))
from src.utils.broker_clock import NEW_YORK_PLUS_7, offset_seconds_at_utc

TMP = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f3")
OUT = Path(__file__).resolve().parent
MONTHS = ["feb", "apr", "may", "jun", "jul"]
EPOCH = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
R_USD = 250.0
THETAS = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5]


def boot_days(vals, days, n=4000, seed=31):
    """Day-block bootstrap of a mean (trades on one day are not independent)."""
    vals = np.asarray(vals, float); days = np.asarray(days)
    ud, inv = np.unique(days, return_inverse=True)
    idx = [np.nonzero(inv == i)[0] for i in range(len(ud))]
    rng = np.random.default_rng(seed)
    mu = []
    for _ in range(n):
        p = rng.integers(0, len(ud), len(ud))
        mu.append(vals[np.concatenate([idx[i] for i in p])].mean())
    mu = np.array(mu)
    return float(vals.mean()), [float(np.percentile(mu, 2.5)), float(np.percentile(mu, 97.5))], \
        float(2 * min((mu <= 0).mean(), (mu >= 0).mean()))


def main():
    trades = []
    for m in MONTHS:
        trades += pickle.load(gzip.open(TMP / f"f3_trades_{m}.pkl.gz", "rb"))
    g = np.array([t["term_gross"] for t in trades])
    mfe = np.array([t["mfe"] for t in trades])
    day = np.array([t["day"] for t in trades])
    ded = np.array([t["ded"] for t in trades])
    kind = np.array([t["term_kind"] for t in trades])
    fam = np.array([t["fam"] for t in trades])
    mo = np.array([t["month"] for t in trades])
    offc = {}

    def off(minute):
        d = int(minute) // 1440
        if d not in offc:
            offc[d] = offset_seconds_at_utc(EPOCH + dt.timedelta(minutes=d * 1440),
                                            NEW_YORK_PLUS_7) // 3600
        return offc[d]

    out = {"schema": "gtos.f3.null.v1", "n": len(trades), "R_usd": R_USD,
           "statistic": "E[terminal gross R | MFE >= theta] - theta; 0 == fair game",
           "why": "optional stopping makes the touch of +theta a fair mark under zero "
                  "drift, so any deviation is real adverse drift AFTER the excursion"}
    lad = {}
    for th in THETAS:
        m = mfe >= th
        d, c, p = boot_days(g[m] - th, day[m])
        lad[str(th)] = dict(
            n=int(m.sum()), share=float(m.mean()),
            mean_gross_after_touch=float(g[m].mean()),
            drift_after_touch_R=d, ci95_dayblock=c, p_two_sided=p,
            drift_after_touch_usd_per_trade=float(d * R_USD),
            total_drift_R=float(d * m.sum()), total_drift_usd=float(d * m.sum() * R_USD),
            mean_deductible_R=float(ded[m].mean()),
            terminal_mix={k: int((kind[m] == k).sum()) for k in sorted(set(kind))})
    out["drift_after_touch"] = lad

    # the fair-game bar for the barrier split, at each theta
    out["barrier_split_vs_driftless"] = {}
    for th in THETAS:
        m = mfe >= th
        res = m & ((kind == "TARGET") | (kind == "STOP"))
        if res.sum() < 100:
            continue
        obs = float((kind[res] == "TARGET").mean())
        out["barrier_split_vs_driftless"][str(th)] = dict(
            n_resolved=int(res.sum()), observed_target_share=obs,
            driftless_prediction=float((1.0 + th) / 3.0),
            note="driftless P(target first) from +theta with barriers at -1R and +2R "
                 "= (1+theta)/((2-theta)+(1+theta)); the horizon censors both barriers, "
                 "so read the DIRECTION, and drift_after_touch for the magnitude")

    # --- does any candidate cause BREAK the fair game? ------------------------
    th = 1.0
    m = mfe >= th
    sub = [t for t, k in zip(trades, m) if k]
    resid = g[m] - th
    dsub = day[m]
    out["fair_game_broken_by"] = {}

    def cut(name, mask):
        if mask.sum() < 200 or (~mask).sum() < 200:
            return
        a, ca, pa = boot_days(resid[mask], dsub[mask])
        b, cb, pb = boot_days(resid[~mask], dsub[~mask])
        out["fair_game_broken_by"][name] = dict(
            n_in=int(mask.sum()), drift_in_R=a, ci95_in=ca, p_in=pa,
            n_out=int((~mask).sum()), drift_out_R=b, ci95_out=cb,
            gap_R=float(a - b), gap_usd_per_trade=float((a - b) * R_USD))

    peakmin = np.array([t["peak_min"] for t in sub])
    bpk = np.array([(int(x) + off(x) * 60) % 1440 for x in peakmin])
    cut("peak_within_30min_of_broker_rollover", (bpk < 30) | (bpk >= 1410))
    cut("peak_in_broker_hour_00", bpk // 60 == 0)
    fill = np.array([t["fill_min"] for t in sub])
    term = np.array([t["term_min"] for t in sub])
    spans = np.array([((int(a) + off(a) * 60) // 1440) != ((int(b) + off(a) * 60) // 1440)
                      for a, b in zip(fill, term)])
    cut("trade_spans_the_rollover", spans)
    uh = (fill % 1440) // 60
    cut("entered_london_session_07_12_utc", (uh >= 7) & (uh < 12))
    cut("entered_ny_session_12_21_utc", (uh >= 12) & (uh < 21))
    cut("entered_asia_00_07_utc", uh < 7)
    ot = np.array([t["ot"] for t in sub])
    cut("order_type_MARKET", ot == "MARKET")
    side = np.array([str(t["side"]).upper() for t in sub])
    cut("side_LONG", side == "LONG")
    fast = np.array([t["peak_bars"] for t in sub])
    cut("peaked_within_5_minutes_of_fill", fast <= 5)
    cut("peaked_after_60_minutes", fast >= 60)
    out["fair_game_by_family"] = {}
    for f in sorted(set(fam[m])):
        k = fam[m] == f
        if k.sum() < 300:
            continue
        a, ca, pa = boot_days(resid[k], dsub[k])
        out["fair_game_by_family"][f] = dict(n=int(k.sum()), drift_R=a, ci95=ca, p=pa)
    out["fair_game_by_month"] = {}
    for f in MONTHS:
        k = mo[m] == f
        a, ca, pa = boot_days(resid[k], dsub[k])
        out["fair_game_by_month"][f] = dict(n=int(k.sum()), drift_R=a, ci95=ca, p=pa)
    (OUT / "F3_NULL.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out["drift_after_touch"], indent=1))
    print(json.dumps(out["fair_game_broken_by"], indent=1))


if __name__ == "__main__":
    main()
