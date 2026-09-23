"""
wave7_pairs_statarb.py
======================
THRUST (pairs_statarb): Statistical-arbitrage / ratio mean-reversion between CORRELATED
symbols. This is a genuinely UNCORRELATED family vs the single-symbol directional
continuation work that converged to one modest gold sleeve. We fade a rolling, PAST-ONLY
z-score of the spread between two correlated legs and exit on mean-revert (z back toward 0)
or a time/stop stop-out. The hedge ratio is estimated on a TRAILING window only (no
full-sample cointegration peeking), and every gate uses data at/<= the decision bar.

PAIRS TESTED (chosen by real H4 coverage in the MT5 deep exports):
  Tier A  (multi-year, supports TRAIN<=2024 / FORWARD 2025-26 OOS):
    - EURUSD / GBPUSD      (continuous 2018..2026; best coverage)
    - EURUSD / AUDUSD      (2018..2026 with gaps)
    - XAUUSD / XAGUSD      (2015..2021 + 2025..2026; metals complex)
  Tier B  (FORWARD-ONLY, 2025-26-ish; NO clean OOS split possible -> walk-forward only,
           reported but explicitly NOT counted as confirmed unless WF is positive):
    - NAS100 / SPX500
    - GER40  / UK100
    - XAUUSD / XAUEUR, XAUUSD / XAUAUD, XAGUSD / XAGEUR  (gold/silver crosses)
    - XAUUSD / XCUUSD (gold/copper)
  Tier DEAD (no usable overlap): USOIL_cash / UKOIL_cash (no common bars in usable window).

STRICT PROTOCOL:
  - NO LOOKAHEAD. At decision bar i:
      * hedge ratio beta estimated by OLS of legA-close on legB-close over the trailing
        HEDGE_WIN bars ending at i (bars[<=i] only).
      * spread_i = a_close_i - beta * b_close_i.
      * z_i = (spread_i - mean(spread over trailing Z_WIN)) / std(...), all bars[<=i].
      * Enter only when |z_i| >= z_entry. No future info.
  - PATH STATE from CLOSED trades only: at most one open pair-position; the next entry is
    considered only at/after the prior trade's CLOSED exit bar. No overlap peek.
  - SPREAD PnL computed DIRECTLY (geometry_lib simulate is single-instrument; a spread is
    two legs). We charge REAL per-leg round-trip cost on BOTH legs every trade:
      leg cost (in price) = spread_price (half-spread crossing modeled as full spread r/t)
      plus we additionally apply the campaign per-asset-class expected_cost_r as a fraction
      of the per-leg risk unit. PnL is reported in R where R = entry spread sigma (the
      z-window std at entry), i.e. a 1-sigma adverse move = -1R before costs.
  - EXITS (all forward-walked, decided bar-by-bar on CLOSED info up to that bar):
      * take-profit: z crosses back through Z_EXIT toward 0 (mean revert) -> close.
      * stop: |z| widens to Z_STOP (spread blew out) -> close.
      * time stop: MAXBARS bars elapsed -> close at that close.
    Direction: z>0 (spread rich) => SHORT spread (short A, long beta*B). z<0 => LONG spread.
  - STRICT OOS: parameters (z_entry, z_exit, z_stop, windows) selected on TRAIN<=2024 by
    after-cost SUM_R; FORWARD 2025-26 is pure read-out. SAME selected params applied to
    RANDOM and INVERT nulls (matched selection).
  - WALK-FORWARD: re-pick z_entry on a trailing past-only block, trade next block; reported
    for every pair (the only honest readout for Tier B forward-only pairs).
  - NULLS (matched): RANDOM = same #entries, random admissible bars, same exit machinery
    (baseline drift of the spread). INVERT = trade WITH the stretch (momentum on the spread)
    instead of fading it. A real reversion edge must beat BOTH forward.
  - WINSORIZE bad single-bar prints on each leg before features.
  - Per-year 2015-2026 reported for every pair.

VERDICT (per pair): CONFIRM only if ALL hold, else DEAD:
  forward mean_R > 0 AND forward sum_R > 0
  AND forward mean_R > RANDOM null forward mean_R + noise band
  AND forward mean_R > INVERT null forward mean_R
  AND positive in a MAJORITY of forward years
  AND walk-forward mean_R > 0.
Tier B pairs can at best be FORWARD-ONLY/WF-positive (flagged, never a hard CONFIRM).
"""
from __future__ import annotations
import sys, os, csv, json, math, random
from datetime import datetime
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
D1 = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022"
DM = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022_metals"
D2 = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
from geometry_lib import Bar, atr14  # geometry_lib is single-instrument; we compute spread PnL directly

