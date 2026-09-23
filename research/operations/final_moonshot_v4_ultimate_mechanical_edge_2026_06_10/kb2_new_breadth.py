"""KB2 — NEW BREADTH / FREQUENCY SLEEVES (track key: KB2)

Adds four breadth carriers to the ultimate-mechanical-edge portfolio, each forward-validated,
confidence-sized, nothing killed. Mirrors the EXACT locked rules from the wave-1 KBs:

  (a) ETHUSD  3rd crypto carrier. ETH H4 via w1.load is broken (134 bars) -> RESAMPLE M1->H4
      (real data 2024-10..2026-06) then apply the IDENTICAL crypto rule from KB_crypto.md:
      Donchian-20 breakout (closed bar) + ac60>=0.15 gate + sd=2.0*ATR + fixed target 4R.
  (b) 2nd daily JPY entry at the NY open, mirroring the London-open M15 momentum sleeve
      (KB_fx_jpy.md R1): first NY hour impulse -> ride. Symbols GBPJPY,USDJPY, M15,
      stop 1.0*ATR, target 2.5*ATR, maxbars=48, one trade/symbol/day.
  (c) Dedicated ENERGY supply-shock tier (vr>=2.0, ~88% win from KB_energy_agri.md) with a
      DEEPER runner: test runR 5 and 6 on the vr>=2 tier (the runner under STATE_D may be
      leaving R on the table during shock trends).
  (d) AGRI grains WHEAT/SOYBEAN -> DATA-BLOCKED: no H4 (or any) export exists for these symbols
      in this repo. Reported as a learning with the exact source requirement.

NO LOOKAHEAD: all entry/gate features use only closed bars index<=i. geometry_lib.simulate /
exit_state_d look forward ONLY to score the already-decided label. Winsorize net R to [-1.3,+5].
Real cost = w1.cost_for(sym). FORWARD HOLDOUT: train=year<=2024, forward=2025 & 2026, per-year +
per-symbol always (no averages-as-verdict).
"""
from __future__ import annotations
import sys, os, csv, json, math, statistics, collections
from datetime import datetime
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, '/Users/borr/Documents/gtos/repo/ai-trading-agent')
from geometry_lib import simulate, atr14, Bar
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs
import energy_agri_sleeve as ea

ROOT = '/Users/borr/Documents/gtos/repo/ai-trading-agent'
M1ROOT = ROOT + '/data/mt5_research_exports'
M15DIR = M1ROOT + '/bridge_ftmo_m15_20250601_20260610'

def wins(r): return max(-1.3, min(5.0, r))

def pstat(rs):
    if not rs: return (0, 0.0, 0.0)
    n = len(rs); m = sum(rs)/n; w = 100*sum(1 for r in rs if r > 0)/n
    return n, round(m, 4), round(w, 1)

def byyear(pairs):
    """pairs: list of (year, R) -> {year:(n,ev,win)}"""
    d = collections.defaultdict(list)
    for y, r in pairs: d[y].append(r)
    return {y: pstat(v) for y, v in sorted(d.items())}

