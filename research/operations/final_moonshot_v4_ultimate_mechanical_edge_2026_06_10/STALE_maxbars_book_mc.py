"""STALE_maxbars_book_mc.py — BOOK-LEVEL test of loosening the maxbars=80 force-close.
The deployed clean_3 series is rebuilt from the cached streams; then for the three EV-carriers
(metals_core, energy_agri, crypto) the per-trade R is RE-LABELED at a loosened H4 force-close
maxbars (entries held fixed -> no lookahead, no selection change), keyed by (sym,date) onto the
deployed stream so non-carrier sleeves and intra_size weighting are untouched.

For metals_core the DEPLOYED stream is cascade (LTF maxbars 320/1280); the H4 maxbars=80 only
binds the H4-FALLBACK trades. We therefore re-derive the H4-pure STATE_D R at maxbars in {80,240}
per (sym,date) and apply the DELTA only to deployed rows whose deployed R equals the H4-base
(i.e. fallback rows) — a conservative, lookahead-free splice. Energy/crypto base paths are H4/
single-stream so the delta applies directly.

Then run the LOCKED MC engine (vol-matched + 1.5x-stress + raw + daily-breach guardrail) at the
deploy size grid and compare DEPLOYED(80) vs LOOSENED(240). Keep only if growth up & P(maxDD) not up.
"""
import sys, statistics, collections, math, pickle, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3
from geometry_lib import simulate, simulate_detail, atr14
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs

def wins(r): return max(-1.3, min(5.0, r))
CLEAN3_CONF = {'sub_xvol_pullback': 0.45, 'vp_euidx_pocgrav': 0.30, 'sub_mid_dn_revert': 0.20}
BOOK_CONF = dict(W3.SLEEVE_CONF); BOOK_CONF.update(CLEAN3_CONF)

streams_w3 = pickle.load(open(HERE / 'INTEG_W3_streams_cache.pkl', 'rb'))
new_streams = pickle.load(open(HERE / 'INTEG_W5_new_streams_cache.pkl', 'rb'))

# ---------- re-derive H4-pure STATE_D R per (sym,date) for metals & energy at a maxbars ----------
def metals_h4_map(maxbars):
    out = {}
    for sym in cs.METALS:
        T, B = w1.load(sym)
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]; cost = w1.cost_for(sym)
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym):
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac < cs.AC_THR: continue
            vr = cs.vol_ratio(atrs, i)
            out[(sym, t.date())] = wins(cs.exit_state_d(B, i, d, sd, vr, cost, maxbars=maxbars)['R'])
    return out

def energy_h4_map(maxbars):
    out = {}
    for sym in cs.ENERGY:
        try: T, B = w1.load(sym)
        except Exception: continue
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]; cost = w1.cost_for(sym)
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym):
            vr = cs.vol_ratio(atrs, i)
            out[(sym, t.date())] = wins(cs.exit_state_d(B, i, d, sd, vr, cost, maxbars=maxbars)['R'])
    return out

def crypto_map(maxbars, ac_thr=0.15, donch=20, stop_atr=2.0, tgt_r=4.0):
    out = {}
    for sym in ('BTCUSD', 'DASHUSD'):
        try: T, B = w1.load(sym)
        except Exception: continue
        if len(B) < 80: continue
        cost = w1.cost_for(sym)
        for i in range(60, len(B) - 1):
            a = atr14(B, i)
            if a <= 0: continue
            hh = max(B[k].h for k in range(i - donch, i)); ll = min(B[k].l for k in range(i - donch, i))
            d = 0
            if B[i].c > hh: d = 1
            elif B[i].c < ll: d = -1
            if d == 0: continue
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac < ac_thr: continue
            sd = stop_atr * a
            out[(sym, T[i].date())] = wins(simulate(B, i, d, stop_dist=sd, target_dist=tgt_r*sd, cost=cost, maxbars=maxbars))
    return out

print("re-deriving carrier H4 maps @80 and @240 ...")
m80, m240 = metals_h4_map(80), metals_h4_map(240)
e80, e240 = energy_h4_map(80), energy_h4_map(240)
c80, c240 = crypto_map(80), crypto_map(240)
# diagnostic: how many deployed rows are H4-base@80 (i.e. exposed to the cap)
def _exposed(stream, mp):
    return sum(1 for r in stream if (r['sym'], r['date']) in mp and abs(r['R']-mp[(r['sym'],r['date'])])<1e-6)
print(f"exposed-to-cap rows: metals {_exposed(streams_w3['metals_core'], m80)}/{len(streams_w3['metals_core'])}  "
      f"energy {_exposed(streams_w3['energy_agri'], e80)}  crypto {_exposed(streams_w3['crypto'], c80)}")

