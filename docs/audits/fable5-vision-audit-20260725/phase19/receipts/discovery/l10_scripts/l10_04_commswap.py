import json, datetime as dt
from collections import Counter, defaultdict
BASE='/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api'
OUTD='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
out={}
for acct in ['ftmo','redacted_account']:
    deals=[json.loads(l) for l in open(f'{BASE}/{acct}_history_deals_get.jsonl')]
    trade=[d for d in deals if d['type'] in (0,1) and d['symbol']]
    per=defaultdict(lambda: dict(n_in=0,n_out=0,vol_in=0.0,vol_out=0.0,comm_in=0.0,comm_out=0.0,swap=0.0,n_swap_nonzero=0,fee=0.0))
    for d in trade:
        p=per[d['symbol']]
        if d['entry']==0: p['n_in']+=1; p['vol_in']+=d['volume']; p['comm_in']+=d['commission']
        else: p['n_out']+=1; p['vol_out']+=d['volume']; p['comm_out']+=d['commission']
        p['swap']+=d['swap']; p['fee']+=d['fee']
        if abs(d['swap'])>1e-9: p['n_swap_nonzero']+=1
    tbl={}
    for s,p in sorted(per.items()):
        tot_vol=p['vol_in']+p['vol_out']; tot_comm=p['comm_in']+p['comm_out']
        tbl[s]=dict(n_in=p['n_in'],n_out=p['n_out'],vol_in=round(p['vol_in'],4),vol_out=round(p['vol_out'],4),
                    comm_in=round(p['comm_in'],4),comm_out=round(p['comm_out'],4),
                    comm_per_lot_roundturn=(round(tot_comm/p['vol_in'],5) if p['vol_in'] else None),
                    comm_per_lot_side=(round(tot_comm/tot_vol,5) if tot_vol else None),
                    swap_total=round(p['swap'],4), n_swap_nonzero=p['n_swap_nonzero'],
                    fee_total=round(p['fee'],4))
    allc=sum(d['commission'] for d in trade); allv=sum(d['volume'] for d in trade if d['entry']==0)
    out[acct]=dict(n_trade_deals=len(trade), n_in=sum(1 for d in trade if d['entry']==0),
                   n_out=sum(1 for d in trade if d['entry']!=0),
                   total_commission=round(allc,4), total_entry_volume=round(allv,4),
                   overall_comm_per_lot_roundturn=(round(allc/allv,5) if allv else None),
                   total_swap=round(sum(d['swap'] for d in trade),4),
                   n_deals_with_swap=sum(1 for d in trade if abs(d['swap'])>1e-9),
                   swap_frac=round(sum(1 for d in trade if abs(d['swap'])>1e-9)/max(1,len(trade)),4),
                   total_fee=round(sum(d['fee'] for d in trade),4),
                   per_symbol=tbl)
json.dump(out,open(OUTD+'/L10_COMM_SWAP_V1.json','w'),indent=1)
for a,o in out.items():
    print('==',a,'trade_deals',o['n_trade_deals'],'IN',o['n_in'],'OUT',o['n_out'])
    print('  total_comm',o['total_commission'],'entry_vol',o['total_entry_volume'],'comm/lot(RT)',o['overall_comm_per_lot_roundturn'])
    print('  total_swap',o['total_swap'],'deals_with_swap',o['n_deals_with_swap'],'frac',o['swap_frac'],'fee',o['total_fee'])
    for s,v in list(o['per_symbol'].items())[:14]:
        print('   ',s,'in',v['n_in'],'vol',v['vol_in'],'comm/lotRT',v['comm_per_lot_roundturn'],'swapTot',v['swap_total'],'nSwap',v['n_swap_nonzero'])
