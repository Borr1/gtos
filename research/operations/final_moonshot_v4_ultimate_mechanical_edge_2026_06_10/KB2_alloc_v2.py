"""KB2_alloc_v2.py — 2-account allocation where the robust engine (metals_core) anchors BOTH
accounts via fractional risk split, so neither account is left without a deep, train-validated
anchor. This fixes the v1 finding that isolating breadth sleeves into one account makes that
account fragile under stress (P(passB) collapsed under 1.5x loss inflation).

Design:
  - metals_core (conf 1.0, deepest train, +1.16R fwd, 43% of book EV) is the ANCHOR. Split its
    risk fA / fB between the two accounts (fA+fB=1).
  - The other sleeves are assigned whole to one account (they are distinct symbols).
  - Each account = anchor_fraction*metals_core + its breadth sleeves, at its own size scalar.
  - Objective: max total deployed size s.t. base P(both)>=99%, stress1.5x P(both)>=85%, 0 daily.
"""
import sys, json, collections, random, pickle
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import INTEG_portfolio_build as I
from KB2_true_corr_mc import build_matrix, SLEEVES, joint_pass_mc

def main():
    streams = pickle.load(open(HERE/'KB2_streams_cache.pkl','rb'))
    days, M = build_matrix(streams)
    fwd_mask=[d.year>=2025 for d in days]
    M_fwd=[r for r,f in zip(M,fwd_mask) if f]
    M_stress=[[ (v*1.5 if v<0 else v) for v in row] for row in M]
    idx={s:i for i,s in enumerate(SLEEVES)}
    def W(d): return {idx[s]:w for s,w in d.items()}
    report={}

    # Anchor-split design: metals_core fraction fA to A, (1-fA) to B.
    # A breadth = crypto + metals_softband + metals_ob_micro (metals-family + liquid crypto)
    # B breadth = fx_jpy + energy_agri + idxrev (the macro/breadth carriers)
    # crypto could go either way; put it with B to balance EV (B otherwise weaker).
    fA = 0.55  # engine slightly favours A
    Aw_base = {'metals_core':fA, 'metals_softband':1.0, 'metals_ob_micro':1.0}
    Bw_base = {'metals_core':1-fA, 'crypto':1.0, 'fx_jpy':1.0, 'energy_agri':1.0, 'idxrev':1.0}

    print(f"Anchor-split: metals_core {fA:.0%}->A / {1-fA:.0%}->B")
    print(f"  A sleeves: {list(Aw_base)}")
    print(f"  B sleeves: {list(Bw_base)}")

    grid=[]
    for sizeA in (0.0075,0.01,0.0125,0.015,0.0175,0.02):
        for sizeB in (0.0075,0.01,0.0125,0.015,0.0175,0.02):
            rb=joint_pass_mc(M,(W(Aw_base),sizeA),(W(Bw_base),sizeB),seed_base=51)
            rs=joint_pass_mc(M_stress,(W(Aw_base),sizeA),(W(Bw_base),sizeB),seed_base=52)
            grid.append(dict(sizeA=sizeA,sizeB=sizeB,
                base_both=rb['p_pass_both'],base_A=rb['p_passA'],base_B=rb['p_passB'],
                daily=max(rb['p_A_fail_daily'],rb['p_B_fail_daily']),
                stress_both=rs['p_pass_both'],stress_A=rs['p_passA'],stress_B=rs['p_passB']))
    report['anchor_fraction_A']=fA; report['A_sleeves']=Aw_base; report['B_sleeves']=Bw_base
    report['grid']=grid
    robust=[g for g in grid if g['base_both']>=0.99 and g['daily']==0 and g['stress_both']>=0.85]
    rec=max(robust,key=lambda g:g['sizeA']+g['sizeB']) if robust else None
    report['recommended']=rec
    print("\nsize grid (base P(both) | stress1.5x P(both) | stress A/B):")
    for g in sorted(grid,key=lambda x:-(x['sizeA']+x['sizeB'])):
        ok=g['base_both']>=0.99 and g['daily']==0 and g['stress_both']>=0.85
        print(f"  A{g['sizeA']*100:.2f}%/B{g['sizeB']*100:.2f}%  base={g['base_both']:.2%}  "
              f"stress={g['stress_both']:.2%} (A{g['stress_A']:.2%}/B{g['stress_B']:.2%}){'  <-ROBUST' if ok else ''}")
    print(f"\nRECOMMENDED anchor-split allocation: {rec}")

    if rec:
        rfwd=joint_pass_mc(M_fwd,(W(Aw_base),rec['sizeA']),(W(Bw_base),rec['sizeB']),seed_base=61)
        report['fwd_validation']=rfwd
        print(f"\nFORWARD 2025-26 @ recommended: P(passA)={rfwd['p_passA']:.3%} P(passB)={rfwd['p_passB']:.3%} "
              f"P(BOTH)={rfwd['p_pass_both']:.3%} | A daily={rfwd['p_A_fail_daily']:.3%} B daily={rfwd['p_B_fail_daily']:.3%}")

    json.dump(report,open(HERE/'KB2_alloc_v2_result.json','w'),indent=1,default=str)
    print("\nwrote KB2_alloc_v2_result.json")

if __name__=='__main__':
    main()
