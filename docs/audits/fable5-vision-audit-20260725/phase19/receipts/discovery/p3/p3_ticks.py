"""p3 — TICK-RESOLUTION adjudication of the quote-side attack.

The lane hold carries true-UTC BID/ASK ticks for XAUUSD, XAGUSD, EURUSD, USDJPY
across the open windows.  This settles two things by measurement rather than model:

  1. are the bridge_ftmo_m1_* bars the lanes walk BID? (d8x settled it on a
     DIFFERENT archive — vps-bars-20260727 M15 — and flagged the transfer as open)
  2. what the roster rows actually do when entry, stop and target are triggered on
     the side of the book MT5 triggers them on, at tick resolution, with no bar,
     no OHLC and therefore no tie rule at all.

Usage:  python3 p3_ticks.py <SYMBOL> <YYYYMM>
"""
from __future__ import annotations
import glob
import gzip
import json
import os
import sys
from datetime import datetime, timezone, timedelta

import numpy as np

TICKS = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
         "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/ticks")
BARS = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
        "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
ROSTER = {"202510": "/tmp/f1/roster_202510", "202511": "/tmp/f1/roster_202511",
          "202512": "/tmp/f1/roster_202512", "202601": "/tmp/pbg_full_jan",
          "202602": "/tmp/pbg_full_feb", "202603": "/tmp/pbg_full_mar",
          "202604": "/tmp/f1/roster_202604", "202605": "/tmp/f1/roster_202605"}
NEXT = {"202510": "202511", "202511": "202512", "202512": "202601", "202601": "202602",
        "202602": "202603", "202603": "202604", "202604": "202605", "202605": None}
HOR_MS = 120 * 60 * 1000
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_DAY = {}


def day_ms(ds: bytes) -> int:
    v = _DAY.get(ds)
    if v is None:
        d = datetime(int(ds[0:4]), int(ds[5:7]), int(ds[8:10]), tzinfo=timezone.utc)
        v = int((d - EPOCH).total_seconds()) * 1000
        _DAY[ds] = v
    return v


def load_ticks(sym, months):
    from array import array
    ts, bd, ak = array('q'), array('d'), array('d')
    for mm in months:
        p = f"{TICKS}/{mm}/{sym}/microstructure_ticks.jsonl"
        if not os.path.isfile(p):
            continue
        with open(p, "rb") as f:
            for line in f:
                try:
                    i = line.index(b',', 7)
                    a = float(line[7:i])
                    j = line.index(b',', i + 7)
                    b = float(line[i + 7:j])
                    k = line.index(b'"time":"') + 8
                    s = line[k:k + 26]
                    t = (day_ms(s[0:10]) + int(s[11:13]) * 3600000 + int(s[14:16]) * 60000
                         + int(s[17:19]) * 1000 + int(s[20:23]))
                except Exception:
                    continue
                ts.append(t); bd.append(b); ak.append(a)
    ts = np.asarray(ts, dtype=np.int64)
    bd = np.asarray(bd)
    ak = np.asarray(ak)
    o = np.argsort(ts, kind="stable")
    return ts[o], bd[o], ak[o]


def verify_bid(sym, month, ts, bd, ak):
    """Compare every M1 bar of the pack against the ticks inside its own minute."""
    p = f"{BARS}/bridge_ftmo_m1_{month}/{sym}_M1.csv"
    rows = []
    with open(p) as fh:
        fh.readline()
        for line in fh:
            f = line.rstrip("\n").split(",")
            d = datetime.fromisoformat(f[0])
            rows.append((int((d - EPOCH).total_seconds()) * 1000,
                         float(f[1]), float(f[2]), float(f[3]), float(f[4])))
    out = {"n_bars": 0, "close_eq_bid": 0, "close_eq_ask": 0,
           "d_close_bid_over_spread": [], "d_close_mid_over_spread": [],
           "d_high_maxbid": [], "d_low_minbid": [], "spread_px": []}
    for t0, o, h, l, c in rows:
        a = int(np.searchsorted(ts, t0, "left"))
        b = int(np.searchsorted(ts, t0 + 60000, "left"))
        if b - a < 3:
            continue
        lb, la = bd[b - 1], ak[b - 1]
        sp = float(np.median(ak[a:b] - bd[a:b]))
        if sp <= 0:
            continue
        out["n_bars"] += 1
        out["close_eq_bid"] += int(abs(c - lb) < 1e-9)
        out["close_eq_ask"] += int(abs(c - la) < 1e-9)
        out["d_close_bid_over_spread"].append((c - lb) / sp)
        out["d_close_mid_over_spread"].append((c - (lb + la) / 2.0) / sp)
        out["d_high_maxbid"].append((h - float(bd[a:b].max())) / sp)
        out["d_low_minbid"].append((l - float(bd[a:b].min())) / sp)
        out["spread_px"].append(sp)
    r = {"symbol": sym, "month": month, "n_bars": out["n_bars"],
         "close_exactly_equals_last_tick_BID": out["close_eq_bid"] / max(out["n_bars"], 1),
         "close_exactly_equals_last_tick_ASK": out["close_eq_ask"] / max(out["n_bars"], 1)}
    for k in ("d_close_bid_over_spread", "d_close_mid_over_spread",
              "d_high_maxbid", "d_low_minbid"):
        v = np.asarray(out[k])
        r[k] = {"median": float(np.median(v)), "p05": float(np.percentile(v, 5)),
                "p95": float(np.percentile(v, 95))}
    r["median_spread_px"] = float(np.median(out["spread_px"]))
    return r


