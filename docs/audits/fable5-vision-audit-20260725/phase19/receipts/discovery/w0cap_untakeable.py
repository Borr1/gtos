"""w0-capture STEP 3: characterise the untakeable population + per-family strict books."""
import sys, json, math
from collections import defaultdict, Counter
D="docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
sys.path.insert(0,D); import w0_ws
rows={w0_ws.key(r):r for r in w0_ws.load()}
fat,tb,strict,mfe_t={},{},{},{}
for rp in w0_ws.iter_rpaths():
    k=(rp["candidate_id"],rp["decision_time_utc"])
    if k not in rows: continue
    fav,adv,cl=rp["fav"],rp["adv"],rp["cls"]
    t=next((i for i,a in enumerate(adv) if a<=1e-12),None); tb[k]=t
    if t is None: continue
    fat[k]=fav[t]; mfe_t[k]=max(fav[t:])
    tg=float(rows[k].get("policy_target_r") or 2.0); r=None
    for j in range(t,len(fav)):
        T=fav[j]>=tg-1e-9; S=adv[j]<=-1.0+1e-9
        if T and S: r=-1.0; break
        if T: r=tg; break
        if S: r=-1.0; break
    strict[k]= r if r is not None else max(-1.0,min(cl[-1],tg))
def cls(k):
    t=tb.get(k)
    return "never" if t is None else ("gap" if fat[k]<0 else "clean")
def stat(v):
    v=sorted(x for x in v if x is not None and math.isfinite(x))
    if not v: return None
    n=len(v);q=lambda p:v[min(n-1,int(p*n))]
    return {"n":n,"mean":sum(v)/n,"p05":q(.05),"p25":q(.25),"median":q(.5),"p75":q(.75),"p95":q(.95)}
out={}
unt=[k for k in rows if cls(k)=="gap" and fat[k]<=-1.0]
cln=[k for k in rows if cls(k)=="clean"]
rd=lambda k:(abs(rows[k]["entry_price"]-rows[k]["stop_loss"])/abs(rows[k]["entry_price"])) if rows[k].get("entry_price") else None
out["risk_distance_pct_of_price"]={"untakeable":stat([rd(k) for k in unt]),"clean":stat([rd(k) for k in cln]),"all":stat([rd(k) for k in rows])}
out["untakeable_touch_bar"]=stat([tb[k]+1 for k in unt])
out["untakeable_by_family"]={}
fam=lambda k: rows[k].get("origin_family") or rows[k].get("route_family") or "?"
tot=Counter(fam(k) for k in rows); u=Counter(fam(k) for k in unt); gp=Counter(fam(k) for k in rows if cls(k)=="gap")
for f in sorted(tot,key=lambda x:-tot[x]):
    out["untakeable_by_family"][f]={"n_family":tot[f],"n_untakeable":u[f],"share_untakeable":u[f]/tot[f],"n_gap":gp[f],"share_gap":gp[f]/tot[f]}
sym=Counter(rows[k].get("symbol") for k in rows); us=Counter(rows[k].get("symbol") for k in unt)
out["untakeable_by_symbol"]={s:{"n":sym[s],"n_untakeable":us[s],"share":us[s]/sym[s]} for s in sorted(sym,key=lambda x:-us[x]/max(1,sym[x]))}
# per-family books: engine record vs strict-limit (gap+never scored 0)
def bk(ks,src):
    g=[src(k) for k in ks]; g=[x for x in g if x is not None and math.isfinite(x)]
    if not g: return None
    n=len(g); w=[x for x in g if x>1e-3]; l=[x for x in g if x<=1e-3]
    mw=sum(w)/len(w) if w else 0.; ml=sum(l)/len(l) if l else 0.
    return {"n":n,"gross_mean_R":sum(g)/n,"win_rate":len(w)/n,"mean_winner_R":mw,"mean_loser_R":ml,
            "breakeven_win_rate":(-ml)/(mw-ml) if (mw-ml) else None}
ENG=lambda k: rows[k].get("gross_r")
STR=lambda k: strict[k] if cls(k)=="clean" else 0.0
out["per_family"]={}
byf=defaultdict(list)
for k in rows: byf[fam(k)].append(k)
for f,ks in sorted(byf.items(),key=lambda x:-len(x[1])):
    out["per_family"][f]={"engine":bk(ks,ENG),"strict_limit_gap_and_never_as_zero":bk(ks,STR),
        "strict_filled_only":bk([k for k in ks if cls(k)=="clean"],lambda k:strict[k])}
json.dump(out,open(D+"/W0CAP_UNTAKEABLE_V1.json","w"),indent=1,default=str)
print("RISK DIST % of price:",{a:(None if b is None else {k:round(v,6) for k,v in b.items() if k in("n","p05","median","p95","mean")}) for a,b in out["risk_distance_pct_of_price"].items()})
print("UNTAKEABLE touch bar:",out["untakeable_touch_bar"])
print(f"{'family':32s} {'n':>5s} {'unt%':>6s} {'gap%':>6s} {'ENGgross':>9s} {'STRICTgross':>11s} {'STRwin':>7s} {'STRbe':>7s}")
for f,v in out["per_family"].items():
    uu=out["untakeable_by_family"][f]
    e=v["engine"]; s=v["strict_limit_gap_and_never_as_zero"]
    print(f"{f:32s} {e['n']:5d} {uu['share_untakeable']*100:6.2f} {uu['share_gap']*100:6.2f} {e['gross_mean_R']:+9.4f} {s['gross_mean_R']:+11.4f} {s['win_rate']:7.4f} {s['breakeven_win_rate']:7.4f}")
print("TOP untakeable symbols:",[(s,v["n"],round(v["share"],3)) for s,v in list(out["untakeable_by_symbol"].items())[:8]])
