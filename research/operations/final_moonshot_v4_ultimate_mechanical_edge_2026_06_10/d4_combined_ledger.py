"""d4_combined_ledger.py  (track key: D4 — standing per-trade improvement miner)

REGENERATE a single COMBINED per-trade ledger across ALL forward-positive sleeves
(metals_core, metals_softband, metals_ob_micro, crypto, energy_agri, idxrev, fx_jpy),
each row carrying:  STATE (leak-free, index<=i)  +  OUTCOME (winsorized net R, exit reason,
mfe/mae/bars-to-1R)  +  a per-trade DIAGNOSIS string.

The ledger ALSO stores, for every trade, the EXACT re-simulation coordinates
(stream key, entry index, direction, stop_dist, vol_ratio, cost) so the improvement
miner can RE-RUN alternative geometry/exit policies through geometry_lib (leak-free) on
the same entries — not merely re-slice the realized R. Gate-threshold experiments only
need the stored state features.

This is the canonical D4 ledger. It reuses INTEG_portfolio_build's sleeve definitions so
the trade UNIVERSE is identical to the deployed portfolio (no double counting, same dedup).

NO LOOKAHEAD: all state features computed from closed bars index<=i. Outcomes scored by
geometry_lib.simulate / cs.exit_state_d which look forward ONLY to label an already-decided
trade. Winsorize net R to [-1.3, +5] (cs.wins / exit_state_d already do). Real cost via
w1.cost_for, scaled by stop tightness where a sleeve re-sims at a non-1R stop.
"""
from __future__ import annotations
import sys, os, csv, json, math, statistics, collections, datetime
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate, atr14, Bar
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs
import csb_commodity_setups as csb
import multitf_lib as m
import INTEG_portfolio_build as INTEG

def wins(r): return max(-1.3, min(5.0, r))

# ---------------------------------------------------------------------------
# STATE FEATURE BLOCK — computed once per (B, i) from closed bars only.
# These are the dimensions the miner conditions on. All leak-free.
# ---------------------------------------------------------------------------
def state_features(B, i, d, atrs=None):
    a = atrs[i] if atrs is not None else atr14(B, i)
    f = {}
    f['ac60'] = cs.autocorr(B, i, 60)
    f['vr'] = cs.vol_ratio(atrs, i) if atrs is not None else None
    # trend / slope (ATR-normalized) over 30 closed bars
    if i >= 30 and a > 0:
        f['slope30'] = (B[i].c - B[i-30].c) / a
    else:
        f['slope30'] = 0.0
    f['htf_trend'] = w1.htf_trend(B, i, 30)
    f['aligned'] = int(f['htf_trend'] == d)            # signal with HTF trend?
    # range position over trailing 50 closed bars
    if i >= 50:
        hi50 = max(B[k].h for k in range(i-50, i)); lo50 = min(B[k].l for k in range(i-50, i))
        f['rng_pos'] = (B[i].c - lo50) / (hi50 - lo50) if hi50 > lo50 else 0.5
    else:
        f['rng_pos'] = 0.5
    # short momentum
    if i >= 5 and a > 0:
        f['ret5'] = (B[i].c - B[i-5].c) / a
    else:
        f['ret5'] = 0.0
    # bar body strength relative to ATR
    f['body'] = abs(B[i].c - B[i].o) / a if a > 0 else 0.0
    return f


# ---------------------------------------------------------------------------
# RE-SIM HOOK — every row stores how to re-simulate it under a new policy.
# stream registry maps stream_key -> (T, B) so the miner can reconstruct.
# For metals_core the scored stream is the lower-TF fill stream (H1/M15) or H4.
# ---------------------------------------------------------------------------
_STREAMS = {}   # stream_key -> (T, B)  (filled during build, reused by miner)

def _reg_stream(key, T, B):
    if key not in _STREAMS:
        _STREAMS[key] = (T, B)

def stream(key):
    return _STREAMS.get(key)


# ===========================================================================
# SLEEVE BUILDERS — re-derive each INTEG sleeve but emit RICH rows.
# Each row dict: sleeve, sym, date(iso), year, month, dir, <state...>,
#   R (winsorized net), reason, mfe, mae, bars1R, base2R, diag,
#   resim: {kind, stream, idx, d, sd, vr, cost, maxbars, intra_size}
# kind in {'state_d','fixed'} tells the miner which exit family produced R and
# how to re-simulate alternatives.
# ===========================================================================

