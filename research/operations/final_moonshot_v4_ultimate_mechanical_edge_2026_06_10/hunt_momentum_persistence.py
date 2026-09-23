"""Hunt: momentum / persistence entry edge (opposite/uncorrelated to reversion).

Two families, both on H4 2022-2026, both using the TESTED geometry_lib for fills:
  TS  = time-series momentum: a symbol that trended over a lookback keeps going.
  XS  = cross-sectional momentum: rank all symbols by recent return each bar,
        long the top, short the bottom.

Discipline:
  TRAIN  2022-01..2024-12
  FORWARD 2025-01..2026-xx (out of sample)
  Report per-trade R, win%, per-year, by asset_class, long vs short separately.
  Bar = POSITIVE & STABLE IN FORWARD. No rejection theater; quantify honestly.

Fills: geometry_lib.simulate (explicit two-sided, pessimistic ties). R-unit = stop_dist.
Geometry default: stop_dist = 0.5*atr14, target_dist = 1.0..2.0*atr14, OR trail.
Cost: real per-asset from ULTIMATE_REAL_COST_MAP.json (crypto/agri fall back to global median).
"""
import sys, json, csv, math, collections
from pathlib import Path
from datetime import datetime

ROUTE = Path("/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10")
REPO = Path("/Users/borr/Documents/gtos/repo/ai-trading-agent")
DATA = REPO / "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(ROUTE))
from geometry_lib import Bar, atr14, simulate
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

COST_MAP = json.loads((ROUTE / "ULTIMATE_REAL_COST_MAP.json").read_text())
GLOBAL_COST = COST_MAP["_global_median"]

def cost_for(sym):
    ac = ASSET_CLASS_BY_SYMBOL.get(sym, "fx")
    # cost map keys: fx, jpy_fx, index, metals, energy ; crypto/agri -> fallbacks
    if ac in COST_MAP:
        return COST_MAP[ac]
    if ac == "crypto":
        return 0.095     # ~ given in brief
    return GLOBAL_COST    # agri / unknown

TRAIN_END = datetime(2025, 1, 1)

