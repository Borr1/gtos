#!/usr/bin/env python3
"""l6 STEP 4 — EXHAUSTIVE gate-subset sweep (2^k books) + the enacted-gate ledger.
Writes L6_SWEEP_V1.json."""
import json, os, sys
from itertools import product

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
from l6_lib import load, stats, cost_corr  # noqa: E402


def f(r, k, d=0.0):
    v = r.get(k)
    return d if v is None else float(v)


PREDS = {
    "P1_spread_cap_0p10": lambda r: f(r, "spread_r") > 0.10,
    "P2_total_cost_0p15": lambda r: f(r, "cost_r") > 0.15,
    "P3_ev_negative": lambda r: f(r, "expected_net_r", 1.0) < 0.0,
    "P4_selector_min_ev_0p10": lambda r: f(r, "expected_net_r", 1.0) < 0.10,
    "P6_fill_floor_0p45": lambda r: f(r, "execution_fill_probability", 1.0) < 0.45,
    "P7_sched_fill_floor_0p80": lambda r: f(r, "execution_fill_probability", 1.0) < 0.80,
    "P8_sched_min_ev_0p20": lambda r: f(r, "expected_net_r", 1.0) < 0.20,
    "P9_off_session": lambda r: r.get("route_session") == "off_configured_session",
}
# gates the system does NOT have, offered as comparators
EXTRA = {
    "X1_drop_born_past_stop": lambda r: r.get("born") == "born_past_stop",
    "X2_spread_cap_at_corrected_0p10": lambda r: f(r, "spread_r") / 7.3 > 0.10,
    "X3_INVERTED_fill_floor_block_high": lambda r: f(r, "execution_fill_probability", 0.0) >= 0.92,
}
ENACTED = {
    "E_cost_authority": lambda r: r.get("final_blocker_class") == "cost_authority",
    "E_offsession_enacted": lambda r: r.get("selector_reason") == "admission_quality_off_configured_session_entry_blocked",
    "E_source_bound_router": lambda r: str(r.get("selector_reason", "")).startswith("source_bound_router_refusal"),
    "E_no_shadow_sleeve": lambda r: r.get("selector_reason") == "ultimate_candidate_package_no_shadow_sleeve_match",
    "E_non_admission_sleeve": lambda r: r.get("selector_reason") == "ultimate_candidate_package_non_admission_sleeve_only",
    "E_dynamic_router": lambda r: "dynamic_router_ref" in str(r.get("selector_reason", "")),
    "E_numeric_disagreement": lambda r: r.get("selector_reason") == "numeric_confluence_structured_disagreement",
    "E_pkg_authority": lambda r: r.get("risk_finalizer_reason") == "package_executable_authority_required_not_met",
    "E_fill_floor_veto": lambda r: "fill_floor" in str(r.get("miss_reason", "")),
    "E_displacement_veto": lambda r: "displacement_quality" in str(r.get("miss_reason", "")),
    "E_signed_authority_invalid": lambda r: "signed_authority_invalid" in str(r.get("miss_reason", "")),
    "E_marketable_guard": lambda r: "marketable_limit_entry_guard" in str(r.get("risk_finalizer_reason", "")),
    "E_daily_lockout": lambda r: "daily_loss_lockout" in str(r.get("risk_finalizer_reason", "")),
    "E_memory_guard": lambda r: "adaptive_replay_memory_guard" in str(r.get("risk_finalizer_reason", "")),
    "E_source_required_fail_closed": lambda r: "source_required_fail_closed" in str(r.get("miss_reason", "")),
    "E_scheduler_vetoed": lambda r: str(r.get("miss_reason", "")).startswith("scheduler_vetoed"),
    "E_scheduler_rank_limited": lambda r: str(r.get("miss_reason", "")).startswith("scheduler_rank_limited"),
    "E_probability_confluence": lambda r: r.get("selector_reason") == "broker_net_probability_confluence_lifecycle_gate",
    "E_source_required_hold": lambda r: "source_required_h" in str(r.get("selector_reason", "")),
}