SEED = 7
TRAIN_MAX = 2024
FWD_YEARS = (2025, 2026)
MAXBARS = 80           # max bars a pair-position is held
N_NULL = 200           # random null resamples for noise band

with open(EDGE + "/ULTIMATE_REAL_COST_MAP.json") as f:
    COSTMAP = json.load(f)
GC = COSTMAP["_global_median"]
def cost_r_for(s):  # per-asset-class expected_cost_r (fraction of a leg's risk unit)
    return COSTMAP.get(ASSET_CLASS_BY_SYMBOL.get(s), GC)

with open(EDGE + "/ULTIMATE_SYMBOL_SPREAD_SNAPSHOT.json") as f:
    SPREAD = json.load(f)
def spread_price(s):
    return SPREAD.get(s, {}).get("spread_price", 0.0)

# ---------------- data load (dedupe all H4 blocks; later wins) ----------------
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
    merged = {}
    for D in (D1, DM, D2):
        T, B = _load_one(f"{D}/{sym}_H4.csv")
        for t, b in zip(T, B):
            merged[t] = b  # later block wins on overlap
    if not merged: return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    return [k for k, _ in items], [v for _, v in items]

# ---------------- winsorize single-bar stitch spikes (causal-safe detection) ----------------
def winsorize_closes(times, bars, k_atr=8.0):
    n = len(bars)
    closes = [b.c for b in bars]
    nclip = 0
    for i in range(15, n - 1):
        a = atr14(bars, i - 1)
        if a <= 0: continue
        gap = bars[i].c - bars[i - 1].c
        if abs(gap) <= k_atr * a: continue
        revert = bars[i + 1].c - bars[i].c
        if gap * revert < 0 and abs(revert) > 0.5 * abs(gap):
            closes[i] = bars[i - 1].c + math.copysign(k_atr * a, gap)
            nclip += 1
    return closes, nclip

# ---------------- aligned pair series on COMMON timestamps ----------------
def aligned_pair(symA, symB):
    tA, bA = load(symA); tB, bB = load(symB)
    if not tA or not tB: return None
    cA, _ = winsorize_closes(tA, bA)
    cB, _ = winsorize_closes(tB, bB)
    mapA = {t: c for t, c in zip(tA, cA)}
    mapB = {t: c for t, c in zip(tB, cB)}
    common = sorted(set(mapA) & set(mapB))
    if len(common) < 600: return None
    times = common
    a = [mapA[t] for t in common]
    b = [mapB[t] for t in common]
    return times, a, b

# ---------------- rolling OLS hedge ratio (past-only) ----------------
def rolling_beta(a, b, i, win):
    # OLS slope of a on b over bars (i-win+1 .. i); needs bars[<=i] only.
    lo = i - win + 1
    if lo < 0: return None
    n = win
    sb = sa = sbb = sab = 0.0
    for j in range(lo, i + 1):
        sb += b[j]; sa += a[j]; sbb += b[j] * b[j]; sab += a[j] * b[j]
    den = n * sbb - sb * sb
    if abs(den) < 1e-12: return None
    beta = (n * sab - sb * sa) / den
    return beta

# ---------------- spread / z features at bar i (past-only) ----------------
def spread_z(a, b, i, hedge_win, z_win):
    beta = rolling_beta(a, b, i, hedge_win)
    if beta is None: return None
    lo = i - z_win + 1
    if lo < 0: return None
    sp = [a[j] - beta * b[j] for j in range(lo, i + 1)]
    m = sum(sp) / len(sp)
    var = sum((x - m) ** 2 for x in sp) / (len(sp) - 1)
    sd = math.sqrt(var)
    if sd <= 0: return None
    cur = a[i] - beta * b[i]
    z = (cur - m) / sd
    return beta, cur, m, sd, z

