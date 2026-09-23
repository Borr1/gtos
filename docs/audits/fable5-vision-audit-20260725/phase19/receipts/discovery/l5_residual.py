"""Is cost_r predictive of outcome BEYOND the stop-tightness it encodes?
cost_r = spread_price/risk_distance and spread_price is a per-symbol CONSTANT for 16/24
symbols -- so within those symbols cost_r is a monotone function of 1/risk_distance and
carries NO independent information at all. Measure the residual."""
import gzip,json,os,collections,math
DISC="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
rows=[json.loads(l) for l in gzip.open(os.path.join(DISC,"l5_MONEY_TABLE.jsonl.gz"),"rt")]
anch={}
for l in gzip.open(os.path.join(DISC,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt"):
    a=json.loads(l); anch[(a["candidate_id"],a["decision_time_utc"])]=a
def bo(m): return "born_past_stop" if m<=-1.0 else ("born_marketable" if m<0.0 else ("born_at_limit" if m==0.0 else "born_resting"))
for r in rows:
    a=anch.get((r["candidate_id"],r["decision_time_utc"])); m=a.get("mkt_r_prev_close") if a else None
    r["born"]=bo(m) if m is not None else "unanchored"
    r["rel_stop"]=r["risk_distance"]/r["entry_price"] if r["entry_price"] else None
pop=[r for r in rows if r["born"]!="born_past_stop" and r["gross_r"] is not None and r["cost_r"] is not None and r["rel_stop"]]
out={"n_pop":len(pop)}
# rank cost_r and rel_stop WITHIN symbol, then cross-tab
bysym=collections.defaultdict(list)
for r in pop: bysym[r["symbol"]].append(r)
def tert(v,i,n): return 1 if i<n/3 else (2 if i<2*n/3 else 3)
for s,v in bysym.items():
    n=len(v)
    v.sort(key=lambda r:r["cost_r"])
    for i,r in enumerate(v): r["ct"]=tert(v,i,n)
    v.sort(key=lambda r:r["rel_stop"])
    for i,r in enumerate(v): r["st"]=tert(v,i,n)
ct=collections.defaultdict(list)
for r in pop: ct[(r["ct"],r["st"])].append(r["gross_r"])
grid={}
for k,g in sorted(ct.items()):
    grid[f"cost_t{k[0]}_stopwidth_t{k[1]}"]={"n":len(g),"gross_mean":round(sum(g)/len(g),5),
        "win_pct":round(100*sum(1 for x in g if x>0)/len(g),2)}
out["cost_x_stopwidth_grid_within_symbol"]=grid
# marginal of stop width alone
sw=collections.defaultdict(list)
for r in pop: sw[r["st"]].append(r["gross_r"])
out["stopwidth_tertile_within_symbol"]={str(k):{"n":len(g),"gross_mean":round(sum(g)/len(g),5),
    "win_pct":round(100*sum(1 for x in g if x>0)/len(g),2)} for k,g in sorted(sw.items())}
# residual: within each stop-width tertile, does cost tertile still move gross?
res={}
for stt in (1,2,3):
    sub=[r for r in pop if r["st"]==stt]
    d=collections.defaultdict(list)
    for r in sub: d[r["ct"]].append(r["gross_r"])
    res[f"stopwidth_t{stt}"]={str(k):{"n":len(g),"gross_mean":round(sum(g)/len(g),5)} for k,g in sorted(d.items())}
    vals=[sum(g)/len(g) for k,g in sorted(d.items())]
    res[f"stopwidth_t{stt}"]["spread_t3_minus_t1"]=round(vals[-1]-vals[0],5) if len(vals)>1 else None
out["cost_signal_within_stopwidth"]=res
# and the reverse: within cost tertile does stop width still move gross?
res2={}
for ctt in (1,2,3):
    sub=[r for r in pop if r["ct"]==ctt]
    d=collections.defaultdict(list)
    for r in sub: d[r["st"]].append(r["gross_r"])
    res2[f"cost_t{ctt}"]={str(k):{"n":len(g),"gross_mean":round(sum(g)/len(g),5)} for k,g in sorted(d.items())}
    vals=[sum(g)/len(g) for k,g in sorted(d.items())]
    res2[f"cost_t{ctt}"]["spread_t3_minus_t1"]=round(vals[-1]-vals[0],5) if len(vals)>1 else None
out["stopwidth_signal_within_cost"]=res2
# how many symbols have cost_r a deterministic function of 1/risk_distance
det={}
for s,v in bysym.items():
    prod=[r["cost_r"]*r["risk_distance"] for r in v]
    sp=[r["spread_r"]*r["risk_distance"] for r in v]
    det[s]={"n":len(v),"n_distinct_spread_price":len(set(round(x,10) for x in sp)),
            "spearman_cost_r_vs_inv_riskdist":None}
    # spearman of cost_r vs 1/risk_distance
    xs=[r["cost_r"] for r in v]; ys=[1.0/r["risk_distance"] for r in v]
    def rk(a):
        idx=sorted(range(len(a)),key=lambda i:a[i]); rr=[0]*len(a); i=0
        while i<len(idx):
            j=i
            while j+1<len(idx) and a[idx[j+1]]==a[idx[i]]: j+=1
            av=(i+j)/2+1
            for k in range(i,j+1): rr[idx[k]]=av
            i=j+1
        return rr
    def pear(x,y):
        n=len(x); mx=sum(x)/n; my=sum(y)/n
        sx=math.sqrt(sum((a-mx)**2 for a in x)); sy=math.sqrt(sum((b-my)**2 for b in y))
        return None if sx==0 or sy==0 else sum((a-mx)*(b-my) for a,b in zip(x,y))/(sx*sy)
    det[s]["spearman_cost_r_vs_inv_riskdist"]=round(pear(rk(xs),rk(ys)),4)
out["cost_r_is_geometry_by_symbol"]=det
json.dump(out,open(os.path.join(DISC,"l5_RESIDUAL_V1.json"),"w"),indent=1)
print("n_pop",len(pop))
print("\n=== stop-width tertile (within symbol) ===")
for k,v in out["stopwidth_tertile_within_symbol"].items(): print(" t",k,v)
print("\n=== cost signal WITHIN each stop-width tertile ===")
for k,v in res.items(): print(" ",k,json.dumps(v))
print("\n=== stop-width signal WITHIN each cost tertile ===")
for k,v in res2.items(): print(" ",k,json.dumps(v))
print("\n=== spearman(cost_r, 1/risk_distance) per symbol ===")
for s,v in sorted(det.items(),key=lambda x:x[1]["spearman_cost_r_vs_inv_riskdist"]):
    print(f"{s:11s} n {v['n']:5d} distinct_spread_price {v['n_distinct_spread_price']:5d} spearman {v['spearman_cost_r_vs_inv_riskdist']:.4f}")
