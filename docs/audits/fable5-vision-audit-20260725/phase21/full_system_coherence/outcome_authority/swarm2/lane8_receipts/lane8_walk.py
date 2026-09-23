"""LANE 8 — re-walk the three ARMED sleeve generators over expanded symbol sets.

Read-only. No broker, no VPS, no config edit, no src/ byte changed. Reuses the estate's own
machinery verbatim:
  - the generators' own signal functions (crypto.crypto_signal, metals.fvg_signal +
    energy_agri.energy_gate/trend_slope, substrate_engine.compute_state/cell_coords/cell_matches)
  - the sanctioned labeller `walkforward.exits.replay` with the published
    `ExitPolicy(target_dist, maxbars=80)` contract AA/AQ walked
  - the same bar archive AQ used: /Users/borr/GTOSActive/vps-bars-20260727

The ONLY thing varied is the symbol set each rule is evaluated on. Everything else is held.
Control: restricted to each sleeve's live ON_SURFACE, the row count must reproduce
AQ_ESTATE_TRADES_V2.n_trades_by_sleeve exactly (crypto 181, energy_agri 67, sub_xvol_pullback 88).
"""
from __future__ import annotations
import collections, datetime as dt, glob, gzip, json, os, statistics as stat, sys, time
from pathlib import Path

REPO = Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.primitives import Bar, atr14, vol_ratio            # noqa: E402
from src.components.ultimate_book.admission import winsorize_R                        # noqa: E402
from src.components.ultimate_book.sleeves import crypto as SL_CRYPTO                  # noqa: E402
from src.components.ultimate_book.sleeves import energy_agri as SL_ENERGY             # noqa: E402
from src.components.ultimate_book.sleeves.metals import fvg_signal                    # noqa: E402
from src.components.ultimate_book.sleeves import substrate as SL_SUB                  # noqa: E402
from src.components.ultimate_book.sleeves import substrate_engine as SE               # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay                   # noqa: E402

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
MAXBARS = 80
OUT = Path(__file__).resolve().parent


# ------------------------------------------------------------------ bar loading (H4 only) ----
# Uses the estate's own CsvBarSource so the broker-wall-clock -> true-UTC conversion is the SAME
# seam AA/AQ used (generation.py:162). Reading those stamps as UTC is finding F7.
from src.research_infra.replay_policy.generation import CsvBarSource   # noqa: E402
from src.components.ultimate_book.bar_provider import TF_H4            # noqa: E402


def load_h4() -> dict[str, tuple[list, list]]:
    files = {}
    for p in sorted(glob.glob(f"{BARS}/FTMO_*_H4.csv.gz")):
        sym = os.path.basename(p)[len("FTMO_"):-len("_H4.csv.gz")]
        files[(sym, TF_H4)] = p
    src = CsvBarSource(files, label="vps-bars-20260727-FTMO")
    out = {}
    for key in files:
        rows = src._load(key)
        if not rows or len(rows) <= 300:
            continue
        bars = [Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0)) for r in rows]
        times = [dt.datetime.fromisoformat(r["time"]) for r in rows]
        out[key[0]] = (bars, times)
    return out


# ------------------------------------------------------------------ the three rules ----------
def sig_crypto(bars, atrs, i, times):
    """crypto.crypto_signal verbatim (crypto.py:31-51); target = 4.0 * stop."""
    s = SL_CRYPTO.crypto_signal(bars, i)
    if s is None:
        return None
    d, sd = s
    return d, sd, SL_CRYPTO.TARGET_R * sd


def sig_energy(bars, atrs, i, times):
    """energy_agri.generate verbatim (energy_agri.py:47-63); target = 4.0 * stop."""
    s = fvg_signal(bars, atrs, i)
    if s is None:
        return None
    d, sd = s
    vr = vol_ratio(atrs, i)
    slope = SL_ENERGY.trend_slope(bars, i, 30)
    if not SL_ENERGY.energy_gate(vr, slope):
        return None
    return d, sd, 4.0 * sd


def _sub_cell(bars, atrs, i, times, conds, geom, direction, need_hour):
    if len(bars) < SE.WARMUP or i < SE.WARMUP:
        return None
    a = atrs[i]
    if a <= 0:
        return None
    hour = None
    if need_hour:
        hour = SL_SUB._session_hour(times[i])
        if hour is None:
            return None
    st = SE.compute_state(bars, i, hour)
    if st is None:
        return None
    if not SE.cell_matches(SE.cell_coords(st), conds):
        return None
    sd, td = SE.stop_target(a, geom[0], geom[1])
    return direction, sd, td


