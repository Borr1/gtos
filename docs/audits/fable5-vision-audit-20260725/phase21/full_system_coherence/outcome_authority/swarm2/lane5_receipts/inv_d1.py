import csv, json, os, glob
D="/Users/borr/Documents/gtos/repo/ai-trading-agent/data/mt5_research_exports/deep_universe_h4d1_2014_2026"
out={}
for p in sorted(glob.glob(os.path.join(D,"*_D1.csv"))):
    sym=os.path.basename(p)[:-7]
    first=last=None; n=0
    with open(p) as f:
        r=csv.reader(f); hdr=next(r)
        for row in r:
            if not row: continue
            n+=1
            if first is None: first=row[0]
            last=row[0]
    out[sym]={"n":n,"first":first,"last":last,"hdr":hdr}
json.dump(out, open("inv_d1.json","w"), indent=0)
import collections
yrs=collections.Counter()
for s,v in out.items(): yrs[v["first"][:4]]+=1
print("symbols:",len(out))
print("header:",list(out.values())[0]["hdr"])
print("first-year histogram:",dict(sorted(yrs.items())))
lastdates=collections.Counter(v["last"][:7] for v in out.values())
print("last-month histogram:",dict(sorted(lastdates.items())))
ns=sorted(v["n"] for v in out.values())
print("rows: min",ns[0],"p25",ns[len(ns)//4],"median",ns[len(ns)//2],"max",ns[-1])
# symbols with >= 2000 rows and last >= 2026-05
good=[s for s,v in out.items() if v["n"]>=1500 and v["last"]>="2026-05"]
print("symbols n>=1500 and last>=2026-05:",len(good))
print(sorted(good))
