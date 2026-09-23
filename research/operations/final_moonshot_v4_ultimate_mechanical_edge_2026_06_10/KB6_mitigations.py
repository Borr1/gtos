"""KB6_mitigations.py — stress-harden the clean_3 deploy book: raise the binding 1.5x P(pass).

Tests four mitigation families on the REAL clean_3 day x sleeve matrix, judged on the LOCKED
W2 MC engine (block-bootstrap whole days, BLOCK=5, N=20000, TARGET 8%/DAILY 5%/MAXDD 10%),
ALWAYS vol-matched (risk-equivalent) so a mitigation cannot win just by de-levering:

  (a) W3 breadth+drawdown regime overlay  (KB3_regime_scaling classifier, ported to clean_3)
  (b) correlation-spike / co-loss circuit breaker (de-risk the day AFTER a cross-sleeve co-loss
      spike — leak-free, state from days < t)
  (c) per-sleeve vol-targeted sizing (cap the high-variance crypto sleeve's daily contribution
      to a vol budget; the diagnosis showed crypto drives ~49% of the worst-day loss mass)
  (d) soft daily de-risk ladder (after consecutive book-loss days, trim next-day size; recover
      after a green day) — leak-free

Every overlay's multiplier uses ONLY days < t. Each scaled series is then NORMALIZED to the
SAME average gross exposure as the base book and re-vol-matched to the W3 book std, so the only
thing being compared is WHERE risk is placed, never the amount. Verdict = 1.5x-stress P(pass)
lift at matched risk, with base P(pass), EV, and frequency preserved.
"""
import sys, json, statistics, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import KB6_stress_lib as L

d = L.build_clean3()
days, sleeves, M, comb, fwd_mask = d['all_days'], d['sleeves'], d['M'], d['comb'], d['fwd_mask']
vs_base = d['vol_scale']; breadth = d['breadth']
book_series = d['book_series']
sd_book = statistics.pstdev([v for v in book_series])
N_DAYS = len(comb)
RISKS = (0.005, 0.0075, 0.01, 0.015, 0.02)
sidx = {s: i for i, s in enumerate(sleeves)}

TRAIN = [i for i in range(N_DAYS) if days[i].year <= 2024]


def wmean(x): return sum(x) / len(x) if x else 0.0


def apply_mult(mults):
    """Apply a per-day multiplier vector to the combined series; normalize to same avg gross
    exposure (mean |day| weighting) as base, then vol-match to the W3 book std. Returns the
    new combined series + the vol_scale to use, so risk is held equal to base."""
    scaled = [comb[t] * mults[t] for t in range(N_DAYS)]
    am = wmean(mults)
    scaled = [v / am for v in scaled]            # neutralize gross-exposure change
    sd = statistics.pstdev(scaled)
    vs = sd_book / sd if sd > 0 else 1.0          # vol-match to W3 book std (same as deploy)
    return scaled, vs


def eval_series(series, vs, label):
    base = L.grid_pass(series, scale=vs, stressed=False)
    strs = L.grid_pass(series, scale=vs, stressed=True)
    mu = statistics.fmean(series); sd = statistics.pstdev(series)
    return dict(label=label, vol_scale=round(vs, 4), mean=round(mu, 5), std=round(sd, 5),
                sharpe=round(mu / sd, 4) if sd else 0.0,
                base=base, stress=strs)


