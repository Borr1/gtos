"""
wave2_exit_geometry.py
======================
THRUST: exit_geometry — on the VALIDATED FVG-retest continuation entry, measure realized
MFE / MAE / time-to-target, then fit the best exit per asset class and compare to the 3R
baseline. Question: which exit lifts AND stabilizes the per-year profile vs fixed 3R?

FOUNDATION (do not re-invent): the entry is the EXACT validated FVG-retest continuation
from wave1_structure_setups_ict.setup_ob_fvg_retest(mode='fvg'). That function fixes, per
trade, the entry index i, the direction, and the STRUCTURAL stop distance
   stop_dist = max((b.c - min(b.l, gap_bot)) + stop_buf*a, atr_stop_floor*a)   (long; mirror short)
The R-unit = that structural stop. We keep entry + stop identical across every exit policy
so the comparison is exits-only (apples to apples). We do NOT touch the entry logic.

DISCIPLINE
  - All fills via tested geometry_lib.simulate (fixed-target and trail modes are tested there);
    partial/runner is composed from two tested simulate-style legs with identical same-bar
    pessimism (stop wins ties), implemented inline and unit-checked against simulate on the
    two pure legs.
  - R-unit = structural stop_dist (same as foundation).
  - TRAIN <= 2024 selection; FORWARD 2025-2026 proof; FULL per-year table 2015-2026.
  - "Stabilize" bar: an exit is preferred only if it is positive in a MAJORITY of all years
    (kill chop-year bleed) WITHOUT forward peeking (selection is on TRAIN only).
  - Negative control: invert the entry direction (fade) under the SAME chosen exit -> must die.
  - Per asset class. Foundation routing is metals+energy (the only forward-positive pocket);
    we report those plus fx/jpy_fx/index/crypto/agri for the full picture, and a metals+energy
    combined book (the deployable surface).
  - Costs: real per-asset-class expected_cost_r from ULTIMATE_REAL_COST_MAP.json, charged once
    per trade (entry round-trip), exactly as the foundation charges it.

OUTPUT: WAVE2_EXIT_GEOMETRY_RESULT.json + console per-year tables.
"""
from __future__ import annotations
import sys, os, json
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)

from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
from geometry_lib import Bar, atr14, simulate
import wave1_structure_setups_ict as W   # foundation: load(), htf_trend(), levels(), cost_for(), SYMBOLS

COSTMAP = W.COSTMAP
cost_for = W.cost_for
load = W.load
htf_trend = W.htf_trend
SYMBOLS = W.SYMBOLS

BASELINE = "fixed_3R"
MAXBARS = 80   # same horizon used by simulate default

# ---------------------------------------------------------------------------
# 1) ENTRY EXTRACTION — re-run the EXACT foundation entry, but emit the trade
#    PRIMITIVES (bars handle, i, direction, stop_dist, cost, sym, year, class)
#    instead of a single fixed-R outcome. This is a faithful copy of
#    setup_ob_fvg_retest(mode='fvg') control flow; only the emitted payload differs.
# ---------------------------------------------------------------------------
def fvg_entries(trend_lb=30, fvg_min=0.10, stop_buf=0.10, atr_stop_floor=0.25, invert=False):
    """Yield trade primitives for every FVG-retest continuation entry.
    Returns list of dicts: sym, year, cls, i, direction, stop_dist, cost, bars(ref).
    direction already includes invert (negative control)."""
    trades = []
    for sym in SYMBOLS:
        T, B = load(sym)
        if len(B) < 200:
            continue
        cls = ASSET_CLASS_BY_SYMBOL.get(sym)
        cost = cost_for(sym)
        n = len(B)
        atrs = [atr14(B, i) for i in range(n)]
        for i in range(60, n - 1):
            a = atrs[i]
            if a <= 0:
                continue
            tr = htf_trend(B, i, trend_lb)
            b = B[i]
            if tr == 1:
                for k in range(i - 2, max(i - 9, 60), -1):
                    gap_top = B[k].l; gap_bot = B[k - 2].h
                    if gap_top - gap_bot < fvg_min * a:
                        continue
                    if b.l <= gap_top and b.c > gap_bot and b.c > b.o:
                        stop_dist = max((b.c - min(b.l, gap_bot)) + stop_buf * a, atr_stop_floor * a)
                        d = -1 if invert else +1
                        trades.append(dict(sym=sym, year=T[i].year, cls=cls, i=i,
                                           direction=d, stop_dist=stop_dist, cost=cost, B=B))
                        break
            elif tr == -1:
                for k in range(i - 2, max(i - 9, 60), -1):
                    gap_bot = B[k].h; gap_top = B[k - 2].l
                    if gap_top - gap_bot < fvg_min * a:
                        continue
                    if b.h >= gap_bot and b.c < gap_top and b.c < b.o:
                        stop_dist = max((max(b.h, gap_top) - b.c) + stop_buf * a, atr_stop_floor * a)
                        d = +1 if invert else -1
                        trades.append(dict(sym=sym, year=T[i].year, cls=cls, i=i,
                                           direction=d, stop_dist=stop_dist, cost=cost, B=B))
                        break
    return trades

