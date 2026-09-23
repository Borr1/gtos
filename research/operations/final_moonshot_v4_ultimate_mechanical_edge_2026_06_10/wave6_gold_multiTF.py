"""
wave6_gold_multiTF.py
=====================
THRUST (gold_multiTF): The ONE proven edge is the gold vol-gated FVG-retest 2R
CONTINUATION carrier on H4 (wave4_metals_fvg_harden: XAUUSD-only WF full R=+0.3224,
n=275 over 11yr, ~0.22%/mo FTMO-safe, XAUUSD = 81% of the precious sleeve's edge).

Question the owner asked:
  Does running the SAME carrier on a FINER timeframe (M15 / H1) give MORE gold trades
  at comparable/better walk-forward edge (=> higher monthly% at same DD), or does a
  COARSER timeframe (D1) give a CLEANER edge? Recommend the best gold TF(s) to maximize
  FTMO-safe monthly%.

WHAT IS HELD CONSTANT (so the comparison is the TIMEFRAME, nothing else):
  * Entry geometry: FVG-retest CONTINUATION in an HTF trend, EXACT logic ported from
    wave4_metals_fvg_harden.fvg_trades / wave1.setup_ob_fvg_retest. Structural stop,
    2R fixed target. (No hand-rolled fills — all R via geometry_lib.simulate /
    simulate_detail.)
  * Vol gate: ATR(14) >= thr * SMA100(ATR), known at the decision bar (sma_atr_ratio).
    Walk-forward re-selects thr on PAST-ONLY in-regime trades, chained per year.
  * Stop buffer / fvg_min / atr_stop_floor in ATR units (so they auto-scale across TFs).
  * Winsorization of single-bar bad-print spikes (identical clamp logic).
  * Real per-asset cost from ULTIMATE_REAL_COST_MAP.json (metals = 0.0459 R).
  * Nulls: invert + count-matched random under the SAME walk-forward selection rule.
  * Strict OOS: TRAIN<=2024, FORWARD 2025-26 readout, AND chained walk-forward.
  * Per-year, per-TF.

WHAT SCALES WITH THE TIMEFRAME (everything in the SAME wall-clock terms, not bar terms,
so each TF "sees" the same trend horizon and trade life — otherwise a finer TF would be
unfairly handicapped/advantaged):
  * trend_lb (HTF-trend lookback): H4 uses 30 bars = 120h ~= 5 trading days. We keep the
    SAME ~5-trading-day wall-clock horizon on each TF:
        D1: 5 bars, H4: 30, H1: 120, M15: 480.
  * maxbars (trade horizon for simulate): H4 default 80 bars = ~13 trading days. Keep the
    same wall-clock life on each TF:
        D1: ~13 bars, H4: 80, H1: ~320, M15: ~1280. (capped to keep runtime sane on M15.)
  These are the ONLY TF-dependent knobs; everything else is ATR-relative or count-based.

DATA (exported full-history 2015-2026 for this wave; gold only):
  H4:  data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022 + _2022_2026   (carrier, the baseline)
  D1:  data/mt5_research_exports/gold_multitf_d1h1_2015_2026/XAUUSD_D1.csv    (2952 bars)
  H1:  data/mt5_research_exports/gold_multitf_d1h1_2015_2026/XAUUSD_H1.csv    (67411 bars)
  M15: data/mt5_research_exports/gold_multitf_m15_2015_2026/XAUUSD_M15.csv    (269442 bars)

ANTI-LEAK DISCIPLINE:
  * Gate feature at decision bar i uses ONLY atrs[<=i]. Trend uses bars[<=i].
  * Walk-forward threshold for year Y selected ONLY on trades strictly before Y.
  * NO M1 weekend-horizon leak here: the simulate horizon is in TF bars (the TF's own
    series already excludes weekends as missing bars), and we additionally REJECT trades
    whose life crosses a wall-clock gap far larger than the TF delta * maxbars (a stitch),
    so a finer TF cannot fabricate a favorable exit by skipping a weekend.
  * Random + invert nulls under the SAME walk-forward selection for every positive.
  * Per-year readout; honest verdict vs the H4 carrier.
"""
from __future__ import annotations
import sys, os, csv, json, random, math
from datetime import datetime, timedelta
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
DATA = ROOT + "/data/mt5_research_exports"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)
from geometry_lib import Bar, atr14, simulate, simulate_detail

