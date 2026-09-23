"""RGATE_substrate_gate.py — Track: REGIME-GATE / SIZE the existing book by the substrate.

GOAL (per brief): compose substrate.best_cell as a confluence GATE + sizer on the
EXISTING validated CORE sleeves (metals_core, crypto, energy_agri):
  - take a sleeve trade ONLY when the live state's DEEPEST forward-validated
    substrate cell (queried at the EXACT entry bar i, in the trade's direction d)
    is +EV (min(train,fwd) mean_R > 0);
  - SIZE by min(train,fwd) mean_R (size-by-confidence; never delete).
Then measure gated-vs-ungated book forward EV + stress P(pass), forward per-year.

LEAK-FREE: the substrate state at bar i is computed on bars[:i+1] (substrate.build_states
already guarantees byte-identical leak-free state). The book trade enters at close[i].
The substrate cell stats are TRAIN(<=2024)/FORWARD(2025-26) holdout cells — but note the
honest caveat in section "GATE LEAKAGE AUDIT": the cell a state maps to was MINED on a map
that INCLUDES forward rows. We therefore ALSO run a strict TRAIN-ONLY-map variant: gate by
a substrate map mined on <=2024 rows only, so the forward gate decision uses NO forward
information at all. Both are reported; the train-only-map is the honest forward proof.

Re-derives entry (bar i, direction d) by RE-RUNNING each CORE sleeve's own signal+exit
logic (verbatim code paths) and validates the resulting R-stream reproduces the W3 cache R
per (sym, date) before gating. The gate touches ONLY which trades fire and their size; it
never changes the exit R of a taken trade.
"""
import sys, json, collections, datetime, statistics, pickle, random, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))

import substrate as sub
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs
import multitf_lib as mtf
import energy_agri_sleeve as ea
import kb2_new_breadth as KB
import INTEG_portfolio_build as I
import INTEG_portfolio_build_w2 as W2
from geometry_lib import atr14, simulate

def wins(r): return max(-1.3, min(5.0, r))
ROOT = str(HERE.parents[2]); DATA = ROOT + '/data/mt5_research_exports'
GATE_GEOM = (1.0, 3.0)     # query the substrate at its headline geometry family
H1_MAXBARS = I.H1_MAXBARS

# --------------------------------------------------------------------------- #
# 0) Build per-symbol leak-free substrate states ONCE (shared across gate calls)
# --------------------------------------------------------------------------- #
_STATE_CACHE = {}
def states_for(sym):
    if sym not in _STATE_CACHE:
        _STATE_CACHE[sym] = sub.build_states(sym)
    return _STATE_CACHE[sym]

# --------------------------------------------------------------------------- #
# 1) Re-derive CORE sleeve trades WITH entry (bar i, dir d), reproducing the
#    W3 cache R per (sym,date). We mirror the exact W2/W3 generator code paths.
# --------------------------------------------------------------------------- #
def metals_core_trades():
    """metals_core: FVG-retest + ac60>=AC_THR gate; STATE_D cascade exit (H4->H1->M15)."""
    out = []
    for sym in cs.METALS:
        T, B = w1.load(sym)
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]
        T1, B1 = mtf.load_ltf(sym, "H1"); have1 = len(B1) > 50
        T15, B15 = mtf.load_ltf(sym, "M15"); have15 = len(B15) > 50
        for (t, d, sd, td, i, B2, cost) in g.fvg_signals(sym):
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac < cs.AC_THR: continue
            vr = cs.vol_ratio(atrs, i)
            base_R = cs.exit_state_d(B, i, d, sd, vr, cost)['R']
            ts = t + datetime.timedelta(hours=4); sc = B[i].c
            R = base_R; filled = False
            if have1:
                si = mtf.first_ltf_index_after(T1, ts)
                if si is not None and 30 <= si < len(B1) - 2:
                    ej = I._find_fill(B1, T1, si, d, sc, 12, 1.0, ts)
                    if ej is not None:
                        R = cs.exit_state_d(B1, ej, d, sd, vr, cost, maxbars=H1_MAXBARS)['R']; filled = True
            if not filled and have15:
                si = mtf.first_ltf_index_after(T15, ts)
                if si is not None and 30 <= si < len(B15) - 2:
                    ej = I._find_fill(B15, T15, si, d, sc, 48, 1.0, ts)
                    if ej is not None:
                        R = cs.exit_state_d(B15, ej, d, sd, vr, cost, maxbars=1280)['R']
            out.append(dict(sleeve='metals_core', sym=sym, date=t.date(), year=t.year,
                            R=wins(R), i=i, d=d))
    return out

