"""Structural-geometry study: tight structural stop -> big R-multiple.

Owner thesis (confirmed by exit diagnostic): the favorable move is a fixed
price distance; tighten the stop to STRUCTURE (swing/prior-bar/OB proxy) so
the same move becomes 3-4R, cut losers fast, let winners run, be patient.

For all entries (H4 deep 2022-2026), for each STOP DEFINITION compute: risk in
pips & ATR, then first-touch of +2R/+3R/+4R (R=that risk) vs -1R stop, win
rates, portfolio R for TP2/TP3/runner, and TIME (median bars to target vs to
stop). Identifies the stop placement that maximizes captured R.
"""
import csv, json, statistics, sys, collections
from pathlib import Path
ROUTE=Path(__file__).resolve().parent; REPO_ROOT=ROUTE.parents[2]
sys.path.insert(0,str(REPO_ROOT))
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
COST=json.loads((ROUTE/"ULTIMATE_REAL_COST_MAP.json").read_text());GCOST=COST.get("_global_median",0.095)
D=REPO_ROOT/"data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
MAXBARS=60
STOP_DEFS=["swing5","swing10","priorbar","atr05","atr075"]
TARGETS=[2.0,3.0,4.0]

def main():
    agg={sd:{"n":0,"risk_atr":[],"risk_pips":[],"tot":{t:0.0 for t in TARGETS},
             "win":{t:0 for t in TARGETS},"bars_win":{t:[] for t in TARGETS},"bars_stop":[],
             "yr":{t:collections.defaultdict(float) for t in TARGETS}} for sd in STOP_DEFS}
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
                # structural stop candidates (price distance below/above entry)
                sdist={}
                sw5=min(L[i-5:i+1]) if d>0 else max(Hh[i-5:i+1])
                sw10=min(L[i-10:i+1]) if d>0 else max(Hh[i-10:i+1])
                pb=L[i] if d>0 else Hh[i]
                sdist["swing5"]=abs(entry-sw5)+0.1*atr
                sdist["swing10"]=abs(entry-sw10)+0.1*atr
                sdist["priorbar"]=abs(entry-pb)+0.1*atr
                sdist["atr05"]=0.5*atr
                sdist["atr075"]=0.75*atr
                for sd,risk in sdist.items():
                    if risk<=0 or risk>3.5*atr: continue   # skip degenerate/too-wide
                    a=agg[sd];a["n"]+=1;a["risk_atr"].append(risk/atr);a["risk_pips"].append(risk)
                    # first touch of targets (in risk units) vs stop (-1 risk)
                    tbars={t:None for t in TARGETS};stbar=None
                    for j in range(i+1,min(i+MAXBARS,n)):
                        fav=d*(Hh[j]-entry) if d>0 else d*(L[j]-entry)  # price favorable extreme
                        adv=d*(entry-L[j]) if d>0 else d*(Hh[j]-entry)
                        if stbar is None and adv>=risk: stbar=j
                        for t in TARGETS:
                            if tbars[t] is None and fav>=t*risk: tbars[t]=j
                        if stbar is not None: break  # stop ends the trade (pessimistic)
                    if stbar is not None: a["bars_stop"].append(stbar-i)
                    for t in TARGETS:
                        tb=tbars[t]
                        if tb is not None and (stbar is None or tb<stbar):
                            a["tot"][t]+=t-c;a["win"][t]+=1;a["bars_win"][t].append(tb-i);a["yr"][t][yr]+=t-c
                        elif stbar is not None:
                            a["tot"][t]+=-1-c;a["yr"][t][yr]+=-1-c
                        else:
                            a["tot"][t]+=-c;a["yr"][t][yr]+=-c
    med=lambda x: round(statistics.median(x),2) if x else None
    out={"schema_version":"structural_geometry_study_v1","entries":N,"stop_defs":{}}
    for sd in STOP_DEFS:
        a=agg[sd]
        if a["n"]<100: continue
        out["stop_defs"][sd]={"n":a["n"],"med_risk_atr":med(a["risk_atr"]),
            "med_bars_to_stop":med(a["bars_stop"]),
            "targets":{f"TP{t}":{"total_R":round(a["tot"][t],0),"per_trade":round(a["tot"][t]/a["n"],4),
                                 "win":round(a["win"][t]/a["n"],3),"med_bars_to_target":med(a["bars_win"][t]),
                                 "per_year":{y:round(v) for y,v in sorted(a["yr"][t].items())}} for t in TARGETS}}
    (ROUTE/"ULTIMATE_STRUCTURAL_GEOMETRY_STUDY.json").write_text(json.dumps(out,indent=1,sort_keys=True))
    print("entries",N)
    for sd,v in out["stop_defs"].items():
        print(f"\n{sd}: med_risk={v['med_risk_atr']}ATR med_bars_to_stop={v['med_bars_to_stop']}")
        for t,tv in v["targets"].items():
            print(f"  {t}: per_trade {tv['per_trade']:+.4f} win {tv['win']} bars_to_tgt {tv['med_bars_to_target']} | yr {tv['per_year']}")

if __name__=="__main__": main()