def tickwalk(ts, bd, ak, t_ms, e, sl, tp2, lng, mkt):
    """Return (filled, r_gross_levelentry, r_true_transacted, code) with MT5 sides."""
    i0 = int(np.searchsorted(ts, t_ms, "left"))
    i1 = int(np.searchsorted(ts, t_ms + HOR_MS, "left"))
    if i1 - i0 < 2:
        return None
    d = abs(e - sl)
    if lng:
        ent = ak[i0:i1]           # a BUY triggers on the ASK
    else:
        ent = bd[i0:i1]           # a SELL triggers on the BID
    if abs(mkt) < 1e-12:
        j = 0
        px_true = float(ent[0])
    else:
        above = ent[0] > e        # where the tradable side sits vs the level now
        hit = (ent <= e) if above else (ent >= e)
        if not hit.any():
            return (0, 0.0, 0.0, 3)
        j = int(np.argmax(hit))
        px_true = e
    a = i0 + j + 1
    if a >= i1:
        return (0, 0.0, 0.0, 3)
    if lng:
        ex = bd[a:i1]             # a LONG's SL/TP trigger on the BID
        hs = ex <= sl
        ht = ex >= tp2
    else:
        ex = ak[a:i1]             # a SHORT's SL/TP trigger on the ASK
        hs = ex >= sl
        ht = ex <= tp2
    any_s, any_t = hs.any(), ht.any()
    i_s = int(np.argmax(hs)) if any_s else 1 << 30
    i_t = int(np.argmax(ht)) if any_t else 1 << 30
    if not any_s and not any_t:
        px_exit = float(ex[-1]); code = 2
    elif i_s <= i_t:
        px_exit = sl; code = 0
    else:
        px_exit = tp2; code = 1
    s = 1.0 if lng else -1.0
    return (1, s * (px_exit - e) / d, s * (px_exit - px_true) / d, code)