def energy_trades():
    """energy_agri ENERGY leg: FVG-retest entry; vr>=2 -> runR4 deeper, else STATE_D.
    Mirrors W2.gen_energy_agri energy emission, but tracks (i,d). One row per (sym,date)
    (the cascade ledger dedup by (sym,date))."""
    out = []
    seen = set()
    for sym in ea.ENERGY:
        try:
            T, B = w1.load(sym)
        except Exception:
            continue
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]; cost = w1.cost_for(sym)
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym):
            key = (sym, str(t.date()))
            if key in seen: continue
            seen.add(key)
            vr = cs.vol_ratio(atrs, i)
            if vr >= 2.0:
                R = KB.exit_state_d_runR(B, i, d, sd, vr, cost, runR_override=4.0)
            else:
                R = cs.exit_state_d(B, i, d, sd, vr, cost)['R']
            out.append(dict(sleeve='energy_agri', sym=sym, date=t.date(), year=t.year,
                            R=wins(R), i=i, d=d))
    return out

def crypto_btc_dash_trades():
    """crypto BTC/DASH: Donchian-20 breakout + ac60>=0.15 gate; cascade target4 exit.
    Reproduces the TW ledger entries on the w1.load H4 series with (i,d)."""
    out = []
    for sym in ['BTCUSD', 'DASHUSD']:
        try:
            T, B = w1.load(sym)
        except Exception:
            continue
        if len(B) < 200: continue
        cost = w1.cost_for(sym)
        atrs = [atr14(B, k) for k in range(len(B))]
        T1, B1 = mtf.load_ltf(sym, "H1"); have1 = len(B1) > 50
        T15, B15 = mtf.load_ltf(sym, "M15"); have15 = len(B15) > 50
        for (i, d) in KB.crypto_breakout_signals(B, 20):
            a = atrs[i]
            if a <= 0: continue
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac < 0.15: continue
            sd = 2.0 * a
            base_R = wins(simulate(B, i, d, stop_dist=sd, target_dist=4*sd, maxbars=80, cost=cost))
            ts = T[i] + datetime.timedelta(hours=4); sc = B[i].c
            R = base_R; filled = False
            if have1:
                si = mtf.first_ltf_index_after(T1, ts)
                if si is not None and 30 <= si < len(B1) - 2:
                    ej = I._find_fill(B1, T1, si, d, sc, 12, 1.0, ts)
                    if ej is not None:
                        R = wins(simulate(B1, ej, d, stop_dist=sd, target_dist=4*sd, maxbars=320, cost=cost)); filled = True
            if not filled and have15:
                si = mtf.first_ltf_index_after(T15, ts)
                if si is not None and 30 <= si < len(B15) - 2:
                    ej = I._find_fill(B15, T15, si, d, sc, 48, 1.0, ts)
                    if ej is not None:
                        R = wins(simulate(B15, ej, d, stop_dist=sd, target_dist=4*sd, maxbars=1280, cost=cost))
            out.append(dict(sleeve='crypto', sym=sym, date=T[i].date(), year=T[i].year,
                            R=wins(R), i=i, d=d))
    return out

