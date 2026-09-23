"""
wave8_microstructure_revalidate.py
==================================
THRUST (microstructure_revalidate):

Re-validate the two volume-based microstructure "book" survivors under the SAME strict
gauntlet that the gold sleeve survived and that caught 5 prior leaks:

  S4 ABSORPTION-reversal : big tick-volume + LOW price-efficiency (range absorbed per unit
                           of volume, vs the bar's own 20-bar efficiency baseline) while AT a
                           48-bar range extreme -> FADE. (limit-wall absorption: lots of
                           participation, little progress. Literal "small absolute range at a
                           48-bar extreme" was tested first and is structurally near-empty at
                           H4 — a bar at a fresh extreme almost always has EXPANDED range — so
                           the faithful absorption proxy is low range/volume efficiency.)
  S5 VOLUME-DELTA-divergence : NEW price extreme on WEAKENING 3-bar signed tick-volume -> FADE.
                           (price pushes a new extreme but participation is fading/opposing.)

Both are explicitly two-sided (top extreme -> SHORT, bottom extreme -> LONG). The prior
implementation (microstructure_engine.py) is treated as SUSPECT:
  * its exits were a hand-rolled fill loop (NOT the tested geometry_lib) with an inconsistent
    R-unit (stop at 2.5*ATR but time/trail exits scaled by 1*ATR);
  * its "book" filter selected on the validation slice (val_same_sign) -> selection-on-OOS;
  * the engine predates geometry_lib and may carry the short-side sign-bug class.
We re-implement entries CLEANLY and take EVERY fill through geometry_lib.simulate.

DISCIPLINE (the bar that caught 5 prior leaks):
  * Fills ONLY via tested geometry_lib.simulate / simulate_detail. Stop = 2.5*ATR => R-unit
    is the stop distance; targets are PRICE multiples of that same R-unit (1R/2R) or an ATR
    trail. No hand-rolled R, no sign tricks.
  * NO LOOKAHEAD: every feature at bar i uses only bars <= i (range extreme over [i-47..i],
    signed-vol over [i-2..i], ATR over [i-13..i], rel-vol vs prior 20-bar mean). Episode
    dedup so consecutive identical-trigger bars don't create overlapping peeks. Bad-print
    bars winsorized (wave4.winsorize, file-stitch-aware).
  * STRICT OOS: TRAIN year <= 2024 SELECT, FORWARD 2025-26 readout, AND chained walk-forward
    (per forward year, threshold/direction frozen on strictly-past trades only).
  * Per-year 2015-2026 reported per setup x class x side (volume present in all H4 bars).
  * Matched RANDOM (count-matched, same bars, random direction) + INVERT (flip every entry
    direction) nulls under the SAME selection, per setup. An edge must beat its random null
    and its inverted self must be the mirror (negative) — both at the SELECTED cells.
  * Gold-sleeve correlation: report whether S4/S5 metals-short trades cluster on the same
    DAYS as the deployable gold FVG sleeve (diversification check).
  * Truth over positives. Honest per-setup verdict with numbers.

DATA: H4 bridge_ftmo_deep_h4_2015_2022 + _2015_2022_metals (metals backfill) + _2022_2026.
      volume column = tick/quote count (NOT traded volume) -> used only as relative
      participation, never as size. Cost: ULTIMATE_REAL_COST_MAP.json (per asset class).
Research-only; no broker calls; no paid API.
"""
from __future__ import annotations
import sys, os, json, csv, math, random, statistics
from collections import defaultdict
from datetime import datetime

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
DATA = ROOT + "/data/mt5_research_exports"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)

from geometry_lib import Bar, atr14, simulate, simulate_detail
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
# Reuse wave4's tested winsorize (file-stitch bad-print clamp) — do NOT reinvent.
from wave4_metals_fvg_harden import winsorize as _winsorize

with open(EDGE + "/ULTIMATE_REAL_COST_MAP.json") as f:
    COSTMAP = json.load(f)
GC = COSTMAP["_global_median"]
def cost_for(sym): return float(COSTMAP.get(ASSET_CLASS_BY_SYMBOL.get(sym), GC))

D_FX1  = DATA + "/bridge_ftmo_deep_h4_2015_2022"
D_MET1 = DATA + "/bridge_ftmo_deep_h4_2015_2022_metals"
D_ALL2 = DATA + "/bridge_ftmo_deep_h4_2022_2026"

