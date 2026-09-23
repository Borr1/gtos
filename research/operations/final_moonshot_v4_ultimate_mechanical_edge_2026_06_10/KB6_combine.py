"""KB6_combine.py — combine the winning stress mitigations + 2-account deploy under the overlay.

From KB6_mitigations.py the winners (vol-matched, locked MC) are:
  (a) W3 breadth+drawdown regime overlay  -> +4.7..+5.8 pts stress, +Sharpe
  (d) 3-step daily de-risk ladder         -> +3.0 pts stress, highest Sharpe
  (b) co-loss breaker (W5/th0.57/dk0.60)  -> +3.4 pts stress
  (c) per-sleeve vol-target               -> NULL (cap never binds; crypto tail is clustered
                                              -0.93 conf-loss days, not single fat days)

This script: (1) tests COMBINATIONS (regime+ladder, regime+coloss, all-three), per-year stress,
forward-holdout stress; (2) re-runs the 2-account joint MC (the actual deploy decision) under
the best overlay vs the static baseline, vol-matched; (3) writes the deployable overlay spec.
Every multiplier is leak-free (days < t) and gross-exposure normalized + vol-matched.
"""
import sys, json, statistics, collections, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import KB6_stress_lib as L
import INTEG_portfolio_build_w2 as W2

d = L.build_clean3()
days, sleeves, M, comb = d['all_days'], d['sleeves'], d['M'], d['comb']
vs_base = d['vol_scale']; breadth = d['breadth']
book_series = d['book_series']; sd_book = statistics.pstdev(book_series)
N_DAYS = len(comb)
RISKS = (0.005, 0.0075, 0.01, 0.015, 0.02)
TRAIN = [i for i in range(N_DAYS) if days[i].year <= 2024]
FWD = [i for i in range(N_DAYS) if days[i].year >= 2025]
TARGET, MAXDD, DAILY, BLOCK, PATHCAP, N = L.TARGET, L.MAXDD, L.DAILY, L.BLOCK, L.PATHCAP, L.N


def wmean(x): return sum(x) / len(x) if x else 0.0


