"""INTEG_W7_final_book.py — WAVE-7 (UNLEASH) FINAL INTEGRATED DEPLOY BOOK + growth-optimal MC.

THE FINAL INTEGRATOR. Folds EVERY Wave-7 UNLEASH track result into ONE deploy book and re-runs the
LOCKED W2 challenge-pass / max-DD-fail / 1.5x+2.0x stress / 2-account MC across the growth-optimal
aggression dial (1.25 / 1.50 / 2.00 % nominal). Objective: MAX GROWTH-RATE s.t. FTMO (5% daily,
10% maxDD) at an acceptable P(maxDD breach) — NOT minimal size.

WHAT EACH TRACK CONTRIBUTES TO THE FINAL BOOK (with the verdict that decided it):
  T1  Un-cap winners + extend runner horizon ......... NULL CHANGE. The winsor[-1.3,+5] is dead
      weight (binds 0/~12k trades; stop=-1R) and the real cap is the fixed TARGET. Lifting targets
      recovers per-trade EV on right-skewed sleeves but is NET NEGATIVE at the vol-matched book MC
      (flat growth, lower Sharpe, higher maxDD tail, SLOWER days-to-pass). => keep winsor+targets.
  T2  Tick-true execution ............................ ONE BOOK CHANGE: DROP HEATOIL+NATGAS from
      energy_agri (real tick spread 0.28-0.34R vs 0.037R map; modeled EV evaporates on real fills).
      Same real-fill energy EV (+0.349 -> +0.350R), lower tail. Adopt small tick upgrades for
      metals (+0.019/-0.005R) and JPY (+0.018R) too. Per-symbol erosion haircut applied to the
      locked deploy rows. (DASH-drop is a conditional refinement; crypto tick ledger not yet
      materialized -> not applied here, flagged.)
  T3  Growth-optimal + Kelly-lite sizing ............. THE GROWTH LEVER. Base 1.50% nominal
      (~1.42% eff vol-matched) is the growth-optimal knee; confidence-proportional Kelly-lite
      (handset bins {0.85,1.10,1.60} on leak-free day-level n_active) is a forward-clean RESHAPE
      that nearly halves the binding 1.5x-stress maxDD-fail at EQUAL vol. Applied here.
  T4  Reinstate dropped sleeves ..................... NULL CHANGE. Under a hard maxDD cap growth is
      variance-bounded; every dropped stream (leadlag_core, subh4_ll_fx, IDB) is sub-book-Sharpe
      and a growth DRAG at iso-risk-of-ruin. Book of record stays the 11-sleeve clean_3.
  T5  Audit static/conservative assumptions ......... NULL DEPLOY CHANGE on the cascade book
      (maxbars/winsor/cost-map all confirmed optimal/inert at book level; maxbars is a LIVE-PACKAGE
      H4-fallback fix only). sqrt-N same-day pooling already in build_matrix.
  T6  Confluence-Kelly router ........................ SIZE-UP OVERLAY (default-off, already wired
      in ultimate_book_live_package). Strict-Pareto matched-ruin speed on the sub_xvol_pullback
      sleeve; book-level lift is diluted (sleeve is 1/11). Documented; not folded as the base MC
      change (the verdict-gate change is sizing + the tick drop).

NET FINAL = clean_3 (11 sleeves) with HEATOIL+NATGAS dropped + tick erosion + Kelly-lite handset
sizing, sized at the growth-optimal dial. The verdict book changes on the VOL-MATCHED challenge-pass
+ maxDD-fail MC, per-year + forward holdout, NOT per-trade EV alone.

Everything routes through the LOCKED engine: INTEG_portfolio_build_w2.mc_series / joint_pass_mc
(N=20000, FTMO 8%/5%/10%, BLOCK=5, whole-cross-sectional-day block-bootstrap). No lookahead
(conviction = same-day n_active, known at decision time; tick erosion forward-measured). Real cost,
leak-free labelers upstream, per-trade R winsorized [-1.3,+5].
"""
from __future__ import annotations
import sys, json, statistics, collections
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))

import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3
import KB7_growth_kelly_sizing as K        # build_deploy_matrix, conviction_count, KELLY_* (locked)
import KB7_tick_mc as TICK                  # tick_erosion(), restate_rows(), energy_daily()

