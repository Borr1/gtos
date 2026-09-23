#!/usr/bin/env python3
"""F3 (3) — WHEN IN TIME.  Do reversals cluster at clock events?

Two denominators, because the naive one is wrong:
  EXPOSURE   peaks per 1,000 trade-minutes actually at risk in that hour.  A raw
             histogram of peak times mostly measures when the book is open.
  PAUSE      the same statistic for non-terminal stalls (the matched control):
             an advance that retraced and RESUMED.  This removes both exposure and
             "price moves more in some hours".

Clock events tested: broker rollover (broker hour 00, the 26.4x cost hour B10
measured), London open, NY open, NY cash open, the H4 bar boundaries the sleeves
decide on, the M15/H1 boundaries, and the weekend gap.
"""
import gzip, json, pickle
from collections import defaultdict
from pathlib import Path
import numpy as np
import datetime as dt
import sys

WT = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
sys.path.insert(0, str(WT))
from src.utils.broker_clock import NEW_YORK_PLUS_7, offset_seconds_at_utc

TMP = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f3")
OUT = Path(__file__).resolve().parent
MONTHS = ["feb", "apr", "may", "jun", "jul"]
EPOCH = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
H4_UTC_EDT = {1, 5, 9, 13, 17, 21}      # observed H4 stamps, US-summer
H4_UTC_EST = {2, 6, 10, 14, 18, 22}


def boff(minute):
    u = EPOCH + dt.timedelta(minutes=int(minute))
    return offset_seconds_at_utc(u, NEW_YORK_PLUS_7) // 3600


def ci_diff(a, b, seed=5, n=2000):
    a = np.asarray(a, float); b = np.asarray(b, float)
    rng = np.random.default_rng(seed)
    d = a.mean() - b.mean()
    ia = rng.integers(0, len(a), (n, len(a))); ib = rng.integers(0, len(b), (n, len(b)))
    mu = a[ia].mean(axis=1) - b[ib].mean(axis=1)
    return float(d), [float(np.percentile(mu, 2.5)), float(np.percentile(mu, 97.5))], \
        float(2 * min((mu <= 0).mean(), (mu >= 0).mean()))


