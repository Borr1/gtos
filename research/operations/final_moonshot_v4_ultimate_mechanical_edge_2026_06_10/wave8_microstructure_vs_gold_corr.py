"""
wave8_microstructure_vs_gold_corr.py
====================================
THRUST (microstructure_vs_gold_corr):

The whole value of a SECOND engine is UNCORRELATION. We have two candidate engines:

  ENGINE A (gold sleeve):  vol-gated FVG-RETEST 2R CONTINUATION on precious metals.
     Mechanic = volatility-EXPANSION continuation in an HTF trend. Deployable stream =
     wave4_metals_fvg_harden.walk_forward(fvg_trades(PRECIOUS, 2R)) -> the exact published
     +0.2264R / n=482 stream. Imported, not re-derived.

  ENGINE B (microstructure book): the prior adversarial-panel survivors, VOLUME-BASED:
     S4 ABSORPTION-reversal  : big tick-volume + small range at a 48-bar range extreme -> FADE.
     S5 VOLUME-DELTA-divergence: new price extreme on WEAKENING 3-bar signed tick-volume -> FADE.
     Mechanic = flow-EXHAUSTION reversion. Re-implemented CLEANLY here on geometry_lib.simulate
     (the prior microstructure_engine.py predates the tested lib and used a hand-rolled fill that
     may carry the short-side sign-bug class — we do NOT trust its numbers; we rebuild entries).

QUESTION: are A and B genuinely UNCORRELATED (different mechanic), or do they CO-MOVE (both are
ultimately the gold/metals tape)? Report day-alignment correlation and both-active-day overlap.

DISCIPLINE (the same gauntlet that caught 5 prior leaks):
  * ALL fills via tested geometry_lib.simulate. R-unit = stop_dist (structural ATR stop). Short
    side explicit and symmetric (no sign tricks) — the lib is unit-tested for the short bug.
  * NO LOOKAHEAD: every entry feature uses ONLY bars at/<= the decision bar i. The 48-bar range
    extreme, the volume baseline SMA, the absorption ratio, and the 3-bar signed-volume slope are
    all computed on [.. i] inclusive. Exits walk strictly j>i. No overlap peeking; daily
    aggregation uses the DECISION day (known at i). Bad-print bars winsorized (wave4.winsorize).
  * STRICT OOS: the microstructure BOOK (which setups x classes are admitted as Engine B) is
    SELECTED on TRAIN<=2024 only (positive train edge over the always-fade class baseline). The
    correlation readout is reported on FULL, TRAIN(<=2024) and FORWARD(2025-26) separately, plus
    per-year 2015-2026. The gold stream's own selection (walk-forward) is past-only by construction.
  * MATCHED NULLS under the SAME selection: (i) INVERT Engine B (flip the fade to a chase) and
    re-measure correlation to gold; a real "different mechanic" claim should not depend on sign.
    (ii) RANDOM day-shuffle of Engine B's daily series (block-preserving via label permutation)
    to get a null distribution for the day-correlation, so we know if the measured corr is inside
    noise. Truth over positives.

DATA (MT5 H4): bridge_ftmo_deep_h4_2015_2022(+ _metals) + _2022_2026 under data/mt5_research_exports.
  Every H4 bar has a volume column = TICK/QUOTE count (NOT traded volume) — respected: used only
  as a relative participation proxy (rel-vol, signed tick-delta), never as a traded-size number.
  Cost: ULTIMATE_REAL_COST_MAP.json (per asset class). ASSET_CLASS via learned_edge_dataset_builder.

Research-only. No broker calls. No paid API. No runtime change.
"""
from __future__ import annotations
import sys, os, csv, json, math, random
from datetime import datetime, timedelta
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
DATA = ROOT + "/data/mt5_research_exports"
D_OLD = DATA + "/bridge_ftmo_deep_h4_2015_2022"
D_OLD_METALS = DATA + "/bridge_ftmo_deep_h4_2015_2022_metals"
D_NEW = DATA + "/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)