mc_series = W2.mc_series
joint_pass_mc = W2.joint_pass_mc
DAILY = W2.DAILY

# aggression dial (nominal %). vol-matched eff = nominal * VS. 0.75 is the conservative comparator.
DIAL = (0.0075, 0.010, 0.0125, 0.015, 0.0175, 0.020)
KEY = 0.015                                  # growth-optimal base for focused checks
BASELINE_CONSERVATIVE = 0.0075               # the prior fear-distilled deploy size


def stress(series, factor):
    return [(v * factor if v < 0 else v) for v in series]


# --------------------------------------------------------------------------------------------------
# 1. REBUILD the deploy matrix the LOCKED way, then apply the T2 tick erosion (drop HEATOIL+NATGAS)
#    to the energy_agri COLUMN only, exactly as KB7_tick_mc does.
# --------------------------------------------------------------------------------------------------
def build_final_matrix():
    """Return (all_days, sleeves, M_final, M_tickonly, sd_book, ero).
    M_tickonly = clean_3 matrix with the energy column tick-restated (HEATOIL+NATGAS dropped) and
    metals/JPY tiny tick upgrades folded; this is the FLAT final book before Kelly sizing.
    Built so column structure is preserved for the 2-account joint MC."""
    all_days, sleeves, M, sd_book = K.build_deploy_matrix()
    eidx = sleeves.index('energy_agri')

    # tick erosion per symbol (T2): mean(tick_real - modeled) over covered trades
    ero = TICK.tick_erosion()

    # rebuild the energy column with the tick restatement (drop HEATOIL+NATGAS) and the metals/JPY
    # tick upgrades, using the SAME locked cached rows the deploy book was built from.
    streams_w3 = W3.W2.build_matrix  # noqa: F841 (parity ref)
    import pickle
    sw3 = pickle.load(open(HERE / 'INTEG_W3_streams_cache.pkl', 'rb'))
    ENERGY_CONF = W3.SLEEVE_CONF['energy_agri']

    # energy: drop HEATOIL+NATGAS + per-symbol erosion -> new per-day conf-weighted contribution
    e_tick_drop = TICK.energy_daily(
        TICK.restate_rows(sw3['energy_agri'], ero, drop={'HEATOIL_c', 'NATGAS_cash'}), ENERGY_CONF)

    # metals column tiny tick upgrades (XAU +0.019, XAG -0.005) on metals_core/softband/ob_micro
    metal_sleeves = {'metals_core': W3.SLEEVE_CONF['metals_core'],
                     'metals_softband': W3.SLEEVE_CONF['metals_softband'],
                     'metals_ob_micro': W3.SLEEVE_CONF['metals_ob_micro']}
    metal_tick = {ms: TICK.energy_daily(TICK.restate_rows(sw3[ms], ero), cf)
                  for ms, cf in metal_sleeves.items()}
    # JPY tick upgrade (USDJPY +0.018) on fx_jpy / fx_jpy_ny
    jpy_sleeves = {'fx_jpy': W3.SLEEVE_CONF['fx_jpy'], 'fx_jpy_ny': W3.SLEEVE_CONF['fx_jpy_ny']}
    jpy_tick = {js: TICK.energy_daily(TICK.restate_rows(sw3[js], ero), cf)
                for js, cf in jpy_sleeves.items()}

    sidx = {s: i for i, s in enumerate(sleeves)}
    M_tick = [row[:] for row in M]
    for di, day in enumerate(all_days):
        M_tick[di][eidx] = e_tick_drop.get(day, 0.0)
        for ms, col in metal_tick.items():
            M_tick[di][sidx[ms]] = col.get(day, 0.0)
        for js, col in jpy_tick.items():
            M_tick[di][sidx[js]] = col.get(day, 0.0)
    return all_days, sleeves, M, M_tick, sd_book, ero


# --------------------------------------------------------------------------------------------------
# 2. Kelly-lite handset conviction tilt (T3), leak-free day-level n_active
# --------------------------------------------------------------------------------------------------
HANDSET = dict(zip(K.KELLY_BINS, K.KELLY_SIZEUP))   # {(1,1):0.85,(2,3):1.10,(4,99):1.60}


def kelly_mult(na):
    for (lo, hi), m in HANDSET.items():
        if lo <= na <= hi:
            return min(m, K.KELLY_CAP)
    return 1.0


