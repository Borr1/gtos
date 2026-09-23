"""KB3 — re-validate the D4 miner's metals_core / metals_softband / ETH harvest items IN
ISOLATION on the DEPLOYED cascade fill stream (not the raw H4 stream the miner ran on), so the
keep/learning verdict is apples-to-apples with what actually ships in the book.

Doctrine: TRAIN year<=2024 -> FORWARD 2025/2026 + per-year. winsorize R[-1.3,+5]. real cost.
leak-free features (index<=i). EXEC_COMBO/STATE_D label forward only.

Items revalidated here (the ones NOT already in the W2 book):
  M1. metals_core confidence-size by entry-vol (full vr<=1.35, half-ish vr>1.6)  [+2.02R loc]
  M2. metals_core EXEC_COMBO vol-banded profit-lock exit (replaces STATE_D)       [+1.04R]
  M3. metals_core body<=0.374 small-bar entry filter
  M4. metals_softband body<=0.431 small-bar entry filter
  E1. ETH ac>=0.10 carrier + ac>=0.20 hi-conviction size tier (vs current ac>=0.15 flat)
Stacking: M1+M2+M3 combined on the same entries.
"""
import sys, json, datetime, statistics, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate, atr14, Bar
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs
import multitf_lib as m
import INTEG_portfolio_build as I
import kb2_new_breadth as KB
import EXEC_exit_variants as EX

def wins(r): return max(-1.3, min(5.0, r))
H1_MAXBARS = 320

# ---------------------------------------------------------------------------
# Build deployed metals_core cascade entries, carrying state (vr, body) + the
# fill stream + fill index so we can re-exit with STATE_D or EXEC_COMBO.
# ---------------------------------------------------------------------------
def metals_core_entries():
    ents = []
    for sym in cs.METALS:
        T, B = w1.load(sym)
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]
        T1, B1 = m.load_ltf(sym, "H1"); have1 = len(B1) > 50
        T15, B15 = m.load_ltf(sym, "M15"); have15 = len(B15) > 50
        for (t, d, sd_h4, td, i_h4, B_h4, cost) in g.fvg_signals(sym):
            ac = cs.autocorr(B, i_h4, 60)
            if ac is None or ac < cs.AC_THR: continue
            vr = cs.vol_ratio(atrs, i_h4)
            a = atrs[i_h4]
            body = abs(B[i_h4].c - B[i_h4].o) / a if a > 0 else 0.0   # leak-free, == d4 ledger
            # resolve the deployed fill stream (H1 preferred, else M15, else H4)
            ts = t + datetime.timedelta(hours=4); sc = B_h4[i_h4].c
            stream = B_h4; fi = i_h4; maxbars = 80; filled = False
            if have1:
                si = m.first_ltf_index_after(T1, ts)
                if si is not None and 30 <= si < len(B1) - 2:
                    ej = I._find_fill(B1, T1, si, d, sc, 12, 1.0, ts)
                    if ej is not None:
                        stream, fi, maxbars, filled = B1, ej, H1_MAXBARS, True
            if not filled and have15:
                si = m.first_ltf_index_after(T15, ts)
                if si is not None and 30 <= si < len(B15) - 2:
                    ej = I._find_fill(B15, T15, si, d, sc, 48, 1.0, ts)
                    if ej is not None:
                        stream, fi, maxbars = B15, ej, 1280
            # cost scaled by stop tightness (same convention as EXEC + cs)
            cs_scaled = cost * (0.5 * a / sd_h4) if sd_h4 > 0 else cost
            ents.append(dict(sym=sym, year=t.year, date=str(t)[:10], d=d, sd=sd_h4, vr=vr, ac=ac,
                             body=body, stream=stream, fi=fi, maxbars=maxbars, cost=cost,
                             cost_scaled=cs_scaled))
    return ents

def exit_state_d_R(e):
    return wins(cs.exit_state_d(e['stream'], e['fi'], e['d'], e['sd'], e['vr'], e['cost'], maxbars=e['maxbars'])['R'])

