"""KB5_fold_new_sleeves.py — INTEGRATOR Wave-5 (track: fold the 4 new Wave-4 sleeves into the book).

Materialize the 4 new Wave-4 sleeves as LEAK-FREE per-day R streams, compute the TRUE
cross-sleeve daily-R correlation vs the existing W3 8-sleeve book, fold the confirmed-additive
(low-corr) ones into the portfolio matrix, and RE-RUN the diversification-aware challenge-pass
MC + 1.5x stress + 2-account allocation.

NEW SLEEVES (from KB4 SUBSTRATE_BUILD.md):
  A sub_xvol_pullback (conf 0.45) — substrate cell, metals/energy/index/fx only (drop crypto+jpy).
  C vp_euidx_pocgrav  (conf 0.30) — VP engine, GER40+UK100 POC-gravitation far>=2.0 vr>=1.2.
  B leadlag_core      (conf 0.30) — leadlag GOLD-tier core (index spillover, US30->USDJPY,
                                    USDJPY->{AUDJPY,GBPJPY} rev); ETH leg held out (double-count watch).
  D sub_mid_dn_revert (conf 0.20) — substrate cell, NY-session mid-vol downtrend reversion long.

Method (every stream leak-free, features index<=i, geometry_lib forward-only labeler, real cost):
  - substrate sleeves : SUBSTRATE_corrcheck.materialize_cell (re-walks leak-free states stride=1).
  - VP sleeve         : VP_confluence gen logic, dated (prior-day volume profile, pessimistic fill).
  - leadlag sleeve    : leadlag.mine_pair per GOLD config (leak-free leader z-impulse, same-close entry).

Corr engine: INTEG_portfolio_build_w3 build_matrix on INTEG_W3_streams_cache.pkl (TRUE per-day
conf-wtd cross-sleeve covariance). New sleeves added as extra matrix columns at their conf, then
the SAME diversification-aware MC (block-bootstrap whole day-rows) + 1.5x left-tail stress.
"""
import sys, json, collections, math, datetime, statistics, random, pickle
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))

import wave1_structure_setups_ict as w1
from geometry_lib import atr14, simulate
import substrate as sub
import SUBSTRATE_corrcheck as SC
import VP_confluence as vc
import volume_profile as vp
import compounding_sleeve as cs
import leadlag as ll
import INTEG_portfolio_build as I            # MC params + sleeve_stats
import INTEG_portfolio_build_w3 as W3        # current book gens/conf (wires W2 machinery)

def wins(r): return max(-1.3, min(5.0, r))

# ----------------------------------------------------------------------------- #
# 1) NEW SLEEVE STREAM GENERATORS — each returns [{sleeve, sym, date, year, R}]
# ----------------------------------------------------------------------------- #

# A. sub_xvol_pullback (conf 0.45): clean 4-class headline — metals/energy/index/fx only.
XVOL_CELL = "g1.0_3.0|dir=1|depth4|vol=xhi|persist=rand|trend=up|mtf=conflict"
# Universe drop crypto + jpy (forward-negative here AND covered by own sleeves).
DROP_XVOL = set(["BTCUSD", "ETHUSD", "DASHUSD", "LTCUSD", "ADAUSD", "DOTUSD", "XTZUSD",
                 "AUDJPY", "CHFJPY", "EURJPY", "GBPJPY", "USDJPY"])
def gen_sub_xvol_pullback():
    syms = [s for s in w1.SYMBOLS if s not in DROP_XVOL]
    rows = SC.materialize_cell(XVOL_CELL, symbols=syms)
    return [dict(sleeve='sub_xvol_pullback', sym=r['sym'], date=r['date'], year=r['year'], R=wins(r['R'])) for r in rows]

# D. sub_mid_dn_revert (conf 0.20): NY mid-vol downtrend reversion long (all classes per KB).
MIDDN_CELL = "g1.0_3.0|dir=1|depth7|vol=mid|trend=dn|mtf=neutral|rngpos=mid|comp=norm|persist=revert|session=ny"
def gen_sub_mid_dn_revert():
    rows = SC.materialize_cell(MIDDN_CELL)
    return [dict(sleeve='sub_mid_dn_revert', sym=r['sym'], date=r['date'], year=r['year'], R=wins(r['R'])) for r in rows]

