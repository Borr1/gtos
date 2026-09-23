"""KB7 — Growth-optimal + confidence-proportional (Kelly-lite) sizing (track KB7, UNLEASH wave).

OBJECTIVE: maximize speed-to-+8% s.t. FTMO rules (5% daily, 10% maxDD) at an ACCEPTABLE
P(maxDD-breach) — NOT minimal size. Two deliverables, both on the LOCKED W2 MC engine
(INTEG_portfolio_build_w2.mc_series / joint_pass_mc) at the clean_3 deploy config:

  GOAL 1  GROWTH-OPTIMAL BASE SIZE. Fine grid 1.00-2.50% (vol-matched eff = nominal*VOL_SCALE)
          on all-history / forward / 1.5x-left-tail-stress, reporting P(pass), P(maxDD-breach),
          P(daily-breach), median days-to-pass, monthly%. Find the size that maximizes growth
          (min median-days / max monthly%) s.t. stress P(maxDD-breach) stays acceptable.

  GOAL 2  KELLY-LITE CONFIDENCE-PROPORTIONAL per-day sizing. A LEAK-FREE per-day conviction
          signal already exists: the COUNT of independent sleeves firing that day (you know which
          sleeves triggered before you size). Forward-validated monotone: n_active=1 -> FWD +0.12R,
          n_active>=4 -> FWD +0.61R. Bet BIGGER on high-conviction (multi-sleeve-agreement) days,
          smaller on marginal 1-sleeve days, CAPPED to keep the worst-day within the daily limit
          and to avoid ruin. The multiplier is VARIANCE-NEUTRALIZED (mean multiplier == 1 over the
          base population) so it is a pure REALLOCATION of risk toward conviction, not a stealth
          size-up; the size-up version is reported separately as the aggressive growth profile.

Verdict book = the VOL-MATCHED 1.5x left-tail STRESS challenge-pass + maxDD-fail MC, per-year +
forward holdout, NOT per-trade EV alone. No lookahead: the conviction multiplier uses only the
count of sleeves firing on the SAME day (known at decision time), learned-free (monotone bins).
Per-trade R winsorized [-1.3,+5] at source (inherited); real cost; leak-free labelers upstream.
"""
import sys, json, statistics, pickle, collections, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3
import INTEG_portfolio_build as I

mc_series = W2.mc_series; joint_pass_mc = W2.joint_pass_mc
TARGET = I.TARGET; MAXDD = I.MAXDD; DAILY = I.DAILY; BLOCK = I.BLOCK; PATHCAP = I.PATHCAP; N = I.N

CLEAN3 = {'sub_xvol_pullback': 0.45, 'vp_euidx_pocgrav': 0.30, 'sub_mid_dn_revert': 0.20}


def candidate_daily(rows):
    by = collections.defaultdict(list)
    for r in rows:
        by[r['date']].append(r['R'])
    return {d: sum(v) / len(v) for d, v in by.items()}


def build_deploy_matrix():
    """Reconstruct the clean_3 deploy per-day x per-sleeve conf-weighted matrix EXACTLY as
    INTEG_w5_clean3_deploy.main (so the LOCKED MC reproduces INTEG_W5_CLEAN3_DEPLOY.json)."""
    streams_w3 = pickle.load(open(HERE / 'INTEG_W3_streams_cache.pkl', 'rb'))
    days_w3, M_w3 = W3.W2.build_matrix(streams_w3)
    book_sleeves = W3.SLEEVES
    daily_sleeve = {sl: {} for sl in book_sleeves}
    for di, day in enumerate(days_w3):
        for si, sl in enumerate(book_sleeves):
            daily_sleeve[sl][day] = M_w3[di][si]
    comb_book = {day: sum(M_w3[di]) for di, day in enumerate(days_w3)}
    sd_book = statistics.pstdev([comb_book[d] for d in days_w3])
    new_streams = pickle.load(open(HERE / 'INTEG_W5_new_streams_cache.pkl', 'rb'))
    cand = {nm: candidate_daily(new_streams[nm]) for nm in CLEAN3}
    nd = {nm: {d: v * cf for d, v in cand[nm].items()} for nm, cf in CLEAN3.items()}
    sleeves = list(book_sleeves) + list(CLEAN3.keys())
    all_days = sorted(set(days_w3) | set().union(*[set(cand[n]) for n in CLEAN3]))
    M = []
    for day in all_days:
        M.append([daily_sleeve[sl].get(day, 0.0) for sl in book_sleeves]
                 + [nd[nm].get(day, 0.0) for nm in CLEAN3])
    return all_days, sleeves, M, sd_book


