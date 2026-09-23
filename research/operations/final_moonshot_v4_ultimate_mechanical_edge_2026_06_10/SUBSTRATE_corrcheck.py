"""SUBSTRATE_corrcheck.py — INTEGRATOR Wave-4.

Surface the TOP forward-validated edges that the substrate + reverse-engineering
layers reveal, MATERIALIZE each candidate as a real per-day R sleeve stream, and
CORR-CHECK each candidate's daily-R stream against the existing 8-sleeve W2 CORE
book (we want LOW correlation; the book is corr~0). Rank by odds x freq x indep.

Method (leak-free, reuses tested engines):
  - substrate cells: re-walk substrate.build_states(sym) per symbol (features
    index<=i only), enter at close[i] when the leak-free state lands in the cell,
    label with substrate.outcome (geometry_lib.simulate_detail, pessimistic same-
    bar, real w1.cost_for scaled by stop tightness). Emit one row/day/sym.
  - leadlag cells: read LEADLAG_EDGES.json GOLD-tier configs (already mined leak-
    free by leadlag.py) -> per-config forward+train EV; corr via the leadlag
    engine's own per-trade dates is heavier, so for leadlag/VP we corr-check using
    the SUBSTRATE headline as the representative new STREAM and report the
    catalog EV/n for the rest (their per-trade ledgers live in their own engines).
  - existing book: load INTEG_W2_streams_cache.pkl, build per-day per-sleeve
    conf-wtd unit-R via INTEG_portfolio_build_w2.build_matrix.

Correlation = Pearson of the candidate's daily summed-R series vs each existing
sleeve's daily conf-wtd series AND vs the combined book, on the intersection of
trading days (0-fill on the union is the book's own convention; we report BOTH
intersection-only and union-0-fill corr to be honest about sparsity).
"""
import sys, json, collections, math, datetime
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))

import substrate as sub
import wave1_structure_setups_ict as w1
from geometry_lib import atr14
import pickle
import INTEG_portfolio_build_w2 as W2

# --------------------------------------------------------------------------- #
# 1) materialize a substrate cell as a real per-day R sleeve stream
# --------------------------------------------------------------------------- #
def parse_cell(cell):
    """'g1.0_3.0|dir=1|depth4|vol=xhi|persist=rand|trend=up|mtf=conflict'
       -> (geom, dmode, {dim:bucket})"""
    parts = cell.split("|")
    g = parts[0][1:]                      # '1.0_3.0'
    stop_atr, target_R = (float(x) for x in g.split("_"))
    dmode = int(parts[1].split("=")[1])
    conds = {}
    for p in parts[3:]:
        d, b = p.split("=")
        conds[d] = b
    return (stop_atr, target_R), dmode, conds


def materialize_cell(cell, symbols=None):
    """Replay the leak-free states; whenever the cell conditions match at bar i,
    enter dir=dmode at close[i] and label with substrate.outcome. Returns rows
    [{sym, date, year, R}] — one per matching bar (a real tradeable signal)."""
    geom, dmode, conds = parse_cell(cell)
    stop_atr, target_R = geom
    syms = symbols or w1.SYMBOLS
    rows = []
    for s in syms:
        built = sub.build_states(s)
        if built is None:
            continue
        T, B, A, states = built
        cost = w1.cost_for(s)
        n = len(B)
        for i in range(sub.WARMUP, n - sub.MAXBARS - 1):
            st = states[i]
            if st is None:
                continue
            co = sub.cell_coords(st)
            if all(co.get(d) == b for d, b in conds.items()):
                a = A[i]
                if a <= 0:
                    continue
                R, hit = sub.outcome(B, i, dmode, stop_atr, target_R, a, cost)
                rows.append(dict(sym=s, date=T[i].date(), year=T[i].year, R=R))
    return rows


# --------------------------------------------------------------------------- #
# 2) existing book daily matrix
# --------------------------------------------------------------------------- #
def existing_book_daily():
    streams = pickle.load(open(HERE / "INTEG_W2_streams_cache.pkl", "rb"))
    days, M = W2.build_matrix(streams)          # conf-wtd per-sleeve per-day
    sleeves = W2.SLEEVES
    # per-sleeve daily series keyed by date
    daily = {sl: {} for sl in sleeves}
    for di, day in enumerate(days):
        for si, sl in enumerate(sleeves):
            daily[sl][day] = M[di][si]
    comb = {day: sum(M[di]) for di, day in enumerate(days)}
    return sleeves, daily, comb, set(days)


# --------------------------------------------------------------------------- #
# 3) candidate stream -> daily summed R (unit conf, so corr is conf-invariant)
# --------------------------------------------------------------------------- #
def candidate_daily(rows):
    byday = collections.defaultdict(list)
    for r in rows:
        byday[r["date"]].append(r["R"])
    return {d: sum(v) / len(v) for d, v in byday.items()}   # mean R/day (sleeve convention)


def pearson(x, y):
    n = len(x)
    if n < 8:
        return None
    mx = sum(x) / n; my = sum(y) / n
    sx = sum((a - mx) ** 2 for a in x); sy = sum((b - my) ** 2 for b in y)
    if sx == 0 or sy == 0:
        return 0.0
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y))
    return cov / math.sqrt(sx * sy)


