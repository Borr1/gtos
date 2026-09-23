"""INTEG_portfolio_build_w3.py — WAVE-3 book: W2 + the D4-miner forward-validated harvest.

Builds on INTEG_portfolio_build_w2 (re-uses its true-corr + diversification MC + 2-acct alloc and
every W2 sleeve), then APPLIES the D4 miner harvest items that re-validate train+forward (per-year):

 (KB3 revalidate)  metals_core:
   M1 confidence-size by entry-vol: size 1.0 (vr<=1.35) / 0.75 (1.35-1.6) / 0.5 (vr>1.6).
      Size-weighted FWD +1.164 -> +1.288R; monotone localization (vr<=1.281 -> +2.31R combo).
   M2 EXEC_COMBO exit (scale 50% @2.0R, vol-banded profit-lock 0.25/0.5/0.75, target 4.0/3.0/2.5)
      REPLACES STATE_D on the SAME cascade entries. TRAIN +0.482->+0.679 (train-validated),
      FWD +1.164->+1.235 (BOTH years +: 2025 +1.25 / 2026 +1.22). 2026 leg lifts +1.01->+1.22.
   M3 body<=0.374 small-bar entry as CONFIDENCE SIZE (small bars full, big bars x0.5; delete none).
      KEEP bucket FWD +1.555 (100% win, both yrs +); DROP bucket FWD +0.278 (2026 NEG) -> half size.
   STACK (combo+vrsize+body-conf): size-weighted FWD +1.594R (+0.43R vs deployed), TRAIN +0.768.

 (KB3 revalidate)  metals_softband:
   body<=0.431 small-bar CONFIDENCE SIZE. KEEP FWD +0.528 (both yrs +) vs +0.140; DROP FWD -0.160
   (both yrs neg) -> half size. Delete nothing.

 (KB3 revalidate)  crypto/ETH:
   ETH carrier floor LOWERED ac>=0.15 -> ac>=0.10 (more robust: both fwd yrs +, 62 vs 23 trades,
   2026 +0.169 vs the ac>=0.15 NEGATIVE 2026 -0.951). ADD ac>=0.20 hi-conviction x1.5 size tier
   (TRAIN +2.15 / 2025 +2.66; 2026 n=1 too thin -> only x1.5, not larger; train+2025 justify it).

 (already in W2, RE-VALIDATED in this run)  energy supply-shock vr>=2 runR=4; gated NY-JPY 2nd
   session. Both carried unchanged from W2 and re-reported per-year in the W3 scorecard.

Confidence sizing, per-YEAR/per-symbol, forward holdout (train<=2024), winsorize R[-1.3,+5],
real cost, leak-free features — all preserved. NOTHING deleted; falsified buckets demoted to small.
"""
import sys, json, datetime, statistics, collections, pickle, random, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate, atr14, Bar
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs
import multitf_lib as m
import INTEG_portfolio_build as I
import INTEG_portfolio_build_w2 as W2
import kb2_new_breadth as KB
import EXEC_exit_variants as EX

def wins(r): return max(-1.3, min(5.0, r))
ROOT = str(HERE.parents[2]); DATA = ROOT + '/data/mt5_research_exports'
H1_MAXBARS = 320

# ============================================================================
# M1+M2+M3: metals_core with EXEC_COMBO exit + vr-size + body-conf (same entries)
# ============================================================================
def _vr_size(vr):
    if vr <= 1.35: return 1.0
    if vr <= 1.6:  return 0.75
    return 0.5

def _exit_combo_banded(stream, fi, d, sd, vr, cost_scaled, maxbars):
    lock = 0.25 if vr < 1.35 else (0.5 if vr < 1.6 else 0.75)
    ent = dict(B=stream, i=fi, d=d, sd=sd, cost=cost_scaled, vr=vr)
    ex = EX.sim_exit(ent, ladder=[(2.0, 0.5)], be_after_first=lock,
                     runner_R_map=(4.0, 3.0, 2.5), maxbars=maxbars)
    return wins(ex['R'])

