"""
substrate.py — Conditional-outcome MAP engine (the core substrate)
==================================================================
Track key: SUBSTRATE

This is the FOUNDATION layer of the ultimate-system program. It is NOT a strategy.
It is a leak-free STATE VOCABULARY + a queryable MAP of barrier-touch odds:

    P( reach +xR before -yR | state )   measured directly via simulate_detail,
    across ALL ~48 instruments on H4, 2014-2026, both directions.

DOCTRINE enforced here:
  - NO LOOKAHEAD: every feature is computed from CLOSED bars index<=i only.
    The outcome label uses geometry_lib.simulate_detail (the trusted pessimistic
    barrier labeler: stop wins ties, same-bar stop-first). Entry = close[i],
    so feature bar i never overlaps the outcome window (i+1..).
  - NO AVERAGES AS VERDICTS: every cell carries n, TRAIN(<=2024) vs FORWARD
    (2025-26) odds, per-year odds, and per-asset-class odds.
  - FORWARD HOLDOUT MANDATORY: a cell is only "forward-validated" if it holds in
    the forward window with n_fwd >= MIN_N_FWD and the forward odds clear the bar.
  - CONFLUENCE: cells are intersections of independent discretized conditions, so
    high-odds cells come from STACKING conditions, not from one thin slice.
  - REAL COST: simulate cost = w1.cost_for(sym) scaled by stop tightness (a tighter
    stop pays the same price-spread as more R), exactly like conditional_engine.

OUTPUTS:
  - SUBSTRATE_MAP.json     : queryable map. For each (geometry, direction-mode)
                             grid point, every populated cell with full stats.
  - SUBSTRATE_TOP_EDGES.json: the top forward-validated high-odds cells
                             (n_fwd>=MIN_N_FWD, holds forward), ranked.
  - importable engine: build_rows(), mine(), StateVec, query_cell(), CELL_DIMS.

USAGE:
  python3 substrate.py [n_symbols] [--quick]
  # or import:
  import substrate as sub
  rows = sub.build_all_rows(symbols)         # leak-free state+outcome rows
  edges = sub.mine(rows)                     # the map
  sub.cell_key(state, geom)                  # discretize a live state -> cell id
"""
from __future__ import annotations
import sys, os, json, math, collections, statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
from geometry_lib import simulate_detail, atr14, Bar
import wave1_structure_setups_ict as w1
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL as AC

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
TRAIN_MAX_YEAR = 2024
FWD_MIN_YEAR   = 2025
MIN_N_TRAIN    = 40       # never trust a thin cell as an edge
MIN_N_FWD      = 40       # forward holdout sample floor
STRIDE         = 1        # sample every bar; raise to subsample for speed
MAXBARS        = 80       # outcome horizon (matches campaign default)
WARMUP         = 210      # need 200-bar vol window + buffers before first row

# (x, y) barrier grid in R. x = profit target, y = stop. We enumerate a small
# grid of geometries so the map answers "which target/stop pays off in this state".
# Each geometry uses stop_dist = y_atr * ATR, target_dist = (x/ y) * stop_dist so
# that +xR / -yR are literal R multiples of the SAME risk unit (stop = 1R-unit).
# We parameterise by (stop_atr, target_R) where target_R is reward in R-units.
GEOMS = [
    # (stop_atr, target_R) ; R-unit == stop_dist == stop_atr*ATR
    (1.0, 1.0),
    (1.0, 1.5),
    (1.0, 2.0),
    (1.0, 3.0),
    (0.75, 2.0),
    (1.5, 1.0),
]

# --------------------------------------------------------------------------- #
# Leak-free state vocabulary
# --------------------------------------------------------------------------- #
# A StateVec is a flat dict of RAW (continuous) features computed from bars<=i.
# Discretization into cell coordinates happens in cell_coords() so the raw map
# can be re-binned without recomputation.

def _ac(rets):
    """lag-1 autocorrelation of a return series (persistence)."""
    n = len(rets)
    if n < 3: return 0.0
    m = sum(rets) / n
    num = sum((rets[k] - m) * (rets[k - 1] - m) for k in range(1, n))
    den = sum((x - m) ** 2 for x in rets)
    return num / den if den > 0 else 0.0


