"""w0-capture STEP 6: per-family repaired books + cost headroom."""
import sys,json,math,re
from collections import Counter,defaultdict
D="docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
sys.path.insert(0,D); import w0_ws
rows={w0_ws.key(r):r for r in w0_ws.load()}
cost_cols=[c for c in rows[next(iter(rows))].keys() if re.search(r'cost|spread|commission|slip|swap',c)]
REC={}
for rp in w0_ws.iter_rpaths():
    k=(rp["candidate_id"],rp["decision_time_utc"])
    if k not in rows: continue
    fav,adv,cl=rp["fav"],rp["adv"],rp["cls"]; tg=float(rows[k].get("policy_target_r") or 2.0)
    t=next((i for i,a in enumerate(adv) if a<=1e-12),None)
    if t is None: REC[k]=("never",0.0,None); continue
    x=max(0.0,-fav[t])
    if x>=1.0: REC[k]=("untakeable",x,None); continue
    sc=1.0/(1.0-x); r=None
    for j in range(t,len(fav)):
        T=fav[j]>=tg-1e-9; S=adv[j]<=-1.0+1e-9
        if T and S: r=-1.0; break
        if T: r=(tg+x)*sc; break
        if S: r=-1.0; break
    if r is None: r=max(-1.0,min((cl[-1]+x)*sc,(tg+x)*sc))
    REC[k]=("clean" if x<=0 else "reanchored",x,r)
def bk(v):
    g=[x for x in v if x is not None and math.isfinite(x)]
    if not g: return None
    n=len(g); w=[x for x in g if x>1e-3]; l=[x for x in g if x<=1e-3]
    mw=sum(w)/len(w) if w else 0.; ml=sum(l)/len(l) if l else 0.
    return {"n":n,"gross_mean_R":sum(g)/n,"win_rate":len(w)/n,"mean_winner_R":mw,"mean_loser_R":ml,
            "breakeven_win_rate":((-ml)/(mw-ml)) if (mw-ml) else None,"total_R":sum(g)}
out={"cost_columns_present":cost_cols}
CST=[rows[k].get("total_cost_r") for k in rows]
CST=[c for c in CST if isinstance(c,(int,float))]
out["frozen_total_cost_r"]={"n":len(CST),"mean":(sum(CST)/len(CST)) if CST else None}
fam=lambda k: rows[k].get("origin_family") or rows[k].get("route_family") or "?"
byf=defaultdict(list)
for k in rows: byf[fam(k)].append(k)
KIND=lambda k: REC[k][0]
out["per_family_repaired"]={}
for f,ks in sorted(byf.items(),key=lambda x:-len(x[1])):
    eng=bk([rows[k].get("gross_r") for k in ks])
    a1=bk([0.0 if KIND(k) in ("untakeable","never") else REC[k][2] for k in ks])
    a2=bk([REC[k][2] for k in ks if KIND(k) in ("clean","reanchored")])
    cst=[rows[k].get("total_cost_r") for k in ks if isinstance(rows[k].get("total_cost_r"),(int,float))]
    mc=(sum(cst)/len(cst)) if cst else None
    out["per_family_repaired"][f]={"engine":eng,"A1_all_rows":a1,"A2_filled_only":a2,
        "mean_frozen_cost_r":mc,"n_untakeable":sum(1 for k in ks if KIND(k)=="untakeable"),
        "n_reanchored":sum(1 for k in ks if KIND(k)=="reanchored"),
        "n_never":sum(1 for k in ks if KIND(k)=="never"),
        "A2_cost_headroom_R":(a2["gross_mean_R"] if a2 else None)}
allA2=bk([REC[k][2] for k in rows if KIND(k) in ("clean","reanchored")])
allA1=bk([0.0 if KIND(k) in ("untakeable","never") else REC[k][2] for k in rows])
out["pool"]={"engine":bk([rows[k].get("gross_r") for k in rows]),"A1":allA1,"A2_filled_only":allA2,
  "mean_frozen_cost_r":(sum(CST)/len(CST)) if CST else None,
  "trade_rate_A1":allA2["n"]/len(rows)}
json.dump(out,open(D+"/W0CAP_FINAL_V1.json","w"),indent=1,default=str)
print("cost cols:",cost_cols[:12])
print("frozen mean cost:",out["frozen_total_cost_r"])
print(f"{'family':32s} {'n':>5s} {'unt':>5s} {'ENG':>8s} {'A2filled':>9s} {'n_fill':>6s} {'win':>6s} {'be':>6s} {'W':>6s} {'L':>6s} {'cost':>6s}")
for f,v in out["per_family_repaired"].items():
    e,a2=v["engine"],v["A2_filled_only"]
    print(f"{f:32s} {e['n']:5d} {v['n_untakeable']:5d} {e['gross_mean_R']:+8.4f} {a2['gross_mean_R']:+9.4f} {a2['n']:6d} {a2['win_rate']:6.4f} {a2['breakeven_win_rate']:6.4f} {a2['mean_winner_R']:+6.3f} {a2['mean_loser_R']:+6.3f} {(v['mean_frozen_cost_r'] or 0):6.3f}")
print("POOL A2 filled-only:",{k:round(v,4) for k,v in allA2.items() if isinstance(v,float)})
print("POOL A1 all rows:",{k:round(v,4) for k,v in allA1.items() if isinstance(v,float)})
