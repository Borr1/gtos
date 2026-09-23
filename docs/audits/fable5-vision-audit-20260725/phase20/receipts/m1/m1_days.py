"""Recover the decision DAY for every accumulation row, in the same order, and prove the
alignment on two independent float columns before it is used for anything."""
import sys, os, glob, gzip, json, bisect, csv
from datetime import datetime, timedelta, timezone
import numpy as np
sys.path.insert(0,'/tmp/m1')
import m1_accum as A
sys.path.insert(0, A.PBG); sys.path.insert(0, A.REPO)
import pbg_lib as PL, pbg_econ as E

syms = sorted(p.name[:-len("_M15.csv")] for p in PL.M15_DIR.glob("*_M15.csv"))
tape = A.CTape(syms); cm = E.CostModel()

S={}
for p in sorted(glob.glob(os.path.join(str(PL.M15_DIR), "*_M15.csv"))):
    sym=os.path.basename(p)[:-len("_M15.csv")]
    t,c=[],[]
    with open(p, newline="") as fh:
        for r in csv.DictReader(fh):
            t.append(datetime.fromisoformat(r["time"]).replace(tzinfo=None)); c.append(float(r["close"]))
    S[sym]=(t,c)
days=[]; ent=[]; dn=[]
for w, rd in sorted(A.LEGACY.items()):
    for f in sorted(glob.glob(os.path.join(rd, "*.jsonl.gz"))):
        if not os.path.exists(f.replace(".jsonl.gz",".stats.json")): continue
        for line in gzip.open(f,"rt"):
            r=json.loads(line)
            if r["k"]!=15: continue
            sym=r["s"]
            if sym not in S or tape.tmin[sym].size==0: continue
            t,c=S[sym]
            T=datetime.fromisoformat(r["t"]).replace(tzinfo=None)
            j=bisect.bisect_right(t, T-timedelta(minutes=15)+timedelta(seconds=2))-1
            if j<0: continue
            e,sl=r["e"],r["sl"]; d=abs(e-sl)
            if not d>0: continue
            pos=tape.pos(sym, r["t"])
            if pos>=tape.tmin[sym].size: continue
            days.append(int(r["t"][:10].replace("-",""))); ent.append(e); dn.append(d)
days=np.asarray(days,dtype=np.int32); ent=np.asarray(ent); dn=np.asarray(dn)
z=np.load('/tmp/m1/M1_ACCUM.npz', allow_pickle=True)
ok = (days.size==z['entry'].size) and np.array_equal(ent, z['entry']) and np.array_equal(dn, z['dnat'])
print("rows",days.size,"ALIGNED" if ok else "MISALIGNED")
if not ok: sys.exit(2)
np.save('/tmp/m1/ACCUM_DAY.npy', days)
print("wrote days, distinct", len(set(days.tolist())))