def build_states(sym):
    """Return (times, bars, atrs, states) where states[i] is the leak-free
    StateVec dict at bar i, or None if i is too early. ALL features index<=i."""
    try:
        T, B = w1.load(sym)
    except Exception:
        return None
    n = len(B)
    if n < WARMUP + MAXBARS + 5:
        return None
    A = [atr14(B, i) for i in range(n)]
    C = [b.c for b in B]; Hh = [b.h for b in B]; Lo = [b.l for b in B]
    # true range series for compression
    tr = [0.0] * n
    for i in range(1, n):
        tr[i] = max(B[i].h - B[i].l, abs(B[i].h - B[i - 1].c), abs(B[i].l - B[i - 1].c))
    rets = [0.0] * n
    for i in range(1, n):
        rets[i] = C[i] - C[i - 1]

    states = [None] * n
    for i in range(WARMUP, n):
        a = A[i]
        if a <= 0:
            continue
        sma100 = sum(A[i - 99:i + 1]) / 100
        vr = a / sma100 if sma100 > 0 else 1.0
        win = A[i - 199:i + 1]
        vol_pct = sum(1 for x in win if x <= a) / len(win)
        # trend slope over two horizons, normalised by ATR (scale-free)
        slope20 = (C[i] - C[i - 20]) / a
        slope50 = (C[i] - C[i - 50]) / a
        slope100 = (C[i] - C[i - 100]) / a
        # htf trend label reused from w1 (slope of 30-bar close vs ATR)
        ht = w1.htf_trend(B, i)
        # multi-TF alignment: do the short (20) and long (100) horizons agree?
        def _sgn(v, thr=0.5):
            return 1 if v > thr else (-1 if v < -thr else 0)
        s_short = _sgn(slope20); s_long = _sgn(slope100)
        mtf_align = 1 if (s_short != 0 and s_short == s_long) else (
            -1 if (s_short != 0 and s_long != 0 and s_short == -s_long) else 0)
        # range position in last 50 bars
        lo50 = min(Lo[i - 49:i + 1]); hi50 = max(Hh[i - 49:i + 1])
        rng_pos = (C[i] - lo50) / (hi50 - lo50) if hi50 > lo50 else 0.5
        # compression: recent 5-bar TR vs 20-bar TR (low => coiled)
        comp = (sum(tr[i - 4:i + 1]) / 5) / (sum(tr[i - 19:i + 1]) / 20 or 1)
        # persistence
        ac60 = _ac(rets[i - 59:i + 1])
        # distance to prior 20-bar extremes (excluding current bar), in ATR
        hi20 = max(Hh[i - 20:i]); lo20 = min(Lo[i - 20:i])
        dist_hi = (hi20 - C[i]) / a       # >0 means below recent high
        dist_lo = (C[i] - lo20) / a       # >0 means above recent low
        # ma distance (mean reversion stretch)
        sma20 = sum(C[i - 19:i + 1]) / 20
        ma_dist = (C[i] - sma20) / a
        states[i] = {
            "vr": vr, "vol_pct": vol_pct,
            "slope20": slope20, "slope50": slope50, "slope100": slope100,
            "htf": ht, "mtf_align": mtf_align,
            "rng_pos": rng_pos, "compression": comp, "ac60": ac60,
            "dist_hi": dist_hi, "dist_lo": dist_lo, "ma_dist": ma_dist,
            "hour": T[i].hour, "dow": T[i].weekday(),
        }
    return T, B, A, states


# --------------------------------------------------------------------------- #
# Discretization -> cell coordinates  (the confluence vocabulary)
# --------------------------------------------------------------------------- #
# Each dimension is a small ordered set of buckets. A cell is the cartesian
# coordinate. cell_coords returns a dict of dimension->bucket-label.
CELL_DIMS = ["vol", "trend", "mtf", "rngpos", "comp", "persist", "session"]

def _bucket_vr(vr):
    if vr < 0.85: return "lo"
    if vr < 1.15: return "mid"
    if vr < 1.6:  return "hi"
    return "xhi"

def _bucket_slope(s):
    if s > 1.5:  return "up"
    if s < -1.5: return "dn"
    return "flat"

def _bucket_rng(p):
    if p < 0.25: return "low"
    if p > 0.75: return "high"
    return "mid"

def _bucket_comp(c):
    if c < 0.7:  return "coil"     # compressed
    if c > 1.3:  return "expand"
    return "norm"

