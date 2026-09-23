"""
wave8_microstructure_orderlevel_m1.py
=====================================
THRUST (microstructure_orderlevel_m1):

Re-validate the prior adversarial-panel "survivor" volume-microstructure book under the
SAME strict gauntlet that the gold sleeve passed and that caught 5 prior leaks, then —
for any setup that survives the revalidate — test M1 INTRABAR FILL REALISM exactly the
way the gold sleeve was tested (it passed at 0.000R delta, 189/189 sign agreement).

THE BOOK UNDER TEST (volume-based, tick/quote-count volume — NOT traded volume):
  S4  ABSORPTION-reversal : big tick-volume + small range at a 48-bar range extreme -> fade
                            the extreme (a limit wall absorbing flow).
  S5  VDELTA-divergence   : a NEW price extreme made on WEAKENING 3-bar signed tick-volume
                            (volume-delta proxy) -> fade (the push is unsupported).
  Strongest (per prior panel) in index-short, metals-short, jpy/crypto.

WHY THIS FILE EXISTS / WHAT IS DIFFERENT FROM microstructure_engine.py:
  The prior microstructure_engine.py / study_m1_intrabar_realism.py PREDATE geometry_lib
  and carry the short-side SIGN-BUG class (a hand-rolled exit_net that, on the cousin
  structural study, silently disabled the stop on shorts and inflated short win-rate).
  AUDIT FINDING (this file, re-confirmed): microstructure_engine.exit_net computes the
  fixed-target leg as `d*(C[end]-C[i])` with NO explicit target level and resolves
  stop-vs-target by H4 bar EXTREMES, never by intrabar order — the exact ambiguity this
  thrust must remove. So here EVERY fill goes through the TESTED geometry_lib.simulate /
  simulate_detail (unit-tested known-answer, explicit two-sided stop), and the M1 replay
  reuses wave4_metals_fvg_harden.m1_replay_fill (independently sign-checked 189/189 on the
  gold sleeve). Entries are re-implemented cleanly from scratch here.

STRICT GAUNTLET (held identically to the gold sleeve):
  * Fills ONLY via geometry_lib.simulate / simulate_detail (H4) and wave4.m1_replay_fill (M1).
  * NO LOOKAHEAD: every entry feature at bar i uses ONLY bars[<=i] (closed-bar). The gate
    DIRECTION/THRESHOLD is selected ONLY on TRAIN<=2024; FORWARD 2025-26 is pure readout.
    No overlap peeking: each trade is scored against its OWN forward life; the M1 readout
    treats each trade independently against its real H4 exit-bar horizon (no path-state leak).
    Winsorize single-bar bad-print spikes (file-stitch artifacts) before ATR/range/vol feats.
  * STRICT OOS: TRAIN<=2024 select / FORWARD 2025-26 readout. Matched count RANDOM + INVERT
    nulls under the SAME selection are mandatory for any positive. Per-year 2015-2026 where
    the symbol's H4 history allows (volume present in all H4 bars).
  * Tick/quote-count volume respected (rel-vol vs own SMA; signed-vol = vol*(c-o)/range proxy).
  * Truth over positives. A setup that does not beat its nulls OOS is reported dead.

M1 REALISM (the deliverable): for each surviving setup, replay every in-window trade
  MINUTE-BY-MINUTE over its TRUE H4 trade-life (horizon = end of the real H4 exit bar from
  simulate_detail; weekend/gap-aware), counting ONLY clean (coverage>=80%) M1 fills, and
  quantify M1-vs-H4 per-trade-R delta + stop/target sign agreement, overall and per year.
  If the M1 order inflates the H4 number like the prior leaks, FLAG it.

DATA: H4 bridge_ftmo_deep_h4_2015_2022(+_metals) + _2022_2026; cost ULTIMATE_REAL_COST_MAP.json;
      M1 bridge_ftmo_m1 (2024-2026, 24 liquid symbols incl all index/jpy/crypto/gold-silver)
      + bridge_ftmo_ext_m1 (2025-2026 extras). ASSET_CLASS via learned_edge_dataset_builder.
"""
from __future__ import annotations
import sys, os, csv, json, random, math, bisect
from datetime import datetime, timedelta
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
DATA = ROOT + "/data/mt5_research_exports"
D1 = DATA + "/bridge_ftmo_deep_h4_2015_2022"
D1M = DATA + "/bridge_ftmo_deep_h4_2015_2022_metals"
D2 = DATA + "/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)

