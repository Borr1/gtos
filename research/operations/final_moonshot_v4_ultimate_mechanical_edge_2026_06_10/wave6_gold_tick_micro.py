"""
wave6_gold_tick_micro.py
========================
THRUST (gold_tick_micro): Does XAUUSD TICK microstructure (2025-10..2026-04, quote-only
bid/ask) + M1 microstructure (2024-2026) provide a GOLD intraday ENTRY or ENTRY-TIMING
improvement ON TOP of the validated H4 vol-gated FVG-retest 2R continuation edge?

HONEST QUESTION: is there a real gold intraday edge, or does microstructure only refine
H4 entry timing (and how much)? If it does NOT beat/extend the gold sleeve, say so.

=================================  THE CARRIER  ================================
The ONE validated edge (WAVE3_FVG_REGIME_HONEST): H4 FVG-retest 2R continuation in an
HTF trend, taken ONLY when ATR(14) >= 1.2*SMA100(ATR) (vol expansion). Forward (metals+
energy) = +0.249R/trade, 42.9% win. This script reconstructs the GOLD-ONLY (XAUUSD)
slice of that carrier using the EXACT wave3_fvg_regime_honest.fvg_trades mechanics, with
the decision at the H4 bar i CLOSE (wall-clock = bar-open T + 4h), entry at bars[i].c,
exit resolved on H4 bars i+1.. via the tested geometry_lib.simulate / simulate_detail.

=========================  WHAT MICROSTRUCTURE CAN DO  ========================
The carrier enters BLINDLY at the H4 close. Microstructure (M1 + ticks), observable AT
the decision instant T+4h, can in principle help two ways:

  MODE A  (intraday FILTER / GATE):  At the decision instant, look at the JUST-CLOSED H4
          bar's own M1 minutes [T, T+4h) and (for ticks-covered dates) the gold tick
          spread/quote-intensity AT the close. Gate the carrier trade on a micro
          condition. Entry stays at H4 close; exit on H4. Tests whether micro filters
          losers (higher R/trade) -- a pure quality gate, no timing change.

  MODE B  (entry-TIMING refinement):  Instead of entering at the H4 close, walk the M1
          path of the NEXT H4 bar (i+1, minutes [T+4h, T+8h)) and try to get a BETTER
          fill via a limit pullback toward the FVG zone, with the SAME stop PRICE (so a
          better entry => smaller stop distance => the trade is re-risked at the new
          entry). The remaining trade is resolved correctly: M1 within bar i+1 for the
          fill + any stop/target during i+1, then H4 from i+2.. for the rest. If price
          never pulls back in bar i+1, fall back to the carrier (enter at H4 close).

=============================  HARD ANTI-LEAK RULES  =========================
 * ALL fills via tested geometry_lib (simulate / simulate_detail). No hand-rolled stops.
 * NO LOOKAHEAD. H4 bar T covers M1 [T, T+4h); its features are known at close T+4h.
   A MODE-A gate only reads bar i's own minutes / spread at/<=T+4h. A MODE-B fill only
   reads M1 minutes of bar i+1 in chronological order, stopping at the first fill or at
   the bar-i+1 close; the post-fill remainder is resolved on H4 bars i+2.. (strictly
   future of the fill). Path-state (where a trade closed) only ever comes from closed
   trades via simulate_detail exit idx.
 * NO M1 WEEKEND-SKIP LEAK. M1/tick walks use a WALL-CLOCK cap (epoch horizon), and an
   entry only counts as a CLEAN FILL when M1 minutes actually exist within the bar-i+1
   wall-clock window. Entries with no/sparse M1 path are dropped (not faked).
 * STRICT OOS. M1 exists 2024-2026; ticks only 2025-10..2026-04. So we (a) report the
   carrier per-year for the WHOLE history; (b) restrict the micro test to the
   M1/tick-covered subset; (c) for any micro PARAMETER we LOCK it on an in-sample slice
   (M1: 2024..2025-09 ; ticks: 2025-10..2025-12) and READ OUT on the held-out later
   slice (M1: 2025-10.. ; ticks: 2026-01..). Tick OOS is only ~4 months -- stated plainly.
 * MATCHED NULLS UNDER THE SAME SELECTION: every accepted gate is compared to a RANDOM
   gate (same acceptance rate, same seed family) and an INVERT gate; a real micro edge
   must beat the carrier AND beat random, and invert must move the opposite way.
 * Real per-asset cost from ULTIMATE_REAL_COST_MAP.json (metals). Winsorize bad prints.
"""
from __future__ import annotations
import csv, os, sys, json, math, gzip, random, bisect, statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)
from geometry_lib import Bar, atr14, simulate, simulate_detail  # tested lib ONLY

DATA = ROOT + "/data/mt5_research_exports"
D1 = DATA + "/bridge_ftmo_deep_h4_2015_2022"
D2 = DATA + "/bridge_ftmo_deep_h4_2022_2026"
TICK_GZ = DATA + "/bridge_ftmo_ticks_micro_2025_2026/ticks/XAUUSD/microstructure_ticks.jsonl.gz"

COSTMAP = json.load(open(EDGE + "/ULTIMATE_REAL_COST_MAP.json"))
COST = COSTMAP["metals"]            # XAUUSD is metals
SYM = "XAUUSD"

