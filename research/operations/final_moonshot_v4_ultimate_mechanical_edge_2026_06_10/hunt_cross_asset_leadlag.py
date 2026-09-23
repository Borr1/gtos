"""
hunt_cross_asset_leadlag.py
===========================
Signal class: CROSS-ASSET / LEAD-LAG.

Thesis: when a DRIVER makes a strong move over a short lookback (z-scored log return),
the FOLLOWER continues in the implied direction over the next few H4 bars (momentum
spillover), OR fades it (reversion). We test BOTH polarities, honestly, per pair.

Fill sim: TESTED geometry_lib.simulate ONLY. Entry on follower at the bar where the
driver signal fires (decision uses info available at close of bar i; entry = close[i];
trade resolves on follower bars i+1..). Geometry: stop=0.5*atr14, fixed targets and a
trail variant. Real per-asset cost from ULTIMATE_REAL_COST_MAP.json.

Honesty about data: H4 coverage is wildly uneven (see survey). Only 6 symbols span
2022-2024. Most cross-asset drivers/followers (DXY, oil, SPX, JPY pairs, USDCAD...)
start in 2025 -> they live almost entirely in FORWARD. So:
  * TRAIN = 2022-2024, FORWARD = 2025-2026 reported wherever both legs have data.
  * For pairs with no/insufficient TRAIN overlap, we ALSO split FORWARD into two
    halves (F1 / F2) to test within-forward stability. A pair only counts as
    "forward-stable" if its forward edge is positive in BOTH halves with enough trades.
"""
import sys, os, json, math, csv
from datetime import datetime
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
sys.path.insert(0, ROOT)
sys.path.insert(0, "/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10")
from geometry_lib import Bar, atr14, simulate
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

DATA = os.path.join(ROOT, "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026")
COST_MAP = json.load(open(os.path.join(
    "/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10",
    "ULTIMATE_REAL_COST_MAP.json")))

def cost_for(sym):
    ac = ASSET_CLASS_BY_SYMBOL.get(sym, "fx")
    return COST_MAP.get(ac, COST_MAP["_global_median"])

def load(sym):
    """Return (times list[str], bars list[Bar]) aligned by index."""
    path = os.path.join(DATA, f"{sym}_H4.csv")
    times, bars = [], []
    with open(path) as f:
        r = csv.reader(f); next(r)
        for row in r:
            if len(row) < 6: continue
            t,o,h,l,c,v = row
            times.append(t)
            bars.append(Bar(float(o), float(h), float(l), float(c), float(v)))
    return times, bars

# ----- panel load -----
SYMBOLS = [s for s in ASSET_CLASS_BY_SYMBOL if os.path.exists(os.path.join(DATA, f"{s}_H4.csv"))]
PANEL = {}   # sym -> dict(time -> (idx, Bar)), plus arrays
for s in SYMBOLS:
    t, b = load(s)
    PANEL[s] = {"times": t, "bars": b, "tmap": {tt: i for i, tt in enumerate(t)}}

def yr(ts):  # year int from "YYYY-..."
    return int(ts[:4])

# ----- core evaluation of one driver->follower hypothesis -----
def driver_signal(driver, look):
    """Return dict time -> z-scored log return of driver over `look` bars (decision at close)."""
    t = PANEL[driver]["times"]; b = PANEL[driver]["bars"]
    n = len(b)
    lr = [0.0]*n
    for i in range(1, n):
        c0, c1 = b[i-1].c, b[i].c
        lr[i] = math.log(c1/c0) if (c0 > 0 and c1 > 0) else 0.0
    # rolling cumulative return over `look` and rolling z over a vol window
    out = {}
    volwin = 100  # ~ bars for z normalization of the move
    cum = [0.0]*n
    for i in range(look, n):
        cum[i] = sum(lr[i-look+1:i+1])
    # z-score the cum move vs its own recent distribution
    for i in range(look+volwin, n):
        window = cum[i-volwin:i]
        m = sum(window)/len(window)
        var = sum((x-m)**2 for x in window)/len(window)
        sd = math.sqrt(var) if var > 0 else 0.0
        if sd > 0:
            out[t[i]] = (cum[i]-m)/sd
    return out

