import gzip, json, itertools, collections, math
P='docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz'
rows=[json.loads(l) for l in gzip.open(P,'rt')]
n=len(rows)
keys=list(rows[0].keys())
# exact alias detection
cols={k:[r[k] for r in rows] for k in keys}
alias=collections.defaultdict(list)
seen={}
for k in keys:
    sig=tuple(cols[k])
    h=hash(sig)
    if h in seen and cols[seen[h]]==cols[k]:
        alias[seen[h]].append(k)
    else:
        seen[h]=k
print("=== EXACT ALIAS GROUPS (byte-identical column) ===")
for a,b in alias.items():
    print('  ',a,'==',b)

def close(a,b,tol=1e-9):
    bad=0; mx=0
    for x,y in zip(a,b):
        if x is None or y is None:
            if x!=y: bad+=1
            continue
        d=abs(x-y); mx=max(mx,d)
        if d>tol: bad+=1
    return bad,mx

print("\n=== ARITHMETIC IDENTITIES ===")
c=cols
# cost_r == spread+comm+swap+slip
lhs=c['cost_r']; rhs=[c['spread_r'][i]+c['commission_r'][i]+c['swap_cost_r'][i]+c['expected_slippage_r'][i] for i in range(n)]
b,mx=close(lhs,rhs,1e-7); print(f"cost_r == spread_r+commission_r+swap_cost_r+expected_slippage_r : violations={b}/{n} maxabs={mx:.3e}")
# expected_net_r == candidate_ev_r - cost_r
rhs=[c['candidate_ev_r'][i]-c['cost_r'][i] for i in range(n)]
b,mx=close(c['expected_net_r'],rhs,1e-7); print(f"expected_net_r == candidate_ev_r - cost_r            : violations={b}/{n} maxabs={mx:.3e}")
# candidate_ev_r vs prob: p*R -(1-p)*1 ?
for R in (1.5,2.0):
    rhs=[c['candidate_probability'][i]*R-(1-c['candidate_probability'][i]) for i in range(n)]
    b,mx=close(c['candidate_ev_r'],rhs,1e-6); print(f"candidate_ev_r == p*{R} - (1-p)                     : violations={b}/{n} maxabs={mx:.3e}")
# broker_pretrade_diag_expected_cost_r vs cost_r (non-null)
idx=[i for i in range(n) if c['broker_pretrade_diag_expected_cost_r'][i] is not None]
b,mx=close([c['broker_pretrade_diag_expected_cost_r'][i] for i in idx],[c['cost_r'][i] for i in idx],1e-6)
print(f"broker_pretrade_diag_expected_cost_r == cost_r (n={len(idx)}): violations={b} maxabs={mx:.3e}")
# old_proxy delta
rhs=[c['cost_r'][i]-c['old_proxy_vs_broker_calibrated_delta_r'][i] for i in range(n)]
print("cost_r - old_proxy_delta stats: min %.5f max %.5f mean %.5f"%(min(rhs),max(rhs),sum(rhs)/n))
# take_profit vs entry/stop -> implied target R
imp=[]
for i in range(n):
    e=c['entry_price'][i]; s=c['stop_loss'][i]; t=c['take_profit_1'][i]
    d=abs(e-s)
    imp.append(abs(t-e)/d if d>0 else None)
b,mx=close(imp,c['policy_target_r'],1e-6); print(f"|tp1-entry|/|entry-stop| == policy_target_r          : violations={b}/{n} maxabs={mx:.3e}")
b,mx=close(c['policy_target_r'],c['raw_target_r'],1e-12); print(f"policy_target_r == raw_target_r                      : violations={b}/{n} maxabs={mx:.3e}")
# gross = net + cost
gross=[c['opportunity_net_proxy_r'][i]+c['cost_r'][i] for i in range(n)]
print("gross mean %.6f  net mean %.6f  cost mean %.6f"%(sum(gross)/n,sum(c['opportunity_net_proxy_r'])/n,sum(c['cost_r'])/n))
# gross histogram of exactly -1 / exactly target
ex_stop=sum(1 for g in gross if abs(g+1.0)<1e-6)
ex_tgt=sum(1 for i,g in enumerate(gross) if abs(g-c['policy_target_r'][i])<1e-6)
print("gross exactly -1.0:",ex_stop, ex_stop/n, " gross exactly == policy_target_r:",ex_tgt, ex_tgt/n)
# spread_r share of cost
sr=sum(c['spread_r'])/n; cr=sum(c['cost_r'])/n
print("mean spread_r %.6f = %.1f%% of mean cost_r; mean commission %.6f (%.1f%%); mean swap %.6f (%.1f%%); slip 0.02 (%.1f%%)"%(
  sr, 100*sr/cr, sum(c['commission_r'])/n, 100*(sum(c['commission_r'])/n)/cr, sum(c['swap_cost_r'])/n, 100*(sum(c['swap_cost_r'])/n)/cr, 100*0.02/cr))
# risk distance in price terms
rd=[abs(c['entry_price'][i]-c['stop_loss'][i]) for i in range(n)]
rds=sorted(rd); print("risk distance price: min %.6g p05 %.6g med %.6g p95 %.6g max %.6g"%(rds[0],rds[int(.05*n)],rds[n//2],rds[int(.95*n)],rds[-1]))