def _bucket_persist(a):
    if a >= 0.10:  return "trend"   # positive autocorr => continuation
    if a <= -0.10: return "revert"  # negative autocorr => mean-revert
    return "rand"

def _bucket_session(h):
    if h < 8:  return "asia"
    if h < 16: return "london"
    return "ny"

def cell_coords(st):
    """Map a raw StateVec to discrete confluence coordinates (leak-free input)."""
    return {
        "vol":     _bucket_vr(st["vr"]),
        "trend":   _bucket_slope(st["slope50"]),
        "mtf":     {1: "aligned", -1: "conflict", 0: "neutral"}[st["mtf_align"]],
        "rngpos":  _bucket_rng(st["rng_pos"]),
        "comp":    _bucket_comp(st["compression"]),
        "persist": _bucket_persist(st["ac60"]),
        "session": _bucket_session(st["hour"]),
    }

def cell_key(coords, geom, dmode, dims=CELL_DIMS):
    """Stable string id for a cell at a given geometry+direction-mode. `dims`
    selects WHICH confluence conditions define the cell (so we can mine at
    multiple confluence depths from broad to deep)."""
    g = f"g{geom[0]}_{geom[1]}"
    c = "|".join(f"{d}={coords[d]}" for d in dims) if dims else "ALL"
    return f"{g}|dir={dmode}|depth{len(dims)}|{c}"


# Confluence-depth mining plan. We mine the map at several depths so high-n
# robust cells (2-3 stacked conditions) AND deep confluence cells (5-7) both
# exist. Deep cells win on odds when data supports them; shallow cells win on
# sample size / frequency. The consumer picks the deepest cell that still has n.
# Each entry is an ordered tuple of dimensions defining a cell family.
CONFLUENCE_PLANS = [
    (),                                                   # depth-0: geometry/dir baseline
    ("vol",),
    ("persist",),
    ("trend",),
    ("vol", "persist"),
    ("vol", "trend"),
    ("trend", "mtf"),
    ("persist", "trend"),
    ("rngpos", "comp"),
    ("vol", "persist", "trend"),
    ("vol", "trend", "mtf"),
    ("persist", "trend", "mtf"),
    ("vol", "rngpos", "comp"),
    ("vol", "persist", "trend", "mtf"),
    ("vol", "trend", "mtf", "rngpos"),
    tuple(CELL_DIMS),                                     # full depth-7 confluence
]


# --------------------------------------------------------------------------- #
# Outcome labelling  (the trusted leak-free barrier touch)
# --------------------------------------------------------------------------- #
def outcome(B, i, direction, stop_atr, target_R, atr, cost):
    """Use simulate_detail to determine +target_R before -1R (stop). Returns
    (R_capped, hit_target_bool). R-unit == stop_dist == stop_atr*ATR.
    cost scaled by 1/stop_atr (tighter stop pays relatively more spread)."""
    sd = stop_atr * atr
    td = target_R * sd
    scaled_cost = cost / stop_atr
    r, _ = simulate_detail(B, i, direction, stop_dist=sd, target_dist=td, cost=scaled_cost,
                           maxbars=MAXBARS)
    # hit target == realized R reached (within eps) the target before stop.
    # With fixed target geometry, a target hit yields ~target_R; a stop yields ~-1.
    hit = r >= (target_R - 0.05)
    return max(-1.3, min(target_R + 0.1, r)), hit


# --------------------------------------------------------------------------- #
# Row building : one row per (bar) carrying state + outcome for every geom/dir
# --------------------------------------------------------------------------- #
def build_all_rows(symbols, stride=STRIDE, verbose=True):
    """Returns a flat list of rows. Each row:
        dict(sym, cls, year, coords, dir, geom_idx, R, hit)
    one entry per (bar, direction, geometry). Leak-free."""
    rows = []
    for s in symbols:
        cls = AC.get(s)
        if cls is None:
            continue
        built = build_states(s)
        if built is None:
            if verbose: print(f"  {s:12s} skip (insufficient)", flush=True)
            continue
        T, B, A, states = built
        cost = w1.cost_for(s)
        n = len(B)
        cnt = 0
        for i in range(WARMUP, n - MAXBARS - 1, stride):
            st = states[i]
            if st is None:
                continue
            coords = cell_coords(st)
            yr = T[i].year
            a = A[i]
            for gi, (stop_atr, target_R) in enumerate(GEOMS):
                for d in (+1, -1):
                    R, hit = outcome(B, i, d, stop_atr, target_R, a, cost)
                    rows.append({
                        "sym": s, "cls": cls, "year": yr,
                        "coords": coords, "dir": d, "gi": gi,
                        "R": R, "hit": hit,
                    })
            cnt += 1
        if verbose:
            print(f"  {s:12s} {cnt:6d} bars -> {cnt*len(GEOMS)*2} rows (cum {len(rows)})", flush=True)
    return rows