def load(sym):
    p = DATA / f"{sym}_H4.csv"
    if not p.exists():
        return None
    bars, ts = [], []
    with open(p) as f:
        for row in csv.DictReader(f):
            try:
                o = float(row["open"]); h = float(row["high"]); l = float(row["low"]); c = float(row["close"])
                v = float(row.get("volume", 0) or 0)
            except (ValueError, KeyError):
                continue
            bars.append(Bar(o, h, l, c, v))
            ts.append(datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S"))
    return bars, ts

# ---- load all symbols present in data dir (asset-class mapped) -------------
SYMS = [s for s in ASSET_CLASS_BY_SYMBOL if (DATA / f"{s}_H4.csv").exists()]
SERIES = {}
for s in SYMS:
    r = load(s)
    if r and len(r[0]) > 200:
        SERIES[s] = r
SYMS = list(SERIES.keys())
print(f"loaded {len(SYMS)} symbols", file=sys.stderr)

def ret(bars, i, lb):
    """log return over lb bars ending at i."""
    if i - lb < 0 or bars[i - lb].c <= 0 or bars[i].c <= 0:
        return None
    return math.log(bars[i].c / bars[i - lb].c)


class Acc:
    __slots__ = ("rs",)
    def __init__(self): self.rs = []
    def add(self, r): self.rs.append(r)
    def stats(self):
        n = len(self.rs)
        if n == 0:
            return {"n": 0, "per_trade_R": 0.0, "win": 0.0, "total_R": 0.0}
        wins = sum(1 for x in self.rs if x > 0)
        return {"n": n, "per_trade_R": round(sum(self.rs) / n, 4),
                "win": round(wins / n, 4), "total_R": round(sum(self.rs), 1)}


def split_report(records):
    """records: list of (year, asset_class, direction, R). Build the report."""
    def bucket():
        return collections.defaultdict(Acc)
    out = {}
    for phase in ("TRAIN", "FORWARD"):
        out[phase] = {"all": Acc(), "long": Acc(), "short": Acc(),
                      "per_year": bucket(), "by_class": bucket(),
                      "by_class_dir": bucket()}
    for (year, ac, d, r) in records:
        phase = "TRAIN" if year < 2025 else "FORWARD"
        b = out[phase]
        b["all"].add(r)
        (b["long"] if d > 0 else b["short"]).add(r)
        b["per_year"][year].add(r)
        b["by_class"][ac].add(r)
        b["by_class_dir"][(ac, "long" if d > 0 else "short")].add(r)
    rep = {}
    for phase in ("TRAIN", "FORWARD"):
        b = out[phase]
        rep[phase] = {
            "all": b["all"].stats(),
            "long": b["long"].stats(),
            "short": b["short"].stats(),
            "per_year": {str(y): b["per_year"][y].stats() for y in sorted(b["per_year"])},
            "by_class": {ac: b["by_class"][ac].stats() for ac in sorted(b["by_class"])},
            "by_class_dir": {f"{ac}|{dd}": b["by_class_dir"][(ac, dd)].stats()
                              for (ac, dd) in sorted(b["by_class_dir"])},
        }
    return rep


# ===========================================================================
# FAMILY 1: TIME-SERIES MOMENTUM
#   Entry rule per symbol per bar i:
#     long  if ret(lb) > +thr   (in vol units)   -> momentum continuation
#     short if ret(lb) < -thr
#   gating optional: require recent acceleration (last leg same sign).
# ===========================================================================

def run_ts(lb, thr_vol, geom, accel=False, breakout=False, cooldown=1):
    """thr_vol: threshold on |ret|/ (atr-based vol over lb) ; geom = config dict."""
    records = []
    for sym in SYMS:
        bars, ts = SERIES[sym]
        ac = ASSET_CLASS_BY_SYMBOL[sym]
        cost = cost_for(sym)
        last_entry = -10 ** 9
        n = len(bars)
        for i in range(30, n - 2):
            a = atr14(bars, i)
            if a <= 0:
                continue
            r = ret(bars, i, lb)
            if r is None:
                continue
            # normalize momentum by per-bar vol * sqrt(lb)
            denom = (a / bars[i].c) * math.sqrt(lb) if bars[i].c > 0 else 0
            if denom <= 0:
                continue
            z = r / denom
            direction = 0
            if z > thr_vol:
                direction = 1
            elif z < -thr_vol:
                direction = -1
            if direction == 0:
                continue
            if breakout:
                # require close beyond prior lb-window extreme (Donchian style)
                hi = max(b.h for b in bars[i - lb:i])
                lo = min(b.l for b in bars[i - lb:i])
                if direction > 0 and bars[i].c < hi:
                    continue
                if direction < 0 and bars[i].c > lo:
                    continue
            if accel:
                # last leg (half lookback) must share sign
                r2 = ret(bars, i, max(2, lb // 2))
                if r2 is None or (r2 > 0) != (direction > 0):
                    continue
            if i - last_entry < cooldown:
                continue
            last_entry = i
            stop = geom["stop_mult"] * a
            R = simulate(bars, i, direction, stop_dist=stop,
                         target_dist=geom.get("target_mult", 0) * a if geom.get("target_mult") else None,
                         trail_arm=geom.get("trail_arm_mult", 0) * stop if geom.get("trail_arm_mult") else None,
                         trail_gap=geom.get("trail_gap_mult", 0) * stop if geom.get("trail_gap_mult") else None,
                         maxbars=geom.get("maxbars", 80), cost=cost)
            records.append((ts[i].year, ac, direction, R))
    return records


# ===========================================================================
# FAMILY 2: CROSS-SECTIONAL MOMENTUM
#   At each bar (aligned by timestamp), rank symbols by recent return over lb.
#   Long the top `k`, short the bottom `k`. Enter one trade per selected symbol.
#   To avoid overlap-heavy churn, only re-rank every `rebal` bars.
# ===========================================================================

def build_time_index():
    """Map each symbol's bar index to a global timestamp; build aligned grid."""
    # union of all timestamps, sorted; per symbol map ts->idx
    allts = set()
    sym_ts_idx = {}
    for sym in SYMS:
        bars, ts = SERIES[sym]
        d = {t: i for i, t in enumerate(ts)}
        sym_ts_idx[sym] = d
        allts.update(ts)
    grid = sorted(allts)
    return grid, sym_ts_idx

def run_xs(lb, k, geom, rebal=6, min_syms=20):
    grid, sym_ts_idx = build_time_index()
    records = []
    gi = 0
    while gi < len(grid):
        t = grid[gi]
        scored = []
        for sym in SYMS:
            idx = sym_ts_idx[sym].get(t)
            if idx is None:
                continue
            bars, ts = SERIES[sym]
            if idx < lb + 30 or idx >= len(bars) - 2:
                continue
            a = atr14(bars, idx)
            if a <= 0:
                continue
            r = ret(bars, idx, lb)
            if r is None:
                continue
            denom = (a / bars[idx].c) * math.sqrt(lb) if bars[idx].c > 0 else 0
            if denom <= 0:
                continue
            scored.append((r / denom, sym, idx))
        if len(scored) >= min_syms:
            scored.sort()
            longs = scored[-k:]      # highest momentum
            shorts = scored[:k]      # lowest (most negative) momentum
            for (_, sym, idx), direction in (
                    [(x, 1) for x in longs] + [(x, -1) for x in shorts]):
                bars, ts = SERIES[sym]
                ac = ASSET_CLASS_BY_SYMBOL[sym]
                cost = cost_for(sym)
                a = atr14(bars, idx)
                stop = geom["stop_mult"] * a
                R = simulate(bars, idx, direction, stop_dist=stop,
                             target_dist=geom.get("target_mult", 0) * a if geom.get("target_mult") else None,
                             trail_arm=geom.get("trail_arm_mult", 0) * stop if geom.get("trail_arm_mult") else None,
                             trail_gap=geom.get("trail_gap_mult", 0) * stop if geom.get("trail_gap_mult") else None,
                             maxbars=geom.get("maxbars", 80), cost=cost)
                records.append((ts[idx].year, ac, direction, R))
        gi += rebal
    return records


# geometry configs to sweep
GEOMS = {
    "tgt1.0": {"stop_mult": 0.5, "target_mult": 1.0, "maxbars": 80},
    "tgt1.5": {"stop_mult": 0.5, "target_mult": 1.5, "maxbars": 80},
    "tgt2.0": {"stop_mult": 0.5, "target_mult": 2.0, "maxbars": 80},
    "trail2_1": {"stop_mult": 0.5, "trail_arm_mult": 2.0, "trail_gap_mult": 1.0, "maxbars": 80},
}


def fwd_key(rep):
    f = rep["FORWARD"]["all"]
    return (f["per_trade_R"], f["n"])


def main():
    results = {}

    # ---- TS sweep ----
    ts_configs = []
    for lb in (3, 6, 12, 24):
        for thr in (0.5, 1.0, 1.5):
            for accel in (False, True):
                for breakout in (False, True):
                    ts_configs.append((lb, thr, accel, breakout))
    print(f"TS configs: {len(ts_configs)} x {len(GEOMS)} geoms", file=sys.stderr)

    ts_results = []
    for (lb, thr, accel, breakout) in ts_configs:
        for gname, geom in GEOMS.items():
            recs = run_ts(lb, thr, geom, accel=accel, breakout=breakout, cooldown=lb)
            if not recs:
                continue
            rep = split_report(recs)
            tag = f"TS|lb{lb}|thr{thr}|acc{int(accel)}|brk{int(breakout)}|{gname}"
            ts_results.append((tag, rep))
        print(f"  done lb{lb} thr{thr} acc{int(accel)} brk{int(breakout)}", file=sys.stderr)

    # ---- XS sweep ----
    xs_results = []
    for lb in (6, 12, 24):
        for k in (3, 5, 8):
            for gname, geom in GEOMS.items():
                recs = run_xs(lb, k, geom, rebal=max(3, lb // 2))
                if not recs:
                    continue
                rep = split_report(recs)
                tag = f"XS|lb{lb}|k{k}|{gname}"
                xs_results.append((tag, rep))
        print(f"  XS done lb{lb}", file=sys.stderr)

    # rank by forward per-trade R (require min sample in forward)
    def eligible(rep):
        return rep["FORWARD"]["all"]["n"] >= 150

    allr = ts_results + xs_results
    ranked = sorted([(t, r) for (t, r) in allr if eligible(r)],
                    key=lambda x: fwd_key(x[1]), reverse=True)

    results["n_configs"] = len(allr)
    results["top10_forward"] = [
        {"config": t,
         "forward": r["FORWARD"]["all"],
         "forward_long": r["FORWARD"]["long"],
         "forward_short": r["FORWARD"]["short"],
         "train": r["TRAIN"]["all"]}
        for (t, r) in ranked[:10]
    ]
    # full report for the best
    if ranked:
        best_tag, best_rep = ranked[0]
        results["best"] = {"config": best_tag, "report": best_rep}

    # ---- FOCUSED PASS: by-class behavior + class-filtered momentum ----------
    # The raw sweep showed momentum lives in trending classes (crypto/energy/
    # metals/agri) and is destroyed by reverting classes (fx/jpy_fx/index).
    # Re-run the strongest TS form per-class to confirm TRAIN->FORWARD sign
    # stability, then build a class-filtered "trending only" portfolio.
    def class_split_report(recs):
        # recs: (year, ac, dir, R). report TRAIN/FORWARD per class.
        per = collections.defaultdict(lambda: {"TRAIN": Acc(), "FORWARD": Acc(),
                                               "TRAIN_long": Acc(), "FORWARD_long": Acc(),
                                               "TRAIN_short": Acc(), "FORWARD_short": Acc()})
        for (year, ac, d, r) in recs:
            ph = "TRAIN" if year < 2025 else "FORWARD"
            per[ac][ph].add(r)
            per[ac][f"{ph}_{'long' if d>0 else 'short'}"].add(r)
        return {ac: {k: v.stats() for k, v in d.items()} for ac, d in per.items()}

    # winner geometry/params from sweep: lb6 thr1.5 breakout trail2_1
    best_geom = GEOMS["trail2_1"]
    recs_focus = run_ts(6, 1.5, best_geom, accel=False, breakout=True, cooldown=6)
    results["per_class_TRAIN_FORWARD"] = class_split_report(recs_focus)

    # class-filtered portfolio: keep only classes positive in BOTH train & fwd
    cs = results["per_class_TRAIN_FORWARD"]
    trending = [ac for ac, d in cs.items()
                if d["TRAIN"]["per_trade_R"] > 0 and d["FORWARD"]["per_trade_R"] > 0
                and d["TRAIN"]["n"] >= 30 and d["FORWARD"]["n"] >= 30]
    results["trending_classes_selected"] = trending
    filt = [(y, ac, d, r) for (y, ac, d, r) in recs_focus if ac in trending]
    results["trending_portfolio"] = split_report(filt)

    # ---- CRYPTO robustness grid: edge is threshold-gated; confirm thr1.5 ----
    crypto_syms = [s for s in SYMS if ASSET_CLASS_BY_SYMBOL[s] == "crypto"]
    crypto_grid = []
    for lb in (6, 12, 24):
        for thr in (0.5, 1.0, 1.5):
            for brk in (True, False):
                for gname, geom in GEOMS.items():
                    recs = []
                    for sym in crypto_syms:
                        bars, ts = SERIES[sym]
                        ac2 = ASSET_CLASS_BY_SYMBOL[sym]
                        cost = cost_for(sym)
                        last = -10 ** 9
                        for i in range(30, len(bars) - 2):
                            a = atr14(bars, i)
                            if a <= 0:
                                continue
                            r = ret(bars, i, lb)
                            if r is None:
                                continue
                            denom = (a / bars[i].c) * math.sqrt(lb) if bars[i].c > 0 else 0
                            if denom <= 0:
                                continue
                            z = r / denom
                            d = 1 if z > thr else (-1 if z < -thr else 0)
                            if d == 0:
                                continue
                            if brk:
                                hi = max(b.h for b in bars[i - lb:i])
                                lo = min(b.l for b in bars[i - lb:i])
                                if (d > 0 and bars[i].c < hi) or (d < 0 and bars[i].c > lo):
                                    continue
                            if i - last < lb:
                                continue
                            last = i
                            st = geom["stop_mult"] * a
                            R = simulate(bars, i, d, stop_dist=st,
                                         target_dist=geom.get("target_mult", 0) * a if geom.get("target_mult") else None,
                                         trail_arm=geom.get("trail_arm_mult", 0) * st if geom.get("trail_arm_mult") else None,
                                         trail_gap=geom.get("trail_gap_mult", 0) * st if geom.get("trail_gap_mult") else None,
                                         maxbars=80, cost=cost)
                            recs.append((ts[i].year, ac2, d, R))
                    if not recs:
                        continue
                    rep = split_report(recs)
                    crypto_grid.append({
                        "config": f"crypto|lb{lb}|thr{thr}|brk{int(brk)}|{gname}",
                        "train": rep["TRAIN"]["all"],
                        "forward": rep["FORWARD"]["all"],
                        "fwd_2025": rep["FORWARD"]["per_year"].get("2025", {}),
                        "fwd_2026": rep["FORWARD"]["per_year"].get("2026", {}),
                        "stable": (rep["TRAIN"]["all"]["per_trade_R"] > 0
                                   and rep["FORWARD"]["all"]["per_trade_R"] > 0
                                   and rep["FORWARD"]["per_year"].get("2025", {}).get("per_trade_R", -1) > 0
                                   and rep["FORWARD"]["per_year"].get("2026", {}).get("per_trade_R", -1) > 0),
                    })
    results["crypto_robustness_grid"] = crypto_grid

    (ROUTE / "HUNT_MOMENTUM_PERSISTENCE_RESULT.json").write_text(
        json.dumps(results, indent=1, default=str))
    print(json.dumps({"n_configs": results["n_configs"],
                      "top10": [(d["config"], d["forward"]["per_trade_R"],
                                 d["forward"]["n"], d["train"]["per_trade_R"])
                                for d in results["top10_forward"]]}, indent=1))
    print("\nPER-CLASS TRAIN->FORWARD (winner TS form):")
    for ac, d in sorted(results["per_class_TRAIN_FORWARD"].items()):
        print(f"  {ac:8s} TRAIN R={d['TRAIN']['per_trade_R']:+.3f} n={d['TRAIN']['n']:4d}"
              f" | FWD R={d['FORWARD']['per_trade_R']:+.3f} n={d['FORWARD']['n']:4d} win={d['FORWARD']['win']:.3f}")
    print("\nTRENDING-ONLY classes:", trending)
    tp = results["trending_portfolio"]
    for ph in ("TRAIN", "FORWARD"):
        print(f"  {ph}: all={tp[ph]['all']}")
        print(f"        long={tp[ph]['long']} short={tp[ph]['short']}")
    print("  FORWARD per_year:")
    for y, s in tp["FORWARD"]["per_year"].items():
        print("     ", y, s)
    return results


if __name__ == "__main__":
    main()
