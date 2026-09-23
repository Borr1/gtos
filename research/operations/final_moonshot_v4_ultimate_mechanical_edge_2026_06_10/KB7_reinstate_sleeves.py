"""KB7_reinstate_sleeves.py — UNLEASH track: reinstate dropped sleeves under GROWTH sizing.

The sleeves dropped at W5/W6 for 1.5x-stress-tail reasons (leadlag_core full 8-config,
subh4_ll_fx, IDB intraday breadth) were all judged at FIXED-R barriers + winsor[-1.3,+5]
+ conservative sizing. This track re-tests them UNDER:
  (1) STATE_D vol-tiered scale-out exit (cs.exit_state_d) instead of fixed-R / trail
      -> the actual deployed exit; lets slow continuations run, halves drawdown.
  (2) RELAXED winsor [-1.3, +12] (the un-capped right tail; the [-1.3,+5] cap clips
      STATE_D's deep runR=4 winners). We report both caps.
  (3) GROWTH sizing 1.0-1.5%/unit on the LOCKED W2 MC (vol-matched challenge-pass +
      1.5x left-tail STRESS + maxDD/ruin), vs the clean_3 deploy baseline.
  (4) the HIGHEST-SHARPE leadlag subset ONLY (US30->USDJPY, NAS<->SPX) as its own sleeve.

VERDICT GATE (binding, from the brief): a sleeve "comes back" if, folded at confidence
weight under STATE_D + growth sizing, it RAISES the book's vol-matched challenge-pass MC
AND does NOT degrade the 1.5x-stress tail / maxDD-breach probability beyond an acceptable
bound. Speed (median days-to-pass) is the growth objective; the guardrail is P(maxDD breach)
+ P(ruin), quantified at every size. Per-year, never blended-only. Honest on sample size.

Leak-free: features from CLOSED bars (leader z-impulse z'd vs trailing window ending i-1;
ac60/vr/FVG all read B[index<=i]); cs.exit_state_d / geometry_lib.simulate label forward only;
real cost w1.cost_for. Forward holdout TRAIN(<=2024) vs FWD(2025-26) + per-year + n reported.
"""
import sys, json, collections, math, datetime, statistics, pickle, os, csv
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))

from geometry_lib import simulate, atr14, Bar
import wave1_structure_setups_ict as w1
import compounding_sleeve as cs
import leadlag as ll
import KB5_leadlag_subh4 as SH
import INTEG_portfolio_build as I
import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3
import IDB_intraday_breadth as IDB

# ---- winsor variants ----
def wins5(r):  return max(-1.3, min(5.0, r))    # the shipped cap
def wins12(r): return max(-1.3, min(12.0, r))   # the relaxed (un-capped right tail) cap

TARGET=I.TARGET; MAXDD=I.MAXDD; DAILY=I.DAILY; BLOCK=I.BLOCK; PATHCAP=I.PATHCAP; N=I.N
mc_series = W2.mc_series

# =========================================================================== #
# STATE_D relabelers for the lead-lag families (parallel miners that emit the
# entry index/dir/stop/vr so we can apply cs.exit_state_d instead of fixed-R).
# Replicates ll.mine_pair / SH.mine_pair gating EXACTLY (stop=0.5*ATR), only the
# EXIT changes. winsor selectable.
# =========================================================================== #
def _exit_R(B, i, d, sd, vr, cost, maxbars, exit_mode, geom, winf):
    """sd = stop distance in price = 0.5*ATR (matches ll/SH mine_pair). a = ATR = 2*sd.
    Fixed target_dist = geom['tmult']*a = geom['tmult']*2*sd (EXACT match to the shipped miner)."""
    if exit_mode == 'state_d':
        if winf is wins5:
            return cs.exit_state_d(B, i, d, sd, vr, cost, maxbars=maxbars)['R']
        return _state_d_raw(B, i, d, sd, vr, cost, maxbars, winf)
    else:
        a = 2.0*sd
        if geom["mode"] == "fixed":
            R = simulate(B, i, d, stop_dist=sd, target_dist=geom["tmult"]*a, cost=cost, maxbars=maxbars)
        else:
            R = simulate(B, i, d, stop_dist=sd, trail_arm=2*sd, trail_gap=1*sd, cost=cost, maxbars=maxbars)
        return winf(R)