# C. vp_euidx_pocgrav (conf 0.30): GER40+UK100 POC-gravitation far>=2.0 vr>=1.2, dated.
#    Re-implements VP_confluence.gen_signals poc_grav path but captures the date.
def _vp_pocgrav_rows(sym, far=2.0, vr_min=1.2):
    T, B = w1.load(sym)
    if len(B) < 200: return []
    cost = w1.cost_for(sym); n = len(B)
    atrs = [atr14(B, i) for i in range(n)]
    profs, days = vp.daily_profiles(sym, bin_atr_frac=vc.BIN_FRAC)
    if not days: return []
    fday = days[0]; out = []
    for i in range(101, n - 1):
        a = atrs[i]
        if a <= 0: continue
        t = T[i]
        if t.date() <= fday: continue
        dp = vp.prior_profile_at(profs, days, t)
        if dp is None: continue
        price = B[i].c
        st = vp.nearest_node_state(dp, price, a)
        if st is None: continue
        vr = cs.vol_ratio(atrs, i)
        dpoc = st["d_poc_atr"]
        if abs(dpoc) < far or st["in_va"]: continue
        if vr < vr_min: continue
        d = -1 if dpoc > 0 else 1
        stop_dist = 1.0 * a
        target_dist = abs(price - dp.poc)
        if target_dist < 0.8 * stop_dist: continue
        r = simulate(B, i, d, stop_dist=stop_dist, target_dist=target_dist, maxbars=60, cost=cost)
        out.append(dict(sleeve='vp_euidx_pocgrav', sym=sym, date=t.date(), year=t.year, R=wins(r)))
    return out
def gen_vp_euidx_pocgrav():
    rows = []
    for s in ["GER40", "UK100"]:
        rows += _vp_pocgrav_rows(s, far=2.0, vr_min=1.2)
    return rows

# B. leadlag_core (conf 0.30): GOLD-tier null-clearing core. mine_pair -> (ts, year, dir, R).
#    KB4 Section E defensible core. BTC->ETH held SEPARATE (double-count watch).
LEADLAG_CORE = [
    # (leader, follower, relsign, look, z, thesis, geom, confirm, confirm_sign, regime)
    ("NAS100", "SPX500", +1, 3, 1.5, "momentum", "T1.5", None, None, "align"),
    ("SPX500", "NAS100", +1, 3, 1.5, "momentum", "T2.0", None, None, "align"),
    ("US30_cash", "GER40", +1, 6, 1.5, "momentum", "T1.5", None, None, "align"),
    ("GER40", "UK100", +1, 6, 2.0, "reversion", "T1.5", None, None, None),
    ("SPX500", "GER40", +1, 6, 2.0, "reversion", "T2.0", None, None, None),
    ("US30_cash", "USDJPY", +1, 6, 2.0, "momentum", "T2.0", None, None, None),
    ("USDJPY", "AUDJPY", +1, 6, 2.0, "reversion", "T2.0", None, None, None),
    ("USDJPY", "GBPJPY", +1, 6, 2.0, "reversion", "T1.5", None, None, None),
]
LEADLAG_ETH = ("BTCUSD", "ETHUSD", +1, 12, 1.0, "momentum", "TRAIL", None, None, None)
def _mine_cfg(cfg):
    leader, follower, sign, look, z, thesis, gname, conf, conf_sign, regime = cfg
    geom = ll.GEOMS[gname]
    trades = ll.mine_pair(leader, follower, sign, look, z, thesis, geom,
                          confirm=conf, confirm_sign=conf_sign, regime=regime)
    rows = []
    for (ts, yr, d, R) in trades:
        rows.append(dict(sym=follower, date=ts.date(), year=yr, R=wins(R)))
    return rows
def gen_leadlag_core(include_eth=False):
    rows = []
    for cfg in LEADLAG_CORE:
        for r in _mine_cfg(cfg):
            rows.append(dict(sleeve='leadlag_core', **r))
    if include_eth:
        for r in _mine_cfg(LEADLAG_ETH):
            rows.append(dict(sleeve='leadlag_core', **r))
    return rows

NEW_GENS = {
    'sub_xvol_pullback': gen_sub_xvol_pullback,
    'vp_euidx_pocgrav':  gen_vp_euidx_pocgrav,
    'leadlag_core':      gen_leadlag_core,
    'sub_mid_dn_revert': gen_sub_mid_dn_revert,
}
NEW_CONF = {
    'sub_xvol_pullback': 0.45,
    'vp_euidx_pocgrav':  0.30,
    'leadlag_core':      0.30,
    'sub_mid_dn_revert': 0.20,
}

