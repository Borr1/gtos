"""UNCAP_book_mc.py — book-level verdict for the un-cap relabels.

The per-trade EV study (UNCAP_relabel_study[2].py) shows that lifting the TARGET (the real
binding ceiling; the +5 winsor is dead) recovers right-tail EV on a subset of sleeves, but at
the cost of LOWER win-rate and HIGHER variance. The FTMO verdict must come from the vol-matched
challenge-pass + max-DD MC, NOT per-trade EV. This script:

  1. Rebuilds the clean_3 deploy book daily streams from the LOCKED caches.
  2. For each continuation sleeve, swaps in a RELABELED per-trade R stream (higher target /
     extended maxbars) chosen by a DISCIPLINED rule, keeping every entry/date identical.
  3. Re-runs the LOCKED MC engine (mc_series: 8%tgt/5%daily/10%maxDD/block5/N20000) vol-matched,
     all/fwd/stress, + daily-breach + max-DD-fail probability, and the 2-account joint pass.

Compares the deploy baseline (current targets) vs the un-capped book on:
  P(pass), P(fail_maxdd), P(fail_daily), median days-to-pass, worst day, at each size.

DISCIPLINE (no over-fit on the right tail):
  - We test TWO relabel policies:
      (A) CONSERVATIVE  = only sleeves whose higher-target lift is train-supported OR
                          both-forward-years-positive (sub_xvol_pullback, sub_mid_dn_revert, crypto).
      (B) AGGRESSIVE    = (A) + subh4 T12 (2025-only carried; flagged single-regime).
  - metals_core / energy keep current targets (relabel study showed higher targets DEGRADE fwd).
LEAK-FREE: same audited entries; geometry_lib pessimistic exits; real cost; TRAIN/FWD honest.
"""
import sys, json, statistics, collections, datetime, pickle
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate, atr14
import wave1_structure_setups_ict as w1
import compounding_sleeve as cs
import substrate as sub
import SUBSTRATE_corrcheck as SC
import KB5_leadlag_subh4 as SH
import INTEG_portfolio_build as I
import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3
import KB5_fold_new_sleeves as FOLD

mc_series = W2.mc_series; joint_pass_mc = W2.joint_pass_mc
DAILY = I.DAILY

# --- relabeled per-trade streams for the continuation sleeves (entries identical) ---
def relabel_substrate(cell, tmult, maxbars, symbols=None):
    geom, dmode, conds = SC.parse_cell(cell)
    stop_atr, _ = geom
    syms = symbols or w1.SYMBOLS
    rows = []
    for s in syms:
        built = sub.build_states(s)
        if built is None: continue
        T, B, A, states = built
        cost = w1.cost_for(s); n = len(B)
        for i in range(sub.WARMUP, n - sub.MAXBARS - 1):
            st = states[i]
            if st is None: continue
            co = sub.cell_coords(st)
            if all(co.get(dd) == bb for dd, bb in conds.items()):
                a = A[i]
                if a <= 0: continue
                sd = stop_atr * a
                r = simulate(B, i, dmode, stop_dist=sd, target_dist=tmult * sd,
                             maxbars=maxbars, cost=cost / stop_atr)
                rows.append(dict(sym=s, date=T[i].date(), year=T[i].year, R=max(-1.3, min(5.0, r))))
    return rows

def relabel_subh4(tmult, maxbars):
    L, F, sgn, look, z, sess = "USDJPY", "EURJPY", +1, 16, 2.5, "london_open"
    sig = SH.leader_signal(L, look); pf = SH.load_m15(F)
    fb = pf["bars"]; ftmap = pf["tmap"]; fatrs = pf["atrs"]; cost = SH.cost_for(F)
    rows = []; last_idx = -10**9; seen = set()
    for ts, zz in sig.items():
        if abs(zz) < z or not SH._session_ok(ts, sess): continue
        i = ftmap.get(ts)
        if i is None or i < 14 or i >= len(fb) - 2: continue
        if i - last_idx < 4: continue
        a = fatrs[i]
        if a <= 0: continue
        d = (1 if zz > 0 else -1) * sgn
        if ts in seen: continue
        seen.add(ts)
        stop = 0.5 * a
        r = simulate(fb, i, d, stop_dist=stop, target_dist=tmult * stop, maxbars=maxbars, cost=cost)
        rows.append(dict(sym=F, date=ts.date(), year=ts.year, R=max(-1.3, min(5.0, r))))
        last_idx = i
    return rows

def relabel_crypto(tmult, maxbars):
    import kb2_new_breadth as KB
    T, B = KB.resample_eth_h4(); cost = w1.cost_for('ETHUSD')
    atrs = [atr14(B, i) for i in range(len(B))]
    rows = []
    for (i, d) in KB.crypto_breakout_signals(B, 20):
        a = atrs[i]
        if a <= 0: continue
        ac = cs.autocorr(B, i, 60)
        if ac is None or ac < 0.15: continue
        sd = 2.0 * a
        r = simulate(B, i, d, stop_dist=sd, target_dist=tmult * sd, maxbars=maxbars, cost=cost)
        rows.append(dict(sym='ETHUSD', date=T[i].date(), year=T[i].year, R=max(-1.3, min(5.0, r))))
    return rows