with open(EDGE + "/ULTIMATE_REAL_COST_MAP.json") as f:
    COSTMAP = json.load(f)
COST_METALS = COSTMAP["metals"]    # 0.0459 R per trade, real gold cost
TRAIN_MAX = 2024

# ---------------------------------------------------------------------------
# TF registry: file path(s), bar wall-clock delta (hours), and the wall-clock-
# matched trend_lb / maxbars (anchored to H4's 30 / 80).
# ---------------------------------------------------------------------------
H4_DEEP1 = DATA + "/bridge_ftmo_deep_h4_2015_2022/XAUUSD_H4.csv"
H4_DEEP2 = DATA + "/bridge_ftmo_deep_h4_2022_2026/XAUUSD_H4.csv"

TF_SPECS = {
    # name: (list of csv paths, hours_per_bar, trend_lb, maxbars)
    "D1":  ([DATA + "/gold_multitf_d1h1_2015_2026/XAUUSD_D1.csv"],       24.0,  5,   14),
    "H4":  ([H4_DEEP1, H4_DEEP2],                                         4.0,  30,   80),
    "H1":  ([DATA + "/gold_multitf_d1h1_2015_2026/XAUUSD_H1.csv"],        1.0, 120,  320),
    "M15": ([DATA + "/gold_multitf_m15_2015_2026/XAUUSD_M15.csv"],        0.25,480, 1280),
}

# ---------------------------------------------------------------------------
# data load + winsorize (identical clamp logic to wave4)
# ---------------------------------------------------------------------------
def _load_csv(p):
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

_CACHE = {}
def load_tf(name, do_winsor=True):
    key = (name, do_winsor)
    if key in _CACHE: return _CACHE[key]
    paths, _hpb, _tl, _mb = TF_SPECS[name]
    merged = {}
    for p in paths:
        T, B = _load_csv(p)
        for t, b in zip(T, B): merged[t] = b   # later file wins on overlap
    if not merged:
        _CACHE[key] = ([], []); return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    times = [k for k, _ in items]; bars = [v for _, v in items]
    if do_winsor: bars = winsorize(times, bars)
    _CACHE[key] = (times, bars)
    return times, bars

# ---------------------------------------------------------------------------
# known-at-i features (identical formulas to wave4)
# ---------------------------------------------------------------------------
def htf_trend(bars, i, lb):
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

