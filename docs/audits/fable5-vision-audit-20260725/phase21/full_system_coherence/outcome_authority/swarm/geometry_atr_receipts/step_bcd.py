"""Steps B, C, D -- build the per-trade stop correction, re-walk the estate, price it.

STEP B  per-trade multiplier
    v_i        = ATR14(i)/ATR50(i) at the trade's OWN decision bar in its OWN (symbol, tf)
                 series -- the same bar the estate's walker enters on.
    raw_mult_i = v_i ** beta(tf)      beta from Step A (bars only, no trade outcome)
    stop_mult_i= raw_mult_i / geomean(raw_mult over that sleeve)      <- normalised to 1.0
    then winsorised to [0.5, 2.0].
    The geomean normalisation is what makes this a CROSS-SECTIONAL rescaling and not a
    global stop widening; a global widening is a different intervention and is already on
    AD's `stop_width` grid.

STEP C  two arms, same walker, same bars, same population
    CONTROL    stop_mult = 1.0 everywhere
    CORRECTED  stop_mult from Step B
    Both at `corrected=True` (the repaired quote convention, r1's finding) on all three
    spread bands; band="mid" is the headline.

TARGET CONVENTION UNDER A STOP RESCALE
    Measured at source, not assumed. Every estate sleeve's `target_dist` is an exact
    constant R-multiple of its own stop, but for three sleeves the GENERATOR sets both
    from the ATR independently (`fx_jpy`/`fx_jpy_ny`: `stop=1.0*a, target=2.5*a`,
    `fx_jpy.py:203`; `vss_fxcross_london_up_low`: `stop=1.0*atr_i, target=2.0*atr_i`,
    `:171,:180`), so rescaling the STOP there does not move the target. That is AD's
    `TARGET_CONVENTION` ("fixed_price", `ad_exit_sweep.py:150-158`) and it is the native
    reading. Headline uses each sleeve's native convention; the alternative is run as a
    labelled sensitivity for exactly those three sleeves.

EXCLUSIONS
    `mx_us100_cash_d1_atr_mean_reversion` and `mx_us500_cash_d1_atr_mean_reversion`:
    their ENTRY SIGNAL reads the risk distance (`market_expansion_d1.py:211
    _atr_mean_reversion_signal(bars, idx, risk)`, declared at
    `ad_exit_sweep.py:143 STOP_DEPENDENT_SIGNAL`), so a stop rescale changes WHICH trades
    exist and a re-walk of the recorded trades is invalid. Reported CONTROL-only.
"""

from __future__ import annotations

import bisect
import collections
import datetime as _dt
import gzip
import json
import math
import pickle
import statistics
import sys
import time
from pathlib import Path

import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/swarm-geom-20260811"
R1 = REPO + "/docs/audits/fable5-vision-audit-20260725/phase20/receipts/r1"
sys.path.insert(0, REPO)
sys.path.insert(0, R1)

import r1_estate_rewalk as R  # noqa: E402
import r1_frontier_surface_sweep as S  # noqa: E402
from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.quote_side import (  # noqa: E402
    BarQuote, SpreadUnavailable, replay_anchor, spread_for,
)
from step_a_beta import _atr_vec, _true_range, atr_n  # noqa: E402

OUTDIR = Path("/private/tmp/atr-scaling-20260811")
OUT = OUTDIR / "ATR_SCALING_ESTATE_V1.json"

