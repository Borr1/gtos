import numpy as np, pandas as pd, tickeng
T=tickeng.load('FTMO'); df=pd.read_pickle('lg_cov.pkl').reset_index(drop=True)
df=df[df.horizon_min.fillna(0)>0].reset_index(drop=True)
WS=[1,2,3,5,10,20]
res=[]
for tsym,g in df.groupby('tsym'):
    A=T[tsym]; t=A['t']
    for r in g.itertuples():
        d=1 if r.side=='LONG' else -1
        s0=int(np.searchsorted(t,r.min_utc,'right')); s1=int(np.searchsorted(t,r.min_utc+int(r.horizon_min),'right'))
        if s1-s0<2: continue
        bh,bl,ah,al,bo,ao,sp=(A[k][s0:s1] for k in ('bh','bl','ah','al','bo','ao','sp'))
        risk=r.risk_price; S=r.stop_price; TG=r.target_price; L=r.entry_price
        def walk(j0,fp):
            if j0>=len(bh): xp=float(bo[-1] if d>0 else ao[-1]); return ('TIME',d*(xp-fp)/risk)
            if d>0: hs=bl[j0:]<=S; ht=bh[j0:]>=TG
            else:   hs=ah[j0:]>=S; ht=al[j0:]<=TG
            iS=int(np.argmax(hs)) if hs.any() else 10**9
            iT=int(np.argmax(ht)) if ht.any() else 10**9
            if iS<=iT and iS<10**9: return ('STOP',d*(S-fp)/risk)
            if iT<10**9:            return ('TARGET',d*(TG-fp)/risk)
            xp=float(bo[-1] if d>0 else ao[-1]); return ('TIME',d*(xp-fp)/risk)
        row=dict(key=r.key,symbol=r.symbol,family=r.family,side=r.side,day=r.day,risk=risk,
                 comm_r=r.comm_r if hasattr(r,'comm_r') else r.commission_r, swap_r=r.swap_r,
                 hour=int(pd.Timestamp(r.decision_utc).hour))
        row['comm_r']=r.commission_r
        # pure market
        fpM=float(ao[0] if d>0 else bo[0]); stM,rM=walk(0,fpM); row['mkt_gross']=rM; row['mkt_state']=stM
        spmean=float(np.nanmean(sp))
        if d>0: elig=al<=L; thr=al<=L-spmean
        else:   elig=bh>=L; thr=bh>=L+spmean
        for tag,mask in (('t',elig),('q',thr)):
            fi=int(np.argmax(mask)) if mask.any() else 10**9
            for W in WS:
                if fi<W:                                    # passive fill inside the window
                    st,rr=walk(fi+1,L); row[f'pc{W}_{tag}']=rr; row[f'pc{W}_{tag}_mode']='PASSIVE'
                else:                                        # cross at minute W
                    j=min(W,len(bh)-1); fp=float(ao[j] if d>0 else bo[j])
                    st,rr=walk(j,fp); row[f'pc{W}_{tag}']=rr; row[f'pc{W}_{tag}_mode']='CROSS'
        res.append(row)
pd.DataFrame(res).to_pickle('walk2.pkl'); print('rows',len(res))
