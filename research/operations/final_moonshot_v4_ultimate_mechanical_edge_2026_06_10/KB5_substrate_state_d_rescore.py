"""KB5 — Re-score the substrate under the DEPLOYED STATE_D vol-tiered scale-out exit.

Track key: KB5_STATE_D. Re-mine the substrate top cells under the VALIDATED STATE_D
exit (compounding_sleeve.exit_state_d) instead of the fixed +xR/-1R barrier labeler.

WHY: the fixed-2R/3R labeler caps win% (~33-55%) because a clean target touch is
rare; the DEPLOYED outcome is the vol-tiered scale-out (book 50% @ scaleR, runner
to BE then deep fixed target, no trail). STATE_D is the REAL tradeable outcome, so
this is the honest re-scoring of every cell.

DISCIPLINE (identical to substrate.py):
  - NO LOOKAHEAD: states are sub.build_states (features index<=i only). Entry=close[i],
    outcome window i+1.. via exit_state_d's own forward bar walk.
  - REAL COST: w1.cost_for(sym), scaled by 1/stop_atr exactly like sub.outcome.
  - FORWARD HOLDOUT: TRAIN(<=2024) vs FWD(2025-26); n_train>=40, n_fwd>=40,
    meanR>=0.05 BOTH train&fwd, MAJORITY of train years +EV AND majority of fwd years +EV.
  - NO AVERAGES AS VERDICTS: per-year + per-class always; verdict metric = mean_R.

GEOMETRY under STATE_D: exit_state_d IGNORES target_R (it derives scaleR/runR from
vr). So the fixed GEOMS grid collapses: the only knob is stop_atr (the R-unit). We
score the DEPLOYED stop_atr=1.0 as the canonical run, and also emit stop_atr=0.75 /
1.5 as robustness variants. The cell key carries only (stop_atr, dir, dims) — NO
target_R — because STATE_D's exit is geometry-self-determined.

vr CONSISTENCY: sub state["vr"] == cs.vol_ratio(atrs,i) (both ATR/100-bar-mean-ATR),
verified byte-identical, so exit_state_d's vr tiering uses the SAME vr that buckets
the substrate vol dimension. No drift.
"""
from __future__ import annotations
import sys, os, json, math, collections
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))

import substrate as sub
import compounding_sleeve as cs
import wave1_structure_setups_ict as w1
from geometry_lib import atr14

TRAIN_MAX_YEAR = sub.TRAIN_MAX_YEAR     # 2024
FWD_MIN_YEAR   = sub.FWD_MIN_YEAR       # 2025
MIN_N_TRAIN    = sub.MIN_N_TRAIN        # 40
MIN_N_FWD      = sub.MIN_N_FWD          # 40
WARMUP         = sub.WARMUP
MAXBARS        = sub.MAXBARS            # 80 — matches exit_state_d default

# STATE_D stop-atr variants. 1.0 = the DEPLOYED config; others are robustness probes.
STOP_ATRS = [1.0, 0.75, 1.5]
# same confluence depths as the substrate
PLANS = sub.CONFLUENCE_PLANS


def state_d_outcome(B, i, direction, stop_atr, atr, vr, cost):
    """Label bar i with the DEPLOYED STATE_D scale-out exit.
    R-unit == sd == stop_atr*ATR. cost scaled by 1/stop_atr (tighter stop pays
    relatively more spread) — IDENTICAL scaling to sub.outcome so EV is comparable."""
    sd = stop_atr * atr
    scaled_cost = cost / stop_atr
    ex = cs.exit_state_d(B, i, direction, sd, vr, scaled_cost, maxbars=MAXBARS)
    return ex["R"], ex["reason"]


def cell_key_sd(coords, stop_atr, dmode, dims):
    """Cell id under STATE_D: NO target_R (exit is self-geometried)."""
    g = f"sd{stop_atr}"
    c = "|".join(f"{d}={coords[d]}" for d in dims) if dims else "ALL"
    return f"{g}|dir={dmode}|depth{len(dims)}|{c}"


