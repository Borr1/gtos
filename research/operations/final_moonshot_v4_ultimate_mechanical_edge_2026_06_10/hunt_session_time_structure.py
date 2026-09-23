"""HUNT: session_time_structure — forward-stable entry edge from session/time-of-day structure.

Signal class: London/NY/Asia session windows, hour-of-day (H4 bar bucket) and
day-of-week conditional drift, opening-range / Asia-range breakouts.

Data: H4 bars 2022-2026, ~46 symbols. Only 6 bars/day (server hours 0,4,8,12,16,20).
Volume-inferred session map (server time): peak volume at 16:00 bar = NY session,
8:00/12:00 = London, 0:00/4:00 = Asia/overnight, 20:00 = NY-PM/Asia-pre.

Discipline:
  TRAIN 2022-2024 / FORWARD 2025-2026. Report per-trade R, win%, per-year, by
  asset_class, separately long & short. Bar = POSITIVE & STABLE IN FORWARD.

MANDATORY: all fills via tested geometry_lib.simulate (no hand-rolled stop/target).
"""
from __future__ import annotations
import csv, datetime, json, sys
from collections import defaultdict

REPO = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
HUNT_DIR = REPO + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
DATA = REPO + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0, REPO)
sys.path.insert(0, HUNT_DIR)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL  # noqa
from geometry_lib import Bar, atr14, simulate  # noqa

COST = json.load(open(HUNT_DIR + "/ULTIMATE_REAL_COST_MAP.json"))

# ---- load ------------------------------------------------------------------
def load(sym):
    bars, times = [], []
    with open(f"{DATA}/{sym}_H4.csv") as f:
        for row in csv.DictReader(f):
            t = datetime.datetime.fromisoformat(row["time"])
            bars.append(Bar(float(row["open"]), float(row["high"]), float(row["low"]),
                            float(row["close"]), float(row["volume"])))
            times.append(t)
    return bars, times

SYMBOLS = sorted(ASSET_CLASS_BY_SYMBOL.keys())
DATASETS = {}
for s in SYMBOLS:
    try:
        DATASETS[s] = load(s)
    except FileNotFoundError:
        pass

def cost_for(sym):
    return COST.get(ASSET_CLASS_BY_SYMBOL[sym], COST["_global_median"])

def in_train(t):    return t.year <= 2024
def in_forward(t):  return t.year >= 2025

# ---- stats helpers ---------------------------------------------------------
def agg(rs):
    n = len(rs)
    if n == 0: return dict(n=0, R=0.0, win=0.0, tot=0.0)
    tot = sum(rs); wins = sum(1 for r in rs if r > 0)
    return dict(n=n, R=round(tot/n, 4), win=round(100*wins/n, 1), tot=round(tot, 1))

def split_stats(trades):
    """trades: list of (year, asset_class, direction, R). Returns nested report."""
    tr = [t for t in trades if t[0] <= 2024]
    fw = [t for t in trades if t[0] >= 2025]
    def block(ts):
        out = {"ALL": agg([r for *_, r in ts])}
        for d, lbl in ((1, "LONG"), (-1, "SHORT")):
            out[lbl] = agg([r for _, _, dr, r in ts if dr == d])
        by_ac = defaultdict(list)
        for _, ac, _, r in ts: by_ac[ac].append(r)
        out["by_class"] = {ac: agg(v) for ac, v in sorted(by_ac.items())}
        by_yr = defaultdict(list)
        for y, _, _, r in ts: by_yr[y].append(r)
        out["by_year"] = {y: agg(v) for y, v in sorted(by_yr.items())}
        return out
    return {"TRAIN": block(tr), "FORWARD": block(fw)}

def per_year_fw(trades):
    by_yr = defaultdict(list)
    for y, _, _, r in trades:
        if y >= 2025: by_yr[y].append(r)
    return {str(y): agg(v) for y, v in sorted(by_yr.items())}

