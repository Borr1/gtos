"""x2 — WHEN WAS EACH SETUP FIRST DETECTABLE?

For every one of the 27,658 January candidates, replay its origin family's DEFINING
CONDITION minute-by-minute across the 15 M1 bars that compose its decision M15 bar,
using exactly the predicates in src/components/broader_origin_generators.py.

Outputs per row:
  first_true_minute      1..15, the first minute m at which the family predicate
                         (evaluated on the partial bar o, max(h_1..h_m), min(l_1..l_m),
                          close(m)) is TRUE **for the row's own side**
  earliness_min          15 - first_true_minute
  comp_<name>_min        first minute each COMPONENT of the predicate is true
  price_edge_r           (close-entry families) signed price improvement of acting at
                         first_true_minute instead of the M15 close, in units of the
                         decision's own risk_distance
Plus, for the three POI-proximity families, a backwalk: how many minutes BEFORE the
decision was the proximity trigger continuously satisfied.
"""
from __future__ import annotations

import gzip
import json
import math
import os
import sys
from bisect import bisect_left
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import w0_ws  # noqa: E402
import x2_bars  # noqa: E402
from src.components.broader_origin_generators import (  # noqa: E402
    LEAD_LAG_PAIRS,
    _canonical_symbol,
    _session_at,
)

OUT = os.path.join(HERE, "x2_EARLINESS_ROWS_V1.jsonl.gz")
PROX_TOL = 0.01           # pre_ai_gates.poi_proximity_tolerance_pct (agent_config.yaml:4032)
BUFFER_ATR = {            # _current_framework_stop_buffer_atr defaults, config-resolved
    "current_fvg_fill": 0.25,        # risk.sl_buffer_atr_multiplier = 0.25
    "current_ob_retest": 0.5,        # gate1.ob_retest_sl_min_buffer_atr = 0.5
    "current_breaker_re_entry": 0.25,
}
POI_FAMILIES = set(BUFFER_ATR)
CLOSE_ENTRY_FAMILIES = {
    "liquidity_sweep_reclaim",
    "displacement_continuation",
    "volatility_compression_expansion",
    "session_open_range_break",
    "regime_transition_break",
    "structural_distance_extreme",
    "cross_asset_lead_lag",
}
BACKWALK_CAP = 2880       # 48 h of M1 bars


# ---------------------------------------------------------------- pre-bar context
class Ctx:
    """Everything the predicate needs that is fixed BEFORE the decision bar opens."""

    __slots__ = (
        "ok", "o", "h", "l", "c", "sum13", "sum49", "ph20", "pl20", "ph50", "pl50",
        "c_m20", "prior_ratio", "prev_trend", "max49", "min49", "prev_close",
        "atr14_close", "atr50_close", "i", "bars",
    )


def build_ctx(symbol: str, decision_utc: str):
    i = x2_bars.m15_index_for_decision(symbol, decision_utc)
    if i is None or i < 51:
        return None
    bars, _ = x2_bars.m15(symbol)
    b = bars[i]
    ctx = Ctx()
    ctx.i = i
    ctx.bars = bars
    ctx.o, ctx.h, ctx.l, ctx.c = b[1], b[2], b[3], b[4]
    prev13 = bars[i - 13:i]
    prev49 = bars[i - 49:i]
    ctx.sum13 = sum(x[2] - x[3] for x in prev13)
    ctx.sum49 = sum(x[2] - x[3] for x in prev49)
    w20 = bars[i - 20:i]
    w50 = bars[i - 50:i]
    ctx.ph20 = max(x[2] for x in w20)
    ctx.pl20 = min(x[3] for x in w20)
    ctx.ph50 = max(x[2] for x in w50)
    ctx.pl50 = min(x[3] for x in w50)
    ctx.c_m20 = bars[i - 20][4]
    ctx.prev_close = bars[i - 1][4]
    ctx.max49 = max(x[2] for x in prev49)
    ctx.min49 = min(x[3] for x in prev49)
    # prior bar ratio (fully pre-bar)
    a14p = sum(x[2] - x[3] for x in bars[i - 14:i]) / 14.0
    a50p = sum(x[2] - x[3] for x in bars[i - 50:i]) / 50.0
    ctx.prior_ratio = a14p / a50p if a50p > 0 else None
    # previous trend state (i-1)
    if a50p > 0:
        score = (bars[i - 1][4] - bars[i - 21][4]) / a50p
        ctx.prev_trend = _trend_label(score)
    else:
        ctx.prev_trend = "insufficient_lookback"
    ctx.atr14_close = (ctx.sum13 + (ctx.h - ctx.l)) / 14.0
    ctx.atr50_close = (ctx.sum49 + (ctx.h - ctx.l)) / 50.0
    ctx.ok = True
    return ctx


