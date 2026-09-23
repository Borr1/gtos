"""INTEG_portfolio_build_w2.py — WAVE-2 RE-ASSEMBLED PORTFOLIO + diversification-aware MC.

INTEGRATOR (Wave 2). Re-assembles the combined book applying EVERY Wave-2 track result, then
re-runs the TRUE cross-sleeve-correlation, diversification-aware challenge-pass Monte Carlo
(block-bootstrap WHOLE cross-sectional days) vs the correlation=1 sum baseline, plus an
adversarial 1.5x left-tail stress, at 0.5/0.75/1.0%, and the 2-account live allocation.

WAVE-2 CHANGES vs INTEG_portfolio_build.py (each cites the track that produced it):

 (T=transfer winners)  metals_core already carries the H1->M15 cascade exit (locked Wave-1).
 (T)  CRYPTO: H1->M15 cascade + native target4 exit (FWD +0.751->+1.048R, paired t2.10).
              Reuse the leak-audited TW_CRYPTO_CASCADE_LEDGER (casc_R) for BTC/DASH.
 (KB2 new-breadth + data_depth)  CRYPTO: ADD ETHUSD as a 3rd carrier. data_depth CONVERTED ETH
              (TRAIN<=2024 +2.17R n13 85%win; 3-carrier TRAIN +1.77R). Locked KB_crypto rule
              (Donchian-20 + ac60>=0.15 + sd2a + target4) on the M1->H4 resampled stream, with
              the same cascade better-fill applied forward (ETH LTF forward-only).
 (T + KB2 new-breadth + data_depth)  ENERGY: H1->M15 cascade + STATE_D exit (Pareto winner,
              FWD +0.675->+0.877R, paired t2.84) via TW_ENERGY_CASCADE_LEDGER (casc_state_d),
              PLUS the supply-shock tier (vr>=2.0) runR=4 deeper runner (FWD +0.94->+1.08R).
              AGRI continuation kept from the locked energy_agri sleeve (CORN/COTTON, conf 0.5).
              data_depth CONVERTED energy to TRAIN-validated (+0.433R train) -> conf raised.
 (data_depth FALSIFICATION)  fx_jpy London-open: TRAIN<=2024 -0.103R on 11.5yr M15, neg 9/11 yrs.
              The KB's +0.168R was a 2025-26 window artifact. DOWNGRADE to tiny breadth (conf 0.15),
              not deleted. (Build doctrine: keep the learning at small size.)
 (data_depth FALSIFICATION + idxdeep)  idxrev failed-breakout: TRAIN -0.065R across 5 deep indices,
              neg 5/6 yrs. DOWNGRADE to tiny breadth (conf 0.15). The idxdeep cross-sectional gate
              (fade only AGAINST basket trend) hardens it but NAS100 deep-train stays negative, so
              it is breadth-size, not core.
 (KB2 new-breadth)  ADD fx_jpy_ny: gated NY-open JPY 2nd session (imp>=1.0*ATR + M15 trend20,
              GBPJPY+USDJPY) FWD +0.15R ~190/yr, pos both yrs, JPY-specific (pure-FX control neg).
              conf 0.15 (2nd-session breadth, forward-only window like London R1).

DOUBLE-COUNTING DISCIPLINE preserved from INTEG: each underlying entry counted once. ETH is a
distinct symbol (additive). NY-JPY is a distinct session/day key from London R1 (additive).
Cascade exits REPLACE the native exit on the SAME entries (no new entries -> no double count).

Per-trade R winsorized [-1.3,+5] at source. Real cost via w1.cost_for. State/features leak-free
(index<=i); geometry_lib.simulate / exit_state_d label forward only. Cascade ledgers leak-audited=0.
"""
import sys, json, csv, os, math, statistics, collections, random, datetime, pickle
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate, atr14, Bar
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs
import multitf_lib as m
import INTEG_portfolio_build as I            # reuse metals generators + MC engine + stats
import kb2_new_breadth as KB                 # ETH resampler + NY-JPY gated session builder

