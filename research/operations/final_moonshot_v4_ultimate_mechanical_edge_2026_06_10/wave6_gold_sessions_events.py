"""
wave6_gold_sessions_events.py
=============================
THRUST: gold_sessions_events.

Question: Are there GOLD-specific time-structure windows -- session-of-day,
day-of-week, and volatility-EVENT (ATR-expansion) days -- with a forward-positive,
cross-year-stable CONTINUATION edge that can ADD trades to the gold sleeve at
the same-or-better per-trade edge as the established carrier?

Established carrier (comparator, from prior waves, NOT re-derived here):
  gold-anchored, vol-gated (ATR14 >= 1.2*SMA100) FVG-retest 2R continuation.
  ~0.2-0.35%/mo FTMO-safe, ~81% XAUUSD share. Per-trade edge on the gated
  metals FVG-retest is modest (train ~+0.06R, fwd ~+0.09R per WAVE3_FVG_REGIME_HONEST).

DATA (MT5 only):
  - H4 gold/silver 2015-2026 (deep, cross-year). 6 bars/day at server hours
    {0,4,8,12,16,20}. This is the PRIMARY surface: it is the only gold series with
    enough cross-year history for honest OOS selection on time structure.
  - D1 gold 2022-2026 for ATR-spike event-day detection (no calendar; spike = proxy
    for FOMC/CPI/large-news days).
  - H1 gold 2025-06..2026 (recent only) used ONLY as an out-of-sample CONFIRMATION
    probe of the chosen session block at finer resolution -- NOT for selection
    (too short for cross-year OOS).

SESSION MAP (server hours on the H4 grid; volume peaks at 16:00 = NY, prior wave):
  Asia   : bar hours {0, 4}
  London : bar hours {8, 12}
  NY     : bar hours {16, 20}
  (Each H4 bar is labeled by its open hour; a "session block" entry uses the
   close of that H4 bar as the decision/entry bar.)

DISCIPLINE (STRICT PROTOCOL):
  - ALL fills via tested geometry_lib.simulate / simulate_detail. No hand-rolled
    fills, signs, or weekend horizons.
  - NO LOOKAHEAD: every gate/feature at bar i uses only data at/<=i. ATR, momentum,
    SMA, and the D1 spike flag are all computed from CLOSED bars strictly before/at i.
  - STRICT OOS: SELECT the single best configuration on TRAIN (year<=2024) ONLY;
    read out FORWARD (2025-2026) and report FULL per-year 2015-2026.
  - MULTIPLE-TESTING HONEST: a window is a "bar" only if it is (a) forward-positive
    AND (b) positive in a MAJORITY of all available years AND (c) positive in
    BOTH forward years. We scan a grid but the verdict is gated on cross-year
    persistence, not on the best forward number.
  - NULLS UNDER THE SAME SELECTION RULE: for the selected winner, run a matched
    RANDOM-entry null (same count, same direction mix, random eligible bars) and an
    INVERT null (opposite direction, same entries). The edge must beat both.
  - Winsorize obviously bad-print bars (drop H4 bars whose true range > 25*ATR14).

Writes WAVE6_GOLD_SESSIONS_EVENTS_RESULT.json and prints an honest verdict.
"""
from __future__ import annotations
import sys, os, csv, json, random, statistics
from datetime import datetime
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
H4_A = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022"
H4_B = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
H4_AM = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022_metals"
D1_DIR = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_d1_2022_2026"
H1_DIR = ROOT + "/data/mt5_research_exports/bridge_ftmo_htf_20250601_20260610"
sys.path.insert(0, ROOT)
sys.path.insert(0, EDGE)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL  # noqa
from geometry_lib import Bar, atr14, simulate, simulate_detail  # noqa

with open(EDGE + "/ULTIMATE_REAL_COST_MAP.json") as f:
    COSTMAP = json.load(f)
GC = COSTMAP["_global_median"]
def cost_for(sym):
    return COSTMAP.get(ASSET_CLASS_BY_SYMBOL.get(sym), GC)

RNG = random.Random(20260614)

GOLD = "XAUUSD"
SILVER = "XAGUSD"

SESSIONS = {
    "Asia":   {0, 4},
    "London": {8, 12},
    "NY":     {16, 20},
}
DOW = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri"}