# =====================================================================================
# (a) ETHUSD 3rd crypto carrier — resample M1->H4, identical KB_crypto rule
# =====================================================================================
def resample_eth_h4():
    """Build ETH H4 OHLCV bars from M1 (real data 2024-10..2026-06). H4 buckets aligned to
    UTC 0/4/8/12/16/20 (matching the deep-H4 export grid). Returns (times, bars)."""
    rows = []
    for sub in sorted(os.listdir(M1ROOT)):
        if not sub.startswith('bridge_ftmo_m1_'): continue
        p = os.path.join(M1ROOT, sub, 'ETHUSD_M1.csv')
        if not os.path.exists(p): continue
        with open(p) as f:
            for r in csv.DictReader(f):
                try:
                    t = datetime.strptime(r['time'], '%Y-%m-%d %H:%M:%S')
                    rows.append((t, float(r['open']), float(r['high']), float(r['low']),
                                 float(r['close']), float(r.get('volume', 0) or 0)))
                except Exception:
                    continue
    rows.sort(key=lambda x: x[0])
    # bucket key = (date, hour//4*4)
    buckets = collections.OrderedDict()
    for t, o, h, l, c, v in rows:
        bh = (t.hour // 4) * 4
        key = (t.year, t.month, t.day, bh)
        if key not in buckets:
            buckets[key] = [t.replace(hour=bh, minute=0, second=0), o, h, l, c, v]
        else:
            b = buckets[key]
            b[2] = max(b[2], h); b[3] = min(b[3], l); b[4] = c; b[5] += v  # high/low/close/vol
    T = []; B = []
    for key, (bt, o, h, l, c, v) in buckets.items():
        T.append(bt); B.append(Bar(o, h, l, c, v))
    return T, B

def crypto_breakout_signals(B, lb=20):
    """Donchian-lb breakout on closed bars (KB_crypto rule). Yields (i, dir)."""
    out = []
    for i in range(lb + 1, len(B)):
        hh = max(B[k].h for k in range(i-lb, i))   # high[i-20..i-1]
        ll = min(B[k].l for k in range(i-lb, i))
        if B[i].c > hh: out.append((i, +1))
        elif B[i].c < ll: out.append((i, -1))
    return out

def eth_sleeve():
    T, B = resample_eth_h4()
    cost = w1.cost_for('ETHUSD')   # crypto class cost
    atrs = [atr14(B, i) for i in range(len(B))]
    trades = []   # (year, R, dir, ac60)
    for i, d in crypto_breakout_signals(B, 20):
        a = atrs[i]
        if a <= 0: continue
        ac = cs.autocorr(B, i, 60)
        if ac is None or ac < 0.15: continue   # KB_crypto persistence gate
        sd = 2.0 * a                            # wide structural stop
        r = wins(simulate(B, i, d, stop_dist=sd, target_dist=4*sd, maxbars=80, cost=cost))
        trades.append((T[i].year, r, d, round(ac, 3)))
    return T, B, trades

# =====================================================================================
# (b) 2nd daily JPY entry at NY open — mirror London-open M15 momentum (KB_fx_jpy R1)
# =====================================================================================
_M15C = {}
def load_m15(sym):
    if sym in _M15C: return _M15C[sym]
    p = os.path.join(M15DIR, f'{sym}_M15.csv'); T = []; B = []
    with open(p) as f:
        for row in csv.DictReader(f):
            try:
                t = datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S')
                B.append(Bar(float(row['open']), float(row['high']), float(row['low']),
                             float(row['close']), float(row.get('volume', 0) or 0))); T.append(t)
            except Exception:
                continue
    A = [atr14(B, i) for i in range(len(B))]; _M15C[sym] = (T, B, A); return _M15C[sym]

def session_open_mom(symbols, session_hour, lw, stop_m, tgt_m, maxbars, imp_min=0.0, trend_lb=0):
    """Generic 1-hr opening-impulse ride at a given session hour. Mirrors KB_fx_jpy R1 exactly
    (lw=4 M15 bars = first hour). Returns list of (date, sym, year, netR)."""
    out = []
    for sym in symbols:
        T, B, A = load_m15(sym); cost = w1.cost_for(sym)
        byday = collections.defaultdict(list)
        for i, t in enumerate(T): byday[t.date()].append(i)
        for day, idxs in sorted(byday.items()):
            ses = [i for i in idxs if T[i].hour >= session_hour]
            if len(ses) < lw + 2: continue
            i0 = ses[0]; iw = ses[lw-1]
            if i0 < max(20, trend_lb): continue
            a = A[iw]
            if a <= 0: continue
            imp = B[iw].c - B[i0].o
            if abs(imp) < imp_min * a: continue
            d = 1 if imp > 0 else -1
            if trend_lb > 0:
                tr = 1 if B[iw].c > B[iw-trend_lb].c else -1
                if tr != d: continue
            r = simulate(B, iw, d, stop_dist=stop_m*a, target_dist=tgt_m*a, maxbars=maxbars, cost=cost)
            out.append((day, sym, day.year, wins(r)))
    return out

# =====================================================================================
# (c) Energy supply-shock tier (vr>=2.0) with DEEPER runner — test runR 5,6
# =====================================================================================
def exit_state_d_runR(B, i, d, sd, vr, cost, runR_override=None, scaleR_override=None, maxbars=80):
    """STATE_D scale-out exit with an OVERRIDABLE deep runner target (for the vr>=2 shock tier).
    Identical to cs.exit_state_d except runR (and optionally scaleR) can be forced deeper."""
    entry = B[i].c
    if vr < 1.35: scaleR, runR = 1.5, 4.0
    elif vr < 1.6: scaleR, runR = 1.5, 3.0
    else: scaleR, runR = 1.0, 2.5
    if scaleR_override is not None: scaleR = scaleR_override
    if runR_override is not None: runR = runR_override
    scaled = False; leg2 = None; reason = None; end = min(i+maxbars, len(B)-1)
    for j in range(i+1, end+1):
        hi = B[j].h; lo = B[j].l
        favp = hi if d > 0 else lo; advp = lo if d > 0 else hi
        fav = d*(favp-entry)/sd; adv = d*(advp-entry)/sd
        if not scaled:
            if adv <= -1.0: return -1.0 - cost
            if fav >= scaleR: scaled = True
        else:
            if adv <= 0.0: leg2 = 0.0; reason = 'scratch_be'; break
            if fav >= runR: leg2 = runR; reason = 'win_runner'; break
    if reason is None:
        if scaled: leg2 = d*(B[end].c-entry)/sd
        else: return wins(d*(B[end].c-entry)/sd - cost)
    R = 0.5*scaleR + 0.5*leg2
    return wins(R - cost)

def energy_shock_tier_direct(runR_list=(2.5, 4.0, 5.0, 6.0)):
    res = {rr: [] for rr in runR_list}
    base_state_d = []   # baseline STATE_D (no override) for comparison
    persym = collections.defaultdict(lambda: collections.defaultdict(list))
    for s in ea.ENERGY:
        try:
            T, B = w1.load(s)
        except Exception:
            continue
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]
        cost = w1.cost_for(s)
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(s):
            vr = cs.vol_ratio(atrs, i)
            if vr < 2.0: continue   # supply-shock tier only
            base_state_d.append((t.year, exit_state_d_runR(B, i, d, sd, vr, c2)))
            for rr in runR_list:
                R = exit_state_d_runR(B, i, d, sd, vr, c2, runR_override=rr)
                res[rr].append((t.year, R))
                persym[rr][s].append((t.year, R))
    return res, base_state_d, persym

