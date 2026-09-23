"""d1_walk — one window: walk EVERY roster emission under BOTH sides, under one
identical contract, and dump compact per-row arrays.

Why both sides: the R-frames are linear in side.  For a fixed entry e and risk
distance d, the long frame is (px-e)/d and the short frame is -(px-e)/d, with
high/low swapping roles.  So walking once "as long" and once "as short" gives
the exact outcome of ANY side assignment on that row by a select --- which makes
every direction control (matched-random, shuffled) exact rather than sampled,
and makes the coin-flip expectation a closed form: (g_long + g_short) / 2.

Contract (identical for real and every control):
  fill      at-market families  -> market fill at the generator's OWN emitted entry
                                   price e (PB: equals the last M1 close strictly
                                   before the decision instant, 0.0 rel. error).
            POI families        -> honest resting limit at e; buy fills when
                                   low<=e, sell when high>=e, scanned over stamps
                                   i..i+H-1; never touched -> 0.0 R, 0 cost.
            CONTROL ARMS REUSE THE REAL ARM'S FILL EVENT (same fill, same minute)
            so the control isolates DIRECTION and nothing else.
  exit      stop -1R, target +T R, else last close of the forward path.
            Forward path = stamps i+j+1 .. i+H  (j = fill offset; 0 at market).
            Tie inside one M1 bar -> the STOP wins.
  toll      h1 four-term broker-true (hour-aware tick spread + broker-true
            commission + measured price-unit slippage + swap), price units / d.
            Charged only on filled rows.  Computed for BOTH sides (swap is the
            only side-dependent term).

Outputs /tmp/d1/out/D1_<window>.npz
"""
from __future__ import annotations

import glob
import gzip
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
DISC = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
sys.path.insert(0, PBG)
sys.path.insert(0, REPO)
os.chdir(REPO)
import pbg_lib as L  # noqa: E402
import pbg_econ as E  # noqa: E402

HOR = 120
POI = ("current_fvg_fill", "current_ob_retest", "current_breaker_re_entry")
NEXT = {"2025-10": "202511", "2025-11": "202512", "2025-12": "202601", "2026-01": "202602",
        "2026-02": "202603", "2026-03": "202604", "2026-04": "202605", "2026-05": None}
SRC = {"2025-10": "/tmp/f1/roster_202510", "2025-11": "/tmp/f1/roster_202511",
       "2025-12": "/tmp/f1/roster_202512", "2026-01": "/tmp/pbg_full_jan",
       "2026-02": "/tmp/pbg_full_feb", "2026-03": "/tmp/pbg_full_mar",
       "2026-04": "/tmp/f1/roster_202604", "2026-05": "/tmp/f1/roster_202605"}
ARM_DAYS = json.load(open(DISC + "/f1_ARM_TRADING_DAYS_V1.json"))


def setup_key(r):
    if r["f"].startswith("current_"):
        return (r["s"], r["f"], r["d"], r["b"], r["cid"])
    return (r["s"], r["f"], r["d"], r["b"])