# ---------------------------------------------------------------- loaders
def _load_csv(p):
    T, B = [], []
    if not os.path.exists(p):
        return T, B
    with open(p) as f:
        for row in csv.DictReader(f):
            try:
                t = datetime.fromisoformat(row["time"])
                b = Bar(float(row["open"]), float(row["high"]), float(row["low"]),
                        float(row["close"]), float(row.get("volume", 0) or 0))
                T.append(t); B.append(b)
            except Exception:
                continue
    return T, B

def load_h4(sym):
    """Concat all H4 sources for sym, dedupe by timestamp, ascending."""
    merged = {}
    for d in (H4_A, H4_AM, H4_B):
        T, B = _load_csv(f"{d}/{sym}_H4.csv")
        for t, b in zip(T, B):
            merged[t] = b  # later dirs win on overlap (H4_B newest)
    if not merged:
        return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    return [k for k, _ in items], [v for _, v in items]

def load_d1(sym):
    return _load_csv(f"{D1_DIR}/{sym}_D1.csv")

def load_h1(sym):
    return _load_csv(f"{H1_DIR}/{sym}_H1.csv")

# ---------------------------------------------------------------- winsorize
def winsorize_mask(B):
    """True = keep. Drop bars whose true range > 25*ATR14 (bad prints). ATR uses
    only data <= i so this is causal."""
    n = len(B)
    keep = [True] * n
    for i in range(1, n):
        a = atr14(B, i)
        if a <= 0:
            continue
        tr = max(B[i].h - B[i].l, abs(B[i].h - B[i-1].c), abs(B[i].l - B[i-1].c))
        if tr > 25 * a:
            keep[i] = False
    return keep

# ---------------------------------------------------------------- features (causal)
def sma(B, i, lb):
    if i < lb:
        return None
    return sum(B[j].c for j in range(i-lb+1, i+1)) / lb

def momentum_dir(B, i, lb):
    """Direction of recent momentum from CLOSED bars only: sign of c[i]-c[i-lb]."""
    if i < lb:
        return 0
    diff = B[i].c - B[i-lb].c
    a = atr14(B, i)
    if a <= 0:
        return 0
    if diff > 0.0:
        return 1
    if diff < 0.0:
        return -1
    return 0

# ---------------------------------------------------------------- event-day maps
# LEAK NOTE: a same-day D1 spike flag uses that day's complete high/low/close, which
# is only known at the day's CLOSE. Taking intraday (H4) entries on that same day is
# lookahead. Two strictly-causal alternatives are used instead:
#   (1) prev_day_spike: enter on the day AFTER a completed D1 spike (post-event drift).
#       The flag is known at the prior day's close => causal for all of the next day.
#   (2) causal H4 vol-gate: ATR-expansion measured ONLY from closed H4 bars at/<=i
#       (this is the established carrier gate; fully causal at the entry bar).

def d1_spike_dates(sym, thresh):
    """Calendar dates whose COMPLETED D1 bar is a volatility spike:
    D1 true range >= thresh * ATR14(strictly-prior days). Returned set is the set of
    spike days themselves (the flag is only confirmed at that day's close)."""
    T, B = load_d1(sym)
    flagged = set()
    n = len(B)
    for i in range(15, n):
        a = atr14(B, i-1)  # ATR from bars strictly before day i (causal)
        if a <= 0:
            continue
        tr = max(B[i].h - B[i].l, abs(B[i].h - B[i-1].c), abs(B[i].l - B[i-1].c))
        if tr >= thresh * a:
            flagged.add(T[i].date())
    return flagged

def post_spike_dates(sym, thresh):
    """Causal post-event set: each date that is the FIRST trading day strictly AFTER a
    D1 spike day. Entering anywhere on these days is lookahead-free because the spike
    was confirmed at the previous day's close."""
    T, B = load_d1(sym)
    n = len(B)
    spike_idx = []
    for i in range(15, n):
        a = atr14(B, i-1)
        if a <= 0:
            continue
        tr = max(B[i].h - B[i].l, abs(B[i].h - B[i-1].c), abs(B[i].l - B[i-1].c))
        if tr >= thresh * a:
            spike_idx.append(i)
    post = set()
    for i in spike_idx:
        if i + 1 < n:
            post.add(T[i+1].date())  # next available trading day
    return post

def h4_volgate_mask(B, i, lb=100, mult=1.2):
    """Causal carrier-style vol gate at H4 bar i: ATR14(i) >= mult * SMA_lb(ATR14).
    Uses only bars at/<=i (ATR14 and the rolling ATR mean are both backward-looking)."""
    if i < lb + 14:
        return False
    a_now = atr14(B, i)
    if a_now <= 0:
        return False
    s = 0.0
    for j in range(i-lb+1, i+1):
        s += atr14(B, j)
    mean_atr = s / lb
    if mean_atr <= 0:
        return False
    return a_now >= mult * mean_atr

