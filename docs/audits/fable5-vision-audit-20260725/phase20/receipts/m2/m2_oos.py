"""m2_oos — the NEVER-READ out-of-sample window, on real bid/ask ticks.

Window: 2026-06-18 .. 2026-07-24, which is AFTER the last roster window (2026-05) and is
therefore untouched by any economic read of this family. Both inputs are broker wall
clock and are converted with `src.utils.broker_clock` (NEW_YORK_PLUS_7), never with a
hardcoded offset:

  bars   /Users/borr/GTOSActive/vps-bars-20260727/FTMO_<sym>_M15.csv.gz  (to 2026-07-24)
  ticks  /Users/borr/GTOSActive/vps-ticks-20260726/ftmo/FTMO_<sym>_ticks_*.csv.gz

The bar<->tick pairing is SELF-VALIDATING: a symbol is used only if the M15 close equals
the last tick bid strictly before the bar's close instant on >= 99 % of in-window bars.
A wrong symbol mapping or a wrong clock cannot pass that test.

Candidates come from `m2_emit.emit_sde`, which reproduces the frozen wave-19 roster
exactly (M2_REPRO_V1.json) — so this is the same family, not a lookalike.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import json
import os
import sys
from pathlib import Path

import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
sys.path.insert(0, REPO)
sys.path.insert(0, "/tmp/m2")
from src.utils.broker_clock import broker_epoch_to_utc, resolve_rule  # noqa: E402
from m2_emit import emit_sde  # noqa: E402

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
TICKS = "/Users/borr/GTOSActive/vps-ticks-20260726/ftmo"
CACHE = "/tmp/m2/oos_cache"
EPOCH = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
RULE = resolve_rule("FTMO-Server3")
BIG = 1 << 62

# broad-universe name -> vps-ticks file name.  Verified by the BID identity test below.
TICK_NAME = {"GER40": "GER40_cash", "JP225": "JP225_cash", "NAS100": "US100_cash",
             "SPX500": "US500_cash", "UK100": "UK100_cash"}
UNIVERSE = ("AUDJPY", "AUDUSD", "BTCUSD", "CHFJPY", "ETHUSD", "EURGBP", "EURJPY",
            "EURUSD", "GBPJPY", "GBPUSD", "GER40", "JP225", "NAS100", "NZDUSD",
            "SPX500", "UK100", "UKOIL_cash", "US30_cash", "USDCAD", "USDCHF",
            "USDJPY", "USOIL_cash", "XAGUSD", "XAUUSD")

W0 = dt.datetime(2026, 6, 18, tzinfo=dt.timezone.utc)
W1 = dt.datetime(2026, 7, 24, tzinfo=dt.timezone.utc)
TARGETS = (1.5, 2.0)
HORIZONS = (120, 240, 1440)


def _ms(d: dt.datetime) -> int:
    return int((d - EPOCH).total_seconds() * 1000)


def load_bars(sym):
    p = f"{BARS}/FTMO_{sym}_M15.csv.gz"
    if not os.path.isfile(p):
        return None
    t, o, h, l, c = [], [], [], [], []
    with gzip.open(p, "rt") as fh:
        for r in csv.DictReader(fh):
            t.append(int(r["time"])); o.append(float(r["open"])); h.append(float(r["high"]))
            l.append(float(r["low"])); c.append(float(r["close"]))
    # broker epoch (seconds) -> true UTC ms
    tu = np.array([_ms(broker_epoch_to_utc(x, RULE)) for x in t], dtype=np.int64)
    o = np.array(o); h = np.array(h); l = np.array(l); c = np.array(c)
    k = np.argsort(tu, kind="stable")
    return tu[k], o[k], h[k], l[k], c[k]


def load_ticks(sym):
    dst = f"{CACHE}/{sym}.npz"
    if os.path.isfile(dst):
        z = np.load(dst)
        return z["ts"], z["bid"], z["ask"]
    name = TICK_NAME.get(sym, sym)
    p = f"{TICKS}/FTMO_{name}_ticks_20260618_to_20260726.csv.gz"
    if not os.path.isfile(p):
        return None
    from array import array
    ts, bd, ak = array('q'), array('d'), array('d')
    with gzip.open(p, "rb") as fh:
        fh.readline()
        for line in fh:
            f = line.split(b',')
            try:
                ts.append(int(f[5])); bd.append(float(f[1])); ak.append(float(f[2]))
            except Exception:
                continue
    T = np.asarray(ts, dtype=np.int64); B = np.asarray(bd); A = np.asarray(ak)
    # broker epoch MILLISECONDS -> true UTC ms.  Offset is a whole number of hours and
    # constant across this window (all of it is US EDT), but it is DERIVED per row from
    # the rule rather than assumed.
    off = np.array([int((broker_epoch_to_utc(int(x / 1000), RULE)
                         - EPOCH).total_seconds()) * 1000 - (int(x / 1000) * 1000)
                    for x in (T[0], T[len(T) // 2], T[-1])], dtype=np.int64)
    assert len(set(off.tolist())) == 1, f"{sym}: broker offset not constant in window: {off}"
    T = T + int(off[0])
    k = np.argsort(T, kind="stable")
    T, B, A = T[k], B[k], A[k]
    os.makedirs(CACHE, exist_ok=True)
    np.savez(dst + ".tmp.npz", ts=T, bid=B, ask=A)
    os.replace(dst + ".tmp.npz", dst)
    return T, B, A


def bid_identity(bt, bc, ts, bd, lo_ms, hi_ms):
    """M15 close == last tick bid strictly before the bar's close instant?"""
    n_ok = n = 0
    for k in range(len(bt)):
        close_ms = int(bt[k]) + 15 * 60_000
        if not (lo_ms <= close_ms <= hi_ms):
            continue
        j = int(np.searchsorted(ts, close_ms, "left"))
        if j == 0:
            continue
        # require the previous tick to be inside the bar
        if int(ts[j - 1]) < int(bt[k]):
            continue
        n += 1
        n_ok += int(abs(float(bd[j - 1]) - float(bc[k])) < 1e-9)
    return n, n_ok


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


