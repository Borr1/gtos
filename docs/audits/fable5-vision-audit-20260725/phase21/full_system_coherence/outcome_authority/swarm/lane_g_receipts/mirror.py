"""LANE G: (1) verify the RR=2.0 correction at scale; (2) the MIRROR benchmark."""
import gzip, pickle, math, json
import numpy as np
from collections import Counter, defaultdict
MONTHS=["feb","apr","may","jun","jul"]
recs=[]
for mo in MONTHS:
    with gzip.open(f"/private/tmp/laneG-walk/lg_{mo}.pkl.gz","rb") as fh:
        for r in pickle.load(fh):
            r["month"]=mo; recs.append(r)
print("records:", len(recs))

# ---------- 1. geometry ------------------------------------------------------
rr=np.array([r["rr_measured"] for r in recs])
print("rr_measured: min %.10f max %.10f  ==2.0 within 1e-9 on %d/%d rows"%(
    rr.min(), rr.max(), int(np.sum(np.abs(rr-2.0)<1e-9)), len(rr)))
print("rr_field values:", Counter(r["rr_field"] for r in recs))
print("policy_target_r:", Counter(r["policy_target_r"] for r in recs))
print("geometry_policy:", Counter(r["geometry_policy"] for r in recs))
print("order_type:", Counter(r["order_type"] for r in recs))

# ---------- 2. control: orig arm must reproduce phase0 walk -------------------
p0={}
for mo in MONTHS:
    with gzip.open(f"/private/tmp/phase0-inversion/walk_{mo}.pkl.gz","rb") as fh:
        for r in pickle.load(fh): p0[(mo,r["key"])]=r
same=diff=0; maxd=0.0
for r in recs:
    o=p0.get((r["month"],r["key"]))
    if o is None: diff+=1; continue
    if o["orig"]["status"]!=r["orig"]["status"]: diff+=1; continue
    a,b=o["orig"]["net"], r["orig"]["net"]
    if (a is None)!=(b is None): diff+=1; continue
    if a is not None: maxd=max(maxd, abs(a-b))
    same+=1
print(f"CONTROL vs phase0 walk: matched {same}, mismatched {diff}, max |net diff| {maxd}")
# and the inv arm
sameI=diffI=0; maxdI=0.0
for r in recs:
    o=p0.get((r["month"],r["key"]))
    if o is None: continue
    if o["inv"]["status"]!=r["inv"]["status"]: diffI+=1; continue
    a,b=o["inv"]["net"], r["inv"]["net"]
    if (a is None)!=(b is None): diffI+=1; continue
    if a is not None: maxdI=max(maxdI, abs(a-b))
    sameI+=1
print(f"INV arm vs phase0 walk: matched {sameI}, mismatched {diffI}, max |net diff| {maxdI}")

# ---------- 3. MIRROR benchmark ---------------------------------------------
def barrier_stats(rows, arm):
    st=Counter(r[arm]["state"] for r in rows)
    b=st["TARGET"]+st["STOP"]
    return st, b, (st["TARGET"]/b if b else None)

print(f"\n{'family':34s} {'n':>6s} | {'ORIG bar':>8s} {'hit':>7s} | {'MIRR bar':>8s} {'hit':>7s} | {'diff':>8s} {'z_paired':>8s} {'p':>9s}")
byfam=defaultdict(list)
for r in recs: byfam[r["family"]].append(r)
out={}
def mirror_test(rows):
    """Paired sign test on candidates where the two arms disagree.
    Each candidate contributes (orig hit target?) vs (mirror hit target?).
    Under H0 (no directional information) the two arms are exchangeable, so among
    discordant pairs each orientation is equally likely -> exact binomial."""
    a=b=0
    for r in rows:
        so,sm=r["orig"]["state"], r["mirror"]["state"]
        if so not in ("TARGET","STOP") or sm not in ("TARGET","STOP"): continue
        o=(so=="TARGET"); mm=(sm=="TARGET")
        if o and not mm: a+=1
        elif mm and not o: b+=1
    return a,b
from scipy.stats import binomtest
for fam,rows in sorted(byfam.items(), key=lambda kv:-len(kv[1])):
    so,bo,ho=barrier_stats(rows,"orig"); sm,bm,hm=barrier_stats(rows,"mirror")
    a,b=mirror_test(rows)
    n=a+b
    z=(a-n/2)/math.sqrt(n/4) if n>0 else None
    p=binomtest(a,n,0.5).pvalue if n>0 else None
    out[fam]={"n":len(rows),"orig_barrier_n":bo,"orig_hit":ho,"mirror_barrier_n":bm,"mirror_hit":hm,
              "discordant_orig_target":a,"discordant_mirror_target":b,"z_paired":z,"p_paired":p}
    print(f"{fam:34s} {len(rows):6d} | {bo:8d} {ho:7.4f} | {bm:8d} {hm:7.4f} | "
          f"{(ho-hm):+8.4f} {z if z is None else z:8.2f} {p:9.2e}")
so,bo,ho=barrier_stats(recs,"orig"); sm,bm,hm=barrier_stats(recs,"mirror")
a,b=mirror_test(recs); n=a+b; z=(a-n/2)/math.sqrt(n/4)
print(f"{'POOLED':34s} {len(recs):6d} | {bo:8d} {ho:7.4f} | {bm:8d} {hm:7.4f} | {(ho-hm):+8.4f} {z:8.2f} {binomtest(a,n,0.5).pvalue:9.2e}")
out["_POOLED"]={"orig_hit":ho,"mirror_hit":hm,"discordant_orig_target":a,"discordant_mirror_target":b,
                "z_paired":z,"p_paired":binomtest(a,n,0.5).pvalue}
json.dump(out, open("/tmp/laneG/mirror_result.json","w"), indent=1)