def main(sym, month):
    months = [month] + ([NEXT[month]] if NEXT.get(month) else [])
    ts, bd, ak = load_ticks(sym, [month])
    sys.stderr.write("%s %s ticks %d\n" % (sym, month, len(ts)))
    res = {"bid_verification": verify_bid(sym, month, ts, bd, ak)}
    sys.stderr.write("bid check done\n")

    rows = []
    for f in sorted(glob.glob(ROSTER[month] + "/*.jsonl.gz")):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if r["k"] == 15 and r["s"] == sym:
                    rows.append(r)
    # the bar tape, for mkt_r0 and the bar-walk comparison
    sys.path.insert(0, "/tmp/p3")
    from p3_walk import load_tape, outcome, fill_index
    t0, n, O, H, L, C = load_tape(months)
    h, l, c = H[sym], L[sym], C[sym]
    ok = ~np.isnan(c)

    acc = {k: [] for k in ("mkt", "bar_BC", "bar_SPRMT5", "tick_gross", "tick_true",
                           "f_BC", "f_tick", "code")}
    tlast = int(ts[-1])
    for r in rows:
        tsd = datetime.fromisoformat(r["t"])
        i = int((tsd - t0).total_seconds() // 60)
        if not (0 < i < n - 2):
            continue
        if int((tsd - EPOCH).total_seconds()) * 1000 + HOR_MS > tlast:
            continue          # keep both arms on identical rows
        e = float(r["e"]); slv = float(r["sl"]); d = abs(e - slv)
        if not (d > 0):
            continue
        lng = r["d"] == "L"
        s = 1.0 if lng else -1.0
        m0 = c[i - 1]
        if m0 != m0:
            continue
        mkt = s * (m0 - e) / d
        tgt = e + s * 2.0 * d
        b = min(i + 120, n)
        # bar walk, BC convention
        if abs(mkt) < 1e-12:
            fi = i
        else:
            fi = fill_index(h, l, ok, i, b, e, from_below=(m0 < e))
        if fi < 0:
            fbc, rbc = 0, 0.0
        else:
            o1 = outcome(h, l, c, ok, fi + 1, b, lng, e, slv, tgt, d, True)
            fbc, rbc = (0, 0.0) if o1 is None else (1, o1[0])
        # bar walk, modelled MT5 shift
        sp = float(np.median(ak[max(0, int(np.searchsorted(ts, int((tsd - EPOCH).total_seconds()) * 1000)) - 20):
                                int(np.searchsorted(ts, int((tsd - EPOCH).total_seconds()) * 1000)) + 1]
                             - bd[max(0, int(np.searchsorted(ts, int((tsd - EPOCH).total_seconds()) * 1000)) - 20):
                                  int(np.searchsorted(ts, int((tsd - EPOCH).total_seconds()) * 1000)) + 1])) \
            if len(ts) else 0.0
        if not (sp == sp) or sp <= 0:
            sp = 0.0
        if lng:
            lvl = e - sp
            fis = i if abs(mkt) < 1e-12 else fill_index(h, l, ok, i, b, lvl, from_below=(m0 < e))
            sl3, tg3 = slv, tgt
        else:
            fis = fi
            sl3, tg3 = slv - sp, tgt - sp
        if fis < 0:
            rmt5 = 0.0
        else:
            o2 = outcome(h, l, c, ok, fis + 1, b, lng, e, sl3, tg3, d, True)
            if o2 is None:
                rmt5 = 0.0
            else:
                rmt5 = -1.0 if o2[1] == 0 else (2.0 if o2[1] == 1 else o2[0])
        tw = tickwalk(ts, bd, ak, int((tsd - EPOCH).total_seconds()) * 1000,
                      e, slv, tgt, lng, mkt)
        if tw is None:
            continue
        acc["mkt"].append(mkt); acc["bar_BC"].append(rbc); acc["bar_SPRMT5"].append(rmt5)
        acc["tick_gross"].append(tw[1]); acc["tick_true"].append(tw[2])
        acc["f_BC"].append(fbc); acc["f_tick"].append(tw[0]); acc["code"].append(tw[3])
    A = {k: np.asarray(v, dtype=np.float64) for k, v in acc.items()}
    nn = len(A["mkt"])
    res["walk"] = {
        "symbol": sym, "month": month, "n": int(nn),
        "bar_BC_gross_per_opp": float(A["bar_BC"].mean()),
        "bar_SPRMT5_gross_per_opp": float(A["bar_SPRMT5"].mean()),
        "tick_gross_per_opp": float(A["tick_gross"].mean()),
        "tick_true_per_opp": float(A["tick_true"].mean()),
        "fill_rate_bar_BC": float((A["f_BC"] > 0).mean()),
        "fill_rate_tick": float((A["f_tick"] > 0).mean()),
        "bar_BC_gross_per_fill": float(A["bar_BC"][A["f_BC"] > 0].mean()),
        "tick_gross_per_fill": float(A["tick_gross"][A["f_tick"] > 0].mean()),
        "tick_true_per_fill": float(A["tick_true"][A["f_tick"] > 0].mean()),
        "exit_mix_tick": {k: float((A["code"][A["f_tick"] > 0] == v).mean())
                          for k, v in (("stop", 0), ("target", 1), ("path_end", 2))},
        "by_segment": {},
    }
    for lab, m in (("limit", A["mkt"] > 1e-12), ("at_market", np.abs(A["mkt"]) < 1e-12),
                   ("stopentry", A["mkt"] < -1e-12)):
        if m.sum():
            res["walk"]["by_segment"][lab] = {
                "n": int(m.sum()), "bar_BC": float(A["bar_BC"][m].mean()),
                "bar_SPRMT5": float(A["bar_SPRMT5"][m].mean()),
                "tick_gross": float(A["tick_gross"][m].mean()),
                "tick_true": float(A["tick_true"][m].mean())}
    json.dump(res, open("/tmp/p3/P3_TICK_%s_%s.json" % (sym, month), "w"), indent=1)
    print(json.dumps(res, indent=1)[:2600])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
