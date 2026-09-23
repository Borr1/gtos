"""
wave2_assembled_system.py
=========================
WAVE 2 SYNTHESIS — compose the four validated levers end-to-end on the SAME
validated FVG-retest continuation entry and measure real per-year numbers.

The four Wave-2 thrusts each isolated ONE variable against the foundation
baseline. This script STACKS them so the assembled-system numbers are measured,
not asserted:

  ENTRY   : validated wave1 FVG-retest continuation (mode='fvg'), reused verbatim
  GATE    : per-symbol consecutive-loss skip, L=3  (the only causal majority lever)
  STOP    : structural retest_wick + 0.40*ATR buffer (structure-isolated winner)
  EXIT    : partial 50% @ 2R + BE + trail-1R runner (exit-geometry winner)
  ROUTING : metals+energy carrier pocket; metals-only high-conviction sub-book

DISCIPLINE: identical entry detection across every arm; loss-streak advances on
the realized FVG signal outcome (past-only, never forward); selection facts (L,
stop arm, exit policy) were all locked on TRAIN<=2024 in their own thrusts;
FORWARD 2025-2026 is read-out only. Full per-year 2015-2026 reported. All fills
via tested geometry_lib primitives. INVERT-entry negative control on the final
assembled book.

Run:  python3 wave2_assembled_system.py
Writes WAVE2_ASSEMBLED_SYSTEM_RESULT.json
"""
from __future__ import annotations
import sys, os, json
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)

from geometry_lib import Bar, atr14, simulate
import wave1_structure_setups_ict as W
from wave1_structure_setups_ict import load, htf_trend, cost_for
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

MAXBARS = 80
FLOOR = 0.20          # structural-stop ATR floor (from structural_stop thrust)
CAP = 3.5             # structural-stop ATR cap (from structural_stop thrust)
WICK_BUF = 0.40       # retest_wick chosen buffer
GATE_L = 3            # loss-skip L (locked on TRAIN in survivability thrust)

METALS = [s for s in W.SYMBOLS if ASSET_CLASS_BY_SYMBOL.get(s) == "metals"]
ENERGY = [s for s in W.SYMBOLS if ASSET_CLASS_BY_SYMBOL.get(s) == "energy"]
POCKET = METALS + ENERGY

_LOAD = {}
def _ld(sym):
    if sym not in _LOAD:
        _LOAD[sym] = load(sym)
    return _LOAD[sym]


# ---------------------------------------------------------------------------
# Entry detection: yields per-signal primitives INCLUDING both the foundation
# stop (foundation_sd) and the structural retest_wick stop (wick_sd), so we can
# switch stop family without re-detecting entries.
# ---------------------------------------------------------------------------
def detect_signals(sym, B, trend_lb=30, fvg_min=0.10, atr_stop_floor=0.25, stop_buf=0.10):
    """Return list of dicts in chronological order:
       i, direction, foundation_sd, wick_sd, year."""
    T, _ = _ld(sym)
    n = len(B)
    atrs = [atr14(B, i) for i in range(n)]
    out = []
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
                    foundation_sd = max((b.c - min(b.l, gap_bot)) + stop_buf * a, atr_stop_floor * a)
                    d_wick = b.c - b.l                          # entry close to retest bar low
                    wick_sd = min(max(d_wick + WICK_BUF * a, FLOOR * a), CAP * a)
                    out.append(dict(i=i, direction=+1, foundation_sd=foundation_sd,
                                    wick_sd=wick_sd, year=T[i].year))
                    break
        elif tr == -1:
            for k in range(i - 2, max(i - 9, 60), -1):
                gap_bot = B[k].h; gap_top = B[k - 2].l
                if gap_top - gap_bot < fvg_min * a:
                    continue
                if b.h >= gap_bot and b.c < gap_top and b.c < b.o:
                    foundation_sd = max((max(b.h, gap_top) - b.c) + stop_buf * a, atr_stop_floor * a)
                    d_wick = b.h - b.c                          # retest bar high to entry close
                    wick_sd = min(max(d_wick + WICK_BUF * a, FLOOR * a), CAP * a)
                    out.append(dict(i=i, direction=-1, foundation_sd=foundation_sd,
                                    wick_sd=wick_sd, year=T[i].year))
                    break
    return out