TRAIN_MAX = 2024
STOP_ATR  = 2.5          # R-unit = 2.5*ATR (matches engine stop; now CONSISTENT for all exits)
MAXBARS   = 24           # H4 holding horizon cap (~4 trading days)
RELV_HI   = 1.5          # "big" tick-volume threshold (vs 20-bar mean)
ABS_RANGE = 0.6          # "small range": bar range <= 0.6*ATR  -> absorption
SEED      = 20260614

# Asset classes the prior panel called strongest; we test ALL but headline these.
FOCUS_CLASSES = ("index", "metals", "jpy_fx", "crypto")
ALL_CLASSES   = ("index", "metals", "jpy_fx", "crypto", "fx", "energy", "agri")

random.seed(SEED)


# ----------------------------------------------------------------------------- data
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

_CACHE = {}
def load(sym):
    """Merge all H4 segments (fx/index 2015_2022, metals backfill, 2022_2026), de-dup by
    timestamp, sort, winsorize bad prints. Volume preserved (tick count)."""
    if sym in _CACHE: return _CACHE[sym]
    merged = {}
    for d in (D_FX1, D_MET1, D_ALL2):
        T, B = _load_one(f"{d}/{sym}_H4.csv")
        for t, b in zip(T, B):
            merged[t] = b
    if not merged:
        _CACHE[sym] = ([], []); return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    times = [k for k, _ in items]; bars = [v for _, v in items]
    bars = _winsorize(times, bars)
    _CACHE[sym] = (times, bars)
    return times, bars


# ----------------------------------------------------------------------------- signals
def signals(sym, times, bars):
    """Yield clean entry records. ALL features use only bars <= i. Two-sided explicit.
    Returns list of dicts: setup, side(+1/-1), i, year, day(date), atr, sym, class.
    Episode dedup: a setup+side fires only on the FIRST bar of a contiguous run of
    identical trigger state (avoids overlapping near-duplicate entries / peeking)."""
    n = len(bars)
    if n < 80: return []
    H = [b.h for b in bars]; L = [b.l for b in bars]; C = [b.c for b in bars]
    O = [b.o for b in bars]; V = [b.v for b in bars]
    rng = [H[k] - L[k] for k in range(n)]
    # signed tick-volume proxy per bar: participation * normalized close location in bar
    vd = [(V[k] * (C[k] - O[k]) / rng[k]) if rng[k] > 0 else 0.0 for k in range(n)]
    ac = ASSET_CLASS_BY_SYMBOL.get(sym)
    out = []
    prev_state = None  # (setup, side) active last bar, for dedup
    for i in range(60, n):
        atr = atr14(bars, i)
        if atr <= 0:
            prev_state = None; continue
        # 48-bar range (inclusive of i): position-in-range locates "at the extreme"
        hi48 = max(H[i-47:i+1]); lo48 = min(L[i-47:i+1])
        span = hi48 - lo48
        pos = (C[i] - lo48) / span if span > 0 else 0.5   # 0=at low, 1=at high (close-based)
        at_top = pos >= 0.75                                # in upper quartile of 48-bar range
        at_bot = pos <= 0.25                                # in lower quartile
        # rel volume vs prior-20 mean (exclude i to keep it strictly "how big is THIS bar")
        m20v = sum(V[i-20:i]) / 20.0 if i >= 20 else (sum(V[:i]) / max(i, 1))
        relv = V[i] / m20v if m20v > 0 else 0.0
        big_vol = relv >= RELV_HI
        # absorption = LOW price-efficiency: this bar moved little PER unit of tick-volume
        # vs its own 20-bar efficiency baseline (lots of participation, little progress).
        # eff = range/volume; absorption when eff <= ABS_RANGE * baseline_eff. Strictly <= i.
        effs = [rng[k] / V[k] if V[k] > 0 else 0.0 for k in range(i-19, i+1)]
        base_eff = sum(effs) / len(effs) if effs else 0.0
        eff_i = rng[i] / V[i] if V[i] > 0 else 0.0
        absorption = (base_eff > 0) and (eff_i <= ABS_RANGE * base_eff)
        # ---- S4 ABSORPTION-reversal: big vol + low efficiency while AT a 48-bar extreme -> fade
        s4_short = at_top and big_vol and absorption                  # near top extreme -> SHORT
        s4_long  = at_bot and big_vol and absorption                  # near bottom extreme -> LONG
        # ---- S5 VOLUME-DELTA-divergence: bar makes a NEW 48-bar price extreme but the signed
        # 3-bar tick-volume is weakening (does NOT confirm the push) -> fade.
        new_hi = H[i] >= max(H[i-47:i])   # this bar's HIGH sets a new 48-bar high (vs prior 47)
        new_lo = L[i] <= min(L[i-47:i])   # this bar's LOW sets a new 48-bar low
        vd3 = sum(vd[i-2:i+1])            # signed participation over last 3 bars (<= i)
        s5_short = new_hi and (vd3 <= 0)                               # new high, no buy push -> SHORT
        s5_long  = new_lo and (vd3 >= 0)                               # new low, no sell push -> LONG
        triggers = []
        if s4_short: triggers.append(("S4_absorption", -1))
        if s4_long:  triggers.append(("S4_absorption", +1))
        if s5_short: triggers.append(("S5_vdelta", -1))
        if s5_long:  triggers.append(("S5_vdelta", +1))
        cur_state = frozenset(triggers)
        # episode dedup: only emit a (setup,side) that was NOT active on the prior bar
        for setup, side in triggers:
            if prev_state is not None and (setup, side) in prev_state:
                continue
            out.append({"setup": setup, "side": side, "i": i, "sym": sym, "class": ac,
                        "atr": atr, "year": times[i].year, "day": times[i].date().isoformat(),
                        "time": times[i]})
        prev_state = cur_state if triggers else None
    return out


