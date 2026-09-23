"""h4: reproduce the swarm's toll decomposition, then substitute LIVE-measured values."""
import sys, json, statistics as st, collections
D='/Users/borr/GTOSActive/worktrees/fable5' # placeholder
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
sys.path.insert(0,D)
import w0_ws
from e_lib import _COMM, _CRYPTO_BPS, TMAP, SLIPMAP, USDCOMM, JPYCOMM
TICK=json.load(open(D+'/L10X_TICK_SPREAD_V1.json'))
LIVE=json.load(open(D+'/L10X_LIVE_COST_PRICEUNITS_V1.json'))
PS={r['symbol']:r for r in json.load(open(D+'/E_PRICESPACE_V1.json'))['per_symbol_live_realisable']}
rows=w0_ws.load()

def comm_px(sym, ep):
    if sym in _CRYPTO_BPS: return _CRYPTO_BPS[sym]*ep/1e4
    if sym=='ETHUSD': return 1.09905
    if sym in ('USDCHF','USDCAD'): return USDCOMM*ep
    if sym=='EURGBP': return USDCOMM*0.74
    return _COMM.get(sym,0.0)

out={}
for sym in sorted(set(r['symbol'] for r in rows)):
    g=[r for r in rows if r['symbol']==sym]
    tk=TICK.get('ftmo:'+TMAP.get(sym,sym))
    spb=tk['spread_bps_median'] if tk and tk.get('spread_bps_median') else None
    slp=LIVE.get(SLIPMAP.get(sym,''),{}).get('slip_px')
    slp=max(slp,0.0) if slp is not None else 0.0
    cb=[comm_px(sym,r['entry_price'])/r['entry_price']*1e4 for r in g]
    sb=[slp/r['entry_price']*1e4 for r in g]
    out[sym]=dict(n_pool=len(g), spread_bps=round(spb,4) if spb else None,
        comm_bps=round(st.mean(cb),4), slip_bps=round(st.mean(sb),4),
        toll_bps_recon=round((spb or 0)+st.mean(cb)+st.mean(sb),4),
        toll_bps_estack=PS.get(sym,{}).get('toll_bps'), n_atmkt=PS.get(sym,{}).get('n'),
        median_ep=round(st.median([r['entry_price'] for r in g]),4),
        median_rd_bps=round(st.median([r['risk_distance']/r['entry_price']*1e4 for r in g]),3))
print('{:12s} {:>6s} {:>7s} {:>8s} {:>7s} {:>8s} {:>9s} {:>6s}'.format('sym','nAtMkt','spread','comm','slip','reconT','estackT','ratio'))
tot=0; totn=0
for s in sorted(out, key=lambda s:-(out[s]['n_atmkt'] or 0)):
    v=out[s]
    r=(v['toll_bps_recon']/v['toll_bps_estack']) if v['toll_bps_estack'] else None
    print('{:12s} {:6d} {:7.4f} {:8.4f} {:7.4f} {:8.4f} {:9.4f} {:6s}'.format(
        s, v['n_atmkt'] or 0, v['spread_bps'] or 0, v['comm_bps'], v['slip_bps'],
        v['toll_bps_recon'], v['toll_bps_estack'] or 0, f'{r:.3f}' if r else 'NA'))
    if v['n_atmkt']: tot+=v['toll_bps_estack']*v['n_atmkt']; totn+=v['n_atmkt']
print('\nn at-market', totn, ' weighted toll from e-stack per-symbol:', round(tot/totn,4))
rec=sum(out[s]['toll_bps_recon']*out[s]['n_atmkt'] for s in out if out[s]['n_atmkt'])/totn
print('weighted toll from MY reconstruction              :', round(rec,4))
json.dump(out, open(D+'/h4_TOLL_DECOMP_V1.json','w'), indent=1)