# ---------------------------------------------------------------------------
# FVG-retest trade generation — geometry/sign IDENTICAL to wave4.fvg_trades.
# The ONLY TF differences are trend_lb, maxbars (wall-clock matched), and a
# stitch-gap guard so a finer TF cannot fabricate a favorable weekend-skip exit.
# ---------------------------------------------------------------------------
def fvg_trades(name, *, target_R=2.0, fvg_min=0.10, stop_buf=0.10, atr_stop_floor=0.25,
               invert=False, atr_win=100, do_winsor=True):
    paths, hpb, trend_lb, maxbars = TF_SPECS[name]
    T, B = load_tf(name, do_winsor=do_winsor)
    if len(B) < 200: return []
    n = len(B)
    atrs = [atr14(B, i) for i in range(n)]
    # stitch guard: max wall-clock a legitimate maxbars-life can span on this TF.
    # Allow generous weekend slack (x4) so normal weekends/holidays are NOT rejected,
    # but a multi-month stitch gap inside a trade's life IS.
    max_life_hours = hpb * maxbars * 4.0
    out = []
    lo_i = max(60, trend_lb + 2)
    for i in range(lo_i, n-1):
        a = atrs[i]
        if a <= 0: continue
        tr = htf_trend(B, i, trend_lb)
        b = B[i]
        d = None; stop_dist = None
        if tr == 1:
            for k in range(i-2, max(i-9, lo_i), -1):
                gap_top = B[k].l; gap_bot = B[k-2].h
                if gap_top - gap_bot < fvg_min*a: continue
                if b.l <= gap_top and b.c > gap_bot and b.c > b.o:
                    stop_dist = max((b.c - min(b.l, gap_bot)) + stop_buf*a, atr_stop_floor*a)
                    d = -1 if invert else +1
                    break
        elif tr == -1:
            for k in range(i-2, max(i-9, lo_i), -1):
                gap_bot = B[k].h; gap_top = B[k-2].l
                if gap_top - gap_bot < fvg_min*a: continue
                if b.h >= gap_bot and b.c < gap_top and b.c < b.o:
                    stop_dist = max((max(b.h, gap_top) - b.c) + stop_buf*a, atr_stop_floor*a)
                    d = +1 if invert else -1
                    break
        if d is None: continue
        target_dist = target_R*stop_dist
        # exit index for stitch guard + horizon-leak protection
        r, exidx = simulate_detail(B, i, d, stop_dist=stop_dist, target_dist=target_dist,
                                   cost=COST_METALS, maxbars=maxbars)
        life_hours = (T[exidx] - T[i]).total_seconds() / 3600.0
        if life_hours > max_life_hours:
            continue   # stitch / huge gap inside the trade life -> reject (anti-leak)
        ratio = sma_atr_ratio(atrs, i, atr_win)
        out.append({
            "sym": "XAUUSD", "tf": name, "year": T[i].year, "ts": T[i], "dir": d,
            "entry_idx": i, "stop_dist": stop_dist, "target_dist": target_dist,
            "atr_ratio": ratio, "r": r, "cost": COST_METALS, "target_R": target_R,
            "exidx": exidx,
        })
    return out

# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# walk-forward: rolling past-only threshold re-selection (identical rule to wave4)
# ---------------------------------------------------------------------------
def walk_forward(base, thresholds, anchor_year=2016, end_year=2026, min_past_n=60):
    by_year_trades = defaultdict(list)
    for d in base: by_year_trades[d["year"]].append(d)
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
        taken = [d for d in by_year_trades.get(Y, [])
                 if d["atr_ratio"] is not None and d["atr_ratio"] >= best_thr]
        picks[str(Y)] = {
            "threshold": best_thr, "note": note, "past_n": best_n,
            "past_R_at_pick": round(best_R, 4) if best_R > -1e8 else None,
            "year_n": len(taken), "year_R": stats([d["r"] for d in taken])["mean_R"],
            "year_sum_R": stats([d["r"] for d in taken])["sum_R"],
        }
        for d in taken: chained.append((Y, d["r"], d))
    full = stats([r for _, r, _ in chained])
    fwd = stats([r for y, r, _ in chained if y > TRAIN_MAX])
    py = {int(y): stats([r for yy, r, _ in chained if yy == y])
          for y in sorted(set(y for y, _, _ in chained))}
    wf_recs = [{"ts": d["ts"], "r": r, "year": y, "sym": d["sym"], "tf": d["tf"]}
               for (y, r, d) in chained]
    return {
        "picks": picks, "chained_full": full, "chained_fwd": fwd,
        "chained_per_year": {str(y): py[y] for y in py},
        "n_trades": len(chained),
    }, wf_recs

