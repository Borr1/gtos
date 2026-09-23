"""The pool question, stated correctly.

net = gross - deductible ; cost_r = spread_r + deductible  =>  net + cost_r = gross + spread_r
and for a driftless tape E[gross + spread_r] = 0 exactly. So `net + cost_r` IS the
cost-free directional edge, and the pool question is: is it positive anywhere?"""
import numpy as np, json, math
from scipy import stats
d=np.load("/private/tmp/laneG-walk/pool_table.npz", allow_pickle=True)
MONTHS=["feb","apr","may","jun","jul"]
status=d["status"].astype(str); net=d["net"]; cost=d["cost_r"]
sel=np.char.startswith(status,"RESOLVED_FILLED") & np.isfinite(net) & np.isfinite(cost)
y=net[sel]+cost[sel]           # cost-free edge
ynet=net[sel]
fam=d["family"][sel].astype(str); sym=d["symbol"][sel].astype(str)
ses=d["session"][sel].astype(str); side=d["side"][sel].astype(str)
ot=d["order_type"][sel].astype(str)
mo=d["month"][sel].astype(str)
print("filled rows with net+cost:",len(y))

# sanity: reproduce the martingale identity on the puzzle cache itself
print(f"POOLED cost-free edge E[net+cost_r] = {y.mean():+.5f} +- {y.std(ddof=1)/math.sqrt(len(y)):.5f} "
      f"(t {y.mean()/(y.std(ddof=1)/math.sqrt(len(y))):+.2f});  E[net] = {ynet.mean():+.5f}")
print(f"  MARKET only: {y[ot=='MARKET'].mean():+.5f} (n {int((ot=='MARKET').sum())});  "
      f"LIMIT only: {y[ot=='LIMIT'].mean():+.5f} (n {int((ot=='LIMIT').sum())})")

print("\nPER FAMILY (all 10, both order types) — cost-free edge vs realised net")
print(f"{'family':34s} {'type':7s} {'n':>7s} {'E[net]':>9s} {'E[cost]':>8s} {'edge':>9s} {'se':>7s} {'t':>7s} {'mo>0':>5s}")
res={}
for f in sorted(set(fam)):
    k=fam==f
    if k.sum()<200: continue
    e=y[k]; se=e.std(ddof=1)/math.sqrt(len(e))
    permo=[float(y[k&(mo==m)].mean()) if (k&(mo==m)).sum()>20 else None for m in MONTHS]
    npos=sum(1 for v in permo if v is not None and v>0)
    typ=("MARKET" if (ot[k]=="MARKET").mean()>0.5 else "LIMIT")
    res[f]=dict(n=int(k.sum()),net=float(ynet[k].mean()),cost=float(cost[sel][k].mean()),
                edge=float(e.mean()),se=float(se),t=float(e.mean()/se),months_positive=npos,per_month=permo,order=typ)
    print(f"{f:34s} {typ:7s} {int(k.sum()):7d} {ynet[k].mean():+9.4f} {cost[sel][k].mean():8.4f} "
          f"{e.mean():+9.4f} {se:7.4f} {e.mean()/se:+7.2f} {npos:5d}")

# ---- BH-corrected cell search on the cost-free edge ------------------------
print("\nCELL SEARCH on the cost-free edge (family x symbol, n>=150), BH q<=0.10")
key=np.char.add(np.char.add(fam,"|"),sym)
rows=[]
for k in sorted(set(key)):
    m=key==k
    if m.sum()<150: continue
    e=y[m]; se=e.std(ddof=1)/math.sqrt(len(e)); t=e.mean()/se
    p=2*(1-stats.t.cdf(abs(t),len(e)-1))
    permo=[float(y[m&(mo==mm)].mean()) if (m&(mo==mm)).sum()>=15 else None for mm in MONTHS]
    rows.append((k,int(m.sum()),float(e.mean()),float(se),float(t),float(p),
                 sum(1 for v in permo if v is not None and v>0),
                 sum(1 for v in permo if v is not None)))
rows.sort(key=lambda r:r[5])
pv=np.array([r[5] for r in rows]); mtot=len(rows)
bh=pv*mtot/np.arange(1,mtot+1)
bh=np.minimum.accumulate(bh[::-1])[::-1]
print(f"  {mtot} cells tested. BH q<=0.10: {int((bh<=0.10).sum())}; of those with a POSITIVE edge: "
      f"{int(sum(1 for i,r in enumerate(rows) if bh[i]<=0.10 and r[2]>0))}")
print(f"  {'cell':40s} {'n':>6s} {'edge':>9s} {'t':>7s} {'p':>9s} {'q':>9s} {'mo>0':>6s}")
for i,r in enumerate(rows[:12]):
    print(f"  {r[0]:40s} {r[1]:6d} {r[2]:+9.4f} {r[4]:+7.2f} {r[5]:9.2e} {bh[i]:9.3f} {r[6]}/{r[7]}")
print("  ... best POSITIVE cells:")
posr=[(i,r) for i,r in enumerate(rows) if r[2]>0]; posr.sort(key=lambda ir: ir[1][5])
for i,r in posr[:8]:
    print(f"  {r[0]:40s} {r[1]:6d} {r[2]:+9.4f} {r[4]:+7.2f} {r[5]:9.2e} {bh[i]:9.3f} {r[6]}/{r[7]}")
json.dump({"family":res,"cells":[dict(zip(("cell","n","edge","se","t","p","months_pos","months_n"),r))|{"q":float(bh[i])}
                                 for i,r in enumerate(rows)]},
          open("/tmp/laneG/pool_edge.json","w"),indent=1)