# --------------------------------------------------------------------------- #
# Mining : aggregate rows into the queryable cell map
# --------------------------------------------------------------------------- #
def _agg(records):
    """records: list of (year, cls, R, hit). Return summary stats."""
    n = len(records)
    if n == 0:
        return None
    rs = [r for _, _, r, _ in records]
    hits = sum(1 for *_, h in records if h)
    s = sum(rs)
    return {
        "n": n,
        "odds": round(hits / n, 4),          # P(reach +xR before -yR)
        "mean_R": round(s / n, 4),
        "sum_R": round(s, 2),
    }

def _per_year(records):
    by = collections.defaultdict(list)
    for y, cls, r, h in records:
        by[y].append((y, cls, r, h))
    return {str(y): _agg(by[y]) for y in sorted(by)}

def _per_class(records):
    by = collections.defaultdict(list)
    for y, cls, r, h in records:
        by[cls].append((y, cls, r, h))
    return {cls: _agg(by[cls]) for cls in sorted(by)}


def mine(rows, plans=CONFLUENCE_PLANS, min_cell_n=20):
    """Aggregate rows into the cell map at MULTIPLE confluence depths.
    Returns dict cell_key -> stats with train/forward/per-year/per-class
    breakdown. NO averages-as-verdicts. Cells below min_cell_n total are
    dropped to keep the map honest and the file finite."""
    buckets = collections.defaultdict(list)
    for r in rows:
        geom = GEOMS[r["gi"]]; d = r["dir"]; co = r["coords"]
        rec = (r["year"], r["cls"], r["R"], r["hit"])
        for dims in plans:
            ck = cell_key(co, geom, d, dims)
            buckets[ck].append(rec)

    # cells with at least `detail_n` total rows get the full per-year / per-class
    # breakdown; thinner cells keep only headline train/fwd stats. Keeps the map
    # genuinely queryable but lean (the verbose dicts dominate file size).
    detail_n = max(min_cell_n, MIN_N_TRAIN + MIN_N_FWD)
    out = {}
    for ck, recs in buckets.items():
        if len(recs) < min_cell_n:
            continue
        train = [x for x in recs if x[0] <= TRAIN_MAX_YEAR]
        fwd = [x for x in recs if x[0] >= FWD_MIN_YEAR]
        ta = _agg(train); fa = _agg(fwd)
        entry = {
            "cell": ck,
            "depth": ck.split("|")[2],
            "n": len(recs),
            "train": ta,
            "fwd": fa,
        }
        if len(recs) >= detail_n:
            entry["per_year"] = _per_year(recs)
            entry["per_class"] = _per_class(recs)
        out[ck] = entry
    return out


def _breakeven_odds(target_R):
    """Cost-free break-even hit-rate for +target_R / -1R: p*tR - (1-p)*1 = 0."""
    return 1.0 / (1.0 + target_R)


def geom_of_cell(ck):
    """Parse 'g{stop}_{tgt}|...' -> (stop_atr, target_R)."""
    g = ck.split("|", 1)[0][1:]
    a, b = g.split("_")
    return float(a), float(b)


