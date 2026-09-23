"""(D) COUNTERFACTUAL GEOMETRY: re-walk the SAME entries with barriers scaled by k and horizon by k^2.
Tests whether the +0.031 R/trade fair-value edge is fixed in R (widening pays) or fixed in price (it does not).
Walked on M15 bars (the tape available for all five months). k=1 is the control against the sealed M1 result."""
import pandas as pd, numpy as np, gzip, pickle, os, json
BAR="/Users/borr/GTOSActive/vps-bars-20260727"
def load(sym):
    f=f"{BAR}/FTMO_{sym}_M15.csv.gz"
    if not os.path.exists(f): return None
    d=pd.read_csv(f,compression="gzip")
    bn=pd.to_datetime(d["time"],unit="s")
    d["t"]=(bn-pd.Timedelta(hours=7)).dt.tz_localize("America/New_York",ambiguous=False,
             nonexistent="shift_forward").dt.tz_convert("UTC")
    return d.sort_values("t").reset_index(drop=True)
rows=[]
for m in ['feb','apr','may','jun','jul']:
    for r in pickle.load(gzip.open(f'/private/tmp/laneG-walk/lg_{m}.pkl.gz','rb')):
        o=r.get('orig') or {}
        if not o.get('fill_time'): continue
        rows.append(dict(month=m,symbol=r['symbol'],side=r['side'],day=r['day'],
            fill_price=o['fill_price'],fill_time=o['fill_time'],risk=r['risk_price'],
            cost_r=r['cost_r'],spread_r=r['spread_r_row'],base_gross=o.get('gross'),
            base_state=o.get('state'),horizon_min=r['horizon_min']))
c=pd.DataFrame(rows); c['ft']=pd.to_datetime(c.fill_time,utc=True)
print("walkable MARKET rows:",len(c),flush=True)
KS=[1,2,4,8,16]
recs=[]
for sym,g in c.groupby('symbol'):
    b=load(sym)
    if b is None: print("  skip",sym,flush=True); continue
    bt=b.t.values.astype('datetime64[ns]'); hi=b.high.values; lo=b.low.values; cl=b.close.values
    g=g.sort_values('ft')
    st=np.searchsorted(bt,g.ft.values.astype('datetime64[ns]'),side='left')
    dr=np.where(g.side.values=='LONG',1.0,-1.0)
    fp=g.fill_price.values; rk=g.risk.values; H=g.horizon_min.values/15.0   # base horizon in M15 bars (8)
    for k in KS:
        stop=fp-dr*rk*k; targ=fp+dr*rk*2.0*k
        nb=np.maximum(1,np.round(H*k*k).astype(int))                        # horizon scales as k^2 (diffusive)
        gross=np.full(len(g),np.nan); state=np.empty(len(g),object)
        for i in range(len(g)):
            a=st[i]; z=min(len(b),a+nb[i])
            if a>=len(b) or z<=a: continue
            H_=hi[a:z]; L_=lo[a:z]
            if dr[i]>0: hs=L_<=stop[i]; ht=H_>=targ[i]
            else:       hs=H_>=stop[i]; ht=L_<=targ[i]
            si=np.argmax(hs) if hs.any() else 10**9; ti=np.argmax(ht) if ht.any() else 10**9
            if si==10**9 and ti==10**9:
                gross[i]=dr[i]*(cl[z-1]-fp[i])/(rk[i]*k); state[i]='TIME_STOP'
            elif si<ti:  gross[i]=-1.0; state[i]='STOP'
            elif ti<si:  gross[i]=+2.0; state[i]='TARGET'
            else:        gross[i]=np.nan; state[i]='AMBIG'     # same-bar: censor (matches engine rule)
        recs.append(pd.DataFrame(dict(symbol=sym,month=g.month.values,day=g.day.values,k=k,
            gross=gross,state=state,cost_r=g.cost_r.values,spread_r=g.spread_r.values,
            base_gross=g.base_gross.values,base_state=g.base_state.values)))
    print("  ok",sym,flush=True)
D=pd.concat(recs); D.to_pickle('geowalk.pkl')
print("\n"+"="*105)
print("COUNTERFACTUAL GEOMETRY.  cost_r scales as 1/k (cost is fixed in PRICE; risk grows k-fold).")
print("edge_k = gross_k + spread_r/k   (fair-value null for gross is -E[spread]/k)")
print(f"{'k':>3}{'n_resolved':>12}{'ambig%':>8}{'pT':>7}{'pS':>7}{'pX':>7}{'gross':>10}{'null':>9}{'EDGE':>9}{'cost_k':>9}{'NET_k':>9}")
tab=[]
for k in KS:
    d=D[(D.k==k)]; r=d[d.gross.notna()]
    if not len(r): continue
    amb=float((d.state=='AMBIG').mean())
    pT=float((r.state=='TARGET').mean()); pS=float((r.state=='STOP').mean()); pX=float((r.state=='TIME_STOP').mean())
    gross=r.gross.mean(); null=-r.spread_r.mean()/k; edge=gross-null
    costk=r.cost_r.mean()/k; net=gross-(costk-r.spread_r.mean()/k)   # net = gross - deductible_k
    net_full=edge-costk
    tab.append(dict(k=k,n=len(r),ambig=amb,pT=pT,pS=pS,pX=pX,gross=gross,null=null,edge=edge,cost=costk,net=net_full))
    print(f"{k:3d}{len(r):12d}{100*amb:7.1f}%{pT:7.3f}{pS:7.3f}{pX:7.3f}{gross:+10.4f}{null:+9.4f}{edge:+9.4f}{costk:9.4f}{net_full:+9.4f}")
json.dump(tab,open('geowalk_table.json','w'),indent=2,default=float)
print("\nInterpretation: if EDGE stays ~flat as k rises, the edge is fixed in R and widening pays.")
print("                if EDGE falls ~1/k, the edge is fixed in PRICE and widening cannot pay.")