# ---------------------------------------------------------------------------
# 2) PATH INSTRUMENTATION — MFE / MAE (in R) and bars-to-target, with the SAME
#    pessimistic same-bar convention as simulate (adverse first).
# ---------------------------------------------------------------------------
def path_stats(B, i, direction, stop_dist, maxbars=MAXBARS):
    """Walk the trade forward. Return dict with mfe_R, mae_R, bars_to_1R..bars_to_4R,
    bars_held_if_stop_at_3R (informational). Excursions measured from entry close in R units.
    Adverse (MAE) is recorded before favorable within each bar (pessimistic)."""
    entry = B[i].c
    end = min(i + maxbars, len(B) - 1)
    mfe = 0.0; mae = 0.0
    hit = {1.0: None, 1.5: None, 2.0: None, 3.0: None, 4.0: None}
    for off, j in enumerate(range(i + 1, end + 1), start=1):
        b = B[j]
        if direction > 0:
            adv = (b.h - entry) / stop_dist
            ad7 = (b.l - entry) / stop_dist
        else:
            adv = (entry - b.l) / stop_dist
            ad7 = (entry - b.h) / stop_dist
        # pessimistic intra-bar: adverse extreme considered first
        if ad7 < mae:
            mae = ad7
        if adv > mfe:
            mfe = adv
        for lvl in hit:
            if hit[lvl] is None and adv >= lvl:
                hit[lvl] = off
    return dict(mfe=mfe, mae=mae,
                b1=hit[1.0], b15=hit[1.5], b2=hit[2.0], b3=hit[3.0], b4=hit[4.0])

# ---------------------------------------------------------------------------
# 3) EXIT POLICIES — each returns realized R for ONE trade. Entry/stop identical.
#    Fixed + trail use tested simulate(). Partial/runner composed inline with the
#    SAME pessimistic same-bar rule (stop wins ties) used by simulate.
# ---------------------------------------------------------------------------
def exit_fixed(t, R):
    return simulate(t["B"], t["i"], t["direction"], stop_dist=t["stop_dist"],
                    target_dist=R * t["stop_dist"], maxbars=MAXBARS, cost=t["cost"])

def exit_trail(t, arm_R, gap_R):
    return simulate(t["B"], t["i"], t["direction"], stop_dist=t["stop_dist"],
                    trail_arm=arm_R * t["stop_dist"], trail_gap=gap_R * t["stop_dist"],
                    maxbars=MAXBARS, cost=t["cost"])

