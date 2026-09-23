"""Structure-anchored geometry — stops/targets at MARKET STRUCTURE, not round numbers.

Owner principle: static 0.25ATR / 1.5R are arbitrary. Anchor the stop just
beyond the protective structure (the liquidity level / zone the entry reacts
from) and the target at the NEXT opposing liquidity (the draw). Let replay
derive the rules: how far beyond the zone before noise wicks it (buffer), and
how far the next-liquidity target naturally sits in R-units (is it 2R? 3R?
data, not a pretty number).

For each entry (shared detection): protective level = the swept/structural
extreme; STOP = protective_level -/+ buffer (sweep a grid of buffers in ATR).
TARGET = next opposing liquidity (prior swing high/low over lookback). Measure:
distance-to-stop (risk), distance-to-target in R, first-touch realized R, and
the natural R-to-next-liquidity distribution. Compare to static 0.5ATR/2R.
"""
import csv, json, statistics, sys, collections
from pathlib import Path
ROUTE=Path(__file__).resolve().parent; REPO_ROOT=ROUTE.parents[2]
sys.path.insert(0,str(REPO_ROOT))
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
COST=json.loads((ROUTE/"ULTIMATE_REAL_COST_MAP.json").read_text());GCOST=COST.get("_global_median",0.095)
D=REPO_ROOT/"data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
MAXBARS=60
BUFFERS=[0.05,0.10,0.25]      # ATR beyond the protective structure
TGT_LOOKBACK=[20,50]          # bars to find next opposing liquidity

def main():
    # structure-anchored: stop beyond swept/protective extreme; target = next liquidity
    res=collections.defaultdict(lambda:{"n":0,"tot":0.0,"win":0,"risk_atr":[],"tgt_R":[],"yr":collections.defaultdict(float),"bars_tgt":[]})
    natural_R=[]  # R-to-next-liquidity distribution (is target naturally ~2-3R?)
    N=0
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
            relv=V[i]/(sum(V[i-19:i+1])/20 or 1)
            eff=rng[i]/V[i] if V[i]>0 else 0;beff=sum((rng[k]/V[k] if V[k]>0 else 0) for k in range(i-19,i+1))/20
            absb=eff<=0.6*beff if beff>0 else False;expb=eff>=1.4*beff if beff>0 else False
            ph,pl=max(Hh[i-20:i]),min(L[i-20:i]);swh=Hh[i]>ph and C[i]<ph and relv>=1.5;swl=L[i]<pl and C[i]>pl and relv>=1.5
            vdacc=sum(vd[i-2:i+1])
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
                N+=1
                # PROTECTIVE structure = the local swing extreme the entry reacts from (last 5 bars)
                prot = min(L[i-5:i+1]) if d>0 else max(Hh[i-5:i+1])
                for buf in BUFFERS:
                    stop = prot - buf*atr if d>0 else prot + buf*atr
                    risk = abs(entry-stop)
                    if risk<=0.05*atr or risk>3.0*atr: continue
                    for tlb in TGT_LOOKBACK:
                        # TARGET = next opposing liquidity (prior swing high/low over lookback)
                        tgt = max(Hh[i-tlb:i]) if d>0 else min(L[i-tlb:i])
                        tgt_R = (d*(tgt-entry))/risk
                        if tgt_R<=0.3: continue   # liquidity already taken / too close
                        natural_R.append(round(tgt_R,2))
                        key=(f"buf{buf}",f"tgt{tlb}")
                        a=res[key];a["n"]+=1;a["risk_atr"].append(risk/atr);a["tgt_R"].append(tgt_R)
                        # first touch: target vs stop (pessimistic same-bar=stop)
                        tb=sb=None
                        for j in range(i+1,min(i+MAXBARS,n)):
                            adv=d*(entry-L[j]) if d>0 else d*(Hh[j]-entry)
                            fav=d*(Hh[j]-entry) if d>0 else d*(entry-L[j])
                            if sb is None and adv>=risk: sb=j
                            if tb is None and fav>=(tgt_R*risk): tb=j
                            if sb is not None: break
                        if sb is not None and (tb is None or sb<=tb): r=-1.0-c
                        elif tb is not None: r=tgt_R-c;a["win"]+=1;a["bars_tgt"].append(tb-i)
                        else: r=-c
                        a["tot"]+=r;a["yr"][yr]+=r
    med=lambda x: round(statistics.median(x),2) if x else None
    natural_R.sort();q=lambda p: natural_R[min(len(natural_R)-1,int(p*len(natural_R)))] if natural_R else None
    out={"schema_version":"structure_anchored_geometry_v1","entries":N,
         "natural_R_to_next_liquidity":{"p25":q(.25),"median":q(.5),"p75":q(.75),"p90":q(.9)},
         "configs":{}}
    for key,a in res.items():
        if a["n"]<200: continue
        out["configs"][f"{key[0]}_{key[1]}"]={"n":a["n"],"med_risk_atr":med(a["risk_atr"]),
            "med_target_R":med(a["tgt_R"]),"per_trade":round(a["tot"]/a["n"],4),"win":round(a["win"]/a["n"],3),
            "med_bars_to_target":med(a["bars_tgt"]),"per_year":{y:round(v) for y,v in sorted(a["yr"].items())}}
    (ROUTE/"ULTIMATE_STRUCTURE_ANCHORED_GEOMETRY.json").write_text(json.dumps(out,indent=1,sort_keys=True))
    print("entries",N,"| natural R-to-next-liquidity:",out["natural_R_to_next_liquidity"])
    for k,v in sorted(out["configs"].items(),key=lambda kv:-kv[1]["per_trade"]):
        print(f"  {k}: per_trade {v['per_trade']:+.4f} win {v['win']} risk {v['med_risk_atr']}ATR tgt {v['med_target_R']}R bars {v['med_bars_to_target']} | yr {v['per_year']}")

if __name__=="__main__": main()