def build_rows(symbols, stop_atrs=STOP_ATRS, verbose=True):
    """One row per (bar, dir, stop_atr) carrying state coords + STATE_D outcome."""
    rows = []
    for s in symbols:
        cls = sub.AC.get(s)
        if cls is None:
            continue
        built = sub.build_states(s)
        if built is None:
            if verbose: print(f"  {s:12s} skip (insufficient)", flush=True)
            continue
        T, B, A, states = built
        cost = w1.cost_for(s)
        n = len(B)
        cnt = 0
        for i in range(WARMUP, n - MAXBARS - 1):
            st = states[i]
            if st is None:
                continue
            a = A[i]
            if a <= 0:
                continue
            coords = sub.cell_coords(st)
            vr = st["vr"]                       # == cs.vol_ratio(A,i)
            yr = T[i].year
            for sa in stop_atrs:
                for d in (+1, -1):
                    R, reason = state_d_outcome(B, i, d, sa, a, vr, cost)
                    rows.append({"sym": s, "cls": cls, "year": yr,
                                 "coords": coords, "dir": d, "sa": sa, "R": R})
            cnt += 1
        if verbose:
            print(f"  {s:12s} {cnt:6d} bars -> {cnt*len(stop_atrs)*2} rows (cum {len(rows)})", flush=True)
    return rows


def _agg(records):
    n = len(records)
    if n == 0:
        return None
    rs = [r for _, _, r in records]
    s = sum(rs)
    wins = sum(1 for x in rs if x > 0)
    return {"n": n, "win_pct": round(wins / n * 100, 1),
            "mean_R": round(s / n, 4), "sum_R": round(s, 2)}


def _per_year(records):
    by = collections.defaultdict(list)
    for y, cls, r in records:
        by[y].append((y, cls, r))
    return {str(y): _agg(by[y]) for y in sorted(by)}


def _per_class(records):
    by = collections.defaultdict(list)
    for y, cls, r in records:
        by[cls].append((y, cls, r))
    return {cls: _agg(by[cls]) for cls in sorted(by)}


def mine(rows, plans=PLANS, min_cell_n=20):
    buckets = collections.defaultdict(list)
    for r in rows:
        sa = r["sa"]; d = r["dir"]; co = r["coords"]
        rec = (r["year"], r["cls"], r["R"])
        for dims in plans:
            ck = cell_key_sd(co, sa, d, dims)
            buckets[ck].append(rec)
    detail_n = max(min_cell_n, MIN_N_TRAIN + MIN_N_FWD)
    out = {}
    for ck, recs in buckets.items():
        if len(recs) < min_cell_n:
            continue
        train = [x for x in recs if x[0] <= TRAIN_MAX_YEAR]
        fwd = [x for x in recs if x[0] >= FWD_MIN_YEAR]
        entry = {"cell": ck, "depth": ck.split("|")[2], "n": len(recs),
                 "train": _agg(train), "fwd": _agg(fwd)}
        if len(recs) >= detail_n:
            entry["per_year"] = _per_year(recs)
            entry["per_class"] = _per_class(recs)
        out[ck] = entry
    return out


