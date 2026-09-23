"""d3 — the analysis: five tables + the paired bootstrap, written to JSON and printed."""
from __future__ import annotations
import gzip, json, sys
from collections import defaultdict
import numpy as np
sys.path.insert(0,"/tmp/d3")
from d3_pool import load, pool, row, paired_signal, WINS

OUT={}
P=load("D3"); tot,dayg,dayn,dayN,perwin=pool(P)
OUT["n_rows_by_window"]={w:P[w]["n_rows"] for w in WINS}
OUT["n_rows_total"]=sum(P[w]["n_rows"] for w in WINS)

# ---- native stop width, measured on the roster itself
import d3_walk as W, d3_tape as D
nat=[]
for w,ind in D.WINDOWS.items():
    for r in W.load_window(w,ind):
        e=float(r["e"]); s=float(r["sl"])
        if e>0: nat.append(abs(e-s)/e*1e4)
nat=np.array(nat)
NAT_MED=float(np.median(nat)); NAT_MEAN=float(nat.mean())
OUT["native_stop_bps"]=dict(median=NAT_MED,mean=NAT_MEAN,p10=float(np.percentile(nat,10)),
                            p90=float(np.percentile(nat,90)),n=len(nat))
BPS={"native":NAT_MED,"25bps":25.,"50bps":50.,"100bps":100.,"200bps":200.,"400bps":400.}

# ---- TABLE B : the forward transplant grid
gridB={}
for sb in ["native","25bps","50bps","100bps","200bps","400bps"]:
    for tr in ["1.5","2.0","3.0","4.0","5.0"]:
        for H,hh in [(8,2),(32,8),(96,24),(288,72),(640,160),(1280,320)]:
            kr="REAL|%s|%s|%d|fixed"%(sb,tr,H); kp=kr.replace("REAL","PLACEBO")
            r=row(tot,kr); p=row(tot,kp)
            if r is None: continue
            sig=r["gross"]-p["gross"]
            gridB["%s|%s|%dh"%(sb,tr,hh)]=dict(
                n=r["n"],gross=r["gross"],placebo_gross=p["gross"],signal=sig,
                cost=r["cost"],net=r["net"],wr=r["wr"],hold_h=r["hold_h"],nights=r["nights"],
                p_stop=r["p_stop"],p_target=r["p_tgt"],p_horizon=r["p_hor"],
                gross_bps=r["gross"]*BPS[sb],signal_bps=sig*BPS[sb],cost_bps=r["cost"]*BPS[sb],
                net_bps=r["net"]*BPS[sb],
                windows_net_positive=sum(1 for w in WINS if perwin[kr].get(w,{}).get("net",0)>0),
                windows_signal_positive=sum(1 for w in WINS
                    if perwin[kr].get(w,{}).get("gross",0)-perwin[kp].get(w,{}).get("gross",0)>0))
        for H,hh in [(8,2),(1280,320)]:
            kr="REAL|%s|be2_4|%d|be_runner"%(sb,H); kp=kr.replace("REAL","PLACEBO")
            r=row(tot,kr); p=row(tot,kp)
            if r is None: continue
            sig=r["gross"]-p["gross"]
            gridB["%s|be2_4|%dh"%(sb,hh)]=dict(n=r["n"],gross=r["gross"],placebo_gross=p["gross"],
                signal=sig,cost=r["cost"],net=r["net"],wr=r["wr"],hold_h=r["hold_h"],
                nights=r["nights"],p_stop=r["p_stop"],p_target=r["p_tgt"],p_horizon=r["p_hor"],
                gross_bps=r["gross"]*BPS[sb],signal_bps=sig*BPS[sb],cost_bps=r["cost"]*BPS[sb],
                net_bps=r["net"]*BPS[sb],
                windows_net_positive=sum(1 for w in WINS if perwin[kr].get(w,{}).get("net",0)>0),
                windows_signal_positive=sum(1 for w in WINS
                    if perwin[kr].get(w,{}).get("gross",0)-perwin[kp].get(w,{}).get("gross",0)>0))
