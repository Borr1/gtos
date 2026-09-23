"""LANE C vs LANE E reconciliation.

Lane C's 'gross' is net + cost_r, which equals the labeler's terminal_gross_r PLUS the
spread the labeler already charged inside it. So Lane C's gross = the COST-FREE tape
travel of the trade. Under a driftless tape E[cost-free] = 0 EXACTLY (optional
stopping), for any geometry, horizon or direction.

That single identity forces Lane E's finding:
   0 = P(bar)*E[cf|bar] + P(ts)*E[cf|ts]  and  E[cf|bar] ~= 3*p_target - 1
   =>  p_target = 1/3 - P(ts)*E[cf|ts] / (3*P(bar))
so a POSITIVE time-stop bucket REQUIRES a target-hit rate BELOW 1/3. The two lanes
report the two halves of one zero."""
import numpy as np, json, math
d=np.load("/private/tmp/laneG-walk/pool_table.npz", allow_pickle=True)
MONTHS=["feb","apr","may","jun","jul"]
st=d["status"].astype(str); net=d["net"]; cost=d["cost_r"]
filled=np.char.startswith(st,"RESOLVED_FILLED") & np.isfinite(net) & np.isfinite(cost)
cf=net+cost                      # cost-free R (Lane C's 'gross')
fam=d["family"].astype(str); mo=d["month"].astype(str); ot=d["order_type"].astype(str)
term=np.where(np.char.startswith(st,"RESOLVED_FILLED_"),
              np.char.replace(st,"RESOLVED_FILLED_",""), "")
print(f"{'family':32s} {'ord':7s} {'n':>6s} | {'TARGET':>16s} {'STOP':>16s} {'TIME_STOP':>16s} | "
      f"{'total cf':>9s} {'se':>7s} | {'p_tgt':>6s} {'implied':>8s}")
print(f"{'':32s} {'':7s} {'':6s} | {'share  mean':>16s} {'share  mean':>16s} {'share  mean':>16s} | ")
res={}
for f in sorted(set(fam[filled])):
    for label,mask in (("",filled&(fam==f)),):
        m=mask
        if m.sum()<200: continue
        parts={}
        for s in ("TARGET","STOP","TIME_STOP"):
            k=m&(term==s)
            parts[s]=(k.sum()/m.sum(), float(cf[k].mean()) if k.sum() else float('nan'))
        tot=float(cf[m].mean()); se=float(cf[m].std(ddof=1)/math.sqrt(m.sum()))
        pbar=parts["TARGET"][0]+parts["STOP"][0]
        ptgt=parts["TARGET"][0]/pbar if pbar else float('nan')
        # what target-hit rate the martingale identity demands, given the measured
        # time-stop bucket and a +2/-1 barrier payoff in cost-free units
        implied=1/3 - parts["TIME_STOP"][0]*parts["TIME_STOP"][1]/(3*pbar) if pbar else float('nan')
        typ="MARKET" if (ot[m]=="MARKET").mean()>0.5 else "LIMIT"
        res[f]=dict(n=int(m.sum()),order=typ,total_cf=tot,se=se,p_target=ptgt,implied_p_target=implied,
                    **{f"{s}_share":parts[s][0] for s in parts}, **{f"{s}_mean_cf":parts[s][1] for s in parts})
        print(f"{f:32s} {typ:7s} {int(m.sum()):6d} | {parts['TARGET'][0]:5.3f} {parts['TARGET'][1]:+9.4f} "
              f"{parts['STOP'][0]:5.3f} {parts['STOP'][1]:+9.4f} {parts['TIME_STOP'][0]:5.3f} "
              f"{parts['TIME_STOP'][1]:+9.4f} | {tot:+9.4f} {se:7.4f} | {ptgt:6.4f} {implied:8.4f}")
m=filled
print(f"{'ALL':32s} {'both':7s} {int(m.sum()):6d} | " + " ".join(
    f"{(m&(term==s)).sum()/m.sum():5.3f} {cf[m&(term==s)].mean():+9.4f}" for s in ("TARGET","STOP","TIME_STOP"))
    + f" | {cf[m].mean():+9.4f} {cf[m].std(ddof=1)/math.sqrt(m.sum()):7.4f}")

# ---- corridor control: Spearman(corridor width in ATR, time-stop mean) -------
from scipy.stats import spearmanr
lc=json.load(open("laneE_corridor.json"))
w=lc["corridor_width_atr_2R"]
fams=[f for f in res if f in w]
x=[w[f] for f in fams]; y=[res[f]["TIME_STOP_mean_cf"] for f in fams]
rho,p=spearmanr(x,y)
print(f"\ncorridor control (Lane E's): Spearman(corridor width ATR, time-stop cost-free mean) "
      f"= {rho:+.4f} (p {p:.4f}) over {len(fams)} families  [Lane E published -0.612]")
y2=[res[f]["TARGET_share"]/(res[f]['TARGET_share']+res[f]['STOP_share']) for f in fams]
rho2,p2=spearmanr(x,y2)
print(f"corridor vs target-hit rate: Spearman = {rho2:+.4f} (p {p2:.4f})  "
      f"-- the SAME artifact seen from the other side")
json.dump(res, open("/tmp/laneG/reconcile.json","w"), indent=1)
