"""KB4 permutation null: does the discovered regime label carry real information,
or could random partitioning of the same trades reproduce the flagship cell EV?
We take XAUUSD momentum-entry trades, compute the real EV of the trades that fall in reg1,
then shuffle regime labels across the SAME trade set 500x and measure how often a random
4-way partition of identical size achieves >= the observed reg1 forward mean_R.
Leak-free: trades & labels already computed by the engine; this only tests the label's value."""
import sys, json
import numpy as np
ROUTE = "/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
sys.path.insert(0, "/Users/borr/Documents/gtos/repo/ai-trading-agent"); sys.path.insert(0, ROUTE)
import numpy as np
import regime_map as rm
from geometry_lib import atr14, simulate
import wave1_structure_setups_ict as w1

def collect(sym, kind="mom"):
    T, B = w1.load(sym)
    closes = np.array([b.c for b in B], float)
    atrs = np.array([atr14(B, i) for i in range(len(B))], float)
    cost = w1.cost_for(sym)
    rows = []
    for i in range(110, len(B) - 1):
        fr = rm.feature_row(B, closes, atrs, i)
        if fr is None: continue
        h = rm.hurst_vr(closes, i, rm.HURST_W)
        if h is None: continue
        fr = dict(fr); fr["i"] = i; fr["year"] = T[i].year; fr["hurst"] = h
        rows.append(fr)
    train = [r for r in rows if r["year"] <= 2024]
    model = rm.RegimeModel().fit(train)
    fn = rm.momentum_entry if kind == "mom" else rm.reversion_entry
    trades = []   # (regime, hurst_sign, year, R)
    for r in rows:
        e = fn(B, closes, atrs, r["i"])
        if e is None: continue
        d, sd, td = e
        R = simulate(B, r["i"], d, stop_dist=sd, target_dist=td, maxbars=60, cost=cost)
        trades.append((model.label(r), "trend" if r["hurst"] >= 0.5 else "revert", r["year"], R))
    return trades

def null_test(sym, kind, target_reg, target_hs, n_perm=500, seed=1):
    trades = collect(sym, kind)
    fwd = [(reg, hs, R) for reg, hs, y, R in trades if y >= 2025]
    obs = [R for reg, hs, R in fwd if reg == target_reg and hs == target_hs]
    if not obs:
        return {"error": "no obs"}
    obs_n = len(obs); obs_mr = float(np.mean(obs))
    allR = np.array([R for _, _, R in fwd])
    rng = np.random.default_rng(seed)
    ge = 0
    for _ in range(n_perm):
        samp = rng.choice(allR, size=obs_n, replace=False)
        if samp.mean() >= obs_mr:
            ge += 1
    return {"symbol": sym, "cell": f"{kind}|reg{target_reg}|{target_hs}",
            "fwd_n": obs_n, "fwd_mean_R": round(obs_mr, 4),
            "perm_p_value": round(ge / n_perm, 4), "n_perm": n_perm,
            "interpretation": "low p => regime label selects materially better-than-random trades"}

if __name__ == "__main__":
    for sym, kind, reg, hs in [("XAUUSD","mom",1,"revert"),("XAGUSD","mom",0,"revert"),
                               ("UK100","mom",2,"trend"),("XAUUSD","rev",0,"trend")]:
        print(json.dumps(null_test(sym, kind, reg, hs), indent=None))
