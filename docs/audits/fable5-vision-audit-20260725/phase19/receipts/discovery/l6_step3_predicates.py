#!/usr/bin/env python3
"""l6 STEP 3 — independent gate PREDICATES, co-blocking, marginal contribution, and the
gate-removal frontier. Writes L6_PREDICATE_V1.json.

Every predicate is evaluated on EVERY row independently of pipeline order, which is what
the pool's single-reason columns cannot do (co-blockers are not projected — see D2).
"""
import json, os, sys
from itertools import combinations

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
from l6_lib import load, stats, mean, total, cost_corr  # noqa: E402


def f(r, k, d=0.0):
    v = r.get(k)
    return d if v is None else float(v)


# --- predicate definitions, each with its source citation -------------------
PREDS = {
    "P1_spread_cap_0p10": (lambda r: f(r, "spread_r") > 0.10,
                           "broker_net_cost_engine.py:857-866 vs max_spread_r (config:715)"),
    "P2_total_cost_0p15": (lambda r: f(r, "cost_r") > 0.15,
                           "broker_net_cost_engine.py:923-927 vs max_total_cost_r (config:716)"),
    "P3_ev_negative": (lambda r: f(r, "expected_net_r", 1.0) < 0.0,
                       "selector_v4.py:3827-3832 min() over EV estimators < 0"),
    "P4_selector_min_ev_0p10": (lambda r: f(r, "expected_net_r", 1.0) < 0.10,
                                "config:809 selector_v4_calibrated_min_expected_net_r"),
    "P5_prob_floor_0p58": (lambda r: f(r, "candidate_probability", 1.0) < 0.58,
                           "config:810 selector_v4_calibrated_min_probability"),
    "P6_fill_floor_0p45": (lambda r: f(r, "execution_fill_probability", 1.0) < 0.45,
                           "config:811 selector_v4_calibrated_min_fill_probability"),
    "P7_sched_fill_floor_0p80": (lambda r: f(r, "execution_fill_probability", 1.0) < 0.80,
                                 "config:1002 scheduler dynamic_budget_min_fill_probability"),
    "P8_sched_min_ev_0p20": (lambda r: f(r, "expected_net_r", 1.0) < 0.20,
                             "config:1000 scheduler dynamic_budget_min_expected_net_r"),
    "P9_off_session": (lambda r: r.get("route_session") == "off_configured_session",
                       "selector_v4.py:2556/4412 admission_quality_off_configured_session_entry_blocked"),
    "P10_sched_prob_0p58": (lambda r: f(r, "candidate_probability", 1.0) < 0.58,
                            "config:1001 scheduler dynamic_budget_min_probability"),
}
# EV recomputed with the spread over-charge corrected (spread/7.3)
def ev_corr(r, div=7.3):
    sp = f(r, "spread_r")
    return f(r, "expected_net_r", 1.0) + sp - sp / div