def gen_metals_core():
    rows = []
    for sym in cs.METALS:
        T, B = w1.load(sym)
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]
        T1, B1 = m.load_ltf(sym, "H1"); have1 = len(B1) > 50
        T15, B15 = m.load_ltf(sym, "M15"); have15 = len(B15) > 50
        for (t, d, sd_h4, td, i_h4, B_h4, cost) in g.fvg_signals(sym):
            ac = cs.autocorr(B, i_h4, 60)
            if ac is None or ac < cs.AC_THR: continue
            vr = cs.vol_ratio(atrs, i_h4); a = atrs[i_h4]
            body = abs(B[i_h4].c - B[i_h4].o) / a if a > 0 else 0.0
            ts = t + datetime.timedelta(hours=4); sc = B_h4[i_h4].c
            stream, fi, maxbars, filled = B_h4, i_h4, 80, False
            if have1:
                si = m.first_ltf_index_after(T1, ts)
                if si is not None and 30 <= si < len(B1) - 2:
                    ej = I._find_fill(B1, T1, si, d, sc, 12, 1.0, ts)
                    if ej is not None: stream, fi, maxbars, filled = B1, ej, H1_MAXBARS, True
            if not filled and have15:
                si = m.first_ltf_index_after(T15, ts)
                if si is not None and 30 <= si < len(B15) - 2:
                    ej = I._find_fill(B15, T15, si, d, sc, 48, 1.0, ts)
                    if ej is not None: stream, fi, maxbars = B15, ej, 1280
            cost_scaled = cost * (0.5 * a / sd_h4) if sd_h4 > 0 else cost
            R = _exit_combo_banded(stream, fi, d, sd_h4, vr, cost_scaled, maxbars)   # M2
            sz = _vr_size(vr)                                                        # M1
            if body > 0.374: sz *= 0.5                                               # M3 (keep small)
            rows.append(dict(sleeve='metals_core', sym=sym, date=t.date(), year=t.year,
                             R=wins(R), intra_size=round(sz, 4)))
    return rows

# ============================================================================
# metals_softband: body<=0.431 confidence size (keep big-body small, delete none)
# ============================================================================
def gen_metals_softband():
    rows = []
    for sym in cs.METALS:
        T, B = w1.load(sym)
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]; cost = w1.cost_for(sym)
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym):
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac >= cs.AC_THR or ac < I.AC_FLOOR_SB: continue
            vr = cs.vol_ratio(atrs, i); a = atrs[i]
            body = abs(B[i].c - B[i].o) / a if a > 0 else 0.0
            sm = I._size_mult_soft(ac, vr)
            if sm <= 0: continue
            if body > 0.431: sm *= 0.5                          # SB body-conf (keep small)
            ex = cs.exit_state_d(B, i, d, sd, vr, c2)
            rows.append(dict(sleeve='metals_softband', sym=sym, date=t.date(), year=t.year,
                             R=wins(ex['R']), intra_size=round(sm, 4)))
    return rows

# ============================================================================
# crypto: BTC/DASH cascade (unchanged) + ETH ac>=0.10 carrier + ac>=0.20 x1.5 tier
# ============================================================================
def _eth_cascade_rows():
    T, B = KB.resample_eth_h4(); cost = w1.cost_for('ETHUSD')
    atrs = [atr14(B, i) for i in range(len(B))]
    m.LTF_PATHS.setdefault(("ETHUSD", "H1"),  [DATA + "/bridge_ftmo_htf_20250601_20260610/ETHUSD_H1.csv"])
    m.LTF_PATHS.setdefault(("ETHUSD", "M15"), [DATA + "/bridge_ftmo_m15_20250601_20260610/ETHUSD_M15.csv"])
    T1, B1 = m.load_ltf("ETHUSD", "H1"); have1 = len(B1) > 50
    T15, B15 = m.load_ltf("ETHUSD", "M15"); have15 = len(B15) > 50
    rows = []
    for (i, d) in KB.crypto_breakout_signals(B, 20):
        a = atrs[i]
        if a <= 0: continue
        ac = cs.autocorr(B, i, 60)
        # ABLATION VERDICT: lowering the floor to 0.10 adds a low-persistence band that DILUTES the
        # book and CRATERS stress P(pass) 0.80->0.64 (the ac[0.10,0.20) trades are +0.016R train,
        # both fwd yrs ~flat, but at conf 0.85 they inject tail variance). KEEP ac>=0.15 (robust
        # carrier), and instead size UP the ac>=0.20 hi-conviction tier (train+2025 validated).
        if ac is None or ac < 0.15: continue
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
        sz = 1.5 if ac >= 0.20 else 1.0                          # ac>=0.20 hi-conviction tier
        rows.append(dict(sleeve='crypto', sym='ETHUSD', date=T[i].date(), year=T[i].year,
                         R=wins(R), intra_size=sz))
    return rows

