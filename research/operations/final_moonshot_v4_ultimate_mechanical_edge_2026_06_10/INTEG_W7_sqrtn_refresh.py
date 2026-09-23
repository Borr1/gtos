"""INTEG_W7_sqrtn_refresh.py — WAVE-7 FINAL book WITH sqrt-N within-sleeve same-day pooling folded.

DEFAULT-OFF REFRESH integrator (new artifact; does NOT touch the locked INTEG_W7_FINAL_RESULT.json).
The locked W7 final integrator (INTEG_W7_final_book.py) built its per-day x per-sleeve matrix with
MEAN within-sleeve same-day pooling (INTEG_portfolio_build_w2.build_matrix L225 `sum(rs)/len(rs)` for
the 8 core sleeves; KB7_growth_kelly_sizing.candidate_daily `sum(v)/len(v)` for the 3 clean_3 sleeves)
— i.e. it treats same-day same-sleeve trades as perfectly correlated (corr=1). KB7_stale_audit.md (b)
proved that is the real growth drag and that the FAIR within-sleeve credit is PARTIAL (effective
N = sqrt(n), not 1), a validated +1.9..+2.2pp vol-matched 1.5x-stress win at matched risk / ~27%
faster speed-to-target at fixed nominal, with daily-breach still 0% to 2% and worst-day inside -5%.

This script folds EXACTLY that one change — within-sleeve same-day pooling sum/len -> sum/sqrt(n),
CROSS-sleeve diversification untouched — on top of the SAME W7 final book (HEATOIL+NATGAS dropped +
per-symbol tick erosion + Kelly-lite handset sizing) and re-runs the SAME LOCKED W2 MC
(INTEG_portfolio_build_w2.mc_series, N=20000, FTMO 8%/5%/10%, BLOCK=5). It reports:
  - the locked-mean W7 final headline (reproduced from INTEG_W7_final_book) AS the parity baseline, and
  - the sqrt-N refreshed final headline,
at the owner dial (1.25% / 1.50% / 2.00%) so the deploy decision sees the free win quantified.

No lookahead (Kelly = same-day n_active; tick erosion forward-measured; pooling is a same-day
correlation-credit convention, not a future-peek). Real cost; leak-free labelers upstream; winsor
[-1.3,+5] inherited. Engine + book are byte-for-byte the locked W7 path apart from the pool function.
"""
from __future__ import annotations
import sys, json, statistics, math, pickle, collections
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))

import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3
import KB7_growth_kelly_sizing as K
import KB7_tick_mc as TICK
import INTEG_W7_final_book as W7

mc_series = W2.mc_series
DAILY = W2.DAILY
DIAL = (0.0075, 0.010, 0.0125, 0.015, 0.0175, 0.020)
KEY = 0.015


def stress(series, factor):
    return [(v * factor if v < 0 else v) for v in series]


# --------------------------------------------------------------------------------------------------
# sqrt-N within-sleeve same-day pooling (the ONE change vs the locked W7 mean-pooled matrix).
# --------------------------------------------------------------------------------------------------
def pool_day(rs, sqrt_n):
    """Within-sleeve same-day pool of per-trade R: mean (sum/len) or sqrt-N (sum/sqrt(n))."""
    n = len(rs)
    if n == 0:
        return 0.0
    if n == 1:
        return rs[0]
    s = sum(rs)
    return s / math.sqrt(n) if sqrt_n else s / n


def build_core_daily(streams, sqrt_n):
    """Reproduce INTEG_portfolio_build_w2.build_matrix per-sleeve daily contributions, but with the
    chosen within-sleeve same-day pooling. Returns {sleeve: {day: conf_wtd_contribution}}."""
    byday = collections.defaultdict(lambda: collections.defaultdict(list))
    for name, rows in streams.items():
        for r in rows:
            byday[r['date']][name].append(r['R_sized'])
    out = {name: {} for name in streams}
    for day, sl in byday.items():
        for name, rs in sl.items():
            out[name][day] = pool_day(rs, sqrt_n) * W3.SLEEVE_CONF[name]
    return out


def candidate_daily(rows, sqrt_n):
    by = collections.defaultdict(list)
    for r in rows:
        by[r['date']].append(r['R'])
    return {d: pool_day(v, sqrt_n) for d, v in by.items()}