def _diag_state_d(sel, ex, base2R):
    if not sel:
        return 'rejected_low_persistence' + ('|missed_winner' if base2R and base2R > 0 else '|correctly_avoided')
    r = ex['reason']
    if r == 'full_stop':
        return 'loss_full' + ('|early_dead' if ex['bars1R'] is None else '') + ('|stop_vs_mfe' if ex['mfe'] > 0.9 else '')
    if r == 'scratch_be': return 'scratch_be|gaveback' if ex['mfe'] > 1.6 else 'scratch_be'
    if r == 'win_runner': return 'win_runner'
    if r in ('win_partial', 'partial_flat'): return 'win_partial' if ex['R'] > 0 else 'partial_flat'
    return r


def build_metals_core():
    """MTF H1->M15 cascade exit on ac60>=0.10 FVG entries (the deepest, train-validated edge).
    Re-sim coordinates point at the actual lower-TF stream the trade was scored on."""
    rows = []
    for sym in cs.METALS:
        sigs = INTEG._metals_h4_signals(sym)
        T1, B1 = m.load_ltf(sym, "H1"); have1 = len(B1) > 50
        T15, B15 = m.load_ltf(sym, "M15"); have15 = len(B15) > 50
        if have1: _reg_stream(('metals_core', sym, 'H1'), T1, B1)
        if have15: _reg_stream(('metals_core', sym, 'M15'), T15, B15)
        T_h4, B_h4_full = w1.load(sym); _reg_stream(('metals_core', sym, 'H4'), T_h4, B_h4_full)
        atrs_h4 = [atr14(B_h4_full, k) for k in range(len(B_h4_full))]
        for (t, d, sd_h4, i_h4, B_h4, vr, cost, ac) in sigs:
            ex_h4 = cs.exit_state_d(B_h4, i_h4, d, sd_h4, vr, cost)
            base_R = ex_h4['R']
            ts = t + datetime.timedelta(hours=4); sc = B_h4[i_h4].c
            R = base_R; filled = False; skey = ('metals_core', sym, 'H4'); ej = i_h4
            mb = 80
            if have1:
                si = m.first_ltf_index_after(T1, ts)
                if si is not None and 30 <= si < len(B1) - 2:
                    e = INTEG._find_fill(B1, T1, si, d, sc, 12, 1.0, ts)
                    if e is not None:
                        ex = cs.exit_state_d(B1, e, d, sd_h4, vr, cost, maxbars=INTEG.H1_MAXBARS)
                        R = ex['R']; filled = True; skey = ('metals_core', sym, 'H1'); ej = e; mb = INTEG.H1_MAXBARS
            if not filled and have15:
                si = m.first_ltf_index_after(T15, ts)
                if si is not None and 30 <= si < len(B15) - 2:
                    e = INTEG._find_fill(B15, T15, si, d, sc, 48, 1.0, ts)
                    if e is not None:
                        ex = cs.exit_state_d(B15, e, d, sd_h4, vr, cost, maxbars=1280)
                        R = ex['R']; filled = True; skey = ('metals_core', sym, 'M15'); ej = e; mb = 1280
            # re-score on the chosen stream to recover mfe/mae/reason/bars1R for the row
            Ts, Bs = stream(skey); ex_final = cs.exit_state_d(Bs, ej, d, sd_h4, vr, cost, maxbars=mb)
            base2R = wins(simulate(Bs, ej, d, stop_dist=sd_h4, target_dist=2*sd_h4, maxbars=mb, cost=cost))
            sf = state_features(B_h4, i_h4, d, atrs_h4)        # state from the H4 decision bar
            rows.append(dict(
                sleeve='metals_core', sym=sym, date=str(t.date()), year=t.year, month=t.month, dir=d,
                ac60=round(ac, 4), vr=round(vr, 3), slope30=round(sf['slope30'], 4),
                htf_trend=sf['htf_trend'], aligned=sf['aligned'], rng_pos=round(sf['rng_pos'], 3),
                ret5=round(sf['ret5'], 4), body=round(sf['body'], 3), hour=t.hour, dow=t.weekday(),
                R=round(wins(R), 4), reason=ex_final['reason'], mfe=round(ex_final['mfe'], 3),
                mae=round(ex_final['mae'], 3), bars1R=ex_final['bars1R'], base2R=round(base2R, 4),
                diag=_diag_state_d(True, ex_final, base2R),
                resim=dict(kind='state_d', stream=list(skey), idx=ej, d=d, sd=sd_h4, vr=round(vr, 6),
                           cost=cost, maxbars=mb),
            ))
    return rows


