"""m2_tickwalk — walk `structural_distance_extreme` on REAL bid/ask ticks.

The family is AT-MARKET by construction: `broader_origin_generators.py:889` and `:907`
set `entry=bar.close`, and the decision instant IS that bar's close, so there is no
resting order, no fill classification and no order-type inference. The order-type
argument that runs through d5/p3 does not apply to this family at all.

THE JOIN IS PROVED, NOT ASSUMED
-------------------------------
`bid(last tick strictly before T) == roster entry price` on 100.00 % of rows (see
M2_JOIN_V1.json). So the decision instant, the clock and the BID identity are all
verified on this family's own rows before any economics is taken.

ENTRY ANCHOR
------------
Primary = r1's canonical convention (`walkforward/quote_side.py`): the trader transacts
at the quote standing at the decision instant, i.e. `fill = ask0` (LONG) / `bid0` (SHORT)
where (bid0, ask0) is the LAST tick before T. This isolates the quote-side correction
from session-gap noise and is exactly comparable to every other wave-20 number.
Secondary = `next_tick`: the price of the first tick at or after T (what a market order
sent at T would actually have got, including the reopen after a session break). Reported
with a tradability flag because at T + 35 min the market was shut, not slipping.

ARMS, all on the same rows and the same instants
------------------------------------------------
  bar     the estate's own walk: bid M1 bars, entry at the emitted level, stop/target
          unshifted, first touch by bar, stop wins a same-bar tie.
  tbid    tick resolution, BID for every leg, entry at the level (isolates intrabar
          ordering from quote side).
  fill    MT5 truth, FILL-anchored (the live book, order_router.py:66-73): SL/TP re-hung
          off the transacted price at the emitted risk distance; LONG exits trigger on
          the BID, SHORT on the ASK; first touch by tick order; stop wins ties.
  lvl     MT5 truth, LEVEL-anchored (the generator's emitted absolute prices kept); same
          trigger sides; R measured from the transacted price.
"""
from __future__ import annotations

import datetime as dt
import glob
import gzip
import json
import os
import sys
from pathlib import Path

import numpy as np

CACHE = "/tmp/m2/tickcache"
M1 = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
          "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
ROSTER = {"202510": "/tmp/f1/roster_202510", "202511": "/tmp/f1/roster_202511",
          "202512": "/tmp/f1/roster_202512", "202601": "/tmp/pbg_full_jan",
          "202602": "/tmp/pbg_full_feb", "202603": "/tmp/pbg_full_mar",
          "202604": "/tmp/f1/roster_202604", "202605": "/tmp/f1/roster_202605"}
NEXT = {"202510": "202511", "202511": "202512", "202512": "202601", "202601": "202602",
        "202602": "202603", "202603": "202604", "202604": "202605"}
FAM = "structural_distance_extreme"
EPOCH = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
BIG = 1 << 62
TARGETS = (1.5, 2.0)
HORIZONS = (120, 240, 1440)


def load_ticks(sym, months):
    ts, bd, ak = [], [], []
    for m in months:
        p = f"{CACHE}/{sym}_{m}.npz"
        if not os.path.isfile(p):
            continue
        z = np.load(p)
        ts.append(z["ts"]); bd.append(z["bid"]); ak.append(z["ask"])
    if not ts:
        return None
    T = np.concatenate(ts); B = np.concatenate(bd); A = np.concatenate(ak)
    o = np.argsort(T, kind="stable")
    return T[o], B[o], A[o]


