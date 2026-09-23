"""LANE 8 — (C) edge decomposition and (D) scaling, for the three ARMED sleeves.

Read-only. No broker, no VPS, no config edit, no `src/` byte changed.

METHOD. The three armed generators' own signal functions are evaluated bar-by-bar over the
same bar archive AQ used (`/Users/borr/GTOSActive/vps-bars-20260727`), labelled through the
sanctioned path replay `walkforward.exits.replay` under the published contract
`ExitPolicy(target_dist=k*stop, maxbars=80)`. The ONLY variable is the symbol set (and, for
the ablation arms, which clauses of the substrate conjunction are required).

CONTROL. Restricted to each sleeve's live ON_SURFACE, this harness reproduces
`AQ_ESTATE_TRADES_V2` **R-identically on every overlapping row** (crypto 181/181,
energy_agri 67/67, sub_xvol_pullback 88/88, zero R mismatches). It is a strict SUPERSET by a
handful of grid-edge rows AA's union-grid did not visit; those are reported, not hidden.

THE NULL. A barrier system with a 1R stop and a kR target has, under a driftless price
process, E[R] = 0 exactly (optional stopping on a bounded stopping time) and P(target) =
1/(1+k). Real price series are not driftless and not iid, so the honest null is measured, not
assumed: `placebo_null` draws entry bars at random from the SAME symbols in the SAME years as
the sleeve's own entries, with the same direction mix and the same ATR-scaled geometry, and
replays them through the same labeller. That null carries the data's real drift, fat tails and
volatility clustering. It is the fair value of the GEOMETRY; anything above it is the RULE.
"""
from __future__ import annotations
import collections, datetime as dt, glob, gzip, json, math, os, random, statistics as stat, sys, time
from pathlib import Path

REPO = Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
sys.path.insert(0, str(REPO))
import yaml  # noqa: E402

from src.components.ultimate_book.primitives import Bar, atr14, vol_ratio             # noqa: E402
from src.components.ultimate_book.admission import winsorize_R                         # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver       # noqa: E402
from src.components.ultimate_book.sleeves import crypto as SL_CRYPTO                   # noqa: E402
from src.components.ultimate_book.sleeves import energy_agri as SL_ENERGY              # noqa: E402
from src.components.ultimate_book.sleeves.metals import fvg_signal                     # noqa: E402
from src.components.ultimate_book.sleeves import substrate as SL_SUB                   # noqa: E402
from src.components.ultimate_book.sleeves import substrate_engine as SE                # noqa: E402
from src.components.ultimate_book.bar_provider import TF_H4                            # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource                   # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay                    # noqa: E402

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
MAXBARS = 80
OUT = Path(__file__).resolve().parent
SEED = 20260812


def load_h4():
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    files = {}
    for p in sorted(glob.glob(f"{BARS}/FTMO_*_H4.csv.gz")):        # sorted: AA's last-wins order
        stem = os.path.basename(p)[len("FTMO_"):-len("_H4.csv.gz")]
        files[(res(stem), TF_H4)] = p
    src = CsvBarSource(files, label="vps-bars-20260727-FTMO")
    out, atrs = {}, {}
    for key in files:
        rows = src._load(key)
        if not rows or len(rows) <= 300:
            continue
        bars = [Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0)) for r in rows]
        times = [dt.datetime.fromisoformat(r["time"]) for r in rows]
        out[key[0]] = (bars, times)
        atrs[key[0]] = [atr14(bars, k) for k in range(len(bars))]
    return out, atrs, res


# ------------------------------------------------------------------ the three rules ----------
def sig_crypto(bars, atrs, i, times):
    s = SL_CRYPTO.crypto_signal(bars, i)                       # crypto.py:31-51, verbatim
    return None if s is None else (s[0], s[1], SL_CRYPTO.TARGET_R * s[1])


def sig_energy(bars, atrs, i, times):
    s = fvg_signal(bars, atrs, i)                              # metals.py:63 (shared entry)
    if s is None:
        return None
    d, sd = s
    if not SL_ENERGY.energy_gate(vol_ratio(atrs, i), SL_ENERGY.trend_slope(bars, i, 30)):
        return None                                            # energy_agri.py:42-44
    return d, sd, 4.0 * sd