def load_rows(indir, days):
    seen = {}
    for p in sorted(glob.glob(os.path.join(indir, "pbg_*.jsonl.gz"))):
        with gzip.open(p, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if r["k"] != 15:
                    continue
                if r["t"][:10] not in days:
                    continue
                k = setup_key(r)
                if k not in seen:
                    seen[k] = r
    return list(seen.values())


def first_true(mask):
    return mask.any(axis=1), np.argmax(mask, axis=1)


def walk_fixed(rc, rh, rl, target_r, stop_r=1.0):
    """stop at -stop_r, target at +target_r, else last valid close. tie -> stop."""
    n, H = rc.shape
    valid = ~np.isnan(rc)
    has_any = valid.any(axis=1)
    hs, is_ = first_true(np.nan_to_num(rl, nan=np.inf) <= -stop_r)
    ht, it = first_true(np.nan_to_num(rh, nan=-np.inf) >= target_r)
    lastidx = H - 1 - np.argmax(valid[:, ::-1], axis=1)
    lastr = rc[np.arange(n), np.clip(lastidx, 0, H - 1)]
    out = np.where(has_any, lastr, np.nan)
    code = np.where(has_any, 2, 3)
    tw = ht & (~hs | (it < is_))
    out = np.where(tw, float(target_r), out)
    code = np.where(tw, 1, code)
    sw = hs & (~ht | (is_ <= it))
    out = np.where(sw, -float(stop_r), out)
    code = np.where(sw, 0, code)
    return out, code


def main(window):
    days = set(ARM_DAYS[window])
    rows = load_rows(SRC[window], days)
    months = [window.replace("-", "")] + ([NEXT[window]] if NEXT.get(window) else [])
    print(f"[{window}] rows={len(rows)} months={months}", flush=True)
    tape = E.Tape(list(L.SYMBOLS), months)
    cm = E.CostModel()

    n = len(rows)
    sym = np.array([r["s"] for r in rows])
    fam = np.array([r["f"] for r in rows])
    day = np.array([r["t"][:10] for r in rows])
    inst = [r["t"] for r in rows]
    e = np.array([float(r["e"]) for r in rows])
    d = np.array([abs(float(r["e"]) - float(r["sl"])) for r in rows])
    real_long = np.array([r["d"] == "L" for r in rows])
    is_poi = np.array([r["f"] in POI for r in rows])

    # ---- path matrix. column 0 = stamp i-1 ; column 1+k = stamp i+k
    EXTRA = HOR + 3
    W_c = np.full((n, EXTRA), np.nan)
    W_h = np.full((n, EXTRA), np.nan)
    W_l = np.full((n, EXTRA), np.nan)
    idx = np.zeros(n, dtype=np.int64)
    by = defaultdict(list)
    for a, r in enumerate(rows):
        idx[a] = tape.idx(r["t"])
        by[r["s"]].append(a)
    for s, aa in by.items():
        c, h, lo = tape.c[s], tape.h[s], tape.l[s]
        aa = np.asarray(aa)
        base = idx[aa] - 1
        cols = base[:, None] + np.arange(EXTRA)[None, :]
        good = (cols >= 0) & (cols < tape.n)
        cl = np.clip(cols, 0, tape.n - 1)
        W_c[aa] = np.where(good, c[cl], np.nan)
        W_h[aa] = np.where(good, h[cl], np.nan)
        W_l[aa] = np.where(good, lo[cl], np.nan)
    mkt = W_c[:, 0]                    # last print strictly before the decision instant
    nbars = np.isfinite(W_c[:, 1:HOR + 1]).sum(axis=1).astype(np.int32)

    # ---- honest fill offset j (stamps i..i+H-1 = cols 1..H)  under the REAL side
    scan_h = W_h[:, 1:HOR + 1]
    scan_l = W_l[:, 1:HOR + 1]
    lvl = e[:, None]
    touch_long = np.nan_to_num(scan_l, nan=np.inf) <= lvl
    touch_short = np.nan_to_num(scan_h, nan=-np.inf) >= lvl
    tmask = np.where(real_long[:, None], touch_long, touch_short)
    has_t, j0 = first_true(tmask)
    j = np.where(is_poi, np.where(has_t, j0, 0), 0).astype(np.int64)
    filled = np.where(is_poi, has_t, True)

    # ---- R frames, computed once "as long"; short is the exact negation
    sl_ = slice(2, 2 + HOR)
    c_ = W_c[:, sl_]
    h_ = W_h[:, sl_]
    l_ = W_l[:, sl_]
    ee = e[:, None]
    dd = d[:, None]
    rcL = (c_ - ee) / dd
    raL = (h_ - ee) / dd
    rbL = (l_ - ee) / dd
    rhL = np.maximum(raL, rbL)
    rlL = np.minimum(raL, rbL)
    # mask the columns before the fill (col k of the frame is stamp i+1+k; the walk
    # starts at stamp i+j+1, i.e. frame column j)
    kk = np.arange(HOR)[None, :]
    pre = kk < j[:, None]
    for arr in (rcL, rhL, rlL):
        arr[pre] = np.nan
    bad = ~np.isfinite(d) | (d <= 0) | ~np.isfinite(e)
    rcS, rhS, rlS = -rcL, -rlL, -rhL

    out = {}
    for T in (2.0, 1.5):
        gL, cdL = walk_fixed(rcL, rhL, rlL, T)
        gS, cdS = walk_fixed(rcS, rhS, rlS, T)
        gL = np.where(filled & ~bad, gL, np.where(bad, np.nan, 0.0))
        gS = np.where(filled & ~bad, gS, np.where(bad, np.nan, 0.0))
        out[f"gL_{T}"] = gL
        out[f"gS_{T}"] = gS
        out[f"codeL_{T}"] = np.where(filled & ~bad, cdL, -1)
        out[f"codeS_{T}"] = np.where(filled & ~bad, cdS, -1)

    # ---- toll, both sides.  hour cache; swap is the only side-dependent term
    hourc = {}
    costL = np.zeros(n)
    costS = np.zeros(n)
    spreadR = np.zeros(n)
    bh = np.zeros(n, dtype=np.int16)
    for a in range(n):
        if bad[a] or not filled[a]:
            costL[a] = costS[a] = spreadR[a] = np.nan
            bh[a] = -1
            continue
        iso = inst[a]
        hh = hourc.get(iso)
        if hh is None:
            hh = cm.broker_hour(iso)
            hourc[iso] = hh
        bh[a] = hh
        sp = cm.spread_bps(sym[a], hh) / 1e4 * e[a]
        cmm = cm.comm_px(sym[a], e[a])
        slp = cm.slip_bps.get(sym[a], ("M", 0.0))[1] / 1e4 * e[a]
        swL = cm.swap_px(sym[a], True, e[a], iso, HOR)
        swS = cm.swap_px(sym[a], False, e[a], iso, HOR)
        costL[a] = (sp + cmm + slp + swL) / d[a]
        costS[a] = (sp + cmm + slp + swS) / d[a]
        spreadR[a] = sp / d[a]

    # ---- born past stop, at the REAL side (a property of geometry, not direction)
    past = np.where(real_long, mkt <= (e - d), mkt >= (e + d))
    past = np.where(np.isfinite(mkt), past, False)

    # ---- realised-vol regime: |c-c| sum over the prior 240 stamps / e, in bps
    rv = np.full(n, np.nan)
    for s, aa in by.items():
        c = tape.c[s]
        dif = np.abs(np.diff(c, prepend=np.nan))
        dif = np.nan_to_num(dif, nan=0.0)
        cs = np.cumsum(dif)
        aa = np.asarray(aa)
        i2 = idx[aa]
        lo = np.clip(i2 - 240, 0, tape.n - 1)
        hi = np.clip(i2 - 1, 0, tape.n - 1)
        rv[aa] = (cs[hi] - cs[lo]) / e[aa] * 1e4

    np.savez_compressed(
        f"/tmp/d1/out/D1_{window}.npz",
        sym=sym, fam=fam, day=day, inst=np.array(inst), e=e, d=d,
        real_long=real_long, is_poi=is_poi, filled=filled, j=j, past=past,
        bh=bh, rv=rv, costL=costL, costS=costS, spreadR=spreadR, bad=bad, nbars=nbars,
        **out,
    )
    print(f"[{window}] wrote n={n} filled={int(filled.sum())} bad={int(bad.sum())}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