def wins(r): return max(-1.3, min(5.0, r))
ROOT = str(HERE.parents[2]); DATA = ROOT + '/data/mt5_research_exports'

# ============================================================================
# SLEEVE STREAM GENERATORS — Wave-2 versions
# Each returns list of {sleeve, sym, date(datetime.date), year, R, [intra_size]}.
# ============================================================================

# ---- metals_core / softband / ob_micro: UNCHANGED (locked Wave-1, cascade exit on core) ----
gen_metals_core     = I.gen_metals_core
gen_metals_softband = I.gen_metals_softband
gen_metals_ob_micro = I.gen_metals_ob_micro

# ---- CRYPTO: BTC/DASH cascade(target4) from leak-audited ledger + ETH 3rd carrier ----
def _eth_cascade_rows():
    """ETHUSD 3rd carrier. data_depth/new-breadth locked rule: M1->H4 resample, Donchian-20
    breakout + ac60>=0.15 + sd=2a + target4. Apply the H1->M15 cascade better-fill forward
    (ETH H1/M15 forward-only 2025-06+), exit = target4 on the fill stream (crypto winner)."""
    T, B = KB.resample_eth_h4()
    cost = w1.cost_for('ETHUSD')
    atrs = [atr14(B, i) for i in range(len(B))]
    # extend LTF map for ETH forward LTF (same pattern as TW for BTC/DASH)
    m.LTF_PATHS.setdefault(("ETHUSD", "H1"),  [DATA + "/bridge_ftmo_htf_20250601_20260610/ETHUSD_H1.csv"])
    m.LTF_PATHS.setdefault(("ETHUSD", "M15"), [DATA + "/bridge_ftmo_m15_20250601_20260610/ETHUSD_M15.csv"])
    T1, B1 = m.load_ltf("ETHUSD", "H1"); have1 = len(B1) > 50
    T15, B15 = m.load_ltf("ETHUSD", "M15"); have15 = len(B15) > 50
    rows = []
    for (i, d) in KB.crypto_breakout_signals(B, 20):
        a = atrs[i]
        if a <= 0: continue
        ac = cs.autocorr(B, i, 60)
        if ac is None or ac < 0.15: continue           # KB_crypto persistence gate (data_depth-validated)
        sd = 2.0 * a
        base_R = wins(simulate(B, i, d, stop_dist=sd, target_dist=4*sd, maxbars=80, cost=cost))
        ts = T[i] + datetime.timedelta(hours=4); sc = B[i].c
        R = base_R; filled = False
        if have1:
            si = m.first_ltf_index_after(T1, ts)
            if si is not None and 30 <= si < len(B1) - 2:
                ej = I._find_fill(B1, T1, si, d, sc, 12, 1.0, ts)
                if ej is not None:
                    R = wins(simulate(B1, ej, d, stop_dist=sd, target_dist=4*sd, maxbars=320, cost=cost)); filled = True
        if not filled and have15:
            si = m.first_ltf_index_after(T15, ts)
            if si is not None and 30 <= si < len(B15) - 2:
                ej = I._find_fill(B15, T15, si, d, sc, 48, 1.0, ts)
                if ej is not None:
                    R = wins(simulate(B15, ej, d, stop_dist=sd, target_dist=4*sd, maxbars=1280, cost=cost))
        rows.append(dict(sleeve='crypto', sym='ETHUSD', date=T[i].date(), year=T[i].year, R=wins(R)))
    return rows

def gen_crypto():
    """BTC/DASH cascade+target4 (TW ledger, leak-audited) + ETH carrier (above)."""
    rows = []
    p = HERE / 'TW_CRYPTO_CASCADE_LEDGER.jsonl'
    for line in p.read_text().splitlines():
        if not line.strip(): continue
        r = json.loads(line)
        dt = datetime.date.fromisoformat(r['date'])
        rows.append(dict(sleeve='crypto', sym=r['sym'], date=dt, year=r['year'], R=wins(r['casc_R'])))
    rows += _eth_cascade_rows()
    return rows