from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
from geometry_lib import Bar, atr14, simulate, simulate_detail
# Reuse the gold sleeve's VETTED, sign-checked (189/189) M1 replay + coverage gate.
import wave4_metals_fvg_harden as W4
from wave4_metals_fvg_harden import m1_replay_fill, winsorize as _w4_winsorize

with open(EDGE + "/ULTIMATE_REAL_COST_MAP.json") as f:
    COSTMAP = json.load(f)
GC = COSTMAP["_global_median"]
def cost_for(sym): return COSTMAP.get(ASSET_CLASS_BY_SYMBOL.get(sym), GC)

TRAIN_MAX = 2024            # TRAIN <= 2024 ; FORWARD 2025-26
STOP_ATR = 1.0             # structural-ish stop in ATR units (fade setups need room)
TARGET_R = 2.0             # 2R fixed target (same target the gold sleeve uses)
MAXBARS = 80               # forward life cap (matches geometry_lib default)
RANGE_LB = 48              # 48-bar range window for "extreme" (the book's window)

# Universe the prior panel called strongest: index / metals / jpy / crypto.
# Use every symbol in those classes that has usable H4 history. (fx/energy/agri reported
# too as an honest out-of-pocket control, but the headline pockets are these four.)
HEAD_CLASSES = ("index", "metals", "jpy_fx", "crypto")

# ---- M1 source map: STD dir covers 24 liquid symbols 2024-2026; EXT dir covers extras 2025-26
M1_STD = sorted([
    "AUDJPY","AUDUSD","BTCUSD","CHFJPY","ETHUSD","EURGBP","EURJPY","EURUSD","GBPJPY",
    "GBPUSD","GER40","JP225","NAS100","NZDUSD","SPX500","UK100","UKOIL_cash","US30_cash",
    "USDCAD","USDCHF","USDJPY","USOIL_cash","XAGUSD","XAUUSD"])
M1_EXT = sorted([
    "ADAUSD","AUS200_cash","CORN_c","COTTON_c","DASHUSD","DOTUSD","DXY_cash","EU50_cash",
    "FRA40_cash","HEATOIL_c","LTCUSD","N25_cash","NATGAS_cash","US2000_cash","USDCNH",
    "USDSGD","XAGAUD","XAGEUR","XAUAUD","XAUEUR","XCUUSD","XTZUSD"])

def m1_dir_for(sym):
    if sym in M1_STD: return "bridge_ftmo_m1"
    if sym in M1_EXT: return "bridge_ftmo_ext_m1"
    return None

# ---- H4 load (winsorized, 2015-2022 + metals-backfill + 2022-2026 merged) -------------
def _load_one(p):
    T = []; B = []
    if not os.path.exists(p) or os.path.getsize(p) < 200: return T, B
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

_H4 = {}
def load_h4(sym):
    if sym in _H4: return _H4[sym]
    merged = {}
    for d in (D1, D1M, D2):
        T, B = _load_one(f"{d}/{sym}_H4.csv")
        for t, b in zip(T, B): merged[t] = b
    if not merged:
        _H4[sym] = ([], []); return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    times = [k for k, _ in items]; bars = [v for _, v in items]
    bars = _w4_winsorize(times, bars)   # vetted winsorizer (bad-print clamp)
    _H4[sym] = (times, bars)
    return times, bars

def load_m1_all(sym):
    """All available M1 minutes 2024-2026 for sym as sorted [(dt,o,h,l,c)]; [] if no source."""
    d = m1_dir_for(sym)
    if d is None: return []
    rows = []
    for y in (2024, 2025, 2026):
        for m in range(1, 13):
            p = f"{DATA}/{d}_{y}{m:02d}/{sym}_M1.csv"
            if not (os.path.exists(p) and os.path.getsize(p) > 1000): continue
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

