"""KB7 — build leadlag candidate streams: full H4 leadlag_core (from W5 cache),
the highest-Sharpe H4 subset (US30->USDJPY + NAS<->SPX), and per-leg stats so we can
choose the strongest subset by leg-level Sharpe/EV. Also recompute subh4 fx core.
All from cached streams + the fold generators (leak-free, deep-train where it exists).
"""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'../../..')
import pickle, statistics, collections, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
import KB5_fold_new_sleeves as F

def leg_stats(rows):
    R=[r['R'] for r in rows]; n=len(R)
    if n==0: return None
    m=sum(R)/n; sd=statistics.pstdev(R) if n>1 else 0
    w=100*sum(1 for x in R if x>0)/n
    tr=[r['R'] for r in rows if r['year']<=2024]; fw=[r['R'] for r in rows if r['year']>=2025]
    by=collections.defaultdict(list)
    for r in rows: by[r['year']].append(r['R'])
    py={y:(len(v),round(sum(v)/len(v),3)) for y,v in sorted(by.items())}
    posyears=sum(1 for y,(c,e) in py.items() if e>0)
    return dict(n=n, ev=round(m,3), sharpe=round(m/sd,3) if sd>0 else 0, win=round(w,1),
                trN=len(tr), trEV=round(sum(tr)/len(tr),3) if tr else None,
                fwN=len(fw), fwEV=round(sum(fw)/len(fw),3) if fw else None,
                posyears=posyears, nyears=len(py), per_year=py)

# per-leg H4 leadlag (re-mine each leg of LEADLAG_CORE individually)
print("=== H4 leadlag_core PER-LEG (deep H4, growth lens: Sharpe + EV + posyears) ===")
legstats={}
for cfg in F.LEADLAG_CORE:
    L,Fl=cfg[0],cfg[1]
    rows=[dict(sleeve='leg', **r) for r in F._mine_cfg(cfg)]
    s=leg_stats(rows)
    legstats[f"{L}->{Fl}"]=dict(cfg=str(cfg), **s)
    print(f"  {L:>10}->{Fl:<8} n={s['n']:>4} EV={s['ev']:+.3f} Sh={s['sharpe']:+.3f} win={s['win']:>4} | TRAIN {s['trEV']} (n{s['trN']}) FWD {s['fwEV']} (n{s['fwN']}) posyr {s['posyears']}/{s['nyears']}")

# rank by sharpe
rank=sorted(legstats.items(), key=lambda kv:-(kv[1]['sharpe']))
print("\n  rank by Sharpe:", [k for k,_ in rank])

# build named subsets
SUBSETS={
 'leadlag_full': F.LEADLAG_CORE,
 'leadlag_hisharpe2': [c for c in F.LEADLAG_CORE if (c[0],c[1]) in {('US30_cash','USDJPY'),('NAS100','SPX500'),('SPX500','NAS100')}],
 'leadlag_top4': None,  # filled below by sharpe rank
}
top4names=set(tuple(legstats[k]['cfg'][1:-1].split(', ')[0:2]) for k,_ in rank[:4])
# simpler: pick top-4 cfgs by sharpe
cfg_by_pair={(c[0],c[1]):c for c in F.LEADLAG_CORE}
ranked_pairs=[tuple(k.split('->')) for k,_ in rank]
SUBSETS['leadlag_top4']=[cfg_by_pair[('US30_cash' if p[0]=='US30_cash' else p[0], p[1])] for p in ranked_pairs[:4] if (p[0],p[1]) in cfg_by_pair]

out={'leg_stats':legstats, 'subsets':{}}
for nm,cfgs in SUBSETS.items():
    rows=[]
    for cfg in cfgs:
        for r in F._mine_cfg(cfg): rows.append(dict(sleeve=nm,**r))
    s=leg_stats(rows)
    out['subsets'][nm]=dict(legs=[f"{c[0]}->{c[1]}" for c in cfgs], **{k:v for k,v in s.items() if k!='per_year'}, per_year=s['per_year'])
    pickle.dump(rows, open(HERE/f'KB7_stream_{nm}.pkl','wb'))
    print(f"\n[{nm}] legs={out['subsets'][nm]['legs']}")
    print(f"   n={s['n']} EV={s['ev']:+.3f} Sharpe={s['sharpe']:+.3f} win={s['win']} | TRAIN {s['trEV']}(n{s['trN']}) FWD {s['fwEV']}(n{s['fwN']}) posyr {s['posyears']}/{s['nyears']}")

json.dump(out, open(HERE/'KB7_leadlag_subsets.json','w'), indent=1, default=str)
print("\nwrote KB7_leadlag_subsets.json + KB7_stream_*.pkl")