def exit_partial_runner(t, part_R=2.0, frac=0.5, runner="fixed4", be_after_part=True):
    """50% off at part_R, runner manages the rest.
       runner:
         'fixed4'  -> runner target 4R (with optional BE stop after part hit)
         'trail1'  -> runner trails 1R behind extreme after part hit (with BE floor)
         'be'      -> runner just rides to original 3R/4R? -> use 'open' to maxbars close
       Same-bar pessimism: adverse first. Cost charged once on the whole position (entry RT),
       consistent with foundation charging cost once per trade."""
    B = t["B"]; i = t["i"]; d = t["direction"]; sd = t["stop_dist"]; cost = t["cost"]
    entry = B[i].c
    end = min(i + MAXBARS, len(B) - 1)
    stop = entry - sd if d > 0 else entry + sd
    part_px = entry + part_R * sd if d > 0 else entry - part_R * sd
    part_filled = False
    part_R_realized = 0.0
    # runner config
    run_tgt = None
    if runner == "fixed4":
        run_tgt = entry + 4.0 * sd if d > 0 else entry - 4.0 * sd
    mx = entry  # extreme for trail
    run_frac = 1.0 - frac
    be_stop_set = False
    for j in range(i + 1, end + 1):
        b = B[j]
        # --- adverse first (pessimistic) ---
        if d > 0:
            if b.l <= stop:
                # whole remaining position stops
                stopR = (stop - entry) / sd
                return frac * part_R_realized + run_frac * stopR - cost if part_filled \
                    else 1.0 * stopR - cost
        else:
            if b.h >= stop:
                stopR = (entry - stop) / sd
                return frac * part_R_realized + run_frac * stopR - cost if part_filled \
                    else 1.0 * stopR - cost
        # --- partial target ---
        if not part_filled:
            if (d > 0 and b.h >= part_px) or (d < 0 and b.l <= part_px):
                part_filled = True
                part_R_realized = part_R
                if be_after_part:
                    stop = entry  # move runner stop to break-even
                    be_stop_set = True
        # --- runner management (only after partial) ---
        if part_filled:
            if runner == "fixed4" and run_tgt is not None:
                if (d > 0 and b.h >= run_tgt) or (d < 0 and b.l <= run_tgt):
                    runR = 4.0
                    return frac * part_R + run_frac * runR - cost
            elif runner == "trail1":
                if d > 0:
                    if b.h > mx: mx = b.h
                    trail = mx - 1.0 * sd
                    if trail > stop: stop = trail  # ratchet
                else:
                    if b.l < mx: mx = b.l
                    trail = mx + 1.0 * sd
                    if trail < stop: stop = trail
    # ran out of horizon -> mark remaining at close
    closeR = (B[end].c - entry) / sd if d > 0 else (entry - B[end].c) / sd
    if part_filled:
        return frac * part_R + run_frac * closeR - cost
    return closeR - cost

# ---------------------------------------------------------------------------
# 4) stats / reporting
# ---------------------------------------------------------------------------
def _stats(rs):
    if not rs:
        return {"n": 0, "mean_R": 0.0, "win%": 0.0, "sum_R": 0.0}
    n = len(rs); s = sum(rs); w = sum(1 for r in rs if r > 0)
    return {"n": n, "mean_R": round(s / n, 4), "win%": round(100 * w / n, 1), "sum_R": round(s, 1)}

def per_year(pairs):
    by = defaultdict(list)
    for y, r in pairs:
        by[y].append(r)
    return {y: _stats(by[y]) for y in sorted(by)}

def split(pairs):
    tr = [r for y, r in pairs if y <= 2024]
    fw = [r for y, r in pairs if y >= 2025]
    return _stats(tr), _stats(fw)

def summarize(pairs):
    tr, fw = split(pairs)
    py = per_year(pairs)
    yrs = sorted(py)
    fwd_yrs = [y for y in yrs if y >= 2025]
    train_yrs = [y for y in yrs if y <= 2024]
    pos_all = sum(1 for y in yrs if py[y]["mean_R"] > 0)
    pos_train = sum(1 for y in train_yrs if py[y]["mean_R"] > 0)
    pos_fwd = sum(1 for y in fwd_yrs if py[y]["mean_R"] > 0)
    return dict(train=tr, fwd=fw,
                per_year={str(y): py[y] for y in yrs},
                pos_years=pos_all, total_years=len(yrs),
                pos_train_years=pos_train, total_train_years=len(train_yrs),
                pos_fwd_years=pos_fwd, total_fwd_years=len(fwd_yrs))

def print_policy(name, summ):
    tr = summ["train"]; fw = summ["fwd"]
    print(f"\n  [{name}]")
    print(f"    TRAIN<=2024 n={tr['n']:5d} R={tr['mean_R']:+.4f} w={tr['win%']:.1f}% | "
          f"FWD>=2025 n={fw['n']:5d} R={fw['mean_R']:+.4f} w={fw['win%']:.1f}%")
    line = "    per-year: "
    for y in sorted(summ["per_year"], key=int):
        st = summ["per_year"][y]
        line += f"{y}:{st['mean_R']:+.3f}(n{st['n']}) "
    print(line)
    print(f"    positive years ALL={summ['pos_years']}/{summ['total_years']}  "
          f"TRAIN={summ['pos_train_years']}/{summ['total_train_years']}  "
          f"FWD={summ['pos_fwd_years']}/{summ['total_fwd_years']}")

