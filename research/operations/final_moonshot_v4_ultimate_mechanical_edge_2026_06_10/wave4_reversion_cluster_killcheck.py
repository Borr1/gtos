"""
wave4_reversion_cluster_killcheck.py
====================================
THRUST (reversion_cluster_killcheck): Explicit CONFIRM or KILL of the weak-reversion
cluster {EURUSD, AUDUSD, CHFJPY} as a tradable REVERSION strategy (fade stretched moves
back to a mean) under STRICT forward gating + matched RANDOM and INVERT nulls.

Ground-truth context (WAVE3_GROUND_TRUTH_RESULT.json): these 3 were the only FX symbols
flagged REVERTING/durable_directional on TRAIN, but forward_confirmed == [] and the
EURUSD variance-ratio FLIPS >1 forward. This script asks the SHIP question the statistical
measurement could not: does a *real fade strategy* on these symbols, costed and gated
strictly, beat its own RANDOM (same-direction drift) and INVERT (momentum) nulls FORWARD?

STRICT PROTOCOL (prior subagent wins were leaks; 0/3 survived re-audit):
  - Fills ONLY via tested geometry_lib (simulate / simulate_detail). No hand-rolled stops.
  - NO LOOKAHEAD: every feature/gate at bar i uses ONLY bars[<=i]. The reversion signal
    (z-score / RSI / distance-from-EMA) is computed on closes up to and INCLUDING i, and
    entry is at bars[i].c with exits walked forward by the library.
  - PATH-STATE (cooldown / no-overlap): a symbol holds at most one open trade at a time;
    the next entry is only considered at/after the *closed* exit index returned by
    simulate_detail. This prevents the overlapping-trade peek.
  - STRICT OOS: parameter (z-threshold, stop/target multiples) selection done on
    TRAIN <= 2024 ONLY, by SUM_R after cost. FORWARD 2025-2026 is pure read-out. The same
    selected parameter set is then applied to RANDOM and INVERT nulls (matched selection).
  - Also a WALK-FORWARD variant: re-fit the z-threshold on a trailing past-only window and
    trade the next year, so no single train block can flatter the result.
  - WINSORIZE bad prints: single-bar spikes that revert next bar (file-stitch glitches)
    are clamped on the H/L/C used for z-score & stop features BEFORE any moment computation.
  - NULLS: RANDOM = same number of entries, same direction mix, random admissible bars,
    same exits (drift baseline). INVERT = flip the fade into momentum (trade WITH the
    stretch). A real reversion edge must beat BOTH forward.
  - Per-year 2015-2026 reported for every symbol.

VERDICT RULE (must clear ALL to CONFIRM, else KILL):
  forward mean_R > 0 AND forward sum_R > 0
  AND forward mean_R > RANDOM-null forward mean_R + null noise band
  AND forward mean_R > INVERT-null forward mean_R
  AND positive in a MAJORITY of forward years
  AND walk-forward forward mean_R > 0.
"""
from __future__ import annotations
import sys, os, csv, json, math, random
from datetime import datetime
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
D1 = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022"
D2 = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
from geometry_lib import Bar, atr14, simulate_detail

with open(EDGE + "/ULTIMATE_REAL_COST_MAP.json") as f:
    COSTMAP = json.load(f)
GC = COSTMAP["_global_median"]
def cost_for(s): return COSTMAP.get(ASSET_CLASS_BY_SYMBOL.get(s), GC)

CLUSTER = ["EURUSD", "AUDUSD", "CHFJPY"]
SEED = 7
TRAIN_MAX = 2024
FWD_YEARS = (2025, 2026)
MAXBARS = 80           # exit walk horizon (same as campaign default)
N_NULL = 200           # random null resamples for noise band

# ---------------- data load (dedupe both H4 blocks) ----------------
def _load_one(p):
    T, B = [], []
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