# ---------------------------------------------------------------------------
# Exit legs (faithful copies of wave2_exit_geometry primitives)
# ---------------------------------------------------------------------------
def exit_fixed(B, i, d, sd, cost, R):
    return simulate(B, i, d, stop_dist=sd, target_dist=R * sd, maxbars=MAXBARS, cost=cost)

def exit_partial_trail1(B, i, d, sd, cost, part_R=2.0, frac=0.5):
    """50% off at part_R, runner BE then trail 1R behind extreme. Cost once."""
    entry = B[i].c
    end = min(i + MAXBARS, len(B) - 1)
    stop = entry - sd if d > 0 else entry + sd
    part_px = entry + part_R * sd if d > 0 else entry - part_R * sd
    part_filled = False
    run_frac = 1.0 - frac
    mx = entry
    for j in range(i + 1, end + 1):
        b = B[j]
        # adverse first (pessimistic)
        if d > 0:
            if b.l <= stop:
                stopR = (stop - entry) / sd
                return (frac * part_R + run_frac * stopR - cost) if part_filled else (stopR - cost)
        else:
            if b.h >= stop:
                stopR = (entry - stop) / sd
                return (frac * part_R + run_frac * stopR - cost) if part_filled else (stopR - cost)
        if not part_filled:
            if (d > 0 and b.h >= part_px) or (d < 0 and b.l <= part_px):
                part_filled = True
                stop = entry  # BE
        if part_filled:
            if d > 0:
                if b.h > mx: mx = b.h
                trail = mx - 1.0 * sd
                if trail > stop: stop = trail
            else:
                if b.l < mx: mx = b.l
                trail = mx + 1.0 * sd
                if trail < stop: stop = trail
    closeR = (B[end].c - entry) / sd if d > 0 else (entry - B[end].c) / sd
    if part_filled:
        return frac * part_R + run_frac * closeR - cost
    return closeR - cost


# ---------------------------------------------------------------------------
# Stats / per-year
# ---------------------------------------------------------------------------
def _stats(rs):
    if not rs: return {"n": 0, "mean_R": 0.0, "win%": 0.0, "sum_R": 0.0}
    n = len(rs); s = sum(rs); w = sum(1 for r in rs if r > 0)
    return {"n": n, "mean_R": round(s / n, 4), "win%": round(100 * w / n, 1), "sum_R": round(s, 1)}

def summarize(records):
    by = defaultdict(list)
    for y, r in records: by[y].append(r)
    py = {y: _stats(by[y]) for y in sorted(by)}
    yrs = sorted(py)
    tr = [r for y, r in records if y <= 2024]
    fw = [r for y, r in records if y >= 2025]
    fwd_yrs = [y for y in yrs if y >= 2025]
    return {
        "train": _stats(tr), "fwd": _stats(fw),
        "per_year": {str(y): round(py[y]["mean_R"], 4) for y in yrs},
        "per_year_n": {str(y): py[y]["n"] for y in yrs},
        "pos_years": sum(1 for y in yrs if py[y]["mean_R"] > 0),
        "total_years": len(yrs),
        "pos_fwd_years": sum(1 for y in fwd_yrs if py[y]["mean_R"] > 0),
        "total_fwd_years": len(fwd_yrs),
    }


# ---------------------------------------------------------------------------
# Run an assembled config over a symbol set.
#   stop_family: 'foundation' or 'wick'
#   exit_mode  : 'fixed3' or 'partial'
#   gate_L     : int or None (None = no gate)
#   invert     : flip direction (negative control)
# ---------------------------------------------------------------------------
def run_config(symbols, stop_family="wick", exit_mode="partial", gate_L=GATE_L, invert=False):
    records = []
    for sym in symbols:
        T, B = _ld(sym)
        if len(B) < 200: continue
        cost = cost_for(sym)
        sigs = detect_signals(sym, B)
        loss_streak = 0
        for s in sigs:
            i = s["i"]; d = -s["direction"] if invert else s["direction"]
            sd = s["wick_sd"] if stop_family == "wick" else s["foundation_sd"]
            take = (gate_L is None) or (loss_streak < gate_L)
            if exit_mode == "partial":
                r = exit_partial_trail1(B, i, d, sd, cost)
            else:
                r = exit_fixed(B, i, d, sd, cost, 3.0)
            if take:
                records.append((s["year"], r))
            # streak advances on realized signal outcome (gate uses the SAME exit
            # family so streak reflects the deployed strategy's loss path).
            if r > 0: loss_streak = 0
            else: loss_streak += 1
    return summarize(records)


