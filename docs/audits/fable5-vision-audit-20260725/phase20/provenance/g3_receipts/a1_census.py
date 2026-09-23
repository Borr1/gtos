import sys, collections, statistics, json
sys.path.insert(0,"docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery")
import w0_ws
rows=w0_ws.load()
MINE=("range_extreme_reversion","liquidity_sweep_reclaim","structural_distance_extreme")
days=sorted({r['decision_time_utc'][:10] for r in rows})
print("window:", days[0], "->", days[-1], " n_days", len(days))
print("path_source_timeframe:", collections.Counter(r.get('path_source_timeframe') for r in rows))
print("path_arm_id:", collections.Counter(r.get('path_arm_id') for r in rows))
print("decision_timeframe:", collections.Counter(r.get('decision_timeframe') for r in rows))
print("policy_target_r:", collections.Counter(round(float(r['policy_target_r']),3) for r in rows if r.get('policy_target_r') is not None).most_common(8))
print()
def q(v,p):
    v=sorted(v); 
    if not v: return float('nan')
    i=(len(v)-1)*p; lo=int(i); hi=min(lo+1,len(v)-1); return v[lo]+(v[hi]-lo+lo-i)*0 if lo==hi else v[lo]+(v[hi]-v[lo])*(i-lo)
hdr=f"{'family':34s} {'n':>6s} {'risk_bps_med':>12s} {'risk_bps_p25':>12s} {'risk_bps_p75':>12s} {'spread_r_med':>12s} {'cost_r_med':>11s} {'tgtR':>5s}"
print(hdr); print("-"*len(hdr))
FAMS=collections.Counter(r['origin_family'] for r in rows)
for fam,_ in FAMS.most_common():
    sub=[r for r in rows if r['origin_family']==fam]
    rb=[float(r['risk_distance'])/float(r['entry_price'])*1e4 for r in sub if r.get('entry_price')]
    sp=[float(r['spread_r']) for r in sub if r.get('spread_r') is not None]
    co=[float(r['cost_r']) for r in sub if r.get('cost_r') is not None]
    tg=[float(r['policy_target_r']) for r in sub if r.get('policy_target_r') is not None]
    mark=" *" if fam in MINE else ""
    print(f"{fam+mark:34s} {len(sub):6d} {q(rb,.5):12.3f} {q(rb,.25):12.3f} {q(rb,.75):12.3f} {q(sp,.5):12.4f} {q(co,.5):11.4f} {statistics.median(tg) if tg else float('nan'):5.2f}")
