#!/usr/bin/env python3
"""l4 step H: THE CONTROL. Is the fill-instant penalty universal limit-order microstructure,
or is it specific to the direction the signal chose?

For every candidate, the SAME price level is used two ways:
  REAL     a limit on the signal's side  -> fills at the first bar whose adv <= 0
           (LONG: low <= entry) and books cls in the signal's sign.
  PLACEBO  a limit on the OPPOSITE side   -> fills at the first bar whose fav >= 0
           (LONG: high >= entry) and books -cls.
On born=at_limit rows the level IS the decision price, so the two orders are equally
marketable and the comparison is symmetric. If both are negative in their own sign the
penalty is microstructure; if only the real side is, the signal is choosing the wrong side.
Also reports the penalty in basis points and in true-spread multiples.
"""
import gzip, json, os, sys
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE)
import w0_ws
info={}
for r in w0_ws.iter_rows():
    info[(r["candidate_id"],r["decision_time_utc"])]=(r["risk_distance"],r["entry_price"],r["spread_r"],r["origin_family"],r["symbol"])
anch={}
with gzip.open(os.path.join(HERE,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt") as fh:
    for l in fh:
        if l.strip():
            a=json.loads(l); anch[(a["candidate_id"],a["decision_time_utc"])]=a.get("mkt_r_prev_close")
def born(m):
    if m is None: return "unknown"
    if m<=-1+1e-12: return "past_stop"
    if m<-1e-12: return "marketable"
    if m<=1e-12: return "at_limit"
    return "resting"
acc={}
def add(k,x,n=1):
    a=acc.setdefault(k,[0.0,0]); a[0]+=x; a[1]+=n
KS=[0,1,5,15,60]
for rp in w0_ws.iter_rpaths():
    k=(rp["candidate_id"],rp["decision_time_utc"])
    fav,adv,cls=rp["fav"],rp["adv"],rp["cls"]; nb=len(fav)
    b=born(anch.get(k)); rd,ep,sp,fm,sy=info.get(k,(None,None,None,None,None))
    fb=next((i for i in range(nb) if adv[i]<=1e-12),None)      # REAL side
    pb=next((i for i in range(nb) if fav[i]>=-1e-12),None)     # PLACEBO opposite side
    for kk in KS:
        if fb is not None and fb+kk<nb: add(("real",b,kk),cls[fb+kk])
        if pb is not None and pb+kk<nb: add(("plac",b,kk),-cls[pb+kk])
    if fb is not None:
        add(("realbar",b,0),fb+1)
    if pb is not None:
        add(("placbar",b,0),pb+1)
    # penalty in bp of price and in TRUE spread multiples (spread_r/7.3)
    if fb is not None and rd and ep:
        add(("bp",b,0), 10000.0*abs(cls[fb])*rd/ep if cls[fb]<0 else 0.0)
        add(("pen_r",b,0), cls[fb])
        if sp: add(("pen_over_truespread",b,0), cls[fb]/(sp/7.3) if sp>0 else 0.0)
out={}
print("  born        n_real   real k=0  k=1     k=5     k=15    k=60  | placebo k=0  k=1     k=5     k=15    k=60  | fillbar real/plac")
for b in ("at_limit","resting","marketable","past_stop"):
    row=[]
    for tag in ("real","plac"):
        for kk in KS:
            a=acc.get((tag,b,kk)); row.append(a[0]/a[1] if a and a[1] else float("nan"))
    nr=acc.get(("real",b,0),[0,0])[1]
    fbm=acc.get(("realbar",b,0)); pbm=acc.get(("placbar",b,0))
    print("  %-11s %7d %8.4f%8.4f%8.4f%8.4f%8.4f | %8.4f%8.4f%8.4f%8.4f%8.4f | %5.1f/%5.1f"%(
        b,nr,row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],
        fbm[0]/fbm[1] if fbm else 0, pbm[0]/pbm[1] if pbm else 0))
    out[b]={"n_real":nr,"real":{str(KS[i]):round(row[i],6) for i in range(5)},
            "placebo":{str(KS[i]):round(row[5+i],6) for i in range(5)},
            "mean_fill_bar_real":round(fbm[0]/fbm[1],3) if fbm else None,
            "mean_fill_bar_placebo":round(pbm[0]/pbm[1],3) if pbm else None}
    for t in ("bp","pen_r","pen_over_truespread"):
        a=acc.get((t,b,0))
        if a and a[1]: out[b][t]=round(a[0]/a[1],6)
print("\n  fill-instant penalty at the fill bar close:")
for b in ("at_limit","resting","marketable"):
    o=out[b]; print("   %-11s pen_r %8.4f   = %7.3f bp of price   = %6.2f x true spread(sp/7.3)"%(
        b,o.get("pen_r",0),o.get("bp",0),o.get("pen_over_truespread",0)))
json.dump(out,open(os.path.join(HERE,"L4_PLACEBO_V1.json"),"w"),indent=1)
