"""m1 — THE ACCUMULATION CURVE, re-derived on the repaired instrument.

This is the load-bearing number of wave 19's verdict: a working sleeve's signal grows
37.58x from 2 h to 320 h and the broad family's grows 0.97x, so no contract, horizon or
broker can make a signal that does not accumulate outrun a toll paid once.  d3 measured it
with a walker that never crossed the spread and on a roster that still carried the
generator's malformed emissions.  Both are repaired; this re-derives the curve.

CONSTRUCTION — d3's, unchanged except for the two repairs
----------------------------------------------------------
* horizons {8, 32, 96, 288, 640, 1280} PRINTED M15 bars = {2, 8, 24, 72, 160, 320}
  TRADING hours (`d3_tape2` — what the live engine's `_trading_m15_bars_since` counts,
  `execution.py:8953-8958`); weekends do not consume the budget.
* native stop (the generator's own risk distance), target 3.0 R, stop wins ties.
* the measurement is PAIRED.  d3 paired against a COIN-FLIP placebo side, which is
  carried here unchanged (seed 20260806) so the two are comparable — but a coin discards
  half the pairs and the draw itself is worth ~27 % of the published signal, so a
  deterministic MIRROR arm is added: every row walked on BOTH sides, signal = (REAL -
  MIRROR)/2, which estimates the same quantity with zero draw variance.
* signal in bps of price: published two ways, because d3 used a constant and the live arm
  used the per-row product, and they differ.

THE REPAIRS, applied
--------------------
* generator — rows the repaired emission contract refuses (stop already breached at the
  decision instant; selected bar older than one M15 period) are dropped.  Measured here
  from the roster itself rather than taken from r2's artifact.
* walker — every arm is anchored at `entry + side * spread`, the canonical FILL anchoring
  (`quote_side.replay_anchor`).  Both the REAL and the PLACEBO arm pay it, on their own
  side, so the paired difference is not trivially preserved: the two arms' geometries
  separate by two spreads and each one's exits resolve differently.

The direction call is measured AT MARKET for every family — anchored at the DECISION-
INSTANT CLOSE, not at the emitted entry.  For the seven at-market families those are the
same number (fill_gap_R == 0 on 144,725 of 144,725 rows).  For the three POI limit families
they are not: the emitted entry is a structural level the market has not reached, 84 % of
those candidates are already beyond their own target when born, and walking them from that
level books an instant +3 R — it measures the gate, not the direction call.  The at-market
cohort alone is also published, because that is the object d3 measured (n = 144,725).
"""
from __future__ import annotations

import bisect
import csv
import glob
import gzip
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
sys.path.insert(0, PBG)
sys.path.insert(0, REPO)
os.chdir(REPO)

import pbg_lib as PL  # noqa: E402
import pbg_econ as E  # noqa: E402

from src.research_infra.walkforward.quote_side import (  # noqa: E402
    BarQuote, SpreadUnavailable, spread_for,
)

HOR = [8, 32, 96, 288, 640, 1280]
HH = [2, 8, 24, 72, 160, 320]
TARGET = 3.0
MAXH = max(HOR)
POI = ("current_fvg_fill", "current_ob_retest", "current_breaker_re_entry")
T0 = datetime(2025, 6, 1, tzinfo=timezone.utc)
CHUNK = 12000
SEED = 20260806
Q = BarQuote.BID

LEGACY = {
    "2025-10": "/tmp/f1/roster_202510", "2025-11": "/tmp/f1/roster_202511",
    "2025-12": "/tmp/f1/roster_202512", "2026-01": "/tmp/d4/rosters/202601",
    "2026-02": "/tmp/d4/rosters/202602", "2026-03": "/tmp/d4/rosters/202603",
    "2026-04": "/tmp/f1/roster_202604", "2026-05": "/tmp/f1/roster_202605",
}
SPREAD_NAME = {"GER40": "GER40.cash", "JP225": "JP225.cash", "NAS100": "US100.cash",
               "SPX500": "US500.cash", "UK100": "UK100.cash", "US30_cash": "US30.cash",
               "UKOIL_cash": "UKOIL.cash", "USOIL_cash": "USOIL.cash"}