def _state_d_raw(B, i, d, sd, vr, cost, maxbars, winf):
    """Re-implements cs.exit_state_d EXACTLY but with selectable final winsor (to admit
    the un-capped right tail). Identical tier logic / scale legs / stops."""
    entry = B[i].c
    if vr < 1.35:   scaleR, runR = 1.5, 4.0
    elif vr < 1.6:  scaleR, runR = 1.5, 3.0
    else:           scaleR, runR = 1.0, 2.5
    scaled=False; leg2=None; reason=None; end=min(i+maxbars, len(B)-1)
    for j in range(i+1, end+1):
        hi=B[j].h; lo=B[j].l
        favp = hi if d>0 else lo; advp = lo if d>0 else hi
        fav = d*(favp-entry)/sd; adv = d*(advp-entry)/sd
        if not scaled:
            if adv <= -1.0: return winf(-1.0-cost)
            if fav >= scaleR: scaled=True
        else:
            if adv <= 0.0: leg2=0.0; reason='scratch_be'; break
            if fav >= runR: leg2=runR; reason='win_runner'; break
    if reason is None:
        if scaled:
            leg2 = d*(B[end].c-entry)/sd
        else:
            R = d*(B[end].c-entry)/sd; return winf(R-cost)
    R = 0.5*scaleR + 0.5*leg2
    return winf(R-cost)

def mine_pair_relabel(leader, follower, relsign, look, zthr, thesis, gname,
                      confirm=None, confirm_sign=None, regime=None,
                      min_gap=2, maxbars=80, exit_mode='state_d', winf=wins12):
    """Clone of ll.mine_pair gating, EXIT swapped to STATE_D (or fixed/trail) with winf."""
    geom = ll.GEOMS[gname]
    sig = ll.leader_signal(leader, look)
    csig = ll.leader_signal(confirm, look) if confirm else None
    pf = ll.panel(follower); fb=pf["bars"]; ftmap=pf["tmap"]; fatrs=pf["atrs"]
    cost = ll.cost_for(follower)
    atrs_for_vr = fatrs
    trades=[]; last_idx=-10**9
    for ts, z in sig.items():
        if abs(z) < zthr: continue
        i = ftmap.get(ts)
        if i is None or i < 100 or i >= len(fb)-2: continue   # need 100 bars for vr
        if i - last_idx < min_gap: continue
        a = fatrs[i]
        if a <= 0: continue
        base = (1 if z>0 else -1)*relsign
        d = base if thesis=="momentum" else -base
        if confirm is not None:
            cz = csig.get(ts)
            if cz is None or abs(cz) < zthr: continue
            cbase=(1 if cz>0 else -1)*confirm_sign
            cd = cbase if thesis=="momentum" else -cbase
            if cd != d: continue
        if regime is not None:
            want = "trend_up" if (d>0 and regime=="align") else \
                   "trend_down" if (d<0 and regime=="align") else regime
            if not ll._laggard_regime_ok(fb, fatrs, i, want): continue
        sd = 0.5*a
        vr = cs.vol_ratio(atrs_for_vr, i)
        R = _exit_R(fb, i, d, sd, vr, cost, maxbars, exit_mode, geom, winf)
        trades.append(dict(sym=follower, date=ts.date(), year=ts.year, R=R))
        last_idx = i
    return trades

