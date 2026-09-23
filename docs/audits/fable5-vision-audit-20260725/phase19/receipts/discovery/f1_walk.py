"""f1 — one identical contract, three populations, per window."""
import sys, os, json, gzip, glob, argparse, math
from datetime import datetime, timezone
from collections import Counter, defaultdict
import numpy as np

REPO="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG=REPO+"/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
sys.path.insert(0,PBG); sys.path.insert(0,REPO)
os.chdir(REPO)
import pbg_lib as L
import pbg_econ as E

sys.path.insert(0,'/tmp/f1')
from paths import ARM

FA2=  "/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/docs/audits/fable5-vision-audit-20260725"
ROOTD=REPO+"/docs/audits/fable5-vision-audit-20260725"
POOL={
 "2025-10":f"{FA2}/phase19/receipts/pools/LP_october_2025_S0R0_POOL_V1.jsonl.gz",
 "2025-11":f"{FA2}/phase19/receipts/pools/LP_november_2025_S0R0_POOL_V1.jsonl.gz",
 "2025-12":f"{FA2}/phase19/receipts/pools/LP_december_2025_S0R0_POOL_V1.jsonl.gz",
 "2026-01":f"{ROOTD}/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz",
 "2026-02":f"{ROOTD}/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz",
 "2026-04":f"{FA2}/phase19/receipts/pools/CS_APRIL_S0R0_POOL_V1.jsonl.gz",
 "2026-05":f"{FA2}/phase19/receipts/pools/CS_MAY_S0R0_POOL_V1.jsonl.gz",
}
ROSTER={"2026-01":"/tmp/pbg_full_jan","2026-02":"/tmp/pbg_full_feb","2026-03":"/tmp/pbg_full_mar"}
NEXT={"2025-10":"202511","2025-11":"202512","2025-12":"202601","2026-01":"202602",
      "2026-02":"202603","2026-03":"202604","2026-04":"202605","2026-05":None}

HOR=120

def walk_limit2(tape,sym,i,*,entry,stop,long,target_r=2.0,horizon=HOR):
    """Honest resting-limit fill: a BUY limit fills when price TRADES AT OR BELOW it
    (low<=entry), a SELL limit when high>=entry.  Gaps through the level fill.
    Walk starts at the next bar (no same-bar credit).  Never touched -> 0.0 R, no cost."""
    d=abs(entry-stop)
    if not (d>0): return None
    a=i; b=min(a+horizon,tape.n)
    if a>=b: return None
    hi=tape.h[sym][a:b]; lo=tape.l[sym][a:b]
    ok=~np.isnan(hi)
    if not ok.any(): return None
    idxs=np.nonzero(ok)[0]
    touched=(lo[idxs]<=entry) if long else (hi[idxs]>=entry)
    if not touched.any(): return (0.0,'no_fill',None,int(ok.sum()),None)
    j=int(idxs[int(np.argmax(touched))])
    res=E.walk(tape,sym,a+j,entry=entry,stop=stop,long=long,target_r=target_r,horizon=horizon-j-1)
    if res is None: return (0.0,'no_fill',None,0,None)
    return (res[0],res[1],res[2],res[3],j)


def months_for(w):
    mm=w.replace('-','')
    out=[mm]
    n=NEXT.get(w)
    if n: out.append(n)
    return out

def bootci(x, n=2000, seed=7):
    a=np.asarray(x,dtype=float)
    if a.size<2: return (float('nan'),float('nan'))
    rs=np.random.default_rng(seed)
    idx=rs.integers(0,a.size,size=(n,a.size))
    m=a[idx].mean(axis=1)
    return float(np.percentile(m,2.5)), float(np.percentile(m,97.5))

def econ(g, c, tag):
    g=np.asarray(g,dtype=float); c=np.asarray(c,dtype=float)
    net=g-c
    n=g.size
    if n==0: return {}
    wins=g[g>0]; loss=g[g<=0]
    aw=float(wins.mean()) if wins.size else 0.0
    al=float(-loss.mean()) if loss.size else 0.0
    payoff=aw/al if al else None
    be=1/(1+payoff) if payoff else None
    nw=net[net>0]; nl=net[net<=0]
    naw=float(nw.mean()) if nw.size else 0.0
    nal=float(-nl.mean()) if nl.size else 0.0
    npay=naw/nal if nal else None
    nbe=1/(1+npay) if npay else None
    lo,hi=bootci(net)
    return dict(tag=tag,n=int(n),
      gross_mean=float(g.mean()),gross_total=float(g.sum()),
      cost_mean=float(c.mean()),
      net_mean=float(net.mean()),net_total=float(net.sum()),
      net_sd=float(net.std(ddof=1)),net_se=float(net.std(ddof=1)/math.sqrt(n)),
      net_ci95=[lo,hi],
      gross_win_rate=float((g>0).mean()),gross_avg_win=aw,gross_avg_loss=al,
      gross_payoff=payoff,gross_breakeven_wr=be,
      gross_gap=float((g>0).mean())-be if be else None,
      net_win_rate=float((net>0).mean()),net_avg_win=naw,net_avg_loss=nal,
      net_payoff=npay,net_breakeven_wr=nbe,
      net_gap=float((net>0).mean())-nbe if nbe else None)