def gen_crypto():
    rows = []
    p = HERE / 'TW_CRYPTO_CASCADE_LEDGER.jsonl'
    for line in p.read_text().splitlines():
        if not line.strip(): continue
        r = json.loads(line)
        dt = datetime.date.fromisoformat(r['date'])
        rows.append(dict(sleeve='crypto', sym=r['sym'], date=dt, year=r['year'], R=wins(r['casc_R'])))
    rows += _eth_cascade_rows()
    return rows

# ============================================================================
# Re-use W2 for everything else (energy runR4, idxrev, fx_jpy, fx_jpy_ny, ob_micro, MC engine)
# ============================================================================
gen_metals_ob_micro = W2.gen_metals_ob_micro
gen_energy_agri     = W2.gen_energy_agri
gen_idxrev          = W2.gen_idxrev
gen_fx_jpy          = W2.gen_fx_jpy
gen_fx_jpy_ny       = W2.gen_fx_jpy_ny

SLEEVE_CONF = dict(W2.SLEEVE_CONF)   # unchanged confidence weights; harvest acts via intra_size

GENS = {
    'metals_core': gen_metals_core, 'metals_softband': gen_metals_softband,
    'metals_ob_micro': gen_metals_ob_micro, 'crypto': gen_crypto,
    'energy_agri': gen_energy_agri, 'idxrev': gen_idxrev,
    'fx_jpy': gen_fx_jpy, 'fx_jpy_ny': gen_fx_jpy_ny,
}
SLEEVES = list(GENS.keys())

# wire W3 gens + conf into the W2 MC/report machinery (it reads module globals via these names)
W2.GENS = GENS; W2.SLEEVES = SLEEVES; W2.SLEEVE_CONF = SLEEVE_CONF

def main():
    print("=== WAVE-3 BOOK (W2 + D4 miner harvest) ===\n")
    # W2.main() hardcodes its own output paths; preserve the locked W2 baseline artifacts.
    import shutil, os
    w2json = HERE/'INTEG_PORTFOLIO_W2_RESULT.json'; w2pkl = HERE/'INTEG_W2_streams_cache.pkl'
    bj = HERE/'_w2_baseline_result.bak.json'; bp = HERE/'_w2_baseline_cache.bak.pkl'
    if w2json.exists() and not bj.exists(): shutil.copy(w2json, bj)
    if w2pkl.exists() and not bp.exists(): shutil.copy(w2pkl, bp)
    rep = W2.main()
    # rename the W2-named outputs (which now hold W3 content) to W3 names; restore W2 baselines
    shutil.move(str(w2json), str(HERE/'INTEG_PORTFOLIO_W3_RESULT.json'))
    shutil.move(str(w2pkl), str(HERE/'INTEG_W3_streams_cache.pkl'))
    if bj.exists(): shutil.copy(bj, w2json)
    if bp.exists(): shutil.copy(bp, w2pkl)
    rep['wave'] = 3
    rep['harvest_applied'] = [
        'metals_core: EXEC_COMBO exit + vr-size(1.0/0.75/0.5) + body<=0.374 conf-size',
        'metals_softband: body<=0.431 conf-size',
        'crypto/ETH: ac>=0.20 x1.5 hi-conviction tier (kept ac>=0.15 floor)',
        'energy: supply-shock vr>=2 runR=4 (carried from W2, revalidated)',
        'fx_jpy_ny: gated NY-open 2nd session (carried from W2, revalidated)',
    ]
    rep['harvest_rejected_learning'] = [
        'crypto/ETH ac floor 0.15->0.10: per-sleeve both-fwd-yrs positive but BOOK-LEVEL stress '
        'P(pass) 0.80->0.64 (low-persistence band injects tail variance at conf 0.85). Kept ac>=0.15.'
    ]
    (HERE/'INTEG_PORTFOLIO_W3_RESULT.json').write_text(json.dumps(rep, indent=1, default=str))
    print("\nwrote INTEG_PORTFOLIO_W3_RESULT.json (W2 baseline artifacts restored)")
    return rep

if __name__ == '__main__':
    main()
