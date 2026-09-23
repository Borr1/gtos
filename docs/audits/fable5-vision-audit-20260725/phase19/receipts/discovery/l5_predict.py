import gzip,json,os,collections,math
DISC="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
rows=[json.loads(l) for l in gzip.open(os.path.join(DISC,"l5_MONEY_TABLE.jsonl.gz"),"rt")]
anch={}
for l in gzip.open(os.path.join(DISC,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt"):
    a=json.loads(l); anch[(a["candidate_id"],a["decision_time_utc"])]=a
def bo(m): return "born_past_stop" if m<=-1.0 else ("born_marketable" if m<0.0 else ("born_at_limit" if m==0.0 else "born_resting"))
for r in rows:
    a=anch.get((r["candidate_id"],r["decision_time_utc"]))
    m=a.get("mkt_r_prev_close") if a else None
    r["born"]=bo(m) if m is not None else "unanchored"
out={}
# (a) is frozen spread a per-symbol constant?
per=collections.defaultdict(list)
for r in rows:
    if r["frozen_spread_price"] is not None: per[r["symbol"]].append(round(r["frozen_spread_price"],10))
consts={}
for s,v in per.items():
    u=collections.Counter(v)
    consts[s]={"n":len(v),"n_distinct":len(u),"top":[[k,c] for k,c in u.most_common(3)],
               "top_share":round(100*u.most_common(1)[0][1]/len(v),3)}
out["frozen_spread_constancy"]=consts
# (b) cost_r deciles vs realized gross
def deciles(pop,key="cost_r"):
    p=[r for r in pop if r.get(key) is not None and r.get("gross_r") is not None]
    p.sort(key=lambda r:r[key])
    n=len(p); res=[]
    for i in range(10):
        a=n*i//10; b=n*(i+1)//10
        seg=p[a:b]
        g=[x["gross_r"] for x in seg]
        res.append({"decile":i+1,"n":len(seg),
                    f"{key}_lo":round(seg[0][key],5),f"{key}_hi":round(seg[-1][key],5),
                    f"{key}_mean":round(sum(x[key] for x in seg)/len(seg),5),
                    "gross_mean":round(sum(g)/len(g),5),
                    "win_pct":round(100*sum(1 for x in g if x>0)/len(g),2),
                    "mean_risk_distance":round(sum(x["risk_distance"] for x in seg)/len(seg),6),
                    "mean_cost_usd":round(sum(x["cost_usd"] for x in seg)/len(seg),2)})
    return res
tradeable=[r for r in rows if r["born"]!="born_past_stop"]
out["deciles_cost_r_ALL"]=deciles(rows)
out["deciles_cost_r_EXPASTSTOP"]=deciles(tradeable)
out["deciles_cost_usd_EXPASTSTOP"]=deciles(tradeable,"cost_usd")
out["deciles_cost_bp_EXPASTSTOP"]=deciles([r for r in tradeable if r["cost_bp_of_notional"] is not None],"cost_bp_of_notional")
out["deciles_true_cost_r_EXPASTSTOP"]=deciles([r for r in tradeable if r["true_total_cost_r"] is not None],"true_total_cost_r")
# correlation (pearson + spearman) cost_r vs gross_r
def pear(xs,ys):
    n=len(xs); mx=sum(xs)/n; my=sum(ys)/n
    sx=math.sqrt(sum((x-mx)**2 for x in xs)); sy=math.sqrt(sum((y-my)**2 for y in ys))
    if sx==0 or sy==0: return None
    return sum((x-mx)*(y-my) for x,y in zip(xs,ys))/(sx*sy)
def spear(xs,ys):
    def rk(v):
        idx=sorted(range(len(v)),key=lambda i:v[i]); r=[0]*len(v)
        i=0
        while i<len(idx):
            j=i
            while j+1<len(idx) and v[idx[j+1]]==v[idx[i]]: j+=1
            avg=(i+j)/2+1
            for k in range(i,j+1): r[idx[k]]=avg
            i=j+1
        return r
    return pear(rk(xs),rk(ys))
corr={}
for name,pop in (("ALL",rows),("EX_PAST_STOP",tradeable)):
    xs=[r["cost_r"] for r in pop if r["cost_r"] is not None and r["gross_r"] is not None]
    ys=[r["gross_r"] for r in pop if r["cost_r"] is not None and r["gross_r"] is not None]
    corr[name]={"n":len(xs),"pearson_cost_r_vs_gross_r":round(pear(xs,ys),5),"spearman":round(spear(xs,ys),5)}
    xs2=[r["cost_usd"] for r in pop if r["cost_usd"] is not None and r["gross_r"] is not None]
    corr[name]["pearson_cost_usd_vs_gross_r"]=round(pear(xs2,ys),5)
    corr[name]["spearman_cost_usd"]=round(spear(xs2,ys),5)
out["correlations"]=corr
# within-symbol deciles (removes symbol confound): pooled tertiles of within-symbol cost_r rank
bysym=collections.defaultdict(list)
for r in tradeable:
    if r["cost_r"] is not None and r["gross_r"] is not None: bysym[r["symbol"]].append(r)
tert={1:[],2:[],3:[]}
sym_spear={}
for s,v in bysym.items():
    v.sort(key=lambda r:r["cost_r"]); n=len(v)
    for i,r in enumerate(v):
        t=1 if i<n/3 else (2 if i<2*n/3 else 3)
        tert[t].append(r["gross_r"])
    if n>=50:
        sym_spear[s]=round(spear([r["cost_r"] for r in v],[r["gross_r"] for r in v]),4)
out["within_symbol_cost_tertiles_EXPASTSTOP"]={str(t):{"n":len(g),"gross_mean":round(sum(g)/len(g),5),
    "win_pct":round(100*sum(1 for x in g if x>0)/len(g),2)} for t,g in tert.items()}
out["within_symbol_spearman_cost_r_vs_gross_r"]=dict(sorted(sym_spear.items(),key=lambda x:x[1]))
out["born_census"]=collections.Counter(r["born"] for r in rows)
json.dump(out,open(os.path.join(DISC,"l5_PREDICT_V1.json"),"w"),indent=1)
print("=== FROZEN SPREAD CONSTANCY (distinct price values per symbol) ===")
for s,v in sorted(consts.items(),key=lambda x:-x[1]["n_distinct"])[:24]:
    print(f"{s:11s} n {v['n']:5d} distinct {v['n_distinct']:5d} modal {v['top'][0][0]:<14} share {v['top_share']:6.2f}%")
print("\n=== cost_r DECILES vs REALIZED GROSS (ex born_past_stop, n=%d) ==="%len(tradeable))
print(f"{'d':>2s} {'n':>5s} {'cost_r_lo':>10s} {'cost_r_hi':>10s} {'cost$mean':>10s} {'gross_mean':>11s} {'win%':>6s}")
for d in out["deciles_cost_r_EXPASTSTOP"]:
    print(f"{d['decile']:2d} {d['n']:5d} {d['cost_r_lo']:10.4f} {d['cost_r_hi']:10.4f} {d['mean_cost_usd']:10.1f} {d['gross_mean']:11.5f} {d['win_pct']:6.2f}")
print("\n=== cost_usd DECILES vs GROSS (ex past-stop) ===")
for d in out["deciles_cost_usd_EXPASTSTOP"]:
    print(f"{d['decile']:2d} {d['n']:5d} ${d['cost_usd_lo']:9.1f}-${d['cost_usd_hi']:9.1f} gross {d['gross_mean']:9.5f} win {d['win_pct']:5.2f}%")
print("\ncorr:",json.dumps(corr))
print("within-symbol tertiles:",json.dumps(out["within_symbol_cost_tertiles_EXPASTSTOP"]))
print("born:",dict(out["born_census"]))
