#!/usr/bin/env python3
"""F3 structural-level engine.

Builds, per symbol, a minute-indexed table of every candidate "level" a reversal
could plausibly be turning at, using ONLY information available at or before the
minute in question.  Everything is derived from the same true-UTC M1 archive the
walker uses, so there is one clock in the whole lane.

Broker day boundary comes from src/utils/broker_clock (NEW_YORK_PLUS_7): the broker
day rolls at 22:00 UTC while New York is on EST and 21:00 UTC while it is on EDT.
That boundary is the rollover B10 measured at up to 26.4x cost.

Level families (all causal):
  pdh/pdl/pdc   prior broker day high / low / close
  dh_f/dl_f     today's high/low AS OF THE TRADE'S FILL MINUTE (fixed at entry)
  ash/asl       Asia session high/low as of fill
  lnh/lnl       London session high/low as of fill
  sma20/50/200  M15 simple moving averages, closed bars only, at the stall minute
  swh/swl       most recent M15 fractal swing high/low strictly before the stall
  rnd           nearest round number at three granularities
  wkh/wkl       prior broker week high/low

Emits f3_levels_<month>.pkl.gz: {sym: {"t": int64[n], <level>: float64[n], ...}}
plus atr14_m15 (for scale-free distances) and the session/day-boundary index.
"""
import csv, gzip, json, os, pickle, sys, time
import datetime as dt
from pathlib import Path
import numpy as np

WT = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
sys.path.insert(0, str(WT))
from src.utils.broker_clock import NEW_YORK_PLUS_7, offset_seconds_at_utc

HOLD = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805")
BARS = HOLD / ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars"
OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f3")
EPOCH = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
MONTH_SRC = {"feb": ["202601", "202602", "202603"], "apr": ["202603", "202604", "202605"],
             "may": ["202604", "202605", "202606"], "jun": ["202605", "202606", "202607"],
             "jul": ["202606", "202607"]}
T0 = time.time()


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


def mins(t):
    return int((t - EPOCH).total_seconds() // 60)


def at(s):
    return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))


