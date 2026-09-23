import gzip, pickle, json, math, collections
rows=[]
for m in ("feb","apr","may","jun","jul"):
    rows+=pickle.load(gzip.open(f"/private/tmp/w21-puzzle-cache/rows_{m}.pkl.gz","rb"))
print("rows",len(rows))
def num(x):
    try:
        v=float(x); return v if v==v else None
    except: return None
# 1) order type
ot=collections.Counter(r.get("proposed_order_type") for r in rows)
print("order_type:",dict(ot))
# 2) swap cross-section
sw=collections.defaultdict(list)
for r in rows:
    v=num(r.get("swap_cost_r"))
    if v is None: continue
    sw[(r.get("symbol"),r.get("side"))].append(v)
allsw=[v for k in sw for v in sw[k]]
print(f"swap_cost_r: n={len(allsw)} mean={sum(allsw)/len(allsw):+.5f} min={min(allsw):+.5f} max={max(allsw):+.5f} n_negative(=credit?)={sum(1 for v in allsw if v<0)} n_zero={sum(1 for v in allsw if v==0)} n_pos={sum(1 for v in allsw if v>0)}")
tab=sorted(((sum(v)/len(v),k,len(v)) for k,v in sw.items() if len(v)>=200))
print("lowest-cost symbol/side (top 12):")
for m_,k,n in tab[:12]: print(f"   {str(k):28s} n={n:6d} mean_swap_cost_r={m_:+.5f}")
print("highest-cost:")
for m_,k,n in tab[-6:]: print(f"   {str(k):28s} n={n:6d} mean_swap_cost_r={m_:+.5f}")
# 3) spread_r by utc hour, MARKET only
byh=collections.defaultdict(list)
for r in rows:
    if r.get("proposed_order_type")!="MARKET": continue
    v=num(r.get("spread_r"))
    if v is None: continue
    byh[r.get("utc_hour")].append(v)
print("spread_r (MARKET) by utc_hour: hour n median mean")
med={}
for h in sorted(byh, key=lambda x:(x is None, x)):
    v=sorted(byh[h]); med[h]=v[len(v)//2]
    print(f"   h={str(h):>4s} n={len(v):6d} median={v[len(v)//2]:.4f} mean={sum(v)/len(v):.4f}")
mm=sorted(med.items(), key=lambda kv: kv[1])
print("BEST hour",mm[0],"WORST hour",mm[-1],"ratio %.2fx"%(mm[-1][1]/max(1e-9,mm[0][1])))
# 4) cost decomposition
comp=collections.defaultdict(list)
for r in rows:
    for k in ("spread_r","commission_r","expected_slippage_r","swap_cost_r","cost_r","terminal_net_r"):
        v=num(r.get(k))
        if v is not None: comp[k].append(v)
print("cost decomposition (all rows):")
for k,v in comp.items(): print(f"   {k:22s} n={len(v):7d} mean={sum(v)/len(v):+.5f}")
json.dump({"order_type":{str(k):v for k,v in ot.items()},
           "spread_r_median_by_hour":{str(k):v for k,v in med.items()},
           "swap_by_symbol_side":{str(k):[len(v),sum(v)/len(v)] for k,v in sw.items()},
           "cost_means":{k:[len(v),sum(v)/len(v)] for k,v in comp.items()}},
          open("cache_stats.json","w"),indent=1)
