"""INTEG_portfolio_build.py — INTEGRATOR: assemble ALL forward-positive sleeves into a
COMBINED PORTFOLIO and run a FTMO challenge-pass Monte Carlo.

Owner goal maximized: P(reach +8% before -5% daily / -10% max DD, no time limit) AND
breadth/frequency. Each sleeve weighted by CONFIDENCE (forward evidence strength); weak-but-
forward-positive sleeves kept at SMALL size (delete nothing).

DOUBLE-COUNTING DISCIPLINE (the metals FVG entry recurs across many built sleeves — same
entries, different exit/timing/sizing). Each underlying entry is counted EXACTLY once:
  - metals_core   = MTF H1->M15 cascade exit on the ac60>=0.10 gated FVG entries (best forward
                    metals exit, train-validated + causally proven). ~33 trades/yr.
  - metals_softband = freqbreadth FVG SOFT-RAMP confidence band ONLY for 0.04<=ac60<0.10
                    (the frequency the hard gate drops). STATE_D exit. Disjoint from core.
  - metals_ob_micro = OB-retest, ac60>=0.20 ONLY, dedup vs FVG core/softband. Small size.
  - crypto, energy_agri, idxrev, fx_jpy = distinct symbols/triggers -> fully additive.

Per-trade R is winsorized [-1.3,+5] at source (exit_state_d / wins). Real cost via w1.cost_for.
State/features leak-free (index<=i); geometry_lib.simulate / exit_state_d label forward only.

CORRELATED-RISK-UNIT MODEL: trades are grouped by (sleeve-class, decision-day). Same-class
same-day trades share ONE risk unit (they are correlated). Across classes on the same day,
each class is an independent risk unit (diversification). The portfolio's daily % move =
sum over classes present that day of class_unit_R * sleeve_confidence_weight * risk_per_unit.
This is the honest worst-case-light model the prior challenge MC used, extended multi-sleeve.
"""
import sys, json, csv, os, statistics, collections, random, datetime
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate, atr14, Bar
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs
import csb_commodity_setups as csb
import multitf_lib as m

def wins(r): return max(-1.3, min(5.0, r))

# ============================================================================
# SLEEVE TRADE-STREAM GENERATORS — each returns list of dicts:
#   {sleeve, sym, date(datetime.date), year, R}   (R = winsorized net R/trade)
# ============================================================================

# ---- 1. METALS CORE: MTF H1->M15 cascade exit on ac60>=0.10 FVG entries -----
H1_MAXBARS = 320
def _metals_h4_signals(sym):
    T, B = w1.load(sym)
    if len(B) < 200: return []
    atrs = [atr14(B, k) for k in range(len(B))]
    out = []
    for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym):
        ac = cs.autocorr(B, i, 60)
        if ac is None or ac < cs.AC_THR: continue
        out.append((t, d, sd, i, B, cs.vol_ratio(atrs, i), c2, ac))
    return out

def _find_fill(Bl, Tl, si, d, sc, window, mi, ts):
    end = min(si + window, len(Bl) - 1)
    a1 = atr14(Bl, si); imp = mi * a1 if a1 > 0 else 0.0
    limit = sc - imp if d > 0 else sc + imp
    for j in range(si, end + 1):
        if Tl[j] < ts: continue
        b = Bl[j]
        if d > 0 and b.l <= limit: return j
        if d < 0 and b.h >= limit: return j
    return None

def gen_metals_core():
    rows = []
    for sym in cs.METALS:
        sigs = _metals_h4_signals(sym)
        T1, B1 = m.load_ltf(sym, "H1"); have1 = len(B1) > 50
        T15, B15 = m.load_ltf(sym, "M15"); have15 = len(B15) > 50
        for (t, d, sd_h4, i_h4, B_h4, vr, cost, ac) in sigs:
            base_R = cs.exit_state_d(B_h4, i_h4, d, sd_h4, vr, cost)['R']
            ts = t + datetime.timedelta(hours=4); sc = B_h4[i_h4].c
            R = base_R; filled = False
            if have1:
                si = m.first_ltf_index_after(T1, ts)
                if si is not None and 30 <= si < len(B1) - 2:
                    ej = _find_fill(B1, T1, si, d, sc, 12, 1.0, ts)
                    if ej is not None:
                        R = cs.exit_state_d(B1, ej, d, sd_h4, vr, cost, maxbars=H1_MAXBARS)['R']; filled = True
            if not filled and have15:
                si = m.first_ltf_index_after(T15, ts)
                if si is not None and 30 <= si < len(B15) - 2:
                    ej = _find_fill(B15, T15, si, d, sc, 48, 1.0, ts)
                    if ej is not None:
                        R = cs.exit_state_d(B15, ej, d, sd_h4, vr, cost, maxbars=1280)['R']
            rows.append(dict(sleeve='metals_core', sym=sym, date=t.date(), year=t.year, R=wins(R)))
    return rows

