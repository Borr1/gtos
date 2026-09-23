"""WAVE 1 — session_dow_microstructure
=====================================
Deep time-conditional structure on H4 MT5 bars (up to 11yr, 2015-2026).

THESIS: For each (symbol or asset_class) x session-hour-bucket x day-of-week,
measure directional drift and breakout edge with TIGHT stops (default 0.5*atr14).
The metals-NY-long lead was real; expand it systematically and find which
(symbol x time) cells are FORWARD-POSITIVE and POSITIVE ACROSS MOST YEARS.

DISCIPLINE (hard rules from the brief):
  * Fills ONLY via the tested geometry_lib.simulate (no hand-rolled stop/target/sign).
  * R-unit = stop_dist = 0.5*atr14 (geometry default).
  * Cost from ULTIMATE_REAL_COST_MAP.json per asset class.
  * TRAIN <= 2024 / FORWARD 2025-2026. ALSO report per-year across all years.
  * A "bar" (real edge) = FORWARD-POSITIVE AND positive in a MAJORITY of years.
  * Honest about multiple testing: require cross-year persistence, negative controls.
  * No acceptance theater: the script reports the numbers and the verdict either way.

The broker timestamps are EET (GMT+2/+3, standard FTMO). H4 grid = 6 bars/day at
broker hours {0,4,8,12,16,20}. The hour-16 bar (NY session) carries the most
volume/range for XAUUSD, consistent with the known metals-NY lead.
"""
from __future__ import annotations
import sys, os, csv, json, math, datetime
from collections import defaultdict

REPO = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
HERE = os.path.join(REPO, "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10")
sys.path.insert(0, REPO)
sys.path.insert(0, HERE)

from geometry_lib import Bar, atr14, simulate
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

DATA_OLD = os.path.join(REPO, "data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022")
DATA_NEW = os.path.join(REPO, "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026")
COST_MAP = json.load(open(os.path.join(HERE, "ULTIMATE_REAL_COST_MAP.json")))

# Symbols present in BOTH ranges -> longest series. Plus we also accept new-only.
def symbols_available():
    old = {f[:-7] for f in os.listdir(DATA_OLD) if f.endswith("_H4.csv")}
    new = {f[:-7] for f in os.listdir(DATA_NEW) if f.endswith("_H4.csv")}
    return sorted(old | new), old, new

def load_series(sym):
    """Concatenate + dedupe by time across both ranges.
    Returns (dates, bars) where dates[i] is a datetime and bars[i] is a Bar
    (bars is a plain list[Bar] so it can be passed straight to atr14/simulate)."""
    rows = {}
    for d in (DATA_OLD, DATA_NEW):
        p = os.path.join(d, sym + "_H4.csv")
        if not os.path.exists(p):
            continue
        with open(p) as f:
            for r in csv.DictReader(f):
                t = r["time"]
                # dedupe by time; prefer later file (NEW) on collision is fine, identical anyway
                rows[t] = (
                    float(r["open"]), float(r["high"]),
                    float(r["low"]), float(r["close"]), float(r["volume"]),
                )
    dates, bars = [], []
    for t in sorted(rows):
        dt = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
        o, h, l, c, v = rows[t]
        dates.append(dt)
        bars.append(Bar(o, h, l, c, v))
    return dates, bars

def cost_for(sym):
    ac = ASSET_CLASS_BY_SYMBOL.get(sym, "fx")
    return COST_MAP.get(ac, COST_MAP["_global_median"]), ac

# ----------------------------------------------------------------------------
# Edge measurement.
# For a given entry bar i (decided at its close), we test two mechanisms:
#   DRIFT (continuation directional): enter direction sign of the just-closed bar
#         body? No -- to test pure time-conditional DRIFT we enter a FIXED direction
#         (long or short) at the close of the session bucket bar and hold with a
#         trailing exit. We sweep both directions and both exit styles, but report
#         honestly with cross-year persistence as the gate.
#   BREAKOUT: enter in the direction of the bar's close-vs-open (momentum of the
#         session bar) -- "the session pushed this way, ride it".
#
# Geometry: stop = 0.5*atr14 (R unit). Exits tested:
#   - fixed target 1.0R, 1.5R, 2.0R
#   - trail: arm at 1.0R, gap 1.0R  (=trail_arm=1*stop, trail_gap=1*stop)
# We keep the exit-style sweep SMALL and fixed up-front to limit multiple testing,
# and the headline gate is cross-year persistence, not best-of-many.
# ----------------------------------------------------------------------------