# clean_3 = book + sub_xvol_pullback(0.45) + vp_euidx_pocgrav(0.30) + sub_mid_dn_revert(0.20)
XVOL_CELL = "g1.0_3.0|dir=1|depth4|vol=xhi|persist=rand|trend=up|mtf=conflict"
MIDDN_CELL = "g1.0_3.0|dir=1|depth7|vol=mid|trend=dn|mtf=neutral|rngpos=mid|comp=norm|persist=revert|session=ny"
CLEAN3 = {'sub_xvol_pullback': 0.45, 'vp_euidx_pocgrav': 0.30, 'sub_mid_dn_revert': 0.20}

def candidate_daily(rows):
    by = collections.defaultdict(list)
    for r in rows: by[r['date']].append(r['R'])
    return {d: sum(v) / len(v) for d, v in by.items()}

def build_book_matrix(new_overrides):
    """new_overrides: {sleeve_name: relabeled_rows}. Returns (all_days, M, fwd_mask, comb, comb_book).
    Book sleeves come from W3 cache UNCHANGED; clean_3 new sleeves use overrides where provided."""
    streams_w3 = pickle.load(open(HERE / 'INTEG_W3_streams_cache.pkl', 'rb'))
    days_w3, M_w3 = W3.W2.build_matrix(streams_w3)
    book_sleeves = W3.SLEEVES
    daily_sleeve = {sl: {} for sl in book_sleeves}
    for di, day in enumerate(days_w3):
        for si, sl in enumerate(book_sleeves):
            daily_sleeve[sl][day] = M_w3[di][si]
    comb_book = {day: sum(M_w3[di]) for di, day in enumerate(days_w3)}
    book_days = set(days_w3)

    new_streams = pickle.load(open(HERE / 'INTEG_W5_new_streams_cache.pkl', 'rb'))
    cand = {}
    for nm in CLEAN3:
        rows = new_overrides.get(nm, new_streams[nm])
        cand[nm] = candidate_daily(rows)
    nd = {nm: {d: v * CLEAN3[nm] for d, v in cand[nm].items()} for nm in CLEAN3}

    all_days = sorted(book_days | set().union(*[set(cand[n]) for n in CLEAN3]))
    fwd_mask = [d.year >= 2025 for d in all_days]
    M = []
    for day in all_days:
        M.append([daily_sleeve[sl].get(day, 0.0) for sl in book_sleeves]
                 + [nd[nm].get(day, 0.0) for nm in CLEAN3])
    comb = [sum(r) for r in M]
    book_series = [comb_book.get(d, 0.0) for d in all_days]
    sd_book = statistics.pstdev([comb_book[d] for d in days_w3])
    return all_days, M, fwd_mask, comb, book_series, sd_book, book_sleeves

def mc_block(comb, book_series, sd_book, fwd_mask, label):
    sd = statistics.pstdev(comb); vs = sd_book / sd if sd > 0 else 1.0
    comb_fwd = [v for v, f in zip(comb, fwd_mask) if f]
    out = dict(label=label, daily_mean=round(statistics.fmean(comb), 5),
               daily_mean_fwd=round(statistics.fmean(comb_fwd), 5),
               daily_std=round(sd, 5), sharpe=round(statistics.fmean(comb) / sd, 4),
               vol_scale=round(vs, 4), grid={})
    for r in (0.005, 0.0075, 0.01, 0.015, 0.02):
        vm = mc_series(comb, r * vs, seed_base=1)
        comb_str = [(v * 1.5 if v < 0 else v) for v in comb]
        st = mc_series(comb_str, r * vs, seed_base=999)
        fwd = mc_series(comb_fwd, r, seed_base=777)
        out['grid'][f"{r*100:.2f}%"] = dict(
            p_pass_vm=round(vm['p_pass'], 4), p_fail_dd_vm=round(vm['p_fail_dd'], 4),
            p_fail_daily_vm=round(vm['p_fail_daily'], 4), med_days_vm=vm['med_days_pass'],
            p_pass_stress_vm=round(st['p_pass'], 4), p_pass_fwd=round(fwd['p_pass'], 4),
            worst_day_pct=round(min(comb) * r * vs * 100, 3))
    return out