# ---- 2. METALS SOFTBAND: freqbreadth FVG soft-ramp, ONLY 0.04<=ac60<0.10 ----
# (the frequency the hard gate drops; disjoint from core which is ac60>=0.10). STATE_D exit.
AC_FLOOR_SB = 0.04
def _size_mult_soft(ac, vr):
    if ac is None or ac < AC_FLOOR_SB: return 0.0
    base = 0.40 + (ac - AC_FLOOR_SB) * (0.80 / 0.15)
    base = max(0.40, min(1.20, base))
    if vr < 1.35: base *= 1.15
    elif vr >= 1.6: base *= 0.90
    return round(min(1.5, base), 4)

def gen_metals_softband():
    rows = []
    for sym in cs.METALS:
        T, B = w1.load(sym)
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]; cost = w1.cost_for(sym)
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym):
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac >= cs.AC_THR or ac < AC_FLOOR_SB: continue  # ONLY the soft band
            vr = cs.vol_ratio(atrs, i)
            sm = _size_mult_soft(ac, vr)
            if sm <= 0: continue
            ex = cs.exit_state_d(B, i, d, sd, vr, c2)
            rows.append(dict(sleeve='metals_softband', sym=sym, date=t.date(), year=t.year,
                             R=wins(ex['R']), intra_size=sm))
    return rows

# ---- 3. METALS OB MICRO: OB-retest, ac60>=0.20 only, dedup vs FVG ----
def gen_metals_ob_micro():
    # build FVG entry keys (sym,date,dir) to dedup
    fvg_keys = set()
    for sym in cs.METALS:
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym):
            ac = cs.autocorr(B2, i, 60)
            if ac is None: continue
            fvg_keys.add((sym, str(t.date()), d))
    rows = []
    for sym in cs.METALS:
        T, B = w1.load(sym)
        if len(B) < 200: continue
        A = csb._atrs(B); cost = w1.cost_for(sym)
        for (t, d, sd, i, B2, c2) in csb.SETUPS['OB'](sym):
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac < 0.20: continue          # micro: strong-persistence tail only
            if (sym, str(t.date()), d) in fvg_keys: continue  # dedup vs FVG core/softband
            vr = cs.vol_ratio(A, i); ex = cs.exit_state_d(B, i, d, sd, vr, c2)
            rows.append(dict(sleeve='metals_ob_micro', sym=sym, date=t.date(), year=t.year, R=wins(ex['R'])))
    return rows

# ---- 4. CRYPTO momentum/persistence (BTCUSD, DASHUSD) ----
def gen_crypto():
    rows = []
    for sym in ('BTCUSD', 'DASHUSD'):
        try: T, B = w1.load(sym)
        except Exception: continue
        if len(B) < 80: continue
        cost = w1.cost_for(sym)
        for i in range(60, len(B) - 1):
            a = atr14(B, i)
            if a <= 0: continue
            hh = max(B[k].h for k in range(i - 20, i)); ll = min(B[k].l for k in range(i - 20, i))
            d = 0
            if B[i].c > hh: d = 1
            elif B[i].c < ll: d = -1
            if d == 0: continue
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac < 0.15: continue
            sd = 2.0 * a
            R = simulate(B, i, d, stop_dist=sd, target_dist=4 * sd, cost=cost)
            rows.append(dict(sleeve='crypto', sym=sym, date=T[i].date(), year=T[i].year, R=wins(R)))
    return rows

