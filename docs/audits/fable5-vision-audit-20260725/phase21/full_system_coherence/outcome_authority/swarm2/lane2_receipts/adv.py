#!/usr/bin/env python3
"""Adversarial checks on this lane's own positives."""
import gzip,pickle,json
from collections import defaultdict,Counter
import numpy as np
RNG=np.random.default_rng(20260812)
M=["feb","apr","may","jun","jul"]
recs=[]
for m in M: recs.extend(pickle.load(gzip.open(f"walk_{m}.pkl.gz","rb")))
cache={}
for m in M:
    for c in pickle.load(gzip.open(f"/private/tmp/w21-puzzle-cache/rows_{m}.pkl.gz","rb")): cache[c["candidate_occurrence_key"]]=c
HS=["h1","h2","h4","h8","hInf"]
F=[r for r in recs if r.get("fi") is not None and r["H1"]>0 and not r.get("err")]
C=[r for r in F if all((r.get(h) or {}).get("kind") not in (None,"CENSOR") for h in HS)]
def net(r,h): 
    d=r.get(h); return None if (not d or d["gross"] is None) else d["gross"]-r["ded"]
def cb(rows,vals,B=4000):
    by=defaultdict(list)
    for r,v in zip(rows,vals): by[r["day"]].append(v)
    dl=list(by); idx={d:np.array(by[d]) for d in dl}
    bs=np.array([np.concatenate([idx[dl[i]] for i in RNG.choice(len(dl),len(dl),replace=True)]).mean() for _ in range(B)])
    return {"mean":float(np.mean(np.concatenate([idx[d] for d in dl]))),
            "ci":[float(np.percentile(bs,2.5)),float(np.percentile(bs,97.5))],
            "p":float(2*min((bs<=0).mean(),(bs>=0).mean())),"days":len(dl)}
out={}
# 1. the structural_distance_extreme time-stop cell (n=175, +0.52 R claimed)
sde=[r for r in C if r["fam"]=="structural_distance_extreme" and r["h1"]["kind"]=="TIME_STOP"]
d=[net(r,"hInf")-net(r,"h1") for r in sde]
out["sde_timestop_cell"]={"n":len(sde),**cb(sde,d),"days_covered":len({r["day"] for r in sde}),
  "share_of_family":len(sde)/len([r for r in C if r["fam"]=="structural_distance_extreme"]),
  "top_5_abs_contributions":sorted([float(x) for x in d],key=abs,reverse=True)[:5],
  "sum_r":float(np.sum(d)),
  "sum_r_excluding_top5":float(np.sum(sorted(d,key=abs,reverse=True)[5:]))}
# 2. the 1x TIME_STOP cohort is profitable -- is that selection or a real property?
ts=[r for r in C if r["h1"]["kind"]=="TIME_STOP"]
out["timestop_cohort"]={"n":len(ts),"net_1x":cb(ts,[net(r,"h1") for r in ts]),
  "net_inf":cb(ts,[net(r,"hInf") for r in ts]),
  "delta":cb(ts,[net(r,"hInf")-net(r,"h1") for r in ts]),
  "note":"conditioning on 'did not resolve in 120 min' is a POST-fill selection; the cohort mean is not an achievable ex-ante return"}
# 3. zero-horizon rows and the day-boundary clip
allrows=[]
for m in M: allrows.extend(pickle.load(gzip.open(f"/private/tmp/w21-puzzle-cache/rows_{m}.pkl.gz","rb")))
import datetime as dt
def at(s): return dt.datetime.fromisoformat(str(s))
h=np.array([ (at(r["expiry_utc"])-at(r["label_span_start_utc"])).total_seconds()/60 for r in allrows])
st=Counter(r["lifecycle_label_status"] for r,x in zip(allrows,h) if x<=0)
out["zero_horizon_rows"]={"n":int((h<=0).sum()),"frac":float((h<=0).mean()),"statuses":dict(st),
  "n_clipped_below_120":int((h<120).sum()),"frac_clipped":float((h<120).mean())}
# 4. the submission-anchored clock burns a limit's trade life
hz=[]
for m in M: hz.extend(pickle.load(gzip.open(f"hz_{m}.pkl.gz","rb")))
for ot in ("MARKET","LIMIT"):
    s=[r for r in hz if r["ot"]==ot]
    rest=np.array([r["rest"] for r in s],dtype=float); rem=np.array([r["remaining"] for r in s],dtype=float)
    out[f"clock_burn_{ot}"]={"n":len(s),"median_rest_min":float(np.median(rest)),"mean_rest_min":float(rest.mean()),
      "median_remaining_min":float(np.median(rem)),"mean_remaining_min":float(rem.mean()),
      "frac_remaining_lt_60":float((rem<60).mean()),"frac_remaining_lt_30":float((rem<30).mean())}
# 5. fill population identity across stop scales
sc=[]
for m in M: sc.extend(pickle.load(gzip.open(f"scale_{m}.pkl.gz","rb")))
out["fill_population_identity_across_k"]={"n_rows_each_k":len(sc),
  "note":"the limit fill depends on `entry` only, so widening the stop cannot change WHICH trades fill; verified by construction in scale.py (one fill per row, five geometries)"}
json.dump(out,open("ADVERSARIAL.json","w"),indent=1)
print(json.dumps(out,indent=1))