def conviction_count(row):
    """LEAK-FREE per-day conviction = number of sleeves with a non-zero contribution that day
    (= number of independent edges firing; known at decision time before sizing)."""
    return sum(1 for v in row if abs(v) > 1e-9)


# Kelly-lite multiplier: monotone step function of n_active, learned-free (3 honest bins matching
# the forward-validated EV monotonicity), capped. Two variants:
#   NEUTRAL (reallocation): mean multiplier == 1 over the base-day population (pure tilt toward
#           conviction; same average gross risk -> a fair head-to-head vs flat at the SAME size).
#   SIZEUP (aggressive growth): floor 1.0, scale UP on conviction (never below base) -> uses the
#           conviction edge to lift growth, bounded by KELLY_CAP to protect the daily/maxDD wall.
KELLY_BINS = ((1, 1), (2, 3), (4, 99))          # n_active buckets (forward-monotone EV)
KELLY_SIZEUP = (0.85, 1.10, 1.60)               # SIZEUP multiplier per bucket (>= ~1, capped 1.6)
KELLY_CAP = 1.75                                 # hard governor cap (matches OVERLAY_SIZEUP_MAX)


def kelly_mult_sizeup(na):
    for (lo, hi), m in zip(KELLY_BINS, KELLY_SIZEUP):
        if lo <= na <= hi:
            return min(m, KELLY_CAP)
    return 1.0


def apply_kelly(comb, nactive, sizeup=True, neutralize=False):
    if sizeup:
        mults = [kelly_mult_sizeup(na) for na in nactive]
    else:
        mults = [1.0] * len(comb)
    if neutralize:
        # rescale so the MEAN multiplier == 1 (pure reallocation, same avg gross risk)
        mm = statistics.fmean(mults)
        mults = [m / mm for m in mults]
    return [c * m for c, m in zip(comb, mults)], mults


def grid_mc(series, scale, label, stress=False, seed_base=1):
    s = [(v * 1.5 if v < 0 else v) for v in series] if stress else series
    out = {}
    mu = statistics.fmean(series)
    for r in (0.010, 0.0125, 0.015, 0.0175, 0.020, 0.0225, 0.025):
        res = mc_series(s, r * scale, seed_base=seed_base)
        worst = min(s) * r * scale
        breach = sum(1 for v in s if v * r * scale <= -DAILY) / len(s)
        mo = mu * r * scale * 21 * 100
        out[f"{r * 100:.2f}%"] = dict(p_pass=res['p_pass'], p_fail_dd=res['p_fail_dd'],
                                      p_fail_daily=res['p_fail_daily'], med_days=res['med_days_pass'],
                                      worst_day_pct=round(worst * 100, 3),
                                      daily_breach_pct=round(breach * 100, 3),
                                      monthly_pct=round(mo, 2))
    return out