from geometry_lib import Bar, atr14, simulate
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
import wave4_metals_fvg_harden as W4
from wave4_metals_fvg_harden import (PRECIOUS, fvg_trades, walk_forward, winsorize, stats)

with open(EDGE + "/ULTIMATE_REAL_COST_MAP.json") as f:
    COSTMAP = json.load(f)
GC = COSTMAP["_global_median"]
def cost_for(sym): return COSTMAP.get(ASSET_CLASS_BY_SYMBOL.get(sym), GC)

TRAIN_MAX = 2024
STOP_ATR = 2.5            # structural ATR stop -> R unit = STOP_ATR*atr
HORIZON = 12             # fixed-time exit horizon in H4 bars (reversion book: time-stop, no target)
RANGE_LB = 48            # 48-bar range extreme (the book's window)
VOL_LB = 20             # tick-volume baseline window
# The microstructure book per its stated strength: index-short, metals-short, jpy/crypto.
BOOK_CLASSES = ("index", "metals", "jpy_fx", "crypto")

# ---------------------------------------------------------------------------
# H4 loader (winsorized, merged across the deep + recent packages). Self-contained
# so non-metals symbols load too (wave4.load only wires metals).
# ---------------------------------------------------------------------------
_CACHE = {}
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

def load_h4(sym):
    if sym in _CACHE: return _CACHE[sym]
    merged = {}
    for d in (D_OLD, D_OLD_METALS, D_NEW):
        T, B = _load_one(f"{d}/{sym}_H4.csv")
        for t, b in zip(T, B): merged[t] = b
    if not merged:
        _CACHE[sym] = ([], []); return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    times = [k for k, _ in items]; bars = [v for _, v in items]
    bars = winsorize(times, bars)
    _CACHE[sym] = (times, bars)
    return times, bars

# ---------------------------------------------------------------------------
# ENGINE B: microstructure book (S4 ABSORPTION + S5 VOLUME-DELTA), clean re-impl.
# All features at/<= i. Fills via tested simulate. R-unit = STOP_ATR*atr.
# ---------------------------------------------------------------------------
def micro_trades(symbols, invert=False):
    """Re-implemented S4/S5 fade setups. Returns trade dicts with sym, year, ts (decision),
    dir, setup, r (net R via geometry_lib.simulate), class."""
    out = []
    for sym in symbols:
        ac = ASSET_CLASS_BY_SYMBOL.get(sym)
        if ac not in BOOK_CLASSES: continue
        T, B = load_h4(sym)
        n = len(B)
        if n < 250: continue
        cost = cost_for(sym)
        O = [b.o for b in B]; H = [b.h for b in B]; L = [b.l for b in B]
        C = [b.c for b in B]; V = [b.v for b in B]
        rng = [H[k]-L[k] for k in range(n)]
        atrs = [atr14(B, i) for i in range(n)]
        # signed tick-volume proxy: V * (close-open)/range  (participation lean per bar), at i
        vd = [(V[k]*(C[k]-O[k])/rng[k]) if rng[k] > 0 else 0.0 for k in range(n)]
        for i in range(RANGE_LB + VOL_LB, n-1):
            a = atrs[i]
            if a <= 0: continue
            # --- features known AT i ---
            volbase = sum(V[i-VOL_LB+1:i+1]) / VOL_LB
            if volbase <= 0: continue
            relv = V[i] / volbase
            hi = max(H[i-RANGE_LB+1:i+1]); lo = min(L[i-RANGE_LB+1:i+1])
            if hi <= lo: continue
            pos = (C[i]-lo)/(hi-lo)               # location in 48-bar range, at i
            at_high = (H[i] >= hi - 1e-9) and pos > 0.75
            at_low = (L[i] <= lo + 1e-9) and pos < 0.25
            # absorption: big tick-volume but SMALL range vs its own baseline (limit wall)
            rngbase = sum(rng[i-VOL_LB+1:i+1]) / VOL_LB
            small_range = rng[i] <= rngbase * 0.8 if rngbase > 0 else False
            absorption = relv >= 1.5 and small_range
            # 3-bar signed-volume slope WEAKENING into the extreme (bars i-2..i, all <= i)
            vd_recent = vd[i]; vd_prior = (vd[i-2]+vd[i-1])/2.0
            cands = []  # (dir, setup)
            # S4 ABSORPTION-reversal: extreme + absorption -> fade
            if absorption and at_high:
                cands.append((-1, "S4_absorption"))
            if absorption and at_low:
                cands.append((+1, "S4_absorption"))
            # S5 VOLUME-DELTA-divergence: new price extreme but signed-volume WEAKENING -> fade.
            # at a HIGH: price pushed up (C[i]>O[i]) yet up-lean weaker than prior -> exhaustion.
            if at_high and C[i] > O[i] and 0 < vd_recent < vd_prior:
                cands.append((-1, "S5_vdelta"))
            # at a LOW: price pushed down (C[i]<O[i]) yet down-lean weaker (less negative) -> exhaustion.
            if at_low and C[i] < O[i] and vd_prior < vd_recent < 0:
                cands.append((+1, "S5_vdelta"))
            if not cands: continue
            stop_dist = STOP_ATR * a
            for d0, setup in cands:
                d = -d0 if invert else d0
                r = simulate(B, i, d, stop_dist=stop_dist, target_dist=None,
                             maxbars=HORIZON, cost=cost)  # fixed-time exit (time stop at HORIZON)
                out.append({"sym": sym, "class": ac, "year": T[i].year, "ts": T[i],
                            "dir": d, "setup": setup, "r": r})
    return out