# ============================================================================
# EXPLORATION: raw next-bar drift by (bar-bucket, dow) per asset class.
# This is a directional scan (close-to-close next bar, in ATR units, net cost)
# to find which time windows have a persistent directional tilt. NOT the final
# fill sim — just a landscape probe to pick entry windows.
# ============================================================================
def explore():
    # bucket -> {train:[atr-return], fwd:[...]} for raw next-bar move (signed long bias)
    # We compute per-class average next-bar return (close[i+1]-close[i])/atr14, by bar hour.
    by = defaultdict(lambda: {"train": [], "fwd": []})
    by_dow = defaultdict(lambda: {"train": [], "fwd": []})
    for sym, (bars, times) in DATASETS.items():
        ac = ASSET_CLASS_BY_SYMBOL[sym]
        for i in range(14, len(bars) - 1):
            a = atr14(bars, i)
            if a <= 0: continue
            ret = (bars[i+1].c - bars[i].c) / a   # next-bar close move in ATR units
            t = times[i]
            seg = "train" if t.year <= 2024 else "fwd"
            by[(ac, t.hour)][seg].append(ret)
            by_dow[(ac, t.weekday())][seg].append(ret)
    print("\n=== NEXT-BAR DRIFT by (asset_class, server-hour) [mean ATR-return, n] ===")
    print("(positive => long bias on entry at that bar's close)")
    cur = None
    for (ac, h) in sorted(by):
        if ac != cur:
            print(f"\n-- {ac} --"); cur = ac
        tr = by[(ac, h)]["train"]; fw = by[(ac, h)]["fwd"]
        mt = sum(tr)/len(tr) if tr else 0; mf = sum(fw)/len(fw) if fw else 0
        flag = "  <== SAME-SIGN STABLE" if tr and fw and (mt>0)==(mf>0) and abs(mt)>0.01 and abs(mf)>0.01 else ""
        print(f"  h{h:02d}: train {mt:+.4f} (n={len(tr):5d})   fwd {mf:+.4f} (n={len(fw):5d}){flag}")
    print("\n=== NEXT-BAR DRIFT by (asset_class, day-of-week 0=Mon) ===")
    cur=None
    for (ac, d) in sorted(by_dow):
        if ac != cur:
            print(f"\n-- {ac} --"); cur = ac
        tr = by_dow[(ac, d)]["train"]; fw = by_dow[(ac, d)]["fwd"]
        mt = sum(tr)/len(tr) if tr else 0; mf = sum(fw)/len(fw) if fw else 0
        flag = "  <== SAME-SIGN STABLE" if tr and fw and (mt>0)==(mf>0) and abs(mt)>0.01 and abs(mf)>0.01 else ""
        print(f"  dow{d}: train {mt:+.4f} (n={len(tr):5d})   fwd {mf:+.4f} (n={len(fw):5d}){flag}")

if __name__ == "__main__":
    import sys as _s
    if len(_s.argv) > 1 and _s.argv[1] == "explore":
        explore()

# ============================================================================
# BACKTEST ENGINE — real fills via geometry_lib.simulate
# ============================================================================
def run_window(entry_hours, direction, *, classes=None, symbols=None,
               stop_mult=0.5, target_mult=2.0, trail=None, dow=None,
               regime=None, maxbars=80):
    """Enter at close of every bar whose server-hour in entry_hours.
    direction: +1 long / -1 short.
    trail: (arm_mult, gap_mult) overrides target if set.
    regime: optional callable(bars,i,times)->bool gate (e.g. trend filter).
    Returns list of (year, asset_class, direction, R)."""
    trades = []
    syms = symbols if symbols else SYMBOLS
    for sym in syms:
        if sym not in DATASETS: continue
        ac = ASSET_CLASS_BY_SYMBOL[sym]
        if classes and ac not in classes: continue
        bars, times = DATASETS[sym]
        c = cost_for(sym)
        for i in range(14, len(bars) - 1):
            t = times[i]
            if t.hour not in entry_hours: continue
            if dow is not None and t.weekday() not in dow: continue
            a = atr14(bars, i)
            if a <= 0: continue
            if regime is not None and not regime(bars, i, times): continue
            sd = stop_mult * a
            if trail:
                R = simulate(bars, i, direction, stop_dist=sd,
                             trail_arm=trail[0]*sd, trail_gap=trail[1]*sd,
                             maxbars=maxbars, cost=c)
            else:
                R = simulate(bars, i, direction, stop_dist=sd,
                             target_dist=target_mult*a, maxbars=maxbars, cost=c)
            trades.append((t.year, ac, direction, R))
    return trades

