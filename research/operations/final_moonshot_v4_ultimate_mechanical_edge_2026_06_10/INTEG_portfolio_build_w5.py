"""INTEG_portfolio_build_w5.py — WAVE-5 UPGRADED BOOK ASSEMBLY (the integrator).

Assembles the strongest deployable book from EVERY Wave-4/5 track and re-runs the
diversification-aware challenge-pass MC + 1.5x stress + 2-account allocation, all on
the LOCKED W2 MC engine (TARGET=0.08, MAXDD=0.10, DAILY=0.05, BLOCK=5, N=20000).

INPUTS (each a forward-validated track result, leak-free, real cost, winsor R[-1.3,+5]):
  BASE   W3 8-sleeve book               (INTEG_W3_streams_cache.pkl) — the locked core.
  ADD-A  sub_xvol_pullback   conf 0.45  (substrate cell, metals/energy/index/fx).
  ADD-C  vp_euidx_pocgrav    conf 0.30  (VP POC-gravitation GER40+UK100, dated).
  ADD-D  sub_mid_dn_revert   conf 0.20  (substrate NY mid-vol dn-revert long).
  ADD-B  leadlag_core        conf 0.10  (DEMOTED — dilutive at 0.30; thin breadth only).
  ADD-G  xlayer_veto_gate    conf 0.20  (CROSS-LAYER: xvol_up_pullback long, leader-impulse
                                         VETO ll=none. Highest-odds confluent setup +1.53R.
                                         It is a FILTERED SUBSET of ADD-A, so it is folded
                                         ONLY in the "gate-as-overlay" variant where ADD-A is
                                         REPLACED by the gated subset to avoid double-count.)
  ADD-H  subh4_ll_fx         conf 0.15  (sub-H4 M15 lead-lag, USDJPY->EURJPY london-open core;
                                         train+forward validated, session-open gate load-bearing).

DOCTRINE:
  - No averages as verdicts: per-sleeve TRAIN(<=2024)/FWD(2025-26) + per-year + n + corr.
  - Low corr + +EV is NECESSARY but NOT SUFFICIENT (fold-track learning): every candidate is
    judged by a vol-matched per-sleeve ablation on the 1.5x-stress pass-rate, not just corr.
  - Risk-equivalent comparison: the fair test scales each book's risk by vol_scale so daily std
    == book-only, then the diversification banks as a higher pass-rate FLOOR at no tail cost.
  - Nothing deleted: dilutive sleeves are demoted to thin breadth, not dropped.

DOUBLE-COUNT DISCIPLINE:
  - xlayer_veto_gate is a SUBSET of sub_xvol_pullback (same substrate base, filtered by ll=none).
    We NEVER fold both at full weight. Two clean deploy variants are compared:
      (i)  CLEAN5    = book + xvol(0.45) + vp(0.30) + middn(0.20) + ll(0.10) + subh4(0.15)
      (ii) GATED5    = book + GATE(0.45) + vp(0.30) + middn(0.20) + ll(0.10) + subh4(0.15)
                       (xvol REPLACED by its leader-veto subset, sized up to 0.45)
  - leadlag_core ETH leg held out (crypto double-count).
"""
import sys, json, collections, math, datetime, statistics, pickle
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))

import wave1_structure_setups_ict as w1
import substrate as sub
import SUBSTRATE_corrcheck as SC
import INTEG_portfolio_build as I
import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3
import KB5_fold_new_sleeves as FOLD
import KB5_leadlag_subh4 as SH

def wins(r): return max(-1.3, min(5.0, r))

# ----------------------------------------------------------------------------- #
# NEW SLEEVE GENERATORS (reuse the fold-track generators verbatim where possible)
# ----------------------------------------------------------------------------- #
gen_sub_xvol_pullback = FOLD.gen_sub_xvol_pullback     # ADD-A
gen_vp_euidx_pocgrav  = FOLD.gen_vp_euidx_pocgrav      # ADD-C
gen_sub_mid_dn_revert = FOLD.gen_sub_mid_dn_revert     # ADD-D
gen_leadlag_core      = lambda: FOLD.gen_leadlag_core(include_eth=False)  # ADD-B (ETH held out)