# ----------------------------------------------------------------------------- #
# 2) corr + sleeve stats helpers
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
    return {d: sum(v)/len(v) for d, v in byday.items()}   # mean R/day (sleeve convention)

# ----------------------------------------------------------------------------- #
# 3) MC engine (reuse W3/W2 machinery wired through INTEG_portfolio_build_w2)
# ----------------------------------------------------------------------------- #
import INTEG_portfolio_build_w2 as W2
TARGET=I.TARGET; MAXDD=I.MAXDD; DAILY=I.DAILY; BLOCK=I.BLOCK; PATHCAP=I.PATHCAP; N=I.N

def mc_series(vals, risk, n_paths=N, seed_base=0):
    return W2.mc_series(vals, risk, n_paths=n_paths, seed_base=seed_base)

def joint_pass_mc(M, accA, accB, n_paths=N, seed_base=0):
    return W2.joint_pass_mc(M, accA, accB, n_paths=n_paths, seed_base=seed_base)

# ----------------------------------------------------------------------------- #
def main():
    print("=== KB5: FOLD 4 NEW WAVE-4 SLEEVES INTO THE BOOK (true-corr MC) ===\n")
    report = {'wave': 5, 'task': 'fold_new_sleeves', 'new_conf': NEW_CONF}

    # --- existing W3 book daily matrix (the corr baseline) ---
    streams_w3 = pickle.load(open(HERE/'INTEG_W3_streams_cache.pkl', 'rb'))
    days_w3, M_w3 = W3.W2.build_matrix(streams_w3)   # W3 wired build_matrix (its sleeves/conf)
    book_sleeves = W3.SLEEVES
    daily_sleeve = {sl: {} for sl in book_sleeves}
    for di, day in enumerate(days_w3):
        for si, sl in enumerate(book_sleeves):
            daily_sleeve[sl][day] = M_w3[di][si]
    comb_book = {day: sum(M_w3[di]) for di, day in enumerate(days_w3)}
    book_days = set(days_w3)
    print(f"existing W3 book: {len(book_sleeves)} sleeves, {len(book_days)} days")

    # --- materialize the 4 new sleeves ---
    print("\n--- materializing new sleeves (leak-free per-day R streams) ---")
    new_streams = {}
    for name, fn in NEW_GENS.items():
        rows = fn()
        new_streams[name] = rows
        st = I.sleeve_stats(rows)
        py = " ".join(f"{y}:{v[1]:+.2f}(n{v[0]})" for y, v in st['per_year'].items())
        print(f"[{name}] conf={NEW_CONF[name]} n={st['n']} TRAIN n={st['train'][0]} EV={st['train'][1]:+.3f} | "
              f"FWD n={st['fwd'][0]} EV={st['fwd'][1]:+.3f} win={st['fwd'][2]:.0f}% ~{st['fwd_per_year']:.0f}/yr fwd")
        print(f"   per-year: {py}")
        report.setdefault('new_sleeve_stats', {})[name] = st

    # leadlag WITH eth (double-count probe only)
    ll_with_eth = gen_leadlag_core(include_eth=True)
    st_eth = I.sleeve_stats(ll_with_eth)
    report['leadlag_with_eth_stats'] = st_eth

    # --- TRUE cross-sleeve daily-R correlation: each new sleeve vs each book sleeve + combined ---
    print("\n=== TRUE CROSS-SLEEVE DAILY-R CORRELATION (new sleeves vs existing W3 book) ===")
    report['corr'] = {}
    for name, rows in new_streams.items():
        cd = candidate_daily(rows)
        cand_days = set(cd)
        per_sleeve_u0 = {}
        for sl in book_sleeves:
            u = sorted(cand_days | set(daily_sleeve[sl]))
            per_sleeve_u0[sl] = pearson([cd.get(d, 0.0) for d in u], [daily_sleeve[sl].get(d, 0.0) for d in u])
        u = sorted(cand_days | book_days)
        vs_comb_u0 = pearson([cd.get(d, 0.0) for d in u], [comb_book.get(d, 0.0) for d in u])
        inter = sorted(cand_days & book_days)
        vs_comb_int = pearson([cd[d] for d in inter], [comb_book[d] for d in inter]) if len(inter) >= 8 else None
        max_abs = max((abs(v) for v in per_sleeve_u0.values() if v is not None), default=None)
        report['corr'][name] = dict(vs_combined_union0=vs_comb_u0, vs_combined_intersect=vs_comb_int,
                                    per_sleeve_union0=per_sleeve_u0, max_abs_sleeve_union0=max_abs,
                                    n_cand_days=len(cand_days), n_overlap_book=len(cand_days & book_days))
        top = sorted(((abs(v), s, v) for s, v in per_sleeve_u0.items() if v is not None), reverse=True)[:3]
        print(f"  [{name}] vs combined: union0={vs_comb_u0:+.4f} intersect={vs_comb_int if vs_comb_int is None else round(vs_comb_int,4)} | "
              f"max|sleeve|={max_abs:.4f}")
        print(f"     top sleeve corrs: " + ", ".join(f"{s}={v:+.3f}" for _, s, v in top))

    # leadlag ETH double-count corr (vs crypto sleeve specifically)
    cd_no = candidate_daily(new_streams['leadlag_core'])
    cd_eth = candidate_daily(ll_with_eth)
    cdays_eth = set(cd_eth)
    u = sorted(cdays_eth | set(daily_sleeve['crypto']))
    ll_eth_vs_crypto = pearson([cd_eth.get(d, 0.0) for d in u], [daily_sleeve['crypto'].get(d, 0.0) for d in u])
    u2 = sorted(set(cd_no) | set(daily_sleeve['crypto']))
    ll_noeth_vs_crypto = pearson([cd_no.get(d, 0.0) for d in u2], [daily_sleeve['crypto'].get(d, 0.0) for d in u2])
    report['leadlag_eth_doublecount'] = dict(
        with_eth_vs_crypto=ll_eth_vs_crypto, no_eth_vs_crypto=ll_noeth_vs_crypto,
        with_eth_fwd_EV=st_eth['fwd'][1], no_eth_fwd_EV=report['new_sleeve_stats']['leadlag_core']['fwd'][1])
    print(f"\n  leadlag ETH double-count: corr(no-eth, crypto)={ll_noeth_vs_crypto:+.4f}  "
          f"corr(with-eth, crypto)={ll_eth_vs_crypto:+.4f}  -> {'ETH leg INFLATES crypto corr; HOLD OUT' if ll_eth_vs_crypto>ll_noeth_vs_crypto+0.01 else 'ETH leg corr ~unchanged'}")

    # --- ADDITIVITY DECISION: low corr (|vs_combined|<0.10) -> additive ---
    CORR_GATE = 0.10
    additive = {}; dropped = {}
    for name in new_streams:
        c = abs(report['corr'][name]['vs_combined_union0'])
        st = report['new_sleeve_stats'][name]
        # additive if low corr AND forward-positive AND 2/2 fwd-year floor (sleeve_stats fwd EV>0)
        ok_corr = c < CORR_GATE
        ok_fwd = st['fwd'][1] > 0
        if ok_corr and ok_fwd:
            additive[name] = NEW_CONF[name]
        else:
            dropped[name] = dict(corr=round(c, 4), fwd_EV=st['fwd'][1],
                                 reason=('corr' if not ok_corr else 'fwd_neg'))
    report['additive_sleeves'] = additive
    report['dropped_sleeves'] = dropped
    print(f"\n=== ADDITIVITY VERDICT (|corr vs book|<{CORR_GATE} AND fwd EV>0) ===")
    print(f"  ADDITIVE -> fold in: {list(additive.keys())}")
    print(f"  DROPPED  : {dropped if dropped else 'none'}")

    # --- BUILD UPGRADED MATRIX: W3 book columns + additive new sleeve columns ---
    folded_sleeves = list(book_sleeves) + list(additive.keys())
    folded_conf = dict(W3.SLEEVE_CONF); folded_conf.update({k: NEW_CONF[k] for k in additive})
    # per-day conf-wtd value for each new sleeve (mean R/day * conf)
    new_daily_conf = {}
    for name in additive:
        cd = candidate_daily(new_streams[name])
        new_daily_conf[name] = {d: v * NEW_CONF[name] for d, v in cd.items()}
    all_days = sorted(book_days | set().union(*[set(new_daily_conf[n]) for n in additive]) if additive else book_days)
    def book_row(day):
        # book sleeve conf-wtd values (0 if absent)
        return [daily_sleeve[sl].get(day, 0.0) for sl in book_sleeves]
    M_folded = []
    for day in all_days:
        row = book_row(day) + [new_daily_conf[n].get(day, 0.0) for n in additive]
        M_folded.append(row)

    # combined daily series (book + new)
    comb_folded = [sum(r) for r in M_folded]
    fwd_mask = [d.year >= 2025 for d in all_days]
    comb_folded_fwd = [v for v, f in zip(comb_folded, fwd_mask) if f]
    M_folded_fwd = [r for r, f in zip(M_folded, fwd_mask) if f]

    # baseline (book-only) combined on the SAME day grid (for apples-to-apples MC)
    comb_book_series = [sum(book_row(day)) for day in all_days]
    comb_book_fwd = [v for v, f in zip(comb_book_series, fwd_mask) if f]

    # frequency
    tot_fwd_new = sum(I.sleeve_stats(new_streams[n])['fwd_per_year'] for n in additive)
    report['frequency'] = dict(
        book_fwd_per_year=1512.0,  # W3 reported
        new_additive_fwd_per_year=round(tot_fwd_new, 1),
        upgraded_fwd_per_year=round(1512.0 + tot_fwd_new, 1))
    print(f"\n=== FREQUENCY ===")
    print(f"  book fwd ~1512/yr  + new additive ~{tot_fwd_new:.0f}/yr  = upgraded ~{1512.0+tot_fwd_new:.0f}/yr")

    # --- correlation matrix of the FOLDED book ---
    cols = list(zip(*M_folded)); k = len(folded_sleeves)
    C = [[round(pearson(list(cols[i]), list(cols[j])), 3) for j in range(k)] for i in range(k)]
    offs = [C[i][j] for i in range(k) for j in range(k) if i < j]
    report['folded_avg_off_diag_corr'] = round(sum(offs)/len(offs), 4)
    report['folded_corr_minmax'] = [round(min(offs), 3), round(max(offs), 3)]
    print(f"\n  folded book avg off-diag corr: {sum(offs)/len(offs):+.4f} (min {min(offs):+.3f} max {max(offs):+.3f})")

    # --- per-sleeve contribution (folded) ---
    contrib = {s: sum(M_folded[d][i] for d in range(len(M_folded))) for i, s in enumerate(folded_sleeves)}
    tot = sum(contrib.values())
    report['sleeve_contribution_folded'] = {}
    print(f"\n=== PER-SLEEVE CONTRIBUTION (folded, conf-wtd unit-R total, share) ===")
    for s in sorted(folded_sleeves, key=lambda k: -contrib[k]):
        share = 100*contrib[s]/tot if tot else 0
        tag = " [NEW]" if s in additive else ""
        report['sleeve_contribution_folded'][s] = dict(sum=round(contrib[s], 3), share_pct=round(share, 1),
                                                       conf=folded_conf[s], is_new=s in additive)
        print(f"  {s:>18}: {contrib[s]:+8.2f} ({share:+.0f}%)  conf={folded_conf[s]}{tag}")

    # --- CHALLENGE-PASS MC: folded vs book-only, all-history + forward + 1.5x stress ---
    print(f"\n=== CHALLENGE-PASS MC ({N} paths; 8% tgt/5% daily/10% maxDD; block={BLOCK}) ===")
    print(f"{'risk':>7} {'P(pass) FOLDED':>15} {'P(pass) BOOK':>13} {'fold fail_dd':>13} {'fold daily':>11} {'med_days':>9}")
    report['mc_folded_all'] = {}; report['mc_book_all'] = {}
    for risk in (0.005, 0.0075, 0.01, 0.015, 0.02):
        rf = mc_series(comb_folded, risk, seed_base=1)
        rb = mc_series(comb_book_series, risk, seed_base=1)
        report['mc_folded_all'][f"{risk*100:.2f}%"] = rf
        report['mc_book_all'][f"{risk*100:.2f}%"] = rb
        print(f"{risk*100:>6.2f}% {rf['p_pass']:>14.2%} {rb['p_pass']:>12.2%} {rf['p_fail_dd']:>13.2%} {rf['p_fail_daily']:>11.2%} {str(rf['med_days_pass']):>9}")

    print(f"\n{'risk':>7} {'P(pass) FWD folded':>19} {'P(pass) FWD book':>17}")
    report['mc_folded_fwd'] = {}; report['mc_book_fwd'] = {}
    for risk in (0.005, 0.0075, 0.01, 0.015, 0.02):
        rf = mc_series(comb_folded_fwd, risk, seed_base=777)
        rb = mc_series(comb_book_fwd, risk, seed_base=777)
        report['mc_folded_fwd'][f"{risk*100:.2f}%"] = rf
        report['mc_book_fwd'][f"{risk*100:.2f}%"] = rb
        print(f"{risk*100:>6.2f}% {rf['p_pass']:>18.2%} {rb['p_pass']:>16.2%}")

    comb_folded_stress = [(v*1.5 if v < 0 else v) for v in comb_folded]
    comb_book_stress = [(v*1.5 if v < 0 else v) for v in comb_book_series]
    print(f"\n{'risk':>7} {'STRESS1.5x FOLDED':>18} {'STRESS1.5x BOOK':>16}  [inflate losing days 1.5x]")
    report['mc_folded_stress_1p5x'] = {}; report['mc_book_stress_1p5x'] = {}
    for risk in (0.005, 0.0075, 0.01, 0.015, 0.02):
        rf = mc_series(comb_folded_stress, risk, seed_base=999)
        rb = mc_series(comb_book_stress, risk, seed_base=999)
        report['mc_folded_stress_1p5x'][f"{risk*100:.2f}%"] = rf
        report['mc_book_stress_1p5x'][f"{risk*100:.2f}%"] = rb
        print(f"{risk*100:>6.2f}% {rf['p_pass']:>17.2%} {rb['p_pass']:>15.2%}")

    # --- VOL-MATCHED (risk-normalized) MC: the FAIR comparison ---------------- #
    # Folding more +EV sleeves makes the book run HOTTER per unit risk (bigger daily
    # std). At equal `risk` the folded book bets bigger => the 1.5x stress (which
    # inflates the now-deeper losing days) looks worse even though the edge is real.
    # The honest test is RISK-EQUIVALENT: scale the folded book's risk DOWN so its
    # daily std matches the book-only daily std, then re-run the same MC + stress.
    sd_book = statistics.pstdev(comb_book_series); sd_fold = statistics.pstdev(comb_folded)
    vol_scale = sd_book / sd_fold if sd_fold > 0 else 1.0
    report['vol_match'] = dict(book_daily_std=round(sd_book, 5), folded_daily_std=round(sd_fold, 5),
                              book_daily_mean=round(statistics.fmean(comb_book_series), 5),
                              folded_daily_mean=round(statistics.fmean(comb_folded), 5),
                              book_sharpe=round(statistics.fmean(comb_book_series)/sd_book, 4),
                              folded_sharpe=round(statistics.fmean(comb_folded)/sd_fold, 4),
                              vol_scale=round(vol_scale, 4))
    print(f"\n=== VOL-MATCHED MC (folded risk x{vol_scale:.3f} so daily std == book) — the FAIR test ===")
    print(f"  book daily: mean={statistics.fmean(comb_book_series):+.5f} std={sd_book:.5f} sharpe={statistics.fmean(comb_book_series)/sd_book:.4f}")
    print(f"  fold daily: mean={statistics.fmean(comb_folded):+.5f} std={sd_fold:.5f} sharpe={statistics.fmean(comb_folded)/sd_fold:.4f}  (vol_scale={vol_scale:.3f})")
    print(f"{'risk':>7} {'FOLDED@volmatch':>16} {'BOOK':>9} {'STRESS fold@vm':>15} {'STRESS book':>12}")
    report['mc_folded_volmatched'] = {}; report['mc_folded_volmatched_stress'] = {}
    for risk in (0.005, 0.0075, 0.01, 0.015, 0.02):
        rfm = mc_series(comb_folded, risk*vol_scale, seed_base=1)
        rb = mc_series(comb_book_series, risk, seed_base=1)
        rfms = mc_series(comb_folded_stress, risk*vol_scale, seed_base=999)
        rbs = mc_series(comb_book_stress, risk, seed_base=999)
        report['mc_folded_volmatched'][f"{risk*100:.2f}%"] = rfm
        report['mc_folded_volmatched_stress'][f"{risk*100:.2f}%"] = rfms
        print(f"{risk*100:>6.2f}% {rfm['p_pass']:>15.2%} {rb['p_pass']:>9.2%} {rfms['p_pass']:>14.2%} {rbs['p_pass']:>12.2%}")

    # --- PER-SLEEVE ABLATION (vol-matched): book + ONE new sleeve at a time ---- #
    # Isolates each sleeve's diversification contribution at risk-equivalence.
    print(f"\n=== PER-SLEEVE ABLATION (book + ONE new sleeve, vol-matched stress P(pass) @1.0%) ===")
    report['ablation_volmatched'] = {}
    base_stress_1pct = mc_series(comb_book_stress, 0.01, seed_base=999)['p_pass']
    print(f"  book-only stress@1.0% = {base_stress_1pct:.2%}")
    for name in additive:
        one = [sum(book_row(d)) + new_daily_conf[name].get(d, 0.0) for d in all_days]
        one_stress = [(v*1.5 if v < 0 else v) for v in one]
        sd_one = statistics.pstdev(one); vs = sd_book/sd_one if sd_one > 0 else 1.0
        shp = statistics.fmean(one)/sd_one if sd_one > 0 else 0.0
        p_vm = mc_series(one, 0.01*vs, seed_base=1)['p_pass']
        p_vm_s = mc_series(one_stress, 0.01*vs, seed_base=999)['p_pass']
        report['ablation_volmatched'][name] = dict(sharpe=round(shp, 4), vol_scale=round(vs, 4),
                                                   p_pass_volmatch=p_vm, stress_p_pass_volmatch=p_vm_s)
        verdict = "ADDITIVE" if shp >= statistics.fmean(comb_book_series)/sd_book - 0.002 else "dilutive"
        print(f"  +{name:>18}: sharpe={shp:.4f} (book {statistics.fmean(comb_book_series)/sd_book:.4f}) "
              f"vm-stress@1%={p_vm_s:.2%}  -> {verdict}")

    # --- daily-breach % ---
    print(f"\n=== DAILY-BREACH % (folded, worst single day vs -5%) ===")
    report['daily_breach_folded'] = {}
    for risk in (0.005, 0.0075, 0.01, 0.015, 0.02):
        worst = min(comb_folded) * risk
        breach = sum(1 for v in comb_folded if v*risk <= -DAILY) / len(comb_folded)
        report['daily_breach_folded'][f"{risk*100:.2f}%"] = dict(worst_day_pct=round(worst*100, 3), breach_pct=round(breach*100, 3))
        print(f"  {risk*100:>5.2f}%: worst day {worst*100:+.3f}%  breach {breach*100:.3f}%")

    # --- 2-ACCOUNT (both trade full folded book), base + fwd + stress ---
    idx = {s: i for i, s in enumerate(folded_sleeves)}
    full = {idx[s]: 1.0 for s in folded_sleeves}
    M_stress = [[(v*1.5 if v < 0 else v) for v in row] for row in M_folded]
    print(f"\n=== 2-ACCOUNT LIVE ALLOCATION (both trade full FOLDED book) ===")
    report['two_account_folded'] = {}
    for (sizeA, sizeB, label) in [(0.0075, 0.0075, 'balanced_A0.75_B0.75'),
                                  (0.01, 0.005, 'staggered_A1.00_B0.50'),
                                  (0.01, 0.0075, 'staggered_A1.00_B0.75'),
                                  (0.005, 0.005, 'conservative_A0.50_B0.50')]:
        base = joint_pass_mc(M_folded, (full, sizeA), (full, sizeB), seed_base=7)
        fwd = joint_pass_mc(M_folded_fwd, (full, sizeA), (full, sizeB), seed_base=33)
        strs = joint_pass_mc(M_stress, (full, sizeA), (full, sizeB), seed_base=44)
        rec = dict(sizeA=sizeA, sizeB=sizeB, base_p_both=base['p_pass_both'],
                   fwd_p_both=fwd['p_pass_both'], stress15_p_both=strs['p_pass_both'],
                   daily_breach_max=max(base['p_A_fail_daily'], base['p_B_fail_daily']))
        report['two_account_folded'][label] = rec
        print(f"  {label}: P(both)={base['p_pass_both']:.2%} | FWD={fwd['p_pass_both']:.2%} | "
              f"STRESS1.5x={strs['p_pass_both']:.2%} | daily-breach={rec['daily_breach_max']:.2%}")

    # --- 2-ACCOUNT VOL-MATCHED: scale folded sizes by vol_scale so per-day risk == book ---
    print(f"\n=== 2-ACCOUNT VOL-MATCHED (folded sizes x{vol_scale:.3f}; per-day risk == book) ===")
    report['two_account_folded_volmatched'] = {}
    for (sizeA, sizeB, label) in [(0.0075, 0.0075, 'balanced_A0.75_B0.75'),
                                  (0.01, 0.005, 'staggered_A1.00_B0.50'),
                                  (0.005, 0.005, 'conservative_A0.50_B0.50')]:
        sA = sizeA*vol_scale; sB = sizeB*vol_scale
        base = joint_pass_mc(M_folded, (full, sA), (full, sB), seed_base=7)
        strs = joint_pass_mc(M_stress, (full, sA), (full, sB), seed_base=44)
        rec = dict(sizeA_eff=round(sA, 5), sizeB_eff=round(sB, 5),
                   base_p_both=base['p_pass_both'], stress15_p_both=strs['p_pass_both'])
        report['two_account_folded_volmatched'][label] = rec
        print(f"  {label} (eff A={sA*100:.2f}% B={sB*100:.2f}%): P(both)={base['p_pass_both']:.2%} | STRESS1.5x={strs['p_pass_both']:.2%}")

    # --- DEPLOY-BOOK SELECTION: the ablation flags leadlag_core as the tail-variance ----
    # injector (vm-stress 82.6% -> 49.4%; sleeve Sharpe 0.119 < book 0.131). Test refined
    # books: (a) the 3 clean additives only, (b) 3 clean + leadlag at reduced breadth conf 0.10.
    # All compared book-only / full-4 / 3-clean / 3+ll010, vol-matched, on the same day grid.
    print(f"\n=== DEPLOY-BOOK SELECTION (vol-matched, all on same day grid) ===")
    CLEAN3 = ['sub_xvol_pullback', 'vp_euidx_pocgrav', 'sub_mid_dn_revert']   # ablation-additive
    def build_comb(extra_conf):
        """extra_conf: {sleeve: conf}. Returns combined daily series over all_days."""
        nd = {}
        for nm, cf in extra_conf.items():
            cd = candidate_daily(new_streams[nm]); nd[nm] = {d: v*cf for d, v in cd.items()}
        return [sum(book_row(d)) + sum(nd[nm].get(d, 0.0) for nm in extra_conf) for d in all_days]
    books = {
        'book_only':   {},
        'full_4':      {n: NEW_CONF[n] for n in additive},
        'clean_3':     {n: NEW_CONF[n] for n in CLEAN3},
        'clean3_ll010':{**{n: NEW_CONF[n] for n in CLEAN3}, 'leadlag_core': 0.10},
    }
    report['deploy_selection'] = {}
    print(f"{'book':>14} {'sharpe':>7} {'volscale':>8} {'P@1%vm':>8} {'stress@1%vm':>11} {'stress@1.5%vm':>13}")
    for label, ec in books.items():
        c = build_comb(ec)
        m = statistics.fmean(c); sd = statistics.pstdev(c); shp = m/sd if sd > 0 else 0
        vs = sd_book/sd if sd > 0 else 1.0
        cs_str = [(v*1.5 if v < 0 else v) for v in c]
        p1 = mc_series(c, 0.01*vs, seed_base=1)['p_pass']
        s1 = mc_series(cs_str, 0.01*vs, seed_base=999)['p_pass']
        s15 = mc_series(cs_str, 0.015*vs, seed_base=999)['p_pass']
        tot_fwd = sum(I.sleeve_stats(new_streams[n])['fwd_per_year'] for n in ec)
        report['deploy_selection'][label] = dict(sharpe=round(shp, 4), vol_scale=round(vs, 4),
            p_pass_1pct_vm=p1, stress_1pct_vm=s1, stress_1p5pct_vm=s15,
            new_fwd_per_year=round(tot_fwd, 1), sleeves=list(ec.keys()))
        print(f"{label:>14} {shp:>7.4f} {vs:>8.3f} {p1:>8.2%} {s1:>11.2%} {s15:>13.2%}  (+{tot_fwd:.0f} new tr/yr)")

    (HERE/'KB5_FOLD_RESULT.json').write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote KB5_FOLD_RESULT.json")
    return report

if __name__ == '__main__':
    main()
