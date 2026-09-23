"""Corrected Lo-MacKinlay z (the earlier run had a spurious n in delta_j) + Roll bid-ask-bounce bound."""
import pandas as pd, numpy as np, os, json
ROOT="/Users/borr/GTOSActive/vps-bars-20260727"
SYMS=["AUDJPY","AUDUSD","BTCUSD","CHFJPY","ETHUSD","EURGBP","EURJPY","EURUSD","GBPJPY","GBPUSD",
      "GER40","JP225","NAS100","NZDUSD","SPX500","UK100","UKOIL_cash","US30_cash","USDCAD",
      "USDCHF","USDJPY","USOIL_cash","XAGUSD","XAUUSD"]
def load(sym,tf):
    f=f"{ROOT}/FTMO_{sym}_{tf}.csv.gz"
    if not os.path.exists(f): return None
    d=pd.read_csv(f,compression="gzip")
    bn=pd.to_datetime(d["time"],unit="s")
    d["t"]=(bn-pd.Timedelta(hours=7)).dt.tz_localize("America/New_York",ambiguous=False,
             nonexistent="shift_forward").dt.tz_convert("UTC")
    return d.set_index("t")[["open","high","low","close"]].sort_index()
def vr_stat(r,q):
    r=np.asarray(r,float); r=r[np.isfinite(r)]; n=len(r)
    if n<20*q: return None
    x=r-r.mean(); var1=np.sum(x**2)/(n-1)
    if var1<=0: return None
    cs=np.concatenate([[0.0],np.cumsum(x)]); yq=cs[q:]-cs[:-q]
    m=q*(n-q+1)*(1-q/n); varq=np.sum(yq**2)/m; vr=varq/var1
    x2=x**2; den=(np.sum(x2))**2; theta=0.0
    for j in range(1,q):
        dj=np.sum(x2[j:]*x2[:-j])/den                     # <-- no spurious n
        theta+=((2*(q-j)/q)**2)*dj
    if theta<=0: return None
    return dict(vr=float(vr),z=float((vr-1)/np.sqrt(theta)),n=int(n),var1=float(var1))
def session(h):
    return "tokyo" if h<7 else ("london" if h<12 else ("newyork" if h<17 else "late"))
out=[]
for tf,qs in [("M15",[2,4,8,16]),("H4",[2,3,6]),("D1",[2,5])]:
    for sym in SYMS:
        d=load(sym,tf)
        if d is None or len(d)<500: continue
        d["lr"]=np.log(d["close"]).diff(); d=d.dropna(subset=["lr"])
        d=d[np.isfinite(d.lr)&(d.lr!=0)]
        if len(d)<500: continue
        d["rv"]=d.lr.rolling(50).std()
        d["reg"]=pd.qcut(d.rv.rank(method="first"),3,labels=["lo","mid","hi"])
        d["sess"]=d.index.hour.map(session)
        grps=[("ALL","ALL",d)]
        if tf!="D1":
            for s,g in d.groupby("sess",observed=True): grps.append((s,"ALL",g))
        for rg,g in d.groupby("reg",observed=True): grps.append(("ALL",str(rg),g))
        for q in qs:
            for s,rg,g in grps:
                st=vr_stat(g["lr"].values,q)
                if st is None: continue
                v=g["lr"].values; v=v[np.isfinite(v)]
                cov1=float(np.cov(v[:-1],v[1:])[0,1]) if len(v)>50 else np.nan
                ac1=float(np.corrcoef(v[:-1],v[1:])[0,1]) if len(v)>50 else np.nan
                # Roll bid-ask-bounce implied effective spread (relative units)
                roll_cov = 2*np.sqrt(-cov1) if (cov1==cov1 and cov1<0) else np.nan
                s_vr = np.sqrt(max(0.0,2*st['var1']*(1-st['vr'])/(1-1/q))) if st['vr']<1 else 0.0
                out.append(dict(tf=tf,symbol=sym,q=q,sess=s,regime=rg,ac1=ac1,cov1=cov1,
                                roll_spread_from_ac=roll_cov, roll_spread_from_vr=float(s_vr),**st))
        print(tf,sym,flush=True)
pd.DataFrame(out).to_csv("vr2_results.csv",index=False)
print("ROWS",len(out))