# ---------------- one pair-trade, forward-walked on CLOSED info ----------------
def run_trade(a, b, i, hedge_win, z_win, z_exit, z_stop, side, sd_entry, beta_entry,
              symA, symB, invert=False):
    """side: +1 = LONG spread (z<0 fade up), -1 = SHORT spread (z>0 fade down).
    invert flips into momentum (trade WITH stretch). Returns (R_after_cost, exit_idx).
    R unit = sd_entry (1-sigma). PnL = side * d(spread)/sd_entry, with spread recomputed
    each bar using the FROZEN entry beta (a real basket holds fixed leg sizes)."""
    if invert: side = -side
    entry_spread = a[i] - beta_entry * b[i]
    end = min(i + MAXBARS, len(a) - 1)
    exit_idx = end
    for j in range(i + 1, end + 1):
        f = spread_z(a, b, j, hedge_win, z_win)
        if f is None:
            continue
        _, _, _, _, zj = f
        # exits decided on closed bar j
        if abs(zj) >= z_stop:            # spread blew out -> stop
            exit_idx = j; break
        if side > 0 and zj >= -z_exit:   # was long (z<0), reverted up
            exit_idx = j; break
        if side < 0 and zj <= z_exit:    # was short (z>0), reverted down
            exit_idx = j; break
    cur_spread = a[exit_idx] - beta_entry * b[exit_idx]
    gross_R = side * (cur_spread - entry_spread) / sd_entry
    # ---- real per-leg costs ----
    # 1) crossing the bid/ask: full round-trip half-spread on BOTH legs, in PRICE,
    #    expressed in spread-R (divide by sd_entry). leg A is 1 unit, leg B is |beta| units.
    cross = (spread_price(symA) + abs(beta_entry) * spread_price(symB)) / sd_entry
    # 2) campaign per-asset-class expected_cost_r on each leg (slippage/commission proxy)
    klass_cost = cost_r_for(symA) + cost_r_for(symB)
    R = gross_R - cross - klass_cost
    return R, exit_idx

# ---------------- backtest a parameter set over an index range ----------------
def backtest(times, a, b, symA, symB, params, lo_i, hi_i, mode="real", rng=None):
    """mode: real | random | invert. Returns list of (year, R)."""
    hedge_win, z_win, z_entry, z_exit, z_stop = params
    out = []
    i = max(lo_i, hedge_win, z_win) + 1
    admissible = []  # for random null we need the admissible entry bars in range
    next_ok = i
    while i <= hi_i:
        f = spread_z(a, b, i, hedge_win, z_win)
        if f is None:
            i += 1; continue
        beta, cur, m, sd, z = f
        admissible.append(i)
        if i < next_ok:
            i += 1; continue
        if abs(z) < z_entry:
            i += 1; continue
        side = -1 if z > 0 else +1   # fade
        R, ex = run_trade(a, b, i, hedge_win, z_win, z_exit, z_stop, side, sd, beta,
                          symA, symB, invert=(mode == "invert"))
        out.append((times[i].year, R))
        next_ok = ex + 1
        i = max(i + 1, ex + 1)
    if mode != "random":
        return out
    # random null: same #entries as real, random admissible bars, same exit machinery
    real_n = backtest(times, a, b, symA, symB, params, lo_i, hi_i, mode="real")
    n = len(real_n)
    if n == 0 or not admissible: return []
    rng = rng or random.Random(SEED)
    picks = rng.sample(admissible, min(n, len(admissible)))
    res = []
    for i in picks:
        f = spread_z(a, b, i, hedge_win, z_win)
        if f is None: continue
        beta, cur, m, sd, z = f
        side = rng.choice((-1, +1))
        R, ex = run_trade(a, b, i, hedge_win, z_win, z_exit, z_stop, side, sd, beta, symA, symB)
        res.append((times[i].year, R))
    return res

def stats(trades):
    if not trades: return dict(n=0, sum_R=0.0, mean_R=0.0)
    rs = [r for _, r in trades]
    return dict(n=len(rs), sum_R=round(sum(rs), 3), mean_R=round(sum(rs) / len(rs), 4))

def per_year(trades):
    d = defaultdict(list)
    for y, r in trades: d[y].append(r)
    return {y: dict(n=len(v), sum_R=round(sum(v), 3), mean_R=round(sum(v) / len(v), 4))
            for y, v in sorted(d.items())}