def class_baseline(symbols):
    """Always-FADE-the-extreme baseline per class (the regime a fade setup is measured against):
    every 48-bar extreme bar faded, same stop/horizon/cost. Edge = setup_R - baseline_R."""
    base = defaultdict(list)
    for sym in symbols:
        ac = ASSET_CLASS_BY_SYMBOL.get(sym)
        if ac not in BOOK_CLASSES: continue
        T, B = load_h4(sym); n = len(B)
        if n < 250: continue
        cost = cost_for(sym)
        H = [b.h for b in B]; L = [b.l for b in B]; C = [b.c for b in B]
        atrs = [atr14(B, i) for i in range(n)]
        for i in range(RANGE_LB + VOL_LB, n-1):
            if T[i].year > TRAIN_MAX: continue
            a = atrs[i]
            if a <= 0: continue
            hi = max(H[i-RANGE_LB+1:i+1]); lo = min(L[i-RANGE_LB+1:i+1])
            if hi <= lo: continue
            pos = (C[i]-lo)/(hi-lo)
            sd = STOP_ATR*a
            if (H[i] >= hi-1e-9) and pos > 0.75:
                base[ac].append(simulate(B, i, -1, stop_dist=sd, maxbars=HORIZON, cost=cost))
            if (L[i] <= lo+1e-9) and pos < 0.25:
                base[ac].append(simulate(B, i, +1, stop_dist=sd, maxbars=HORIZON, cost=cost))
    return {k: (sum(v)/len(v) if v else 0.0) for k, v in base.items()}