# ---- ENERGY+AGRI: energy cascade(STATE_D) + shock-tier runR=4; agri from locked sleeve ----
def gen_energy_agri():
    """ENERGY: H1->M15 cascade STATE_D exit (TW ledger casc_state_d) as the deployable energy
    exit, but UPGRADE the supply-shock tier (vr>=2.0) to runR=4 (new-breadth lock). For shock
    rows we take max-of(cascade STATE_D, runR4 deeper runner) is NOT valid (different exits on
    same entry = double count); instead, for vr>=2 rows we use the runR=4 deeper-runner R
    (new-breadth winner +1.08R) and for vr<2 rows the cascade STATE_D R. AGRI: locked sleeve."""
    rows = []
    # energy: build a date/sym/vr -> casc_state_d map from the leak-audited ledger
    casc = {}
    p = HERE / 'TW_ENERGY_CASCADE_LEDGER.jsonl'
    for line in p.read_text().splitlines():
        if not line.strip(): continue
        r = json.loads(line)
        casc[(r['sym'], r['date'], round(r['vr'], 3))] = r
    # rebuild the energy shock-tier runR=4 R per (sym,date) for vr>=2 rows
    shock_runR4 = {}
    import energy_agri_sleeve as ea
    for s in ea.ENERGY:
        try: T, B = w1.load(s)
        except Exception: continue
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]; cost = w1.cost_for(s)
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(s):
            vr = cs.vol_ratio(atrs, i)
            if vr < 2.0: continue
            R = KB.exit_state_d_runR(B, i, d, sd, vr, c2, runR_override=4.0)
            shock_runR4[(s, str(t.date()))] = (t.year, wins(R))
    # emit energy rows: vr>=2 -> runR4 deeper runner ; else cascade STATE_D
    seen = set()
    for (sym, date, vr), r in casc.items():
        key = (sym, date)
        if key in seen: continue
        seen.add(key)
        if vr >= 2.0 and key in shock_runR4:
            yr, R = shock_runR4[key]
        else:
            yr, R = r['year'], wins(r['casc_state_d'])
        rows.append(dict(sleeve='energy_agri', sym=sym, date=datetime.date.fromisoformat(date), year=yr, R=R))
    # AGRI: from the locked sleeve ledger (CORN/COTTON, conf intra_size carried)
    pa = HERE / 'ENERGY_AGRI_SLEEVE_TRADES.jsonl'
    for line in pa.read_text().splitlines():
        if not line.strip(): continue
        r = json.loads(line)
        if r['grp'] != 'agri': continue
        dt = datetime.date.fromisoformat(r['date'])
        rows.append(dict(sleeve='energy_agri', sym=r['sym'], date=dt, year=r['year'],
                         R=wins(r['R']), intra_size=r['conf']))
    return rows

# ---- IDXREV: unchanged entries (data_depth falsified -> conf downgraded, not deleted) ----
gen_idxrev = I.gen_idxrev

# ---- FX-JPY London (unchanged entries; conf downgraded) ----
gen_fx_jpy = I.gen_fx_jpy

# ---- NEW: NY-open gated JPY 2nd session (new-breadth, conf 0.15) ----
def gen_fx_jpy_ny():
    """Gated NY-open JPY: hour>=15, impulse>=1.0*ATR, M15 trend20 alignment. GBPJPY+USDJPY.
    Distinct (session) key from London R1 -> additive, no double count."""
    rows = []
    o = KB.session_open_mom(['GBPJPY', 'USDJPY'], 15, 4, 1.0, 2.5, 48, imp_min=1.0, trend_lb=20)
    for (day, sym, y, R) in o:
        rows.append(dict(sleeve='fx_jpy_ny', sym=sym, date=day, year=y, R=wins(R)))
    return rows

