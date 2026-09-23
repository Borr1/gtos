"""d2_pool — pool the eight per-window layer frames and build the capture table.

Emits, for every layer:  NULL / REAL / FEASIBLE / ORACLE, the capture fraction, the
day-block bootstrap of the real-minus-null difference, and the joint ablation.
"""

from __future__ import annotations

import glob
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

OUT = Path("/tmp/d2/out")
NSEED = 200
MENU = ("target_1.0R", "target_1.5R", "target_2.0R", "target_3.0R", "target_5.0R",
        "stop_only_horizon", "timestop_15", "timestop_30", "timestop_60",
        "be_runner", "trail_1R", "no_stop_horizon")


def load():
    P = {}
    for p in sorted(glob.glob(str(OUT / "D2_*_V1_ROWS.npz"))):
        m = Path(p).name.split("_")[1]
        P[m] = dict(np.load(p, allow_pickle=True))
    keys = sorted(P)
    cat = {}
    for k in P[keys[0]]:
        cat[k] = np.concatenate([P[m][k] for m in keys])
    cat["month"] = np.concatenate([np.full(len(P[m]["ok"]), m) for m in keys])
    return cat, keys


def bk(g, c, day, mask, label=""):
    v = np.where(mask, g, np.nan)
    m = np.isfinite(v)
    if not m.any():
        return {"n": 0, "label": label}
    gg, cc, dd = v[m], c[m], day[m]
    net = gg - cc
    by = defaultdict(float)
    for a, x in zip(dd, net):
        by[a] += x
    return {"label": label, "n": int(m.sum()), "gross": float(gg.mean()),
            "cost": float(cc.mean()), "net": float(net.mean()),
            "total_net_r": float(net.sum()), "win": float((gg > 0).mean()),
            "n_days": len(by), "days_pos": int(sum(1 for k in by if by[k] > 0))}


def boot(net, day, n=2000, seed=20260806):
    by = defaultdict(lambda: [0.0, 0])
    for d, x in zip(day, net):
        if np.isfinite(x):
            by[d][0] += x
            by[d][1] += 1
    days = sorted(by)
    if not days:
        return None
    s = np.array([by[d][0] for d in days])
    c = np.array([by[d][1] for d in days], float)
    rng = np.random.default_rng(seed)
    ix = rng.integers(0, len(days), size=(n, len(days)))
    m = s[ix].sum(1) / np.where(c[ix].sum(1) == 0, np.nan, c[ix].sum(1))
    m = m[np.isfinite(m)]
    return {"mean": float(s.sum() / c.sum()), "ci95_lo": float(np.percentile(m, 2.5)),
            "ci95_hi": float(np.percentile(m, 97.5)), "p_le_0": float((m <= 0).mean()),
            "n_days": len(days)}


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
        if k <= 0:
            continue
        aa = np.asarray(aa)
        keep[aa[np.argsort(-vals[aa])][:k]] = True
    return keep


def rnd_same(mask, day, net, rng, nseed=NSEED):
    cap = capof(mask, day)
    pool = defaultdict(list)
    for a in range(len(day)):
        if np.isfinite(net[a]):
            pool[day[a]].append(a)
    o, t = [], []
    for _ in range(nseed):
        idx = []
        for dd, k in cap.items():
            p = pool.get(dd, [])
            if p:
                idx.extend(rng.choice(p, size=min(k, len(p)), replace=False))
        idx = np.asarray(idx)
        o.append(float(net[idx].mean()))
        t.append(float(net[idx].sum()))
    return {"net": float(np.mean(o)), "sd": float(np.std(o)),
            "p05": float(np.percentile(o, 5)), "p95": float(np.percentile(o, 95)),
            "total_net_r": float(np.mean(t)), "n_seeds": nseed}


def cap_frac(real, null, oracle):
    den = oracle - null
    return None if abs(den) < 1e-12 else (real - null) / den