def corr_vs_book(cand_daily, sleeves, daily, comb, book_days):
    """Two corr conventions:
       UNION-0FILL: over the union of (candidate days ∪ book days), 0-fill the
         absent side. This is the book's own diversification convention.
       INTERSECT: over only days both trade (sharper but sparser).
    """
    cand_days = set(cand_daily)
    out = {"per_sleeve_union0": {}, "per_sleeve_intersect": {},
           "vs_combined_union0": None, "vs_combined_intersect": None,
           "n_cand_days": len(cand_days), "n_overlap_book": len(cand_days & book_days)}
    # union-0fill vs each sleeve
    for sl in sleeves:
        u = sorted(cand_days | set(daily[sl]))
        cx = [cand_daily.get(d, 0.0) for d in u]
        cy = [daily[sl].get(d, 0.0) for d in u]
        out["per_sleeve_union0"][sl] = pearson(cx, cy)
        inter = sorted(cand_days & set(daily[sl]))
        if len(inter) >= 8:
            out["per_sleeve_intersect"][sl] = pearson(
                [cand_daily[d] for d in inter], [daily[sl][d] for d in inter])
    # vs combined book
    u = sorted(cand_days | book_days)
    out["vs_combined_union0"] = pearson(
        [cand_daily.get(d, 0.0) for d in u], [comb.get(d, 0.0) for d in u])
    inter = sorted(cand_days & book_days)
    if len(inter) >= 8:
        out["vs_combined_intersect"] = pearson(
            [cand_daily[d] for d in inter], [comb[d] for d in inter])
    out["max_abs_sleeve_union0"] = max((abs(v) for v in out["per_sleeve_union0"].values() if v is not None), default=None)
    return out


def stream_stats(rows):
    fwd = [r["R"] for r in rows if r["year"] >= 2025]
    tr = [r["R"] for r in rows if r["year"] < 2025]
    yrs = collections.Counter(r["year"] for r in rows)
    fwd_yrs = sum(1 for y in (2025, 2026) if yrs.get(y, 0) >= 5)
    span = max(yrs) - min(yrs) + 1 if yrs else 0
    return dict(n=len(rows), n_train=len(tr), n_fwd=len(fwd),
                meanR_train=round(sum(tr) / len(tr), 4) if tr else None,
                meanR_fwd=round(sum(fwd) / len(fwd), 4) if fwd else None,
                fwd_per_year=round(len(fwd) / 1.5, 1),   # 2025 + ~half 2026
                all_per_year=round(len(rows) / span, 1) if span else None,
                fwd_years_with_n5=fwd_yrs)


# --------------------------------------------------------------------------- #
# Candidate registry: the TOP forward-validated substrate cells to test as sleeves
# --------------------------------------------------------------------------- #
CANDIDATES = {
    # the headline — strong-train + strong-fwd, broad across classes, deep
    "sub_xvol_uptrend_pullback_L3R":
        "g1.0_3.0|dir=1|depth4|vol=xhi|persist=rand|trend=up|mtf=conflict",
    # same edge, 2R geometry (internal confluence robustness check)
    "sub_xvol_uptrend_pullback_L2R":
        "g1.0_2.0|dir=1|depth4|vol=xhi|persist=rand|trend=up|mtf=conflict",
    # highest clean-odds tight-target pocket (0.50 fwd hit-odds)
    "sub_hi_uptrend_pullback_asia_L1R":
        "g1.0_1.0|dir=1|depth7|vol=hi|trend=up|mtf=conflict|rngpos=mid|comp=expand|persist=rand|session=asia",
    # short reversion pocket (asia), 2/2 fwd
    "sub_hi_flat_aligned_revert_asia_S3R":
        "g1.0_3.0|dir=-1|depth7|vol=hi|trend=flat|mtf=aligned|rngpos=mid|comp=norm|persist=revert|session=asia",
    # london trend-pullback long, 1R, good odds 0.45 fwd
    "sub_lo_uptrend_high_trend_london_L1R":
        "g1.0_1.0|dir=1|depth7|vol=lo|trend=up|mtf=neutral|rngpos=high|comp=norm|persist=trend|session=london",
    # mid-vol downtrend reversion long (frequent, n126 fwd) — breadth candidate
    "sub_mid_dn_revert_ny_L3R":
        "g1.0_3.0|dir=1|depth7|vol=mid|trend=dn|mtf=neutral|rngpos=mid|comp=norm|persist=revert|session=ny",
}


def main():
    print("Loading existing W2 CORE book daily matrix...")
    sleeves, daily, comb, book_days = existing_book_daily()
    print(f"  book: {len(sleeves)} sleeves, {len(book_days)} trading days")

    report = {"meta": {"book_sleeves": sleeves, "n_book_days": len(book_days),
                       "corr_convention": "union-0fill (book diversification convention) + intersect"},
              "candidates": {}}

    for name, cell in CANDIDATES.items():
        print(f"\n=== {name} ===\n  cell: {cell}")
        rows = materialize_cell(cell)
        st = stream_stats(rows)
        cd = candidate_daily(rows)
        cc = corr_vs_book(cd, sleeves, daily, comb, book_days)
        print(f"  n={st['n']} (tr {st['n_train']} / fwd {st['n_fwd']}) "
              f"Rtr={st['meanR_train']} Rfw={st['meanR_fwd']} ~{st['fwd_per_year']}/yr fwd")
        print(f"  corr vs COMBINED book: union0={cc['vs_combined_union0']}  "
              f"intersect={cc['vs_combined_intersect']}")
        print(f"  max |corr| vs any single sleeve (union0): {cc['max_abs_sleeve_union0']}")
        top = sorted(((abs(v), s, v) for s, v in cc["per_sleeve_union0"].items() if v is not None), reverse=True)[:3]
        print("  top sleeve corrs (union0): " + ", ".join(f"{s}={v:+.3f}" for _, s, v in top))
        report["candidates"][name] = {"cell": cell, "stats": st, "corr": cc}

    (HERE / "SUBSTRATE_CORRCHECK_RESULT.json").write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote SUBSTRATE_CORRCHECK_RESULT.json")
    return report


if __name__ == "__main__":
    main()
