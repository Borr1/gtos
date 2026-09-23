import sys,collections,json,math,random,statistics
R='/Users/borr/GTOSActive/worktrees/w7-restate-20260811'
sys.path.insert(0,R); sys.path.insert(0,R+'/scripts')
sys.argv=['x']
import recost_w7_validation as M
exec(open(R+'/docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority/swarm/w7_restatement_receipts/w7_survivor_tiers.py').read().split('def main()')[0].split('REPO =')[0])
import gzip
AUD=R+'/docs/audits/fable5-vision-audit-20260725'
R1=AUD+'/phase20/receipts/r1/R1_ESTATE_ROWS_V1.json.gz'
def calib():
    r1=json.load(gzip.open(R1,'rt')); per={}; ptg=pmg=0; poth=[]
    for sl in sorted({r['sleeve'] for r in r1}):
        rs=[r for r in r1 if r['sleeve']==sl]
        tg=[r for r in rs if r['reason_old']=='target']; mig=[r for r in tg if r['reason_new']!='target']
        oth=[r['r_new_mid']-r['r_old'] for r in rs if r['reason_old'] in ('trail','maxbars')]
        per[sl]=dict(n_target=len(tg),n_migrated=len(mig),other_deltas=oth); ptg+=len(tg); pmg+=len(mig); poth+=oth
    per['_POOLED_']=dict(n_target=ptg,n_migrated=pmg,other_deltas=poth); return per
def pctl(xs,q):
    xs=sorted(xs); i=(len(xs)-1)*q/100.0; lo,hi=int(math.floor(i)),int(math.ceil(i))
    return xs[lo] if lo==hi else xs[lo]+(xs[hi]-xs[lo])*(i-lo)
st=M.build([]); rows=st['rows']
for r in rows:
    g=r['R']+r['charged_cost_r']; r['_gross']=g
    r['_reason']='stop' if abs(g+1.0)<1e-6 else ('target' if (g>0 and abs(g-round(g*4)/4)<1e-6) else 'other')
cms={}
for a in ('FTMO','redacted_account'):
    p=collections.defaultdict(list)
    for r in rows:
        c=r['cost_'+a]
        if c['status']=='priced': p[r['sleeve']].append(c['cost_ex_swap_r'])
    cms[a]={k:statistics.median(v) for k,v in p.items()}
cal=calib(); rng=random.Random(20260811)
base={a:M.sleeve_table(rows,a,cms[a]) for a in ('FTMO','redacted_account')}
acc={a:collections.defaultdict(lambda:collections.defaultdict(list)) for a in ('FTMO','redacted_account')}
B=150
for b in range(B):
    rates={}
    for sl in {r['sleeve'] for r in rows}:
        c=cal.get(sl) or cal['_POOLED_']
        if not c['n_target']: c=cal['_POOLED_']
        aa,bb=c['n_migrated']+0.5,c['n_target']-c['n_migrated']+0.5
        x,y=rng.gammavariate(aa,1.0),rng.gammavariate(bb,1.0); rates[sl]=x/(x+y)
    cr=[]
    for r in rows:
        d=0.0
        if r['_reason']=='target':
            if rng.random()<rates[r['sleeve']]: d=-1.0-r['_gross']
        elif r['_reason']=='other':
            pool=(cal.get(r['sleeve']) or {}).get('other_deltas') or cal['_POOLED_']['other_deltas']
            d=rng.choice(pool) if pool else 0.0
        q=dict(r); q['R_gross']=r['R_gross']+d; cr.append(q)
    for a in ('FTMO','redacted_account'):
        t=M.sleeve_table(cr,a,cms[a])
        for sl,v in t.items():
            acc[a][sl]['gross'].append(v['gross_r']); acc[a][sl]['nmax'].append(v['net_r']['n_max'])
out={}
for a in ('FTMO','redacted_account'):
    print('\n=== %s ==='%a)
    print(f"{'sleeve':22s} {'n':>5s} {'gross(pub)':>10s} {'gross(corr)':>11s} {'Δ%':>7s} | {'net@max(pub)':>12s} {'net@max(corr)':>13s} {'ci95':>22s}")
    out[a]={}
    for sl,v in sorted(base[a].items()):
        g=acc[a][sl]['gross']; nm=acc[a][sl]['nmax']
        gm=pctl(g,50); nmm=pctl(nm,50)
        d=100*(gm-v['gross_r'])/abs(v['gross_r']) if v['gross_r'] else 0
        out[a][sl]=dict(n=v['n'],gross_published=v['gross_r'],gross_corrected_median=gm,
            gross_corrected_ci95=[pctl(g,2.5),pctl(g,97.5)],pct_change=d,
            net_at_max_carry_published=v['net_r']['n_max'],net_at_max_carry_corrected_median=nmm,
            net_at_max_carry_ci95=[pctl(nm,2.5),pctl(nm,97.5)],
            survives_published=v['survives_at_max_carry'])
        print(f"  {sl:20s} {v['n']:5d} {v['gross_r']:+10.4f} {gm:+11.4f} {d:+6.1f}% | {v['net_r']['n_max']:+12.4f} {nmm:+13.4f} [{pctl(nm,2.5):+.4f},{pctl(nm,97.5):+.4f}]")
json.dump(out,open('/tmp/w7probe/persleeve.json','w'),indent=1,default=str)
