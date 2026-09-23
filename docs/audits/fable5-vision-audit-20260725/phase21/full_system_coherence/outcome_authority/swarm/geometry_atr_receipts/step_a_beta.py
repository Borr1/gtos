"""Step A -- estimate the travel exponent beta from BARS ONLY.

No trade outcome, no P&L, no estate record is read here. The only inputs are the
OHLC bars in `/Users/borr/GTOSActive/vps-bars-20260727` as loaded by
`r1_estate_rewalk.load_series()` (so: FTMO tape, broker clock, the same 123
(symbol, timeframe) series the estate's own walker resolves against).

    v_i      = ATR14(i) / ATR50(i)
    travel_i = max(high[i+1..i+80]) - min(low[i+1..i+80])        (unconditional range)
    up_i     = max(high[i+1..i+80]) - close[i]                    (one-sided, favourable long)
    dn_i     = close[i] - min(low[i+1..i+80])                     (one-sided, favourable short)
    y_i      = travel_i / ATR14(i)

    log(y) = b0 + beta*log(v)   by OLS, pooled and per timeframe.

ATR is the ESTATE's ATR: `src/components/ultimate_book/primitives.py:23 atr14` -- a
SIMPLE (not Wilder) mean of TrueRange over [i-13, i], TR = max(h-l, |h-prev_c|,
|l-prev_c|), returning 0.0 when i < n. `atr_n` below is that function generalised to
window n, and `_selftest_atr` proves the n=14 case is bit-identical to the vendored
primitive on real bars.

SEs are NOT naive OLS SEs. Overlapping 80-bar forward windows make adjacent rows
almost the same observation; the honest clustering unit is the SYMBOL (the same
symbol at M15/H4/D1 is one market). Two SEs are reported: a CR1 cluster-robust
sandwich clustered on symbol, and a symbol-block bootstrap (resample symbols with
replacement). The bootstrap is the headline.
"""

from __future__ import annotations

import collections
import json
import math
import pickle
import sys
import time
from pathlib import Path

import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/swarm-geom-20260811"
R1 = REPO + "/docs/audits/fable5-vision-audit-20260725/phase20/receipts/r1"
sys.path.insert(0, REPO)
sys.path.insert(0, R1)

OUTDIR = Path("/private/tmp/atr-scaling-20260811")
SERIES_PKL = OUTDIR / "series.pkl"

TF_NAME = {15: "M15", 16388: "H4", 16408: "D1"}
HORIZON = 80
N_FAST, N_SLOW = 14, 50
NBOOT = 2000
SEED = 20260811


# --------------------------------------------------------------------------- ATR
def atr_n(bars, i, n):
    """`primitives.atr14` generalised to window n. SAME TR definition, SAME 0.0 guard."""
    if i < n:
        return 0.0
    s = 0.0
    for j in range(i - n + 1, i + 1):
        tr = max(bars[j].h - bars[j].l,
                 abs(bars[j].h - bars[j - 1].c),
                 abs(bars[j].l - bars[j - 1].c))
        s += tr
    return s / n


def _true_range(h, l, c):
    """Vectorised TR. TR[0] is set to 0 and never used (every window starts at j>=1)."""
    prev_c = np.concatenate(([c[0]], c[:-1]))
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
    tr[0] = 0.0
    return tr


def _atr_vec(tr, n):
    """atr[i] = mean(tr[i-n+1 .. i]) for i >= n, else 0.0 -- matches `atr_n` exactly."""
    cs = np.concatenate(([0.0], np.cumsum(tr)))
    out = np.zeros_like(tr)
    idx = np.arange(len(tr))
    ok = idx >= n
    out[ok] = (cs[idx[ok] + 1] - cs[idx[ok] - n + 1]) / n
    return out


def _selftest_atr(series):
    """Prove `_atr_vec` == `atr_n` == vendored `primitives.atr14` on real bars."""
    from src.components.ultimate_book.primitives import atr14 as vendored
    key = sorted(series)[0]
    bars, _ = series[key]
    h = np.array([b.h for b in bars]); l = np.array([b.l for b in bars])
    c = np.array([b.c for b in bars])
    tr = _true_range(h, l, c)
    a14 = _atr_vec(tr, 14); a50 = _atr_vec(tr, 50)
    worst14 = worst50 = worstvend = 0.0
    for i in list(range(0, 60)) + list(range(200, 260)) + list(range(len(bars) - 60, len(bars))):
        worst14 = max(worst14, abs(a14[i] - atr_n(bars, i, 14)))
        worst50 = max(worst50, abs(a50[i] - atr_n(bars, i, 50)))
        worstvend = max(worstvend, abs(atr_n(bars, i, 14) - vendored(bars, i)))
    return {"key": f"{key[0]}|{TF_NAME[key[1]]}", "n_bars": len(bars),
            "max_abs_err_vec_vs_atr_n_14": worst14,
            "max_abs_err_vec_vs_atr_n_50": worst50,
            "max_abs_err_atr_n_vs_vendored_atr14": worstvend}