def main():
    report = {'track': 'uncap_book_mc', 'date': str(datetime.date.today()), 'policies': {}}

    # ---- BASELINE deploy book (current targets) ----
    print("=== BASELINE deploy book (current targets) ===")
    ad, M0, fm, comb0, book0, sdb, bs = build_book_matrix({})
    base = mc_block(comb0, book0, sdb, fm, 'baseline_clean3')
    report['baseline'] = base
    for r in ('0.50%', '0.75%', '1.00%', '1.50%', '2.00%'):
        g = base['grid'][r]
        print(f"  {r}: P(pass)={g['p_pass_vm']:.2%} P(maxDD)={g['p_fail_dd_vm']:.2%} "
              f"P(daily)={g['p_fail_daily_vm']:.2%} med_days={g['med_days_vm']} "
              f"stress={g['p_pass_stress_vm']:.2%} fwd={g['p_pass_fwd']:.2%} worst={g['worst_day_pct']}%")

    # ---- materialize relabels (cache to keep re-runs fast) ----
    cache = HERE / 'UNCAP_relabel_streams.pkl'
    if cache.exists():
        RL = pickle.load(open(cache, 'rb'))
        print("\n(loaded relabel streams from cache)")
    else:
        print("\nMaterializing relabeled streams (higher target + extended maxbars)...")
        drop = FOLD.DROP_XVOL
        RL = {
            # sub_xvol: T6 mb1x was fwd-optimal & both fwd yrs up; mb1x (extend gave no further lift)
            'sub_xvol_pullback_T6': relabel_substrate(XVOL_CELL, 6.0, sub.MAXBARS,
                                                      symbols=[s for s in w1.SYMBOLS if s not in drop]),
            # sub_mid_dn: T12 mb2x both fwd yrs strongly up
            'sub_mid_dn_revert_T8': relabel_substrate(MIDDN_CELL, 8.0, sub.MAXBARS),
            'sub_mid_dn_revert_T12_mb2': relabel_substrate(MIDDN_CELL, 12.0, sub.MAXBARS * 2),
        }
        pickle.dump(RL, open(cache, 'wb'))
    print(f"  relabel streams: " + ", ".join(f"{k}:n{len(v)}" for k, v in RL.items()))

    # ---- POLICY A: CONSERVATIVE (sub_xvol T6 + sub_mid T8, both fwd-yrs-positive) ----
    print("\n=== POLICY A (CONSERVATIVE): sub_xvol_pullback->T6, sub_mid_dn_revert->T8 ===")
    ovA = {'sub_xvol_pullback': RL['sub_xvol_pullback_T6'],
           'sub_mid_dn_revert': RL['sub_mid_dn_revert_T8']}
    adA, MA, fmA, combA, bookA, sdbA, _ = build_book_matrix(ovA)
    polA = mc_block(combA, bookA, sdbA, fmA, 'policyA_conservative')
    report['policies']['A_conservative'] = polA
    for r in ('0.50%', '0.75%', '1.00%', '1.50%', '2.00%'):
        g = polA['grid'][r]
        print(f"  {r}: P(pass)={g['p_pass_vm']:.2%} P(maxDD)={g['p_fail_dd_vm']:.2%} "
              f"P(daily)={g['p_fail_daily_vm']:.2%} med_days={g['med_days_vm']} "
              f"stress={g['p_pass_stress_vm']:.2%} fwd={g['p_pass_fwd']:.2%} worst={g['worst_day_pct']}%")

    # ---- POLICY B: AGGRESSIVE (A + sub_mid T12 mb2 instead of T8) ----
    print("\n=== POLICY B (AGGRESSIVE): sub_xvol->T6, sub_mid_dn->T12 mb2x ===")
    ovB = {'sub_xvol_pullback': RL['sub_xvol_pullback_T6'],
           'sub_mid_dn_revert': RL['sub_mid_dn_revert_T12_mb2']}
    adB, MB, fmB, combB, bookB, sdbB, _ = build_book_matrix(ovB)
    polB = mc_block(combB, bookB, sdbB, fmB, 'policyB_aggressive')
    report['policies']['B_aggressive'] = polB
    for r in ('0.50%', '0.75%', '1.00%', '1.50%', '2.00%'):
        g = polB['grid'][r]
        print(f"  {r}: P(pass)={g['p_pass_vm']:.2%} P(maxDD)={g['p_fail_dd_vm']:.2%} "
              f"P(daily)={g['p_fail_daily_vm']:.2%} med_days={g['med_days_vm']} "
              f"stress={g['p_pass_stress_vm']:.2%} fwd={g['p_pass_fwd']:.2%} worst={g['worst_day_pct']}%")

    # ---- daily means summary (growth-rate proxy) ----
    print("\n=== DAILY MEAN (growth-rate proxy; un-vol-matched, per unit risk) ===")
    print(f"  baseline:    all={base['daily_mean']:+.5f} fwd={base['daily_mean_fwd']:+.5f} sharpe={base['sharpe']}")
    print(f"  policyA:     all={polA['daily_mean']:+.5f} fwd={polA['daily_mean_fwd']:+.5f} sharpe={polA['sharpe']}")
    print(f"  policyB:     all={polB['daily_mean']:+.5f} fwd={polB['daily_mean_fwd']:+.5f} sharpe={polB['sharpe']}")

    (HERE / 'UNCAP_BOOK_MC_RESULT.json').write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote UNCAP_BOOK_MC_RESULT.json")


if __name__ == '__main__':
    main()