def top_edges(cmap, min_n_train=MIN_N_TRAIN, min_n_fwd=MIN_N_FWD,
              min_meanR_train=0.05, min_meanR_fwd=0.05):
    """Identical forward-validation gate as substrate.top_edges, on STATE_D mean_R."""
    edges = []
    for ck, c in cmap.items():
        ta, fa = c["train"], c["fwd"]
        if ta is None or fa is None:
            continue
        if ta["n"] < min_n_train or fa["n"] < min_n_fwd:
            continue
        if not (ta["mean_R"] >= min_meanR_train and fa["mean_R"] >= min_meanR_fwd):
            continue
        py = c.get("per_year") or {}
        fwd_years = {y: s for y, s in py.items() if int(y) >= FWD_MIN_YEAR and s}
        pos_fwd = sum(1 for s in fwd_years.values() if s["mean_R"] > 0)
        if len(fwd_years) >= 2 and pos_fwd < math.ceil(len(fwd_years) / 2):
            continue
        tr_years = {y: s for y, s in py.items() if int(y) <= TRAIN_MAX_YEAR and s}
        pos_tr = sum(1 for s in tr_years.values() if s["mean_R"] > 0)
        if len(tr_years) >= 2 and pos_tr < math.ceil(len(tr_years) / 2):
            continue
        edges.append({
            "cell": ck, "depth": c.get("depth"), "stop_atr": float(ck.split("|")[0][2:]),
            "n_train": ta["n"], "n_fwd": fa["n"],
            "win_train": ta["win_pct"], "win_fwd": fa["win_pct"],
            "meanR_train": ta["mean_R"], "meanR_fwd": fa["mean_R"],
            "pos_fwd_years": pos_fwd, "total_fwd_years": len(fwd_years),
            "pos_train_years": pos_tr, "total_train_years": len(tr_years),
            "per_class_fwd": {k: v for k, v in (c.get("per_class") or {}).items()},
            "per_year": py,
        })
    edges.sort(key=lambda e: (-min(e["meanR_train"], e["meanR_fwd"]),
                              -e["meanR_fwd"], -e["n_fwd"]))
    return edges


# --------------------------------------------------------------------------- #
# Comparison harness: line up STATE_D vs fixed-barrier for the SAME state cells
# --------------------------------------------------------------------------- #
def fixed_cell_to_sd_coords(cell):
    """Parse a fixed-barrier cell id -> (dims-tuple, coords-dict, dmode). Used to
    look up the STATE_D re-score of an existing forward-validated fixed cell."""
    parts = cell.split("|")
    dmode = int(parts[1].split("=")[1])
    coords = {}
    dims = []
    for p in parts[3:]:
        d, b = p.split("=")
        coords[d] = b; dims.append(d)
    return tuple(dims), coords, dmode


def main():
    quick = "--quick" in sys.argv
    nlim = next((int(a) for a in sys.argv[1:] if a.isdigit()), None)
    syms = [s for s in w1.SYMBOLS if sub.AC.get(s)]
    if nlim:
        syms = syms[:nlim]
    print(f"KB5 STATE_D re-score: {len(syms)} symbols, stop_atrs={STOP_ATRS}, "
          f"maxbars={MAXBARS}", flush=True)
    rows = build_rows(syms)
    print(f"\nTotal STATE_D-labeled rows: {len(rows):,}", flush=True)
    cmap = mine(rows)
    print(f"Populated cells: {len(cmap):,}", flush=True)
    edges = top_edges(cmap)
    print(f"Forward-validated cells under STATE_D: {len(edges)}", flush=True)

    out = {
        "meta": {
            "exit": "compounding_sleeve.exit_state_d (DEPLOYED vol-tiered scale-out)",
            "stop_atrs": STOP_ATRS, "deployed_stop_atr": 1.0,
            "min_n_train": MIN_N_TRAIN, "min_n_fwd": MIN_N_FWD,
            "verdict_metric": "mean_R under STATE_D (real cost, pessimistic same-bar fill)",
            "rule": "n_train>=40 & n_fwd>=40 & meanR>=0.05 BOTH train&fwd & "
                    "majority train years +EV & majority fwd years +EV",
            "n_symbols": len(syms), "total_rows": len(rows),
            "n_cells": len(cmap), "n_edges": len(edges),
        },
        "cells": cmap,
        "edges": edges,
    }
    (HERE / "KB5_STATE_D_RESCORE.json").write_text(json.dumps(out, indent=1, default=str))
    print("wrote KB5_STATE_D_RESCORE.json", flush=True)
    return cmap, edges


if __name__ == "__main__":
    main()