def build_final_matrix(sqrt_n):
    """Build the W7 FINAL book matrix (tick drop-HN + metals/JPY tick upgrades + Kelly applied later)
    with the chosen within-sleeve same-day pooling. Mirrors INTEG_W7_final_book.build_final_matrix but
    re-pools every sleeve column (core via build_core_daily, clean_3 via candidate_daily) so sqrt_n
    folds uniformly. Energy is then tick-restated (drop HEATOIL+NATGAS) using the SAME pool."""
    sw3 = pickle.load(open(HERE / 'INTEG_W3_streams_cache.pkl', 'rb'))
    new_streams = pickle.load(open(HERE / 'INTEG_W5_new_streams_cache.pkl', 'rb'))
    ero = TICK.tick_erosion()

    core_daily = build_core_daily(sw3, sqrt_n)
    book_sleeves = list(W3.SLEEVES)

    # energy: drop HEATOIL+NATGAS + per-symbol tick erosion, pooled with the chosen convention.
    ENERGY_CONF = W3.SLEEVE_CONF['energy_agri']
    e_rows = TICK.restate_rows(sw3['energy_agri'], ero, drop={'HEATOIL_c', 'NATGAS_cash'})
    e_by = collections.defaultdict(list)
    for r in e_rows:
        e_by[r['date']].append(r['R_sized'])
    e_tick = {d: pool_day(v, sqrt_n) * ENERGY_CONF for d, v in e_by.items()}

    # metals + JPY tiny tick upgrades, same pooling.
    def tick_col(sleeve):
        rows = TICK.restate_rows(sw3[sleeve], ero)
        by = collections.defaultdict(list)
        for r in rows:
            by[r['date']].append(r['R_sized'])
        cf = W3.SLEEVE_CONF[sleeve]
        return {d: pool_day(v, sqrt_n) * cf for d, v in by.items()}

    metal_tick = {ms: tick_col(ms) for ms in ('metals_core', 'metals_softband', 'metals_ob_micro')}
    jpy_tick = {js: tick_col(js) for js in ('fx_jpy', 'fx_jpy_ny')}

    # clean_3 additive sleeves.
    nd = {nm: {d: v * cf for d, v in candidate_daily(new_streams[nm], sqrt_n).items()}
          for nm, cf in K.CLEAN3.items()}

    sleeves = book_sleeves + list(K.CLEAN3.keys())
    all_days = sorted(set().union(*[set(core_daily[s]) for s in book_sleeves],
                                  *[set(nd[n]) for n in K.CLEAN3]))

    def col_for(sleeve, day):
        if sleeve == 'energy_agri':
            return e_tick.get(day, 0.0)
        if sleeve in metal_tick:
            return metal_tick[sleeve].get(day, 0.0)
        if sleeve in jpy_tick:
            return jpy_tick[sleeve].get(day, 0.0)
        if sleeve in nd:
            return nd[sleeve].get(day, 0.0)
        return core_daily[sleeve].get(day, 0.0)

    M = [[col_for(s, day) for s in sleeves] for day in all_days]
    # sd_book parity reference (book-only daily std, mean-pooled, like the locked engine).
    _, _, _, sd_book = K.build_deploy_matrix()
    return all_days, sleeves, M, sd_book, ero


def kelly_matrix(M, sleeves):
    nactive = [K.conviction_count(r) for r in M]
    return [[v * W7.kelly_mult(nactive[i]) for v in M[i]] for i in range(len(M))], nactive


def grid(series, scale, factor=1.0, seed_base=1):
    s = stress(series, factor) if factor != 1.0 else series
    mu = statistics.fmean(series)
    out = {}
    for r in DIAL:
        res = mc_series(s, r * scale, seed_base=seed_base)
        worst = min(s) * r * scale
        breach = sum(1 for v in s if v * r * scale <= -DAILY) / len(s)
        out[f"{r*100:.2f}%"] = dict(
            p_pass=round(res['p_pass'], 5), p_fail_dd=round(res['p_fail_dd'], 5),
            p_fail_daily=round(res['p_fail_daily'], 5), med_days=res['med_days_pass'],
            worst_day_pct=round(worst * 100, 3), daily_breach_pct=round(breach * 100, 3),
            monthly_pct=round(mu * r * scale * 21 * 100, 3))
    return out


def headline(M, sleeves, sd_book, label):
    comb = [sum(r) for r in M]
    Mk, nactive = kelly_matrix(M, sleeves)
    comb_final = [sum(r) for r in Mk]
    sd_final = statistics.pstdev(comb_final)
    VS_final = round(sd_book / sd_final, 4)
    rep = dict(
        label=label, sd_book=round(sd_book, 5),
        final_mean=round(statistics.fmean(comb_final), 5), final_std=round(sd_final, 5),
        VS_final=VS_final,
        mc_volmatched_all=grid(comb_final, VS_final, 1.0, seed_base=1),
        mc_volmatched_stress15=grid(comb_final, VS_final, 1.5, seed_base=999),
        mc_volmatched_stress20=grid(comb_final, VS_final, 2.0, seed_base=2000),
    )
    return rep


