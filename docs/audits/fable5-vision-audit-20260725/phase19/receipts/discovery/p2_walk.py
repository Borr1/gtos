"""p2_walk — walk one sealed window's reproduced roster under every contract the
pre-declaration names.  One pass, no thresholds applied here.

Usage: python3 p2_walk.py --month 202506 --gen /tmp/p2/gen/202506 --out /tmp/p2/rows_202506.npz
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

PBG = Path(
    "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/"
    "docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
)
sys.path.insert(0, str(PBG))
import pbg_lib as L  # noqa: E402
import pbg_econ as E  # noqa: E402

AT_MARKET = (
    "displacement_continuation", "liquidity_sweep_reclaim",
    "structural_distance_extreme", "volatility_compression_expansion",
    "session_open_range_break", "regime_transition_break", "cross_asset_lead_lag",
)
POI = ("current_fvg_fill", "current_ob_retest", "current_breaker_re_entry")
FAMS = list(AT_MARKET) + list(POI)
EARLY5 = (
    "displacement_continuation", "liquidity_sweep_reclaim",
    "session_open_range_break", "regime_transition_break",
    "volatility_compression_expansion",
)
XR = {"stop": 0, "target": 1, "path_end": 2, "no_fill": 3}
BIG = 1e9


def fill_lag(tape, sym, i, e, horizon=E.HORIZON):
    """first j>=0 with bar i+j range containing e; -1 if never inside horizon."""
    a, b = i, min(i + horizon, tape.n)
    if a >= b:
        return -1
    hi, lo = tape.h[sym][a:b], tape.l[sym][a:b]
    ok = ~np.isnan(hi)
    if not ok.any():
        return -1
    idxs = np.nonzero(ok)[0]
    t = (lo[idxs] <= e) & (hi[idxs] >= e)
    return int(idxs[int(np.argmax(t))]) if t.any() else -1


def cross_lag(tape, sym, i, e, up, horizon=E.HORIZON):
    """first j>=0 where price reaches e from the required side.
    up=True -> need high>=e ; up=False -> need low<=e.  -1 if never."""
    a, b = i, min(i + horizon, tape.n)
    if a >= b:
        return -1
    hi, lo = tape.h[sym][a:b], tape.l[sym][a:b]
    ok = ~np.isnan(hi)
    if not ok.any():
        return -1
    idxs = np.nonzero(ok)[0]
    t = (hi[idxs] >= e) if up else (lo[idxs] <= e)
    return int(idxs[int(np.argmax(t))]) if t.any() else -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", required=True)
    ap.add_argument("--gen", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--target-r", type=float, default=2.0)
    args = ap.parse_args()

    gen = Path(args.gen)
    files = sorted(gen.glob("pbg_*.jsonl.gz"))
    close_rows = []
    early_first = {}          # setup key -> row with the smallest k<15
    early_close = {}          # setup key -> the k=15 row
    n_raw = 0
    for f in files:
        with gzip.open(f, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                n_raw += 1
                if r["k"] == 15:
                    close_rows.append(r)
                    if r["f"] in EARLY5:
                        early_close[(r["s"], r["f"], r["d"], r["b"])] = r
                elif r["f"] in EARLY5:
                    k = (r["s"], r["f"], r["d"], r["b"])
                    p = early_first.get(k)
                    if p is None or r["k"] < p["k"]:
                        early_first[k] = r

    symbols = sorted({r["s"] for r in close_rows})
    tape = E.Tape(symbols, [args.month])
    cm = E.CostModel()

    def one(r, *, limit_family=None, mirror=False):
        """Walk one emission under all declared contracts. Returns dict or None."""
        sym, i = r["s"], tape.idx(r["t"])
        e, sl = r["e"], r["sl"]
        d = abs(e - sl)
        if not (d > 0):
            return None
        long = r["d"] == "L"
        stop_eff = e - d if long else e + d
        return sym, i, e, d, long, stop_eff

    out = defaultdict(list)
    fam_ix = {f: k for k, f in enumerate(FAMS)}
    sym_ix = {s: k for k, s in enumerate(symbols)}
    days = sorted({r["t"][:10] for r in close_rows})
    day_ix = {d: k for k, d in enumerate(days)}

    for r in close_rows:
        z = one(r)
        if z is None:
            continue
        sym, i, e, d, long, stop_eff = z
        if i < 1 or i >= tape.n:
            continue
        mkt = tape.last_close_before(sym, i)
        if mkt != mkt:
            continue
        gap_r = (mkt - e) / d if long else (e - mkt) / d
        bps = (mkt <= stop_eff) if long else (mkt >= stop_eff)
        atm = r["f"] in AT_MARKET

        kw = dict(entry=e, stop=stop_eff, long=long)
        wc = (E.walk if atm else E.walk_limit)(tape, sym, i, target_r=args.target_r, **kw)
        wl = E.walk_limit(tape, sym, i, target_r=args.target_r, **kw)
        ws = (E.walk if atm else E.walk_limit)(tape, sym, i, target_r=BIG, **kw)
        if wc is None or wl is None or ws is None:
            continue

        # ---- side-aware fill contract (d5) -----------------------------
        if gap_r > 0:                       # reachable resting limit
            wa = wl
        elif gap_r == 0:                    # already at market
            wa = E.walk(tape, sym, i, target_r=args.target_r, **kw)
        else:                               # level already through -> re-cross
            j = cross_lag(tape, sym, i, e, up=long)
            if j < 0:
                wa = (0.0, "no_fill", None, 0)
            else:
                w2 = E.walk(tape, sym, i + j, target_r=args.target_r,
                            horizon=E.HORIZON - j - 1, **kw)
                wa = w2 if w2 is not None else (0.0, "no_fill", None, 0)

        # ---- d5-style ESTATE one-sided fill: a BUY fills on low<=e whatever
        # side of e the market is on (and a SELL on high>=e).  This is the
        # convention in which d5 measured +0.02995; pbg_econ.walk_limit uses
        # range containment instead, so both baselines are carried.
        je = cross_lag(tape, sym, i, e, up=(not long))
        if je < 0:
            we = (0.0, "no_fill", None, 0)
        else:
            w2 = E.walk(tape, sym, i + je, target_r=args.target_r,
                        horizon=E.HORIZON - je - 1, **kw)
            we = w2 if w2 is not None else (0.0, "no_fill", None, 0)

        # ---- mirror (at-market only; a mirrored resting limit is an artifact)
        if atm:
            wm = E.walk(tape, sym, i, entry=e, stop=(e + d if long else e - d),
                        long=(not long), target_r=args.target_r)
        else:
            wm = None

        cpx, _ = cm.cost_px(sym, r["t"], e, long)
        lag = fill_lag(tape, sym, i, e)

        out["day"].append(day_ix[r["t"][:10]])
        out["sym"].append(sym_ix[sym])
        out["fam"].append(fam_ix[r["f"]])
        out["long"].append(1 if long else 0)
        out["e"].append(e); out["d"].append(d)
        out["gap_r"].append(gap_r); out["bps"].append(1 if bps else 0)
        out["lag"].append(lag)
        out["cost_r"].append(cpx / d)
        for tag, w in (("c", wc), ("l", wl), ("s", ws), ("a", wa), ("e", we)):
            out["g_" + tag].append(w[0]); out["x_" + tag].append(XR[w[1]])
        out["g_m"].append(wm[0] if wm else np.nan)
        out["x_m"].append(XR[wm[1]] if wm else -1)

    arrs = {k: np.asarray(v) for k, v in out.items()}

    # ------------------------------------------------ H5: the partial arm
    ekeys = set(early_first) | set(early_close)
    p = defaultdict(list)
    for k in sorted(ekeys):
        rc, rp = early_close.get(k), early_first.get(k)
        rec = {}
        for tag, r in (("c", rc), ("p", rp)):
            if r is None:
                rec[tag] = None
                continue
            z = one(r)
            if z is None:
                rec[tag] = None
                continue
            sym, i, e, d, long, stop_eff = z
            if i < 1 or i >= tape.n:
                rec[tag] = None
                continue
            w = E.walk(tape, sym, i, entry=e, stop=stop_eff, long=long,
                       target_r=args.target_r)
            if w is None:
                rec[tag] = None
                continue
            cpx, _ = cm.cost_px(sym, r["t"], e, long)
            rec[tag] = (w[0], cpx / d, r["t"][:10], r["k"], sym, r["f"], r["d"], i)
        if rec["c"] is None and rec["p"] is None:
            continue
        for tag in ("c", "p"):
            v = rec[tag]
            p[tag + "_g"].append(v[0] if v else np.nan)
            p[tag + "_c"].append(v[1] if v else np.nan)
            p[tag + "_k"].append(v[3] if v else -1)
            p[tag + "_i"].append(v[7] if v else -1)
        ref = rec["c"] or rec["p"]
        p["day"].append(day_ix.get(ref[2], -1))
        p["sym"].append(sym_ix.get(ref[4], -1))
        p["fam"].append(fam_ix[ref[5]])
        p["side"].append(1 if ref[6] == "L" else 0)
    parr = {("P_" + k): np.asarray(v) for k, v in p.items()}

    meta = {
        "month": args.month, "n_raw_rows": n_raw, "n_close_rows": len(close_rows),
        "n_walked": int(len(arrs["day"])), "days": days, "symbols": symbols,
        "families": FAMS, "target_r": args.target_r,
        "early5_setup_keys": len(ekeys),
    }
    np.savez_compressed(args.out, meta=json.dumps(meta), **arrs, **parr)
    print(json.dumps({k: meta[k] for k in
                      ("month", "n_raw_rows", "n_close_rows", "n_walked",
                       "early5_setup_keys")}))


if __name__ == "__main__":
    main()