def top_edges(cmap, min_n_train=MIN_N_TRAIN, min_n_fwd=MIN_N_FWD,
              min_meanR_train=0.05, min_meanR_fwd=0.05):
    """Return forward-validated +EV cells, ranked. A cell qualifies if:
       - n_train >= min_n_train AND n_fwd >= min_n_fwd  (never trust thin cells)
       - mean_R (the REAL cost-bearing, pessimistic-fill tradeable outcome) is
         >= min_meanR in BOTH train and forward  -> the edge HOLDS forward
       - a MAJORITY of forward years are +EV  -> not a single-year fluke
    NOTE: we validate on mean_R, not on the clean-barrier `odds`, because with a
    maxbars time-exit a cell can be tradeably +EV via favorable drift without a
    clean +xR touch; mean_R is the honest verdict. `odds` is reported alongside.
    Ranked by forward mean_R, tie-broken by min(train,fwd) mean_R and n_fwd."""
    edges = []
    for ck, c in cmap.items():
        ta, fa = c["train"], c["fwd"]
        if ta is None or fa is None:
            continue
        if ta["n"] < min_n_train or fa["n"] < min_n_fwd:
            continue
        _, target_R = geom_of_cell(ck)
        be = _breakeven_odds(target_R)
        holds = (ta["mean_R"] >= min_meanR_train and fa["mean_R"] >= min_meanR_fwd)
        if not holds:
            continue
        py = c.get("per_year") or {}
        # per-year forward stability: require a MAJORITY of forward years +EV
        fwd_years = {y: s for y, s in py.items() if int(y) >= FWD_MIN_YEAR and s}
        pos_fwd_years = sum(1 for s in fwd_years.values() if s["mean_R"] > 0)
        if len(fwd_years) >= 2 and pos_fwd_years < math.ceil(len(fwd_years) / 2):
            continue
        # per-year TRAIN stability: require >=half of train years +EV too
        tr_years = {y: s for y, s in py.items() if int(y) <= TRAIN_MAX_YEAR and s}
        pos_tr_years = sum(1 for s in tr_years.values() if s["mean_R"] > 0)
        if len(tr_years) >= 2 and pos_tr_years < math.ceil(len(tr_years) / 2):
            continue
        edges.append({
            "cell": ck,
            "depth": c.get("depth"),
            "target_R": target_R,
            "breakeven_odds": round(be, 4),
            "n_train": ta["n"], "n_fwd": fa["n"],
            "odds_train": ta["odds"], "odds_fwd": fa["odds"],
            "meanR_train": ta["mean_R"], "meanR_fwd": fa["mean_R"],
            "edge_over_be_fwd": round(fa["odds"] - be, 4),
            "pos_fwd_years": pos_fwd_years, "total_fwd_years": len(fwd_years),
            "pos_train_years": pos_tr_years, "total_train_years": len(tr_years),
            "per_class_fwd": {k: v for k, v in (c.get("per_class") or {}).items()},
            "per_year": py,
        })
    # rank: min(train,fwd) mean_R primary (robust both-sides), then fwd, then n_fwd
    edges.sort(key=lambda e: (-min(e["meanR_train"], e["meanR_fwd"]),
                              -e["meanR_fwd"], -e["n_fwd"]))
    return edges


# --------------------------------------------------------------------------- #
# Live query helper  (how strategies consume the substrate)
# --------------------------------------------------------------------------- #
def query_cell(cmap, state, geom, dmode, dims=CELL_DIMS):
    """Given a LIVE leak-free StateVec, a geometry, and direction mode (+1/-1),
    return the cell stats at the requested confluence `dims` (or None)."""
    ck = cell_key(cell_coords(state), geom, dmode, dims)
    return cmap.get(ck)


def best_cell(cmap, state, geom, dmode, min_n_fwd=MIN_N_FWD,
              plans=CONFLUENCE_PLANS):
    """Consumer entrypoint: return the DEEPEST confluence cell for this live
    state+geometry+direction that still has n_fwd>=min_n_fwd, else fall back
    shallower. Returns (dims, stats) or (None, None). This is how a strategy
    queries the substrate: 'give me the most specific reliable cell I'm in.'"""
    co = cell_coords(state)
    # deepest first
    for dims in sorted(plans, key=lambda d: -len(d)):
        ck = cell_key(co, geom, dmode, dims)
        c = cmap.get(ck)
        if c and c["fwd"] and c["fwd"]["n"] >= min_n_fwd:
            return list(dims), c
    return None, None


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    args = [a for a in sys.argv[1:]]
    quick = "--quick" in args
    nlim = None
    for a in args:
        if a.isdigit():
            nlim = int(a)
    stride = 3 if quick else STRIDE

    syms = [s for s in w1.SYMBOLS if AC.get(s)]
    if nlim:
        syms = syms[:nlim]
    print(f"SUBSTRATE: building leak-free state+outcome rows for {len(syms)} symbols "
          f"(stride={stride}, geoms={len(GEOMS)}, maxbars={MAXBARS})", flush=True)
    rows = build_all_rows(syms, stride=stride)
    print(f"\nTotal rows: {len(rows):,}", flush=True)
    if not rows:
        print("no rows"); return

    cmap = mine(rows)
    print(f"Populated cells: {len(cmap):,}", flush=True)

    # write the full queryable map
    map_path = HERE / "SUBSTRATE_MAP.json"
    with open(map_path, "w") as f:
        json.dump({
            "meta": {
                "symbols": syms, "n_symbols": len(syms),
                "geoms": GEOMS, "cell_dims": CELL_DIMS,
                "train_max_year": TRAIN_MAX_YEAR, "fwd_min_year": FWD_MIN_YEAR,
                "maxbars": MAXBARS, "stride": stride,
                "total_rows": len(rows), "n_cells": len(cmap),
            },
            "cells": cmap,
        }, f, indent=1)
    print(f"wrote {map_path.name}", flush=True)

    edges = top_edges(cmap)
    write_edges(edges)
    report_edges(edges)
    return cmap, edges


