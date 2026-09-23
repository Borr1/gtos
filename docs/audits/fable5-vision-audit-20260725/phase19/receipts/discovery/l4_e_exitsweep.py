#!/usr/bin/env python3
"""l4 step E: exit geometry under the OWNER'S FILL-HONEST contract.

For every candidate: fill at the first bar where price trades at/through entry_price
(cancel window = 120 = the engine's own pending expiry), then sweep
  target T in R, stop S in R, time-stop M in bars measured FROM THE FILL.
Booked two ways:
  same_size  : position size unchanged, so a tighter stop simply risks less
  risknorm   : position resized so the stop is exactly 1R  ->  r / |S|
Emits a per-candidate exit ladder so downstream cuts need no re-walk.
"""
import gzip, json, os, sys
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE)
import w0_ws

TGT=[0.25,0.5,0.75,1.0,1.25,1.5,1.75,2.0,2.5,3.0,4.0,5.0]
STP=[-0.5,-0.75,-1.0,-1.5,-2.0]
MB =[15,30,60,120]

anch={}
with gzip.open(os.path.join(HERE,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt") as fh:
    for l in fh:
        if l.strip():
            a=json.loads(l); anch[(a["candidate_id"],a["decision_time_utc"])]=a.get("mkt_r_prev_close")
fam={}
for r in w0_ws.iter_rows():
    fam[(r["candidate_id"],r["decision_time_utc"])]=(r["origin_family"],r["symbol"],r["session_bucket"])

def born(m):
    if m is None: return "unknown"
    if m<=-1+1e-12: return "past_stop"
    if m<-1e-12: return "marketable"
    if m<=1e-12: return "at_limit"
    return "resting"

OUT=os.path.join(HERE,"l4_EXITLADDER_V1.jsonl.gz")
n=0
with gzip.open(OUT,"wt") as out:
    for rp in w0_ws.iter_rpaths():
        k=(rp["candidate_id"],rp["decision_time_utc"])
        fav,adv,cls=rp["fav"],rp["adv"],rp["cls"]; nb=len(fav)
        fb=next((i for i in range(nb) if adv[i]<=1e-12),None)
        f_,s_,se_=fam.get(k,(None,None,None))
        rec={"cid":rp["candidate_id"],"dt":rp["decision_time_utc"],"fam":f_,"sym":s_,"ses":se_,
             "born":born(anch.get(k)),"fb":fb,"nb":nb}
        if fb is None:
            rec["tb"]=[None]*len(TGT); rec["sb"]=[None]*len(STP); rec["cl"]=[None]*len(MB); rec["clend"]=None
        else:
            tb=[None]*len(TGT); sb=[None]*len(STP)
            ti=0; si=0
            for i in range(fb,nb):
                f,a=fav[i],adv[i]
                while ti<len(TGT) and f>=TGT[ti]-1e-12:
                    tb[ti]=i-fb+1; ti+=1
                while si<len(STP) and a<=STP[si]+1e-12:
                    sb[si]=i-fb+1; si+=1
                if ti>=len(TGT) and si>=len(STP): break
            # ladder is monotone in level only if touches are recorded in order; fix by scanning
            # for any level whose first touch precedes an earlier-index level (cannot happen: levels sorted)
            rec["tb"]=tb; rec["sb"]=sb
            rec["cl"]=[cls[min(nb-1,fb+m-1)] for m in MB]
            rec["clend"]=cls[nb-1]
        out.write(json.dumps(rec)+"\n"); n+=1
sys.stderr.write("ladder rows %d -> %s\n"%(n,OUT))