def bar_walk_m15(bh, bl, bc, i0, i1, lng, sl, tp):
    """Estate convention on M15 bid bars (the only bar resolution this archive has)."""
    hs = (bl[i0:i1] <= sl) if lng else (bh[i0:i1] >= sl)
    ht = (bh[i0:i1] >= tp) if lng else (bl[i0:i1] <= tp)
    a_s = int(np.argmax(hs)) if hs.any() else BIG
    a_t = int(np.argmax(ht)) if ht.any() else BIG
    if a_s == BIG and a_t == BIG:
        return float(bc[i1 - 1]), 2
    if a_s <= a_t:
        return sl, 0
    return tp, 1


def main(sym, out):
    b = load_bars(sym)
    if b is None:
        sys.stderr.write(f"{sym}: no bars\n"); return
    bt, bo, bh, bl, bc = b
    tk = load_ticks(sym)
    if tk is None:
        sys.stderr.write(f"{sym}: no ticks\n"); return
    ts, bd, ak = tk
    lo_ms, hi_ms = int(ts[0]), int(ts[-1])

    n_id, n_ok = bid_identity(bt, bc, ts, bd, max(lo_ms, _ms(W0)), min(hi_ms, _ms(W1)))
    frac = n_ok / max(n_id, 1)

    idx, lng_a, e_a, s_a, tp_a, pos_a, atr_a = emit_sde(bo, bh, bl, bc, target_rr=1.5)
    res = {"symbol": sym, "tick_name": TICK_NAME.get(sym, sym),
           "bid_identity_n": n_id, "bid_identity_frac": frac,
           "n_bars": len(bt), "n_ticks": int(len(ts)),
           "tick_first_utc": dt.datetime.fromtimestamp(lo_ms / 1000, dt.timezone.utc).isoformat(),
           "tick_last_utc": dt.datetime.fromtimestamp(hi_ms / 1000, dt.timezone.utc).isoformat(),
           "rows": []}
    if frac < 0.99:
        res["status"] = "REJECTED_bar_tick_pairing"
        Path(out).write_text(json.dumps(res))
        sys.stderr.write(f"{sym}: REJECTED bid identity {n_ok}/{n_id} = {frac:.4f}\n")
        return
    res["status"] = "OK"

    w0, w1 = _ms(W0), _ms(W1)
    for k, L_, E, S in zip(idx, lng_a, e_a, s_a):
        T = int(bt[k]) + 15 * 60_000           # the decision instant
        if not (w0 <= T <= w1):
            continue
        if T <= lo_ms or T > hi_ms:
            continue
        j = int(np.searchsorted(ts, T, "left"))
        if j == 0 or int(ts[j - 1]) < int(bt[k]):
            continue
        b0 = float(bd[j - 1]); a0 = float(ak[j - 1])
        if abs(b0 - float(E)) > 1e-9:
            continue                            # the row's own join must be exact
        d = abs(float(E) - float(S))
        if not (d > 0):
            continue
        s = 1.0 if L_ else -1.0
        fill = a0 if L_ else b0
        spread = a0 - b0
        rec = {"sym": sym, "t": dt.datetime.fromtimestamp(T / 1000, dt.timezone.utc).isoformat(),
               "day": dt.datetime.fromtimestamp(T / 1000, dt.timezone.utc).date().isoformat(),
               "long": bool(L_), "e": float(E), "sl": float(S), "d": d,
               "d_bps": d / float(E) * 1e4, "spread": spread,
               "spread_bps": spread / float(E) * 1e4, "spread_over_d": spread / d}
        for tr in TARGETS:
            tp = float(E) + s * tr * d
            tp_f = fill + s * tr * d
            for hm in HORIZONS:
                key = f"{tr:g}_{hm}"
                if T + hm * 60_000 > hi_ms:
                    for pre in ("bar", "tbid", "fill", "lvl", "code", "barcode"):
                        rec[f"{pre}_{key}"] = None
                    continue
                i_bar = int(np.searchsorted(bt, T, "left"))
                bw = bar_walk_m15(bh, bl, bc, i_bar, min(i_bar + hm // 15, len(bt)), L_, float(S), tp)
                rec[f"bar_{key}"] = s * (bw[0] - float(E)) / d
                rec[f"barcode_{key}"] = bw[1]
                tb = tick_walk(ts, bd, ak, j, T, hm * 60_000, L_, float(S), tp, one_sided=True)
                rec[f"tbid_{key}"] = None if tb is None else s * (tb[0] - float(E)) / d
                tf = tick_walk(ts, bd, ak, j, T, hm * 60_000, L_, fill - s * d, tp_f)
                rec[f"fill_{key}"] = None if tf is None else s * (tf[0] - fill) / d
                rec[f"code_{key}"] = None if tf is None else tf[1]
                tl = tick_walk(ts, bd, ak, j, T, hm * 60_000, L_, float(S), tp)
                rec[f"lvl_{key}"] = None if tl is None else s * (tl[0] - fill) / d
                mlng = not bool(L_)
                ms_ = -s
                mfill = a0 if mlng else b0
                mtf = tick_walk(ts, bd, ak, j, T, hm * 60_000, mlng,
                                mfill - ms_ * d, mfill + ms_ * tr * d)
                rec[f"mir_{key}"] = None if mtf is None else ms_ * (mtf[0] - mfill) / d
                mtb = tick_walk(ts, bd, ak, j, T, hm * 60_000, mlng,
                                float(E) - ms_ * d, float(E) + ms_ * tr * d, one_sided=True)
                rec[f"mirbar_{key}"] = None if mtb is None else ms_ * (mtb[0] - float(E)) / d
                rec[f"tbidcode_{key}"] = None if tb is None else tb[1]
        mid0 = 0.5 * (b0 + a0)
        for hh, mins in (("15m", 15), ("2h", 120), ("8h", 480), ("24h", 1440),
                         ("72h", 4320), ("160h", 9600), ("320h", 19200)):
            if T + mins * 60_000 > hi_ms:
                rec[f"cap_{hh}"] = rec[f"capg_{hh}"] = rec[f"capm_{hh}"] = None
                continue
            kk = int(np.searchsorted(ts, T + mins * 60_000, "left")) - 1
            if kk < j:
                rec[f"cap_{hh}"] = rec[f"capg_{hh}"] = rec[f"capm_{hh}"] = None
            else:
                px = float(bd[kk]) if L_ else float(ak[kk])
                rec[f"cap_{hh}"] = s * (px - fill) / fill * 1e4
                rec[f"capg_{hh}"] = s * (float(bd[kk]) - b0) / b0 * 1e4
                mk = 0.5 * (float(bd[kk]) + float(ak[kk]))
                rec[f"capm_{hh}"] = s * (mk - mid0) / mid0 * 1e4
        res["rows"].append(rec)

    Path(out).write_text(json.dumps(res))
    sys.stderr.write(f"{sym}: bid_id {n_ok}/{n_id}={frac:.4f}  rows {len(res['rows'])}\n")


if __name__ == "__main__":
    if sys.argv[1] == "ALL":
        for s in UNIVERSE:
            main(s, f"/tmp/m2/oos/{s}.json")
    else:
        main(sys.argv[1], sys.argv[2])