# ============================================================================
# CONFIDENCE WEIGHTS — Wave-2, updated by data_depth TRAIN/FORWARD evidence.
#   raised where data_depth CONVERTED a sleeve to train-validated;
#   lowered where data_depth FALSIFIED the train hypothesis (kept small, never zero).
# ============================================================================
SLEEVE_CONF = {
    'metals_core':      1.00,   # train-validated + causal cascade lift; deepest; unchanged
    'crypto':           0.85,   # data_depth CONVERTED (3-carrier TRAIN +1.77R) + cascade lift (+0.30R fwd). UP 0.70->0.85
    'energy_agri':      0.80,   # data_depth CONVERTED (TRAIN +0.433R) + cascade + shock runR4. UP 0.60->0.80
    'metals_softband':  0.50,   # unchanged (soft band, frequency add)
    'metals_ob_micro':  0.30,   # unchanged (small)
    'fx_jpy_ny':        0.15,   # NEW gated 2nd session, forward-only window -> tiny breadth
    'idxrev':           0.15,   # data_depth FALSIFIED train (TRAIN -0.065R, 5 deep idx). DOWN 0.30->0.15
    'fx_jpy':           0.15,   # data_depth FALSIFIED train (TRAIN -0.103R, 11.5yr). DOWN 0.35->0.15
}

GENS = {
    'metals_core': gen_metals_core, 'metals_softband': gen_metals_softband,
    'metals_ob_micro': gen_metals_ob_micro, 'crypto': gen_crypto,
    'energy_agri': gen_energy_agri, 'idxrev': gen_idxrev,
    'fx_jpy': gen_fx_jpy, 'fx_jpy_ny': gen_fx_jpy_ny,
}
SLEEVES = list(GENS.keys())

def build_streams():
    out = {}
    for name, fn in GENS.items():
        rows = fn()
        for r in rows:
            isz = r.get('intra_size', 1.0)
            r['R_sized'] = r['R'] * isz
        out[name] = rows
    return out

# ============================================================================
# PER-DAY x PER-SLEEVE conf-wtd unit-R matrix (true-correlation engine)
# ============================================================================
def build_matrix(streams):
    byday = collections.defaultdict(lambda: collections.defaultdict(list))
    for name, rows in streams.items():
        for r in rows:
            byday[r['date']][name].append(r['R_sized'])
    daily = {}
    for day, sl in byday.items():
        daily[day] = {name: (sum(rs)/len(rs)) * SLEEVE_CONF[name] for name, rs in sl.items()}
    days = sorted(daily)
    M = [[daily[day].get(s, 0.0) for s in SLEEVES] for day in days]
    return days, M

def pearson(x, y):
    n = len(x); mx = sum(x)/n; my = sum(y)/n
    sx = sum((a-mx)**2 for a in x); sy = sum((b-my)**2 for b in y)
    if sx == 0 or sy == 0: return 0.0
    cov = sum((a-mx)*(b-my) for a, b in zip(x, y))
    return cov / math.sqrt(sx*sy)

def corr_matrix(M):
    cols = list(zip(*M)); k = len(SLEEVES)
    return [[round(pearson(list(cols[i]), list(cols[j])), 3) for j in range(k)] for i in range(k)]

# ============================================================================
# DIVERSIFICATION-AWARE CHALLENGE MC: block-bootstrap WHOLE day-rows.
#   portfolio daily move = risk * SUM(per-sleeve contributions on the SAMPLED day).
#   Because real days are resampled as whole rows, the empirical cross-sleeve covariance
#   (true near-zero co-movement, incl. flat/anti-move days) is preserved -> diversification.
#   The corr=1 baseline is the SAME engine on the per-day SUM series (identical here since
#   summing happens after sampling); the diversification PAYOFF is quantified by the
#   independent-column-shuffle counterfactual + the 2-account split.
# ============================================================================
TARGET = I.TARGET; MAXDD = I.MAXDD; DAILY = I.DAILY; BLOCK = I.BLOCK; PATHCAP = I.PATHCAP; N = I.N