def evaluate(driver, follower, look, zthr, polarity, geom, min_gap=2):
    """
    polarity: 'momentum' (follower follows driver sign) or 'reversion' (opposite).
    Returns per-trade list: (time, year, direction, R).
    Entry: at the follower bar whose time == driver signal time (close-to-close aligned).
    geom: dict with mode 'fixed' (target_mult) or 'trail'.
    Sign mapping: a positive driver z means driver went UP. We translate to follower
    direction via the assumed economic relationship encoded in PAIRS (corr_sign).
    Here corr_sign is folded into polarity by the caller passing the right sign.
    """
    sig = driver_signal(driver, look)
    ft = PANEL[follower]["times"]; fb = PANEL[follower]["bars"]
    ftmap = PANEL[follower]["tmap"]
    cost = cost_for(follower)
    trades = []
    last_entry_idx = -10**9
    for ts, z in sig.items():
        if abs(z) < zthr: continue
        i = ftmap.get(ts)
        if i is None: continue
        if i < 14 or i >= len(fb)-2: continue
        if i - last_entry_idx < min_gap: continue
        a = atr14(fb, i)
        if a <= 0: continue
        stop = 0.5*a
        # base direction = sign of driver move
        d = 1 if z > 0 else -1
        if polarity == 'reversion':
            d = -d
        if geom["mode"] == "fixed":
            R = simulate(fb, i, d, stop_dist=stop, target_dist=geom["tmult"]*a, cost=cost)
        else:
            R = simulate(fb, i, d, stop_dist=stop,
                         trail_arm=2*stop, trail_gap=1*stop, cost=cost)
        trades.append((ts, yr(ts), d, R))
        last_entry_idx = i
    return trades

def stats(trades):
    if not trades: return {"n":0,"R":0.0,"win":0.0}
    rs = [t[3] for t in trades]
    n = len(rs)
    return {"n":n, "R":sum(rs)/n, "win":sum(1 for r in rs if r>0)/n}

def split_stats(trades):
    train = [t for t in trades if t[1] <= 2024]
    fwd   = [t for t in trades if t[1] >= 2025]
    # within-forward halves by time order
    fwd_sorted = sorted(fwd, key=lambda x: x[0])
    h = len(fwd_sorted)//2
    f1, f2 = fwd_sorted[:h], fwd_sorted[h:]
    per_year = {}
    for y in sorted(set(t[1] for t in trades)):
        per_year[y] = stats([t for t in trades if t[1]==y])
    return {
        "train": stats(train), "forward": stats(fwd),
        "fwd_h1": stats(f1), "fwd_h2": stats(f2),
        "per_year": per_year,
    }

# ----- hypothesis catalog -----
# Each entry: (driver, follower, base_polarity_for_positive_corr)
# polarity flag tells how to turn driver-up into follower direction:
#   'pos'  -> driver up => follower up (long)   [positive correlation, momentum]
#   'neg'  -> driver up => follower down (short) [negative correlation]
# We then test BOTH momentum and reversion on top of this by flipping in evaluate.
# We encode the economic sign by choosing polarity in the eval call.