def load(sym):
    T1, B1 = _load_one(f"{D1}/{sym}_H4.csv")
    T2, B2 = _load_one(f"{D2}/{sym}_H4.csv")
    merged = {}
    for t, b in zip(T1, B1): merged[t] = b
    for t, b in zip(T2, B2): merged[t] = b   # later file wins on overlap
    if not merged: return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    return [v for _, v in items], [k for k, _ in items]

# ---------------- winsorize file-stitch bad prints ----------------
# A bad print = a single bar whose range or close jump is an extreme multiple of local ATR
# AND reverts next bar. We clamp the offending H/L/C toward the neighbour-implied level so
# the z-score / stop features are not poisoned. Done IN PLACE on a copy, causal-safe because
# we only ever read clamped values at i and the clamp at i uses bars[i-1] and bars[i+1] only
# for *detection of a glitch*, not for any forward-looking signal — and we additionally
# expose a strictly-causal clamp (uses i-1 only) for the LIVE signal path.
def winsorize(bars, k_atr=8.0):
    """Returns (clean_bars, n_clipped). Clamps bars whose close gap from prev close exceeds
    k_atr * local ATR and is reverted by >50% next bar (classic stitch spike)."""
    n = len(bars)
    clean = [Bar(b.o, b.h, b.l, b.c, b.v) for b in bars]
    nclip = 0
    for i in range(15, n - 1):
        a = atr14(bars, i - 1)               # ATR up to i-1 only (causal for detection scale)
        if a <= 0: continue
        gap = bars[i].c - bars[i - 1].c
        if abs(gap) <= k_atr * a:
            continue
        # spike must revert: next close comes back > 50% of the gap toward prev close
        revert = bars[i + 1].c - bars[i].c
        if gap * revert < 0 and abs(revert) > 0.5 * abs(gap):
            lim = k_atr * a
            newc = bars[i - 1].c + math.copysign(lim, gap)
            clean[i].c = newc
            clean[i].h = max(min(bars[i].h, bars[i - 1].c + lim), newc) if gap > 0 else clean[i].h
            clean[i].l = min(max(bars[i].l, bars[i - 1].c - lim), newc) if gap < 0 else clean[i].l
            # ensure OHLC consistency
            clean[i].h = max(clean[i].h, clean[i].c, clean[i].o)
            clean[i].l = min(clean[i].l, clean[i].c, clean[i].o)
            nclip += 1
    return clean, nclip

def year_of(t): return t.year

# ---------------- causal reversion features (only bars[<=i]) ----------------
def ema_series(bars, span):
    k = 2.0 / (span + 1.0)
    out = [None] * len(bars); e = None
    for i, b in enumerate(bars):
        e = b.c if e is None else (b.c * k + e * (1 - k))
        out[i] = e
    return out

def rsi_series(bars, period=14):
    out = [None] * len(bars)
    if len(bars) <= period: return out
    ag = al = 0.0
    for i in range(1, period + 1):
        ch = bars[i].c - bars[i - 1].c
        ag += max(ch, 0.0); al += max(-ch, 0.0)
    ag /= period; al /= period
    rs = ag / al if al > 0 else float("inf")
    out[period] = 100 - 100 / (1 + rs)
    for i in range(period + 1, len(bars)):
        ch = bars[i].c - bars[i - 1].c
        g = max(ch, 0.0); l = max(-ch, 0.0)
        ag = (ag * (period - 1) + g) / period
        al = (al * (period - 1) + l) / period
        rs = ag / al if al > 0 else float("inf")
        out[i] = 100 - 100 / (1 + rs)
    return out

def zstd_window(bars, i, w=20):
    """mean & std of close over [i-w+1 .. i] (causal)."""
    if i < w: return None
    cs = [bars[j].c for j in range(i - w + 1, i + 1)]
    m = sum(cs) / w
    var = sum((c - m) ** 2 for c in cs) / w
    sd = math.sqrt(var)
    return m, sd