def main():
    print("=== WAVE-7 FINAL — sqrt-N within-sleeve pooling REFRESH (vs locked mean) ===")
    # mean-pooled (parity baseline = the locked W7 final path) and sqrt-N refresh.
    d_m, s_m, M_mean, sd_book, ero = build_final_matrix(sqrt_n=False)
    d_s, s_s, M_sqrt, _, _ = build_final_matrix(sqrt_n=True)
    assert s_m == s_s == ['metals_core', 'metals_softband', 'metals_ob_micro', 'crypto',
                          'energy_agri', 'idxrev', 'fx_jpy', 'fx_jpy_ny',
                          'sub_xvol_pullback', 'vp_euidx_pocgrav', 'sub_mid_dn_revert']

    mean_rep = headline(M_mean, s_m, sd_book, 'final_mean_pool_PARITY')
    sqrt_rep = headline(M_sqrt, s_s, sd_book, 'final_sqrtN_pool_REFRESH')

    rep = dict(
        wave=7, book='clean_3_W7_final_sqrtN_refresh',
        sleeves=s_m, n_sleeves=len(s_m),
        dropped_symbols=['HEATOIL_c', 'NATGAS_cash'],
        pooling_change='within-sleeve same-day sum/len -> sum/sqrt(n); cross-sleeve unchanged',
        source='KB7_stale_audit.md (b); locked engine INTEG_portfolio_build_w2.mc_series',
        mean_pool=mean_rep, sqrtn_pool=sqrt_rep,
    )

    # focused owner-dial delta table (1.25 / 1.50 / 2.00)
    rep['owner_dial_delta'] = {}
    for k in ('1.25%', '1.50%', '2.00%'):
        m_all = mean_rep['mc_volmatched_all'][k]; s_all = sqrt_rep['mc_volmatched_all'][k]
        m_s15 = mean_rep['mc_volmatched_stress15'][k]; s_s15 = sqrt_rep['mc_volmatched_stress15'][k]
        rep['owner_dial_delta'][k] = dict(
            mean_p_pass=m_all['p_pass'], sqrtn_p_pass=s_all['p_pass'],
            mean_maxdd=m_all['p_fail_dd'], sqrtn_maxdd=s_all['p_fail_dd'],
            mean_med_days=m_all['med_days'], sqrtn_med_days=s_all['med_days'],
            mean_stress15_pass=m_s15['p_pass'], sqrtn_stress15_pass=s_s15['p_pass'],
            stress15_pass_delta_pp=round((s_s15['p_pass'] - m_s15['p_pass']) * 100, 2),
            days_speedup_pct=(round((m_all['med_days'] - s_all['med_days']) / m_all['med_days'] * 100, 1)
                             if m_all['med_days'] else None),
            daily_breach_pct_sqrtn=s_all['daily_breach_pct'],
            worst_day_pct_sqrtn=s_all['worst_day_pct'])

    (HERE / 'INTEG_W7_SQRTN_REFRESH_RESULT.json').write_text(json.dumps(rep, indent=1, default=str))

    print(f"\nmean-pool  VS_final={mean_rep['VS_final']}  sqrtN VS_final={sqrt_rep['VS_final']}")
    print(f"\n{'dial':>6} | {'meanP':>7} {'sqrtP':>7} | {'meanDD':>7} {'sqrtDD':>7} | "
          f"{'mDays':>5} {'sDays':>5} spd | {'meanS15':>7} {'sqrtS15':>7} (+pp) | dbreach worstDay")
    for k, v in rep['owner_dial_delta'].items():
        print(f"{k:>6} | {v['mean_p_pass']:>7.4f} {v['sqrtn_p_pass']:>7.4f} | "
              f"{v['mean_maxdd']:>7.4f} {v['sqrtn_maxdd']:>7.4f} | "
              f"{v['mean_med_days']:>5} {v['sqrtn_med_days']:>5} {str(v['days_speedup_pct'])+'%':>5} | "
              f"{v['mean_stress15_pass']:>7.4f} {v['sqrtn_stress15_pass']:>7.4f} (+{v['stress15_pass_delta_pp']}pp) | "
              f"{v['daily_breach_pct_sqrtn']:.2f}% {v['worst_day_pct_sqrtn']:.2f}%")
    print("\nwrote INTEG_W7_SQRTN_REFRESH_RESULT.json")
    return rep


if __name__ == '__main__':
    main()