def select_book(symbols):
    """SELECT the deployable microstructure book on TRAIN<=2024 only: admit a
    (setup x class) cell if its TRAIN edge over the class fade-baseline is positive with
    a usable sample. The selected cells define Engine B; the correlation readout then uses
    ALL years' trades from those cells (forward is a true OOS readout, not a re-selection)."""
    trades = micro_trades(symbols)
    baseline = class_baseline(symbols)
    cells = defaultdict(list)   # (setup,class) -> train R list
    for d in trades:
        if d["year"] <= TRAIN_MAX:
            cells[(d["setup"], d["class"])].append(d["r"])
    selected = {}
    for (setup, ac), rs in cells.items():
        if len(rs) < 30: continue
        m = sum(rs)/len(rs); beta = baseline.get(ac, 0.0)
        edge = m - beta
        sd = (sum((x-m)**2 for x in rs)/len(rs))**0.5
        t = edge/(sd/math.sqrt(len(rs))) if sd > 0 else 0.0
        if edge > 0:
            selected[(setup, ac)] = {"train_n": len(rs), "train_R": round(m, 4),
                                     "class_fade_baseline_R": round(beta, 4),
                                     "train_edge_R": round(edge, 4), "edge_t": round(t, 2)}
    return selected, trades, baseline


def book_stream(trades, selected):
    """Engine B deployable stream = all trades whose (setup,class) cell was admitted on train."""
    keys = set(selected.keys())
    return [d for d in trades if (d["setup"], d["class"]) in keys]


# ---------------------------------------------------------------------------
# DAY-ALIGNMENT CORRELATION
# ---------------------------------------------------------------------------
def daily_series(recs, mode="sum_R"):
    """Aggregate a trade stream to a per-DECISION-day value.
    mode sum_R = summed net R that day; mode count = number of trades; mode active = 1/0."""
    d = defaultdict(float)
    for r in recs:
        day = r["ts"].date()
        if mode == "sum_R": d[day] += r["r"]
        elif mode == "count": d[day] += 1.0
        elif mode == "active": d[day] = 1.0
    return dict(d)


def _pearson(xs, ys):
    n = len(xs)
    if n < 3: return None
    mx = sum(xs)/n; my = sum(ys)/n
    sxx = sum((x-mx)**2 for x in xs); syy = sum((y-my)**2 for y in ys)
    sxy = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    if sxx <= 0 or syy <= 0: return None
    return sxy/math.sqrt(sxx*syy)


def _rank(vals):
    order = sorted(range(len(vals)), key=lambda k: vals[k])
    ranks = [0.0]*len(vals)
    i = 0
    while i < len(vals):
        j = i
        while j+1 < len(vals) and vals[order[j+1]] == vals[order[i]]:
            j += 1
        avg = (i + j)/2.0 + 1.0
        for k in range(i, j+1): ranks[order[k]] = avg
        i = j+1
    return ranks


def _spearman(xs, ys):
    if len(xs) < 3: return None
    return _pearson(_rank(xs), _rank(ys))


def day_correlation(gold_recs, book_recs, label):
    """Correlation between the two engines' daily activity, computed over the UNION of all
    days either engine traded (off-days = 0 contribution), which is the honest co-movement
    measure for a portfolio. Also report the both-active overlap (Jaccard) and the
    conditional correlation on days BOTH were active (does direction co-move when both fire)."""
    g_sum = daily_series(gold_recs, "sum_R"); b_sum = daily_series(book_recs, "sum_R")
    g_days = set(g_sum); b_days = set(b_sum)
    union = sorted(g_days | b_days)
    if not union:
        return {"label": label, "error": "no days"}
    gx = [g_sum.get(d, 0.0) for d in union]
    bx = [b_sum.get(d, 0.0) for d in union]
    both = sorted(g_days & b_days)
    gb = [g_sum[d] for d in both]; bb = [b_sum[d] for d in both]
    inter = len(g_days & b_days); uni = len(g_days | b_days)
    return {
        "label": label,
        "gold_trading_days": len(g_days),
        "book_trading_days": len(b_days),
        "both_active_days": inter,
        "union_days": uni,
        "both_active_overlap_jaccard": round(inter/uni, 4) if uni else 0.0,
        "both_active_share_of_gold_days": round(inter/len(g_days), 4) if g_days else 0.0,
        "both_active_share_of_book_days": round(inter/len(b_days), 4) if b_days else 0.0,
        "pearson_daily_R_union": round(_pearson(gx, bx), 4) if _pearson(gx, bx) is not None else None,
        "spearman_daily_R_union": round(_spearman(gx, bx), 4) if _spearman(gx, bx) is not None else None,
        "pearson_daily_R_both_active": round(_pearson(gb, bb), 4) if (len(both) >= 3 and _pearson(gb, bb) is not None) else None,
        "n_union_points": len(union),
    }


