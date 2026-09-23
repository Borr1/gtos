"""f2_ladder — THE DECIDING EXPERIMENT: the system's own signals under ORACLE usage.

Lane f2, wave 19.  Answers: is the broad V4 family's problem the SIGNAL or the USAGE?

Method.  Take the sealed arms' own candidate roster (Session PB's reproduced close-only
emissions, 99.82 % matched to the sealed January arm on a 10-decimal geometry hash), and
price a ladder of rungs on THE SAME ROWS, each rung replacing one downstream layer with a
perfect (impossible-to-run-live) version of itself:

    R0  as the system runs it        shipped cost gate + shipped exit contract
    R1  + no gate at all             admit every emission
    R2  + oracle ORDERING            at the system's own daily capacity, keep the winners
    R3  + oracle EXIT                per trade, the best exit on its own realised path
    R4  + oracle ENTRY TIMING        the best entry instant in the following M15 bar
    R5  + oracle DIRECTION           flip every trade that would have lost

Every rung is charged the same broker-true four-term toll (h1 basis), and every rung is
ALSO computed on two matched PLACEBOS:

    PLACEBO-SIDE   identical rows, identical instants, identical risk distance, RANDOM side
    PLACEBO-TIME   same symbol + same trading day + same risk distance, RANDOM instant on
                   the system's own 96-window grid, RANDOM side

The placebo is the whole point.  An oracle exit is enormously positive on random entries
too; a rung's number is uninterpretable on its own.  `real - placebo` at each rung is what
the SIGNAL contributes once that layer is perfect.

Nothing is sampled.  Nothing under src/ is read for anything but the cost model and the
broker clock.
"""

from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PBG = HERE.parent / "pbg"
sys.path.insert(0, str(PBG))
sys.path.insert(0, str(HERE.parents[5]))

import pbg_econ as E  # noqa: E402
import pbg_lib as L  # noqa: E402

AT_MARKET = (
    "displacement_continuation",
    "liquidity_sweep_reclaim",
    "structural_distance_extreme",
    "volatility_compression_expansion",
    "session_open_range_break",
    "regime_transition_break",
    "cross_asset_lead_lag",
)
POI = ("current_fvg_fill", "current_ob_retest", "current_breaker_re_entry")

HORIZON = 120          # M1 bars; the sealed sidecar's own convention (PB reproduced it)
ENTRY_WINDOW = 15      # candidate entry stamps for the oracle-entry rung
SHIPPED_TARGET_R = 2.0  # the downstream momentum_exhaustion geometry the pool carries
GEN_TARGET_R = 1.5      # risk.min_rr, the geometry the generator itself emits


# ----------------------------------------------------------------- row loading


def setup_key(r):
    if r["f"].startswith("current_"):
        return (r["s"], r["f"], r["d"], r["b"], r["cid"])
    return (r["s"], r["f"], r["d"], r["b"])


