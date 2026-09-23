"""h4: fill mechanics — partial fills, limit outcomes, latency, deviation, and the per-symbol re-rank."""
import sys, json, statistics as st, collections, datetime as dt
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
E='/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api/'
S='/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/'
sys.path.insert(0,D)
raw=[json.loads(l) for l in open(S+'broker_order_lifecycle_capture_v4.jsonl')]
# ---- partial fills: requested vs result volume; multiple entry deals per position
part=collections.Counter(); vols=[]
for r in raw:
    if r.get('stage')!='entry_fill_reconciled': continue
    oso=r.get('order_send_observation') or {}; req=(oso.get('request') or {}); res=(oso.get('result') or {})
    rv, fv = req.get('volume'), res.get('volume')
    if rv is None or fv is None: part['no_volume_pair']+=1; continue
    vols.append((rv,fv))
    part['exact' if abs(rv-fv)<1e-9 else 'partial_or_over']+=1
print('=== FILL MECHANICS ===')
print('requested vs filled volume:',dict(part))
mism=[(a,b) for a,b in vols if abs(a-b)>1e-9]
print('mismatched volume pairs:',mism[:5],'... n=',len(mism))
# multi-deal entries per position, from broker deal history
multi=collections.Counter()
for b in ('ftmo','redacted_account'):
    ds=[json.loads(l) for l in open(E+f'{b}_history_deals_get.jsonl')]
    bypos=collections.defaultdict(list)
    for d in ds:
        if d['magic']==20260401 and d['type'] in (0,1): bypos[d['position_id']].append(d)
    for p,g in bypos.items():
        ne=sum(1 for x in g if x['entry']==0); nx=sum(1 for x in g if x['entry']==1)
        multi[(b,'entry_deals',ne)]+=1; multi[(b,'exit_deals',nx)]+=1
print('deals per position:',sorted(multi.items()))
# ---- slippage_runtime: latency, outcome, spread capture status
SR=[json.loads(l) for l in open(S+'slippage_runtime.jsonl')]
print('\nslippage_runtime rows:',len(SR))
print('order_outcome_status:',collections.Counter(r.get('order_outcome_status') for r in SR).most_common())
print('fill_price_status   :',collections.Counter(r.get('fill_price_status') for r in SR).most_common())
print('slippage_event_type :',collections.Counter(r.get('slippage_event_type') for r in SR).most_common())
print('trigger             :',collections.Counter(r.get('trigger') for r in SR).most_common())
lat=[r['reject_or_fill_latency_ms'] for r in SR if r.get('reject_or_fill_latency_ms') is not None]
def q(v,p):
    s=sorted(v); return s[max(0,min(len(s)-1,int(round(p*(len(s)-1)))))]
print('latency ms n=%d  p10 %.1f med %.1f p90 %.1f p99 %.1f max %.1f'%(len(lat),q(lat,.1),q(lat,.5),q(lat,.9),q(lat,.99),max(lat)))
pend=[r for r in SR if r.get('pending_age_seconds') is not None]
print('rows with pending_age_seconds:',len(pend))
# spread at request vs fill spread
both=[(r['spread_at_request'],r['fill_spread']) for r in SR if r.get('spread_at_request') is not None and r.get('fill_spread') is not None]
print('spread_at_request == fill_spread on %d/%d rows'%(sum(1 for a,b in both if abs(a-b)<1e-9),len(both)))
json.dump(dict(volume_pairs=dict(part),mismatched=len(mism),
  deals_per_position={str(k):v for k,v in multi.items()},
  outcome=dict(collections.Counter(r.get('order_outcome_status') for r in SR)),
  latency=dict(n=len(lat),p10=q(lat,.1),median=q(lat,.5),p90=q(lat,.9),p99=q(lat,.99),max=max(lat)),
  spread_request_equals_fill=sum(1 for a,b in both if abs(a-b)<1e-9), n_spread_pairs=len(both)),
  open(D+'/h4_FILL_MECHANICS_V1.json','w'),indent=1)

# ---- per-symbol re-rank: e-stack signal_bps vs corrected toll
PS={r['symbol']:r for r in json.load(open(D+'/E_PRICESPACE_V1.json'))['per_symbol_live_realisable']}
CT={r['symbol']:r for r in json.load(open(D+'/h4_CORRECTED_TOLL_V1.json'))['per_symbol']}
print('\n=== PER-SYMBOL EDGE:COST, published vs live-grounded (January at-market) ===')
print('{:12s} {:>5s} {:>9s} {:>9s} {:>9s} {:>8s} {:>8s}'.format('sym','n','signal','tollPub','tollLive','ec_pub','ec_live'))
tab=[]
for s in sorted(PS, key=lambda s:-(PS[s]['signal_bps']/CT[s]['toll_corrected_bps'] if s in CT else -9)):
    p=PS[s]; c=CT.get(s)
    if not c: continue
    ecp=p['signal_bps']/p['toll_bps']; ecl=p['signal_bps']/c['toll_corrected_bps']
    tab.append(dict(symbol=s,n=p['n'],signal_bps=p['signal_bps'],toll_pub=p['toll_bps'],
        toll_live=c['toll_corrected_bps'],ec_pub=round(ecp,4),ec_live=round(ecl,4),
        net_pub=round(p['signal_bps']-p['toll_bps'],4),net_live=round(p['signal_bps']-c['toll_corrected_bps'],4)))
    print('{:12s} {:5d} {:9.4f} {:9.4f} {:9.4f} {:8.3f} {:8.3f}'.format(s,p['n'],p['signal_bps'],p['toll_bps'],c['toll_corrected_bps'],ecp,ecl))
json.dump(tab, open(D+'/h4_PERSYMBOL_RERANK_V1.json','w'), indent=1)