def mine_subh4_relabel(leader, follower, relsign, look, zthr, thesis, gname, sess,
                       maxbars=64, exit_mode='state_d', winf=wins12, sig=None):
    geom = SH.GEOMS[gname]
    if sig is None: sig = SH.leader_signal(leader, look)
    pf = SH.load_m15(follower); fb=pf["bars"]; ftmap=pf["tmap"]; fatrs=pf["atrs"]
    cost = SH.cost_for(follower)
    trades=[]; last_idx=-10**9; min_gap=4
    for ts, z in sig.items():
        if abs(z) < zthr: continue
        if not SH._session_ok(ts, sess): continue
        i = ftmap.get(ts)
        if i is None or i < 100 or i >= len(fb)-2: continue
        if i - last_idx < min_gap: continue
        a = fatrs[i]
        if a <= 0: continue
        base=(1 if z>0 else -1)*relsign
        d = base if thesis=="momentum" else -base
        sd = 0.5*a
        vr = cs.vol_ratio(fatrs, i)
        R = _exit_R(fb, i, d, sd, vr, cost, maxbars, exit_mode, geom, winf)
        trades.append(dict(ts=ts, sym=follower, date=ts.date(), year=ts.year, R=R))
        last_idx = i
    return trades

# ---- the catalogs (from KB5_fold_new_sleeves + KB5_leadlag_subh4) ----
LEADLAG_FULL = [  # the dropped full 8-config core (leader,follower,sign,look,z,thesis,geom,confirm,confirm_sign,regime)
    ("NAS100","SPX500",+1,3,1.5,"momentum","T1.5",None,None,"align"),
    ("SPX500","NAS100",+1,3,1.5,"momentum","T2.0",None,None,"align"),
    ("US30_cash","GER40",+1,6,1.5,"momentum","T1.5",None,None,"align"),
    ("GER40","UK100",+1,6,2.0,"reversion","T1.5",None,None,None),
    ("SPX500","GER40",+1,6,2.0,"reversion","T2.0",None,None,None),
    ("US30_cash","USDJPY",+1,6,2.0,"momentum","T2.0",None,None,None),
    ("USDJPY","AUDJPY",+1,6,2.0,"reversion","T2.0",None,None,None),
    ("USDJPY","GBPJPY",+1,6,2.0,"reversion","T1.5",None,None,None),
]
# HIGHEST-SHARPE subset (brief): US30->USDJPY + NAS<->SPX index spillover (null-clearing, deepest n)
LEADLAG_HISHARPE = [
    ("NAS100","SPX500",+1,3,1.5,"momentum","T1.5",None,None,"align"),
    ("SPX500","NAS100",+1,3,1.5,"momentum","T2.0",None,None,"align"),
    ("US30_cash","USDJPY",+1,6,2.0,"momentum","T2.0",None,None,None),
]
SUBH4_LEGS = [
    ("USDJPY","EURJPY",+1,16,2.5,"momentum","T2.0","london_open"),
    ("USDJPY","EURJPY",+1,16,2.5,"momentum","T1.5","london_open"),
]

def gen_leadlag(catalog, exit_mode, winf, label):
    rows=[]; seen=set()
    for cfg in catalog:
        L,F,sgn,look,z,th,gname,conf,csign,regime = cfg
        for r in mine_pair_relabel(L,F,sgn,look,z,th,gname,confirm=conf,confirm_sign=csign,
                                   regime=regime, exit_mode=exit_mode, winf=winf):
            rows.append(dict(sleeve=label, **r))
    return rows

def gen_subh4(exit_mode, winf, label):
    rows=[]; seen=set()
    for (L,F,sgn,look,z,th,gname,sess) in SUBH4_LEGS:
        sig = SH.leader_signal(L, look)
        for r in mine_subh4_relabel(L,F,sgn,look,z,th,gname,sess,exit_mode=exit_mode,winf=winf,sig=sig):
            key=(F, r['ts'])  # dedupe across the two geoms on the same entry timestamp (matches shipped)
            if key in seen: continue
            seen.add(key)
            rows.append(dict(sleeve=label, sym=r['sym'], date=r['date'], year=r['year'], R=r['R']))
    return rows