MAXBARS = 80                       # r1_estate_rewalk.MAXBARS
BANDS = R.BANDS                    # ("low", "mid", "high")
HEADLINE_BAND = "mid"
ARMED = ("crypto", "energy_agri", "sub_mid_dn_revert", "sub_xvol_pullback")
EXCLUDED = {
    "mx_us100_cash_d1_atr_mean_reversion":
        "entry signal reads the risk distance -- market_expansion_d1.py:211 "
        "_atr_mean_reversion_signal(bars, idx, risk); declared STOP_DEPENDENT_SIGNAL at "
        "ad_exit_sweep.py:143. Rescaling the stop changes WHICH trades exist, so a re-walk "
        "of the recorded trades measures a different candidate set, not a geometry change.",
    "mx_us500_cash_d1_atr_mean_reversion":
        "same -- market_expansion_d1.py:211 / ad_exit_sweep.py:143.",
}
#: native target behaviour under a STOP rescale, read at source (see module docstring)
TARGET_FIXED_PRICE = {
    "fx_jpy": "fx_jpy.py:203  stop=_STOP_M*a, target=_TGT_M*a  (both from ATR14)",
    "fx_jpy_ny": "fx_jpy.py:203  stop=_STOP_M*a, target=_TGT_M*a  (both from ATR14)",
    "vss_fxcross_london_up_low":
        "vss_fxcross_london_up_low.py:171,180  stop=STOP_ATR*atr_i, target=TGT_ATR*atr_i",
}
WINSOR_LO, WINSOR_HI = 0.5, 2.0
NBOOT_DELTA = 10_000
NBOOT_DD = 2_000
SEED = 20260811


# ============================================================== the walker copy
def walk_pertrade(trades, series, index, tm, mb, band, corrected, mults, tid,
                  target_scales=True, collect=None):
    """`r1_frontier_surface_sweep.walk` with ONE arithmetic change.

    The single edit is the stop line:

        walk()          sd = float(r["sl_distance_price"]) * stop_mult
        walk_pertrade() sd = float(r["sl_distance_price"]) * mults.get(tid(k, r), 1.0)

    Everything else -- the skip ladder and its order, the index lookup, the `i + 2 >=
    len(bars)` room test, the trail policy, the target expression, the spread lookup and
    its fail-closed `continue`, the BID anchor, `replay`, `winsorize_R`, the by-day and
    exit-reason tallies -- is copied verbatim. `collect` only APPENDS to a caller list and
    touches no arithmetic. `tm="native"` reads the trade's own `target_dist` (which is what
    `r1_estate_rewalk.main()` passes) instead of an R-multiple of the cell.

    Faithfulness is asserted, not asserted-about: `_prove_copy_faithful` runs this with
    every multiplier equal to 1.0 against `walk(..., stop_mult=1.0)` and requires identical
    n, identical `vals` element by element, identical exit-reason counts and identical
    by-day buckets.
    """
    label = "stop_only" if tm is None else (
        "native" if tm == "native" else f"target_{tm}R")
    vals, by_day = [], collections.defaultdict(list)
    reasons, unpriceable, skips = collections.Counter(), 0, collections.Counter()
    for k, r in enumerate(trades):
        tf = int(r["timeframe"])
        key = (r["symbol"], tf)
        if key not in index:
            skips["no_series"] += 1
            continue
        i = index[key].get(_dt.datetime.fromisoformat(r["decision_bar_iso"]))
        if i is None:
            skips["bar_not_found"] += 1
            continue
        bars, times = series[key]
        if i + 2 >= len(bars):
            skips["no_room"] += 1
            continue
        d = int(r["direction"])
        m = mults.get(tid(k, r), 1.0)                       # <-- THE ONLY CHANGE
        sd = float(r["sl_distance_price"]) * m
        trig_r, gap_r = R._trail_policy(r["sleeve"])
        if tm == "native":
            td = r["target_dist"]
            tdist = (float(td) * (m if target_scales else 1.0)) if td else None
        else:
            tdist = (None if tm is None else tm * sd)
        pol = ExitPolicy(
            target_dist=tdist,
            maxbars=mb,
            trail_arm=(None if trig_r is None else float(trig_r) * sd),
            trail_gap=(None if gap_r is None else float(gap_r) * sd),
            label=label,
        )
        if corrected:
            at = times[i] + _dt.timedelta(minutes=R.TF_MINUTES[tf])
            try:
                sp = spread_for(r["symbol"], at, account="FTMO", band=band)
            except SpreadUnavailable:
                unpriceable += 1
                continue
            anchor = replay_anchor(bars[i].c, d, sp, BarQuote.BID)
            res = replay(bars, i, d, stop_dist=sd, policy=pol, entry_price=anchor)
        else:
            res = replay(bars, i, d, stop_dist=sd, policy=pol)
        val = winsorize_R(res.r_gross)
        vals.append(val)
        by_day[r["decision_day"]].append(val)
        reasons[res.exit_reason] += 1
        if collect is not None:
            collect.append((tid(k, r), val, res.exit_reason,
                            times[min(res.exit_index, len(times) - 1)], m))
    return vals, by_day, reasons, unpriceable, skips


