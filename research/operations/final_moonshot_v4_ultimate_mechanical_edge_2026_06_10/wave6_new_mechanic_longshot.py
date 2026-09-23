"""
wave6_new_mechanic_longshot.py
==============================
THRUST: new_mechanic_longshot — one genuinely-NEW mechanic, honest long-shot, strict audit.

The established gold sleeve (the thing to BEAT or EXTEND) is:
  precious-metals vol-gated (ATR14 >= 1.2*SMA100(ATR)) FVG-RETEST CONTINUATION, 2R fixed
  target, structural stop. Walk-forward fwd ~+0.23R, 7/11 yrs, ~81% XAUUSD.

This file tests TWO mechanics that are STRUCTURALLY DIFFERENT from that sleeve:

  M1) RANGE-EXPANSION BREAKOUT BOTH-WAYS (squeeze-release).
      Detect a volatility CONTRACTION squeeze at the decision bar (the OPPOSITE regime
      to the existing edge's expansion gate): ATR14 compressed vs its own SMA100 baseline
      AND Donchian-N channel width compressed vs its baseline. Then enter on the CONFIRMED
      directional break of the squeeze range (close beyond the prior N-bar high/low ->
      direction = the break). Tight ATR stop, RUNNER exit (trail). Genuinely new: this is
      contraction->expansion ONSET, BOTH directions, trailed runner — not expansion-state
      continuation with a fixed target.

  M2) MULTI-TIMEFRAME CONFLUENCE (D1 trend + H4 FVG).
      Reuse the EXACT H4 FVG-retest continuation entry (same geometry as the sleeve), but
      require the DAILY (D1) trend to AGREE with the H4 entry direction. Deep D1 gold was
      exported 2015-2026 for this. Question: does D1 confluence (a) BEAT the H4-only sleeve
      entry, or (b) provide an UNCORRELATED component (different trades, additive)?

STRICT AUDIT (every loose claim has been a leak; only audited results count):
  * ALL fills via tested geometry_lib.simulate / simulate_detail. NO hand-rolled fills/signs.
  * NO LOOKAHEAD: every gate/feature at decision bar i uses ONLY data at/<=i. Squeeze
    stats, Donchian channel, ATR ratios, D1 trend — all strictly past/at-bar. Entry decided
    on the CLOSE of bar i (a confirmed break), simulated from i forward.
  * STRICT OOS: select any tunable on TRAIN<=2024, read FORWARD 2025-2026 untouched.
  * MATCHED RANDOM null (count-matched random-direction entries at the SAME bars under the
    SAME selection) AND INVERT null (flip the entry direction) — both under the SAME rule.
  * Winsorize file-stitch bad-print bars before ATR/feature computation (reuse harden logic).
  * Real per-asset costs from ULTIMATE_REAL_COST_MAP.json.
  * Per-year 2015-2026 reported. A mechanic only "wins/extends" if it clears the sleeve
    forward bar AND beats both nulls AND is not a single-symbol artifact.

If neither beats nor extends the gold sleeve: SAY SO plainly.
"""
from __future__ import annotations
import sys, os, csv, json, random, math
from datetime import datetime
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
DATA = ROOT + "/data/mt5_research_exports"
H4_OLD = DATA + "/bridge_ftmo_deep_h4_2015_2022"
H4_NEW = DATA + "/bridge_ftmo_deep_h4_2022_2026"
H4_METALS_OLD = DATA + "/bridge_ftmo_deep_h4_2015_2022_metals"
D1_GOLD_DEEP = DATA + "/gold_d1_deep_2015_2026/XAUUSD_D1.csv"
D1_DIR = DATA + "/bridge_ftmo_deep_d1_2022_2026"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
from geometry_lib import Bar, atr14, simulate, simulate_detail

with open(EDGE + "/ULTIMATE_REAL_COST_MAP.json") as f:
    COSTMAP = json.load(f)
GC = COSTMAP["_global_median"]
def cost_for(s): return COSTMAP.get(ASSET_CLASS_BY_SYMBOL.get(s), GC)

ALL_METALS = sorted([s for s, c in ASSET_CLASS_BY_SYMBOL.items() if c == "metals"])
PRECIOUS = sorted([s for s in ALL_METALS if s.startswith("XAU") or s.startswith("XAG")])
TRAIN_MAX = 2024
SEED = 20260614

