import sys,json,math
from collections import defaultdict,Counter
D="docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
sys.path.insert(0,D); import w0_ws
rows={w0_ws.key(r):r for r in w0_ws.load()}
REC={}
for rp in w0_ws.iter_rpaths():
    k=(rp["candidate_id"],rp["decision_time_utc"])
    if k not in rows: continue
    fav,adv,cl=rp["fav"],rp["adv"],rp["cls"]; tg=float(rows[k].get("policy_target_r") or 2.0)
    t=next((i for i,a in enumerate(adv) if a<=1e-12),None)
    if t is None: REC[k]=("never",None); continue
    x=max(0.0,-fav[t])
    if x>=1.0: REC[k]=("untakeable",None); continue
    sc=1/(1-x); r=None
    for j in range(t,len(fav)):
        T=fav[j]>=tg-1e-9; S=adv[j]<=-1.0+1e-9
        if T and S: r=-1.0;break
        if T: r=(tg+x)*sc;break
        if S: r=-1.0;break
    if r is None: r=max(-1.0,min((cl[-1]+x)*sc,(tg+x)*sc))
    REC[k]=("clean" if x<=0 else "reanchored",r)
def bk(v):
    g=[x for x in v if x is not None and math.isfinite(x)]
    if not g: return None
    n=len(g);w=[x for x in g if x>1e-3];l=[x for x in g if x<=1e-3]
    mw=sum(w)/len(w) if w else 0.;ml=sum(l)/len(l) if l else 0.
    return {"n":n,"gross_mean_R":sum(g)/n,"win_rate":len(w)/n,"mean_winner_R":mw,"mean_loser_R":ml,
            "breakeven_win_rate":((-ml)/(mw-ml)) if (mw-ml) else None}
byb=defaultdict(list)
for k,r in rows.items(): byb[str(r.get("final_blocker_class"))].append(k)
out={}
for b,ks in sorted(byb.items(),key=lambda x:-len(x[1])):
    unt=sum(1 for k in ks if REC[k][0]=="untakeable"); nev=sum(1 for k in ks if REC[k][0]=="never")
    out[b]={"n":len(ks),"share_of_pool":len(ks)/len(rows),"n_untakeable":unt,"share_untakeable":unt/len(ks),
      "n_never_touched":nev,
      "engine":bk([rows[k].get("gross_r") for k in ks]),
      "engine_net":bk([rows[k].get("opportunity_net_proxy_r") for k in ks]),
      "repaired_filled_only":bk([REC[k][1] for k in ks if REC[k][0] in ("clean","reanchored")]),
      "mean_expected_cost_r":sum(rows[k].get("expected_cost_r") or 0 for k in ks)/len(ks)}
json.dump(out,open(D+"/W0CAP_BLOCKER_V1.json","w"),indent=1,default=str)
print(f"{'blocker':28s} {'n':>6s} {'unt%':>6s} {'ENGgro':>8s} {'REPgro':>8s} {'nfill':>6s} {'win':>6s} {'be':>6s} {'cost':>6s}")
for b,v in out.items():
    e,r_=v["engine"],v["repaired_filled_only"]
    if r_ is None: print(f"{b:28s} {v['n']:6d} {v['share_untakeable']*100:6.2f} {e['gross_mean_R']:+8.4f}  (no filled rows)"); continue
    print(f"{b:28s} {v['n']:6d} {v['share_untakeable']*100:6.2f} {e['gross_mean_R']:+8.4f} {r_['gross_mean_R']:+8.4f} {r_['n']:6d} {r_['win_rate']:6.4f} {r_['breakeven_win_rate']:6.4f} {v['mean_expected_cost_r']:6.3f}")
