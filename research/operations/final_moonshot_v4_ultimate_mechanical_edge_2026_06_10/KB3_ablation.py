"""KB3 ablation — turn each harvest item on individually over the W2 baseline and measure the
BOOK-LEVEL verdict (combined MC P(pass) all/fwd, stress 1.5x, frequency, combined daily mean/worst).
Doctrine: improvement only counts if it BEATS baseline at the book level (not just per-sleeve EV).
"""
import sys, json, datetime, statistics, collections, random, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate, atr14, Bar
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs
import multitf_lib as m
import INTEG_portfolio_build as I
import INTEG_portfolio_build_w2 as W2
import kb2_new_breadth as KB
import EXEC_exit_variants as EX
import INTEG_portfolio_build_w3 as W3

def wins(r): return max(-1.3, min(5.0, r))

# Flag-driven metals_core / softband / eth generators (subset of W3 logic)
FLAGS = dict(combo=False, vrsize=False, body=False, ethfloor=False, ethtier=False)

def gen_metals_core_flagged():
    rows = []
    for sym in cs.METALS:
        T, B = w1.load(sym)
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]
        T1, B1 = m.load_ltf(sym, "H1"); have1 = len(B1) > 50
        T15, B15 = m.load_ltf(sym, "M15"); have15 = len(B15) > 50
        for (t, d, sd_h4, td, i_h4, B_h4, cost) in g.fvg_signals(sym):
            ac = cs.autocorr(B, i_h4, 60)
            if ac is None or ac < cs.AC_THR: continue
            vr = cs.vol_ratio(atrs, i_h4); a = atrs[i_h4]
            body = abs(B[i_h4].c - B[i_h4].o) / a if a > 0 else 0.0
            ts = t + datetime.timedelta(hours=4); sc = B_h4[i_h4].c
            stream, fi, maxbars, filled = B_h4, i_h4, 80, False
            if have1:
                si = m.first_ltf_index_after(T1, ts)
                if si is not None and 30 <= si < len(B1) - 2:
                    ej = I._find_fill(B1, T1, si, d, sc, 12, 1.0, ts)
                    if ej is not None: stream, fi, maxbars, filled = B1, ej, W3.H1_MAXBARS, True
            if not filled and have15:
                si = m.first_ltf_index_after(T15, ts)
                if si is not None and 30 <= si < len(B15) - 2:
                    ej = I._find_fill(B15, T15, si, d, sc, 48, 1.0, ts)
                    if ej is not None: stream, fi, maxbars = B15, ej, 1280
            cost_scaled = cost * (0.5 * a / sd_h4) if sd_h4 > 0 else cost
            if FLAGS['combo']:
                R = W3._exit_combo_banded(stream, fi, d, sd_h4, vr, cost_scaled, maxbars)
            else:
                R = wins(cs.exit_state_d(stream, fi, d, sd_h4, vr, cost, maxbars=maxbars)['R'])
            sz = W3._vr_size(vr) if FLAGS['vrsize'] else 1.0
            if FLAGS['body'] and body > 0.374: sz *= 0.5
            rows.append(dict(sleeve='metals_core', sym=sym, date=t.date(), year=t.year, R=wins(R), intra_size=round(sz,4)))
    return rows

def gen_softband_flagged():
    rows = []
    for sym in cs.METALS:
        T, B = w1.load(sym)
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]; cost = w1.cost_for(sym)
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym):
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac >= cs.AC_THR or ac < I.AC_FLOOR_SB: continue
            vr = cs.vol_ratio(atrs, i); a = atrs[i]
            body = abs(B[i].c - B[i].o) / a if a > 0 else 0.0
            sm = I._size_mult_soft(ac, vr)
            if sm <= 0: continue
            if FLAGS['body'] and body > 0.431: sm *= 0.5
            ex = cs.exit_state_d(B, i, d, sd, vr, c2)
            rows.append(dict(sleeve='metals_softband', sym=sym, date=t.date(), year=t.year, R=wins(ex['R']), intra_size=round(sm,4)))
    return rows

