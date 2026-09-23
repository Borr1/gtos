"""w0-capture STEP 5: re-anchored fill, the engine's OWN documented contract.

v4_timewarp_simulated_live_research_loop.py:54264-54268 --
  "A marketable limit is not a resting order in replay. The requested limit is the worst
   acceptable price; the effective fill is the decision-time market price."

If the limit is already through, the true fill E' is x*d past E toward the stop
(x = -fav_at_touch > 0).  Keeping the ORIGINAL stop and target PRICES:
      d'  = (1-x)*d                       (true risk of the trade you actually got)
      R'(bar) = (fav(bar)+x)/(1-x)        (exact algebraic restatement, no new data)
      target'  = (target+x)/(1-x)         stop' = -1  (same bar, larger R multiple)
x >= 1  =>  the stop price is already breached at the fill bar: NO TRADE EXISTS.
"""
import sys,json,math
from collections import Counter,defaultdict
D="docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
sys.path.insert(0,D); import w0_ws
rows={w0_ws.key(r):r for r in w0_ws.load()}
REC={}
for rp in w0_ws.iter_rpaths():
    k=(rp["candidate_id"],rp["decision_time_utc"])
    if k not in rows: continue
    fav,adv,cl=rp["fav"],rp["adv"],rp["cls"]
    tg=float(rows[k].get("policy_target_r") or 2.0)
    t=next((i for i,a in enumerate(adv) if a<=1e-12),None)
    if t is None: REC[k]=("never",None,None,None,None); continue
    x=-fav[t]
    if x<0: x=0.0
    if x>=1.0: REC[k]=("untakeable",x,None,None,None); continue
    kind="clean" if x<=0.0 else "reanchored"
    sc=1.0/(1.0-x)
    r=None; why=None
    for j in range(t,len(fav)):
        T=fav[j]>=tg-1e-9; S=adv[j]<=-1.0+1e-9
        if T and S: r,why=-1.0,"same_bar_conservative_stop"; break
        if T: r,why=(tg+x)*sc,"target"; break
        if S: r,why=-1.0,"stop_1R"; break
    if r is None:
        r=max(-1.0,min((cl[-1]+x)*sc,(tg+x)*sc)); why="mark_at_horizon"
    REC[k]=(kind,x,r,why,(1.0-x))
def bk(vals):
    g=[v for v in vals if v is not None and math.isfinite(v)]
    if not g: return None
    n=len(g); w=[v for v in g if v>1e-3]; l=[v for v in g if v<=1e-3]
    mw=sum(w)/len(w) if w else 0.; ml=sum(l)/len(l) if l else 0.
    return {"n":n,"gross_mean_R":sum(g)/n,"win_rate":len(w)/n,"mean_winner_R":mw,"mean_loser_R":ml,
            "payoff":(mw/-ml) if ml else None,"breakeven_win_rate":((-ml)/(mw-ml)) if (mw-ml) else None,
            "total_R":sum(g)}
out={}
KIND=lambda k: REC[k][0]
out["fill_taxonomy"]=dict(Counter(KIND(k) for k in rows))
ENG=lambda k: rows[k].get("gross_r")
# arms
def arm(f): return bk([f(k) for k in rows])
out["A0_engine_record"]=arm(ENG)
out["A1_reanchored_untakeable_and_never_scored_zero"]=arm(
    lambda k: 0.0 if KIND(k) in ("untakeable","never") else REC[k][2])
out["A2_reanchored_filled_only"]=bk([REC[k][2] for k in rows if KIND(k) in ("clean","reanchored")])
out["A3_clean_only_filled"]=bk([REC[k][2] for k in rows if KIND(k)=="clean"])
out["A4_reanchored_only"]=bk([REC[k][2] for k in rows if KIND(k)=="reanchored"])
CAP=0.8
out["A5_reanchor_capped_x_le_0.8_rest_zero"]=arm(
    lambda k: (REC[k][2] if (KIND(k)=="clean" or (KIND(k)=="reanchored" and REC[k][1]<=CAP)) else 0.0))
out["A6_untakeable_only_engine"]=bk([ENG(k) for k in rows if KIND(k)=="untakeable"])
out["A7_never_only_engine"]=bk([ENG(k) for k in rows if KIND(k)=="never"])
# leverage implied by re-anchoring
xs=sorted(REC[k][1] for k in rows if KIND(k)=="reanchored")
n=len(xs); q=lambda p: xs[min(n-1,int(p*n))]
out["reanchor_x_dist"]={"n":n,"mean":sum(xs)/n,"p25":q(.25),"median":q(.5),"p75":q(.75),"p90":q(.9),"p95":q(.95),"max":xs[-1]}
out["reanchor_size_multiplier_1_over_1_minus_x"]={"median":1/(1-q(.5)),"p90":1/(1-q(.9)),"p95":1/(1-q(.95))}
out["exit_reasons_A1"]=dict(Counter(REC[k][3] for k in rows if KIND(k) in ("clean","reanchored")))
# decomposition, R per pool trade
e=out["A0_engine_record"]["gross_mean_R"]
out["DECOMPOSITION_R_per_pool_trade"]={
  "engine_record":e,
  "C1_drop_untakeable_3699": -out["A6_untakeable_only_engine"]["total_R"]/len(rows),
  "C2_drop_never_touched_phantom": -out["A7_never_only_engine"]["total_R"]/len(rows),
  "C3_reanchor_remaining_gap_rows": out["A1_reanchored_untakeable_and_never_scored_zero"]["gross_mean_R"]-e
      +out["A6_untakeable_only_engine"]["total_R"]/len(rows)+out["A7_never_only_engine"]["total_R"]/len(rows),
  "TOTAL_C_entry_contract": out["A1_reanchored_untakeable_and_never_scored_zero"]["gross_mean_R"]-e}
json.dump(out,open(D+"/W0CAP_REANCHOR_V1.json","w"),indent=1,default=str)
print("TAXONOMY:",out["fill_taxonomy"])
for a in ["A0_engine_record","A1_reanchored_untakeable_and_never_scored_zero","A2_reanchored_filled_only",
          "A3_clean_only_filled","A4_reanchored_only","A5_reanchor_capped_x_le_0.8_rest_zero"]:
    v=out[a]; print(f"{a:48s} n={v['n']:6d} gross={v['gross_mean_R']:+.4f} win={v['win_rate']:.4f} be={v['breakeven_win_rate']:.4f} W={v['mean_winner_R']:+.3f} L={v['mean_loser_R']:+.3f}")
print("x dist:",{k:round(v,4) for k,v in out["reanchor_x_dist"].items()})
print("size mult:",{k:round(v,2) for k,v in out["reanchor_size_multiplier_1_over_1_minus_x"].items()})
print("DECOMP:",{k:round(v,5) for k,v in out["DECOMPOSITION_R_per_pool_trade"].items()})
print("exit reasons A1:",out["exit_reasons_A1"])
