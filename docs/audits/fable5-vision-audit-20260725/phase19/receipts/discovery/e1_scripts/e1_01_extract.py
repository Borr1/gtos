"""e1 step 1: stream a month's MISSED_OPPORTUNITY ledger and emit a compact
cost-forensic slice. Reads .jsonl / .jsonl.gz / .jsonl.zst (zst via zstdcat pipe)."""
import json, gzip, sys, subprocess, io, os
FIELDS=['symbol','entry_price','stop_loss','spread_r','expected_cost_r','cost_r','commission_r',
 'expected_slippage_r','swap_cost_r','opportunity_net_proxy_r','origin_family','route_family',
 'route_session','utc_hour_bucket','decision_time_utc','direction','policy_target_r','take_profit_1',
 'missed_opportunity_headline_r_scoreable','missed_opportunity_non_executable_diagnostic_scoreable',
 'missed_opportunity_r_scoreability_status','broker_pretrade_cost_executable','pretrade_cost_packet_status',
 'final_blocker_class','candidate_id','decision_timeframe']
def opener(p):
    if p.endswith('.zst'):
        pr=subprocess.Popen(['zstdcat',p],stdout=subprocess.PIPE)
        return io.TextIOWrapper(pr.stdout,encoding='utf-8')
    if p.endswith('.gz'): return gzip.open(p,'rt',encoding='utf-8')
    return open(p,'r',encoding='utf-8')
src,out=sys.argv[1],sys.argv[2]
n=0; w=gzip.open(out,'wt',encoding='utf-8')
for line in opener(src):
    line=line.strip()
    if not line: continue
    r=json.loads(line); n+=1
    w.write(json.dumps({k:r.get(k) for k in FIELDS},separators=(',',':'))+'\n')
w.close()
print(json.dumps({'src':src,'out':out,'rows':n}))
