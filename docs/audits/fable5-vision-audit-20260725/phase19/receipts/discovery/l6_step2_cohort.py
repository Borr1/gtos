#!/usr/bin/env python3
"""l6 STEP 2 — the positive-refusal COHORT: overlap, composition, robustness.
Writes L6_POSITIVE_COHORT_V1.json."""
import json, os, sys
from collections import Counter

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
from l6_lib import load, stats, mean, cost_corr  # noqa: E402

SIGN = "scheduler_materialization_skipped_package_positive_reduce_risk_signed_authority_invalid"

LABELS = {
    "A_numeric_disagreement": lambda r: r.get("selector_reason") == "numeric_confluence_structured_disagreement",
    "B_signed_authority_invalid": lambda r: r.get("miss_reason") == SIGN,
    "C_execution_fillability": lambda r: r.get("final_blocker_class") == "execution_fillability",
    "D_reduce_risk_action": lambda r: r.get("effective_selector_action") == "reduce-risk",
    "E_daily_lockout": lambda r: r.get("final_blocker_class") == "daily_lockout",
    "F_marketable_guard": lambda r: r.get("final_blocker_class") == "marketable_guard",
}


def main():
    rows = load()
    res = {"n_pool": len(rows), "POOL": stats(rows)}
    sets = {k: set() for k in LABELS}
    for i, r in enumerate(rows):
        for k, fn in LABELS.items():
            if fn(r):
                sets[k].add(i)
    res["label_n"] = {k: len(v) for k, v in sets.items()}
    # pairwise overlap
    ov = {}
    for a in LABELS:
        for b in LABELS:
            if a < b:
                ov[f"{a}&{b}"] = len(sets[a] & sets[b])
    res["pairwise_overlap"] = ov
    union = set()
    for v in sets.values():
        union |= v
    res["union_n"] = len(union)
    ur = [rows[i] for i in union]
    res["UNION"] = stats(ur)
    # first-emission robustness
    res["UNION_first_emission"] = stats([r for r in ur if r.get("is_first_emission")])
    # per-label detail incl. composition + robustness
    det = {}
    for k, v in sets.items():
        sub = [rows[i] for i in v]
        s = stats(sub)
        s["first_emission"] = stats([r for r in sub if r.get("is_first_emission")])
        s["by_family"] = {f: {"n": c} for f, c in Counter(r.get("origin_family") for r in sub).most_common(6)}
        for f in s["by_family"]:
            fr = [r for r in sub if r.get("origin_family") == f and r.get("takeable")]
            s["by_family"][f]["h_gross_mean"] = mean([r["hr"] for r in fr])
            s["by_family"][f]["takeable_n"] = len(fr)
        s["by_symbol"] = {}
        for sym, c in Counter(r.get("symbol") for r in sub).most_common(8):
            sr = [r for r in sub if r.get("symbol") == sym and r.get("takeable")]
            s["by_symbol"][sym] = {"n": c, "takeable_n": len(sr), "h_gross_mean": mean([r["hr"] for r in sr])}
        # per-day stability
        byday = {}
        for r in sub:
            if r.get("takeable"):
                byday.setdefault(r["decision_time_utc"][:10], []).append(r["hr"])
        days = sorted(byday)
        s["n_days"] = len(days)
        s["day_pos_frac"] = round(sum(1 for d in days if sum(byday[d]) / len(byday[d]) > 0) / len(days), 4) if days else None
        s["day_means"] = {d: round(sum(byday[d]) / len(byday[d]), 4) for d in days}
        det[k] = s
    res["labels"] = det
    # union minus the dominant label to test independence
    res["B_minus_A"] = stats([rows[i] for i in (sets["B_signed_authority_invalid"] - sets["A_numeric_disagreement"])])
    res["A_minus_B"] = stats([rows[i] for i in (sets["A_numeric_disagreement"] - sets["B_signed_authority_invalid"])])
    res["A_and_B"] = stats([rows[i] for i in (sets["A_numeric_disagreement"] & sets["B_signed_authority_invalid"])])
    with open(os.path.join(D, "L6_POSITIVE_COHORT_V1.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    K = ("n", "takeable_n", "h_gross_mean", "h_win_pct", "h_net_corr73_mean", "h_net_corr73_total")
    print("POOL ", {k: res["POOL"][k] for k in K})
    print("UNION", {k: res["UNION"][k] for k in K}, "  1stEm:", {k: res["UNION_first_emission"][k] for k in K})
    for k, s in det.items():
        print(f"{k:28s}", {kk: s[kk] for kk in K}, f"days={s['n_days']} posfrac={s['day_pos_frac']}")
    print("overlap", ov)
    for k in ("A_minus_B", "B_minus_A", "A_and_B"):
        print(k, {kk: res[k][kk] for kk in K})


if __name__ == "__main__":
    main()