def main():
    rows = load()
    res = {"n_pool": len(rows), "POOL": stats(rows), "predicate_source": {k: v[1] for k, v in PREDS.items()}}
    M = {k: [bool(fn(r)) for r in rows] for k, (fn, _) in PREDS.items()}

    # --- per-predicate refused-set economics
    per = {}
    for k in PREDS:
        blocked = [r for r, b in zip(rows, M[k]) if b]
        passed = [r for r, b in zip(rows, M[k]) if not b]
        s = stats(blocked)
        s["passed_n"] = len(passed)
        s["passed_h_gross_mean"] = stats(passed)["h_gross_mean"] if passed else None
        s["passed_h_net_corr73_mean"] = stats(passed)["h_net_corr73_mean"] if passed else None
        s["discrimination_h_gross"] = (round(s["passed_h_gross_mean"] - s["h_gross_mean"], 5)
                                       if passed and s["h_gross_mean"] is not None else None)
        per[k] = s
    res["per_predicate"] = per

    # --- co-blocking: how many predicates does each row trip?
    cnt = [sum(M[k][i] for k in PREDS) for i in range(len(rows))]
    dist = {}
    for i, c in enumerate(cnt):
        dist.setdefault(c, []).append(rows[i])
    res["coblock_distribution"] = {str(c): stats(v) for c, v in sorted(dist.items())}

    # --- marginal / unique contribution: rows blocked ONLY by k
    uniq = {}
    for k in PREDS:
        only = [rows[i] for i in range(len(rows)) if M[k][i] and cnt[i] == 1]
        uniq[k] = stats(only)
        uniq[k]["blocked_n"] = per[k]["n"]
        uniq[k]["unique_share_pct"] = round(100 * len(only) / per[k]["n"], 2) if per[k]["n"] else None
    res["unique_block"] = uniq

    # --- pairwise containment: is k a subset of j (dead weight)?
    cont = {}
    for a, b in combinations(PREDS, 2):
        na = sum(M[a]); nb = sum(M[b])
        both = sum(1 for i in range(len(rows)) if M[a][i] and M[b][i])
        cont[f"{a}|{b}"] = {"n_a": na, "n_b": nb, "both": both,
                            "a_subset_of_b_pct": round(100 * both / na, 2) if na else None,
                            "b_subset_of_a_pct": round(100 * both / nb, 2) if nb else None}
    res["pairwise_containment"] = cont

    # --- corrected-cost EV counterfactual
    n_ev_neg = sum(M["P3_ev_negative"])
    flip = [r for r, b in zip(rows, M["P3_ev_negative"]) if b and ev_corr(r) >= 0.0]
    res["EV_GATE_AT_CORRECTED_COST"] = {
        "ev_negative_now_n": n_ev_neg,
        "would_flip_positive_at_spread_div_7p3_n": len(flip),
        "flip_share_pct": round(100 * len(flip) / n_ev_neg, 2) if n_ev_neg else None,
        "flipped_rows": stats(flip),
        "still_negative_rows": stats([r for r, b in zip(rows, M["P3_ev_negative"])
                                      if b and ev_corr(r) < 0.0]),
        "candidate_ev_r_min": min(f(r, "candidate_ev_r", 9) for r in rows),
        "candidate_ev_r_negative_n": sum(1 for r in rows if f(r, "candidate_ev_r", 9) < 0),
        "expected_net_r_negative_n": n_ev_neg,
        "note": "candidate_ev_r (the candidate's own expectancy) is never negative; the EV "
                "rejection is produced ONLY by the cost-subtracted members of the min()",
    }

    # --- greedy gate-removal frontier -------------------------------------
    def book(active):
        keep = [rows[i] for i in range(len(rows))
                if not any(M[k][i] for k in active)]
        return keep

    active = list(PREDS)
    frontier = []
    b = book(active)
    frontier.append({"removed": [], "n_active": len(active), **stats(b)})
    while active:
        best = None
        for k in active:
            trial = [x for x in active if x != k]
            s = stats(book(trial))
            score = s["h_net_corr73_total"]
            if best is None or score > best[1]:
                best = (k, score, s, trial)
        k, score, s, trial = best
        frontier.append({"removed_now": k, "removed": [x for x in PREDS if x not in trial],
                         "n_active": len(trial), **s})
        active = trial
    res["greedy_removal_frontier"] = frontier

    # --- single-gate-only books (what each gate ALONE would produce)
    solo = {}
    for k in PREDS:
        solo[k] = stats([rows[i] for i in range(len(rows)) if not M[k][i]])
    res["solo_gate_book"] = solo

    with open(os.path.join(D, "L6_PREDICATE_V1.json"), "w") as fh:
        json.dump(res, fh, indent=1)

    K = ("n", "takeable_n", "h_gross_mean", "h_win_pct", "h_net_corr73_mean", "h_net_corr73_total")
    print("POOL", {k: res["POOL"][k] for k in K})
    print("\n-- what each predicate REFUSES (h = honest no-look-ahead) --")
    for k, s in sorted(per.items(), key=lambda kv: -(kv[1]["h_gross_mean"] or -9)):
        print(f"{k:26s} blk={s['n']:6d} hG={str(s['h_gross_mean']):>9s} hNet={str(s['h_net_corr73_mean']):>9s} "
              f"| kept={s['passed_n']:6d} keptG={str(s['passed_h_gross_mean']):>9s} disc={str(s['discrimination_h_gross']):>9s}")
    print("\n-- co-block distribution --")
    for c, s in res["coblock_distribution"].items():
        print(f"  trips {c}: n={s['n']:6d} hG={s['h_gross_mean']} hNet={s['h_net_corr73_mean']}")
    print("\n-- unique blocks --")
    for k, s in sorted(uniq.items(), key=lambda kv: -kv[1]["n"]):
        print(f"{k:26s} uniq={s['n']:6d} ({s['unique_share_pct']}% of its blocks) hG={s['h_gross_mean']} hNet={s['h_net_corr73_mean']}")
    print("\n-- greedy removal frontier --")
    for fr in frontier:
        print(f"  active={fr['n_active']:2d} rm={str(fr.get('removed_now'))[:24]:24s} n={fr['n']:6d} "
              f"tk={fr['takeable_n']:6d} hG={fr['h_gross_mean']} hNet={fr['h_net_corr73_mean']} TOT={fr['h_net_corr73_total']}")


if __name__ == "__main__":
    main()
