"""H4 order-level reconciliation: episode entries, time exit, wide stop,
spread + nightly swap costs. Direction pre-registered from TRAIN sign.
H4-bar stop checks (wide 3xATR stop makes bar resolution acceptable)."""
import csv, json, math, statistics, sys, collections
from pathlib import Path
ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

SNAP = json.loads((ROUTE / "ULTIMATE_SYMBOL_SPREAD_SNAPSHOT.json").read_text())
D = REPO_ROOT / "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
STOP_ATR = 3.0

def state(closes, highs, lows, i, atr):
    if i < 60 or atr <= 0: return None
    m20 = sum(closes[i-19:i+1])/20; m50 = sum(closes[i-49:i+1])/50
    trend = "up" if m20 > m50*1.001 else ("down" if m20 < m50*0.999 else "flat")
    hi, lo = max(highs[i-47:i+1]), min(lows[i-47:i+1])
    pos = (closes[i]-lo)/(hi-lo) if hi > lo else 0.5
    posb = "low" if pos < 0.25 else ("high" if pos > 0.75 else "mid")
    tr48 = [max(highs[j]-lows[j], abs(highs[j]-closes[j-1]), abs(lows[j]-closes[j-1])) for j in range(i-47,i+1)]
    a48 = sum(tr48)/48
    vol = "expand" if atr > a48*1.15 else ("contract" if atr < a48*0.85 else "norm")
    return trend, posb, vol

mine = json.loads((ROUTE / "ULTIMATE_DEEP_HORIZON_MINE_V1.json").read_text())
top_cells = {}
for r in sorted(mine["h4"]["top"], key=lambda x: -abs(x.get("t", 0)))[:40]:
    top_cells[tuple(r["cell"][:3]) + (r["cell"][3],)] = 1 if r["mean_atr"] > 0 else -1
for r in mine["h4"].get("confirmations", []):
    key = tuple(r["cell"][:3]) + (r["cell"][3],)
    if key not in top_cells and abs(r.get("t",0)) >= 4:
        top_cells[key] = 1 if r["mean_atr"] > 0 else -1
print(f"pre-registered cells: {len(top_cells)}", flush=True)

train_net, val_net = collections.defaultdict(list), collections.defaultdict(list)
for f in sorted(D.glob("*_H4.csv")):
    symbol = f.name[:-7]
    ac = ASSET_CLASS_BY_SYMBOL.get(symbol)
    meta = SNAP.get(symbol) or {}
    sp = float(meta.get("spread_price") or 0)
    if ac is None or sp <= 0: continue
    point = float(meta.get("point") or 0)
    mode = meta.get("swap_mode")
    swl = float(meta.get("swap_long") or 0); sws = float(meta.get("swap_short") or 0)
    rows = [(str(r["time"])[:19], float(r["high"]), float(r["low"]), float(r["close"]))
            for r in csv.DictReader(open(f)) if r.get("close")]
    times=[r[0] for r in rows]; highs=[r[1] for r in rows]; lows=[r[2] for r in rows]; closes=[r[3] for r in rows]
    trs=[0.0]*len(rows)
    for i in range(1,len(rows)):
        trs[i]=max(highs[i]-lows[i],abs(highs[i]-closes[i-1]),abs(lows[i]-closes[i-1]))
    prev=None
    for i in range(60, len(rows)-30):
        atr=sum(trs[i-13:i+1])/14
        st=state(closes,highs,lows,i,atr)
        if st is None: continue
        is_entry = st != prev; prev = st
        if not is_entry: continue
        month=times[i][:7]
        if month >= "2026-05": continue
        for (c_ac, c_a, c_b, h), direction in top_cells.items():
            if c_ac != ac: continue
            tags = {f"trend={st[0]}", f"pos={st[1]}", f"vol={st[2]}"}
            if c_a not in tags or c_b not in tags: continue
            # simulate: stop at 3 ATR adverse; else exit close[i+h]
            stop_price = closes[i] - direction*STOP_ATR*atr
            net=None
            for j in range(i+1, i+h+1):
                if direction>0 and lows[j] <= stop_price: net=-STOP_ATR; break
                if direction<0 and highs[j] >= stop_price: net=-STOP_ATR; break
            if net is None:
                net = direction*(closes[i+h]-closes[i])/atr
            nights = max(0, (h*4)//24)
            swap = (swl if direction>0 else sws)
            swap_price = swap*point if mode == 1 else 0.0
            net -= sp/atr
            net += (swap_price*nights)/atr  # swap is signed (usually negative)
            cell=(c_ac,c_a,c_b,h)
            (val_net if month>="2026-01" else train_net)[cell].append(net)

report=[]
pv=[]
for cell, vals in train_net.items():
    v = val_net.get(cell, [])
    if len(vals)<50: continue
    tm=statistics.fmean(vals)
    vm=statistics.fmean(v) if len(v)>=8 else None
    report.append({"cell": list(cell), "train_n": len(vals), "train_net_mean": round(tm,4),
                   "val_n": len(v), "val_net_mean": round(vm,4) if vm is not None else None})
    if v: pv.extend(v)
report.sort(key=lambda r: -(r["train_net_mean"]))
port_t=None
if len(pv)>=30:
    pm,psd=statistics.fmean(pv),statistics.pstdev(pv)
    port_t=pm/(psd/math.sqrt(len(pv))) if psd>0 else None
out={"schema_version":"h4_reconciliation_v1","cells":report,
     "train_pos_cells": sum(1 for r in report if r["train_net_mean"]>0),
     "val_portfolio_n": len(pv),
     "val_portfolio_mean": round(statistics.fmean(pv),4) if pv else None,
     "val_portfolio_t": round(port_t,2) if port_t else None,
     "broker_operation": False,"paid_api_or_vendor_call": False,
     "broker_runtime_change_status": False,"validation_result_status": False,
     "outcome_result_rows_status": False}
(ROUTE/"ULTIMATE_H4_RECONCILIATION_V1.json").write_text(json.dumps(out,indent=1,sort_keys=True))
print(json.dumps({k:out[k] for k in ("train_pos_cells","val_portfolio_n","val_portfolio_mean","val_portfolio_t")},sort_keys=True))
print("top:", json.dumps(report[:6]))
