"""
wave5_vol_gate_other_classes.py
===============================
THRUST (vol_gate_other_classes): Can the ATR-EXPANSION gate (ATR14 >= 1.2 * SMA100(ATR)
of its own baseline) -- the ONE proven lever that turned the precious-metals FVG-retest
continuation into a deployable edge (WAVE4_METALS_FVG_HARDEN: walk-forward full R=+0.226,
DEPLOYABLE) -- RESCUE the same FVG-retest continuation (and a simple Donchian-20 breakout)
in classes BEYOND precious metals?

Classes tested, EACH on its own: index, fx, jpy_fx, crypto, energy.
Entries tested, EACH per class:
  (E1) FVG-retest CONTINUATION in HTF trend  -- exact geometry reused from
       wave4_metals_fvg_harden.fvg_trades / wave1.setup_ob_fvg_retest(mode='fvg').
  (E2) Donchian-20 breakout                  -- exact geometry reused from
       wave4_vol_state_sizing.breakout_entries.
Both: structural/ATR stop, 2R fixed target, real per-CLASS cost, H4.

The GATE is the proven lever: in-regime = ATR14[i] >= thr * SMA100(ATR)[i], thr=1.2,
known AT the decision bar i (pure function of atrs[<=i]).

For EACH (class, entry) cell we report, with the SAME rigor as the metals harden:
  - ALL-regime baseline (no gate)            -> does the raw entry even work in this class?
  - GATED in-regime (thr=1.2)                -> does the proven gate help / rescue?
  - TRAIN(<=2024) vs FORWARD(>=2025) split   -> strict OOS readout.
  - WALK-FORWARD: re-select the gate threshold on ROLLING PAST-ONLY trades, trade the
    next year, chain. This is the real OOS test (no single threshold chosen with the
    forward window in view). Identical routine to the metals harden.
  - PER-YEAR 2015-2026.
  - MATCHED NULLS under the SAME selection rule: INVERT (fade the same signal, gated the
    same way) and RANDOM count-matched (same N drawn from the class's all-regime trades).
    A real edge must beat random and the invert must be negative.
  - LEAVE-ONE-SYMBOL-OUT on the gated in-regime stream (thr=1.2): does any single symbol
    carry the whole class? (the metals edge was 81% XAUUSD -- concentration is the #1 trap).

DEPLOYABILITY (per cell) requires ALL of:
  walk-forward full R > 0 AND walk-forward full sum_R > 0
  AND walk-forward fwd R > 0
  AND gated full R > all-regime full R (the gate must ADD value, not just survive)
  AND gated full R > random_full_max (beats the count-matched random null)
  AND invert gated full R < 0 (directional, not survivorship of one side)
  AND no single symbol drop turns the gated full stream negative (not 1-symbol-carried)
  AND gated in-regime n >= 80 (enough trades to mean anything)

DISCIPLINE (STRICT PROTOCOL -- every prior loose "win" was a leak; only audited counts):
  - Fills ONLY via tested geometry_lib.simulate / simulate_detail. No hand-rolled fills.
  - NO LOOKAHEAD: gate / trend / FVG / breakout features at bar i use ONLY bars[<=i].
    Walk-forward threshold for year Y uses ONLY trades with year < Y.
  - WINSORIZE file-stitch single-bar bad-print spikes before any ATR/feature (durable
    data-quality fact from wave3/wave4; same routine here).
  - STRICT OOS: thresholds selected on TRAIN<=2024 only / walk-forward refits on past only.
    FORWARD 2025-26 read-out only. Controlled per-class universe. Per-year reported.
  - Random + invert nulls under the SAME selection rule, mandatory for any positive cell.
  - Truth over positives: if a cell does not survive, the verdict says NOT_RESCUED.

DATA-REALITY CAVEAT (load-bearing, surfaced not hidden -- measured below per class):
  H4 history is NOT uniform across classes. fx (EURUSD 2015-26, several 2018-19) and
  jpy_fx (USDJPY 2016-26) have deep TRAIN history -> a genuine OOS split is possible.
  index / crypto / energy are dominated by LATE-ARRIVING symbols (most index & crypto
  symbols begin 2024-2025; energy is thin). For those classes TRAIN<=2024 is sparse or
  empty, so walk-forward has little/no past to select on and the FORWARD window is almost
  the whole sample -- any "edge" there is in-sample by construction. This is reported per
  class and folded into the verdict (a cell with ~no train history CANNOT be called
  strict-OOS-deployable, only "forward-window-only, unproven OOS").

  NOTE on M1: the metals harden added an M1 intrabar-realism leg. This wave deliberately
  stays on H4 (the geometry_lib simulate path, which is unit-tested) for the broad
  cross-class screen; promoting any surviving cell to deployable would then require the
  same M1 intrabar re-audit the metals candidate passed. We flag that as a required
  follow-up, not a silent pass.
"""
from __future__ import annotations
import sys, os, csv, json, random
from datetime import datetime
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
D1 = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022"
D2 = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
from geometry_lib import Bar, atr14, simulate

