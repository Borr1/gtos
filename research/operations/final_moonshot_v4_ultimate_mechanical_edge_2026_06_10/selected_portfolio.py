"""Selected-portfolio: broad generation + select-what-worked-in-replay, forward.

Bar = positive in replay, forward. No red-team, no significance gauntlet, no
'safe' filter. Just: which (family x asset x side x session-bucket x regime)
cells were positive in TRAIN replay (2022-2024), applied FORWARD (2025-2026).
Price reaching entry = filled. Measure the forward portfolio R.
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
STOP_ATR = 2.5; H = 12
MIN_TRAIN_N = 20

def giveback(C,i,d,atr,c,n):
    end=min(i+H,n-1); return d*(C[end]-C[i])/atr-c

def main():
    trades=[]   # (cell, date, R)
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
            vdacc=sum(vd[i-2:i+1]);hb=f"h{int(T[i][11:13])//4*4:02d}"
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
                cell=(fam,ac,"L" if d>0 else "S",hb,trend)
                trades.append((cell,T[i][:10],giveback(C,i,d,atr,c,n)))
    # train-select-forward
    train=collections.defaultdict(list)
    for cell,date,R in trades:
        if date<"2025-01": train[cell].append(R)
    selected={cell for cell,v in train.items() if len(v)>=MIN_TRAIN_N and statistics.fmean(v)>0}
    # forward portfolio
    fdays=collections.defaultdict(float);fyear=collections.defaultdict(float);ftot=0.0;fn=0
    for cell,date,R in trades:
        if date>="2025-01" and cell in selected:
            fdays[date]+=R;fyear[date[:4]]+=R;ftot+=R;fn+=1
    days=sorted(fdays)
    vals=[fdays[x] for x in days]
    out={"schema_version":"selected_portfolio_v1","total_cells":len(train),"selected_cells":len(selected),
         "forward_trades":fn,"forward_days":len(days),
         "forward_total_R":round(ftot,1),"forward_per_day":round(ftot/max(1,len(days)),3),
         "forward_pos_days_pct":round(sum(1 for v in vals if v>0)/max(1,len(days)),3),
         "forward_by_year":{y:round(fyear[y],1) for y in sorted(fyear)},
         "broker_operation":False,"paid_api_or_vendor_call":False,"broker_runtime_change_status":False,
         "validation_result_status":False,"outcome_result_rows_status":False}
    (ROUTE/"ULTIMATE_SELECTED_PORTFOLIO.json").write_text(json.dumps(out,indent=1,sort_keys=True))
    print(json.dumps(out,sort_keys=True))

if __name__=="__main__": main()
