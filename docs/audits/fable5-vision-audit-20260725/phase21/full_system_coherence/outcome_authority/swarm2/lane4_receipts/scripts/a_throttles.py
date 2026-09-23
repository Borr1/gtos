"""LANE 4 (A/D): price every FUNNEL-surface throttle by A/B on the frozen protocol.
Reuses lane I's proved-equivalent protocol implementation (read-only import).
"""
import json, sys, numpy as np, pandas as pd
from pathlib import Path
sys.path.insert(0, "/tmp/lane_i")
import protocol as P
OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane4")
rng = np.random.default_rng(20260812)
MONTHS = ["feb","apr","may","jun","jul"]

df = pd.read_parquet("/tmp/lane_i/pop.parquet")
for c in ('month','symbol','lifecycle_label_status','proposed_order_type','origin_family','trading_day','utc_session','decision_window_id','candidate_occurrence_key'):
    df[c] = df[c].astype(str)
df['net'] = pd.to_numeric(df.terminal_net_r, errors='coerce').fillna(0.0)
df['filled'] = df.lifecycle_label_status.str.startswith('RESOLVED_FILLED_')

def arrays_for(d):
    return {'symbol': d.symbol.to_numpy(), 'end': d.label_span_end_utc.fillna(d.expiry_utc).to_numpy(),
            'cost_r': d.cost_r.to_numpy(), 'key': d.candidate_occurrence_key.to_numpy(),
            'is_market': (d.proposed_order_type.to_numpy()=='MARKET'),
            'resolved': d.resolved.to_numpy(), 'net_r': d.net.to_numpy(),
            'deductible_cost_r': d.deductible_cost_r.to_numpy()}

def run_arm(d, *, policy, threshold, symbol_occupancy=True, per_window=1, score=None):
    """Generalised protocol. per_window>1 relaxes one-trade-per-window; symbol_occupancy=False
    removes the same-symbol block. Returns selected index positions into d."""
    a = arrays_for(d); sc = d.pred_month_boundary.to_numpy() if score is None else score
    sym, end, cost, key, mkt = a['symbol'], a['end'], a['cost_r'], a['key'], a['is_market']
    start = d.label_span_start_utc.to_numpy()
    wid = d.decision_window_id.to_numpy()
    from collections import defaultdict
    by = defaultdict(list)
    for i in range(len(d)): by[wid[i]].append(i)
    ordered = sorted(by.items(), key=lambda kv: (min(start[i] for i in kv[1]), kv[0]))
    active = {}; sel=[]; disp=defaultdict(int)
    for _k, idx in ordered:
        dat = min(start[i] for i in idx)
        for s in [s for s,e in active.items() if e <= dat]: del active[s]
        cands=[]
        for i in idx:
            if symbol_occupancy and sym[i] in active: continue
            if np.isnan(sc[i]): continue
            if policy=="market_rerank" and not mkt[i]: continue
            cands.append((sc[i], -cost[i], key[i], i))
        if not cands: disp['no_available_candidate']+=1; continue
        cands.sort(key=lambda t: t[:3], reverse=True)
        taken=0; local_sym=set()
        for c in cands:
            if taken>=per_window: break
            i=c[3]
            if symbol_occupancy and (sym[i] in active or sym[i] in local_sym): continue
            if c[0] < threshold:
                if taken==0: disp['top_below_threshold']+=1
                break
            if policy=="market_top_abstain" and not mkt[i]:
                if taken==0: disp['top_limit_abstain']+=1
                break
            sel.append(i); taken+=1; local_sym.add(sym[i])
            if symbol_occupancy: active[sym[i]] = end[i]
        if taken: disp['trade']+=taken
    return np.asarray(sel, dtype=np.int64), dict(sorted(disp.items()))

def book(d, sel):
    if len(sel)==0: return dict(trades=0, resolved=0, net_r=0.0, per_trade=None, worst=0.0, sd=None, t=None)
    res = d.resolved.to_numpy()[sel]; net = d.net.to_numpy()[sel]; dc = d.deductible_cost_r.to_numpy()[sel]
    actual = float(np.sum(np.where(res, net, 0.0)))
    worst = actual + float(np.sum(np.where(~res, -1.0-dc, 0.0)))
    r = net[res]
    return dict(trades=int(len(sel)), resolved=int(res.sum()), net_r=round(actual,4),
                per_trade=round(actual/max(res.sum(),1),6), worst=round(worst,4),
                sd=round(float(np.std(r, ddof=1)),4) if len(r)>1 else None,
                t=round(float(np.mean(r)/(np.std(r,ddof=1)/np.sqrt(len(r)))),3) if len(r)>1 else None)

