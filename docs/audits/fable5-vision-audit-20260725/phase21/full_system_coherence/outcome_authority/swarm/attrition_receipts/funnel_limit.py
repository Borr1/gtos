#!/usr/bin/env python3
"""Target 4b — is the abstain margin information, or is it the cost of the LIMIT rows?
Leading hypothesis (Lane G §1.4): E[net] = -E[cost_r]; abstaining buys exactly the cost."""
import numpy as np, json, math, collections
from math import erf, sqrt
z=np.load("/private/tmp/laneG-walk/pool_table.npz", allow_pickle=True)
fam,ot,st,net,cost,sp,pred,win,day,mo = (z[k] for k in
   ('family','order_type','status','net','cost_r','spread_r','pred','window','day','month'))
res = np.isfinite(net)
LIM = ot=="LIMIT"; MKT = ot=="MARKET"
def blk(name, m):
    m = m & res
    n=m.sum(); mu=net[m].mean(); se=net[m].std(ddof=1)/sqrt(n)
    c=cost[m].mean(); s=sp[m].mean(); cf=(net[m]+cost[m])
    cfse=cf.std(ddof=1)/sqrt(n); t=cf.mean()/cfse
    p=2*(1-0.5*(1+erf(abs(t)/sqrt(2))))
    print(f"{name:34s} n={n:7d}  E[net] {mu:+.5f}+-{se:.5f}   E[cost_r] {c:.5f}  E[spread_r] {s:.5f}"
          f"   E[net+cost] {cf.mean():+.5f}+-{cfse:.5f} (t {t:+.2f}, p {p:.3f})   half-spread {s/2:.5f}")
    return dict(n=int(n), E_net=float(mu), se_net=float(se), E_cost=float(c), E_spread=float(s),
                E_cost_free=float(cf.mean()), se_cost_free=float(cfse), t=float(t), p=float(p),
                half_spread=float(s/2), ratio_costfree_to_halfspread=float(cf.mean()/(s/2)) if s else None)
out={}
print("RESOLVED ROWS — the whole pool")
out["ALL"]=blk("all resolved", np.ones(len(net),bool))
out["MARKET"]=blk("MARKET families (abstain's book)", MKT)
out["LIMIT"]=blk("LIMIT families (what abstain skips)", LIM)
print()
for f in ("current_breaker_re_entry","current_fvg_fill","current_ob_retest"):
    out[f]=blk(f"  {f}", fam==f)
print()
# --- restricted to the rows a top-of-window policy could actually pick (pred >= 0.10, top of window)
ok = res & np.isfinite(pred)
order = np.lexsort((-pred[ok], win[ok]))
idx = np.flatnonzero(ok)[order]
w = win[idx]; first = np.ones(len(idx), bool); first[1:] = w[1:] != w[:-1]
top = idx[first]
tp = pred[top] >= 0.10
top = top[tp]
print(f"top-of-window candidates with pred >= 0.10: {len(top)}")
tl = ot[top]=="LIMIT"
out["TOP_LIMIT"]=blk("  top-of-window & LIMIT (skipped)", np.isin(np.arange(len(net)), top[tl]))
out["TOP_MARKET"]=blk("  top-of-window & MARKET (taken)", np.isin(np.arange(len(net)), top[~tl]))
# --- count-matched random-abstention control on the top-of-window book
rng=np.random.default_rng(20260812)
tn = net[top]; k=int(tl.sum())
real = -tn[tl].sum()                       # R saved by skipping the LIMIT-topped windows
rand=[]
for _ in range(20000):
    pick = rng.choice(len(tn), k, replace=False)
    rand.append(-tn[pick].sum())
rand=np.sort(np.asarray(rand))
p_rand = float((rand >= real).mean())
print(f"\nCOUNT-MATCHED CONTROL on the top-of-window book (n {len(tn)}, abstained {k}):")
print(f"  R saved by skipping the LIMIT-topped windows : {real:+.4f}")
print(f"  R saved by skipping {k} windows AT RANDOM     : mean {rand.mean():+.4f}  CI95 [{rand[500]:+.4f},{rand[19500]:+.4f}]")
print(f"  P(random abstention saves at least as much)   : {p_rand:.4f}")
out["count_matched_control"]=dict(n_top=int(len(tn)), k_abstained=k, real_saving=float(real),
    random_mean=float(rand.mean()), random_ci95=[float(rand[500]),float(rand[19500])], p=p_rand, n_draws=20000)
json.dump(out, open("/private/tmp/FUNNEL_LIMIT.json","w"), indent=1)