def fill(bars, rec, mode, cost):
    """Take a record through the tested simulate. mode: 'fixed1' 1R target, 'fixed2' 2R,
    'trail' ATR-trail (arm 1R, gap 1*ATR). R-unit = STOP_ATR*atr for ALL modes."""
    i = rec["i"]; side = rec["side"]; atr = rec["atr"]
    sd = STOP_ATR * atr
    if mode == "fixed1":
        return simulate(bars, i, side, stop_dist=sd, target_dist=sd, maxbars=MAXBARS, cost=cost)
    if mode == "fixed2":
        return simulate(bars, i, side, stop_dist=sd, target_dist=2*sd, maxbars=MAXBARS, cost=cost)
    if mode == "trail":
        return simulate(bars, i, side, stop_dist=sd, trail_arm=sd, trail_gap=atr,
                        maxbars=MAXBARS, cost=cost)
    raise ValueError(mode)


# ----------------------------------------------------------------------------- stats
def stats(rs):
    rs = list(rs)
    if not rs: return {"n": 0, "mean_R": 0.0, "win%": 0.0, "sum_R": 0.0, "t": 0.0}
    n = len(rs); s = sum(rs); m = s / n
    w = sum(1 for r in rs if r > 0)
    sd = statistics.pstdev(rs) if n > 1 else 0.0
    t = (m / (sd / math.sqrt(n))) if sd > 0 else 0.0
    return {"n": n, "mean_R": round(m, 4), "win%": round(100*w/n, 1),
            "sum_R": round(s, 2), "t": round(t, 2)}


def per_year(recs):
    by = defaultdict(list)
    for d in recs: by[d["year"]].append(d["r"])
    return {int(y): stats(by[y]) for y in sorted(by)}


# ----------------------------------------------------------------------------- gauntlet
def build_records(symbols, mode):
    """Build filled records for all symbols under one exit mode. r attached. No lookahead:
    each fill is independent path-wise (geometry_lib walks forward bars only)."""
    recs = []
    for sym in symbols:
        times, bars = load(sym)
        if len(bars) < 80: continue
        c = cost_for(sym)
        for s in signals(sym, times, bars):
            s = dict(s)
            s["r"] = fill(bars, s, mode, c)
            recs.append(s)
    return recs


def matched_random_null(recs, mode):
    """Count-matched random-direction null: SAME bars/symbols, direction randomized.
    Re-simulate with the flipped-coin side so cost/geometry identical."""
    out = []
    by_sym = defaultdict(list)
    for d in recs: by_sym[d["sym"]].append(d)
    for sym, ds in by_sym.items():
        times, bars = load(sym); c = cost_for(sym)
        for d in ds:
            side = random.choice((+1, -1))
            r = fill(bars, {**d, "side": side}, mode, c)
            out.append({**d, "side": side, "r": r})
    return out


