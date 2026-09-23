"""h4: cost is HOUR-STRUCTURED. Per-symbol toll by broker-hour band + the cells that opens."""
import sys, json, statistics as st, collections, datetime as dt
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
E='/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api/'
sys.path.insert(0,D); sys.path.insert(0,'/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801')
import w0_ws
from e_lib import TMAP
from src.utils import broker_clock as BC
TICK=json.load(open(D+'/L10X_TICK_SPREAD_V1.json'))
PSY=json.load(open(D+'/E_ATMKT_PERSYMBOL_V1.json'))
CT={r['symbol']:r for r in json.load(open(D+'/h4_CORRECTED_TOLL_V1.json'))['per_symbol']}
rows=w0_ws.load(); RULE=BC.resolve_rule('FTMO-Server3')
SLIP=0.1165
BANDS={'asia_bh_00_08':range(0,9),'euro_bh_09_13':range(9,14),'us_bh_14_18':range(14,19),'late_bh_19_23':range(19,24)}
tab={}
for sym in sorted(PSY):
    tk=TICK.get('ftmo:'+TMAP.get(sym,sym))
    if not tk: continue
    byh=tk.get('spread_bps_median_by_broker_hour') or {}
    g=[r for r in rows if r['symbol']==sym]
    hh=[BC.utc_to_broker_naive(dt.datetime.fromisoformat(r['decision_time_utc']),RULE).hour for r in g]
    comm=CT[sym]['comm_live_bps']
    blk={}
    for bn,rg in BANDS.items():
        idx=[i for i,h in enumerate(hh) if h in rg]
        sp=[byh[str(h)] for h in (hh[i] for i in idx) if str(h) in byh]
        if not sp: continue
        blk[bn]=dict(n=len(idx),share=round(len(idx)/len(g),4),spread_bps=round(st.mean(sp),4),
                     toll_bps=round(st.mean(sp)+comm+SLIP,4))
    best=min(blk.items(),key=lambda kv:kv[1]['toll_bps'])
    worst=max(blk.items(),key=lambda kv:kv[1]['toll_bps'])
    tab[sym]=dict(n_pool=len(g),comm_live_bps=comm,bands=blk,
        cheapest_band=best[0],cheapest_toll=best[1]['toll_bps'],cheapest_share=best[1]['share'],
        dearest_band=worst[0],dearest_toll=worst[1]['toll_bps'],
        dispersion=round(worst[1]['toll_bps']/best[1]['toll_bps'],3),
        edge_bps=PSY[sym]['edge_bps'], toll_all_hours=CT[sym]['toll_corrected_bps'],
        ratio_all_hours=round(PSY[sym]['edge_bps']/CT[sym]['toll_corrected_bps'],4),
        ratio_cheapest_band=round(PSY[sym]['edge_bps']/best[1]['toll_bps'],4))
print('=== TOLL BY BROKER-HOUR BAND (spread hour-medians + live commission + live entry slip) ===')
print('{:12s} {:>7s} {:>9s} {:>7s} {:>16s} {:>9s} {:>6s} {:>8s} {:>9s}'.format(
  'sym','edge','tollAll','ratAll','cheapestBand','tollChp','share','ratChp','disp'))
for s in sorted(tab,key=lambda s:-tab[s]['ratio_cheapest_band']):
    v=tab[s]
    print('{:12s} {:7.4f} {:9.4f} {:7.3f} {:>16s} {:9.4f} {:6.3f} {:8.3f} {:9.2f}'.format(
      s,v['edge_bps'],v['toll_all_hours'],v['ratio_all_hours'],v['cheapest_band'],v['cheapest_toll'],
      v['cheapest_share'],v['ratio_cheapest_band'],v['dispersion']))
print('\ncells with edge:cost>1 restricted to the cheapest hour band (edge assumed hour-invariant): %d'%
      sum(1 for v in tab.values() if v['ratio_cheapest_band']>1))
json.dump(tab, open(D+'/h4_HOURBAND_TOLL_V1.json','w'), indent=1)
