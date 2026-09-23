#!/usr/bin/env python3
"""l4 step J: THE CLEAN SIGNAL TEST + the 0.92 calibration.

born=at_limit rows have entry_price == the decision-instant market price, so they carry
NO staleness, NO fill fiction and (unconditionally) NO fill selection: 98.5% of them are
already at the market.  Their unconditional mean mark at k bars after the decision is the
purest read of whether the signal's DIRECTION predicts anything at all.
"""
import gzip, json, os, sys
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE)
import w0_ws
info={}
for r in w0_ws.iter_rows():
    info[(r["candidate_id"],r["decision_time_utc"])]=(r["origin_family"],r["symbol"],r["session_bucket"],
        r["side"],r["execution_fill_probability"],r["spread_r"],r["cost_r"],r["commission_r"])
anch={}
with gzip.open(os.path.join(HERE,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt") as fh:
    for l in fh:
        if l.strip():
            a=json.loads(l); anch[(a["candidate_id"],a["decision_time_utc"])]=a.get("mkt_r_prev_close")
KS=[1,5,15,30,60,119]
acc={}
def add(k,x):
    a=acc.setdefault(k,[0.0,0,0]); a[0]+=x; a[1]+=1; a[2]+= (1 if x>0 else 0)
fillrate={}
for rp in w0_ws.iter_rpaths():
    k=(rp["candidate_id"],rp["decision_time_utc"])
    fav,adv,cls=rp["fav"],rp["adv"],rp["cls"]; nb=len(fav)
    m=anch.get(k)
    fm,sy,se,sd,ep,sp,cr,cm=info.get(k,(None,)*8)
    fb=next((i for i in range(nb) if adv[i]<=1e-12),None)
    d=fillrate.setdefault(sy,{"n":0,"f15":0,"f60":0,"f120":0,"p":0.0})
    d["n"]+=1; d["p"]+=(ep or 0)
    if fb is not None:
        if fb+1<=15: d["f15"]+=1
        if fb+1<=60: d["f60"]+=1
        if fb+1<=120: d["f120"]+=1
    if m is None or abs(m)>1e-12: continue          # at_limit only
    for kk in KS:
        if kk<nb:
            add(("ALL",kk),cls[kk]); add(("F|"+str(fm),kk),cls[kk])
            add(("S|"+str(sy),kk),cls[kk]); add(("X|"+str(se),kk),cls[kk])
            add(("D|"+str(sd),kk),cls[kk])
out={"KS":KS,"note":"unconditional close-based mark, born=at_limit only (entry==decision price)"}
def dump(pref,title,minn=150):
    keys=sorted({k[0] for k in acc if k[0].startswith(pref)})
    rowsout=[]
    for kk in keys:
        a=[acc.get((kk,x)) for x in KS]
        if not a[0] or a[0][1]<minn: continue
        rowsout.append({"key":kk[len(pref):],"n":a[0][1],
            **{"k%d"%KS[i]:round(a[i][0]/a[i][1],6) for i in range(len(KS)) if a[i]},
            "pos_share_k119":round(a[-1][2]/a[-1][1],5) if a[-1] else None})
    rowsout.sort(key=lambda d:-d.get("k119",-9))
    out[title]=rowsout
    print("\n"+title+"   (mean mark in R at k bars after the decision; at-market cohort)")
    print("  key                         n"+"".join("%9d"%k for k in KS))
    for d in rowsout:
        print("  %-24s %6d"%(d["key"][:24],d["n"])+"".join("%9.4f"%d.get("k%d"%k,0) for k in KS))
dump("ALL","overall",1)
dump("F|","by_family")
dump("S|","by_symbol")
dump("D|","by_side",1)
dump("X|","by_session",250)
# ---- 0.92 calibration
cal=[]
for sy,d in fillrate.items():
    if d["n"]<100: continue
    cal.append({"symbol":sy,"n":d["n"],"declared_p_mean":round(d["p"]/d["n"],5),
        "fill_15m":round(d["f15"]/d["n"],5),"fill_60m":round(d["f60"]/d["n"],5),
        "fill_120m":round(d["f120"]/d["n"],5),
        "err_at_120m":round(d["p"]/d["n"]-d["f120"]/d["n"],5),
        "err_at_15m":round(d["p"]/d["n"]-d["f15"]/d["n"],5)})
cal.sort(key=lambda d:d["err_at_120m"])
out["calibration_by_symbol"]=cal
e15=sum(abs(c["err_at_15m"]) for c in cal)/len(cal); e120=sum(abs(c["err_at_120m"]) for c in cal)/len(cal)
out["calibration_summary"]={"mean_abs_err_15m":round(e15,5),"mean_abs_err_120m":round(e120,5),
    "n_symbols":len(cal)}
print("\nFILL-PROBABILITY CALIBRATION  (declared execution_fill_probability vs measured)")
print("  symbol       n   declared   fill15m  fill60m  fill120m   err@120m")
for c in cal:
    print("  %-10s %5d %9.4f %9.4f %8.4f %9.4f %10.4f"%(c["symbol"],c["n"],c["declared_p_mean"],c["fill_15m"],c["fill_60m"],c["fill_120m"],c["err_at_120m"]))
print("  MEAN ABS ERROR: at 15m %.4f   at 120m %.4f  (n=%d symbols)"%(e15,e120,len(cal)))
json.dump(out,open(os.path.join(HERE,"L4_SIGNAL_V1.json"),"w"),indent=1)
