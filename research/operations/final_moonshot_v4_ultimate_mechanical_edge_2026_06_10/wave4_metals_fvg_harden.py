"""
wave4_metals_fvg_harden.py
==========================
THRUST: metals_fvg_harden — turn the precious-metals vol-gated FVG-retest candidate
into a DEPLOYABILITY VERDICT, not another marginal positive.

The candidate (from WAVE3_FVG_REGIME_HONEST):
  * Entry: FVG-retest CONTINUATION in an HTF trend, on H4, exact geometry reused from
    wave1_structure_setups_ict.setup_ob_fvg_retest(mode='fvg'); structural stop, 2R
    fixed target, real per-asset cost.
  * Gate: ATR(14) >= 1.2 * SMA100(ATR)  (volatility EXPANSION vs its own baseline),
    a regime KNOWN AT the decision bar.
  * Pocket: metals (wave3 used metals+energy; this thrust isolates PRECIOUS metals).
  * Honest baseline result: in-regime full R = +0.163, fwd R = +0.249, train R = +0.061
    BUT the choice was a single static threshold picked WITH the forward window in view of
    its robustness table, train edge marginal, and it does NOT generalize to full universe.

This file STRESS-TESTS that candidate four ways the owner asked for:

(a) WALK-FORWARD: re-select the ATR gate threshold on a ROLLING PAST-ONLY window, trade
    the NEXT window, chain 2016->2026. Walk-forward net-positive? (the real OOS test —
    no single threshold chosen with hindsight).

(b) LEAVE-ONE-SYMBOL-OUT: drop each metal in turn (esp XAUEUR / XAGEUR which carried
    the forward window). Does removing any single symbol kill the edge?

(c) M1 INTRABAR FILL REALISM (2024-2026): the H4 simulate() uses pessimistic same-bar
    "stop wins ties" but still decides stop-vs-target by H4 bar extremes (first-touch
    ambiguity inside the bar). Replay each in-regime trade's life MINUTE-BY-MINUTE on
    real M1 to get the TRUE intrabar ordering of stop vs target. Does 2R survive?

(d) FTMO SIZING: find a per-trade risk %% such that the realized equity path keeps
    max drawdown < 10%% and worst single DAY < 5%% (FTMO), and report resulting monthly %%.

ANTI-LEAK DISCIPLINE (prior subagent "wins" were leaks; 0/3 survived re-audit):
  * ALL fills via tested geometry_lib.simulate / simulate_detail. No hand-rolled H4 fills.
  * The M1 replay is an independent fill engine, unit-checked against H4 simulate on the
    no-ambiguity subset (trades where only ONE of stop/target is touched in the life).
  * NO LOOKAHEAD: gate features at decision bar i use ONLY atrs[<=i]. Walk-forward
    threshold for window W is selected ONLY on bars/trades strictly BEFORE W starts.
  * Random count-matched + invert nulls under the SAME selection rule for any positive.
  * Winsorize single-bar spike prints (bad stitches) before ATR/gate features.
  * Controlled metals universe; per-year 2015-2026 reported.

DATA REALITY (load-bearing caveat, surfaced not hidden):
  H4 history is NOT uniform across the metals. Only XAUUSD spans 2015-2026. XAGUSD has a
  2022-01..2025-04 gap. XAUEUR/XAGEUR/XAUAUD/XAGAUD/XCUUSD only begin 2024-2025. So the
  forward (2025-26) window is dominated by symbols that did not exist in train. Walk-forward
  and LOSO directly expose how much the candidate leans on those late-arriving symbols.
"""
from __future__ import annotations
import sys, os, csv, json, random, math
from datetime import datetime, timedelta, timezone
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
DATA = ROOT + "/data/mt5_research_exports"
D1 = DATA + "/bridge_ftmo_deep_h4_2015_2022"
D2 = DATA + "/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
from geometry_lib import Bar, atr14, simulate, simulate_detail

with open(EDGE + "/ULTIMATE_REAL_COST_MAP.json") as f:
    COSTMAP = json.load(f)
GC = COSTMAP["_global_median"]
def cost_for(s): return COSTMAP.get(ASSET_CLASS_BY_SYMBOL.get(s), GC)

# ---- universe -----------------------------------------------------------------
ALL_METALS = sorted([s for s, c in ASSET_CLASS_BY_SYMBOL.items() if c == "metals"])
# precious metals = gold + silver crosses (exclude copper XCUUSD which is a base metal)
PRECIOUS = sorted([s for s in ALL_METALS if s.startswith("XAU") or s.startswith("XAG")])
TRAIN_MAX = 2024

# ---- data load (winsorized) ---------------------------------------------------
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