def main():
    rows = load()
    res = {"n_pool": len(rows), "POOL": stats(rows)}
    keys = list(PREDS)
    M = {k: [bool(PREDS[k](r)) for r in rows] for k in keys}

    books = []
    for mask in product([0, 1], repeat=len(keys)):
        active = [k for k, m in zip(keys, mask) if m]
        keep = [rows[i] for i in range(len(rows))
                if not any(M[k][i] for k in active)]
        if not keep:
            continue
        s = stats(keep)
        s["active"] = active
        s["n_active"] = len(active)
        books.append(s)
    res["n_books"] = len(books)
    # global best per-trade with a minimum book size
    for minn in (100, 250, 500, 1000, 2000):
        cand = [b for b in books if b["takeable_n"] >= minn]
        best = max(cand, key=lambda b: b["h_net_corr73_mean"])
        bestg = max(cand, key=lambda b: b["h_gross_mean"])
        res[f"best_min{minn}_by_net"] = best
        res[f"best_min{minn}_by_gross"] = bestg
    # best at each active-count
    per_size = {}
    for k in range(len(keys) + 1):
        cand = [b for b in books if b["n_active"] == k and b["takeable_n"] >= 250]
        if cand:
            per_size[str(k)] = max(cand, key=lambda b: b["h_net_corr73_mean"])
    res["best_by_active_count"] = per_size
    # the as-shipped full stack
    full = [b for b in books if b["n_active"] == len(keys)][0]
    res["FULL_STACK"] = full
    solo = {k: [b for b in books if b["active"] == [k]][0] for k in keys}
    res["SOLO"] = solo

    # marginal value of each gate at the as-shipped stack: remove one
    marg = {}
    for k in keys:
        trial = sorted([x for x in keys if x != k])
        b = [bb for bb in books if sorted(bb["active"]) == trial][0]
        marg[k] = {"book_without_it_n": b["n"], "book_without_it_h_net": b["h_net_corr73_mean"],
                   "full_stack_h_net": full["h_net_corr73_mean"],
                   "delta_h_net_from_keeping_it": round(full["h_net_corr73_mean"] - b["h_net_corr73_mean"], 5),
                   "delta_trades_from_keeping_it": full["n"] - b["n"]}
    res["marginal_at_full_stack"] = marg

    # extras
    ex = {}
    for k, fn in EXTRA.items():
        blocked = [r for r in rows if fn(r)]
        kept = [r for r in rows if not fn(r)]
        ex[k] = {"blocked": stats(blocked), "kept": stats(kept)}
    res["extra_gates"] = ex

    # ENACTED gate ledger (label-level, one row = one reason as the pipeline recorded it)
    en = {}
    for k, fn in ENACTED.items():
        blocked = [r for r in rows if fn(r)]
        if not blocked:
            continue
        s = stats(blocked)
        s["h_gross_vs_pool"] = round((s["h_gross_mean"] or 0) - res["POOL"]["h_gross_mean"], 5)
        s["first_emission"] = stats([r for r in blocked if r.get("is_first_emission")])
        en[k] = s
    res["enacted_gate_ledger"] = en

    with open(os.path.join(D, "L6_SWEEP_V1.json"), "w") as fh:
        json.dump(res, fh, indent=1)

    K = ("n", "takeable_n", "h_gross_mean", "h_win_pct", "h_net_corr73_mean", "h_net_corr73_total")
    print("POOL      ", {k: res["POOL"][k] for k in K})
    print("FULL_STACK", {k: full[k] for k in K})
    print("\n-- best book at each active-gate count (takeable>=250) --")
    for k, b in per_size.items():
        print(f"  k={k} n={b['n']:6d} tk={b['takeable_n']:6d} hG={b['h_gross_mean']} hNet={b['h_net_corr73_mean']} :: {b['active']}")
    print("\n-- marginal value of each gate at the full stack --")
    for k, m in sorted(marg.items(), key=lambda kv: kv[1]["delta_h_net_from_keeping_it"]):
        print(f"  {k:26s} delta_hNet={m['delta_h_net_from_keeping_it']:+.5f} costs_trades={m['delta_trades_from_keeping_it']:6d}")
    print("\n-- ENACTED gates, sorted by h_gross of what they refused --")
    for k, s in sorted(en.items(), key=lambda kv: -(kv[1]["h_gross_mean"] or -9)):
        fe = s["first_emission"]
        print(f"  {k:30s} n={s['n']:6d} tk={s['takeable_n']:6d} hG={str(s['h_gross_mean']):>9s} vsPool={s['h_gross_vs_pool']:+.4f} "
              f"hNet={str(s['h_net_corr73_mean']):>9s} TOT={str(s['h_net_corr73_total']):>10s} | 1stEm n={fe['n']:5d} hG={fe['h_gross_mean']}")


if __name__ == "__main__":
    main()