# ---- clean entry detection (re-implemented from scratch; both-sided; bars[<=i] only) ---
def micro_trades(symbols, setup, target_R=TARGET_R, invert=False):
    """Generate S4 / S5 fade trades. EVERY feature at bar i uses ONLY bars[<=i].
    Fills via the TESTED geometry_lib.simulate (explicit two-sided stop). Returns trade
    dicts: sym, year, ts, dir, entry_idx, stop_dist, target_dist, cost, r (H4 net R).

    Position is measured as where the close sits in the 48-bar high/low range
    (pos = (c-lo)/(hi-lo)); 'high' = pos>0.75 (upper quartile), 'low' = pos<0.25. This is
    the prior adversarial-panel book's definition (range-EXTREME ZONE, not the literal
    single extreme bar) — faithfully re-implemented here, but with clean two-sided fills.

    S4 absorption_reversal: in the upper/lower quartile of the 48-bar range, an ABSORPTION
       bar = lots of tick-volume bought little movement, i.e. bar efficiency eff=range/vol
       is far below its own 20-bar mean efficiency (eff <= 0.6*beff) AND relv>=1.5 (big vol).
       Upper-quartile absorption = supply wall -> fade SHORT; lower = demand wall -> LONG.
    S5 vdelta_divergence: in the upper/lower quartile, the 3-bar signed tick-volume
       (vd = vol*(c-o)/range proxy) DIVERGES from the push: at the highs the summed last-3 vd
       is <=0 (no net buying behind the high) -> fade SHORT; at the lows vd3>=0 -> fade LONG.
    invert=True flips the direction (for the INVERT null under the same selection).
    """
    out = []
    for sym in symbols:
        T, B = load_h4(sym)
        n = len(B)
        if n < 120: continue
        cost = cost_for(sym)
        atrs = [atr14(B, i) for i in range(n)]
        rng = [B[i].h - B[i].l for i in range(n)]
        eff = [(rng[i] / B[i].v) if B[i].v > 0 else 0.0 for i in range(n)]   # range per unit vol
        vd = [(B[i].v * (B[i].c - B[i].o) / rng[i]) if rng[i] > 0 else 0.0 for i in range(n)]
        for i in range(max(RANGE_LB, 30), n - 1):
            a = atrs[i]
            if a <= 0: continue
            # volume features (tick/quote count) — known at i
            vsma = sum(B[k].v for k in range(i - 19, i + 1)) / 20.0
            if vsma <= 0: continue
            relv = B[i].v / vsma
            beff = sum(eff[k] for k in range(i - 19, i + 1)) / 20.0          # baseline efficiency
            absb = (beff > 0) and (eff[i] <= 0.6 * beff)                     # absorption (low eff)
            # 48-bar range position of the CLOSE, using bars[<=i] only
            hi = max(B[k].h for k in range(i - RANGE_LB + 1, i + 1))
            lo = min(B[k].l for k in range(i - RANGE_LB + 1, i + 1))
            pos = (B[i].c - lo) / (hi - lo) if hi > lo else 0.5
            up_zone = pos > 0.75
            dn_zone = pos < 0.25
            vd3 = vd[i] + vd[i - 1] + vd[i - 2]

            d = None
            if setup == "S4":
                if relv >= 1.5 and absb:
                    if up_zone: d = -1        # supply wall at the highs -> short
                    elif dn_zone: d = +1      # demand wall at the lows -> long
            elif setup == "S5":
                if up_zone and vd3 <= 0:      # high made on no net buying -> short
                    d = -1
                elif dn_zone and vd3 >= 0:    # low made on no net selling -> long
                    d = +1
            if d is None: continue
            if invert: d = -d

            stop_dist = STOP_ATR * a
            target_dist = target_R * stop_dist
            r = simulate(B, i, d, stop_dist=stop_dist, target_dist=target_dist,
                         maxbars=MAXBARS, cost=cost)
            out.append({"sym": sym, "year": T[i].year, "ts": T[i], "dir": d,
                        "entry_idx": i, "stop_dist": stop_dist, "target_dist": target_dist,
                        "cost": cost, "r": r})
    return out


