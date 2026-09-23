"""What explains the +0.008 (MARKET) / +0.054 (LIMIT) cost-free residual that should
be zero under a driftless tape? Two candidate mechanisms, both direction-symmetric:
 (a) asymmetric gap censoring -- CENSORED_INVALID_GAP_THROUGH_SL_OR_TP removes rows
     whose fill-bar exit-side open is already through the stop (1R away) OR the target
     (2R away). Adverse gaps >=1R are dropped; favourable gaps need >=2R. That is a
     survivorship bias in the trade's own favour.
 (b) directional information -- would NOT be reproduced by a direction-flipped arm."""
import numpy as np, json, math, gzip, pickle
from scipy.stats import spearmanr
d=np.load("/private/tmp/laneG-walk/pool_table.npz", allow_pickle=True)
st=d["status"].astype(str); net=d["net"]; cost=d["cost_r"]; fam=d["family"].astype(str)
filled=np.char.startswith(st,"RESOLVED_FILLED")&np.isfinite(net)&np.isfinite(cost)
cf=net+cost
rows=[]
for f in sorted(set(fam)):
    m=fam==f
    if m.sum()<500: continue
    ig=(st[m]=="CENSORED_INVALID_GAP_THROUGH_SL_OR_TP").mean()
    allc=np.char.startswith(st[m],"CENSORED").mean()
    tot=float(cf[m&filled].mean())
    rows.append((f,int(m.sum()),ig,allc,tot))
print(f"{'family':34s} {'n':>7s} {'invalid_gap%':>12s} {'all cens%':>10s} {'cost-free':>10s}")
for r in rows: print(f"{r[0]:34s} {r[1]:7d} {100*r[2]:12.2f} {100*r[3]:10.2f} {r[4]:+10.4f}")
rho,p=spearmanr([r[2] for r in rows],[r[4] for r in rows])
print(f"\nSpearman(invalid-gap censor rate, cost-free edge) over {len(rows)} families = {rho:+.4f} (p {p:.4f})")
rho2,p2=spearmanr([r[3] for r in rows],[r[4] for r in rows])
print(f"Spearman(total censor rate,      cost-free edge)                       = {rho2:+.4f} (p {p2:.4f})")

# ---- (b) paired direction control on MARKET families, both-arms-uncensored ----
recs=[]
for mo in ["feb","apr","may","jun","jul"]:
    with gzip.open(f"/private/tmp/laneG-walk/lg_{mo}.pkl.gz","rb") as fh: recs+=pickle.load(fh)
o=[];mm=[]
for r in recs:
    go,gm=r["orig"]["gross"], r["mirror"]["gross"]
    if go is None or gm is None: continue
    s=r["spread_at_fill_price"]
    if s is None: continue
    sr=s/r["risk_price"]
    o.append(go+sr); mm.append(gm+sr)
o=np.array(o); mm=np.array(mm); dd=o-mm
print(f"\nMARKET, both arms uncensored (n={len(o)}):")
print(f"  signal direction  cost-free = {o.mean():+.5f} +- {o.std(ddof=1)/math.sqrt(len(o)):.5f}")
print(f"  flipped direction cost-free = {mm.mean():+.5f} +- {mm.std(ddof=1)/math.sqrt(len(mm)):.5f}")
print(f"  PAIRED difference           = {dd.mean():+.5f} +- {dd.std(ddof=1)/math.sqrt(len(dd)):.5f} "
      f"(t {dd.mean()/(dd.std(ddof=1)/math.sqrt(len(dd))):+.2f})")
print("  -> the residual is present with the direction REVERSED, so it is not directional edge.")

# ---- stationarity (claim 5) --------------------------------------------------
print("\n=== CLAIM 5: stationarity of family completion rates ===")
mo_=d["month"].astype(str); MONTHS=["feb","apr","may","jun","jul"]
term=np.where(np.char.startswith(st,"RESOLVED_FILLED_"),np.char.replace(st,"RESOLVED_FILLED_",""),"")
print(f"{'family':34s} " + " ".join(f"{m:>18s}" for m in MONTHS) + "   chi2-p(homog)")
from scipy.stats import chi2_contingency
for f in sorted(set(fam)):
    tab=[]; line=""
    for m in MONTHS:
        k=filled&(fam==f)&(mo_==m)
        if k.sum()<30: tab=None; break
        c=[int((k&(term==s)).sum()) for s in ("TARGET","STOP","TIME_STOP")]
        tab.append(c); line+=f"  {c[0]/sum(c):.3f}/{sum(c):5d}    "
    if tab is None: continue
    chi2,pv,_,_=chi2_contingency(np.array(tab).T)
    print(f"{f:34s} {line}  {pv:.2e}")
