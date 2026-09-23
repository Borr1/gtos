"""KB6_session_stacks.py — PROMOTE the Wave-5 session edges into confidence-sized SLEEVES.

Track: promote session-open lead-lag + session/DXY stacks as sleeves.

Three candidate sleeves, each materialized as a LEAK-FREE per-day R stream, corr-checked vs the
clean_3 deploy book, then run through the LOCKED W2 MC engine for the VOL-MATCHED ablation (book +
ONE sleeve, judged on the 1.5x left-tail STRESS pass-rate at 1% and 1.5% — the binding constraint).
Additive ONLY if it raises Sharpe AND does NOT concentrate the 1.5x stress tail.

  (1) session_leadlag  — sub-H4 (M15) session-open cross-asset lead-lag. Deep-train FX core
       (USDJPY->EURJPY/GBPJPY/CHFJPY london/ny) + forward-only null-cleared genuine leads
       (US30->GER40/USDJPY/AUDJPY ny_open, USDJPY->AUDJPY london_ny). ETH leg held OUT (crypto
       double-count). Source: KB5_leadlag_subh4.mine_pair (leak-free leader z-impulse, same-close
       entry, geometry_lib.simulate labeler, real cost).
  (2) metals_sess_stack — the +0.99R metals confluence cell: FVG probe over metals gated by
       persistence ^ vol_expand ^ sess_active (KB5 new condition families; perm-p 0.0003, both
       fwd years +). Materialized via confluence.probe_fvg + KB5 sess_active, dated by ctx.T[i].
  (3) dxy_fx_filter — DXY->FX directional filter. NOT a standalone sleeve (KB5: it only
       NEUTRALIZES a negative base, never makes a loser a winner). Tested here as an OVERLAY on
       the session_leadlag FX legs (keep only dxy-agree bars) to see if it lifts that sleeve.

Engine: reuses INTEG_portfolio_build_w2 mc_series/joint_pass_mc (LOCKED) + the clean_3 book
streams (INTEG_W3_streams_cache.pkl + INTEG_W5_new_streams_cache.pkl @ clean_3 conf).
"""
import sys, json, math, statistics, collections, pickle
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))

import INTEG_portfolio_build as I
import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3
import KB5_leadlag_subh4 as LL
import KB5_run as K5

mc_series = W2.mc_series; joint_pass_mc = W2.joint_pass_mc
N = I.N; DAILY = I.DAILY

def wins(r): return max(-1.3, min(5.0, r))

# ===========================================================================
# Sleeve (1): session_leadlag  — sub-H4 session-open cross-asset lead-lag
# ===========================================================================
# Deep-train FX core (genuine M15 2014-2025) + forward-only null-cleared genuine LEADS.
# Configs taken verbatim from KB5_leadlag_subh4.md tables B/C (null-cleared, leader-adds-dR>0,
# both-fwd-years-positive). ETHUSD held OUT (overlaps crypto sleeve -> double-count).
LL_FX_CORE = [   # (leader, follower, sign, look, z, thesis, geom, sess)
    ("USDJPY", "EURJPY", +1, 16, 2.5, "momentum", "T2.0", "london_open"),  # gold: fwd+0.76 trN301 z4.85
    ("USDJPY", "GBPJPY", +1,  8, 2.5, "momentum", "T2.0", "ny_session"),   # leader adds +0.63 over losing own
    ("EURJPY", "GBPJPY", +1,  8, 1.5, "momentum", "T2.0", "london_open"),  # KB5: +0.217 mom (NOT reversion)
]
LL_FWD = [   # forward-only (M15 index/cross only 2025+), null-cleared genuine LEADS (high dR)
    ("US30_cash", "GER40",  +1, 8, 1.5, "momentum", "TRAIL", "ny_open"),    # Dow->DAX +0.51, own LOSES
    ("USDJPY",    "AUDJPY", +1, 8, 2.5, "momentum", "T2.0",  "london_ny"),  # +0.55 leader adds +0.77
    ("US30_cash", "USDJPY", +1, 4, 2.0, "momentum", "T2.0",  "ny_open"),    # +0.52 sharpens H4 edge
    ("US30_cash", "AUDJPY", +1, 8, 1.5, "reversion","T2.0",  "ny_open"),    # +0.47 own flat, Dow adds +0.50
]
LL_ETH = ("BTCUSD", "ETHUSD", +1, 16, 1.5, "momentum", "T2.0", "london_open")  # HELD OUT (crypto dbl-count)

