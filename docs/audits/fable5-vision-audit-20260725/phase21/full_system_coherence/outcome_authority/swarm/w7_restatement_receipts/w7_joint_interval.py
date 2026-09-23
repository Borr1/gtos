import sys,collections,json,math,random,statistics,gzip
R='/Users/borr/GTOSActive/worktrees/w7-restate-20260811'
sys.path.insert(0,R); sys.path.insert(0,R+'/scripts'); sys.argv=['x']
import mc_firm_rules as Q, recost_w7_validation as M
AUD=R+'/docs/audits/fable5-vision-audit-20260725'
r1=json.load(gzip.open(AUD+'/phase20/receipts/r1/R1_ESTATE_ROWS_V1.json.gz','rt'))
cal={}; ptg=pmg=0; poth=[]
for sl in sorted({r['sleeve'] for r in r1}):
    rs=[r for r in r1 if r['sleeve']==sl]
    tg=[r for r in rs if r['reason_old']=='target']; mig=[r for r in tg if r['reason_new']!='target']
    oth=[r['r_new_mid']-r['r_old'] for r in rs if r['reason_old'] in ('trail','maxbars')]
    cal[sl]=dict(n_target=len(tg),n_migrated=len(mig),other_deltas=oth); ptg+=len(tg); pmg+=len(mig); poth+=oth
cal['_POOLED_']=dict(n_target=ptg,n_migrated=pmg,other_deltas=poth)
def pctl(xs,q):
    xs=sorted(xs); i=(len(xs)-1)*q/100.0; lo,hi=int(math.floor(i)),int(math.ceil(i))
    return xs[lo] if lo==hi else xs[lo]+(xs[hi]-xs[lo])*(i-lo)
def mblock(s,rng,b=5):
    n=len(s); o=[]
    while len(o)<n:
        st=rng.randrange(0,n); o.extend(s[st:st+b] if st+b<=n else s[st:]+s[:st+b-n])
    return o[:n]
st=M.build([]); rows=st['rows']
for r in rows:
    g=r['R']+r['charged_cost_r']; r['_gross']=g; r['R_legacy']=r['R']
    r['_reason']='stop' if abs(g+1.0)<1e-6 else ('target' if (g>0 and abs(g-round(g*4)/4)<1e-6) else 'other')
_,_,_,sd_book=M.build_matrix_from(rows,'R_legacy')
SETS={'ARMED_3':['crypto','energy_agri','sub_xvol_pullback'],
      'ARMED_4':['crypto','energy_agri','sub_xvol_pullback','sub_mid_dn_revert']}
cms={}
for a in ('FTMO','redacted_account'):
    p=collections.defaultdict(list)
    for r in rows:
        c=r['cost_'+a]
        if c['status']=='priced': p[r['sleeve']].append(c['cost_ex_swap_r'])
    cms[a]={k:statistics.median(v) for k,v in p.items()}
rng=random.Random(20260811); N=250
acc=collections.defaultdict(list); accm=collections.defaultdict(list)
for i in range(N):
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
    for lab,keep in SETS.items():
        for a in ('FTMO','redacted_account'):
            sub=[r for r in cr if r['sleeve'] in keep]
            days,comb,risk,_=Q.series(sub,a,cms[a],'max',sd_book,forward=True,kelly=Q.KELLY_HALF,risk_basis=Q.RISK_LIVE_NOMINAL)
            bs=mblock(comb,rng)
            rl,_=Q.rule_sets(a); P2=[x for x in rl if x.label=='P2_BOTH_PHASES'][0]
            acc[a+':'+lab].append(Q.mc(bs,risk,P2,20000,seed_base=1)['p_pass'])
            b0,b1=min(days),max(days); mo=(b1.year-b0.year)*12+(b1.month-b0.month)+1
            accm[a+':'+lab].append(100.0*statistics.fmean(bs)*risk*len(days)/mo)
    if (i+1)%50==0: print('  rep',i+1,flush=True)
out={}
for k,v in acc.items():
    m=accm[k]
    out[k]=dict(p_pass=dict(median=pctl(v,50),p2_5=pctl(v,2.5),p97_5=pctl(v,97.5),p10=pctl(v,10),n=len(v)),
                monthly_pct=dict(median=pctl(m,50),p2_5=pctl(m,2.5),p97_5=pctl(m,97.5)))
    print(f"{k}: JOINT p_pass median {pctl(v,50):.5f} CI95 [{pctl(v,2.5):.5f},{pctl(v,97.5):.5f}] p10 {pctl(v,10):.5f} | %/mo {pctl(m,50):+.3f} [{pctl(m,2.5):+.3f},{pctl(m,97.5):+.3f}]")
out['method']='joint: quote-side migration posterior x moving-block bootstrap (block 5) over book-days, full firm-rule MC 20k paths each, N=250'
json.dump(out,open(R+'/docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority/swarm/w7_restatement_receipts/W7_JOINT_INTERVAL_V1.json','w'),indent=1)
