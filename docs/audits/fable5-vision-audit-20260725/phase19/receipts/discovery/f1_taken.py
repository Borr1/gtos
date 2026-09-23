import json, os
from collections import Counter
cen=json.load(open('/tmp/f1/census.json'))
CAND={'2025-10':174479,'2025-11':151190,'2025-12':136141,'2026-01':153486,
      '2026-02':129231,'2026-03':130124,'2026-04':134489,'2026-05':132500}
MISSED={'2025-10':174382,'2025-11':151131,'2025-12':136093,'2026-01':153425,
        '2026-02':129165,'2026-03':130004,'2026-04':134443,'2026-05':132445}
def econ(g,c,nr):
    n=len(g)
    wins=[x for x in g if x>0]; loss=[x for x in g if x<=0]
    aw=sum(wins)/len(wins) if wins else 0.0
    al=abs(sum(loss)/len(loss)) if loss else 0.0
    payoff=aw/al if al else None
    be=1/(1+payoff) if payoff else None
    wr=len(wins)/n
    nwins=[x for x in nr if x>0]; nloss=[x for x in nr if x<=0]
    naw=sum(nwins)/len(nwins) if nwins else 0.0
    nal=abs(sum(nloss)/len(nloss)) if nloss else 0.0
    npay=naw/nal if nal else None
    nbe=1/(1+npay) if npay else None
    nwr=len(nwins)/n
    m=sum(nr)/n
    sd=(sum((v-m)**2 for v in nr)/(n-1))**0.5 if n>1 else 0.0
    return dict(n=n,gross_mean=sum(g)/n,gross_total=sum(g),cost_mean=sum(c)/n,
      net_mean=m,net_total=sum(nr),net_sd=sd,net_se=sd/n**0.5,
      gross_win_rate=wr,gross_avg_win=aw,gross_avg_loss=al,gross_payoff=payoff,
      gross_breakeven_wr=be,gross_gap=wr-be if be else None,
      net_win_rate=nwr,net_avg_win=naw,net_avg_loss=nal,net_payoff=npay,
      net_breakeven_wr=nbe,net_gap=nwr-nbe if nbe else None)
out={}
allg=[];allc=[];alln=[]
for w,rec in sorted(cen.items()):
    lane=rec['lane_path']
    rows=[json.loads(l) for l in open(lane)]
    tr=[r for r in rows if r.get('row_kind')=='trade']
    sc=[r for r in tr if r.get('final_r') is not None]
    g=[r['final_r'] for r in sc]; c=[r['cost_r'] for r in sc]; nr=[r['net_r'] for r in sc]
    allg+=g;allc+=c;alln+=nr
    e=econ(g,c,nr)
    e['trade_rows_total']=len(tr); e['unscored_open']=len(tr)-len(sc)
    e['candidates']=CAND[w]; e['missed']=MISSED[w]; e['selected']=CAND[w]-MISSED[w]
    e['pool_scoreable']=rec.get('pool_rows')
    e['take_rate_trades_per_candidate']=len(tr)/CAND[w]
    e['close_reasons']=dict(Counter(r['close_reason'] for r in tr).most_common())
    e['symbols']=dict(Counter(r['symbol'] for r in tr).most_common())
    e['families_missing']=True
    out[w]=e
out['POOLED_8']=econ(allg,allc,alln)
out['POOLED_8']['candidates']=sum(CAND.values()); out['POOLED_8']['missed']=sum(MISSED.values())
out['POOLED_8']['selected']=sum(CAND.values())-sum(MISSED.values())
json.dump(out,open('/tmp/f1/taken.json','w'),indent=1)
hdr=f"{'win':9s} {'cand':>7s} {'sel':>4s} {'trd':>4s} {'scd':>4s} {'gross':>8s} {'cost':>7s} {'net':>8s} {'wr':>6s} {'payoff':>6s} {'be':>6s} {'gap':>7s} {'netTot':>8s}"
print(hdr); print('-'*len(hdr))
for w in sorted(k for k in out if k!='POOLED_8'):
    d=out[w]
    print(f"{w:9s} {d['candidates']:7d} {d['selected']:4d} {d['trade_rows_total']:4d} {d['n']:4d} {d['gross_mean']:+8.4f} {d['cost_mean']:7.4f} {d['net_mean']:+8.4f} {d['gross_win_rate']:6.4f} {d['gross_payoff']:6.3f} {d['gross_breakeven_wr']:6.4f} {d['gross_gap']:+7.4f} {d['net_total']:+8.2f}")
d=out['POOLED_8']
print('-'*len(hdr))
print(f"{'POOLED':9s} {d['candidates']:7d} {d['selected']:4d} {'':4s} {d['n']:4d} {d['gross_mean']:+8.4f} {d['cost_mean']:7.4f} {d['net_mean']:+8.4f} {d['gross_win_rate']:6.4f} {d['gross_payoff']:6.3f} {d['gross_breakeven_wr']:6.4f} {d['gross_gap']:+7.4f} {d['net_total']:+8.2f}")
print(f"net se={d['net_se']:.4f}  t={d['net_mean']/d['net_se']:.3f}  sd={d['net_sd']:.4f}")
print(f"selection rate: {d['selected']}/{d['candidates']} = {d['selected']/d['candidates']*100:.4f}%")
