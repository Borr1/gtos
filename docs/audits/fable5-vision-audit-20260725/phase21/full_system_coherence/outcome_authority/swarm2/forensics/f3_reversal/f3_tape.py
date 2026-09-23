#!/usr/bin/env python3
"""F3 (3) — WHAT IN THE TAPE, 2026-06-18..07-24 only, where ticks exist.

BOUNDARY, stated up front: the archive is QUOTE-ONLY.  Verified by direct scan of
300,000 rows of FTMO_EURUSD: `last`, `volume` and `volume_real` are zero on every
row; only `flags` is populated.  There is no traded volume and no trade direction
in this data at any effort, so true order flow (aggressor side, trade size,
imbalance) is NOT recoverable.  What IS measurable is the quote process: spread,
quote intensity (ticks per minute), and quote-range.

Normalisation matters here.  B10 measured a 34x spread spike at broker hour 00 and
a DST smear that has already cost two lanes: comparing a raw spread at a reversal
against a pooled average mostly measures what hour it was.  Every tape quantity is
therefore divided by the SAME SYMBOL's median for the SAME broker hour, and the
control is the matched within-trade pause.
"""
import gzip, json, pickle, sys
from collections import defaultdict
from pathlib import Path
import datetime as dt
import numpy as np

TMP = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f3")
MIN = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/minute")
OUT = Path(__file__).resolve().parent
EPOCH = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
EPOFF = int(EPOCH.timestamp()) // 60          # walker-minutes -> UTC epoch minutes
BOFF = 3                                       # NY on EDT for the whole tick window
LAGS = [-10, -5, -2, -1, 0, 1, 2, 5]


def load_tape():
    tape = {}
    for p in sorted(MIN.glob("FTMO_*.npz")):
        d = np.load(p, allow_pickle=True)
        sym = str(d["symbol"])
        m = d["minute_utc"].astype(np.int64)
        n = d["n"].astype(float)
        sp = np.where(n > 0, d["sp_sum"] / np.maximum(n, 1), np.nan)
        spmax = d["sp_max"].astype(float)
        rng = (d["ask_hi"] - d["bid_lo"]).astype(float)
        hr = ((m + BOFF * 60) % 1440) // 60
        # per-symbol, per-broker-hour medians
        med_sp = np.full(24, np.nan); med_n = np.full(24, np.nan); med_r = np.full(24, np.nan)
        for h in range(24):
            k = hr == h
            if k.sum() > 20:
                med_sp[h] = np.nanmedian(sp[k]); med_n[h] = np.nanmedian(n[k])
                med_r[h] = np.nanmedian(rng[k])
        tape[sym] = dict(m=m, sp=sp, n=n, spmax=spmax, rng=rng, hr=hr,
                         med_sp=med_sp, med_n=med_n, med_r=med_r)
    return tape


def main():
    tape = load_tape()
    print(json.dumps({"stage": "tape", "symbols": len(tape)}), flush=True)
    stalls = []
    for mo in ["jun", "jul"]:
        stalls += pickle.load(gzip.open(TMP / f"f3_stalls_{mo}.pkl.gz", "rb"))
    lo, hi = 29695506, 29748774                # archive coverage, UTC epoch minutes
    byk = defaultdict(lambda: ([], []))
    rows = 0
    per = {L: defaultdict(lambda: ([], [])) for L in LAGS}
    for s in stalls:
        T = tape.get(s["sym"])
        if T is None:
            continue
        mu = int(s["minute"]) + EPOFF
        if not (lo <= mu <= hi):
            continue
        j = int(np.searchsorted(T["m"], mu))
        if j >= len(T["m"]) or T["m"][j] != mu:
            continue
        h = T["hr"][j]
        if not (T["med_sp"][h] > 0):
            continue
        i = 0 if s["kind"] == "peak" else 1
        rows += 1
        byk[s["k"]][i].append((T["sp"][j] / T["med_sp"][h],
                               T["n"][j] / max(T["med_n"][h], 1e-9),
                               T["rng"][j] / max(T["med_r"][h], 1e-9),
                               T["spmax"][j] / T["med_sp"][h]))
        for L in LAGS:
            jj = int(np.searchsorted(T["m"], mu + L))
            if jj < len(T["m"]) and T["m"][jj] == mu + L:
                hh = T["hr"][jj]
                if T["med_sp"][hh] > 0:
                    per[L][s["k"]][i].append((T["sp"][jj] / T["med_sp"][hh],
                                              T["n"][jj] / max(T["med_n"][hh], 1e-9)))

    def paired(sel):
        dif = []
        pk, pa = [], []
        for k, (P, Q) in byk.items():
            if not P or not Q:
                continue
            a = np.mean([x[sel] for x in P]); b = np.mean([x[sel] for x in Q])
            dif.append(a - b); pk.append(a); pa.append(b)
        dif = np.array(dif)
        rng = np.random.default_rng(21)
        mu = dif[rng.integers(0, len(dif), (2000, len(dif)))].mean(axis=1)
        return dict(n_trades=len(dif), peak=float(np.mean(pk)), pause=float(np.mean(pa)),
                    diff=float(dif.mean()),
                    ci95=[float(np.percentile(mu, 2.5)), float(np.percentile(mu, 97.5))],
                    p_two_sided=float(2 * min((mu <= 0).mean(), (mu >= 0).mean())))

    out = {"schema": "gtos.f3.tape.v1",
           "boundary": "QUOTE-ONLY archive: last/volume/volume_real are zero on every "
                       "row (verified by scan of 300,000 FTMO_EURUSD rows); true order "
                       "flow is not recoverable at any effort",
           "window": "2026-06-18..2026-07-24 (tick archive coverage)",
           "normalisation": "each quantity / same symbol's median for the same broker hour",
           "n_stalls_matched": rows, "n_symbols": len(tape),
           "spread_at_stall": paired(0), "quote_intensity_at_stall": paired(1),
           "quote_range_at_stall": paired(2), "max_spread_at_stall": paired(3)}
    traj = {}
    for L in LAGS:
        P = [x for k, (a, b) in per[L].items() for x in a] if False else None
        pk = [x for kk in ("peak",) for x in per[L][kk][0]]
        pa = [x for kk in ("pause",) for x in per[L][kk][1]]
        if len(pk) < 50 or len(pa) < 50:
            continue
        traj[str(L)] = dict(
            n_peak=len(pk), n_pause=len(pa),
            spread_peak=float(np.mean([x[0] for x in pk])),
            spread_pause=float(np.mean([x[0] for x in pa])),
            intensity_peak=float(np.mean([x[1] for x in pk])),
            intensity_pause=float(np.mean([x[1] for x in pa])))
    out["trajectory_minutes_around_stall"] = traj
    (OUT / "F3_TAPE.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("n_stalls_matched", "spread_at_stall",
                                          "quote_intensity_at_stall")}, indent=1))


if __name__ == "__main__":
    main()