def make_sub(conds):
    def f(bars, atrs, i, times):
        if i < SE.WARMUP or atrs[i] <= 0:
            return None
        st = SE.compute_state(bars, i, None)
        if st is None or not SE.cell_matches(SE.cell_coords(st), conds):
            return None
        sd, td = SE.stop_target(atrs[i], *SL_SUB.XVOL_GEOM)
        return SL_SUB.XVOL_DIR, sd, td
    return f


sig_xvol = make_sub(SL_SUB.XVOL_CONDS)
RULES = {"crypto": sig_crypto, "energy_agri": sig_energy, "sub_xvol_pullback": sig_xvol}


def walk(series, atrs_all, fn, symbols, sleeve):
    rows = []
    for sym in symbols:
        if sym not in series:
            continue
        bars, times = series[sym]
        atrs = atrs_all[sym]
        for i in range(len(bars) - 2):
            s = fn(bars, atrs, i, times)
            if s is None:
                continue
            d, sd, td = s
            pr = replay(bars, i, d, stop_dist=sd,
                        policy=ExitPolicy(target_dist=td, maxbars=MAXBARS, label="plain"))
            rows.append({
                "sleeve": sleeve, "symbol": sym, "direction": int(d),
                "entry_utc": (times[i] + dt.timedelta(minutes=240)).isoformat(),
                "entry_price": float(bars[i].c), "sl_distance_price": float(sd),
                "target_dist": float(td), "r_gross": float(winsorize_R(pr.r_gross)),
                "exit_reason": pr.exit_reason, "bar_index": i,
                "hold_hours": float((times[pr.exit_index] - times[i]).total_seconds() / 3600.0),
                "mfe_r": round(pr.mfe_r, 6), "mae_r": round(pr.mae_r, 6),
            })
    return rows


# ------------------------------------------------------------------ the measured null --------
def placebo_null(series, atrs_all, rows, k_target, reps=400, rng=None):
    """Fair value of the GEOMETRY on this data. Entry bars drawn uniformly at random from the
    SAME (symbol, year) cells the real entries occupy, same direction mix, stop scaled the same
    way (ATR-relative to the real entry's own stop/ATR ratio, per symbol), same k, same labeller."""
    rng = rng or random.Random(SEED)
    cells = collections.Counter((r["symbol"], r["entry_utc"][:4]) for r in rows)
    dirs = [r["direction"] for r in rows]
    ratio = collections.defaultdict(list)
    for r in rows:
        a = atrs_all[r["symbol"]][r["bar_index"]]
        if a > 0:
            ratio[r["symbol"]].append(r["sl_distance_price"] / a)
    year_idx = {}
    for sym in {c[0] for c in cells}:
        bars, times = series[sym]
        d = collections.defaultdict(list)
        for i, t in enumerate(times):
            if 100 <= i < len(bars) - 2 and atrs_all[sym][i] > 0:
                d[str(t.year)].append(i)
        year_idx[sym] = d
    means, tgt_rates = [], []
    for _ in range(reps):
        rs, ntgt, n = [], 0, 0
        for (sym, yr), cnt in cells.items():
            pool = year_idx.get(sym, {}).get(yr) or []
            if not pool:
                continue
            bars, times = series[sym]
            rr = ratio.get(sym) or [1.0]
            for _c in range(cnt):
                i = rng.choice(pool)
                sd = rng.choice(rr) * atrs_all[sym][i]
                if sd <= 0:
                    continue
                d = rng.choice(dirs)
                pr = replay(bars, i, d, stop_dist=sd,
                            policy=ExitPolicy(target_dist=k_target * sd, maxbars=MAXBARS))
                rs.append(winsorize_R(pr.r_gross))
                n += 1
                ntgt += (pr.exit_reason == "target")
        if rs:
            means.append(stat.fmean(rs)); tgt_rates.append(ntgt / n)
    means.sort(); tgt_rates.sort()
    q = lambda a, p: a[max(0, min(len(a) - 1, int(round(p * (len(a) - 1)))))]
    return {"reps": len(means), "mean_r_null": round(stat.fmean(means), 5),
            "null_ci95": [round(q(means, .025), 5), round(q(means, .975), 5)],
            "null_p975": round(q(means, .975), 5),
            "target_rate_null": round(stat.fmean(tgt_rates), 5),
            "analytic_driftless_target_rate": round(1.0 / (1.0 + k_target), 5),
            "analytic_driftless_mean_r": 0.0}