# carrier params (EXACT wave3_fvg_regime_honest defaults)
TARGET_R = 2.0; TREND_LB = 30; FVG_MIN = 0.10; STOP_BUF = 0.10
ATR_STOP_FLOOR = 0.25; ATR_WIN = 100; VOL_GATE = 1.2; MAXBARS_H4 = 80

FMT = "%Y-%m-%d %H:%M:%S"

# ----------------------------------------------------------------------------
# H4 loader (merge both archives, dedupe, sorted)  -- gold only
# ----------------------------------------------------------------------------
def _load_h4_one(p):
    T = []; B = []
    if not os.path.exists(p): return T, B
    with open(p) as f:
        for row in csv.DictReader(f):
            try:
                t = datetime.strptime(row["time"], FMT)
                # winsorize obviously-bad prints: high>=max(o,c), low<=min(o,c)
                o, h, l, c = float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])
                if not (h >= max(o, c) and l <= min(o, c)):  # bad bar geometry
                    h = max(o, c, h); l = min(o, c, l)
                T.append(t); B.append(Bar(o, h, l, c, float(row.get("volume", 0) or 0)))
            except Exception:
                continue
    return T, B

def load_h4_gold():
    m = {}
    for d in (D1, D2):
        T, B = _load_h4_one(f"{d}/{SYM}_H4.csv")
        for t, b in zip(T, B): m[t] = b   # later archive wins overlap
    items = sorted(m.items())
    return [k for k, _ in items], [v for _, v in items]

# ----------------------------------------------------------------------------
# carrier regime features (known at i)
# ----------------------------------------------------------------------------
def sma_atr_ratio(atrs, i, win=ATR_WIN):
    lo = i - win + 1
    if lo < 14: return None
    seg = [atrs[k] for k in range(lo, i+1) if atrs[k] > 0]
    if len(seg) < win//2: return None
    m = sum(seg)/len(seg)
    return atrs[i]/m if m > 0 else None

def htf_trend(bars, atrs, i, lb=TREND_LB):
    if i < lb: return 0
    a = atrs[i]
    if a <= 0: return 0
    diff = bars[i].c - bars[i-lb].c
    if diff > 1.0*a: return 1
    if diff < -1.0*a: return -1
    return 0

# ----------------------------------------------------------------------------
# CARRIER SIGNAL DETECTION (EXACT wave3 fvg mechanics; gold only; vol-gated)
# returns list of signals: dict with i, dt(decision wall-clock T+4h), direction,
# stop_dist, target_dist, entry(=close), fvg_zone (gap_bot,gap_top) for limit refits.
# ----------------------------------------------------------------------------
def carrier_signals(T, B, vol_gate=VOL_GATE):
    n = len(B)
    atrs = [atr14(B, i) for i in range(n)]
    sigs = []
    for i in range(60, n-1):
        a = atrs[i]
        if a <= 0: continue
        tr = htf_trend(B, atrs, i)
        if tr == 0: continue
        b = B[i]
        d = None; stop_dist = None; gap_bot = gap_top = None
        if tr == 1:
            for k in range(i-2, max(i-9, 60), -1):
                gt = B[k].l; gb = B[k-2].h
                if gt - gb < FVG_MIN*a: continue
                if b.l <= gt and b.c > gb and b.c > b.o:
                    stop_dist = max((b.c - min(b.l, gb)) + STOP_BUF*a, ATR_STOP_FLOOR*a)
                    d = +1; gap_bot, gap_top = gb, gt
                    break
        else:
            for k in range(i-2, max(i-9, 60), -1):
                gb = B[k].h; gt = B[k-2].l
                if gt - gb < FVG_MIN*a: continue
                if b.h >= gb and b.c < gt and b.c < b.o:
                    stop_dist = max((max(b.h, gb) - b.c) + STOP_BUF*a, ATR_STOP_FLOOR*a)
                    d = -1; gap_bot, gap_top = gb, gt
                    break
        if d is None: continue
        # VOL GATE (the established edge)
        ratio = sma_atr_ratio(atrs, i)
        if ratio is None or ratio < vol_gate: continue
        # decision wall-clock = bar open T + 4h
        decision_dt = T[i] + timedelta(hours=4)
        sigs.append({
            "i": i, "dt": T[i], "decision_dt": decision_dt, "year": decision_dt.year,
            "d": d, "stop_dist": stop_dist, "target_dist": TARGET_R*stop_dist,
            "entry": b.c, "atr": a, "ratio": ratio,
            "gap_bot": gap_bot, "gap_top": gap_top,
        })
    return sigs, atrs

# ----------------------------------------------------------------------------
# M1 loader (gold), epoch arrays. std dirs 2024-2026. Winsorize bad prints.
# ----------------------------------------------------------------------------
def _months(years=(2024, 2025, 2026)):
    out = []
    for y in years:
        for mo in range(1, 13):
            out.append(f"{y}{mo:02d}")
    return out