def exit_combo_R(e):
    """EXEC_COMBO: scale 50% @ +2.0R, vol-banded profit-lock runner stop, vol-banded runner target."""
    ent = dict(B=e['stream'], i=e['fi'], d=e['d'], sd=e['sd'], cost=e['cost_scaled'], vr=e['vr'])
    ex = EX.sim_exit(ent, ladder=[(2.0, 0.5)], be_after_first=None,
                     runner_R_map=(4.0, 3.0, 2.5), maxbars=e['maxbars'])
    # vol-banded lock: be_after_first must vary by vr -> set per-regime below
    return ex

def exit_combo_R_banded(e):
    """EXEC_COMBO with the vol-banded LOCK (0.25/0.5/0.75) — sim_exit's be_after_first is scalar,
    so resolve the lock by vr here and pass it in."""
    vr = e['vr']
    lock = 0.25 if vr < 1.35 else (0.5 if vr < 1.6 else 0.75)
    ent = dict(B=e['stream'], i=e['fi'], d=e['d'], sd=e['sd'], cost=e['cost_scaled'], vr=vr)
    ex = EX.sim_exit(ent, ladder=[(2.0, 0.5)], be_after_first=lock,
                     runner_R_map=(4.0, 3.0, 2.5), maxbars=e['maxbars'])
    return wins(ex['R'])

def vr_size(vr):
    """Confidence size by entry-vol: full size low-vol, half size high-vol (KB2 localization)."""
    if vr <= 1.35: return 1.0
    if vr <= 1.6:  return 0.75
    return 0.5

# ---------------------------------------------------------------------------
def scorecard(rows, label):
    """rows: list of dict(year, R, [size]). report TRAIN<=2024 + per-year FWD."""
    def ev(rs):
        if not rs: return (0, 0.0, 0.0)
        n = len(rs); m_ = sum(r['R'] for r in rs)/n
        w = sum(1 for r in rs if r['R']>0)/n*100
        return (n, round(m_,4), round(w,1))
    def ev_sized(rs):
        if not rs: return (0, 0.0)
        n = len(rs); tot = sum(r['R']*r.get('size',1.0) for r in rs)
        sz = sum(r.get('size',1.0) for r in rs)
        return (n, round(tot/sz,4) if sz else 0.0)   # size-weighted EV per unit risk
    tr = [r for r in rows if r['year']<=2024]
    f25 = [r for r in rows if r['year']==2025]; f26 = [r for r in rows if r['year']==2026]
    fwd = [r for r in rows if r['year']>=2025]
    out = dict(label=label, train=ev(tr), y2025=ev(f25), y2026=ev(f26), fwd=ev(fwd),
               train_sized=ev_sized(tr), fwd_sized=ev_sized(fwd))
    print(f"{label:<34} TRAIN {out['train'][1]:+.3f}(n{out['train'][0]}) | "
          f"2025 {out['y2025'][1]:+.3f}(n{out['y2025'][0]}) | 2026 {out['y2026'][1]:+.3f}(n{out['y2026'][0]}) | "
          f"FWD {out['fwd'][1]:+.3f}(n{out['fwd'][0]}) w{out['fwd'][2]:.0f}%")
    if any(r.get('size',1.0)!=1.0 for r in rows):
        print(f"{'  -> size-weighted EV/unit-risk':<34} TRAIN {out['train_sized'][1]:+.3f} | FWD {out['fwd_sized'][1]:+.3f}")
    return out