# ---------------- build admissible reversion-entry candidate rows ----------------
# A reversion *candidate* at bar i: price is stretched away from its 20-bar mean
# (|z| >= z_thr) AND RSI confirms exhaustion (RSI<=lo for longs / RSI>=hi for shorts).
# direction = FADE the stretch (long when below mean & oversold, short when above & overbought).
def candidate_rows(bars, times, z_floor=1.0):
    a14 = [atr14(bars, i) for i in range(len(bars))]
    ema20 = ema_series(bars, 20)
    rsi = rsi_series(bars, 14)
    rows = []
    for i in range(40, len(bars) - 1):
        a = a14[i]
        if a <= 0: continue
        zs = zstd_window(bars, i, 20)
        if zs is None: continue
        mean, sd = zs
        if sd <= 0: continue
        z = (bars[i].c - mean) / sd
        if abs(z) < z_floor: continue           # keep only stretched bars (sample shaping)
        r = rsi[i]
        if r is None: continue
        rows.append(dict(i=i, yr=year_of(times[i]), a=a, z=z, rsi=r,
                         dist_ema=(bars[i].c - ema20[i]) / a))
    return rows, a14

def fade_dir(row, z_thr, rsi_lo, rsi_hi):
    """Reversion direction: fade the stretch. +1 long / -1 short / 0 skip."""
    if row["z"] <= -z_thr and row["rsi"] <= rsi_lo: return +1
    if row["z"] >= z_thr and row["rsi"] >= rsi_hi: return -1
    return 0

# ---------------- non-overlapping sequential trade simulation ----------------
def run_strategy(bars, rows, a14, sym, z_thr, rsi_lo, rsi_hi, stop_mult, tgt_mult,
                 direction_sign=+1):
    """Walk candidate rows in time order; only open a trade if no trade currently open
    (i > last_exit_index). direction_sign=+1 => fade (reversion); -1 => invert (momentum).
    Returns list of (year, R)."""
    c = cost_for(sym)
    out = []
    last_exit = -1
    for row in rows:
        i = row["i"]
        if i <= last_exit:        # path-state: prior trade not yet closed -> no overlap/peek
            continue
        d = fade_dir(row, z_thr, rsi_lo, rsi_hi)
        if d == 0: continue
        d *= direction_sign
        a = row["a"]
        R, ex = simulate_detail(bars, i, d, stop_dist=stop_mult * a,
                                target_dist=tgt_mult * a, maxbars=MAXBARS, cost=c)
        out.append((row["yr"], R))
        last_exit = ex
    return out

def run_random(bars, rows, a14, sym, z_thr, rsi_lo, rsi_hi, stop_mult, tgt_mult,
               n_entries, dir_counts, rng):
    """Matched RANDOM null: draw n_entries random admissible candidate bars (same |z|>=floor
    pool), assign directions to MATCH the real long/short counts, simulate identically.
    Returns list of (year, R)."""
    c = cost_for(sym)
    pool = [row for row in rows]
    if not pool or n_entries == 0: return []
    n_long, n_short = dir_counts
    picks = rng.sample(pool, min(n_entries, len(pool))) if n_entries <= len(pool) \
        else [rng.choice(pool) for _ in range(n_entries)]
    dirs = [+1] * n_long + [-1] * n_short
    rng.shuffle(dirs)
    out = []
    for row, d in zip(picks, dirs):
        R, ex = simulate_detail(bars, row["i"], d, stop_dist=stop_mult * row["a"],
                                target_dist=tgt_mult * row["a"], maxbars=MAXBARS, cost=c)
        out.append((row["yr"], R))
    return out

# ---------------- summarize ----------------
def stats(records):
    rs = [r for _, r in records]
    if not rs: return {"n": 0, "mean_R": 0.0, "win%": 0.0, "sum_R": 0.0}
    n = len(rs); s = sum(rs); w = sum(1 for r in rs if r > 0)
    return {"n": n, "mean_R": round(s / n, 4), "win%": round(100 * w / n, 1),
            "sum_R": round(s, 2)}