# ---- 5. ENERGY + AGRI (reuse committed locked sleeve ledger) ----
def gen_energy_agri():
    rows = []
    p = HERE / 'ENERGY_AGRI_SLEEVE_TRADES.jsonl'
    for line in p.read_text().splitlines():
        if not line.strip(): continue
        r = json.loads(line)
        dt = datetime.date.fromisoformat(r['date'])
        rows.append(dict(sleeve='energy_agri', sym=r['sym'], date=dt, year=r['year'],
                         R=wins(r['R']), intra_size=r['conf']))
    return rows

# ---- 6. INDEX REVERSION pocket (failed-breakout fade) ----
IDX_POCKET = ["SPX500", "UK100", "FRA40_cash", "EU50_cash", "US2000_cash", "JP225", "GER40", "US30_cash"]
def gen_idxrev():
    rows = []
    LB = 16; STOP_ATR = 1.5; TGT_R = 0.75; MAXBARS = 60
    for sym in IDX_POCKET:
        try: T, B = w1.load(sym)
        except Exception: continue
        if len(B) < 150: continue
        atrs = [atr14(B, k) for k in range(len(B))]; cost = w1.cost_for(sym)
        for i in range(120, len(B)):
            a = atrs[i]
            if a <= 0: continue
            rhi = max(B[k].h for k in range(i - LB, i)); rlo = min(B[k].l for k in range(i - LB, i))
            b = B[i]; d = 0
            if b.h > rhi and b.c < rhi: d = -1
            elif b.l < rlo and b.c > rlo: d = 1
            if d == 0: continue
            sd = STOP_ATR * a; rcost = cost / STOP_ATR
            R = simulate(B, i, d, stop_dist=sd, target_dist=TGT_R * sd, maxbars=MAXBARS, cost=rcost)
            rows.append(dict(sleeve='idxrev', sym=sym, date=T[i].date(), year=T[i].year, R=wins(R)))
    return rows

# ---- 7. FX-JPY London-open momentum (M15, GBPJPY+USDJPY, forward-only) ----
M15DIR = str(HERE.parents[2]) + '/data/mt5_research_exports/bridge_ftmo_m15_20250601_20260610'
_FXC = {}
def _load_fx_m15(sym):
    if sym in _FXC: return _FXC[sym]
    p = os.path.join(M15DIR, f'{sym}_M15.csv'); T = []; B = []
    if os.path.exists(p):
        with open(p) as f:
            for row in csv.DictReader(f):
                try:
                    t = datetime.datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S')
                    B.append(Bar(float(row['open']), float(row['high']), float(row['low']),
                                 float(row['close']), float(row.get('volume', 0) or 0))); T.append(t)
                except Exception: continue
    A = [atr14(B, i) for i in range(len(B))]; _FXC[sym] = (T, B, A); return _FXC[sym]

def gen_fx_jpy():
    rows = []
    for sym in ('GBPJPY', 'USDJPY'):
        T, B, A = _load_fx_m15(sym); cost = w1.cost_for(sym)
        if len(B) < 100: continue
        byday = collections.defaultdict(list)
        for i, t in enumerate(T): byday[t.date()].append(i)
        for day, idxs in sorted(byday.items()):
            lon = [i for i in idxs if T[i].hour >= 8]
            if len(lon) < 6: continue
            i0 = lon[0]
            if i0 < 20: continue
            iw = lon[3]                      # 4th London M15 bar (1h opening impulse close)
            a = A[iw]
            if a <= 0: continue
            d = 1 if B[iw].c > B[i0].o else -1
            R = simulate(B, iw, d, stop_dist=1.0 * a, target_dist=2.5 * a, maxbars=48, cost=cost)
            rows.append(dict(sleeve='fx_jpy', sym=sym, date=day, year=T[iw].year, R=wins(R)))
    return rows