def load_close_rows(indir, families):
    """One row per setup key, close-only (k=15).  PB's BOOK_close_only population."""
    seen = {}
    for p in sorted(glob.glob(os.path.join(indir, "pbg_*.jsonl.gz"))):
        with gzip.open(p, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if r["k"] != 15 or r["f"] not in families:
                    continue
                k = setup_key(r)
                if k not in seen:
                    seen[k] = r
    return list(seen.values())


# ------------------------------------------------------------------- path math


def build_paths(tape, rows, extra=ENTRY_WINDOW + HORIZON + 4):
    """Return arrays aligned to `rows`:
        idx   decision stamp index
        W_c/W_h/W_l   (n, extra) close/high/low from stamp i-1 forward
        ok    rows whose entry price is a real print
    Column j of W corresponds to stamp i-1+j.  So column 0 is the fill the shipped
    contract gets (the last print strictly before the decision instant).
    """
    n = len(rows)
    W_c = np.full((n, extra), np.nan)
    W_h = np.full((n, extra), np.nan)
    W_l = np.full((n, extra), np.nan)
    idx = np.zeros(n, dtype=np.int64)
    by_sym = defaultdict(list)
    for a, r in enumerate(rows):
        i = tape.idx(r["t"])
        idx[a] = i
        by_sym[r["s"]].append(a)
    for sym, aa in by_sym.items():
        c, h, lo = tape.c[sym], tape.h[sym], tape.l[sym]
        aa = np.asarray(aa)
        base = idx[aa] - 1
        cols = base[:, None] + np.arange(extra)[None, :]
        good = (cols >= 0) & (cols < tape.n)
        cl = np.clip(cols, 0, tape.n - 1)
        W_c[aa] = np.where(good, c[cl], np.nan)
        W_h[aa] = np.where(good, h[cl], np.nan)
        W_l[aa] = np.where(good, lo[cl], np.nan)
    return idx, W_c, W_h, W_l


def r_frames(W_c, W_h, W_l, entry, d, long, j, horizon):
    """Signed-R path frames for a trade whose FILL is the close of column j.

    Column j of W is stamp i-1+j, so an order filled there was sent at instant
    i+j, and the sealed sidecar's forward path is stamps i+j+1 .. i+j+horizon —
    columns j+2 .. j+1+horizon.  (Omitting the fill minute is the estate's own
    convention; x3 §5a measured that it flatters the shipped contract by 0.003 R.)
    Returns (rc, rh, rl): R at close / best / worst inside each bar.
    """
    sl = slice(j + 2, j + 2 + horizon)
    c = W_c[:, sl]
    h = W_h[:, sl]
    lo = W_l[:, sl]
    e = entry[:, None]
    dd = d[:, None]
    sgn = np.where(long, 1.0, -1.0)[:, None]
    rc = (c - e) / dd * sgn
    ra = (h - e) / dd * sgn        # a = the price at the bar high
    rb = (lo - e) / dd * sgn       # b = the price at the bar low
    rh = np.maximum(ra, rb)        # best inside the bar, side-aware
    rl = np.minimum(ra, rb)        # worst inside the bar, side-aware
    return rc, rh, rl


def _first_true(mask):
    """(has_any, first_index) along axis 1."""
    any_ = mask.any(axis=1)
    first = np.argmax(mask, axis=1)
    return any_, first


def walk_fixed(rc, rh, rl, target_r, *, stop_r=1.0, max_bars=None):
    """Shipped contract: stop at -stop_r, target at +target_r, else last close.
    Tie inside one bar -> the STOP wins (M1 OHLC carries no intrabar ordering).
    Returns (r, exit_code) with 0=stop 1=target 2=path_end 3=dead."""
    n, H = rc.shape
    if max_bars is not None and max_bars < H:
        rc, rh, rl = rc[:, :max_bars], rh[:, :max_bars], rl[:, :max_bars]
        H = max_bars
    valid = ~np.isnan(rc)
    has_any = valid.any(axis=1)
    hs, is_ = _first_true(np.nan_to_num(rl, nan=np.inf) <= -stop_r)
    ht, it = _first_true(np.nan_to_num(rh, nan=-np.inf) >= (target_r if target_r is not None else np.inf))
    # last valid close
    lastidx = H - 1 - np.argmax(valid[:, ::-1], axis=1)
    lastr = rc[np.arange(n), np.clip(lastidx, 0, H - 1)]
    out = np.where(has_any, lastr, np.nan)
    code = np.where(has_any, 2, 3)
    tgt_wins = ht & (~hs | (it < is_))
    out = np.where(tgt_wins, float(target_r) if target_r is not None else out, out)
    code = np.where(tgt_wins, 1, code)
    stp_wins = hs & (~ht | (is_ <= it))
    out = np.where(stp_wins, -float(stop_r), out)
    code = np.where(stp_wins, 0, code)
    return out, code


def walk_be_runner(rc, rh, rl, *, arm_r=1.0, stop_r=1.0):
    """Stop at -1R until the bar AFTER the trade first prints +arm_r, then breakeven;
    run to the horizon.  Arming is shifted by one bar so no intrabar credit is taken."""
    n, H = rc.shape
    armed = np.zeros((n, H), dtype=bool)
    hit = np.nan_to_num(rh, nan=-np.inf) >= arm_r
    armed[:, 1:] = np.maximum.accumulate(hit, axis=1)[:, :-1]
    level = np.where(armed, 0.0, -stop_r)
    stopped = np.nan_to_num(rl, nan=np.inf) <= level
    hs, is_ = _first_true(stopped)
    valid = ~np.isnan(rc)
    has_any = valid.any(axis=1)
    lastidx = H - 1 - np.argmax(valid[:, ::-1], axis=1)
    lastr = rc[np.arange(n), np.clip(lastidx, 0, H - 1)]
    stop_level = level[np.arange(n), np.clip(is_, 0, H - 1)]
    out = np.where(hs, stop_level, np.where(has_any, lastr, np.nan))
    return out, np.where(hs, 0, np.where(has_any, 2, 3))


def walk_trail(rc, rh, rl, *, arm_r=1.0, gap_r=1.0, stop_r=1.0):
    """Trail `gap_r` below the running best, armed after +arm_r.  The trail level for
    bar t is built from bars < t only (no intrabar self-triggering)."""
    n, H = rc.shape
    runmax = np.maximum.accumulate(np.nan_to_num(rh, nan=-np.inf), axis=1)
    prev = np.full((n, H), -np.inf)
    prev[:, 1:] = runmax[:, :-1]
    armed = prev >= arm_r
    level = np.where(armed, prev - gap_r, -stop_r)
    stopped = np.nan_to_num(rl, nan=np.inf) <= level
    hs, is_ = _first_true(stopped)
    valid = ~np.isnan(rc)
    has_any = valid.any(axis=1)
    lastidx = H - 1 - np.argmax(valid[:, ::-1], axis=1)
    lastr = rc[np.arange(n), np.clip(lastidx, 0, H - 1)]
    lv = level[np.arange(n), np.clip(is_, 0, H - 1)]
    out = np.where(hs, lv, np.where(has_any, lastr, np.nan))
    return out, np.where(hs, 0, np.where(has_any, 2, 3))


MENU_TARGETS = (1.0, 1.5, 2.0, 3.0, 5.0)
MENU_TIMESTOPS = (15, 30, 60)


def exit_menu(rc, rh, rl):
    """Every exit contract a live engine could actually run, priced on the same path.
    Returns dict name -> r array."""
    out = {}
    for t in MENU_TARGETS:
        out["target_%.1fR" % t], _ = walk_fixed(rc, rh, rl, t)
    out["stop_only_horizon"], _ = walk_fixed(rc, rh, rl, None)
    for nb in MENU_TIMESTOPS:
        out["timestop_%d" % nb], _ = walk_fixed(rc, rh, rl, None, max_bars=nb)
    out["be_runner"], _ = walk_be_runner(rc, rh, rl)
    out["trail_1R"], _ = walk_trail(rc, rh, rl)
    out["no_stop_horizon"], _ = walk_fixed(rc, rh, rl, None, stop_r=1e9)
    return out


def oracle_exit_close(rc):
    """The best exit AT A REAL PRINT: the max close-based R anywhere on the path.
    Uses closes, never intrabar extremes -- headline #1 of this week died on exactly
    that premium, so it is quantified separately, not banked."""
    with np.errstate(invalid="ignore"):
        return np.nanmax(rc, axis=1)


def oracle_exit_intrabar(rh):
    """The unachievable ceiling: exit at the best intrabar print.  Reported only to
    price the bar-resolution premium."""
    with np.errstate(invalid="ignore"):
        return np.nanmax(rh, axis=1)


# ------------------------------------------------------------------ aggregation


def agg(r, cost_r, day, *, label, extra=None):
    r = np.asarray(r, dtype=float)
    cost_r = np.asarray(cost_r, dtype=float)
    m = np.isfinite(r)
    r, cost_r, day = r[m], cost_r[m], np.asarray(day)[m]
    if r.size == 0:
        return {"label": label, "n": 0}
    net = r - cost_r
    by = defaultdict(float)
    cnt = defaultdict(int)
    for d, x in zip(day, net):
        by[d] += x
        cnt[d] += 1
    days = sorted(by)
    out = {
        "label": label,
        "n": int(r.size),
        "gross_r_per_trade": float(r.mean()),
        "cost_r_per_trade": float(cost_r.mean()),
        "net_r_per_trade": float(net.mean()),
        "total_gross_r": float(r.sum()),
        "total_net_r": float(net.sum()),
        "win_rate_gross": float((r > 0).mean()),
        "win_rate_net": float((net > 0).mean()),
        "n_days": len(days),
        "days_net_positive": int(sum(1 for d in days if by[d] > 0)),
    }
    if extra:
        out.update(extra)
    return out


def day_boot(net, day, n=2000, seed=20260806):
    by = defaultdict(lambda: [0.0, 0])
    for d, x in zip(day, net):
        if np.isfinite(x):
            by[d][0] += x
            by[d][1] += 1
    days = sorted(by)
    if not days:
        return None
    s = np.array([by[d][0] for d in days])
    c = np.array([by[d][1] for d in days], dtype=float)
    rng = np.random.default_rng(seed)
    ix = rng.integers(0, len(days), size=(n, len(days)))
    num = s[ix].sum(axis=1)
    den = c[ix].sum(axis=1)
    den[den == 0] = np.nan
    m = num / den
    m = m[np.isfinite(m)]
    return {
        "mean": float(s.sum() / c.sum()),
        "ci95_lo": float(np.percentile(m, 2.5)),
        "ci95_hi": float(np.percentile(m, 97.5)),
        "p_le_0": float((m <= 0).mean()),
        "n_days": len(days),
    }