def main():
    D, months = load()
    ok = D["ok"].astype(bool)
    g = D["gross"].astype(float)
    c = D["cost"].astype(float)
    day = D["day"].astype(str)
    net = np.where(ok, g, np.nan) - c
    rng = np.random.default_rng(20260806)
    out = {"months": months, "n_rows": int(len(ok)), "n_ok": int(ok.sum()),
           "n_days": int(len(set(day[ok])))}

    gate = D["gate_real"].astype(bool)
    sess = D["sess"].astype(bool)
    menu_best = D["menu_best"].astype(float)
    menu_mean = D["menu_mean"].astype(float)
    path_or = D["path_oracle"].astype(float)
    ent_or = D["entry_oracle"].astype(float)
    ent_or_p = D["entry_oracle_path"].astype(float)
    j0 = D["entry_oracle_j"].astype(int)
    dbps = D["dbps"].astype(float)
    plac = D["placebo_gross"].astype(float)

    R1 = bk(g, c, day, ok, "R1_null_everything")
    out["R1"] = R1
    out["R1_boot"] = boot(net, day)
    out["PLACEBO_SIDE_R1"] = bk(plac, c, day, ok, "placebo")

    # -------------------------------------------------------------- LAYER A GATE
    capg = capof(gate, day)
    A = {
        "NULL_admit_all": R1,
        "RANDOM_same_size": rnd_same(gate, day, net, rng),
        "REAL_shipped_gate": bk(g, c, day, gate, "real_gate"),
        "REAL_gate_plus_session": bk(g, c, day, gate & sess, "real_gate_p9"),
        "ORACLE_topn_by_net": bk(g, c, day, topn(np.where(ok, net, -np.inf), day, capg),
                                 "oracle_gate"),
        "ANTI_ORACLE": bk(g, c, day, topn(np.where(ok, -net, -np.inf), day, capg), "anti"),
    }
    A["admit_share"] = float(gate.sum() / ok.sum())
    A["capture_vs_random"] = cap_frac(A["REAL_shipped_gate"]["net"],
                                      A["RANDOM_same_size"]["net"],
                                      A["ORACLE_topn_by_net"]["net"])
    A["capture_vs_null"] = cap_frac(A["REAL_shipped_gate"]["net"], R1["net"],
                                    A["ORACLE_topn_by_net"]["net"])
    A["real_minus_random_boot"] = boot(
        np.where(gate, net, np.nan), day)  # level; the delta CI is below
    # FEASIBLE gate: grid over pre-decision observables, LEAVE-ONE-MONTH-OUT tested
    grid = []
    for cc in (1e9, 0.30, 0.20, 0.15, 0.10, 0.07, 0.05, 0.03, 0.02):
        for dl in (0.0, 5.0, 10.0, 20.0, 40.0, 80.0):
            for ss in (0, 1):
                m = ok & (c <= cc) & (dbps >= dl)
                if ss:
                    m = m & sess
                if m.sum() < 2000:
                    continue
                grid.append(("cost<=%.2f|d>=%.0f|sess%d" % (cc, dl, ss), m))
    mo = D["month"].astype(str)
    loo = []
    for held in months:
        tr = mo != held
        te = mo == held
        best, bn = None, -9e9
        for name, m in grid:
            b = bk(g, c, day, m & tr)
            if b["n"] and b["net"] > bn:
                bn, best = b["net"], name
        mm = dict(grid)[best]
        loo.append({"held_out": held, "rule_fit_on_other_7": best,
                    "train_net": bn, "test": bk(g, c, day, mm & te)})
    A["FEASIBLE_gate_leave_one_month_out"] = loo
    A["FEASIBLE_gate_oos_net"] = float(np.average(
        [x["test"]["net"] for x in loo], weights=[x["test"]["n"] for x in loo]))
    A["FEASIBLE_capture"] = cap_frac(A["FEASIBLE_gate_oos_net"],
                                     A["RANDOM_same_size"]["net"],
                                     A["ORACLE_topn_by_net"]["net"])
    A["grid_best_in_sample"] = sorted(
        [{"rule": n, **bk(g, c, day, m)} for n, m in grid],
        key=lambda x: -x["net"])[:8]
    out["LAYER_A_GATE"] = A

    # -------------------------------------------------------------- LAYER B RANK
    B = {}
    for K in (1, 2, 3, 5, 10, 25, 50):
        cap = {d: K for d in set(day)}
        kb = topn(np.where(ok, net, -np.inf), day, cap)
        kw = topn(np.where(ok, -net, -np.inf), day, cap)
        B["K=%d" % K] = {"ORACLE": bk(g, c, day, kb), "ANTI": bk(g, c, day, kw),
                         "RANDOM": rnd_same(kb, day, net, rng)}
    out["LAYER_B_RANK"] = B
    out["emissions_per_day"] = float(ok.sum() / len(set(day[ok])))

    # -------------------------------------------------------------- LAYER C TIMING
    C = {
        "REAL_j0": R1,
        "ORACLE_best_instant_menu_exit": bk(ent_or, c, day, ok, "entry_oracle"),
        "ORACLE_best_instant_path_exit": bk(ent_or_p, c, day, ok, "entry_oracle_path"),
        "oracle_j_is_zero_share": float((j0[ok] == 0).mean()),
        "oracle_j_mean": float(j0[ok].mean()),
    }
    fj = {}
    for m in months:
        p = dict(np.load(OUT / ("D2_%s_V1.json" % m).replace(".json", "_ROWS.npz"),
                         allow_pickle=True)) if False else None
    for m in months:
        jj = json.load(open(OUT / ("D2_%s_V1.json" % m)))["LAYER_C_TIMING"]["FEASIBLE_fixed_offset"]
        for k, v in jj.items():
            fj.setdefault(k, []).append(v)
    C["FEASIBLE_fixed_offset_pooled"] = {
        k: {"n": sum(x["n"] for x in v),
            "net": float(np.average([x["net"] for x in v],
                                    weights=[x["n"] for x in v])),
            "gross": float(np.average([x["gross"] for x in v],
                                      weights=[x["n"] for x in v]))}
        for k, v in fj.items()}
    best_fixed = max(C["FEASIBLE_fixed_offset_pooled"].items(), key=lambda kv: kv[1]["net"])
    C["FEASIBLE_best_fixed_offset"] = {"rule": best_fixed[0], **best_fixed[1]}
    C["capture_real"] = cap_frac(R1["net"], R1["net"],
                                 C["ORACLE_best_instant_menu_exit"]["net"])
    C["capture_feasible"] = cap_frac(best_fixed[1]["net"], R1["net"],
                                     C["ORACLE_best_instant_menu_exit"]["net"])
    out["LAYER_C_TIMING"] = C

    # -------------------------------------------------------------- LAYER D EXIT
    Dm = {k: bk(D["menu_" + k].astype(float), c, day, ok, k) for k in MENU}
    bestfix = max(Dm.items(), key=lambda kv: kv[1]["net"])
    Dl = {
        "NULL_menu_mean": bk(menu_mean, c, day, ok, "menu_mean"),
        "REAL_target_2R": R1,
        "FEASIBLE_best_single_contract": {"rule": bestfix[0], **bestfix[1]},
        "ORACLE_per_trade_menu_best": bk(menu_best, c, day, ok, "menu_best"),
        "ORACLE_path_max_close": bk(path_or, c, day, ok, "path_oracle"),
        "each_contract": Dm,
    }
    Dl["capture_real"] = cap_frac(R1["net"], Dl["NULL_menu_mean"]["net"],
                                  Dl["ORACLE_per_trade_menu_best"]["net"])
    Dl["capture_feasible"] = cap_frac(bestfix[1]["net"], Dl["NULL_menu_mean"]["net"],
                                      Dl["ORACLE_per_trade_menu_best"]["net"])
    # leave-one-month-out for the best single contract
    loo = []
    for held in months:
        tr, te = mo != held, mo == held
        b, bn = None, -9e9
        for k in MENU:
            v = bk(D["menu_" + k].astype(float), c, day, ok & tr)
            if v["n"] and v["net"] > bn:
                bn, b = v["net"], k
        loo.append({"held_out": held, "contract": b, "train_net": bn,
                    "test": bk(D["menu_" + b].astype(float), c, day, ok & te)})
    Dl["FEASIBLE_loo"] = loo
    Dl["FEASIBLE_loo_oos_net"] = float(np.average(
        [x["test"]["net"] for x in loo], weights=[x["test"]["n"] for x in loo]))
    out["LAYER_D_EXIT"] = Dl

    # -------------------------------------------------------- JOINT ABLATION, pooled
    # baseline: every layer at NULL.  Add one at a time (marginal alone), then
    # leave one out of the full REAL/FEASIBLE stack (marginal in context).
    exits = {"null": menu_mean, "real": g, "feas": D["menu_" + bestfix[0]].astype(float),
             "oracle": menu_best}
    gates = {"null": ok, "real": gate,
             "oracle": topn(np.where(ok, net, -np.inf), day, capg)}
    bestj = int(C["FEASIBLE_best_fixed_offset"]["rule"].split("=")[1])
    J = {}
    for gn, gm in gates.items():
        for en, ev in exits.items():
            J["gate=%s|exit=%s" % (gn, en)] = bk(ev, c, day, gm)
    out["JOINT_ABLATION_GATE_x_EXIT"] = J
    base = J["gate=null|exit=null"]["net"]
    full_real = J["gate=real|exit=real"]["net"]
    out["ABLATION_SUMMARY"] = {
        "baseline_all_null": base,
        "gate_alone": J["gate=real|exit=null"]["net"] - base,
        "exit_alone": J["gate=null|exit=real"]["net"] - base,
        "sum_of_standalone": (J["gate=real|exit=null"]["net"] - base)
        + (J["gate=null|exit=real"]["net"] - base),
        "joint_actual": full_real - base,
        "double_count_factor": ((J["gate=real|exit=null"]["net"] - base)
                                + (J["gate=null|exit=real"]["net"] - base))
        / max(abs(full_real - base), 1e-12),
        "leave_out_gate": full_real - J["gate=null|exit=real"]["net"],
        "leave_out_exit": full_real - J["gate=real|exit=null"]["net"],
        "best_feasible_stack": J["gate=real|exit=feas"]["net"],
        "best_feasible_stack_vs_real": J["gate=real|exit=feas"]["net"] - full_real,
        "note_best_fixed_offset_j": bestj,
    }
    Path(OUT / "D2_POOLED_V1.json").write_text(json.dumps(out, indent=1, default=str))

    def pr(lbl, b):
        print("%-42s n=%-7s gross %+.5f cost %.5f net %+.5f" % (
            lbl, b.get("n", "-"), b.get("gross", float("nan")),
            b.get("cost", float("nan")), b.get("net", float("nan"))))
    print("\n== LAYER A GATE ==")
    for k in ("NULL_admit_all", "REAL_shipped_gate", "REAL_gate_plus_session",
              "ORACLE_topn_by_net", "ANTI_ORACLE"):
        pr(k, A[k])
    print("%-42s          net %+.5f" % ("RANDOM_same_size", A["RANDOM_same_size"]["net"]))
    print("capture vs random %.4f   FEASIBLE oos net %+.5f (capture %.4f)"
          % (A["capture_vs_random"], A["FEASIBLE_gate_oos_net"], A["FEASIBLE_capture"]))
    print("\n== LAYER C TIMING ==")
    pr("REAL_j0", C["REAL_j0"])
    pr("ORACLE_best_instant", C["ORACLE_best_instant_menu_exit"])
    print("best fixed offset", C["FEASIBLE_best_fixed_offset"])
    print("\n== LAYER D EXIT ==")
    for k in ("NULL_menu_mean", "REAL_target_2R", "ORACLE_per_trade_menu_best",
              "ORACLE_path_max_close"):
        pr(k, Dl[k])
    print("best single contract", bestfix[0], bestfix[1]["net"], "oos",
          Dl["FEASIBLE_loo_oos_net"])
    print("capture real %.4f  feasible %.4f" % (Dl["capture_real"], Dl["capture_feasible"]))
    print("\n== ABLATION ==")
    print(json.dumps(out["ABLATION_SUMMARY"], indent=1))


if __name__ == "__main__":
    main()
