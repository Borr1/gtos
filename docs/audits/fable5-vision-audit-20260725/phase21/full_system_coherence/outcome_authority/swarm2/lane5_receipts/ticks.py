import gzip, csv, math, json, sys
from collections import defaultdict
ROOT="/Users/borr/GTOSActive/vps-ticks-20260726/ftmo/"
SYMS=["EURUSD","XAUUSD","BTCUSD","US500_cash","USOIL_cash","GBPJPY"]
out={}
for sym in SYMS:
    p=f"{ROOT}FTMO_{sym}_ticks_20260618_to_20260726.csv.gz"
    n=0; hour_spread=defaultdict(lambda:[0.0,0]); hour_n=defaultdict(int)
    # minute bars of mid + OFI proxy
    minute=defaultdict(lambda:{"first":None,"last":None,"nb":0,"na":0,"n":0,"sp":0.0,"bu":0,"bd":0,"au":0,"ad":0})
    pb=pa=None
    try: f=gzip.open(p,"rt")
    except Exception as e: print("skip",sym,e); continue
    r=csv.reader(f); hdr=next(r)
    for row in r:
        try:
            t=int(row[0]); b=float(row[1]); a=float(row[2]); tm=int(row[5])
        except: continue
        if b<=0 or a<=0 or a<b: continue
        mid=(a+b)/2.0; sp=(a-b)/mid*1e4  # bps
        n+=1
        h=(t//3600)%24
        hour_spread[h][0]+=sp; hour_spread[h][1]+=1
        m=tm//60000
        d=minute[m]
        if d["first"] is None: d["first"]=mid
        d["last"]=mid; d["n"]+=1; d["sp"]+=sp
        if pb is not None:
            if b>pb: d["bu"]+=1
            elif b<pb: d["bd"]+=1
            if a>pa: d["au"]+=1
            elif a<pa: d["ad"]+=1
        pb,pa=b,a
    f.close()
    hs={h:(v[0]/v[1],v[1]) for h,v in sorted(hour_spread.items())}
    mins=sorted(minute)
    # predictive test: OFI proxy in minute m -> midpoint return over next K minutes
    def ic(K):
        xs=[];ys=[]
        for i in range(len(mins)-K-1):
            m0=mins[i]
            if mins[i+K+1]!=m0+K+1: continue   # require contiguous minutes
            d0=minute[m0]
            if d0["n"]<3: continue
            tot=d0["bu"]+d0["bd"]+d0["au"]+d0["ad"]
            if tot<3: continue
            ofi=((d0["bu"]+d0["ad"])-(d0["bd"]+d0["au"]))/tot
            p0=minute[m0]["last"]; p1=minute[mins[i+K+1]]["last"]
            if p0<=0 or p1<=0: continue
            xs.append(ofi); ys.append(math.log(p1/p0)*1e4)
        if len(xs)<200: return None
        mx=sum(xs)/len(xs); my=sum(ys)/len(ys)
        sxy=sum((x-mx)*(y-my) for x,y in zip(xs,ys)); sxx=sum((x-mx)**2 for x in xs); syy=sum((y-my)**2 for y in ys)
        if sxx<=0 or syy<=0: return None
        r=sxy/math.sqrt(sxx*syy); nn=len(xs)
        t=r*math.sqrt((nn-2)/max(1e-12,1-r*r))
        beta=sxy/sxx
        return {"n":nn,"ic":r,"t":t,"beta_bps_per_unit_ofi":beta,"mean_fwd_bps":my,"sd_fwd_bps":math.sqrt(syy/(nn-1))}
    out[sym]={"n_ticks":n,"n_minutes":len(mins),
              "spread_bps_by_broker_hour":hs,
              "spread_bps_median_hour_min":min(v[0] for v in hs.values()),
              "spread_bps_median_hour_max":max(v[0] for v in hs.values()),
              "ofi_ic":{f"fwd_{k}m":ic(k) for k in (1,2,5,15)}}
    print(sym,"ticks",n,"min",len(mins),"spread bps hour-min/max %.3f/%.3f"%(out[sym]["spread_bps_median_hour_min"],out[sym]["spread_bps_median_hour_max"]))
    for k,v in out[sym]["ofi_ic"].items():
        print("   ",k,json.dumps(v) if v else None)
    sys.stdout.flush()
json.dump(out,open("tick_micro.json","w"),indent=1)