def build_metals_softband():
    """freqbreadth FVG soft-ramp, ONLY 0.04<=ac60<0.10 (disjoint from core). STATE_D exit."""
    rows = []
    for sym in cs.METALS:
        T, B = w1.load(sym)
        if len(B) < 200: continue
        _reg_stream(('metals_softband', sym, 'H4'), T, B)
        atrs = [atr14(B, k) for k in range(len(B))]; cost = w1.cost_for(sym)
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym):
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac >= cs.AC_THR or ac < INTEG.AC_FLOOR_SB: continue
            vr = cs.vol_ratio(atrs, i); sm = INTEG._size_mult_soft(ac, vr)
            if sm <= 0: continue
            ex = cs.exit_state_d(B, i, d, sd, vr, c2)
            base2R = wins(simulate(B, i, d, stop_dist=sd, target_dist=2*sd, cost=c2))
            sf = state_features(B, i, d, atrs)
            rows.append(dict(
                sleeve='metals_softband', sym=sym, date=str(t.date()), year=t.year, month=t.month, dir=d,
                ac60=round(ac, 4), vr=round(vr, 3), slope30=round(sf['slope30'], 4),
                htf_trend=sf['htf_trend'], aligned=sf['aligned'], rng_pos=round(sf['rng_pos'], 3),
                ret5=round(sf['ret5'], 4), body=round(sf['body'], 3), hour=t.hour, dow=t.weekday(),
                R=round(wins(ex['R']), 4), reason=ex['reason'], mfe=round(ex['mfe'], 3),
                mae=round(ex['mae'], 3), bars1R=ex['bars1R'], base2R=round(base2R, 4), intra_size=sm,
                diag=_diag_state_d(True, ex, base2R),
                resim=dict(kind='state_d', stream=['metals_softband', sym, 'H4'], idx=i, d=d, sd=sd,
                           vr=round(vr, 6), cost=c2, maxbars=80, intra_size=sm),
            ))
    return rows


def build_metals_ob_micro():
    """OB-retest, ac60>=0.20 only, dedup vs FVG. STATE_D exit."""
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
        _reg_stream(('metals_ob_micro', sym, 'H4'), T, B)
        A = csb._atrs(B); cost = w1.cost_for(sym)
        for (t, d, sd, i, B2, c2) in csb.SETUPS['OB'](sym):
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac < 0.20: continue
            if (sym, str(t.date()), d) in fvg_keys: continue
            vr = cs.vol_ratio(A, i); ex = cs.exit_state_d(B, i, d, sd, vr, c2)
            base2R = wins(simulate(B, i, d, stop_dist=sd, target_dist=2*sd, cost=c2))
            sf = state_features(B, i, d, A)
            rows.append(dict(
                sleeve='metals_ob_micro', sym=sym, date=str(t.date()), year=t.year, month=t.month, dir=d,
                ac60=round(ac, 4), vr=round(vr, 3), slope30=round(sf['slope30'], 4),
                htf_trend=sf['htf_trend'], aligned=sf['aligned'], rng_pos=round(sf['rng_pos'], 3),
                ret5=round(sf['ret5'], 4), body=round(sf['body'], 3), hour=t.hour, dow=t.weekday(),
                R=round(wins(ex['R']), 4), reason=ex['reason'], mfe=round(ex['mfe'], 3),
                mae=round(ex['mae'], 3), bars1R=ex['bars1R'], base2R=round(base2R, 4),
                diag=_diag_state_d(True, ex, base2R),
                resim=dict(kind='state_d', stream=['metals_ob_micro', sym, 'H4'], idx=i, d=d, sd=sd,
                           vr=round(vr, 6), cost=c2, maxbars=80),
            ))
    return rows


def build_crypto():
    """BTCUSD/DASHUSD 20-bar breakout, ac60>=0.15, fixed stop 2*ATR target 4R."""
    rows = []
    for sym in ('BTCUSD', 'DASHUSD'):
        try: T, B = w1.load(sym)
        except Exception: continue
        if len(B) < 80: continue
        _reg_stream(('crypto', sym, 'H4'), T, B)
        cost = w1.cost_for(sym); atrs = [atr14(B, k) for k in range(len(B))]
        for i in range(60, len(B) - 1):
            a = atrs[i]
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
            vr = cs.vol_ratio(atrs, i); sf = state_features(B, i, d, atrs)
            rows.append(dict(
                sleeve='crypto', sym=sym, date=str(T[i].date()), year=T[i].year, month=T[i].month, dir=d,
                ac60=round(ac, 4), vr=round(vr, 3), slope30=round(sf['slope30'], 4),
                htf_trend=sf['htf_trend'], aligned=sf['aligned'], rng_pos=round(sf['rng_pos'], 3),
                ret5=round(sf['ret5'], 4), body=round(sf['body'], 3), hour=T[i].hour, dow=T[i].weekday(),
                R=round(wins(R), 4), reason='fixed_4R', mfe=None, mae=None, bars1R=None,
                base2R=round(wins(simulate(B, i, d, stop_dist=sd, target_dist=2*sd, cost=cost)), 4),
                diag='win_fixed' if R > 0 else 'loss_fixed',
                resim=dict(kind='fixed', stream=['crypto', sym, 'H4'], idx=i, d=d, sd=sd, vr=round(vr, 6),
                           cost=cost, maxbars=80, target_R=4.0),
            ))
    return rows