def main():
    out = {
        "thrust": "assembled_system",
        "spec": {
            "entry": "validated wave1 FVG-retest continuation (mode=fvg), metals+energy",
            "gate": f"per-symbol consecutive-loss skip, L={GATE_L} (resume after a winner)",
            "stop": f"structural retest_wick + {WICK_BUF}*ATR buffer, floor {FLOOR}*ATR, cap {CAP}*ATR",
            "exit": "partial 50% @ 2R + BE + trail-1R runner",
            "routing": "metals+energy carrier pocket; metals-only high-conviction sub-book",
        },
        "discipline": "identical entry detection; loss-streak past-only on realized signal; "
                      "all selection locked on TRAIN<=2024 in source thrusts; FORWARD 2025-26 read-out only; "
                      "full per-year 2015-2026; INVERT negative control; tested geometry_lib fills.",
        "books": {},
    }

    books = {
        "metals_energy": POCKET,
        "metals_only": METALS,
        "energy_only": ENERGY,
    }

    # Reference points + the assembled stack, per book.
    for bname, syms in books.items():
        entry = {}
        # baseline = foundation stop, fixed 3R, NO gate (reproduces foundation)
        entry["A_baseline_found_fixed3R_nogate"] = run_config(syms, "foundation", "fixed3", gate_L=None)
        # + gate only (loss-skip), foundation stop, fixed 3R
        entry["B_gate_found_fixed3R"] = run_config(syms, "foundation", "fixed3", gate_L=GATE_L)
        # + structural wick stop, fixed 3R, gate
        entry["C_gate_wick_fixed3R"] = run_config(syms, "wick", "fixed3", gate_L=GATE_L)
        # FULL assembled: gate + wick stop + partial exit
        entry["D_ASSEMBLED_gate_wick_partial"] = run_config(syms, "wick", "partial", gate_L=GATE_L)
        # invert negative control on the full assembled stack
        entry["D_invert_control"] = run_config(syms, "wick", "partial", gate_L=GATE_L, invert=True)
        # exit/stop without gate (isolate gate contribution within the full stack)
        entry["E_wick_partial_NOGATE"] = run_config(syms, "wick", "partial", gate_L=None)
        out["books"][bname] = entry

    # verdict on the deployable books
    verdict = {}
    for bname in ("metals_energy", "metals_only"):
        d = out["books"][bname]["D_ASSEMBLED_gate_wick_partial"]
        inv = out["books"][bname]["D_invert_control"]
        base = out["books"][bname]["A_baseline_found_fixed3R_nogate"]
        majority = d["pos_years"] > d["total_years"] / 2
        fwd_ok = d["fwd"]["mean_R"] > 0 and d["pos_fwd_years"] == d["total_fwd_years"]
        causal = d["fwd"]["mean_R"] > inv["fwd"]["mean_R"] and inv["fwd"]["mean_R"] < 0
        verdict[bname] = {
            "baseline_pos_years": f'{base["pos_years"]}/{base["total_years"]}',
            "assembled_pos_years": f'{d["pos_years"]}/{d["total_years"]}',
            "baseline_fwd_R": base["fwd"]["mean_R"],
            "assembled_fwd_R": d["fwd"]["mean_R"],
            "assembled_train_R": d["train"]["mean_R"],
            "invert_fwd_R": inv["fwd"]["mean_R"],
            "majority_positive": bool(majority),
            "forward_positive_both_years": bool(fwd_ok),
            "causal_vs_invert": bool(causal),
        }
    out["verdict"] = verdict

    with open(EDGE + "/WAVE2_ASSEMBLED_SYSTEM_RESULT.json", "w") as f:
        json.dump(out, f, indent=1)

    # console
    for bname in books:
        print(f"\n================ {bname} ================")
        for arm, s in out["books"][bname].items():
            py = s["per_year"]
            line = " ".join(f"{y}:{py[y]:+.2f}" for y in sorted(py, key=int))
            print(f"  {arm:38s} pos{s['pos_years']:2d}/{s['total_years']} "
                  f"train{s['train']['mean_R']:+.3f} fwd{s['fwd']['mean_R']:+.3f}(pf{s['pos_fwd_years']}/{s['total_fwd_years']})")
            print(f"      {line}")
    print("\n---- VERDICT ----")
    print(json.dumps(verdict, indent=1))
    print("\nWROTE WAVE2_ASSEMBLED_SYSTEM_RESULT.json")


if __name__ == "__main__":
    main()
