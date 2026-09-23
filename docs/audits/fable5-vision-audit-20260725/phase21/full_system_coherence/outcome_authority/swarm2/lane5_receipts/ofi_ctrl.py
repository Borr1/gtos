import gzip, csv, math, json
from collections import defaultdict
ROOT="/Users/borr/GTOSActive/vps-ticks-20260726/ftmo/"
def load(sym):
    p=f"{ROOT}FTMO_{sym}_ticks_20260618_to_20260726.csv.gz"
    M=defaultdict(lambda:{"n":0,"bu":0,"bd":0,"au":0,"ad":0,"lastmid":None,"sumw":0.0,"wmid":0.0,"lastt":None,"firstmid":None})
    pb=pa=None
    with gzip.open(p,"rt") as f:
        r=csv.reader(f); next(r)
        for row in r:
            try: b=float(row[1]); a=float(row[2]); tm=int(row[5])
            except: continue
            if b<=0 or a<=0 or a<b: continue
            mid=(a+b)/2.0; m=tm//60000; d=M[m]
            if d["firstmid"] is None: d["firstmid"]=mid
            if d["lastt"] is not None:
                dt=max(0,min(60000,tm-d["lastt"])); d["sumw"]+=dt; d["wmid"]+=mid*dt
            d["lastt"]=tm; d["lastmid"]=mid; d["n"]+=1
            if pb is not None:
                if b>pb: d["bu"]+=1
                elif b<pb: d["bd"]+=1
                if a>pa: d["au"]+=1
                elif a<pa: d["ad"]+=1
            pb,pa=b,a
    return M
def corr(xs,ys):
    n=len(xs)
    if n<200: return None
    mx=sum(xs)/n; my=sum(ys)/n
    sxy=sum((x-mx)*(y-my) for x,y in zip(xs,ys)); sxx=sum((x-mx)**2 for x in xs); syy=sum((y-my)**2 for y in ys)
    if sxx<=0 or syy<=0: return None
    r=sxy/math.sqrt(sxx*syy); t=r*math.sqrt((n-2)/max(1e-12,1-r*r))
    return {"n":n,"ic":round(r,5),"t":round(t,3)}
OUT={}
for sym in ["US500_cash","BTCUSD","XAUUSD","EURUSD"]:
    M=load(sym); mins=sorted(M)
    res={}
    for label,gap,anchor in [("A_lastmid_gap0",0,"last"),("B_lastmid_gap1m",1,"last"),
                             ("C_twmid_gap0",0,"tw"),("D_twmid_gap1m",1,"tw"),
                             ("E_twmid_gap2m",2,"tw")]:
        for K in (1,5):
            xs=[];ys=[]
            for i in range(len(mins)-(gap+K+2)):
                m0=mins[i]
                # require contiguity across the whole window
                if mins[i+gap+K+1]!=m0+gap+K+1: continue
                d0=M[m0]
                if d0["n"]<3: continue
                tot=d0["bu"]+d0["bd"]+d0["au"]+d0["ad"]
                if tot<3: continue
                ofi=((d0["bu"]+d0["ad"])-(d0["bd"]+d0["au"]))/tot
                def px(m):
                    dd=M[m]
                    if anchor=="last": return dd["lastmid"]
                    return dd["wmid"]/dd["sumw"] if dd["sumw"]>0 else dd["lastmid"]
                p0=px(m0+gap); p1=px(m0+gap+K)
                if not p0 or not p1 or p0<=0 or p1<=0: continue
                xs.append(ofi); ys.append(math.log(p1/p0)*1e4)
            c=corr(xs,ys)
            if c: res[f"{label}|fwd{K}m"]=c
    OUT[sym]=res
    print("==",sym)
    for k,v in res.items(): print(f"   {k:24s} n={v['n']:6d} ic={v['ic']:+.5f} t={v['t']:+7.2f}")
json.dump(OUT,open("ofi_control.json","w"),indent=1)