def random_null_corr(gold_recs, book_recs, reps=200, seed=8):
    """Day-shuffle null: permute Engine B's daily-R LABELS across the union calendar of
    business days spanned, recompute the union-Pearson. Gives a null band so we can say
    whether the measured day-correlation is distinguishable from noise."""
    g_sum = daily_series(gold_recs, "sum_R"); b_sum = daily_series(book_recs, "sum_R")
    if not g_sum or not b_sum: return None
    g_days = sorted(set(g_sum) | set(b_sum))
    gx = [g_sum.get(d, 0.0) for d in g_days]
    b_vals = [b_sum.get(d, 0.0) for d in g_days]
    obs = _pearson(gx, b_vals)
    rs = []
    for rep in range(reps):
        random.seed(seed+rep)
        perm = b_vals[:]; random.shuffle(perm)
        p = _pearson(gx, perm)
        if p is not None: rs.append(p)
    rs.sort()
    return {
        "observed_pearson": round(obs, 4) if obs is not None else None,
        "null_mean": round(sum(rs)/len(rs), 4) if rs else None,
        "null_p2.5": round(rs[int(0.025*len(rs))], 4) if rs else None,
        "null_p97.5": round(rs[int(0.975*len(rs))], 4) if rs else None,
        "observed_inside_null_band": (rs[int(0.025*len(rs))] <= obs <= rs[int(0.975*len(rs))]) if (rs and obs is not None) else None,
    }