# ---------------------------------------------------------------------------
# nulls under the SAME walk-forward selection rule
# ---------------------------------------------------------------------------
def nulls(name, base, wf_recs, thresholds, seed=4242, reps=50):
    # invert under WF rule
    inv = fvg_trades(name, invert=True)
    wf_inv, _ = walk_forward(inv, thresholds)
    # random count-matched: same number of WF-taken trades drawn from full base pool
    kk = len(wf_recs); rr_full = []; rr_fwd = []
    for rep in range(reps):
        random.seed(seed + rep)
        samp = random.sample(base, kk) if 0 < kk <= len(base) else base
        rr_full.append(stats([d["r"] for d in samp])["mean_R"])
        fw = [d["r"] for d in samp if d["year"] > TRAIN_MAX]
        rr_fwd.append(stats(fw)["mean_R"] if fw else 0.0)
    return {
        "wf_invert_full_R": wf_inv["chained_full"]["mean_R"],
        "wf_invert_fwd_R": wf_inv["chained_fwd"]["mean_R"],
        "wf_invert_n": wf_inv["n_trades"],
        "random_full_mean_R": round(sum(rr_full)/len(rr_full), 4) if rr_full else 0.0,
        "random_full_max_R": round(max(rr_full), 4) if rr_full else 0.0,
        "random_fwd_mean_R": round(sum(rr_fwd)/len(rr_fwd), 4) if rr_fwd else 0.0,
    }

# ---------------------------------------------------------------------------
# FTMO sizing on the chronological WF trade stream (identical to wave4)
# ---------------------------------------------------------------------------
def ftmo_sizing(recs_for_path, risk_grid=None):
    if risk_grid is None:
        risk_grid = [0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1.0, 1.5, 2.0]
    recs = sorted(recs_for_path, key=lambda d: d["ts"])
    if not recs: return {"error": "no trades"}
    span_days = (recs[-1]["ts"] - recs[0]["ts"]).days or 1
    span_months = span_days / 30.44
    results = {}; best_ok = None
    for risk in risk_grid:
        eq = 1.0; peak = 1.0; maxdd = 0.0
        day_pl = defaultdict(float)
        for d in recs:
            before = eq
            eq *= (1.0 + (risk/100.0) * d["r"])
            day_pl[d["ts"].date()] += (eq - before)
            peak = max(peak, eq)
            maxdd = max(maxdd, (peak - eq)/peak)
        worst_day = min(day_pl.values()) if day_pl else 0.0
        worst_day_pct = -worst_day * 100.0
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
        if ok: best_ok = results[str(risk)]
    return {"span_days": span_days, "span_months": round(span_months, 1),
            "n_trades": len(recs), "grid": results, "max_risk_within_ftmo": best_ok}

# ---------------------------------------------------------------------------
# per-TF full evaluation
# ---------------------------------------------------------------------------
THRESHOLDS = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]