def gen_crypto_flagged():
    rows = []
    p = HERE / 'TW_CRYPTO_CASCADE_LEDGER.jsonl'
    for line in p.read_text().splitlines():
        if not line.strip(): continue
        r = json.loads(line); dt = datetime.date.fromisoformat(r['date'])
        rows.append(dict(sleeve='crypto', sym=r['sym'], date=dt, year=r['year'], R=wins(r['casc_R'])))
    # ETH
    T, B = KB.resample_eth_h4(); cost = w1.cost_for('ETHUSD')
    atrs = [atr14(B, i) for i in range(len(B))]
    m.LTF_PATHS.setdefault(("ETHUSD","H1"),[W3.DATA+"/bridge_ftmo_htf_20250601_20260610/ETHUSD_H1.csv"])
    m.LTF_PATHS.setdefault(("ETHUSD","M15"),[W3.DATA+"/bridge_ftmo_m15_20250601_20260610/ETHUSD_M15.csv"])
    T1,B1=m.load_ltf("ETHUSD","H1"); have1=len(B1)>50
    T15,B15=m.load_ltf("ETHUSD","M15"); have15=len(B15)>50
    floor = 0.10 if FLAGS['ethfloor'] else 0.15
    for (i,d) in KB.crypto_breakout_signals(B,20):
        a=atrs[i]
        if a<=0: continue
        ac=cs.autocorr(B,i,60)
        if ac is None or ac<floor: continue
        sd=2.0*a; base_R=wins(simulate(B,i,d,stop_dist=sd,target_dist=4*sd,maxbars=80,cost=cost))
        ts=T[i]+datetime.timedelta(hours=4); sc=B[i].c; R=base_R; filled=False
        if have1:
            si=m.first_ltf_index_after(T1,ts)
            if si is not None and 30<=si<len(B1)-2:
                ej=I._find_fill(B1,T1,si,d,sc,12,1.0,ts)
                if ej is not None: R=wins(simulate(B1,ej,d,stop_dist=sd,target_dist=4*sd,maxbars=320,cost=cost)); filled=True
        if not filled and have15:
            si=m.first_ltf_index_after(T15,ts)
            if si is not None and 30<=si<len(B15)-2:
                ej=I._find_fill(B15,T15,si,d,sc,48,1.0,ts)
                if ej is not None: R=wins(simulate(B15,ej,d,stop_dist=sd,target_dist=4*sd,maxbars=1280,cost=cost))
        sz = 1.5 if (FLAGS['ethtier'] and ac>=0.20) else 1.0
        rows.append(dict(sleeve='crypto',sym='ETHUSD',date=T[i].date(),year=T[i].year,R=wins(R),intra_size=sz))
    return rows

def book_verdict(label):
    GENS = dict(W2.GENS)
    GENS['metals_core']=gen_metals_core_flagged; GENS['metals_softband']=gen_softband_flagged
    GENS['crypto']=gen_crypto_flagged
    W2.GENS=GENS; W2.SLEEVES=list(GENS.keys())
    streams={}
    for name,fn in GENS.items():
        rs=fn()
        for r in rs: r['R_sized']=r['R']*r.get('intra_size',1.0)
        streams[name]=rs
    days,M=W2.build_matrix(streams)
    fwd_mask=[d.year>=2025 for d in days]
    comb=[sum(r) for r in M]; comb_fwd=[sum(r) for r,f in zip(M,fwd_mask) if f]
    comb_stress=[(v*1.5 if v<0 else v) for v in comb]
    tpy=sum(W2.I.sleeve_stats(streams[n])['fwd_per_year'] for n in streams)
    def mc(vals,sb): return W2.mc_series(vals,0.01,n_paths=8000,seed_base=sb)['p_pass']
    out=dict(label=label, mean=round(statistics.fmean(comb),4), mean_fwd=round(statistics.fmean(comb_fwd),4),
             worst=round(min(comb),3), best=round(max(comb),3), tpy=round(tpy),
             pass_all_1=round(mc(comb,1),4), pass_fwd_1=round(mc(comb_fwd,777),4), pass_stress_1=round(mc(comb_stress,999),4))
    print(f"{label:<26} mean{out['mean']:+.4f} fwd{out['mean_fwd']:+.4f} worst{out['worst']:+.2f} best{out['best']:+.2f} "
          f"tpy{out['tpy']:>5} | P1all {out['pass_all_1']:.3f} fwd {out['pass_fwd_1']:.3f} STRESS {out['pass_stress_1']:.3f}")
    return out

def main():
    res={}
    for k in FLAGS: FLAGS[k]=False
    res['baseline']=book_verdict("W2 baseline")
    singles=[('combo','+combo only'),('vrsize','+vr-size only'),('body','+body-conf only'),
             ('ethfloor','+ETH ac0.10 only'),('ethtier','+ETH x1.5 tier only')]
    for flag,lab in singles:
        for k in FLAGS: FLAGS[k]=False
        FLAGS[flag]=True
        res[flag]=book_verdict(lab)
    # combos that look promising
    for k in FLAGS: FLAGS[k]=False
    FLAGS['vrsize']=True; FLAGS['body']=True
    res['vrsize_body']=book_verdict("+vr-size+body")
    for k in FLAGS: FLAGS[k]=False
    FLAGS['vrsize']=True; FLAGS['body']=True; FLAGS['ethtier']=True
    res['vrsize_body_ethtier']=book_verdict("+vrsize+body+ethtier")
    for k in FLAGS: FLAGS[k]=True
    res['all']=book_verdict("ALL (=W3)")
    (HERE/'KB3_ABLATION_RESULT.json').write_text(json.dumps(res,indent=1,default=str))
    print("\nwrote KB3_ABLATION_RESULT.json")

if __name__=='__main__': main()