# ============================================================================
# CONFIDENCE WEIGHTS — by forward evidence strength (train-validated + both
# forward years positive + sample depth). Weak-but-positive kept small, none zero.
# ============================================================================
SLEEVE_CONF = {
    'metals_core':      1.00,   # train-validated, causal paired-lift proof, +1.16R fwd, deepest
    'crypto':           0.70,   # both fwd years +, liquid carriers, but thin train (n=8)
    'energy_agri':      0.60,   # gate positive every year, but shallow/fragmented H4 data
    'metals_softband':  0.50,   # soft band lower-EV than core, frequency add
    'metals_ob_micro':  0.30,   # OB tail carried by 2025; 2026 thin -> small
    'idxrev':           0.30,   # 2024+ only (single-regime confound); NAS100 honest comp neg
    'fx_jpy':           0.35,   # robust 12/13 months but ONE forward window, no train
}
# intra-sleeve per-trade size multipliers (softband ramp, energy/agri conf) are applied to the
# per-trade R BEFORE day-aggregation so the daily unit reflects realised confidence sizing.

def build_streams():
    gens = {
        'metals_core': gen_metals_core, 'metals_softband': gen_metals_softband,
        'metals_ob_micro': gen_metals_ob_micro, 'crypto': gen_crypto,
        'energy_agri': gen_energy_agri, 'idxrev': gen_idxrev, 'fx_jpy': gen_fx_jpy,
    }
    out = {}
    for name, fn in gens.items():
        rows = fn()
        # apply intra-sleeve size to R if present (softband ramp, energy/agri conf)
        for r in rows:
            isz = r.get('intra_size', 1.0)
            r['R_sized'] = r['R'] * isz
        out[name] = rows
    return out

# ============================================================================
# DAILY CORRELATED-RISK-UNIT STREAM
#   For each (sleeve, day): unit_R = mean(R_sized of that sleeve that day)  [correlated within]
#   Portfolio daily % = sum over sleeves present(day) [ unit_R * sleeve_conf * risk_per_unit ]
# Cross-sleeve = independent units (diversification). This matches the prior MC's
# per-day correlated-unit convention, generalized to a multi-sleeve book.
# ============================================================================
def daily_class_units(streams):
    """Return dict: day -> {sleeve: confidence-weighted unit_R contribution per 1.0 risk_per_unit}."""
    byday = collections.defaultdict(lambda: collections.defaultdict(list))
    for name, rows in streams.items():
        for r in rows:
            byday[r['date']][name].append(r['R_sized'])
    daily = {}
    for day, sl in byday.items():
        contrib = {}
        for name, rs in sl.items():
            unit_R = sum(rs) / len(rs)            # correlated within class = 1 unit
            contrib[name] = unit_R * SLEEVE_CONF[name]
        daily[day] = contrib
    return daily

def combined_daily_R(daily):
    """List of (day, summed confidence-weighted unit-R) sorted by day, for 1.0 risk_per_unit."""
    return [(day, sum(c.values())) for day, c in sorted(daily.items())]

# ============================================================================
# CHALLENGE-PASS MONTE CARLO (block bootstrap, preserves vol clustering)
# ============================================================================
TARGET = 0.08; MAXDD = 0.10; DAILY = 0.05; BLOCK = 5; N = 20000; PATHCAP = 2000
def challenge_mc(daily_R, risk_per_unit, n_paths=N, seed_base=0):
    vals = [v for _, v in daily_R]; n = len(vals)
    outs = collections.Counter(); days_pass = []
    for s in range(n_paths):
        rng = random.Random(s * 131 + seed_base + int(risk_per_unit * 1e6))
        eq = 1.0; peak = 1.0; res = 'timeout'; dc = 0
        for _ in range(PATHCAP):
            start = rng.randrange(n)
            broke = False
            for k in range(BLOCK):
                r = vals[(start + k) % n]; dp = r * risk_per_unit; dc += 1
                if dp <= -DAILY: res = 'fail_daily'; broke = True; break
                eq *= (1 + dp); peak = max(peak, eq)
                if (peak - eq) / peak >= MAXDD: res = 'fail_maxdd'; broke = True; break
                if eq - 1.0 >= TARGET: res = 'pass'; broke = True; break
            if broke: break
        outs[res] += 1
        if res == 'pass': days_pass.append(dc)
    md = int(statistics.median(days_pass)) if days_pass else None
    return dict(p_pass=outs['pass'] / n_paths, p_fail_dd=outs['fail_maxdd'] / n_paths,
                p_fail_daily=outs['fail_daily'] / n_paths, p_timeout=outs['timeout'] / n_paths,
                med_days_pass=md)

