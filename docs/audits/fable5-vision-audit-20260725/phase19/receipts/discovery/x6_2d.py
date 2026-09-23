import json, statistics
d=json.load(open('/tmp/x6/X6_SPREAD_2D_ftmo.json'))
S=[s for s in d['symbols'] if not s.get('error')]
# per symbol per hour: normalise the 60 minute-cells by THAT HOUR's own mean, so the
# hour-level (rollover/session) premium is divided out entirely and only the WITHIN-HOUR
# minute shape survives.
prof={h:[[] for _ in range(60)] for h in range(24)}
for s in S:
    cm=s['cell_median']
    for h in range(24):
        v=[cm.get(f"{h}|{mo}") for mo in range(60)]
        if any(x is None for x in v): continue
        m=sum(v)/60.0
        if m<=0: continue
        for mo in range(60): prof[h][mo].append(v[mo]/m)
rows=[]
print("broker_hr  :00     :01     :02     :05    interior(+3..59)  premium_at_:00  n_sym")
for h in range(24):
    if not prof[h][0]: continue
    p=[statistics.mean(prof[h][mo]) for mo in range(60)]
    interior=statistics.mean(p[3:])
    rows.append((h,p[0],p[1],p[2],p[5],interior,p[0]/interior,len(prof[h][0])))
    print(f"   {h:02d}    {p[0]:.4f}  {p[1]:.4f}  {p[2]:.4f}  {p[5]:.4f}     {interior:.4f}        {100*(p[0]/interior-1):+6.2f}%     {len(prof[h][0])}")
prem=[r[6] for r in rows]
print()
print(f"WITHIN-HOUR minute-0 premium, hour effect removed by construction:")
print(f"  median across the 24 broker hours : {100*(statistics.median(prem)-1):+.2f}%")
print(f"  min / max                          : {100*(min(prem)-1):+.2f}% / {100*(max(prem)-1):+.2f}%")
print(f"  hours where :00 is WIDER than the interior : {sum(1 for x in prem if x>1)}/{len(prem)}")
# which hours are the extremes
rr=sorted(rows,key=lambda r:-r[6])
print(f"  widest 3 hours : " + ", ".join(f"h{r[0]:02d} {100*(r[6]-1):+.1f}%" for r in rr[:3]))
print(f"  narrowest 3    : " + ", ".join(f"h{r[0]:02d} {100*(r[6]-1):+.1f}%" for r in rr[-3:]))
# the H4 close hours on this broker clock: H4 bars close at 01,05,09,13,17,21 broker
h4=[1,5,9,13,17,21]
h4p=[r[6] for r in rows if r[0] in h4]
print(f"  H4-CLOSE hours (01,05,09,13,17,21) median premium : {100*(statistics.median(h4p)-1):+.2f}%  n={len(h4p)}")
json.dump({"per_hour":[{"broker_hour":r[0],"min0":r[1],"min1":r[2],"min2":r[3],"min5":r[4],
                        "interior":r[5],"premium_at_min0":r[6],"n_symbols":r[7]} for r in rows],
           "median_premium":statistics.median(prem),"h4_close_hours_median":statistics.median(h4p)},
          open('/tmp/x6/X6_2D_SUMMARY.json','w'),indent=1)