def run(w):
    mons=months_for(w)
    syms=list(L.SYMBOLS)
    tape=E.Tape(syms,mons)
    cm=E.CostModel()
    res={"window":w,"m1_months":mons}

    def walk_rows(rows, target_r, label, contract='market'):
        G=[];C=[];meta=[]
        for r in rows:
            sym=r['sym']
            if sym not in tape.c: continue
            i=tape.idx(r['t'])
            if not (0<i<tape.n): continue
            d=abs(r['entry']-r['stop'])
            if not (d>0): continue
            if contract=='market':
                out=E.walk(tape,sym,i,entry=r['entry'],stop=r['stop'],long=r['long'],
                           target_r=target_r,horizon=HOR)
                j=0
            else:
                out=walk_limit2(tape,sym,i,entry=r['entry'],stop=r['stop'],long=r['long'],
                                target_r=target_r,horizon=HOR)
                j=out[4] if out else None
            if out is None: continue
            rr,reason,ebar,used=out[0],out[1],out[2],out[3]
            filled = reason!='no_fill'
            px,_=cm.cost_px(sym,r['t'],r['entry'],r['long'],hold_min=HOR)
            cst=(px/d) if filled else 0.0
            G.append(rr); C.append(cst)
            mkt=tape.last_close_before(sym,i)
            past=(mkt<=r['stop']) if r['long'] else (mkt>=r['stop'])
            meta.append(dict(fam=r.get('fam'),reason=reason,ebar=ebar,d_bps=d/r['entry']*1e4,
                             past_stop=bool(past) if mkt==mkt else None,
                             day=r['t'][:10],sym=sym,r=rr,cost=cst,filled=filled,touch=j))
        e=econ(G,C,label)
        e['contract']=contract
        e['reasons']=dict(Counter(m['reason'] for m in meta))
        e['fill_rate']=float(np.mean([1.0 if m['filled'] else 0.0 for m in meta])) if meta else None
        e['stop_bar1_share']=float(np.mean([1.0 if (m['reason']=='stop' and m['ebar']==1) else 0.0 for m in meta])) if meta else None
        st=[m for m in meta if m['reason']=='stop']
        e['stop_in_bar1_of_stops']=float(np.mean([1.0 if m['ebar']==1 else 0.0 for m in st])) if st else None
        e['born_past_stop_share']=float(np.mean([1.0 if m['past_stop'] else 0.0 for m in meta])) if meta else None
        ps=[m['r'] for m in meta if m['past_stop']]
        e['born_past_stop_gross']=float(np.mean(ps)) if ps else None
        e['d_bps_mean']=float(np.mean([m['d_bps'] for m in meta])) if meta else None
        e['d_bps_median']=float(np.median([m['d_bps'] for m in meta])) if meta else None
        byd=defaultdict(list)
        for m in meta: byd[m['day']].append(m['r']-m['cost'])
        e['days']=len(byd); e['days_net_positive']=sum(1 for v in byd.values() if np.mean(v)>0)
        fam={}
        for f in set(m['fam'] for m in meta):
            sel=[m for m in meta if m['fam']==f]
            fam[f]=dict(n=len(sel),gross=float(np.mean([m['r'] for m in sel])),
                        cost=float(np.mean([m['cost'] for m in sel])),
                        net=float(np.mean([m['r']-m['cost'] for m in sel])),
                        fill_rate=float(np.mean([1.0 if m['filled'] else 0.0 for m in sel])))
        e['by_family']=fam
        POI={'current_fvg_fill','current_ob_retest','current_breaker_re_entry'}
        fl=[m for m in meta if m['filled']]
        if fl:
            e['filled_only']=econ([m['r'] for m in fl],[m['cost'] for m in fl],label+'_FILLED')
        for cname,sel in (('at_market',[m for m in meta if m['fam'] not in POI]),
                          ('poi',[m for m in meta if m['fam'] in POI])):
            if not sel: continue
            sub=econ([m['r'] for m in sel],[m['cost'] for m in sel],label+'_'+cname)
            sub['fill_rate']=float(np.mean([1.0 if m['filled'] else 0.0 for m in sel]))
            f2=[m for m in sel if m['filled']]
            if f2: sub['filled_only']=econ([m['r'] for m in f2],[m['cost'] for m in f2],label+'_'+cname+'_FILLED')
            byd=defaultdict(list)
            for m in sel: byd[m['day']].append(m['r']-m['cost'])
            sub['days']=len(byd); sub['days_net_positive']=sum(1 for v in byd.values() if np.mean(v)>0)
            sub['d_bps_median']=float(np.median([m['d_bps'] for m in sel]))
            sub['born_past_stop_share']=float(np.mean([1.0 if m['past_stop'] else 0.0 for m in sel]))
            e['cohort_'+cname]=sub
        return e, meta

    # ---------- TAKEN
    tk=json.load(open('/tmp/f1/taken_slim.json'))[w]
    trows=[]
    for r in tk:
        if r.get('stop_loss') is None or r.get('entry_price') is None: continue
        trows.append(dict(sym=r['symbol'],t=r['decision_time_utc'],
                          long=(r['direction']=='LONG'),entry=r['entry_price'],
                          stop=r['stop_loss'],fam=r.get('origin_family')))
    for tr_ in (1.5,2.0):
        for ct in ('market','honest'):
            e,_=walk_rows(trows,tr_,f'TAKEN_{ct}_t{tr_}',contract=ct)
            res[f'taken_{ct}_t{tr_}']=e
    # realised
    sc=[r for r in tk if r.get('final_r') is not None]
    res['taken_realised']=econ([r['final_r'] for r in sc],[r['cost_r'] for r in sc],'TAKEN_realised_arm')
    res['taken_realised']['n_rows_total']=len(tk)
    res['taken_realised']['d_bps_mean']=float(np.mean([abs(r['entry_price']-r['stop_loss'])/r['entry_price']*1e4 for r in tk if r.get('stop_loss')]))
    res['taken_realised']['d_bps_median']=float(np.median([abs(r['entry_price']-r['stop_loss'])/r['entry_price']*1e4 for r in tk if r.get('stop_loss')]))
    res['taken_realised']['by_family']=dict(Counter(r.get('origin_family') for r in tk))
    res['taken_realised']['order_type']=dict(Counter(r.get('effective_order_type') for r in tk))

    # ---------- POOL
    if w in POOL and os.path.isfile(POOL[w]):
        prows=[];pc=[]
        with gzip.open(POOL[w],'rt') as fh:
            for line in fh:
                r=json.loads(line)
                if r.get('stop_loss') is None or r.get('entry_price') is None: continue
                prows.append(dict(sym=r['symbol'],t=r['decision_time_utc'],
                                  long=(r.get('direction') or r.get('side'))=='LONG',
                                  entry=r['entry_price'],stop=r['stop_loss'],
                                  fam=r.get('origin_family')))
                pc.append(r.get('cost_r'))
        for tr_ in (1.5,2.0):
            for ct in ('market','honest'):
                e,_=walk_rows(prows,tr_,f'POOL_{ct}_t{tr_}',contract=ct)
                res[f'pool_{ct}_t{tr_}']=e
        res['pool_frozen_cost_mean']=float(np.mean([x for x in pc if x is not None]))
        res['pool_n']=len(prows)

    # ---------- ROSTER
    if w in ROSTER and os.path.isdir(ROSTER[w]):
        rrows=[]
        for f in sorted(glob.glob(ROSTER[w]+'/*.jsonl.gz')):
            with gzip.open(f,'rt') as fh:
                for line in fh:
                    r=json.loads(line)
                    if r['k']!=15: continue
                    rrows.append(dict(sym=r['s'],t=r['t'],long=(r['d']=='L'),
                                      entry=r['e'],stop=r['sl'],fam=r['f']))
        for tr_ in (1.5,2.0):
            for ct in ('market','honest'):
                e,_=walk_rows(rrows,tr_,f'ROSTER_{ct}_t{tr_}',contract=ct)
                res[f'roster_{ct}_t{tr_}']=e
        res['roster_n']=len(rrows)
    json.dump(res,open(f'/tmp/f1/out/W_{w}.json','w'),indent=1)
    print('done',w, {k:(v.get('n') if isinstance(v,dict) else v) for k,v in res.items() if isinstance(v,dict)})

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--window',required=True)
    a=ap.parse_args(); run(a.window)