EXIT_CONFIGS = [
    ("tp1.0R",  dict(target_dist_mult=1.0)),
    ("tp1.5R",  dict(target_dist_mult=1.5)),
    ("tp2.0R",  dict(target_dist_mult=2.0)),
    ("trail1_1", dict(trail_arm_mult=1.0, trail_gap_mult=1.0)),
]

STOP_MULT = 0.5  # 0.5*atr14 (geometry default)

def run_trade(bars, i, direction, cost, exit_cfg):
    atr = atr14(bars, i)
    if atr <= 0:
        return None
    stop = STOP_MULT * atr
    if stop <= 0:
        return None
    kw = dict(stop_dist=stop, cost=cost, maxbars=12)  # max 2 trading days hold on H4
    if "target_dist_mult" in exit_cfg:
        kw["target_dist"] = exit_cfg["target_dist_mult"] * stop
    else:
        kw["trail_arm"] = exit_cfg["trail_arm_mult"] * stop
        kw["trail_gap"] = exit_cfg["trail_gap_mult"] * stop
    return simulate(bars, i, direction, **kw)


def analyze(symbols):
    # cell key -> per-(year) list of R, plus train/forward buckets, per exit cfg & direction & mode
    # We organize results as: results[(scope, hour, dow, mode, dirlabel, exitname)] = {year: [R,...]}
    results = defaultdict(lambda: defaultdict(list))

    series_cache = {}
    for sym in symbols:
        dates, bars = load_series(sym)
        if len(bars) < 200:
            continue
        series_cache[sym] = (dates, bars)
        cost, ac = cost_for(sym)

        for i in range(15, len(bars) - 13):
            dt = dates[i]
            b = bars[i]
            yr = dt.year
            hour = dt.hour
            dow = dt.weekday()  # 0=Mon..4=Fri (Sat/Sun rare)
            if dow > 4:
                continue
            body = b.c - b.o
            if body == 0:
                breakout_dir = 0
            else:
                breakout_dir = 1 if body > 0 else -1

            for exitname, ecfg in EXIT_CONFIGS:
                # DRIFT long / DRIFT short (fixed direction conditional on time cell)
                for dirlabel, direction in (("LONG", 1), ("SHORT", -1)):
                    r = run_trade(bars, i, direction, cost, ecfg)
                    if r is None:
                        continue
                    for scope in (sym, "AC:" + ac):
                        key = (scope, hour, dow, "DRIFT", dirlabel, exitname)
                        results[key][yr].append(r)
                # BREAKOUT: ride session bar momentum
                if breakout_dir != 0:
                    r = run_trade(bars, i, breakout_dir, cost, ecfg)
                    if r is not None:
                        for scope in (sym, "AC:" + ac):
                            key = (scope, hour, dow, "BREAKOUT", "MOM", exitname)
                            results[key][yr].append(r)
    return results, series_cache


def summarize_cell(year_map):
    """Return dict with train/forward means, per-year means, counts, persistence."""
    all_years = sorted(year_map)
    per_year = {}
    for y in all_years:
        rs = year_map[y]
        per_year[y] = (sum(rs) / len(rs), len(rs))
    train_R = [r for y in all_years if y <= 2024 for r in year_map[y]]
    fwd_R   = [r for y in all_years if y >= 2025 for r in year_map[y]]
    train_mean = sum(train_R) / len(train_R) if train_R else None
    fwd_mean   = sum(fwd_R) / len(fwd_R) if fwd_R else None
    # persistence: fraction of years with positive mean (require >=20 trades that yr)
    qual_years = [y for y in all_years if per_year[y][1] >= 20]
    pos_years = [y for y in qual_years if per_year[y][0] > 0]
    n_total = sum(len(year_map[y]) for y in all_years)
    return {
        "per_year": per_year,
        "train_mean": train_mean, "train_n": len(train_R),
        "fwd_mean": fwd_mean, "fwd_n": len(fwd_R),
        "qual_years": qual_years,
        "n_pos_years": len(pos_years),
        "n_qual_years": len(qual_years),
        "n_total": n_total,
    }


