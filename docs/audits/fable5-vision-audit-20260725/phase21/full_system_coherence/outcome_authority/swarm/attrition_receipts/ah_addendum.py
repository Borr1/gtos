import sys, json, math, statistics
from pathlib import Path
import numpy as np
REPO = Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
for p in ("", "docs/audits/fable5-vision-audit-20260725/phase7/receipts",
          "docs/audits/fable5-vision-audit-20260725/phase8/receipts"):
    sys.path.insert(0, str(REPO/p))
import af_repairs as AFR, ah_conditioning as AH
art, series, regimes = AH.load_all(); fams = AH.members_of(art)
rows = [dict(r, _m=m) for m in fams["fam_volume_surge_reversal_index_d1"]
        for r in AH.reachable(art["trades"].get(m, []))]
lab = np.array([AFR.bucket("VOL_REGIME", regimes.get(r["_m"],{}).get(r["decision_bar_iso"],{}).get("VOL_REGIME")) for r in rows])
g = np.array([r["r_gross"] for r in rows])
hi = lab=="hi"; rest = ~hi
print(f"pooled family mean {g.mean():+.6f} (n {len(g)})")
print(f"hi   mean {g[hi].mean():+.6f} (n {hi.sum()})   rest mean {g[rest].mean():+.6f} (n {rest.sum()})")
diff = g[hi].mean()-g[rest].mean()
se = math.sqrt(g[hi].var(ddof=1)/hi.sum() + g[rest].var(ddof=1)/rest.sum())
print(f"CONDITIONING EFFECT (hi vs rest): {diff:+.6f}  se {se:.6f}  t {diff/se:+.3f}")
from math import erf, sqrt
pz = 2*(1-0.5*(1+erf(abs(diff/se)/sqrt(2))))
print(f"  two-sided normal p = {pz:.4f}   ; x9 enumeration = {min(1,9*pz):.4f}")
# cell mean vs zero, trade-level and bootstrap over decision days
gh = g[hi]; se0 = gh.std(ddof=1)/math.sqrt(len(gh))
t0 = gh.mean()/se0
p0 = 2*(1-0.5*(1+erf(abs(t0)/sqrt(2))))
print(f"CELL vs ZERO: mean {gh.mean():+.6f} se {se0:.6f} t {t0:+.3f} p {p0:.4f}  CI95 [{gh.mean()-1.96*se0:+.4f},{gh.mean()+1.96*se0:+.4f}]")
days = np.array([r["decision_day"] for r in rows])[hi]
uniq = sorted(set(days.tolist())); rng = np.random.default_rng(20260812)
byd = {u: gh[days==u] for u in uniq}; bs=[]
for _ in range(20000):
    pick = rng.choice(len(uniq), len(uniq), replace=True)
    bs.append(np.concatenate([byd[uniq[i]] for i in pick]).mean())
bs=np.sort(np.asarray(bs))
print(f"  day-block bootstrap CI95 [{bs[500]:+.4f},{bs[19500]:+.4f}] p(<=0) {(bs<=0).mean():.4f}  n_days {len(uniq)}")
json.dump(dict(pooled=float(g.mean()), hi_mean=float(g[hi].mean()), rest_mean=float(g[rest].mean()),
  n_hi=int(hi.sum()), n_rest=int(rest.sum()), conditioning_diff=float(diff), conditioning_se=float(se),
  conditioning_t=float(diff/se), conditioning_p=float(pz), conditioning_p_x9=float(min(1,9*pz)),
  cell_vs_zero_t=float(t0), cell_vs_zero_p=float(p0),
  cell_day_block_ci95=[float(bs[500]),float(bs[19500])], cell_day_block_p_le0=float((bs<=0).mean()),
  n_decision_days=len(uniq)), open("/private/tmp/AH_ADDENDUM.json","w"), indent=1)
