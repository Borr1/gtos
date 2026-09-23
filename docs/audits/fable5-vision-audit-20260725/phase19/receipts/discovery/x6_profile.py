import json, statistics
def load(b):
    d=json.load(open(f'/tmp/x6/X6_SPREAD_MINUTE_{b}.json'))
    return [s for s in d['symbols'] if not s.get('error')]

def profile(S, key, n):
    """cross-symbol profile: each symbol normalised by ITS OWN mean across the buckets,
    so a symbol with a wide absolute spread cannot dominate."""
    rows=[]
    for s in S:
        v=[s[key].get(str(i)) for i in range(n)]
        if any(x is None for x in v): continue
        m=sum(v)/len(v)
        if m<=0: continue
        rows.append([x/m for x in v])
    if not rows: return None,0
    return [statistics.mean(r[i] for r in rows) for i in range(n)], len(rows)

for b in ("ftmo","redacted_account"):
    try: S=load(b)
    except FileNotFoundError: print(f"{b}: not ready"); continue
    print(f"\n########## {b}  n_symbols={len(S)}  ticks={sum(s['n_ticks_parsed'] for s in S):,}")
    p,n = profile(S,'m15_offset_median',15)
    print(f"--- spread by MINUTE-WITHIN-M15 (normalised to each symbol's own 15-bucket mean), n={n} ---")
    for i,x in enumerate(p): print(f"   +{i:02d} min  x{x:.4f}" + ("   <-- BAR BOUNDARY (every decision lands here)" if i==0 else ""))
    print(f"   boundary premium vs mean of +1..+14 : {p[0]/statistics.mean(p[1:]):.4f}  ({100*(p[0]/statistics.mean(p[1:])-1):+.2f}%)")
    print(f"   boundary premium vs +5              : {p[0]/p[5]:.4f}  ({100*(p[0]/p[5]-1):+.2f}%)")
    q,n2 = profile(S,'m15_offset_ticks_per_min_median',15)
    print(f"--- TICKS PER MINUTE by minute-within-M15 (same normalisation), n={n2} ---")
    for i,x in enumerate(q): print(f"   +{i:02d} min  x{x:.4f}" + ("   <-- BAR BOUNDARY" if i==0 else ""))
    print(f"   boundary activity vs mean of +1..+14: {q[0]/statistics.mean(q[1:]):.4f}  ({100*(q[0]/statistics.mean(q[1:])-1):+.2f}%)")
    r,n3 = profile(S,'moh_median',60)
    print(f"--- spread by MINUTE-OF-HOUR, first 10 + last 3 (n={n3}) ---")
    for i in list(range(10))+[57,58,59]: print(f"   :{i:02d}  x{r[i]:.4f}" + ("   <-- H1/H4/D1 CLOSE" if i==0 else ""))
    print(f"   hour-boundary premium vs :05..:55 mean: {r[0]/statistics.mean(r[5:56]):.4f}  ({100*(r[0]/statistics.mean(r[5:56])-1):+.2f}%)")
    json.dump({"m15_offset_profile":p,"ticks_per_min_profile":q,"minute_of_hour_profile":r,
               "n_symbols":len(S),"n_ticks":sum(s['n_ticks_parsed'] for s in S)},
              open(f'/tmp/x6/X6_PROFILE_{b}.json','w'),indent=1)