def boot_ci(vals, reps=4000, rng=None):
    rng = rng or random.Random(SEED + 1)
    n = len(vals)
    if n < 2:
        return None
    ms = sorted(stat.fmean([vals[rng.randrange(n)] for _ in range(n)]) for _ in range(reps))
    return [round(ms[int(.025 * reps)], 5), round(ms[int(.975 * reps)], 5)]


def summarise(rows, k, label, null=None):
    if not rows:
        return {"arm": label, "n": 0}
    r = [x["r_gross"] for x in rows]
    n = len(r); m = stat.fmean(r)
    se = stat.stdev(r) / math.sqrt(n) if n > 1 else float("nan")
    reasons = collections.Counter(x["exit_reason"] for x in rows)
    fwd = [x["r_gross"] for x in rows if x["entry_utc"][:4] >= "2025"]
    pre = [x["r_gross"] for x in rows if x["entry_utc"][:4] < "2025"]
    days = sorted({x["entry_utc"][:10] for x in rows})
    byday = collections.defaultdict(list)
    for x in rows:
        byday[x["entry_utc"][:10]].append(x["r_gross"])
    dmeans = [stat.fmean(v) for v in byday.values()]
    span_y = (dt.date.fromisoformat(days[-1]) - dt.date.fromisoformat(days[0])).days / 365.25
    d = {"arm": label, "n": n, "n_symbols": len({x["symbol"] for x in rows}),
         "mean_r": round(m, 5), "sd": round(stat.pstdev(r), 5), "se": round(se, 5),
         "t": round(m / se, 3) if se and not math.isnan(se) else None,
         "ci95_t": [round(m - 1.96 * se, 5), round(m + 1.96 * se, 5)],
         "ci95_boot": boot_ci(r),
         "target_rate": round(reasons.get("target", 0) / n, 5),
         "stop_rate": round(reasons.get("stop", 0) / n, 5),
         "maxbars_rate": round(reasons.get("maxbars", 0) / n, 5),
         "analytic_null_target_rate": round(1.0 / (1.0 + k), 5),
         "n_days": len(days), "first": days[0], "last": days[-1],
         "years_span": round(span_y, 2), "trades_per_month": round(n / (span_y * 12), 3),
         "days_per_month": round(len(days) / (span_y * 12), 3),
         "mean_r_per_day": round(stat.fmean(dmeans), 5),
         "total_r": round(sum(r), 3),
         "fwd_n": len(fwd), "fwd_mean_r": round(stat.fmean(fwd), 5) if fwd else None,
         "pre_n": len(pre), "pre_mean_r": round(stat.fmean(pre), 5) if pre else None,
         "median_hold_h": round(stat.median([x["hold_hours"] for x in rows]), 1),
         "long_frac": round(sum(1 for x in rows if x["direction"] > 0) / n, 4)}
    if null:
        d["null"] = null
        d["excess_over_null"] = round(m - null["mean_r_null"], 5)
        d["beats_null_p975"] = bool(m > null["null_p975"])
    return d


CRYPTO_FAMILY = ["ADAUSD", "AVAUSD", "BTCUSD", "DASHUSD", "DOTUSD", "ETHUSD", "LTCUSD",
                 "XRPUSD", "XTZUSD"]
ENERGY_FAMILY = ["USOIL.cash", "UKOIL.cash", "NATGAS.cash"]