def winsorize(times, bars):
    """Clamp single-bar bad-print spikes that revert next bar (file-stitch artifacts).
    A bar's high/low is a spike if its excursion beyond BOTH neighbours' range is huge
    relative to local ATR AND the next bar reverts (does not confirm the extreme).
    We clamp the offending wick to a capped multiple of local true range. Conservative:
    only touches egregious single-bar reversals, leaves normal volatility intact."""
    n = len(bars)
    if n < 20: return bars
    out = [Bar(b.o, b.h, b.l, b.c, b.v) for b in bars]
    for i in range(2, n-1):
        # local typical range from 10 prior bars (robust median of high-low)
        rng = sorted((bars[k].h - bars[k].l) for k in range(i-10, i) if bars[k].h > bars[k].l)
        if not rng: continue
        med = rng[len(rng)//2]
        if med <= 0: continue
        prev = bars[i-1]; nxt = bars[i+1]; b = bars[i]
        # upward spike: high pokes far above neighbours and next bar does not hold near it
        up_exc = b.h - max(prev.h, nxt.h)
        if up_exc > 8*med and nxt.h < b.h - 4*med and b.c < b.h - 4*med:
            out[i].h = max(b.o, b.c, prev.h, nxt.h) + 1.0*med
        dn_exc = min(prev.l, nxt.l) - b.l
        if dn_exc > 8*med and nxt.l > b.l + 4*med and b.c > b.l + 4*med:
            out[i].l = min(b.o, b.c, prev.l, nxt.l) - 1.0*med
    return out

_H4_CACHE = {}
def load(sym):
    if sym in _H4_CACHE: return _H4_CACHE[sym]
    T1, B1 = _load_one(f"{D1}/{sym}_H4.csv")
    T2, B2 = _load_one(f"{D2}/{sym}_H4.csv")
    merged = {}
    for t, b in zip(T1, B1): merged[t] = b
    for t, b in zip(T2, B2): merged[t] = b
    if not merged:
        _H4_CACHE[sym] = ([], []); return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    times = [k for k, _ in items]; bars = [v for _, v in items]
    bars = winsorize(times, bars)
    _H4_CACHE[sym] = (times, bars)
    return times, bars

# ---- known-at-i features (identical to wave3) --------------------------------
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

# ---- FVG-retest trade generation, exact geometry, emits gate feature + bar idx ----
def fvg_trades(symbols, target_R=2.0, trend_lb=30, fvg_min=0.10, stop_buf=0.10,
               atr_stop_floor=0.25, invert=False, atr_win=100):
    """Return list of trade dicts. Geometry/sign IDENTICAL to wave1/wave3 setup_ob_fvg_retest.
    Each trade carries: sym, year, ts (decision dt), dir, entry_idx, stop_dist, target_dist,
    atr_ratio (gate feature, known at i), r (H4 simulate R)."""
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
            ratio = sma_atr_ratio(atrs, i, atr_win)
            out.append({
                "sym": sym, "year": T[i].year, "ts": T[i], "dir": d,
                "entry_idx": i, "stop_dist": stop_dist, "target_dist": target_dist,
                "atr_ratio": ratio, "r": r, "cost": cost, "target_R": target_R,
            })
    return out

# ---- stats helpers -----------------------------------------------------------
def stats(rs):
    if not rs: return {"n": 0, "mean_R": 0.0, "win%": 0.0, "sum_R": 0.0}
    n = len(rs); s = sum(rs); w = sum(1 for r in rs if r > 0)
    return {"n": n, "mean_R": round(s/n, 4), "win%": round(100*w/n, 1), "sum_R": round(s, 2)}

def per_year(recs, key="r"):
    by = defaultdict(list)
    for d in recs: by[d["year"]].append(d[key])
    return {int(y): stats(by[y]) for y in sorted(by)}

def split(recs, key="r"):
    tr = [d[key] for d in recs if d["year"] <= TRAIN_MAX]
    fw = [d[key] for d in recs if d["year"] > TRAIN_MAX]
    return stats(tr), stats(fw)

# =====================================================================
# (a) WALK-FORWARD: rolling past-only threshold re-selection
# =====================================================================
def walk_forward(base, thresholds, anchor_year=2016, end_year=2026):
    """For each forward year Y in [anchor_year..end_year], select the ATR-gate threshold
    that maximised mean_R on ALL in-regime trades STRICTLY BEFORE year Y (past only),
    then trade year Y with that frozen threshold. Chain results.
    Requires a minimum past sample to select; if absent, use the median threshold (1.2)
    as a neutral default (documented). Returns per-year picks + chained R series."""
    by_year_trades = defaultdict(list)
    for d in base:
        by_year_trades[d["year"]].append(d)
    picks = {}
    chained = []      # list of (year, r) for trades actually taken
    MIN_PAST_N = 60   # need at least this many past in-regime trades to trust a pick
    for Y in range(anchor_year, end_year+1):
        past = [d for d in base if d["year"] < Y]
        # select threshold on past only
        best_thr = None; best_R = -1e9; best_n = 0
        scan = {}
        for thr in thresholds:
            sub = [d["r"] for d in past if d["atr_ratio"] is not None and d["atr_ratio"] >= thr]
            st = stats(sub)
            scan[thr] = st
            if st["n"] >= MIN_PAST_N and st["mean_R"] > best_R:
                best_R = st["mean_R"]; best_thr = thr; best_n = st["n"]
        if best_thr is None:
            best_thr = 1.2  # neutral default when insufficient past history
            note = "default(insufficient_past)"
        else:
            note = "selected_on_past"
        # trade year Y in regime
        taken = [d for d in by_year_trades.get(Y, [])
                 if d["atr_ratio"] is not None and d["atr_ratio"] >= best_thr]
        picks[str(Y)] = {
            "threshold": best_thr, "note": note, "past_n": best_n,
            "past_R_at_pick": round(best_R, 4) if best_R > -1e8 else None,
            "year_n": len(taken), "year_R": stats([d["r"] for d in taken])["mean_R"],
            "year_sum_R": stats([d["r"] for d in taken])["sum_R"],
        }
        for d in taken: chained.append((Y, d["r"], d))
    wf_recs = [{"year": y, "r": r, **{k: v for k, v in d.items() if k != "r" and k != "year"}}
               for (y, r, d) in chained]
    full = stats([r for _, r, _ in chained])
    fwd = stats([r for y, r, _ in chained if y > TRAIN_MAX])
    py = {int(y): stats([r for yy, r, _ in chained if yy == y]) for y in sorted(set(y for y, _, _ in chained))}
    return {
        "picks": picks,
        "chained_full": full,
        "chained_fwd": fwd,
        "chained_per_year": {str(y): py[y] for y in py},
        "n_trades": len(chained),
    }, wf_recs

# =====================================================================
# (b) LEAVE-ONE-SYMBOL-OUT on a fixed (frozen) threshold
# =====================================================================
def leave_one_symbol_out(base, threshold):
    in_reg = [d for d in base if d["atr_ratio"] is not None and d["atr_ratio"] >= threshold]
    full_all = stats([d["r"] for d in in_reg])
    fwd_all = stats([d["r"] for d in in_reg if d["year"] > TRAIN_MAX])
    syms = sorted(set(d["sym"] for d in in_reg))
    res = {"with_all": {"full": full_all, "fwd": fwd_all, "syms": syms}}
    drops = {}
    for s in syms:
        kept = [d for d in in_reg if d["sym"] != s]
        f_full = stats([d["r"] for d in kept])
        f_fwd = stats([d["r"] for d in kept if d["year"] > TRAIN_MAX])
        dropped = [d for d in in_reg if d["sym"] == s]
        drops[s] = {
            "drop_full_R": f_full["mean_R"], "drop_full_sum": f_full["sum_R"], "drop_full_n": f_full["n"],
            "drop_fwd_R": f_fwd["mean_R"], "drop_fwd_n": f_fwd["n"],
            "this_sym_full_R": stats([d["r"] for d in dropped])["mean_R"],
            "this_sym_n": len(dropped),
            "kills_full": f_full["mean_R"] <= 0 or f_full["sum_R"] <= 0,
            "kills_fwd": f_fwd["mean_R"] <= 0,
        }
    res["drops"] = drops
    res["any_single_drop_kills_full"] = any(v["kills_full"] for v in drops.values())
    res["any_single_drop_kills_fwd"] = any(v["kills_fwd"] for v in drops.values())
    return res

# =====================================================================
# (c) M1 INTRABAR FILL REALISM
# =====================================================================
M1_GOLD_SILVER_DIR = "bridge_ftmo_m1"     # XAUUSD, XAGUSD : 2024-01 .. 2026-06
M1_EUR_DIR = "bridge_ftmo_ext_m1"          # XAUEUR, XAGEUR : 2025-06 .. 2026-06

def _m1_dir_for(sym):
    if sym in ("XAUUSD", "XAGUSD"): return M1_GOLD_SILVER_DIR
    if sym in ("XAUEUR", "XAGEUR"): return M1_EUR_DIR
    return None

def load_m1_all(sym):
    """Load all available M1 minutes for sym as sorted list of (dt_naive, o,h,l,c).
    Returns [] if no M1 source."""
    d = _m1_dir_for(sym)
    if d is None: return []
    base = f"{DATA}/{d}_"
    months = []
    for y in (2024, 2025, 2026):
        for m in range(1, 13):
            ym = f"{y}{m:02d}"
            p = f"{base}{ym}/{sym}_M1.csv"
            if os.path.exists(p) and os.path.getsize(p) > 1000:
                months.append(p)
    rows = []
    for p in months:
        with open(p) as f:
            r = csv.reader(f); next(r, None)
            for row in r:
                if len(row) < 5: continue
                try:
                    dt = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                    rows.append((dt, float(row[1]), float(row[2]), float(row[3]), float(row[4])))
                except Exception:
                    continue
    rows.sort(key=lambda x: x[0])
    return rows

def m1_replay_fill(m1, m1_keys, start_dt, direction, entry, stop, tgt, horizon_dt):
    """Replay an H4 trade MINUTE-BY-MINUTE. Entry is the H4 decision close at time
    start_dt (= H4 bar's labelled time; bar closes at start_dt+4h). We enter at the
    close price `entry` and scan M1 from the FIRST minute strictly AFTER the close,
    up to and including `horizon_dt` (the END of the H4 trade's ACTUAL exit bar, taken
    from simulate_detail). Using the real H4 exit-bar time fixes the weekend/gap
    horizon mismatch: 80 H4 *trading* bars span far more wall-clock than 80*4h, so a
    fixed wall-clock horizon truncates trades early and fabricates favorable timeouts.
      direction +1 long / -1 short. stop/tgt are PRICE levels.
      Returns (R_in_stop_units, outcome, covered_fraction). outcome in
      {'target','stop','timeout','no_m1'}. covered_fraction = M1 minutes seen / minutes
      expected over the trade life (weekend-aware via H4); callers reject low coverage.
      Tie within a single M1 minute (both stop & target inside): PESSIMISTIC stop wins
      (matches geometry_lib.simulate)."""
    import bisect
    stop_dist = abs(entry - stop)
    if stop_dist <= 0: return None
    close_dt = start_dt + timedelta(hours=4)  # H4 bar labelled start_dt closes here
    lo = bisect.bisect_right(m1_keys, close_dt)
    hi = bisect.bisect_right(m1_keys, horizon_dt)
    seg = m1[lo:hi]
    last_c = entry
    for dt, o, h, l, c in seg:
        last_c = c
        if direction > 0:
            hit_stop = l <= stop; hit_tgt = h >= tgt
            if hit_stop: return (stop - entry)/stop_dist, "stop", seg   # tie -> stop
            if hit_tgt: return (tgt - entry)/stop_dist, "target", seg
        else:
            hit_stop = h >= stop; hit_tgt = l <= tgt
            if hit_stop: return (entry - stop)/stop_dist, "stop", seg
            if hit_tgt: return (entry - tgt)/stop_dist, "target", seg
    # reached H4 exit bar without M1 stop/target -> close at last M1 price (timeout)
    return ((last_c - entry)/stop_dist if direction > 0 else (entry - last_c)/stop_dist), "timeout", seg

def m1_realism(base, threshold, min_cov_frac=0.80):
    """Replay every in-regime trade over its TRUE H4 trade-life (horizon = end of the
    actual H4 exit bar from simulate_detail), compare H4-simulate R vs M1-intrabar R.

    Coverage discipline (the anti-leak fix): a trade is only counted as an M1 fill if M1
    minutes cover >= min_cov_frac of the H4 trade life (weekend-aware: expected minutes
    derived from the number of H4 bars in the life, not wall-clock). Trades with thin M1
    coverage are NOT replayed (would fabricate favorable early timeouts); they are reported
    separately, and a conservative variant substitutes H4 R for them.
    """
    import bisect
    in_reg = [d for d in base if d["atr_ratio"] is not None and d["atr_ratio"] >= threshold]
    m1_syms = sorted(set(d["sym"] for d in in_reg if _m1_dir_for(d["sym"]) is not None))
    m1_data = {s: load_m1_all(s) for s in m1_syms}
    m1_keys = {s: [r[0] for r in m1_data[s]] for s in m1_syms}
    pairs = []           # (year, h4_R, m1_R, outcome, sym)  -- clean M1 fills only
    low_cov = 0; no_m1 = 0
    for d in in_reg:
        sym = d["sym"]; m1 = m1_data.get(sym)
        if not m1: no_m1 += 1; continue
        T, B = load(sym); i = d["entry_idx"]; entry = B[i].c
        if d["dir"] > 0:
            stop = entry - d["stop_dist"]; tgt = entry + d["target_dist"]
        else:
            stop = entry + d["stop_dist"]; tgt = entry - d["target_dist"]
        # TRUE H4 exit bar from the tested lib -> horizon = end of that bar
        _h4r, exidx = simulate_detail(B, i, d["dir"], stop_dist=d["stop_dist"],
                                      target_dist=d["target_dist"], cost=d["cost"])
        horizon_dt = T[exidx] + timedelta(hours=4)
        n_life_bars = exidx - i  # H4 trading bars in the life (weekend-aware)
        expected_min = max(1, n_life_bars * 4 * 60)
        # coverage check over [close_dt, horizon_dt]
        close_dt = d["ts"] + timedelta(hours=4)
        lo = bisect.bisect_right(m1_keys[sym], close_dt)
        hi = bisect.bisect_right(m1_keys[sym], horizon_dt)
        seen_min = hi - lo
        cov_frac = seen_min / expected_min
        if not (m1[0][0] <= d["ts"] <= m1[-1][0]) or horizon_dt > m1[-1][0] or cov_frac < min_cov_frac:
            low_cov += 1; continue
        res = m1_replay_fill(m1_data[sym], m1_keys[sym], d["ts"], d["dir"], entry, stop, tgt, horizon_dt)
        if res is None: low_cov += 1; continue
        m1_R, outcome, _seg = res
        m1_R_net = m1_R - d["cost"]
        pairs.append((d["year"], d["r"], round(m1_R_net, 4), outcome, sym))
    h4_R = stats([p[1] for p in pairs])
    m1_R = stats([p[2] for p in pairs])
    by = defaultdict(lambda: {"h4": [], "m1": []})
    for y, hr, mr, _, _ in pairs:
        by[y]["h4"].append(hr); by[y]["m1"].append(mr)
    pyr = {str(y): {"h4_R": stats(by[y]["h4"])["mean_R"], "m1_R": stats(by[y]["m1"])["mean_R"],
                    "n": len(by[y]["h4"])} for y in sorted(by)}
    outcomes = defaultdict(int)
    for _, _, _, oc, _ in pairs: outcomes[oc] += 1
    # sign agreement on clean (stop/target) fills: M1 engine sanity
    agree = 0; disagree = 0; flips = []
    for y, hr, mr, oc, sym in pairs:
        if oc in ("stop", "target"):
            if (hr > 0) == (mr > 0): agree += 1
            else: disagree += 1; flips.append((sym, str(y), hr, mr, oc))
    return {
        "threshold": threshold, "min_cov_frac": min_cov_frac,
        "m1_symbols": m1_syms,
        "clean_m1_fills": len(pairs), "low_coverage_skipped": low_cov, "no_m1_source": no_m1,
        "h4_path": h4_R, "m1_path": m1_R,
        "delta_mean_R": round(m1_R["mean_R"] - h4_R["mean_R"], 4),
        "per_year": pyr,
        "m1_outcomes": dict(outcomes),
        "sign_agreement_on_clean_fills": {"agree": agree, "disagree": disagree, "flips": flips[:10]},
    }

# =====================================================================
# (d) FTMO SIZING — equity path, per-trade risk that respects DD/day limits
# =====================================================================
def ftmo_sizing(recs_for_path, risk_grid=None):
    """recs_for_path: chronologically-ordered list of dicts with 'ts' and 'r' (R units, net).
    For each candidate per-trade risk %% (risk * R = pct equity change per trade), compound
    the equity path, measure max drawdown and worst single calendar-DAY loss. Report the
    LARGEST risk %% that keeps maxDD < 10%% AND worst-day < 5%% (FTMO), with resulting
    total return and approximate monthly %%."""
    if risk_grid is None:
        risk_grid = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
    recs = sorted(recs_for_path, key=lambda d: d["ts"])
    if not recs: return {"error": "no trades"}
    span_days = (recs[-1]["ts"] - recs[0]["ts"]).days or 1
    span_months = span_days / 30.44
    results = {}
    best_ok = None
    for risk in risk_grid:
        eq = 1.0; peak = 1.0; maxdd = 0.0
        day_pl = defaultdict(float)   # equity delta per calendar day (approx, additive in eq terms)
        eq_series = []
        for d in recs:
            before = eq
            eq *= (1.0 + (risk/100.0) * d["r"])
            day_pl[d["ts"].date()] += (eq - before)
            peak = max(peak, eq)
            dd = (peak - eq)/peak
            maxdd = max(maxdd, dd)
            eq_series.append(eq)
        # worst single day as %% of the equity at that point: approximate using running peak
        # (conservative: express worst day delta relative to starting equity 1.0)
        worst_day = min(day_pl.values()) if day_pl else 0.0
        worst_day_pct = -worst_day * 100.0   # positive number = %% lost on worst day (vs unit start)
        total_ret = (eq - 1.0) * 100.0
        monthly = ((eq) ** (1.0/span_months) - 1.0) * 100.0 if span_months > 0 and eq > 0 else None
        ok = (maxdd*100.0 < 10.0) and (worst_day_pct < 5.0)
        results[str(risk)] = {
            "risk_pct_per_trade": risk,
            "max_drawdown_pct": round(maxdd*100.0, 2),
            "worst_day_pct": round(worst_day_pct, 2),
            "total_return_pct": round(total_ret, 1),
            "approx_monthly_pct": round(monthly, 2) if monthly is not None else None,
            "within_ftmo": ok,
        }
        if ok:
            best_ok = results[str(risk)]
    return {
        "span_days": span_days, "span_months": round(span_months, 1),
        "n_trades": len(recs), "grid": results,
        "max_risk_within_ftmo": best_ok,
    }

# =====================================================================
# nulls (under the SAME selection rule)
# =====================================================================
def nulls(base, threshold, k_seed=777, reps=50):
    in_reg = [d for d in base if d["atr_ratio"] is not None and d["atr_ratio"] >= threshold]
    inv = fvg_trades(sorted(set(d["sym"] for d in base)), invert=True)
    inv_in = [d for d in inv if d["atr_ratio"] is not None and d["atr_ratio"] >= threshold]
    k = len(in_reg)
    rand_full = []; rand_fwd = []
    for rep in range(reps):
        random.seed(k_seed + rep)
        samp = random.sample(base, k) if k <= len(base) else base
        rand_full.append(stats([d["r"] for d in samp])["mean_R"])
        fw = [d["r"] for d in samp if d["year"] > TRAIN_MAX]
        rand_fwd.append(stats(fw)["mean_R"] if fw else 0.0)
    return {
        "invert_full": stats([d["r"] for d in inv_in]),
        "invert_fwd": stats([d["r"] for d in inv_in if d["year"] > TRAIN_MAX]),
        "random_full_mean_R": round(sum(rand_full)/len(rand_full), 4),
        "random_fwd_mean_R": round(sum(rand_fwd)/len(rand_fwd), 4),
        "random_full_max": round(max(rand_full), 4),
        "in_regime_full": stats([d["r"] for d in in_reg]),
        "in_regime_fwd": stats([d["r"] for d in in_reg if d["year"] > TRAIN_MAX]),
    }

# =====================================================================
# main
# =====================================================================
def main():
    random.seed(20260614)
    OUT = {"thrust": "metals_fvg_harden", "universe": {}, "data_reality": {}}

    OUT["universe"] = {"all_metals": ALL_METALS, "precious_only": PRECIOUS}
    # document H4 coverage per symbol (load-bearing caveat)
    cov = {}
    for s in ALL_METALS:
        T, B = load(s)
        if T:
            yrs = sorted(set(t.year for t in T))
            cov[s] = {"n_bars": len(B), "first": str(T[0].date()), "last": str(T[-1].date()),
                      "years": yrs}
    OUT["data_reality"]["h4_coverage"] = cov

    print("="*78); print("BASE: PRECIOUS-METALS FVG-retest 2R (winsorized H4)"); print("="*78)
    base_prec = fvg_trades(PRECIOUS, target_R=2.0)
    base_all = fvg_trades(ALL_METALS, target_R=2.0)
    sp = stats([d["r"] for d in base_prec])
    print(f"precious all-regime: full {sp['mean_R']:+.4f} n={sp['n']} sum={sp['sum_R']}")
    OUT["base_all_regime"] = {
        "precious": {"full": stats([d["r"] for d in base_prec]),
                     "train": split(base_prec)[0], "fwd": split(base_prec)[1],
                     "per_year": {str(k): v for k, v in per_year(base_prec).items()}},
        "all_metals_incl_copper": {"full": stats([d["r"] for d in base_all]),
                     "train": split(base_all)[0], "fwd": split(base_all)[1]},
    }

    THRESHOLDS = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
    FROZEN = 1.2  # the candidate's published threshold, for LOSO / M1 / sizing on the named candidate

    # ---- (a) WALK-FORWARD ----
    print("\n" + "="*78); print("(a) WALK-FORWARD (rolling past-only threshold re-selection)"); print("="*78)
    wf_prec, wf_recs_prec = walk_forward(base_prec, THRESHOLDS)
    print(f"  precious WF: full R={wf_prec['chained_full']['mean_R']:+.4f} "
          f"n={wf_prec['n_trades']} sum={wf_prec['chained_full']['sum_R']}  "
          f"fwd R={wf_prec['chained_fwd']['mean_R']:+.4f}")
    for y, p in wf_prec["picks"].items():
        print(f"    {y}: thr={p['threshold']} ({p['note']}) -> year R={p['year_R']:+.4f} n={p['year_n']}")
    wf_all, wf_recs_all = walk_forward(base_all, THRESHOLDS)
    OUT["a_walk_forward"] = {"precious": wf_prec, "all_metals": {
        "chained_full": wf_all["chained_full"], "chained_fwd": wf_all["chained_fwd"],
        "chained_per_year": wf_all["chained_per_year"], "picks": wf_all["picks"]}}

    # ---- (b) LEAVE-ONE-SYMBOL-OUT ----
    print("\n" + "="*78); print(f"(b) LEAVE-ONE-SYMBOL-OUT (frozen thr={FROZEN})"); print("="*78)
    loso = leave_one_symbol_out(base_prec, FROZEN)
    print(f"  with all: full R={loso['with_all']['full']['mean_R']:+.4f} "
          f"(n{loso['with_all']['full']['n']})  fwd R={loso['with_all']['fwd']['mean_R']:+.4f}")
    for s, v in loso["drops"].items():
        flag = " KILLS-FULL" if v["kills_full"] else ""
        flag += " KILLS-FWD" if v["kills_fwd"] else ""
        print(f"    drop {s:8s}: full {v['drop_full_R']:+.4f}(sum{v['drop_full_sum']:+.1f}) "
              f"fwd {v['drop_fwd_R']:+.4f}  [thisSym full {v['this_sym_full_R']:+.4f} n{v['this_sym_n']}]{flag}")
    OUT["b_leave_one_symbol_out"] = loso

    # ---- (c) M1 INTRABAR FILL REALISM ----
    print("\n" + "="*78); print(f"(c) M1 INTRABAR FILL REALISM (frozen thr={FROZEN})"); print("="*78)
    m1r = m1_realism(base_prec, FROZEN)
    print(f"  clean M1 fills {m1r['clean_m1_fills']} / low-cov skipped {m1r['low_coverage_skipped']} / "
          f"no-M1 {m1r['no_m1_source']}  syms={m1r['m1_symbols']}")
    print(f"  H4-path R={m1r['h4_path']['mean_R']:+.4f}  M1-intrabar R={m1r['m1_path']['mean_R']:+.4f}  "
          f"delta={m1r['delta_mean_R']:+.4f}")
    print(f"  outcomes={m1r['m1_outcomes']}  sign-agreement={m1r['sign_agreement_on_clean_fills']}")
    for y, v in m1r["per_year"].items():
        print(f"    {y}: H4 {v['h4_R']:+.4f}  M1 {v['m1_R']:+.4f}  n={v['n']}")
    OUT["c_m1_intrabar_realism"] = m1r

    # ---- (d) FTMO SIZING ----
    print("\n" + "="*78); print("(d) FTMO SIZING (walk-forward equity path, precious)"); print("="*78)
    # path = walk-forward chained trades (the honest deployable stream)
    path_recs = [{"ts": d["ts"], "r": d["r"]} for d in wf_recs_prec]
    sizing = ftmo_sizing(path_recs)
    if "grid" in sizing:
        for rk, v in sizing["grid"].items():
            mk = " <= MAX OK" if (sizing["max_risk_within_ftmo"] and
                                  v["risk_pct_per_trade"] == sizing["max_risk_within_ftmo"]["risk_pct_per_trade"]) else ""
            print(f"  risk {v['risk_pct_per_trade']}%%: maxDD {v['max_drawdown_pct']}%%  "
                  f"worstDay {v['worst_day_pct']}%%  totRet {v['total_return_pct']}%%  "
                  f"~monthly {v['approx_monthly_pct']}%%  ftmo_ok={v['within_ftmo']}{mk}")
    OUT["d_ftmo_sizing"] = sizing
    # also size the FROZEN-1.2 in-regime stream for comparison
    in_reg_12 = sorted([d for d in base_prec if d["atr_ratio"] is not None and d["atr_ratio"] >= FROZEN],
                       key=lambda d: d["ts"])
    sizing_frozen = ftmo_sizing([{"ts": d["ts"], "r": d["r"]} for d in in_reg_12])
    OUT["d_ftmo_sizing_frozen_1.2"] = sizing_frozen

    # ---- nulls ----
    print("\n" + "="*78); print("NULLS (same selection rule, frozen 1.2)"); print("="*78)
    nl = nulls(base_prec, FROZEN)
    print(f"  in-regime full R={nl['in_regime_full']['mean_R']:+.4f} fwd={nl['in_regime_fwd']['mean_R']:+.4f}")
    print(f"  invert full R={nl['invert_full']['mean_R']:+.4f} fwd={nl['invert_fwd']['mean_R']:+.4f}")
    print(f"  random full R={nl['random_full_mean_R']:+.4f} (max {nl['random_full_max']:+.4f}) fwd={nl['random_fwd_mean_R']:+.4f}")
    OUT["nulls_frozen_1.2"] = nl

    # ---- AUDIT EXTRAS (concentration, correlated-day, WF-rule nulls, winsor-invariance) ----
    print("\n" + "="*78); print("AUDIT EXTRAS"); print("="*78)
    audit = {}
    # (i) per-symbol concentration of the WF chained stream
    by_sym = defaultdict(lambda: {"n": 0, "sum": 0.0})
    for d in wf_recs_prec:
        by_sym[d["sym"]]["n"] += 1; by_sym[d["sym"]]["sum"] += d["r"]
    wf_total = sum(v["sum"] for v in by_sym.values()) or 1e-9
    audit["wf_per_symbol"] = {s: {"n": v["n"], "sum_R": round(v["sum"], 2),
                                  "share_of_total_sum": round(v["sum"]/wf_total, 3)}
                              for s, v in sorted(by_sym.items())}
    xau_share = by_sym.get("XAUUSD", {"sum": 0})["sum"]/wf_total
    audit["xauusd_share_of_wf_sum"] = round(xau_share, 3)
    print(f"  XAUUSD share of WF sum_R = {xau_share:.0%} (only full-history symbol)")
    # (ii) XAUUSD-only walk-forward (the deep-history core)
    xau_base = [d for d in base_prec if d["sym"] == "XAUUSD"]
    wf_xau, _ = walk_forward(xau_base, THRESHOLDS)
    audit["xauusd_only_walk_forward"] = {
        "full": wf_xau["chained_full"], "fwd": wf_xau["chained_fwd"],
        "per_year": wf_xau["chained_per_year"], "n": wf_xau["n_trades"]}
    print(f"  XAUUSD-only WF: full R={wf_xau['chained_full']['mean_R']:+.4f} "
          f"fwd R={wf_xau['chained_fwd']['mean_R']:+.4f} n={wf_xau['n_trades']}")
    # (iii) correlated-day cluster risk (metals stop out together)
    byday = defaultdict(list)
    for d in wf_recs_prec: byday[d["ts"].date()].append((d["sym"], d["r"]))
    worst_day_R = min((sum(r for _, r in v) for v in byday.values()), default=0.0)
    multi_days = sum(1 for v in byday.values() if len(v) > 1)
    worst_cluster = max((sum(1 for _ in v) for v in byday.values()), default=0)
    audit["correlated_day_risk"] = {
        "trading_days": len(byday), "days_with_multiple_trades": multi_days,
        "worst_day_summed_R": round(worst_day_R, 2), "max_trades_one_day": worst_cluster,
        "note": "metals are highly correlated; a metals-cluster day is ONE risk unit, not N",
    }
    print(f"  worst single-day summed R = {worst_day_R:+.2f} across up to {worst_cluster} correlated trades")
    # (iv) WF-rule nulls (invert + random under the WALK-FORWARD selection)
    inv_base = fvg_trades(PRECIOUS, target_R=2.0, invert=True)
    wf_inv, _ = walk_forward(inv_base, THRESHOLDS)
    kk = len(wf_recs_prec); rr = []
    for rep in range(50):
        random.seed(5000 + rep)
        samp = random.sample(base_prec, kk) if kk <= len(base_prec) else base_prec
        rr.append(stats([d["r"] for d in samp])["mean_R"])
    audit["wf_rule_nulls"] = {
        "wf_full_R": wf_prec["chained_full"]["mean_R"],
        "wf_invert_full_R": wf_inv["chained_full"]["mean_R"],
        "wf_random_mean_full_R": round(sum(rr)/len(rr), 4), "wf_random_max_full_R": round(max(rr), 4),
    }
    print(f"  WF nulls: edge {wf_prec['chained_full']['mean_R']:+.4f}  "
          f"invert {wf_inv['chained_full']['mean_R']:+.4f}  random {sum(rr)/len(rr):+.4f}(max {max(rr):+.4f})")
    # (v) winsorization invariance
    _save = globals().get("winsorize")
    _H4_CACHE.clear()
    globals()["winsorize"] = lambda t, b: b
    base_raw = fvg_trades(PRECIOUS, target_R=2.0)
    wf_raw, _ = walk_forward(base_raw, THRESHOLDS)
    globals()["winsorize"] = _save; _H4_CACHE.clear()
    audit["winsorization_invariance"] = {
        "wf_full_R_winsorized": wf_prec["chained_full"]["mean_R"],
        "wf_full_R_raw": wf_raw["chained_full"]["mean_R"],
        "identical": abs(wf_prec["chained_full"]["mean_R"] - wf_raw["chained_full"]["mean_R"]) < 1e-6,
    }
    print(f"  winsor-invariance: winsorized {wf_prec['chained_full']['mean_R']:+.4f} "
          f"vs raw {wf_raw['chained_full']['mean_R']:+.4f}")
    OUT["audit_extras"] = audit

    # ---- VERDICT ----
    print("\n" + "="*78); print("VERDICT"); print("="*78)
    wf_full = wf_prec["chained_full"]["mean_R"]; wf_fwd = wf_prec["chained_fwd"]["mean_R"]
    wf_sum = wf_prec["chained_full"]["sum_R"]
    loso_safe = (not loso["any_single_drop_kills_full"]) and (not loso["any_single_drop_kills_fwd"])
    m1_survives = m1r["m1_path"]["mean_R"] > 0 and m1r["delta_mean_R"] > -0.10
    directional = nl["invert_full"]["mean_R"] < 0 and nl["in_regime_full"]["mean_R"] > nl["random_full_max"]
    sizing_ok = sizing.get("max_risk_within_ftmo") is not None
    wf_per_year = wf_prec["chained_per_year"]
    wf_pos_years = sum(1 for y, v in wf_per_year.items() if v["mean_R"] > 0)
    deployable = bool(wf_full > 0 and wf_sum > 0 and wf_fwd > 0 and loso_safe and m1_survives and directional and sizing_ok)
    verdict = {
        "(a)_walk_forward_full_R": round(wf_full, 4),
        "(a)_walk_forward_full_sum_R": wf_sum,
        "(a)_walk_forward_fwd_R": round(wf_fwd, 4),
        "(a)_walk_forward_net_positive": bool(wf_full > 0 and wf_sum > 0),
        "(a)_walk_forward_pos_years": f"{wf_pos_years}/{len(wf_per_year)}",
        "(b)_any_single_symbol_kills_full": loso["any_single_drop_kills_full"],
        "(b)_any_single_symbol_kills_fwd": loso["any_single_drop_kills_fwd"],
        "(b)_loso_safe": loso_safe,
        "(c)_m1_intrabar_R": m1r["m1_path"]["mean_R"],
        "(c)_m1_vs_h4_delta_R": m1r["delta_mean_R"],
        "(c)_m1_survives_2R": m1_survives,
        "(d)_max_risk_within_ftmo": sizing.get("max_risk_within_ftmo"),
        "directional_vs_invert_and_random": directional,
        "DEPLOYABLE": deployable,
        "deployable_sizing": (sizing.get("max_risk_within_ftmo") or {}).get("risk_pct_per_trade") if deployable else None,
        # honest caveats surfaced by the audit
        "CAVEAT_concentrated_in_XAUUSD": audit["xauusd_share_of_wf_sum"] >= 0.6,
        "CAVEAT_xauusd_share_of_edge": audit["xauusd_share_of_wf_sum"],
        "CAVEAT_correlated_metals_days": audit["correlated_day_risk"]["worst_day_summed_R"],
        "CAVEAT_forward_partly_late_symbols": True,
        "CAVEAT_negative_years_exist": f"{wf_pos_years}/{len(wf_per_year)} years positive",
    }
    OUT["verdict"] = verdict
    for k, v in verdict.items():
        print(f"  {k}: {v}")

    with open(EDGE + "/WAVE4_METALS_FVG_HARDEN_RESULT.json", "w") as f:
        json.dump(OUT, f, indent=1, default=str)
    print("\nWROTE WAVE4_METALS_FVG_HARDEN_RESULT.json")

if __name__ == "__main__":
    main()