# ---- IDB intraday FVG re-labeled under STATE_D ----
def fvg_state_d_rows(grp, syms, tf, sleeve, *, gate_k=1.2, ac_thr=0.10, trend_lb=30, winf=wins12):
    """IDB FVG-retest entry (structural stop sd computed per trade) re-exited with STATE_D."""
    mb = 320 if tf=='H1' else 1280
    rows=[]
    for s in syms:
        T,B = IDB.load_ltf(grp,s,tf)
        if len(B) < 300: continue
        atrs=[atr14(B,k) for k in range(len(B))]
        cost = w1.cost_for(s)
        n=len(B)
        for i in range(max(trend_lb+2,101), n-1):
            a=atrs[i]
            if a<=0: continue
            sma100=sum(atrs[i-99:i+1])/100
            if sma100<=0 or a < gate_k*sma100: continue
            diff=B[i].c-B[i-trend_lb].c
            tr = 1 if diff>1.0*a else (-1 if diff<-1.0*a else 0)
            if tr==0: continue
            ac=cs.autocorr(B,i,60)
            if ac_thr is not None and (ac is None or ac<ac_thr): continue
            b=B[i]; d=0; sd=None
            if tr==1:
                for k in range(i-2, max(i-9,60), -1):
                    gap_top=B[k].l; gap_bot=B[k-2].h
                    if gap_top-gap_bot < 0.10*a: continue
                    if b.l<=gap_top and b.c>gap_bot and b.c>b.o:
                        sd=max((b.c-min(b.l,gap_bot))+0.10*a, 0.25*a); d=1; break
            else:
                for k in range(i-2, max(i-9,60), -1):
                    gap_bot=B[k].h; gap_top=B[k-2].l
                    if gap_top-gap_bot < 0.10*a: continue
                    if b.h>=gap_bot and b.c<gap_top and b.c<b.o:
                        sd=max((max(b.h,gap_top)-b.c)+0.10*a, 0.25*a); d=-1; break
            if d==0 or sd is None: continue
            vr = cs.vol_ratio(atrs, i)
            R = _state_d_raw(B, i, d, sd, vr, cost, mb, winf)
            rows.append(dict(sleeve=sleeve, sym=s, date=T[i].date(), year=T[i].year, R=R))
    return rows

def gen_idb(exit_mode, winf):
    """crypto + metals intraday FVG (the two VALIDATED IDB tiers). STATE_D or fixed via fvg fallback."""
    if exit_mode == 'state_d':
        cr = fvg_state_d_rows('crypto', IDB.CRYPTO, 'H1', 'idb_crypto_fvg', ac_thr=0.10, winf=winf)
        me = fvg_state_d_rows('metals', IDB.METALS, 'H1', 'idb_metals_fvg', ac_thr=None, winf=winf)
        return cr, me
    else:
        # fixed-2R baseline (what IDB shipped)
        cra,_ = IDB.build_fvg('crypto', IDB.CRYPTO, 'H1', ac_thr=0.10, tgt_R=2.0)
        mea,_ = IDB.build_fvg('metals', IDB.METALS, 'H1', ac_thr=None, tgt_R=2.0)
        cr=[dict(sleeve='idb_crypto_fvg', sym=r['sym'], date=r['t'].date(), year=r['year'], R=winf(r['R'])) for r in cra]
        me=[dict(sleeve='idb_metals_fvg', sym=r['sym'], date=r['t'].date(), year=r['year'], R=winf(r['R'])) for r in mea]
        return cr, me

# =========================================================================== #
# Book assembly + MC harness (reuse the locked clean_3 day grid + LOCKED MC)
# =========================================================================== #
def candidate_daily(rows):
    byday=collections.defaultdict(list)
    for r in rows: byday[r['date']].append(r['R'])
    return {d: sum(v)/len(v) for d,v in byday.items()}

def pearson(x,y):
    n=len(x)
    if n<8: return None
    mx=sum(x)/n; my=sum(y)/n
    sx=sum((a-mx)**2 for a in x); sy=sum((b-my)**2 for b in y)
    if sx==0 or sy==0: return 0.0
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/math.sqrt(sx*sy)