def load_m1(sym, months):
    y, m = int(months[0][:4]), int(months[0][4:])
    t0 = dt.datetime(y, m, 1, tzinfo=dt.timezone.utc)
    y2, m2 = int(months[-1][:4]), int(months[-1][4:])
    y3, m3 = (y2 + 1, 1) if m2 == 12 else (y2, m2 + 1)
    n = int((dt.datetime(y3, m3, 1, tzinfo=dt.timezone.utc) - t0).total_seconds() // 60)
    H = np.full(n, np.nan); L = np.full(n, np.nan); C = np.full(n, np.nan)
    import csv
    for mm in months:
        p = M1 / f"bridge_ftmo_m1_{mm}" / f"{sym}_M1.csv"
        if not p.is_file():
            continue
        with p.open() as fh:
            for r in csv.DictReader(fh):
                k = int((dt.datetime.fromisoformat(r["time"]) - t0).total_seconds() // 60)
                if 0 <= k < n:
                    H[k] = float(r["high"]); L[k] = float(r["low"]); C[k] = float(r["close"])
    return t0, n, H, L, C


def bar_walk(H, L, C, i0, i1, lng, sl, tp):
    hs = (L[i0:i1] <= sl) if lng else (H[i0:i1] >= sl)
    ht = (H[i0:i1] >= tp) if lng else (L[i0:i1] <= tp)
    a_s = int(np.argmax(hs)) if hs.any() else BIG
    a_t = int(np.argmax(ht)) if ht.any() else BIG
    if a_s == BIG and a_t == BIG:
        v = C[i0:i1]
        v = v[~np.isnan(v)]
        if not len(v):
            return None
        return float(v[-1]), 2
    if a_s <= a_t:
        return sl, 0
    return tp, 1


def tick_walk(ts, bd, ak, j0, t0ms, horizon_ms, lng, sl, tp, one_sided=False):
    i1 = int(np.searchsorted(ts, t0ms + horizon_ms, "left"))
    if i1 - j0 < 1:
        return None
    ex = bd[j0:i1] if (one_sided or lng) else ak[j0:i1]
    hs = (ex <= sl) if lng else (ex >= sl)
    ht = (ex >= tp) if lng else (ex <= tp)
    a_s = int(np.argmax(hs)) if hs.any() else BIG
    a_t = int(np.argmax(ht)) if ht.any() else BIG
    if a_s == BIG and a_t == BIG:
        return float(ex[-1]), 2, int(ts[i1 - 1] - t0ms)
    if a_s <= a_t:
        return sl, 0, int(ts[j0 + a_s] - t0ms)
    return tp, 1, int(ts[j0 + a_t] - t0ms)


def main(sym, month, out):
    months = [month] + ([NEXT[month]] if NEXT.get(month) else [])
    tk = load_ticks(sym, months)
    if tk is None:
        sys.stderr.write(f"no ticks {sym} {month}\n"); return
    ts, bd, ak = tk
    t0, n, H, L, C = load_m1(sym, months)
    tlast = int(ts[-1])
    max_hor = max(HORIZONS) * 60_000

    rows = []
    for f in sorted(glob.glob(ROSTER[month] + "/*.jsonl.gz")):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                if '"structural_distance_extreme"' not in line:
                    continue
                r = json.loads(line)
                if r["f"] == FAM and r["k"] == 15 and r["s"] == sym:
                    rows.append(r)

    out_rows = []
    drops = {"tick_horizon_short": 0, "no_bar_index": 0, "bad_d": 0, "no_prev_tick": 0,
             "entry_join_mismatch": 0}
    join_exact = 0
    for r in rows:
        T = dt.datetime.fromisoformat(r["t"])
        tms = int((T - EPOCH).total_seconds()) * 1000
        i = int((T - t0).total_seconds() // 60)
        if not (0 < i < n - 2):
            drops["no_bar_index"] += 1
            continue
        e = float(r["e"]); slv = float(r["sl"])
        d = abs(e - slv)
        if not (d > 0):
            drops["bad_d"] += 1
            continue
        lng = r["d"] == "L"
        s = 1.0 if lng else -1.0

        j = int(np.searchsorted(ts, tms, "left"))     # first tick at/after T
        if j == 0:
            drops["no_prev_tick"] += 1
            continue
        b0 = float(bd[j - 1]); a0 = float(ak[j - 1])  # the quote standing AT T
        join_exact += int(abs(b0 - e) < 1e-9)
        spread = a0 - b0
        fill = a0 if lng else b0
        nxt_gap_s = (int(ts[j]) - tms) / 1000.0 if j < len(ts) else None
        fill_next = (float(ak[j]) if lng else float(bd[j])) if j < len(ts) else None

        rec = {
            "sym": sym, "mm": month, "t": r["t"], "day": r["t"][:10], "long": lng,
            "e": e, "sl": slv, "d": d, "d_bps": d / e * 1e4,
            "bid0": b0, "ask0": a0, "spread": spread, "spread_bps": spread / e * 1e4,
            "spread_over_d": spread / d, "fill": fill, "fill_next": fill_next,
            "next_gap_s": nxt_gap_s, "join_exact": bool(abs(b0 - e) < 1e-9),
            "tick_cov_min": (tlast - tms) / 60000.0,
        }
        for tr in TARGETS:
            tp = e + s * tr * d
            tp_f = fill + s * tr * d
            for hm in HORIZONS:
                key = f"{tr:g}_{hm}"
                if tms + hm * 60_000 > tlast:
                    rec[f"bar_{key}"] = rec[f"tbid_{key}"] = None
                    rec[f"fill_{key}"] = rec[f"lvl_{key}"] = None
                    rec[f"code_{key}"] = rec[f"hold_{key}"] = None
                    continue
                bw = bar_walk(H, L, C, i, min(i + hm, n), lng, slv, tp)
                rec[f"bar_{key}"] = None if bw is None else s * (bw[0] - e) / d
                rec[f"barcode_{key}"] = None if bw is None else bw[1]
                tb = tick_walk(ts, bd, ak, j, tms, hm * 60_000, lng, slv, tp, one_sided=True)
                rec[f"tbid_{key}"] = None if tb is None else s * (tb[0] - e) / d
                tf = tick_walk(ts, bd, ak, j, tms, hm * 60_000, lng, fill - s * d, tp_f)
                rec[f"fill_{key}"] = None if tf is None else s * (tf[0] - fill) / d
                rec[f"code_{key}"] = None if tf is None else tf[1]
                rec[f"hold_{key}"] = None if tf is None else tf[2]
                tl = tick_walk(ts, bd, ak, j, tms, hm * 60_000, lng, slv, tp)
                rec[f"lvl_{key}"] = None if tl is None else s * (tl[0] - fill) / d
                rec[f"lvlcode_{key}"] = None if tl is None else tl[1]
                # EXACT SIDE MIRROR: same instant, same |risk|, opposite direction, same
                # MT5 trigger sides and the same fill-anchoring. Isolates the direction
                # call from the toll -- if the mirror books the same number, the family's
                # loss is entirely the cost of transacting, not a wrong call.
                mlng = not lng
                ms_ = -s
                mfill = a0 if mlng else b0
                mtf = tick_walk(ts, bd, ak, j, tms, hm * 60_000, mlng,
                                mfill - ms_ * d, mfill + ms_ * tr * d)
                rec[f"mir_{key}"] = None if mtf is None else ms_ * (mtf[0] - mfill) / d
                mtb = tick_walk(ts, bd, ak, j, tms, hm * 60_000, mlng,
                                e - ms_ * d, e + ms_ * tr * d, one_sided=True)
                rec[f"mirbar_{key}"] = None if mtb is None else ms_ * (mtb[0] - e) / d
        # unconditional price capture (the SIGNAL, no exit rule).  Three units:
        #   cap_      transacted: entry on the fill side, exit on the exit-quote side.
        #             This IS net of the round-trip spread.
        #   capg_     one-sided BID tape both legs -- d3's own convention, so the
        #             accumulation curve is comparable to the published one.
        #   capm_     mid-to-mid, the neutral reference.
        mid0 = 0.5 * (b0 + a0)
        for hh, mins in (("15m", 15), ("2h", 120), ("8h", 480), ("24h", 1440),
                         ("72h", 4320), ("160h", 9600), ("320h", 19200)):
            if tms + mins * 60_000 > tlast:
                rec[f"cap_{hh}"] = rec[f"capg_{hh}"] = rec[f"capm_{hh}"] = None
                continue
            k = int(np.searchsorted(ts, tms + mins * 60_000, "left")) - 1
            if k < j:
                rec[f"cap_{hh}"] = rec[f"capg_{hh}"] = rec[f"capm_{hh}"] = None
            else:
                px = float(bd[k]) if lng else float(ak[k])
                rec[f"cap_{hh}"] = s * (px - fill) / fill * 1e4
                rec[f"capg_{hh}"] = s * (float(bd[k]) - b0) / b0 * 1e4
                mk = 0.5 * (float(bd[k]) + float(ak[k]))
                rec[f"capm_{hh}"] = s * (mk - mid0) / mid0 * 1e4
        out_rows.append(rec)

    Path(out).write_text(json.dumps({
        "symbol": sym, "month": month, "targets": TARGETS, "horizons": HORIZONS,
        "n_roster": len(rows), "n_walked": len(out_rows), "drops": drops,
        "join_exact_frac": join_exact / max(len(out_rows), 1),
        "tick_last_utc": dt.datetime.fromtimestamp(tlast / 1000, dt.timezone.utc).isoformat(),
        "rows": out_rows}))
    sys.stderr.write(f"{sym} {month}: roster {len(rows)} walked {len(out_rows)} "
                     f"join_exact {join_exact}/{len(out_rows)} drops {drops}\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
