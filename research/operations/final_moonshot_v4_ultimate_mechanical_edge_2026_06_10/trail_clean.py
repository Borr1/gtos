"""CLEAN make-or-break test of trail_after_2R — explicit long/short price levels,
NO d-sign arithmetic (the bug class). Reports long & short SEPARATELY so any
residual sign error is visible. Tight 0.5ATR stop, arm at +2R, trail 1R behind
the favorable extreme. Pessimistic same-bar (stop wins ties). Real cost.
"""
import csv,json,statistics,sys,collections
from pathlib import Path
ROUTE=Path(__file__).resolve().parent;REPO_ROOT=ROUTE.parents[2];sys.path.insert(0,str(REPO_ROOT))
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
COST=json.loads((ROUTE/"ULTIMATE_REAL_COST_MAP.json").read_text());GCOST=COST.get("_global_median",0.095)
D=REPO_ROOT/"data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026";MAXBARS=80
STOP_ATR=0.5;ARM=2.0;TRAIL=1.0  # in R (R=0.5ATR)

def main():
    import math
    side=collections.defaultdict(lambda:{"n":0,"win":0,"tot":0.0,"yr":collections.defaultdict(float)})
    ac_tot=collections.defaultdict(lambda:[0,0.0])
    N=0
    for f in sorted(D.glob("*_H4.csv")):
        sym=f.name[:-7];ac=ASSET_CLASS_BY_SYMBOL.get(sym)
        if ac is None: continue
        c=float(COST.get(ac,GCOST))
        rows=[(str(r["time"])[:19],float(r["open"]),float(r["high"]),float(r["low"]),float(r["close"]),float(r["volume"])) for r in csv.DictReader(open(f)) if r.get("close") and r.get("volume")]
        if len(rows)<250: continue
        n=len(rows);O=[x[1] for x in rows];H=[x[2] for x in rows];L=[x[3] for x in rows];C=[x[4] for x in rows];V=[x[5] for x in rows];T=[x[0] for x in rows]
        tr=[0.0]*n
        for i in range(1,n): tr[i]=max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1]))
        rng=[H[i]-L[i] for i in range(n)];vd=[(V[i]*(C[i]-O[i])/rng[i]) if rng[i]>0 else 0.0 for i in range(n)]
        prev=None
        for i in range(60,n-1):
            atr=sum(tr[i-13:i+1])/14
            if atr<=0: continue
            m20=sum(C[i-19:i+1])/20;m50=sum(C[i-49:i+1])/50
            trend="up" if m20>m50*1.001 else("down" if m20<m50*0.999 else"flat")
            hi,lo=max(H[i-47:i+1]),min(L[i-47:i+1]);pos=(C[i]-lo)/(hi-lo) if hi>lo else .5
            posb="low" if pos<.25 else("high" if pos>.75 else"mid")
            relv=V[i]/(sum(V[i-19:i+1])/20 or 1);eff=rng[i]/V[i] if V[i]>0 else 0;beff=sum((rng[k]/V[k] if V[k]>0 else 0) for k in range(i-19,i+1))/20
            absb=eff<=0.6*beff if beff>0 else False;expb=eff>=1.4*beff if beff>0 else False
            ph,pl=max(H[i-20:i]),min(L[i-20:i]);swh=H[i]>ph and C[i]<ph and relv>=1.5;swl=L[i]<pl and C[i]>pl and relv>=1.5;vdacc=sum(vd[i-2:i+1])
            is_entry=(trend,posb,relv>=1.5,bool(swh or swl))!=prev;prev=(trend,posb,relv>=1.5,bool(swh or swl))
            if not is_entry: continue
            longs=[];shorts=[]
            if swl:longs.append(1)
            if swh:shorts.append(1)
            if relv<=0.6 and trend=="down" and posb=="low":longs.append(1)
            if relv<=0.6 and trend=="up" and posb=="high":shorts.append(1)
            if relv>=1.8 and expb and posb=="high" and C[i]>O[i]:longs.append(1)
            if relv>=1.8 and expb and posb=="low" and C[i]<O[i]:shorts.append(1)
            if absb and posb=="low":longs.append(1)
            if absb and posb=="high":shorts.append(1)
            if posb=="high" and vdacc<0:shorts.append(1)
            if posb=="low" and vdacc>0:longs.append(1)
            entry=C[i];risk=STOP_ATR*atr;yr=T[i][:4]
            for _ in longs:
                stop=entry-risk;arm=entry+ARM*risk;armed=False;mx=entry;r=None
                for j in range(i+1,min(i+MAXBARS,n)):
                    if L[j]<=stop: r=(stop-entry)/risk-c;break
                    if H[j]>mx:mx=H[j]
                    if not armed and H[j]>=arm:armed=True
                    if armed and L[j]<=mx-TRAIL*risk: r=((mx-TRAIL*risk)-entry)/risk-c;break
                if r is None: r=(C[min(i+MAXBARS,n)-1]-entry)/risk-c
                s=side["long"];s["n"]+=1;s["tot"]+=r;s["yr"][yr]+=r
                if r>0:s["win"]+=1
                ac_tot[ac][0]+=1;ac_tot[ac][1]+=r;N+=1
            for _ in shorts:
                stop=entry+risk;arm=entry-ARM*risk;armed=False;mn=entry;r=None
                for j in range(i+1,min(i+MAXBARS,n)):
                    if H[j]>=stop: r=(entry-stop)/risk-c;break
                    if L[j]<mn:mn=L[j]
                    if not armed and L[j]<=arm:armed=True
                    if armed and H[j]>=mn+TRAIL*risk: r=(entry-(mn+TRAIL*risk))/risk-c;break
                if r is None: r=(entry-C[min(i+MAXBARS,n)-1])/risk-c
                s=side["short"];s["n"]+=1;s["tot"]+=r;s["yr"][yr]+=r
                if r>0:s["win"]+=1
                ac_tot[ac][0]+=1;ac_tot[ac][1]+=r;N+=1
    out={"schema_version":"trail_clean_v1","entries":N,"geometry":"0.5ATR stop, arm +2R, trail 1R behind extreme, explicit two-sided",
         "by_side":{k:{"n":v["n"],"win":round(v["win"]/v["n"],3),"per_trade":round(v["tot"]/v["n"],4),
                       "per_year":{y:round(z) for y,z in sorted(v["yr"].items())}} for k,v in side.items()},
         "combined_per_trade":round(sum(v["tot"] for v in side.values())/N,4),
         "by_asset":{a:{"n":t[0],"per_trade":round(t[1]/t[0],4)} for a,t in sorted(ac_tot.items())}}
    (ROUTE/"ULTIMATE_TRAIL_CLEAN.json").write_text(json.dumps(out,indent=1,sort_keys=True))
    print(json.dumps({"entries":N,"combined_per_trade":out["combined_per_trade"]}))
    for k,v in out["by_side"].items(): print(f"  {k}: n={v['n']} win={v['win']} per_trade={v['per_trade']:+.4f} | yr {v['per_year']}")
    print("  by asset:",json.dumps(out["by_asset"]))
if __name__=="__main__": main()
