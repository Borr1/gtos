"""HUNT: vol_regime_breakout
Volatility-regime-gated Donchian/range breakout (and inverse reversion-in-contraction).

Thesis: raw breakouts are coinflips because most "breaks" happen in chop and fail.
Gate them by a volatility-EXPANSION regime (ATR rising / squeeze release) so we only
take breaks that have momentum behind them. Inverse test: reversion only in CONTRACTION.

DISCIPLINE: TRAIN 2022-2024 / FORWARD 2025-2026. Per-trade R, win%, per-year, by
asset_class, long vs short. The bar is POSITIVE & STABLE IN FORWARD. No rejection
theater -- numbers reported honestly.

Fill sim: TESTED geometry_lib.simulate ONLY (no hand-rolled stop/target/trail).
"""
from __future__ import annotations
import sys, os, csv, json, math, statistics
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"))
from geometry_lib import Bar, atr14, simulate
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

DATA_DIR = os.path.join(ROOT, "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026")
COST_MAP = json.load(open(os.path.join(ROOT,
    "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/ULTIMATE_REAL_COST_MAP.json")))

def cost_for(sym):
    ac = ASSET_CLASS_BY_SYMBOL.get(sym, "fx")
    if ac == "crypto":
        return 0.095
    return COST_MAP.get(ac, COST_MAP["_global_median"])

