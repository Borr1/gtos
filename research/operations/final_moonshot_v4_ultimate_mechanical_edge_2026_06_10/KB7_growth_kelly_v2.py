"""KB7 v2 — HARDEN the growth-optimal + confidence-proportional (Kelly-lite) sizing (track KB7).

Builds on KB7_growth_kelly_sizing.py (reproduced bit-for-bit). v2 adds the pieces the UNLEASH brief
demands for an honest aggressive deploy decision, so the recommendation is not resting on a single
stress point or a hand-set multiplier:

  A. PRINCIPLED confidence-proportional multiplier. Instead of 3 hand-set bins, DERIVE the per-bucket
     tilt from the conditional Kelly fraction f*_bucket = mu_bucket / var_bucket, expressed RELATIVE
     to the base f*, then damp it (half-Kelly) for ruin protection and cap it. This is the textbook
     confidence-proportional rule (bet in proportion to edge/variance) — learned from the structure,
     not fitted weights. Compare it head-to-head with the hand-set bins.

  B. PER-YEAR stress maxDD-fail decomposition (no single-regime hiding): run the 1.5x-stress MC on
     each forward year separately so a blended stress number can't mask a bad cell.

  C. DEEP-STRESS / RUIN check: 2.0x left-tail inflation at the recommended size to quantify the
     genuine blow-up tail (P(maxDD) and P(daily)) under a regime far worse than backtest.

  D. BIN-ROBUSTNESS: perturb the conviction bin boundaries and the cap; confirm the recommendation
     (1.5% + Kelly-lite beats flat on stress maxDD-fail at equal vol) is not boundary-fragile.

All MC on the LOCKED W2 engine (mc_series / joint_pass_mc, N=20000, 8%/5%/10%, block=5) at clean_3,
reconstructed via KB7_growth_kelly_sizing.build_deploy_matrix. No lookahead (conviction = count of
sleeves firing that day, known at decision time); forward holdout + per-year; verdict = vol-matched
stress challenge-pass + maxDD-fail, not per-trade EV alone.
"""
import sys, json, statistics, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import KB7_growth_kelly_sizing as K
import INTEG_portfolio_build_w2 as W2

mc_series = W2.mc_series; joint_pass_mc = W2.joint_pass_mc
DAILY = K.DAILY

SIZES = (0.010, 0.0125, 0.015, 0.0175, 0.020, 0.0225, 0.025)
KEY = 0.015  # the recommended base for the focused checks


def stress(series, factor):
    return [(v * factor if v < 0 else v) for v in series]


def grid(series, scale, factor=1.0, seed_base=1):
    s = stress(series, factor) if factor != 1.0 else series
    mu = statistics.fmean(series)
    out = {}
    for r in SIZES:
        res = mc_series(s, r * scale, seed_base=seed_base)
        breach = sum(1 for v in s if v * r * scale <= -DAILY) / len(s)
        out[f"{r*100:.2f}%"] = dict(p_pass=round(res['p_pass'], 4), p_fail_dd=round(res['p_fail_dd'], 4),
                                    p_fail_daily=round(res['p_fail_daily'], 4), med_days=res['med_days_pass'],
                                    daily_breach_pct=round(breach * 100, 3),
                                    monthly_pct=round(mu * r * scale * 21 * 100, 2))
    return out


