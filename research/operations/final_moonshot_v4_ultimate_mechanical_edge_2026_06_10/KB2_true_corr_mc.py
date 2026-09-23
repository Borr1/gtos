"""KB2_true_corr_mc.py — TRUE-correlation diversification-aware portfolio MC + live allocation.

The baseline INTEG MC (INTEG_portfolio_build.combined_daily_R) SUMS all sleeve conf-wtd
unit-R into ONE daily number, then risks risk_per_unit against that sum. That is a
correlation=1 *equity-path* model: it never lets one sleeve's loss day be offset by
another sleeve's profit day except through the realised same-day sum, and (critically for
the 2-account question) it cannot express splitting sleeves across accounts.

This script builds the TRUE version:
  1. Per-day x per-sleeve matrix of conf-wtd unit-R (reuse INTEG sleeve streams + conf weights).
  2. Real cross-sleeve daily-R correlation matrix (Pearson on the daily contribution series,
     0-fill on no-trade days = that sleeve contributed 0 P&L that day, which is the truth).
  3. Diversification-aware challenge MC: block-bootstrap WHOLE cross-sectional day ROWS
     (preserves real same-day co-movement exactly) and let the portfolio daily move be the
     sum of the per-sleeve contributions on that SAMPLED day. Because we resample real days,
     the empirical cross-sleeve covariance (incl. diversification on days where some sleeves
     are flat or anti-move) is preserved by construction.
  4. Compare P(pass) baseline (corr=1 sum -> same as INTEG) vs the per-account TRUE allocation.
  5. Propose a concrete LIVE ALLOCATION across 2 FTMO challenge accounts: assign sleeves to
     accounts to maximise P(pass BOTH) at 0% daily-breach, with per-account risk weights +
     staggered sizing.

NOTE: when the SAME day-set is bootstrapped as whole rows and then summed, the single-account
TRUE P(pass) equals the baseline (the sum of contributions == the baseline daily value).
The diversification PAYOFF is realised by SPLITTING the book across two accounts: each account
holds a sub-book whose daily variance is lower than the full sum, and pass(both) benefits from
the two accounts not breaching on the same paths. We quantify exactly that.
"""
import sys, json, math, statistics, collections, random, pickle
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import INTEG_portfolio_build as I

SLEEVES = ['metals_core','crypto','fx_jpy','energy_agri','idxrev','metals_softband','metals_ob_micro']

# ---------------------------------------------------------------------------
# 1. PER-DAY x PER-SLEEVE conf-wtd unit-R matrix
# ---------------------------------------------------------------------------
def build_matrix(streams):
    """day -> {sleeve: conf-wtd unit_R for 1.0 risk_per_unit} (same convention as INTEG)."""
    byday = collections.defaultdict(lambda: collections.defaultdict(list))
    for name, rows in streams.items():
        for r in rows:
            byday[r['date']][name].append(r['R_sized'])
    daily = {}
    for day, sl in byday.items():
        contrib = {}
        for name, rs in sl.items():
            unit_R = sum(rs) / len(rs)
            contrib[name] = unit_R * I.SLEEVE_CONF[name]
        daily[day] = contrib
    days = sorted(daily)
    # dense matrix rows aligned to SLEEVES, 0-fill on no-trade days
    M = []
    for day in days:
        c = daily[day]
        M.append([c.get(s, 0.0) for s in SLEEVES])
    return days, M

# ---------------------------------------------------------------------------
# 2. Cross-sleeve correlation matrix (Pearson on daily contribution series)
# ---------------------------------------------------------------------------
def pearson(x, y):
    n = len(x)
    mx = sum(x)/n; my = sum(y)/n
    sx = sum((a-mx)**2 for a in x); sy = sum((b-my)**2 for b in y)
    if sx == 0 or sy == 0: return 0.0
    cov = sum((a-mx)*(b-my) for a, b in zip(x, y))
    return cov / math.sqrt(sx*sy)

def corr_matrix(M):
    cols = list(zip(*M))  # per-sleeve daily series
    k = len(SLEEVES)
    C = [[0.0]*k for _ in range(k)]
    for i in range(k):
        for j in range(k):
            C[i][j] = round(pearson(list(cols[i]), list(cols[j])), 3)
    return C