def crypto_eth_trades():
    """ETH 3rd carrier on the RESAMPLED H4 series (NOT w1.load). The substrate map has
    no ETH-resampled coverage at these bars, so ETH is gated on its own resampled state
    via a dedicated build_states_from_bars (same leak-free vocabulary)."""
    out = []
    T, B = KB.resample_eth_h4()
    cost = w1.cost_for('ETHUSD')
    atrs = [atr14(B, k) for k in range(len(B))]
    mtf.LTF_PATHS.setdefault(("ETHUSD", "H1"),  [DATA + "/bridge_ftmo_htf_20250601_20260610/ETHUSD_H1.csv"])
    mtf.LTF_PATHS.setdefault(("ETHUSD", "M15"), [DATA + "/bridge_ftmo_m15_20250601_20260610/ETHUSD_M15.csv"])
    T1, B1 = mtf.load_ltf("ETHUSD", "H1"); have1 = len(B1) > 50
    T15, B15 = mtf.load_ltf("ETHUSD", "M15"); have15 = len(B15) > 50
    states = build_states_from_bars(T, B)
    for (i, d) in KB.crypto_breakout_signals(B, 20):
        a = atrs[i]
        if a <= 0: continue
        ac = cs.autocorr(B, i, 60)
        if ac is None or ac < 0.15: continue
        sd = 2.0 * a
        base_R = wins(simulate(B, i, d, stop_dist=sd, target_dist=4*sd, maxbars=80, cost=cost))
        ts = T[i] + datetime.timedelta(hours=4); sc = B[i].c
        R = base_R; filled = False
        if have1:
            si = mtf.first_ltf_index_after(T1, ts)
            if si is not None and 30 <= si < len(B1) - 2:
                ej = I._find_fill(B1, T1, si, d, sc, 12, 1.0, ts)
                if ej is not None:
                    R = wins(simulate(B1, ej, d, stop_dist=sd, target_dist=4*sd, maxbars=320, cost=cost)); filled = True
        if not filled and have15:
            si = mtf.first_ltf_index_after(T15, ts)
            if si is not None and 30 <= si < len(B15) - 2:
                ej = I._find_fill(B15, T15, si, d, sc, 48, 1.0, ts)
                if ej is not None:
                    R = wins(simulate(B15, ej, d, stop_dist=sd, target_dist=4*sd, maxbars=1280, cost=cost))
        out.append(dict(sleeve='crypto', sym='ETHUSD', date=T[i].date(), year=T[i].year,
                        R=wins(R), i=i, d=d, eth_state=states[i]))
    return out

def agri_trades():
    """AGRI continuation from the locked sleeve ledger (CORN/COTTON). These carry conf
    intra_size and NOT an i/d on the substrate H4 series, so they pass-through UNGATED
    (the substrate has agri coverage but the agri sleeve entry is a different mechanic;
    gating it would require re-deriving its entries — out of scope, kept ungated breadth)."""
    out = []
    pa = HERE / 'ENERGY_AGRI_SLEEVE_TRADES.jsonl'
    for line in pa.read_text().splitlines():
        if not line.strip(): continue
        r = json.loads(line)
        if r['grp'] != 'agri': continue
        dt = datetime.date.fromisoformat(r['date'])
        out.append(dict(sleeve='energy_agri', sym=r['sym'], date=dt, year=r['year'],
                        R=wins(r['R']), intra_size=r['conf'], i=None, d=None, ungated=True))
    return out

# --------------------------------------------------------------------------- #
# ETH resampled-series leak-free state builder (mirror of sub.build_states body,
# operating on an in-memory (T,B) instead of w1.load).
# --------------------------------------------------------------------------- #
def build_states_from_bars(T, B):
    n = len(B)
    A = [atr14(B, i) for i in range(n)]
    C = [b.c for b in B]; Hh = [b.h for b in B]; Lo = [b.l for b in B]
    tr = [0.0]*n
    for i in range(1, n):
        tr[i] = max(B[i].h-B[i].l, abs(B[i].h-B[i-1].c), abs(B[i].l-B[i-1].c))
    rets = [0.0]*n
    for i in range(1, n):
        rets[i] = C[i]-C[i-1]
    states = [None]*n
    for i in range(sub.WARMUP, n):
        a = A[i]
        if a <= 0: continue
        sma100 = sum(A[i-99:i+1])/100
        vr = a/sma100 if sma100 > 0 else 1.0
        win = A[i-199:i+1]; vol_pct = sum(1 for x in win if x <= a)/len(win)
        slope20 = (C[i]-C[i-20])/a; slope50 = (C[i]-C[i-50])/a; slope100 = (C[i]-C[i-100])/a
        ht = w1.htf_trend(B, i)
        def _sgn(v, thr=0.5): return 1 if v > thr else (-1 if v < -thr else 0)
        s_short = _sgn(slope20); s_long = _sgn(slope100)
        mtf_align = 1 if (s_short != 0 and s_short == s_long) else (-1 if (s_short != 0 and s_long != 0 and s_short == -s_long) else 0)
        lo50 = min(Lo[i-49:i+1]); hi50 = max(Hh[i-49:i+1])
        rng_pos = (C[i]-lo50)/(hi50-lo50) if hi50 > lo50 else 0.5
        comp = (sum(tr[i-4:i+1])/5)/(sum(tr[i-19:i+1])/20 or 1)
        ac60 = sub._ac(rets[i-59:i+1])
        states[i] = {"vr": vr, "vol_pct": vol_pct, "slope20": slope20, "slope50": slope50,
                     "slope100": slope100, "htf": ht, "mtf_align": mtf_align, "rng_pos": rng_pos,
                     "compression": comp, "ac60": ac60, "dist_hi": 0.0, "dist_lo": 0.0,
                     "ma_dist": 0.0, "hour": T[i].hour, "dow": T[i].weekday()}
    return states