# ADD-G: cross-layer leader-impulse VETO gate on the xvol_up_pullback long.
# Materialize the SAME substrate base as ADD-A, but keep ONLY bars where NO relevant
# cross-asset leader is impulsing (|z|>=1.5). Reuses KB5_cross_layer_miner leak-free tags.
import KB5_cross_layer_miner as XL
def gen_xlayer_veto_gate():
    """xvol_up_pullback long, leader-impulse VETO (ll_impulse=none). Highest-odds setup.
    Universe = same 4-class kept set as ADD-A. Leak-free leader z at same H4 close."""
    syms = [s for s in w1.SYMBOLS if s not in FOLD.DROP_XVOL]
    sigs = XL.build_leader_signals()
    base_conds = dict(vol="xhi", persist="rand", trend="up", mtf="conflict")  # flagship base
    geom = (1.0, 3.0); dmode = 1
    rows = []
    for s in syms:
        built = sub.build_states(s)
        if built is None: continue
        T, B, A, states = built
        cost = w1.cost_for(s); n = len(B)
        rels = XL.relevant_leaders(s)
        for i in range(sub.WARMUP, n - sub.MAXBARS - 1):
            st = states[i]
            if st is None: continue
            co = sub.cell_coords(st)
            if not all(co.get(d) == v for d, v in base_conds.items()): continue
            a = A[i]
            if a <= 0: continue
            t = T[i]
            # leader-impulse VETO: skip if ANY relevant leader is impulsing |z|>=1.5 at this close
            impulsing = False
            for L in rels:
                z = sigs.get(L, {}).get(t)
                if z is not None and abs(z) >= XL.LL_Z:
                    impulsing = True; break
            if impulsing: continue
            R, hit = sub.outcome(B, i, dmode, geom[0], geom[1], a, cost)
            rows.append(dict(sleeve='xlayer_veto_gate', sym=s, date=t.date(), year=t.year, R=wins(R)))
    return rows

# ADD-H: sub-H4 lead-lag FX-train core. USDJPY->EURJPY london-open (train+fwd validated).
# The session-open gate is the load-bearing confluence; leader-vs-self falsification confirmed.
SUBH4_LEGS = [
    # (leader, follower, relsign, look, z, thesis, geom, sess)  — fx_train tier, london_open core
    ("USDJPY", "EURJPY", +1, 16, 2.5, "momentum", "T2.0", "london_open"),
    ("USDJPY", "EURJPY", +1, 16, 2.5, "momentum", "T1.5", "london_open"),
]
def gen_subh4_ll_fx():
    rows = []
    seen = set()
    for (L, F, sgn, look, z, th, gname, sess) in SUBH4_LEGS:
        sig = SH.leader_signal(L, look)
        tr = SH.mine_pair(L, F, sgn, look, z, th, SH.GEOMS[gname], sess=sess, sig=sig)
        for (ts, yr, d, R) in tr:
            key = (F, ts)               # dedupe across the two geoms on the same entry timestamp
            if key in seen: continue
            seen.add(key)
            rows.append(dict(sleeve='subh4_ll_fx', sym=F, date=ts.date(), year=yr, R=wins(R)))
    return rows

NEW_GENS = collections.OrderedDict([
    ('sub_xvol_pullback', gen_sub_xvol_pullback),
    ('vp_euidx_pocgrav',  gen_vp_euidx_pocgrav),
    ('sub_mid_dn_revert', gen_sub_mid_dn_revert),
    ('leadlag_core',      gen_leadlag_core),
    ('xlayer_veto_gate',  gen_xlayer_veto_gate),
    ('subh4_ll_fx',       gen_subh4_ll_fx),
])
# deploy confidence weights for the upgraded book
NEW_CONF = {
    'sub_xvol_pullback': 0.45,
    'vp_euidx_pocgrav':  0.30,
    'sub_mid_dn_revert': 0.20,
    'leadlag_core':      0.10,   # DEMOTED from 0.30 (dilutive); thin breadth only
    'xlayer_veto_gate':  0.45,   # gate replaces xvol in the GATED variant, sized as the flagship
    'subh4_ll_fx':       0.15,
}

