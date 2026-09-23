#!/usr/bin/env python3
import json, math
AR="/private/tmp/attrition-inputs/"  # AI_GATE_AT_DECLARED_FAMILY_V1.json, CANDIDATE_FAMILY_V27.json, LANE_B_FAMILY_TAXONOMY_V1.json extracted from origin/main
fam=json.load(open(AR+'CANDIDATE_FAMILY_V27.json'))['families']['CANDIDATE_BOOK_V1']
members=[m['name'] for m in fam['members']]
tax=json.load(open(AR+'LANE_B_FAMILY_TAXONOMY_V1.json'))
mech={r['name']: r['base_mechanism'] for r in tax['rows']}
ai=json.load(open(AR+'AI_GATE_AT_DECLARED_FAMILY_V1.json'))
P={k:v['p_raw'] for k,v in ai['arms']['CANDIDATE_BOOK_V1@all_declared']['alpha_0.1']['rows'].items() if v['p_raw'] is not None}
pv=sorted(P.values())
CQ=0.0025997400259974   # phase19 CS_CURRENT_BREAKER_RATIFIED_GATE_V1, submitted ALONE

def bh_k(pvals,m,alpha=0.10):
    ps=sorted(pvals); k=0
    for i,p in enumerate(ps,1):
        if p <= i*alpha/m: k=i
    return k
def largest_m_multi(name,alpha=0.10):
    for m in range(200,0,-1):
        k=bh_k(pv,m,alpha)
        if k and P[name] <= sorted(pv)[k-1]: return m
    return 0
def largest_m_solo(p,alpha=0.10): return int(math.floor(alpha/p))

print("LARGEST DECLARED FAMILY AT WHICH EACH CANDIDATE ADMITS, alpha 0.10")
print(f"  sub_xvol_pullback   p {P['sub_xvol_pullback']:.6f}  submitted WITH its 27 siblings -> m <= {largest_m_multi('sub_xvol_pullback')}   ; submitted ALONE (padded gate) -> m <= {largest_m_solo(P['sub_xvol_pullback'])}")
print(f"  mx_btcusd           p {P['mx_btcusd_d1_donchian_20_breakout']:.6f}  with siblings -> m <= {largest_m_multi('mx_btcusd_d1_donchian_20_breakout')}   ; alone -> m <= {largest_m_solo(P['mx_btcusd_d1_donchian_20_breakout'])}")
print(f"  cq inverted breaker p {CQ:.6f}  submitted ALONE (it was) -> m <= {largest_m_solo(CQ)}")

VSR_INDEX=[n for n in members if "volume_surge_reversal" in n and any(s in n for s in
   ("ger40","jp225","nas100","spx500","uk100","us30","eu50","fra40","us100","us500"))]
VSR_ALL=[n for n in members if "volume_surge_reversal" in n]
M1=["mx_btcusd_d1_donchian_20_breakout","mx_ethusd_d1_donchian_20_breakout","vol_compression"]
KZ=[n for n in members if n in ("ny_crypto_momentum","kz_london_crypto_low","ny_index_momentum")]
dups=[d['row'] for d in tax['duplicate_series']]; nolook=[d['row'] for d in tax['no_look_rows']]

def chain(strict=True):
    m=len(members); out=[("declared V27",m)]
    m-=len(dups); out.append(("less 3 exact duplicate series",m))
    m-=len(nolook); out.append(("less 2 rows that produced no look",m))
    m-=len(M1)-1; out.append(("MERGE 1 (crypto D1 channel breakout)",m))
    grp=[n for n in (VSR_INDEX if strict else VSR_ALL) if n not in dups and n not in nolook]
    m-=len(grp)-1; out.append((f"MERGE 2 (index volume surge, {len(grp)} carriers)",m))
    m-=max(0,len(KZ)-1); out.append((f"MERGE 3 (killzone, {len(KZ)} carriers)",m))
    return out
for strict in (True,False):
    print(f"\nMERGE CHAIN — {'strict (index-only volume surge)' if strict else 'broad (all volume-surge rows)'}")
    for lab,m in chain(strict):
        k=bh_k(pv,m); who=sorted(k for k in P if P[k]<=sorted(pv)[k-1]) if k else []
        print(f"  {lab:52s} m={m:3d}  BH rank-1 bar {0.10/m:.6f}  admits(multi) {k}  admits(solo CQ) {'YES' if CQ<=0.10/m else 'no'}")
print(f"\nLane B full mechanism collapse: m={len(set(mech.values()))}  bar {0.10/len(set(mech.values())):.6f}  "
      f"admits(multi) {bh_k(pv,len(set(mech.values())))}  admits(solo CQ) {'YES' if CQ<=0.10/25 else 'no'}")
print(f"\nTHRESHOLD THAT MATTERS: the two best sleeves need m <= {largest_m_multi('mx_btcusd_d1_donchian_20_breakout')}. "
      f"The merges reach m = {chain(True)[-1][1]} (strict) / {chain(False)[-1][1]} (broad). "
      f"Shortfall: {chain(True)[-1][1]-16} / {chain(False)[-1][1]-16} members.")
json.dump(dict(strict_chain=chain(True), broad_chain=chain(False),
  mechanisms=len(set(mech.values())),
  largest_m_sub_xvol_multi=largest_m_multi('sub_xvol_pullback'),
  largest_m_mx_btcusd_multi=largest_m_multi('mx_btcusd_d1_donchian_20_breakout'),
  largest_m_sub_xvol_solo=largest_m_solo(P['sub_xvol_pullback']),
  largest_m_mx_btcusd_solo=largest_m_solo(P['mx_btcusd_d1_donchian_20_breakout']),
  largest_m_cq_solo=largest_m_solo(CQ), p_values=P, cq_p=CQ,
  vsr_index=VSR_INDEX, vsr_all=VSR_ALL, m1=M1, kz=KZ, dups=dups, nolook=nolook),
  open("/private/tmp/MERGE_ARITH_V2.json","w"), indent=1)
