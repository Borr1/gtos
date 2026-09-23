"""Combined synthesis geometry: TIGHT stop + FAR liquidity target + TRAIL.
Stop = 0.5*ATR (tight). Ride toward next-liquidity (~5R). Trail after +1.5R
giving back 0.75R to bank the move if it reverses before liquidity. Real cost,
pessimistic same-bar, per year. The full owner-vision geometry."""
import csv,json,statistics,sys,collections
from pathlib import Path
ROUTE=Path(__file__).resolve().parent;REPO_ROOT=ROUTE.parents[2];sys.path.insert(0,str(REPO_ROOT))
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
COST=json.loads((ROUTE/"ULTIMATE_REAL_COST_MAP.json").read_text());GCOST=COST.get("_global_median",0.095)
D=REPO_ROOT/"data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026";MAXBARS=80
STOP_ATR=0.5;TRAIL_TRIG=1.5;TRAIL_GAP=0.75   # in R (R=0.5ATR)
def main():
    variants={"fixed2R":{},"fixed3R":{},"trail_to_liq":{}}
    for v in variants: variants[v]=collections.defaultdict(float)
    win=collections.defaultdict(int);tot=collections.defaultdict(float);N=0;bars=collections.defaultdict(list)
    for f in sorted(D.glob("*_H4.csv")):
        sym=f.name[:-7];ac=ASSET_CLASS_BY_SYMBOL.get(sym)
        if ac is None: continue
        c=float(COST.get(ac,GCOST))
        rows=[(str(r["time"])[:19],float(r["open"]),float(r["high"]),float(r["low"]),float(r["close"]),float(r["volume"])) for r in csv.DictReader(open(f)) if r.get("close") and r.get("volume")]
        if len(rows)<250: continue
        n=len(rows);O=[x[1] for x in rows];Hh=[x[2] for x in rows];L=[x[3] for x in rows];C=[x[4] for x in rows];V=[x[5] for x in rows];T=[x[0] for x in rows]
        tr=[0.0]*n
        for i in range(1,n): tr[i]=max(Hh[i]-L[i],abs(Hh[i]-C[i-1]),abs(L[i]-C[i-1]))
        rng=[Hh[i]-L[i] for i in range(n)];vd=[(V[i]*(C[i]-O[i])/rng[i]) if rng[i]>0 else 0.0 for i in range(n)]
        prev=None
        for i in range(60,n-1):
            atr=sum(tr[i-13:i+1])/14
            if atr<=0: continue
            m20=sum(C[i-19:i+1])/20;m50=sum(C[i-49:i+1])/50
            trend="up" if m20>m50*1.001 else("down" if m20<m50*0.999 else"flat")
            hi,lo=max(Hh[i-47:i+1]),min(L[i-47:i+1]);pos=(C[i]-lo)/(hi-lo) if hi>lo else .5
            posb="low" if pos<.25 else("high" if pos>.75 else"mid")
            relv=V[i]/(sum(V[i-19:i+1])/20 or 1);eff=rng[i]/V[i] if V[i]>0 else 0;beff=sum((rng[k]/V[k] if V[k]>0 else 0) for k in range(i-19,i+1))/20
            absb=eff<=0.6*beff if beff>0 else False;expb=eff>=1.4*beff if beff>0 else False
            ph,pl=max(Hh[i-20:i]),min(L[i-20:i]);swh=Hh[i]>ph and C[i]<ph and relv>=1.5;swl=L[i]<pl and C[i]>pl and relv>=1.5;vdacc=sum(vd[i-2:i+1])
            is_entry=(trend,posb,relv>=1.5,bool(swh or swl))!=prev;prev=(trend,posb,relv>=1.5,bool(swh or swl))
            if not is_entry: continue
            cands=[]
            if swl:cands.append(+1)
            if swh:cands.append(-1)
            if relv<=0.6 and trend=="down" and posb=="low":cands.append(+1)
            if relv<=0.6 and trend=="up" and posb=="high":cands.append(-1)
            if relv>=1.8 and expb and posb=="high" and C[i]>O[i]:cands.append(+1)
            if relv>=1.8 and expb and posb=="low" and C[i]<O[i]:cands.append(-1)
            if absb and posb=="low":cands.append(+1)
            if absb and posb=="high":cands.append(-1)
            if posb=="high" and vdacc<0:cands.append(-1)
            if posb=="low" and vdacc>0:cands.append(+1)
            entry=C[i];yr=T[i][:4]
            for d in cands:
                N+=1;risk=STOP_ATR*atr;stop=entry-d*risk
                liq=max(Hh[i-50:i]) if d>0 else min(L[i-50:i]);liqR=(d*(liq-entry))/risk
                # simulate path for each variant (pessimistic same-bar=stop)
                got={"fixed2R":None,"fixed3R":None,"trail_to_liq":None};tstop=stop;trailing=False;wb=None
                for j in range(i+1,min(i+MAXBARS,n)):
                    favp=Hh[j] if d>0 else L[j];advp=L[j] if d>0 else Hh[j]
                    fav=d*(favp-entry)/risk;adv=d*(entry-advp)/risk
                    # fixed targets (independent)
                    if got["fixed2R"] is None:
                        if adv>=1.0: got["fixed2R"]=-1.0-c
                        elif fav>=2.0: got["fixed2R"]=2.0-c
                    if got["fixed3R"] is None:
                        if adv>=1.0: got["fixed3R"]=-1.0-c
                        elif fav>=3.0: got["fixed3R"]=3.0-c
                    # trail-to-liquidity
                    if got["trail_to_liq"] is None:
                        cur=d*(C[j]-entry)/risk
                        if not trailing and cur>=TRAIL_TRIG: trailing=True
                        tlevel=(cur-TRAIL_GAP) if trailing else -1.0
                        if adv>=1.0 and not trailing: got["trail_to_liq"]=-1.0-c
                        elif trailing and (d*(advp-entry)/risk)<=tlevel: got["trail_to_liq"]=round(tlevel,2)-c
                        elif liqR>0.3 and fav>=liqR: got["trail_to_liq"]=liqR-c;wb=j-i
                for v in got:
                    r=got[v] if got[v] is not None else (d*(C[min(i+MAXBARS,n)-1]-entry)/risk-c)
                    variants[v][yr]+=r
                    if v=="trail_to_liq":
                        tot["trail"]+=r
                        if r>0: win["trail"]+=1
                        if wb: bars["trail"].append(wb)
    out={"schema_version":"combined_geometry_v1","entries":N,"stop":"0.5ATR","liquidity_lookback":50,
         "per_year":{v:{y:round(variants[v][y]) for y in sorted(variants[v])} for v in variants},
         "per_trade":{v:round(sum(variants[v].values())/N,4) for v in variants},
         "trail_win_rate":round(win["trail"]/N,3),"trail_med_bars":round(statistics.median(bars["trail"]),1) if bars["trail"] else None}
    (ROUTE/"ULTIMATE_COMBINED_GEOMETRY.json").write_text(json.dumps(out,indent=1,sort_keys=True))
    print("entries",N)
    for v in variants: print(f"  {v}: per_trade {out['per_trade'][v]:+.4f} | yr {out['per_year'][v]}")
    print("  trail win",out["trail_win_rate"],"med_bars",out["trail_med_bars"])
if __name__=="__main__": main()