# ----------------------------------------------------------------------------- #
def pearson(x, y):
    n = len(x)
    if n < 8: return None
    mx = sum(x)/n; my = sum(y)/n
    sx = sum((a-mx)**2 for a in x); sy = sum((b-my)**2 for b in y)
    if sx == 0 or sy == 0: return 0.0
    return sum((a-mx)*(b-my) for a, b in zip(x, y)) / math.sqrt(sx*sy)

def candidate_daily(rows):
    byday = collections.defaultdict(list)
    for r in rows: byday[r['date']].append(r['R'])
    return {d: sum(v)/len(v) for d, v in byday.items()}

TARGET=I.TARGET; MAXDD=I.MAXDD; DAILY=I.DAILY; BLOCK=I.BLOCK; PATHCAP=I.PATHCAP; N=I.N
mc_series = W2.mc_series
joint_pass_mc = W2.joint_pass_mc

def mc_grid(series, label, stress=False, vol_scale=1.0):
    s = [(v*1.5 if v < 0 else v) for v in series] if stress else series
    out = {}
    for risk in (0.005, 0.0075, 0.01, 0.015, 0.02):
        out[f"{risk*100:.2f}%"] = mc_series(s, risk*vol_scale, seed_base=(999 if stress else 1))
    return out

# ----------------------------------------------------------------------------- #
def main():
    print("=== WAVE-5 UPGRADED BOOK ASSEMBLY ===\n")
    report = {'wave': 5, 'task': 'assemble_upgraded_book', 'new_conf': NEW_CONF}

    # --- existing W3 book daily matrix (the corr baseline) ---
    streams_w3 = pickle.load(open(HERE/'INTEG_W3_streams_cache.pkl', 'rb'))
    days_w3, M_w3 = W3.W2.build_matrix(streams_w3)
    book_sleeves = W3.SLEEVES
    daily_sleeve = {sl: {} for sl in book_sleeves}
    for di, day in enumerate(days_w3):
        for si, sl in enumerate(book_sleeves):
            daily_sleeve[sl][day] = M_w3[di][si]
    comb_book = {day: sum(M_w3[di]) for di, day in enumerate(days_w3)}
    book_days = set(days_w3)
    print(f"existing W3 book: {len(book_sleeves)} sleeves, {len(book_days)} days, ~1512 tr/yr fwd")

    # --- materialize the new sleeves (cache the heavy substrate re-walks) ---
    print("\n--- materializing new/confluence sleeves (leak-free per-day R) ---")
    cache_p = HERE/'INTEG_W5_new_streams_cache.pkl'
    if cache_p.exists():
        new_streams = pickle.load(open(cache_p, 'rb'))
        print(f"  (loaded {len(new_streams)} new sleeve streams from cache)")
    else:
        new_streams = {}
        for name, fn in NEW_GENS.items():
            new_streams[name] = fn()
        pickle.dump(new_streams, open(cache_p, 'wb'))
    for name in NEW_GENS:
        rows = new_streams[name]
        st = I.sleeve_stats(rows)
        py = " ".join(f"{y}:{v[1]:+.2f}(n{v[0]})" for y, v in st['per_year'].items())
        print(f"[{name}] conf={NEW_CONF[name]} n={st['n']} TRAIN n={st['train'][0]} EV={st['train'][1]:+.3f} | "
              f"FWD n={st['fwd'][0]} EV={st['fwd'][1]:+.3f} win={st['fwd'][2]:.0f}% ~{st['fwd_per_year']:.0f}/yr")
        print(f"   per-year: {py}")
        report.setdefault('new_sleeve_stats', {})[name] = st

    # --- TRUE cross-sleeve daily-R correlation vs book + the OTHER new sleeves ---
    print("\n=== CROSS-SLEEVE DAILY-R CORRELATION (new vs book + new-vs-new double-count check) ===")
    report['corr'] = {}
    cand_dailies = {name: candidate_daily(rows) for name, rows in new_streams.items()}
    for name in new_streams:
        cd = cand_dailies[name]; cand_days = set(cd)
        per_sleeve = {}
        for sl in book_sleeves:
            u = sorted(cand_days | set(daily_sleeve[sl]))
            per_sleeve[sl] = pearson([cd.get(d, 0.0) for d in u], [daily_sleeve[sl].get(d, 0.0) for d in u])
        u = sorted(cand_days | book_days)
        vs_comb = pearson([cd.get(d, 0.0) for d in u], [comb_book.get(d, 0.0) for d in u])
        # new-vs-new (double-count radar)
        nvn = {}
        for other in new_streams:
            if other == name: continue
            cdo = cand_dailies[other]
            u2 = sorted(cand_days | set(cdo))
            nvn[other] = pearson([cd.get(d, 0.0) for d in u2], [cdo.get(d, 0.0) for d in u2])
        max_abs = max((abs(v) for v in per_sleeve.values() if v is not None), default=None)
        report['corr'][name] = dict(vs_combined_book=vs_comb, per_sleeve=per_sleeve,
                                    max_abs_sleeve=max_abs, vs_new_sleeves=nvn,
                                    n_cand_days=len(cand_days), n_overlap_book=len(cand_days & book_days))
        top = sorted(((abs(v), s, v) for s, v in {**per_sleeve, **{f"NEW:{k}":val for k,val in nvn.items()}}.items() if v is not None), reverse=True)[:3]
        print(f"  [{name}] vs book={vs_comb:+.4f} max|sleeve|={max_abs:.4f} | top: " +
              ", ".join(f"{s}={v:+.3f}" for _, s, v in top))

    # --- DEPLOY-BOOK VARIANTS (vol-matched, all on same day grid) -------------- #
    sd_book = statistics.pstdev([comb_book[d] for d in days_w3])
    def book_row_sum(day): return comb_book.get(day, 0.0)
    def build_comb(extra_conf, all_days):
        nd = {}
        for nm, cf in extra_conf.items():
            cd = cand_dailies[nm]; nd[nm] = {d: v*cf for d, v in cd.items()}
        return [book_row_sum(d) + sum(nd[nm].get(d, 0.0) for nm in extra_conf) for d in all_days]

    A = NEW_CONF
    CLEAN3 = {'sub_xvol_pullback':A['sub_xvol_pullback'], 'vp_euidx_pocgrav':A['vp_euidx_pocgrav'],
              'sub_mid_dn_revert':A['sub_mid_dn_revert']}
    variants = collections.OrderedDict([
        ('book_only', {}),
        ('clean_3', dict(CLEAN3)),
        ('clean_3+ll010', {**CLEAN3, 'leadlag_core':A['leadlag_core']}),
        ('clean_3+ll010+subh4', {**CLEAN3, 'leadlag_core':A['leadlag_core'], 'subh4_ll_fx':A['subh4_ll_fx']}),
        # GATED: xvol REPLACED by its leader-veto subset (no double-count), + breadth
        ('gated_5', {'xlayer_veto_gate':A['xlayer_veto_gate'], 'vp_euidx_pocgrav':A['vp_euidx_pocgrav'],
                     'sub_mid_dn_revert':A['sub_mid_dn_revert'], 'leadlag_core':A['leadlag_core'],
                     'subh4_ll_fx':A['subh4_ll_fx']}),
        # FULL CLEAN deploy candidate (xvol + breadth + subh4, no gate replacement)
        ('UPGRADED', {**CLEAN3, 'leadlag_core':A['leadlag_core'], 'subh4_ll_fx':A['subh4_ll_fx']}),
    ])

    print(f"\n=== DEPLOY-BOOK SELECTION (vol-matched; book std={sd_book:.4f}) ===")
    print(f"{'variant':>22} {'sharpe':>7} {'volscale':>8} {'P@1%vm':>8} {'P@1.5%vm':>9} {'str@1%':>8} {'str@1.5%':>9} {'newtr/yr':>9}")
    report['deploy_selection'] = {}
    for label, ec in variants.items():
        all_days = sorted(book_days | set().union(*[set(cand_dailies[n]) for n in ec]) if ec else book_days)
        c = build_comb(ec, all_days)
        m = statistics.fmean(c); sd = statistics.pstdev(c); shp = m/sd if sd>0 else 0
        vs = sd_book/sd if sd>0 else 1.0
        cstr = [(v*1.5 if v<0 else v) for v in c]
        p1   = mc_series(c, 0.01*vs, seed_base=1)['p_pass']
        p15  = mc_series(c, 0.015*vs, seed_base=1)['p_pass']
        s1   = mc_series(cstr, 0.01*vs, seed_base=999)['p_pass']
        s15  = mc_series(cstr, 0.015*vs, seed_base=999)['p_pass']
        tot_fwd = sum(I.sleeve_stats(new_streams[n])['fwd_per_year'] for n in ec)
        report['deploy_selection'][label] = dict(
            sharpe=round(shp,4), vol_scale=round(vs,4), daily_mean=round(m,5), daily_std=round(sd,5),
            p_pass_1pct_vm=p1, p_pass_1p5pct_vm=p15, stress_1pct_vm=s1, stress_1p5pct_vm=s15,
            new_fwd_per_year=round(tot_fwd,1), sleeves=list(ec.keys()))
        print(f"{label:>22} {shp:>7.4f} {vs:>8.3f} {p1:>8.2%} {p15:>9.2%} {s1:>8.2%} {s15:>9.2%} {tot_fwd:>9.0f}")

    # --- choose the DEPLOY book = UPGRADED (clean3 + ll010 breadth + subh4) ---
    DEPLOY = variants['UPGRADED']
    deploy_sleeves = list(book_sleeves) + list(DEPLOY.keys())
    deploy_conf = dict(W3.SLEEVE_CONF); deploy_conf.update(DEPLOY)
    all_days = sorted(book_days | set().union(*[set(cand_dailies[n]) for n in DEPLOY]))
    fwd_mask = [d.year >= 2025 for d in all_days]

    # full per-day x per-sleeve matrix for the deploy book (book cols + new cols)
    nd = {nm: {d: v*cf for d, v in cand_dailies[nm].items()} for nm, cf in DEPLOY.items()}
    M_dep = []
    for day in all_days:
        row = [daily_sleeve[sl].get(day, 0.0) for sl in book_sleeves] + [nd[nm].get(day, 0.0) for nm in DEPLOY]
        M_dep.append(row)
    comb_dep = [sum(r) for r in M_dep]
    comb_dep_fwd = [v for v, f in zip(comb_dep, fwd_mask) if f]
    M_dep_fwd = [r for r, f in zip(M_dep, fwd_mask) if f]
    sd_dep = statistics.pstdev(comb_dep); vol_scale = sd_book/sd_dep if sd_dep>0 else 1.0
    report['deploy_book'] = dict(sleeves=deploy_sleeves, conf=deploy_conf,
                                 vol_scale=round(vol_scale,4),
                                 daily_mean=round(statistics.fmean(comb_dep),5), daily_std=round(sd_dep,5),
                                 sharpe=round(statistics.fmean(comb_dep)/sd_dep,4))

    # --- frequency ---
    tot_new_fwd = sum(I.sleeve_stats(new_streams[n])['fwd_per_year'] for n in DEPLOY)
    report['frequency'] = dict(book_fwd_per_year=1512.0, new_fwd_per_year=round(tot_new_fwd,1),
                               upgraded_fwd_per_year=round(1512.0+tot_new_fwd,1))
    print(f"\n=== FREQUENCY ===  book ~1512 + new ~{tot_new_fwd:.0f} = upgraded ~{1512.0+tot_new_fwd:.0f} tr/yr fwd")

    # --- folded correlation matrix ---
    cols = list(zip(*M_dep)); k = len(deploy_sleeves)
    C = [[round(pearson(list(cols[i]), list(cols[j])), 3) for j in range(k)] for i in range(k)]
    offs = [C[i][j] for i in range(k) for j in range(k) if i<j]
    report['deploy_corr_matrix'] = C; report['deploy_sleeve_order'] = deploy_sleeves
    report['deploy_avg_off_diag_corr'] = round(sum(offs)/len(offs),4)
    report['deploy_corr_minmax'] = [round(min(offs),3), round(max(offs),3)]
    print(f"deploy avg off-diag corr {sum(offs)/len(offs):+.4f} (min {min(offs):+.3f} max {max(offs):+.3f})")

    # --- per-sleeve contribution + confidence ---
    contrib = {s: sum(M_dep[d][i] for d in range(len(M_dep))) for i,s in enumerate(deploy_sleeves)}
    tot = sum(contrib.values()); report['sleeve_contribution'] = {}
    print(f"\n=== PER-SLEEVE CONTRIBUTION (conf-wtd unit-R total, share) ===")
    for s in sorted(deploy_sleeves, key=lambda x:-contrib[x]):
        share = 100*contrib[s]/tot if tot else 0
        is_new = s in DEPLOY
        report['sleeve_contribution'][s] = dict(sum=round(contrib[s],3), share_pct=round(share,1),
                                                conf=deploy_conf[s], is_new=is_new)
        print(f"  {s:>18}: {contrib[s]:+8.2f} ({share:+5.1f}%) conf={deploy_conf[s]}{' [NEW]' if is_new else ''}")

    # --- CHALLENGE-PASS MC: deploy vol-matched + raw, all/fwd/stress ---
    print(f"\n=== CHALLENGE-PASS MC ({N} paths; 8%tgt/5%daily/10%maxDD; block={BLOCK}) ===")
    print(f"  vol_scale={vol_scale:.4f} (deploy risk x vol_scale -> daily std == book-only)")
    report['mc_deploy_volmatched_all']    = mc_grid(comb_dep, 'all', vol_scale=vol_scale)
    report['mc_deploy_volmatched_stress'] = mc_grid(comb_dep, 'stress', stress=True, vol_scale=vol_scale)
    report['mc_deploy_raw_all']           = mc_grid(comb_dep, 'all_raw', vol_scale=1.0)
    report['mc_deploy_raw_stress']        = mc_grid(comb_dep, 'stress_raw', stress=True, vol_scale=1.0)
    report['mc_deploy_fwd']               = {f"{r*100:.2f}%": mc_series(comb_dep_fwd, r, seed_base=777)
                                             for r in (0.005,0.0075,0.01,0.015,0.02)}
    report['mc_book_all']    = mc_grid([comb_book.get(d, 0.0) for d in all_days], 'book_all')
    report['mc_book_stress'] = mc_grid([comb_book.get(d, 0.0) for d in all_days], 'book_stress', stress=True)
    print(f"{'risk':>7} {'DEP@vm':>8} {'DEP stress@vm':>13} {'BOOK':>7} {'BOOK stress':>11} {'DEP fwd':>8}")
    for r in (0.005,0.0075,0.01,0.015,0.02):
        kk = f"{r*100:.2f}%"
        print(f"{r*100:>6.2f}% {report['mc_deploy_volmatched_all'][kk]['p_pass']:>8.2%} "
              f"{report['mc_deploy_volmatched_stress'][kk]['p_pass']:>13.2%} "
              f"{report['mc_book_all'][kk]['p_pass']:>7.2%} {report['mc_book_stress'][kk]['p_pass']:>11.2%} "
              f"{report['mc_deploy_fwd'][kk]['p_pass']:>8.2%}")

    # --- per-sleeve vol-matched ablation on the 1.5x-stress pass-rate (the real gate) ---
    print(f"\n=== PER-SLEEVE ABLATION (book + ONE new sleeve, vol-matched, stress@1.5%) ===")
    report['ablation'] = {}
    book_series_full = [comb_book.get(d, 0.0) for d in all_days]
    base_str_15 = mc_series([(v*1.5 if v<0 else v) for v in book_series_full], 0.015, seed_base=999)['p_pass']
    book_shp = statistics.fmean(book_series_full)/statistics.pstdev(book_series_full)
    print(f"  book-only: sharpe={book_shp:.4f} stress@1.5%={base_str_15:.2%}")
    for name in DEPLOY:
        one = [comb_book.get(d,0.0) + nd[name].get(d,0.0) for d in all_days]
        one_s = [(v*1.5 if v<0 else v) for v in one]
        sd1 = statistics.pstdev(one); vs1 = sd_book/sd1 if sd1>0 else 1.0
        shp1 = statistics.fmean(one)/sd1 if sd1>0 else 0
        p_s15 = mc_series(one_s, 0.015*vs1, seed_base=999)['p_pass']
        verdict = 'ADDITIVE' if (shp1 >= book_shp-0.002 and p_s15 >= base_str_15-0.02) else 'dilutive'
        report['ablation'][name] = dict(sharpe=round(shp1,4), vol_scale=round(vs1,4),
                                        stress_1p5pct_vm=p_s15, verdict=verdict)
        print(f"  +{name:>18}: sharpe={shp1:.4f} vm-stress@1.5%={p_s15:.2%} -> {verdict}")

    # --- daily-breach across size grid ---
    print(f"\n=== DAILY-BREACH % (deploy book, worst single day vs -5%) ===")
    report['daily_breach'] = {}
    for r in (0.005,0.0075,0.01,0.015,0.02):
        worst = min(comb_dep)*r
        breach = sum(1 for v in comb_dep if v*r <= -DAILY)/len(comb_dep)
        report['daily_breach'][f"{r*100:.2f}%"] = dict(worst_day_pct=round(worst*100,3), breach_pct=round(breach*100,3))
        print(f"  {r*100:>5.2f}%: worst {worst*100:+.3f}%  breach {breach*100:.3f}%")

    # --- 2-ACCOUNT LIVE ALLOCATION (both trade full deploy book), vol-matched ---
    idx = {s:i for i,s in enumerate(deploy_sleeves)}
    full = {idx[s]:1.0 for s in deploy_sleeves}
    M_stress = [[(v*1.5 if v<0 else v) for v in row] for row in M_dep]
    print(f"\n=== 2-ACCOUNT LIVE ALLOCATION (both trade full deploy book; vol-matched eff sizes) ===")
    report['two_account'] = {}
    for (sA, sB, label) in [(0.0075,0.0075,'balanced_A0.75_B0.75'),
                            (0.01,0.005,'staggered_A1.00_B0.50'),
                            (0.01,0.0075,'staggered_A1.00_B0.75'),
                            (0.005,0.005,'conservative_A0.50_B0.50')]:
        sAe = sA*vol_scale; sBe = sB*vol_scale
        base = joint_pass_mc(M_dep, (full,sAe), (full,sBe), seed_base=7)
        fwd  = joint_pass_mc(M_dep_fwd, (full,sAe), (full,sBe), seed_base=33)
        strs = joint_pass_mc(M_stress, (full,sAe), (full,sBe), seed_base=44)
        rec = dict(sizeA_nominal=sA, sizeB_nominal=sB, sizeA_eff=round(sAe,5), sizeB_eff=round(sBe,5),
                   base_p_both=base['p_pass_both'], fwd_p_both=fwd['p_pass_both'],
                   stress15_p_both=strs['p_pass_both'],
                   daily_breach_max=max(base['p_A_fail_daily'], base['p_B_fail_daily']))
        report['two_account'][label] = rec
        print(f"  {label} (eff A={sAe*100:.2f}% B={sBe*100:.2f}%): P(both)={base['p_pass_both']:.2%} | "
              f"FWD={fwd['p_pass_both']:.2%} | STRESS1.5x={strs['p_pass_both']:.2%} | breach={rec['daily_breach_max']:.2%}")

    # --- highest-odds confluent setups (honest EV/win/n) ---
    report['highest_odds_setups'] = {
        'xlayer_veto_gate_flagship': dict(
            desc='xvol_up_pullback long, leader-impulse VETO (ll=none), 4-class metals/index/energy/fx',
            stat=report['new_sleeve_stats'].get('xlayer_veto_gate')),
        'sub_xvol_pullback': dict(desc='substrate xhi-vol uptrend pullback long (base flagship)',
                                  stat=report['new_sleeve_stats'].get('sub_xvol_pullback')),
        'subh4_ll_fx': dict(desc='M15 USDJPY->EURJPY london-open momentum (sub-H4 lead-lag)',
                            stat=report['new_sleeve_stats'].get('subh4_ll_fx')),
    }

    (HERE/'INTEG_PORTFOLIO_W5_RESULT.json').write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote INTEG_PORTFOLIO_W5_RESULT.json")
    return report

if __name__ == '__main__':
    main()