# Driver -> follower economic relationships (sign = expected corr of returns)
RELATIONS = [
    # USD strength block: DXY up => USD-base pairs up, USD-quote pairs down
    ("DXY_cash", "EURUSD", -1),
    ("DXY_cash", "GBPUSD", -1),
    ("DXY_cash", "AUDUSD", -1),
    ("DXY_cash", "NZDUSD", -1),
    ("DXY_cash", "USDJPY", +1),
    ("DXY_cash", "USDCHF", +1),
    ("DXY_cash", "USDCAD", +1),
    ("DXY_cash", "XAUUSD", -1),
    ("DXY_cash", "XAGUSD", -1),
    # Oil -> CAD (oil up => USDCAD down)
    ("USOIL_cash", "USDCAD", -1),
    ("UKOIL_cash", "USDCAD", -1) if os.path.exists(os.path.join(DATA,"UKOIL_cash_H4.csv")) else None,
    # Risk-on via equity index leads risk FX & crypto
    ("SPX500", "AUDUSD", +1),
    ("SPX500", "NZDUSD", +1),
    ("SPX500", "USDJPY", +1),   # risk-on => yen weak => USDJPY up
    ("SPX500", "BTCUSD", +1),
    ("NAS100", "BTCUSD", +1),
    ("NAS100", "ETHUSD", +1),
    ("NAS100", "AUDUSD", +1),
    ("NAS100", "USDJPY", +1),
    # Gold vs silver / metals cross
    ("XAUUSD", "XAGUSD", +1),
    ("XAUUSD", "XCUUSD", +1),
    # BTC leads alts
    ("BTCUSD", "ETHUSD", +1),
    ("BTCUSD", "LTCUSD", +1),
    ("BTCUSD", "ADAUSD", +1),
    ("BTCUSD", "DOTUSD", +1),
    ("ETHUSD", "ADAUSD", +1),
    # EUR strength proxy: EURUSD leads other EUR crosses / GBP
    ("EURUSD", "GBPUSD", +1),
    ("EURUSD", "AUDUSD", +1),
    ("EURUSD", "XAUUSD", +1),   # weak USD => gold up, EURUSD up
    # JPY risk: USDJPY leads other JPY crosses
    ("USDJPY", "EURJPY", +1),
    ("USDJPY", "GBPJPY", +1),
    ("USDJPY", "AUDJPY", +1),
    # Copper as growth proxy -> AUD
    ("XCUUSD", "AUDUSD", +1),
]
RELATIONS = [r for r in RELATIONS if r is not None]
RELATIONS = [r for r in RELATIONS
             if os.path.exists(os.path.join(DATA, f"{r[0]}_H4.csv"))
             and os.path.exists(os.path.join(DATA, f"{r[1]}_H4.csv"))]

GEOMS = {
    "T1.0": {"mode":"fixed","tmult":1.0},
    "T1.5": {"mode":"fixed","tmult":1.5},
    "T2.0": {"mode":"fixed","tmult":2.0},
    "TRAIL": {"mode":"trail"},
}

def overlap_count(driver, follower):
    dt = set(PANEL[driver]["times"]); ft = set(PANEL[follower]["times"])
    return len(dt & ft)