# ---------------- parameter grid ----------------
HEDGE_WINS = [120, 250]
Z_WINS = [60, 120]
Z_ENTRIES = [1.5, 2.0, 2.5]
Z_EXITS = [0.0, 0.5]
Z_STOPS = [3.5, 4.5]
def grid():
    for hw in HEDGE_WINS:
        for zw in Z_WINS:
            for ze in Z_ENTRIES:
                for zx in Z_EXITS:
                    for zs in Z_STOPS:
                        if zx < ze and zs > ze:
                            yield (hw, zw, ze, zx, zs)

def idx_for_years(times, years):
    lo = hi = None
    for k, t in enumerate(times):
        if t.year in years:
            if lo is None: lo = k
            hi = k
    return lo, hi

def select_on_train(times, a, b, symA, symB):
    lo, hi = idx_for_years(times, set(range(2010, TRAIN_MAX + 1)))
    if lo is None: return None, None
    best = None; best_p = None
    for p in grid():
        tr = backtest(times, a, b, symA, symB, p, lo, hi, mode="real")
        s = stats(tr)
        if s["n"] < 12: continue   # need enough train trades to trust selection
        key = s["sum_R"]
        if best is None or key > best:
            best = key; best_p = p
    return best_p, (lo, hi)

# ---------------- walk-forward (trailing block re-fit z_entry) ----------------
def walk_forward(times, a, b, symA, symB, base_params):
    hw, zw, _, zx, zs = base_params
    n = len(times)
    start = max(hw, zw) + 1
    block = 1500  # ~ one year of H4 bars
    trades = []
    seg0 = start + block
    while seg0 + block <= n:
        # fit z_entry on trailing block [seg0-block, seg0)
        best = None; best_ze = None
        for ze in Z_ENTRIES:
            p = (hw, zw, ze, zx, zs)
            tr = backtest(times, a, b, symA, symB, p, seg0 - block, seg0 - 1, mode="real")
            s = stats(tr)
            if s["n"] < 6: continue
            if best is None or s["sum_R"] > best:
                best = s["sum_R"]; best_ze = ze
        if best_ze is not None:
            p = (hw, zw, best_ze, zx, zs)
            tr = backtest(times, a, b, symA, symB, p, seg0, min(seg0 + block - 1, n - 1), mode="real")
            trades += tr
        seg0 += block
    return trades