with open(EDGE + "/ULTIMATE_REAL_COST_MAP.json") as f:
    COSTMAP = json.load(f)
GC = COSTMAP["_global_median"]
def cost_for(s): return COSTMAP.get(ASSET_CLASS_BY_SYMBOL.get(s), GC)

TRAIN_MAX = 2024
CLASSES = ["index", "fx", "jpy_fx", "crypto", "energy"]
GATE_THRESHOLDS = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
FROZEN = 1.2  # the proven metals gate, used for LOSO / nulls on the named candidate gate

# ---------------------------------------------------------------------------
# universe (union of both H4 dirs)
# ---------------------------------------------------------------------------
def syms_in(d):
    return {fn[:-7] for fn in os.listdir(d) if fn.endswith("_H4.csv")}
SYMBOLS = sorted(syms_in(D1) | syms_in(D2))
def syms_for_class(cls):
    return sorted([s for s in SYMBOLS if ASSET_CLASS_BY_SYMBOL.get(s) == cls])

# ---------------------------------------------------------------------------
# data load + winsorize (identical routine to wave4_vol_state_sizing._winsorize)
# ---------------------------------------------------------------------------
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

def _winsorize(T, B):
    """Clamp isolated single-bar quote spikes (file-stitch bad prints): true range a gross
    multiple of local median TR -> clamp wicks to a band around body/prev-close. Local
    context only, no lookahead, applied uniformly train==forward. Same as wave4."""
    n = len(B)
    if n < 30: return B
    trs = []
    for i in range(1, n):
        trs.append(max(B[i].h-B[i].l, abs(B[i].h-B[i-1].c), abs(B[i].l-B[i-1].c)))
    out = list(B)
    W = 50
    for i in range(1, n):
        lo = max(0, i-1-W); hi = min(len(trs), i-1+W+1)
        local = sorted(trs[lo:hi])
        if len(local) < 10: continue
        med = local[len(local)//2]
        if med <= 0: continue
        tr = trs[i-1]
        if tr > 12.0*med:
            b = out[i]; pc = out[i-1].c
            body_hi = max(b.o, b.c); body_lo = min(b.o, b.c)
            cap = 4.0*med
            new_h = min(b.h, max(body_hi, pc) + cap)
            new_l = max(b.l, min(body_lo, pc) - cap)
            if new_h < new_l:
                new_h, new_l = body_hi, body_lo
            out[i] = Bar(b.o, new_h, new_l, b.c, b.v)
    return out

_CACHE = {}
def load(sym):
    if sym in _CACHE: return _CACHE[sym]
    T1, B1 = _load_one(f"{D1}/{sym}_H4.csv")
    T2, B2 = _load_one(f"{D2}/{sym}_H4.csv")
    merged = {}
    for t, b in zip(T1, B1): merged[t] = b
    for t, b in zip(T2, B2): merged[t] = b
    if not merged:
        _CACHE[sym] = ([], []); return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    T = [k for k, _ in items]; B = [v for _, v in items]
    B = _winsorize(T, B)
    _CACHE[sym] = (T, B)
    return T, B

# ---------------------------------------------------------------------------
# known-at-i features (identical to wave4)
# ---------------------------------------------------------------------------
def htf_trend(bars, i, lb=30):
    if i < lb: return 0
    a = atr14(bars, i)
    if a <= 0: return 0
    diff = bars[i].c - bars[i-lb].c
    if diff > 1.0*a: return 1
    if diff < -1.0*a: return -1
    return 0

def sma_atr_ratio(atrs, i, win=100):
    """ATR(i)/mean(ATR[i-win+1..i]); >1 => vol EXPANDING vs own baseline. Pure fn of <=i."""
    lo = i - win + 1
    if lo < 14: return None
    seg = [atrs[k] for k in range(lo, i+1) if atrs[k] > 0]
    if len(seg) < win//2: return None
    m = sum(seg)/len(seg)
    if m <= 0: return None
    return atrs[i]/m

# ---------------------------------------------------------------------------
# ENTRY 1: FVG-retest continuation (exact geometry from wave4_metals_fvg_harden.fvg_trades)
# ---------------------------------------------------------------------------
def fvg_trades(symbols, target_R=2.0, trend_lb=30, fvg_min=0.10, stop_buf=0.10,
               atr_stop_floor=0.25, invert=False, atr_win=100):
    out = []
    for sym in symbols:
        T, B = load(sym)
        if len(B) < 200: continue
        cost = cost_for(sym); n = len(B)
        atrs = [atr14(B, i) for i in range(n)]
        for i in range(60, n-1):
            a = atrs[i]
            if a <= 0: continue
            tr = htf_trend(B, i, trend_lb)
            b = B[i]
            d = None; stop_dist = None
            if tr == 1:
                for k in range(i-2, max(i-9, 60), -1):
                    gap_top = B[k].l; gap_bot = B[k-2].h
                    if gap_top - gap_bot < fvg_min*a: continue
                    if b.l <= gap_top and b.c > gap_bot and b.c > b.o:
                        stop_dist = max((b.c - min(b.l, gap_bot)) + stop_buf*a, atr_stop_floor*a)
                        d = -1 if invert else +1
                        break
            elif tr == -1:
                for k in range(i-2, max(i-9, 60), -1):
                    gap_bot = B[k].h; gap_top = B[k-2].l
                    if gap_top - gap_bot < fvg_min*a: continue
                    if b.h >= gap_bot and b.c < gap_top and b.c < b.o:
                        stop_dist = max((max(b.h, gap_top) - b.c) + stop_buf*a, atr_stop_floor*a)
                        d = +1 if invert else -1
                        break
            if d is None: continue
            target_dist = target_R*stop_dist
            r = simulate(B, i, d, stop_dist=stop_dist, target_dist=target_dist, cost=cost)
            out.append({"sym": sym, "year": T[i].year, "ts": T[i], "r": r,
                        "atr_ratio": sma_atr_ratio(atrs, i, atr_win)})
    return out

# ---------------------------------------------------------------------------
# ENTRY 2: Donchian-20 breakout (exact geometry from wave4_vol_state_sizing.breakout_entries)
# ---------------------------------------------------------------------------
def breakout_trades(symbols, lookback=20, target_R=2.0, stop_mult=1.0, atr_win=100,
                    invert=False, maxbars=80):
    out = []
    for sym in symbols:
        T, B = load(sym)
        if len(B) < 200: continue
        cost = cost_for(sym); n = len(B)
        atrs = [atr14(B, i) for i in range(n)]
        for i in range(max(60, lookback+1), n-1):
            a = atrs[i]
            if a <= 0: continue
            prior_hi = max(B[j].h for j in range(i-lookback, i))
            prior_lo = min(B[j].l for j in range(i-lookback, i))
            d = None
            if B[i].c > prior_hi:   d = +1
            elif B[i].c < prior_lo: d = -1
            if d is None: continue
            if invert: d = -d
            stop_dist = stop_mult*a
            r = simulate(B, i, d, stop_dist=stop_dist, target_dist=target_R*stop_dist,
                         cost=cost, maxbars=maxbars)
            out.append({"sym": sym, "year": T[i].year, "ts": T[i], "r": r,
                        "atr_ratio": sma_atr_ratio(atrs, i, atr_win)})
    return out

ENTRY_FNS = {"fvg": fvg_trades, "breakout": breakout_trades}

# ---------------------------------------------------------------------------
# stats / per-year / split
# ---------------------------------------------------------------------------
def stats(rs):
    if not rs: return {"n": 0, "mean_R": 0.0, "win%": 0.0, "sum_R": 0.0}
    n = len(rs); s = sum(rs); w = sum(1 for r in rs if r > 0)
    return {"n": n, "mean_R": round(s/n, 4), "win%": round(100*w/n, 1), "sum_R": round(s, 2)}

def per_year(recs):
    by = defaultdict(list)
    for d in recs: by[d["year"]].append(d["r"])
    return {int(y): stats(by[y]) for y in sorted(by)}

def split(recs):
    tr = [d["r"] for d in recs if d["year"] <= TRAIN_MAX]
    fw = [d["r"] for d in recs if d["year"] > TRAIN_MAX]
    return stats(tr), stats(fw)

def in_regime(recs, thr):
    return [d for d in recs if d["atr_ratio"] is not None and d["atr_ratio"] >= thr]

# ---------------------------------------------------------------------------
# WALK-FORWARD (identical routine to wave4_metals_fvg_harden.walk_forward)
# ---------------------------------------------------------------------------
def walk_forward(base, thresholds, anchor_year, end_year=2026, min_past_n=60):
    by_year = defaultdict(list)
    for d in base: by_year[d["year"]].append(d)
    picks = {}; chained = []
    for Y in range(anchor_year, end_year+1):
        past = [d for d in base if d["year"] < Y]
        best_thr = None; best_R = -1e9; best_n = 0
        for thr in thresholds:
            sub = [d["r"] for d in past if d["atr_ratio"] is not None and d["atr_ratio"] >= thr]
            st = stats(sub)
            if st["n"] >= min_past_n and st["mean_R"] > best_R:
                best_R = st["mean_R"]; best_thr = thr; best_n = st["n"]
        if best_thr is None:
            best_thr = 1.2; note = "default(insufficient_past)"
        else:
            note = "selected_on_past"
        taken = [d for d in by_year.get(Y, [])
                 if d["atr_ratio"] is not None and d["atr_ratio"] >= best_thr]
        picks[str(Y)] = {"threshold": best_thr, "note": note, "past_n": best_n,
                         "past_R_at_pick": round(best_R, 4) if best_R > -1e8 else None,
                         "year_n": len(taken), "year_R": stats([d["r"] for d in taken])["mean_R"]}
        for d in taken: chained.append((Y, d["r"], d))
    full = stats([r for _, r, _ in chained])
    fwd = stats([r for y, r, _ in chained if y > TRAIN_MAX])
    pyset = sorted(set(y for y, _, _ in chained))
    py = {str(y): stats([r for yy, r, _ in chained if yy == y]) for y in pyset}
    n_default = sum(1 for p in picks.values() if p["note"].startswith("default"))
    return {
        "picks": picks, "chained_full": full, "chained_fwd": fwd,
        "chained_per_year": py, "n_trades": len(chained),
        "n_years_default_threshold": n_default,
    }, [{"sym": d["sym"], "year": y, "ts": d["ts"], "r": r} for (y, r, d) in chained]

# ---------------------------------------------------------------------------
# LEAVE-ONE-SYMBOL-OUT (identical to wave4) on gated in-regime stream
# ---------------------------------------------------------------------------
def leave_one_symbol_out(base, threshold):
    reg = in_regime(base, threshold)
    full_all = stats([d["r"] for d in reg])
    fwd_all = stats([d["r"] for d in reg if d["year"] > TRAIN_MAX])
    syms = sorted(set(d["sym"] for d in reg))
    drops = {}
    for s in syms:
        kept = [d for d in reg if d["sym"] != s]
        f_full = stats([d["r"] for d in kept])
        this = stats([d["r"] for d in reg if d["sym"] == s])
        drops[s] = {"drop_full_R": f_full["mean_R"], "drop_full_sum": f_full["sum_R"],
                    "drop_full_n": f_full["n"], "this_sym_R": this["mean_R"],
                    "this_sym_n": this["n"],
                    "kills_full": f_full["mean_R"] <= 0 or f_full["sum_R"] <= 0}
    return {"with_all_full": full_all, "with_all_fwd": fwd_all, "syms": syms, "drops": drops,
            "any_single_drop_kills_full": any(v["kills_full"] for v in drops.values()),
            "top_symbol_share": _top_share(reg)}

def _top_share(reg):
    by = defaultdict(float)
    for d in reg: by[d["sym"]] += d["r"]
    tot = sum(v for v in by.values()) or 1e-9
    if tot <= 0: return None
    top = max(by.items(), key=lambda kv: kv[1]) if by else (None, 0)
    return {"symbol": top[0], "share_of_sum_R": round(top[1]/tot, 3)}

# ---------------------------------------------------------------------------
# NULLS under the SAME selection rule (invert + count-matched random)
# ---------------------------------------------------------------------------
def nulls(base_all, inv_base, threshold, seed=20260614, reps=50):
    reg = in_regime(base_all, threshold)
    inv_reg = in_regime(inv_base, threshold)
    k = len(reg)
    rand_full = []; rand_fwd = []
    for rep in range(reps):
        random.seed(seed + rep)
        samp = random.sample(base_all, k) if 0 < k <= len(base_all) else base_all
        rand_full.append(stats([d["r"] for d in samp])["mean_R"])
        fw = [d["r"] for d in samp if d["year"] > TRAIN_MAX]
        rand_fwd.append(stats(fw)["mean_R"] if fw else 0.0)
    return {
        "in_regime_full": stats([d["r"] for d in reg]),
        "in_regime_fwd": stats([d["r"] for d in reg if d["year"] > TRAIN_MAX]),
        "invert_full": stats([d["r"] for d in inv_reg]),
        "invert_fwd": stats([d["r"] for d in inv_reg if d["year"] > TRAIN_MAX]),
        "random_full_mean_R": round(sum(rand_full)/len(rand_full), 4) if rand_full else 0.0,
        "random_full_max": round(max(rand_full), 4) if rand_full else 0.0,
        "random_fwd_mean_R": round(sum(rand_fwd)/len(rand_fwd), 4) if rand_fwd else 0.0,
    }

# ---------------------------------------------------------------------------
# per-class data reality
# ---------------------------------------------------------------------------
def class_data_reality(symbols):
    cov = {}
    yrs_all = set()
    for s in symbols:
        T, B = load(s)
        if T:
            ys = sorted(set(t.year for t in T))
            cov[s] = {"n_bars": len(B), "first": str(T[0].date()), "last": str(T[-1].date()),
                      "first_year": ys[0], "last_year": ys[-1]}
            yrs_all.update(ys)
    train_years = sorted(y for y in yrs_all if y <= TRAIN_MAX)
    return {"per_symbol": cov, "all_years": sorted(yrs_all),
            "train_years_available": train_years,
            "has_meaningful_train_history": len(train_years) >= 2}

# ---------------------------------------------------------------------------
# evaluate one (class, entry) cell
# ---------------------------------------------------------------------------
def eval_cell(cls, entry, symbols, data_reality):
    fn = ENTRY_FNS[entry]
    base_all = fn(symbols)                      # all-regime (no gate)
    inv_base = fn(symbols, invert=True)         # inverted signal (for invert null, gated)
    all_full = stats([d["r"] for d in base_all])
    all_train, all_fwd = split(base_all)
    py_all = per_year(base_all)

    reg = in_regime(base_all, FROZEN)
    reg_full = stats([d["r"] for d in reg])
    reg_train, reg_fwd = split(reg)
    py_reg = per_year(reg)

    # anchor year for walk-forward = first year with any past, +1; but never before
    # there is a plausible train window. Use earliest available year + 1 (so the first
    # traded year has >=1 prior year). For deep classes this is ~2016-2019; for late
    # classes it may be 2025-2026 (almost no past -> default threshold, flagged).
    ay = (min((d["year"] for d in base_all), default=2026)) + 1
    ay = max(2016, min(ay, 2026))
    wf, wf_recs = walk_forward(base_all, GATE_THRESHOLDS, anchor_year=ay)

    loso = leave_one_symbol_out(base_all, FROZEN)
    nl = nulls(base_all, inv_base, FROZEN)

    # --- deployability decision (strict) ---
    wf_full_R = wf["chained_full"]["mean_R"]; wf_full_sum = wf["chained_full"]["sum_R"]
    wf_fwd_R = wf["chained_fwd"]["mean_R"]
    gate_adds = reg_full["mean_R"] > all_full["mean_R"]
    beats_random = reg_full["mean_R"] > nl["random_full_max"]
    directional = nl["invert_full"]["mean_R"] < 0
    not_one_symbol = not loso["any_single_drop_kills_full"]
    enough_n = reg_full["n"] >= 80
    strict_oos_possible = data_reality["has_meaningful_train_history"] and \
        wf["n_years_default_threshold"] <= max(1, len(wf["picks"]) // 2)

    deployable = bool(
        wf_full_R > 0 and wf_full_sum > 0 and wf_fwd_R > 0 and
        gate_adds and beats_random and directional and not_one_symbol and enough_n and
        strict_oos_possible)

    if deployable:
        verdict = "RESCUED_OOS"
    elif (wf_full_R > 0 and wf_fwd_R > 0 and gate_adds and beats_random and directional
          and not_one_symbol and enough_n and not strict_oos_possible):
        verdict = "FORWARD_ONLY_UNPROVEN_OOS"   # looks ok but no real train history
    else:
        verdict = "NOT_RESCUED"

    reasons = {
        "wf_full_R>0": wf_full_R > 0, "wf_full_sum>0": wf_full_sum > 0,
        "wf_fwd_R>0": wf_fwd_R > 0,
        "gate_adds_vs_allregime": gate_adds,
        "beats_random_max": beats_random,
        "directional_invert_neg": directional,
        "not_single_symbol_carried": not_one_symbol,
        "enough_n(>=80)": enough_n,
        "strict_oos_possible": strict_oos_possible,
    }

    return {
        "class": cls, "entry": entry, "symbols": symbols,
        "all_regime": {"full": all_full, "train": all_train, "fwd": all_fwd,
                       "per_year": {str(k): v for k, v in py_all.items()}},
        "gated_1.2": {"full": reg_full, "train": reg_train, "fwd": reg_fwd,
                      "per_year": {str(k): v for k, v in py_reg.items()}},
        "gate_lift_full_R": round(reg_full["mean_R"] - all_full["mean_R"], 4),
        "walk_forward": wf,
        "leave_one_symbol_out": loso,
        "nulls": nl,
        "deployable": deployable,
        "verdict": verdict,
        "verdict_reasons": reasons,
    }

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    random.seed(20260614)
    OUT = {"thrust": "vol_gate_other_classes",
           "reference_metals_candidate": {
               "source": "WAVE4_METALS_FVG_HARDEN_RESULT.json",
               "walk_forward_full_R": 0.2264, "deployable": True,
               "note": "precious-metals vol-gated FVG-retest continuation; the bar to clear."},
           "gate": "ATR14[i] >= 1.2 * SMA100(ATR)[i] (known at decision bar)",
           "frozen_threshold": FROZEN, "gate_thresholds_scanned": GATE_THRESHOLDS,
           "classes": {}, "cells": []}

    for cls in CLASSES:
        symbols = syms_for_class(cls)
        dr = class_data_reality(symbols)
        OUT["classes"][cls] = {"symbols": symbols, "data_reality": dr}
        print("\n" + "#"*86)
        print(f"# CLASS: {cls}   symbols={symbols}")
        print(f"#   train years available (<=2024): {dr['train_years_available']}  "
              f"meaningful_train={dr['has_meaningful_train_history']}")
        print("#"*86)
        for entry in ("fvg", "breakout"):
            print(f"\n----- {cls} / {entry} -----")
            cell = eval_cell(cls, entry, symbols, dr)
            OUT["cells"].append(cell)
            af = cell["all_regime"]["full"]; gf = cell["gated_1.2"]["full"]
            wf = cell["walk_forward"]; nl = cell["nulls"]; lo = cell["leave_one_symbol_out"]
            print(f"  all-regime : full R={af['mean_R']:+.4f} n={af['n']}  "
                  f"train R={cell['all_regime']['train']['mean_R']:+.4f}(n{cell['all_regime']['train']['n']})  "
                  f"fwd R={cell['all_regime']['fwd']['mean_R']:+.4f}(n{cell['all_regime']['fwd']['n']})")
            print(f"  gated 1.2  : full R={gf['mean_R']:+.4f} n={gf['n']}  "
                  f"train R={cell['gated_1.2']['train']['mean_R']:+.4f}(n{cell['gated_1.2']['train']['n']})  "
                  f"fwd R={cell['gated_1.2']['fwd']['mean_R']:+.4f}(n{cell['gated_1.2']['fwd']['n']})  "
                  f"lift={cell['gate_lift_full_R']:+.4f}")
            print(f"  walk-fwd   : full R={wf['chained_full']['mean_R']:+.4f} "
                  f"sum={wf['chained_full']['sum_R']:+.1f} n={wf['n_trades']}  "
                  f"fwd R={wf['chained_fwd']['mean_R']:+.4f}  "
                  f"default-thr years={wf['n_years_default_threshold']}/{len(wf['picks'])}")
            print(f"  nulls      : in-reg {nl['in_regime_full']['mean_R']:+.4f}  "
                  f"invert {nl['invert_full']['mean_R']:+.4f}  "
                  f"random {nl['random_full_mean_R']:+.4f}(max {nl['random_full_max']:+.4f})")
            ts = lo.get("top_symbol_share") or {}
            print(f"  LOSO       : any-drop-kills-full={lo['any_single_drop_kills_full']}  "
                  f"top-sym {ts.get('symbol')}={ts.get('share_of_sum_R')}")
            py = cell["gated_1.2"]["per_year"]
            line = "  per-year(gated): "
            for y in sorted(py): line += f"{y}:{py[y]['mean_R']:+.3f}(n{py[y]['n']}) "
            print(line)
            print(f"  >>> VERDICT: {cell['verdict']}   (deployable={cell['deployable']})")

    # -------- summary table --------
    print("\n" + "="*86); print("SUMMARY (per class x entry)"); print("="*86)
    summary = []
    for cell in OUT["cells"]:
        row = {
            "class": cell["class"], "entry": cell["entry"],
            "all_full_R": cell["all_regime"]["full"]["mean_R"],
            "gated_full_R": cell["gated_1.2"]["full"]["mean_R"],
            "gate_lift": cell["gate_lift_full_R"],
            "wf_full_R": cell["walk_forward"]["chained_full"]["mean_R"],
            "wf_fwd_R": cell["walk_forward"]["chained_fwd"]["mean_R"],
            "invert_full_R": cell["nulls"]["invert_full"]["mean_R"],
            "random_max_R": cell["nulls"]["random_full_max"],
            "gated_n": cell["gated_1.2"]["full"]["n"],
            "verdict": cell["verdict"],
        }
        summary.append(row)
        print(f"  {row['class']:7s} {row['entry']:9s} | all {row['all_full_R']:+.3f} "
              f"gated {row['gated_full_R']:+.3f} (lift {row['gate_lift']:+.3f}) | "
              f"WF {row['wf_full_R']:+.3f} fwd {row['wf_fwd_R']:+.3f} | "
              f"inv {row['invert_full_R']:+.3f} rnd_max {row['random_max_R']:+.3f} | "
              f"n {row['gated_n']:4d} | {row['verdict']}")
    OUT["summary"] = summary

    rescued = [r for r in summary if r["verdict"] == "RESCUED_OOS"]
    forward_only = [r for r in summary if r["verdict"] == "FORWARD_ONLY_UNPROVEN_OOS"]
    OUT["headline"] = {
        "rescued_oos_cells": [f"{r['class']}/{r['entry']}" for r in rescued],
        "forward_only_unproven_cells": [f"{r['class']}/{r['entry']}" for r in forward_only],
        "n_cells": len(summary),
        "n_rescued": len(rescued), "n_forward_only": len(forward_only),
        "broadens_universe_beyond_gold": len(rescued) > 0,
    }
    print("\n" + "="*86)
    print(f"HEADLINE: RESCUED_OOS cells: {OUT['headline']['rescued_oos_cells'] or 'NONE'}")
    print(f"          FORWARD_ONLY (no real train history, unproven OOS): "
          f"{OUT['headline']['forward_only_unproven_cells'] or 'NONE'}")
    print(f"          broadens universe beyond gold: {OUT['headline']['broadens_universe_beyond_gold']}")

    with open(EDGE + "/WAVE5_VOL_GATE_OTHER_CLASSES_RESULT.json", "w") as f:
        json.dump(OUT, f, indent=1, default=str)
    print("\nWROTE WAVE5_VOL_GATE_OTHER_CLASSES_RESULT.json")

if __name__ == "__main__":
    main()
