import pickle, math, json, collections, numpy as np
exec(open("xs4.py").read().split("CFG=[")[0])   # reuse loaders/bt
# vol-unit -> bps conversion
dailyvol={}
for s in syms:
    j=S[s]; ts=OWN[s]; lc=LC[ts,j]
    if len(lc)>100:
        r=np.diff(lc); dailyvol[s]=float(np.nanstd(r))
mv=float(np.median(list(dailyvol.values())))
print("median symbol daily vol (log):",round(mv,5),"=", round(mv*1e4,1),"bps/day")
out={}
TESTS=[
 ("XS_MOM_12_1|EQUITY",252,21,21,300,{"classes":["equity"]}),
 ("XS_MOM_12_1|ALL",252,21,21,300,{}),
 ("XS_MOM_12_1|EQ_2014_2023",252,21,21,300,{"classes":["equity"],"end":"2024-01-01"}),
 ("XS_MOM_12_1|EQ_2024PLUS",252,21,21,300,{"classes":["equity"],"start":"2024-01-01"}),
 ("XS_MOM_1M|NOCRYPTO",21,0,21,120,{"exclude":["crypto"]}),
 ("XS_MOM_1M|NOCRYPTO_pre2020",21,0,21,120,{"exclude":["crypto"],"end":"2020-01-01"}),
 ("XS_MOM_1M|NOCRYPTO_2020plus",21,0,21,120,{"exclude":["crypto"],"start":"2020-01-01"}),
 ("XS_REV_1D|FXONLY",1,0,1,120,{"classes":["fx"]}),
 ("XS_REV_1D|EQUITYONLY",1,0,1,120,{"classes":["equity"]}),
 ("XS_REV_1D|CRYPTOONLY",1,0,1,120,{"classes":["crypto"]}),
 ("XS_REV_1D|ALL_pre2020",1,0,1,120,{"end":"2020-01-01"}),
 ("XS_REV_1D|ALL_2020plus",1,0,1,120,{"start":"2020-01-01"}),
 ("XS_REV_5D|ALL",5,0,5,120,{}),
]
def bt2(lb,skip,hold,minhist,classes=None,exclude=None,nperm=1000,seed=11,start=None,end=None):
    SIG=own_cum(lb,skip); FW=own_fwd(hold)
    mask=np.ones(N,bool)
    if classes is not None: mask&=np.isin(CL,classes)
    if exclude is not None: mask&=~np.isin(CL,exclude)
    rets=[];ns=[];dts=[];keep=[]; t=1
    while t<T:
        if (start and dates[t]<start) or (end and dates[t]>=end): t+=1; continue
        ok=(~np.isnan(SIG[t]))&(~np.isnan(FW[t]))&(~np.isnan(VOL[t]))&(VOL[t]>0)&(HC[t]>=minhist)&mask
        idx=np.where(ok)[0]
        if len(idx)>=20:
            sig=SIG[t,idx]/(VOL[t,idx]*math.sqrt(lb)); f=FW[t,idx]/VOL[t,idx]
            o=np.argsort(sig); q=max(3,len(idx)//5)
            rets.append(float(f[o[-q:]].mean()-f[o[:q]].mean())); ns.append(len(idx)); dts.append(dates[t])
            keep.append((sig,f,set(idx[o[-q:]]),set(idx[o[:q]]),float(np.median(VOL[t,idx])))); t+=hold
        else: t+=1
    if len(rets)<5: return None
    a=np.array(rets); m=a.mean(); sd=a.std(ddof=1); tt=m/(sd/math.sqrt(len(a)))
    rng=np.random.default_rng(seed); pm=np.empty(nperm)
    for p in range(nperm):
        acc=0.0
        for (sig,f,_,_,_) in keep:
            n_=len(sig); pr=rng.permutation(n_); q=max(3,n_//5)
            acc+=f[pr[:q]].mean()-f[pr[q:2*q]].mean()
        pm[p]=acc/len(keep)
    turn=[(len(keep[i][2]-keep[i-1][2])+len(keep[i][3]-keep[i-1][3]))/(len(keep[i][2])+len(keep[i][3])) for i in range(1,len(keep))]
    medvol=float(np.median([k[4] for k in keep]))
    gross_bps_per_rebal = m*medvol*1e4      # vol-units * median daily vol -> log-return -> bps
    tno=float(np.mean(turn)) if turn else 1.0
    yr=collections.defaultdict(list)
    for dd,rr in zip(dts,rets): yr[dd[:4]].append(rr)
    return {"n_rebal":len(a),"mean_volnorm":float(m),"t":float(tt),
            "ci95_volnorm":[float(m-1.96*sd/math.sqrt(len(a))),float(m+1.96*sd/math.sqrt(len(a)))],
            "perm_p":float((np.abs(pm-pm.mean())>=abs(m)).mean()),
            "median_universe":int(np.median(ns)),"turnover":tno,
            "median_daily_vol_of_book":medvol,
            "gross_bps_per_rebalance":gross_bps_per_rebal,
            "breakeven_roundtrip_cost_bps_per_leg": gross_bps_per_rebal/(2*tno) if tno>0 else None,
            "hold_days":hold,"first":dts[0],"last":dts[-1],
            "pos_years":int(sum(1 for y in yr if np.mean(yr[y])>0)),"tot_years":len(yr),
            "by_year":{y:[round(float(np.mean(v)),4),len(v)] for y,v in sorted(yr.items())}}
for name,lb,skip,hold,mh,kw in TESTS:
    r=bt2(lb,skip,hold,mh,**kw)
    if not r: print(name,"-> insufficient"); continue
    out[name]=r
    print(f"{name:32s} n={r['n_rebal']:5d} u={r['median_universe']:4d} m={r['mean_volnorm']:+.4f} t={r['t']:+.2f} p={r['perm_p']:.4f} "
          f"gross={r['gross_bps_per_rebalance']:+8.2f}bps/{hold}d turn={r['turnover']:.2f} BE={r['breakeven_roundtrip_cost_bps_per_leg']:+7.2f}bps yrs={r['pos_years']}/{r['tot_years']}")
json.dump(out,open("xs_pilot_v5.json","w"),indent=1)