def eval_tf(name):
    paths, hpb, trend_lb, maxbars = TF_SPECS[name]
    T, B = load_tf(name)
    print("\n" + "#"*78)
    print(f"# TF = {name}  (hpb={hpb}h, trend_lb={trend_lb}, maxbars={maxbars}, bars={len(B)})")
    if T: print(f"#   coverage {T[0].date()} -> {T[-1].date()}")
    print("#"*78)
    res = {"tf": name, "hours_per_bar": hpb, "trend_lb": trend_lb, "maxbars": maxbars,
           "n_bars": len(B),
           "coverage": {"first": str(T[0].date()) if T else None,
                        "last": str(T[-1].date()) if T else None,
                        "years": sorted(set(t.year for t in T))} if T else {}}
    base = fvg_trades(name, target_R=2.0)
    res["n_signals_all_regime"] = len(base)
    sa = stats([d["r"] for d in base])
    tr, fw = split(base)
    res["all_regime"] = {"full": sa, "train": tr, "fwd": fw,
                         "per_year": {str(k): v for k, v in per_year(base).items()}}
    print(f"  all-regime: full {sa['mean_R']:+.4f} n={sa['n']} sum={sa['sum_R']}  "
          f"train {tr['mean_R']:+.4f}(n{tr['n']}) fwd {fw['mean_R']:+.4f}(n{fw['n']})")

    wf, wf_recs = walk_forward(base, THRESHOLDS)
    res["walk_forward"] = {
        "chained_full": wf["chained_full"], "chained_fwd": wf["chained_fwd"],
        "chained_per_year": wf["chained_per_year"], "n_trades": wf["n_trades"],
        "picks": wf["picks"],
    }
    cf = wf["chained_full"]; cw = wf["chained_fwd"]
    n_years = len(wf["chained_per_year"]) or 1
    trades_per_year = round(wf["n_trades"]/n_years, 1)
    pos_years = sum(1 for v in wf["chained_per_year"].values() if v["mean_R"] > 0)
    res["walk_forward"]["trades_per_year"] = trades_per_year
    res["walk_forward"]["pos_years"] = f"{pos_years}/{n_years}"
    print(f"  WALK-FORWARD: full R={cf['mean_R']:+.4f} n={cf['n']} sum={cf['sum_R']}  "
          f"fwd R={cw['mean_R']:+.4f}(n{cw['n']})  ~{trades_per_year}/yr  pos_years {pos_years}/{n_years}")
    for y, p in wf["picks"].items():
        if p["year_n"]:
            print(f"     {y}: thr={p['threshold']} -> R={p['year_R']:+.4f} n={p['year_n']}")

    nl = nulls(name, base, wf_recs, THRESHOLDS)
    res["nulls"] = nl
    edge_directional = (nl["wf_invert_full_R"] < 0) and (cf["mean_R"] > nl["random_full_max_R"])
    res["edge_beats_nulls"] = bool(edge_directional)
    print(f"  NULLS: edge {cf['mean_R']:+.4f}  invert {nl['wf_invert_full_R']:+.4f}  "
          f"random {nl['random_full_mean_R']:+.4f}(max {nl['random_full_max_R']:+.4f})  "
          f"beats_nulls={edge_directional}")

    sizing = ftmo_sizing([{"ts": d["ts"], "r": d["r"]} for d in wf_recs])
    res["ftmo_sizing"] = sizing
    mx = sizing.get("max_risk_within_ftmo")
    if mx:
        print(f"  FTMO: max risk {mx['risk_pct_per_trade']}%/trade -> maxDD {mx['max_drawdown_pct']}%  "
              f"worstDay {mx['worst_day_pct']}%  ~monthly {mx['approx_monthly_pct']}%  "
              f"(totRet {mx['total_return_pct']}% over {sizing['span_months']}mo)")
    else:
        print(f"  FTMO: NO risk level keeps maxDD<10% AND worstDay<5%")
    return res