def build_idxrev():
    """Index failed-breakout fade, fixed stop 1.5*ATR target 0.75R, maxbars 60. (2024+ data.)"""
    rows = []
    LB = 16; STOP_ATR = 1.5; TGT_R = 0.75; MAXBARS = 60
    for sym in INTEG.IDX_POCKET:
        try: T, B = w1.load(sym)
        except Exception: continue
        if len(B) < 150: continue
        _reg_stream(('idxrev', sym, 'H4'), T, B)
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
            vr = cs.vol_ratio(atrs, i); sf = state_features(B, i, d, atrs)
            rows.append(dict(
                sleeve='idxrev', sym=sym, date=str(T[i].date()), year=T[i].year, month=T[i].month, dir=d,
                ac60=round(sf['ac60'], 4) if sf['ac60'] is not None else None, vr=round(vr, 3),
                slope30=round(sf['slope30'], 4), htf_trend=sf['htf_trend'], aligned=sf['aligned'],
                rng_pos=round(sf['rng_pos'], 3), ret5=round(sf['ret5'], 4), body=round(sf['body'], 3),
                hour=T[i].hour, dow=T[i].weekday(),
                R=round(wins(R), 4), reason='fixed_0p75R', mfe=None, mae=None, bars1R=None,
                base2R=round(wins(simulate(B, i, d, stop_dist=sd, target_dist=2*sd, maxbars=MAXBARS, cost=rcost)), 4),
                diag='win_fade' if R > 0 else 'loss_fade',
                resim=dict(kind='fixed', stream=['idxrev', sym, 'H4'], idx=i, d=d, sd=sd, vr=round(vr, 6),
                           cost=rcost, maxbars=MAXBARS, target_R=TGT_R),
            ))
    return rows


def build_fx_jpy():
    """GBPJPY/USDJPY London-open momentum (M15), fixed stop 1*ATR target 2.5R, maxbars 48."""
    rows = []
    for sym in ('GBPJPY', 'USDJPY'):
        T, B, A = INTEG._load_fx_m15(sym); cost = w1.cost_for(sym)
        if len(B) < 100: continue
        _reg_stream(('fx_jpy', sym, 'M15'), T, B)
        byday = collections.defaultdict(list)
        for i, t in enumerate(T): byday[t.date()].append(i)
        for day, idxs in sorted(byday.items()):
            lon = [i for i in idxs if T[i].hour >= 8]
            if len(lon) < 6: continue
            i0 = lon[0]
            if i0 < 20: continue
            iw = lon[3]; a = A[iw]
            if a <= 0: continue
            d = 1 if B[iw].c > B[i0].o else -1
            sd = 1.0 * a
            R = simulate(B, iw, d, stop_dist=sd, target_dist=2.5 * sd, maxbars=48, cost=cost)
            vr = cs.vol_ratio(A, iw); sf = state_features(B, iw, d, A)
            rows.append(dict(
                sleeve='fx_jpy', sym=sym, date=str(day), year=T[iw].year, month=T[iw].month, dir=d,
                ac60=round(sf['ac60'], 4) if sf['ac60'] is not None else None, vr=round(vr, 3),
                slope30=round(sf['slope30'], 4), htf_trend=sf['htf_trend'], aligned=sf['aligned'],
                rng_pos=round(sf['rng_pos'], 3), ret5=round(sf['ret5'], 4), body=round(sf['body'], 3),
                hour=T[iw].hour, dow=T[iw].weekday(),
                R=round(wins(R), 4), reason='fixed_2p5R', mfe=None, mae=None, bars1R=None,
                base2R=round(wins(simulate(B, iw, d, stop_dist=sd, target_dist=2*sd, maxbars=48, cost=cost)), 4),
                diag='win_fixed' if R > 0 else 'loss_fixed',
                resim=dict(kind='fixed', stream=['fx_jpy', sym, 'M15'], idx=iw, d=d, sd=sd, vr=round(vr, 6),
                           cost=cost, maxbars=48, target_R=2.5),
            ))
    return rows