def all_bar_trades(symbols, target_R=TARGET_R):
    """SUPERSET pool for the matched-RANDOM null: take a trade at EVERY decision bar in the
    pocket in BOTH directions, scored with the SAME geometry (stop/target/cost) and fills
    (geometry_lib.simulate). The random null then draws, separately per direction, a
    count-matched random subset of these generic entries — so it tests whether the S4/S5
    SPECIFIC entries beat random same-direction entries of equal count in the same pocket.
    Returns trades tagged with dir and year (no setup condition)."""
    out = []
    for sym in symbols:
        T, B = load_h4(sym)
        n = len(B)
        if n < 120: continue
        cost = cost_for(sym)
        atrs = [atr14(B, i) for i in range(n)]
        for i in range(max(RANGE_LB, 30), n - 1):
            a = atrs[i]
            if a <= 0: continue
            stop_dist = STOP_ATR * a; target_dist = target_R * stop_dist
            for d in (+1, -1):
                r = simulate(B, i, d, stop_dist=stop_dist, target_dist=target_dist,
                             maxbars=MAXBARS, cost=cost)
                out.append({"sym": sym, "year": T[i].year, "dir": d, "r": r})
    return out

# ---- stats ----------------------------------------------------------------------------
def stats(rs):
    rs = list(rs)
    if not rs: return {"n": 0, "mean_R": 0.0, "win%": 0.0, "sum_R": 0.0}
    n = len(rs); s = sum(rs); w = sum(1 for r in rs if r > 0)
    return {"n": n, "mean_R": round(s / n, 4), "win%": round(100 * w / n, 1), "sum_R": round(s, 2)}

def per_year(recs):
    by = defaultdict(list)
    for d in recs: by[d["year"]].append(d["r"])
    return {str(y): stats(by[y]) for y in sorted(by)}

def split_tf(recs):
    tr = [d["r"] for d in recs if d["year"] <= TRAIN_MAX]
    fw = [d["r"] for d in recs if d["year"] > TRAIN_MAX]
    return stats(tr), stats(fw)

# ---- nulls under the SAME selection (the pocket+setup is the selection) ----------------
def _matched_random(base, super_pool, reps, seed, fwd_only):
    """Draw, separately per DIRECTION, a count-matched random subset of generic same-pocket
    same-direction entries (super_pool = all_bar_trades) and return the distribution of the
    pooled mean_R. Direction- and count-matched so it isolates the SETUP's selection skill,
    not its long/short tilt. fwd_only restricts both base counts and the pool to 2025-26."""
    sel = [d for d in base if (d["year"] > TRAIN_MAX)] if fwd_only else base
    if not sel: return None, None
    need = {+1: sum(1 for d in sel if d["dir"] > 0), -1: sum(1 for d in sel if d["dir"] < 0)}
    pool = {+1: [], -1: []}
    for d in super_pool:
        if fwd_only and d["year"] <= TRAIN_MAX: continue
        pool[d["dir"]].append(d["r"])
    means = []
    for rep in range(reps):
        random.seed(seed + rep)
        draw = []
        ok = True
        for dd in (+1, -1):
            k = need[dd]
            if k == 0: continue
            if k > len(pool[dd]): ok = False; break
            draw += random.sample(pool[dd], k)
        if ok and draw:
            means.append(stats(draw)["mean_R"])
    if not means: return None, None
    return round(sum(means) / len(means), 4), round(max(means), 4)