# ---------------------------------------------------------------- stats
def agg(rs):
    n = len(rs)
    if n == 0:
        return {"n": 0, "R": 0.0, "win": 0.0, "tot": 0.0}
    tot = sum(rs); w = sum(1 for r in rs if r > 0)
    return {"n": n, "R": round(tot/n, 4), "win": round(100*w/n, 1), "tot": round(tot, 1)}

def per_year(recs):
    by = defaultdict(list)
    for y, r in recs:
        by[y].append(r)
    return {y: agg(by[y]) for y in sorted(by)}

def split(recs):
    """recs: list of (year, R)."""
    tr = [r for y, r in recs if y <= 2024]
    fw = [r for y, r in recs if y >= 2025]
    return agg(tr), agg(fw)

def persistence(recs):
    """returns (pos_years, total_years, pos_fwd_years, total_fwd_years)."""
    py = per_year(recs)
    yrs = sorted(py)
    fwd = [y for y in yrs if y >= 2025]
    return (sum(1 for y in yrs if py[y]["R"] > 0), len(yrs),
            sum(1 for y in fwd if py[y]["R"] > 0), len(fwd))

# ---------------------------------------------------------------- core entry engine
def gen_entries(sym, hours, *, mom_lb, stop_mult, target_R, dow=None,
                spike_dates=None, spike_mode=None, volgate=False,
                direction_mode="momentum",
                fixed_dir=0, invert=False, random_bars=False, keep=None,
                B=None, T=None, atrs=None):
    """
    Generate continuation trades for sym at H4 bars whose open-hour is in `hours`.
    Entry = close of that bar (decision bar i). Direction:
      direction_mode='momentum' -> sign of momentum over mom_lb (continuation).
      direction_mode='fixed'    -> fixed_dir (drift bias).
    Gates (ALL CAUSAL):
      optional day-of-week.
      spike_mode=None        -> ignore event flag
      spike_mode='on'        -> only bars whose DATE is in spike_dates
                                (use a CAUSAL set, e.g. post_spike_dates, NOT same-day)
      spike_mode='off'       -> only bars whose DATE is NOT in spike_dates
      volgate=True           -> require causal H4 vol-expansion at i (carrier gate)
    stop_dist = stop_mult*ATR14(i); target_dist = target_R*stop_dist.
    invert -> flip direction (null).
    Returns list of (year, R).
    """
    out = []
    n = len(B)
    cost = cost_for(sym)
    for i in range(60, n - 1):
        if keep is not None and not keep[i]:
            continue
        t = T[i]
        if t.hour not in hours:
            continue
        if dow is not None and t.weekday() != dow:
            continue
        if spike_mode == "on" and t.date() not in spike_dates:
            continue
        if spike_mode == "off" and t.date() in spike_dates:
            continue
        if volgate and not h4_volgate_mask(B, i):
            continue
        a = atrs[i]
        if a <= 0:
            continue
        if direction_mode == "momentum":
            d = momentum_dir(B, i, mom_lb)
            if d == 0:
                continue
        else:
            d = fixed_dir
        if invert:
            d = -d
        stop_dist = stop_mult * a
        target_dist = target_R * stop_dist
        r = simulate(B, i, d, stop_dist=stop_dist, target_dist=target_dist, cost=cost)
        out.append((t.year, r))
    return out

def gen_random_null(sym, n_target, *, mom_lb, stop_mult, target_R, dir_pool,
                    B, T, atrs, keep):
    """Matched random null: pick n_target random eligible bars (any hour, valid ATR,
    winsor-kept) and assign directions sampled from dir_pool (the realized direction
    distribution of the actual entries). Same geometry/cost."""
    cost = cost_for(sym)
    n = len(B)
    elig = [i for i in range(60, n-1)
            if (keep is None or keep[i]) and atrs[i] > 0]
    if not elig or not dir_pool:
        return []
    out = []
    for _ in range(n_target):
        i = RNG.choice(elig)
        d = RNG.choice(dir_pool)
        stop_dist = stop_mult * atrs[i]
        r = simulate(B, i, d, stop_dist=stop_dist, target_dist=target_R*stop_dist, cost=cost)
        out.append((T[i].year, r))
    return out