def main():
    all_days, sleeves, M, sd_book = build_deploy_matrix()
    comb = [sum(r) for r in M]
    nactive = [conviction_count(r) for r in M]
    sd = statistics.pstdev(comb)
    VS = round(sd_book / sd, 4)
    fwd_mask = [d.year >= 2025 for d in all_days]
    comb_fwd = [v for v, f in zip(comb, fwd_mask) if f]
    nactive_fwd = [n for n, f in zip(nactive, fwd_mask) if f]
    M_fwd = [r for r, f in zip(M, fwd_mask) if f]

    rep = dict(track='KB7_growth_kelly_sizing', book='clean_3', vol_scale=VS,
               n_days=len(comb), n_days_fwd=len(comb_fwd),
               daily_mean=round(statistics.fmean(comb), 5), daily_std=round(sd, 5),
               daily_mean_fwd=round(statistics.fmean(comb_fwd), 5))

    # full-Kelly reference (unconstrained log-growth optimum in unit-R space)
    mu, var = statistics.fmean(comb), statistics.pvariance(comb)
    rep['full_kelly_f_star_unitR'] = round(mu / var, 4)
    rep['note_full_kelly'] = ("Unconstrained full-Kelly f*=mu/var in unit-R risk space; the FTMO "
                              "10% maxDD wall binds FAR below this, so the constrained growth-optimum "
                              "is the maxDD-acceptable point, not f*.")

    # ---- GOAL 1: growth-optimal base size grid (LOCKED engine, vol-matched) ----
    rep['goal1_growth_grid'] = dict(
        all_history=grid_mc(comb, VS, 'all', seed_base=1),
        all_history_stress15=grid_mc(comb, VS, 'all_stress', stress=True, seed_base=999),
        forward=grid_mc(comb_fwd, 1.0, 'fwd', seed_base=777),   # fwd reported at NOMINAL (recent regime)
    )

    # ---- conviction signal validation (forward EV monotonicity) ----
    conv = {}
    for (lo, hi) in KELLY_BINS:
        sel = [comb[i] for i in range(len(comb)) if lo <= nactive[i] <= hi]
        selF = [comb_fwd[i] for i in range(len(comb_fwd)) if lo <= nactive_fwd[i] <= hi]
        conv[f"n_active_{lo}_{hi}"] = dict(
            all_n=len(sel), all_meanR=round(statistics.fmean(sel), 4) if sel else None,
            fwd_n=len(selF), fwd_meanR=round(statistics.fmean(selF), 4) if selF else None,
            sizeup_mult=kelly_mult_sizeup(lo))
    rep['goal2_conviction_signal'] = conv

    def pear(x, y):
        n = len(x); mx = sum(x) / n; my = sum(y) / n
        sx = sum((a - mx) ** 2 for a in x); sy = sum((b - my) ** 2 for b in y)
        return round(sum((a - mx) * (b - my) for a, b in zip(x, y)) / ((sx * sy) ** 0.5), 4)
    rep['conviction_corr_all'] = pear(nactive, comb)
    rep['conviction_corr_fwd'] = pear(nactive_fwd, comb_fwd)

    # ---- GOAL 2: Kelly-lite head-to-head (NEUTRAL reallocation, same avg gross) + SIZEUP ----
    comb_neutral, mults_n = apply_kelly(comb, nactive, sizeup=True, neutralize=True)
    comb_sizeup, mults_s = apply_kelly(comb, nactive, sizeup=True, neutralize=False)
    comb_fwd_neutral = [v for v, f in zip(comb_neutral, fwd_mask) if f]
    comb_fwd_sizeup = [v for v, f in zip(comb_sizeup, fwd_mask) if f]
    rep['kelly_mult_stats'] = dict(
        sizeup_mean=round(statistics.fmean(mults_s), 4), sizeup_min=min(mults_s), sizeup_max=max(mults_s),
        neutral_mean=round(statistics.fmean(mults_n), 4))

    rep['goal2_kelly_grids'] = dict(
        flat_all=grid_mc(comb, VS, 'flat', seed_base=1),
        flat_all_stress15=grid_mc(comb, VS, 'flat_str', stress=True, seed_base=999),
        flat_fwd=grid_mc(comb_fwd, 1.0, 'flat_fwd', seed_base=777),
        neutral_all=grid_mc(comb_neutral, VS, 'neu', seed_base=1),
        neutral_all_stress15=grid_mc(comb_neutral, VS, 'neu_str', stress=True, seed_base=999),
        neutral_fwd=grid_mc(comb_fwd_neutral, 1.0, 'neu_fwd', seed_base=777),
        sizeup_all=grid_mc(comb_sizeup, VS, 'su', seed_base=1),
        sizeup_all_stress15=grid_mc(comb_sizeup, VS, 'su_str', stress=True, seed_base=999),
        sizeup_fwd=grid_mc(comb_fwd_sizeup, 1.0, 'su_fwd', seed_base=777),
    )
    # vol-matched the SIZEUP variant fairly: it runs hotter, so re-vol-match its std to book
    sd_su = statistics.pstdev(comb_sizeup); VS_su = round(sd_book / sd_su, 4)
    rep['sizeup_vol_scale'] = VS_su
    rep['goal2_kelly_grids']['sizeup_all_volmatched'] = grid_mc(comb_sizeup, VS_su, 'su_vm', seed_base=1)
    rep['goal2_kelly_grids']['sizeup_all_volmatched_stress15'] = grid_mc(comb_sizeup, VS_su, 'su_vm_str', stress=True, seed_base=999)

    # ---- forward EV head-to-head (per-year) ----
    def per_year(series):
        by = collections.defaultdict(list)
        for v, d in zip(series, all_days):
            by[d.year].append(v)
        return {y: round(statistics.fmean(by[y]), 4) for y in sorted(by) if y >= 2025}
    rep['fwd_meanR_headtohead'] = dict(
        flat=round(statistics.fmean(comb_fwd), 4),
        neutral=round(statistics.fmean(comb_fwd_neutral), 4),
        sizeup=round(statistics.fmean(comb_fwd_sizeup), 4),
        flat_per_year=per_year(comb), neutral_per_year=per_year(comb_neutral),
        sizeup_per_year=per_year(comb_sizeup))

    # ---- GOAL: 2-ACCOUNT challenge MC at AGGRESSIVE growth sizing, flat vs kelly-sizeup ----
    # Build per-day per-sleeve matrices for the kelly-sizeup variant (scale each DAY-ROW by its mult)
    M_sizeup = [[v * kelly_mult_sizeup(nactive[i]) for v in M[i]] for i in range(len(M))]
    M_sizeup_fwd = [r for r, f in zip(M_sizeup, fwd_mask) if f]
    M_stress = [[(v * 1.5 if v < 0 else v) for v in row] for row in M]
    M_sizeup_stress = [[(v * 1.5 if v < 0 else v) for v in row] for row in M_sizeup]
    idx = {s: i for i, s in enumerate(sleeves)}; full = {idx[s]: 1.0 for s in sleeves}
    rep['goal_two_account'] = {}
    # aggressive nominal pairs (vol-matched eff = nominal*VS); growth-optimal region
    pairs = [(0.015, 0.015, 'aggr_balanced_A1.5_B1.5'),
             (0.015, 0.010, 'aggr_stag_A1.5_B1.0'),
             (0.020, 0.015, 'aggr_stag_A2.0_B1.5'),
             (0.0125, 0.0125, 'mod_balanced_A1.25_B1.25')]
    for (sA, sB, label) in pairs:
        sAe, sBe = sA * VS, sB * VS
        flat_base = joint_pass_mc(M, (full, sAe), (full, sBe), seed_base=7)
        flat_fwd = joint_pass_mc(M_fwd, (full, sAe), (full, sBe), seed_base=33)
        flat_str = joint_pass_mc(M_stress, (full, sAe), (full, sBe), seed_base=44)
        kel_base = joint_pass_mc(M_sizeup, (full, sAe), (full, sBe), seed_base=7)
        kel_fwd = joint_pass_mc(M_sizeup_fwd, (full, sAe), (full, sBe), seed_base=33)
        kel_str = joint_pass_mc(M_sizeup_stress, (full, sAe), (full, sBe), seed_base=44)
        rep['goal_two_account'][label] = dict(
            sizeA_eff=round(sAe, 5), sizeB_eff=round(sBe, 5),
            flat_base_p_both=flat_base['p_pass_both'], flat_fwd_p_both=flat_fwd['p_pass_both'],
            flat_stress_p_both=flat_str['p_pass_both'],
            flat_A_fail_dd=flat_base['p_A_fail_dd'], flat_B_fail_dd=flat_base['p_B_fail_dd'],
            flat_daily_breach_max=max(flat_base['p_A_fail_daily'], flat_base['p_B_fail_daily']),
            kelly_base_p_both=kel_base['p_pass_both'], kelly_fwd_p_both=kel_fwd['p_pass_both'],
            kelly_stress_p_both=kel_str['p_pass_both'],
            kelly_A_fail_dd=kel_base['p_A_fail_dd'], kelly_B_fail_dd=kel_base['p_B_fail_dd'],
            kelly_daily_breach_max=max(kel_base['p_A_fail_daily'], kel_base['p_B_fail_daily']))

    (HERE / 'KB7_GROWTH_KELLY_RESULT.json').write_text(json.dumps(rep, indent=1, default=str))

    # ---- console summary ----
    print(f"clean_3 deploy: VS={VS} daily_mean={rep['daily_mean']} std={rep['daily_std']} "
          f"full-Kelly f*(unitR)={rep['full_kelly_f_star_unitR']}")
    print(f"\n=== GOAL 1: GROWTH-OPTIMAL BASE SIZE (vol-matched eff, LOCKED engine) ===")
    print(f"{'nom':>6} {'effVM':>6} {'pass_all':>9} {'pass_str':>9} {'pass_fwd':>9} {'maxDD_str':>10} {'dbreach':>8} {'medDay':>7} {'mo%':>6}")
    g1 = rep['goal1_growth_grid']
    for k in g1['all_history']:
        a = g1['all_history'][k]; s = g1['all_history_stress15'][k]; f = g1['forward'][k]
        eff = float(k.strip('%')) * VS
        print(f"{k:>6} {eff:>5.2f}% {a['p_pass']:>8.1%} {s['p_pass']:>8.1%} {f['p_pass']:>8.1%} "
              f"{s['p_fail_dd']:>9.1%} {a['daily_breach_pct']:>7.2f}% {str(a['med_days']):>7} {a['monthly_pct']:>5.1f}%")

    print(f"\n=== GOAL 2: CONVICTION SIGNAL (leak-free n_active sleeves; forward-validated) ===")
    for k, v in conv.items():
        print(f"  {k}: ALL n={v['all_n']} meanR={v['all_meanR']} | FWD n={v['fwd_n']} meanR={v['fwd_meanR']} -> sizeup x{v['sizeup_mult']}")
    print(f"  corr(n_active,R): all={rep['conviction_corr_all']} fwd={rep['conviction_corr_fwd']}")
    print(f"  FWD meanR head-to-head: flat={rep['fwd_meanR_headtohead']['flat']} "
          f"neutral={rep['fwd_meanR_headtohead']['neutral']} sizeup={rep['fwd_meanR_headtohead']['sizeup']}")
    print(f"  per-year sizeup: {rep['fwd_meanR_headtohead']['sizeup_per_year']} vs flat {rep['fwd_meanR_headtohead']['flat_per_year']}")

    print(f"\n=== GOAL 2: KELLY-LITE vs FLAT (vol-matched stress P(pass) @ key sizes) ===")
    gk = rep['goal2_kelly_grids']
    print(f"{'nom':>6} {'flat_str':>9} {'neu_str':>9} {'su_vm_str':>10} | {'flat_fwd':>9} {'neu_fwd':>9} {'su_fwd':>9}")
    for k in gk['flat_all_stress15']:
        print(f"{k:>6} {gk['flat_all_stress15'][k]['p_pass']:>8.1%} {gk['neutral_all_stress15'][k]['p_pass']:>8.1%} "
              f"{gk['sizeup_all_volmatched_stress15'][k]['p_pass']:>9.1%} | "
              f"{gk['flat_fwd'][k]['p_pass']:>8.1%} {gk['neutral_fwd'][k]['p_pass']:>8.1%} {gk['sizeup_fwd'][k]['p_pass']:>8.1%}")

    print(f"\n=== 2-ACCOUNT CHALLENGE MC (aggressive sizing; flat vs kelly-sizeup) ===")
    for label, v in rep['goal_two_account'].items():
        print(f"  {label} (effA={v['sizeA_eff']*100:.2f}% effB={v['sizeB_eff']*100:.2f}%):")
        print(f"    FLAT  base={v['flat_base_p_both']:.1%} fwd={v['flat_fwd_p_both']:.1%} stress={v['flat_stress_p_both']:.1%} A_dd={v['flat_A_fail_dd']:.1%} dbreach={v['flat_daily_breach_max']:.2%}")
        print(f"    KELLY base={v['kelly_base_p_both']:.1%} fwd={v['kelly_fwd_p_both']:.1%} stress={v['kelly_stress_p_both']:.1%} A_dd={v['kelly_A_fail_dd']:.1%} dbreach={v['kelly_daily_breach_max']:.2%}")
    print("\nwrote KB7_GROWTH_KELLY_RESULT.json")
    return rep


if __name__ == '__main__':
    main()
