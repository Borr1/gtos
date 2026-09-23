"""h4: per-fill realised cost in bps at the real fill instants, vs the swarm's broker-true model."""
import json, collections, statistics as st, datetime as dt
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
L=json.load(open(D+'/h4_FILL_LEDGER_RAW.json'))
TICK=json.load(open(D+'/L10X_TICK_SPREAD_V1.json'))

def agg(v,r=6):
    v=[x for x in v if x is not None]
    if not v: return None
    s=sorted(v)
    def q(p): return s[max(0,min(len(s)-1,int(round(p*(len(s)-1)))))]
    return dict(n=len(v),mean=round(st.mean(v),r),median=round(q(.5),r),p10=round(q(.1),r),p25=round(q(.25),r),
                p75=round(q(.75),r),p90=round(q(.9),r),min=round(min(v),r),max=round(max(v),r))

F=[]
for x in L:
    if not (x['fill'] and x['req'] and x['ask'] and x['bid']): continue
    upl=(x['tickval']/x['ticksize']) if x['tickval'] and x['ticksize'] else None
    mid=(x['ask']+x['bid'])/2.0
    spread_px=x['ask']-x['bid']
    sign=1.0 if x['side']=='LONG' else -1.0
    slip_px=(x['fill']-x['req'])*sign
    comm_usd=abs(x['comm']) if x['comm'] is not None else None
    comm_px=(comm_usd/(x['vol']*upl)) if (comm_usd is not None and upl and x['vol']) else None
    t=dt.datetime.fromisoformat(x['t'])
    F.append(dict(sym=x['sym'],bsym=x['bsym'],broker=x['broker'],side=x['side'],t=x['t'],hour=t.hour,
        vol=x['vol'],req=x['req'],fill=x['fill'],mid=mid,upl=upl,
        spread_px=spread_px, spread_bps=spread_px/mid*1e4,
        slip_px=slip_px, slip_bps=slip_px/x['req']*1e4,
        slip_r=(slip_px/x['m_sl_dist']) if x['m_sl_dist'] else None,
        comm_usd=comm_usd, comm_px_1side=comm_px,
        comm_bps_1side=(comm_px/x['req']*1e4) if comm_px is not None else None,
        swap_usd=x['swap'], m_spread_px=x['m_spread_px'], m_spread_r=x['m_spread_r'],
        m_slip_r=x['m_slip_r'], sl_dist=x['m_sl_dist'],
        risk_bps=(x['m_sl_dist']/x['req']*1e4) if x['m_sl_dist'] else None))
print('fills costed:',len(F))
print('spread_px == modelled spread_price:', sum(1 for f in F if abs((f['spread_px'] or 0)-(f['m_spread_px'] or 0))<1e-9),'/',len(F))

# ---- per broker-symbol: realised spread bps at fill instants vs tick-archive median
cmp={}
for k in sorted(set((f['broker'],f['bsym']) for f in F)):
    g=[f for f in F if (f['broker'],f['bsym'])==k]
    tk=TICK.get(f"{k[0]}:{k[1]}")
    cmp[f'{k[0]}:{k[1]}']=dict(n=len(g),
        live_spread_bps=agg([f['spread_bps'] for f in g],4),
        tick_archive_spread_bps_median=round(tk['spread_bps_median'],4) if tk and tk.get('spread_bps_median') else None,
        tick_archive_p90=round(tk['spread_bps_p90'],4) if tk and tk.get('spread_bps_p90') else None,
        live_slip_bps=agg([f['slip_bps'] for f in g],4),
        live_slip_r=agg([f['slip_r'] for f in g],6),
        comm_bps_1side=agg([f['comm_bps_1side'] for f in g],4),
        risk_bps=agg([f['risk_bps'] for f in g],2))
json.dump(dict(n=len(F),per_symbol=cmp,
    pooled_spread_bps=agg([f['spread_bps'] for f in F],4),
    pooled_slip_bps=agg([f['slip_bps'] for f in F],4),
    pooled_slip_r=agg([f['slip_r'] for f in F],6),
    pooled_comm_bps_1side=agg([f['comm_bps_1side'] for f in F],4),
    pooled_risk_bps=agg([f['risk_bps'] for f in F],2)),
  open(D+'/h4_FILL_COST_BPS_V1.json','w'), indent=1)

print('\nPOOLED live spread bps :',cmp and agg([f['spread_bps'] for f in F],4))
print('POOLED live slip   bps :',agg([f['slip_bps'] for f in F],4))
print('POOLED live slip   R   :',agg([f['slip_r'] for f in F],6))
print('POOLED comm 1side  bps :',agg([f['comm_bps_1side'] for f in F],4))
print('POOLED risk-dist   bps :',agg([f['risk_bps'] for f in F],2))
print('\n{:26s} {:>3s} {:>10s} {:>10s} {:>7s} {:>9s}'.format('broker:symbol','n','liveSprMed','tickArchMed','ratio','slipBpsMed'))
for k in sorted(cmp, key=lambda k:-cmp[k]['n']):
    v=cmp[k]; a=v['live_spread_bps']['median']; b=v['tick_archive_spread_bps_median']
    r=(a/b) if b else None
    print('{:26s} {:3d} {:10.4f} {:>10s} {:>7s} {:9.4f}'.format(k,v['n'],a, f'{b:.4f}' if b else 'NA', f'{r:.3f}' if r else 'NA', v['live_slip_bps']['median']))
