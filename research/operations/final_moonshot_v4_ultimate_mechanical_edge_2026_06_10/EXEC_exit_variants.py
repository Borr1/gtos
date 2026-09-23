"""EXEC track — Deepen dynamic execution / exits.
Lift the +0.865R compounding core (metals ex-copper FVG + ac60>=0.10 persistence gate).
SAME fixed entries as compounding_sleeve; only the EXIT manager varies.

No lookahead: all exit decisions use entry-state vol (known at i) + running MFE/MAE/bar-count
during the trade (bars index>i, used as the trade unfolds, exactly like a live trade manager).
geometry_lib pessimism preserved: per bar, adverse (stop) is checked BEFORE favorable.
Cost = w1.cost_for(sym) scaled by stop tightness (base * 0.5*ATR/stop_dist), applied to the
fraction of position still open at each exit leg. Winsorize net R to [-1.3,+5].

TRAIN = entries year<=2024. FORWARD = 2025 and 2026 reported separately + per-year + per-symbol.
"""
import sys, json, statistics, collections
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE)); sys.path.insert(0,str(HERE.parents[2]))
from geometry_lib import atr14, simulate
import gold_sleeve_strategy as g
import wave1_structure_setups_ict as w1
import compounding_sleeve as cs

METALS=cs.METALS
AC_THR=cs.AC_THR
def wins(r): return max(-1.3,min(5.0,r))

# ---------------------------------------------------------------------------
# Build the FIXED entry set ONCE (entries are identical for every exit policy).
# Each entry carries the full forward bar path so exit policies are pure functions.
# ---------------------------------------------------------------------------
def build_entries():
    ents=[]
    for s in METALS:
        try: T,B=w1.load(s)
        except Exception: continue
        if len(B)<200: continue
        atrs=[atr14(B,k) for k in range(len(B))]
        base_cost=w1.cost_for(s)
        for (t,d,sd,td,i,B2,c2) in g.fvg_signals(s):
            ac=cs.autocorr(B,i,60)
            if ac is None or ac<AC_THR: continue
            vr=cs.vol_ratio(atrs,i)
            # cost scaled by stop tightness (per doctrine). c2 already = base cost in R at 0.5ATR ref?
            # gold_sleeve cost_for returns a flat R figure; scale to this stop:
            a=atrs[i] if atrs[i]>0 else sd
            cost_scaled = base_cost * (0.5*a/sd) if sd>0 else base_cost
            ents.append(dict(sym=s,year=t.year,date=str(t)[:10],i=i,d=d,sd=sd,vr=vr,ac=ac,
                             cost=cost_scaled, atr=a, B=B))
    return ents

