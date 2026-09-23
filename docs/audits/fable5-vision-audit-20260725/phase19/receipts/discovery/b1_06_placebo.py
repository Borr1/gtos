"""b1 step 6 — THE CONTROL. Does b1-BOOK-V1 beat a book with the signal removed?

Rebuild the identical book with the DECISION INSTANT shifted, keeping the instrument,
the side, the risk unit, the cost, the gate and the exit contract exactly as they are.
The signal is decorrelated; every structural feature survives.

Two families of shift, and the second is the sharp one:
  intraday  -120 -60 +60 +120 +180 min : same day, different instant
  whole-day -2880 -1440 +1440 +2880 min: THE SAME BROKER HOUR on a different day, so
            the instrument x hour x cost structure is preserved EXACTLY. If b1-BOOK-V1
            is "index CFDs are cheap in these hours and drift up", this control pays.

Plus a side-flip control (same instants, opposite direction).
"""
import bisect
import csv
import gzip
import json
import os
import sys
import time
from datetime import datetime, timedelta

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import b1_np as N  # noqa: E402

BARS = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
        "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
HZ = 120
K = 3
GATE = 0.60
SHIFTS = [-2880, -1440, -120, -60, 60, 120, 180, 1440, 2880]
_bars = {}


def load_bars(sym):
    if sym in _bars:
        return _bars[sym]
    ts, h, l, c = [], [], [], []
    for mm in ("202512", "202601", "202602", "202603", "202604"):
        p = os.path.join(BARS, f"bridge_ftmo_m1_{mm}", f"{sym}_M1.csv")
        if not os.path.isfile(p):
            continue
        with open(p) as f:
            rd = csv.reader(f)
            next(rd)
            for r in rd:
                ts.append(r[0]); h.append(float(r[2])); l.append(float(r[3])); c.append(float(r[4]))
    if not ts:
        _bars[sym] = None
        return None
    o = sorted(range(len(ts)), key=lambda i: ts[i])
    _bars[sym] = {"t": [ts[i] for i in o], "h": [h[i] for i in o],
                  "l": [l[i] for i in o], "c": [c[i] for i in o]}
    return _bars[sym]


def walk_one(fav, adv, cls, k):
    """b1's exact exit contract: stop -1R from the k-bar fill, no target, no trail,
    close at the 120-minute horizon. Conservative tie rule (stop wins in a bar)."""
    n = len(fav)
    if n <= k:
        return None
    c0 = cls[k - 1] if k > 0 else 0.0
    for i in range(k, n):
        if adv[i] - c0 <= -1.0 + 1e-12:
            return -1.0
    return cls[n - 1] - c0


def build(rows, shift, flip=False):
    out = []
    for r in rows:
        b = load_bars(r["symbol"])
        if b is None:
            continue
        dt = (datetime.fromisoformat(r["dt"]) + timedelta(minutes=shift)).isoformat()
        i = bisect.bisect_right(b["t"], dt) - 1
        if i < 1:
            continue
        entry = b["c"][i]
        d = float(r["risk_distance"])
        sgn = (1.0 if r["side"] == "LONG" else -1.0) * (-1.0 if flip else 1.0)
        end = (datetime.fromisoformat(dt) + timedelta(minutes=120)).isoformat()
        fav, adv, cls = [], [], []
        for kx in range(i + 1, min(i + 126, len(b["t"]))):
            if b["t"][kx] > end:
                break
            if b["t"][kx] <= dt:
                continue
            hi = sgn * (b["h"][kx] - entry) / d
            lo = sgn * (b["l"][kx] - entry) / d
            fav.append(max(hi, lo)); adv.append(min(hi, lo))
            cls.append(sgn * (b["c"][kx] - entry) / d)
            if len(fav) >= HZ:
                break
        if len(fav) < K + 3:
            continue
        g = walk_one(fav, adv, cls, K)
        if g is None:
            continue
        out.append((g, r))
    return out