# ============================================================================
# DATA LOAD (winsorized; reuse harden's spike clamp logic verbatim)
# ============================================================================
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
    n = len(bars)
    if n < 20: return bars
    out = [Bar(b.o, b.h, b.l, b.c, b.v) for b in bars]
    for i in range(2, n-1):
        rng = sorted((bars[k].h - bars[k].l) for k in range(i-10, i) if bars[k].h > bars[k].l)
        if not rng: continue
        med = rng[len(rng)//2]
        if med <= 0: continue
        prev = bars[i-1]; nxt = bars[i+1]; b = bars[i]
        up_exc = b.h - max(prev.h, nxt.h)
        if up_exc > 8*med and nxt.h < b.h - 4*med and b.c < b.h - 4*med:
            out[i].h = max(b.o, b.c, prev.h, nxt.h) + 1.0*med
        dn_exc = min(prev.l, nxt.l) - b.l
        if dn_exc > 8*med and nxt.l > b.l + 4*med and b.c > b.l + 4*med:
            out[i].l = min(b.o, b.c, prev.l, nxt.l) - 1.0*med
    return out

_H4_CACHE = {}
def load_h4(sym):
    if sym in _H4_CACHE: return _H4_CACHE[sym]
    merged = {}
    for d in (H4_OLD, H4_METALS_OLD, H4_NEW):
        T, B = _load_one(f"{d}/{sym}_H4.csv")
        for t, b in zip(T, B): merged[t] = b   # later dir wins on overlap
    if not merged:
        _H4_CACHE[sym] = ([], []); return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    times = [k for k, _ in items]; bars = [v for _, v in items]
    bars = winsorize(times, bars)
    _H4_CACHE[sym] = (times, bars)
    return times, bars

_D1_CACHE = {}
def load_d1(sym):
    """Deep D1. For XAUUSD use the 2015-2026 deep export; otherwise the 2022-2026 dir."""
    if sym in _D1_CACHE: return _D1_CACHE[sym]
    merged = {}
    if sym == "XAUUSD":
        T, B = _load_one(D1_GOLD_DEEP)
        for t, b in zip(T, B): merged[t] = b
    Tn, Bn = _load_one(f"{D1_DIR}/{sym}_D1.csv")
    for t, b in zip(Tn, Bn): merged.setdefault(t, b)  # deep export wins for XAUUSD
    if not merged:
        _D1_CACHE[sym] = ([], []); return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    times = [k for k, _ in items]; bars = [v for _, v in items]
    bars = winsorize(times, bars)
    _D1_CACHE[sym] = (times, bars)
    return times, bars

# ============================================================================
# stats / reporting
# ============================================================================
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

def pos_years(py): return sum(1 for y, st in py.items() if st["mean_R"] > 0 and st["n"] > 0)

def report(name, recs, out_list):
    tr, fw = split(recs); py = per_year(recs)
    pj = {str(y): py[y] for y in sorted(py)}
    py_pos = pos_years(py); fwd_pos = pos_years({y: s for y, s in py.items() if y > TRAIN_MAX})
    fwd_tot = len([y for y in py if y > TRAIN_MAX])
    print(f"\n===== {name} =====")
    print(f"  TRAIN(<=2024): n={tr['n']:6d}  R={tr['mean_R']:+.4f}  w={tr['win%']:.1f}%")
    print(f"  FWD  (>=2025): n={fw['n']:6d}  R={fw['mean_R']:+.4f}  w={fw['win%']:.1f}%")
    line = "  per-year: "
    for y in sorted(py): line += f"{y}:{py[y]['mean_R']:+.3f}(n{py[y]['n']}) "
    print(line)
    print(f"  positive years: {py_pos}/{len(py)}   positive FWD years: {fwd_pos}/{fwd_tot}")
    rec = {"name": name, "train": tr, "fwd": fw, "per_year": pj,
           "pos_years": py_pos, "total_years": len(py),
           "pos_fwd_years": fwd_pos, "total_fwd_years": fwd_tot}
    out_list.append(rec)
    return rec

def by_symbol_fwd(recs):
    by = defaultdict(list)
    for d in recs:
        if d["year"] > TRAIN_MAX: by[d["sym"]].append(d["r"])
    return {s: stats(by[s]) for s in sorted(by)}

# ============================================================================
# known-at-i features
# ============================================================================
def sma_atr_ratio(atrs, i, win=100):
    lo = i - win + 1
    if lo < 14: return None
    seg = [atrs[k] for k in range(lo, i+1) if atrs[k] > 0]
    if len(seg) < win//2: return None
    m = sum(seg)/len(seg)
    if m <= 0: return None
    return atrs[i]/m

def htf_trend(bars, i, lb=30):
    if i < lb: return 0
    a = atr14(bars, i)
    if a <= 0: return 0
    diff = bars[i].c - bars[i-lb].c
    if diff > 1.0*a: return 1
    if diff < -1.0*a: return -1
    return 0

# ============================================================================
# MECHANIC 1: RANGE-EXPANSION BREAKOUT BOTH-WAYS (squeeze release)
# ============================================================================
def squeeze_breakout(symbols, donch_n=20, atr_squeeze=0.85, width_squeeze=0.85,
                     stop_mult=0.75, trail_arm_R=1.0, trail_gap_R=1.0,
                     maxbars=80, invert=False, random_dir=False, rng=None,
                     atr_win=100, width_win=100):
    """
    Squeeze-release breakout, BOTH ways. At decision bar i (using ONLY data <=i):
      - SQUEEZE detected: ATR14[i] <= atr_squeeze * SMA(ATR14, atr_win) [vol contraction]
        AND Donchian width (max(high)-min(low) over prior donch_n bars) <=
            width_squeeze * SMA(width, width_win) [range contraction].
      - BREAK confirmed: close[i] > prior donch_n-bar HIGH (long) or < prior LOW (short).
        Direction = the break direction.
      - Stop = stop_mult * ATR14[i]. Runner: trail_arm = trail_arm_R*stop, gap = trail_gap_R*stop.
    invert: flip direction (neg control). random_dir: random +-1 (neg control), same bars.
    Returns trade dicts.
    """
    out = []
    for sym in symbols:
        T, B = load_h4(sym)
        if len(B) < 200: continue
        cost = cost_for(sym); n = len(B)
        atrs = [atr14(B, i) for i in range(n)]
        # rolling Donchian width series (width at i = chan over [i-donch_n, i-1])
        for i in range(max(donch_n, 130), n-1):
            a = atrs[i]
            if a <= 0: continue
            ratio = sma_atr_ratio(atrs, i, atr_win)
            if ratio is None or ratio > atr_squeeze: continue
            # prior-N Donchian channel (strictly before i)
            pri_hi = max(B[k].h for k in range(i-donch_n, i))
            pri_lo = min(B[k].l for k in range(i-donch_n, i))
            cur_width = pri_hi - pri_lo
            # width baseline: SMA of per-bar (rolling donch width) over width_win
            wlo = i - width_win
            if wlo < donch_n: continue
            widths = []
            for j in range(wlo, i):
                wj = max(B[k].h for k in range(j-donch_n, j)) - min(B[k].l for k in range(j-donch_n, j))
                widths.append(wj)
            wbase = sum(widths)/len(widths) if widths else 0.0
            if wbase <= 0 or cur_width > width_squeeze*wbase: continue
            b = B[i]
            d = 0
            if b.c > pri_hi: d = +1
            elif b.c < pri_lo: d = -1
            if d == 0: continue
            if random_dir and rng is not None: d = rng.choice((+1, -1))
            elif invert: d = -d
            stop_dist = stop_mult*a
            r = simulate(B, i, d, stop_dist=stop_dist,
                         trail_arm=trail_arm_R*stop_dist, trail_gap=trail_gap_R*stop_dist,
                         maxbars=maxbars, cost=cost)
            out.append({"sym": sym, "year": T[i].year, "ts": T[i], "dir": d,
                        "entry_idx": i, "r": r})
    return out

# fixed-target variant (R-target instead of trailing runner) for honest comparison
def squeeze_breakout_fixedR(symbols, donch_n=20, atr_squeeze=0.85, width_squeeze=0.85,
                            stop_mult=0.75, target_R=2.0, maxbars=80,
                            invert=False, random_dir=False, rng=None,
                            atr_win=100, width_win=100):
    out = []
    for sym in symbols:
        T, B = load_h4(sym)
        if len(B) < 200: continue
        cost = cost_for(sym); n = len(B)
        atrs = [atr14(B, i) for i in range(n)]
        for i in range(max(donch_n, 130), n-1):
            a = atrs[i]
            if a <= 0: continue
            ratio = sma_atr_ratio(atrs, i, atr_win)
            if ratio is None or ratio > atr_squeeze: continue
            pri_hi = max(B[k].h for k in range(i-donch_n, i))
            pri_lo = min(B[k].l for k in range(i-donch_n, i))
            cur_width = pri_hi - pri_lo
            wlo = i - width_win
            if wlo < donch_n: continue
            widths = []
            for j in range(wlo, i):
                wj = max(B[k].h for k in range(j-donch_n, j)) - min(B[k].l for k in range(j-donch_n, j))
                widths.append(wj)
            wbase = sum(widths)/len(widths) if widths else 0.0
            if wbase <= 0 or cur_width > width_squeeze*wbase: continue
            b = B[i]
            d = 0
            if b.c > pri_hi: d = +1
            elif b.c < pri_lo: d = -1
            if d == 0: continue
            if random_dir and rng is not None: d = rng.choice((+1, -1))
            elif invert: d = -d
            stop_dist = stop_mult*a
            r = simulate(B, i, d, stop_dist=stop_dist, target_dist=target_R*stop_dist,
                         maxbars=maxbars, cost=cost)
            out.append({"sym": sym, "year": T[i].year, "ts": T[i], "dir": d,
                        "entry_idx": i, "r": r})
    return out

# ============================================================================
# MECHANIC 2: MTF CONFLUENCE (D1 trend + H4 FVG-retest continuation)
# ============================================================================
def d1_trend_at(sym, dt, lb=20):
    """D1 trend KNOWN at H4 decision time `dt`: use the most recent CLOSED daily bar
    strictly BEFORE dt's date (no lookahead — the current day's D1 bar is not complete
    when an intraday H4 bar closes). Trend = sign of (close - close[lb bars earlier])
    vs daily ATR14. Returns +1/-1/0, or None if insufficient D1 history."""
    Td, Bd = load_d1(sym)
    if len(Bd) < lb + 20: return None
    # last D1 index whose date < dt.date()
    lastj = -1
    target_date = dt.date()
    for j in range(len(Td)):
        if Td[j].date() < target_date: lastj = j
        else: break
    if lastj < lb + 14: return None
    a = atr14(Bd, lastj)
    if a <= 0: return 0
    diff = Bd[lastj].c - Bd[lastj-lb].c
    if diff > 0.5*a: return +1
    if diff < -0.5*a: return -1
    return 0

def fvg_trades(symbols, target_R=2.0, trend_lb=30, fvg_min=0.10, stop_buf=0.10,
               atr_stop_floor=0.25, invert=False, random_dir=False, rng=None,
               atr_win=100, gate=True, gate_thr=1.2,
               d1_confluence=False, d1_lb=20):
    """EXACT sleeve FVG-retest continuation (geometry identical to wave1/wave3/wave4).
    gate: ATR14 >= gate_thr*SMA100(ATR) expansion gate (the sleeve gate).
    d1_confluence: also require D1 trend (no-lookahead) to AGREE with H4 entry direction.
    Returns trade dicts incl. atr_ratio + d1_aligned flag for diagnostics."""
    out = []
    for sym in symbols:
        T, B = load_h4(sym)
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
                        d = +1; break
            elif tr == -1:
                for k in range(i-2, max(i-9, 60), -1):
                    gap_bot = B[k].h; gap_top = B[k-2].l
                    if gap_top - gap_bot < fvg_min*a: continue
                    if b.h >= gap_bot and b.c < gap_top and b.c < b.o:
                        stop_dist = max((max(b.h, gap_top) - b.c) + stop_buf*a, atr_stop_floor*a)
                        d = -1; break
            if d is None: continue
            base_dir = d  # the signal direction BEFORE controls
            ratio = sma_atr_ratio(atrs, i, atr_win)
            if gate and (ratio is None or ratio < gate_thr): continue
            d1 = d1_trend_at(sym, T[i], d1_lb)
            d1_aligned = (d1 is not None and d1 == base_dir)
            if d1_confluence:
                if d1 is None: continue
                if d1 != base_dir: continue
            # controls applied to the FILLED direction
            if random_dir and rng is not None: d = rng.choice((+1, -1))
            elif invert: d = -base_dir
            target_dist = target_R*stop_dist
            r = simulate(B, i, d, stop_dist=stop_dist, target_dist=target_dist, cost=cost)
            out.append({"sym": sym, "year": T[i].year, "ts": T[i], "dir": d,
                        "entry_idx": i, "r": r, "atr_ratio": ratio,
                        "d1_aligned": d1_aligned})
    return out

# ============================================================================
# MAIN
# ============================================================================
def main():
    out = {"thrust": "new_mechanic_longshot",
           "gold_sleeve_baseline_to_beat": {
               "spec": "precious-metals vol-gated(ATR14>=1.2*SMA100) FVG-retest 2R continuation",
               "walk_forward_fwd_R": 0.227, "fwd_pos_years": "7/11", "xauusd_share": "~81%"},
           "mechanics": {}}
    rng = random.Random(SEED)

    print("#"*78)
    print("# MECHANIC 1: RANGE-EXPANSION BREAKOUT BOTH-WAYS (squeeze release)")
    print("#"*78)
    m1 = {"variants": [], "controls": [], "by_symbol_fwd": {}}

    # ---- TRAIN-only selection over a small squeeze/exit grid ----
    # Select the config with best TRAIN(<=2024) mean_R on precious metals; read FWD untouched.
    grid = []
    for dn in (20, 30):
        for sq in (0.80, 0.90):
            for sm in (0.5, 0.75):
                grid.append(dict(donch_n=dn, atr_squeeze=sq, width_squeeze=sq, stop_mult=sm))
    sel = []
    cache = {}
    for g in grid:
        key = tuple(sorted(g.items()))
        recs = squeeze_breakout(PRECIOUS, trail_arm_R=1.0, trail_gap_R=1.0, **g)
        cache[key] = recs
        tr, fw = split(recs)
        sel.append((g, tr, fw, recs))
    sel_valid = [s for s in sel if s[1]["n"] >= 80]
    sel_valid.sort(key=lambda s: -s[1]["mean_R"])
    print("\n-- TRAIN-only selection grid (runner exit) --")
    for g, tr, fw, _ in sel:
        flag = "*" if tr["n"] >= 80 else " "
        print(f"  {flag} {g}  TRAIN n={tr['n']:4d} R={tr['mean_R']:+.4f} | (peek FWD n={fw['n']:4d} R={fw['mean_R']:+.4f})")
    if not sel_valid:
        print("  NO config met min TRAIN n>=80 -> squeeze too rare. Mechanic1 underpowered.")
        chosen_g, _, _, chosen_recs = sel[0]
    else:
        chosen_g, ctr, cfw, chosen_recs = sel_valid[0]
        print(f"\n  CHOSEN (best TRAIN R, n>=80): {chosen_g}")
    rec = report(f"M1_squeeze_runner_CHOSEN {chosen_g}", chosen_recs, m1["variants"])
    m1["chosen_config"] = chosen_g

    # also report the fixed-2R variant of the chosen config (sleeve-comparable exit)
    fr_recs = squeeze_breakout_fixedR(PRECIOUS, target_R=2.0, **chosen_g)
    report(f"M1_squeeze_fixed2R {chosen_g}", fr_recs, m1["variants"])

    # ---- controls on the CHOSEN config (runner) ----
    inv = squeeze_breakout(PRECIOUS, trail_arm_R=1.0, trail_gap_R=1.0, invert=True, **chosen_g)
    report("M1_CONTROL_invert", inv, m1["controls"])
    rnd_fwd = []
    for s in range(8):
        rr = random.Random(SEED + 100 + s)
        rnd = squeeze_breakout(PRECIOUS, trail_arm_R=1.0, trail_gap_R=1.0,
                               random_dir=True, rng=rr, **chosen_g)
        _, rfw = split(rnd)
        rnd_fwd.append(rfw["mean_R"])
    rnd_fwd.sort()
    m1["random_fwd_R_dist"] = {"min": rnd_fwd[0], "median": rnd_fwd[len(rnd_fwd)//2],
                               "max": rnd_fwd[-1], "n_draws": len(rnd_fwd)}
    print(f"\n  RANDOM-dir null FWD R over 8 draws: min={rnd_fwd[0]:+.4f} "
          f"med={rnd_fwd[len(rnd_fwd)//2]:+.4f} max={rnd_fwd[-1]:+.4f}")
    m1["by_symbol_fwd"] = by_symbol_fwd(chosen_recs)
    print("  by-symbol FWD (chosen runner):")
    for s, st in m1["by_symbol_fwd"].items():
        print(f"     {s:8s} n={st['n']:4d} R={st['mean_R']:+.4f} sum={st['sum_R']:+.2f}")
    out["mechanics"]["M1_squeeze_breakout"] = m1

    print("\n" + "#"*78)
    print("# MECHANIC 2: MTF CONFLUENCE (D1 trend + H4 FVG-retest continuation)")
    print("#"*78)
    m2 = {"variants": [], "controls": [], "by_symbol_fwd": {}}

    # baseline = the SLEEVE entry exactly (gated FVG 2R, no D1 filter)
    base = fvg_trades(PRECIOUS, target_R=2.0, gate=True, gate_thr=1.2, d1_confluence=False)
    rec_base = report("M2_sleeve_baseline_gatedFVG_2R (no D1)", base, m2["variants"])

    # MTF confluence = same entry + require D1 trend agree
    conf = fvg_trades(PRECIOUS, target_R=2.0, gate=True, gate_thr=1.2, d1_confluence=True)
    rec_conf = report("M2_MTF_confluence_D1+H4_gatedFVG_2R", conf, m2["variants"])

    # ALSO: ungated FVG + D1 confluence (does D1 replace the vol gate? uncorrelated path?)
    conf_nogate = fvg_trades(PRECIOUS, target_R=2.0, gate=False, d1_confluence=True)
    report("M2_D1confluence_NOgate_FVG_2R", conf_nogate, m2["variants"])

    # the COMPLEMENT: gated FVG trades where D1 DISAGREES (is D1 filtering OUT good or bad trades?)
    disagree = [d for d in base if not d.get("d1_aligned", False)]
    agree = [d for d in base if d.get("d1_aligned", False)]
    report("M2_diag_gatedFVG_D1_AGREE_subset", agree, m2["variants"])
    report("M2_diag_gatedFVG_D1_DISAGREE_subset", disagree, m2["variants"])

    # controls on the confluence book
    inv2 = fvg_trades(PRECIOUS, target_R=2.0, gate=True, gate_thr=1.2,
                      d1_confluence=True, invert=True)
    report("M2_CONTROL_invert_confluence", inv2, m2["controls"])
    rnd2_fwd = []
    for s in range(8):
        rr = random.Random(SEED + 200 + s)
        rnd = fvg_trades(PRECIOUS, target_R=2.0, gate=True, gate_thr=1.2,
                         d1_confluence=True, random_dir=True, rng=rr)
        _, rfw = split(rnd)
        rnd2_fwd.append(rfw["mean_R"])
    rnd2_fwd.sort()
    m2["random_fwd_R_dist"] = {"min": rnd2_fwd[0], "median": rnd2_fwd[len(rnd2_fwd)//2],
                               "max": rnd2_fwd[-1], "n_draws": len(rnd2_fwd)}
    print(f"\n  RANDOM-dir null FWD R over 8 draws (confluence): min={rnd2_fwd[0]:+.4f} "
          f"med={rnd2_fwd[len(rnd2_fwd)//2]:+.4f} max={rnd2_fwd[-1]:+.4f}")
    m2["by_symbol_fwd"] = by_symbol_fwd(conf)
    print("  by-symbol FWD (confluence):")
    for s, st in m2["by_symbol_fwd"].items():
        print(f"     {s:8s} n={st['n']:4d} R={st['mean_R']:+.4f} sum={st['sum_R']:+.2f}")

    # XAUUSD-only deep check (the only full-history symbol) for both base and confluence
    base_xau = [d for d in base if d["sym"] == "XAUUSD"]
    conf_xau = [d for d in conf if d["sym"] == "XAUUSD"]
    report("M2_XAUUSD_only_baseline", base_xau, m2["variants"])
    report("M2_XAUUSD_only_confluence", conf_xau, m2["variants"])
    out["mechanics"]["M2_mtf_confluence"] = m2

    # ========================================================================
    # VERDICT
    # ========================================================================
    SLEEVE_FWD = 0.227
    def fwdR(rec): return rec["fwd"]["mean_R"]
    m1_best = max((v for v in m1["variants"]), key=lambda v: v["fwd"]["mean_R"]) if m1["variants"] else None
    verdict = {"sleeve_fwd_R_bar": SLEEVE_FWD}

    # M1 verdict
    m1_chosen = m1["variants"][0]
    m1_inv = m1["controls"][0]
    m1_beats_sleeve = m1_chosen["fwd"]["mean_R"] > SLEEVE_FWD
    m1_beats_invert = m1_chosen["fwd"]["mean_R"] > m1_inv["fwd"]["mean_R"]
    m1_beats_rnd = m1_chosen["fwd"]["mean_R"] > m1["random_fwd_R_dist"]["max"]
    m1_sym_vals = [st["sum_R"] for st in m1["by_symbol_fwd"].values()]
    m1_total = sum(m1_sym_vals) if m1_sym_vals else 0.0
    m1_top_share = (max(m1_sym_vals)/m1_total) if m1_total > 0 and m1_sym_vals else None
    verdict["M1_squeeze_breakout"] = {
        "chosen_fwd_R": m1_chosen["fwd"]["mean_R"],
        "chosen_fwd_pos_years": f'{m1_chosen["pos_fwd_years"]}/{m1_chosen["total_fwd_years"]}',
        "beats_sleeve_fwd": m1_beats_sleeve,
        "beats_invert": m1_beats_invert,
        "beats_random_max": m1_beats_rnd,
        "top_symbol_fwd_share": m1_top_share,
        "deployable": bool(m1_beats_sleeve and m1_beats_invert and m1_beats_rnd
                           and (m1_top_share is None or m1_top_share < 0.6)),
    }

    # M2 verdict
    m2_base = rec_base; m2_conf = rec_conf
    m2_conf_beats_base = m2_conf["fwd"]["mean_R"] > m2_base["fwd"]["mean_R"]
    m2_conf_beats_sleeve = m2_conf["fwd"]["mean_R"] > SLEEVE_FWD
    m2_inv = m2["controls"][0]
    m2_beats_invert = m2_conf["fwd"]["mean_R"] > m2_inv["fwd"]["mean_R"]
    m2_beats_rnd = m2_conf["fwd"]["mean_R"] > m2["random_fwd_R_dist"]["max"]
    m2_sym_vals = [st["sum_R"] for st in m2["by_symbol_fwd"].values()]
    m2_total = sum(m2_sym_vals) if m2_sym_vals else 0.0
    m2_top_share = (max(m2_sym_vals)/m2_total) if m2_total > 0 and m2_sym_vals else None
    verdict["M2_mtf_confluence"] = {
        "baseline_fwd_R": m2_base["fwd"]["mean_R"],
        "confluence_fwd_R": m2_conf["fwd"]["mean_R"],
        "confluence_fwd_pos_years": f'{m2_conf["pos_fwd_years"]}/{m2_conf["total_fwd_years"]}',
        "confluence_beats_baseline": m2_conf_beats_base,
        "confluence_beats_sleeve_bar": m2_conf_beats_sleeve,
        "confluence_beats_invert": m2_beats_invert,
        "confluence_beats_random_max": m2_beats_rnd,
        "confluence_top_symbol_share": m2_top_share,
        "confluence_n_fwd": m2_conf["fwd"]["n"],
        "baseline_n_fwd": m2_base["fwd"]["n"],
        # "extends" = adds value as a FILTER (better per-trade or robustness) without being a single-name artifact
        "improves_per_trade_over_baseline": m2_conf_beats_base,
        "deployable_as_improvement": bool(m2_conf_beats_base and m2_conf_beats_sleeve
                                          and m2_beats_invert and m2_beats_rnd
                                          and (m2_top_share is None or m2_top_share < 0.7)),
    }

    out["verdict"] = verdict

    with open(EDGE + "/WAVE6_NEW_MECHANIC_LONGSHOT_RESULT.json", "w") as f:
        json.dump(out, f, indent=1, default=str)
    print("\n" + "="*78)
    print("VERDICT")
    print("="*78)
    print(json.dumps(verdict, indent=1))
    print("\nWROTE WAVE6_NEW_MECHANIC_LONGSHOT_RESULT.json")

if __name__ == "__main__":
    main()