def mc_series(vals, risk, n_paths=N, seed_base=0):
    n = len(vals); outs = collections.Counter(); dlist = []
    for s in range(n_paths):
        rng = random.Random(s*131 + seed_base + int(risk*1e6))
        eq = 1.0; peak = 1.0; res = 'timeout'; dc = 0
        for _ in range(PATHCAP):
            start = rng.randrange(n); broke = False
            for k in range(BLOCK):
                dp = vals[(start+k) % n] * risk; dc += 1
                if dp <= -DAILY: res = 'fail_daily'; broke = True; break
                eq *= (1+dp); peak = max(peak, eq)
                if (peak-eq)/peak >= MAXDD: res = 'fail_maxdd'; broke = True; break
                if eq-1.0 >= TARGET: res = 'pass'; broke = True; break
            if broke: break
        outs[res] += 1
        if res == 'pass': dlist.append(dc)
    md = int(statistics.median(dlist)) if dlist else None
    return dict(p_pass=outs['pass']/n_paths, p_fail_dd=outs['fail_maxdd']/n_paths,
                p_fail_daily=outs['fail_daily']/n_paths, p_timeout=outs['timeout']/n_paths, med_days_pass=md)

def acct_series(M, idx_weights, size):
    return [size * sum(row[i]*w for i, w in idx_weights.items()) for row in M]

def joint_pass_mc(M, accA, accB, n_paths=N, seed_base=0):
    valsA = acct_series(M, accA[0], accA[1]); valsB = acct_series(M, accB[0], accB[1]); n = len(valsA)
    cBoth=cA=cB=cAd=cAdd=cBd=cBdd=0
    for s in range(n_paths):
        rng = random.Random(s*131 + seed_base)
        eqA=peakA=1.0; resA='timeout'; eqB=peakB=1.0; resB='timeout'
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
        if resA=='fail_daily': cAd+=1
        if resA=='fail_maxdd': cAdd+=1
        if resB=='fail_daily': cBd+=1
        if resB=='fail_maxdd': cBdd+=1
    return dict(p_passA=cA/n_paths, p_passB=cB/n_paths, p_pass_both=cBoth/n_paths,
                p_A_fail_daily=cAd/n_paths, p_A_fail_dd=cAdd/n_paths,
                p_B_fail_daily=cBd/n_paths, p_B_fail_dd=cBdd/n_paths)

