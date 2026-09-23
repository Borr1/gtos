import pickle, math, json, collections, numpy as np
d=pickle.load(open("panel_d1.pkl","rb")); panel=d["panel"]; dates=d["dates"]
syms=sorted({s for dt in dates for s in panel[dt]})
S={s:i for i,s in enumerate(syms)}; T=len(dates); N=len(syms)
LC=np.full((T,N),np.nan)
for ti,dt in enumerate(dates):
    for s,v in panel[dt].items(): LC[ti,S[s]]=math.log(v[3])
OWN={s:np.where(~np.isnan(LC[:,S[s]]))[0] for s in syms}

VOL=np.full((T,N),np.nan); HC=np.zeros((T,N),np.int32)
for s in syms:
    j=S[s]; ts=OWN[s]; lc=LC[ts,j]; HC[ts,j]=np.arange(1,len(ts)+1)
    r=np.diff(lc); n=60
    if len(r)>=n:
        cs=np.cumsum(np.insert(r,0,0.0)); cs2=np.cumsum(np.insert(r*r,0,0.0))
        m=(cs[n:]-cs[:-n])/n; m2=(cs2[n:]-cs2[:-n])/n
        sd=np.sqrt(np.maximum(m2-m*m,0.0)*n/(n-1))
        VOL[ts[n:],j]=sd          # at own-obs i (i>=n): vol of r[i-n..i-1] -> strictly past

def own_cum(lb,skip):
    """signal at own-obs i = lc[i-skip] - lc[i-skip-lb];  defined for i>=lb+skip"""
    out=np.full((T,N),np.nan); k=lb+skip
    for s in syms:
        j=S[s]; ts=OWN[s]; lc=LC[ts,j]; L=len(lc)
        if L<=k: continue
        out[ts[k:],j] = lc[k-skip:L-skip] - lc[k-skip-lb:L-skip-lb]
    return out
def own_fwd(hold):
    out=np.full((T,N),np.nan)
    for s in syms:
        j=S[s]; ts=OWN[s]; lc=LC[ts,j]; L=len(lc)
        if L<=hold: continue
        out[ts[:L-hold],j]=lc[hold:]-lc[:L-hold]
    return out
# sanity
sg=own_cum(21,0); jj=S["EURUSD"]; ts=OWN["EURUSD"]
assert abs(sg[ts[100],jj]-(LC[ts[100],jj]-LC[ts[79],jj]))<1e-12, "own_cum broken"
fw=own_fwd(21); assert abs(fw[ts[100],jj]-(LC[ts[121],jj]-LC[ts[100],jj]))<1e-12
print("sanity OK")

def cls(s):
    b=s[:-3]
    if s.endswith("USD") and b in {"BTC","ETH","LTC","XRP","ADA","DOT","DOGE","BCH","XLM","XMR","ETC","SOL","BNB","AVA","AAV","ALG","BAR","FET","GAL","GRT","ICP","IMX","LNK","MAN","NEO","NER","SAN","UNI","VEC","XTZ","MST"}: return "crypto"
    if s.endswith("_cash") or s in {"GER40","NAS100","SPX500","JP225","UK100"}: return "index"
    if s.endswith("_c") or s.startswith(("XAU","XAG","XPT","XPD","XCU")): return "commodity"
    if len(s)==6 and s.isupper() and s.isalpha(): return "fx"
    return "equity"
CL=np.array([cls(s) for s in syms])