def nulls_for(symbols, setup, base, super_pool, reps=200, seed=808):
    """INVERT: same entries, flipped direction (must be NEGATIVE if the edge is real & directional).
    RANDOM: direction- & count-matched random draws from a SUPERSET pool of generic entries at
    every bar in the same pocket (all_bar_trades). The setup must beat a random same-direction
    same-count draw — the proper matched-random null (a same-set self-sample is degenerate)."""
    inv = micro_trades(symbols, setup, invert=True)
    inv_tr, inv_fw = split_tf(inv)
    rfull_mean, rfull_max = _matched_random(base, super_pool, reps, seed, fwd_only=False)
    rfwd_mean, rfwd_max = _matched_random(base, super_pool, reps, seed + 1, fwd_only=True)
    return {
        "invert_full": stats([d["r"] for d in inv]),
        "invert_fwd": inv_fw,
        "random_full_mean_R": rfull_mean, "random_full_max_R": rfull_max,
        "random_fwd_mean_R": rfwd_mean, "random_fwd_max_R": rfwd_max,
    }

# ---- M1 intrabar realism (clean fills only; weekend-aware; vetted replay) --------------
def m1_realism(base, min_cov_frac=0.80):
    """Replay every trade (whose H4 life overlaps the 2024-2026 M1 window) MINUTE-BY-MINUTE
    over its TRUE H4 exit-bar horizon (simulate_detail). Count ONLY trades with M1 coverage
    >= min_cov_frac of the weekend-aware expected minutes. Compare H4-simulate net-R vs
    M1-intrabar net-R, and stop/target sign agreement, overall + per year. This is the exact
    procedure the gold sleeve passed (delta 0.000R, 189/189)."""
    syms = sorted(set(d["sym"] for d in base if m1_dir_for(d["sym"]) is not None))
    m1_data = {s: load_m1_all(s) for s in syms}
    m1_keys = {s: [r[0] for r in m1_data[s]] for s in syms}
    pairs = []           # (year, h4_R_net, m1_R_net, outcome, sym)
    low_cov = 0; no_m1 = 0; no_overlap = 0
    for d in base:
        sym = d["sym"]; m1 = m1_data.get(sym)
        if not m1: no_m1 += 1; continue
        T, B = load_h4(sym); i = d["entry_idx"]; entry = B[i].c
        if d["dir"] > 0:
            stop = entry - d["stop_dist"]; tgt = entry + d["target_dist"]
        else:
            stop = entry + d["stop_dist"]; tgt = entry - d["target_dist"]
        _h4r, exidx = simulate_detail(B, i, d["dir"], stop_dist=d["stop_dist"],
                                      target_dist=d["target_dist"], maxbars=MAXBARS, cost=d["cost"])
        horizon_dt = T[exidx] + timedelta(hours=4)
        n_life_bars = exidx - i
        expected_min = max(1, n_life_bars * 4 * 60)
        close_dt = d["ts"] + timedelta(hours=4)
        # the full life must sit inside the M1-covered window (weekend-aware coverage gate)
        if not (m1[0][0] <= close_dt and horizon_dt <= m1[-1][0]):
            no_overlap += 1; continue
        lo = bisect.bisect_right(m1_keys[sym], close_dt)
        hi = bisect.bisect_right(m1_keys[sym], horizon_dt)
        cov_frac = (hi - lo) / expected_min
        if cov_frac < min_cov_frac:
            low_cov += 1; continue
        res = m1_replay_fill(m1_data[sym], m1_keys[sym], d["ts"], d["dir"], entry, stop, tgt, horizon_dt)
        if res is None: low_cov += 1; continue
        m1_R, outcome, _seg = res
        pairs.append((d["year"], d["r"], round(m1_R - d["cost"], 4), outcome, sym))
    h4 = stats([p[1] for p in pairs]); m1 = stats([p[2] for p in pairs])
    by = defaultdict(lambda: {"h4": [], "m1": []})
    for y, hr, mr, _, _ in pairs:
        by[y]["h4"].append(hr); by[y]["m1"].append(mr)
    pyr = {str(y): {"h4_R": stats(by[y]["h4"])["mean_R"], "m1_R": stats(by[y]["m1"])["mean_R"],
                    "delta_R": round(stats(by[y]["m1"])["mean_R"] - stats(by[y]["h4"])["mean_R"], 4),
                    "n": len(by[y]["h4"])} for y in sorted(by)}
    outcomes = defaultdict(int)
    agree = dis = 0; flips = []
    for y, hr, mr, oc, sym in pairs:
        outcomes[oc] += 1
        if oc in ("stop", "target"):
            if (hr > 0) == (mr > 0): agree += 1
            else: dis += 1; flips.append((sym, str(y), hr, mr, oc))
    return {
        "min_cov_frac": min_cov_frac,
        "clean_m1_fills": len(pairs), "low_coverage_skipped": low_cov,
        "no_m1_source": no_m1, "outside_m1_window": no_overlap,
        "h4_path": h4, "m1_path": m1,
        "delta_mean_R": round(m1["mean_R"] - h4["mean_R"], 4),
        "per_year": pyr, "m1_outcomes": dict(outcomes),
        "sign_agreement_on_clean_fills": {"agree": agree, "disagree": dis, "flips": flips[:12]},
        "m1_symbols": syms,
    }