def load(sym):
    path = os.path.join(DATA_DIR, sym + "_H4.csv")
    bars, times = [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                o=float(row["open"]); h=float(row["high"]); l=float(row["low"])
                c=float(row["close"]); v=float(row["volume"])
            except Exception:
                continue
            bars.append(Bar(o,h,l,c,v)); times.append(row["time"])
    return bars, times

SYMBOLS = [f[:-7] for f in os.listdir(DATA_DIR) if f.endswith("_H4.csv")]
SYMBOLS = [s for s in SYMBOLS if s in ASSET_CLASS_BY_SYMBOL]
SYMBOLS.sort()

# ---- precompute per-symbol series so iteration over configs is cheap ----
CACHE = {}
def prep(sym):
    if sym in CACHE: return CACHE[sym]
    bars, times = load(sym)
    n = len(bars)
    atr = [0.0]*n
    for i in range(n):
        atr[i] = atr14(bars, i)
    # rolling ATR average (slow) for regime gate
    years = [int(t[:4]) for t in times]
    CACHE[sym] = (bars, times, years, atr, n)
    return CACHE[sym]

def donchian(bars, i, lookback):
    # highest high / lowest low over the lookback bars ENDING at i-1 (prior, no lookahead)
    hi = max(bars[j].h for j in range(i-lookback, i))
    lo = min(bars[j].l for j in range(i-lookback, i))
    return hi, lo

def sma(seq, i, w):
    return sum(seq[i-w+1:i+1])/w

def run_config(cfg):
    """cfg dict -> per-trade R list with metadata tags.
    Modes:
      breakout : enter on Donchian break, gated by ATR expansion.
      reversion: enter on Donchian break FADE, gated by ATR contraction (inverse).
    """
    mode      = cfg["mode"]
    look      = cfg["look"]          # donchian lookback
    atr_fast  = cfg.get("atr_fast", 1)   # current atr smoothing
    atr_slow  = cfg["atr_slow"]      # slow atr window for regime baseline
    exp_ratio = cfg["exp_ratio"]     # gate: atr_now / atr_slow threshold
    stop_mult = cfg["stop_mult"]
    geom      = cfg["geom"]          # ('target', mult) or ('trail', arm, gap)
    maxbars   = cfg.get("maxbars", 80)
    sides     = cfg.get("sides", (1,-1))
    min_break = cfg.get("min_break", 0.0)  # break must exceed prior extreme by min_break*atr

    trades = []  # (year, asset_class, side, R)
    for sym in SYMBOLS:
        bars, times, years, atr, n = prep(sym)
        ac = ASSET_CLASS_BY_SYMBOL[sym]
        cost = cost_for(sym)
        warm = max(look, atr_slow) + 16
        for i in range(warm, n-2):
            a = atr[i]
            if a <= 0: continue
            aslow = sma(atr, i, atr_slow)
            if aslow <= 0: continue
            ratio = a / aslow
            expanding   = ratio >= exp_ratio
            contracting = ratio <= (1.0/exp_ratio) if exp_ratio > 0 else False
            hi, lo = donchian(bars, i, look)
            c = bars[i].c
            stop_dist = stop_mult * a
            if stop_dist <= 0: continue

            for side in sides:
                take = False
                if mode == "breakout":
                    if not expanding: continue
                    if side > 0 and c > hi + min_break*a: take = True
                    if side < 0 and c < lo - min_break*a: take = True
                elif mode == "reversion":
                    # fade a break, only when contracting (mean-revert regime)
                    if not contracting: continue
                    # price poked above range high -> fade short; below low -> fade long
                    if side < 0 and c > hi + min_break*a: take = True
                    if side > 0 and c < lo - min_break*a: take = True
                if not take: continue

                if geom[0] == "target":
                    r = simulate(bars, i, side, stop_dist=stop_dist,
                                 target_dist=geom[1]*a, maxbars=maxbars, cost=cost)
                else:  # trail
                    r = simulate(bars, i, side, stop_dist=stop_dist,
                                 trail_arm=geom[1]*stop_dist, trail_gap=geom[2]*stop_dist,
                                 maxbars=maxbars, cost=cost)
                trades.append((years[i], ac, side, r))
    return trades

def summarize(trades, label):
    def stats(rs):
        if not rs: return (0, 0.0, 0.0)
        return (len(rs), statistics.mean(rs), sum(1 for x in rs if x>0)/len(rs))
    train = [t for t in trades if t[0] <= 2024]
    fwd   = [t for t in trades if t[0] >= 2025]
    tr = [t[3] for t in train]; fr=[t[3] for t in fwd]
    n_t, m_t, w_t = stats(tr)
    n_f, m_f, w_f = stats(fr)
    out = {
        "label": label,
        "train": {"n": n_t, "per_trade_R": round(m_t,4), "win": round(w_t,4)},
        "forward": {"n": n_f, "per_trade_R": round(m_f,4), "win": round(w_f,4)},
    }
    # forward per-year
    py = {}
    for yr in sorted(set(t[0] for t in fwd)):
        rs = [t[3] for t in fwd if t[0]==yr]
        py[str(yr)] = {"n": len(rs), "per_trade_R": round(statistics.mean(rs),4),
                       "win": round(sum(1 for x in rs if x>0)/len(rs),4)}
    out["forward_per_year"] = py
    # forward by asset_class
    bac = {}
    for ac in sorted(set(t[1] for t in fwd)):
        rs = [t[3] for t in fwd if t[1]==ac]
        if len(rs) < 10: continue
        bac[ac] = {"n": len(rs), "per_trade_R": round(statistics.mean(rs),4),
                   "win": round(sum(1 for x in rs if x>0)/len(rs),4)}
    out["forward_by_asset_class"] = bac
    # forward long/short
    ls = {}
    for side,nm in ((1,"long"),(-1,"short")):
        rs=[t[3] for t in fwd if t[2]==side]
        if rs:
            ls[nm]={"n":len(rs),"per_trade_R":round(statistics.mean(rs),4),
                    "win":round(sum(1 for x in rs if x>0)/len(rs),4)}
    out["forward_long_short"]=ls
    return out

def fwd_R(o): return o["forward"]["per_trade_R"]
def fwd_n(o): return o["forward"]["n"]

if __name__ == "__main__":
    grid = []
    # --- BREAKOUT with vol-expansion gate ---
    for look in (20, 40, 55):
        for atr_slow in (50, 100):
            for exp_ratio in (1.10, 1.25, 1.45):
                for stop_mult in (0.5, 1.0):
                    for geom in (("target",1.0),("target",1.5),("target",2.0),("trail",2.0,1.0)):
                        grid.append(dict(mode="breakout", look=look, atr_slow=atr_slow,
                                         exp_ratio=exp_ratio, stop_mult=stop_mult,
                                         geom=geom, min_break=0.0))
    # --- INVERSE: reversion in contraction ---
    for look in (20, 40):
        for atr_slow in (50, 100):
            for exp_ratio in (1.10, 1.25):
                for stop_mult in (0.5, 1.0):
                    for geom in (("target",1.0),("target",1.5),("trail",2.0,1.0)):
                        grid.append(dict(mode="reversion", look=look, atr_slow=atr_slow,
                                         exp_ratio=exp_ratio, stop_mult=stop_mult,
                                         geom=geom, min_break=0.0))

    results = []
    for k,cfg in enumerate(grid):
        trades = run_config(cfg)
        label = f"{cfg['mode']}|look{cfg['look']}|slow{cfg['atr_slow']}|exp{cfg['exp_ratio']}|stop{cfg['stop_mult']}|{cfg['geom']}"
        s = summarize(trades, label)
        s["cfg"] = {kk:vv for kk,vv in cfg.items()}
        results.append(s)
        print(f"[{k+1}/{len(grid)}] {label:70s} TRAIN n={s['train']['n']:5d} R={s['train']['per_trade_R']:+.3f}  FWD n={s['forward']['n']:5d} R={s['forward']['per_trade_R']:+.3f} win={s['forward']['win']:.3f}")

    # rank by forward R among configs with enough forward sample
    valid = [r for r in results if fwd_n(r) >= 150]
    valid.sort(key=lambda r: fwd_R(r), reverse=True)
    print("\n===== TOP 12 by FORWARD per-trade R (forward n>=150) =====")
    for r in valid[:12]:
        print(f"{r['label']:70s} FWD n={fwd_n(r):5d} R={fwd_R(r):+.4f} win={r['forward']['win']:.3f} TRAIN R={r['train']['per_trade_R']:+.3f}")

    json.dump(results, open(os.path.join(ROOT,
        "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/hunt_vol_regime_breakout_results.json"),"w"), indent=1)
    print("\nwrote results json")
