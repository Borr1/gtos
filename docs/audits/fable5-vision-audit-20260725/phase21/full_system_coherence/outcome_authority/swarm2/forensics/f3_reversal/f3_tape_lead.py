#!/usr/bin/env python3
"""F3 (3b) — the tape AROUND the turn: is there a signature BEFORE it?

A spread widening or an intensity spike measured AT the reversal minute is not
actionable: by then the trade has already topped.  The question that matters is
whether the tape moves first.  This walks -15..+15 minutes around every stall and
reports peaks against the matched within-trade pauses at each offset.
"""
import gzip, json, pickle
from collections import defaultdict
from pathlib import Path
import datetime as dt
import numpy as np

TMP = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f3")
MIN = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/minute")
OUT = Path(__file__).resolve().parent
EPOFF = int(dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc).timestamp()) // 60
BOFF = 3
LAGS = list(range(-15, 16))


def main():
    tape = {}
    for p in sorted(MIN.glob("FTMO_*.npz")):
        d = np.load(p, allow_pickle=True)
        m = d["minute_utc"].astype(np.int64)
        n = d["n"].astype(float)
        sp = np.where(n > 0, d["sp_sum"] / np.maximum(n, 1), np.nan)
        hr = ((m + BOFF * 60) % 1440) // 60
        msp = np.full(24, np.nan); mn = np.full(24, np.nan)
        for h in range(24):
            k = hr == h
            if k.sum() > 20:
                msp[h] = np.nanmedian(sp[k]); mn[h] = np.nanmedian(n[k])
        pos = {int(v): i for i, v in enumerate(m)}
        tape[str(d["symbol"])] = dict(pos=pos, sp=sp, n=n, hr=hr, msp=msp, mn=mn)
    stalls = []
    for mo in ["jun", "jul"]:
        stalls += pickle.load(gzip.open(TMP / f"f3_stalls_{mo}.pkl.gz", "rb"))
    acc = {L: {"peak": [[], []], "pause": [[], []]} for L in LAGS}
    matched = 0
    for s in stalls:
        T = tape.get(s["sym"])
        if T is None:
            continue
        mu = int(s["minute"]) + EPOFF
        if mu not in T["pos"]:
            continue
        matched += 1
        for L in LAGS:
            j = T["pos"].get(mu + L)
            if j is None:
                continue
            h = T["hr"][j]
            if not (T["msp"][h] > 0):
                continue
            acc[L][s["kind"]][0].append(T["sp"][j] / T["msp"][h])
            acc[L][s["kind"]][1].append(T["n"][j] / max(T["mn"][h], 1e-9))
    out = {"schema": "gtos.f3.tape_lead.v1", "n_stalls_matched": matched,
           "normalisation": "value / same symbol's median for the same broker hour",
           "boundary": "quote-only archive; no traded volume exists in this data",
           "by_offset_minutes": {}}
    for L in LAGS:
        a = acc[L]
        if len(a["peak"][0]) < 200 or len(a["pause"][0]) < 200:
            continue
        out["by_offset_minutes"][str(L)] = dict(
            n_peak=len(a["peak"][0]), n_pause=len(a["pause"][0]),
            spread_peak=float(np.nanmean(a["peak"][0])),
            spread_pause=float(np.nanmean(a["pause"][0])),
            spread_ratio=float(np.nanmean(a["peak"][0]) / np.nanmean(a["pause"][0])),
            intensity_peak=float(np.nanmean(a["peak"][1])),
            intensity_pause=float(np.nanmean(a["pause"][1])),
            intensity_ratio=float(np.nanmean(a["peak"][1]) / np.nanmean(a["pause"][1])))
    (OUT / "F3_TAPE_LEAD.json").write_text(json.dumps(out, indent=1))
    for L in LAGS:
        r = out["by_offset_minutes"].get(str(L))
        if r:
            print(f"{L:+3d} spread pk={r['spread_peak']:.4f} pa={r['spread_pause']:.4f} "
                  f"ratio={r['spread_ratio']:.4f} | intens pk={r['intensity_peak']:.4f} "
                  f"pa={r['intensity_pause']:.4f} ratio={r['intensity_ratio']:.4f}")


if __name__ == "__main__":
    main()