# --------------------------------------------------------------------------- #
# 1b) ENTRY-BAR LOOKUPS: map each W3 cache row (sym,date) -> (bar i, dir d) on the
#     substrate H4 series, by re-running each sleeve's signal logic. We attach the
#     gate to the ACTUAL validated cache rows (keeping their exit R), so the gate
#     changes ONLY take/skip + size, never the exit R of a taken trade.
#     For symbols/dates with >1 signal that day, we record all (i,d); the gate uses
#     the FIRST (earliest entry bar) as the live decision bar.
# --------------------------------------------------------------------------- #
def _metals_id_map():
    mp = collections.defaultdict(list)
    for sym in cs.METALS:
        try: T, B = w1.load(sym)
        except Exception: continue
        if len(B) < 200: continue
        for (t, d, sd, td, i, B2, cost) in g.fvg_signals(sym):
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac < cs.AC_THR: continue
            mp[(sym, t.date())].append((i, d))
    return mp

def _energy_id_map():
    mp = collections.defaultdict(list)
    for sym in ea.ENERGY:
        try: T, B = w1.load(sym)
        except Exception: continue
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym):
            vr = cs.vol_ratio(atrs, i)
            if vr < 1.2: continue       # TW ledger entry vol gate
            mp[(sym, t.date())].append((i, d))
    return mp

def _crypto_btc_dash_id_map():
    mp = collections.defaultdict(list)
    for sym in ['BTCUSD', 'DASHUSD']:
        try: T, B = w1.load(sym)
        except Exception: continue
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]
        for (i, d) in KB.crypto_breakout_signals(B, 20):
            if atrs[i] <= 0: continue
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac < 0.15: continue
            mp[(sym, T[i].date())].append((i, d))
    return mp

def _eth_id_state_map():
    """ETH: (date)->list of (i,d,state) on the resampled series."""
    T, B = KB.resample_eth_h4()
    atrs = [atr14(B, k) for k in range(len(B))]
    states = build_states_from_bars(T, B)
    mp = collections.defaultdict(list)
    for (i, d) in KB.crypto_breakout_signals(B, 20):
        if atrs[i] <= 0: continue
        ac = cs.autocorr(B, i, 60)
        if ac is None or ac < 0.15: continue
        mp[('ETHUSD', T[i].date())].append((i, d, states[i]))
    return mp

def build_id_maps():
    mp = {}
    mp.update(_metals_id_map())
    mp.update(_energy_id_map())
    mp.update(_crypto_btc_dash_id_map())
    eth = _eth_id_state_map()
    return mp, eth