def broker_day_index(tm):
    """Broker trading-day id for each UTC minute, via NEW_YORK_PLUS_7.

    broker wall clock = UTC + off, off = 2 (NY on EST) or 3 (NY on EDT).
    The broker day rolls at broker 00:00, i.e. UTC minute where (utc + off) crosses
    midnight.  Returns (day_id, broker_hour, offset_hours).
    """
    out_d = np.empty(len(tm), dtype=np.int64)
    out_h = np.empty(len(tm), dtype=np.int8)
    out_o = np.empty(len(tm), dtype=np.int8)
    cache = {}
    for i, m in enumerate(tm):
        d0 = int(m // 1440)
        if d0 not in cache:
            u = EPOCH + dt.timedelta(minutes=int(d0) * 1440)
            cache[d0] = offset_seconds_at_utc(u, NEW_YORK_PLUS_7) // 3600
        off = cache[d0]
        bm = int(m) + off * 60
        out_d[i] = bm // 1440
        out_h[i] = (bm % 1440) // 60
        out_o[i] = off
    return out_d, out_h, out_o


def load_m1(month):
    per = {}
    for tag in MONTH_SRC[month]:
        d = BARS / f"bridge_ftmo_m1_{tag}"
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*_M1.csv")):
            sym = p.name[:-7]
            rows = per.setdefault(sym, [])
            with p.open(newline="") as fh:
                for row in csv.DictReader(fh):
                    rows.append((row["time"], row["open"], row["high"], row["low"], row["close"]))
    out = {}
    for sym, rows in per.items():
        rows = sorted(set(rows), key=lambda r: r[0])
        tm = np.array([mins(at(r[0])) for r in rows], dtype=np.int64)
        keep = np.concatenate([[True], np.diff(tm) > 0])
        rows = [r for r, k in zip(rows, keep) if k]
        tm = tm[keep]
        out[sym] = dict(
            t=tm,
            o=np.array([float(r[1]) for r in rows]),
            h=np.array([float(r[2]) for r in rows]),
            l=np.array([float(r[3]) for r in rows]),
            c=np.array([float(r[4]) for r in rows]))
    return out


def running_extreme_by_group(vals, grp, kind):
    """Running max/min of vals within each contiguous group, INCLUSIVE of current bar."""
    out = np.empty(len(vals))
    if len(vals) == 0:
        return out
    cur = vals[0]
    out[0] = cur
    for i in range(1, len(vals)):
        if grp[i] != grp[i - 1]:
            cur = vals[i]
        else:
            cur = max(cur, vals[i]) if kind == "max" else min(cur, vals[i])
        out[i] = cur
    return out


def prior_group_stat(vals, grp, fn):
    """For each bar, the stat of the PREVIOUS group (fully closed)."""
    uniq, first = np.unique(grp, return_index=True)
    stats = {}
    order = list(uniq)
    for a, g in enumerate(order):
        m = grp == g
        stats[g] = fn(vals[m])
    prev = {g: (stats[order[a - 1]] if a > 0 else np.nan) for a, g in enumerate(order)}
    return np.array([prev[g] for g in grp])


def m15_features(tm, o, h, l, c):
    """M15 SMAs / ATR / fractal swings, mapped back to minute resolution, causal."""
    b = tm // 15
    idx = np.nonzero(np.concatenate([[True], np.diff(b) != 0]))[0]
    ends = np.concatenate([idx[1:], [len(tm)]])
    bh = np.array([h[a:e].max() for a, e in zip(idx, ends)])
    bl = np.array([l[a:e].min() for a, e in zip(idx, ends)])
    bc = c[ends - 1]
    bb = b[idx]
    n = len(bb)

    def sma(k):
        cs = np.concatenate([[0.0], np.cumsum(bc)])
        out = np.full(n, np.nan)
        if n > k:
            out[k:] = (cs[k:n] - cs[0:n - k]) / k          # closed bars only, shifted by 1
        return out
    tr = np.maximum(bh - bl, np.maximum(np.abs(bh - np.concatenate([[bc[0]], bc[:-1]])),
                                        np.abs(bl - np.concatenate([[bc[0]], bc[:-1]]))))
    cs = np.concatenate([[0.0], np.cumsum(tr)])
    atr = np.full(n, np.nan)
    if n > 14:
        atr[14:] = (cs[14:n] - cs[0:n - 14]) / 14
    # fractal swings: bar j is a swing high if bh[j] is the max of j-2..j+2; only
    # confirmed (i.e. usable from j+2 onward)
    swh = np.full(n, np.nan); swl = np.full(n, np.nan)
    lastH = np.nan; lastL = np.nan
    for j in range(n):
        k = j - 2
        if k >= 2:
            w = slice(k - 2, k + 3)
            if bh[k] == bh[w].max():
                lastH = bh[k]
            if bl[k] == bl[w].min():
                lastL = bl[k]
        swh[j] = lastH; swl[j] = lastL
    m = np.searchsorted(bb, tm // 15, side="right") - 1     # index of the bar containing tm
    m = np.clip(m, 0, n - 1)
    prev = np.clip(m - 1, 0, n - 1)                          # last CLOSED M15 bar
    return dict(sma20=sma(20)[prev], sma50=sma(50)[prev], sma200=sma(200)[prev],
                atr=atr[prev], swh=swh[prev], swl=swl[prev])


def round_levels(px, step):
    """Nearest round level at a given step, and the distance to it."""
    return np.round(px / step) * step


def build(month):
    ser = load_m1(month)
    log(stage="m1_loaded", month=month, symbols=len(ser))
    out = {}
    for sym, S in ser.items():
        tm, o, h, l, c = S["t"], S["o"], S["h"], S["l"], S["c"]
        bd, bh_, boff = broker_day_index(tm)
        wk = bd // 7
        f = dict(t=tm, bday=bd, bhour=bh_, boff=boff, o=o, h=h, l=l, c=c)
        f["pdh"] = prior_group_stat(h, bd, np.max)
        f["pdl"] = prior_group_stat(l, bd, np.min)
        f["pdc"] = prior_group_stat(c, bd, lambda v: v[-1])
        f["wkh"] = prior_group_stat(h, wk, np.max)
        f["wkl"] = prior_group_stat(l, wk, np.min)
        f["dh"] = running_extreme_by_group(h, bd, "max")     # incl. current bar
        f["dl"] = running_extreme_by_group(l, bd, "min")
        # UTC-session extremes within the broker day (asia 00-07, london 07-12 UTC)
        uh = (tm % 1440) // 60
        sess = np.where(uh < 7, 0, np.where(uh < 12, 1, 2))
        skey = bd * 4 + sess
        f["sh"] = running_extreme_by_group(h, skey, "max")
        f["sl"] = running_extreme_by_group(l, skey, "min")
        f["psh"] = prior_group_stat(h, skey, np.max)
        f["psl"] = prior_group_stat(l, skey, np.min)
        f.update(m15_features(tm, o, h, l, c))
        out[sym] = f
    OUT.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT / f"f3_levels_{month}.pkl.gz", "wb") as fh:
        pickle.dump(out, fh, protocol=5)
    log(stage="month_done", month=month, symbols=len(out))


if __name__ == "__main__":
    for m in sys.argv[1:] or ["feb", "apr", "may", "jun", "jul"]:
        build(m)
    log(stage="ALL_DONE")