def main():
    rep = {}
    print("Building metals_core deployed cascade entries...")
    ME = metals_core_entries()
    print(f"metals_core entries: {len(ME)}\n")

    # baseline = STATE_D on the cascade stream (== deployed metals_core)
    base = [dict(year=e['year'], R=exit_state_d_R(e)) for e in ME]
    rep['M_baseline_state_d'] = scorecard(base, "M0 baseline STATE_D (deployed)")

    # M2: EXEC_COMBO exit (banded lock)
    combo = [dict(year=e['year'], R=exit_combo_R_banded(e)) for e in ME]
    rep['M2_exec_combo'] = scorecard(combo, "M2 EXEC_COMBO exit")

    # M1: confidence-size by entry-vol (on STATE_D baseline exit)
    vsize = [dict(year=e['year'], R=exit_state_d_R(e), size=vr_size(e['vr'])) for e in ME]
    rep['M1_vr_size'] = scorecard(vsize, "M1 vr-size (STATE_D)")

    # M3: body<=0.374 entry filter (on STATE_D)
    body = [dict(year=e['year'], R=exit_state_d_R(e)) for e in ME if e['body'] <= 0.374]
    bodydrop = [dict(year=e['year'], R=exit_state_d_R(e)) for e in ME if e['body'] > 0.374]
    rep['M3_body_keep'] = scorecard(body, "M3 body<=0.374 KEEP")
    rep['M3_body_drop'] = scorecard(bodydrop, "M3 body>0.374 DROP-bucket (keep small)")

    # STACK: M1 (vr-size) + M2 (combo) + M3 (body filter on full size; drop bucket small size)
    stack = []
    for e in ME:
        R = exit_combo_R_banded(e)
        sz = vr_size(e['vr'])
        if e['body'] > 0.374: sz *= 0.5   # small-bar: full conf; big-bar: half (keep, don't delete)
        stack.append(dict(year=e['year'], R=R, size=sz))
    rep['M_STACK_combo_vrsize_body'] = scorecard(stack, "STACK combo+vrsize+body-conf")

    # also the pure stacked LOCALIZATION the miner reported: vr<=1.28 gate + exec_combo
    loc = [dict(year=e['year'], R=exit_combo_R_banded(e)) for e in ME if e['vr'] <= 1.281]
    rep['M_localized_vr128_combo'] = scorecard(loc, "LOC vr<=1.281 + combo (miner +2.28)")

    # ---- metals_softband body<=0.431 ----
    print("\nBuilding metals_softband entries...")
    SB = []
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
            R = wins(cs.exit_state_d(B, i, d, sd, vr, c2)['R'])
            SB.append(dict(year=t.year, R=R, body=body, size=sm))
    rep['SB_baseline'] = scorecard([dict(year=r['year'],R=r['R'],size=r['size']) for r in SB], "SB0 baseline softband")
    sbkeep = [dict(year=r['year'],R=r['R'],size=r['size']) for r in SB if r['body']<=0.431]
    sbdrop = [dict(year=r['year'],R=r['R'],size=r['size']) for r in SB if r['body']>0.431]
    rep['SB_body_keep'] = scorecard(sbkeep, "SB body<=0.431 KEEP")
    rep['SB_body_drop'] = scorecard(sbdrop, "SB body>0.431 DROP-bucket")

    # ---- ETH ac>=0.10 carrier + ac>=0.20 size tier (vs current ac>=0.15 flat) ----
    print("\nBuilding ETH carriers at varying ac floors...")
    T, B = KB.resample_eth_h4(); cost = w1.cost_for('ETHUSD')
    atrs = [atr14(B, k) for k in range(len(B))]
    eth = []
    for (i, dd) in KB.crypto_breakout_signals(B, 20):
        a = atrs[i]
        if a <= 0: continue
        ac = cs.autocorr(B, i, 60)
        if ac is None: continue
        sd = 2.0 * a
        R = wins(simulate(B, i, dd, stop_dist=sd, target_dist=4*sd, maxbars=80, cost=cost))
        eth.append(dict(year=T[i].year, R=R, ac=ac))
    for flo in (0.10, 0.15):
        rows = [dict(year=r['year'], R=r['R']) for r in eth if r['ac'] >= flo]
        rep[f'ETH_ac{int(flo*100)}'] = scorecard(rows, f"ETH ac>={flo} flat (n carrier)")
    # ac>=0.10 carrier with ac>=0.20 hi-conviction 1.5x size tier
    tier = []
    for r in eth:
        if r['ac'] < 0.10: continue
        sz = 1.5 if r['ac'] >= 0.20 else 1.0
        tier.append(dict(year=r['year'], R=r['R'], size=sz))
    rep['ETH_ac10_tier20'] = scorecard(tier, "ETH ac>=0.10 + ac>=0.20 x1.5 tier")

    (HERE/'KB3_REVALIDATE_METALS_RESULT.json').write_text(json.dumps(rep, indent=1, default=str))
    print("\nwrote KB3_REVALIDATE_METALS_RESULT.json")

if __name__ == '__main__':
    main()
