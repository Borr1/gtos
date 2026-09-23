#!/usr/bin/env python3
"""Cartographer receipt tool: measure the stamped-EV vs realized-outcome gap on
a compact pool, streaming. Wave 19 forensic, Session FA."""
import gzip
import json
import sys


def main(path: str) -> None:
    n = 0
    ev_eq_expect = 0
    exp_net_identity = 0  # expected_net_r ~= expectancy_r - cost_r
    pos_exp = {"n": 0, "sum_out": 0.0, "sum_exp": 0.0}
    neg_exp = {"n": 0, "sum_out": 0.0, "sum_exp": 0.0}
    prob_sum = 0.0
    prob_n = 0
    # binary-endpoint realized hit rate vs stamped probability
    hits = 0
    stops = 0
    with gzip.open(path, "rt") as fh:
        for line in fh:
            row = json.loads(line)
            n += 1
            ev = row.get("candidate_ev_r")
            ex = row.get("expectancy_r")
            en = row.get("expected_net_r")
            cr = row.get("cost_r")
            out = row.get("opportunity_net_proxy_r")
            p = row.get("candidate_probability")
            if ev is not None and ex is not None and abs(ev - ex) < 1e-9:
                ev_eq_expect += 1
            if en is not None and ex is not None and cr is not None and abs(en - (ex - cr)) < 1e-6:
                exp_net_identity += 1
            if en is not None and out is not None:
                b = pos_exp if en > 0 else neg_exp
                b["n"] += 1
                b["sum_out"] += out
                b["sum_exp"] += en
            if p is not None:
                prob_sum += p
                prob_n += 1
            reason = str(row.get("miss_reason") or "")
            g = row.get("opportunity_gross_r")
            oc = str(row.get("opportunity_close_reason") or row.get("raw_opportunity_close_reason") or "")
    print(f"rows={n}")
    print(f"candidate_ev_r == expectancy_r on {ev_eq_expect}/{n}")
    print(f"expected_net_r == expectancy_r - cost_r on {exp_net_identity}/{n}")
    print(f"mean stamped candidate_probability = {prob_sum/prob_n:.4f}")
    for name, b in (("expected_net_r>0", pos_exp), ("expected_net_r<=0", neg_exp)):
        if b["n"]:
            print(
                f"{name}: n={b['n']} mean_expected={b['sum_exp']/b['n']:+.4f} "
                f"mean_realized={b['sum_out']/b['n']:+.4f}"
            )


if __name__ == "__main__":
    main(sys.argv[1])