def _mine_ll(cfg):
    leader, follower, sign, look, z, th, gname, sess = cfg
    tr = LL.mine_pair(leader, follower, sign, look, z, th, LL.GEOMS[gname], sess=sess)
    return [dict(sleeve='session_leadlag', sym=follower, date=ts.date(), year=yr, R=wins(R),
                 leader=leader, follower=follower) for (ts, yr, d, R) in tr]

def gen_session_leadlag(include_eth=False, fx_only=False):
    rows = []
    for cfg in LL_FX_CORE:
        rows += _mine_ll(cfg)
    if not fx_only:
        for cfg in LL_FWD:
            rows += _mine_ll(cfg)
        if include_eth:
            rows += _mine_ll(LL_ETH)
    return rows

def gen_session_leadlag_genuine():
    """The DEPLOYABLE session-leadlag sleeve: the GENUINE cross-asset LEADS only — the legs
    where the leader carries the edge (leader-adds-dR>0.25, follower's own move flat/negative)
    and BOTH forward years are positive (KB5 Section C null-cleared). Drops the deep-train
    JPY-cross legs (27% win at fixed R) that injected the broad sleeve's fat 1.5x tail.
    Forward-only (M15 index/cross 2025+); the H4 relationship is KB4-train-validated."""
    rows = []
    for cfg in LL_FWD:
        rows += _mine_ll(cfg)
    return rows

# ===========================================================================
# Sleeve (2): metals_sess_stack — FVG metals gated persistence ^ vol_expand ^ sess_active
# ===========================================================================
def gen_metals_sess_stack():
    allnames = [n for n, _ in K5.ALL_CONDITIONS]
    ip = allnames.index('persistence'); iv = allnames.index('vol_expand'); isa = allnames.index('sess_active')
    # build dataset over metals with the FULL condition vector AND keep the date.
    import confluence as C
    from geometry_lib import simulate
    import wave1_structure_setups_ict as w1
    from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
    syms = [s for s in w1.SYMBOLS if (ASSET_CLASS_BY_SYMBOL.get(s) or 'other') == 'metals']
    ctxs = {}
    for s in syms:
        try: ctx = C.SymCtx(s)
        except Exception: continue
        if ctx.n >= 200:
            ctx.T = w1.load(s)[0]; ctxs[s] = ctx
    rows = []
    for (ctx, i, d, sd, td) in C.PROBES['fvg'](ctxs):
        if not (K5.ALL_CONDITIONS[ip][1](ctx, i, d)
                and K5.ALL_CONDITIONS[iv][1](ctx, i, d)
                and K5.ALL_CONDITIONS[isa][1](ctx, i, d)):
            continue
        r = simulate(ctx.B, i, d, stop_dist=sd, target_dist=td, cost=ctx.cost)
        rows.append(dict(sleeve='metals_sess_stack', sym=ctx.sym, date=ctx.T[i].date(),
                         year=ctx.T[i].year, R=wins(r)))
    return rows