def bt(lb,skip,hold,minhist,classes=None,exclude=None,nperm=2000,seed=11,start=None):
    SIG=own_cum(lb,skip); FW=own_fwd(hold)
    mask=np.ones(N,bool)
    if classes is not None: mask&=np.isin(CL,classes)
    if exclude is not None: mask&=~np.isin(CL,exclude)
    rets=[];ns=[];dts=[];keep=[]
    t=1
    while t<T:
        if start and dates[t]<start: t+=1; continue
        ok=(~np.isnan(SIG[t]))&(~np.isnan(FW[t]))&(~np.isnan(VOL[t]))&(VOL[t]>0)&(HC[t]>=minhist)&mask
        idx=np.where(ok)[0]
        if len(idx)>=20:
            sig=SIG[t,idx]/(VOL[t,idx]*math.sqrt(lb)); f=FW[t,idx]/VOL[t,idx]
            o=np.argsort(sig); q=max(3,len(idx)//5)
            rets.append(float(f[o[-q:]].mean()-f[o[:q]].mean())); ns.append(len(idx)); dts.append(dates[t])
            keep.append((sig,f,set(idx[o[-q:]]),set(idx[o[:q]])))
            t+=hold
        else: t+=1
    if len(rets)<5: return None
    a=np.array(rets); m=a.mean(); sd=a.std(ddof=1); tt=m/(sd/math.sqrt(len(a)))
    rng=np.random.default_rng(seed); pm=np.empty(nperm)
    for p in range(nperm):
        acc=0.0
        for (sig,f,_,_) in keep:
            n_=len(sig); pr=rng.permutation(n_); q=max(3,n_//5)
            acc+=f[pr[:q]].mean()-f[pr[q:2*q]].mean()      # random disjoint legs = correct null
        pm[p]=acc/len(keep)
    turn=[(len(keep[i][2]-keep[i-1][2])+len(keep[i][3]-keep[i-1][3]))/(len(keep[i][2])+len(keep[i][3])) for i in range(1,len(keep))]
    yr=collections.defaultdict(list)
    for dd,rr in zip(dts,rets): yr[dd[:4]].append(rr)
    return {"n_rebal":len(a),"mean_volnorm_per_rebal":float(m),"sd":float(sd),"t":float(tt),
            "ci95":[float(m-1.96*sd/math.sqrt(len(a))),float(m+1.96*sd/math.sqrt(len(a)))],
            "perm_p_two_sided":float((np.abs(pm-pm.mean())>=abs(m)).mean()),"perm_mean":float(pm.mean()),"perm_sd":float(pm.std(ddof=1)),
            "median_universe":int(np.median(ns)),"min_universe":int(min(ns)),"max_universe":int(max(ns)),
            "turnover_per_rebal":float(np.mean(turn)) if turn else None,
            "first":dts[0],"last":dts[-1],
            "pos_years":int(sum(1 for y in yr if np.mean(yr[y])>0)),"tot_years":len(yr),
            "by_year":{y:[round(float(np.mean(v)),4),len(v)] for y,v in sorted(yr.items())}}

CFG=[("XS_MOM_12_1",252,21,21,300),("XS_MOM_6_1",126,21,21,200),
     ("XS_MOM_1M",21,0,21,120),("XS_REV_5D",5,0,5,120),("XS_REV_1D",1,0,1,120)]
out={}
for name,lb,skip,hold,mh in CFG:
    for tag,kw in [("ALL",{}),("NOCRYPTO",{"exclude":["crypto"]}),("CRYPTO",{"classes":["crypto"]}),
                   ("FXCOMIDX",{"classes":["fx","commodity","index"]}),("EQUITY",{"classes":["equity"]}),
                   ("ALL_2021PLUS",{"start":"2021-01-01"})]:
        r=bt(lb,skip,hold,mh,**kw)
        if not r: continue
        out[f"{name}|{tag}"]=r
        print(f"{name:12s}|{tag:12s} n={r['n_rebal']:5d} univ={r['median_universe']:4d} m={r['mean_volnorm_per_rebal']:+.4f} t={r['t']:+.2f} permp={r['perm_p_two_sided']:.4f} turn={r['turnover_per_rebal']:.2f} yrs={r['pos_years']}/{r['tot_years']} {r['first']}..{r['last']}")
json.dump(out,open("xs_pilot_v4.json","w"),indent=1)