# ============================================================================
# (a) W3 BREADTH + DRAWDOWN regime overlay (ported to clean_3)
# ============================================================================
BW = 10
def regime_mults():
    feats = []
    cum = 0.0; peak = 0.0; started = False
    for t in range(N_DAYS):
        pb = breadth[max(0, t - BW):t]
        tb = wmean(pb) if pb else 0.0
        dd = (peak - cum) if started else 0.0
        warm = t >= BW
        feats.append(dict(trail_breadth=tb, dd=dd, warm=warm))
        cum += comb[t]; peak = max(peak, cum); started = True
    dd_train = sorted(feats[t]['dd'] for t in TRAIN)
    DD_MED = dd_train[len(dd_train) // 2] if dd_train else 0.0
    mults = []
    for f in feats:
        if not f['warm']:
            m = 1.0
        elif f['trail_breadth'] >= 2.0:
            m = 1.25
        elif f['trail_breadth'] >= 1.3:
            m = 1.00
        else:
            m = 0.85
        if f['dd'] > DD_MED * 1.5:
            m *= 0.80
        mults.append(m)
    return mults


# ============================================================================
# (b) CORRELATION-SPIKE / CO-LOSS circuit breaker
# Leak-free: on day t, look at the trailing W days. If the recent cross-sleeve realized
# co-movement spiked (many sleeves losing together = correlation regime), de-risk day t.
# Proxy for "realized cross-sleeve corr jump" without lookahead: the trailing fraction of
# sleeve-days that were negative among co-firing sleeves (co-loss intensity) + a same-sign
# concentration measure. Both computed from days < t only.
# ============================================================================
def coloss_mults(W=5, thresh=0.62, derisk=0.70):
    mults = [1.0] * N_DAYS
    for t in range(N_DAYS):
        if t < W:
            continue
        # trailing window co-loss intensity: of all (sleeve,day) firings in [t-W,t), fraction negative
        nfire = 0; nneg = 0
        for u in range(t - W, t):
            for si in range(len(sleeves)):
                v = M[u][si]
                if v != 0.0:
                    nfire += 1
                    if v < 0:
                        nneg += 1
        if nfire >= 4:
            frac = nneg / nfire
            if frac >= thresh:
                mults[t] = derisk
    return mults


# ============================================================================
# (c) PER-SLEEVE VOL-TARGET (cap the high-variance sleeve's daily contribution).
# The diagnosis: crypto drives ~49% of worst-day loss mass. Cap each sleeve's per-day
# contribution at a vol budget = k * (TRAIN per-sleeve daily std). Leak-free: cap derived
# from TRAIN<=2024 std, applied to all days. This is NOT a multiplier on the book — it
# reshapes the matrix, so it is risk-matched by the final vol_scale, not by avg_mult.
# ============================================================================
def voltarget_series(k=2.0, sleeve_subset=None):
    # per-sleeve TRAIN daily std (over days that sleeve fired, train only)
    sl_std = {}
    for si, s in enumerate(sleeves):
        vals = [M[t][si] for t in TRAIN if M[t][si] != 0.0]
        sl_std[s] = statistics.pstdev(vals) if len(vals) > 1 else 0.0
    target = sleeve_subset if sleeve_subset else sleeves
    newM = []
    for t in range(N_DAYS):
        row = list(M[t])
        for si, s in enumerate(sleeves):
            if s in target and sl_std[s] > 0:
                cap = k * sl_std[s]
                if row[si] < -cap:
                    row[si] = -cap            # cap only the LEFT tail (don't clip winners)
        newM.append(row)
    scaled = [sum(r) for r in newM]
    sd = statistics.pstdev(scaled)
    vs = sd_book / sd if sd > 0 else 1.0
    return scaled, vs


# ============================================================================
# (d) SOFT DAILY DE-RISK LADDER. After k consecutive book-loss days, trim next-day size;
# step back up after a green day. Leak-free (uses realized days < t).
# ============================================================================
def ladder_mults(steps=(1.0, 0.85, 0.70, 0.55), recover_full=True):
    mults = [1.0] * N_DAYS
    streak = 0
    for t in range(N_DAYS):
        lvl = min(streak, len(steps) - 1)
        mults[t] = steps[lvl]
        # update streak from realized day t (used for day t+1)
        if comb[t] < 0:
            streak += 1
        else:
            streak = 0 if recover_full else max(0, streak - 1)
    return mults


# ============================================================================
def main():
    report = {'book': 'clean_3', 'engine': 'LOCKED W2 (BLOCK5 N20000 8/5/10)',
              'risk_equivalence': 'vol-matched to W3 book std + gross-exposure normalized',
              'baseline_vol_scale': round(vs_base, 4), 'results': {}}

    def record(key, series, vs, note=''):
        r = eval_series(series, vs, key); r['note'] = note
        report['results'][key] = r
        print(f"\n[{key}]  {note}")
        print(f"   sharpe={r['sharpe']:.4f} vol_scale={r['vol_scale']}")
        print(f"   {'risk':>7} {'base':>8} {'stress1.5x':>11}")
        for k in r['base']:
            print(f"   {k:>7} {r['base'][k]:>8.4f} {r['stress'][k]:>11.4f}")
        return r

    print("=" * 80)
    print("KB6 STRESS-HARDENING — mitigations on clean_3 (vol-matched, locked MC)")
    print("=" * 80)

    base = record('BASELINE', comb, vs_base, 'clean_3 deploy book (matches deploy JSON)')

    # (a) W3 regime overlay
    rm = regime_mults()
    sa, va = apply_mult(rm)
    record('a_regime_overlay', sa, va, 'W3 breadth+drawdown regime scaling (ACTIVE1.25/QUIET0.85/DDx0.80)')

    # (b) co-loss circuit breaker — sweep
    for (W, th, dk) in [(5, 0.62, 0.70), (5, 0.58, 0.60), (3, 0.60, 0.70), (7, 0.60, 0.65)]:
        cm = coloss_mults(W, th, dk)
        nfired = sum(1 for m in cm if m < 1.0)
        sb, vb = apply_mult(cm)
        record(f'b_coloss_W{W}_th{int(th*100)}_dk{int(dk*100)}', sb, vb,
               f'co-loss breaker: de-risk x{dk} after trailing-{W}d neg-frac>={th} (fired {nfired}d)')

    # (c) per-sleeve vol-target — crypto only, then all sleeves, sweep k
    for k in (2.5, 2.0, 1.5):
        sc, vc = voltarget_series(k=k, sleeve_subset={'crypto'})
        record(f'c_voltarget_crypto_k{k}', sc, vc, f'cap crypto left-tail at {k}x TRAIN sleeve-std')
    for k in (2.0, 1.5):
        sc, vc = voltarget_series(k=k, sleeve_subset={'crypto', 'metals_core', 'energy_agri'})
        record(f'c_voltarget_top3_k{k}', sc, vc, f'cap crypto+metals+energy left-tail at {k}x TRAIN std')

    # (d) soft daily de-risk ladder — sweep depth
    for steps in [(1.0, 0.85, 0.70, 0.55), (1.0, 0.80, 0.60), (1.0, 0.90, 0.80, 0.70, 0.60)]:
        lm = ladder_mults(steps)
        sd_, vd = apply_mult(lm)
        record(f'd_ladder_{len(steps)}step', sd_, vd, f'daily de-risk ladder steps={steps}')

    (HERE / 'KB6_MITIGATIONS_RESULT.json').write_text(json.dumps(report, indent=1, default=str))
    print("\n\nwrote KB6_MITIGATIONS_RESULT.json")

    # ---- summary table: stress lift vs baseline at the key sizes ----
    print("\n" + "=" * 80)
    print("SUMMARY — 1.5x-stress P(pass) vs baseline (vol-matched). Δ in pts.")
    print("=" * 80)
    bk = base['stress']
    print(f"{'mitigation':>34} {'sh':>7} | " + " ".join(f"{k:>8}" for k in RISKS_K()))
    for key, r in report['results'].items():
        if key == 'BASELINE':
            print(f"{key:>34} {r['sharpe']:>7.4f} | " + " ".join(f"{r['stress'][k]:>8.4f}" for k in r['stress']))
            print("-" * 90)
            continue
        deltas = []
        for k in r['stress']:
            deltas.append(f"{(r['stress'][k]-bk[k])*100:>+7.1f}")
        print(f"{key:>34} {r['sharpe']:>7.4f} | " + " ".join(f"{x:>8}" for x in deltas))


def RISKS_K():
    return [f"{r*100:.2f}%" for r in RISKS]


if __name__ == '__main__':
    main()