# --------------------------------------------------------------------------- #
# 2) The SUBSTRATE GATE: query best_cell at (state_i, GATE_GEOM, dir d).
#    take if min(train,fwd) mean_R > 0 ; size = confidence(min(train,fwd) mean_R).
# --------------------------------------------------------------------------- #
def gate_decision(cmap, state, d):
    """Return (take: bool, conf_meanR: float, depth, cell_meanR_min) for a trade
    entering in direction d at this leak-free state."""
    if state is None:
        return False, 0.0, None, None
    dims, c = sub.best_cell(cmap, state, geom=GATE_GEOM, dmode=d)
    if c is None or c.get("train") is None or c.get("fwd") is None:
        return False, 0.0, None, None
    mt = c["train"]["mean_R"]; mf = c["fwd"]["mean_R"]
    mn = min(mt, mf)
    return (mn > 0.0), max(0.0, mn), len(dims), mn

def gate_decision_trainonly(cmap, state, d):
    """STRICT forward-honest gate: decide using ONLY the TRAIN side of the deepest
    cell that has train sample (>=MIN_N_TRAIN). For a forward trade this uses NO
    forward information at all (the cell's forward outcome of OTHER trades is not
    read), so it is a clean forward decision. We still require the cell to have
    >=MIN_N_TRAIN train rows; we walk deepest->shallowest on TRAIN-n availability."""
    if state is None:
        return False, 0.0, None, None
    co = sub.cell_coords(state)
    for dims in sorted(sub.CONFLUENCE_PLANS, key=lambda dd: -len(dd)):
        ck = sub.cell_key(co, GATE_GEOM, d, dims)
        c = cmap.get(ck)
        if c and c.get("train") and c["train"]["n"] >= sub.MIN_N_TRAIN:
            mt = c["train"]["mean_R"]
            return (mt > 0.0), max(0.0, mt), len(dims), mt
    return False, 0.0, None, None

def size_from_conf(mn, scale=0.5, cap=2.0):
    """Size-by-confidence: scale the trade size by min(train,fwd) mean_R / scale,
    capped. mn is already >0 for taken trades. scale=0.5R -> a +0.5R cell trades 1x;
    a +1.0R cell trades 2x (capped). Never deletes (gate already decided take/skip)."""
    return min(cap, mn / scale)

def gate_cache_rows(cache_rows, sleeve, cmap, id_map, eth_map, eth_cmap=None,
                    size=True, scale=0.5, cap=2.0, mode='minboth'):
    """Gate the ACTUAL W3 cache rows of a CORE sleeve (keeps validated exit R).
    For each (sym,date) row, look up the entry (i,d) on the substrate H4 series,
    query best_cell at that leak-free state in dir d, and apply take/skip + size.
    Rows whose (sym,date) has no entry-bar lookup (e.g. AGRI) pass through UNGATED.
    Returns gated rows with gate_take / gate_conf / gate_depth / R_sized."""
    # consume per-key signal list in row order so multi-signal days map deterministically
    used = collections.defaultdict(int)
    out = []
    for r in cache_rows:
        key = (r['sym'], r['date'])
        # AGRI / non-derivable -> ungated breadth pass-through
        if r['sym'] == 'ETHUSD':
            lst = eth_map.get(key, [])
            cm = eth_cmap or cmap
        else:
            lst = id_map.get(key, [])
            cm = cmap
        if r['sym'] in ('CORN_c', 'COTTON_c') or not lst:
            t2 = dict(r); t2['gate_take'] = True; t2['gate_conf'] = None
            t2['gate_depth'] = None; t2['ungated'] = True
            t2['R_sized'] = r['R'] * r.get('intra_size', 1.0)
            out.append(t2); continue
        k = min(used[key], len(lst) - 1)
        if r['sym'] == 'ETHUSD':
            i, d, st = lst[k]
        else:
            i, d = lst[k]
            built = states_for(r['sym']); st = built[3][i] if built else None
        used[key] += 1
        if mode == 'trainonly':
            take, conf, depth, mn = gate_decision_trainonly(cm, st, d)
        else:
            take, conf, depth, mn = gate_decision(cm, st, d)
        t2 = dict(r); t2['gate_take'] = take
        t2['gate_conf'] = round(conf, 4) if conf else conf
        t2['gate_depth'] = depth; t2['i'] = i; t2['d'] = d
        isz = r.get('intra_size', 1.0)
        if take:
            sz = (min(cap, conf / scale)) if size else 1.0
            t2['R_sized'] = r['R'] * sz * isz
        else:
            t2['R_sized'] = 0.0
        out.append(t2)
    return out