def main():
    looks = [3, 6, 12]
    zthrs = [1.0, 1.5, 2.0]
    pols  = ["momentum", "reversion"]
    rows = []
    for (driver, follower, sign) in RELATIONS:
        ov = overlap_count(driver, follower)
        if ov < 300:   # need a minimum aligned sample
            continue
        for look in looks:
            sig = driver_signal(driver, look)  # cache-ish (recomputed in evaluate, fine)
            for z in zthrs:
                for base_pol in pols:
                    # translate economic sign + chosen polarity into evaluate's polarity arg.
                    # evaluate uses sign of driver move; 'momentum' means follow driver sign.
                    # For a +1 relation, momentum => follower follows driver (correct).
                    # For a -1 relation, the economic momentum is follower OPPOSITE driver,
                    # i.e. evaluate 'reversion'. So map:
                    if sign == +1:
                        eval_pol = "momentum" if base_pol=="momentum" else "reversion"
                    else:
                        eval_pol = "reversion" if base_pol=="momentum" else "momentum"
                    for gname, geom in GEOMS.items():
                        trades = evaluate(driver, follower, look, z, eval_pol, geom)
                        if len(trades) < 40:  # need enough trades to mean anything
                            continue
                        sp = split_stats(trades)
                        rows.append({
                            "driver":driver, "follower":follower, "relsign":sign,
                            "look":look, "z":z, "thesis":base_pol, "geom":gname,
                            "overlap":ov,
                            "n":len(trades),
                            "all_R":stats(trades)["R"], "all_win":stats(trades)["win"],
                            "train":sp["train"], "forward":sp["forward"],
                            "fwd_h1":sp["fwd_h1"], "fwd_h2":sp["fwd_h2"],
                            "per_year":sp["per_year"],
                            "follower_ac":ASSET_CLASS_BY_SYMBOL.get(follower),
                        })
    # ---- ranking: forward-positive AND within-forward stable ----
    def forward_stable(r):
        f = r["forward"]; h1 = r["fwd_h1"]; h2 = r["fwd_h2"]
        return (f["n"] >= 40 and f["R"] > 0 and
                h1["n"] >= 15 and h2["n"] >= 15 and
                h1["R"] > 0 and h2["R"] > 0)
    rows.sort(key=lambda r: (r["forward"]["R"]), reverse=True)

    print("="*120)
    print("ALL configs with forward n>=40, sorted by forward per-trade R (top 40):")
    print("-"*120)
    hdr = f"{'driver':>11} {'follower':>9} {'L':>2} {'z':>3} {'thesis':>9} {'geom':>5} | {'fN':>4} {'fR':>7} {'fWin':>5} | {'h1R':>7} {'h2R':>7} | {'trN':>4} {'trR':>7} | stable"
    print(hdr)
    for r in rows[:40]:
        f=r["forward"]; tr=r["train"]; h1=r["fwd_h1"]; h2=r["fwd_h2"]
        print(f"{r['driver']:>11} {r['follower']:>9} {r['look']:>2} {r['z']:>3} {r['thesis']:>9} {r['geom']:>5} | "
              f"{f['n']:>4} {f['R']:>7.3f} {f['win']:>5.2f} | {h1['R']:>7.3f} {h2['R']:>7.3f} | "
              f"{tr['n']:>4} {tr['R']:>7.3f} | {'YES' if forward_stable(r) else ''}")

    stable = [r for r in rows if forward_stable(r)]
    print("\n"+"="*120)
    print(f"FORWARD-STABLE configs (fwd n>=40, fwd R>0, both halves R>0, each half n>=15): {len(stable)}")
    print("-"*120)
    stable.sort(key=lambda r: r["forward"]["R"], reverse=True)
    for r in stable[:40]:
        f=r["forward"]; tr=r["train"]; h1=r["fwd_h1"]; h2=r["fwd_h2"]
        py = " ".join(f"{y}:{v['R']:+.2f}({v['n']})" for y,v in sorted(r["per_year"].items()))
        print(f"{r['driver']:>11}->{r['follower']:<9} L{r['look']} z{r['z']} {r['thesis']:>9} {r['geom']:>5} | "
              f"fN={f['n']:>4} fR={f['R']:>+.3f} fWin={f['win']:.2f} | h1={h1['R']:+.2f}/{h1['n']} h2={h2['R']:+.2f}/{h2['n']} | "
              f"trN={tr['n']} trR={tr['R']:+.3f}\n            per-year: {py}")

    # ---- aggregate by polarity to see if momentum or reversion dominates forward ----
    print("\n"+"="*120)
    print("AGGREGATE forward edge by thesis (trade-weighted across all configs n>=40):")
    agg = defaultdict(lambda: [0,0.0,0])  # thesis -> [ntrades, sumR, nwins-ish via win*n]
    for r in rows:
        f=r["forward"]
        agg[r["thesis"]][0]+=f["n"]; agg[r["thesis"]][1]+=f["R"]*f["n"]; agg[r["thesis"]][2]+=f["win"]*f["n"]
    for th,(n,sr,wn) in agg.items():
        if n: print(f"  {th:>9}: forward N={n:>6}  per-trade R={sr/n:+.4f}  win={wn/n:.3f}")

    # save full table
    out = os.path.join("/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10",
                       "hunt_cross_asset_leadlag_results.json")
    json.dump(rows, open(out,"w"), default=str, indent=1)
    print(f"\nwrote {out}  ({len(rows)} configs)")
    return rows

if __name__ == "__main__":
    main()
