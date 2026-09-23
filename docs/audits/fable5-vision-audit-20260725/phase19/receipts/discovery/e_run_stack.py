"""Lane e-stack main run: 64 arms x 3 months, ablation, marginals, interaction matrix."""
import json, os, sys, itertools, collections

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import e_score, e_lib  # noqa: E402

C = "TRAIL025"
DEPTH = 1.0
MONTHS = [("2026-01", "e_JAN_BASE_V1.jsonl.gz"),
          ("2026-02", "e_FEB_BASE_V1.jsonl.gz"),
          ("2026-03", "e_MAR_BASE_V1.jsonl.gz")]
L = e_score.LEVERS
OFF = {k: False for k in L}
ALL = {k: True for k in L}


def maskkey(a):
    return "".join("1" if a[k] else "0" for k in L)


res = {"contract": C, "depth_r": DEPTH, "levers": L, "months": {}}
for mon, f in MONTHS:
    rows = e_score.load(f"{D}/{f}")
    arms = e_score.allarms(rows, contract=C, depth_r=DEPTH)
    by = {}
    for a in arms:
        a.pop("equity_net_true", None)
        a.pop("day_index", None)
        by[maskkey(a["arm"])] = a
    base = by["000000"]
    full = by["111111"]

    # ---- marginal value of each lever ALONE (baseline + one)
    marg = {}
    for i, k in enumerate(L):
        m = ["0"] * 6
        m[i] = "1"
        a = by["".join(m)]
        marg[k] = {"net_true_per_opportunity": a["net_true_per_opportunity"],
                   "delta_vs_baseline": round(a["net_true_per_opportunity"]
                                              - base["net_true_per_opportunity"], 6),
                   "n_trades": a["n_trades"],
                   "gross_per_trade": a["gross_per_trade"]}
    # ---- ablation: full stack minus one
    abl = {}
    for i, k in enumerate(L):
        m = list("111111")
        m[i] = "0"
        a = by["".join(m)]
        abl[k] = {"net_true_per_opportunity": a["net_true_per_opportunity"],
                  "marginal_contribution": round(full["net_true_per_opportunity"]
                                                 - a["net_true_per_opportunity"], 6),
                  "n_trades": a["n_trades"]}
    sum_alone = sum(marg[k]["delta_vs_baseline"] for k in L)
    joint = round(full["net_true_per_opportunity"] - base["net_true_per_opportunity"], 6)
    sum_abl = sum(abl[k]["marginal_contribution"] for k in L)

    # ---- pairwise interaction: d(i | j on) - d(i | j off), all other levers OFF
    inter = {}
    for i, j in itertools.permutations(range(6), 2):
        m00 = ["0"] * 6
        mi = ["0"] * 6; mi[i] = "1"
        mj = ["0"] * 6; mj[j] = "1"
        mij = ["0"] * 6; mij[i] = "1"; mij[j] = "1"
        d_off = (by["".join(mi)]["net_true_per_opportunity"]
                 - by["".join(m00)]["net_true_per_opportunity"])
        d_on = (by["".join(mij)]["net_true_per_opportunity"]
                - by["".join(mj)]["net_true_per_opportunity"])
        inter[f"{L[i]}|{L[j]}"] = {"delta_alone": round(d_off, 6),
                                   "delta_given_other": round(d_on, 6),
                                   "interaction": round(d_on - d_off, 6),
                                   "kind": ("substitute" if d_on < d_off - 1e-6
                                            else "complement" if d_on > d_off + 1e-6
                                            else "independent")}
    # ---- decline-set overlap (population geometry, cost-free)
    def declset(k):
        arm = {k: True}
        return {(r["cid"], r["dt"]) for r in rows if not e_score.eligible(r, arm, DEPTH)}
    ds = {k: declset(k) for k in L if k != "B1_EXIT"}
    ov = {}
    for a, b in itertools.combinations(ds, 2):
        A, B = ds[a], ds[b]
        ov[f"{a}&{b}"] = {"nA": len(A), "nB": len(B), "inter": len(A & B),
                          "jaccard": round(len(A & B) / len(A | B), 4) if (A | B) else None,
                          "A_subset_of_B": len(A - B) == 0, "B_subset_of_A": len(B - A) == 0}

    res["months"][mon] = {
        "n_pool": len(rows), "baseline": base, "full_stack": full,
        "marginal_alone": marg, "ablation_full_minus_one": abl,
        "sum_of_alone_deltas": round(sum_alone, 6),
        "joint_delta": joint,
        "overlap_fraction": round(1 - joint / sum_alone, 4) if sum_alone else None,
        "sum_of_ablation_marginals": round(sum_abl, 6),
        "pairwise_interaction": inter, "decline_set_overlap": ov,
        "all_arms": {k: {kk: v[kk] for kk in
                         ("n_trades", "gross_per_opportunity", "net_true_per_opportunity",
                          "gross_per_trade", "net_true_per_trade", "win_rate",
                          "t_net_true", "days_net_true_positive", "n_days",
                          "mean_cost_true_charged", "max_drawdown_net_true_R",
                          "total_net_true_R", "total_gross_R")}
                     for k, v in by.items()},
    }
    print(mon, "base", base["net_true_per_opportunity"], "full", full["net_true_per_opportunity"],
          "sum_alone", round(sum_alone, 5), "joint", joint, flush=True)

json.dump(res, open(f"{D}/E_STACK_MAIN_V1.json", "w"), indent=1)
print("written E_STACK_MAIN_V1.json")