HOURLBL = {0: "Asia(00)", 4: "Asia/EU(04)", 8: "EUopen(08)", 12: "EUmid(12)",
           16: "NY(16)", 20: "NYlate(20)"}
DOWLBL = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri"}


def main():
    syms, old, new = symbols_available()
    # Focus on the previous live surface + metals/oil/index/fx majors that have data.
    # Use ALL symbols that have files; asset-class scope aggregates anyway.
    print(f"symbols available: {len(syms)}")
    results, series = analyze(syms)
    print(f"data series loaded: {len(series)}  cells: {len(results)}")

    summaries = {}
    for key, ym in results.items():
        s = summarize_cell(ym)
        summaries[key] = s

    # ---- GATING -----------------------------------------------------------
    # A real edge ("bar") must be:
    #   1. forward-positive (fwd_mean > 0) with enough forward trades (>=30)
    #   2. positive in a MAJORITY of qualifying years (n_pos_years/n_qual_years > 0.5)
    #      with at least 4 qualifying years (cross-year persistence, not luck)
    #   3. train-positive too (not a forward-only fluke)
    #   4. meaningful per-trade edge after cost (fwd_mean >= 0.02R) and big enough sample
    MIN_FWD_N = 30
    MIN_QUAL_YEARS = 4
    MIN_FWD_R = 0.02

    robust = []
    for key, s in summaries.items():
        if s["fwd_mean"] is None or s["train_mean"] is None:
            continue
        if s["fwd_n"] < MIN_FWD_N:
            continue
        if s["n_qual_years"] < MIN_QUAL_YEARS:
            continue
        frac_pos = s["n_pos_years"] / s["n_qual_years"]
        if (s["fwd_mean"] > MIN_FWD_R and s["train_mean"] > 0
                and frac_pos > 0.5):
            robust.append((key, s, frac_pos))

    # Rank robust cells by a conservative score: min(train,fwd) * sqrt(persistence)
    def score(item):
        key, s, frac = item
        return min(s["train_mean"], s["fwd_mean"]) * frac
    robust.sort(key=score, reverse=True)

    print("\n" + "=" * 100)
    print("ROBUST CELLS (forward+ AND train+ AND positive in majority of years, >=4 qual yrs, fwd_n>=30)")
    print("=" * 100)
    print(f"{'scope':14s} {'hour':12s} {'dow':4s} {'mode':9s} {'dir':5s} {'exit':9s} "
          f"{'train_R':>8s} {'fwd_R':>8s} {'fwd_n':>6s} {'posYr':>7s}")
    for key, s, frac in robust[:60]:
        scope, hour, dow, mode, dirlabel, exitname = key
        print(f"{scope:14s} {HOURLBL[hour]:12s} {DOWLBL[dow]:4s} {mode:9s} {dirlabel:5s} {exitname:9s} "
              f"{s['train_mean']:8.3f} {s['fwd_mean']:8.3f} {s['fwd_n']:6d} "
              f"{s['n_pos_years']:d}/{s['n_qual_years']:d}")
    print(f"\nTOTAL robust cells passing all gates: {len(robust)}")

    # ---- NEGATIVE CONTROL -------------------------------------------------
    # How many cells would pass the SAME gates by chance? Compare to a shuffled
    # (random-direction) baseline AND report the count of all tested cells.
    n_tested = sum(1 for s in summaries.values()
                   if s["fwd_mean"] is not None and s["train_mean"] is not None
                   and s["fwd_n"] >= MIN_FWD_N and s["n_qual_years"] >= MIN_QUAL_YEARS)
    print(f"\nNEGATIVE-CONTROL CONTEXT: {n_tested} cells met sample-size gates; "
          f"{len(robust)} passed the edge+persistence gates "
          f"({100.0*len(robust)/max(1,n_tested):.1f}%).")

    # ---- ASSET-CLASS HEADLINE TABLE (the time-routing table) --------------
    print("\n" + "=" * 100)
    print("ASSET-CLASS TIME-ROUTING TABLE (robust AC-scope cells only)")
    print("=" * 100)
    ac_robust = [r for r in robust if r[0][0].startswith("AC:")]
    for key, s, frac in ac_robust:
        scope, hour, dow, mode, dirlabel, exitname = key
        py = "  ".join(f"{y}:{s['per_year'][y][0]:+.2f}" for y in sorted(s['per_year']) if s['per_year'][y][1] >= 20)
        print(f"{scope:10s} {HOURLBL[hour]:12s} {DOWLBL[dow]:4s} {mode:9s} {dirlabel:5s} {exitname:9s} "
              f"train{s['train_mean']:+.3f} fwd{s['fwd_mean']:+.3f} n{s['fwd_n']} pos{s['n_pos_years']}/{s['n_qual_years']}")
        print(f"             per-year: {py}")

    # ---- HARD NEGATIVE CONTROL: random-direction null ---------------------
    # Re-run the SAME pipeline but assign each trade a random (seeded) direction,
    # independent of time cell. Count how many "robust" cells the gates produce
    # under the null. If the real count is not far above the null, the survivors
    # are multiple-testing artifacts. This is the honesty check.
    import random
    def analyze_null(symbols, seed):
        rng = random.Random(seed)
        res = defaultdict(lambda: defaultdict(list))
        for sym in symbols:
            cached = series.get(sym)
            if cached is None:
                continue
            dates, bars = cached
            cost, ac = cost_for(sym)
            for i in range(15, len(bars) - 13):
                dt = dates[i]
                if dt.weekday() > 4:
                    continue
                hour, dow, yr = dt.hour, dt.weekday(), dt.year
                for exitname, ecfg in EXIT_CONFIGS:
                    d = 1 if rng.random() < 0.5 else -1
                    r = run_trade(bars, i, d, cost, ecfg)
                    if r is None:
                        continue
                    for scope in (sym, "AC:" + ac):
                        res[(scope, hour, dow, "NULL", "RND", exitname)][yr].append(r)
        return res

    null_counts = []
    for seed in (1, 2, 3):
        nres = analyze_null(syms, seed)
        cnt = 0
        for key, ym in nres.items():
            s = summarize_cell(ym)
            if s["fwd_mean"] is None or s["train_mean"] is None:
                continue
            if s["fwd_n"] < MIN_FWD_N or s["n_qual_years"] < MIN_QUAL_YEARS:
                continue
            frac = s["n_pos_years"] / s["n_qual_years"]
            if s["fwd_mean"] > MIN_FWD_R and s["train_mean"] > 0 and frac > 0.5:
                cnt += 1
        null_counts.append(cnt)
    null_mean = sum(null_counts) / len(null_counts)
    print("\n" + "=" * 100)
    print("HARD NEGATIVE CONTROL (random-direction null, same gates)")
    print("=" * 100)
    print(f"null robust counts per seed: {null_counts}  mean={null_mean:.1f}")
    print(f"real robust count: {len(robust)}   ->  real/null ratio = "
          f"{len(robust)/max(0.5,null_mean):.1f}x")
    print("NOTE: same DRIFT pipeline tests LONG and SHORT, so a random-sign null"
          " is the correct chance baseline for 'a direction worked here'.")

    # ---- ROUTING PORTFOLIO: combine AC-scope robust cells, OOS by year ----
    # Build the routing table from TRAIN-ONLY selection (<=2024), then measure
    # the FORWARD (2025-2026) per-trade R of the combined book. This avoids the
    # look-ahead of selecting on full-sample fwd_mean.
    print("\n" + "=" * 100)
    print("OUT-OF-SAMPLE ROUTING BOOK: select AC cells on TRAIN<=2024 only, trade them FORWARD")
    print("=" * 100)
    # Re-select using ONLY train info: train_mean>MIN_FWD_R, positive in majority of TRAIN years.
    train_selected = []
    for key, ym in results.items():
        scope = key[0]
        if not scope.startswith("AC:"):
            continue
        train_years = {y: ym[y] for y in ym if y <= 2024}
        if not train_years:
            continue
        ty = sorted(train_years)
        per = {y: (sum(train_years[y]) / len(train_years[y]), len(train_years[y])) for y in ty}
        qual = [y for y in ty if per[y][1] >= 20]
        if len(qual) < 4:
            continue
        pos = [y for y in qual if per[y][0] > 0]
        train_R = [r for y in ty for r in train_years[y]]
        tmean = sum(train_R) / len(train_R)
        if tmean > MIN_FWD_R and len(pos) / len(qual) > 0.6:
            train_selected.append((key, tmean, len(pos), len(qual)))

    # Now measure forward performance of the selected book (equal-weight per trade).
    fwd_all = []
    fwd_by_year = defaultdict(list)
    for key, tmean, npos, nq in train_selected:
        ym = results[key]
        for y in ym:
            if y >= 2025:
                fwd_all.extend(ym[y])
                fwd_by_year[y].extend(ym[y])
    print(f"AC cells selected on TRAIN-ONLY criteria: {len(train_selected)}")
    for key, tmean, npos, nq in sorted(train_selected, key=lambda x: -x[1]):
        scope, hour, dow, mode, dirlabel, exitname = key
        print(f"  {scope:10s} {HOURLBL[hour]:12s} {DOWLBL[dow]:4s} {mode:9s} {dirlabel:5s} "
              f"{exitname:9s} train{tmean:+.3f} trainPosYr{npos}/{nq}")
    if fwd_all:
        fwd_mean = sum(fwd_all) / len(fwd_all)
        print(f"\nFORWARD (2025-2026) book per-trade R = {fwd_mean:+.4f}  over {len(fwd_all)} trades")
        for y in sorted(fwd_by_year):
            rs = fwd_by_year[y]
            print(f"  {y}: {sum(rs)/len(rs):+.4f}R  n={len(rs)}")
    else:
        fwd_mean = None
        print("no forward trades in selected book")

    # Persist machine-readable output
    out = {
        "gates": dict(MIN_FWD_N=MIN_FWD_N, MIN_QUAL_YEARS=MIN_QUAL_YEARS, MIN_FWD_R=MIN_FWD_R,
                      stop="0.5*atr14", maxbars=12, exit_configs=[e[0] for e in EXIT_CONFIGS]),
        "n_cells_tested_with_samplesize": n_tested,
        "n_robust": len(robust),
        "null_robust_counts": null_counts,
        "null_robust_mean": null_mean,
        "real_to_null_ratio": len(robust) / max(0.5, null_mean),
        "oos_train_selected_book": [
            {"scope": k[0], "hour": k[1], "dow": k[2], "mode": k[3], "dir": k[4],
             "exit": k[5], "train_mean": tm, "train_pos_years": npos, "train_qual_years": nq}
            for (k, tm, npos, nq) in train_selected
        ],
        "oos_forward_book_per_trade_R": fwd_mean,
        "oos_forward_book_n": len(fwd_all),
        "oos_forward_by_year": {str(y): {"mean": sum(rs)/len(rs), "n": len(rs)}
                                for y, rs in fwd_by_year.items()},
        "robust": [
            {
                "scope": k[0], "hour": k[1], "dow": k[2], "mode": k[3], "dir": k[4], "exit": k[5],
                "train_mean": s["train_mean"], "train_n": s["train_n"],
                "fwd_mean": s["fwd_mean"], "fwd_n": s["fwd_n"],
                "frac_pos_years": frac, "n_pos_years": s["n_pos_years"],
                "n_qual_years": s["n_qual_years"],
                "per_year": {str(y): {"mean": v[0], "n": v[1]} for y, v in s["per_year"].items()},
            }
            for k, s, frac in robust
        ],
    }
    outp = os.path.join(HERE, "wave1_session_dow_microstructure_RESULT.json")
    json.dump(out, open(outp, "w"), indent=1)
    print(f"\nwrote {outp}")
    return out


if __name__ == "__main__":
    main()
