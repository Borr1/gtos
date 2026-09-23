import numpy as np, pandas as pd, tickeng, json, sys
T=tickeng.load('FTMO'); df=pd.read_pickle('lg_cov.pkl').reset_index(drop=True)
df=df[df.horizon_min.fillna(0)>0].reset_index(drop=True)
KS=[0.0,0.05,0.10,0.25,0.50]
res=[]
for tsym,g in df.groupby('tsym'):
    A=T[tsym]; t=A['t']
    for r in g.itertuples():
        d=1 if r.side=='LONG' else -1
        s0=int(np.searchsorted(t, r.min_utc, 'right'))          # first strictly-post-decision minute
        s1=int(np.searchsorted(t, r.min_utc+int(r.horizon_min), 'right'))
        if s1-s0<2: continue
        bh,bl,ah,al,bo,ao,sp=(A[k][s0:s1] for k in ('bh','bl','ah','al','bo','ao','sp'))
        risk=r.risk_price; S=r.stop_price; TG=r.target_price
        true_sp_entry=float(ao[0]-bo[0]); true_sp_mean=float(np.nanmean(sp))
        # ---- barrier walk helper: from index j0 (inclusive), fill price fp
        def walk(j0, fp):
            if j0>=len(bh): return ('NONE', np.nan, np.nan, 0)
            if d>0: hitS=bl[j0:]<=S; hitT=bh[j0:]>=TG
            else:   hitS=ah[j0:]>=S; hitT=al[j0:]<=TG
            iS=int(np.argmax(hitS)) if hitS.any() else 10**9
            iT=int(np.argmax(hitT)) if hitT.any() else 10**9
            amb=int(iS==iT and iS<10**9)
            if iS<=iT and iS<10**9:  return ('STOP', S, d*(S-fp)/risk, amb)
            if iT<10**9:             return ('TARGET', TG, d*(TG-fp)/risk, amb)
            xp = float(bo[-1] if d>0 else ao[-1]); return ('TIME', xp, d*(xp-fp)/risk, 0)
        # ---- MARKET arm (true tick prices)
        fpM = float(ao[0] if d>0 else bo[0])
        stM,xpM,rM,ambM = walk(0, fpM)
        row=dict(key=r.key, symbol=r.symbol, family=r.family, side=r.side, day=r.day, hour=int(pd.Timestamp(r.decision_utc).hour),
                 risk=risk, model_spread_px=r.spread_at_fill_price, true_spread_px=true_sp_entry, true_spread_mean_px=true_sp_mean,
                 model_spread_r=r.spread_r_row, true_spread_r=true_sp_entry/risk, comm_r=r.commission_r, swap_r=r.swap_r,
                 mkt_state=stM, mkt_gross=rM, mkt_amb=ambM, n_min=len(bh))
        # ---- gap-through measurement on the STOP (D)
        if stM=='STOP':
            if d>0:
                j=int(np.argmax(bl<=S)); row['stop_gap_px']=float(S-bl[j]); row['stop_open_px']=float(bo[j])
                row['stop_gap_open_px']=float(max(0.0, S-bo[j]))
            else:
                j=int(np.argmax(ah>=S)); row['stop_gap_px']=float(ah[j]-S); row['stop_open_px']=float(ao[j])
                row['stop_gap_open_px']=float(max(0.0, ao[j]-S))
            row['stop_bar_idx']=j
        # ---- PASSIVE arms
        for k in KS:
            lvl = r.entry_price - d*k*risk
            if d>0: elig=al<=lvl; thr=al<=lvl-true_sp_mean
            else:   elig=bh>=lvl; thr=bh>=lvl+true_sp_mean
            for tag,mask in (('t',elig),('q',thr)):
                if not mask.any():
                    row[f'lim{k}_{tag}_fill']=0; continue
                j=int(np.argmax(mask)); row[f'lim{k}_{tag}_fill']=1; row[f'lim{k}_{tag}_wait']=j
                st,xp,rr,am=walk(j+1, lvl)
                row[f'lim{k}_{tag}_state']=st; row[f'lim{k}_{tag}_gross']=rr
        res.append(row)
out=pd.DataFrame(res); out.to_pickle('walk.pkl'); print('walked', len(out))
print(out.mkt_state.value_counts().to_dict())