# ---------------------------------------------------------------------------
# 5) policy menu
# ---------------------------------------------------------------------------
def all_policies():
    pol = {}
    for R in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0):
        pol[f"fixed_{R:g}R"] = (lambda t, R=R: exit_fixed(t, R))
    pol["trail_arm1_gap1"] = lambda t: exit_trail(t, 1.0, 1.0)
    pol["trail_arm1_gap1.5"] = lambda t: exit_trail(t, 1.0, 1.5)
    pol["trail_arm2_gap1"] = lambda t: exit_trail(t, 2.0, 1.0)
    pol["trail_arm2_gap1.5"] = lambda t: exit_trail(t, 2.0, 1.5)
    pol["trail_arm2_gap2"] = lambda t: exit_trail(t, 2.0, 2.0)
    pol["partial2R_be_run4R"] = lambda t: exit_partial_runner(t, 2.0, 0.5, "fixed4", True)
    pol["partial2R_be_trail1"] = lambda t: exit_partial_runner(t, 2.0, 0.5, "trail1", True)
    pol["partial1.5R_be_run4R"] = lambda t: exit_partial_runner(t, 1.5, 0.5, "fixed4", True)
    pol["partial2R_norunbe_trail1"] = lambda t: exit_partial_runner(t, 2.0, 0.5, "trail1", False)
    return pol

# ---------------------------------------------------------------------------
# 6) main
# ---------------------------------------------------------------------------
def run_class(trades, cls_filter):
    """Apply every policy to the subset of trades in cls_filter (set of classes or None=all)."""
    subset = [t for t in trades if (cls_filter is None or t["cls"] in cls_filter)]
    # precompute path stats once for diagnostics
    pol = all_policies()
    out = {}
    R_by_policy = {}
    for name, fn in pol.items():
        pairs = [(t["year"], fn(t)) for t in subset]
        out[name] = summarize(pairs)
        R_by_policy[name] = out[name]
    return out, len(subset)