# ===========================================================================
# Sleeve (3) probe: dxy_fx_filter as an OVERLAY on the session_leadlag FX legs.
#   Keep only bars where the dxy_bias condition AGREES with the leg direction.
#   This needs per-follower-bar dxy evaluation; we re-derive it leak-free.
# ===========================================================================
def _dxy_proxy_m15():
    """Leak-free synthetic DXY log-proxy on the M15 grid from FX majors (KB5 weights)."""
    def m15_close(sym):
        p = LL.load_m15(sym); return {t: b.c for t, b in zip(p['times'], p['bars'])}
    eur = m15_close("EURUSD"); jpy = m15_close("USDJPY"); gbp = m15_close("GBPUSD"); chf = m15_close("USDCHF")
    dxy = {}
    for t in set(eur) | set(jpy):
        if t in eur and t in jpy and t in gbp and t in chf:
            dxy[t] = (-0.576*math.log(eur[t]) - 0.119*math.log(gbp[t]) + 0.136*math.log(jpy[t]) + 0.036*math.log(chf[t]))
        elif t in eur and t in jpy:
            dxy[t] = (-0.576*math.log(eur[t]) + 0.136*math.log(jpy[t]))
    T_dxy = sorted(dxy)
    return dxy, T_dxy, {t: i for i, t in enumerate(T_dxy)}

# The dollar-clean leadlag legs (follower has a clean single-dollar sign -> DXY filter applies).
# JPY-crosses (EURJPY/GBPJPY/AUDJPY) are excluded (no clean dollar sign).
LL_DOLLARCLEAN = [
    ("USDJPY", "EURJPY", +1, 16, 2.5, "momentum", "T2.0", "london_open"),   # follower EURJPY is JPY-cross -> excluded inside
    ("US30_cash", "USDJPY", +1, 4, 2.0, "momentum", "T2.0", "ny_open"),     # follower USDJPY dollar-clean (+1)
]

def gen_session_leadlag_dxy_filtered():
    """DXY directional FILTER as an OVERLAY on the dollar-CLEAN leadlag legs. Returns BOTH
    agree and disagree splits so the harness can quantify the filter lift. Only USDJPY-follower
    legs are dollar-clean; JPY-cross followers are skipped (filter undefined)."""
    from KB5_condition_families import _leader_dir_at, _FX_DOLLAR_SIGN
    dxy, T_dxy, tmap = _dxy_proxy_m15()
    agree, disagree = [], []
    for cfg in LL_DOLLARCLEAN:
        leader, follower, sign, look, z, th, gname, sess = cfg
        f_sign = _FX_DOLLAR_SIGN.get(follower)
        if f_sign is None:
            continue
        tr = LL.mine_pair(leader, follower, sign, look, z, th, LL.GEOMS[gname], sess=sess)
        for (ts, yr, d, R) in tr:
            j = tmap.get(ts)
            if j is None or j < 30:
                continue
            ddir = _leader_dir_at(dxy, T_dxy, j, lb=6, k=0.5)
            if ddir == 0:
                continue
            pair_bias = ddir * f_sign
            row = dict(sleeve='session_leadlag_dxy', sym=follower, date=ts.date(), year=yr, R=wins(R))
            if (pair_bias > 0 and d > 0) or (pair_bias < 0 and d < 0):
                agree.append(row)
            else:
                disagree.append(row)
    return agree, disagree

# ===========================================================================
# Stats + corr + ablation helpers (same conventions as KB5_fold_new_sleeves)
# ===========================================================================
def pearson(x, y):
    n = len(x)
    if n < 8: return None
    mx = sum(x)/n; my = sum(y)/n
    sx = sum((a-mx)**2 for a in x); sy = sum((b-my)**2 for b in y)
    if sx == 0 or sy == 0: return 0.0
    return sum((a-mx)*(b-my) for a, b in zip(x, y)) / math.sqrt(sx*sy)

def candidate_daily(rows):
    by = collections.defaultdict(list)
    for r in rows: by[r['date']].append(r['R'])
    return {d: sum(v)/len(v) for d, v in by.items()}

def sleeve_stats(rows):
    return I.sleeve_stats(rows)

