"""ROOT-CAUSE exit diagnostic: derive the optimal exit from the path data.

The recurring fact: moves touch +0.72R MFE avg but realize negative. The gap
is the exit. This maps, for the FULL 46-symbol H4 population 2022-2026, the
first-touch of every take-profit level vs every stop level -> the exact (TP,
stop) the data optimizes, the win rate and EV, the realized-vs-achievable gap,
and per-family MFE/MAE asymmetry. Intelligence, not pass/fail.
"""
import csv, json, statistics, sys, collections
from pathlib import Path
ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
COST = json.loads((ROUTE / "ULTIMATE_REAL_COST_MAP.json").read_text())
GCOST = COST.get("_global_median", 0.095)
D = REPO_ROOT / "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
TPS = [0.3,0.4,0.5,0.65,0.8,1.0,1.5,2.0]
STOPS = [0.5,0.75,1.0,1.5,2.0,2.5]
MAXBARS = 48  # 8 days

def main():
    # per trade: first-touch bar for each TP and each stop (R units, 1R=1xATR here)
    trades=[]   # (family, ac, cost, {tp:bar}, {stop:bar}, mfe, mae)
    for f in sorted(D.glob("*_H4.csv")):
        sym=f.name[:-7]; ac=ASSET_CLASS_BY_SYMBOL.get(sym)
        if ac is None: continue
        c=float(COST.get(ac,GCOST))
        rows=[(str(r["time"])[:19],float(r["open"]),float(r["high"]),float(r["low"]),float(r["close"]),float(r["volume"])) for r in csv.DictReader(open(f)) if r.get("close") and r.get("volume")]
        if len(rows)<250: continue
        n=len(rows);O=[x[1] for x in rows];Hh=[x[2] for x in rows];L=[x[3] for x in rows];C=[x[4] for x in rows];V=[x[5] for x in rows];T=[x[0] for x in rows]
        rng=[Hh[i]-L[i] for i in range(n)];tr=[0.0]*n
        for i in range(1,n): tr[i]=max(Hh[i]-L[i],abs(Hh[i]-C[i-1]),abs(L[i]-C[i-1]))
        vd=[(V[i]*(C[i]-O[i])/rng[i]) if rng[i]>0 else 0.0 for i in range(n)]
        prev=None
        for i in range(60,n-1):
            atr=sum(tr[i-13:i+1])/14
            if atr<=0: continue
            m20=sum(C[i-19:i+1])/20;m50=sum(C[i-49:i+1])/50
            trend="up" if m20>m50*1.001 else ("down" if m20<m50*0.999 else "flat")
            hi,lo=max(Hh[i-47:i+1]),min(L[i-47:i+1]);pos=(C[i]-lo)/(hi-lo) if hi>lo else .5
            posb="low" if pos<.25 else ("high" if pos>.75 else "mid")
            relv=V[i]/(sum(V[i-19:i+1])/20 or 1)
            eff=rng[i]/V[i] if V[i]>0 else 0;beff=sum((rng[k]/V[k] if V[k]>0 else 0) for k in range(i-19,i+1))/20
            absb=eff<=0.6*beff if beff>0 else False;expb=eff>=1.4*beff if beff>0 else False
            ph,pl=max(Hh[i-20:i]),min(L[i-20:i]);swh=Hh[i]>ph and C[i]<ph and relv>=1.5;swl=L[i]<pl and C[i]>pl and relv>=1.5
            vdacc=sum(vd[i-2:i+1])
            is_entry=(trend,posb,relv>=1.5,bool(swh or swl))!=prev;prev=(trend,posb,relv>=1.5,bool(swh or swl))
            if not is_entry: continue
            cands=[]
            if swl: cands.append((+1,"S1"))
            if swh: cands.append((-1,"S1"))
            if relv<=0.6 and trend=="down" and posb=="low": cands.append((+1,"S2"))
            if relv<=0.6 and trend=="up" and posb=="high": cands.append((-1,"S2"))
            if relv>=1.8 and expb and posb=="high" and C[i]>O[i]: cands.append((+1,"S3"))
            if relv>=1.8 and expb and posb=="low" and C[i]<O[i]: cands.append((-1,"S3"))
            if absb and posb=="low": cands.append((+1,"S4"))
            if absb and posb=="high": cands.append((-1,"S4"))
            if posb=="high" and vdacc<0: cands.append((-1,"S5"))
            if posb=="low" and vdacc>0: cands.append((+1,"S5"))
            for d,fam in cands:
                tp_bar={tp:None for tp in TPS}; st_bar={s:None for s in STOPS}; mfe=0.0;mae=0.0
                for j in range(i+1,min(i+MAXBARS,n)):
                    up=d*(Hh[j]-C[i])/atr if d>0 else d*(L[j]-C[i])/atr   # favorable extreme
                    dn=d*(L[j]-C[i])/atr if d>0 else d*(Hh[j]-C[i])/atr   # adverse extreme
                    fav=d*(Hh[j]-C[i])/atr if d>0 else d*(C[i]-L[j])/atr
                    adv=d*(C[i]-L[j])/atr if d>0 else d*(Hh[j]-C[i])/atr
                    mfe=max(mfe,fav);mae=max(mae,adv)
                    for tp in TPS:
                        if tp_bar[tp] is None and fav>=tp: tp_bar[tp]=j
                    for s in STOPS:
                        if st_bar[s] is None and adv>=s: st_bar[s]=j
                trades.append((fam,ac,c,tp_bar,st_bar,round(mfe,2),round(mae,2)))
    N=len(trades)
    # grid: for each (tp,stop) -> portfolio total R (first touch wins)
    grid={}
    for tp in TPS:
        for s in STOPS:
            if s<tp-1e-9 and s<0.5: pass
            tot=0.0;wins=0
            for fam,ac,c,tpb,stb,mfe,mae in trades:
                tb=tpb[tp];sb=stb[s]
                if tb is not None and (sb is None or tb<=sb): tot+=tp-c;wins+=1
                elif sb is not None: tot+=-s-c
                else: tot+=0.0-c  # neither touched in window: ~flat minus cost (approx)
            grid[(tp,s)]={"total_R":round(tot,0),"per_trade":round(tot/N,4),"win_rate":round(wins/N,3)}
    best=max(grid.items(), key=lambda kv: kv[1]["total_R"])
    # MFE/MAE per family
    fam=collections.defaultdict(lambda:{"mfe":[],"mae":[],"n":0})
    for f_,ac,c,tpb,stb,mfe,mae in trades:
        fam[f_]["mfe"].append(mfe);fam[f_]["mae"].append(mae);fam[f_]["n"]+=1
    fam_stats={k:{"n":v["n"],"med_mfe":round(statistics.median(v["mfe"]),3),"med_mae":round(statistics.median(v["mae"]),3),
                  "mfe_over_mae":round(statistics.median(v["mfe"])/(statistics.median(v["mae"]) or 1),3)} for k,v in fam.items()}
    allmfe=sorted(m for _,_,_,_,_,m,_ in trades); q=lambda a,p:a[min(len(a)-1,int(p*len(a)))]
    out={"schema_version":"exit_diagnostic_v1","trades":N,
         "mfe_dist":{"p25":q(allmfe,.25),"median":q(allmfe,.5),"p75":q(allmfe,.75),"p90":q(allmfe,.9)},
         "best_exit":{"tp":best[0][0],"stop":best[0][1],**best[1]},
         "grid":{f"tp{tp}_st{s}":grid[(tp,s)] for tp in TPS for s in STOPS},
         "by_family_asymmetry":fam_stats,
         "broker_operation":False,"paid_api_or_vendor_call":False,"broker_runtime_change_status":False,
         "validation_result_status":False,"outcome_result_rows_status":False}
    (ROUTE/"ULTIMATE_EXIT_DIAGNOSTIC.json").write_text(json.dumps(out,indent=1,sort_keys=True))
    print("trades",N,"| MFE median",out["mfe_dist"]["median"])
    print("BEST EXIT:",out["best_exit"])
    print("family asymmetry:",json.dumps(fam_stats))
    # top few exits
    tops=sorted(grid.items(),key=lambda kv:-kv[1]["total_R"])[:6]
    for (tp,s),v in tops: print(f"  TP{tp}/ST{s}: total {v['total_R']} per_trade {v['per_trade']} win {v['win_rate']}")

if __name__=="__main__": main()