def fmt(report, title):
    print(f"\n########## {title} ##########")
    for seg in ("TRAIN", "FORWARD"):
        b = report[seg]
        print(f"  [{seg}] ALL  n={b['ALL']['n']:5d}  R={b['ALL']['R']:+.4f}  win={b['ALL']['win']:.1f}%  tot={b['ALL']['tot']:+.1f}")
        print(f"         LONG n={b['LONG']['n']:5d} R={b['LONG']['R']:+.4f} | SHORT n={b['SHORT']['n']:5d} R={b['SHORT']['R']:+.4f}")
        ys = "  ".join(f"{y}:{v['R']:+.3f}(n{v['n']})" for y, v in b["by_year"].items())
        print(f"         years: {ys}")
        cs = "  ".join(f"{ac}:{v['R']:+.3f}(n{v['n']})" for ac, v in b["by_class"].items())
        print(f"         class: {cs}")

# ============================================================================
# SCAN — probe candidate (class, hour, direction, geometry) combos
# ============================================================================
def scan_basic():
    """Full grid: each class x each entry-hour x each direction, fixed 0.5/2.0 ATR.
    Surfaces every same-direction window that is forward-positive."""
    print("\n##### GRID SCAN: class x hour x direction (stop 0.5ATR, target 2.0ATR) #####")
    print("Looking for FORWARD per-trade R > 0 that also has TRAIN R > 0 (stable).\n")
    rows = []
    for ac in sorted(set(ASSET_CLASS_BY_SYMBOL.values())):
        for h in (0, 4, 8, 12, 16, 20):
            for d in (1, -1):
                tr = run_window([h], d, classes={ac}, target_mult=2.0)
                rep = split_stats(tr)
                T = rep["TRAIN"]["ALL"]; F = rep["FORWARD"]["ALL"]
                rows.append((ac, h, d, T, F))
    # print stable forward-positive ones
    print(f"{'class':8s} {'h':>3s} {'dir':>4s} | {'TRAIN R':>9s} {'tr n':>6s} {'tr win':>6s} | {'FWD R':>9s} {'fw n':>6s} {'fw win':>6s}  flag")
    for ac, h, d, T, F in rows:
        stable = T["R"] > 0 and F["R"] > 0 and F["n"] >= 60
        strong = stable and F["R"] > 0.03
        flag = "STRONG" if strong else ("stable" if stable else "")
        if T["R"] > 0 and F["R"] > -0.05:  # only print the interesting half
            ds = "L" if d == 1 else "S"
            print(f"{ac:8s} {h:3d} {ds:>4s} | {T['R']:+9.4f} {T['n']:6d} {T['win']:6.1f} | {F['R']:+9.4f} {F['n']:6d} {F['win']:6.1f}  {flag}")

if __name__ == "__main__":
    import sys as _s
    mode = _s.argv[1] if len(_s.argv) > 1 else "scan"
    if mode == "explore":
        explore()
    elif mode == "scan":
        scan_basic()