class CTape:
    """Printed-bar M15 series, d3_tape2's object."""

    def __init__(self, symbols):
        self.h, self.l, self.c, self.tmin, self.tc = {}, {}, {}, {}, {}
        for sym in symbols:
            p = PL.M15_DIR / f"{sym}_M15.csv"
            th, tl, tc, tt = [], [], [], []
            if p.is_file():
                with p.open() as fh:
                    for row in csv.DictReader(fh):
                        ts = datetime.fromisoformat(row["time"])
                        tt.append(int((ts - T0).total_seconds() // 60))
                        th.append(float(row["high"]))
                        tl.append(float(row["low"]))
                        tc.append(float(row["close"]))
            self.h[sym] = np.array(th)
            self.l[sym] = np.array(tl)
            self.c[sym] = np.array(tc)
            self.tmin[sym] = np.array(tt, dtype=np.int64)

    def minutes(self, iso):
        return int((datetime.fromisoformat(iso) - T0).total_seconds() // 60)

    def pos(self, sym, iso):
        return int(np.searchsorted(self.tmin[sym], self.minutes(iso), side="left"))


def first_true_idx(mask):
    n, H = mask.shape
    has = mask.any(axis=1)
    idx = np.argmax(mask, axis=1)
    return np.where(has, idx, H + 1)


def cell_walk(rc, rh, rl, target_r, horizons):
    """d3_walk.cell_walk, verbatim in behaviour: {H: r} by first touch, stop wins ties."""
    is_ = first_true_idx(np.nan_to_num(rl, nan=np.inf) <= -1.0)
    it = first_true_idx(np.nan_to_num(rh, nan=-np.inf) >= target_r)
    valid = ~np.isnan(rc)
    n, H = rc.shape
    ar = np.arange(n)
    out = {}
    for Hh in horizons:
        v = valid[:, :Hh]
        has = v.any(axis=1)
        lastidx = np.clip(Hh - 1 - np.argmax(v[:, ::-1], axis=1), 0, Hh - 1)
        r = np.where(has, rc[ar, lastidx], np.nan)
        st, tg = is_ < Hh, it < Hh
        tw = tg & (~st | (it < is_))
        sw = st & (~tg | (is_ <= it))
        r = np.where(tw, target_r, r)
        r = np.where(sw, -1.0, r)
        out[Hh] = r
    return out


def load_rows(tape, cm):
    """Every emission of the eight open windows, with the repair's two gate keys."""
    S = {}
    for p in sorted(glob.glob(os.path.join(str(PL.M15_DIR), "*_M15.csv"))):
        sym = os.path.basename(p)[: -len("_M15.csv")]
        t, c = [], []
        with open(p, newline="") as fh:
            for r in csv.DictReader(fh):
                t.append(datetime.fromisoformat(r["time"]).replace(tzinfo=None))
                c.append(float(r["close"]))
        S[sym] = (t, c)
    rows = []
    scache = {}
    for w, rd in sorted(LEGACY.items()):
        for f in sorted(glob.glob(os.path.join(rd, "*.jsonl.gz"))):
            if not os.path.exists(f.replace(".jsonl.gz", ".stats.json")):
                continue
            for line in gzip.open(f, "rt"):
                r = json.loads(line)
                if r["k"] != 15:
                    continue
                sym = r["s"]
                if sym not in S or tape.tmin[sym].size == 0:
                    continue
                t, c = S[sym]
                T = datetime.fromisoformat(r["t"]).replace(tzinfo=None)
                j = bisect.bisect_right(t, T - timedelta(minutes=15)
                                        + timedelta(seconds=2)) - 1
                if j < 0:
                    continue
                e, sl = r["e"], r["sl"]
                d = abs(e - sl)
                if not d > 0:
                    continue
                lng = r["d"] == "L"
                sgn = 1.0 if lng else -1.0
                gap = (c[j] - e) / d * sgn
                age = int((T - (t[j] + timedelta(minutes=15))).total_seconds() // 60)
                pos = tape.pos(sym, r["t"])
                if pos >= tape.tmin[sym].size:
                    continue
                h = cm.broker_hour(r["t"])
                s_tick = cm.spread_bps(sym, h) / 1e4 * e
                ck = (sym, T.date(), T.hour)
                s_era = scache.get(ck)
                if s_era is None:
                    try:
                        s_era = spread_for(SPREAD_NAME.get(sym, sym),
                                           T.replace(tzinfo=timezone.utc),
                                           account="FTMO", band="mid")
                    except SpreadUnavailable:
                        s_era = float("nan")
                    scache[ck] = s_era
                rows.append((w, sym, r["f"], lng, e, d, gap, age, pos, s_tick, s_era))
    return rows


def main(out_path):
    syms = sorted(p.name[: -len("_M15.csv")] for p in PL.M15_DIR.glob("*_M15.csv"))
    tape = CTape(syms)
    cm = E.CostModel()
    rows = load_rows(tape, cm)
    n = len(rows)
    print("rows", n, flush=True)

    win = np.array([r[0] for r in rows])
    sym = np.array([r[1] for r in rows])
    fam = np.array([r[2] for r in rows])
    long = np.array([r[3] for r in rows])
    entry = np.array([r[4] for r in rows], dtype=float)
    dnat = np.array([r[5] for r in rows], dtype=float)
    gap = np.array([r[6] for r in rows], dtype=float)
    age = np.array([r[7] for r in rows], dtype=int)
    pos = np.array([r[8] for r in rows], dtype=np.int64)
    s_tick = np.array([r[9] for r in rows], dtype=float)
    s_era = np.array([r[10] for r in rows], dtype=float)
    dbps = dnat / entry * 1e4
    is_poi = np.isin(fam, POI)

    # the repaired emission contract, re-derived from the roster
    refused_past_stop = is_poi & (gap < -1.0)
    refused_stale = age >= 15
    kept = ~(refused_past_stop | refused_stale)
    print("refused: past_stop", int(refused_past_stop.sum()),
          "stale", int(refused_stale.sum()), "kept", int(kept.sum()), flush=True)

    rng = np.random.default_rng(SEED)
    plong = rng.random(n) < 0.5
    sgnR = np.where(long, 1.0, -1.0)
    sgnP = np.where(plong, 1.0, -1.0)

    # ANCHOR BASE — the decision-instant close, for every family.
    # For the seven at-market families this IS the emitted entry (gap == 0 on
    # 144,725 of 144,725 rows, r2's census).  For the three POI limit families the
    # emitted entry is a structural level the market has not reached, and 84 % of
    # them are already beyond their own target when born, so walking them from that
    # level books an instant +3 R and measures the gate, not the direction call.
    cp = entry + gap * dnat * sgnR

    arms = {"old_REAL": (sgnR, None), "old_PLACEBO": (sgnP, None), "old_MIRROR": (-sgnR, None),
            "cor_REAL": (sgnR, s_tick), "cor_PLACEBO": (sgnP, s_tick), "cor_MIRROR": (-sgnR, s_tick),
            "era_REAL": (sgnR, s_era), "era_MIRROR": (-sgnR, s_era)}
    acc = {k: {h: np.full(n, np.nan, dtype=np.float32) for h in HOR} for k in arms}

    by = defaultdict(list)
    for a in range(n):
        by[sym[a]].append(a)
    ar = np.arange(MAXH + 2)
    done = 0
    for s, aa in by.items():
        h_, l_, c_, m = tape.h[s], tape.l[s], tape.c[s], tape.c[s].size
        aa = np.asarray(aa)
        for k0 in range(0, aa.size, CHUNK):
            idx = aa[k0:k0 + CHUNK]
            cols = pos[idx][:, None] + ar[None, :]
            good = (cols >= 0) & (cols < m)
            cl = np.clip(cols, 0, max(m - 1, 0))
            Wh = np.where(good, h_[cl], np.nan)
            Wl = np.where(good, l_[cl], np.nan)
            Wc = np.where(good, c_[cl], np.nan)
            for name, (sg, sp) in arms.items():
                g = sg[idx][:, None]
                anchor = cp[idx] if sp is None else cp[idx] + sg[idx] * sp[idx]
                a_ = anchor[:, None]
                dd = dnat[idx][:, None]
                rc = (Wc - a_) / dd * g
                rh = (Wh - a_) / dd * g
                rl = (Wl - a_) / dd * g
                rhi, rlo = np.maximum(rh, rl), np.minimum(rh, rl)
                out = cell_walk(rc, rhi, rlo, TARGET, HOR)
                for h in HOR:
                    acc[name][h][idx] = out[h]
            done += idx.size
        print("  ", s, done, flush=True)

    np.savez_compressed(
        out_path, win=win, sym=sym, fam=fam, long=long, plong=plong, entry=entry, cp=cp,
        dnat=dnat, dbps=dbps, gap=gap, age=age, kept=kept, is_poi=is_poi,
        s_tick=s_tick, s_era=s_era,
        **{f"{k}_{h}": v[h] for k, v in acc.items() for h in HOR})
    print("WROTE", out_path, flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