# ============================================================================
# PER-SLEEVE FORWARD STATS (per-year, never a bulk verdict)
# ============================================================================
def sleeve_stats(rows):
    def st(rs):
        if not rs: return (0, 0.0, 0.0)
        nn = len(rs); mm = sum(x['R'] for x in rs) / nn
        ww = sum(1 for x in rs if x['R'] > 0) / nn * 100
        return (nn, round(mm, 4), round(ww, 1))
    yrs = sorted(set(r['year'] for r in rows))
    per_year = {str(y): st([r for r in rows if r['year'] == y]) for y in yrs}
    fwd = [r for r in rows if r['year'] >= 2025]
    tr = [r for r in rows if r['year'] <= 2024]
    span_years = max(1, len(yrs))
    fwd_years = len([y for y in yrs if y >= 2025]) or 1
    return dict(n=len(rows), per_year=per_year, train=st(tr), fwd=st(fwd),
                fwd_per_year=round(len(fwd) / fwd_years, 1), all_per_year=round(len(rows) / span_years, 1))

def main():
    print("Building sleeve trade streams (this regenerates each forward-positive sleeve)...")
    streams = build_streams()
    report = {'sleeves': {}, 'confidence_weights': SLEEVE_CONF}
    total_fwd_tpy = 0.0; total_all_tpy = 0.0
    print("\n=== PER-SLEEVE (per-year, forward holdout) ===")
    for name in streams:
        s = sleeve_stats(streams[name])
        report['sleeves'][name] = s
        total_fwd_tpy += s['fwd_per_year']; total_all_tpy += s['all_per_year']
        py = " ".join(f"{y}:{v[1]:+.2f}(n{v[0]})" for y, v in s['per_year'].items())
        print(f"\n[{name}] conf={SLEEVE_CONF[name]}  n={s['n']}  FWD25-26 n={s['fwd'][0]} EV={s['fwd'][1]:+.3f} "
              f"win={s['fwd'][2]:.0f}%  (~{s['fwd_per_year']:.0f}/yr fwd)")
        print(f"   train<=24: n={s['train'][0]} EV={s['train'][1]:+.3f}")
        print(f"   per-year: {py}")

    daily = daily_class_units(streams)
    comb = combined_daily_R(daily)
    vals = [v for _, v in comb]
    # forward-only combined daily stream (2025-26) for an honest forward MC too
    comb_fwd = [(d, v) for d, v in comb if d.year >= 2025]
    vals_fwd = [v for _, v in comb_fwd]
    report['combined_daily'] = dict(
        n_days=len(comb), mean_unit_R=round(statistics.fmean(vals), 4),
        win_days_pct=round(100 * sum(1 for x in vals if x > 0) / len(vals), 1),
        worst_day_unitR=round(min(vals), 4), best_day_unitR=round(max(vals), 4),
        std_unit_R=round(statistics.pstdev(vals), 4),
        n_days_fwd=len(comb_fwd), mean_unit_R_fwd=round(statistics.fmean(vals_fwd), 4) if vals_fwd else None,
    )
    print(f"\n=== COMBINED DAILY CORRELATED-RISK-UNIT STREAM ===")
    print(f"  ALL: {len(comb)} trading days w/ signals | mean {statistics.fmean(vals):+.4f} conf-wtd unit-R/day "
          f"| win-days {100*sum(1 for x in vals if x>0)/len(vals):.0f}% | worst {min(vals):+.3f} best {max(vals):+.3f}")
    print(f"  FWD2025-26: {len(comb_fwd)} days | mean {statistics.fmean(vals_fwd):+.4f} unit-R/day")
    print(f"  TOTAL frequency: ~{total_fwd_tpy:.0f} trades/yr (forward) | ~{total_all_tpy:.0f} trades/yr (full-history)")
    report['total_trades_per_year_fwd'] = round(total_fwd_tpy, 1)
    report['total_trades_per_year_all'] = round(total_all_tpy, 1)

    # per-sleeve contribution to combined daily mean unit-R (additive decomposition)
    print("\n=== PER-SLEEVE CONTRIBUTION to combined conf-wtd daily unit-R (ALL history) ===")
    sleeve_contrib = collections.defaultdict(float)
    for day, c in daily.items():
        for name, v in c.items(): sleeve_contrib[name] += v
    tot = sum(sleeve_contrib.values())
    report['sleeve_contribution'] = {}
    for name in sorted(sleeve_contrib, key=lambda k: -sleeve_contrib[k]):
        share = 100 * sleeve_contrib[name] / tot if tot else 0
        report['sleeve_contribution'][name] = dict(sum_conf_wtd_unitR=round(sleeve_contrib[name], 3), share_pct=round(share, 1))
        print(f"  {name:>16}: {sleeve_contrib[name]:+8.2f} conf-wtd unit-R total ({share:+.0f}% of book)")

    # ---- CHALLENGE MC at sizing 0.5 / 0.75 / 1.0% (and a few refs) ----
    print(f"\n=== FTMO CHALLENGE-PASS MONTE CARLO ({N} paths/level; 8% tgt / 5% daily / 10% maxDD; block={BLOCK}) ===")
    print("  (risk_per_unit = % equity risked per INDEPENDENT correlated-risk-unit; confidence weights already baked into unit-R)")
    print(f"\n{'risk/unit':>10} {'P(pass)':>9} {'P(fail_dd)':>11} {'P(fail_daily)':>14} {'med_days':>9}   [ALL-history stream]")
    report['challenge_mc_all'] = {}
    for risk in (0.005, 0.0075, 0.01, 0.015, 0.02):
        res = challenge_mc(comb, risk)
        report['challenge_mc_all'][f"{risk*100:.2f}%"] = res
        print(f"{risk*100:>9.2f}% {res['p_pass']:>9.1%} {res['p_fail_dd']:>11.1%} {res['p_fail_daily']:>14.1%} {str(res['med_days_pass']):>9}")
    print(f"\n{'risk/unit':>10} {'P(pass)':>9} {'P(fail_dd)':>11} {'P(fail_daily)':>14} {'med_days':>9}   [FORWARD 2025-26 only]")
    report['challenge_mc_fwd'] = {}
    for risk in (0.005, 0.0075, 0.01, 0.015, 0.02):
        res = challenge_mc(comb_fwd, risk, seed_base=777)
        report['challenge_mc_fwd'][f"{risk*100:.2f}%"] = res
        print(f"{risk*100:>9.2f}% {res['p_pass']:>9.1%} {res['p_fail_dd']:>11.1%} {res['p_fail_daily']:>14.1%} {str(res['med_days_pass']):>9}")

    # ---- ADVERSARIAL STRESS: 2x daily-loss inflation (fat-tail / slippage / gap stress).
    #      The base model risks `risk_per_unit` against the SUMMED daily unit-R already, i.e.
    #      it takes NO cross-sleeve diversification credit (worst-case correlation = 1). To probe
    #      robustness further we inflate every NEGATIVE day by 1.5x (model fatter left tail than
    #      history showed) and re-run. If P(pass) holds, the result is not knife-edge.
    comb_stress = [(d, (v * 1.5 if v < 0 else v)) for d, v in comb]
    print(f"\n{'risk/unit':>10} {'P(pass)':>9} {'P(fail_dd)':>11} {'P(fail_daily)':>14} {'med_days':>9}   [STRESS: 1.5x loss-day inflation, ALL hist]")
    report['challenge_mc_stress_1p5x_losses'] = {}
    report['model_note'] = ("Base model risks risk_per_unit against the SUMMED daily conf-wtd unit-R, taking NO "
                            "cross-sleeve diversification credit (implicit correlation=1 on the equity path). It is "
                            "therefore a CONSERVATIVE bound; true diversification would lower breach risk further. "
                            "STRESS variant additionally inflates every losing day 1.5x to probe a fatter left tail.")
    for risk in (0.005, 0.0075, 0.01, 0.015, 0.02):
        res = challenge_mc(comb_stress, risk, seed_base=999)
        report['challenge_mc_stress_1p5x_losses'][f"{risk*100:.2f}%"] = res
        print(f"{risk*100:>9.2f}% {res['p_pass']:>9.1%} {res['p_fail_dd']:>11.1%} {res['p_fail_daily']:>14.1%} {str(res['med_days_pass']):>9}")

    (HERE / 'INTEG_PORTFOLIO_RESULT.json').write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote INTEG_PORTFOLIO_RESULT.json")
    return report

if __name__ == '__main__':
    main()