def relabel_stream(name, rows, loosen):
    """Return new rows with R/R_sized relabeled to maxbars=240 for carrier trades.
    metals_core: apply delta only where deployed R == H4-base@80 (fallback rows) -> conservative.
    energy_agri: energy rows get the H4 delta directly (agri rows untouched).
    crypto: get the single-stream delta directly."""
    if not loosen: return rows
    out = []
    for r in rows:
        nr = dict(r); key = (r['sym'], r['date'])
        if name == 'metals_core' and key in m80 and key in m240:
            # only treat as fallback if deployed R matches the H4-base@80 within tol
            if abs(r['R'] - m80[key]) < 1e-6:
                nr['R'] = m240[key]
        elif name == 'energy_agri' and key in e80 and key in e240:
            if abs(r['R'] - e80[key]) < 1e-6:
                nr['R'] = e240[key]
        elif name == 'crypto' and key in c80 and key in c240:
            if abs(r['R'] - c80[key]) < 1e-6:
                nr['R'] = c240[key]
        isz = nr.get('intra_size', 1.0); nr['R_sized'] = nr['R'] * isz
        out.append(nr)
    return out

def build_comb(loosen):
    bysleeve_day = collections.defaultdict(lambda: collections.defaultdict(list))
    for nm, rows in streams_w3.items():
        for r in relabel_stream(nm, rows, loosen):
            bysleeve_day[nm][r['date']].append(r.get('R_sized', r['R']))
    for nm, rows in new_streams.items():
        if nm not in CLEAN3_CONF: continue
        for r in rows:
            isz = r.get('intra_size', 1.0)
            bysleeve_day[nm][r['date']].append(r['R'] * isz)
    all_days = sorted(set(d for nm in bysleeve_day for d in bysleeve_day[nm]))
    comb = []; comb_fwd = []
    for day in all_days:
        v = 0.0
        for nm in bysleeve_day:
            if day in bysleeve_day[nm]:
                rs = bysleeve_day[nm][day]
                v += (sum(rs)/len(rs)) * BOOK_CONF[nm]
        comb.append(v)
        if day.year >= 2025: comb_fwd.append(v)
    return comb, comb_fwd

def run(comb, comb_fwd, tag, vs=1.0):
    cstr = [(v*1.5 if v < 0 else v) for v in comb]
    out = {}
    for sz in (0.005, 0.0075, 0.01, 0.015, 0.02):
        r = W2.mc_series(comb, sz*vs, seed_base=1)
        s = W2.mc_series(cstr, sz*vs, seed_base=999)
        worst = min(comb) * sz
        breach = sum(1 for v in comb if v*sz <= -0.05) / len(comb)
        out[f"{sz*100:.2f}%"] = dict(p_pass=r['p_pass'], p_fail_dd=r['p_fail_dd'], days=r['med_days_pass'],
                                     stress_pass=s['p_pass'], worst_day_pct=round(worst*100, 3),
                                     breach_pct=round(breach*100, 4))
    f1 = W2.mc_series(comb_fwd, 0.01, seed_base=777) if comb_fwd else {}
    out['fwd@1%'] = dict(p_pass=f1.get('p_pass'), days=f1.get('med_days_pass'))
    return out

report = {}
comb80, fwd80 = build_comb(False)
comb240, fwd240 = build_comb(True)
m80m, sd80 = statistics.fmean(comb80), statistics.pstdev(comb80)
m240m, sd240 = statistics.fmean(comb240), statistics.pstdev(comb240)
print(f"\nDEPLOYED(80):  mean {m80m:.5f} std {sd80:.5f} sharpe {m80m/sd80:.4f}")
print(f"LOOSENED(240): mean {m240m:.5f} std {sd240:.5f} sharpe {m240m/sd240:.4f}")
report['series'] = dict(deployed=dict(mean=round(m80m,5), std=round(sd80,5), sharpe=round(m80m/sd80,4)),
                        loosened=dict(mean=round(m240m,5), std=round(sd240,5), sharpe=round(m240m/sd240,4)))

# RAW (fixed nominal size = true speed-to-target)
report['raw_deployed'] = run(comb80, fwd80, 'raw80')
report['raw_loosened'] = run(comb240, fwd240, 'raw240')
# VOL-MATCHED (loosened matched to deployed std -> apples-to-apples robustness)
vs = sd80 / sd240
report['volmatched_loosened'] = run(comb240, fwd240, 'vm240', vs=vs)

print("\n=== RAW (fixed nominal, true speed-to-target) — pass / days / stress / worst-day / breach ===")
for sz in ('0.50%', '0.75%', '1.00%', '1.50%', '2.00%'):
    d = report['raw_deployed'][sz]; l = report['raw_loosened'][sz]
    print(f"  {sz}: DEP pass {d['p_pass']:.4f} days {d['days']} str {d['stress_pass']:.3f} worst {d['worst_day_pct']}% brch {d['breach_pct']}%  "
          f"|| LOOSE pass {l['p_pass']:.4f} days {l['days']} str {l['stress_pass']:.3f} worst {l['worst_day_pct']}% brch {l['breach_pct']}%")
print(f"  FWD@1%: DEP days {report['raw_deployed']['fwd@1%']['days']}  LOOSE days {report['raw_loosened']['fwd@1%']['days']}")
print("\n=== VOL-MATCHED loosened (std matched to deployed) — robustness apples-to-apples ===")
for sz in ('1.00%', '1.50%'):
    v = report['volmatched_loosened'][sz]
    print(f"  {sz}: pass {v['p_pass']:.4f} stress {v['stress_pass']:.3f} days {v['days']}")

(HERE / 'STALE_maxbars_book_mc_RESULT.json').write_text(json.dumps(report, indent=1, default=str))
print("\nwrote STALE_maxbars_book_mc_RESULT.json")
