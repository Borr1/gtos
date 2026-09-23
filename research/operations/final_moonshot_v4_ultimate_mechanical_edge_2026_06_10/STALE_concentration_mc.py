"""STALE_concentration_mc.py — (b) concentration-cap drag, book-level, LOCKED MC engine.
Rebuilds the clean_3 deploy matrix from caches but varies the SAME-DAY SAME-SLEEVE pooling rule:
  - 'mean' (DEPLOYED): unit_R = mean(R) -> all same-day same-sleeve trades = 1 unit (corr=1 within).
  - 'pool_k2'/'pool_k3': unit_R = sum(R)/min(K, n) -> allow up to K independent units/day.
  - 'sqrtn': unit_R = sum(R)/sqrt(n) -> partial-correlation credit (effective N = sqrt(n)).
Then runs the locked vol-matched + 1.5x-stress MC at the deploy size grid. Reports pass-rate,
median days-to-pass, AND the worst-day / max-DD tail (the guardrail) so loosening is only kept
if it raises growth WITHOUT raising P(maxDD breach) unacceptably. Forward-validated (mc_fwd).
"""
import sys, statistics, collections, math, pickle, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3

streams_w3 = pickle.load(open(HERE / 'INTEG_W3_streams_cache.pkl', 'rb'))
new_streams = pickle.load(open(HERE / 'INTEG_W5_new_streams_cache.pkl', 'rb'))
CLEAN3_CONF = {'sub_xvol_pullback': 0.45, 'vp_euidx_pocgrav': 0.30, 'sub_mid_dn_revert': 0.20}
BOOK_CONF = W3.SLEEVE_CONF

def pool_unit(rs, mode):
    n = len(rs); ssum = sum(rs)
    if mode == 'mean': return ssum / n
    if mode == 'pool_k2': return ssum / min(2, n)
    if mode == 'pool_k3': return ssum / min(3, n)
    if mode == 'sqrtn': return ssum / math.sqrt(n)
    raise ValueError(mode)

def build_comb(mode):
    """Build the clean_3 combined daily series under a given pooling mode for ALL sleeves."""
    # gather per-sleeve per-day raw R lists
    bysleeve_day = collections.defaultdict(lambda: collections.defaultdict(list))
    for nm, rows in streams_w3.items():
        for r in rows:
            isz = r.get('intra_size', 1.0)
            bysleeve_day[nm][r['date']].append(r['R'] * isz)
    for nm, rows in new_streams.items():
        if nm not in CLEAN3_CONF: continue
        for r in rows:
            isz = r.get('intra_size', 1.0)
            bysleeve_day[nm][r['date']].append(r['R'] * isz)
    conf = dict(BOOK_CONF); conf.update(CLEAN3_CONF)
    all_days = sorted(set(d for nm in bysleeve_day for d in bysleeve_day[nm]))
    comb = []; comb_fwd = []
    for day in all_days:
        v = 0.0
        for nm in bysleeve_day:
            if day in bysleeve_day[nm]:
                v += pool_unit(bysleeve_day[nm][day], mode) * conf[nm]
        comb.append(v)
        if day.year >= 2025: comb_fwd.append(v)
    return comb, comb_fwd, all_days

def main():
    report = {}
    # baseline std for vol-matching (the DEPLOYED 'mean' book std is the reference)
    comb_mean, _, _ = build_comb('mean')
    sd_ref = statistics.pstdev(comb_mean)
    print(f"reference (deployed 'mean') std = {sd_ref:.4f}  mean = {statistics.fmean(comb_mean):.5f}\n")

    print(f"{'mode':>9} {'mean':>8} {'std':>8} {'sharpe':>7} {'worst':>8} | "
          f"{'vm@1%P':>8} {'vm@1%d':>7} {'vm@1.5%P':>9} {'str@1%':>8} {'str@1.5%':>9} | {'fwd@1%d':>8}")
    for mode in ('mean', 'sqrtn', 'pool_k2', 'pool_k3'):
        comb, comb_fwd, days = build_comb(mode)
        m = statistics.fmean(comb); sd = statistics.pstdev(comb); shp = m / sd
        worst = min(comb)
        vs = sd_ref / sd  # vol-match every variant to the SAME daily std as deployed
        cstr = [(v * 1.5 if v < 0 else v) for v in comb]
        r1 = W2.mc_series(comb, 0.01 * vs, seed_base=1)
        r15 = W2.mc_series(comb, 0.015 * vs, seed_base=1)
        s1 = W2.mc_series(cstr, 0.01 * vs, seed_base=999)
        s15 = W2.mc_series(cstr, 0.015 * vs, seed_base=999)
        f1 = W2.mc_series(comb_fwd, 0.01 * vs, seed_base=777)
        report[mode] = dict(mean=round(m, 5), std=round(sd, 5), sharpe=round(shp, 4),
                            worst_day_unitR=round(worst, 4), vol_scale=round(vs, 4),
                            vm_1pct=r1, vm_1p5pct=r15, stress_1pct=s1, stress_1p5pct=s15, fwd_1pct=f1)
        print(f"{mode:>9} {m:>8.5f} {sd:>8.4f} {shp:>7.4f} {worst:>8.3f} | "
              f"{r1['p_pass']:>8.2%} {str(r1['med_days_pass']):>7} {r15['p_pass']:>9.2%} "
              f"{s1['p_pass']:>8.2%} {s15['p_pass']:>9.2%} | {str(f1['med_days_pass']):>8}")

    # ---- RAW (NOT vol-matched) comparison: does looser pooling actually grow FASTER at a fixed nominal size? ----
    print("\n=== RAW (fixed nominal size, NOT vol-matched) — true growth-rate test ===")
    print(f"{'mode':>9} {'@0.75%P':>9} {'@0.75%d':>9} {'@1%P':>7} {'@1%d':>7} {'str@1%P':>9} {'worstday@1%':>12} {'breach@1%':>10}")
    report['raw'] = {}
    for mode in ('mean', 'sqrtn', 'pool_k2', 'pool_k3'):
        comb, comb_fwd, days = build_comb(mode)
        cstr = [(v * 1.5 if v < 0 else v) for v in comb]
        r075 = W2.mc_series(comb, 0.0075, seed_base=1)
        r1 = W2.mc_series(comb, 0.01, seed_base=1)
        s1 = W2.mc_series(cstr, 0.01, seed_base=999)
        worst1 = min(comb) * 0.01
        breach1 = sum(1 for v in comb if v * 0.01 <= -0.05) / len(comb)
        report['raw'][mode] = dict(p075=r075, p1=r1, stress1=s1, worst_day_pct_at1=round(worst1 * 100, 3),
                                   breach_pct_at1=round(breach1 * 100, 4))
        print(f"{mode:>9} {r075['p_pass']:>9.2%} {str(r075['med_days_pass']):>9} {r1['p_pass']:>7.2%} "
              f"{str(r1['med_days_pass']):>7} {s1['p_pass']:>9.2%} {worst1*100:>11.3f}% {breach1*100:>9.3f}%")

    (HERE / 'STALE_concentration_mc_RESULT.json').write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote STALE_concentration_mc_RESULT.json")

if __name__ == '__main__':
    main()