def write_edges(edges):
    top_path = HERE / "SUBSTRATE_TOP_EDGES.json"
    with open(top_path, "w") as f:
        json.dump({
            "meta": {
                "min_n_train": MIN_N_TRAIN, "min_n_fwd": MIN_N_FWD,
                "verdict_metric": "mean_R (real cost, pessimistic same-bar fill)",
                "rule": "n_train>=40 & n_fwd>=40 & meanR>=0.05 BOTH train&fwd & "
                        "majority of train years +EV & majority of fwd years +EV. "
                        "odds = clean P(reach +xR before -yR); reported but not the gate.",
                "n_edges": len(edges),
            },
            "edges": edges,
        }, f, indent=1)
    print(f"wrote {top_path.name}  ({len(edges)} forward-validated cells)", flush=True)


def report_edges(edges, k=40):
    # ---- console report : the TOP forward-validated +EV cells ----
    print("\n" + "=" * 112)
    print("TOP FORWARD-VALIDATED +EV CELLS  (n_train>=40, n_fwd>=40, meanR>=0.05 both, "
          "majority years +EV)")
    print("=" * 112)
    print(f"{'tgtR':>5}{'oddsT':>7}{'oddsF':>7}{'Rtr':>7}{'Rfw':>7}{'nT':>6}{'nF':>6}{'Tyr':>5}{'Fyr':>5}  cell")
    for e in edges[:k]:
        c = e["cell"]
        short = c.split("|", 3)[3] if c.count("|") >= 3 else c
        dmode = "L" if "dir=1" in c else "S"
        print(f"{e['target_R']:>5.1f}{e['odds_train']:>7.2f}{e['odds_fwd']:>7.2f}"
              f"{e['meanR_train']:>+7.2f}{e['meanR_fwd']:>+7.2f}{e['n_train']:>6d}{e['n_fwd']:>6d}"
              f"{e['pos_train_years']:>2d}/{e['total_train_years']:<2d}"
              f"{e['pos_fwd_years']:>2d}/{e['total_fwd_years']:<2d} [{dmode}] {short}")
    if not edges:
        print("  (no cells cleared the forward-validation bar)")

    # ---- frequency of the very best edges ----
    print("\nFREQUENCY of top edges (trades available per forward year, pooled across universe):")
    for e in edges[:10]:
        fy = {y: s for y, s in e["per_year"].items() if int(y) >= FWD_MIN_YEAR and s}
        per = ", ".join(f"{y}:n{s['n']}(R{s['mean_R']:+.2f},odds{s['odds']:.2f})"
                        for y, s in sorted(fy.items()))
        cls = ", ".join(f"{k}:R{v['mean_R']:+.2f}(n{v['n']})"
                        for k, v in sorted((e['per_class_fwd'] or {}).items(),
                                           key=lambda x: -(x[1]['mean_R'] if x[1] else 0))[:4]
                        if v)
        short = e["cell"].split("|", 3)[3]
        print(f"  [{ 'LONG' if 'dir=1' in e['cell'] else 'SHORT'}] tgt{e['target_R']}R  {short}")
        print(f"      fwd years: {per}")
        print(f"      fwd by class: {cls}")


if __name__ == "__main__":
    main()
