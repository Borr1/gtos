"""d2_master — the layer table: NULL / REAL / FEASIBLE / ORACLE, and the three denominators.

Produces D2_RESULT.json: the capture fraction of every downstream layer, the
leave-one-oracle-in ranking (which layer is the largest engineering target), and the
signal-attributable version of the same table (f2's placebo arm as the denominator).
"""

from __future__ import annotations

import glob
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

OUT = Path("/tmp/d2/out")
F2 = Path("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/"
          "fable5-vision-audit-20260725/phase19/receipts/discovery/f2/F2_POOLED_V1.json")
MENU = ("target_1.0R", "target_1.5R", "target_2.0R", "target_3.0R", "target_5.0R",
        "stop_only_horizon", "timestop_15", "timestop_30", "timestop_60",
        "be_runner", "trail_1R", "no_stop_horizon")


def load():
    P = {}
    for p in sorted(glob.glob(str(OUT / "D2_2*_V1_ROWS.npz"))):
        m = Path(p).name.split("_")[1]
        P[m] = dict(np.load(p, allow_pickle=True))
    ks = sorted(P)
    cat = {k: np.concatenate([P[m][k] for m in ks]) for k in P[ks[0]]}
    cat["month"] = np.concatenate([np.full(len(P[m]["ok"]), m) for m in ks])
    return cat, ks


def bk(g, c, day, mask):
    v = np.where(mask, g, np.nan)
    m = np.isfinite(v)
    if not m.any():
        return {"n": 0}
    gg, cc = v[m], c[m]
    net = gg - cc
    by = defaultdict(float)
    for a, x in zip(day[m], net):
        by[a] += x
    return {"n": int(m.sum()), "gross": float(gg.mean()), "cost": float(cc.mean()),
            "net": float(net.mean()), "total_net_r": float(net.sum()),
            "win": float((gg > 0).mean()), "n_days": len(by),
            "days_pos": int(sum(1 for k in by if by[k] > 0))}


def boot_diff(a, b, day, n=2000, seed=20260806):
    """day-block bootstrap of mean(a-b) over paired rows."""
    d = a - b
    by = defaultdict(lambda: [0.0, 0])
    for k, x in zip(day, d):
        if np.isfinite(x):
            by[k][0] += x
            by[k][1] += 1
    days = sorted(by)
    s = np.array([by[k][0] for k in days])
    c = np.array([by[k][1] for k in days], float)
    rng = np.random.default_rng(seed)
    ix = rng.integers(0, len(days), size=(n, len(days)))
    m = s[ix].sum(1) / np.where(c[ix].sum(1) == 0, np.nan, c[ix].sum(1))
    m = m[np.isfinite(m)]
    return {"mean": float(s.sum() / c.sum()), "ci95_lo": float(np.percentile(m, 2.5)),
            "ci95_hi": float(np.percentile(m, 97.5)), "p_le_0": float((m <= 0).mean())}


def capof(mask, day):
    cap = defaultdict(int)
    for a in np.nonzero(mask)[0]:
        cap[day[a]] += 1
    return cap


def topn(vals, day, cap):
    keep = np.zeros(len(vals), bool)
    by = defaultdict(list)
    for a, dd in enumerate(day):
        if np.isfinite(vals[a]):
            by[dd].append(a)
    for dd, aa in by.items():
        k = cap.get(dd, 0)
        if k > 0:
            aa = np.asarray(aa)
            keep[aa[np.argsort(-vals[aa])][:k]] = True
    return keep