def main():
    trades, stalls = [], []
    for m in MONTHS:
        trades += pickle.load(gzip.open(TMP / f"f3_trades_{m}.pkl.gz", "rb"))
        stalls += pickle.load(gzip.open(TMP / f"f3_stalls_{m}.pkl.gz", "rb"))
    offcache = {}

    def off(minute):
        d = int(minute) // 1440
        if d not in offcache:
            offcache[d] = boff(d * 1440)
        return offcache[d]

    # ---- exposure: trade-minutes at risk, by UTC and broker hour --------------
    expo_u = np.zeros(24); expo_b = np.zeros(24)
    for t in trades:
        a, b = int(t["fill_min"]), int(t["term_min"])
        if b <= a:
            b = a + 1
        mm = np.arange(a, min(b, a + 5000))
        o = off(a)
        np.add.at(expo_u, (mm % 1440) // 60, 1.0)
        np.add.at(expo_b, ((mm + o * 60) % 1440) // 60, 1.0)

    peaks = [s for s in stalls if s["kind"] == "peak"]
    pauses = [s for s in stalls if s["kind"] == "pause"]

    def hist(rows, mode):
        h = np.zeros(24)
        for s in rows:
            m = int(s["minute"])
            hh = ((m + off(m) * 60) % 1440) // 60 if mode == "broker" else (m % 1440) // 60
            h[hh] += 1
        return h

    out = {"schema": "gtos.f3.timing.v1", "n_peaks": len(peaks), "n_pauses": len(pauses),
           "note": "peaks per 1,000 trade-minutes of exposure; pause row is the matched control"}
    for mode, ex in (("utc", expo_u), ("broker", expo_b)):
        pk = hist(peaks, mode); pa = hist(pauses, mode)
        out[f"by_{mode}_hour"] = {
            str(h): dict(exposure_trade_minutes=float(ex[h]),
                         peaks=int(pk[h]), pauses=int(pa[h]),
                         peaks_per_1k_min=float(1000 * pk[h] / ex[h]) if ex[h] else None,
                         pauses_per_1k_min=float(1000 * pa[h] / ex[h]) if ex[h] else None,
                         peak_to_pause_ratio=float(pk[h] / pa[h]) if pa[h] else None)
            for h in range(24)}
        base = pk.sum() / pa.sum()
        out[f"by_{mode}_hour_excess"] = {
            str(h): float((pk[h] / pa[h]) / base) if pa[h] else None for h in range(24)}

    # ---- distance to clock events -------------------------------------------
    def event_flags(m):
        o = off(m)
        bm = (m + o * 60) % 1440
        um = m % 1440
        return dict(
            rollover_win=1.0 if (bm < 30 or bm >= 1410) else 0.0,      # +/-30 min of broker 00
            rollover_hour=1.0 if bm // 60 == 0 else 0.0,
            london_open=1.0 if 420 <= um < 450 else 0.0,               # 07:00-07:30 UTC
            ny_open=1.0 if 780 <= um < 810 else 0.0,                   # 13:00-13:30 UTC
            ny_cash=1.0 if 810 <= um < 840 else 0.0,                   # 13:30-14:00 UTC
            h4_edge=1.0 if (um // 60 in (H4_UTC_EDT if o == 3 else H4_UTC_EST)
                            and um % 60 < 15) else 0.0,
            h1_edge=1.0 if um % 60 < 5 else 0.0,
            m15_edge=1.0 if um % 15 == 0 else 0.0)

    keys = list(event_flags(0).keys())
    P = {k: [] for k in keys}; Q = {k: [] for k in keys}
    for s in peaks:
        f = event_flags(int(s["minute"]))
        for k in keys:
            P[k].append(f[k])
    for s in pauses:
        f = event_flags(int(s["minute"]))
        for k in keys:
            Q[k].append(f[k])
    out["clock_events"] = {}
    for k in keys:
        d, c, p = ci_diff(P[k], Q[k])
        out["clock_events"][k] = dict(peak_rate=float(np.mean(P[k])),
                                      pause_rate=float(np.mean(Q[k])),
                                      diff=d, ci95=c, p_two_sided=p,
                                      lift=float(np.mean(P[k]) / np.mean(Q[k]))
                                      if np.mean(Q[k]) else None)

    # ---- economics by hour of ENTRY (knowable ex ante) -----------------------
    net = np.array([t["term_gross"] - t["ded"] for t in trades])
    gb = np.array([t["give_back"] for t in trades])
    mfe = np.array([t["mfe"] for t in trades])
    fh = np.array([(int(t["fill_min"]) + off(t["fill_min"]) * 60) % 1440 // 60 for t in trades])
    uh = np.array([(int(t["fill_min"]) % 1440) // 60 for t in trades])
    out["by_entry_broker_hour"] = {
        str(h): dict(n=int((fh == h).sum()), mean_net_R=float(net[fh == h].mean()),
                     mean_give_back_R=float(gb[fh == h].mean()),
                     reversal_rate=float(((mfe >= 1.0) & (net < 0))[fh == h].mean()))
        for h in range(24) if (fh == h).sum() > 50}
    out["by_entry_utc_hour"] = {
        str(h): dict(n=int((uh == h).sum()), mean_net_R=float(net[uh == h].mean()),
                     mean_give_back_R=float(gb[uh == h].mean()),
                     reversal_rate=float(((mfe >= 1.0) & (net < 0))[uh == h].mean()))
        for h in range(24) if (uh == h).sum() > 50}

    # ---- did the trade SPAN the rollover? (knowable only in expectation) -----
    span = []
    for t in trades:
        a, b = int(t["fill_min"]), int(t["term_min"])
        o = off(a)
        ba, bb = a + o * 60, b + o * 60
        span.append(1.0 if (ba // 1440) != (bb // 1440) else 0.0)
    span = np.array(span)
    out["rollover_spanning_trades"] = dict(
        n=int(span.sum()), share=float(span.mean()),
        mean_net_R_spanning=float(net[span == 1].mean()),
        mean_net_R_not=float(net[span == 0].mean()),
        mean_give_back_spanning=float(gb[span == 1].mean()),
        mean_give_back_not=float(gb[span == 0].mean()))
    d, c, p = ci_diff(net[span == 1], net[span == 0])
    out["rollover_spanning_trades"].update(net_diff=d, net_ci95=c, net_p=p)
    (OUT / "F3_TIMING.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out["clock_events"], indent=1))


if __name__ == "__main__":
    main()
