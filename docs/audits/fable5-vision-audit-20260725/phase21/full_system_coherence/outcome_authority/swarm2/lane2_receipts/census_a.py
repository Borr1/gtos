#!/usr/bin/env python3
"""(A) Truncation census over the five sealed months, from the sealed corpus alone."""
import gzip, pickle, json, math, datetime as dt
from collections import Counter, defaultdict
import numpy as np

MONTHS = ["feb","apr","may","jun","jul"]
CACHE = "/private/tmp/w21-puzzle-cache/rows_%s.pkl.gz"

def at(s):
    return dt.datetime.fromisoformat(str(s))

out = {}
allrows = []
for m in MONTHS:
    rows = pickle.load(gzip.open(CACHE % m,'rb'))
    for r in rows:
        r['month'] = m
    allrows.extend(rows)
print("total rows", len(allrows), flush=True)

# horizon distribution
hz = []
clip = 0
for r in allrows:
    s = at(r['label_span_start_utc']); e = at(r['expiry_utc'])
    mins = (e-s).total_seconds()/60.0
    hz.append(mins)
    day_end = dt.datetime.fromisoformat(r['trading_day']).replace(tzinfo=dt.timezone.utc) + dt.timedelta(days=1)
    if abs((e - day_end).total_seconds()) < 1: clip += 1
hz = np.array(hz)
print(json.dumps({
 "horizon_minutes": {"n": int(len(hz)), "min": float(hz.min()), "p01": float(np.percentile(hz,1)),
   "p25": float(np.percentile(hz,25)), "median": float(np.median(hz)), "mean": float(hz.mean()),
   "p75": float(np.percentile(hz,75)), "max": float(hz.max()),
   "frac_exactly_120": float((hz==120).mean()), "frac_below_120": float((hz<120).mean())},
 "clipped_at_day_boundary": clip, "clip_frac": clip/len(allrows)}, indent=1), flush=True)
np.save("horizons.npy", hz)

# status census
def cen(rows):
    c = Counter(r['lifecycle_label_status'] for r in rows)
    filled = {k.removeprefix("RESOLVED_FILLED_"): v for k,v in c.items() if k.startswith("RESOLVED_FILLED_")}
    nf = sum(v for k,v in c.items() if k=="RESOLVED_NO_FILL")
    other = sum(v for k,v in c.items() if not k.startswith("RESOLVED_FILLED_") and k!="RESOLVED_NO_FILL")
    tot = sum(filled.values())
    return {"n": len(rows), "no_fill": nf, "censored_other": other, "filled": tot,
            "TARGET": filled.get("TARGET",0), "STOP": filled.get("STOP",0), "TIME_STOP": filled.get("TIME_STOP",0),
            "frac_TARGET": filled.get("TARGET",0)/tot if tot else None,
            "frac_STOP": filled.get("STOP",0)/tot if tot else None,
            "frac_TIME_STOP": filled.get("TIME_STOP",0)/tot if tot else None}

res = {"overall": cen(allrows), "by_month": {}, "by_family": {}, "by_order_type": {}, "by_family_month": {}}
for m in MONTHS:
    res["by_month"][m] = cen([r for r in allrows if r['month']==m])
fams = sorted({r['origin_family'] for r in allrows})
for f in fams:
    res["by_family"][f] = cen([r for r in allrows if r['origin_family']==f])
for ot in ("MARKET","LIMIT"):
    res["by_order_type"][ot] = cen([r for r in allrows if r['proposed_order_type']==ot])
print(json.dumps(res, indent=1), flush=True)
json.dump(res, open("A_census.json","w"), indent=1)