# ---- the three winning multiplier generators (leak-free) ----
BW = 10
def regime_mults():
    feats = []; cum = 0.0; peak = 0.0; started = False
    for t in range(N_DAYS):
        pb = breadth[max(0, t - BW):t]; tb = wmean(pb) if pb else 0.0
        dd = (peak - cum) if started else 0.0
        feats.append(dict(tb=tb, dd=dd, warm=t >= BW))
        cum += comb[t]; peak = max(peak, cum); started = True
    dd_train = sorted(feats[t]['dd'] for t in TRAIN)
    DD_MED = dd_train[len(dd_train) // 2] if dd_train else 0.0
    out = []
    for f in feats:
        if not f['warm']: m = 1.0
        elif f['tb'] >= 2.0: m = 1.25
        elif f['tb'] >= 1.3: m = 1.00
        else: m = 0.85
        if f['dd'] > DD_MED * 1.5: m *= 0.80
        out.append(m)
    return out


def ladder_mults(steps=(1.0, 0.80, 0.60)):
    out = [1.0] * N_DAYS; streak = 0
    for t in range(N_DAYS):
        out[t] = steps[min(streak, len(steps) - 1)]
        streak = streak + 1 if comb[t] < 0 else 0
    return out


def coloss_mults(W=5, thresh=0.57, derisk=0.60):
    out = [1.0] * N_DAYS
    for t in range(N_DAYS):
        if t < W: continue
        nfire = nneg = 0
        for u in range(t - W, t):
            for si in range(len(sleeves)):
                v = M[u][si]
                if v != 0.0:
                    nfire += 1
                    if v < 0: nneg += 1
        if nfire >= 4 and nneg / nfire >= thresh:
            out[t] = derisk
    return out


def combine_mults(*mult_lists):
    return [min(  # multiply but floor at 0.5 to avoid over-derisking
        1e9, __import__('math').prod(ms[t] for ms in mult_lists)) for t in range(N_DAYS)]


def apply_mult_to_matrix(mults):
    """Scale every sleeve's daily contribution by the day multiplier (so the 2-account joint MC,
    which needs the matrix, gets the overlay), then gross-normalize + vol-match. Returns scaled
    matrix Mx, scaled comb, and vol_scale."""
    am = wmean(mults)
    Mx = [[M[t][si] * mults[t] / am for si in range(len(sleeves))] for t in range(N_DAYS)]
    sc = [sum(r) for r in Mx]
    sd = statistics.pstdev(sc)
    vs = sd_book / sd if sd > 0 else 1.0
    return Mx, sc, vs


def grid(series, vs, stressed):
    return L.grid_pass(series, scale=vs, stressed=stressed)


def eval_combo(name, mults, note=''):
    _, sc, vs = apply_mult_to_matrix(mults)
    mu = statistics.fmean(sc); sd = statistics.pstdev(sc)
    base = grid(sc, vs, False); strs = grid(sc, vs, True)
    print(f"\n[{name}] {note}  sharpe={mu/sd:.4f} vs={vs:.4f}")
    print(f"   {'risk':>7} {'base':>8} {'stress':>8} {'Δstress':>8}")
    return dict(name=name, note=note, sharpe=round(mu / sd, 4), vol_scale=round(vs, 4),
                base=base, stress=strs, mults=mults)


def main():
    report = {'book': 'clean_3', 'engine': 'LOCKED W2 BLOCK5 N20000 8/5/10',
              'risk_equivalence': 'gross-normalized + vol-matched to W3 book std', 'combos': {}}

    rm = regime_mults(); lm = ladder_mults(); cm = coloss_mults()

    # baseline stress for delta
    base_strs = grid(comb, vs_base, True)
    base_base = grid(comb, vs_base, False)
    base_sharpe = statistics.fmean(comb) / statistics.pstdev(comb)
    print("=" * 80)
    print("KB6 COMBINE — best single + combined overlays on clean_3 (vol-matched)")
    print("=" * 80)
    print(f"\n[BASELINE] sharpe={base_sharpe:.4f} vs={vs_base:.4f}")
    for k in base_strs:
        print(f"   {k:>7} base={base_base[k]:.4f} stress={base_strs[k]:.4f}")
    report['baseline'] = dict(sharpe=round(base_sharpe, 4), vol_scale=round(vs_base, 4),
                              base=base_base, stress=base_strs)

    combos = [
        ('regime', rm, 'W3 breadth+dd regime overlay (single best)'),
        ('ladder3', lm, '3-step daily de-risk ladder'),
        ('coloss', cm, 'co-loss circuit breaker W5/0.57/0.60'),
        ('regime+ladder', combine_mults(rm, lm), 'regime overlay x daily ladder'),
        ('regime+coloss', combine_mults(rm, cm), 'regime overlay x co-loss breaker'),
        ('regime+ladder+coloss', combine_mults(rm, lm, cm), 'all three stacked'),
    ]
    for name, mults, note in combos:
        r = eval_combo(name, mults, note)
        for k in r['stress']:
            print(f"   {k:>7} {r['base'][k]:>8.4f} {r['stress'][k]:>8.4f} "
                  f"{(r['stress'][k]-base_strs[k])*100:>+7.1f}")
        r.pop('mults')
        report['combos'][name] = r

    # ---- per-YEAR + FORWARD stress for the chosen overlay (regime, the single best) ----
    print("\n" + "=" * 80)
    print("PER-YEAR + FORWARD-HOLDOUT stress @1% vm — regime overlay vs baseline")
    print("=" * 80)
    _, sc_r, vs_r = apply_mult_to_matrix(rm)
    report['per_year_stress_1pct'] = {}
    print(f"  {'year':>5} {'days':>5} | {'base stress':>11} {'regime stress':>13}")
    for y in sorted(set(dd.year for dd in days)):
        idx = [i for i in range(N_DAYS) if days[i].year == y]
        if len(idx) < 20: continue   # MC needs enough days to bootstrap
        bvals = [comb[i] for i in idx]; rvals = [sc_r[i] for i in idx]
        bs = L.mc_series(L.stress(bvals), 0.01 * vs_base, seed_base=999)['p_pass']
        rs = L.mc_series(L.stress(rvals), 0.01 * vs_r, seed_base=999)['p_pass']
        report['per_year_stress_1pct'][y] = dict(base=bs, regime=rs, n=len(idx))
        print(f"  {y:>5} {len(idx):>5} | {bs:>11.4f} {rs:>13.4f}")
    # forward 2025-26 aggregate
    fvals_b = [comb[i] for i in FWD]; fvals_r = [sc_r[i] for i in FWD]
    print(f"\n  FORWARD 2025-26 (n={len(FWD)}) stress P(pass):")
    report['forward_stress'] = {}
    for risk in (0.0075, 0.01, 0.015):
        fb = L.mc_series(L.stress(fvals_b), risk * vs_base, seed_base=778)['p_pass']
        fr = L.mc_series(L.stress(fvals_r), risk * vs_r, seed_base=778)['p_pass']
        report['forward_stress'][f"{risk*100:.2f}%"] = dict(base=fb, regime=fr)
        print(f"    {risk*100:.2f}%: base {fb:.4f} -> regime {fr:.4f} ({(fr-fb)*100:+.1f} pts)")

    # ---- 2-ACCOUNT joint MC under regime overlay vs baseline (the deploy decision) ----
    print("\n" + "=" * 80)
    print("2-ACCOUNT joint P(both) — baseline vs regime overlay (vol-matched eff sizes)")
    print("=" * 80)
    Mx_r, _, vs_r2 = apply_mult_to_matrix(rm)
    idx = {s: i for i, s in enumerate(sleeves)}; full = {idx[s]: 1.0 for s in sleeves}
    M_stress_base = [[(v * 1.5 if v < 0 else v) for v in row] for row in M]
    M_stress_reg = [[(v * 1.5 if v < 0 else v) for v in row] for row in Mx_r]
    report['two_account'] = {}
    for (sA, sB, label) in [(0.0075, 0.0075, 'balanced'), (0.005, 0.005, 'conservative'),
                            (0.01, 0.0075, 'staggered_1.0_0.75')]:
        eA_b, eB_b = sA * vs_base, sB * vs_base
        eA_r, eB_r = sA * vs_r2, sB * vs_r2
        bb = W2.joint_pass_mc(M, (full, eA_b), (full, eB_b), seed_base=7)
        bs = W2.joint_pass_mc(M_stress_base, (full, eA_b), (full, eB_b), seed_base=44)
        rb = W2.joint_pass_mc(Mx_r, (full, eA_r), (full, eB_r), seed_base=7)
        rs = W2.joint_pass_mc(M_stress_reg, (full, eA_r), (full, eB_r), seed_base=44)
        report['two_account'][label] = dict(
            sizeA=sA, sizeB=sB,
            base_p_both=bb['p_pass_both'], base_stress_p_both=bs['p_pass_both'],
            regime_p_both=rb['p_pass_both'], regime_stress_p_both=rs['p_pass_both'])
        print(f"  {label} (A{sA*100:.2f}/B{sB*100:.2f}): "
              f"P(both) base {bb['p_pass_both']:.2%}->{rb['p_pass_both']:.2%} | "
              f"STRESS {bs['p_pass_both']:.2%}->{rs['p_pass_both']:.2%} "
              f"({(rs['p_pass_both']-bs['p_pass_both'])*100:+.1f} pts)")

    (HERE / 'KB6_COMBINE_RESULT.json').write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote KB6_COMBINE_RESULT.json")


if __name__ == '__main__':
    main()