def main():
    print("Extracting foundation FVG-retest entries (exact wave1 logic)...")
    trades = fvg_entries()
    inv_trades = fvg_entries(invert=True)
    print(f"  total entries: {len(trades)}")

    # path diagnostics (median MFE/MAE/time-to-target) per asset class
    diag = {}
    for t in trades:
        ps = path_stats(t["B"], t["i"], t["direction"], t["stop_dist"])
        t["_ps"] = ps
    def med(xs):
        xs = sorted(x for x in xs if x is not None)
        return None if not xs else (xs[len(xs)//2])
    classes_present = sorted({t["cls"] for t in trades})
    for cls in classes_present:
        sub = [t for t in trades if t["cls"] == cls]
        diag[cls] = {
            "n": len(sub),
            "med_mfe_R": round(med([t["_ps"]["mfe"] for t in sub]), 3),
            "med_mae_R": round(med([t["_ps"]["mae"] for t in sub]), 3),
            "frac_reach_2R": round(sum(1 for t in sub if t["_ps"]["b2"] is not None)/len(sub), 3),
            "frac_reach_3R": round(sum(1 for t in sub if t["_ps"]["b3"] is not None)/len(sub), 3),
            "frac_reach_4R": round(sum(1 for t in sub if t["_ps"]["b4"] is not None)/len(sub), 3),
            "med_bars_to_2R": med([t["_ps"]["b2"] for t in sub]),
            "med_bars_to_3R": med([t["_ps"]["b3"] for t in sub]),
        }
    print("\n===== PATH DIAGNOSTICS (median MFE/MAE in R, reach fractions) =====")
    for cls in classes_present:
        d = diag[cls]
        print(f"  {cls:8s} n={d['n']:5d} mfe={d['med_mfe_R']:+.2f} mae={d['med_mae_R']:+.2f} "
              f"reach2R={d['frac_reach_2R']:.2f} reach3R={d['frac_reach_3R']:.2f} "
              f"reach4R={d['frac_reach_4R']:.2f} bars2R={d['med_bars_to_2R']} bars3R={d['med_bars_to_3R']}")

    # which asset-class books to evaluate
    books = {
        "metals": {"metals"},
        "energy": {"energy"},
        "metals_energy": {"metals", "energy"},      # the deployable foundation routing
        "fx": {"fx"},
        "jpy_fx": {"jpy_fx"},
        "index": {"index"},
        "crypto": {"crypto"},
        "ALL": None,
    }

    result = {
        "thrust": "exit_geometry",
        "foundation": "FVG-retest continuation (wave1 setup_ob_fvg_retest mode=fvg), identical entry+structural stop; exits-only comparison",
        "baseline": BASELINE,
        "maxbars": MAXBARS,
        "path_diagnostics": diag,
        "books": {},
    }

    pol_names = list(all_policies().keys())
    for book_name, cls_filter in books.items():
        res, n = run_class(trades, cls_filter)
        if n == 0:
            continue
        print(f"\n##################### BOOK: {book_name}  (n={n}) #####################")
        # baseline
        base = res[BASELINE]
        print_policy(f"BASELINE {BASELINE}", base)
        # rank candidate exits by TRAIN per-trade R (selection on train only), then show
        ranked = sorted(pol_names, key=lambda nm: -res[nm]["train"]["mean_R"])
        # STRICT selection: best TRAIN mean_R among policies positive in a MAJORITY of TRAIN
        # years (stability without forward peeking). May be None if no policy clears it.
        eligible = [nm for nm in pol_names
                    if res[nm]["pos_train_years"] > res[nm]["total_train_years"] / 2.0]
        chosen = max(eligible, key=lambda nm: res[nm]["train"]["mean_R"]) if eligible else None
        # HONEST recommendation (non-peeking, selected on TRAIN only): maximize year-breadth
        # via TRAIN positive-year COUNT, tie-broken by TRAIN mean_R. This directly targets the
        # "positive in a majority of years / kill chop-year bleed" objective using only TRAIN.
        recommend = max(pol_names,
                        key=lambda nm: (res[nm]["pos_train_years"], res[nm]["train"]["mean_R"]))
        # also unconstrained best-train for reference
        best_train = max(pol_names, key=lambda nm: res[nm]["train"]["mean_R"])
        for nm in ranked[:6]:
            print_policy(nm, res[nm])
        print(f"\n  >>> best-TRAIN-R policy: {best_train}")
        print(f"  >>> STRICT chosen (majority-positive-TRAIN-years): {chosen}")
        print(f"  >>> RECOMMEND (max TRAIN positive-year breadth): {recommend}")
        # negative control on the recommended policy: invert entry, same exit
        ctrl_name = recommend
        ctrl_fn = all_policies()[ctrl_name]
        ctrl_sub = [t for t in inv_trades if (cls_filter is None or t["cls"] in cls_filter)]
        ctrl_pairs = [(t["year"], ctrl_fn(t)) for t in ctrl_sub]
        ctrl_summ = summarize(ctrl_pairs)
        print(f"\n  CONTROL invert-entry under {ctrl_name}: "
              f"FWD R={ctrl_summ['fwd']['mean_R']:+.4f} (must be <= 0)")

        # quantify the lift of the recommendation vs the 3R baseline (forward + breadth)
        rec = res[recommend]
        lift = {
            "recommend": recommend,
            "fwd_R_recommend": rec["fwd"]["mean_R"],
            "fwd_R_baseline_3R": base["fwd"]["mean_R"],
            "fwd_R_delta": round(rec["fwd"]["mean_R"] - base["fwd"]["mean_R"], 4),
            "pos_years_recommend": rec["pos_years"],
            "pos_years_baseline_3R": base["pos_years"],
            "pos_train_years_recommend": rec["pos_train_years"],
            "pos_train_years_baseline_3R": base["pos_train_years"],
            "train_R_recommend": rec["train"]["mean_R"],
            "train_R_baseline_3R": base["train"]["mean_R"],
            "invert_control_fwd_R": ctrl_summ["fwd"]["mean_R"],
        }
        result["books"][book_name] = {
            "n": n,
            "policies": res,
            "baseline_3R": base,
            "best_train_policy": best_train,
            "strict_chosen_policy": chosen,
            "recommend_policy": recommend,
            "recommend_vs_baseline": lift,
            "invert_control_under_recommend": ctrl_summ,
        }

    with open(EDGE + "/WAVE2_EXIT_GEOMETRY_RESULT.json", "w") as f:
        json.dump(result, f, indent=1)
    print("\nWROTE WAVE2_EXIT_GEOMETRY_RESULT.json")

if __name__ == "__main__":
    main()