# ---------------------------------------------------------------- precompute per-symbol
def prep(sym):
    T, B = load_h4(sym)
    atrs = [atr14(B, i) for i in range(len(B))]
    keep = winsorize_mask(B)
    return {"T": T, "B": B, "atrs": atrs, "keep": keep}

# ---------------------------------------------------------------- main
def main():
    out = {"thrust": "gold_sessions_events", "data_notes": {}, "experiments": {}}

    P = {GOLD: prep(GOLD), SILVER: prep(SILVER)}
    for s in (GOLD, SILVER):
        d = P[s]
        out["data_notes"][s] = {
            "h4_bars": len(d["B"]),
            "first": str(d["T"][0]) if d["T"] else None,
            "last": str(d["T"][-1]) if d["T"] else None,
            "winsor_dropped": int(sum(1 for k in d["keep"] if not k)),
        }

    # Common geometry grid (kept small + pre-justified by the established carrier):
    # 0.5*ATR stop = vindicated noise floor; 2R target = carrier target. We also probe
    # 1R and 3R to characterize, but selection is on 2R continuation (carrier-matched).
    MOM_LB = 6          # ~1 trading day of H4 momentum
    STOP_MULT = 0.5
    TARGETS = [1.0, 2.0, 3.0]

    # =========================================================================
    # EXPERIMENT 1: SESSION-BLOCK continuation (gold + silver, deep cross-year)
    # =========================================================================
    sess_scan = {}
    for sym in (GOLD, SILVER):
        d = P[sym]
        sess_scan[sym] = {}
        for sname, hours in SESSIONS.items():
            for tR in TARGETS:
                recs = gen_entries(sym, hours, mom_lb=MOM_LB, stop_mult=STOP_MULT,
                                   target_R=tR, direction_mode="momentum",
                                   B=d["B"], T=d["T"], atrs=d["atrs"], keep=d["keep"])
                tr, fw = split(recs)
                py, ty, pfy, tfy = persistence(recs)
                sess_scan[sym][f"{sname}_{tR:.0f}R"] = {
                    "hours": sorted(hours), "target_R": tR,
                    "train": tr, "fwd": fw,
                    "pos_years": py, "total_years": ty,
                    "pos_fwd_years": pfy, "total_fwd_years": tfy,
                    "per_year": {str(y): v for y, v in per_year(recs).items()},
                }
    out["experiments"]["session_block_continuation"] = sess_scan

    # =========================================================================
    # EXPERIMENT 2: DAY-OF-WEEK conditional continuation (gold + silver, all hours)
    # =========================================================================
    dow_scan = {}
    for sym in (GOLD, SILVER):
        d = P[sym]
        dow_scan[sym] = {}
        for wd, lbl in DOW.items():
            recs = gen_entries(sym, set(SESSIONS["Asia"]) | set(SESSIONS["London"]) | set(SESSIONS["NY"]),
                               mom_lb=MOM_LB, stop_mult=STOP_MULT, target_R=2.0,
                               direction_mode="momentum", dow=wd,
                               B=d["B"], T=d["T"], atrs=d["atrs"], keep=d["keep"])
            tr, fw = split(recs)
            py, ty, pfy, tfy = persistence(recs)
            dow_scan[sym][lbl] = {
                "weekday": wd, "train": tr, "fwd": fw,
                "pos_years": py, "total_years": ty,
                "pos_fwd_years": pfy, "total_fwd_years": tfy,
                "per_year": {str(y): v for y, v in per_year(recs).items()},
            }
    out["experiments"]["day_of_week_continuation"] = dow_scan

    # =========================================================================
    # EXPERIMENT 3: VOLATILITY-EVENT behavior (gold + silver) -- STRICTLY CAUSAL
    # =========================================================================
    # Two causal event definitions (the same-day D1 spike flag is LOOKAHEAD and is
    # NOT used as an entry gate):
    #   (3a) post_spike: enter H4 bars on the day AFTER a completed D1 spike. The flag
    #        is confirmed at the prior day's close, so all next-day entries are causal.
    #        D1 only covers 2022-2026, so this is a 2022-2026 (not deep) test.
    #   (3b) h4_volgate: enter H4 bars where a causal H4 vol-expansion holds at the
    #        entry bar (ATR14(i) >= 1.2*SMA100(ATR14)). This is the established carrier
    #        gate, fully causal, and available across the deep 2015-2026 history.
    #        This is the honest, deep, cross-year test of "trade gold when vol expands".
    event_scan = {}
    SPIKE_THRESH = 1.5  # D1 TR >= 1.5*ATR14(prev) ~ large-news/expansion day
    all_hours = set().union(*SESSIONS.values())
    for sym in (GOLD, SILVER):
        d = P[sym]
        post = post_spike_dates(sym, SPIKE_THRESH)
        spk = d1_spike_dates(sym, SPIKE_THRESH)
        event_scan[sym] = {
            "spike_thresh": SPIKE_THRESH,
            "spike_day_count": len(spk),
            "post_spike_day_count": len(post),
            "d1_coverage_note": "D1 source is 2022-2026 only; post_spike test is 2022-2026",
        }
        # 3a post-spike (causal next-day)
        for mode, lbl in (("on", "post_spike_days"), ("off", "non_post_spike_days")):
            recs = gen_entries(sym, all_hours, mom_lb=MOM_LB, stop_mult=STOP_MULT,
                               target_R=2.0, direction_mode="momentum",
                               spike_dates=post, spike_mode=mode,
                               B=d["B"], T=d["T"], atrs=d["atrs"], keep=d["keep"])
            tr, fw = split(recs)
            py, ty, pfy, tfy = persistence(recs)
            event_scan[sym][lbl] = {
                "train": tr, "fwd": fw, "pos_years": py, "total_years": ty,
                "pos_fwd_years": pfy, "total_fwd_years": tfy,
                "per_year": {str(y): v for y, v in per_year(recs).items()},
            }
        # 3b causal H4 vol-gate (deep) vs ungated baseline
        for vg, lbl in ((True, "h4_volgate"), (False, "ungated_all")):
            recs = gen_entries(sym, all_hours, mom_lb=MOM_LB, stop_mult=STOP_MULT,
                               target_R=2.0, direction_mode="momentum", volgate=vg,
                               B=d["B"], T=d["T"], atrs=d["atrs"], keep=d["keep"])
            tr, fw = split(recs)
            py, ty, pfy, tfy = persistence(recs)
            event_scan[sym][lbl] = {
                "train": tr, "fwd": fw, "pos_years": py, "total_years": ty,
                "pos_fwd_years": pfy, "total_fwd_years": tfy,
                "per_year": {str(y): v for y, v in per_year(recs).items()},
            }
        # 3c causal H4 vol-gate INSIDE each session block (does session add to vol-gate?)
        for sname, hours in SESSIONS.items():
            recs = gen_entries(sym, hours, mom_lb=MOM_LB, stop_mult=STOP_MULT,
                               target_R=2.0, direction_mode="momentum", volgate=True,
                               B=d["B"], T=d["T"], atrs=d["atrs"], keep=d["keep"])
            tr, fw = split(recs)
            py, ty, pfy, tfy = persistence(recs)
            event_scan[sym][f"volgate_{sname}"] = {
                "train": tr, "fwd": fw, "pos_years": py, "total_years": ty,
                "pos_fwd_years": pfy, "total_fwd_years": tfy,
                "per_year": {str(y): v for y, v in per_year(recs).items()},
            }
    out["experiments"]["volatility_event_days"] = event_scan

    # =========================================================================
    # SELECTION: choose the single best config on TRAIN ONLY, gold-first.
    # Candidate pool = all session-block (gold+silver) + dow (gold+silver) + event.
    # Selection metric = TRAIN mean R, with a minimum train n floor.
    # =========================================================================
    MIN_TRAIN_N = 150
    candidates = []  # (key, train_R, fwd_R, recs_meta)
    for sym in (GOLD, SILVER):
        for k, v in sess_scan[sym].items():
            if v["train"]["n"] >= MIN_TRAIN_N:
                candidates.append((f"SESSION:{sym}:{k}", v["train"]["R"], v["fwd"]["R"], v))
        for k, v in dow_scan[sym].items():
            if v["train"]["n"] >= MIN_TRAIN_N:
                candidates.append((f"DOW:{sym}:{k}", v["train"]["R"], v["fwd"]["R"], v))
        for k in ("post_spike_days", "non_post_spike_days", "h4_volgate", "ungated_all",
                  "volgate_Asia", "volgate_London", "volgate_NY"):
            v = event_scan[sym][k]
            if v["train"]["n"] >= MIN_TRAIN_N:
                candidates.append((f"EVENT:{sym}:{k}", v["train"]["R"], v["fwd"]["R"], v))
    candidates.sort(key=lambda x: -x[1])  # by TRAIN R (selection on train only)

    out["selection"] = {
        "metric": "TRAIN mean R (year<=2024), min_train_n=%d" % MIN_TRAIN_N,
        "ranked_top": [
            {"key": k, "train_R": tR, "fwd_R": fR,
             "train_n": v["train"]["n"], "fwd_n": v["fwd"]["n"],
             "pos_years": v["pos_years"], "total_years": v["total_years"],
             "pos_fwd_years": v["pos_fwd_years"], "total_fwd_years": v["total_fwd_years"]}
            for k, tR, fR, v in candidates[:12]
        ],
    }

    # =========================================================================
    # NULLS on the TRAIN-selected winner (re-derive its entries to get dir pool).
    # =========================================================================
    if candidates:
        win_key, win_trainR, win_fwdR, win_v = candidates[0]
        parts = win_key.split(":")
        kind, sym = parts[0], parts[1]
        d = P[sym]
        # rebuild the exact entry set + record realized directions for matched null
        def rebuild(invert=False):
            out_recs = []
            dir_pool = []
            n = len(d["B"]); cost = cost_for(sym)
            T, B, atrs, keep = d["T"], d["B"], d["atrs"], d["keep"]
            wd = None; spike_dates = None; spike_mode = None; volgate = False
            tR = 2.0; hours = set().union(*SESSIONS.values())
            # decode selection
            if kind == "SESSION":
                sname = parts[2].split("_")[0]
                tR = float(parts[2].split("_")[1].replace("R", ""))
                hours = SESSIONS[sname]
            elif kind == "DOW":
                wd = [k for k, lbl in DOW.items() if lbl == parts[2]][0]
            else:  # EVENT
                key = parts[2]
                if key in ("post_spike_days", "non_post_spike_days"):
                    spike_dates = post_spike_dates(sym, SPIKE_THRESH)
                    spike_mode = "on" if key == "post_spike_days" else "off"
                elif key == "h4_volgate":
                    volgate = True
                elif key == "ungated_all":
                    volgate = False
                elif key.startswith("volgate_"):
                    volgate = True
                    hours = SESSIONS[key.split("_", 1)[1]]
            for i in range(60, n-1):
                if keep is not None and not keep[i]:
                    continue
                t = T[i]
                if t.hour not in hours:
                    continue
                if wd is not None and t.weekday() != wd:
                    continue
                if spike_mode == "on" and t.date() not in spike_dates:
                    continue
                if spike_mode == "off" and t.date() in spike_dates:
                    continue
                if volgate and not h4_volgate_mask(B, i):
                    continue
                a = atrs[i]
                if a <= 0:
                    continue
                dd = momentum_dir(B, i, MOM_LB)
                if dd == 0:
                    continue
                dir_pool.append(dd)
                use = -dd if invert else dd
                sd = STOP_MULT * a
                r = simulate(B, i, use, stop_dist=sd, target_dist=tR*sd, cost=cost)
                out_recs.append((t.year, r))
            return out_recs, dir_pool, tR

        actual_recs, dir_pool, winR = rebuild(invert=False)
        inv_recs, _, _ = rebuild(invert=True)
        rand_recs = gen_random_null(sym, len(actual_recs), mom_lb=MOM_LB,
                                    stop_mult=STOP_MULT, target_R=winR,
                                    dir_pool=dir_pool, B=d["B"], T=d["T"],
                                    atrs=d["atrs"], keep=d["keep"])
        a_tr, a_fw = split(actual_recs)
        i_tr, i_fw = split(inv_recs)
        r_tr, r_fw = split(rand_recs)
        out["nulls"] = {
            "winner_key": win_key,
            "actual": {"train": a_tr, "fwd": a_fw,
                       "per_year": {str(y): v for y, v in per_year(actual_recs).items()}},
            "invert": {"train": i_tr, "fwd": i_fw},
            "random_matched": {"train": r_tr, "fwd": r_fw},
            "beats_invert_fwd": a_fw["R"] > i_fw["R"],
            "beats_random_fwd": a_fw["R"] > r_fw["R"],
        }

    # =========================================================================
    # H1 finer-resolution CONFIRMATION probe (2025-06..2026 only, NOT selection).
    # If the chosen session block is real, the same continuation logic at H1 inside
    # those server-hours should not flip sign on the recent OOS window.
    # =========================================================================
    h1_probe = {}
    try:
        Th1, Bh1 = load_h1(GOLD)
        if Bh1:
            atrs1 = [atr14(Bh1, i) for i in range(len(Bh1))]
            keep1 = winsorize_mask(Bh1)
            cost = cost_for(GOLD)
            # map H4 session blocks to H1 hour ranges
            h1_hours = {"Asia": set(range(0, 8)), "London": set(range(8, 16)), "NY": set(range(16, 24))}
            for sname, hrs in h1_hours.items():
                recs = []
                for i in range(60, len(Bh1)-1):
                    if not keep1[i]:
                        continue
                    if Th1[i].hour not in hrs:
                        continue
                    a = atrs1[i]
                    if a <= 0:
                        continue
                    dd = momentum_dir(Bh1, i, 24)  # ~1 day of H1 momentum
                    if dd == 0:
                        continue
                    sd = STOP_MULT * a
                    r = simulate(Bh1, i, dd, stop_dist=sd, target_dist=2.0*sd, cost=cost)
                    recs.append((Th1[i].year, r))
                h1_probe[sname] = {**agg([r for _, r in recs]),
                                   "per_year": {str(y): v for y, v in per_year(recs).items()}}
    except Exception as e:
        h1_probe = {"error": str(e)}
    out["h1_confirmation_probe_2025_2026"] = h1_probe

    # =========================================================================
    # VERDICT (multiple-testing honest): a window is a "bar" only if it passes
    # cross-year persistence AND beats both nulls forward.
    # =========================================================================
    # A window is "persistent" only if: TRAIN R>0 with adequate n, a MAJORITY of all
    # available years are positive, AND BOTH forward years are positive. This is the
    # multiple-testing-honest bar (cross-year persistence, not best-forward).
    def passes(v):
        majority = v["pos_years"] > v["total_years"] / 2.0
        fwd_ok = v["fwd"]["R"] > 0 and v["pos_fwd_years"] == v["total_fwd_years"] and v["total_fwd_years"] >= 2
        return majority and fwd_ok and v["train"]["n"] >= MIN_TRAIN_N and v["train"]["R"] > 0

    EVENT_KEYS = ("post_spike_days", "non_post_spike_days", "h4_volgate", "ungated_all",
                  "volgate_Asia", "volgate_London", "volgate_NY")
    persistent = []
    for sym in (GOLD, SILVER):
        for fam, scan in (("SESSION", sess_scan[sym]), ("DOW", dow_scan[sym])):
            for k, v in scan.items():
                if passes(v):
                    persistent.append({"key": f"{fam}:{sym}:{k}",
                                       "train_R": v["train"]["R"], "train_n": v["train"]["n"],
                                       "fwd_R": v["fwd"]["R"], "fwd_n": v["fwd"]["n"],
                                       "pos_years": v["pos_years"], "total_years": v["total_years"]})
        for k in EVENT_KEYS:
            v = event_scan[sym][k]
            if passes(v):
                persistent.append({"key": f"EVENT:{sym}:{k}",
                                   "train_R": v["train"]["R"], "train_n": v["train"]["n"],
                                   "fwd_R": v["fwd"]["R"], "fwd_n": v["fwd"]["n"],
                                   "pos_years": v["pos_years"], "total_years": v["total_years"]})
    persistent.sort(key=lambda x: -x["fwd_R"])
    out["persistent_windows"] = persistent

    # Carrier comparator: established gated FVG metals edge ~ train +0.06R / fwd +0.09R.
    CARRIER_FWD_R = 0.09
    nulls = out.get("nulls", {})
    win = candidates[0] if candidates else None
    extends = False
    if persistent and nulls.get("beats_invert_fwd") and nulls.get("beats_random_fwd"):
        # the strongest persistent window must also clear the carrier per-trade edge
        # forward to be a genuine extension (adding trades at >= carrier edge).
        extends = persistent[0]["fwd_R"] >= CARRIER_FWD_R
    out["verdict"] = {
        "carrier_fwd_R_comparator": CARRIER_FWD_R,
        "n_persistent_windows": len(persistent),
        "selected_winner": win[0] if win else None,
        "winner_train_R": win[1] if win else None,
        "winner_fwd_R": win[2] if win else None,
        "winner_beats_invert_fwd": nulls.get("beats_invert_fwd"),
        "winner_beats_random_fwd": nulls.get("beats_random_fwd"),
        "extends_or_beats_gold_sleeve": bool(extends),
    }

    with open(EDGE + "/WAVE6_GOLD_SESSIONS_EVENTS_RESULT.json", "w") as f:
        json.dump(out, f, indent=1)

    # ----- console summary -----
    print("\n=================== WAVE6 GOLD SESSIONS & EVENTS ===================")
    for sym in (GOLD, SILVER):
        dn = out["data_notes"][sym]
        print(f"{sym}: {dn['h4_bars']} H4 bars {dn['first']}..{dn['last']} (winsor dropped {dn['winsor_dropped']})")
    print("\n--- SESSION BLOCK continuation (2R) train -> fwd, pos_years ---")
    for sym in (GOLD, SILVER):
        for sname in SESSIONS:
            v = sess_scan[sym][f"{sname}_2R"]
            print(f"  {sym} {sname:7s} train n={v['train']['n']:4d} R={v['train']['R']:+.4f} | "
                  f"fwd n={v['fwd']['n']:4d} R={v['fwd']['R']:+.4f} | "
                  f"pos_yr {v['pos_years']}/{v['total_years']} fwd {v['pos_fwd_years']}/{v['total_fwd_years']}")
    print("\n--- DAY OF WEEK continuation (2R) train -> fwd ---")
    for sym in (GOLD, SILVER):
        for lbl in DOW.values():
            v = dow_scan[sym][lbl]
            print(f"  {sym} {lbl} train n={v['train']['n']:4d} R={v['train']['R']:+.4f} | "
                  f"fwd n={v['fwd']['n']:4d} R={v['fwd']['R']:+.4f} | "
                  f"pos_yr {v['pos_years']}/{v['total_years']}")
    print("\n--- VOLATILITY EVENT (causal: post-spike day & H4 vol-gate, 2R) ---")
    ev_labels = ("post_spike_days", "non_post_spike_days", "h4_volgate", "ungated_all",
                 "volgate_Asia", "volgate_London", "volgate_NY")
    for sym in (GOLD, SILVER):
        es = event_scan[sym]
        for lbl in ev_labels:
            v = es[lbl]
            print(f"  {sym} {lbl:20s} train n={v['train']['n']:5d} R={v['train']['R']:+.4f} | "
                  f"fwd n={v['fwd']['n']:5d} R={v['fwd']['R']:+.4f} | pos_yr {v['pos_years']}/{v['total_years']}")
    print(f"\n  D1 spike day counts (2022-2026): {GOLD}={event_scan[GOLD]['spike_day_count']} "
          f"{SILVER}={event_scan[SILVER]['spike_day_count']}")
    print("\n--- SELECTION (train-only) top 6 ---")
    for c in out["selection"]["ranked_top"][:6]:
        print(f"  {c['key']:34s} train R={c['train_R']:+.4f}(n{c['train_n']}) "
              f"-> fwd R={c['fwd_R']:+.4f}(n{c['fwd_n']}) pos_yr {c['pos_years']}/{c['total_years']}")
    if "nulls" in out:
        nu = out["nulls"]
        print(f"\n--- NULLS on winner {nu['winner_key']} ---")
        print(f"  actual fwd R={nu['actual']['fwd']['R']:+.4f}")
        print(f"  invert fwd R={nu['invert']['fwd']['R']:+.4f}  (beats={nu['beats_invert_fwd']})")
        print(f"  random fwd R={nu['random_matched']['fwd']['R']:+.4f}  (beats={nu['beats_random_fwd']})")
    print("\n--- H1 confirmation probe (2025-06..2026, NOT selection) ---")
    if isinstance(h1_probe, dict) and "error" not in h1_probe:
        for sname, v in h1_probe.items():
            print(f"  {sname:7s} n={v['n']:5d} R={v['R']:+.4f} win={v['win']:.1f}%")
    print(f"\n--- PERSISTENT windows passing cross-year + fwd test: {len(persistent)} ---")
    for p in persistent[:10]:
        print(f"  {p['key']:34s} train R={p['train_R']:+.4f}(n{p['train_n']}) "
              f"fwd R={p['fwd_R']:+.4f}(n{p['fwd_n']}) pos_yr {p['pos_years']}/{p['total_years']}")
    v = out["verdict"]
    print("\n=================== VERDICT ===================")
    print(f"  carrier fwd-R comparator: {v['carrier_fwd_R_comparator']:+.4f}")
    print(f"  persistent windows: {v['n_persistent_windows']}")
    print(f"  EXTENDS/BEATS gold sleeve: {v['extends_or_beats_gold_sleeve']}")
    print("\nWROTE WAVE6_GOLD_SESSIONS_EVENTS_RESULT.json")


if __name__ == "__main__":
    main()
