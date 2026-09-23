"""Deep-horizon origin miner: D1/H4 conditional forward returns, 2022-2026.

Lessons encoded from the M15 mine failure:
- EPISODE semantics: only the FIRST bar of each consecutive same-state run
  counts (entry-on-state-change == how a system trades it; kills the
  persistence inflation that faked the M15 t-stats).
- Costs measured per cell as spread_price/ATR of that bar.
- t across episode observations directly (episodes are far apart in time).
- TRAIN 2022-01..2025-12; VALIDATION 2026-01..2026-04 once. May/June 2026
  untouched (sealed-adjacent buffer).
"""
import csv, json, math, statistics, sys, collections
from pathlib import Path
ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

DATA = REPO_ROOT / "data/mt5_research_exports"
SPREADS = json.loads((ROUTE / "ULTIMATE_SYMBOL_SPREAD_SNAPSHOT.json").read_text())
SETUPS = {"d1": (DATA / "bridge_ftmo_deep_d1_2022_2026", (2, 5, 10), "_D1.csv"),
          "h4": (DATA / "bridge_ftmo_deep_h4_2022_2026", (6, 12, 30), "_H4.csv")}
BH_Q = 0.05
MIN_EPISODES = 80

def state(closes, highs, lows, i, atr):
    if i < 60 or atr <= 0: return None
    m20 = sum(closes[i-19:i+1])/20; m50 = sum(closes[i-49:i+1])/50
    trend = "up" if m20 > m50*1.001 else ("down" if m20 < m50*0.999 else "flat")
    hi, lo = max(highs[i-47:i+1]), min(lows[i-47:i+1])
    pos = (closes[i]-lo)/(hi-lo) if hi > lo else 0.5
    posb = "low" if pos < 0.25 else ("high" if pos > 0.75 else "mid")
    tr48 = [max(highs[j]-lows[j], abs(highs[j]-closes[j-1]), abs(lows[j]-closes[j-1])) for j in range(i-47,i+1)]
    vol = "expand" if atr > (sum(tr48)/48)*1.15 else ("contract" if atr < (sum(tr48)/48)*0.85 else "norm")
    return {"trend": trend, "pos": posb, "vol": vol}

results = {}
for tag, (dirpath, horizons, suffix) in SETUPS.items():
    train = collections.defaultdict(list); val = collections.defaultdict(list)
    n_eps = 0
    for f in sorted(dirpath.glob(f"*{suffix}")):
        symbol = f.name[:-len(suffix)]
        ac = ASSET_CLASS_BY_SYMBOL.get(symbol)
        sp = float((SPREADS.get(symbol) or {}).get("spread_price") or 0)
        if ac is None or sp <= 0: continue
        rows = [(str(r["time"])[:19], float(r["high"]), float(r["low"]), float(r["close"]))
                for r in csv.DictReader(open(f)) if r.get("close")]
        times = [r[0] for r in rows]; highs=[r[1] for r in rows]; lows=[r[2] for r in rows]; closes=[r[3] for r in rows]
        trs = [0.0]*len(rows)
        for i in range(1, len(rows)):
            trs[i] = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
        prev_state = None
        for i in range(60, len(rows)-max(horizons)):
            atr = sum(trs[i-13:i+1])/14
            st = state(closes, highs, lows, i, atr)
            if st is None: continue
            key = (st["trend"], st["pos"], st["vol"])
            is_entry = key != prev_state
            prev_state = key
            if not is_entry: continue  # episode semantics
            n_eps += 1
            year = times[i][:4]
            month = times[i][:7]
            if month >= "2026-05": continue
            bucket = val if month >= "2026-01" else train
            for h in horizons:
                fwd = (closes[i+h]-closes[i])/atr - sp/atr
                for cell_key in ((ac, f"trend={st['trend']}", f"pos={st['pos']}", h),
                                 (ac, f"pos={st['pos']}", f"vol={st['vol']}", h),
                                 (ac, f"trend={st['trend']}", f"vol={st['vol']}", h)):
                    bucket[cell_key].append(fwd)
            _ = year
    tested = []
    for cell, vals in train.items():
        if len(vals) < MIN_EPISODES: continue
        m, sd = statistics.fmean(vals), statistics.pstdev(vals)
        if sd <= 0: continue
        t = m/(sd/math.sqrt(len(vals)))
        p = 2*(1-0.5*(1+math.erf(abs(t)/math.sqrt(2))))
        tested.append({"cell": list(cell), "n": len(vals), "mean_atr": round(m,4), "t": round(t,2), "p": p})
    tested.sort(key=lambda r: r["p"])
    mt = len(tested); mk = 0
    for k, r in enumerate(tested, 1):
        if r["p"] <= BH_Q*k/mt: mk = k
    surv = tested[:mk]
    conf = []
    for r in surv:
        v = val.get(tuple(r["cell"][:3]) + (r["cell"][3],), [])
        if len(v) >= 10:
            vm = statistics.fmean(v)
            conf.append({**r, "val_n": len(v), "val_mean_atr": round(vm,4),
                         "same_sign": (vm>0)==(r["mean_atr"]>0)})
    results[tag] = {"episodes": n_eps, "cells_tested": mt, "bh_survivors": len(surv),
                    "confirmed_same_sign": sum(1 for c in conf if c["same_sign"]),
                    "confirm_evaluable": len(conf),
                    "top": sorted(surv, key=lambda r: -abs(r["mean_atr"]))[:25],
                    "confirmations": conf[:40]}

out = {"schema_version": "ultimate_deep_horizon_mine_v1", **results,
       "broker_operation": False, "paid_api_or_vendor_call": False,
       "broker_runtime_change_status": False, "validation_result_status": False,
       "outcome_result_rows_status": False}
(ROUTE / "ULTIMATE_DEEP_HORIZON_MINE_V1.json").write_text(json.dumps(out, indent=1, sort_keys=True))
print(json.dumps({t: {k: results[t][k] for k in ("episodes","cells_tested","bh_survivors","confirmed_same_sign","confirm_evaluable")} for t in results}, sort_keys=True))