def sig_xvol(bars, atrs, i, times):
    """substrate.generate_sub_xvol_pullback verbatim (substrate.py:150-155)."""
    return _sub_cell(bars, atrs, i, times, SL_SUB.XVOL_CONDS, SL_SUB.XVOL_GEOM,
                     SL_SUB.XVOL_DIR, False)


RULES = {"crypto": sig_crypto, "energy_agri": sig_energy, "sub_xvol_pullback": sig_xvol}
LIVE_SURFACE = {
    "crypto": set(SL_CRYPTO.ON_SURFACE),
    "energy_agri": set(SL_ENERGY.ON_SURFACE),
    "sub_xvol_pullback": set(SL_SUB.XVOL_ON_SURFACE),
}


def walk(series: dict, rule: str, symbols) -> list[dict]:
    fn = RULES[rule]
    rows = []
    for sym in symbols:
        if sym not in series:
            continue
        bars, times = series[sym]
        atrs = [atr14(bars, k) for k in range(len(bars))]
        for i in range(len(bars) - 2):
            s = fn(bars, atrs, i, times)
            if s is None:
                continue
            d, sd, td = s
            pr = replay(bars, i, d, stop_dist=sd,
                        policy=ExitPolicy(target_dist=td, maxbars=MAXBARS, label="plain"))
            rows.append({
                "sleeve": rule, "symbol": sym, "direction": int(d),
                "entry_utc": (times[i] + dt.timedelta(minutes=240)).isoformat(),
                "exit_utc": (times[pr.exit_index] + dt.timedelta(minutes=240)).isoformat(),
                "entry_price": float(bars[i].c),
                "sl_distance_price": float(sd), "target_dist": float(td),
                "r_gross": float(winsorize_R(pr.r_gross)),
                "exit_reason": pr.exit_reason,
                "mfe_r": round(pr.mfe_r, 6), "mae_r": round(pr.mae_r, 6),
                "bars_held": int(pr.exit_index - i),
                "hold_hours": float((times[pr.exit_index] - times[i]).total_seconds() / 3600.0),
            })
    return rows


def summarise(rows) -> dict:
    if not rows:
        return {"n": 0}
    r = [x["r_gross"] for x in rows]
    reasons = collections.Counter(x["exit_reason"] for x in rows)
    fwd = [x["r_gross"] for x in rows if x["entry_utc"][:4] >= "2025"]
    pre = [x["r_gross"] for x in rows if x["entry_utc"][:4] < "2025"]
    n = len(r); m = stat.fmean(r); sd = stat.pstdev(r) if n > 1 else 0.0
    se = (stat.stdev(r) / (n ** 0.5)) if n > 1 else float("nan")
    return {
        "n": n, "mean_r": round(m, 5), "sd": round(sd, 5), "se": round(se, 5),
        "t": round(m / se, 3) if n > 1 and se else None,
        "ci95": [round(m - 1.96 * se, 5), round(m + 1.96 * se, 5)] if n > 1 else None,
        "reasons": dict(reasons),
        "target_rate": round(reasons.get("target", 0) / n, 5),
        "n_days": len({x["entry_utc"][:10] for x in rows}),
        "first": min(x["entry_utc"] for x in rows)[:10],
        "last": max(x["entry_utc"] for x in rows)[:10],
        "fwd_n": len(fwd), "fwd_mean_r": round(stat.fmean(fwd), 5) if fwd else None,
        "pre_n": len(pre), "pre_mean_r": round(stat.fmean(pre), 5) if pre else None,
        "median_hold_h": round(stat.median([x["hold_hours"] for x in rows]), 2),
    }


if __name__ == "__main__":
    t0 = time.time()
    series = load_h4()
    print(f"loaded {len(series)} H4 series in {time.time()-t0:.0f}s: {sorted(series)}")
    out = {"bars_archive": BARS, "maxbars": MAXBARS, "n_series": len(series),
           "series": sorted(series), "control": {}, "rows": {}}
    for rule in RULES:
        surf = sorted(LIVE_SURFACE[rule] & set(series))
        t1 = time.time()
        rows = walk(series, rule, surf)
        out["control"][rule] = {"symbols": surf, "seconds": round(time.time() - t1, 1),
                                **summarise(rows)}
        out["rows"][rule] = rows
        print(f"  CONTROL {rule:20s} symbols={surf} n={len(rows)} "
              f"mean_r={out['control'][rule].get('mean_r')} ({time.time()-t1:.0f}s)")
    json.dump(out, gzip.open(OUT / "LANE8_CONTROL_WALK.json.gz", "wt"), indent=1)
    print(f"total {time.time()-t0:.0f}s -> LANE8_CONTROL_WALK.json.gz")