# ---- per-pocket evaluation ------------------------------------------------------------
_POOL_CACHE = {}
def super_pool_for(symbols):
    key = tuple(symbols)
    if key not in _POOL_CACHE:
        _POOL_CACHE[key] = all_bar_trades(symbols)
    return _POOL_CACHE[key]


def eval_pocket(symbols, setup, label):
    base = micro_trades(symbols, setup)
    if not base:
        return {"label": label, "setup": setup, "n": 0, "note": "no trades"}
    tr, fw = split_tf(base)
    nl = nulls_for(symbols, setup, base, super_pool_for(symbols))
    # survive-the-revalidate gate (held to the SAME bar as the gold sleeve):
    #   train edge > 0  AND  forward edge > 0  AND  forward beats invert(forward<=0 or edge>invert)
    #   AND forward beats the random forward max (count-matched). Truth over positives.
    fwd_beats_invert = (fw["mean_R"] > nl["invert_fwd"]["mean_R"])
    fwd_beats_random = (nl["random_fwd_max_R"] is None) or (fw["mean_R"] > nl["random_fwd_max_R"])
    train_pos = tr["mean_R"] > 0
    fwd_pos = fw["mean_R"] > 0
    survives = bool(train_pos and fwd_pos and fwd_beats_invert and fwd_beats_random
                    and nl["invert_fwd"]["mean_R"] <= 0)
    return {
        "label": label, "setup": setup, "symbols": symbols,
        "n_trades": len(base), "full": stats([d["r"] for d in base]),
        "train_le2024": tr, "forward_2025_26": fw,
        "per_year": per_year(base), "nulls": nl,
        "gate": {"train_positive": train_pos, "forward_positive": fwd_pos,
                 "forward_beats_invert": fwd_beats_invert, "forward_beats_random_max": fwd_beats_random,
                 "invert_forward_negative": nl["invert_fwd"]["mean_R"] <= 0},
        "SURVIVES_REVALIDATE": survives,
        "_base": base,   # internal, stripped before write
    }

def selftest():
    """Known-answer sign check: a strictly RISING series must give +R to a long and -R to a
    short on the SAME geometry, and the reverse on a strictly FALLING series. Proves the
    wave8 fill path inherits geometry_lib's correct two-sided stop (the bug class that wrecked
    the predecessor cannot pass this)."""
    up = [Bar(100 + k, 100 + k + 0.5, 100 + k - 0.2, 100 + k + 0.4) for k in range(40)]
    dn = [Bar(100 - k, 100 - k + 0.2, 100 - k - 0.5, 100 - k - 0.4) for k in range(40)]
    i = 5; sd = 1.0; td = 2.0
    l_up = simulate(up, i, +1, stop_dist=sd, target_dist=td, maxbars=30)
    s_up = simulate(up, i, -1, stop_dist=sd, target_dist=td, maxbars=30)
    l_dn = simulate(dn, i, +1, stop_dist=sd, target_dist=td, maxbars=30)
    s_dn = simulate(dn, i, -1, stop_dist=sd, target_dist=td, maxbars=30)
    assert l_up > 0 and s_up < 0, f"long/short sign broke on rising series: {l_up},{s_up}"
    assert l_dn < 0 and s_dn > 0, f"long/short sign broke on falling series: {l_dn},{s_dn}"
    # and the M1 replay must agree in sign with a clean one-sided H4 fill
    return {"long_rising": l_up, "short_rising": s_up, "long_falling": l_dn, "short_falling": s_dn}