def _trend_label(score: float) -> str:
    if score >= 2.0:
        return "strong_up"
    if score >= 0.75:
        return "up"
    if score <= -2.0:
        return "strong_down"
    if score <= -0.75:
        return "down"
    return "flat"


def partials(symbol: str, decision_utc: str, ctx):
    """List of (minute, o, h_m, l_m, c_m) for m = 1..15 (only minutes with an M1 bar)."""
    T = datetime.fromisoformat(decision_utc)
    seg = x2_bars.m1_slice(symbol, T - timedelta(minutes=15), T)
    if not seg:
        return []
    out = []
    h = -math.inf
    lo = math.inf
    o = seg[0][1]
    for bar in seg:
        m = int((bar[0] - (T - timedelta(minutes=15))).total_seconds() // 60) + 1
        h = max(h, bar[2])
        lo = min(lo, bar[3])
        out.append((m, o, h, lo, bar[4]))
    return out


# ---------------------------------------------------------------- predicates
def eval_family(family, side, ctx, o, h, l, c, extra):
    """Return (fires_for_side, {component: bool}).  Mirrors broader_origin_generators.py."""
    atr14 = (ctx.sum13 + (h - l)) / 14.0
    atr50 = (ctx.sum49 + (h - l)) / 50.0
    rng = h - l
    comps = {}

    if family == "liquidity_sweep_reclaim":
        sh = h > ctx.ph20
        shc = c < ctx.ph20
        sl = l < ctx.pl20
        slc = c > ctx.pl20
        swept_high = sh and shc
        swept_low = sl and slc
        comps["pierce"] = sh if side == "SHORT" else sl
        comps["reclaim_close"] = shc if side == "SHORT" else slc
        comps["no_opposite_sweep"] = not (swept_low if side == "SHORT" else swept_high)
        fires = (swept_high and not swept_low) if side == "SHORT" else (swept_low and not swept_high)
        return fires, comps

    if family == "displacement_continuation":
        if atr14 <= 0:
            return False, {"range_ge_1p5_atr": False, "body_ge_0p75_atr": False, "side_match": False}
        c1 = rng / atr14 >= 1.5
        c2 = abs(c - o) / atr14 >= 0.75
        c3 = ("LONG" if c > o else "SHORT") == side
        comps.update(range_ge_1p5_atr=c1, body_ge_0p75_atr=c2, side_match=c3)
        return c1 and c2 and c3, comps

    if family == "volatility_compression_expansion":
        pr = ctx.prior_ratio
        c0 = pr is not None and pr <= 0.75
        c1 = atr14 > 0 and rng / atr14 >= 1.25
        c2 = (c > ctx.ph20) if side == "LONG" else (c < ctx.pl20)
        comps.update(prior_compression=c0, range_ge_1p25_atr=c1, close_beyond_20=c2)
        return c0 and c1 and c2, comps

    if family == "regime_transition_break":
        if atr50 <= 0:
            return False, {"trend_extreme": False, "prev_trend_ok": False, "close_beyond_20": False}
        tr = _trend_label((c - ctx.c_m20) / atr50)
        want = "strong_up" if side == "LONG" else "strong_down"
        c0 = tr == want
        c1 = ctx.prev_trend not in ({"strong_up", "up"} if side == "LONG" else {"strong_down", "down"})
        c2 = (c > ctx.ph20) if side == "LONG" else (c < ctx.pl20)
        comps.update(trend_extreme=c0, prev_trend_ok=c1, close_beyond_20=c2)
        return c0 and c1 and c2, comps

    if family == "structural_distance_extreme":
        hi = max(ctx.max49, h)
        lo = min(ctx.min49, l)
        if hi <= lo:
            return False, {"pos50_extreme": False}
        pos = (c - lo) / (hi - lo)
        fires = pos >= 0.97 if side == "SHORT" else pos <= 0.03
        comps["pos50_extreme"] = fires
        return fires, comps

    if family == "session_open_range_break":
        rh, rl, prev_break = extra.get("rh"), extra.get("rl"), extra.get("prev_break")
        if rh is None:
            return False, {"range_known": False, "no_prior_break": False, "close_beyond_range": False}
        c1 = not prev_break
        c2 = (c > rh) if side == "LONG" else (c < rl)
        comps.update(range_known=True, no_prior_break=c1, close_beyond_range=c2)
        return c1 and c2, comps

    if family == "cross_asset_lead_lag":
        li = extra.get("leader_impulse")
        lm = extra.get("leader_move")
        if li is None:
            return False, {"leader_impulse_ge_1atr": False, "lag_quiet_le_0p5atr": False, "side_match": False}
        c0 = li >= 1.0
        c1 = atr14 > 0 and abs(c - ctx.prev_close) / atr14 <= 0.5
        c2 = ("LONG" if lm > 0 else "SHORT") == side
        comps.update(leader_impulse_ge_1atr=c0, lag_quiet_le_0p5atr=c1, side_match=c2)
        return c0 and c1 and c2, comps

    if family in POI_FAMILIES:
        zl, zh = extra.get("zl"), extra.get("zh")
        if zl is None:
            return False, {"price_within_tolerance": False}
        prox = 0.0 if zl <= c <= zh else min(abs(c - zl), abs(c - zh)) / c if c > 0 else math.inf
        fires = prox <= PROX_TOL
        comps["price_within_tolerance"] = fires
        return fires, comps

    return False, {}


# ---------------------------------------------------------------- family extras
def orb_extra(symbol, ctx):
    bars = ctx.bars
    i = ctx.i
    latest = bars[i]
    sess = _session_at(symbol, latest[0])
    if sess == "off_configured_session" or str(sess).startswith("moonshot_h"):
        return {"rh": None, "rl": None, "prev_break": None, "session": sess}
    j = i
    while j > 0:
        prev = bars[j - 1]
        if prev[0].date() != latest[0].date():
            break
        if _session_at(symbol, prev[0]) != sess:
            break
        j -= 1
    rc = j + 1
    if i <= rc:
        return {"rh": None, "rl": None, "prev_break": None, "session": sess}
    rb = bars[j:rc + 1]
    rh = max(x[2] for x in rb)
    rl = min(x[3] for x in rb)
    prev_break = any(x[4] > rh or x[4] < rl for x in bars[rc + 1:i])
    return {"rh": rh, "rl": rl, "prev_break": prev_break, "session": sess,
            "range_close_index": rc, "bars_since_range": i - rc}


_LEAD_FOR = {}
for _ldr, _lag in LEAD_LAG_PAIRS:
    _LEAD_FOR.setdefault(_lag, []).append(_ldr)
_CANON_TO_FILE = {}


def _file_symbol(canon):
    if canon in _CANON_TO_FILE:
        return _CANON_TO_FILE[canon]
    cand = canon
    if canon.endswith("_CASH"):
        cand = canon[:-5] + "_cash"
    if not os.path.isfile(os.path.join(x2_bars.M15_DIR, f"{cand}_M15.csv")):
        cand = None
    _CANON_TO_FILE[canon] = cand
    return cand


def leadlag_extra(symbol, ctx, side):
    """Leader condition is measured on the leader bar that CLOSES when the decision
    bar OPENS -> fully known 15 minutes early."""
    canon = _canonical_symbol(symbol)
    best = {"leader_impulse": None, "leader_move": None, "leader_symbol": None}
    want_open = ctx.bars[ctx.i][0] - timedelta(minutes=15)
    for ldr in _LEAD_FOR.get(canon, []):
        fs = _file_symbol(ldr)
        if fs is None:
            continue
        lb, lt = x2_bars.m15(fs)
        k = bisect_left(lt, want_open)
        if k >= len(lt) or lt[k] != want_open or k < 50:
            continue
        latr = sum(x[2] - x[3] for x in lb[k - 13:k + 1]) / 14.0
        if latr <= 0:
            continue
        mv = lb[k][4] - lb[k - 1][4]
        imp = abs(mv) / latr
        sd = "LONG" if mv > 0 else "SHORT"
        if sd == side and imp >= 1.0:
            return {"leader_impulse": imp, "leader_move": mv, "leader_symbol": ldr}
        if best["leader_impulse"] is None or imp > best["leader_impulse"]:
            best = {"leader_impulse": imp, "leader_move": mv, "leader_symbol": ldr}
    return best


def poi_extra(family, side, row, ctx):
    """Recover the POI zone from the emitted geometry.
       entry = (zl+zh)/2 ; stop = zl - b*atr14 (LONG) | zh + b*atr14 (SHORT)."""
    b = BUFFER_ATR[family]
    e = row["entry_price"]
    s = row["stop_loss"]
    a = ctx.atr14_close
    if side == "LONG":
        zl = s + b * a
        zh = 2 * e - zl
    else:
        zh = s - b * a
        zl = 2 * e - zh
    if not (zh > zl):
        return {"zl": None, "zh": None}
    return {"zl": zl, "zh": zh, "zone_width_atr": (zh - zl) / a if a > 0 else None}


def poi_backwalk(symbol, T, zl, zh, cap=BACKWALK_CAP):
    """How many minutes before the decision was proximity <= tol CONTINUOUSLY satisfied
       (using each M1 bar's close)?  Returns (minutes, censored)."""
    bars, times = x2_bars.m1(symbol)
    end = bisect_left(times, T)          # bars strictly before T
    n = 0
    k = end - 1
    while k >= 0 and n < cap:
        c = bars[k][4]
        prox = 0.0 if zl <= c <= zh else (min(abs(c - zl), abs(c - zh)) / c if c > 0 else math.inf)
        if prox > PROX_TOL:
            break
        n += 1
        k -= 1
    return n, n >= cap


# ---------------------------------------------------------------- main
def main():
    rows = w0_ws.load()
    rows.sort(key=lambda r: (r["symbol"], r["decision_time_utc"]))
    out = gzip.open(OUT, "wt")
    n = 0
    for r in rows:
        sym = r["symbol"]
        fam = r["origin_family"]
        side = r["side"]
        T = datetime.fromisoformat(r["decision_time_utc"])
        rec = {
            "candidate_id": r["candidate_id"],
            "decision_time_utc": r["decision_time_utc"],
            "symbol": sym,
            "origin_family": fam,
            "side": side,
            "gross_r": r.get("gross_r"),
            "plain_walk_r": r.get("plain_walk_r"),
            "risk_distance": r.get("risk_distance"),
            "is_first_emission": r.get("is_first_emission"),
        }
        ctx = build_ctx(sym, r["decision_time_utc"])
        if ctx is None:
            rec["status"] = "no_m15_context"
            out.write(json.dumps(rec) + "\n")
            n += 1
            continue
        ps = partials(sym, r["decision_time_utc"], ctx)
        rec["m1_minutes_present"] = len(ps)
        if fam == "session_open_range_break":
            extra = orb_extra(sym, ctx)
        elif fam == "cross_asset_lead_lag":
            extra = leadlag_extra(sym, ctx, side)
        elif fam in POI_FAMILIES:
            extra = poi_extra(fam, side, r, ctx)
        else:
            extra = {}
        rec["extra"] = {k: v for k, v in extra.items()
                        if k in ("session", "bars_since_range", "leader_symbol",
                                 "leader_impulse", "zone_width_atr")}

        # closed-bar truth (validation): predicate on the completed M15 bar
        fires_close, comps_close = eval_family(fam, side, ctx, ctx.o, ctx.h, ctx.l, ctx.c, extra)
        rec["reproduces_at_close"] = bool(fires_close)
        rec["comps_at_close"] = comps_close

        first_true = None
        comp_first = {}
        true_minutes = []
        for (m, o, h, l, c) in ps:
            f, comps = eval_family(fam, side, ctx, o, h, l, c, extra)
            for k, v in comps.items():
                if v and k not in comp_first:
                    comp_first[k] = m
            if f:
                true_minutes.append(m)
                if first_true is None:
                    first_true = m
        rec["first_true_minute"] = first_true
        rec["comp_first_minute"] = comp_first
        rec["n_true_minutes"] = len(true_minutes)
        rec["true_at_minute_1"] = bool(true_minutes and true_minutes[0] == 1)
        rec["contiguous_from_first"] = bool(
            true_minutes and true_minutes == list(range(true_minutes[0], true_minutes[-1] + 1))
        )
        if first_true is not None:
            rec["earliness_min"] = 15 - first_true
            cm = next(p[4] for p in ps if p[0] == first_true)
            rec["price_at_first_true"] = cm
            rd = r.get("risk_distance") or 0.0
            if fam in CLOSE_ENTRY_FAMILIES and rd > 0:
                imp = (r["entry_price"] - cm) if side == "LONG" else (cm - r["entry_price"])
                rec["price_edge_r"] = imp / rd
        if fam in POI_FAMILIES and extra.get("zl") is not None:
            mins, cens = poi_backwalk(sym, T, extra["zl"], extra["zh"])
            rec["poi_prox_backwalk_min"] = mins
            rec["poi_prox_backwalk_censored"] = cens
        rec["status"] = "ok"
        out.write(json.dumps(rec) + "\n")
        n += 1
        if n % 4000 == 0:
            print(f"  {n}/{len(rows)}", flush=True)
    out.close()
    print("wrote", OUT, n)


if __name__ == "__main__":
    main()