def invert_null(recs, mode):
    """INVERT: flip every entry's direction, re-simulate. A real edge's invert should be
    the negative mirror (lose what the edge wins)."""
    out = []
    by_sym = defaultdict(list)
    for d in recs: by_sym[d["sym"]].append(d)
    for sym, ds in by_sym.items():
        times, bars = load(sym); c = cost_for(sym)
        for d in ds:
            r = fill(bars, {**d, "side": -d["side"]}, mode, c)
            out.append({**d, "side": -d["side"], "r": r})
    return out


def walk_forward(recs, mode, anchor=2015, end=2026):
    """Chained walk-forward. For each forward year Y, on trades STRICTLY BEFORE Y choose
    the side-policy among {as-signalled (+1), inverted (-1)} with higher PAST mean_R,
    requiring a min past sample; then trade Y with that frozen policy. Tests whether the
    SIGN of the edge is stable / learnable from the past, not fitted to the future.
    The inverted side is RE-SIMULATED through the tested fill (exact for asymmetric exits),
    not approximated by negating R."""
    # precompute as-is and inverted R for every rec via the tested fill
    by_sym = defaultdict(list)
    for d in recs: by_sym[d["sym"]].append(d)
    asis = {}; inv = {}
    for sym, ds in by_sym.items():
        _, bars = load(sym); c = cost_for(sym)
        for d in ds:
            asis[id(d)] = d["r"]
            inv[id(d)] = fill(bars, {**d, "side": -d["side"]}, mode, c)
    by_year = defaultdict(list)
    for d in recs: by_year[d["year"]].append(d)
    MIN_PAST = 40
    picks = {}; chained = []
    for Y in range(anchor, end + 1):
        past = [d for d in recs if d["year"] < Y]
        if len(past) < MIN_PAST:
            policy = +1; note = "default(insufficient_past)"; past_R = None
        else:
            a = stats([asis[id(d)] for d in past])["mean_R"]
            b = stats([inv[id(d)] for d in past])["mean_R"]
            if a >= b: policy = +1; past_R = round(a, 4)
            else:      policy = -1; past_R = round(b, 4)
            note = "selected_on_past"
        taken = by_year.get(Y, [])
        ys = [(asis if policy > 0 else inv)[id(d)] for d in taken]
        picks[str(Y)] = {"policy": policy, "note": note, "past_R": past_R,
                         "year_n": len(taken), **{f"year_{k}": v for k, v in stats(ys).items()}}
        for d, r in zip(taken, ys): chained.append((Y, r))
    full = stats([r for _, r in chained])
    fwd = stats([r for y, r in chained if y > TRAIN_MAX])
    py = {int(y): stats([r for yy, r in chained if yy == y]) for y in sorted({y for y, _ in chained})}
    return {"picks": picks, "chained_full": full, "chained_forward": fwd,
            "chained_per_year": py}


def evaluate_cell(recs, mode):
    """Strict select->forward + nulls for one cohort of records (already a single
    setup x class x side OR setup x class cohort)."""
    train = [d["r"] for d in recs if d["year"] <= TRAIN_MAX]
    fwd   = [d["r"] for d in recs if d["year"] > TRAIN_MAX]
    rnd = matched_random_null(recs, mode)
    inv = invert_null(recs, mode)
    return {
        "n": len(recs),
        "train": stats(train), "forward": stats(fwd),
        "per_year": per_year(recs),
        "random_null_full": stats([d["r"] for d in rnd]),
        "random_null_forward": stats([d["r"] for d in rnd if d["year"] > TRAIN_MAX]),
        "invert_full": stats([d["r"] for d in inv]),
        "invert_forward": stats([d["r"] for d in inv if d["year"] > TRAIN_MAX]),
    }


# ----------------------------------------------------------------------------- gold corr
def gold_sleeve_days():
    """Pull the DAYS the deployable gold FVG sleeve traded (for diversification check).
    The result JSON stores cluster days; we read the worst_clusters day list as the
    available day stream (best available without re-running the sleeve here)."""
    try:
        gs = json.load(open(EDGE + "/WAVE5_METALS_RISK_UNIT_AND_TARGET_RESULT.json"))
        days = set()
        for c in gs.get("a_cluster_stress", {}).get("worst_clusters", []):
            if "day" in c: days.add(str(c["day"])[:10])
        return days
    except Exception:
        return set()