def main():
    random.seed(20260614)
    OUT = {"thrust": "gold_multiTF",
           "question": "finer TF (M15/H1) = more gold trades at comparable WF edge => higher monthly%? "
                       "or coarser TF (D1) = cleaner edge? recommend best gold TF(s) for FTMO-safe monthly%.",
           "carrier_reference_H4_from_wave4": {
               "xauusd_only_wf_full_R": 0.3224, "n": 275, "fwd_R": 0.5191,
               "precious_sleeve_ftmo_monthly_pct": 0.22, "xauusd_share_of_edge": 0.812},
           "held_constant": "FVG-retest 2R continuation geometry (geometry_lib), ATR14>=thr*SMA100 vol gate, "
                            "walk-forward thr re-selection, winsorize, real metals cost 0.0459R, invert+random nulls, "
                            "TRAIN<=2024 / FWD 2025-26 / chained WF, per-year.",
           "scaled_with_tf": "trend_lb and maxbars matched to the SAME wall-clock horizon as H4 (30 bars=120h, 80 bars). "
                             "stitch-gap guard rejects trades whose life exceeds 4x the nominal max wall-clock (anti-weekend-leak)."}

    by_tf = {}
    for name in ["D1", "H4", "H1", "M15"]:
        by_tf[name] = eval_tf(name)
    OUT["by_tf"] = by_tf

    # ---- COMPARISON TABLE + RECOMMENDATION ----
    print("\n" + "="*78); print("COMPARISON: gold carrier across timeframes (walk-forward)"); print("="*78)
    print(f"  {'TF':4s} {'WF_full_R':>10s} {'n':>6s} {'/yr':>6s} {'fwd_R':>8s} {'posYr':>7s} "
          f"{'beatsNull':>10s} {'maxRisk%':>9s} {'monthly%':>9s} {'maxDD%':>7s}")
    table = {}
    for name in ["D1", "H4", "H1", "M15"]:
        r = by_tf[name]; wf = r["walk_forward"]; mx = r["ftmo_sizing"].get("max_risk_within_ftmo")
        row = {
            "wf_full_R": wf["chained_full"]["mean_R"], "n": wf["n_trades"],
            "trades_per_year": wf["trades_per_year"], "fwd_R": wf["chained_fwd"]["mean_R"],
            "pos_years": wf["pos_years"], "beats_nulls": r["edge_beats_nulls"],
            "max_risk_pct": mx["risk_pct_per_trade"] if mx else None,
            "monthly_pct": mx["approx_monthly_pct"] if mx else None,
            "maxDD_pct": mx["max_drawdown_pct"] if mx else None,
        }
        table[name] = row
        print(f"  {name:4s} {row['wf_full_R']:>10.4f} {row['n']:>6d} {row['trades_per_year']:>6.1f} "
              f"{row['fwd_R']:>8.4f} {row['pos_years']:>7s} {str(row['beats_nulls']):>10s} "
              f"{str(row['max_risk_pct']):>9s} {str(row['monthly_pct']):>9s} {str(row['maxDD_pct']):>7s}")
    OUT["comparison_table"] = table

    # ---- recommendation: best FTMO-safe monthly% among TFs whose edge beats nulls & WF>0 ----
    valid = {k: v for k, v in table.items()
             if v["beats_nulls"] and v["wf_full_R"] > 0 and v["monthly_pct"] is not None}
    best_tf = max(valid, key=lambda k: valid[k]["monthly_pct"]) if valid else None
    h4 = table["H4"]
    finer_helps = best_tf in ("H1", "M15") and best_tf != "H4"
    rec = {
        "qualifying_tfs": list(valid.keys()),
        "best_tf_by_ftmo_monthly_pct": best_tf,
        "best_monthly_pct": valid[best_tf]["monthly_pct"] if best_tf else None,
        "h4_carrier_monthly_pct": h4["monthly_pct"],
        "finer_tf_beats_h4_monthly": bool(finer_helps),
        "verdict": None,
    }
    if best_tf is None:
        rec["verdict"] = ("No TF (incl H4) produced an FTMO-safe positive-WF edge that beats nulls "
                          "in THIS run; the gold carrier does not extend cleanly to other TFs.")
    elif best_tf == "H4":
        rec["verdict"] = ("H4 remains the best gold timeframe: finer TFs (M15/H1) did NOT deliver "
                          "more net trades at comparable edge, and D1 did not produce a cleaner deployable edge. "
                          "Keep the carrier on H4.")
    else:
        rec["verdict"] = (f"{best_tf} delivers higher FTMO-safe monthly% than H4 "
                          f"({valid[best_tf]['monthly_pct']}% vs {h4['monthly_pct']}%) at "
                          f"~{valid[best_tf]['trades_per_year']} trades/yr — finer TF extends the gold sleeve.")
    OUT["recommendation"] = rec
    print("\n" + "="*78); print("RECOMMENDATION"); print("="*78)
    for k, v in rec.items(): print(f"  {k}: {v}")

    with open(EDGE + "/WAVE6_GOLD_MULTITF_RESULT.json", "w") as f:
        json.dump(OUT, f, indent=1, default=str)
    print("\nWROTE WAVE6_GOLD_MULTITF_RESULT.json")

if __name__ == "__main__":
    main()