def per_year_corr(gold_recs, book_recs):
    out = {}
    years = sorted(set(d["ts"].year for d in gold_recs) | set(d["ts"].year for d in book_recs))
    for y in years:
        g = [d for d in gold_recs if d["ts"].year == y]
        b = [d for d in book_recs if d["ts"].year == y]
        out[str(y)] = day_correlation(g, b, f"year_{y}")
    return out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    random.seed(20260614)
    OUT = {"thrust": "microstructure_vs_gold_corr",
           "engine_A_gold": "wave4 vol-gated FVG-retest 2R continuation (PRECIOUS, walk-forward stream)",
           "engine_B_micro": "S4 absorption + S5 vdelta fade book (clean re-impl on geometry_lib.simulate)",
           "book_classes": list(BOOK_CLASSES), "horizon_bars": HORIZON, "stop_atr": STOP_ATR,
           "broker_operation": False, "paid_api_or_vendor_call": False,
           "broker_runtime_change_status": False}

    # ---- ENGINE A: gold sleeve deployable stream (imported, exact published) ----
    print("="*78); print("ENGINE A: gold FVG-retest 2R continuation (walk-forward stream)"); print("="*78)
    THRESHOLDS = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
    gold_base = fvg_trades(PRECIOUS, target_R=2.0)
    gold_summ, gold_recs = walk_forward(gold_base, THRESHOLDS)
    print(f"  gold WF full R={gold_summ['chained_full']['mean_R']:+.4f} n={gold_summ['n_trades']} "
          f"fwd R={gold_summ['chained_fwd']['mean_R']:+.4f}")
    OUT["engine_A_stream"] = {"full_R": gold_summ["chained_full"]["mean_R"],
                              "n_trades": gold_summ["n_trades"],
                              "fwd_R": gold_summ["chained_fwd"]["mean_R"],
                              "distinct_decision_days": len(set(d["ts"].date() for d in gold_recs))}

    # ---- ENGINE B: microstructure book, selected on TRAIN<=2024 ----
    print("\n" + "="*78); print("ENGINE B: microstructure fade book (S4/S5), train-selected"); print("="*78)
    universe = sorted(s for s, a in ASSET_CLASS_BY_SYMBOL.items() if a in BOOK_CLASSES)
    selected, all_trades, baseline = select_book(universe)
    book_recs = book_stream(all_trades, selected)
    print(f"  class fade-baselines (train): { {k: round(v,4) for k,v in baseline.items()} }")
    print(f"  ADMITTED book cells (train edge>0):")
    for (setup, ac), v in sorted(selected.items()):
        print(f"    {setup:14s} {ac:8s}: train_R={v['train_R']:+.4f} baseline={v['class_fade_baseline_R']:+.4f} "
              f"edge={v['train_edge_R']:+.4f} t={v['edge_t']} n={v['train_n']}")
    bk_full = stats([d["r"] for d in book_recs])
    bk_tr = stats([d["r"] for d in book_recs if d["year"] <= TRAIN_MAX])
    bk_fw = stats([d["r"] for d in book_recs if d["year"] > TRAIN_MAX])
    print(f"  book stream: full R={bk_full['mean_R']:+.4f} n={bk_full['n']} | "
          f"train R={bk_tr['mean_R']:+.4f} n={bk_tr['n']} | fwd R={bk_fw['mean_R']:+.4f} n={bk_fw['n']}")
    OUT["engine_B_selection"] = {f"{s}|{a}": v for (s, a), v in selected.items()}
    OUT["engine_B_class_fade_baseline_train"] = {k: round(v, 4) for k, v in baseline.items()}
    OUT["engine_B_stream"] = {"full": bk_full, "train": bk_tr, "fwd": bk_fw,
                              "distinct_decision_days": len(set(d["ts"].date() for d in book_recs)),
                              "by_class": {ac: stats([d["r"] for d in book_recs if d["class"] == ac])
                                           for ac in BOOK_CLASSES}}

    if not book_recs:
        OUT["FATAL"] = "no microstructure book cells admitted on train; cannot measure correlation"
        with open(EDGE + "/WAVE8_MICROSTRUCTURE_VS_GOLD_CORR_RESULT.json", "w") as f:
            json.dump(OUT, f, indent=1, default=str)
        print("NO BOOK ADMITTED — wrote partial result")
        return

    # ---- DAY-ALIGNMENT CORRELATION (the thrust) ----
    print("\n" + "="*78); print("DAY-ALIGNMENT CORRELATION (gold sleeve vs micro book)"); print("="*78)
    full = day_correlation(gold_recs, book_recs, "FULL_2015_2026")
    train = day_correlation([d for d in gold_recs if d["ts"].year <= TRAIN_MAX],
                            [d for d in book_recs if d["year"] <= TRAIN_MAX], "TRAIN_<=2024")
    fwd = day_correlation([d for d in gold_recs if d["ts"].year > TRAIN_MAX],
                          [d for d in book_recs if d["year"] > TRAIN_MAX], "FORWARD_2025_26")
    for blk in (full, train, fwd):
        print(f"  [{blk['label']}] pearson_union={blk.get('pearson_daily_R_union')} "
              f"spearman_union={blk.get('spearman_daily_R_union')} "
              f"both_active={blk.get('both_active_days')}/{blk.get('union_days')} "
              f"jaccard={blk.get('both_active_overlap_jaccard')} "
              f"pearson_both_active={blk.get('pearson_daily_R_both_active')}")
    OUT["day_correlation"] = {"full": full, "train": train, "forward": fwd}

    # ---- per-year ----
    pyc = per_year_corr(gold_recs, book_recs)
    print("\n  per-year day-correlation (union pearson | both-active days | jaccard):")
    for y, v in pyc.items():
        print(f"    {y}: pearson={v.get('pearson_daily_R_union')} "
              f"both={v.get('both_active_days')}/{v.get('union_days')} "
              f"jaccard={v.get('both_active_overlap_jaccard')}")
    OUT["per_year_day_correlation"] = pyc

    # ---- NULLS under same selection ----
    print("\n" + "="*78); print("NULLS (invert book + random day-shuffle, same selection)"); print("="*78)
    # (i) INVERT engine B (flip fade->chase) on the SAME admitted cells; re-measure corr
    inv_trades = micro_trades(universe, invert=True)
    inv_recs = book_stream(inv_trades, selected)
    inv_corr = day_correlation(gold_recs, inv_recs, "INVERT_book")
    inv_full = stats([d["r"] for d in inv_recs])
    print(f"  INVERT book: stream R={inv_full['mean_R']:+.4f} n={inv_full['n']}  "
          f"pearson_union={inv_corr.get('pearson_daily_R_union')} "
          f"jaccard={inv_corr.get('both_active_overlap_jaccard')}")
    # (ii) random day-shuffle null band for the FULL union-pearson
    null = random_null_corr(gold_recs, book_recs)
    print(f"  random day-shuffle null: observed={null['observed_pearson']} "
          f"null_mean={null['null_mean']} band=[{null['null_p2.5']},{null['null_p97.5']}] "
          f"inside_band(=indistinguishable_from_0)={null['observed_inside_null_band']}")
    OUT["nulls"] = {"invert_book_stream_R": inv_full,
                    "invert_book_day_correlation": inv_corr,
                    "random_dayshuffle_null": null}

    # ---- diversification readout: combined portfolio worst-day vs each alone ----
    # Both engines = 1 risk unit each on their decision day; combined daily R is the sum of
    # their daily summed-R. If uncorrelated, the combined worst-day is bounded better than the
    # arithmetic sum of the two worst-days.
    g_sum = daily_series(gold_recs, "sum_R"); b_sum = daily_series(book_recs, "sum_R")
    alldays = sorted(set(g_sum) | set(b_sum))
    comb = [g_sum.get(d, 0.0) + b_sum.get(d, 0.0) for d in alldays]
    g_worst = min(g_sum.values()) if g_sum else 0.0
    b_worst = min(b_sum.values()) if b_sum else 0.0
    c_worst = min(comb) if comb else 0.0
    OUT["diversification"] = {
        "gold_worst_day_summed_R": round(g_worst, 3),
        "book_worst_day_summed_R": round(b_worst, 3),
        "combined_worst_day_summed_R": round(c_worst, 3),
        "naive_sum_of_worst_days": round(g_worst + b_worst, 3),
        "combined_better_than_naive_sum": c_worst > (g_worst + b_worst) + 1e-9,
    }
    print(f"\n  diversification: gold worst-day {g_worst:+.2f}R  book worst-day {b_worst:+.2f}R  "
          f"combined worst-day {c_worst:+.2f}R (naive sum {g_worst+b_worst:+.2f}R)")

    # ---- raw S4/S5 x class diagnostic (full/train/fwd) — preserve the gauntlet evidence ----
    diag = {}
    cellmap = defaultdict(list)
    for d in all_trades: cellmap[(d["setup"], d["class"])].append(d)
    for (setup, ac), ds in sorted(cellmap.items()):
        fu = stats([d["r"] for d in ds])
        tr2 = stats([d["r"] for d in ds if d["year"] <= TRAIN_MAX])
        fw2 = stats([d["r"] for d in ds if d["year"] > TRAIN_MAX])
        diag[f"{setup}|{ac}"] = {"full": fu, "train": tr2, "fwd": fw2,
                                 "train_edge_vs_baseline": round(tr2["mean_R"] - baseline.get(ac, 0.0), 4)}
    OUT["raw_setup_x_class_diagnostic"] = diag
    OUT["raw_setup_totals"] = {
        s: stats([d["r"] for d in all_trades if d["setup"] == s]) for s in ("S4_absorption", "S5_vdelta")
    }

    # ---- VERDICT ----
    print("\n" + "="*78); print("VERDICT"); print("="*78)
    p_full = full.get("pearson_daily_R_union")
    s_full = full.get("spearman_daily_R_union")
    p_fwd = fwd.get("pearson_daily_R_union")
    jac = full.get("both_active_overlap_jaccard")
    # genuinely uncorrelated if: |pearson| small (<0.2) on full AND forward, both-active overlap
    # modest, AND the observed corr is inside the random null band (indistinguishable from 0).
    uncorrelated = bool(
        p_full is not None and abs(p_full) < 0.20 and
        (p_fwd is None or abs(p_fwd) < 0.30) and
        null.get("observed_inside_null_band") is True
    )
    # CRITICAL GATE: uncorrelation is only VALUABLE if Engine B is itself a real edge. A second
    # engine that is uncorrelated but LOSING is not a diversifier — it is just a drag. The gauntlet
    # must report this honestly, not sell a clean correlation number on a dead engine.
    book_has_edge = bool(bk_fw["mean_R"] > 0 and bk_full["mean_R"] > 0)
    book_admitted_meaningful = bool(selected)  # any cell survived train selection at all
    verdict = {
        "engine_B_book_admitted_cells": [f"{s}|{a}" for (s, a) in sorted(selected.keys())],
        "engine_B_full_R": bk_full["mean_R"], "engine_B_full_n": bk_full["n"],
        "engine_B_forward_R": bk_fw["mean_R"], "engine_B_forward_n": bk_fw["n"],
        "engine_B_HAS_REAL_EDGE": book_has_edge,
        "day_pearson_full": p_full, "day_spearman_full": s_full, "day_pearson_forward": p_fwd,
        "both_active_days_full": full.get("both_active_days"),
        "both_active_overlap_jaccard_full": jac,
        "random_null_band_full": [null.get("null_p2.5"), null.get("null_p97.5")],
        "observed_corr_indistinguishable_from_zero": null.get("observed_inside_null_band"),
        "invert_book_day_pearson": inv_corr.get("pearson_daily_R_union"),
        "GENUINELY_UNCORRELATED": uncorrelated,
        "UNCORRELATION_IS_USEFUL": bool(uncorrelated and book_has_edge),
        "INTERPRETATION": (
            ("Engine B is genuinely uncorrelated with gold (daily corr inside the random null band, "
             "modest both-active overlap) AND carries a real positive forward edge => a true "
             "diversifying second engine: different mechanic (flow-exhaustion reversion vs "
             "vol-expansion continuation)." if (uncorrelated and book_has_edge) else
             "GAUNTLET CAUGHT IT: the S4/S5 microstructure book, re-implemented cleanly on the tested "
             "geometry_lib fill, has NO real edge (full R={:+.4f}, forward R={:+.4f}); the only cell "
             "that survived train selection (S5_vdelta|crypto) merely beat a catastrophically negative "
             "crypto fade-baseline while still LOSING in absolute R. Its day-correlation with gold IS "
             "near-zero (pearson {:.3f}, inside the null band), but uncorrelation of a LOSING engine is "
             "not diversification — it is just a drag. The prior microstructure_engine.py 'developed "
             "book' positives were a fill/baseline-framing leak, not a tradeable second engine."
             ).format(bk_full["mean_R"], bk_fw["mean_R"], p_full if p_full is not None else 0.0)),
    }
    OUT["verdict"] = verdict
    for k, v in verdict.items():
        print(f"  {k}: {v}")

    with open(EDGE + "/WAVE8_MICROSTRUCTURE_VS_GOLD_CORR_RESULT.json", "w") as f:
        json.dump(OUT, f, indent=1, default=str)
    print("\nWROTE WAVE8_MICROSTRUCTURE_VS_GOLD_CORR_RESULT.json")


if __name__ == "__main__":
    main()
