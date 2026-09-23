"""Isolate the M15-bar-close effect from the hour-close effect, using the minute-of-hour
profile only. The :15/:30/:45 boundaries are M15 closes that are NOT hour closes, so if the
premium survives there it is a bar-boundary effect and not a rollover/hour artifact."""
import json, statistics
for b in ("ftmo","redacted_account"):
    try: d=json.load(open(f'/tmp/x6/X6_SPREAD_MINUTE_{b}.json'))
    except FileNotFoundError: print(b,"missing"); continue
    S=[s for s in d['symbols'] if not s.get('error')]
    rows=[]
    for s in S:
        v=[s['moh_median'].get(str(i)) for i in range(60)]
        if any(x is None for x in v): continue
        m=sum(v)/60.0
        if m<=0: continue
        rows.append([x/m for x in v])
    prof=[statistics.mean(r[i] for r in rows) for i in range(60)]
    def mm(idx): return statistics.mean(prof[i] for i in idx)
    hour0   = prof[0]
    m15only = mm([15,30,45])                     # M15 closes that are NOT hour closes
    interior= mm([i for i in range(60) if i%15 not in (0,1,2)])   # deep interior
    plus5   = mm([5,20,35,50])
    print(f"\n===== {b}  n_symbols={len(rows)} =====")
    print(f"  :00  (H1/H4/D1 close + M15 close + rollover minute)   x{hour0:.4f}")
    print(f"  :15/:30/:45 (M15 close, NOT an hour close)            x{m15only:.4f}")
    print(f"  +5 into the bar (:05/:20/:35/:50)                     x{plus5:.4f}")
    print(f"  bar interior (offsets +3..+14)                        x{interior:.4f}")
    print(f"  --> PURE M15-close premium  (:15/:30/:45 vs interior) {100*(m15only/interior-1):+.2f}%")
    print(f"  --> HOUR-close extra        (:00 vs :15/:30/:45)      {100*(hour0/m15only-1):+.2f}%")
    print(f"  --> total at :00 vs interior                          {100*(hour0/interior-1):+.2f}%")
    print(f"  --> value of waiting 5 min from an M15 close          {100*(1-plus5/m15only):+.2f}% of spread")
    print(f"  --> value of waiting 5 min from an HOUR close         {100*(1-plus5/hour0):+.2f}% of spread")
    json.dump({"minute_of_hour_profile":prof,"n_symbols":len(rows),
               "hour0":hour0,"m15_only":m15only,"plus5":plus5,"interior":interior},
              open(f'/tmp/x6/X6_ISOLATE_{b}.json','w'),indent=1)