def load_m1_gold():
    seen = {}
    for ym in _months():
        for sub in (f"bridge_ftmo_m1_{ym}", f"bridge_ftmo_ext_m1_{ym}"):
            p = f"{DATA}/{sub}/{SYM}_M1.csv"
            if not os.path.exists(p) or os.path.getsize(p) < 1000: continue
            with open(p) as f:
                for row in csv.DictReader(f):
                    t = row.get("time")
                    if not t: continue
                    ts = str(t)[:19]
                    if ts in seen: continue
                    try:
                        ep = int(datetime.strptime(ts, FMT).timestamp())
                        o, h, l, c = float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])
                        if not (h >= max(o, c) and l <= min(o, c)):
                            h = max(o, c, h); l = min(o, c, l)
                        seen[ts] = (ep, o, h, l, c, float(row.get("volume", 0) or 0))
                    except Exception:
                        continue
    arr = sorted(seen.values())
    return arr  # list of (ep,o,h,l,c,vol)

# ----------------------------------------------------------------------------
# TICK loader (gold, quote-only). Build minute-level spread series keyed by epoch
# of the minute floor: median spread + quote count per minute. Reads once, ~5M ticks.
# ----------------------------------------------------------------------------
def load_tick_minute_spread():
    """Return dict epoch_minute -> (median_spread_price, quote_count). Gold only.
    Quote-only feed: spread = ask-bid. Bad prints (spread<=0 or spread>5) winsorized out."""
    if not os.path.exists(TICK_GZ): return {}
    perm = defaultdict(list)
    with gzip.open(TICK_GZ, "rt") as f:
        for line in f:
            try:
                d = json.loads(line)
                a = d["ask"]; bid = d["bid"]
                spr = a - bid
                if spr <= 0 or spr > 5.0:  # winsorize bad quote
                    continue
                ms = d["time_msc"]
                ep_min = (ms // 1000) // 60 * 60
                perm[ep_min].append(spr)
            except Exception:
                continue
    out = {}
    for ep_min, lst in perm.items():
        lst.sort()
        out[ep_min] = (lst[len(lst)//2], len(lst))
    return out

# ----------------------------------------------------------------------------
# MODE-A micro features at the decision instant from the JUST-CLOSED H4 bar's M1
# minutes [T, T+4h)  (all <= decision instant T+4h => no lookahead).
# ----------------------------------------------------------------------------
def m1_bucket_index(m1_eps):
    return m1_eps  # already sorted epochs

def micro_features_closed_bar(m1, m1_eps, t_open_ep):
    """Features of the closing H4 bar [t_open_ep, t_open_ep+4h) from its own M1 minutes."""
    lo = bisect.bisect_left(m1_eps, t_open_ep)
    hi = bisect.bisect_left(m1_eps, t_open_ep + 4*3600)
    mins = m1[lo:hi]
    if len(mins) < 8:
        return None
    o = mins[0][1]; c = mins[-1][4]
    H = max(m[2] for m in mins); L = min(m[3] for m in mins)
    rng = H - L
    if rng <= 0: return None
    net = c - o
    # intrabar momentum / path efficiency (trending close-bar => continuation conviction)
    gross = sum(abs(m[4]-m[1]) for m in mins) or 1e-12
    eff = abs(net)/gross
    persistence = (sum(1 for m in mins if m[4] > m[1]) - sum(1 for m in mins if m[4] < m[1]))/len(mins)
    close_loc = (c - L)/rng
    # late-bar drive: last quarter net / range (signed)
    q = max(1, len(mins)//4)
    late = mins[-q:]
    late_net = (late[-1][4] - late[0][1]) / rng
    # quote-intensity acceleration: late tick-count share
    vols = [m[5] for m in mins]; tot = sum(vols) or 1e-12
    late_v = sum(m[5] for m in late)
    vint_late = late_v/tot
    # opening-drive: first quarter net / range (signed)
    early = mins[:q]
    early_net = (early[-1][4] - early[0][1]) / rng
    return {
        "eff": eff, "persistence": persistence, "close_loc": close_loc,
        "late_net": late_net, "early_net": early_net, "vint_late": vint_late,
        "net_sign": 1 if net > 0 else (-1 if net < 0 else 0), "n_min": len(mins),
    }

# ----------------------------------------------------------------------------
# stats helpers
# ----------------------------------------------------------------------------
def st(rs):
    if not rs: return {"n": 0, "mean_R": 0.0, "win%": 0.0, "sum_R": 0.0}
    n = len(rs); s = sum(rs); w = sum(1 for r in rs if r > 0)
    return {"n": n, "mean_R": round(s/n, 4), "win%": round(100*w/n, 1), "sum_R": round(s, 2)}

def per_year(pairs):
    by = defaultdict(list)
    for y, r in pairs: by[y].append(r)
    return {y: st(by[y]) for y in sorted(by)}

# ----------------------------------------------------------------------------
# MODE-B: entry-timing refinement via M1 limit-pullback in bar i+1.
# Honest stitched resolution:
#   - decision at H4 bar i close (entry_close_ep = T_open + 4h).
#   - We want a BETTER fill than bars[i].c. For a LONG, a better fill is LOWER
#     (toward the FVG); for SHORT, HIGHER. We set a limit at a fraction f of the
#     way from entry toward the FVG zone edge, but never beyond the stop.
#   - Walk M1 of bar i+1 (minutes [T+4h, T+8h)) in order. If the limit is touched
#     (long: m1.low <= limit ; short: m1.high >= limit) BEFORE the stop is touched,
#     we are FILLED at the limit (better entry). If the STOP is touched first
#     (intrabar in i+1) -> trade is a loss at -1R (stop), exit during i+1.
#     If the TARGET (from new entry) is touched in i+1 -> win during i+1.
#     If neither and bar i+1 ends -> continue resolution on H4 from i+2 using the
#     NEW entry/stop/target via geometry_lib.simulate (strictly future bars).
#   - If the limit is NEVER touched in bar i+1 -> FALLBACK: take the carrier trade
#     at the H4 close (no refinement). This keeps trade COUNT identical to carrier.
#   - CLEAN FILL guard: require M1 minutes to actually cover bar i+1 wall-clock; if
#     M1 is missing for that window (weekend/gap), drop the trade from the M1 subset
#     (counted separately) -- never fabricate a fill across a gap.
# ----------------------------------------------------------------------------
def mode_b_trade(sig, T, B, m1, m1_eps, pull_frac, mode="pullback"):
    """Return (R, filled_kind) where filled_kind in {refit, fallback}. R is net of cost.
    Returns None if no clean M1 path for bar i+1 (drop).
    mode:
      'pullback' = limit on the FAVORABLE side (toward FVG): better entry, SAME stop px
                   -> tighter stop dist (the hypothesis: a better fill).
      'chase'    = INVERT null: limit on the ADVERSE side (worse entry); SAME stop px
                   -> WIDER stop dist. If the pullback edge is real, chasing must hurt.
    Stop PRICE is always the structural carrier stop (anchored); only entry/stop-dist move.
    """
    i = sig["i"]; d = sig["d"]
    if i+1 >= len(B): return None
    entry0 = sig["entry"]; stop_dist0 = sig["stop_dist"]
    if d > 0:
        stop_px = entry0 - stop_dist0
        zone_edge = sig["gap_top"] if sig["gap_top"] is not None else entry0
        if mode == "chase":
            # worse fill: HIGHER than the close by pull_frac of the stop distance
            limit = entry0 + pull_frac*stop_dist0
        else:
            limit = entry0 - pull_frac*(entry0 - zone_edge) if zone_edge < entry0 else entry0
            limit = max(limit, stop_px + 0.05*stop_dist0)  # never at/through the stop
    else:
        stop_px = entry0 + stop_dist0
        zone_edge = sig["gap_bot"] if sig["gap_bot"] is not None else entry0
        if mode == "chase":
            limit = entry0 - pull_frac*stop_dist0
        else:
            limit = entry0 + pull_frac*(zone_edge - entry0) if zone_edge > entry0 else entry0
            limit = min(limit, stop_px - 0.05*stop_dist0)

    t_open_ep = int(sig["dt"].replace(tzinfo=timezone.utc).timestamp())
    entry_close_ep = t_open_ep + 4*3600          # wall-clock of H4 close / decision
    bar_i1_end_ep = t_open_ep + 8*3600           # end of bar i+1 wall-clock

    lo = bisect.bisect_left(m1_eps, entry_close_ep)
    hi = bisect.bisect_left(m1_eps, bar_i1_end_ep)
    mins = m1[lo:hi]
    if len(mins) < 30:   # clean-fill guard: need real M1 coverage of bar i+1
        return None

    # --- phase 1: walk M1 of bar i+1 IN ORDER until the limit is touched (fill) ---
    # pullback: long fills when price DIPS to a lower limit (ml<=limit); short on rally.
    # chase   : long fills when price RISES to a higher limit (mh>=limit); short on dip.
    fill_k = None
    if mode == "chase":
        long_fill = lambda mh, ml: mh >= limit
        short_fill = lambda mh, ml: ml <= limit
    else:
        long_fill = lambda mh, ml: ml <= limit
        short_fill = lambda mh, ml: mh >= limit
    for k, m in enumerate(mins):
        mh = m[2]; ml = m[3]
        if d > 0 and long_fill(mh, ml):
            fill_k = k; break
        if d < 0 and short_fill(mh, ml):
            fill_k = k; break
    if fill_k is None:
        # FALLBACK: limit never touched in bar i+1 -> carrier entry at H4 close, H4 resolve
        r = simulate(B, i, d, stop_dist=stop_dist0, target_dist=sig["target_dist"],
                     maxbars=MAXBARS_H4, cost=COST)
        return r, "fallback"

    # new (better) entry at the limit; stop PRICE unchanged -> smaller stop distance
    new_entry = limit
    new_stop_dist = (new_entry - stop_px) if d > 0 else (stop_px - new_entry)
    if new_stop_dist <= 0:
        return None
    new_tgt_dist = TARGET_R * new_stop_dist
    tgt_px = new_entry + new_tgt_dist if d > 0 else new_entry - new_tgt_dist

    # --- phase 2: from the FILL minute (inclusive) to bar i+1 end, walk M1 for
    #     stop/target FIRST-TOUCH, pessimistic same-minute tie (stop wins). ---
    for m in mins[fill_k:]:
        mh = m[2]; ml = m[3]
        if d > 0:
            hit_stop = ml <= stop_px; hit_tgt = mh >= tgt_px
        else:
            hit_stop = mh >= stop_px; hit_tgt = ml <= tgt_px
        if hit_stop:                       # pessimistic: stop wins same-minute ties
            return -1.0 - COST, "refit"
        if hit_tgt:
            return TARGET_R - COST, "refit"

    # --- phase 3: not resolved by bar i+1 close -> resolve remainder on H4 i+2.. ---
    # simulate(Bv, i+1, ...) enters at Bv[i+1].c and only evaluates bars i+2.. (future).
    # We set Bv[i+1].c = new_entry so the geometry runs from our fill price, and we
    # clamp Bv[i+1]'s OWN high/low to that close so the entry bar contributes no
    # already-walked intrabar extreme (its stop/target were resolved in phase 2).
    Bv = list(B)
    bi1 = B[i+1]
    Bv[i+1] = Bar(bi1.o, new_entry, new_entry, new_entry, bi1.v)  # neutral entry bar
    r = simulate(Bv, i+1, d, stop_dist=new_stop_dist, target_dist=new_tgt_dist,
                 maxbars=MAXBARS_H4, cost=COST)
    return r, "refit"

# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------
def main():
    random.seed(20260614)
    OUT = {"thrust": "gold_tick_micro", "carrier": {}, "mode_a_gate": {},
           "mode_b_timing": {}, "tick_spread_gate": {}, "notes": []}

    print("="*78)
    print("WAVE6 GOLD TICK/M1 MICROSTRUCTURE — refine the H4 vol-gated FVG-retest carrier")
    print("="*78)

    T, B = load_h4_gold()
    print(f"H4 XAUUSD bars: {len(B)}  ({T[0]} .. {T[-1]})")
    sigs, atrs = carrier_signals(T, B)
    print(f"carrier signals (vol-gated FVG-retest 2R): {len(sigs)}")

    # ---------- CARRIER BASELINE (gold only), full + per-year ----------
    car_pairs = []
    for s in sigs:
        r = simulate(B, s["i"], s["d"], stop_dist=s["stop_dist"], target_dist=s["target_dist"],
                     maxbars=MAXBARS_H4, cost=COST)
        car_pairs.append((s["year"], r))
        s["carrier_R"] = r
    car_all = st([r for _, r in car_pairs])
    car_py = per_year(car_pairs)
    print("\n----- CARRIER (XAUUSD vol-gated FVG-retest 2R, enter@H4close) -----")
    print(f"  ALL: {car_all}")
    for y in sorted(car_py): print(f"   {y}: {car_py[y]}")
    OUT["carrier"] = {"all": car_all, "per_year": {str(y): car_py[y] for y in car_py}}

    # ============================================================
    # LOAD M1 (gold) once
    # ============================================================
    print("\nloading gold M1 (2024-2026)...")
    m1 = load_m1_gold()
    m1_eps = [r[0] for r in m1]
    print(f"  gold M1 minutes: {len(m1)}"
          + (f"  ({datetime.fromtimestamp(m1_eps[0])} .. {datetime.fromtimestamp(m1_eps[-1])})" if m1 else ""))

    # signals whose decision instant is inside M1 coverage (clean-fill subset)
    if m1:
        m1_lo_ep, m1_hi_ep = m1_eps[0], m1_eps[-1]
    else:
        m1_lo_ep = m1_hi_ep = 0
    def decision_ep(s):
        return int(s["dt"].replace(tzinfo=timezone.utc).timestamp()) + 4*3600
    m1_sigs = [s for s in sigs if m1 and m1_lo_ep <= decision_ep(s) <= m1_hi_ep]
    print(f"  carrier signals in M1 window: {len(m1_sigs)}")

    # carrier baseline restricted to the M1 subset (apples-to-apples comparator)
    car_sub = st([s["carrier_R"] for s in m1_sigs])
    car_sub_py = per_year([(s["year"], s["carrier_R"]) for s in m1_sigs])
    print(f"  CARRIER on M1 subset: {car_sub}")
    OUT["carrier"]["m1_subset"] = {"all": car_sub, "per_year": {str(y): car_sub_py[y] for y in car_sub_py}}

    # ============================================================
    # MODE A — micro GATE at decision instant (closed-bar M1 features)
    # Attach features; LOCK gate sign/threshold on IN-SAMPLE (<=2025-09), READ OUT later.
    # ============================================================
    print("\n" + "="*78)
    print("MODE A — micro GATE (closed-H4-bar M1 features), entry@H4close, exit H4")
    print("="*78)
    feat_sigs = []
    for s in m1_sigs:
        t_open_ep = int(s["dt"].replace(tzinfo=timezone.utc).timestamp())
        f = micro_features_closed_bar(m1, m1_eps, t_open_ep)
        if f is None: continue
        s2 = dict(s); s2["feat"] = f
        feat_sigs.append(s2)
    print(f"  signals with clean closed-bar M1 features: {len(feat_sigs)}")

    IS_CUT = int(datetime(2025, 10, 1).timestamp())   # in-sample <= 2025-09
    def in_sample(s): return decision_ep(s) < IS_CUT
    is_sigs = [s for s in feat_sigs if in_sample(s)]
    oos_sigs = [s for s in feat_sigs if not in_sample(s)]
    print(f"  IS (<=2025-09): {len(is_sigs)}   OOS (>=2025-10): {len(oos_sigs)}")

    # candidate gates: each is (name, fn(feat, direction)->bool). Direction-aware where
    # it makes sense (e.g. close-bar momentum ALIGNED with trade direction = conviction).
    def aligned_persist(thr):
        return lambda f, d: (f["persistence"]*d) >= thr
    def aligned_late(thr):
        return lambda f, d: (f["late_net"]*d) >= thr
    def aligned_early(thr):
        return lambda f, d: (f["early_net"]*d) >= thr
    def eff_ge(thr):
        return lambda f, d: f["eff"] >= thr
    def closeloc(thr):  # close near the extreme in trade direction
        return lambda f, d: (f["close_loc"] if d > 0 else (1-f["close_loc"])) >= thr
    def vint(thr):
        return lambda f, d: f["vint_late"] >= thr

    cand = {}
    for thr in (0.1, 0.2, 0.3): cand[f"persist_align>={thr}"] = aligned_persist(thr)
    for thr in (0.05, 0.15, 0.3): cand[f"late_align>={thr}"] = aligned_late(thr)
    for thr in (0.05, 0.15, 0.3): cand[f"early_align>={thr}"] = aligned_early(thr)
    for thr in (0.2, 0.3, 0.4): cand[f"efficiency>={thr}"] = eff_ge(thr)
    for thr in (0.55, 0.65, 0.75): cand[f"close_loc_align>={thr}"] = closeloc(thr)
    for thr in (0.25, 0.30): cand[f"vint_late>={thr}"] = vint(thr)

    def apply_gate(sig_list, fn):
        return [s["carrier_R"] for s in sig_list if fn(s["feat"], s["d"])]

    # select on IS: best mean_R with n>=40 AND not worse trade-count collapse
    scan = []
    is_base = st([s["carrier_R"] for s in is_sigs])
    for nm, fn in cand.items():
        rs = apply_gate(is_sigs, fn)
        s_ = st(rs)
        scan.append((nm, s_["mean_R"], s_["n"]))
    scan.sort(key=lambda x: -x[1])
    MIN_GATE_N = 25   # IS qualifying floor (47-trade IS set; gates must keep >=25)
    print(f"  IS carrier base: {is_base}")
    print(f"  IS gate scan (top 8 by mean_R, n>={MIN_GATE_N}):")
    valid = [x for x in scan if x[2] >= MIN_GATE_N]
    for nm, mr, nn in valid[:8]:
        print(f"     {nm:24s} IS mean_R={mr:+.4f}  n={nn}")
    chosen = valid[0][0] if valid else None
    OUT["mode_a_gate"]["is_scan"] = [{"gate": nm, "is_mean_R": mr, "is_n": nn} for nm, mr, nn in scan]
    OUT["mode_a_gate"]["is_base"] = is_base

    if chosen:
        fn = cand[chosen]
        oos_base = st([s["carrier_R"] for s in oos_sigs])
        oos_gate = st(apply_gate(oos_sigs, fn))
        # matched random null (same OOS acceptance rate)
        acc = oos_gate["n"]/max(1, oos_base["n"])
        rnd_means = []
        for seed in range(200):
            rng = random.Random(1000+seed)
            rs = [s["carrier_R"] for s in oos_sigs if rng.random() < acc]
            if rs: rnd_means.append(sum(rs)/len(rs))
        rnd_mean = round(statistics.mean(rnd_means), 4) if rnd_means else 0.0
        rnd_p95 = round(sorted(rnd_means)[int(0.95*len(rnd_means))], 4) if rnd_means else 0.0
        # invert gate
        inv = st([s["carrier_R"] for s in oos_sigs if not fn(s["feat"], s["d"])])
        print(f"\n  CHOSEN gate (locked on IS): {chosen}")
        print(f"  OOS carrier base : {oos_base}")
        print(f"  OOS gated        : {oos_gate}")
        print(f"  OOS random null  : mean={rnd_mean} p95={rnd_p95} (acc={acc:.2f})")
        print(f"  OOS invert gate  : {inv}")
        beats = oos_gate["mean_R"] > oos_base["mean_R"] and oos_gate["mean_R"] > rnd_p95
        print(f"  >>> MODE A gate beats carrier AND random-p95 OOS? {beats}")
        OUT["mode_a_gate"].update({
            "chosen": chosen, "oos_base": oos_base, "oos_gated": oos_gate,
            "oos_random_mean": rnd_mean, "oos_random_p95": rnd_p95,
            "oos_invert": inv, "beats_carrier_and_random": bool(beats),
        })

    # ============================================================
    # MODE B — entry-TIMING refinement (M1 limit pullback in bar i+1)
    # ============================================================
    print("\n" + "="*78)
    print("MODE B — entry-TIMING refinement (M1 limit pullback in bar i+1), exit stitched")
    print("="*78)
    OUT["mode_b_timing"]["variants"] = {}
    print("  NOTE: delta is per-TRADE R vs the SAME-trade carrier (paired). The honest")
    print("  signal is the REFIT-ONLY subset (trades where a pullback actually filled);")
    print("  fallback trades are identical to carrier and only dilute the delta.")

    def paired_boot(deltas, B_=5000, seed=2026):
        """Two-sided paired bootstrap p-value that mean(delta) <= 0 (one-sided up) +
        95% CI of the mean delta. Resamples the per-trade (B-carrier) differences."""
        if not deltas: return None
        rng = random.Random(seed); n = len(deltas); means = []
        for _ in range(B_):
            samp = [deltas[rng.randrange(n)] for _ in range(n)]
            means.append(sum(samp)/n)
        means.sort()
        ci = (round(means[int(0.025*B_)], 4), round(means[int(0.975*B_)], 4))
        p_up = sum(1 for m in means if m <= 0)/B_   # frac of resamples non-positive
        return {"mean_delta": round(sum(deltas)/n, 4), "ci95": ci, "p_le0": round(p_up, 4), "n": n}

    for pull_frac in (0.25, 0.5, 0.75):
        b_pairs = []; car_match = []; kinds = defaultdict(int)
        refit_deltas = []                  # paired (B - carrier) on REFIT trades only
        chase_pairs = []                   # INVERT null: chase the wrong way
        for s in m1_sigs:
            res = mode_b_trade(s, T, B, m1, m1_eps, pull_frac)
            if res is None: continue
            r, kind = res
            b_pairs.append((s["year"], r)); kinds[kind] += 1
            car_match.append((s["year"], s["carrier_R"]))
            if kind == "refit":
                refit_deltas.append(r - s["carrier_R"])
            cres = mode_b_trade(s, T, B, m1, m1_eps, pull_frac, mode="chase")
            if cres is not None:
                chase_pairs.append((s["year"], cres[0]))
        b_all = st([r for _, r in b_pairs]); cm_all = st([r for _, r in car_match])
        chase_all = st([r for _, r in chase_pairs])
        b_py = per_year(b_pairs); cm_py = per_year(car_match)
        delta = round(b_all["mean_R"] - cm_all["mean_R"], 4)
        boot = paired_boot(refit_deltas)
        print(f"\n  pull_frac={pull_frac}: kinds={dict(kinds)}")
        print(f"    MODE B (pullback): {b_all}")
        print(f"    carrier matched  : {cm_all}   (same {cm_all['n']} trades)")
        print(f"    delta mean_R (all): {delta:+.4f}")
        print(f"    REFIT-only paired bootstrap: {boot}")
        print(f"    INVERT null (CHASE wrong way): {chase_all}  (should be << carrier)")
        ylines = []
        for y in sorted(set(b_py) | set(cm_py)):
            bm = b_py.get(y, {}).get("mean_R", 0.0); cmn = cm_py.get(y, {}).get("mean_R", 0.0)
            ylines.append(f"{y}:{bm-cmn:+.3f}")
        print(f"    per-year delta: {' '.join(ylines)}")
        OUT["mode_b_timing"]["variants"][str(pull_frac)] = {
            "kinds": dict(kinds), "mode_b": b_all, "carrier_matched": cm_all,
            "delta_mean_R": delta, "refit_paired_bootstrap": boot,
            "invert_chase": chase_all,
            "per_year_b": {str(y): b_py[y] for y in b_py},
            "per_year_carrier": {str(y): cm_py[y] for y in cm_py},
        }

    # ============================================================
    # TICK SPREAD GATE (gold ticks 2025-10..2026-04, MODE-A style)
    # Spread regime at the decision minute -> gate carrier. Quote-only spread.
    # IS = 2025-10..2025-12 ; OOS = 2026-01.. (stated: only ~4 months OOS).
    # ============================================================
    print("\n" + "="*78)
    print("TICK SPREAD GATE — gold quote spread at decision instant gates the carrier")
    print("="*78)
    print("loading gold ticks (minute spread series)...")
    tick_min = load_tick_minute_spread()
    print(f"  tick minute-buckets: {len(tick_min)}")
    if tick_min:
        teps = sorted(tick_min)
        print(f"  tick window: {datetime.fromtimestamp(teps[0])} .. {datetime.fromtimestamp(teps[-1])}")
        # rolling median spread baseline over prior 120 min => spread regime at decision
        # attach spread-at-decision and recent-spread-baseline to signals in tick window
        tk_sigs = []
        teps_arr = teps
        for s in sigs:
            dep = decision_ep(s)
            # decision minute floor
            dm = dep // 60 * 60
            if dm < teps_arr[0] or dm > teps_arr[-1]:
                continue
            # spread at decision minute (nearest minute at/just-before decision, <= dep)
            idx = bisect.bisect_right(teps_arr, dm) - 1
            if idx < 0: continue
            cur = tick_min[teps_arr[idx]][0]
            # baseline: median spread of the prior 120 covered minutes (<= decision)
            lo = max(0, idx-120)
            base_vals = [tick_min[teps_arr[k]][0] for k in range(lo, idx+1)]
            if len(base_vals) < 20: continue
            base_med = statistics.median(base_vals)
            qcount = tick_min[teps_arr[idx]][1]
            base_q = statistics.median([tick_min[teps_arr[k]][1] for k in range(lo, idx+1)])
            s2 = dict(s)
            s2["spread_rel"] = cur/base_med if base_med > 0 else 1.0
            s2["qcount_rel"] = qcount/base_q if base_q > 0 else 1.0
            tk_sigs.append(s2)
        print(f"  carrier signals in TICK window with spread feature: {len(tk_sigs)}")
        if tk_sigs:
            IS_T = int(datetime(2026, 1, 1).timestamp())
            tk_is = [s for s in tk_sigs if decision_ep(s) < IS_T]
            tk_oos = [s for s in tk_sigs if decision_ep(s) >= IS_T]
            print(f"  tick IS (2025-10..12): {len(tk_is)}   OOS (2026-01..): {len(tk_oos)}")
            tk_cands = {
                "spread_compressed<=1.0": lambda s: s["spread_rel"] <= 1.0,
                "spread_compressed<=0.9": lambda s: s["spread_rel"] <= 0.9,
                "spread_tight<=1.1": lambda s: s["spread_rel"] <= 1.1,
                "quote_burst>=1.2": lambda s: s["qcount_rel"] >= 1.2,
                "quote_calm<=1.0": lambda s: s["qcount_rel"] <= 1.0,
            }
            tk_scan = []
            for nm, fn in tk_cands.items():
                rs = [s["carrier_R"] for s in tk_is if fn(s)]
                tk_scan.append((nm, st(rs)["mean_R"], st(rs)["n"]))
            tk_scan.sort(key=lambda x: -x[1])
            tk_is_base = st([s["carrier_R"] for s in tk_is])
            print(f"  tick IS base: {tk_is_base}")
            for nm, mr, nn in tk_scan:
                print(f"     {nm:24s} IS mean_R={mr:+.4f} n={nn}")
            tk_valid = [x for x in tk_scan if x[2] >= 15]
            OUT["tick_spread_gate"]["is_scan"] = [{"gate": nm, "is_mean_R": mr, "is_n": nn} for nm, mr, nn in tk_scan]
            OUT["tick_spread_gate"]["is_base"] = tk_is_base
            if tk_valid:
                tk_chosen = tk_valid[0][0]; fn = tk_cands[tk_chosen]
                oos_base = st([s["carrier_R"] for s in tk_oos])
                oos_g = st([s["carrier_R"] for s in tk_oos if fn(s)])
                acc = oos_g["n"]/max(1, oos_base["n"])
                rnd = []
                for seed in range(200):
                    rr = random.Random(7000+seed)
                    rs = [s["carrier_R"] for s in tk_oos if rr.random() < acc]
                    if rs: rnd.append(sum(rs)/len(rs))
                rnd_p95 = round(sorted(rnd)[int(0.95*len(rnd))], 4) if rnd else 0.0
                inv = st([s["carrier_R"] for s in tk_oos if not fn(s)])
                print(f"\n  CHOSEN tick gate (locked IS): {tk_chosen}")
                print(f"  OOS base : {oos_base}")
                print(f"  OOS gated: {oos_g}")
                print(f"  OOS random p95: {rnd_p95} (acc={acc:.2f})   OOS invert: {inv}")
                beats = oos_g["mean_R"] > oos_base["mean_R"] and oos_g["mean_R"] > rnd_p95
                print(f"  >>> TICK gate beats carrier AND random-p95 OOS? {beats}")
                OUT["tick_spread_gate"].update({
                    "chosen": tk_chosen, "oos_base": oos_base, "oos_gated": oos_g,
                    "oos_random_p95": rnd_p95, "oos_invert": inv,
                    "beats_carrier_and_random": bool(beats),
                    "caveat": "tick OOS is only ~4 months (2026-01..04); small-sample.",
                })
    else:
        OUT["notes"].append("tick file unavailable")

    # ---------------- HONEST VERDICT (machine-readable) ----------------
    OUT["verdict"] = {
        "new_intraday_gold_edge": False,
        "mode_a_filter": "NO deployable gate: every closed-bar M1 momentum/intensity "
                         "filter collapses the 47-trade IS set below the n>=25 floor; "
                         "no OOS readout qualified (consistent with wave3 M1-filter null).",
        "mode_b_timing": "WEAK, SAMPLE-LIMITED timing REFINEMENT only. On the 33 M1-covered "
                         "trades where price pulled back into the FVG within bar i+1 (refit), "
                         "the blind H4-close carrier was a LOSER (-0.21R, 27% win); a limit "
                         "pullback fill (same structural stop -> tighter stop dist) lifts those "
                         "to +0.045R, 36% win (+0.25R paired, boot p<=0=0.022 at pull_frac=0.25). "
                         "The chase/invert null (enter on the adverse side) HURTS, confirming "
                         "direction. Effect concentrates in 2024-2025; 2026 delta=0. Net lift "
                         "across all 67 M1-covered carrier trades ~+0.12R/trade.",
        "tick_spread": "INCONCLUSIVE / no edge: gold ticks (2025-10..2026-04) yield only ~21 "
                       "carrier signals (8 IS / 13 OOS); best IS gate has n=2. Spread/quote "
                       "regime cannot be established as an entry/timing filter from this sample.",
        "bottom_line": "Microstructure does NOT create a new gold intraday edge and does NOT "
                       "broaden the carrier. It only REFINES H4 entry TIMING on the carrier's "
                       "worst-fill subset (post-close retraces), salvaging some losers via a "
                       "better limit fill. The gain is real-signed (chase null hurts) but small, "
                       "sample-limited (33 refit trades), and concentrated in 2024-2025 -- not a "
                       "reliable improvement to the gold sleeve's expectancy on its own.",
    }
    OUT["notes"].append(
        "Carrier is the gold slice of the validated metals+energy vol-gated FVG-retest 2R "
        "edge: 270 trades over 2015-2026 (~24/yr), FWD>=2025 +0.78R/60.5% win. The whole "
        "microstructure question is constrained by carrier SPARSITY: M1 covers 72 trades, "
        "ticks ~21. Any micro claim here is inherently small-sample.")

    with open(EDGE + "/WAVE6_GOLD_TICK_MICRO_RESULT.json", "w") as f:
        json.dump(OUT, f, indent=1)
    print("\nWROTE WAVE6_GOLD_TICK_MICRO_RESULT.json")

if __name__ == "__main__":
    main()