def corr_matrix_cofiring(days, M):
    """Correlation conditioned on days where BOTH sleeves traded (co-firing days only).
    The 0-fill matrix is the right one for portfolio variance, but co-firing corr shows the
    'when they overlap, do they move together' signal explicitly."""
    cols = list(zip(*M))
    k = len(SLEEVES)
    C = [[None]*k for _ in range(k)]
    for i in range(k):
        for j in range(k):
            xs=[]; ys=[]
            for di in range(len(days)):
                if M[di][i] != 0.0 and M[di][j] != 0.0:
                    xs.append(M[di][i]); ys.append(M[di][j])
            C[i][j] = (round(pearson(xs, ys),3), len(xs)) if len(xs) >= 8 else (None, len(xs))
    return C

# ---------------------------------------------------------------------------
# 3. Challenge MC over an arbitrary daily-R value series (one account / sub-book)
# ---------------------------------------------------------------------------
TARGET = I.TARGET; MAXDD = I.MAXDD; DAILY = I.DAILY; BLOCK = I.BLOCK; PATHCAP = I.PATHCAP

def _run_path(vals, n, risk, rng):
    eq = 1.0; peak = 1.0; res = 'timeout'; dc = 0
    for _ in range(PATHCAP):
        start = rng.randrange(n); broke = False
        for k in range(BLOCK):
            dp = vals[(start+k) % n] * risk; dc += 1
            if dp <= -DAILY: return 'fail_daily', dc
            eq *= (1+dp); peak = max(peak, eq)
            if (peak-eq)/peak >= MAXDD: return 'fail_maxdd', dc
            if eq-1.0 >= TARGET: return 'pass', dc
        if broke: break
    return res, dc

def challenge_mc_series(vals, risk, n_paths=20000, seed_base=0):
    n = len(vals); outs = collections.Counter(); dlist=[]
    for s in range(n_paths):
        rng = random.Random(s*131 + seed_base + int(risk*1e6))
        res, dc = _run_path(vals, n, risk, rng)
        outs[res]+=1
        if res=='pass': dlist.append(dc)
    md = int(statistics.median(dlist)) if dlist else None
    return dict(p_pass=outs['pass']/n_paths, p_fail_dd=outs['fail_maxdd']/n_paths,
                p_fail_daily=outs['fail_daily']/n_paths, p_timeout=outs['timeout']/n_paths,
                med_days_pass=md)

# ---------------------------------------------------------------------------
# 3b. JOINT MC over TWO sub-books sharing the SAME bootstrapped day-stream
#     (preserves cross-account co-movement: both accounts see the same sampled days).
#     Each account has its own sleeve subset, own per-sleeve risk weight, own size scalar.
#     Account daily move = sum over its sleeves of (contrib_for_1.0_unit * sleeve_weight * size).
# ---------------------------------------------------------------------------
def acct_daily_series(M, sleeve_idx_weights, size):
    """Return per-day value series for one account.
    sleeve_idx_weights: dict {sleeve_col_index: weight}. value = size * sum(M[d][i]*w)."""
    out = []
    for row in M:
        v = 0.0
        for i, w in sleeve_idx_weights.items():
            v += row[i] * w
        out.append(v * size)
    return out