# ---------------------------------------------------------------------------
# Generic exit simulator. ladder = list of (R_level, fraction). After scaling,
# the runner stop moves to be_level (in R; 0.0 = breakeven). Runner exits at
# runner_R fixed target, or trail (arm_R,gap_R) if trail set, or maxbars close.
# struct_stop: if set, after first ladder fill move runner stop to a structural
# level computed from realized swing (in R from entry). All legs charged cost.
# ---------------------------------------------------------------------------
def sim_exit(ent, *, ladder, be_after_first=0.0, runner_R=4.0, runner_R_map=None,
             trail_arm=None, trail_gap=None, time_stop_bar=None, time_stop_minR=None,
             maxbars=80, be_arm_R=None):
    B=ent['B']; i=ent['i']; d=ent['d']; sd=ent['sd']; cost=ent['cost']; vr=ent['vr']
    entry=B[i].c
    end=min(i+maxbars, len(B)-1)
    # resolve runner target per vol regime if a map is given
    if runner_R_map is not None:
        if vr<1.35: runner_R=runner_R_map[0]
        elif vr<1.6: runner_R=runner_R_map[1]
        else: runner_R=runner_R_map[2]
    legs_left=list(ladder)  # mutable
    pos=1.0
    booked=0.0          # realized R weighted by fraction booked
    runner_stop=-1.0    # in R (initial structural 1R stop)
    runner_active=True
    mfe=0.0; mae=0.0; bars1R=None; armed_trail=False; trail_ref=None
    reason='open'; n_legs_filled=0
    for j in range(i+1, end+1):
        hi=B[j].h; lo=B[j].l
        favp=hi if d>0 else lo; advp=lo if d>0 else hi
        fav=d*(favp-entry)/sd; adv=d*(advp-entry)/sd
        mfe=max(mfe,fav); mae=min(mae,adv)
        if bars1R is None and fav>=1.0: bars1R=j-i
        # ---- pessimistic: check adverse (runner stop) FIRST ----
        if adv<=runner_stop:
            booked += pos*runner_stop
            pos=0.0
            reason='stop' if n_legs_filled==0 else ('be_scratch' if runner_stop==0.0 else 'runner_stop')
            break
        # ---- time stop (no-progress) BEFORE banking fav this bar ----
        if time_stop_bar is not None and (j-i)>=time_stop_bar and n_legs_filled==0:
            if mfe < (time_stop_minR if time_stop_minR is not None else 1.0):
                term=d*(B[j].c-entry)/sd
                booked += pos*term; pos=0.0; reason='time_stop'; break
        # ---- ladder fills (favorable) ----
        while legs_left and fav>=legs_left[0][0]:
            lvl,frac=legs_left.pop(0)
            f=min(frac,pos)
            booked += f*lvl
            pos-=f; n_legs_filled+=1
            # after first fill, move runner stop to be (or be_after_first level)
            if n_legs_filled==1:
                # smarter BE timing: only arm BE once fav>=be_arm_R (default = first ladder level)
                runner_stop=be_after_first
        if pos<=1e-9:
            reason='ladder_complete'; break
        # ---- trailing runner (only after first leg, if requested) ----
        if trail_arm is not None and n_legs_filled>=1:
            if not armed_trail and fav>=trail_arm:
                armed_trail=True; trail_ref=mfe
            if armed_trail:
                trail_ref=max(trail_ref,mfe)
                new_stop=trail_ref-trail_gap
                if new_stop>runner_stop: runner_stop=new_stop
        # ---- runner fixed target ----
        if pos>0 and fav>=runner_R:
            booked += pos*runner_R; pos=0.0; reason='runner_target'; break
    if pos>0:
        # market close on remaining
        term=d*(B[end].c-entry)/sd
        booked += pos*term
        if reason=='open': reason='market_close'
    R=wins(booked - cost)
    return dict(R=R, reason=reason, mfe=mfe, mae=mae, bars1R=bars1R, n_legs=n_legs_filled, vr=vr)

# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def stats(rs):
    if not rs: return dict(n=0,ev=0.0,win=0.0,std=0.0,worst=0.0,rc=0.0)
    n=len(rs); ev=sum(r['R'] for r in rs)/n
    win=sum(1 for r in rs if r['R']>0)/n*100
    std=statistics.pstdev([r['R'] for r in rs]) if n>1 else 0.0
    worst=min(r['R'] for r in rs)
    fwins=[r for r in rs if r['R']>0]
    runners=[r for r in rs if r['reason'] in ('runner_target',)]
    rc=100*len(runners)/max(1,len(fwins))
    return dict(n=n,ev=ev,win=win,std=std,worst=worst,rc=rc)

def maxdd_equity(rs_dated, risk=0.0025):
    # correlated-risk-unit by decision day, same model as gold_sleeve.backtest
    byday=collections.defaultdict(list)
    for r in rs_dated: byday[r['date']].append(r['R'])
    eq=1.0; peak=1.0; mdd=0.0
    for day in sorted(byday):
        u=sum(byday[day])/len(byday[day])
        eq*= (1+u*risk); peak=max(peak,eq); mdd=max(mdd,(peak-eq)/peak)
    return mdd*100

def run_policy(ents, name, **kw):
    out=[]
    for e in ents:
        ex=sim_exit(e, **kw)
        out.append(dict(sym=e['sym'],year=e['year'],date=e['date'],vr=e['vr'],R=ex['R'],
                        reason=ex['reason'],mfe=ex['mfe'],bars1R=ex['bars1R']))
    return name,out

def report(name, rows, baseline_rows=None):
    train=[r for r in rows if r['year']<=2024]
    f25=[r for r in rows if r['year']==2025]; f26=[r for r in rows if r['year']==2026]
    fwd=[r for r in rows if r['year']>=2025]
    st=stats(train); s25=stats(f25); s26=stats(f26); sf=stats(fwd)
    mdd=maxdd_equity(fwd,0.0025)
    line=(f"{name:<28} TRAIN ev{st['ev']:+.3f}/w{st['win']:.0f} | "
          f"2025 ev{s25['ev']:+.3f}/w{s25['win']:.0f} | 2026 ev{s26['ev']:+.3f}/w{s26['win']:.0f} | "
          f"FWD ev{sf['ev']:+.3f}/w{sf['win']:.0f} rc{sf['rc']:.0f}% std{sf['std']:.2f} mdd{mdd:.2f}%")
    print(line)
    return dict(name=name, train=st, y2025=s25, y2026=s26, fwd=sf, fwd_mdd=mdd, rows=rows)