def main():
    t0 = time.time()
    series, atrs_all, res = load_h4()
    ALL = sorted(series)
    print(f"loaded {len(ALL)} H4 series in {time.time()-t0:.0f}s")
    live = {"crypto": [res(s) for s in SL_CRYPTO.ON_SURFACE],
            "energy_agri": [res(s) for s in SL_ENERGY.ON_SURFACE],
            "sub_xvol_pullback": [res(s) for s in SL_SUB.XVOL_ON_SURFACE]}
    K = {"crypto": 4.0, "energy_agri": 4.0, "sub_xvol_pullback": 3.0}

    arms = {
        "crypto": [("A0_LIVE_2sym", [res(s) for s in SL_CRYPTO.ON_SURFACE]),
                   ("A1_plus_ETH", [res(s) for s in ("BTCUSD", "DASHUSD", "ETHUSD")]),
                   ("A2_crypto_family_9", [res(s) for s in CRYPTO_FAMILY]),
                   ("A3_all_archive", ALL),
                   ("A4_noncrypto_only", [s for s in ALL if s not in {res(x) for x in CRYPTO_FAMILY}])],
        "energy_agri": [("B0_LIVE_2sym", [res(s) for s in SL_ENERGY.ON_SURFACE]),
                        ("B1_plus_NATGAS", [res(s) for s in ENERGY_FAMILY]),
                        ("B2_all_archive", ALL),
                        ("B3_nonenergy_only", [s for s in ALL if s not in {res(x) for x in ENERGY_FAMILY}])],
        "sub_xvol_pullback": [("C0_LIVE_13sym", [res(s) for s in SL_SUB.XVOL_ON_SURFACE]),
                              ("C1_all_archive", ALL),
                              ("C2_offsurface_only",
                               [s for s in ALL if s not in {res(x) for x in SL_SUB.XVOL_ON_SURFACE}])],
    }

    out = {"generated": dt.datetime.now(dt.UTC).isoformat(), "bars_archive": BARS,
           "maxbars": MAXBARS, "seed": SEED, "n_series": len(ALL), "series": ALL,
           "targets_R": K, "arms": {}, "rows": {}}

    for sleeve, alist in arms.items():
        fn = RULES[sleeve]
        out["arms"][sleeve] = []
        for label, syms in alist:
            t1 = time.time()
            rows = walk(series, atrs_all, fn, sorted(set(syms) & set(ALL)), sleeve)
            reps = max(60, min(300, 150000 // max(1, len(rows))))
            null = placebo_null(series, atrs_all, rows, K[sleeve], reps=reps) if rows else None
            s = summarise(rows, K[sleeve], label, null)
            s["seconds"] = round(time.time() - t1, 1)
            out["arms"][sleeve].append(s)
            out["rows"][f"{sleeve}::{label}"] = rows
            print(f"  {sleeve:20s} {label:22s} n={s.get('n',0):5d} mean_r={s.get('mean_r')} "
                  f"t={s.get('t')} null={None if not null else null['mean_r_null']} "
                  f"tgt={s.get('target_rate')} vs {s.get('analytic_null_target_rate')} "
                  f"({s['seconds']}s)", flush=True)

    # ---- substrate clause ablations: is the depth-4 conjunction load-bearing? ---------------
    base = dict(SL_SUB.XVOL_CONDS)
    ab = {"D0_full_depth4": base}
    for drop in base:
        ab[f"D1_drop_{drop}"] = {k: v for k, v in base.items() if k != drop}
    out["ablations"] = []
    for label, conds in ab.items():
        t1 = time.time()
        rows = walk(series, atrs_all, make_sub(conds),
                    sorted(set(live["sub_xvol_pullback"]) & set(ALL)), "sub_xvol_pullback")
        s = summarise(rows, 3.0, label,
                      placebo_null(series, atrs_all, rows, 3.0, reps=max(60, min(150, 60000 // max(1, len(rows))))) if rows else None)
        s["conds"] = conds; s["seconds"] = round(time.time() - t1, 1)
        out["ablations"].append(s)
        print(f"  ABLATION {label:22s} n={s.get('n',0):5d} mean_r={s.get('mean_r')} "
              f"t={s.get('t')} null={s.get('null',{}).get('mean_r_null')} ({s['seconds']}s)",
              flush=True)

    json.dump(out, gzip.open(OUT / "LANE8_EXPANSION_V1.json.gz", "wt"), indent=1)
    slim = {k: v for k, v in out.items() if k != "rows"}
    json.dump(slim, open(OUT / "LANE8_EXPANSION_V1.json", "w"), indent=1)
    print(f"total {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
