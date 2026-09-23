#!/usr/bin/env python3
"""Decomposition: is expected_net_r's correlation with realized net just the shared cost term?

expected_cost_r == cost_r EXACTLY on every row (COST_BELIEF.json), so
  expected_net_r = candidate_ev_r - cost_r     (belief)
  realized net   = realized gross - cost_r     (reality)
The cost term appears on both sides with coefficient -1. This script quantifies how much
of corr(expected_net, net) survives once the shared term is removed, and tests whether
candidate_ev_r is a deterministic transform of candidate_probability.
Also: given the scheduler ranks WITHIN a day, per-day top-vs-bottom quintile by
expected_net_r and by candidate_ev_r (cost-free belief) as a second decision-relevance cut.
"""
import gzip, json, math
from collections import defaultdict

POOLS = {
    "january": "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz",
    "february": "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz",
}

def pearson(xs, ys):
    n=len(xs); mx=sum(xs)/n; my=sum(ys)/n
    sxy=sxx=syy=0.0
    for x,y in zip(xs,ys):
        dx,dy=x-mx,y-my; sxy+=dx*dy; sxx+=dx*dx; syy+=dy*dy
    return sxy/math.sqrt(sxx*syy) if sxx and syy else None

out={}
for w,path in POOLS.items():
    ev=[];p=[];cost=[];net=[];exp_net=[];tgt=[];day=[];fam=[]
    with gzip.open(path,'rt') as f:
        for line in f:
            r=json.loads(line)
            ev.append(r['candidate_ev_r']); p.append(r['candidate_probability'])
            cost.append(r['cost_r']); net.append(r['opportunity_net_proxy_r'])
            exp_net.append(r['expected_net_r']); tgt.append(r['policy_target_r'])
            day.append(r['decision_time_utc'][:10]); fam.append(r['origin_family'])
    gross=[n+c for n,c in zip(net,cost)]
    # implied payoff multiple k where ev = p*(1+k) - 1  (i.e. win pays k R, loss pays -1 R)
    ks=[(e+1.0)/pp - 1.0 for e,pp in zip(ev,p)]
    k_rounded=set(round(k,6) for k in ks)
    # is k explained by policy_target_r?
    k_by_tgt=defaultdict(set)
    for k,t in zip(ks,tgt): k_by_tgt[t].add(round(k,4))
    res={
        "corr_expected_net_vs_net": pearson(exp_net,net),
        "corr_ev_vs_gross": pearson(ev,gross),
        "corr_neg_cost_vs_net": pearson([-c for c in cost],net),
        "corr_cost_vs_gross": pearson(cost,gross),
        "corr_p_vs_net": pearson(p,net),
        "corr_p_vs_gross": pearson(p,gross),
        "corr_p_vs_ev": pearson(p,ev),
        "implied_k_distinct_rounded6": len(k_rounded),
        "implied_k_min": min(ks), "implied_k_max": max(ks),
        "implied_k_by_policy_target_r": {str(t): {"n_distinct_k_rounded4": len(v), "sample": sorted(v)[:5]} for t,v in sorted(k_by_tgt.items())},
        "policy_target_r_distinct": sorted(set(tgt)),
    }
    # per-day within-day ranking (scheduler view): top vs bottom quintile by expected_net_r
    by_day=defaultdict(list)
    for d,e,nv in zip(day,exp_net,net): by_day[d].append((e,nv))
    tops=[];bots=[]
    for d,rows in by_day.items():
        rows.sort(key=lambda t:t[0]); q=len(rows)//5
        if q==0: continue
        bots.extend(v for _,v in rows[:q]); tops.extend(v for _,v in rows[-q:])
    res["within_day_top_quintile_by_expected_net_realized_mean"]=sum(tops)/len(tops)
    res["within_day_bottom_quintile_by_expected_net_realized_mean"]=sum(bots)/len(bots)
    # same by candidate_ev_r against gross (cost-free belief vs cost-free reality)
    by_day2=defaultdict(list)
    for d,e,gv in zip(day,ev,gross): by_day2[d].append((e,gv))
    tops2=[];bots2=[]
    for d,rows in by_day2.items():
        rows.sort(key=lambda t:t[0]); q=len(rows)//5
        if q==0: continue
        bots2.extend(v for _,v in rows[:q]); tops2.extend(v for _,v in rows[-q:])
    res["within_day_top_quintile_by_ev_realized_gross_mean"]=sum(tops2)/len(tops2)
    res["within_day_bottom_quintile_by_ev_realized_gross_mean"]=sum(bots2)/len(bots2)
    res["n_days"]=len(by_day)
    out[w]=res

path="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/research/operations/wave19_broad_forensic_2026_08_01/calibration/DECOMPOSITION_CHECK.json"
with open(path,'w') as f: json.dump(out,f,indent=1)
print(json.dumps(out,indent=1))
