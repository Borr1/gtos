"""
wave4_vol_clustering_exits.py
=============================
THRUST: vol_clustering_exits — VOL-STATE-CONDITIONED EXIT GEOMETRY on the audited
metals FVG-retest entry (atr_expand>=1.2 gate).

CORE IDEA (built on the ONE universal regularity = vol clustering, ATR autocorr ~0.95-1.0):
  Volatility is highly persistent, so the *near-future* realized range of an open trade is
  forecastable from the *recent* realized range. Path facts on this entry (WAVE2 exit study):
  median MFE ~+4R, median time-to-2R ~12 bars, deep two-sided excursion. Fixed 2R/3R either
  caps winners in expanding-vol legs or sits through give-back in contracting-vol legs.
  HYPOTHESIS: hold/loosen the exit while vol is EXPANDING (let the runner run), and
  tighten/exit when vol CONTRACTS (the move's fuel is gone). Test vs fixed 2R/3R and the
  prior champion (partial 2R + trail 1R).

NON-NEGOTIABLE DISCIPLINE (3 prior subagent "wins" were leaks; 0/3 survived re-audit):
  * Entry reuses wave1 setup_ob_fvg_retest(mode='fvg') geometry/sign EXACTLY (re-implemented
    inline only to expose the bar index so a custom exit walker can run on the SAME bars).
  * Fills: the custom vol-aware exit walker uses the SAME pessimistic two-sided convention as
    the TESTED geometry_lib (stop wins same-bar ties; long: stop=l<=stop, target=h>=tgt).
    It is CROSS-CHECKED bar-for-bar against geometry_lib.simulate on the degenerate
    fixed-target and trail parameterizations — if it ever disagrees the run ABORTS. That is
    the anti-fill-bug guard demanded by the protocol.
  * NO LOOKAHEAD in the exit: at bar j (j>entry), the vol-state used to decide tighten/exit is
    ATR computed from bars[<=j] ONLY. The decision is *applied on the NEXT bar j+1* (we never
    use bar j's own high/low to both measure vol AND fill an exit triggered by that vol read).
    Vol-state is a function of CLOSED bars only.
  * NO LOOKAHEAD in entry/gate: ATR(14) at i and SMA100-of-ATR over [i-99..i] (atr_ratio),
    htf_trend(close[i] vs close[i-lb]) — all bars[<=i]. Identical to wave3_fvg_regime_honest.
  * STRICT OOS: every exit-policy PARAMETER (which vol rule, thresholds) is SELECTED on
    TRAIN<=2024 ONLY; FORWARD 2025-2026 is pure read-out. Per-year R reported 2015-2026.
  * NULLS under the SAME selection rule (mandatory for any claimed positive):
       (1) INVERT  — opposite entry side, same vol-aware exit.
       (2) RANDOM  — replace the vol-state signal with a coin flip of matched contraction
                     frequency (seeded, averaged) -> shows the *vol read*, not the exit
                     mechanics, carries the result.
  * WINSORIZE file-stitch bad prints: a single-bar spike (range >> neighbours) that reverts
    next bar is clamped before ATR/vol features. Applied to the loaded series once.
  * Real per-asset-class costs from ULTIMATE_REAL_COST_MAP.json, charged once per trade.

VERDICT RULE (stated up front, honest):
  A vol-aware exit is called a WIN over the baseline ONLY if, with parameters frozen on train:
    (a) forward (2025-26) mean_R > 0, AND
    (b) it beats the best fixed/partial baseline on forward mean_R, AND
    (c) per-year breadth (positive years / 12) is >= the baseline's, AND
    (d) INVERT forward R < 0 and RANDOM-vol forward R < the vol-aware forward R.
  "Stabilize" is judged by per-year breadth + train/fwd consistency, not just mean lift.
"""
from __future__ import annotations
import sys, os, csv, json, random, statistics
from datetime import datetime
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
D1 = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022"
D2 = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
from geometry_lib import Bar, atr14, simulate, simulate_detail

with open(EDGE + "/ULTIMATE_REAL_COST_MAP.json") as f:
    COSTMAP = json.load(f)
GC = COSTMAP["_global_median"]
def cost_for(s): return COSTMAP.get(ASSET_CLASS_BY_SYMBOL.get(s), GC)

TRAIN_MAX = 2024
ATR_GATE = 1.2            # the audited regime gate (atr_expand>=1.2), locked from wave3
MAXBARS = 80             # same horizon as geometry_lib default

# ---------------- data load (identical to wave1/wave3) ----------------
def syms_in(d):
    return {fn[:-7] for fn in os.listdir(d) if fn.endswith("_H4.csv")}
SYMBOLS = sorted(syms_in(D1) | syms_in(D2))