def load_clean3_daily():
    """Rebuild the clean_3 deploy daily series + per-sleeve day map from the locked caches.
    clean_3 = W3 book (8) + sub_xvol_pullback(.45) + vp_euidx_pocgrav(.30) + sub_mid_dn_revert(.20)."""
    streams_w3 = pickle.load(open(HERE/'INTEG_W3_streams_cache.pkl','rb'))
    days_w3, M_w3 = W3.W2.build_matrix(streams_w3)
    book_sleeves = W3.SLEEVES
    daily_sleeve = {sl:{} for sl in book_sleeves}
    for di,day in enumerate(days_w3):
        for si,sl in enumerate(book_sleeves):
            daily_sleeve[sl][day]=M_w3[di][si]
    comb_book = {day: sum(M_w3[di]) for di,day in enumerate(days_w3)}
    new = pickle.load(open(HERE/'INTEG_W5_new_streams_cache.pkl','rb'))
    CLEAN3_CONF = {'sub_xvol_pullback':0.45,'vp_euidx_pocgrav':0.30,'sub_mid_dn_revert':0.20}
    clean3 = dict(comb_book)
    new_daily = {}
    for nm,cf in CLEAN3_CONF.items():
        cd = candidate_daily(new[nm]); new_daily[nm]={d:v*cf for d,v in cd.items()}
    all_days = sorted(set(clean3) | set().union(*[set(new_daily[n]) for n in CLEAN3_CONF]))
    comb_clean3 = {d: clean3.get(d,0.0) + sum(new_daily[n].get(d,0.0) for n in CLEAN3_CONF) for d in all_days}
    return all_days, comb_clean3, comb_book

def mc_full(series_map_days, all_days, label, vol_scale_ref_std, sizes=(0.0075,0.01,0.0125,0.015,0.02)):
    """Run the LOCKED MC at growth sizes, vol-matched to ref std, all + stress, + maxDD/ruin."""
    series = [series_map_days.get(d,0.0) for d in all_days]
    fwd = [series_map_days.get(d,0.0) for d in all_days if d.year>=2025]
    sd = statistics.pstdev(series); mean=statistics.fmean(series)
    vs = vol_scale_ref_std/sd if sd>0 else 1.0
    stress = [(v*1.5 if v<0 else v) for v in series]
    out = dict(daily_mean=round(mean,5), daily_std=round(sd,5), sharpe=round(mean/sd,4) if sd>0 else 0.0,
               vol_scale=round(vs,4), n_days=len(series), grid={})
    for sz in sizes:
        all_r = mc_series(series, sz*vs, seed_base=1)
        str_r = mc_series(stress, sz*vs, seed_base=999)
        fwd_r = mc_series(fwd, sz*vs, seed_base=777)
        out['grid'][f"{sz*100:.2f}%"] = dict(
            p_pass=all_r['p_pass'], p_fail_dd=all_r['p_fail_dd'], p_fail_daily=all_r['p_fail_daily'],
            med_days=all_r['med_days_pass'],
            stress_p_pass=str_r['p_pass'], stress_p_fail_dd=str_r['p_fail_dd'], stress_p_fail_daily=str_r['p_fail_daily'],
            fwd_p_pass=fwd_r['p_pass'], fwd_med_days=fwd_r['med_days_pass'])
    return out

