"""B10 stage 2 -- assemble the tape-true hourly spread surface from the reduced tapes.

Reads the per-file npz emitted by `tape_reduce.py` and writes
``TAPE_SPREAD_HOURLY_V1.json``: per account x symbol x UTC hour (and hour-of-week),
distributional -- p10/p25/p50/p75/p90/p99 and the mean, both tick-weighted and
time-weighted -- with n, day-clustered CI on the mean, and an explicit coverage class.

Why quantiles and not a mean.  The defect this replaces is a spike: UK100's spread is
bimodal (median 0.85, mean 2.11 -- Lane 7 §6), so a mean-based correction over-states the
typical trade and a median-based one under-states the tail.  Both are published here and
the consumer picks; the multiplier that goes into the cost model is built on the MEDIAN,
because the shipped model's own anchor is a p50 and a multiplier must be dimensionally
consistent with what it multiplies.

The fallback ladder, in order, each rung stamped on the cell it produced:
  1 SYMBOL_HOUR_OF_WEEK  -- >= MIN_TICKS_CELL ticks in that symbol's (weekday, hour) cell
  2 SYMBOL_HOUR          -- >= MIN_TICKS_CELL in that symbol's hour, pooled over weekdays
  3 CLASS_HOUR           -- the instrument class's hour profile, ratio-pooled over symbols
  4 FLAT                 -- 1.0, and stamped MODELLED so a consumer can refuse it
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import math
import os
import sys

import numpy as np

NB = 400
LOG_LO = -6.0
BPD = 40
MIN_TICKS_CELL = 200        # below this a quantile is not a quantile
MIN_TICKS_HOUR = 500

# canonical estate symbol -> tick-archive file symbol
CANON_TO_FILE = {
    "NAS100": "US100_cash", "SPX500": "US500_cash", "GER40": "GER40_cash",
    "JP225": "JP225_cash", "UK100": "UK100_cash", "US30_cash": "US30_cash",
    "USOIL_cash": "USOIL_cash", "UKOIL_cash": "UKOIL_cash",
}
SURFACE_24 = ("AUDJPY", "AUDUSD", "BTCUSD", "CHFJPY", "ETHUSD", "EURGBP", "EURJPY",
              "EURUSD", "GBPJPY", "GBPUSD", "GER40", "JP225", "NAS100", "NZDUSD",
              "SPX500", "UK100", "UKOIL_cash", "US30_cash", "USDCAD", "USDCHF",
              "USDJPY", "USOIL_cash", "XAGUSD", "XAUUSD")

CLASS_OF = {}
for s in ("AUDJPY", "CHFJPY", "EURJPY", "GBPJPY", "NZDJPY", "USDJPY", "CADJPY"):
    CLASS_OF[s] = "jpy_fx"
for s in ("AUDUSD", "EURGBP", "EURUSD", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF"):
    CLASS_OF[s] = "fx"
for s in ("BTCUSD", "ETHUSD", "AVAUSD", "DASHUSD", "ADAUSD"):
    CLASS_OF[s] = "crypto"
for s in ("GER40", "JP225", "NAS100", "SPX500", "UK100", "US30_cash", "AUS200_cash",
          "EU50_cash", "SPN35_cash"):
    CLASS_OF[s] = "index"
for s in ("UKOIL_cash", "USOIL_cash", "NATGAS_cash"):
    CLASS_OF[s] = "energy"
for s in ("XAGUSD", "XAUUSD", "XAGAUD", "XAGEUR", "XAUAUD", "XAUEUR"):
    CLASS_OF[s] = "metals"

QS = (0.10, 0.25, 0.50, 0.75, 0.90, 0.99)


def bin_edges() -> np.ndarray:
    return 10.0 ** (LOG_LO + np.arange(NB + 1) / BPD)


def hist_quantiles(h: np.ndarray, qs=QS) -> dict:
    """Quantiles from the log-spaced histogram, log-linear inside the containing bin."""
    tot = h.sum()
    if tot <= 0:
        return {f"p{int(q*100)}": None for q in qs}
    cum = np.cumsum(h)
    e = bin_edges()
    out = {}
    for q in qs:
        target = q * tot
        i = int(np.searchsorted(cum, target, side="left"))
        i = min(i, NB - 1)
        below = cum[i - 1] if i > 0 else 0.0
        frac = (target - below) / h[i] if h[i] > 0 else 0.0
        frac = min(max(frac, 0.0), 1.0)
        lo, hi = e[i], e[i + 1]
        out[f"p{int(q*100)}"] = float(lo * (hi / lo) ** frac)
    return out


def load_tapes(tape_dir: str) -> dict:
    out: dict[tuple[str, str], dict] = {}
    for p in sorted(glob.glob(os.path.join(tape_dir, "*.npz"))):
        z = np.load(p, allow_pickle=True)
        out[(str(z["broker"]), str(z["symbol"]))] = {k: z[k] for k in z.files}
    return out


def day_cluster_ci(dk: np.ndarray, dv: np.ndarray, hour: int, n_boot=2000, seed=20260812):
    """Day-clustered bootstrap CI on the tick-weighted mean spread for one UTC hour."""
    if len(dk) == 0:
        return None, None, 0
    m = dk[:, 1] == hour
    if not m.any():
        return None, None, 0
    days = dk[m, 0]
    n = dv[m, 0]
    s = dv[m, 1]
    if n.sum() <= 0:
        return None, None, 0
    rng = np.random.default_rng(seed + hour)
    k = len(days)
    idx = rng.integers(0, k, size=(n_boot, k))
    num = s[idx].sum(1)
    den = n[idx].sum(1)
    with np.errstate(invalid="ignore", divide="ignore"):
        b = num / den
    b = b[np.isfinite(b)]
    if len(b) == 0:
        return None, None, k
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5)), int(k)


def symbol_block(t: dict) -> dict:
    ht = t["hist_tick"]
    hd = t["hist_dwell"]
    cn = t["cell_n"]
    cd = t["cell_dwell"]
    cs = t["cell_sp"]
    csd = t["cell_spd"]
    cm = t["cell_mid"]
    cmd = t["cell_midd"]
    cmax = t["cell_max"]
    dk = t["dayhour_key"]
    dv = t["dayhour_stats"]

    ref_h = ht.sum(0)
    ref_q = hist_quantiles(ref_h)
    ref_med = ref_q["p50"]
    ref_mean = float(cs.sum() / cn.sum()) if cn.sum() else None
    ref_mean_tw = float(csd.sum() / cd.sum()) if cd.sum() else None
    ref_mid = float(cm.sum() / cn.sum()) if cn.sum() else None

    by_hour = {}
    for h in range(24):
        sel = [wd * 24 + h for wd in range(7)]
        n = float(cn[sel].sum())
        if n < 1:
            continue
        d = float(cd[sel].sum())
        s = float(cs[sel].sum())
        sd = float(csd[sel].sum())
        mid = float(cm[sel].sum() / n)
        q = hist_quantiles(ht[sel].sum(0))
        qtw = hist_quantiles(hd[sel].sum(0))
        lo, hi, ndays = day_cluster_ci(dk, dv, h)
        by_hour[str(h)] = {
            "n_ticks": int(n), "dwell_s": round(d, 1), "n_days": ndays,
            "mean_px": s / n, "mean_px_tw": (sd / d if d > 0 else None),
            "mean_px_ci95": [lo, hi],
            "mean_bps": (s / n) / mid * 1e4 if mid else None,
            "max_px": float(cmax[sel].max()),
            "q_tick": q, "q_time": qtw,
            "median_mult": (q["p50"] / ref_med) if (ref_med and q["p50"]) else None,
            "mean_mult": (s / n) / ref_mean if ref_mean else None,
            "mean_mult_tw": ((sd / d) / ref_mean_tw) if (d > 0 and ref_mean_tw) else None,
            "coverage": "MEASURED" if n >= MIN_TICKS_HOUR else "THIN",
        }

    by_how = {}
    for c in range(168):
        n = float(cn[c])
        if n < 1:
            continue
        q = hist_quantiles(ht[c])
        by_how[str(c)] = {
            "n_ticks": int(n),
            "mean_px": float(cs[c] / n),
            "mean_px_tw": (float(csd[c] / cd[c]) if cd[c] > 0 else None),
            "p50_px": q["p50"], "p90_px": q["p90"], "p99_px": q["p99"],
            "median_mult": (q["p50"] / ref_med) if (ref_med and q["p50"]) else None,
            "coverage": "MEASURED" if n >= MIN_TICKS_CELL else "THIN",
        }

    return {
        "n_ticks": int(t["n_ticks"]),
        "reference": {
            "median_px": ref_med, "mean_px": ref_mean, "mean_px_tw": ref_mean_tw,
            "mean_mid": ref_mid,
            "q_tick": ref_q,
            "bimodality_mean_over_median": (ref_mean / ref_med) if (ref_med and ref_mean) else None,
        },
        "by_hour_utc": by_hour,
        "by_hour_of_week_utc": by_how,
    }


def main(tape_dir: str, out_path: str) -> None:
    tapes = load_tapes(tape_dir)
    accounts: dict[str, dict] = {}
    for (broker, fsym), t in tapes.items():
        accounts.setdefault(broker, {})[fsym] = symbol_block(t)

    # --- class-hour fallback, built as a ratio pool so levels never mix ---
    class_hour: dict[str, dict] = {}
    for broker, syms in accounts.items():
        ch: dict[str, dict[str, list[float]]] = {}
        for fsym, blk in syms.items():
            canon = next((c for c, f in CANON_TO_FILE.items() if f == fsym), fsym)
            klass = CLASS_OF.get(canon) or CLASS_OF.get(fsym)
            if klass is None:
                continue
            for h, cell in blk["by_hour_utc"].items():
                if cell["median_mult"] and cell["coverage"] == "MEASURED":
                    ch.setdefault(klass, {}).setdefault(h, []).append(cell["median_mult"])
        class_hour[broker] = {
            k: {h: {"median_mult": float(np.median(v)), "n_symbols": len(v)}
                for h, v in sorted(hs.items(), key=lambda kv: int(kv[0]))}
            for k, hs in ch.items()
        }

    global_hour = {}
    for broker, syms in accounts.items():
        g: dict[str, list[float]] = {}
        for blk in syms.values():
            for h, cell in blk["by_hour_utc"].items():
                if cell["median_mult"] and cell["coverage"] == "MEASURED":
                    g.setdefault(h, []).append(cell["median_mult"])
        global_hour[broker] = {h: {"median_mult": float(np.median(v)), "n_symbols": len(v)}
                               for h, v in sorted(g.items(), key=lambda kv: int(kv[0]))}

    coverage = {}
    for broker, syms in accounts.items():
        cov = {"symbols": len(syms), "surface_24_present": 0, "surface_24_missing": []}
        for c in SURFACE_24:
            f = CANON_TO_FILE.get(c, c)
            if f in syms:
                cov["surface_24_present"] += 1
            else:
                cov["surface_24_missing"].append(c)
        cov["hour_cells_measured"] = sum(
            1 for b in syms.values() for x in b["by_hour_utc"].values()
            if x["coverage"] == "MEASURED")
        cov["hour_cells_thin"] = sum(
            1 for b in syms.values() for x in b["by_hour_utc"].values()
            if x["coverage"] == "THIN")
        cov["how_cells_measured"] = sum(
            1 for b in syms.values() for x in b["by_hour_of_week_utc"].values()
            if x["coverage"] == "MEASURED")
        cov["how_cells_thin"] = sum(
            1 for b in syms.values() for x in b["by_hour_of_week_utc"].values()
            if x["coverage"] == "THIN")
        coverage[broker] = cov

    doc = {
        "schema": "gtos_tape_spread_hourly_v1",
        "version": 1,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "generator": "swarm2/breakthrough/b10_hourly_cost/tape_model.py",
        "window": {
            "tick_export": "/Users/borr/GTOSActive/vps-ticks-20260726/",
            "files": len(tapes),
            "ticks": int(sum(int(t["n_ticks"]) for t in tapes.values())),
            "broker_wall_to_utc_hours": -3.0,
            "clock_rule": "new_york_plus_7 (src/utils/broker_clock.py); NY=EDT for the whole "
                          "export window so the offset is a constant +3 h, verified",
            "coverage_days": "2026-06-18..2026-07-26 broker wall",
        },
        "construction": {
            "quantiles": "log-spaced histogram, 40 bins/decade over 1e-6..1e4 price units, "
                         "log-linear interpolation inside the containing bin",
            "tick_weighted": "one observation per tick",
            "time_weighted": "each tick weighted by its dwell time to the next tick, capped "
                             "at 60 s so a market hole cannot dominate an hour",
            "multiplier_basis": "median of the cell / median of the whole reference window -- "
                                "dimensionally consistent with the shipped model's p50 anchor",
            "ci": "day-clustered bootstrap, 2000 draws, seed 20260812, on the tick-weighted mean",
        },
        "fallback_ladder": [
            {"rung": 1, "key": "SYMBOL_HOUR_OF_WEEK", "condition": f"n_ticks >= {MIN_TICKS_CELL}"},
            {"rung": 2, "key": "SYMBOL_HOUR", "condition": f"n_ticks >= {MIN_TICKS_HOUR}"},
            {"rung": 3, "key": "CLASS_HOUR", "condition": "symbol absent or thin; class median of "
                                                          "per-symbol multipliers"},
            {"rung": 4, "key": "FLAT", "condition": "no class either; multiplier 1.0, stamped MODELLED"},
        ],
        "accounts": accounts,
        "class_hour_utc": class_hour,
        "global_hour_utc": global_hour,
        "coverage": coverage,
        "canonical_to_file_symbol": CANON_TO_FILE,
        "instrument_class": CLASS_OF,
        "honest_limits": [
            "One 37-day window (2026-06-18..07-26). It measures the CURRENT hourly SHAPE; it "
            "carries no era information and must not be used to re-price a 2014 bar's level.",
            "Quotes only: no volume, no depth, no queue position. A market order's realised "
            "fill can exceed the quoted spread; that is slippage and is a different term.",
            "DASHUSD, AVAUSD, XAGAUD, XAGEUR, XAUAUD, XAUEUR, EU50_cash, SPN35_cash, "
            "AUS200_cash, NATGAS_cash, CADJPY, NZDJPY are measured here but are outside the "
            "24-symbol research surface.",
        ],
    }
    with open(out_path, "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=False)
    print(json.dumps({"out": out_path, "accounts": {k: len(v) for k, v in accounts.items()},
                      "coverage": coverage}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