def stat(pairs, key="cost_h1_r"):
    if not pairs:
        return {"n": 0}
    g = np.array([p[0] for p in pairs])
    c = np.array([p[1][key] for p in pairs])
    net = g - c
    bf = np.array([p[1]["rdp"] * 1e4 for p in pairs])
    day = np.array([p[1]["day"] for p in pairs])
    ud, inv = np.unique(day, return_inverse=True)
    G = len(ud)
    dsum = np.bincount(inv, weights=net, minlength=G)
    dcnt = np.bincount(inv, minlength=G)
    mn = float(net.mean())
    resid = dsum - mn * dcnt
    ss = float((resid ** 2).sum())
    td = float(mn / (np.sqrt(ss) / len(net) * np.sqrt(G / max(G - 1, 1)))) if ss > 0 else None
    return {"n": len(g), "gross_R": float(g.mean()), "cost_R": float(c.mean()),
            "net_R": mn, "ratio_R": float(g.mean() / c.mean()),
            "net_bps": float((net * bf).mean()),
            "t_net": float(mn / (net.std(ddof=1) / np.sqrt(len(net)))),
            "t_net_day": td,
            "n_days_net_pos": int((dsum / dcnt > 0).sum()), "n_days": G}


def main():
    t0 = time.time()
    M, G, _ = N.load()
    rows = [json.loads(x) for x in gzip.open(f"{D}/h5_SUBSTRATE_5M.jsonl.gz", "rt") if x.strip()]
    h1 = {}
    for ln in gzip.open(f"{D}/b1_COST_JOIN_V1.jsonl.gz", "rt"):
        o = json.loads(ln)
        h1[(o["cid"], o["dt"])] = o
    book = []
    for r in rows:
        o = h1.get((r["cid"], r["dt"]))
        if o is None:
            continue
        cb = o["cost_h1_r"] * r["rdp"] * 1e4
        if cb <= GATE + 1e-12 and r.get("K3_STOPONLY") is not None:
            r["cost_h1_r"] = o["cost_h1_r"]
            book.append(r)
    print("book rows", len(book), "symbols", sorted({r["symbol"] for r in book}), flush=True)

    out = {"gate_bps": GATE, "k": K, "exit": "STOPONLY(-1R, no target, no trail, 120min)",
           "book_n_from_substrate": len(book)}
    real = [(r["K3_STOPONLY"], r) for r in book]
    out["REAL"] = stat(real)
    print("REAL", {k: round(v, 5) if isinstance(v, float) else v
                   for k, v in out["REAL"].items()}, flush=True)

    # sanity: the rebuilt-from-bars real anchor must reproduce the substrate value
    chk = build(book, 0)
    out["REAL_rebuilt_from_bars"] = stat(chk)
    diffs = []
    idx = {(p[1]["cid"], p[1]["dt"]): p[0] for p in chk}
    for r in book:
        v = idx.get((r["cid"], r["dt"]))
        if v is not None:
            diffs.append(abs(v - r["K3_STOPONLY"]))
    out["rebuild_check"] = {"n_matched": len(diffs),
                            "max_abs_diff": (max(diffs) if diffs else None),
                            "mean_abs_diff": (float(np.mean(diffs)) if diffs else None)}
    print("rebuild check", out["rebuild_check"], flush=True)

    for sh in SHIFTS:
        out[f"shift_{sh}"] = stat(build(book, sh))
        s = out[f"shift_{sh}"]
        print(f"shift {sh:+6d}  n={s['n']:>5} gross={s['gross_R']:>+8.5f} "
              f"net={s['net_R']:>+8.5f} ratio={s['ratio_R']:>7.3f} t={s['t_net']:>+6.2f}",
              flush=True)

    out["SIDE_FLIP"] = stat(build(book, 0, flip=True))
    print("SIDE_FLIP", {k: round(v, 5) if isinstance(v, float) else v
                        for k, v in out["SIDE_FLIP"].items()}, flush=True)

    ph = [out[f"shift_{s}"]["net_R"] for s in SHIFTS if out[f"shift_{s}"]["n"]]
    whole = [out[f"shift_{s}"]["net_R"] for s in (-2880, -1440, 1440, 2880)
             if out[f"shift_{s}"]["n"]]
    out["summary"] = {
        "real_net_R": out["REAL"]["net_R"],
        "placebo_mean_net_R": float(np.mean(ph)),
        "placebo_max_net_R": float(np.max(ph)),
        "placebo_whole_day_mean_net_R": float(np.mean(whole)),
        "real_beats_n_of": f"{sum(1 for x in ph if out['REAL']['net_R'] > x)} of {len(ph)}",
        "signal_vs_placebo_mean": out["REAL"]["net_R"] - float(np.mean(ph)),
        "signal_vs_best_placebo": out["REAL"]["net_R"] - float(np.max(ph)),
    }
    out["elapsed_s"] = round(time.time() - t0, 1)
    with open(f"{D}/B1_PLACEBO_V1.json", "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out["summary"], indent=1))


if __name__ == "__main__":
    main()