def main():
    report = {'track':'KB7_reinstate_sleeves', 'wave':'UNLEASH',
              'objective':'max growth-rate s.t. FTMO; reinstate dropped sleeves under STATE_D + growth sizing'}
    all_days, comb_clean3, comb_book = load_clean3_daily()
    ref_std = statistics.pstdev([comb_clean3[d] for d in all_days])
    report['clean3_ref_std'] = round(ref_std,5)

    print("=== BASELINE: clean_3 deploy book (locked) ===")
    base = mc_full(comb_clean3, all_days, 'clean_3', ref_std)
    report['baseline_clean3'] = base
    for sz,g in base['grid'].items():
        print(f"  {sz}: P(pass)={g['p_pass']:.3%} stress={g['stress_p_pass']:.3%} maxDD-fail={g['p_fail_dd']:.3%} med_days={g['med_days']}")

    # ---- materialize the candidate sleeves under exit/winsor variants ----
    print("\n=== MATERIALIZING dropped sleeves (STATE_D + relaxed winsor) ===")
    candidates = {}
    # leadlag full + hi-sharpe, fixed-R(shipped) vs STATE_D, winsor5 vs winsor12
    for emode in ('fixed','state_d'):
        for wlbl,winf in (('w5',wins5),('w12',wins12)):
            candidates[f'leadlag_full__{emode}__{wlbl}'] = gen_leadlag(LEADLAG_FULL, emode, winf, 'leadlag_full')
            candidates[f'leadlag_hisharpe__{emode}__{wlbl}'] = gen_leadlag(LEADLAG_HISHARPE, emode, winf, 'leadlag_hisharpe')
            candidates[f'subh4_ll_fx__{emode}__{wlbl}'] = gen_subh4(emode, winf, 'subh4_ll_fx')
    # IDB crypto/metals
    for emode in ('fixed','state_d'):
        for wlbl,winf in (('w5',wins5),('w12',wins12)):
            cr,me = gen_idb(emode, winf)
            candidates[f'idb_crypto__{emode}__{wlbl}'] = cr
            candidates[f'idb_metals__{emode}__{wlbl}'] = me

    # per-sleeve stats
    report['sleeve_stats'] = {}
    print(f"\n{'sleeve_variant':>34} {'n':>5} {'TRAIN':>16} {'FWD':>16} {'win%':>5} {'/yr':>5}")
    for nm, rows in candidates.items():
        st = I.sleeve_stats(rows)
        py = {y:v for y,v in st['per_year'].items()}
        report['sleeve_stats'][nm] = dict(n=st['n'], train=st['train'], fwd=st['fwd'],
                                          fwd_per_year=st['fwd_per_year'], per_year=py)
        print(f"{nm:>34} {st['n']:>5} {str(st['train']):>16} {str(st['fwd']):>16} {st['fwd'][2]:>5.0f} {st['fwd_per_year']:>5.0f}")

    # ---- fold each candidate (STATE_D + w12, the growth config) into clean_3 + MC ----
    print("\n=== FOLD CANDIDATE INTO clean_3 + LOCKED MC (vol-matched, growth sizes) ===")
    # confidence weights to test (size-by-confidence; growth posture = a bit higher than the W5 demotes)
    FOLD_CONF = {
        'leadlag_full': [0.10, 0.20],
        'leadlag_hisharpe': [0.20, 0.35],
        'subh4_ll_fx': [0.15, 0.30],
        'idb_crypto': [0.30, 0.45],
        'idb_metals': [0.20, 0.30],
    }
    report['fold_results'] = {}
    report['corr_vs_book'] = {}
    # use STATE_D + w12 streams
    for base_sleeve, confs in FOLD_CONF.items():
        key = f'{base_sleeve}__state_d__w12'
        rows = candidates[key]
        cd = candidate_daily(rows)
        # corr vs clean_3 combined
        u = sorted(set(cd) | set(all_days))
        cc = pearson([cd.get(d,0.0) for d in u], [comb_clean3.get(d,0.0) for d in u])
        report['corr_vs_book'][base_sleeve] = round(cc,4) if cc is not None else None
        for cf in confs:
            folded = {d: comb_clean3.get(d,0.0) + cd.get(d,0.0)*cf for d in sorted(set(all_days)|set(cd))}
            fdays = sorted(folded)
            res = mc_full(folded, fdays, f'{base_sleeve}@{cf}', ref_std)
            report['fold_results'][f'{base_sleeve}@{cf}'] = dict(corr=report['corr_vs_book'][base_sleeve],
                                                                 fwd_per_year=report['sleeve_stats'][key]['fwd_per_year'],
                                                                 mc=res)
            g1 = res['grid']['1.00%']; g15 = res['grid']['1.50%']
            print(f"  {base_sleeve}@{cf} corr={report['corr_vs_book'][base_sleeve]:+.3f} | "
                  f"@1%: P={g1['p_pass']:.2%} str={g1['stress_p_pass']:.2%} dd={g1['p_fail_dd']:.2%} d={g1['med_days']} | "
                  f"@1.5%: P={g15['p_pass']:.2%} str={g15['stress_p_pass']:.2%} dd={g15['p_fail_dd']:.2%} d={g15['med_days']}")

    (HERE/'KB7_REINSTATE_RESULT.json').write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote KB7_REINSTATE_RESULT.json")
    return report

if __name__ == '__main__':
    main()
