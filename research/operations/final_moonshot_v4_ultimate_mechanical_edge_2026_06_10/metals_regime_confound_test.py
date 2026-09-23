"""Regime-confound checks for the metals H4 continuation family.

(a) Baseline: same bars, always-long-metals at the same horizon — does the
    state conditioning beat unconditional exposure?
(b) Sub-period sign stability: 2022H2 (gold drawdown), 2023, 2024, 2025.
(c) Short symmetry: pos=low short-side cells under identical accounting.
"""
import csv, json, math, statistics, sys, collections
from pathlib import Path
ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

SNAP = json.loads((ROUTE / "ULTIMATE_SYMBOL_SPREAD_SNAPSHOT.json").read_text())
D = REPO_ROOT / "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
H = 30
STOP_ATR = 3.0

def state(closes, highs, lows, i, atr):
    if i < 60 or atr <= 0: return None
    m20 = sum(closes[i-19:i+1])/20; m50 = sum(closes[i-49:i+1])/50
    trend = "up" if m20 > m50*1.001 else ("down" if m20 < m50*0.999 else "flat")
    hi, lo = max(highs[i-47:i+1]), min(lows[i-47:i+1])
    pos = (closes[i]-lo)/(hi-lo) if hi > lo else 0.5
    posb = "low" if pos < 0.25 else ("high" if pos > 0.75 else "mid")
    return trend, posb

def sim(closes, highs, lows, i, atr, direction, sp):
    stop_price = closes[i] - direction*STOP_ATR*atr
    for j in range(i+1, i+H+1):
        if direction>0 and lows[j] <= stop_price: return -STOP_ATR - sp/atr
        if direction<0 and highs[j] >= stop_price: return -STOP_ATR - sp/atr
    return direction*(closes[i+H]-closes[i])/atr - sp/atr

cond = collections.defaultdict(list)   # period -> conditioned (pos=high long, state-change entries)
base = collections.defaultdict(list)   # period -> always-long baseline (every 30th bar)
shorts = collections.defaultdict(list) # period -> pos=low short-side
def period(ts):
    if ts < "2022-07": return "2022H1"
    if ts < "2023-01": return "2022H2"
    return ts[:4]

for f in sorted(D.glob("*_H4.csv")):
    symbol = f.name[:-7]
    if ASSET_CLASS_BY_SYMBOL.get(symbol) != "metals": continue
    meta = SNAP.get(symbol) or {}
    sp = float(meta.get("spread_price") or 0)
    if sp <= 0: continue
    rows = [(str(r["time"])[:19], float(r["high"]), float(r["low"]), float(r["close"]))
            for r in csv.DictReader(open(f)) if r.get("close")]
    times=[r[0] for r in rows]; highs=[r[1] for r in rows]; lows=[r[2] for r in rows]; closes=[r[3] for r in rows]
    trs=[0.0]*len(rows)
    for i in range(1,len(rows)):
        trs[i]=max(highs[i]-lows[i],abs(highs[i]-closes[i-1]),abs(lows[i]-closes[i-1]))
    prev=None
    for i in range(60, len(rows)-H):
        atr=sum(trs[i-13:i+1])/14
        st=state(closes,highs,lows,i,atr)
        if st is None: continue
        is_entry = st != prev; prev = st
        pd = period(times[i])
        if times[i][:7] >= "2026-05": continue
        if i % H == 0:
            base[pd].append(sim(closes,highs,lows,i,atr,+1,sp))
        if not is_entry: continue
        if st[1] == "high":
            cond[pd].append(sim(closes,highs,lows,i,atr,+1,sp))
        elif st[1] == "low":
            shorts[pd].append(sim(closes,highs,lows,i,atr,-1,sp))

out = {"schema_version": "metals_regime_confound_v1", "horizon_h4": H, "periods": {}}
for pd in sorted(set(cond) | set(base) | set(shorts)):
    c, b, s = cond.get(pd, []), base.get(pd, []), shorts.get(pd, [])
    out["periods"][pd] = {
        "conditioned_long_n": len(c), "conditioned_long_mean": round(statistics.fmean(c),4) if c else None,
        "always_long_n": len(b), "always_long_mean": round(statistics.fmean(b),4) if b else None,
        "edge_vs_baseline": round(statistics.fmean(c)-statistics.fmean(b),4) if c and b else None,
        "short_low_n": len(s), "short_low_mean": round(statistics.fmean(s),4) if s else None,
    }
allc = [x for v in cond.values() for x in v]; allb = [x for v in base.values() for x in v]
out["overall"] = {"conditioned_mean": round(statistics.fmean(allc),4), "baseline_mean": round(statistics.fmean(allb),4),
                  "edge": round(statistics.fmean(allc)-statistics.fmean(allb),4)}
out.update({"broker_operation": False, "paid_api_or_vendor_call": False, "broker_runtime_change_status": False,
            "validation_result_status": False, "outcome_result_rows_status": False})
(ROUTE/"ULTIMATE_METALS_REGIME_CONFOUND_TEST.json").write_text(json.dumps(out,indent=1,sort_keys=True))
print(json.dumps(out["periods"],indent=1,sort_keys=True)); print(json.dumps(out["overall"],sort_keys=True))