# --------------------------------------------------------------------------- fits
def _ols(x, y, w=None):
    X = np.column_stack([np.ones_like(x), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    ss_res = float(resid @ resid)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return beta, resid, r2, X


def _cluster_robust_se(X, resid, clusters):
    """CR1 sandwich clustered on `clusters` (integer codes)."""
    n, k = X.shape
    XtX_inv = np.linalg.inv(X.T @ X)
    meat = np.zeros((k, k))
    uniq = np.unique(clusters)
    for g in uniq:
        m = clusters == g
        Xg = X[m]; ug = resid[m]
        s = Xg.T @ ug
        meat += np.outer(s, s)
    G = len(uniq)
    c = (G / (G - 1.0)) * ((n - 1.0) / (n - k)) if G > 1 else 1.0
    V = c * (XtX_inv @ meat @ XtX_inv)
    return np.sqrt(np.diag(V)), G


def _block_bootstrap(sym_codes, x, y, nboot, rng):
    """Resample SYMBOLS with replacement; refit OLS on the concatenated blocks."""
    uniq = np.unique(sym_codes)
    order = np.argsort(sym_codes, kind="stable")
    xs, ys, cs = x[order], y[order], sym_codes[order]
    starts = np.searchsorted(cs, uniq, side="left")
    ends = np.searchsorted(cs, uniq, side="right")
    slices = [(int(a), int(b)) for a, b in zip(starts, ends)]
    G = len(uniq)
    out = np.empty(nboot)
    for b in range(nboot):
        pick = rng.integers(0, G, size=G)
        xb = np.concatenate([xs[slices[p][0]:slices[p][1]] for p in pick])
        yb = np.concatenate([ys[slices[p][0]:slices[p][1]] for p in pick])
        Xb = np.column_stack([np.ones_like(xb), xb])
        bb, *_ = np.linalg.lstsq(Xb, yb, rcond=None)
        out[b] = bb[1]
    return out


def fit(logv, logy, sym_codes, rng, nboot=NBOOT):
    beta, resid, r2, X = _ols(logv, logy)
    se_cr, G = _cluster_robust_se(X, resid, sym_codes)
    boot = _block_bootstrap(sym_codes, logv, logy, nboot, rng)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {
        "n": int(len(logv)),
        "n_symbol_clusters": int(G),
        "b0": float(beta[0]),
        "beta": float(beta[1]),
        "r2": float(r2),
        "se_cluster_robust_cr1_by_symbol": float(se_cr[1]),
        "ci95_cluster_robust": [float(beta[1] - 1.96 * se_cr[1]),
                                float(beta[1] + 1.96 * se_cr[1])],
        "se_block_bootstrap_by_symbol": float(boot.std(ddof=1)),
        "ci95_block_bootstrap": [float(lo), float(hi)],
        "n_bootstrap": int(nboot),
    }


def quintiles(v, y, q=5):
    edges = np.quantile(v, np.linspace(0, 1, q + 1))
    edges[0] -= 1e-12; edges[-1] += 1e-12
    idx = np.clip(np.digitize(v, edges[1:-1]), 0, q - 1)
    rows = []
    for k in range(q):
        m = idx == k
        rows.append({"quintile": k, "n": int(m.sum()),
                     "v_lo": float(edges[k]), "v_hi": float(edges[k + 1]),
                     "mean_v": float(v[m].mean()) if m.any() else None,
                     "mean_y": float(y[m].mean()) if m.any() else None,
                     "median_y": float(np.median(y[m])) if m.any() else None})
    ratio = (rows[0]["mean_y"] / rows[-1]["mean_y"]) if rows[-1]["mean_y"] else None
    med_ratio = (rows[0]["median_y"] / rows[-1]["median_y"]) if rows[-1]["median_y"] else None
    return {"bins": rows, "Q0_over_Q4_mean_y": ratio, "Q0_over_Q4_median_y": med_ratio}


def main() -> int:
    t0 = time.time()
    import r1_estate_rewalk as _R
    series, _index = _R.load_series()
    print(f"series {len(series)}  ({time.time()-t0:.0f}s)", flush=True)

    selftest = _selftest_atr(series)
    print("ATR selftest:", json.dumps(selftest), flush=True)
    assert selftest["max_abs_err_atr_n_vs_vendored_atr14"] < 1e-12, selftest
    assert selftest["max_abs_err_vec_vs_atr_n_14"] < 1e-9, selftest
    assert selftest["max_abs_err_vec_vs_atr_n_50"] < 1e-9, selftest

    per_tf = collections.defaultdict(lambda: {"v": [], "y": [], "yup": [], "ydn": [], "sym": []})
    coverage = []
    sym_ids = {}

    for (sym, tf), (bars, _times) in sorted(series.items()):
        if tf not in TF_NAME:
            continue
        h = np.fromiter((b.h for b in bars), dtype=np.float64, count=len(bars))
        l = np.fromiter((b.l for b in bars), dtype=np.float64, count=len(bars))
        c = np.fromiter((b.c for b in bars), dtype=np.float64, count=len(bars))
        n = len(bars)
        if n < N_SLOW + HORIZON + 2:
            coverage.append({"symbol": sym, "tf": TF_NAME[tf], "n_bars": n, "n_rows": 0,
                             "reason": "too_short"})
            continue
        tr = _true_range(h, l, c)
        a14 = _atr_vec(tr, N_FAST)
        a50 = _atr_vec(tr, N_SLOW)

        # forward window [i+1, i+80]: rolling max of high / min of low over 80 bars
        sw_h = np.lib.stride_tricks.sliding_window_view(h, HORIZON)   # sw_h[k] = h[k..k+79]
        sw_l = np.lib.stride_tricks.sliding_window_view(l, HORIZON)
        fmax = sw_h.max(axis=1)   # fmax[k] = max(h[k .. k+79])
        fmin = sw_l.min(axis=1)

        i_hi = n - 1 - HORIZON                    # need i+80 <= n-1
        i_lo = N_SLOW                             # need ATR50 defined
        if i_hi < i_lo:
            coverage.append({"symbol": sym, "tf": TF_NAME[tf], "n_bars": n, "n_rows": 0,
                             "reason": "no_room"})
            continue
        idx = np.arange(i_lo, i_hi + 1)
        fw_max = fmax[idx + 1]
        fw_min = fmin[idx + 1]
        A14 = a14[idx]; A50 = a50[idx]
        ok = (A50 > 0) & (A14 > 0)
        idx = idx[ok]; fw_max = fw_max[ok]; fw_min = fw_min[ok]
        A14 = A14[ok]; A50 = A50[ok]
        v = A14 / A50
        travel = fw_max - fw_min
        up = fw_max - c[idx]
        dn = c[idx] - fw_min
        y = travel / A14
        yup = np.maximum(up, 0.0) / A14
        ydn = np.maximum(dn, 0.0) / A14
        good = np.isfinite(v) & np.isfinite(y) & (v > 0) & (y > 0)
        v, y, yup, ydn = v[good], y[good], yup[good], ydn[good]

        sid = sym_ids.setdefault(sym, len(sym_ids))
        d = per_tf[tf]
        d["v"].append(v); d["y"].append(y); d["yup"].append(yup); d["ydn"].append(ydn)
        d["sym"].append(np.full(len(v), sid, dtype=np.int32))
        coverage.append({"symbol": sym, "tf": TF_NAME[tf], "n_bars": n, "n_rows": int(len(v)),
                         "first_bar": str(_times_first(series, sym, tf)),
                         "last_bar": str(_times_last(series, sym, tf))})
        print(f"  {sym:12s} {TF_NAME[tf]:4s} bars={n:7d} rows={len(v):7d} "
              f"({time.time()-t0:.0f}s)", flush=True)

    rng = np.random.default_rng(SEED)
    out = {
        "what": ("travel exponent beta: log(travel_per_ATR14) = b0 + beta*log(ATR14/ATR50), "
                 "estimated from BARS ONLY -- no trade, no P&L, no estate record"),
        "bars": "/Users/borr/GTOSActive/vps-bars-20260727 (FTMO, broker clock)",
        "atr": ("simple mean of TrueRange over [i-n+1, i]; TR = max(h-l, |h-prev_c|, "
                "|l-prev_c|); 0.0 when i<n -- generalisation of "
                "src/components/ultimate_book/primitives.py:23 atr14"),
        "atr_selftest": selftest,
        "horizon_bars": HORIZON,
        "n_fast": N_FAST, "n_slow": N_SLOW,
        "se_note": ("overlapping 80-bar forward windows make adjacent rows near-duplicates; "
                    "SEs are clustered/blocked on SYMBOL, the coarsest honest unit. "
                    "Naive OLS SEs are NOT reported and would be meaningless here."),
        "seed": SEED,
        "coverage": coverage,
        "per_timeframe": {},
        "pooled": {},
    }

    allv, ally, allyup, allydn, allsym = [], [], [], [], []
    for tf in sorted(per_tf):
        d = per_tf[tf]
        v = np.concatenate(d["v"]); y = np.concatenate(d["y"])
        yup = np.concatenate(d["yup"]); ydn = np.concatenate(d["ydn"])
        sym = np.concatenate(d["sym"])
        allv.append(v); ally.append(y); allyup.append(yup); allydn.append(ydn); allsym.append(sym)
        lv = np.log(v)
        rec = {
            "timeframe_enum": tf, "timeframe": TF_NAME[tf],
            "n_series": len(d["v"]),
            "two_sided_travel": fit(lv, np.log(y), sym, rng),
            "quintiles_two_sided": quintiles(v, y),
        }
        m = yup > 0
        rec["one_sided_up"] = fit(lv[m], np.log(yup[m]), sym[m], rng, nboot=500)
        rec["one_sided_up_n_dropped_nonpositive"] = int((~m).sum())
        m = ydn > 0
        rec["one_sided_dn"] = fit(lv[m], np.log(ydn[m]), sym[m], rng, nboot=500)
        rec["one_sided_dn_n_dropped_nonpositive"] = int((~m).sum())
        # one-sided pooled: stack up and dn (each direction is one draw of "favourable")
        vv = np.concatenate([v[yup > 0], v[ydn > 0]])
        yy = np.concatenate([yup[yup > 0], ydn[ydn > 0]])
        ss = np.concatenate([sym[yup > 0], sym[ydn > 0]])
        rec["one_sided_both"] = fit(np.log(vv), np.log(yy), ss, rng, nboot=500)
        rec["quintiles_one_sided_both"] = quintiles(vv, yy)
        out["per_timeframe"][TF_NAME[tf]] = rec
        print(f"TF {TF_NAME[tf]}: beta={rec['two_sided_travel']['beta']:.4f} "
              f"CI{rec['two_sided_travel']['ci95_block_bootstrap']} "
              f"R2={rec['two_sided_travel']['r2']:.4f} n={rec['two_sided_travel']['n']} "
              f"Q0/Q4={rec['quintiles_two_sided']['Q0_over_Q4_mean_y']:.4f}", flush=True)

    v = np.concatenate(allv); y = np.concatenate(ally)
    yup = np.concatenate(allyup); ydn = np.concatenate(allydn); sym = np.concatenate(allsym)
    out["pooled"] = {
        "two_sided_travel": fit(np.log(v), np.log(y), sym, rng),
        "quintiles_two_sided": quintiles(v, y),
    }
    vv = np.concatenate([v[yup > 0], v[ydn > 0]])
    yy = np.concatenate([yup[yup > 0], ydn[ydn > 0]])
    ss = np.concatenate([sym[yup > 0], sym[ydn > 0]])
    out["pooled"]["one_sided_both"] = fit(np.log(vv), np.log(yy), ss, rng, nboot=500)
    out["pooled"]["quintiles_one_sided_both"] = quintiles(vv, yy)
    out["elapsed_s"] = round(time.time() - t0, 1)

    (OUTDIR / "STEP_A_BETA_V1.json").write_text(json.dumps(out, indent=1))
    print("WROTE", OUTDIR / "STEP_A_BETA_V1.json")
    print(json.dumps({k: {"beta": r["two_sided_travel"]["beta"],
                          "ci": r["two_sided_travel"]["ci95_block_bootstrap"],
                          "r2": r["two_sided_travel"]["r2"],
                          "n": r["two_sided_travel"]["n"],
                          "Q0/Q4": r["quintiles_two_sided"]["Q0_over_Q4_mean_y"]}
                      for k, r in out["per_timeframe"].items()}, indent=1))
    return 0


def _times_first(series, sym, tf):
    return series[(sym, tf)][1][0]


def _times_last(series, sym, tf):
    return series[(sym, tf)][1][-1]


if __name__ == "__main__":
    raise SystemExit(main())