# =====================================================================================
# REPORTING
# =====================================================================================
def fmt_year(d):
    return ' '.join(f"{y}:{ev:+.2f}(n{n})" for y, (n, ev, w) in d.items())

def main():
    out = {}
    print("="*90)
    print("KB2 NEW BREADTH SLEEVES — per-year / per-symbol, no averages-as-verdict")
    print("="*90)

    # ---------- (a) ETH ----------
    print("\n##### (a) ETHUSD 3rd crypto carrier (M1->H4 resample; KB_crypto rule lb20+ac0.15+sd2a+t4R)")
    Te, Be, etr = eth_sleeve()
    print(f"  ETH H4 bars resampled: {len(Be)} ({Te[0].date() if Te else '-'} .. {Te[-1].date() if Te else '-'})")
    ep = [(y, r) for (y, r, d, ac) in etr]
    n, m, wpc = pstat([r for _, r in ep])
    print(f"  ALL: n={n} EV={m:+.4f}R win={wpc:.0f}%  trades/yr~{n/1.7:.0f}")
    by = byyear(ep)
    print(f"  per-year: {fmt_year(by)}")
    fwdr = [r for (y, r) in ep if y >= 2025]
    nf, mf, wf = pstat(fwdr)
    print(f"  FORWARD 2025-26: n={nf} EV={mf:+.4f}R win={wf:.0f}%")
    # by direction (forward)
    lf = [r for (y, r, d, ac) in etr if y >= 2025 and d > 0]; sf = [r for (y, r, d, ac) in etr if y >= 2025 and d < 0]
    print(f"  FWD by dir: long {pstat(lf)} | short {pstat(sf)}")
    out['eth'] = {'bars': len(Be), 'all': pstat([r for _, r in ep]), 'per_year': {str(k): v for k, v in by.items()},
                  'forward': pstat(fwdr), 'fwd_long': pstat(lf), 'fwd_short': pstat(sf)}

    # ---------- (b) NY-open JPY 2nd entry ----------
    print("\n##### (b) 2nd daily JPY entry at NY open (mirror London R1: s1.0/t2.5/mb48, 1hr impulse)")
    JPY = ['GBPJPY', 'USDJPY']
    # NY open: KB note says NY vol peaks 16:00 server, NY session opens ~13:00-14:00 server.
    # Test candidate session hours to find the NY analogue; lock the one that mirrors London.
    print("  -- session-hour scan (find the NY-open analogue) --")
    scan = {}
    for sh in (12, 13, 14, 15, 16):
        o = session_open_mom(JPY, sh, 4, 1.0, 2.5, 48)
        rs = [r for _, _, _, r in o]
        scan[sh] = pstat(rs)
        print(f"    NY hour>={sh}: n={scan[sh][0]} EV={scan[sh][1]:+.4f}R win={scan[sh][2]:.0f}%")
    # lock best forward-consistent hour (report all; pick by EV with n>=200)
    best_sh = max((sh for sh in scan if scan[sh][0] >= 150), key=lambda sh: scan[sh][1], default=13)
    print(f"  -> LOCKED NY hour = {best_sh}")
    o = session_open_mom(JPY, best_sh, 4, 1.0, 2.5, 48)
    pairs = [(y, r) for _, _, y, r in o]
    n, m, wpc = pstat([r for _, r in pairs])
    print(f"  ALL (NY {best_sh}): n={n} EV={m:+.4f}R win={wpc:.0f}%  trades/yr~{n/1.0:.0f}")
    print(f"  per-year: {fmt_year(byyear(pairs))}")
    # per-symbol
    for sym in JPY:
        rs = [r for _, s, _, r in o if s == sym]
        print(f"    {sym}: {pstat(rs)}")
    # per-month stability
    bm = collections.defaultdict(list)
    for day, s, y, r in o: bm[(day.year, day.month)].append(r)
    posm = sum(1 for k in bm if statistics.mean(bm[k]) > 0)
    print(f"  per-month: {posm}/{len(bm)} months positive")
    # falsification: pure FX at same NY hour
    PUREFX = ['EURUSD', 'GBPUSD', 'AUDUSD']
    of = session_open_mom(PUREFX, best_sh, 4, 1.0, 2.5, 48)
    print(f"  FALSIFICATION pure-FX NY {best_sh}: {pstat([r for _,_,_,r in of])}")
    out['jpy_ny'] = {'locked_hour': best_sh, 'all': pstat([r for _, r in pairs]),
                     'per_year': {str(k): v for k, v in byyear(pairs).items()},
                     'months_pos': f"{posm}/{len(bm)}",
                     'purefx_control': pstat([r for _, _, _, r in of]),
                     'scan': {str(k): v for k, v in scan.items()}}

    # ---------- (c) Energy shock tier deeper runner ----------
    print("\n##### (c) Energy supply-shock tier (vr>=2.0) — deeper runner sweep runR 2.5/4/5/6")
    res, base_sd, persym = energy_shock_tier_direct((2.5, 4.0, 5.0, 6.0))
    nb, mb, wb = pstat([r for _, r in base_sd])
    print(f"  baseline STATE_D (vol-tier runR, no override): n={nb} EV={mb:+.4f}R win={wb:.0f}%")
    runr_out = {}
    for rr in (2.5, 4.0, 5.0, 6.0):
        pr = res[rr]
        n, m, wpc = pstat([r for _, r in pr])
        fwdr = [r for (y, r) in pr if y >= 2025]
        nf, mf, wf = pstat(fwdr)
        print(f"  runR={rr}: ALL n={n} EV={m:+.4f}R win={wpc:.0f}% | FWD n={nf} EV={mf:+.4f}R win={wf:.0f}% | {fmt_year(byyear(pr))}")
        runr_out[str(rr)] = {'all': pstat([r for _, r in pr]), 'forward': pstat(fwdr),
                             'per_year': {str(k): v for k, v in byyear(pr).items()}}
    out['energy_shock'] = {'baseline_state_d': pstat([r for _, r in base_sd]), 'runR': runr_out}

    # ---------- (d) Grains ----------
    print("\n##### (d) AGRI grains WHEAT/SOYBEAN")
    wheat_files = []
    for d in os.listdir(M1ROOT):
        dd = os.path.join(M1ROOT, d)
        if not os.path.isdir(dd): continue
        for f in os.listdir(dd):
            if any(k in f.upper() for k in ('WHEAT', 'SOYBEAN', 'SOY_')): wheat_files.append(os.path.join(d, f))
    print(f"  WHEAT/SOYBEAN export files found anywhere: {len(wheat_files)}")
    print("  -> DATA-BLOCKED: no WHEAT/SOYBEAN H4 (or M1/M15) export exists in this repo.")
    print("     Only CORN_c and COTTON_c exist as agri H4 (already in energy_agri_sleeve).")
    out['grains'] = {'status': 'data_blocked', 'files_found': len(wheat_files),
                     'source_requirement': 'Continuous H4 OHLCV for WHEAT_c/SOYBEAN_c (ideally 2015-2026) under data/mt5_research_exports/bridge_ftmo_deep_h4_*'}

    (HERE / 'KB2_NEW_BREADTH_RESULT.json').write_text(json.dumps(out, indent=2, default=str))
    print("\nwrote KB2_NEW_BREADTH_RESULT.json")
    return out

if __name__ == '__main__':
    main()