# ----------------------------------------------------------------------------- main
def main():
    symbols = sorted([s for s in ASSET_CLASS_BY_SYMBOL
                      if ASSET_CLASS_BY_SYMBOL[s] in ALL_CLASSES])
    # primary exit mode for headline: fixed 1R (symmetric, cleanest fade target);
    # also evaluate 2R and trail to check the verdict is not exit-mode-fragile.
    modes = ("fixed1", "fixed2", "trail")
    report = {"thrust": "microstructure_revalidate", "stop_atr": STOP_ATR,
              "maxbars": MAXBARS, "relv_hi": RELV_HI, "abs_range_frac": ABS_RANGE,
              "train_max": TRAIN_MAX, "seed": SEED,
              "data_coverage_note": ("index/crypto thin pre-2024: most index symbols start "
                  "2025+, crypto starts 2024+; only NAS100/EU50/FRA40/N25/US2000 give index "
                  "depth, only metals & EURUSD/GBPUSD/USDCHF/USDJPY give true 2015-2026."),
              "broker_operation": False, "paid_api_or_vendor_call": False,
              "setups": {}}

    base_recs = {m: build_records(symbols, m) for m in modes}

    for setup in ("S4_absorption", "S5_vdelta"):
        report["setups"][setup] = {"by_mode": {}}
        for m in modes:
            recs_all = [d for d in base_recs[m] if d["setup"] == setup]
            modeblock = {"overall": evaluate_cell(recs_all, m), "by_class": {}, "by_class_side": {}, "walk_forward_by_class": {}}
            for ac in ALL_CLASSES:
                cr = [d for d in recs_all if d["class"] == ac]
                if len(cr) < 30: continue
                modeblock["by_class"][ac] = evaluate_cell(cr, m)
                modeblock["walk_forward_by_class"][ac] = walk_forward(cr, m)
                for side, sname in ((-1, "short"), (+1, "long")):
                    sr = [d for d in cr if d["side"] == side]
                    if len(sr) < 30: continue
                    modeblock["by_class_side"][f"{ac}_{sname}"] = evaluate_cell(sr, m)
            report["setups"][setup]["by_mode"][m] = modeblock

    # ---- STRICT select->forward verdict on the prior "strongest" cells (fixed1 headline)
    # Prior claim: strongest in index-short, metals-short, jpy/crypto. We pre-state:
    # a cell SURVIVES iff: train edge positive AND forward edge positive AND forward beats
    # its forward random null AND forward invert is negative (mirror) AND >=2 forward years
    # positive where >=2 forward years exist.
    verdict = {}
    for setup in ("S4_absorption", "S5_vdelta"):
        verdict[setup] = {}
        m = "fixed1"
        mb = report["setups"][setup]["by_mode"][m]
        prior_strong = []
        for ac in FOCUS_CLASSES:
            for sname in ("short", "long"):
                key = f"{ac}_{sname}"
                cell = mb["by_class_side"].get(key)
                if not cell: continue
                tr = cell["train"]; fw = cell["forward"]
                rndfw = cell["random_null_forward"]; invfw = cell["invert_forward"]
                fwd_years = [y for y, st in cell["per_year"].items() if y > TRAIN_MAX]
                fwd_pos_years = [y for y in fwd_years if cell["per_year"][y]["mean_R"] > 0]
                survives = (
                    tr["n"] >= 30 and fw["n"] >= 20 and
                    tr["mean_R"] > 0 and fw["mean_R"] > 0 and
                    fw["mean_R"] > rndfw["mean_R"] and
                    invfw["mean_R"] < 0 and
                    (len(fwd_years) < 2 or len(fwd_pos_years) >= 2)
                )
                rec = {"train_mean_R": tr["mean_R"], "train_n": tr["n"],
                       "forward_mean_R": fw["mean_R"], "forward_n": fw["n"],
                       "forward_t": fw["t"],
                       "forward_random_null_mean_R": rndfw["mean_R"],
                       "forward_invert_mean_R": invfw["mean_R"],
                       "forward_years": fwd_years, "forward_pos_years": fwd_pos_years,
                       "SURVIVES": bool(survives)}
                verdict[setup][key] = rec
                if cell["forward"]["mean_R"] != 0 or cell["train"]["mean_R"] != 0:
                    prior_strong.append((key, survives))
        verdict[setup]["_survivor_keys"] = [k for k, s in prior_strong if s]
        verdict[setup]["_killed_keys"] = [k for k, s in prior_strong if not s]
    report["strict_verdict_fixed1"] = verdict

    # ---- gold-sleeve diversification (metals-short day overlap)
    gdays = gold_sleeve_days()
    s4_metals_days = {d["day"] for d in base_recs["fixed1"]
                      if d["setup"] == "S4_absorption" and d["class"] == "metals" and d["side"] == -1}
    s5_metals_days = {d["day"] for d in base_recs["fixed1"]
                      if d["setup"] == "S5_vdelta" and d["class"] == "metals" and d["side"] == -1}
    report["gold_sleeve_correlation"] = {
        "gold_sleeve_day_sample_n": len(gdays),
        "s4_metals_short_days": len(s4_metals_days),
        "s4_overlap_with_gold": len(s4_metals_days & gdays),
        "s5_metals_short_days": len(s5_metals_days),
        "s5_overlap_with_gold": len(s5_metals_days & gdays),
        "note": "gold day sample is only the worst-cluster days stored in WAVE5 result; "
                "low overlap is suggestive not definitive without full sleeve day stream.",
    }

    out = EDGE + "/WAVE8_MICROSTRUCTURE_REVALIDATE_RESULT.json"
    with open(out, "w") as f:
        json.dump(report, f, indent=1, sort_keys=True, default=str)

    # ---- console summary
    print("=" * 78)
    print("WAVE8 MICROSTRUCTURE RE-VALIDATE  (fixed1 = 1R target headline)")
    print("=" * 78)
    for setup in ("S4_absorption", "S5_vdelta"):
        mb = report["setups"][setup]["by_mode"]["fixed1"]
        ov = mb["overall"]
        print(f"\n### {setup}  overall n={ov['n']}  "
              f"TRAIN {ov['train']['mean_R']:+.3f}R(n{ov['train']['n']})  "
              f"FWD {ov['forward']['mean_R']:+.3f}R(n{ov['forward']['n']}, t={ov['forward']['t']})  "
              f"| rnd-fwd {ov['random_null_forward']['mean_R']:+.3f}  inv-fwd {ov['invert_forward']['mean_R']:+.3f}")
        print("  -- focus class x side (TRAIN -> FORWARD | rnd-fwd / inv-fwd | survives) --")
        for ac in FOCUS_CLASSES:
            for sname in ("short", "long"):
                cell = mb["by_class_side"].get(f"{ac}_{sname}")
                if not cell: continue
                tr = cell["train"]; fw = cell["forward"]
                surv = report["strict_verdict_fixed1"][setup].get(f"{ac}_{sname}", {}).get("SURVIVES")
                print(f"    {ac:8} {sname:5} n={cell['n']:4} "
                      f"{tr['mean_R']:+.3f}->{fw['mean_R']:+.3f}R (fwd n={fw['n']:3}, t={fw['t']:+.2f}) "
                      f"| {cell['random_null_forward']['mean_R']:+.3f}/{cell['invert_forward']['mean_R']:+.3f} "
                      f"| {'SURVIVES' if surv else 'killed'}")
        sv = report["strict_verdict_fixed1"][setup]
        print(f"  SURVIVORS: {sv['_survivor_keys']}")
        print(f"  KILLED   : {sv['_killed_keys']}")
        # walk-forward headline for metals/index (deepest classes)
        for ac in ("metals", "index", "jpy_fx", "crypto"):
            wf = mb["walk_forward_by_class"].get(ac)
            if wf:
                print(f"  WF {ac:7}: chained_full {wf['chained_full']['mean_R']:+.3f}R "
                      f"fwd {wf['chained_forward']['mean_R']:+.3f}R (n={wf['chained_forward']['n']})")
    gc = report["gold_sleeve_correlation"]
    print(f"\nGOLD CORR: gold-day-sample={gc['gold_sleeve_day_sample_n']} "
          f"S4 metals-short days={gc['s4_metals_short_days']} overlap={gc['s4_overlap_with_gold']} "
          f"S5 days={gc['s5_metals_short_days']} overlap={gc['s5_overlap_with_gold']}")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