# ============================================================================
# REFINE — baseline comparison + geometry variants for top candidates
# ============================================================================
def refine():
    print("\n##### BASELINE: does the SESSION-HOUR beat all-hours (is it real time-structure)? #####")
    # metals long: all hours vs best hours
    for label, hrs in (("metals ALL-hours L", [0,4,8,12,16,20]),
                       ("metals h16+h20 L", [16,20]),
                       ("metals h20 only L", [20]),
                       ("metals h0+h4 L (overnight)", [0,4])):
        tr = run_window(hrs, 1, classes={"metals"}, target_mult=2.0)
        fmt(split_stats(tr), label)

    print("\n##### crypto h4 SHORT robustness + nearby hours #####")
    for label, hrs in (("crypto ALL-hours S", [0,4,8,12,16,20]),
                       ("crypto h4 S", [4]),
                       ("crypto h4+h8 S", [4,8])):
        tr = run_window(hrs, -1, classes={"crypto"}, target_mult=2.0)
        fmt(split_stats(tr), label)

    print("\n##### index h20 LONG + energy NY long #####")
    fmt(split_stats(run_window([20], 1, classes={"index"}, target_mult=2.0)), "index h20 L")
    fmt(split_stats(run_window([16,20], 1, classes={"energy"}, target_mult=2.0)), "energy h16+h20 L (low train n!)")

    print("\n##### jpy_fx NY-session long (h16) + overnight (h0,h4) #####")
    fmt(split_stats(run_window([16], 1, classes={"jpy_fx"}, target_mult=2.0)), "jpy_fx h16 L (NY)")
    fmt(split_stats(run_window([0,4], 1, classes={"jpy_fx"}, target_mult=2.0)), "jpy_fx h0+h4 L (overnight)")

    print("\n##### GEOMETRY VARIANTS on metals h16+h20 LONG #####")
    for tm in (1.0, 1.5, 2.0):
        fmt(split_stats(run_window([16,20], 1, classes={"metals"}, target_mult=tm)),
            f"metals h16+h20 L  target={tm}ATR (stop 0.5)")
    for arm, gap in ((2,1), (3,1.5)):
        fmt(split_stats(run_window([16,20], 1, classes={"metals"}, trail=(arm,gap))),
            f"metals h16+h20 L  trail arm={arm} gap={gap}")

if __name__ == "__main__":
    import sys as _s
    mode = _s.argv[1] if len(_s.argv) > 1 else "scan"
    if mode == "explore": explore()
    elif mode == "scan": scan_basic()
    elif mode == "refine": refine()

# ============================================================================
# STRESS — per-symbol breakdown + regime filters for the metals NY-long winner
# ============================================================================
def per_symbol(hrs, direction, classes, target_mult=2.0, trail=None):
    print(f"\n----- PER-SYMBOL  hrs={hrs} dir={direction} classes={classes} tgt={target_mult} -----")
    print(f"{'sym':10s} | {'TR n':>5s} {'TR R':>8s} | {'FW n':>5s} {'FW R':>8s} {'FW win':>6s} | {'25 R':>7s} {'26 R':>7s}")
    for sym in sorted(s for s in SYMBOLS if ASSET_CLASS_BY_SYMBOL[s] in classes and s in DATASETS):
        tr = run_window(hrs, direction, symbols=[sym], target_mult=target_mult, trail=trail)
        rep = split_stats(tr)
        T = rep["TRAIN"]["ALL"]; F = rep["FORWARD"]["ALL"]
        yr = rep["FORWARD"]["by_year"]
        r25 = yr.get(2025, {}).get("R", 0.0); r26 = yr.get(2026, {}).get("R", 0.0)
        print(f"{sym:10s} | {T['n']:5d} {T['R']:+8.4f} | {F['n']:5d} {F['R']:+8.4f} {F['win']:6.1f} | {r25:+7.3f} {r26:+7.3f}")

def trend_gate(up=True, lookback=10):
    """Gate: only take long if close[i] > close[i-lookback] (i.e. in uptrend)."""
    def g(bars, i, times):
        if i < lookback: return False
        return (bars[i].c > bars[i-lookback].c) if up else (bars[i].c < bars[i-lookback].c)
    return g