def main():
    D, months = load()
    ok = D["ok"].astype(bool)
    g = D["gross"].astype(float)
    c = D["cost"].astype(float)
    day = D["day"].astype(str)
    gate = D["gate_real"].astype(bool)
    net = np.where(ok, g, np.nan) - c
    menu_mean = D["menu_mean"].astype(float)
    menu_best = D["menu_best"].astype(float)
    ent_sh = D["entry_oracle_shipped_exit"].astype(float)
    ent_j = D["entry_oracle_shipped_j"].astype(int)
    best_fixed_exit = D["menu_stop_only_horizon"].astype(float)
    pooled = json.load(open(OUT / "D2_POOLED_V1.json"))
    f2 = json.load(open(F2))
    f2b = {r["rung"]: r for r in f2["LADDER_TABLE_TRACK_B"]}

    out = {"lane": "d2", "population": "PB reproduced sealed roster, AT_MARKET cohort, "
           "close-only k=15, 8 windows Oct-2025..May-2026",
           "months": months, "n": int(ok.sum()), "n_days": int(len(set(day[ok])))}

    # ---------------- the two reference books
    R1 = bk(g, c, day, ok)                       # every layer NULL except the exit
    NULLALL = bk(menu_mean, c, day, ok)          # every layer NULL including the exit
    REALSTACK = bk(g, c, day, gate)              # gate REAL, entry j0, exit 2R
    out["BOOKS"] = {"ALL_NULL_menu_mean_exit_no_gate": NULLALL,
                    "R1_no_gate_shipped_exit": R1,
                    "FULL_REAL_STACK_gate_j0_2R": REALSTACK}

    capg = capof(gate, day)
    orc_gate = topn(np.where(ok, net, -np.inf), day, capg)

    # ---------------- LEAVE-ONE-ORACLE-IN, from the FULL REAL STACK, same rows
    L = {}
    L["GATE"] = {
        "real": REALSTACK["net"],
        "oracle": bk(g, c, day, orc_gate)["net"],
        "feasible_oos": pooled["LAYER_A_GATE"]["FEASIBLE_gate_oos_net"],
        "null_random_same_size": pooled["LAYER_A_GATE"]["RANDOM_same_size"]["net"],
        "null_admit_all": R1["net"],
    }
    L["EXIT"] = {
        "real": REALSTACK["net"],
        "oracle": bk(menu_best, c, day, gate)["net"],
        "feasible_oos": bk(best_fixed_exit, c, day, gate)["net"],
        "null_random_contract": bk(menu_mean, c, day, gate)["net"],
    }
    # ENTRY_TIMING is priced on the FULL population: the feasible arm (a single fixed
    # M1 offset) is only available there, so all three cells must share those rows.
    L["ENTRY_TIMING"] = {
        "real": R1["net"],
        "oracle": bk(ent_sh, c, day, ok)["net"],
        "feasible_oos": None,   # filled below (best fixed offset, pooled)
        "null_shipped_instant": R1["net"],
        "priced_on": "FULL_POPULATION_no_gate (all three cells)",
        "oracle_on_gate_mask_for_reference": bk(ent_sh, c, day, gate)["net"],
    }
    # feasible timing = best fixed offset, leave-one-month-out, ON THE GATE MASK
    mo = D["month"].astype(str)
    fj = json.load(open(OUT / "D2_POOLED_V1.json"))["LAYER_C_TIMING"][
        "FEASIBLE_fixed_offset_pooled"]
    L["ENTRY_TIMING"]["feasible_full_population_best_fixed_offset"] = max(
        fj.items(), key=lambda kv: kv[1]["net"])
    L["ENTRY_TIMING"]["feasible_oos"] = pooled["LAYER_C_TIMING"][
        "FEASIBLE_best_fixed_offset"]["net"]

    for k, v in L.items():
        nullk = [x for x in v if x.startswith("null")][0]
        v["ORACLE_GAP"] = v["oracle"] - v["real"]
        v["FEASIBLE_GAP"] = (v["feasible_oos"] - v["real"]) if v["feasible_oos"] is not None else None
        v["capture_real_vs_" + nullk] = (
            (v["real"] - v[nullk]) / (v["oracle"] - v[nullk])
            if abs(v["oracle"] - v[nullk]) > 1e-12 else None)
        v["reachable_share_of_oracle_gap"] = (
            v["FEASIBLE_GAP"] / v["ORACLE_GAP"] if v["FEASIBLE_GAP"] is not None
            and abs(v["ORACLE_GAP"]) > 1e-12 else None)
    out["LAYER_TABLE_LEAVE_ONE_ORACLE_IN"] = L

    # ---------------- RANK layer, at the arm's own realised capacity
    r2 = json.load(open(OUT / "D2_RANK2_V1.json"))
    K3 = {}
    for K in (1, 2, 3, 5):
        cap = {d: K for d in set(day)}
        K3["K=%d" % K] = {
            "ORACLE_within_gate": bk(g, c, day, topn(np.where(gate, net, -np.inf), day, cap)),
        }
    out["LAYER_RANK"] = {
        "arm_realised_capacity_trades_per_roster_day": 507 / 172.0,
        "on_roster_at_market_oracle_at_capacity": K3,
        "on_pool_union_taken": r2["BOOK_AT_REAL_CAPACITY"],
        "window_paired_decomposition": r2["WINDOW_PAIRED"],
        "geometry_matched": r2["MATCHED_SAME_SYMBOL_SAME_TOLL"],
        "toll_matched_any_symbol": r2["MATCHED_SAME_TOLL_ANY_SYMBOL"],
        "score_ordering": r2["SCORE_ORDERING"],
        "score_deciles": r2["SCORE_DECILES"],
        "component_ordering": r2["COMPONENT_ORDERING"],
    }

    # ---------------- SIGNAL-ATTRIBUTABLE denominators (f2's placebo arm)
    out["SIGNAL_ATTRIBUTABLE"] = {
        "R1": {"real": f2b["R1_no_gate"]["net"], "placebo": f2b["R1_no_gate"]["placebo_net"],
               "signal": f2b["R1_no_gate"]["signal_net"]},
        "oracle_exit_menu": {"real": f2b["R3_oracle_exit_menu"]["net"],
                             "placebo": f2b["R3_oracle_exit_menu"]["placebo_net"],
                             "signal": f2b["R3_oracle_exit_menu"]["signal_net"]},
        "oracle_exit_path": {"real": f2b["R3b_oracle_exit_path"]["net"],
                             "placebo": f2b["R3b_oracle_exit_path"]["placebo_net"],
                             "signal": f2b["R3b_oracle_exit_path"]["signal_net"]},
        "oracle_entry_plus_menu_exit": {
            "real": f2b["R4_oracle_entry_plus_menu_exit"]["net"],
            "placebo": f2b["R4_oracle_entry_plus_menu_exit"]["placebo_net"],
            "signal": f2b["R4_oracle_entry_plus_menu_exit"]["signal_net"]},
        "note": "every oracle rung is 98.2-100.8 % reproduced by a coin flip on the same "
                "rows (f2 §2); the ORACLE_GAP column above is therefore mostly path "
                "volatility available to any participant, not headroom in this signal.",
    }

    # ---------------- significance of the two real, deployable improvements
    permo = {m: json.load(open(OUT / ("D2_%s_V1.json" % m))) for m in months}
    out["DEPLOYABLE_DELTAS"] = {
        "exit_2R_to_stop_only_horizon_on_gate": boot_diff(
            np.where(gate, best_fixed_exit, np.nan), np.where(gate, g, np.nan), day),
        "exit_2R_to_stop_only_horizon_full_pop": boot_diff(
            np.where(ok, best_fixed_exit, np.nan), np.where(ok, g, np.nan), day),
        "exit_per_month": {m: {
            "target_2.0R": permo[m]["LAYER_D_EXIT"]["each_fixed_contract"]["target_2.0R"]["net"],
            "stop_only_horizon": permo[m]["LAYER_D_EXIT"]["each_fixed_contract"]["stop_only_horizon"]["net"],
            "delta": permo[m]["LAYER_D_EXIT"]["each_fixed_contract"]["stop_only_horizon"]["net"]
            - permo[m]["LAYER_D_EXIT"]["each_fixed_contract"]["target_2.0R"]["net"]}
            for m in months},
        "entry_per_month_j0_vs_j5": {m: {
            "j0": permo[m]["LAYER_C_TIMING"]["FEASIBLE_fixed_offset"]["j=0"]["net"],
            "j5": permo[m]["LAYER_C_TIMING"]["FEASIBLE_fixed_offset"]["j=5"]["net"],
            "delta": permo[m]["LAYER_C_TIMING"]["FEASIBLE_fixed_offset"]["j=5"]["net"]
            - permo[m]["LAYER_C_TIMING"]["FEASIBLE_fixed_offset"]["j=0"]["net"],
            "j0_rank_of_15": 1 + sorted(
                (-permo[m]["LAYER_C_TIMING"]["FEASIBLE_fixed_offset"]["j=%d" % j]["net"]
                 for j in range(15)),
            ).index(-permo[m]["LAYER_C_TIMING"]["FEASIBLE_fixed_offset"]["j=0"]["net"])}
            for m in months},
        "gate_per_month": {m: {
            "null": permo[m]["LAYER_A_GATE"]["NULL_admit_all"]["net"],
            "real": permo[m]["LAYER_A_GATE"]["REAL_shipped_cost_gate"]["net"],
            "random": permo[m]["LAYER_A_GATE"]["RANDOM_same_size"]["net_mean"],
            "oracle": permo[m]["LAYER_A_GATE"]["ORACLE_topn_by_net"]["net"]}
            for m in months},
    }
    out["ENTRY_TIMING_DETAIL"] = {
        "oracle_j_hist": {int(k): int(v) for k, v in
                          zip(*np.unique(ent_j[ok], return_counts=True))},
        "oracle_j0_share": float((ent_j[ok] == 0).mean()),
        "oracle_gross": float(np.nanmean(ent_sh[ok])),
        "shipped_gross": float(np.nanmean(g[ok])),
    }

    # ---------------- JOINT: the full deployable stack vs the shipped stack
    stack = {
        "shipped": bk(g, c, day, gate),
        "shipped_plus_best_exit": bk(best_fixed_exit, c, day, gate),
        "shipped_no_session_gate": bk(g, c, day, gate),
        "all_null": NULLALL,
    }
    out["DEPLOYABLE_STACK"] = stack
    out["ABLATION_SUMMARY"] = pooled["ABLATION_SUMMARY"]
    out["JOINT_ABLATION_GATE_x_EXIT"] = pooled["JOINT_ABLATION_GATE_x_EXIT"]
    out["LAYER_A_GATE_POOLED"] = pooled["LAYER_A_GATE"]
    out["LAYER_D_EXIT_POOLED"] = pooled["LAYER_D_EXIT"]
    out["LAYER_C_TIMING_POOLED"] = pooled["LAYER_C_TIMING"]
    out["GATE_LEDGER_ROSTER"] = json.load(open(OUT / "D2_GATE_ROSTER_V1.json"))
    out["RANK_PER_WINDOW"] = json.load(open(OUT / "D2_RANK_V1.json"))

    Path(OUT / "D2_RESULT.json").write_text(json.dumps(out, indent=1, default=str))

    print("== BOOKS ==")
    for k, v in out["BOOKS"].items():
        print("%-38s n=%-7d gross %+.5f cost %.5f net %+.5f" % (
            k, v["n"], v["gross"], v["cost"], v["net"]))
    print("\n== LAYER TABLE (leave-one-oracle-in, from the FULL REAL STACK) ==")
    print("%-14s %10s %10s %10s %10s %10s %8s" % (
        "layer", "null", "REAL", "FEASIBLE", "ORACLE", "oracgap", "reach%"))
    for k, v in L.items():
        nullk = [x for x in v if x.startswith("null")][0]
        print("%-14s %+10.5f %+10.5f %10s %+10.5f %+10.5f %8s" % (
            k, v[nullk], v["real"],
            ("%+.5f" % v["feasible_oos"]) if v["feasible_oos"] is not None else "-",
            v["oracle"], v["ORACLE_GAP"],
            ("%.2f%%" % (100 * v["reachable_share_of_oracle_gap"]))
            if v["reachable_share_of_oracle_gap"] is not None else "-"))
    print("\n== RANK at the arm's own capacity ==")
    print(json.dumps(out["LAYER_RANK"]["on_pool_union_taken"], indent=1))
    print("\n== deployable deltas ==")
    print(json.dumps(out["DEPLOYABLE_DELTAS"], indent=1, default=str))
    print("\n== entry timing detail ==")
    print(json.dumps(out["ENTRY_TIMING_DETAIL"], indent=1, default=str))


if __name__ == "__main__":
    main()