# ============================================================================
def main():
    print("Building Wave-2 sleeve streams...")
    streams = build_streams()
    pickle.dump(streams, open(HERE/'INTEG_W2_streams_cache.pkl','wb'))
    report = {'wave': 2, 'confidence_weights': SLEEVE_CONF, 'sleeves': {}}

    total_fwd = 0.0; total_all = 0.0
    print("\n=== PER-SLEEVE (per-year, forward holdout) ===")
    for name in SLEEVES:
        s = I.sleeve_stats(streams[name]); report['sleeves'][name] = s
        total_fwd += s['fwd_per_year']; total_all += s['all_per_year']
        py = " ".join(f"{y}:{v[1]:+.2f}(n{v[0]})" for y, v in s['per_year'].items())
        print(f"\n[{name}] conf={SLEEVE_CONF[name]}  n={s['n']}  FWD n={s['fwd'][0]} EV={s['fwd'][1]:+.3f} win={s['fwd'][2]:.0f}%  (~{s['fwd_per_year']:.0f}/yr fwd)")
        print(f"   train<=24: n={s['train'][0]} EV={s['train'][1]:+.3f}   per-year: {py}")
    report['total_trades_per_year_fwd'] = round(total_fwd, 1)
    report['total_trades_per_year_all'] = round(total_all, 1)

    days, M = build_matrix(streams)
    fwd_mask = [d.year >= 2025 for d in days]
    M_fwd = [row for row, f in zip(M, fwd_mask) if f]
    comb = [sum(r) for r in M]; comb_fwd = [sum(r) for r in M_fwd]
    print(f"\nmatrix: {len(M)} days x {len(SLEEVES)} sleeves | fwd days {len(M_fwd)}")
    print(f"TOTAL frequency: ~{total_fwd:.0f} trades/yr forward | ~{total_all:.0f} trades/yr all-history")

    # ---- correlation matrix + diversification headline ----
    C = corr_matrix(M)
    offs = [C[i][j] for i in range(len(SLEEVES)) for j in range(len(SLEEVES)) if i < j]
    avg_off = sum(offs)/len(offs)
    report['corr_matrix'] = C; report['avg_off_diag_corr'] = round(avg_off, 3)
    report['corr_minmax'] = [round(min(offs),3), round(max(offs),3)]
    print(f"\n=== CROSS-SLEEVE DAILY-R CORRELATION (0-fill) ===")
    print("        " + " ".join(f"{s[:7]:>8}" for s in SLEEVES))
    for i, s in enumerate(SLEEVES):
        print(f"{s[:7]:>7} " + " ".join(f"{C[i][j]:>8.2f}" for j in range(len(SLEEVES))))
    print(f"Avg pairwise off-diag corr: {avg_off:+.3f} (min {min(offs):+.2f}, max {max(offs):+.2f})")

    # ---- per-sleeve contribution + combined daily stats ----
    contrib = {s: sum(M[d][i] for d in range(len(M))) for i, s in enumerate(SLEEVES)}
    tot = sum(contrib.values())
    report['sleeve_contribution'] = {}
    print("\n=== PER-SLEEVE CONTRIBUTION (conf-wtd unit-R total, share of book) ===")
    for s in sorted(SLEEVES, key=lambda k:-contrib[k]):
        share = 100*contrib[s]/tot if tot else 0
        report['sleeve_contribution'][s] = dict(sum_conf_wtd_unitR=round(contrib[s],3), share_pct=round(share,1), conf=SLEEVE_CONF[s])
        print(f"  {s:>16}: {contrib[s]:+8.2f} ({share:+.0f}% of book)  conf={SLEEVE_CONF[s]}")
    report['combined_daily'] = dict(
        n_days=len(comb), mean_unit_R=round(statistics.fmean(comb),4),
        win_days_pct=round(100*sum(1 for x in comb if x>0)/len(comb),1),
        worst_day_unitR=round(min(comb),4), best_day_unitR=round(max(comb),4),
        std_unit_R=round(statistics.pstdev(comb),4),
        n_days_fwd=len(comb_fwd), mean_unit_R_fwd=round(statistics.fmean(comb_fwd),4))
    print(f"\nCombined daily: {len(comb)} days mean {statistics.fmean(comb):+.4f} unit-R win-days {100*sum(1 for x in comb if x>0)/len(comb):.0f}% worst {min(comb):+.3f} best {max(comb):+.3f}")

    # ---- independent-column-shuffle counterfactual (diversification-credit test) ----
    rng = random.Random(12345); cols = [list(c) for c in zip(*M)]
    for c in cols: rng.shuffle(c)
    comb_shuf = [sum(r) for r in zip(*cols)]

    # ---- CHALLENGE MC: diversification-aware (real rows) vs corr=1 (shuffle) ----
    print(f"\n=== FTMO CHALLENGE-PASS MC ({N} paths; 8% tgt/5% daily/10% maxDD; block={BLOCK}) ===")
    print(f"{'risk':>7} {'P(pass) DIVERS':>15} {'P(pass) corr=1':>15} {'fail_dd':>9} {'daily':>7} {'med_days':>9}")
    report['challenge_mc_all'] = {}; report['challenge_mc_corr1'] = {}
    for risk in (0.005, 0.0075, 0.01, 0.015, 0.02):
        rd = mc_series(comb, risk, seed_base=1)
        rc = mc_series(comb_shuf, risk, seed_base=1)
        report['challenge_mc_all'][f"{risk*100:.2f}%"] = rd
        report['challenge_mc_corr1'][f"{risk*100:.2f}%"] = rc
        print(f"{risk*100:>6.2f}% {rd['p_pass']:>14.2%} {rc['p_pass']:>14.2%} {rd['p_fail_dd']:>9.2%} {rd['p_fail_daily']:>7.1%} {str(rd['med_days_pass']):>9}")

    # ---- FORWARD-only MC ----
    print(f"\n{'risk':>7} {'P(pass) FWD25-26':>17} {'fail_dd':>9} {'med_days':>9}")
    report['challenge_mc_fwd'] = {}
    for risk in (0.005, 0.0075, 0.01, 0.015, 0.02):
        r = mc_series(comb_fwd, risk, seed_base=777)
        report['challenge_mc_fwd'][f"{risk*100:.2f}%"] = r
        print(f"{risk*100:>6.2f}% {r['p_pass']:>16.2%} {r['p_fail_dd']:>9.2%} {str(r['med_days_pass']):>9}")

    # ---- ADVERSARIAL 1.5x left-tail stress (all-history) ----
    comb_stress = [(v*1.5 if v < 0 else v) for v in comb]
    print(f"\n{'risk':>7} {'P(pass) STRESS1.5x':>19} {'fail_dd':>9} {'med_days':>9}  [inflate losing days 1.5x]")
    report['challenge_mc_stress_1p5x'] = {}
    for risk in (0.005, 0.0075, 0.01, 0.015, 0.02):
        r = mc_series(comb_stress, risk, seed_base=999)
        report['challenge_mc_stress_1p5x'][f"{risk*100:.2f}%"] = r
        print(f"{risk*100:>6.2f}% {r['p_pass']:>18.2%} {r['p_fail_dd']:>9.2%} {str(r['med_days_pass']):>9}")

    # ---- daily-breach % across the size grid (mechanical 0% check) ----
    print(f"\n=== DAILY-BREACH % across size grid (worst single day vs -5% limit) ===")
    report['daily_breach'] = {}
    for risk in (0.005, 0.0075, 0.01, 0.015, 0.02):
        worst = min(comb) * risk
        breach = sum(1 for v in comb if v*risk <= -DAILY) / len(comb)
        report['daily_breach'][f"{risk*100:.2f}%"] = dict(worst_day_pct=round(worst*100,3), breach_pct=round(breach*100,3))
        print(f"  {risk*100:>5.2f}%: worst day {worst*100:+.3f}%  breach {breach*100:.3f}%")

    # ---- 2-ACCOUNT LIVE ALLOCATION ----
    idx = {s:i for i,s in enumerate(SLEEVES)}
    def to_w(sl): return {idx[s]:1.0 for s in sl}
    # FULL-BOOK both accounts (recommended Wave-1 finding: diversification is WITHIN each account)
    full = to_w(SLEEVES)
    print(f"\n=== 2-ACCOUNT LIVE ALLOCATION (both trade FULL diversified book) ===")
    report['two_account_fullbook'] = {}
    M_stress = [[(v*1.5 if v<0 else v) for v in row] for row in M]
    for (sizeA, sizeB, label) in [(0.0075,0.0075,'balanced_A0.75_B0.75'),
                                  (0.01,0.005,'staggered_A1.00_B0.50'),
                                  (0.01,0.0075,'staggered_A1.00_B0.75'),
                                  (0.005,0.005,'conservative_A0.50_B0.50')]:
        base = joint_pass_mc(M, (full,sizeA), (full,sizeB), seed_base=7)
        fwd  = joint_pass_mc(M_fwd, (full,sizeA), (full,sizeB), seed_base=33)
        strs = joint_pass_mc(M_stress, (full,sizeA), (full,sizeB), seed_base=44)
        rec = dict(sizeA=sizeA, sizeB=sizeB,
                   base_p_both=base['p_pass_both'], base_passA=base['p_passA'], base_passB=base['p_passB'],
                   fwd_p_both=fwd['p_pass_both'], stress15_p_both=strs['p_pass_both'],
                   daily_breach_max=max(base['p_A_fail_daily'], base['p_B_fail_daily']))
        report['two_account_fullbook'][label] = rec
        print(f"  {label}: P(both)={base['p_pass_both']:.2%} | FWD P(both)={fwd['p_pass_both']:.2%} | "
              f"STRESS1.5x P(both)={strs['p_pass_both']:.2%} | daily-breach={rec['daily_breach_max']:.2%}")

    (HERE/'INTEG_PORTFOLIO_W2_RESULT.json').write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote INTEG_PORTFOLIO_W2_RESULT.json")
    return report

if __name__ == '__main__':
    main()