def _prove_copy_faithful(estate, series, index, tid):
    """walk_pertrade with all multipliers 1.0 must BE walk(..., stop_mult=1.0)."""
    checks = []
    ones = {}
    for cell_tm, cell_mb in ((None, 80), (2.0, 80), (4.0, 20), (1.5, 160)):
        for band in ("mid", "high"):
            for corrected in (False, True):
                nv = nr = 0
                worst = 0.0
                same_reasons = same_days = True
                for sleeve, rows in sorted(estate.items()):
                    a = S.walk(rows, series, index, cell_tm, cell_mb, band, corrected,
                               stop_mult=1.0)
                    b = walk_pertrade(rows, series, index, cell_tm, cell_mb, band,
                                      corrected, ones, tid)
                    if len(a[0]) != len(b[0]):
                        raise AssertionError(f"n differs {sleeve} {cell_tm} {cell_mb}")
                    for x, y in zip(a[0], b[0]):
                        if x != y:
                            worst = max(worst, abs(x - y))
                            nr += 1
                    nv += len(a[0])
                    same_reasons &= (dict(a[2]) == dict(b[2]))
                    same_days &= ({k: list(v) for k, v in a[1].items()}
                                  == {k: list(v) for k, v in b[1].items()})
                    if a[3] != b[3] or dict(a[4]) != dict(b[4]):
                        raise AssertionError(f"skips differ {sleeve}")
                checks.append({"cell": ("stop_only" if cell_tm is None
                                        else f"target_{cell_tm}R"),
                               "maxbars": cell_mb, "band": band,
                               "quote_convention": "corrected" if corrected else "published",
                               "n_values_compared": nv,
                               "n_values_differing": nr,
                               "max_abs_difference": worst,
                               "exit_reason_counts_identical": bool(same_reasons),
                               "by_day_buckets_identical": bool(same_days)})
                print(f"  faithful: {checks[-1]}", flush=True)
    return checks