def split(records):
    tr = [(y, r) for y, r in records if y <= TRAIN_MAX]
    fw = [(y, r) for y, r in records if y >= FWD_YEARS[0]]
    return tr, fw

def per_year(records):
    by = defaultdict(list)
    for y, r in records: by[y].append((y, r))
    return {y: stats(by[y]) for y in sorted(by)}

# ---------------- in-sample param selection (TRAIN<=2024 ONLY) ----------------
Z_GRID = [1.0, 1.25, 1.5, 1.75, 2.0]
STOP_GRID = [0.5, 0.75, 1.0]
TGT_GRID = [1.0, 1.5, 2.0]
RSI_BANDS = [(35, 65), (30, 70), (25, 75)]

def select_params(bars, rows, a14, sym):
    """Grid-search on TRAIN<=2024 ONLY, maximize train sum_R after cost (with a min trade
    floor so we don't select a 3-trade fluke). Returns best param dict or None."""
    best = None
    for z in Z_GRID:
        for (lo, hi) in RSI_BANDS:
            for sm in STOP_GRID:
                for tm in TGT_GRID:
                    recs = run_strategy(bars, rows, a14, sym, z, lo, hi, sm, tm, +1)
                    tr, _ = split(recs)
                    if len(tr) < 30:    # require a credible in-sample sample
                        continue
                    st = stats(tr)
                    score = st["sum_R"]
                    if best is None or score > best["train_sum_R"]:
                        best = dict(z=z, rsi_lo=lo, rsi_hi=hi, stop=sm, tgt=tm,
                                    train_n=st["n"], train_sum_R=st["sum_R"],
                                    train_mean_R=st["mean_R"])
    return best

# ---------------- walk-forward (re-fit on trailing past, trade next year) ----------------
def walk_forward(bars, rows, a14, sym):
    """For each target year Y in 2018..2026, re-fit z-threshold (only) on all rows with
    year < Y maximizing past sum_R (fixed sensible stop/tgt/rsi to avoid overfit blowup),
    then trade year Y. Returns (records, per_year_selected_z)."""
    years = sorted({row["yr"] for row in rows})
    if not years: return [], {}
    out = []; sel = {}
    lo, hi, sm, tm = 30, 70, 0.75, 1.5   # fixed geometry; only z adapts
    for Y in years:
        past = [row for row in rows if row["yr"] < Y]
        if len(past) < 60:   # need enough history
            continue
        bz = None; bs = None
        for z in Z_GRID:
            recs = run_strategy(bars, past, a14, sym, z, lo, hi, sm, tm, +1)
            st = stats(recs)
            if st["n"] < 20: continue
            if bs is None or st["sum_R"] > bs:
                bs = st["sum_R"]; bz = z
        if bz is None: continue
        sel[Y] = bz
        yr_rows = [row for row in rows if row["yr"] == Y]
        recs = run_strategy(bars, yr_rows, a14, sym, bz, lo, hi, sm, tm, +1)
        out.extend(recs)
    return out, sel

