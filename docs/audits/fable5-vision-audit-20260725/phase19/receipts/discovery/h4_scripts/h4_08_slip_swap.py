import sys, json, statistics as st, collections, datetime as dt
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
sys.path.insert(0,D); sys.path.insert(0,'/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801')
import w0_ws
from src.utils import broker_clock as BC
L=json.load(open(D+'/h4_FILL_LEDGER_RAW.json'))
PS={r['symbol']:r for r in json.load(open(D+'/E_PRICESPACE_V1.json'))['per_symbol_live_realisable']}
CLS={'BTCUSD':'crypto','ETHUSD':'crypto','XAUUSD':'metals','XAGUSD':'metals'}
def cls(sym):
    if sym in CLS: return CLS[sym]
    if sym.endswith('_cash') or sym in ('UK100','JP225','GER40','NAS100','SPX500','US30_cash','NDX100','US30','GER30','US500'): return 'index'
    if 'OIL' in sym.upper() or sym.startswith('UKO') or sym.startswith('USO'): return 'energy'
    return 'fx'
def agg(v,r=6):
    v=[x for x in v if x is not None]
    if not v: return None
    s=sorted(v)
    def q(p): return s[max(0,min(len(s)-1,int(round(p*(len(s)-1)))))]
    return dict(n=len(v),mean=round(st.mean(v),r),median=round(q(.5),r),p10=round(q(.1),r),p90=round(q(.9),r),
                p99=round(q(.99),r),min=round(min(v),r),max=round(max(v),r))
RULES={'ftmo':BC.resolve_rule('FTMO-Server3'),'redacted_account':BC.resolve_rule('redacted_account-Server 2')}
def sess(h):
    return 'asia_00_07' if h<7 else 'london_07_12' if h<12 else 'ny_overlap_12_17' if h<17 else 'late_ny_17_24'

F=[]
for x in L:
    if not (x['fill'] and x['req']): continue
    sign=1.0 if x['side']=='LONG' else -1.0
    slip_px=(x['fill']-x['req'])*sign
    t=dt.datetime.fromisoformat(x['t'])
    F.append(dict(sym=x['sym'],bsym=x['bsym'],broker=x['broker'],cls=cls(x['bsym']),
      slip_bps=slip_px/x['req']*1e4, slip_r=(slip_px/x['m_sl_dist']) if x['m_sl_dist'] else None,
      rd_bps=(x['m_sl_dist']/x['req']*1e4) if x['m_sl_dist'] else None,
      utc_h=t.hour, sess=sess(t.hour), broker_h=BC.utc_to_broker_naive(t,RULES[x['broker']]).hour))
print('=== C. ENTRY SLIPPAGE vs the modelled flat 0.02 R ===')
print('POOLED       ', 'R:',agg([f['slip_r'] for f in F]), )
print('POOLED bps   ', agg([f['slip_bps'] for f in F],4))
print('modelled flat 0.02 R -> in bps at LIVE stop widths: %.4f (live median rd_bps %.3f)'%(
   0.02*st.median([f['rd_bps'] for f in F if f['rd_bps']]), st.median([f['rd_bps'] for f in F if f['rd_bps']])))
over=sum(1 for f in F if f['slip_r'] is not None and f['slip_r']<0.02)
print('fills where realised slip < modelled 0.02 R: %d/%d = %.4f'%(over,len(F),over/len(F)))
out={'pooled_slip_r':agg([f['slip_r'] for f in F]),'pooled_slip_bps':agg([f['slip_bps'] for f in F],4),
     'model_flat_slip_r':0.02,'overcharged_share':round(over/len(F),4)}
for key,fn in (('by_class',lambda f:f['cls']),('by_session_trueUTC',lambda f:f['sess']),('by_broker',lambda f:f['broker'])):
    blk={}
    for g in sorted(set(fn(f) for f in F)):
        s=[f for f in F if fn(f)==g]
        blk[g]=dict(n=len(s),slip_r=agg([f['slip_r'] for f in s]),slip_bps=agg([f['slip_bps'] for f in s],4),
                    median_rd_bps=round(st.median([f['rd_bps'] for f in s if f['rd_bps']]),3))
    out[key]=blk
    print(f'\n--- {key} ---')
    for g,v in blk.items():
        print('  {:20s} n={:3d} slip_R mean {:+.6f} med {:+.6f} | slip_bps mean {:+.4f} med {:+.4f}'.format(
          g,v['n'],v['slip_r']['mean'],v['slip_r']['median'],v['slip_bps']['mean'],v['slip_bps']['median']))
persym={}
for s in sorted(set(f['bsym'] for f in F)):
    g=[f for f in F if f['bsym']==s]
    persym[s]=dict(n=len(g),slip_r=agg([f['slip_r'] for f in g]),slip_bps=agg([f['slip_bps'] for f in g],4))
out['per_broker_symbol']=persym
json.dump(out, open(D+'/h4_SLIPPAGE_TRUTH_V1.json','w'), indent=1)

# ---------- E. SWAP AT A 2 HOUR HORIZON: does the pool cross a rollover?
rows=w0_ws.load()
RULE=RULES['ftmo']
cross=0; tot=0; bycross=collections.Counter()
for r in rows:
    t=dt.datetime.fromisoformat(r['decision_time_utc'])
    b0=BC.utc_to_broker_naive(t,RULE); b1=BC.utc_to_broker_naive(t+dt.timedelta(hours=2),RULE)
    tot+=1
    if b1.date()!=b0.date(): cross+=1; bycross[r['symbol']]+=1
print('\n=== E. SWAP AT THE POOL 2 h HORIZON (FTMO broker clock) ===')
print('pool rows whose [decision, +2h] window crosses broker midnight: %d/%d = %.4f'%(cross,tot,cross/tot))
print('top symbols crossing:',bycross.most_common(6))
out2=dict(n_pool=tot,n_cross_rollover_2h=cross,share=round(cross/tot,6),by_symbol=dict(bycross))
json.dump(out2, open(D+'/h4_SWAP_AT_2H_V1.json','w'), indent=1)