def apply_kelly_matrix(M, nactive):
    return [[v * kelly_mult(nactive[i]) for v in M[i]] for i in range(len(M))]


# --------------------------------------------------------------------------------------------------
# 3. MC grids
# --------------------------------------------------------------------------------------------------
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
            monthly_pct=round(mu * r * scale * 21 * 100, 3),
            dollars_per_100k_monthly=round(mu * r * scale * 21 * 100000, 0))
    return out


def main():
    print("=== WAVE-7 FINAL INTEGRATED BOOK ===")
    all_days, sleeves, M_base, M_tick, sd_book, ero = build_final_matrix()
    fwd_mask = [d.year >= 2025 for d in all_days]

    comb_base = [sum(r) for r in M_base]            # clean_3 as-deployed (W5 baseline)
    comb_tick = [sum(r) for r in M_tick]            # + tick drop-HN + metals/JPY tick upgrades
    nactive = [K.conviction_count(r) for r in M_tick]
    M_final = apply_kelly_matrix(M_tick, nactive)   # + Kelly-lite handset
    comb_final = [sum(r) for r in M_final]

    sd_base = statistics.pstdev(comb_base)
    sd_tick = statistics.pstdev(comb_tick)
    sd_final = statistics.pstdev(comb_final)
    VS_base = round(sd_book / sd_base, 4)
    VS_tick = round(sd_book / sd_tick, 4)
    VS_final = round(sd_book / sd_final, 4)         # Kelly runs hotter -> smaller vol_scale (equal vol)

    comb_base_fwd = [v for v, f in zip(comb_base, fwd_mask) if f]
    comb_tick_fwd = [v for v, f in zip(comb_tick, fwd_mask) if f]
    comb_final_fwd = [v for v, f in zip(comb_final, fwd_mask) if f]

    rep = dict(
        wave=7, book='clean_3_W7_final',
        sleeves=sleeves, n_sleeves=len(sleeves),
        tick_erosion_applied={s: round(ero.get(s, 0.0), 4) for s in sorted(ero)},
        dropped_symbols=['HEATOIL_c', 'NATGAS_cash'],
        kelly_handset_bins={f"{lo}_{hi}": m for (lo, hi), m in HANDSET.items()},
        sd_book=round(sd_book, 5),
        variant_daily=dict(
            base=dict(mean=round(statistics.fmean(comb_base), 5), std=round(sd_base, 5), vs=VS_base,
                      mean_fwd=round(statistics.fmean(comb_base_fwd), 5)),
            tick=dict(mean=round(statistics.fmean(comb_tick), 5), std=round(sd_tick, 5), vs=VS_tick,
                      mean_fwd=round(statistics.fmean(comb_tick_fwd), 5)),
            final=dict(mean=round(statistics.fmean(comb_final), 5), std=round(sd_final, 5), vs=VS_final,
                       mean_fwd=round(statistics.fmean(comb_final_fwd), 5)),
        ),
        n_days=len(all_days), n_days_fwd=sum(fwd_mask),
    )
    print(f"days={len(all_days)} fwd={sum(fwd_mask)}  sd_book={sd_book:.5f}")
    print(f"BASE  mean={statistics.fmean(comb_base):.5f} std={sd_base:.5f} VS={VS_base}")
    print(f"TICK  mean={statistics.fmean(comb_tick):.5f} std={sd_tick:.5f} VS={VS_tick}")
    print(f"FINAL mean={statistics.fmean(comb_final):.5f} std={sd_final:.5f} VS={VS_final} (Kelly)")

    # ---- challenge-pass MC across the aggression dial (vol-matched), all 3 variants ----
    rep['mc_volmatched_all'] = dict(
        base=grid(comb_base, VS_base, 1.0, seed_base=1),
        tick=grid(comb_tick, VS_tick, 1.0, seed_base=1),
        final=grid(comb_final, VS_final, 1.0, seed_base=1),
    )
    rep['mc_volmatched_stress15'] = dict(
        base=grid(comb_base, VS_base, 1.5, seed_base=999),
        tick=grid(comb_tick, VS_tick, 1.5, seed_base=999),
        final=grid(comb_final, VS_final, 1.5, seed_base=999),
    )
    rep['mc_volmatched_stress20'] = dict(
        base=grid(comb_base, VS_base, 2.0, seed_base=2000),
        tick=grid(comb_tick, VS_tick, 2.0, seed_base=2000),
        final=grid(comb_final, VS_final, 2.0, seed_base=2000),
    )
    # forward-only reported at NOMINAL (recent regime, not vol-matched against full history)
    rep['mc_forward'] = dict(
        base=grid(comb_base_fwd, 1.0, 1.0, seed_base=777),
        tick=grid(comb_tick_fwd, 1.0, 1.0, seed_base=777),
        final=grid(comb_final_fwd, 1.0, 1.0, seed_base=777),
    )

    # ---- per-year stress maxDD-fail (no single-regime hiding) on the FINAL book @KEY ----
    rep['per_year_stress15_final'] = {}
    for yr in (2025, 2026):
        sel = [v for v, d in zip(comb_final, all_days) if d.year == yr]
        if len(sel) < 30:
            rep['per_year_stress15_final'][yr] = dict(n=len(sel), note='thin'); continue
        res = mc_series(stress(sel, 1.5), KEY * VS_final, seed_base=2025 + yr)
        rep['per_year_stress15_final'][yr] = dict(
            n=len(sel), p_pass=round(res['p_pass'], 4), p_fail_dd=round(res['p_fail_dd'], 4),
            p_fail_daily=round(res['p_fail_daily'], 4))

    # ---- 2-account joint MC at the aggression dial (FINAL book = tick+Kelly columns) ----
    idx = {s: i for i, s in enumerate(sleeves)}
    full = {idx[s]: 1.0 for s in sleeves}
    M_final_str = [[(v * 1.5 if v < 0 else v) for v in row] for row in M_final]
    M_final_fwd = [r for r, f in zip(M_final, fwd_mask) if f]
    rep['two_account_final'] = {}
    pairs = [(0.0125, 0.0125, 'balanced_1.25_1.25'),
             (0.015, 0.015, 'balanced_1.50_1.50'),
             (0.0175, 0.0175, 'balanced_1.75_1.75'),
             (0.020, 0.015, 'staggered_2.00_1.50'),
             (0.0075, 0.0075, 'conservative_0.75_0.75')]
    for (sA, sB, label) in pairs:
        sAe, sBe = sA * VS_final, sB * VS_final
        base = joint_pass_mc(M_final, (full, sAe), (full, sBe), seed_base=7)
        fwd = joint_pass_mc(M_final_fwd, (full, sAe), (full, sBe), seed_base=33)
        strs = joint_pass_mc(M_final_str, (full, sAe), (full, sBe), seed_base=44)
        rep['two_account_final'][label] = dict(
            sizeA_nominal=sA, sizeB_nominal=sB, sizeA_eff=round(sAe, 5), sizeB_eff=round(sBe, 5),
            base_p_both=round(base['p_pass_both'], 4), fwd_p_both=round(fwd['p_pass_both'], 4),
            stress15_p_both=round(strs['p_pass_both'], 4),
            base_A_fail_dd=round(base['p_A_fail_dd'], 4),
            daily_breach_max=round(max(base['p_A_fail_daily'], base['p_B_fail_daily']), 4))

    # ---- per-sleeve contribution (conf-wtd unit-R total, FINAL book columns) ----
    contrib = {s: sum(M_final[d][i] for d in range(len(M_final))) for i, s in enumerate(sleeves)}
    tot = sum(contrib.values())
    rep['sleeve_contribution_final'] = {}
    for s in sorted(sleeves, key=lambda k: -contrib[k]):
        rep['sleeve_contribution_final'][s] = dict(
            sum_conf_wtd_unitR=round(contrib[s], 3),
            share_pct=round(100 * contrib[s] / tot, 1) if tot else 0.0)

    # ---- TOTAL LIFT vs conservative 0.75% clean_3 (what fear was costing) ----
    base_075 = rep['mc_volmatched_all']['base']['0.75%']
    final_150 = rep['mc_volmatched_all']['final']['1.50%']
    final_125 = rep['mc_volmatched_all']['final']['1.25%']
    final_200 = rep['mc_volmatched_all']['final']['2.00%']
    rep['lift_vs_conservative_0p75'] = dict(
        conservative_base_0p75=dict(
            p_pass=base_075['p_pass'], p_fail_dd=base_075['p_fail_dd'],
            med_days=base_075['med_days'], monthly_pct=base_075['monthly_pct']),
        final_1p25=dict(p_pass=final_125['p_pass'], p_fail_dd=final_125['p_fail_dd'],
                        med_days=final_125['med_days'], monthly_pct=final_125['monthly_pct']),
        final_1p50=dict(p_pass=final_150['p_pass'], p_fail_dd=final_150['p_fail_dd'],
                        med_days=final_150['med_days'], monthly_pct=final_150['monthly_pct']),
        final_2p00=dict(p_pass=final_200['p_pass'], p_fail_dd=final_200['p_fail_dd'],
                        med_days=final_200['med_days'], monthly_pct=final_200['monthly_pct']),
        speedup_days_1p50=(round(base_075['med_days'] / final_150['med_days'], 2)
                           if final_150['med_days'] else None),
        monthly_multiple_1p50=(round(final_150['monthly_pct'] / base_075['monthly_pct'], 2)
                               if base_075['monthly_pct'] else None),
    )

    (HERE / 'INTEG_W7_FINAL_RESULT.json').write_text(json.dumps(rep, indent=1, default=str))

    # ---- console ----
    print(f"\n=== CHALLENGE-PASS MC (vol-matched, FINAL book) across the aggression dial ===")
    print(f"{'nom':>7} {'eff':>6} {'P(pass)':>9} {'P(maxDD)':>9} {'str15 P':>8} {'str15 DD':>9} "
          f"{'str20 DD':>9} {'dbreach':>8} {'medDay':>7} {'mo%':>6} {'$/100k/mo':>10}")
    for k in rep['mc_volmatched_all']['final']:
        a = rep['mc_volmatched_all']['final'][k]
        s15 = rep['mc_volmatched_stress15']['final'][k]
        s20 = rep['mc_volmatched_stress20']['final'][k]
        eff = float(k.strip('%')) * VS_final
        print(f"{k:>7} {eff:>5.2f}% {a['p_pass']:>8.2%} {a['p_fail_dd']:>8.2%} {s15['p_pass']:>7.1%} "
              f"{s15['p_fail_dd']:>8.2%} {s20['p_fail_dd']:>8.2%} {a['daily_breach_pct']:>7.2f}% "
              f"{str(a['med_days']):>7} {a['monthly_pct']:>5.2f}% {a['dollars_per_100k_monthly']:>10.0f}")

    print(f"\n=== per-year 1.5x-stress maxDD-fail (FINAL @1.50%) ===")
    for yr, v in rep['per_year_stress15_final'].items():
        print(f"  {yr}: " + (v.get('note') or
              f"P(pass)={v['p_pass']:.1%} maxDD={v['p_fail_dd']:.1%} dbreach={v['p_fail_daily']:.1%} (n{v['n']})"))

    print(f"\n=== 2-ACCOUNT (FINAL book) ===")
    for label, v in rep['two_account_final'].items():
        print(f"  {label} (effA={v['sizeA_eff']*100:.2f}% effB={v['sizeB_eff']*100:.2f}%): "
              f"P(both)={v['base_p_both']:.2%} fwd={v['fwd_p_both']:.2%} "
              f"stress={v['stress15_p_both']:.2%} dbreach={v['daily_breach_max']:.2%}")

    print(f"\n=== TOTAL LIFT vs conservative 0.75% clean_3 ===")
    L = rep['lift_vs_conservative_0p75']
    print(f"  0.75% base : pass={L['conservative_base_0p75']['p_pass']:.2%} "
          f"maxDD={L['conservative_base_0p75']['p_fail_dd']:.2%} "
          f"days={L['conservative_base_0p75']['med_days']} mo={L['conservative_base_0p75']['monthly_pct']:.2f}%")
    print(f"  FINAL 1.50%: pass={L['final_1p50']['p_pass']:.2%} maxDD={L['final_1p50']['p_fail_dd']:.2%} "
          f"days={L['final_1p50']['med_days']} mo={L['final_1p50']['monthly_pct']:.2f}%  "
          f"=> {L['speedup_days_1p50']}x faster, {L['monthly_multiple_1p50']}x monthly")

    print("\nwrote INTEG_W7_FINAL_RESULT.json")
    return rep


if __name__ == '__main__':
    main()
