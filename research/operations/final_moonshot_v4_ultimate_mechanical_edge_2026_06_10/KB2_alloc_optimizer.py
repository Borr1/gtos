"""KB2_alloc_optimizer.py — diversification-aware single-book MC, independent-shuffle bound,
and the 2-account live allocation optimizer. Run AFTER KB2_true_corr_mc.py (uses cache).
"""
import sys, json, itertools, statistics, collections, random, pickle
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import INTEG_portfolio_build as I
from KB2_true_corr_mc import (build_matrix, SLEEVES, challenge_mc_series, acct_daily_series,
                              joint_pass_mc, TARGET, MAXDD, DAILY, BLOCK, PATHCAP)

def main():
    streams = pickle.load(open(HERE/'KB2_streams_cache.pkl','rb'))
    days, M = build_matrix(streams)
    fwd_mask = [d.year >= 2025 for d in days]
    M_fwd = [row for row, fwd in zip(M, fwd_mask) if fwd]
    idx = {s:i for i,s in enumerate(SLEEVES)}
    report = {}

    # ===================================================================
    # A. TRUE DIVERSIFICATION single-account model.
    #    Baseline: risk `risk` against SUM(row) -> one risk unit for whole book (corr=1 path).
    #    TRUE:     each sleeve carries its OWN `risk` -> daily move = risk * SUM(row).
    #    NOTE these are algebraically identical when all sleeves share one `risk`!
    #    The genuine diversification question is: how much LARGER can per-sleeve risk be at
    #    equal breach risk, because real days rarely have all sleeves losing together.
    #    We answer it by sweeping risk on the REAL-day-row bootstrap (which already preserves
    #    the true near-zero co-movement) and reporting the size that holds P(pass)>=99% AND
    #    daily-breach==0 -> that is the diversification-justified live size.
    # ===================================================================
    comb = [sum(r) for r in M]
    comb_fwd = [sum(r) for r in M_fwd]

    # Independent-shuffle counterfactual: break same-day co-movement by shuffling each sleeve
    # column independently across days, then re-sum. If P(pass) is ~unchanged vs real rows,
    # co-movement is irrelevant (i.e. corr really is ~0) -> diversification credit is REAL.
    rng = random.Random(12345)
    cols = [list(c) for c in zip(*M)]
    for c in cols: rng.shuffle(c)
    M_shuf = list(zip(*cols))
    comb_shuf = [sum(r) for r in M_shuf]

    print("=== A. Single-account: REAL-day rows vs INDEPENDENT-shuffle (co-movement test) ===")
    report['single_account'] = {}
    for risk in (0.005,0.0075,0.01,0.015,0.02,0.025,0.03):
        rr = challenge_mc_series(comb, risk, seed_base=1)
        rs = challenge_mc_series(comb_shuf, risk, seed_base=1)
        report['single_account'][f"{risk*100:.2f}%"] = dict(real=rr, indep_shuffle=rs)
        print(f"  {risk*100:>5.2f}%  REAL P(pass)={rr['p_pass']:.3%} dd={rr['p_fail_dd']:.3%} daily={rr['p_fail_daily']:.3%} | "
              f"SHUF P(pass)={rs['p_pass']:.3%} dd={rs['p_fail_dd']:.3%} daily={rs['p_fail_daily']:.3%}")

    # ===================================================================
    # B. 2-ACCOUNT LIVE ALLOCATION OPTIMIZER.
    #    Two FTMO challenge accounts. We split sleeves into two sub-books (account A / account B)
    #    + per-account size scalar. Goal: maximise P(pass BOTH) at 0% daily-breach.
    #    Diversification across ACCOUNTS is the real prize: each account's daily variance is
    #    lower than the full book, so it passes safely, and because the two accounts hold
    #    different sleeves their pass paths are not perfectly coupled.
    #    Search: assign each sleeve to A or B (the big engine metals_core is the anchor of A;
    #    we also test a 'balanced-EV' split). Per-sleeve weight = its confidence (already baked
    #    into M as conf-wtd unit-R, so weight here is a STRATEGIC OVERWEIGHT multiplier, default 1).
    # ===================================================================
    # candidate splits (sleeve sets for account A; rest -> B). Keep all 7 sleeves live (delete nothing).
    # design intuition: pair the big engine with low-corr breadth; balance EV across the two books.
    contrib = {s: sum(M[d][idx[s]] for d in range(len(M))) for s in SLEEVES}  # total conf-wtd unit-R per sleeve
    print("\nper-sleeve total conf-wtd unit-R (book EV contribution):")
    for s in sorted(SLEEVES, key=lambda k:-contrib[k]):
        print(f"   {s:>16}: {contrib[s]:+.2f}")

    splits = {
        # A = engine + uncorrelated carriers ; B = breadth/frequency
        'engine_vs_breadth': (['metals_core','crypto','metals_softband','metals_ob_micro'],
                              ['fx_jpy','energy_agri','idxrev']),
        # EV-balanced: split so each account ~ half the book EV
        'ev_balanced':       (['metals_core','idxrev','metals_softband'],
                              ['crypto','fx_jpy','energy_agri','metals_ob_micro']),
        # metals-vs-rest (max asset-class separation)
        'metals_vs_rest':    (['metals_core','metals_softband','metals_ob_micro'],
                              ['crypto','fx_jpy','energy_agri','idxrev']),
        # engine+jpy vs crypto+energy+idx (both books have a deep carrier + breadth)
        'twin_carrier':      (['metals_core','fx_jpy','metals_softband'],
                              ['crypto','energy_agri','idxrev','metals_ob_micro']),
    }
    def to_w(sl): return {idx[s]:1.0 for s in sl}

    print("\n=== B. 2-ACCOUNT JOINT MC (shared sampled days; per-account size sweep) ===")
    report['two_account'] = {}
    best = None
    for sname,(A,B) in splits.items():
        report['two_account'][sname] = dict(A=A, B=B, A_EV=round(sum(contrib[s] for s in A),2),
                                             B_EV=round(sum(contrib[s] for s in B),2), sizes={})
        print(f"\n-- split '{sname}' | A={A} (EV {sum(contrib[s] for s in A):+.1f}) | B={B} (EV {sum(contrib[s] for s in B):+.1f})")
        for sizeA, sizeB in [(0.005,0.005),(0.0075,0.0075),(0.01,0.01),(0.015,0.015),
                              (0.01,0.0075),(0.015,0.01),(0.02,0.015)]:
            r = joint_pass_mc(M, (to_w(A),sizeA), (to_w(B),sizeB), seed_base=7)
            key=f"A{sizeA*100:.2f}%/B{sizeB*100:.2f}%"
            report['two_account'][sname]['sizes'][key]=r
            both=r['p_pass_both']
            print(f"   {key}: P(passA)={r['p_passA']:.3%} P(passB)={r['p_passB']:.3%} "
                  f"P(BOTH)={both:.3%} | A daily={r['p_A_fail_daily']:.3%} B daily={r['p_B_fail_daily']:.3%}")
            cand=dict(split=sname,sizes=key,p_both=both,
                      daily=max(r['p_A_fail_daily'],r['p_B_fail_daily']),detail=r,A=A,B=B,
                      sizeA=sizeA,sizeB=sizeB)
            # objective: max P(both) subject to 0% daily breach
            if cand['daily']==0.0 and (best is None or both>best['p_both'] or
               (abs(both-best['p_both'])<1e-9 and (sizeA+sizeB)>(best['sizeA']+best['sizeB']))):
                best=cand
    report['best_allocation_max_pboth']=best
    print("\n=== BEST 2-ACCOUNT ALLOCATION (max P(both) @ 0% daily breach) ===")
    print(json.dumps({k:best[k] for k in ('split','sizes','p_both','daily','A','B')}, indent=1))

    # ---- C. Frontier: for the best STRUCTURAL split, find the FASTEST (largest size)
    #         allocation that still holds P(both) >= 0.99 at 0% daily breach. Speed matters
    #         (fewer challenge days) so we want the largest safe size, not the timid corner. ----
    # use 'metals_vs_rest' (max asset-class separation, balanced EV) as the recommended split.
    REC = ('metals_vs_rest', splits['metals_vs_rest'])
    A,B = REC[1]
    print(f"\n=== C. RECOMMENDED SPLIT '{REC[0]}' size frontier (target P(both)>=99%, daily=0) ===")
    frontier=[]
    for sizeA in (0.0075,0.01,0.0125,0.015,0.0175,0.02):
        for sizeB in (0.0075,0.01,0.0125,0.015):
            r=joint_pass_mc(M,(to_w(A),sizeA),(to_w(B),sizeB),seed_base=21)
            frontier.append(dict(sizeA=sizeA,sizeB=sizeB,p_both=r['p_pass_both'],
                                 p_passA=r['p_passA'],p_passB=r['p_passB'],
                                 daily=max(r['p_A_fail_daily'],r['p_B_fail_daily'])))
    report['recommended_split']=REC[0]; report['frontier']=frontier
    safe=[f for f in frontier if f['p_both']>=0.99 and f['daily']==0.0]
    fastest=max(safe,key=lambda f:f['sizeA']+f['sizeB']) if safe else None
    report['fastest_safe_allocation']=fastest
    for f in sorted(frontier,key=lambda x:-(x['sizeA']+x['sizeB'])):
        flag=' <- SAFE' if (f['p_both']>=0.99 and f['daily']==0) else ''
        print(f"   A{f['sizeA']*100:.2f}%/B{f['sizeB']*100:.2f}%  P(both)={f['p_both']:.3%}  daily={f['daily']:.3%}{flag}")
    print(f"\n  FASTEST-SAFE (max size, P(both)>=99%, 0 daily): {fastest}")

    # ---- D. STRESS-ROBUST selection: re-run frontier under 1.5x loss inflation, pick the
    #         LARGEST size that holds BOTH base P(both)>=99% AND stressed P(both)>=85%
    #         (matches the INTEG stress acceptance bar) at 0% daily breach. ----
    M_stress=[[ (v*1.5 if v<0 else v) for v in row] for row in M]
    print(f"\n=== D. STRESS-ROBUST frontier (base P(both)>=99% AND stress1.5x P(both)>=85%) ===")
    robust=[]
    for f in frontier:
        rs=joint_pass_mc(M_stress,(to_w(A),f['sizeA']),(to_w(B),f['sizeB']),seed_base=44)
        f['stress_p_both']=rs['p_pass_both']; f['stress_passA']=rs['p_passA']; f['stress_passB']=rs['p_passB']
        if f['p_both']>=0.99 and f['daily']==0 and rs['p_pass_both']>=0.85:
            robust.append(f)
    rec=max(robust,key=lambda f:f['sizeA']+f['sizeB']) if robust else None
    report['frontier']=frontier  # now annotated with stress
    report['recommended_allocation']=rec
    for f in sorted(frontier,key=lambda x:-(x['sizeA']+x['sizeB'])):
        ok = f['p_both']>=0.99 and f['daily']==0 and f['stress_p_both']>=0.85
        print(f"   A{f['sizeA']*100:.2f}%/B{f['sizeB']*100:.2f}%  base P(both)={f['p_both']:.2%}  "
              f"stress P(both)={f['stress_p_both']:.2%}{'  <- ROBUST' if ok else ''}")
    print(f"\n  RECOMMENDED (max size; base>=99% & stress>=85% & 0 daily): {rec}")

    # ---- E. Forward-only validation of the recommended robust allocation ----
    if rec:
        rfwd=joint_pass_mc(M_fwd,(to_w(A),rec['sizeA']),(to_w(B),rec['sizeB']),seed_base=33)
        report['fwd_validation']=dict(sizeA=rec['sizeA'],sizeB=rec['sizeB'],result=rfwd)
        print(f"\n=== E. FORWARD 2025-26 validation of RECOMMENDED alloc ===")
        print(f"   P(passA)={rfwd['p_passA']:.3%} P(passB)={rfwd['p_passB']:.3%} P(BOTH)={rfwd['p_pass_both']:.3%} "
              f"| A daily={rfwd['p_A_fail_daily']:.3%} B daily={rfwd['p_B_fail_daily']:.3%}")

    json.dump(report, open(HERE/'KB2_alloc_result.json','w'), indent=1, default=str)
    print("\nwrote KB2_alloc_result.json")

if __name__ == '__main__':
    main()