def main():
    all_days, sleeves, M, sd_book = K.build_deploy_matrix()
    comb = [sum(r) for r in M]
    nactive = [K.conviction_count(r) for r in M]
    fwd_mask = [d.year >= 2025 for d in all_days]
    comb_fwd = [v for v, f in zip(comb, fwd_mask) if f]
    sd = statistics.pstdev(comb); VS = round(sd_book / sd, 4)

    rep = dict(track='KB7_growth_kelly_v2', book='clean_3', vol_scale=VS,
               n_days=len(comb), n_days_fwd=len(comb_fwd),
               daily_mean=round(statistics.fmean(comb), 5), daily_std=round(sd, 5))

    # ---------------------------------------------------------------- A. PRINCIPLED multiplier
    base_mu = statistics.fmean(comb); base_var = statistics.pvariance(comb); base_f = base_mu / base_var
    bins = K.KELLY_BINS
    principled = {}
    raw_ratio = {}
    for (lo, hi) in bins:
        sel = [comb[i] for i in range(len(comb)) if lo <= nactive[i] <= hi]
        mu = statistics.fmean(sel); var = statistics.pvariance(sel)
        f = mu / var if var > 0 else 0.0
        ratio = f / base_f if base_f else 0.0
        raw_ratio[f"{lo}_{hi}"] = round(ratio, 4)
        principled[(lo, hi)] = ratio
    # half-Kelly damp toward 1.0 (ruin protection): m' = 1 + 0.5*(ratio-1), then cap
    CAP = K.KELLY_CAP
    FLOOR = 0.5
    def damp(ratio, frac=0.5):
        return max(FLOOR, min(CAP, 1.0 + frac * (ratio - 1.0)))
    mult_principled_full = {b: max(FLOOR, min(CAP, principled[b])) for b in bins}
    mult_principled_half = {b: damp(principled[b], 0.5) for b in bins}
    rep['principled_multiplier'] = dict(
        base_kelly_f_star=round(base_f, 4),
        bucket_conditional_f_star=raw_ratio,
        note=("ratio = f*_bucket / f*_base = (mu/var per bucket) / (mu/var base) — the textbook "
              "confidence-proportional tilt. FULL = capped raw ratio; HALF = half-Kelly damp toward "
              "1.0 (standard ruin protection). Handset bins were 0.85/1.10/1.60."),
        full_kelly_mult={f"{lo}_{hi}": round(mult_principled_full[(lo, hi)], 3) for (lo, hi) in bins},
        half_kelly_mult={f"{lo}_{hi}": round(mult_principled_half[(lo, hi)], 3) for (lo, hi) in bins},
        handset_mult={f"{lo}_{hi}": m for (lo, hi), m in zip(bins, K.KELLY_SIZEUP)})

    def mult_of(table, na):
        for (lo, hi), m in table.items():
            if lo <= na <= hi:
                return m
        return 1.0

    def apply(table):
        return [comb[i] * mult_of(table, nactive[i]) for i in range(len(comb))]

    variants = {
        'flat': comb,
        'handset': apply({b: m for b, m in zip(bins, K.KELLY_SIZEUP)}),
        'principled_full': apply(mult_principled_full),
        'principled_half': apply(mult_principled_half),
    }
    # vol-match every sized variant to the book std so comparisons are at EQUAL vol
    rep['variant_vol_scale'] = {}
    rep['equal_vol_stress_grid'] = {}
    rep['equal_vol_base_grid'] = {}
    fwd_means = {}
    for name, ser in variants.items():
        vs = round(sd_book / statistics.pstdev(ser), 4)
        rep['variant_vol_scale'][name] = vs
        rep['equal_vol_stress_grid'][name] = grid(ser, vs, factor=1.5, seed_base=999)
        rep['equal_vol_base_grid'][name] = grid(ser, vs, factor=1.0, seed_base=1)
        ser_fwd = [v for v, f in zip(ser, fwd_mask) if f]
        fwd_means[name] = round(statistics.fmean(ser_fwd), 4)
    rep['fwd_meanR_by_variant'] = fwd_means

    # ---------------------------------------------------------------- B. PER-YEAR stress maxDD-fail
    # at the KEY size, equal-vol, for flat and handset (the documented deploy form)
    rep['per_year_stress_maxdd_fail'] = {}
    for name in ('flat', 'handset', 'principled_half'):
        ser = variants[name]; vs = rep['variant_vol_scale'][name]
        peryr = {}
        for yr in (2025, 2026):
            sel = [v for v, d in zip(ser, all_days) if d.year == yr]
            if len(sel) < 30:
                peryr[yr] = dict(n=len(sel), note='thin'); continue
            res = mc_series(stress(sel, 1.5), KEY * vs, seed_base=2025 + yr)
            peryr[yr] = dict(n=len(sel), p_pass=round(res['p_pass'], 4),
                             p_fail_dd=round(res['p_fail_dd'], 4),
                             p_fail_daily=round(res['p_fail_daily'], 4))
        # also all-history at KEY for reference
        res_all = mc_series(stress(ser, 1.5), KEY * vs, seed_base=999)
        peryr['all'] = dict(n=len(ser), p_pass=round(res_all['p_pass'], 4),
                            p_fail_dd=round(res_all['p_fail_dd'], 4))
        rep['per_year_stress_maxdd_fail'][name] = peryr

    # ---------------------------------------------------------------- C. DEEP-STRESS / RUIN
    rep['deep_stress_ruin'] = {}
    for name in ('flat', 'handset', 'principled_half'):
        ser = variants[name]; vs = rep['variant_vol_scale'][name]
        row = {}
        for factor, lbl in ((1.5, 'stress1.5x'), (2.0, 'stress2.0x'), (2.5, 'stress2.5x')):
            res = mc_series(stress(ser, factor), KEY * vs, seed_base=int(factor * 1000))
            row[lbl] = dict(p_pass=round(res['p_pass'], 4), p_fail_dd=round(res['p_fail_dd'], 4),
                            p_fail_daily=round(res['p_fail_daily'], 4), med_days=res['med_days_pass'])
        rep['deep_stress_ruin'][name] = row

    # ---------------------------------------------------------------- D. BIN-ROBUSTNESS
    # perturb the >=4 boundary to >=3 and >=5, and the cap to 1.5 / 2.0, recompute handset stress @KEY
    rep['bin_robustness'] = {}
    perturb_tables = {
        'baseline_2_3_4': {(1, 1): 0.85, (2, 3): 1.10, (4, 99): 1.60},
        'hi_at_3':        {(1, 1): 0.85, (2, 2): 1.10, (3, 99): 1.60},
        'hi_at_5':        {(1, 1): 0.85, (2, 4): 1.10, (5, 99): 1.60},
        'cap_1.4':        {(1, 1): 0.85, (2, 3): 1.10, (4, 99): 1.40},
        'cap_2.0':        {(1, 1): 0.85, (2, 3): 1.10, (4, 99): 2.00},
        'mild_0.9_1.05_1.3': {(1, 1): 0.90, (2, 3): 1.05, (4, 99): 1.30},
    }
    for lbl, tbl in perturb_tables.items():
        ser = apply(tbl); vs = round(sd_book / statistics.pstdev(ser), 4)
        res = mc_series(stress(ser, 1.5), KEY * vs, seed_base=999)
        res_base = mc_series(ser, KEY * vs, seed_base=1)
        ser_fwd = [v for v, f in zip(ser, fwd_mask) if f]
        rep['bin_robustness'][lbl] = dict(
            vol_scale=vs, stress_maxdd_fail=round(res['p_fail_dd'], 4),
            base_pass=round(res_base['p_pass'], 4), base_med_days=res_base['med_days_pass'],
            fwd_meanR=round(statistics.fmean(ser_fwd), 4))

    # ---------------------------------------------------------------- E. 2-ACCOUNT at recommended (equal-vol handset)
    # use the per-day per-sleeve matrix scaled by the handset multiplier, then vol-matched
    handset_tbl = {b: m for b, m in zip(bins, K.KELLY_SIZEUP)}
    M_hand = [[v * mult_of(handset_tbl, nactive[i]) for v in M[i]] for i in range(len(M))]
    vs_hand = rep['variant_vol_scale']['handset']
    idx = {s: i for i, s in enumerate(sleeves)}; full = {idx[s]: 1.0 for s in sleeves}
    M_hand_str = [[(v * 1.5 if v < 0 else v) for v in row] for row in M_hand]
    M_flat_str = [[(v * 1.5 if v < 0 else v) for v in row] for row in M]
    rep['two_account_equalvol'] = {}
    for (sA, sB, lbl) in [(0.015, 0.015, 'balanced_1.5_1.5'), (0.0175, 0.0175, 'balanced_1.75_1.75'),
                          (0.015, 0.0125, 'stag_1.5_1.25')]:
        # flat at book VS; handset at its own (smaller) vol_scale so EQUAL vol
        fa, fb = sA * VS, sB * VS
        ha, hb = sA * vs_hand, sB * vs_hand
        flat_b = joint_pass_mc(M, (full, fa), (full, fb), seed_base=7)
        flat_s = joint_pass_mc(M_flat_str, (full, fa), (full, fb), seed_base=44)
        kel_b = joint_pass_mc(M_hand, (full, ha), (full, hb), seed_base=7)
        kel_s = joint_pass_mc(M_hand_str, (full, ha), (full, hb), seed_base=44)
        rep['two_account_equalvol'][lbl] = dict(
            flat_eff=round(fa, 5), kelly_eff_base=round(ha, 5),
            flat_base_both=round(flat_b['p_pass_both'], 4), flat_stress_both=round(flat_s['p_pass_both'], 4),
            flat_A_dd=round(flat_b['p_A_fail_dd'], 4), flat_dbreach=round(max(flat_b['p_A_fail_daily'], flat_b['p_B_fail_daily']), 4),
            kelly_base_both=round(kel_b['p_pass_both'], 4), kelly_stress_both=round(kel_s['p_pass_both'], 4),
            kelly_A_dd=round(kel_b['p_A_fail_dd'], 4), kelly_dbreach=round(max(kel_b['p_A_fail_daily'], kel_b['p_B_fail_daily']), 4))

    (HERE / 'KB7_GROWTH_KELLY_V2_RESULT.json').write_text(json.dumps(rep, indent=1, default=str))

    # ---------------------------------------------------------------- console
    print(f"VS={VS} base_kelly_f*={base_f:.4f}")
    print("\n== A. PRINCIPLED vs HANDSET multiplier (per n_active bucket) ==")
    print(f"  conditional f*/base ratio: {raw_ratio}")
    print(f"  FULL-kelly (capped): {rep['principled_multiplier']['full_kelly_mult']}")
    print(f"  HALF-kelly (damped): {rep['principled_multiplier']['half_kelly_mult']}")
    print(f"  HANDSET (deployed):  {rep['principled_multiplier']['handset_mult']}")
    print(f"  fwd meanR: {fwd_means}")
    print("\n== EQUAL-VOL 1.5x-STRESS maxDD-FAIL (lower=better) by size ==")
    print(f"{'nom':>7} {'flat':>8} {'handset':>8} {'pr_full':>8} {'pr_half':>8}")
    for k in rep['equal_vol_stress_grid']['flat']:
        f = rep['equal_vol_stress_grid']['flat'][k]['p_fail_dd']
        h = rep['equal_vol_stress_grid']['handset'][k]['p_fail_dd']
        pf = rep['equal_vol_stress_grid']['principled_full'][k]['p_fail_dd']
        ph = rep['equal_vol_stress_grid']['principled_half'][k]['p_fail_dd']
        print(f"{k:>7} {f:>8.1%} {h:>8.1%} {pf:>8.1%} {ph:>8.1%}")
    print("\n== B. PER-YEAR stress maxDD-fail @1.5% (handset) ==")
    for name, d in rep['per_year_stress_maxdd_fail'].items():
        print(f"  {name}: " + " ".join(f"{y}:dd={v.get('p_fail_dd','?')}(n{v['n']})" for y, v in d.items()))
    print("\n== C. DEEP-STRESS / RUIN @1.5% ==")
    for name, d in rep['deep_stress_ruin'].items():
        print(f"  {name}: " + " ".join(f"{k}:dd={v['p_fail_dd']:.1%},dbr={v['p_fail_daily']:.2%}" for k, v in d.items()))
    print("\n== D. BIN-ROBUSTNESS (stress maxDD-fail @1.5%, equal-vol) ==")
    for lbl, v in rep['bin_robustness'].items():
        print(f"  {lbl}: stress_dd={v['stress_maxdd_fail']:.1%} base_pass={v['base_pass']:.1%} med={v['base_med_days']} fwdR={v['fwd_meanR']}")
    print("\n== E. 2-ACCOUNT (equal-vol, flat vs handset) ==")
    for lbl, v in rep['two_account_equalvol'].items():
        print(f"  {lbl}: FLAT base={v['flat_base_both']:.1%} str={v['flat_stress_both']:.1%} | KELLY base={v['kelly_base_both']:.1%} str={v['kelly_stress_both']:.1%} dbr={v['kelly_dbreach']:.2%}")
    print("\nwrote KB7_GROWTH_KELLY_V2_RESULT.json")
    return rep


if __name__ == '__main__':
    main()