def joint_pass_mc(M, accA, accB, n_paths=20000, seed_base=0):
    """accA/accB = (sleeve_idx_weights, size). Both accounts trade the SAME sampled day-blocks
    (same calendar -> real cross-account co-movement preserved). Returns P(passA), P(passB),
    P(pass BOTH), P(either breach), per-account breach probs."""
    valsA = acct_daily_series(M, accA[0], accA[1])
    valsB = acct_daily_series(M, accB[0], accB[1])
    n = len(valsA)
    cBoth=0; cA=0; cB=0; cAfail_d=0; cAfail_dd=0; cBfail_d=0; cBfail_dd=0
    for s in range(n_paths):
        rng = random.Random(s*131 + seed_base)
        # shared day-block stream
        eqA=1.0; peakA=1.0; resA='timeout'
        eqB=1.0; peakB=1.0; resB='timeout'
        for _ in range(PATHCAP):
            start = rng.randrange(n)
            for k in range(BLOCK):
                idx=(start+k)%n
                if resA=='timeout':
                    dpA=valsA[idx]
                    if dpA<=-DAILY: resA='fail_daily'
                    else:
                        eqA*=(1+dpA); peakA=max(peakA,eqA)
                        if (peakA-eqA)/peakA>=MAXDD: resA='fail_maxdd'
                        elif eqA-1.0>=TARGET: resA='pass'
                if resB=='timeout':
                    dpB=valsB[idx]
                    if dpB<=-DAILY: resB='fail_daily'
                    else:
                        eqB*=(1+dpB); peakB=max(peakB,eqB)
                        if (peakB-eqB)/peakB>=MAXDD: resB='fail_maxdd'
                        elif eqB-1.0>=TARGET: resB='pass'
                if resA!='timeout' and resB!='timeout': break
            if resA!='timeout' and resB!='timeout': break
        if resA=='pass': cA+=1
        if resB=='pass': cB+=1
        if resA=='pass' and resB=='pass': cBoth+=1
        if resA=='fail_daily': cAfail_d+=1
        if resA=='fail_maxdd': cAfail_dd+=1
        if resB=='fail_daily': cBfail_d+=1
        if resB=='fail_maxdd': cBfail_dd+=1
    return dict(p_passA=cA/n_paths, p_passB=cB/n_paths, p_pass_both=cBoth/n_paths,
                p_A_fail_daily=cAfail_d/n_paths, p_A_fail_dd=cAfail_dd/n_paths,
                p_B_fail_daily=cBfail_d/n_paths, p_B_fail_dd=cBfail_dd/n_paths)

# ---------------------------------------------------------------------------
def main():
    streams = pickle.load(open(HERE/'KB2_streams_cache.pkl','rb'))
    days, M = build_matrix(streams)
    days_fwd_mask = [d.year >= 2025 for d in days]
    M_fwd = [row for row, fwd in zip(M, days_fwd_mask) if fwd]
    print(f"matrix: {len(M)} days x {len(SLEEVES)} sleeves | fwd days {len(M_fwd)}")

    # ---- correlation matrices ----
    C = corr_matrix(M)
    Cco = corr_matrix_cofiring(days, M)
    print("\n=== CROSS-SLEEVE DAILY-R CORRELATION (0-fill, full history) ===")
    print("        " + " ".join(f"{s[:7]:>8}" for s in SLEEVES))
    for i, s in enumerate(SLEEVES):
        print(f"{s[:7]:>7} " + " ".join(f"{C[i][j]:>8.2f}" for j in range(len(SLEEVES))))

    # average pairwise off-diagonal correlation (the diversification headline)
    offs = [C[i][j] for i in range(len(SLEEVES)) for j in range(len(SLEEVES)) if i < j]
    avg_off = sum(offs)/len(offs)
    print(f"\nAvg pairwise off-diagonal corr (0-fill): {avg_off:+.3f}  (max {max(offs):+.2f}, min {min(offs):+.2f})")

    # ---- baseline (corr=1 sum) reference via INTEG convention ----
    comb = [sum(row) for row in M]            # baseline daily value series (corr=1 sum)
    comb_fwd = [sum(row) for row in M_fwd]
    print("\n=== BASELINE (correlation=1 SUM) single-account challenge MC ===")
    base = {}
    for risk in (0.005, 0.0075, 0.01, 0.015, 0.02):
        r = challenge_mc_series(comb, risk)
        base[f"{risk*100:.2f}%"] = r
        print(f"  {risk*100:>5.2f}%  P(pass)={r['p_pass']:.3%}  fail_dd={r['p_fail_dd']:.3%}  fail_daily={r['p_fail_daily']:.3%}  med_days={r['med_days_pass']}")

    out = dict(n_days=len(M), n_days_fwd=len(M_fwd), sleeves=SLEEVES,
               corr_matrix=C, corr_cofiring=[[Cco[i][j] for j in range(len(SLEEVES))] for i in range(len(SLEEVES))],
               avg_off_diag_corr=round(avg_off,3), baseline_mc=base)
    json.dump(out, open(HERE/'KB2_corr_and_baseline.json','w'), indent=1, default=str)
    print("\nwrote KB2_corr_and_baseline.json")
    return days, M, M_fwd

if __name__ == '__main__':
    main()