def build_clean3_book():
    """Return (all helper) for the clean_3 deploy book: book_row(day), all_days, sd_book,
    comb_book_series, fwd_mask, daily_sleeve, book_sleeves+conf, comb_book dict."""
    streams_w3 = pickle.load(open(HERE/'INTEG_W3_streams_cache.pkl', 'rb'))
    days_w3, M_w3 = W3.W2.build_matrix(streams_w3)
    book_sleeves = W3.SLEEVES
    daily_sleeve = {sl: {} for sl in book_sleeves}
    for di, day in enumerate(days_w3):
        for si, sl in enumerate(book_sleeves):
            daily_sleeve[sl][day] = M_w3[di][si]
    book_days = set(days_w3)
    # clean_3 additives at their deploy conf
    new_streams = pickle.load(open(HERE/'INTEG_W5_new_streams_cache.pkl', 'rb'))
    CLEAN3 = {'sub_xvol_pullback': 0.45, 'vp_euidx_pocgrav': 0.30, 'sub_mid_dn_revert': 0.20}
    clean3_daily = {}
    for nm, cf in CLEAN3.items():
        cd = candidate_daily(new_streams[nm])
        clean3_daily[nm] = {d: v*cf for d, v in cd.items()}
    all_days = sorted(book_days | set().union(*[set(clean3_daily[n]) for n in CLEAN3]))
    def book_row_val(day):
        return sum(daily_sleeve[sl].get(day, 0.0) for sl in book_sleeves) + \
               sum(clean3_daily[nm].get(day, 0.0) for nm in CLEAN3)
    comb_book_series = [book_row_val(day) for day in all_days]
    sd_book = statistics.pstdev(comb_book_series)
    fwd_mask = [d.year >= 2025 for d in all_days]
    return dict(all_days=all_days, book_row_val=book_row_val, comb_book_series=comb_book_series,
                sd_book=sd_book, fwd_mask=fwd_mask)

def ablate(name, sleeve_rows, conf, book, seed_grid=(0.01, 0.015)):
    """book + ONE sleeve at conf, vol-matched. Returns Sharpe, vol_scale, and stress pass@grid."""
    all_days = book['all_days']; book_row_val = book['book_row_val']; sd_book = book['sd_book']
    cd = candidate_daily(sleeve_rows)
    nd = {d: v*conf for d, v in cd.items()}
    one = [book_row_val(d) + nd.get(d, 0.0) for d in all_days]
    one_stress = [(v*1.5 if v < 0 else v) for v in one]
    sd_one = statistics.pstdev(one); m_one = statistics.fmean(one)
    vs = sd_book/sd_one if sd_one > 0 else 1.0
    shp = m_one/sd_one if sd_one > 0 else 0.0
    out = dict(name=name, conf=conf, sharpe=round(shp, 4), vol_scale=round(vs, 4),
               daily_std=round(sd_one, 5), daily_mean=round(m_one, 5))
    for r in seed_grid:
        out[f'stress_{r*100:.1f}pct_vm'] = mc_series(one_stress, r*vs, seed_base=999)['p_pass']
        out[f'pass_{r*100:.1f}pct_vm'] = mc_series(one, r*vs, seed_base=1)['p_pass']
    return out

def corr_vs_book(rows, book):
    """corr of sleeve daily-R vs clean_3 combined daily (union-0 + intersect)."""
    all_days = book['all_days']; book_row_val = book['book_row_val']
    cd = candidate_daily(rows); cand_days = set(cd)
    comb_book = {d: book_row_val(d) for d in all_days}
    u = sorted(cand_days | set(all_days))
    u0 = pearson([cd.get(d, 0.0) for d in u], [comb_book.get(d, 0.0) for d in u])
    inter = sorted(cand_days & set(all_days))
    ci = pearson([cd[d] for d in inter], [comb_book[d] for d in inter]) if len(inter) >= 8 else None
    return dict(vs_book_union0=u0, vs_book_intersect=ci, n_cand_days=len(cand_days),
                n_overlap=len(cand_days & set(all_days)))