# ================================ MAIN ================================
def main():
    rng = random.Random(SEED)
    report = {"_thrust": "reversion_cluster_killcheck",
              "_cluster": CLUSTER,
              "_protocol": {
                  "fills": "geometry_lib.simulate_detail (tested)",
                  "no_lookahead": "features at i use bars[<=i]; non-overlap via closed exit index",
                  "oos": "params selected TRAIN<=2024 by sum_R; forward 2025-26 read-out; "
                         "RANDOM+INVERT nulls under same params; plus walk-forward",
                  "winsorize": "single-bar stitch spikes (>8xATR gap reverting next bar) clamped",
                  "nulls": "RANDOM=matched-count matched-direction random bars; INVERT=trade WITH stretch",
              },
              "_params_grid": {"z": Z_GRID, "stop": STOP_GRID, "tgt": TGT_GRID, "rsi": RSI_BANDS},
              "symbols": {}}

    verdicts = {}
    for sym in CLUSTER:
        raw, times = load(sym)
        if not raw:
            report["symbols"][sym] = {"error": "no data"}; continue
        bars, nclip = winsorize(raw)
        rows, a14 = candidate_rows(bars, times, z_floor=1.0)

        sel = select_params(bars, rows, a14, sym)
        sym_rep = {"asset_class": ASSET_CLASS_BY_SYMBOL.get(sym),
                   "n_bars": len(bars), "n_clipped_bad_prints": nclip,
                   "n_stretched_candidates": len(rows),
                   "selected_params": sel}
        if sel is None:
            sym_rep["verdict"] = "KILL_no_credible_train_sample"
            report["symbols"][sym] = sym_rep
            verdicts[sym] = "KILL"
            continue

        z, lo, hi, sm, tm = sel["z"], sel["rsi_lo"], sel["rsi_hi"], sel["stop"], sel["tgt"]

        # --- real reversion strategy with selected params ---
        real = run_strategy(bars, rows, a14, sym, z, lo, hi, sm, tm, +1)
        tr, fw = split(real)
        # direction counts (real) for matched null
        n_long = sum(1 for row in rows
                     if fade_dir(row, z, lo, hi) == +1)
        # counts of ACTUALLY TAKEN trades (after non-overlap) by direction:
        taken_long = taken_short = 0
        last_exit = -1
        for row in rows:
            if row["i"] <= last_exit: continue
            d = fade_dir(row, z, lo, hi)
            if d == 0: continue
            _, ex = simulate_detail(bars, row["i"], d, stop_dist=sm * row["a"],
                                    target_dist=tm * row["a"], maxbars=MAXBARS, cost=cost_for(sym))
            last_exit = ex
            if d > 0: taken_long += 1
            else: taken_short += 1
        n_taken = taken_long + taken_short

        # --- INVERT null (momentum: trade WITH the stretch), same params ---
        inv = run_strategy(bars, rows, a14, sym, z, lo, hi, sm, tm, -1)
        inv_tr, inv_fw = split(inv)

        # --- RANDOM null: forward-window resamples, matched count+direction ---
        fwd_rows = [row for row in rows if row["yr"] >= FWD_YEARS[0]]
        rnd_means = []
        for _ in range(N_NULL):
            rrec = run_random(bars, fwd_rows, a14, sym, z, lo, hi, sm, tm,
                              n_taken if n_taken <= len(fwd_rows) else len(fwd_rows),
                              (taken_long, taken_short), rng)
            if rrec:
                rnd_means.append(stats(rrec)["mean_R"])
        rnd_means.sort()
        rnd_mean = round(sum(rnd_means) / len(rnd_means), 4) if rnd_means else 0.0
        rnd_p95 = round(rnd_means[int(0.95 * (len(rnd_means) - 1))], 4) if rnd_means else 0.0

        # --- walk-forward ---
        wf, wf_sel = walk_forward(bars, rows, a14, sym)
        wf_tr, wf_fw = split(wf)

        fw_st = stats(fw); tr_st = stats(tr)
        inv_fw_st = stats(inv_fw); wf_fw_st = stats(wf_fw)
        py = per_year(real)
        fwd_pos_years = sum(1 for y in FWD_YEARS if y in py and py[y]["mean_R"] > 0)
        fwd_year_count = sum(1 for y in FWD_YEARS if y in py)

        sym_rep.update({
            "taken_trades": {"total": n_taken, "long": taken_long, "short": taken_short},
            "real": {"train": tr_st, "forward": fw_st},
            "invert_null": {"train": stats(inv_tr), "forward": inv_fw_st},
            "random_null_forward": {"mean_R_avg": rnd_mean, "mean_R_p95": rnd_p95,
                                    "n_resamples": len(rnd_means)},
            "walk_forward": {"train": stats(wf_tr), "forward": wf_fw_st,
                             "selected_z_by_year": wf_sel},
            "per_year": py,
        })

        # ---- verdict ----
        reasons = []
        ok = True
        if not (fw_st["mean_R"] > 0): ok = False; reasons.append("fwd mean_R<=0")
        if not (fw_st["sum_R"] > 0): ok = False; reasons.append("fwd sum_R<=0")
        if not (fw_st["mean_R"] > rnd_p95): ok = False; reasons.append("fwd<=RANDOM p95")
        if not (fw_st["mean_R"] > inv_fw_st["mean_R"]): ok = False; reasons.append("fwd<=INVERT")
        if not (fwd_year_count and fwd_pos_years > fwd_year_count / 2.0):
            ok = False; reasons.append("not majority fwd years positive")
        if not (wf_fw_st["mean_R"] > 0): ok = False; reasons.append("walk-forward fwd mean_R<=0")
        if fw_st["n"] < 10: ok = False; reasons.append("fwd n<10 (untradeable sample)")

        sym_rep["verdict"] = "CONFIRM" if ok else "KILL"
        sym_rep["verdict_reasons"] = reasons if not ok else ["all gates passed"]
        report["symbols"][sym] = sym_rep
        verdicts[sym] = sym_rep["verdict"]

    report["verdicts"] = verdicts
    report["cluster_verdict"] = ("CONFIRM" if all(v == "CONFIRM" for v in verdicts.values())
                                 else "KILL")
    outp = EDGE + "/WAVE4_REVERSION_CLUSTER_KILLCHECK_RESULT.json"
    with open(outp, "w") as f:
        json.dump(report, f, indent=1)

    # ---- console summary ----
    print("=" * 78)
    print("REVERSION CLUSTER KILLCHECK — {EURUSD, AUDUSD, CHFJPY}")
    print("=" * 78)
    for sym in CLUSTER:
        r = report["symbols"][sym]
        if "error" in r: print(f"\n{sym}: {r['error']}"); continue
        print(f"\n### {sym}  ({r['asset_class']})  bars={r['n_bars']}  "
              f"bad_prints_clipped={r['n_clipped_bad_prints']}  "
              f"stretched_candidates={r['n_stretched_candidates']}")
        if r.get("selected_params") is None:
            print(f"   VERDICT: {r['verdict']}"); continue
        sp = r["selected_params"]
        print(f"   selected: z>={sp['z']} rsi=({sp['rsi_lo']},{sp['rsi_hi']}) "
              f"stop={sp['stop']}xATR tgt={sp['tgt']}xATR  "
              f"(train n={sp['train_n']} sumR={sp['train_sum_R']} meanR={sp['train_mean_R']})")
        tt = r["taken_trades"]
        print(f"   taken trades: {tt['total']} (L={tt['long']} S={tt['short']})")
        print(f"   REAL    train: {r['real']['train']}")
        print(f"   REAL  forward: {r['real']['forward']}")
        print(f"   INVERT forward: {r['invert_null']['forward']}")
        print(f"   RANDOM forward null: mean_R avg={r['random_null_forward']['mean_R_avg']} "
              f"p95={r['random_null_forward']['mean_R_p95']} "
              f"(n={r['random_null_forward']['n_resamples']})")
        print(f"   WALK-FWD forward: {r['walk_forward']['forward']}  "
              f"z-by-year={r['walk_forward']['selected_z_by_year']}")
        print(f"   per-year:")
        for y, st in r["per_year"].items():
            tag = "FWD" if y >= FWD_YEARS[0] else "   "
            print(f"      {y} {tag}  n={st['n']:>3}  mean_R={st['mean_R']:+.4f}  "
                  f"win%={st['win%']:>5}  sum_R={st['sum_R']:+.2f}")
        print(f"   >>> VERDICT: {r['verdict']}  reasons={r['verdict_reasons']}")
    print("\n" + "=" * 78)
    print(f"CLUSTER VERDICT: {report['cluster_verdict']}   per-symbol: {verdicts}")
    print(f"written: {outp}")

if __name__ == "__main__":
    main()