OUT["forward_transplant_grid"]=gridB
best_net=max(gridB.items(),key=lambda kv: kv[1]["net"])
best_sig=max(gridB.items(),key=lambda kv: kv[1]["signal"])
OUT["forward_best_net_cell"]={"cell":best_net[0],**best_net[1]}
OUT["forward_best_signal_cell"]={"cell":best_sig[0],**best_sig[1]}
OUT["forward_cells_net_positive"]=sum(1 for v in gridB.values() if v["net"]>0)
OUT["forward_cells_total"]=len(gridB)

# ---- paired bootstrap on the decision cells
BOOT={}
for cell,(sb,tr,H) in {
  "shipped_native_2R_2h":("native","2.0",8),
  "native_2R_320h":("native","2.0",1280),
  "sub_xvol_shape_3R_320h_nativestop":("native","3.0",1280),
  "crypto_shape_4R_320h_nativestop":("native","4.0",1280),
  "cryptoscale_4R_320h_400bps":("400bps","4.0",1280),
  "subxvolscale_3R_320h_200bps":("200bps","3.0",1280),
  "submid_shape_3R_320h_50bps":("50bps","3.0",1280),
  "cheapest_toll_2R_2h_400bps":("400bps","2.0",8),
}.items():
    kr="REAL|%s|%s|%d|fixed"%(sb,tr,H); kp=kr.replace("REAL","PLACEBO")
    BOOT[cell]=dict(paired_signal=paired_signal(dayg,dayN,kr,kp),
                    **{k:v for k,v in row(tot,kr).items()})
OUT["paired_bootstrap"]=BOOT

# ---- horizon accumulation curve, broad family
curve={}
for sb in ["native","50bps","100bps","200bps","400bps"]:
    row_=[]
    for H,hh in [(8,2),(32,8),(96,24),(288,72),(640,160),(1280,320)]:
        kr="REAL|%s|3.0|%d|fixed"%(sb,H); kp=kr.replace("REAL","PLACEBO")
        r=row(tot,kr); p=row(tot,kp)
        row_.append(dict(hours=hh,signal=r["gross"]-p["gross"],signal_bps=(r["gross"]-p["gross"])*BPS[sb],
                         gross=r["gross"],net=r["net"]))
    curve[sb]=row_
OUT["broad_horizon_curve_target3R"]=curve

# ---- per-family at the two ends
fam=defaultdict(lambda: defaultdict(float))
for w in WINS:
    for k,v in P[w]["families"].items():
        for f,x in v.items(): fam[k][f]+=x
FAMT={}
for k,v in fam.items():
    if v["n"]<1: continue
    FAMT[k]=dict(n=int(v["n"]),gross=v["sum_gross"]/v["n"],cost=v["sum_cost"]/v["n"],net=v["sum_net"]/v["n"])
famrows={}
for f in ("displacement_continuation","liquidity_sweep_reclaim","structural_distance_extreme",
          "volatility_compression_expansion","session_open_range_break","regime_transition_break",
          "cross_asset_lead_lag"):
    d={}
    for lbl,(sb,tr,H) in {"shipped_2R_2h":("native","2.0",8),
                          "live_shape_3R_320h":("native","3.0",1280),
                          "wide_3R_320h_200bps":("200bps","3.0",1280)}.items():
        kr="REAL|%s|%s|%d|fixed||%s"%(sb,tr,H,f); kp=kr.replace("REAL","PLACEBO")
        a=FAMT.get(kr); b=FAMT.get(kp)
        if a: d[lbl]=dict(n=a["n"],gross=a["gross"],net=a["net"],
                          signal=a["gross"]-(b["gross"] if b else 0.0))
    famrows[f]=d
OUT["per_family"]=famrows
json.dump(OUT,open("/tmp/d3/D3_ANALYSIS.json","w"),indent=1)
print("native stop bps median %.3f mean %.3f  n=%d"%(NAT_MED,NAT_MEAN,len(nat)))
print("total rows walked (per arm, per cell): %d"%OUT["n_rows_total"])
print("cells with net>0: %d of %d"%(OUT["forward_cells_net_positive"],OUT["forward_cells_total"]))
print("best net cell:", best_net[0], "net %.5f"%best_net[1]["net"], "gross %.5f"%best_net[1]["gross"],
      "signal %.5f"%best_net[1]["signal"], "windows net+ %d/8"%best_net[1]["windows_net_positive"])
print("best signal cell:", best_sig[0], "signal %.5f"%best_sig[1]["signal"], "net %.5f"%best_sig[1]["net"])