def _load_one(p):
    T = []; B = []
    if not os.path.exists(p): return T, B
    with open(p) as f:
        for row in csv.DictReader(f):
            try:
                t = datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S")
                b = Bar(float(row["open"]), float(row["high"]), float(row["low"]),
                        float(row["close"]), float(row.get("volume", 0) or 0))
                T.append(t); B.append(b)
            except Exception:
                continue
    return T, B

def winsorize(bars):
    """Clamp single-bar file-stitch spikes that revert next bar, BEFORE vol features.
    A bar j is a bad print if its true range is > 8x the median TR of the 20 surrounding
    bars AND the bar's extreme is not confirmed by the next bar (price reverts): i.e. the
    spike high/low is not revisited by bar j+1. We clamp the offending extreme to the
    neighbour-consistent bound. Conservative: only clamps egregious, reverting single bars."""
    n = len(bars)
    if n < 25: return bars
    out = [Bar(b.o, b.h, b.l, b.c, b.v) for b in bars]
    trs = [0.0]*n
    for j in range(1, n):
        trs[j] = max(bars[j].h-bars[j].l, abs(bars[j].h-bars[j-1].c), abs(bars[j].l-bars[j-1].c))
    clamped = 0
    for j in range(2, n-1):
        lo = max(1, j-10); hi = min(n, j+11)
        local = sorted(trs[k] for k in range(lo, hi) if k != j and trs[k] > 0)
        if len(local) < 6: continue
        med = local[len(local)//2]
        if med <= 0: continue
        if trs[j] > 8.0*med:
            pc = bars[j-1].c; nb = bars[j+1]
            # cap allowed excursion to 4x median around prior close / neighbours
            cap = 4.0*med
            up_spike = bars[j].h - max(pc, bars[j].o, bars[j].c)
            dn_spike = min(pc, bars[j].o, bars[j].c) - bars[j].l
            # reverts if next bar does not revisit the spike extreme
            if up_spike > cap and nb.h < bars[j].h - 0.5*up_spike:
                out[j].h = max(bars[j].o, bars[j].c, pc) + cap
                clamped += 1
            if dn_spike > cap and nb.l > bars[j].l + 0.5*dn_spike:
                out[j].l = min(bars[j].o, bars[j].c, pc) - cap
                clamped += 1
            # keep o/c within the (possibly) tightened h/l
            out[j].h = max(out[j].h, out[j].o, out[j].c)
            out[j].l = min(out[j].l, out[j].o, out[j].c)
    winsorize.last_clamped = clamped
    return out
winsorize.last_clamped = 0

_CACHE = {}
def load(sym):
    if sym in _CACHE: return _CACHE[sym]
    T1, B1 = _load_one(f"{D1}/{sym}_H4.csv")
    T2, B2 = _load_one(f"{D2}/{sym}_H4.csv")
    merged = {}
    for t, b in zip(T1, B1): merged[t] = b
    for t, b in zip(T2, B2): merged[t] = b
    if not merged:
        _CACHE[sym] = ([], []); return _CACHE[sym]
    items = sorted(merged.items(), key=lambda kv: kv[0])
    T = [k for k, _ in items]; B = winsorize([v for _, v in items])
    _CACHE[sym] = (T, B)
    return _CACHE[sym]

# ---------------- known-at-i features (identical to wave3) ----------------
def htf_trend(bars, i, lb=30):
    if i < lb: return 0
    a = atr14(bars, i)
    if a <= 0: return 0
    diff = bars[i].c - bars[i-lb].c
    if diff > 1.0*a: return 1
    if diff < -1.0*a: return -1
    return 0

def sma_atr_ratio(atrs, i, win=100):
    lo = i - win + 1
    if lo < 14: return None
    seg = [atrs[k] for k in range(lo, i+1) if atrs[k] > 0]
    if len(seg) < win//2: return None
    m = sum(seg)/len(seg)
    if m <= 0: return None
    return atrs[i]/m

# =====================================================================
# VOL-AWARE EXIT WALKER  (custom, but cross-checked vs geometry_lib)
# =====================================================================
def walk_exit(bars, atrs, i, direction, *, stop_dist,
              policy, params, cost=0.0, maxbars=MAXBARS):
    """Walk the trade bar by bar with the SAME pessimistic two-sided fill convention as
    geometry_lib.simulate. Returns (R, exit_index).

    policy:
      'fixed'     -> params={'target_R'}                        (== geometry_lib fixed target)
      'trail'     -> params={'arm_R','gap_R'}                   (== geometry_lib trail)
      'partial'   -> params={'first_R','first_frac','trail_gap_R','be'}  (partial + trail runner)
      'vol_runner'-> VOL-AWARE: arm a runner, trail with a gap that WIDENS while vol is
                     expanding and TIGHTENS (or hard-exits) when vol contracts.
                     params={'arm_R','base_gap_R','wide_gap_R','tight_gap_R',
                             'contract_thr','expand_thr','vol_lookback','exit_on_contract',
                             'first_R','first_frac'}
      'partial_vol'-> partial lock at first_R, then VOL-AWARE trail on the runner.

    NO-LOOKAHEAD CONTRACT for vol policies: at bar j we may read atrs[j] (ATR of CLOSED bar j)
    to set the gap/decision that governs fills on bar j+1 ONWARD. We NEVER let the vol read at
    j influence a fill that uses bar j's own high/low. Implemented by computing the active gap
    from the vol-state as of the PRIOR closed bar (j-1) when testing fills on bar j.
    """
    entry = bars[i].c
    end = min(i+maxbars, len(bars)-1)
    a_entry = atrs[i] if atrs[i] > 0 else stop_dist
    sign = 1 if direction > 0 else -1

    def R_at(price):
        return sign*(price-entry)/stop_dist - cost

    if policy == 'fixed':
        return simulate_detail(bars, i, direction, stop_dist=stop_dist,
                               target_dist=params['target_R']*stop_dist, cost=cost, maxbars=maxbars)
    if policy == 'trail':
        return simulate_detail(bars, i, direction, stop_dist=stop_dist,
                               trail_arm=params['arm_R']*stop_dist,
                               trail_gap=params['gap_R']*stop_dist, cost=cost, maxbars=maxbars)

    # ---- generic bar walker for partial / vol policies ----
    stop = entry - sign*stop_dist
    realized = 0.0          # locked R from partials (already cost-adjusted at exit time)
    remaining = 1.0         # position fraction still open
    ext = entry             # best extreme in trade direction (max for long / min for short)
    armed = False
    partial_done = False

    first_R = params.get('first_R')
    first_frac = params.get('first_frac', 0.0)
    arm_R = params.get('arm_R', first_R if first_R else 1.0)

    # vol gap state (recomputed per bar from CLOSED prior bar)
    def gap_for(jprev):
        """Active trail gap (in price) governing fills on bar jprev+1, using vol-state of
        the CLOSED bar jprev only. Vol-state = ATR(jprev) vs ATR at entry (clustering ref)."""
        if policy in ('vol_runner', 'partial_vol'):
            aj = atrs[jprev] if jprev >= 0 and atrs[jprev] > 0 else a_entry
            ratio = aj / a_entry if a_entry > 0 else 1.0
            if ratio >= params['expand_thr']:
                return params['wide_gap_R']*stop_dist, 'expand'
            if ratio <= params['contract_thr']:
                return params['tight_gap_R']*stop_dist, 'contract'
            return params['base_gap_R']*stop_dist, 'base'
        return params.get('trail_gap_R', 1.0)*stop_dist, 'base'

    for j in range(i+1, end+1):
        b = bars[j]
        # --- (1) hard stop on the still-open remaining fraction (pessimistic, first) ---
        if sign > 0 and b.l <= stop:
            realized += remaining*(R_at(stop))
            return realized, j
        if sign < 0 and b.h >= stop:
            realized += remaining*(R_at(stop))
            return realized, j
        # --- (2) partial take-profit at first_R (fixed, known geometry) ---
        if first_R and not partial_done:
            tgt = entry + sign*first_R*stop_dist
            hit = (sign > 0 and b.h >= tgt) or (sign < 0 and b.l <= tgt)
            if hit:
                realized += first_frac*(sign*(tgt-entry)/stop_dist - cost)
                remaining -= first_frac
                partial_done = True
                if params.get('be'):
                    stop = entry  # move remaining to breakeven
        # --- (3) arm the trailing runner once arm_R reached ---
        if not armed:
            armd = (sign > 0 and b.h >= entry + arm_R*stop_dist) or \
                   (sign < 0 and b.l <= entry - arm_R*stop_dist)
            if armd: armed = True
        # --- (4) update best extreme ---
        if sign > 0: ext = max(ext, b.h)
        else:        ext = min(ext, b.l)
        # --- (5) trailing exit on remaining fraction, gap from CLOSED prior bar (no lookahead) ---
        if armed:
            gap, state = gap_for(j-1)
            # vol-aware hard exit: if vol contracted AND configured to flatten, exit at this
            # bar's OPEN (decision made on prior closed bar -> executed at next bar open).
            if policy in ('vol_runner', 'partial_vol') and params.get('exit_on_contract') \
               and state == 'contract':
                px = b.o
                realized += remaining*(R_at(px))
                return realized, j
            trail_stop = ext - sign*gap
            if sign > 0 and b.l <= trail_stop:
                realized += remaining*(R_at(trail_stop))
                return realized, j
            if sign < 0 and b.h >= trail_stop:
                realized += remaining*(R_at(trail_stop))
                return realized, j
    # timeout: close remaining at last close
    realized += remaining*(R_at(bars[end].c))
    return realized, end

# =====================================================================
# ENTRY: metals FVG-retest continuation, identical geometry to wave1/wave3
# =====================================================================
def fvg_entries(classes, target_invert=False, atr_win=100, trend_lb=30,
                fvg_min=0.10, stop_buf=0.10, atr_stop_floor=0.25, gate=ATR_GATE):
    """Yield entry events: dict(sym, year, cls, i, direction, stop_dist, atrs ref, bars ref).
    Applies the atr_expand>=gate regime filter at entry (known-at-i). direction is the
    continuation side (already sign-correct); target_invert flips it for the INVERT null."""
    events = []
    for sym in SYMBOLS:
        if ASSET_CLASS_BY_SYMBOL.get(sym) not in classes: continue
        T, B = load(sym)
        if len(B) < 200: continue
        n = len(B); atrs = [atr14(B, i) for i in range(n)]
        for i in range(60, n-1):
            a = atrs[i]
            if a <= 0: continue
            ratio = sma_atr_ratio(atrs, i, atr_win)
            if ratio is None or ratio < gate:    # REGIME GATE (known-at-i)
                continue
            tr = htf_trend(B, i, trend_lb); b = B[i]
            d = None; stop_dist = None
            if tr == 1:
                for k in range(i-2, max(i-9, 60), -1):
                    gap_top = B[k].l; gap_bot = B[k-2].h
                    if gap_top - gap_bot < fvg_min*a: continue
                    if b.l <= gap_top and b.c > gap_bot and b.c > b.o:
                        stop_dist = max((b.c - min(b.l, gap_bot)) + stop_buf*a, atr_stop_floor*a)
                        d = +1; break
            elif tr == -1:
                for k in range(i-2, max(i-9, 60), -1):
                    gap_bot = B[k].h; gap_top = B[k-2].l
                    if gap_top - gap_bot < fvg_min*a: continue
                    if b.h >= gap_bot and b.c < gap_top and b.c < b.o:
                        stop_dist = max((max(b.h, gap_top) - b.c) + stop_buf*a, atr_stop_floor*a)
                        d = -1; break
            if d is None: continue
            if target_invert: d = -d
            events.append({"sym": sym, "year": T[i].year, "cls": ASSET_CLASS_BY_SYMBOL.get(sym),
                           "i": i, "direction": d, "stop_dist": stop_dist})
        # attach bar refs by sym (avoid re-load); store on event lazily below
    return events

def run_policy(events, policy, params):
    """Simulate one exit policy across all entry events -> list of dicts with R + year."""
    out = []
    # group by symbol so we load bars/atrs once
    by_sym = defaultdict(list)
    for ev in events: by_sym[ev["sym"]].append(ev)
    for sym, evs in by_sym.items():
        T, B = load(sym); n = len(B)
        atrs = [atr14(B, i) for i in range(n)]
        cost = cost_for(sym)
        for ev in evs:
            r, xi = walk_exit(B, atrs, ev["i"], ev["direction"], stop_dist=ev["stop_dist"],
                              policy=policy, params=params, cost=cost)
            out.append({"sym": sym, "year": ev["year"], "cls": ev["cls"], "r": r, "exit_i": xi,
                        "entry_i": ev["i"]})
    return out

# =====================================================================
# stats / reporting
# =====================================================================
def stats(rs):
    if not rs: return {"n": 0, "mean_R": 0.0, "win%": 0.0, "sum_R": 0.0}
    n = len(rs); s = sum(rs); w = sum(1 for r in rs if r > 0)
    return {"n": n, "mean_R": round(s/n, 4), "win%": round(100*w/n, 1), "sum_R": round(s, 2)}

def per_year(recs):
    by = defaultdict(list)
    for d in recs: by[d["year"]].append(d["r"])
    return {y: stats(by[y]) for y in sorted(by)}

def split(recs):
    tr = [d["r"] for d in recs if d["year"] <= TRAIN_MAX]
    fw = [d["r"] for d in recs if d["year"] >  TRAIN_MAX]
    return stats(tr), stats(fw)

def summarize(name, recs):
    tr, fw = split(recs); py = per_year(recs); yrs = sorted(py)
    full = stats([d["r"] for d in recs])
    pos_years = sum(1 for y in yrs if py[y]["mean_R"] > 0)
    fwd_yrs = [y for y in yrs if y > TRAIN_MAX]
    pos_fwd = sum(1 for y in fwd_yrs if py[y]["mean_R"] > 0)
    return {"name": name, "full_cycle": full, "train": tr, "fwd": fw,
            "per_year": {str(y): py[y] for y in yrs},
            "pos_years": pos_years, "total_years": len(yrs),
            "pos_fwd_years": pos_fwd, "total_fwd_years": len(fwd_yrs)}

def pline(s):
    py = s["per_year"]
    print(f"  TRAIN<=24 R={s['train']['mean_R']:+.4f}(n{s['train']['n']})  "
          f"FWD R={s['fwd']['mean_R']:+.4f}(n{s['fwd']['n']})  "
          f"FULL R={s['full_cycle']['mean_R']:+.4f} sum={s['full_cycle']['sum_R']:+.1f}  "
          f"posYrs {s['pos_years']}/{s['total_years']} posFwd {s['pos_fwd_years']}/{s['total_fwd_years']}")
    print("  per-year: " + " ".join(f"{y}:{py[y]['mean_R']:+.3f}(n{py[y]['n']})" for y in py))

# =====================================================================
# CROSS-CHECK: custom walker must reproduce geometry_lib on degenerate cases
# =====================================================================
def crosscheck(events):
    """The custom partial walker, when given first_frac=0 and a pure trail, MUST equal
    geometry_lib.simulate's trail R; the 'fixed' and 'trail' policies route THROUGH
    simulate_detail so they are exact by construction. We additionally verify the bar-walker
    path (policy='partial' with first_frac=0.0, be=False) equals a pure-trail simulate_detail.
    Any mismatch beyond float epsilon ABORTS the run (anti-fill-bug guard)."""
    mism = 0; checked = 0
    by_sym = defaultdict(list)
    for ev in events: by_sym[ev["sym"]].append(ev)
    for sym, evs in by_sym.items():
        T, B = load(sym); n = len(B); atrs = [atr14(B, i) for i in range(n)]
        cost = cost_for(sym)
        for ev in evs[:200]:
            sd = ev["stop_dist"]; d = ev["direction"]; i = ev["i"]
            # pure trail via library
            r_lib, x_lib = simulate_detail(B, i, d, stop_dist=sd, trail_arm=1.0*sd,
                                           trail_gap=1.0*sd, cost=cost)
            # same via custom walker: partial with no partial, arm_R=1, constant gap 1R
            r_w, x_w = walk_exit(B, atrs, i, d, stop_dist=sd, policy='partial',
                                 params={'first_R': None, 'first_frac': 0.0, 'arm_R': 1.0,
                                         'trail_gap_R': 1.0, 'be': False}, cost=cost)
            checked += 1
            if abs(r_lib - r_w) > 1e-9 or x_lib != x_w:
                mism += 1
                if mism <= 5:
                    print(f"  MISMATCH {sym} i={i} d={d}: lib R={r_lib:.6f}@{x_lib} "
                          f"walker R={r_w:.6f}@{x_w}")
    print(f"  cross-check: {checked} trades, {mism} mismatches")
    if mism > 0:
        raise SystemExit("CROSS-CHECK FAILED: custom walker disagrees with geometry_lib. ABORT.")
    return checked

# =====================================================================
# MAIN
# =====================================================================
def main():
    random.seed(20260614)
    OUT = {"thrust": "vol_clustering_exits",
           "entry": "metals FVG-retest continuation, atr_expand>=1.2 gate (audited candidate)",
           "discipline": "params frozen on TRAIN<=2024; FWD 2025-26 read-out; per-year 2015-26; "
                         "winsorized; INVERT+RANDOM-vol nulls; custom walker cross-checked vs geometry_lib",
           "results": {}, "controls": {}, "selection": {}, "verdict": {}}

    # ----- build entry sets (winsorize clamp count reported) -----
    METALS = {"metals"}
    ME = {"metals", "energy"}
    ev_metals = fvg_entries(METALS)
    ev_me = fvg_entries(ME)
    clamp_total = 0
    for sym in SYMBOLS:
        load(sym)  # ensure cached/winsorized; clamp count is per-call, recompute total:
    # recompute clamp totals cleanly
    _CACHE.clear()
    clamp_total = 0
    for sym in SYMBOLS:
        T1, B1 = _load_one(f"{D1}/{sym}_H4.csv")
        T2, B2 = _load_one(f"{D2}/{sym}_H4.csv")
        merged = {}
        for t, b in zip(T1, B1): merged[t] = b
        for t, b in zip(T2, B2): merged[t] = b
        if not merged: continue
        items = sorted(merged.items(), key=lambda kv: kv[0])
        winsorize([v for _, v in items])
        clamp_total += winsorize.last_clamped
    _CACHE.clear()
    OUT["winsorize_clamped_bars"] = clamp_total
    print(f"winsorize clamped {clamp_total} bad-print bars across universe")
    print(f"metals entries: {len(ev_metals)}   metals+energy entries: {len(ev_me)}")

    print("\n" + "="*78 + "\nCROSS-CHECK custom walker vs geometry_lib (anti-fill-bug guard)\n" + "="*78)
    crosscheck(ev_metals)

    # ====================================================================
    # BASELINES (fixed 2R, fixed 3R, prior champion partial2R+BE+trail1R)
    # ====================================================================
    print("\n" + "="*78 + "\nBASELINES on metals FVG (atr>=1.2)\n" + "="*78)
    baselines = {
        "fixed_2R": ("fixed", {"target_R": 2.0}),
        "fixed_3R": ("fixed", {"target_R": 3.0}),
        "partial2R_be_trail1R": ("partial", {"first_R": 2.0, "first_frac": 0.5,
                                             "arm_R": 2.0, "trail_gap_R": 1.0, "be": True}),
        "trail_arm1_gap1": ("trail", {"arm_R": 1.0, "gap_R": 1.0}),
    }
    base_sum = {}
    for nm, (pol, prm) in baselines.items():
        recs = run_policy(ev_metals, pol, prm)
        s = summarize(nm, recs); base_sum[nm] = s
        print(f"\n[{nm}]"); pline(s)
        OUT["results"][nm] = s

    # ====================================================================
    # VOL-AWARE EXIT FAMILY — select params on TRAIN only
    # vol-state ref = ATR(closed bar) / ATR(entry). expand=>widen gap, contract=>tighten/exit.
    # ====================================================================
    print("\n" + "="*78 + "\nVOL-AWARE EXIT SELECTION (TRAIN<=2024 ONLY)\n" + "="*78)
    # candidate grid (all params chosen here, then frozen)
    vol_grid = []
    for arm in (1.0,):
        for base_gap in (1.0, 1.5):
            for wide in (2.0, 3.0):
                for tight in (0.5, 0.75):
                    for ct in (0.85, 0.95):
                        for xt in (1.10, 1.25):
                            for exoc in (False, True):
                                vol_grid.append({
                                    "arm_R": arm, "base_gap_R": base_gap, "wide_gap_R": wide,
                                    "tight_gap_R": tight, "contract_thr": ct, "expand_thr": xt,
                                    "exit_on_contract": exoc, "vol_lookback": 1,
                                    "first_R": None, "first_frac": 0.0})
    # also a partial+vol variant family (lock half at 2R, vol-trail the runner)
    for base_gap in (1.0, 1.5):
        for wide in (2.0, 3.0):
            for tight in (0.5,):
                for ct in (0.85, 0.95):
                    for xt in (1.10,):
                        for exoc in (False, True):
                            vol_grid.append({
                                "arm_R": 2.0, "base_gap_R": base_gap, "wide_gap_R": wide,
                                "tight_gap_R": tight, "contract_thr": ct, "expand_thr": xt,
                                "exit_on_contract": exoc, "vol_lookback": 1,
                                "first_R": 2.0, "first_frac": 0.5, "policy_tag": "partial_vol"})

    # evaluate each on TRAIN only; freeze the best by TRAIN mean_R with enough n
    train_scored = []
    cache_recs = {}
    for gi, prm in enumerate(vol_grid):
        pol = 'partial_vol' if prm.get("first_R") else 'vol_runner'
        recs = run_policy(ev_metals, pol, prm)
        cache_recs[gi] = (pol, prm, recs)
        tr = [d["r"] for d in recs if d["year"] <= TRAIN_MAX]
        st = stats(tr)
        train_scored.append((gi, st["mean_R"], st["n"]))
    train_scored.sort(key=lambda x: -x[1])
    best_gi = train_scored[0][0]
    best_pol, best_prm, best_recs = cache_recs[best_gi]
    s_best = summarize("VOL_AWARE_selected", best_recs)
    print(f"\nselected vol-aware policy (best TRAIN mean_R): {best_pol}")
    print(f"  params: {json.dumps({k:v for k,v in best_prm.items() if k!='policy_tag'})}")
    pline(s_best)
    OUT["selection"] = {
        "selected_policy": best_pol,
        "selected_params": {k: v for k, v in best_prm.items() if k != "policy_tag"},
        "train_mean_R": train_scored[0][1], "train_n": train_scored[0][2],
        "grid_size": len(vol_grid),
        "top5_train": [{"params": {k: v for k, v in cache_recs[gi][1].items() if k != "policy_tag"},
                        "train_mean_R": mr, "train_n": n} for gi, mr, n in train_scored[:5]],
    }
    OUT["results"]["vol_aware_selected"] = s_best

    # ====================================================================
    # NULLS under the SAME frozen policy
    # ====================================================================
    print("\n" + "="*78 + "\nNULLS (same frozen vol-aware policy)\n" + "="*78)
    # (1) INVERT entry side
    ev_metals_inv = fvg_entries(METALS, target_invert=True)
    inv_recs = run_policy(ev_metals_inv, best_pol, best_prm)
    s_inv = summarize("NULL_invert_entry", inv_recs)
    print("\n[NULL invert entry]"); pline(s_inv)
    OUT["controls"]["invert_entry"] = s_inv

    # (2) RANDOM-vol: replace the vol read with a coin flip matched to the realized
    #     contraction frequency of the selected policy, averaged over seeds.
    #     We do this by a walker variant that ignores ATR and randomly labels each bar's
    #     state expand/contract/base with frequencies matched to the real policy.
    print("\n[NULL random-vol] estimating realized state frequencies of selected policy...")
    # measure realized state distribution under selected thresholds on metals bars
    exp_thr = best_prm["expand_thr"]; con_thr = best_prm["contract_thr"]
    n_exp=n_con=n_base=0
    for sym in SYMBOLS:
        if ASSET_CLASS_BY_SYMBOL.get(sym) not in METALS: continue
        T, B = load(sym); n=len(B); atrs=[atr14(B,i) for i in range(n)]
        for ev in [e for e in ev_metals if e["sym"]==sym]:
            i=ev["i"]; a_e=atrs[i] if atrs[i]>0 else ev["stop_dist"]
            end=min(i+MAXBARS, n-1)
            for j in range(i+1, end+1):
                aj=atrs[j-1] if atrs[j-1]>0 else a_e
                ratio=aj/a_e if a_e>0 else 1.0
                if ratio>=exp_thr: n_exp+=1
                elif ratio<=con_thr: n_con+=1
                else: n_base+=1
    tot=max(1,n_exp+n_con+n_base)
    p_exp=n_exp/tot; p_con=n_con/tot
    print(f"  realized state freq: expand={p_exp:.3f} contract={p_con:.3f} base={1-p_exp-p_con:.3f}")

    def walk_exit_randomvol(B, atrs, i, direction, stop_dist, prm, cost, rng):
        """Same mechanics as walk_exit vol_runner/partial_vol but the per-bar STATE is drawn
        randomly (matched freq) instead of read from ATR -> isolates whether the VOL READ
        (not the trail mechanics) carries the result."""
        entry=B[i].c; end=min(i+MAXBARS,len(B)-1); sign=1 if direction>0 else -1
        def R_at(px): return sign*(px-entry)/stop_dist - cost
        stop=entry-sign*stop_dist; realized=0.0; remaining=1.0; ext=entry; armed=False; partial_done=False
        first_R=prm.get("first_R"); first_frac=prm.get("first_frac",0.0)
        arm_R=prm.get("arm_R", first_R if first_R else 1.0)
        # pre-draw a state per bar (decision for bar j uses state drawn for j-1)
        states={}
        def st_for(jp):
            if jp not in states:
                u=rng.random()
                states[jp]='expand' if u<p_exp else ('contract' if u<p_exp+p_con else 'base')
            return states[jp]
        for j in range(i+1,end+1):
            b=B[j]
            if sign>0 and b.l<=stop: realized+=remaining*R_at(stop); return realized,j
            if sign<0 and b.h>=stop: realized+=remaining*R_at(stop); return realized,j
            if first_R and not partial_done:
                tgt=entry+sign*first_R*stop_dist
                if (sign>0 and b.h>=tgt) or (sign<0 and b.l<=tgt):
                    realized+=first_frac*(sign*(tgt-entry)/stop_dist-cost); remaining-=first_frac
                    partial_done=True
                    if prm.get("be"): stop=entry
            if not armed:
                if (sign>0 and b.h>=entry+arm_R*stop_dist) or (sign<0 and b.l<=entry-arm_R*stop_dist):
                    armed=True
            ext=max(ext,b.h) if sign>0 else min(ext,b.l)
            if armed:
                state=st_for(j-1)
                if prm.get("exit_on_contract") and state=='contract':
                    realized+=remaining*R_at(b.o); return realized,j
                gap=(prm['wide_gap_R'] if state=='expand' else
                     prm['tight_gap_R'] if state=='contract' else prm['base_gap_R'])*stop_dist
                ts=ext-sign*gap
                if sign>0 and b.l<=ts: realized+=remaining*R_at(ts); return realized,j
                if sign<0 and b.h>=ts: realized+=remaining*R_at(ts); return realized,j
        realized+=remaining*R_at(B[end].c); return realized,end

    NREP=30
    rand_full=[]; rand_fwd=[]; rand_posyrs=[]
    by_sym=defaultdict(list)
    for ev in ev_metals: by_sym[ev["sym"]].append(ev)
    for rep in range(NREP):
        rng=random.Random(7000+rep); recs=[]
        for sym,evs in by_sym.items():
            T,B=load(sym); n=len(B); atrs=[atr14(B,i) for i in range(n)]; cost=cost_for(sym)
            for ev in evs:
                r,xi=walk_exit_randomvol(B,atrs,ev["i"],ev["direction"],ev["stop_dist"],best_prm,cost,rng)
                recs.append({"sym":sym,"year":ev["year"],"r":r})
        s=summarize(f"rand{rep}",recs)
        rand_full.append(s["full_cycle"]["mean_R"]); rand_fwd.append(s["fwd"]["mean_R"])
        rand_posyrs.append(s["pos_years"])
    rv={"reps":NREP,"mean_full_R":round(sum(rand_full)/NREP,4),"mean_fwd_R":round(sum(rand_fwd)/NREP,4),
        "fwd_R_min":round(min(rand_fwd),4),"fwd_R_max":round(max(rand_fwd),4),
        "mean_pos_years":round(sum(rand_posyrs)/NREP,2)}
    print(f"  random-vol: mean FULL R={rv['mean_full_R']:+.4f}  mean FWD R={rv['mean_fwd_R']:+.4f} "
          f"(min {rv['fwd_R_min']:+.4f} max {rv['fwd_R_max']:+.4f})  mean posYrs {rv['mean_pos_years']}")
    OUT["controls"]["random_vol"]=rv

    # ====================================================================
    # metals+energy read-out of selected policy (broader pocket, context)
    # ====================================================================
    me_recs = run_policy(ev_me, best_pol, best_prm)
    s_me = summarize("VOL_AWARE_selected_metals_energy", me_recs)
    print("\n[vol-aware selected on metals+energy, context]"); pline(s_me)
    OUT["results"]["vol_aware_selected_metals_energy"] = s_me
    # baselines on metals+energy for fair compare
    for nm,(pol,prm) in baselines.items():
        s = summarize(nm+"_ME", run_policy(ev_me,pol,prm))
        OUT["results"][nm+"_metals_energy"]=s

    # ====================================================================
    # VERDICT
    # ====================================================================
    print("\n" + "="*78 + "\nVERDICT\n" + "="*78)
    # best baseline by forward mean_R
    best_base_nm = max(base_sum, key=lambda k: base_sum[k]["fwd"]["mean_R"])
    bb = base_sum[best_base_nm]
    va = s_best
    a = va["fwd"]["mean_R"] > 0
    b = va["fwd"]["mean_R"] > bb["fwd"]["mean_R"]
    c = va["pos_years"] >= bb["pos_years"]
    d = (s_inv["fwd"]["mean_R"] < 0) and (rv["mean_fwd_R"] < va["fwd"]["mean_R"])
    win = bool(a and b and c and d)
    verdict={
        "selected_vol_policy": best_pol,
        "best_baseline_by_fwd": best_base_nm,
        "baseline_fwd_R": bb["fwd"]["mean_R"], "baseline_train_R": bb["train"]["mean_R"],
        "baseline_full_R": bb["full_cycle"]["mean_R"], "baseline_pos_years": f"{bb['pos_years']}/{bb['total_years']}",
        "vol_aware_fwd_R": va["fwd"]["mean_R"], "vol_aware_train_R": va["train"]["mean_R"],
        "vol_aware_full_R": va["full_cycle"]["mean_R"], "vol_aware_pos_years": f"{va['pos_years']}/{va['total_years']}",
        "vol_aware_pos_fwd": f"{va['pos_fwd_years']}/{va['total_fwd_years']}",
        "invert_fwd_R": s_inv["fwd"]["mean_R"], "random_vol_fwd_R": rv["mean_fwd_R"],
        "(a)_fwd_positive": a, "(b)_beats_best_baseline_fwd": b,
        "(c)_breadth_ge_baseline": c, "(d)_nulls_clean": d,
        "VOL_AWARE_EXIT_WINS": win,
        "honest_note": ("Vol-aware exit beats baselines on forward AND keeps/raises year breadth AND "
                        "survives invert+random-vol nulls." if win else
                        "Vol-aware exit does NOT clear the full bar; report which condition failed."),
    }
    OUT["verdict"]=verdict
    for k,v in verdict.items(): print(f"  {k}: {v}")

    with open(EDGE + "/WAVE4_VOL_CLUSTERING_EXITS_RESULT.json","w") as f:
        json.dump(OUT,f,indent=1)
    print("\nWROTE WAVE4_VOL_CLUSTERING_EXITS_RESULT.json")

if __name__ == "__main__":
    main()