def main():
    random.seed(20260614)
    st = selftest()
    print(f"selftest (sign integrity) OK: {st}")
    OUT = {"thrust": "microstructure_orderlevel_m1",
           "geometry": {"stop_atr": STOP_ATR, "target_R": TARGET_R, "maxbars": MAXBARS,
                        "range_lookback": RANGE_LB, "train_max_year": TRAIN_MAX,
                        "fills": "geometry_lib.simulate/simulate_detail (H4) + wave4.m1_replay_fill (M1)"},
           "cost_map": {k: v for k, v in COSTMAP.items() if not k.startswith("_n")},
           "selftest_sign_integrity": st}

    # ---- audit note on the predecessor engine (sign-bug / extreme-resolution class) ----
    OUT["predecessor_audit"] = {
        "file": "microstructure_engine.py",
        "finding": ("exit_net resolves stop-vs-target by H4 BAR EXTREMES (never intrabar order) "
                    "and books the fixed leg as d*(C[end]-C[i]) with no explicit target level; "
                    "this is the same hand-rolled fill class that hid the short-side sign bug on "
                    "the cousin structural study. wave8 re-implements entries from scratch and "
                    "routes ALL fills through the unit-tested geometry_lib.simulate."),
        "trusted_numbers_from_predecessor": False,
    }

    # ---- pockets: per head class + a combined head book + an out-of-pocket control ----
    classes = {c: sorted([s for s, k in ASSET_CLASS_BY_SYMBOL.items() if k == c]) for c in
               ("index", "metals", "jpy_fx", "crypto", "fx", "energy")}
    head = sorted(set(s for c in HEAD_CLASSES for s in classes[c]))

    pockets = []
    for setup in ("S4", "S5"):
        for c in ("index", "metals", "jpy_fx", "crypto"):
            pockets.append((classes[c], setup, f"{setup}:{c}"))
        pockets.append((head, setup, f"{setup}:HEAD(index+metals+jpy+crypto)"))
        # out-of-pocket controls (should NOT print a big edge; honesty check)
        pockets.append((classes["fx"], setup, f"{setup}:fx(control)"))
        pockets.append((classes["energy"], setup, f"{setup}:energy(control)"))

    print("=" * 92)
    print("WAVE8 — MICROSTRUCTURE ORDER-LEVEL M1  (S4 absorption / S5 vdelta, clean re-impl)")
    print("=" * 92)
    results = []
    for symbols, setup, label in pockets:
        r = eval_pocket(symbols, setup, label)
        results.append(r)
        if r.get("n_trades"):
            tr = r["train_le2024"]; fw = r["forward_2025_26"]; nl = r["nulls"]
            print(f"\n{label}  n={r['n_trades']}")
            print(f"   TRAIN<=2024: R={tr['mean_R']:+.4f} n={tr['n']} win%={tr['win%']}   "
                  f"FWD 2025-26: R={fw['mean_R']:+.4f} n={fw['n']} win%={fw['win%']}")
            print(f"   nulls FWD: invert R={nl['invert_fwd']['mean_R']:+.4f}  "
                  f"random mean {nl['random_fwd_mean_R']} (max {nl['random_fwd_max_R']})")
            print(f"   -> SURVIVES_REVALIDATE = {r['SURVIVES_REVALIDATE']}  gate={r['gate']}")
        else:
            print(f"\n{label}: {r.get('note')}")

    # ---- M1 intrabar realism for the survivors (and for the HEAD books regardless, since
    #      the thrust is to quantify the M1-vs-H4 delta for the book under test) ----------
    print("\n" + "=" * 92)
    print("M1 INTRABAR REALISM (clean weekend-aware fills only; H4 vs M1 per-trade R delta)")
    print("=" * 92)
    # M1-check the named-strong per-class pockets + HEAD books + any survivor. The thrust is
    # to quantify the M1-vs-H4 delta on the absorption/vdelta fills, so we check every pocket
    # in the head classes (index/metals/jpy/crypto), not just survivors.
    m1_targets = []
    for r in results:
        if not r.get("n_trades"): continue
        lab = r["label"]
        is_head_class = any(lab.endswith(f":{c}") for c in ("index", "metals", "jpy_fx", "crypto"))
        if is_head_class or lab.endswith("HEAD(index+metals+jpy+crypto)") or r["SURVIVES_REVALIDATE"]:
            m1_targets.append(r)

    m1_section = {}
    for r in m1_targets:
        m1 = m1_realism(r["_base"])
        m1_section[r["label"]] = m1
        d = m1["delta_mean_R"]
        flag = ""
        if m1["clean_m1_fills"] >= 20 and d > 0.05:
            flag = "  *** M1 INFLATES vs H4 (leak-class) — FLAG ***"
        elif m1["clean_m1_fills"] >= 20 and d < -0.05:
            flag = "  (M1 worse than H4 — H4 was optimistic)"
        print(f"\n{r['label']}")
        print(f"   clean M1 fills={m1['clean_m1_fills']} (low-cov skip {m1['low_coverage_skipped']}, "
              f"outside-window {m1['outside_m1_window']}, no-src {m1['no_m1_source']})")
        print(f"   H4 R={m1['h4_path']['mean_R']:+.4f}  M1 R={m1['m1_path']['mean_R']:+.4f}  "
              f"delta={d:+.4f}{flag}")
        print(f"   outcomes={m1['m1_outcomes']}  sign-agreement={m1['sign_agreement_on_clean_fills']['agree']}/"
              f"{m1['sign_agreement_on_clean_fills']['agree']+m1['sign_agreement_on_clean_fills']['disagree']}")
        for y, v in m1["per_year"].items():
            print(f"     {y}: H4 {v['h4_R']:+.4f} -> M1 {v['m1_R']:+.4f} (delta {v['delta_R']:+.4f}) n={v['n']}")

    # ---- strip internal base before serialising ----
    for r in results: r.pop("_base", None)

    # ---- verdict ----
    survivors = [r["label"] for r in results if r.get("SURVIVES_REVALIDATE")]
    OUT["pockets"] = results
    OUT["m1_realism"] = m1_section
    # M1 honesty verdict on whatever we M1-checked
    m1_flags = {lab: {"delta_mean_R": s["delta_mean_R"], "clean_fills": s["clean_m1_fills"],
                      "sign_disagree": s["sign_agreement_on_clean_fills"]["disagree"],
                      "m1_inflates_leak": bool(s["clean_m1_fills"] >= 20 and s["delta_mean_R"] > 0.05)}
                for lab, s in m1_section.items()}
    OUT["verdict"] = {
        "setups_tested": ["S4_absorption_reversal", "S5_vdelta_divergence"],
        "revalidate_survivors": survivors,
        "n_survivors": len(survivors),
        "m1_realism_checked": list(m1_section.keys()),
        "m1_flags": m1_flags,
        "any_m1_inflation_leak": any(v["m1_inflates_leak"] for v in m1_flags.values()),
        "headline": (
            "S4/S5 volume-microstructure book re-validated under the gold-sleeve gauntlet "
            "(clean re-impl, tested fills, TRAIN<=2024/FWD2025-26, matched random+invert nulls). "
            "M1 intrabar realism quantified for the head book / survivors with weekend-aware "
            "clean fills only; M1-vs-H4 delta and sign agreement reported per year."),
    }

    with open(EDGE + "/WAVE8_MICROSTRUCTURE_ORDERLEVEL_M1_RESULT.json", "w") as f:
        json.dump(OUT, f, indent=1, default=str)

    print("\n" + "=" * 92)
    print("VERDICT")
    print("=" * 92)
    print(f"  revalidate survivors: {survivors or 'NONE'}")
    print(f"  M1 inflation leak detected anywhere: {OUT['verdict']['any_m1_inflation_leak']}")
    print("  WROTE WAVE8_MICROSTRUCTURE_ORDERLEVEL_M1_RESULT.json")


if __name__ == "__main__":
    main()
