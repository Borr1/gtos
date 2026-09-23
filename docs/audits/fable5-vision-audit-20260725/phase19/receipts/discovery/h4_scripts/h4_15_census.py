"""h4 item 1: inventory of EVERY live execution record on this machine."""
import json, os, subprocess, collections, hashlib
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
CAND=[
 ('/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api/ftmo_history_deals_get.jsonl','MT5 account deal history FTMO','commission,swap,volume,price,entry,position_id'),
 ('/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api/redacted_account_history_deals_get.jsonl','MT5 account deal history redacted_account','same'),
 ('/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api/ftmo_history_orders_get.jsonl','MT5 order history FTMO','type,state,volume_initial/current,price_open,time_setup/done'),
 ('/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api/redacted_account_history_orders_get.jsonl','MT5 order history redacted_account','same'),
 ('/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/broker_order_lifecycle_capture_v4.jsonl','runtime order/deal lifecycle','request vs fill, deal commission/swap, pretrade cost packet, captured ask/bid'),
 ('/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/slippage_runtime.jsonl','entry/close slippage shadow v3','requested vs fill px, spread at request/send/fill, latency ms, outcome'),
 ('/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/slippage.jsonl','legacy slippage log','requested vs fill (fill_price 0 on limit rows - unusable)'),
 ('/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/broker_actual_r_audit.jsonl','account-history joined R audit','account_truth_status'),
 ('/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/execution_manager_v4_decisions.jsonl','EMv4 decisions w/ embedded lifecycle packet',''),
 ('/Users/borr/gtos-vps-archive-20260803/shadow_logs/ultimate_book_runtime_learning_packets.jsonl.zst','book runtime learning packets (ARCHIVE, freshest)','placement/close events; NO cost fields'),
 ('/Users/borr/gtos-vps-archive-20260803/shadow_logs/slippage_runtime.jsonl','ARCHIVE copy','byte-identical to export'),
 ('/Users/borr/gtos-vps-archive-20260803/shadow_logs/broker_order_lifecycle_capture_v4.jsonl','ARCHIVE copy','byte-identical to export'),
]
cen=[]
for p,what,fields in CAND:
    if not os.path.exists(p): cen.append(dict(path=p,exists=False)); continue
    sz=os.path.getsize(p)
    if p.endswith('.zst'):
        n=int(subprocess.run(f'zstd -dc "{p}" | wc -l',shell=True,capture_output=True,text=True).stdout.strip())
    else:
        n=sum(1 for _ in open(p,errors='replace'))
    h=hashlib.sha256(open(p,'rb').read()).hexdigest()[:16]
    cen.append(dict(path=p,exists=True,bytes=sz,rows=n,sha256_16=h,what=what,cost_fields=fields))
for c in cen:
    print(('%-95s %8s rows %10s B  %s'%(c['path'].split('/')[-1],c.get('rows'),c.get('bytes'),c.get('what',''))))
json.dump(cen, open(D+'/h4_LIVE_RECORD_CENSUS_V1.json','w'), indent=1)
