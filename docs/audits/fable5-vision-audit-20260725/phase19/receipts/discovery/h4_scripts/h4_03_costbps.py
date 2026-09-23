"""h4: realised per-fill cost in bps of notional, from live broker records."""
import json, collections, statistics as st, datetime as dt, math
E='/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api/'
S='/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/'
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'

specs={b:json.load(open(E+f'{b}_symbol_specs_traded.json')) for b in ('ftmo','redacted_account')}
deals={b:[json.loads(l) for l in open(E+f'{b}_history_deals_get.jsonl')] for b in ('ftmo','redacted_account')}

def usd_per_px_lot(b,sym):
    s=specs[b].get(sym)
    if not s: return None
    tv,ts=s.get('trade_tick_value'),s.get('trade_tick_size')
    if not tv or not ts: return None
    return tv/ts

# ---------------- COMMISSION: measured per deal, in price units per lot and bps of notional
rows=[]
for b in ('ftmo','redacted_account'):
    for d in deals[b]:
        if not d['symbol'] or d['type'] not in (0,1): continue
        if d['magic']!=20260401: continue      # strategy magic only (excludes smoke/preflight)
        upl=usd_per_px_lot(b,d['symbol'])
        if not upl or not d['volume'] or not d['price']: continue
        notional=d['volume']*upl*d['price']
        comm=abs(d['commission']); swp=d['swap']
        rows.append(dict(b=b,sym=d['symbol'],entry=d['entry'],vol=d['volume'],px=d['price'],
            time=d['time'],upl=upl,notional=notional,
            comm_usd=comm, comm_px_per_lot=comm/(d['volume']*upl),
            comm_bps=comm/notional*1e4,
            swap_usd=swp, swap_bps=(-swp)/notional*1e4 if swp else 0.0,
            pos=d['position_id']))
print('strategy deals costed:',len(rows))

def agg(v):
    v=[x for x in v if x is not None]
    if not v: return None
    v2=sorted(v)
    def q(p): return v2[max(0,min(len(v2)-1,int(round(p*(len(v2)-1)))))]
    return dict(n=len(v),mean=round(st.mean(v),6),median=round(q(.5),6),p10=round(q(.1),6),p90=round(q(.9),6),
                min=round(min(v),6),max=round(max(v),6),
                sd=round(st.pstdev(v),6) if len(v)>1 else 0.0)

# per symbol per broker: entry-side commission bps (one side) and round-turn (entry+exit on same position)
bypos=collections.defaultdict(list)
for r in rows: bypos[(r['b'],r['pos'])].append(r)
rt=[]
for (b,pos),g in bypos.items():
    ins=[x for x in g if x['entry']==0]; outs=[x for x in g if x['entry']==1]
    if not ins: continue
    e=ins[0]
    comm_rt=sum(x['comm_usd'] for x in g)
    notional=e['notional']
    swap_tot=sum(x['swap_usd'] for x in g)
    rt.append(dict(b=b,sym=e['sym'],pos=pos,time=e['time'],vol=e['vol'],px=e['px'],notional=notional,
        comm_rt_usd=comm_rt, comm_rt_bps=comm_rt/notional*1e4,
        comm_rt_px=comm_rt/(e['vol']*e['upl']),
        swap_usd=swap_tot, swap_bps=(-swap_tot)/notional*1e4,
        n_out=len(outs)))
print('positions with entry deal:',len(rt))

persym={}
for b in ('ftmo','redacted_account'):
    for sym in sorted(set(x['sym'] for x in rt if x['b']==b)):
        g=[x for x in rt if x['b']==b and x['sym']==sym]
        persym[f'{b}:{sym}']=dict(n=len(g),
            comm_rt_bps=agg([x['comm_rt_bps'] for x in g]),
            comm_rt_px=agg([x['comm_rt_px'] for x in g]),
            swap_bps=agg([x['swap_bps'] for x in g]),
            median_px=round(st.median([x['px'] for x in g]),6),
            median_notional=round(st.median([x['notional'] for x in g]),2),
            pct_any_swap=round(sum(1 for x in g if abs(x['swap_usd'])>1e-9)/len(g),4))
json.dump(dict(n_deals=len(rows),n_positions=len(rt),per_symbol=persym,
    pooled_comm_rt_bps=agg([x['comm_rt_bps'] for x in rt]),
    pooled_swap_bps=agg([x['swap_bps'] for x in rt]),
    pooled_pct_any_swap=round(sum(1 for x in rt if abs(x['swap_usd'])>1e-9)/len(rt),4)),
  open(D+'/h4_COMMISSION_TRUTH_V1.json','w'), indent=1)
print('POOLED comm round-turn bps:', agg([x['comm_rt_bps'] for x in rt]))
print('POOLED swap bps (whole hold):', agg([x['swap_bps'] for x in rt]))
print('pct positions with any swap:', round(sum(1 for x in rt if abs(x['swap_usd'])>1e-9)/len(rt),4))
print()
for k in sorted(persym, key=lambda k:-persym[k]['n'])[:30]:
    v=persym[k]
    print(f"{k:28s} n={v['n']:3d} commRT={v['comm_rt_bps']['median']:9.4f} bps  swap={v['swap_bps']['median']:8.4f} bps  px={v['median_px']:10.2f}")
