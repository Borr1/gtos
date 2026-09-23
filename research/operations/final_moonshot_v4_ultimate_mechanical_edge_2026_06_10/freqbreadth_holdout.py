"""FREQBREADTH holdout discipline:
  (1) Choose AC_FLOOR on TRAIN (<=2024) by conf-wtd EV with a trades-floor, then report the
      SAME floor FORWARD 2025 & 2026 separately. FVG-only soft-ramp (the surviving lever).
  (2) Per-trigger ac60-gate transfer diagnostic: does the persistence gate make sweep/ob pay
      if we raise the gate? (find where each trigger DID work, per the build doctrine).
  (3) Confirm the size_mult ramp is monotone-useful: bucket realised EV by ac60 decile (fwd).
"""
import sys, json, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import freqbreadth_build as fb
import compounding_sleeve as cs

# ---- raw candidate rows for FVG (ungated, ac>=0 so we can sweep the floor) ----
def raw_fvg_rows():
    rows = []
    for sym in fb.METALS:
        T, B, atrs, cost = fb.ctx(sym)
        if len(B) < 200: continue
        for (t, d, sd, i, src) in fb.trig_fvg(sym):
            ac = cs.autocorr(B, i, 60); vr = cs.vol_ratio(atrs, i)
            if ac is None: continue
            ex = cs.exit_state_d(B, i, d, sd, vr, cost)
            rows.append(dict(sym=sym, year=t.year, ac60=ac, vr=vr, R=ex['R'], src='fvg'))
    return rows

def raw_pooled_rows(triggers):
    pri = {'fvg':0,'ob':1,'sweep':2}; rows=[]
    for sym in fb.METALS:
        T,B,atrs,cost = fb.ctx(sym)
        if len(B)<200: continue
        cand={}
        for tg in triggers:
            for (t,d,sd,i,src) in fb.TRIGS[tg](sym):
                key=(i,d)
                if key not in cand or pri[src]<pri[cand[key][4]]: cand[key]=(t,d,sd,i,src)
        for (i,dd),(t,_,sd,ii,src) in cand.items():
            ac=cs.autocorr(B,ii,60); vr=cs.vol_ratio(atrs,ii)
            if ac is None: continue
            ex=cs.exit_state_d(B,ii,dd,sd,vr,cost)
            rows.append(dict(sym=sym,year=t.year,ac60=ac,vr=vr,R=ex['R'],src=src))
    return rows

def wtd(rows, shape='ramp', floor=0.05):
    sw=0.0; swr=0.0; n=0; wn=0
    for r in rows:
        m=fb.size_mult(r['ac60'], r['vr'], shape=shape) if floor==fb.AC_FLOOR else _mult_floor(r['ac60'],r['vr'],shape,floor)
        if m<=0: continue
        sw+=m; swr+=m*r['R']; n+=1; wn+= (r['R']>0)
    return dict(n=n, wev=round(swr/sw,4) if sw>0 else 0.0, win=round(100*wn/n,1) if n else 0.0)

def _mult_floor(ac,vr,shape,floor):
    if ac is None or ac<floor: return 0.0
    base = 0.40 + (ac-floor)*(0.80/0.15); base=max(0.40,min(1.20,base))
    if vr<1.35: base*=1.15
    elif vr>=1.6: base*=0.90
    return min(1.5,base)

def main():
    out={}
    fvg = raw_fvg_rows()
    tr = [r for r in fvg if r['year']<=2024]
    print("="*72)
    print("(1) AC_FLOOR chosen on TRAIN (<=2024), reported FORWARD — FVG soft-ramp")
    print(f"{'floor':>6} | TRAIN n  wtdEV  | FWD25 n wtdEV win | FWD26 n wtdEV win")
    best=None
    for fl in (0.03,0.04,0.05,0.06,0.08,0.10,0.12):
        st=wtd(tr,'ramp',fl)
        f25=wtd([r for r in fvg if r['year']==2025],'ramp',fl)
        f26=wtd([r for r in fvg if r['year']==2026],'ramp',fl)
        mark=''
        # selection metric on TRAIN ONLY: wev with n>=80 train trades
        if st['n']>=80 and (best is None or st['wev']>best[1]):
            best=(fl,st['wev']); mark=' *trainpick-candidate'
        print(f"{fl:>6} | {st['n']:>6} {st['wev']:+.3f} | {f25['n']:>4} {f25['wev']:+.3f} {f25['win']:>3.0f} | {f26['n']:>4} {f26['wev']:+.3f} {f26['win']:>3.0f}{mark}")
    pick = best[0] if best else 0.05
    print(f"  -> TRAIN-picked floor = {pick}")
    fwd_all = wtd([r for r in fvg if r['year']>=2025],'ramp',pick)
    print(f"  -> FORWARD 2025-26 at train-picked floor: n={fwd_all['n']} ({fwd_all['n']/2:.1f}/yr) wtdEV={fwd_all['wev']:+.3f} win={fwd_all['win']:.0f}%")
    out['train_picked_floor']=pick; out['fwd_at_pick']=fwd_all

    print("\n"+"="*72)
    print("(3) Realised EV by ac60 bucket, FVG, FORWARD 2025-26 (does conf rise with ac?)")
    fwd=[r for r in fvg if r['year']>=2025]
    buckets=[('<0.05',-9,0.05),('0.05-0.075',0.05,0.075),('0.075-0.10',0.075,0.10),
             ('0.10-0.15',0.10,0.15),('0.15-0.25',0.15,0.25),('>=0.25',0.25,99)]
    for lab,lo,hi in buckets:
        rr=[r for r in fwd if lo<=r['ac60']<hi]
        if rr:
            ev=sum(x['R'] for x in rr)/len(rr); win=100*sum(1 for x in rr if x['R']>0)/len(rr)
            print(f"   ac60 {lab:>10}: n={len(rr):>3} rawEV={ev:+.3f} win={win:.0f}%")
    print("   (the soft band 0.05-0.10 is the FREQUENCY we recover; verify it is still net +)")

    print("\n"+"="*72)
    print("(2) Per-trigger ac60-gate TRANSFER: raise the gate on sweep & ob alone, FWD 2025-26")
    for tg in ('sweep','ob'):
        rows=raw_pooled_rows((tg,))
        fwd=[r for r in rows if r['year']>=2025]
        print(f"  --- {tg} ---")
        for g in (0.05,0.10,0.15,0.20,0.30):
            rr=[r for r in fwd if r['ac60']>=g]
            if rr:
                ev=sum(x['R'] for x in rr)/len(rr); win=100*sum(1 for x in rr if x['R']>0)/len(rr)
                print(f"     ac60>={g}: n={len(rr):>4} rawEV={ev:+.3f} win={win:.0f}%")
    out_path=HERE/'FREQBREADTH_HOLDOUT_RESULT.json'
    out_path.write_text(json.dumps(out,indent=1))
    print("\nwrote FREQBREADTH_HOLDOUT_RESULT.json")

if __name__=='__main__':
    main()
