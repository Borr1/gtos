import csv, glob, os, json, pickle
from collections import defaultdict
D="/Users/borr/Documents/gtos/repo/ai-trading-agent/data/mt5_research_exports/deep_universe_h4d1_2014_2026"
panel=defaultdict(dict)   # date -> sym -> (o,h,l,c,v)
meta={}
for p in sorted(glob.glob(os.path.join(D,"*_D1.csv"))):
    sym=os.path.basename(p)[:-7]
    n=0
    with open(p) as f:
        r=csv.reader(f); next(r)
        for row in r:
            if len(row)<6: continue
            d=row[0][:10]
            try: o,h,l,c,v=float(row[1]),float(row[2]),float(row[3]),float(row[4]),float(row[5])
            except: continue
            if c<=0: continue
            panel[d][sym]=(o,h,l,c,v); n+=1
    meta[sym]=n
dates=sorted(panel)
print("dates",len(dates),dates[0],dates[-1])
# coverage curve by year
cov=defaultdict(list)
for d in dates: cov[d[:4]].append(len(panel[d]))
for y in sorted(cov):
    xs=sorted(cov[y]); print(y,"days",len(xs),"median symbols/day",xs[len(xs)//2],"max",xs[-1])
pickle.dump({"panel":dict(panel),"dates":dates,"meta":meta}, open("panel_d1.pkl","wb"))