BUILDERS = {
    'metals_core': build_metals_core,
    'metals_softband': build_metals_softband,
    'metals_ob_micro': build_metals_ob_micro,
    'crypto': build_crypto,
    'energy_agri': None,        # special — needs both gate tag + raw resim, built below
    'idxrev': build_idxrev,
    'fx_jpy': build_fx_jpy,
}


def build_energy_agri():
    """ENERGY+AGRI locked-gate sleeve (STATE_D exit). Re-derive with full state + resim coords.
    Reuses energy_agri_sleeve gates so the universe matches the deployed sleeve exactly."""
    import energy_agri_sleeve as ea
    rows = []
    cand = ea.build_candidates()
    sleeve = ea.final_sleeve(cand)                     # tagged + confidence
    # index tagged trades by (sym,date,dir) so we attach tag/conf and resim coords
    tagmap = {(r['sym'], r['date'], r['dir']): r for r in sleeve}
    # re-walk signals to recover entry index i for resim (build_candidates dropped i)
    for grp, syms in (('energy', ea.ENERGY), ('agri', ea.AGRI)):
        for s in syms:
            try: T, B = w1.load(s)
            except Exception: continue
            if len(B) < 200: continue
            _reg_stream(('energy_agri', s, 'H4'), T, B)
            atrs = [atr14(B, k) for k in range(len(B))]; cost = w1.cost_for(s)
            for (t, d, sd, td, i, B2, c2) in g.fvg_signals(s):
                key = (s, str(t.date()), d)
                if key not in tagmap: continue          # not in the gated sleeve
                tr_row = tagmap[key]
                ac = cs.autocorr(B, i, 60); vr = cs.vol_ratio(atrs, i)
                ex = cs.exit_state_d(B, i, d, sd, vr, c2)
                base2R = wins(simulate(B, i, d, stop_dist=sd, target_dist=2*sd, cost=c2))
                sf = state_features(B, i, d, atrs)
                rows.append(dict(
                    sleeve='energy_agri', sym=s, date=str(t.date()), year=t.year, month=t.month, dir=d,
                    ac60=round(ac, 4) if ac is not None else None, vr=round(vr, 3),
                    slope30=round(sf['slope30'], 4), htf_trend=sf['htf_trend'], aligned=sf['aligned'],
                    rng_pos=round(sf['rng_pos'], 3), ret5=round(sf['ret5'], 4), body=round(sf['body'], 3),
                    hour=t.hour, dow=t.weekday(), tag=tr_row['tag'], intra_size=tr_row['conf'],
                    R=round(wins(ex['R']), 4), reason=ex['reason'], mfe=round(ex['mfe'], 3),
                    mae=round(ex['mae'], 3), bars1R=ex['bars1R'], base2R=round(base2R, 4),
                    diag=_diag_state_d(True, ex, base2R),
                    resim=dict(kind='state_d', stream=['energy_agri', s, 'H4'], idx=i, d=d, sd=sd,
                               vr=round(vr, 6), cost=c2, maxbars=80, intra_size=tr_row['conf']),
                ))
    return rows

BUILDERS['energy_agri'] = build_energy_agri


def build_all():
    led = []
    for name, fn in BUILDERS.items():
        rows = fn()
        led.extend(rows)
        print(f"  {name:>16}: {len(rows):>5} rows", flush=True)
    return led


def main():
    print("Regenerating COMBINED per-trade ledger across ALL sleeves...")
    led = build_all()
    out = HERE / 'D4_COMBINED_TRADE_LEDGER.jsonl'
    out.write_text('\n'.join(json.dumps(r) for r in led))
    print(f"\nwrote {out.name}  ({len(led)} per-trade rows w/ state+outcome+diagnosis+resim coords)")
    # quick per-sleeve, per-year sanity (never a bulk verdict)
    by = collections.defaultdict(list)
    for r in led: by[r['sleeve']].append(r)
    print("\n=== per-sleeve forward holdout sanity (train<=2024 / fwd 2025-26) ===")
    for name in BUILDERS:
        rs = by[name]
        if not rs: continue
        tr = [r for r in rs if r['year'] <= 2024]; fw = [r for r in rs if r['year'] >= 2025]
        def ev(x): return (len(x), round(sum(r['R'] for r in x)/len(x), 3)) if x else (0, 0.0)
        print(f"  {name:>16}: n={len(rs):>4}  train{ev(tr)}  fwd{ev(fw)}")
    return led


if __name__ == '__main__':
    main()