# ============================================================== statistics
def _boot_mean(a, nboot, rng, chunk_elems=4_000_000):
    """Bootstrap distribution of the mean, chunked so a 22k x 10k index never allocates."""
    n = len(a)
    per = max(1, min(nboot, chunk_elems // max(n, 1)))
    out = np.empty(nboot)
    done = 0
    while done < nboot:
        k = min(per, nboot - done)
        idx = rng.integers(0, n, size=(k, n))
        out[done:done + k] = a[idx].mean(axis=1)
        done += k
    return out


def _mean_ci(x, nboot=NBOOT_DELTA, rng=None):
    n = len(x)
    if n == 0:
        return {"n": 0}
    a = np.asarray(x, dtype=float)
    mu = float(a.mean())
    if n == 1:
        return {"n": 1, "mean": mu, "se": None, "ci95_t": None, "ci95_bootstrap": None}
    se = float(a.std(ddof=1) / math.sqrt(n))
    tcrit = 1.96 if n > 200 else _t975(n - 1)
    rng = rng or np.random.default_rng(SEED)
    bs = _boot_mean(a, nboot, rng)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return {"n": n, "mean": mu, "se": se,
            "ci95_t": [mu - tcrit * se, mu + tcrit * se],
            "ci95_bootstrap": [float(lo), float(hi)],
            "sum": float(a.sum())}


_T = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306,
      9: 2.262, 10: 2.228, 12: 2.179, 15: 2.131, 20: 2.086, 25: 2.060, 30: 2.042,
      40: 2.021, 50: 2.009, 60: 2.000, 80: 1.990, 100: 1.984, 150: 1.976, 200: 1.972}


def _t975(df):
    ks = sorted(_T)
    for k in ks:
        if df <= k:
            return _T[k]
    return 1.96


def _paired_delta(ctrl, corr, nboot=NBOOT_DELTA, rng=None):
    a = np.asarray(ctrl, float); b = np.asarray(corr, float)
    assert len(a) == len(b)
    n = len(a)
    if n == 0:
        return {"n": 0}
    d = b - a
    mu = float(d.mean())
    rng = rng or np.random.default_rng(SEED + 1)
    bs = _boot_mean(d, nboot, rng)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    se = float(d.std(ddof=1) / math.sqrt(n)) if n > 1 else None
    return {"n": n, "mean_delta": mu, "se": se,
            "ci95_paired_bootstrap": [float(lo), float(hi)],
            "n_bootstrap": nboot,
            "excludes_zero": bool(lo > 0 or hi < 0),
            "n_changed": int((d != 0).sum()),
            "frac_changed": float((d != 0).mean()),
            "n_better": int((d > 0).sum()), "n_worse": int((d < 0).sum())}


def _wilson(k, n, z=1.96):
    if n == 0:
        return {"n": 0}
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return {"k": int(k), "n": int(n), "rate": p,
            "ci95_wilson": [max(0.0, centre - half), min(1.0, centre + half)]}


def _maxdd(vals_in_time_order):
    a = np.asarray(vals_in_time_order, float)
    if a.size == 0:
        return 0.0
    cum = np.cumsum(a)
    peak = np.maximum.accumulate(np.concatenate(([0.0], cum)))[1:]
    return float(np.max(peak - cum))


def _maxdd_pair(ctrl_rows, corr_rows, nboot=NBOOT_DD, rng=None):
    """ctrl_rows/corr_rows: list of (exit_time, r) already PAIRED by index.

    Point estimate: cumulative R ordered by exit time. Interval: paired resample of
    trades with replacement, re-sorted by exit time inside each resample. This preserves
    the marginal distribution and the ordering of whatever was drawn; it does NOT preserve
    serial dependence, so read it as a rough sampling interval, not a path-risk figure.
    """
    if not ctrl_rows:
        return {"n": 0}
    n = len(ctrl_rows)
    order = sorted(range(n), key=lambda k: (ctrl_rows[k][0], k))
    c_sorted = np.array([ctrl_rows[k][1] for k in order])
    order2 = sorted(range(n), key=lambda k: (corr_rows[k][0], k))
    n_sorted = np.array([corr_rows[k][1] for k in order2])
    dd_c, dd_n = _maxdd(c_sorted), _maxdd(n_sorted)
    rng = rng or np.random.default_rng(SEED + 2)
    ct = np.array([r[0].timestamp() for r in ctrl_rows])
    nt = np.array([r[0].timestamp() for r in corr_rows])
    cv = np.array([r[1] for r in ctrl_rows]); nv = np.array([r[1] for r in corr_rows])
    bc = np.empty(nboot); bn = np.empty(nboot)
    for b in range(nboot):
        pick = rng.integers(0, n, size=n)
        oc = pick[np.argsort(ct[pick], kind="stable")]
        on = pick[np.argsort(nt[pick], kind="stable")]
        bc[b] = _maxdd(cv[oc]); bn[b] = _maxdd(nv[on])
    d = bn - bc
    return {"n": n,
            "control_maxdd_R": dd_c,
            "corrected_maxdd_R": dd_n,
            "delta_maxdd_R": dd_n - dd_c,
            "control_ci95_bootstrap": [float(np.percentile(bc, 2.5)),
                                       float(np.percentile(bc, 97.5))],
            "corrected_ci95_bootstrap": [float(np.percentile(bn, 2.5)),
                                         float(np.percentile(bn, 97.5))],
            "delta_ci95_bootstrap": [float(np.percentile(d, 2.5)),
                                     float(np.percentile(d, 97.5))],
            "n_bootstrap": nboot,
            "caveat": ("resampling bootstrap on a path statistic: preserves marginals and "
                       "the ordering of the draw, NOT serial dependence")}


# ============================================================== main
def main() -> int:
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    series, index = R.load_series()   # ~25 s; the pickle cache was dropped (disk full)
    beta_doc = json.loads((OUTDIR / "STEP_A_BETA_V1.json").read_text())
    BETA = {15: beta_doc["per_timeframe"]["M15"]["two_sided_travel"]["beta"],
            16388: beta_doc["per_timeframe"]["H4"]["two_sided_travel"]["beta"],
            16408: beta_doc["per_timeframe"]["D1"]["two_sided_travel"]["beta"]}
    print("beta", BETA, flush=True)

    with gzip.open(R.TRADES, "rt") as fh:
        doc = json.load(fh)
    estate_all = {k: v for k, v in doc["trades"].items() if v}
    estate = {k: v for k, v in estate_all.items() if k not in EXCLUDED}

    def tid(k, r):
        return f"{r['sleeve']}#{k}"

    # ---------------------------------------------------------- Step B
    print("STEP B: per-trade v and multipliers", flush=True)
    atr_cache = {}

    def atrs(key):
        if key not in atr_cache:
            bars, _ = series[key]
            n = len(bars)
            h = np.fromiter((b.h for b in bars), np.float64, n)
            l = np.fromiter((b.l for b in bars), np.float64, n)
            c = np.fromiter((b.c for b in bars), np.float64, n)
            tr = _true_range(h, l, c)
            atr_cache[key] = (_atr_vec(tr, 14), _atr_vec(tr, 50))
        return atr_cache[key]

    per_trade_v = {}
    sleeve_stopcal = collections.defaultdict(list)
    v_missing = collections.Counter()
    for sleeve, rows in sorted(estate_all.items()):
        for k, r in enumerate(rows):
            key = (r["symbol"], int(r["timeframe"]))
            if key not in index:
                v_missing[f"{sleeve}:no_series"] += 1
                continue
            i = index[key].get(_dt.datetime.fromisoformat(r["decision_bar_iso"]))
            if i is None:
                v_missing[f"{sleeve}:bar_not_found"] += 1
                continue
            a14, a50 = atrs(key)
            if i >= len(a14) or a50[i] <= 0 or a14[i] <= 0:
                v_missing[f"{sleeve}:atr_undefined"] += 1
                continue
            v = float(a14[i] / a50[i])
            per_trade_v[tid(k, r)] = (v, int(r["timeframe"]))
            sd = float(r["sl_distance_price"])
            if a14[i] > 0 and sd > 0:
                sleeve_stopcal[sleeve].append(sd / float(a14[i]))

    # spot-check the vectorised ATR against the scalar reference on real trade bars
    spot = []
    for sleeve, rows in list(sorted(estate.items()))[:6]:
        for k, r in enumerate(rows[:3]):
            key = (r["symbol"], int(r["timeframe"]))
            if key not in index:
                continue
            i = index[key].get(_dt.datetime.fromisoformat(r["decision_bar_iso"]))
            if i is None:
                continue
            bars, _ = series[key]
            a14, a50 = atrs(key)
            spot.append(max(abs(a14[i] - atr_n(bars, i, 14)), abs(a50[i] - atr_n(bars, i, 50))))
    spot_max = max(spot) if spot else 0.0
    assert spot_max < 1e-8, spot_max

    step_b = {}
    mults_corrected = {}
    for sleeve, rows in sorted(estate.items()):
        raws, ids = [], []
        for k, r in enumerate(rows):
            key = tid(k, r)
            if key not in per_trade_v:
                continue
            v, tf = per_trade_v[key]
            raws.append(v ** BETA[tf]); ids.append(key)
        if not raws:
            step_b[sleeve] = {"n": 0}
            continue
        gm = float(np.exp(np.mean(np.log(raws))))
        norm = [x / gm for x in raws]
        wins = [min(WINSOR_HI, max(WINSOR_LO, x)) for x in norm]
        nb = sum(1 for a, b in zip(norm, wins) if a != b)
        for key, m in zip(ids, wins):
            mults_corrected[key] = m
        vv = [per_trade_v[key][0] for key in ids]
        sc = sleeve_stopcal.get(sleeve, [])
        step_b[sleeve] = {
            "n_with_multiplier": len(ids),
            "n_trades": len(rows),
            "n_without_multiplier_left_at_1.0": len(rows) - len(ids),
            "beta_used": BETA[int(rows[0]["timeframe"])],
            "timeframe": R.TF_NAME[int(rows[0]["timeframe"])],
            "geomean_normaliser_raw_mult": gm,
            "v_atr14_over_atr50": {"p5": float(np.percentile(vv, 5)),
                                   "p50": float(np.percentile(vv, 50)),
                                   "p95": float(np.percentile(vv, 95)),
                                   "mean": float(np.mean(vv))},
            "stop_mult_before_winsor": {"p5": float(np.percentile(norm, 5)),
                                        "p50": float(np.percentile(norm, 50)),
                                        "p95": float(np.percentile(norm, 95)),
                                        "min": float(np.min(norm)),
                                        "max": float(np.max(norm))},
            "stop_mult_after_winsor": {"p5": float(np.percentile(wins, 5)),
                                       "p50": float(np.percentile(wins, 50)),
                                       "p95": float(np.percentile(wins, 95)),
                                       "geomean": float(np.exp(np.mean(np.log(wins))))},
            "n_winsor_bound": nb,
            "frac_winsor_bound": nb / len(wins),
            "stop_over_atr14_at_decision_bar": (
                {"n": len(sc), "median": float(np.median(sc)),
                 "p5": float(np.percentile(sc, 5)), "p95": float(np.percentile(sc, 95)),
                 "cv": float(np.std(sc) / np.mean(sc)) if np.mean(sc) else None}
                if sc else None),
            "target_convention_under_stop_rescale": (
                "fixed_price" if sleeve in TARGET_FIXED_PRICE else "scales_with_stop"),
        }
    print(f"  step B done ({time.time()-t0:.0f}s)", flush=True)

    # ---------------------------------------------------------- faithfulness
    print("PROOF 1: walk_pertrade(all mults 1.0) == walk(stop_mult=1.0)", flush=True)
    # small sleeves plus BOTH trailing_runner sleeves, so the trail arms are covered
    small = {k: v for k, v in sorted(estate.items())
             if len(v) <= 400 or R._trail_policy(k)[0] is not None}
    faithful = _prove_copy_faithful(small, series, index, tid)

    print("PROOF 2: native-contract uncorrected arm reproduces published r_gross",
          flush=True)
    ones = {}
    ctrl_check = {"checked": 0, "mismatch": 0, "max_abs_err": 0.0, "examples": []}
    for sleeve, rows in sorted(estate_all.items()):
        rowsout = []
        walk_pertrade(rows, series, index, "native", MAXBARS, "mid", False, ones, tid,
                      target_scales=True, collect=rowsout)
        pub = {}
        for k, r in enumerate(rows):
            pub[tid(k, r)] = float(r["r_gross"])
        for (t, val, _reason, _et, _m) in rowsout:
            e = abs(val - pub[t])
            ctrl_check["checked"] += 1
            ctrl_check["max_abs_err"] = max(ctrl_check["max_abs_err"], e)
            if e > 1e-9:
                ctrl_check["mismatch"] += 1
                if len(ctrl_check["examples"]) < 6:
                    ctrl_check["examples"].append({"tid": t, "published": pub[t],
                                                   "rederived": val})
    print("  ", json.dumps(ctrl_check), flush=True)

    # ---------------------------------------------------------- Step C
    print("STEP C: arms", flush=True)
    arms = {}   # (arm, band, tgtmode) -> {sleeve: rows}
    specs = [("control", {}, "native"),
             ("corrected", mults_corrected, "native"),
             ("corrected_altconv", mults_corrected, "alt")]
    for band in BANDS:
        for name, mults, tmode in specs:
            if name == "control" and tmode != "native":
                continue
            store = {}
            for sleeve, rows in sorted(estate.items()):
                scales = (sleeve not in TARGET_FIXED_PRICE) if tmode == "native" \
                    else (sleeve in TARGET_FIXED_PRICE)
                out = []
                vals, by_day, reasons, unp, skips = walk_pertrade(
                    rows, series, index, "native", MAXBARS, band, True, mults, tid,
                    target_scales=scales, collect=out)
                store[sleeve] = {"rows": out, "unpriceable": unp, "skips": dict(skips)}
            arms[(name, band, tmode)] = store
            print(f"  arm {name:18s} band={band:5s} tgt={tmode:6s} "
                  f"({time.time()-t0:.0f}s)", flush=True)

    # excluded sleeves: control only
    excl_store = {}
    for sleeve in EXCLUDED:
        rows = estate_all.get(sleeve)
        if not rows:
            continue
        out = []
        walk_pertrade(rows, series, index, "native", MAXBARS, HEADLINE_BAND, True, {}, tid,
                      target_scales=True, collect=out)
        excl_store[sleeve] = out

    # ---------------------------------------------------------- Step D
    print("STEP D: statistics", flush=True)

    def pair(sleeve, band, tmode):
        c = arms[("control", band, "native")][sleeve]["rows"]
        n = arms[("corrected", band, tmode)][sleeve]["rows"] if tmode == "native" \
            else arms[("corrected_altconv", band, tmode)][sleeve]["rows"]
        assert [x[0] for x in c] == [x[0] for x in n], f"population mismatch {sleeve}"
        return c, n

    def stats_for(rows_c, rows_n, band, do_dd):
        cv = [x[1] for x in rows_c]; nv = [x[1] for x in rows_n]
        rec = {
            "n": len(cv),
            "control_expectancy_R_per_trade": _mean_ci(cv, rng=rng),
            "corrected_expectancy_R_per_trade": _mean_ci(nv, rng=rng),
            "paired_delta_R_per_trade": _paired_delta(cv, nv, rng=rng),
            "stop_rate_control": _wilson(sum(1 for x in rows_c if x[2] == "stop"), len(cv)),
            "stop_rate_corrected": _wilson(sum(1 for x in rows_n if x[2] == "stop"), len(nv)),
            "exit_reasons_control": dict(collections.Counter(x[2] for x in rows_c)),
            "exit_reasons_corrected": dict(collections.Counter(x[2] for x in rows_n)),
            "n_exit_reason_changed": sum(1 for a, b in zip(rows_c, rows_n) if a[2] != b[2]),
        }
        if do_dd:
            rec["max_drawdown"] = _maxdd_pair([(x[3], x[1]) for x in rows_c],
                                              [(x[3], x[1]) for x in rows_n], rng=rng)
        return rec

    per_sleeve = {}
    for sleeve in sorted(estate):
        rec = {"armed": sleeve in ARMED,
               "timeframe": step_b.get(sleeve, {}).get("timeframe"),
               "exit_policy_walked": ("trailing_runner"
                                      if R._trail_policy(sleeve)[0] is not None else "plain"),
               "step_b": step_b.get(sleeve, {}),
               "bands": {}}
        for band in BANDS:
            c, n = pair(sleeve, band, "native")
            rec["bands"][band] = stats_for(c, n, band, do_dd=(band == HEADLINE_BAND))
            rec["bands"][band]["unpriceable"] = \
                arms[("control", band, "native")][sleeve]["unpriceable"]
            rec["bands"][band]["skips"] = arms[("control", band, "native")][sleeve]["skips"]
        if sleeve in TARGET_FIXED_PRICE:
            c, n = pair(sleeve, HEADLINE_BAND, "alt")
            rec["sensitivity_target_scales_with_stop_instead"] = {
                "band": HEADLINE_BAND, "why": TARGET_FIXED_PRICE[sleeve],
                **stats_for(c, n, HEADLINE_BAND, do_dd=False)}
        per_sleeve[sleeve] = rec

    def pooled(names, band, tmode="native", do_dd=True):
        rc, rn = [], []
        for s in names:
            c, n = pair(s, band, tmode)
            rc += c; rn += n
        return stats_for(rc, rn, band, do_dd)

    all_sleeves = sorted(estate)
    totals = {
        "estate_excluding_stop_dependent": {
            "sleeves": all_sleeves, "n_sleeves": len(all_sleeves),
            "bands": {b: pooled(all_sleeves, b, do_dd=(b == HEADLINE_BAND))
                      for b in BANDS}},
        "armed_four": {
            "sleeves": list(ARMED),
            "bands": {b: pooled(list(ARMED), b, do_dd=(b == HEADLINE_BAND))
                      for b in BANDS}},
    }

    excluded_report = {}
    for sleeve, rows in excl_store.items():
        cv = [x[1] for x in rows]
        excluded_report[sleeve] = {
            "status": "EXCLUDED",
            "reason": EXCLUDED[sleeve],
            "n": len(cv),
            "control_expectancy_R_per_trade": _mean_ci(cv, rng=rng),
            "stop_rate_control": _wilson(sum(1 for x in rows if x[2] == "stop"), len(cv)),
            "corrected_arm": None,
        }

    flagged = []
    for sleeve, rec in per_sleeve.items():
        for band in BANDS:
            d = rec["bands"][band]["paired_delta_R_per_trade"]
            if d.get("excludes_zero"):
                flagged.append({"sleeve": sleeve, "band": band, "armed": rec["armed"],
                                "n": d["n"], "mean_delta": d["mean_delta"],
                                "ci95": d["ci95_paired_bootstrap"],
                                "direction": "IMPROVES" if d["mean_delta"] > 0 else "WORSENS"})

    out = {
        "what": ("mis-scaling of ATR14-pegged stops implied by the ATR14/ATR50 vol-regime "
                 "relationship, measured on the GTOS sleeve estate and priced per sleeve"),
        "generated": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "population": str(R.TRADES),
        "bars": R.BARS,
        "walker": ("r1_frontier_surface_sweep.walk, copied to walk_pertrade with one "
                   "arithmetic change (the stop line); faithfulness asserted below"),
        "quote_convention": ("corrected=True (r1's repaired BID-anchored fill convention) "
                             "for both arms; band mid is the headline"),
        "maxbars": MAXBARS,
        "target_convention_note": TARGET_FIXED_PRICE,
        "winsor": [WINSOR_LO, WINSOR_HI],
        "beta_used_per_timeframe": {R.TF_NAME[k]: v for k, v in BETA.items()},
        "beta_source": str(OUTDIR / "STEP_A_BETA_V1.json"),
        "proof_walker_copy_is_faithful": faithful,
        "proof_native_arm_reproduces_published_r_gross": ctrl_check,
        "atr_vector_vs_scalar_max_abs_err_on_trade_bars": spot_max,
        "trades_without_a_multiplier": dict(v_missing),
        "per_sleeve": per_sleeve,
        "totals": totals,
        "excluded_sleeves": excluded_report,
        "paired_ci_excludes_zero": flagged,
        "elapsed_s": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print("WROTE", OUT, f"({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