results = {}
# eligibility gate A/B: cost_r <= 0.20 (the funnel's own admission gate)
allrows = df[df.predecision_geometry_valid & df.cost_r.notna() & np.isfinite(df.cost_r)].copy()
gate_in  = allrows[allrows.cost_r <= 0.20]
gate_out = allrows[allrows.cost_r >  0.20]
def desc(d, label):
    f = d[d.filled]
    return {'label':label,'rows':int(len(d)),'filled':int(len(f)),
            'mean_net_r_filled': float(f.net.mean()) if len(f) else None,
            'sd_net_r_filled': float(f.net.std(ddof=1)) if len(f)>1 else None,
            'median_cost_r': float(d.cost_r.median()),
            'per_month_rows': round(len(d)/5,1),'per_month_filled': round(len(f)/5,1)}
results['T5_cost_gate_0p20'] = {'kept': desc(gate_in,'cost_r<=0.20 (admitted)'),
                                'removed': desc(gate_out,'cost_r>0.20 (EXCLUDED by gate)')}
# geometry gate
geo_out = df[~df.predecision_geometry_valid]
results['T6_predecision_geometry_valid'] = {'removed_rows': int(len(geo_out)),
        'removed_filled': int(geo_out.filled.sum()),
        'removed_mean_net_r_filled': float(geo_out[geo_out.filled].net.mean()) if geo_out.filled.sum() else None}

el = df[df.eligible & df.pred_month_boundary.notna()].copy().reset_index(drop=True)
results['eligible_scored_rows'] = int(len(el))

ARMS = {
 'A0_frozen_rule':                dict(policy='market_top_abstain', threshold=0.10, symbol_occupancy=True, per_window=1),
 'A1_no_market_abstain_rerank':   dict(policy='market_rerank',      threshold=0.10, symbol_occupancy=True, per_window=1),
 'A2_no_market_abstain_mixed':    dict(policy='mixed',              threshold=0.10, symbol_occupancy=True, per_window=1),
 'A3_no_min_R_floor':             dict(policy='market_top_abstain', threshold=-1e18, symbol_occupancy=True, per_window=1),
 'A4_no_floor_no_abstain':        dict(policy='mixed',              threshold=-1e18, symbol_occupancy=True, per_window=1),
 'A5_two_per_window':             dict(policy='market_top_abstain', threshold=0.10, symbol_occupancy=True, per_window=2),
 'A6_five_per_window':            dict(policy='market_top_abstain', threshold=0.10, symbol_occupancy=True, per_window=5),
 'A7_no_symbol_occupancy':        dict(policy='market_top_abstain', threshold=0.10, symbol_occupancy=False, per_window=1),
 'A8_all_throttles_off_k5':       dict(policy='mixed',              threshold=-1e18, symbol_occupancy=False, per_window=5),
 'A9_all_throttles_off_k99':      dict(policy='mixed',              threshold=-1e18, symbol_occupancy=False, per_window=99),
}
arm_out = {}
for name, kw in ARMS.items():
    per_month = {}
    tot_sel = []
    for m in MONTHS:
        d = el[el.month==m].reset_index(drop=True)
        sel, disp = run_arm(d, **kw)
        b = book(d, sel); b['dispositions']=disp
        per_month[m]=b
        tot_sel.append((m, len(sel), b['net_r']))
    trades = sum(x[1] for x in tot_sel); netr = sum(x[2] for x in tot_sel)
    arm_out[name] = {'params':kw,'per_month':per_month,'total_trades':trades,
                     'trades_per_month': round(trades/5,2), 'total_net_r': round(netr,4),
                     'net_r_per_month': round(netr/5,4),
                     'months_positive': sum(1 for x in tot_sel if x[2]>0)}
results['arms'] = arm_out
(OUT/"A_THROTTLE_CENSUS_FUNNEL_V1.json").write_text(json.dumps(results, indent=1, default=str))
print(json.dumps(results['T5_cost_gate_0p20'], indent=1))
for k,v in arm_out.items():
    print(f"{k:32s} trades/mo={v['trades_per_month']:9.2f}  netR/mo={v['net_r_per_month']:9.3f}  months+={v['months_positive']}/5")