def stress():
    print("\n========== STRESS TEST: metals NY-session (h16+h20) LONG, target 2.0ATR ==========")
    per_symbol([16,20], 1, {"metals"}, 2.0)

    print("\n========== Compare: also test metals h20-only and h12+h16+h20 (broader NY) ==========")
    for hrs in ([20], [16,20], [12,16,20]):
        fmt(split_stats(run_window(hrs, 1, classes={"metals"}, target_mult=2.0)),
            f"metals {hrs} L tgt2.0")

    print("\n========== REGIME: metals h16+h20 L with uptrend gate (close>close[-10]) ==========")
    fmt(split_stats(run_window([16,20], 1, classes={"metals"}, target_mult=2.0,
                               regime=trend_gate(up=True, lookback=10))),
        "metals h16+h20 L tgt2.0 + uptrend10 gate")
    fmt(split_stats(run_window([16,20], 1, classes={"metals"}, target_mult=2.0,
                               regime=trend_gate(up=True, lookback=6))),
        "metals h16+h20 L tgt2.0 + uptrend6 gate")

    print("\n========== crypto h4 SHORT per-symbol (stable-in-train check) ==========")
    per_symbol([4], -1, {"crypto"}, 2.0)

if __name__ == "__main__":
    import sys as _s
    mode = _s.argv[1] if len(_s.argv) > 1 else "scan"
    if mode == "explore": explore()
    elif mode == "scan": scan_basic()
    elif mode == "refine": refine()
    elif mode == "stress": stress()

# ============================================================================
# FINAL — lock the winner, full report + sanity comparators, write JSON
# ============================================================================
WINNER = dict(
    name="metals_NY_session_long_uptrend_gated",
    desc="LONG metals at close of NY-session H4 bars (server-hour 16:00 & 20:00) "
         "when close>close[-10] (uptrend). stop=0.5*ATR14, target=2.0*ATR14.",
    entry_hours=[16, 20], direction=1, classes=["metals"],
    stop_mult=0.5, target_mult=2.0, lookback=10,
)

def final():
    print("\n=================== WINNER CONFIG ===================")
    print(json.dumps(WINNER, indent=2))
    tr = run_window(WINNER["entry_hours"], 1, classes=set(WINNER["classes"]),
                    stop_mult=0.5, target_mult=2.0,
                    regime=trend_gate(up=True, lookback=WINNER["lookback"]))
    rep = split_stats(tr)
    fmt(rep, WINNER["name"])

    print("\n=================== COMPARATORS (is the structure real?) ===================")
    # ungated metals NY
    fmt(split_stats(run_window([16,20], 1, classes={"metals"}, target_mult=2.0)),
        "COMPARATOR ungated metals NY-long")
    # metals NON-NY hours, gated (should be weaker if NY window matters)
    fmt(split_stats(run_window([0,4,8], 1, classes={"metals"}, target_mult=2.0,
                               regime=trend_gate(up=True, lookback=10))),
        "COMPARATOR metals NON-NY (h0,4,8) long gated")
    # same recipe on ALL classes (should NOT be as good -> proves metals-specific)
    fmt(split_stats(run_window([16,20], 1, target_mult=2.0,
                               regime=trend_gate(up=True, lookback=10))),
        "COMPARATOR all-classes NY-long gated")

    # write machine-readable result
    out = {
        "winner": WINNER,
        "report": rep,
        "forward_per_year": per_year_fw(tr),
        "inferred_session_map": {
            "server_hours_present": [0,4,8,12,16,20],
            "note": "volume peaks at 16:00 server bar (NY). 16:00 & 20:00 bars = NY session.",
        },
    }
    with open(HUNT_DIR + "/hunt_session_time_structure_RESULT.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\nwrote hunt_session_time_structure_RESULT.json")

if __name__ == "__main__":
    import sys as _s
    mode = _s.argv[1] if len(_s.argv) > 1 else "scan"
    if mode == "explore": explore()
    elif mode == "scan": scan_basic()
    elif mode == "refine": refine()
    elif mode == "stress": stress()
    elif mode == "final": final()