# ---------------- per-pair driver ----------------
def evaluate_pair(symA, symB, tier):
    al = aligned_pair(symA, symB)
    if al is None:
        return dict(pair=f"{symA}/{symB}", tier=tier, status="NO_DATA")
    times, a, b = al
    # correlation of returns (diagnostic, full-sample is fine for description only)
    ra = [a[k] / a[k - 1] - 1 for k in range(1, len(a))]
    rb = [b[k] / b[k - 1] - 1 for k in range(1, len(b))]
    ma = sum(ra) / len(ra); mb = sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb)) / len(ra)
    va = sum((x - ma) ** 2 for x in ra) / len(ra)
    vb = sum((y - mb) ** 2 for y in rb) / len(rb)
    corr = cov / math.sqrt(va * vb) if va > 0 and vb > 0 else 0.0

    res = dict(pair=f"{symA}/{symB}", tier=tier, n_common=len(times),
               span=f"{times[0].date()}..{times[-1].date()}",
               ret_corr=round(corr, 3))

    # walk-forward (always available)
    base = (HEDGE_WINS[0], Z_WINS[0], Z_ENTRIES[1], Z_EXITS[0], Z_STOPS[0])
    wf = walk_forward(times, a, b, symA, symB, base)
    res["walk_forward"] = stats(wf)
    res["walk_forward_by_year"] = per_year(wf)

    if tier == "A":
        sel, tridx = select_on_train(times, a, b, symA, symB)
        if sel is None:
            res["status"] = "INSUFFICIENT_TRAIN"
            return res
        res["selected_params"] = dict(hedge_win=sel[0], z_win=sel[1], z_entry=sel[2],
                                      z_exit=sel[3], z_stop=sel[4])
        lo_tr, hi_tr = tridx
        tr_real = backtest(times, a, b, symA, symB, sel, lo_tr, hi_tr, mode="real")
        res["train"] = stats(tr_real)
        # forward
        lo_fw, hi_fw = idx_for_years(times, set(FWD_YEARS))
        if lo_fw is None:
            res["status"] = "NO_FORWARD_DATA"
            return res
        fw_real = backtest(times, a, b, symA, symB, sel, lo_fw, hi_fw, mode="real")
        fw_rand = backtest(times, a, b, symA, symB, sel, lo_fw, hi_fw, mode="random",
                           rng=random.Random(SEED))
        fw_inv = backtest(times, a, b, symA, symB, sel, lo_fw, hi_fw, mode="invert")
        # random noise band over N_NULL resamples
        rmeans = []
        for s in range(N_NULL):
            rr = backtest(times, a, b, symA, symB, sel, lo_fw, hi_fw, mode="random",
                          rng=random.Random(1000 + s))
            if rr: rmeans.append(stats(rr)["mean_R"])
        rmeans.sort()
        band_hi = rmeans[int(0.95 * len(rmeans))] if rmeans else 0.0
        rand_mean = (sum(rmeans) / len(rmeans)) if rmeans else 0.0
        res["forward"] = stats(fw_real)
        res["forward_by_year"] = per_year(fw_real)
        res["forward_random_mean_R"] = round(rand_mean, 4)
        res["forward_random_p95_mean_R"] = round(band_hi, 4)
        res["forward_invert"] = stats(fw_inv)
        # verdict
        f = res["forward"]
        fy = res["forward_by_year"]
        pos_years = sum(1 for y in fy.values() if y["mean_R"] > 0)
        checks = dict(
            fwd_mean_pos = f["mean_R"] > 0,
            fwd_sum_pos = f["sum_R"] > 0,
            beats_random_band = f["mean_R"] > band_hi,
            beats_invert = f["mean_R"] > res["forward_invert"]["mean_R"],
            majority_years_pos = pos_years > len(fy) / 2 if fy else False,
            wf_pos = res["walk_forward"]["mean_R"] > 0,
        )
        res["checks"] = checks
        res["status"] = "CONFIRM" if all(checks.values()) else "DEAD"
    else:
        # Tier B: forward-only; honest readout = walk-forward only (no clean OOS split).
        wf_pos = res["walk_forward"]["mean_R"] > 0 and res["walk_forward"]["n"] >= 8
        res["status"] = "FORWARD_ONLY_WF_POSITIVE" if wf_pos else "DEAD"
    return res

PAIRS = [
    ("EURUSD", "GBPUSD", "A"),
    ("EURUSD", "AUDUSD", "A"),
    ("XAUUSD", "XAGUSD", "A"),
    ("NAS100", "SPX500", "B"),
    ("GER40", "UK100", "B"),
    ("XAUUSD", "XAUEUR", "B"),
    ("XAUUSD", "XAUAUD", "B"),
    ("XAGUSD", "XAGEUR", "B"),
    ("XAUUSD", "XCUUSD", "B"),
    ("USOIL_cash", "UKOIL_cash", "B"),
]

def main():
    random.seed(SEED)
    out = dict(thrust="pairs_statarb", generated=datetime.utcnow().isoformat() + "Z",
               protocol=dict(train_max=TRAIN_MAX, forward_years=list(FWD_YEARS),
                             maxbars=MAXBARS, n_null=N_NULL,
                             cost_model="per-leg crossing spread + per-asset-class expected_cost_r, in spread-sigma units",
                             R_unit="entry z-window spread sigma"),
               pairs=[])
    for symA, symB, tier in PAIRS:
        print(f"... {symA}/{symB} (tier {tier})", flush=True)
        r = evaluate_pair(symA, symB, tier)
        out["pairs"].append(r)
        print(json.dumps(r, indent=2), flush=True)
    confirmed = [p["pair"] for p in out["pairs"] if p.get("status") == "CONFIRM"]
    fwd_only = [p["pair"] for p in out["pairs"] if p.get("status") == "FORWARD_ONLY_WF_POSITIVE"]
    out["summary"] = dict(confirmed=confirmed, forward_only_wf_positive=fwd_only,
                          n_pairs=len(out["pairs"]))
    with open(EDGE + "/WAVE7_PAIRS_STATARB_RESULT.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\n==== SUMMARY ====")
    print("CONFIRMED:", confirmed or "NONE")
    print("FORWARD-ONLY WF+:", fwd_only or "NONE")

if __name__ == "__main__":
    main()
