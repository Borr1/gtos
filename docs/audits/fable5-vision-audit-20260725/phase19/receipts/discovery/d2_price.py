"""d2_price — the layer capture table, the roster gate ledger, the ranker test,
and the joint ablation.  Reads the pooled artifacts d2_layers.py wrote.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

SEED = 20260806
NDRAW = 500
OUT = Path("/tmp/d2/D2_LAYERS_V1.json")


def load():
    z = np.load("/tmp/d2/pooled.npz", allow_pickle=False)
    return {k: z[k] for k in z.files}


def econ(net, day):
    net = np.asarray(net, float)
    m = np.isfinite(net)
    net, day = net[m], np.asarray(day)[m]
    if net.size == 0:
        return {"n": 0}
    by = defaultdict(float)
    for a, x in zip(day, net):
        by[a] += x
    return {"n": int(net.size), "net_r_per_trade": float(net.mean()),
            "total_net_r": float(net.sum()), "n_days": len(by),
            "days_positive": int(sum(1 for v in by.values() if v > 0))}


def topk(score, day, cap, elig):
    keep = np.zeros(score.size, dtype=bool)
    by = defaultdict(list)
    for a in np.nonzero(elig & np.isfinite(score))[0]:
        by[day[a]].append(a)
    for dd, aa in by.items():
        k = cap.get(dd, 0)
        if k <= 0:
            continue
        aa = np.asarray(aa)
        keep[aa[np.argsort(-score[aa])[:k]]] = True
    return keep


def randk_mean(net, day, cap, elig, rng, ndraw=NDRAW):
    """Expected net/trade and total of drawing cap[d] eligible rows uniformly per day."""
    by = defaultdict(list)
    for a in np.nonzero(elig & np.isfinite(net))[0]:
        by[day[a]].append(a)
    per, tot = [], []
    for _ in range(ndraw):
        acc, cnt = 0.0, 0
        for dd, aa in by.items():
            k = min(cap.get(dd, 0), len(aa))
            if k <= 0:
                continue
            sel = rng.choice(np.asarray(aa), size=k, replace=False)
            acc += float(net[sel].sum())
            cnt += k
        if cnt:
            per.append(acc / cnt)
            tot.append(acc)
    return {"n_draws": len(per), "net_r_per_trade": float(np.mean(per)),
            "sd_net_r_per_trade": float(np.std(per)),
            "total_net_r": float(np.mean(tot)),
            "n_selected": int(sum(min(cap.get(d, 0), len(a)) for d, a in by.items()))}


def capture(real, null, oracle):
    den = oracle - null
    return None if abs(den) < 1e-12 else (real - null) / den


def main():
    rng = np.random.default_rng(SEED)
    P = load()
    stage = P["stage"].astype(str)
    day = P["day"].astype(str)
    net = P["net"]
    taken = P["taken"]
    sched = P["sched"]
    res = {"lane": "d2", "seed": SEED, "random_draws": NDRAW}

    # ---- restrict to the arm's own trading days (whole days the sealed arm never ran
    #      are present in the regenerated roster and have no arm record at all)
    armday = set()
    for a in np.nonzero(stage != "G0_no_arm_record")[0]:
        armday.add(day[a])
    on = np.array([d in armday for d in day])
    Q = on & (stage != "G0_no_arm_record") & np.isfinite(net)
    res["population"] = {
        "roster_rows_all": int(net.size),
        "rows_on_arm_trading_days": int(on.sum()),
        "rows_matched_and_priced_Q": int(Q.sum()),
        "residual_unmatched_on_arm_days": int((on & (stage == "G0_no_arm_record")).sum()),
        "residual_unmatched_share": float((on & (stage == "G0_no_arm_record")).sum() / max(on.sum(), 1)),
        "arm_trading_days": len(armday),
        "taken": int((taken & Q).sum()),
        "reached_scheduler": int((sched & Q).sum()),
        "reached_scheduler_share_of_Q": float((sched & Q).sum() / max(Q.sum(), 1)),
        "Q_net_r_per_row": float(net[Q].mean()),
        "Q_total_net_r": float(net[Q].sum()),
    }

    cap = Counter(day[taken & Q])
    kd = dict(cap)
    res["capacity"] = {"total_trades": int(sum(kd.values())), "days_with_a_trade": len(kd),
                       "max_per_day": int(max(kd.values())) if kd else 0}

    # ================================================================= 1. GATE
    real_gate = econ(net[taken & Q], day[taken & Q])
    null_gate = randk_mean(net, day, kd, Q, rng)
    orc_full = topk(net, day, kd, Q)
    orc_short = topk(net, day, kd, Q & sched)
    worst_full = topk(-net, day, kd, Q)
    G = {
        "REAL_shipped_gate": real_gate,
        "NULL_random_same_k_same_days": null_gate,
        "ORACLE_top_k_whole_roster": econ(net[orc_full], day[orc_full]),
        "ORACLE_top_k_scheduler_shortlist": econ(net[orc_short], day[orc_short]),
        "ANTI_ORACLE_worst_k_whole_roster": econ(net[worst_full], day[worst_full]),
        "ungated_whole_roster": econ(net[Q], day[Q]),
    }
    G["capture_vs_roster_oracle"] = capture(
        real_gate["net_r_per_trade"], null_gate["net_r_per_trade"],
        G["ORACLE_top_k_whole_roster"]["net_r_per_trade"])
    G["capture_vs_shortlist_oracle"] = capture(
        real_gate["net_r_per_trade"], null_gate["net_r_per_trade"],
        G["ORACLE_top_k_scheduler_shortlist"]["net_r_per_trade"])
    G["gap_to_roster_oracle_r_per_trade"] = (
        G["ORACLE_top_k_whole_roster"]["net_r_per_trade"] - real_gate["net_r_per_trade"])
    G["gap_to_roster_oracle_total_r"] = (
        G["ORACLE_top_k_whole_roster"]["total_net_r"] - real_gate["total_net_r"])
    res["LAYER_1_GATE"] = G

    # gate at a WIDER capacity, so the number is not 507-row noise
    for mult in (10, 100):
        kw = {d: k * mult for d, k in kd.items()}
        nu = randk_mean(net, day, kw, Q, rng, ndraw=120)
        oc = topk(net, day, kw, Q)
        res[f"LAYER_1_GATE_capacity_x{mult}"] = {
            "NULL": nu, "ORACLE": econ(net[oc], day[oc]),
            "note": "the real gate has no counterpart at this capacity; this prices how "
                    "fast the oracle's edge decays as the gate is loosened",
        }

    # ================================================================= 2. RANKING
    short = Q & sched
    rank_real = econ(net[taken & Q], day[taken & Q])
    rank_null = randk_mean(net, day, kd, short, rng)
    rank_orc = topk(net, day, kd, short)
    R = {
        "universe": {"n": int(short.sum()),
                     "net_r_per_row": float(net[short].mean()),
                     "share_of_roster": float(short.sum() / max(Q.sum(), 1))},
        "REAL_as_run_neutral_hash": rank_real,
        "NULL_random_from_shortlist": rank_null,
        "ORACLE_top_k_from_shortlist": econ(net[rank_orc], day[rank_orc]),
    }
    R["capture"] = capture(rank_real["net_r_per_trade"], rank_null["net_r_per_trade"],
                           R["ORACLE_top_k_from_shortlist"]["net_r_per_trade"])
    # every pre-decision score the arm published, used as the ranker
    scorers = {
        "candidate_ev_r": P["ev"], "expected_net_r": P["enet"],
        "candidate_probability": P["prob"], "fill_probability": P["fillp"],
        "candidate_confidence": P["conf"], "neg_expected_cost_r": -P["cr"],
        "ev_x_prob": P["ev"] * P["prob"],
        "expected_net_r_x_fillp": P["enet"] * P["fillp"],
    }
    R["score_rankers_on_the_shortlist"] = {}
    for nm, sc in scorers.items():
        el = short & np.isfinite(sc)
        if el.sum() < 100:
            continue
        m = topk(sc, day, kd, el)
        mm = topk(-sc, day, kd, el)
        # rank correlation against outcome, pooled over decision days
        e = econ(net[m], day[m])
        e["inverted_same_k"] = econ(net[mm], day[mm])
        e["coverage_on_shortlist"] = float(el.sum() / max(short.sum(), 1))
        e["capture"] = capture(e["net_r_per_trade"], rank_null["net_r_per_trade"],
                               R["ORACLE_top_k_from_shortlist"]["net_r_per_trade"])
        R["score_rankers_on_the_shortlist"][nm] = e
    # and the same rankers over the WHOLE roster (item 4: rank vs outcome on the roster)
    R["score_rankers_on_the_whole_roster"] = {}
    for nm, sc in scorers.items():
        el = Q & np.isfinite(sc)
        if el.sum() < 100:
            continue
        m = topk(sc, day, kd, el)
        e = econ(net[m], day[m])
        e["coverage_on_roster"] = float(el.sum() / max(Q.sum(), 1))
        # decile table by score, over the whole eligible set
        v = sc[el]
        nn = net[el]
        qs = np.quantile(v, np.linspace(0, 1, 11))
        dec = []
        for i in range(10):
            lo, hi = qs[i], qs[i + 1]
            mask = (v >= lo) & (v <= hi) if i == 9 else (v >= lo) & (v < hi)
            if mask.sum():
                dec.append({"decile": i + 1, "n": int(mask.sum()),
                            "net_r_per_row": float(nn[mask].mean()),
                            "lo": float(lo), "hi": float(hi)})
        e["deciles"] = dec
        # Spearman over the whole eligible set
        rv = np.argsort(np.argsort(v)).astype(float)
        rn = np.argsort(np.argsort(nn)).astype(float)
        e["spearman_vs_outcome"] = float(np.corrcoef(rv, rn)[0, 1])
        R["score_rankers_on_the_whole_roster"][nm] = e
    res["LAYER_2_RANKING"] = R

    # ================================================================= 3. SIZING
    tn = net[taken & Q]
    td = day[taken & Q]
    nt = tn.size
    # oracle sizing at matched TOTAL risk: weights proportional to outcome rank, and a
    # realistic two-bin sizer (2x on the better half, 0 on the worst half)
    order = np.argsort(np.argsort(tn))
    w_prop = (order + 1) / (order + 1).mean() / nt * nt      # mean weight 1
    half = tn >= np.median(tn)
    w_bin = np.where(half, 2.0, 0.0)
    S = {
        "REAL_R0_fixed_equal_account_risk": {
            "n": nt, "net_r_per_trade": float(tn.mean()), "total_net_r": float(tn.sum()),
            "weights": "every trade exactly one risk unit (0.1 % of equity), by arm construction",
        },
        "NULL_equal_weight": {"net_r_per_trade": float(tn.mean()),
                              "note": "identical to REAL — R0 IS the equal-weight null"},
        "ORACLE_rank_proportional_same_total_risk": {
            "net_r_per_trade": float((tn * w_prop).sum() / nt),
            "total_net_r": float((tn * w_prop).sum())},
        "ORACLE_two_bin_2x_on_better_half_same_total_risk": {
            "net_r_per_trade": float((tn * w_bin).sum() / nt),
            "total_net_r": float((tn * w_bin).sum())},
        "capture": 0.0,
        "capture_note": "exactly zero BY CONSTRUCTION: the sealed arms are R0 = "
                        "fixed_equal_account_risk, so the shipped sizer is the null.",
        "shipped_dynamic_sizer_R1_sealed_january": {
            "effect_cash_per_accepted_risk_dollar": -0.110527807547,
            "classification": "material_negative",
            "source": "JANUARY_BANK.md §1 factorial_effects (S0R1 - S0R0)",
        },
    }
    res["LAYER_3_SIZING"] = S

    # ================================================================= 4. ENTRY TIMING
    Ez = np.load("/tmp/d2/pooled_entry.npz", allow_pickle=False)
    st = Ez["stamps"]
    ecost = Ez["cost"]
    eday = np.char.add(np.char.add(Ez["mo"].astype(str), "|"), Ez["day"].astype(str))
    okat = np.isfinite(st[0])
    onq = np.array([d in armday for d in eday]) & okat
    rj = st[0][onq] - ecost[onq]
    oj = np.nanmax(st[:, onq], axis=0) - ecost[onq]
    per_j = {}
    for j in range(st.shape[0]):
        vj = st[j][onq] - ecost[onq]
        per_j[j] = float(np.nanmean(vj))
    rnd = []
    for _ in range(200):
        pick = rng.integers(0, st.shape[0], size=int(onq.sum()))
        vals = st[pick, np.nonzero(onq)[0]] - ecost[onq]
        rnd.append(float(np.nanmean(vals)))
    T = {
        "universe": {"n": int(onq.sum()), "note": "at-market families only; the toll is held "
                     "at the shipped fill for every stamp (f2's convention)"},
        "REAL_m15_close_j0": {"net_r_per_trade": float(np.nanmean(rj))},
        "NULL_random_stamp": {"net_r_per_trade": float(np.mean(rnd)),
                              "sd": float(np.std(rnd))},
        "ORACLE_best_stamp": {"net_r_per_trade": float(np.nanmean(oj))},
        "per_stamp_net_r_per_trade": per_j,
        "best_single_fixed_stamp": max(per_j, key=per_j.get),
        "best_single_fixed_stamp_value": max(per_j.values()),
        "real_minus_best_fixed_stamp": float(np.nanmean(rj)) - max(per_j.values()),
    }
    T["capture"] = capture(T["REAL_m15_close_j0"]["net_r_per_trade"],
                           T["NULL_random_stamp"]["net_r_per_trade"],
                           T["ORACLE_best_stamp"]["net_r_per_trade"])
    res["LAYER_4_ENTRY_TIMING"] = T
    del Ez, st

    # ================================================================= 5. EXIT
    Xz = np.load("/tmp/d2/pooled_exit.npz", allow_pickle=False)
    menu = Xz["menu"]
    xcost = Xz["cost"]
    xday = np.char.add(np.char.add(Xz["mo"].astype(str), "|"), Xz["day"].astype(str))
    xok = np.isfinite(Xz["shipped"])
    xq = np.array([d in armday for d in xday]) & xok
    names = json.loads(Path("/tmp/d2/fr/202601.meta.json").read_text())["menu_names"]
    per_c = {}
    for i, nm in enumerate(names):
        per_c[nm] = float(np.nanmean(menu[i][xq] - xcost[xq]))
    shipped_net = float(np.nanmean(Xz["shipped"][xq] - xcost[xq]))
    menu_best = float(np.nanmean(np.nanmax(menu[:, xq], axis=0) - xcost[xq]))
    path_or = float(np.nanmean(Xz["path"][xq] - xcost[xq]))
    null_c = float(np.mean(list(per_c.values())))
    Xo = {
        "universe": {"n": int(xq.sum()), "note": "at-market families only"},
        "REAL_shipped_target_2R": {"net_r_per_trade": shipped_net},
        "NULL_random_contract_from_the_13_menu": {"net_r_per_trade": null_c},
        "ORACLE_best_menu_contract_per_trade": {"net_r_per_trade": menu_best},
        "ORACLE_best_close_on_the_path": {"net_r_per_trade": path_or},
        "per_contract_net_r_per_trade": dict(sorted(per_c.items(), key=lambda kv: -kv[1])),
        "best_single_fixed_contract": max(per_c, key=per_c.get),
        "best_single_fixed_contract_value": max(per_c.values()),
        "real_minus_best_fixed_contract": shipped_net - max(per_c.values()),
    }
    Xo["capture_vs_menu_oracle"] = capture(shipped_net, null_c, menu_best)
    Xo["capture_vs_path_oracle"] = capture(shipped_net, null_c, path_or)
    res["LAYER_5_EXIT"] = Xo

    # ================================================================= 6. JOINT
    ti = np.nonzero(taken & Q)[0]
    Xmap = {}
    # index of each taken row inside the exit/entry frames is the same row order
    joint = {}
    base = float(net[ti].mean())
    joint["BASE_real_book"] = {"n": int(ti.size), "net_r_per_trade": base,
                               "total_net_r": float(net[ti].sum())}
    # oracle exit / oracle entry on the SAME taken rows (at-market ones only)
    at_taken = ti[np.isfinite(Xz["shipped"][ti])]
    if at_taken.size:
        b2 = float(np.nanmean(Xz["shipped"][at_taken] - xcost[at_taken]))
        oe = float(np.nanmean(np.nanmax(menu[:, at_taken], axis=0) - xcost[at_taken]))
        joint["taken_at_market_subset"] = {"n": int(at_taken.size), "real": b2,
                                           "oracle_exit_menu": oe,
                                           "delta_oracle_exit": oe - b2}
    res["LAYER_6_JOINT_on_the_real_book"] = joint

    # marginal-in-context on a common wide capacity: real gate cannot be widened, so the
    # joint ablation is run on the whole at-market roster where every layer has an arm
    W = {}
    wq = xq
    wnet_real = Xz["shipped"][wq] - xcost[wq]
    Ez2 = np.load("/tmp/d2/pooled_entry.npz", allow_pickle=False)
    st2 = Ez2["stamps"]
    wnet_oe = np.nanmax(menu[:, wq], axis=0) - xcost[wq]
    wnet_oi = np.nanmax(st2[:, wq], axis=0) - xcost[wq]
    # oracle entry AND exit together needs the joint frame; the menu at the best stamp is
    # not stored, so the joint cell here is entry-oracle-under-shipped-exit + exit oracle
    # measured on the SAME rows and reported as a bound, not a product.
    base_w = float(np.nanmean(wnet_real))
    W["base_all_real_at_market_roster"] = {"n": int(wq.sum()), "net_r_per_trade": base_w}
    W["marginal_oracle_exit"] = float(np.nanmean(wnet_oe)) - base_w
    W["marginal_oracle_entry"] = float(np.nanmean(wnet_oi)) - base_w
    kd_w = {d: max(1, k) for d, k in kd.items()}
    ogate = topk(np.where(wq, np.nan_to_num(Xz["shipped"] - xcost, nan=-1e9), -1e9),
                 xday, kd_w, wq)
    W["marginal_oracle_gate_at_real_capacity"] = (
        float(np.nanmean((Xz["shipped"] - xcost)[ogate])) - base_w)
    W["sum_of_marginals"] = (W["marginal_oracle_exit"] + W["marginal_oracle_entry"]
                             + W["marginal_oracle_gate_at_real_capacity"])
    # joint: gate oracle chosen on the ORACLE-EXIT outcome, then priced at oracle exit
    val_oe = np.full(xday.size, -1e9)
    val_oe[np.nonzero(wq)[0]] = wnet_oe
    ogate2 = topk(val_oe, xday, kd_w, wq)
    W["joint_gate_plus_exit_oracle"] = float(np.nanmean(val_oe[ogate2])) - base_w
    W["double_count_ratio_gate_plus_exit"] = (
        (W["marginal_oracle_exit"] + W["marginal_oracle_gate_at_real_capacity"])
        / W["joint_gate_plus_exit_oracle"] if W["joint_gate_plus_exit_oracle"] else None)
    res["LAYER_7_JOINT_ABLATION"] = W

    # ================================================================= 8. GATE LEDGER
    L = {}
    for s in sorted(set(stage[Q])):
        m = Q & (stage == s)
        e = econ(net[m], day[m])
        e["share_of_roster"] = float(m.sum() / max(Q.sum(), 1))
        e["reached_scheduler_share"] = float(sched[m].mean()) if m.sum() else None
        e["born_past_stop_share"] = float(P["born"][m].mean()) if m.sum() else None
        e["filled_share"] = float(P["filled"][m].mean()) if m.sum() else None
        e["mean_toll_r"] = float(np.nanmean(P["cost"][m])) if m.sum() else None
        L[s] = e
    res["GATE_OPPORTUNITY_LEDGER_ON_THE_ROSTER"] = dict(
        sorted(L.items(), key=lambda kv: -kv[1].get("n", 0)))

    # marginal value of each gate stage: what admitting its refusals AS WELL would do
    marg = {}
    for s in L:
        if s == "TAKEN":
            continue
        m = Q & (stage == s)
        if m.sum() < 50:
            continue
        marg[s] = {
            "n_refused": int(m.sum()),
            "net_r_per_trade_if_taken": float(net[m].mean()),
            "total_net_r_if_all_taken": float(net[m].sum()),
            "vs_roster_mean": float(net[m].mean() - net[Q].mean()),
        }
    res["GATE_STAGE_MARGINAL_VALUE"] = dict(
        sorted(marg.items(), key=lambda kv: kv[1]["net_r_per_trade_if_taken"]))

    OUT.write_text(json.dumps(res, indent=1, default=float))
    print("WROTE", OUT, flush=True)
    print(json.dumps({k: v for k, v in res.items()
                      if k in ("population", "capacity")}, indent=1))


if __name__ == "__main__":
    main()