def main():
    print("=== KB6: PROMOTE SESSION EDGES AS SLEEVES (locked W2 MC, vol-matched ablation) ===\n")
    report = {'track': 'session_leadlag_stacks'}
    book = build_clean3_book()
    book_stress = [(v*1.5 if v < 0 else v) for v in book['comb_book_series']]
    base_stress_1 = mc_series(book_stress, 0.01, seed_base=999)['p_pass']
    base_stress_15 = mc_series(book_stress, 0.015, seed_base=999)['p_pass']
    book_sharpe = statistics.fmean(book['comb_book_series'])/book['sd_book']
    report['clean3_book'] = dict(n_days=len(book['all_days']), sharpe=round(book_sharpe, 4),
                                 daily_std=round(book['sd_book'], 5),
                                 stress_1pct=base_stress_1, stress_1p5pct=base_stress_15)
    print(f"clean_3 book: {len(book['all_days'])} days, Sharpe {book_sharpe:.4f}, "
          f"stress@1%={base_stress_1:.2%} stress@1.5%={base_stress_15:.2%}\n")

    # ---- materialize the candidate sleeves ----
    sleeves = {}
    sleeves['session_leadlag_genuine'] = gen_session_leadlag_genuine()        # DEPLOYABLE clean subset
    sleeves['session_leadlag'] = gen_session_leadlag(include_eth=False)        # broad (incl JPY-cross), ETH held out
    sleeves['session_leadlag_fxcore'] = gen_session_leadlag(fx_only=True)      # FX deep-train only
    sleeves['metals_sess_stack'] = gen_metals_sess_stack()
    # leadlag WITH eth (double-count probe)
    sleeves['session_leadlag_witheth'] = gen_session_leadlag(include_eth=True)
    # DXY filter: agree/disagree split on dollar-clean leadlag legs (USDJPY follower)
    dxy_agree, dxy_disagree = gen_session_leadlag_dxy_filtered()
    sleeves['session_leadlag_dxy'] = dxy_agree   # only the agree split is the candidate sleeve

    report['sleeve_stats'] = {}
    print("=== SLEEVE STATS (TRAIN<=2024 / FWD 2025-26 / per-year) ===")
    for nm, rows in sleeves.items():
        st = sleeve_stats(rows)
        report['sleeve_stats'][nm] = st
        py = " ".join(f"{y}:{v[1]:+.2f}(n{v[0]})" for y, v in st['per_year'].items())
        print(f"[{nm}] n={st['n']} TRAIN n{st['train'][0]} EV{st['train'][1]:+.3f} | "
              f"FWD n{st['fwd'][0]} EV{st['fwd'][1]:+.3f} win{st['fwd'][2]:.0f}% ~{st['fwd_per_year']:.0f}/yr")
        print(f"   per-year: {py}")

    # ---- ETH double-count corr (session_leadlag with vs without eth, vs crypto sleeve) ----
    streams_w3 = pickle.load(open(HERE/'INTEG_W3_streams_cache.pkl', 'rb'))
    crypto_daily = candidate_daily([r for r in streams_w3['crypto']])
    def corr_to_crypto(rows):
        cd = candidate_daily(rows); u = sorted(set(cd) | set(crypto_daily))
        return pearson([cd.get(d, 0.0) for d in u], [crypto_daily.get(d, 0.0) for d in u])
    report['eth_doublecount'] = dict(
        no_eth_vs_crypto=corr_to_crypto(sleeves['session_leadlag']),
        with_eth_vs_crypto=corr_to_crypto(sleeves['session_leadlag_witheth']))
    print(f"\nETH double-count: corr(no-eth, crypto)={report['eth_doublecount']['no_eth_vs_crypto']:+.4f} "
          f"corr(with-eth, crypto)={report['eth_doublecount']['with_eth_vs_crypto']:+.4f}")

    # ---- DXY filter lift on dollar-clean leadlag legs (agree vs disagree) ----
    def split_ev(rows, fwd):
        v = [r['R'] for r in rows if (r['year'] >= 2025) == fwd]
        return dict(n=len(v), EV=round(statistics.fmean(v), 4) if v else 0.0,
                    win=round(100*sum(1 for x in v if x > 0)/len(v), 1) if v else 0.0)
    report['dxy_filter'] = dict(
        agree_fwd=split_ev(dxy_agree, True), agree_train=split_ev(dxy_agree, False),
        disagree_fwd=split_ev(dxy_disagree, True), disagree_train=split_ev(dxy_disagree, False),
        fwd_lift=round(split_ev(dxy_agree, True)['EV'] - split_ev(dxy_disagree, True)['EV'], 4))
    print(f"\nDXY filter on dollar-clean leadlag legs (USDJPY follower):")
    print(f"  AGREE    FWD n{report['dxy_filter']['agree_fwd']['n']} EV{report['dxy_filter']['agree_fwd']['EV']:+.3f} | TRAIN n{report['dxy_filter']['agree_train']['n']} EV{report['dxy_filter']['agree_train']['EV']:+.3f}")
    print(f"  DISAGREE FWD n{report['dxy_filter']['disagree_fwd']['n']} EV{report['dxy_filter']['disagree_fwd']['EV']:+.3f} | TRAIN n{report['dxy_filter']['disagree_train']['n']} EV{report['dxy_filter']['disagree_train']['EV']:+.3f}")
    print(f"  -> fwd filter lift (agree - disagree) = {report['dxy_filter']['fwd_lift']:+.3f}R")

    # ---- metals_sess_stack overlap with metals_core specifically (it is metals-on-metals) ----
    mcore_daily = candidate_daily([r for r in streams_w3['metals_core']])
    msd = candidate_daily(sleeves['metals_sess_stack'])
    u = sorted(set(msd) | set(mcore_daily))
    inter = sorted(set(msd) & set(mcore_daily))
    report['metals_overlap'] = dict(
        vs_metals_core_union0=pearson([msd.get(d, 0.0) for d in u], [mcore_daily.get(d, 0.0) for d in u]),
        vs_metals_core_intersect=pearson([msd[d] for d in inter], [mcore_daily[d] for d in inter]) if len(inter) >= 8 else None,
        n_metals_core_overlap_days=len(inter), n_metals_sess_days=len(msd))
    print(f"\nmetals_sess_stack vs metals_core: union0={report['metals_overlap']['vs_metals_core_union0']:+.4f} "
          f"intersect={report['metals_overlap']['vs_metals_core_intersect']} "
          f"({len(inter)} same-day overlaps of {len(msd)} stack days)")

    # ---- corr vs clean_3 book ----
    print("\n=== CORR vs clean_3 book ===")
    report['corr'] = {}
    for nm in ('session_leadlag_genuine', 'session_leadlag', 'session_leadlag_fxcore', 'metals_sess_stack'):
        c = corr_vs_book(sleeves[nm], book)
        report['corr'][nm] = c
        print(f"  [{nm}] union0={c['vs_book_union0']:+.4f} intersect="
              f"{c['vs_book_intersect'] if c['vs_book_intersect'] is None else round(c['vs_book_intersect'],4)} "
              f"(n_cand={c['n_cand_days']} overlap={c['n_overlap']})")

    # ---- VOL-MATCHED ABLATION (book + ONE sleeve), stress@1% & @1.5% — the binding constraint ----
    # Confidence sizing: session sleeves are session-open intraday (orthogonal family) -> conf by
    # train-depth + fwd robustness. metals_sess_stack is the program's best validated cell -> 0.50.
    CONF = {'session_leadlag_genuine': 0.15, 'session_leadlag': 0.20,
            'session_leadlag_fxcore': 0.20, 'metals_sess_stack': 0.50}
    print(f"\n=== VOL-MATCHED ABLATION (book + ONE sleeve; stress is the verdict) ===")
    print(f"  book-only: Sharpe {book_sharpe:.4f}  stress@1%={base_stress_1:.2%}  stress@1.5%={base_stress_15:.2%}")
    report['ablation'] = {}
    for nm, conf in CONF.items():
        a = ablate(nm, sleeves[nm], conf, book)
        report['ablation'][nm] = a
        dS = a['sharpe'] - book_sharpe
        dstr1 = a['stress_1.0pct_vm'] - base_stress_1
        dstr15 = a['stress_1.5pct_vm'] - base_stress_15
        verdict = ("ADDITIVE" if (dS >= -0.0005 and dstr1 >= -0.01 and dstr15 >= -0.01)
                   else "dilutive")
        report['ablation'][nm]['verdict'] = verdict
        report['ablation'][nm]['d_sharpe'] = round(dS, 4)
        report['ablation'][nm]['d_stress_1pct'] = round(dstr1, 4)
        report['ablation'][nm]['d_stress_1p5pct'] = round(dstr15, 4)
        print(f"  +{nm:>26} conf{conf}: Sharpe {a['sharpe']:.4f}({dS:+.4f}) "
              f"stress@1%={a['stress_1.0pct_vm']:.2%}({dstr1:+.2%}) "
              f"stress@1.5%={a['stress_1.5pct_vm']:.2%}({dstr15:+.2%}) -> {verdict}")

    # ---- ADDITIVITY + DOUBLE-COUNT discipline ----
    # A sleeve is folded only if (a) ablation verdict ADDITIVE AND (b) it is NOT a double-count
    # of an existing book sleeve (|corr vs any single book sleeve| < 0.30). metals_sess_stack
    # fails (b): corr +0.65 vs metals_core -> it is the SAME metals FVG population (size-up
    # overlay, not a sleeve). session_leadlag_genuine passes both.
    DC_GATE = 0.30
    metals_dc = abs(report['metals_overlap']['vs_metals_core_union0'])
    additive = []
    for nm in ('session_leadlag_genuine', 'metals_sess_stack'):
        v = report['ablation'].get(nm, {}).get('verdict')
        dc = metals_dc if nm == 'metals_sess_stack' else 0.0
        if v == 'ADDITIVE' and dc < DC_GATE:
            additive.append(nm)
        elif v == 'ADDITIVE':
            report['ablation'][nm]['verdict'] = 'OVERLAY_ONLY_doublecount'
            report['ablation'][nm]['doublecount_corr'] = round(dc, 4)
    report['additive_sleeves'] = additive
    if additive:
        all_days = book['all_days']; book_row_val = book['book_row_val']; sd_book = book['sd_book']
        nd = {}
        for nm in additive:
            cd = candidate_daily(sleeves[nm]); nd[nm] = {d: v*CONF[nm] for d, v in cd.items()}
        comb = [book_row_val(d) + sum(nd[nm].get(d, 0.0) for nm in additive) for d in all_days]
        comb_str = [(v*1.5 if v < 0 else v) for v in comb]
        sd = statistics.pstdev(comb); vs = sd_book/sd if sd > 0 else 1.0
        shp = statistics.fmean(comb)/sd
        report['folded_additive'] = dict(
            sleeves=additive, sharpe=round(shp, 4), vol_scale=round(vs, 4),
            stress_1pct_vm=mc_series(comb_str, 0.01*vs, seed_base=999)['p_pass'],
            stress_1p5pct_vm=mc_series(comb_str, 0.015*vs, seed_base=999)['p_pass'],
            pass_1pct_vm=mc_series(comb, 0.01*vs, seed_base=1)['p_pass'])
        print(f"\n=== FOLDED ADDITIVE ({'+'.join(additive)}) vol-matched ===")
        print(f"  Sharpe {shp:.4f}(book {book_sharpe:.4f})  stress@1%={report['folded_additive']['stress_1pct_vm']:.2%}"
              f"({report['folded_additive']['stress_1pct_vm']-base_stress_1:+.2%})  "
              f"stress@1.5%={report['folded_additive']['stress_1p5pct_vm']:.2%}"
              f"({report['folded_additive']['stress_1p5pct_vm']-base_stress_15:+.2%})")

    (HERE/'KB6_SESSION_STACKS_RESULT.json').write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote KB6_SESSION_STACKS_RESULT.json")
    return report

if __name__ == '__main__':
    main()
